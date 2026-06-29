"""
Sistema de Coleta e Indexação Automática
Baixa PDFs via PCI Concursos e indexa automaticamente no RAG
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.pci_banca_scraper import PCIBancaScraper

# Importar core para indexação
try:
    from src.core import indexar_pdf, init_db
    CORE_AVAILABLE = True
    print("✅ Core RAG disponível - PDFs serão indexados automaticamente")
except Exception as e:
    CORE_AVAILABLE = False
    print(f"⚠️ Core não disponível: {e}")
    print("   PDFs serão apenas baixados, não indexados")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coleta_automatica.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ColetorIndexadorAutomatico:
    """
    Coleta PDFs e indexa automaticamente no ChromaDB
    """
    
    def __init__(self, download_dir='editais'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        self.scraper = PCIBancaScraper(download_dir=str(self.download_dir))
        
        self.stats = {
            'total_baixados': 0,
            'total_indexados': 0,
            'total_erros': 0,
            'inicio': datetime.now()
        }
        
        # Inicializa ChromaDB se disponível
        if CORE_AVAILABLE:
            try:
                init_db()
                logger.info("✅ ChromaDB inicializado")
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar ChromaDB: {e}")
    
    def indexar_arquivo(self, filepath, banca, tipo='documento'):
        """
        Indexa um PDF no ChromaDB
        
        Args:
            filepath: Caminho do arquivo PDF
            banca: Nome da banca
            tipo: Tipo do documento (edital, prova, gabarito)
        """
        if not CORE_AVAILABLE:
            logger.warning("⚠️ Core não disponível - pulando indexação")
            return False
        
        try:
            filename = os.path.basename(filepath)
            
            # Cria metadados
            metadata = {
                'fonte': 'PCI Concursos',
                'banca': banca.upper(),
                'tipo': tipo,
                'arquivo': filename,
                'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"📊 Indexando: {filename}")
            
            # Indexa no ChromaDB
            num_chunks = indexar_pdf(filepath, metadata)
            
            if num_chunks > 0:
                logger.info(f"✅ Indexado: {filename} ({num_chunks} chunks)")
                self.stats['total_indexados'] += 1
                return True
            else:
                logger.warning(f"⚠️ Nenhum chunk criado: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao indexar {filepath}: {e}")
            self.stats['total_erros'] += 1
            return False
    
    def coletar_e_indexar_banca(self, banca, max_concursos=5, max_provas_por_concurso=5):
        """
        Coleta PDFs de uma banca e indexa automaticamente
        
        Args:
            banca: Nome da banca (cebraspe, fcc, fgv)
            max_concursos: Máximo de concursos a processar
            max_provas_por_concurso: Máximo de provas por concurso
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 COLETA E INDEXAÇÃO AUTOMÁTICA - {banca.upper()}")
        logger.info(f"{'='*70}\n")
        
        # 1. Coleta PDFs
        logger.info(f"📥 Fase 1: Coletando PDFs...")
        
        concursos = self.scraper.get_concursos(banca, max_concursos)
        
        if not concursos:
            logger.warning(f"⚠️ Nenhum concurso encontrado para {banca}")
            return
        
        pdfs_coletados = []
        
        for i, concurso in enumerate(concursos, 1):
            logger.info(f"\n📚 [{i}/{len(concursos)}] {concurso['titulo'][:80]}...")
            
            # Busca provas do concurso
            provas = self.scraper.get_provas_concurso(concurso['url'])
            provas = provas[:max_provas_por_concurso]
            
            # Baixa cada prova
            for prova in provas:
                arquivo = self.scraper.download_pdf(
                    prova['url'],
                    prova['titulo'],
                    banca,
                    prova['tipo']
                )
                
                if arquivo:
                    pdfs_coletados.append({
                        'filepath': arquivo,
                        'banca': banca,
                        'tipo': prova['tipo']
                    })
                    self.stats['total_baixados'] += 1
                
                # Delay entre downloads
                import time
                time.sleep(2)
            
            # Delay entre concursos
            if i < len(concursos):
                import time
                time.sleep(3)
        
        # 2. Indexa PDFs
        if pdfs_coletados and CORE_AVAILABLE:
            logger.info(f"\n📊 Fase 2: Indexando {len(pdfs_coletados)} PDFs no RAG...")
            
            for i, pdf_info in enumerate(pdfs_coletados, 1):
                logger.info(f"\n[{i}/{len(pdfs_coletados)}]")
                self.indexar_arquivo(
                    pdf_info['filepath'],
                    pdf_info['banca'],
                    pdf_info['tipo']
                )
                
                # Pequeno delay entre indexações
                import time
                time.sleep(1)
        
        # 3. Relatório final
        self._imprimir_relatorio(banca)
    
    def coletar_e_indexar_todas(self, max_concursos=5, max_provas_por_concurso=5):
        """
        Coleta e indexa todas as bancas disponíveis
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🌐 COLETA E INDEXAÇÃO COMPLETA - TODAS AS BANCAS")
        logger.info(f"{'='*70}\n")
        
        bancas = ['cebraspe', 'fcc', 'fgv']
        
        for i, banca in enumerate(bancas, 1):
            logger.info(f"\n🎯 Banca {i}/{len(bancas)}: {banca.upper()}")
            self.coletar_e_indexar_banca(banca, max_concursos, max_provas_por_concurso)
            
            # Delay entre bancas
            if i < len(bancas):
                logger.info("\n⏸️ Aguardando 10 segundos antes da próxima banca...\n")
                import time
                time.sleep(10)
        
        # Relatório geral
        self._imprimir_relatorio_geral()
    
    def _imprimir_relatorio(self, banca):
        """Imprime relatório de coleta de uma banca"""
        tempo_decorrido = (datetime.now() - self.stats['inicio']).total_seconds()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 RELATÓRIO - {banca.upper()}")
        logger.info(f"{'='*70}")
        logger.info(f"✅ PDFs baixados: {self.stats['total_baixados']}")
        logger.info(f"📊 PDFs indexados: {self.stats['total_indexados']}")
        logger.info(f"❌ Erros: {self.stats['total_erros']}")
        logger.info(f"⏱️ Tempo: {tempo_decorrido:.0f}s")
        logger.info(f"📁 Diretório: {self.download_dir.absolute()}")
        logger.info(f"{'='*70}\n")
    
    def _imprimir_relatorio_geral(self):
        """Imprime relatório geral de todas as bancas"""
        tempo_total = (datetime.now() - self.stats['inicio']).total_seconds()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 RELATÓRIO GERAL - COLETA COMPLETA")
        logger.info(f"{'='*70}")
        logger.info(f"✅ Total de PDFs baixados: {self.stats['total_baixados']}")
        logger.info(f"📊 Total de PDFs indexados: {self.stats['total_indexados']}")
        logger.info(f"❌ Total de erros: {self.stats['total_erros']}")
        logger.info(f"⏱️ Tempo total: {tempo_total/60:.1f} minutos")
        logger.info(f"📁 Diretório: {self.download_dir.absolute()}")
        
        if CORE_AVAILABLE:
            logger.info(f"\n🤖 Sistema RAG pronto para consultas!")
            logger.info(f"   Use o Streamlit ou API para perguntar sobre os editais")
        
        logger.info(f"{'='*70}\n")


# Funções de conveniência
def coletar_indexar_cebraspe(max_concursos=5):
    """Coleta e indexa Cebraspe"""
    coletor = ColetorIndexadorAutomatico()
    coletor.coletar_e_indexar_banca('cebraspe', max_concursos)


def coletar_indexar_fcc(max_concursos=5):
    """Coleta e indexa FCC"""
    coletor = ColetorIndexadorAutomatico()
    coletor.coletar_e_indexar_banca('fcc', max_concursos)


def coletar_indexar_fgv(max_concursos=5):
    """Coleta e indexa FGV"""
    coletor = ColetorIndexadorAutomatico()
    coletor.coletar_e_indexar_banca('fgv', max_concursos)


def coletar_indexar_todas(max_concursos=5):
    """Coleta e indexa todas as bancas"""
    coletor = ColetorIndexadorAutomatico()
    coletor.coletar_e_indexar_todas(max_concursos)


if __name__ == '__main__':
    import sys
    
    print("\n🤖 COLETOR E INDEXADOR AUTOMÁTICO")
    print("="*70)
    print()
    
    # Permite passar argumentos via linha de comando
    if len(sys.argv) > 1:
        banca = sys.argv[1].lower()
        max_concursos = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        
        if banca == 'todas':
            print(f"🌐 Coletando TODAS as bancas ({max_concursos} concursos cada)")
            coletar_indexar_todas(max_concursos)
        elif banca in ['cebraspe', 'fcc', 'fgv']:
            print(f"🎯 Coletando {banca.upper()} ({max_concursos} concursos)")
            coletor = ColetorIndexadorAutomatico()
            coletor.coletar_e_indexar_banca(banca, max_concursos)
        else:
            print(f"❌ Banca inválida: {banca}")
            print("   Use: cebraspe, fcc, fgv ou todas")
    else:
        # Modo interativo
        print("Escolha uma opção:")
        print("  1. Cebraspe (5 concursos)")
        print("  2. FCC (5 concursos)")
        print("  3. FGV (5 concursos)")
        print("  4. TODAS as bancas (5 concursos cada)")
        print()
        
        try:
            escolha = input("Digite o número da opção (1-4): ").strip()
            
            if escolha == '1':
                coletar_indexar_cebraspe(5)
            elif escolha == '2':
                coletar_indexar_fcc(5)
            elif escolha == '3':
                coletar_indexar_fgv(5)
            elif escolha == '4':
                coletar_indexar_todas(5)
            else:
                print("❌ Opção inválida")
        except KeyboardInterrupt:
            print("\n\n⚠️ Operação cancelada pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro: {e}")
