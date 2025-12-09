# scrapers/scraper_scheduler.py
"""
Sistema de agendamento e indexação automática de editais
Coleta PDFs e indexa no ChromaDB automaticamente
"""

import os
import sys
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import time

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.cebraspe_scraper import CebraspeScraper
from scrapers.fgv_scraper import FGVScraper
from scrapers.pci_banca_scraper import PCIBancaScraper, coletar_cebraspe, coletar_fcc, coletar_fgv, coletar_todas_bancas

# Tenta importar core (pode falhar se LLM não estiver carregado)
try:
    from src.core import indexar_pdf, init_db
    CORE_AVAILABLE = True
except Exception as e:
    logging.warning(f"Core não disponível: {e}")
    CORE_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScraperScheduler:
    """
    Gerenciador de scraping e indexação automática
    """
    
    def __init__(self, output_dir="editais"):
        self.output_dir = output_dir
        self.scheduler = BackgroundScheduler()
        self.stats = {
            'total_coletados': 0,
            'total_indexados': 0,
            'ultima_coleta': None,
            'proxima_coleta': None
        }
        
        # Inicializa scrapers
        self.scrapers = {
            'cebraspe': CebraspeScraper(output_dir),
            'fgv': FGVScraper(output_dir)
        }
        
        # Inicializa PCI scraper (mais confiável)
        self.pci_scraper = PCIBancaScraper(output_dir)
        logger.info("✓ PCI Scraper inicializado (Cebraspe, FCC, FGV)")
        
        # Inicializa DB se disponível
        if CORE_AVAILABLE:
            try:
                init_db()
                logger.info("✓ ChromaDB inicializado")
            except Exception as e:
                logger.warning(f"Não foi possível inicializar DB: {e}")
    
    def coletar_e_indexar(self, banca='cebraspe', max_concursos=5):
        """
        Coleta PDFs de uma banca e indexa automaticamente
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🕷️ INICIANDO COLETA: {banca.upper()}")
        logger.info(f"{'='*60}")
        
        try:
            # 1. Coleta PDFs
            scraper = self.scrapers.get(banca)
            if not scraper:
                logger.error(f"Scraper não encontrado: {banca}")
                return
            
            pdfs = scraper.coletar_tudo(max_concursos=max_concursos)
            self.stats['total_coletados'] += len(pdfs)
            self.stats['ultima_coleta'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if not pdfs:
                logger.warning("⚠ Nenhum PDF coletado")
                return
            
            # 2. Indexa no ChromaDB
            if CORE_AVAILABLE:
                logger.info(f"\n📊 Indexando {len(pdfs)} PDFs no RAG...")
                
                for i, pdf_data in enumerate(pdfs, 1):
                    filepath = pdf_data['filepath']
                    metadata = pdf_data['metadata']
                    
                    try:
                        num_chunks = indexar_pdf(filepath, metadata)
                        self.stats['total_indexados'] += 1
                        logger.info(f"  [{i}/{len(pdfs)}] ✓ {os.path.basename(filepath)} → {num_chunks} chunks")
                    except Exception as e:
                        logger.error(f"  [{i}/{len(pdfs)}] ✗ Erro ao indexar {filepath}: {e}")
                
                logger.info(f"\n✅ CONCLUÍDO: {self.stats['total_indexados']}/{len(pdfs)} indexados")
            else:
                logger.info(f"\n⊗ PDFs coletados mas não indexados (core não disponível)")
            
        except Exception as e:
            logger.error(f"❌ Erro na coleta: {e}")
    
    def coletar_todas_bancas(self, max_concursos=3):
        """Coleta de todas as bancas configuradas"""
        logger.info(f"\n{'#'*60}")
        logger.info(f"🚀 COLETA GERAL - TODAS AS BANCAS")
        logger.info(f"{'#'*60}")
        
        for banca in self.scrapers.keys():
            self.coletar_e_indexar(banca, max_concursos)
            time.sleep(5)  # Pausa entre bancas
        
        self._print_stats()
    
    def agendar_coleta_diaria(self, hora=6, minuto=0):
        """
        Agenda coleta diária em horário específico
        """
        job = self.scheduler.add_job(
            func=self.coletar_todas_bancas,
            trigger=CronTrigger(hour=hora, minute=minuto),
            id='coleta_diaria',
            replace_existing=True,
            args=[3]  # max_concursos
        )
        
        self.stats['proxima_coleta'] = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"⏰ Coleta diária agendada para {hora:02d}:{minuto:02d}")
        logger.info(f"   Próxima execução: {self.stats['proxima_coleta']}")
    
    def agendar_coleta_semanal(self, dia_semana='monday', hora=6):
        """
        Agenda coleta semanal (0=Monday, 6=Sunday)
        """
        dias = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        job = self.scheduler.add_job(
            func=self.coletar_todas_bancas,
            trigger=CronTrigger(day_of_week=dias[dia_semana.lower()], hour=hora),
            id='coleta_semanal',
            replace_existing=True,
            args=[5]  # max_concursos
        )
        
        self.stats['proxima_coleta'] = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"⏰ Coleta semanal agendada: {dia_semana.capitalize()} às {hora}h")
    
    def iniciar(self):
        """Inicia o scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler iniciado")
        else:
            logger.info("⊗ Scheduler já está rodando")
    
    def parar(self):
        """Para o scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("⊗ Scheduler parado")
    
    def status(self):
        """Retorna status do sistema"""
        return {
            'rodando': self.scheduler.running,
            'jobs_ativos': len(self.scheduler.get_jobs()),
            **self.stats
        }
    
    def _print_stats(self):
        """Imprime estatísticas"""
        logger.info(f"\n📊 ESTATÍSTICAS:")
        logger.info(f"  • Total coletado: {self.stats['total_coletados']} PDFs")
        logger.info(f"  • Total indexado: {self.stats['total_indexados']} PDFs")
        logger.info(f"  • Última coleta: {self.stats['ultima_coleta']}")
        logger.info(f"  • Próxima coleta: {self.stats['proxima_coleta']}")


# Instância global
scheduler_instance = ScraperScheduler()


# Funções de conveniência
def coletar_agora(banca='cebraspe', max_concursos=5):
    """Coleta imediata de uma banca"""
    scheduler_instance.coletar_e_indexar(banca, max_concursos)


def coletar_todas_agora(max_concursos=3):
    """Coleta imediata de todas as bancas"""
    scheduler_instance.coletar_todas_bancas(max_concursos)


def coletar_pci_agora(banca='cebraspe', max_concursos=5):
    """
    Coleta via PCI Concursos (mais confiável)
    Bancas disponíveis: cebraspe, fcc, fgv
    """
    logger.info(f"🌐 Coletando {banca.upper()} via PCI Concursos...")
    arquivos = scheduler_instance.pci_scraper.coletar_banca(banca, max_concursos)
    
    # Indexar PDFs se core disponível
    if CORE_AVAILABLE and arquivos:
        logger.info(f"📊 Indexando {len(arquivos)} PDFs...")
        for arquivo in arquivos:
            try:
                metadata = {
                    'banca': banca.upper(),
                    'fonte': 'PCI Concursos',
                    'data_coleta': datetime.now().strftime('%Y-%m-%d')
                }
                indexar_pdf(arquivo, metadata)
                logger.info(f"✅ Indexado: {os.path.basename(arquivo)}")
            except Exception as e:
                logger.error(f"❌ Erro ao indexar {arquivo}: {e}")
    
    return arquivos


def coletar_todas_pci(max_concursos=5):
    """Coleta todas as bancas via PCI Concursos"""
    logger.info("🌐 Coletando TODAS as bancas via PCI Concursos...")
    return scheduler_instance.pci_scraper.coletar_todas(max_concursos)


def agendar_diario(hora=6, minuto=0):
    """Agenda coleta diária"""
    scheduler_instance.agendar_coleta_diaria(hora, minuto)
    scheduler_instance.iniciar()


def agendar_semanal(dia='monday', hora=6):
    """Agenda coleta semanal"""
    scheduler_instance.agendar_coleta_semanal(dia, hora)
    scheduler_instance.iniciar()


def obter_status():
    """Obtém status do scheduler"""
    return scheduler_instance.status()


def parar_scheduler():
    """Para o scheduler"""
    scheduler_instance.parar()


# Teste standalone
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SCRAPER SCHEDULER - TESTE")
    print("="*60)
    
    # Teste de coleta única
    print("\n1. Teste de coleta Cebraspe (2 concursos)...")
    coletar_agora('cebraspe', max_concursos=2)
    
    print("\n2. Status do sistema:")
    status = obter_status()
    for key, value in status.items():
        print(f"  • {key}: {value}")
    
    print("\n3. Agendando coleta diária às 6h...")
    agendar_diario(hora=6, minuto=0)
    
    print("\n✅ Teste concluído! Scheduler rodando em background.")
    print("   Use Ctrl+C para parar.")
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n⊗ Parando scheduler...")
        parar_scheduler()
