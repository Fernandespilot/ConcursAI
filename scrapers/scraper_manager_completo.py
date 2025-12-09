"""
🎯 SCRAPER MANAGER UNIFICADO - Versão Completa
==============================================
Gerencia e unifica dados de todos os scrapers
"""

import pandas as pd
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
import threading
from pathlib import Path

# Importar scrapers
try:
    from scrapers.pci_scraper_completo import PCIConcursoScraperCompleto
    from scrapers.concursos_brasil_scraper_completo import ConcursosBrasilScraperCompleto
except ImportError:
    # Fallback para scraper híbrido
    from scrapers.scraper_hibrido_otimizado import ScraperHibridoOtimizado

class ScraperManagerCompleto:
    def __init__(self, output_dir: str = "data"):
        """Manager unificado para todos os scrapers"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Inicializar scrapers
        self.pci_scraper = PCIConcursoScraperCompleto()
        self.brasil_scraper = ConcursosBrasilScraperCompleto()
        
        # Dados coletados
        self.todos_concursos = []
        self.dados_por_fonte = {}
    
    def coletar_pci_concurso(self, max_pages: int = 25) -> List[Dict]:
        """Coleta dados do PCI Concurso"""
        self.logger.info("🚀 INICIANDO COLETA PCI CONCURSO")
        self.logger.info("=" * 50)
        
        try:
            concursos_pci = self.pci_scraper.coletar_todos_concursos(max_pages=max_pages)
            
            if concursos_pci:
                # Salvar dados específicos
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.output_dir / f"pci_concursos_{timestamp}.csv"
                
                df = pd.DataFrame(concursos_pci)
                df.to_csv(filename, index=False, encoding='utf-8')
                
                self.dados_por_fonte['PCI Concurso'] = concursos_pci
                
                self.logger.info(f"✅ PCI Concurso: {len(concursos_pci)} concursos coletados")
                self.logger.info(f"💾 Salvos em: {filename}")
                
                return concursos_pci
            else:
                self.logger.warning("⚠️ PCI Concurso: nenhum dado coletado")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Erro no PCI Concurso: {e}")
            return []
    
    def coletar_concursos_brasil(self, max_pages: int = 20) -> List[Dict]:
        """Coleta dados do Concursos Brasil"""
        self.logger.info("🚀 INICIANDO COLETA CONCURSOS BRASIL")
        self.logger.info("=" * 50)
        
        try:
            concursos_brasil = self.brasil_scraper.coletar_todos_concursos(max_pages=max_pages)
            
            if concursos_brasil:
                # Salvar dados específicos
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.output_dir / f"concursos_brasil_{timestamp}.csv"
                
                df = pd.DataFrame(concursos_brasil)
                df.to_csv(filename, index=False, encoding='utf-8')
                
                self.dados_por_fonte['Concursos Brasil'] = concursos_brasil
                
                self.logger.info(f"✅ Concursos Brasil: {len(concursos_brasil)} concursos coletados")
                self.logger.info(f"💾 Salvos em: {filename}")
                
                return concursos_brasil
            else:
                self.logger.warning("⚠️ Concursos Brasil: nenhum dado coletado")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Erro no Concursos Brasil: {e}")
            return []
    
    def coletar_todos_sites(self, pci_pages: int = 25, brasil_pages: int = 20) -> Dict:
        """Coleta dados de todos os sites"""
        self.logger.info("🎯 INICIANDO COLETA COMPLETA DE TODOS OS SITES")
        self.logger.info("=" * 60)
        
        resultados = {
            'pci_concurso': [],
            'concursos_brasil': [],
            'total_geral': 0,
            'sucesso': False
        }
        
        try:
            # Coletar PCI Concurso
            resultados['pci_concurso'] = self.coletar_pci_concurso(max_pages=pci_pages)
            
            # Aguardar um pouco entre coletas
            self.logger.info("⏳ Aguardando 5 segundos antes da próxima coleta...")
            import time
            time.sleep(5)
            
            # Coletar Concursos Brasil
            resultados['concursos_brasil'] = self.coletar_concursos_brasil(max_pages=brasil_pages)
            
            # Unificar todos os dados
            self.todos_concursos = []
            self.todos_concursos.extend(resultados['pci_concurso'])
            self.todos_concursos.extend(resultados['concursos_brasil'])
            
            resultados['total_geral'] = len(self.todos_concursos)
            resultados['sucesso'] = True
            
            # Salvar dados unificados
            if self.todos_concursos:
                self.salvar_dados_unificados()
            
            return resultados
            
        except Exception as e:
            self.logger.error(f"❌ Erro na coleta geral: {e}")
            resultados['sucesso'] = False
            return resultados
    
    def salvar_dados_unificados(self) -> str:
        """Salva todos os dados unificados"""
        if not self.todos_concursos:
            self.logger.warning("⚠️ Nenhum dado para salvar")
            return ""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Salvar CSV unificado
            csv_filename = self.output_dir / f"concursos_unificados_{timestamp}.csv"
            df = pd.DataFrame(self.todos_concursos)
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            
            # Salvar JSON unificado
            json_filename = self.output_dir / f"concursos_unificados_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.todos_concursos, f, ensure_ascii=False, indent=2)
            
            # Salvar relatório
            relatorio_filename = self.output_dir / f"relatorio_coleta_{timestamp}.txt"
            self.gerar_relatorio_completo(relatorio_filename)
            
            self.logger.info(f"💾 Dados unificados salvos:")
            self.logger.info(f"   📊 CSV: {csv_filename}")
            self.logger.info(f"   📋 JSON: {json_filename}")
            self.logger.info(f"   📄 Relatório: {relatorio_filename}")
            
            return str(csv_filename)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar dados unificados: {e}")
            return ""
    
    def gerar_relatorio_completo(self, filename: str = None):
        """Gera relatório detalhado da coleta"""
        if not self.todos_concursos:
            return
        
        df = pd.DataFrame(self.todos_concursos)
        
        # Calcular estatísticas
        stats = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_concursos': len(df),
            'total_vagas': df['vagas'].sum(),
            'concursos_por_fonte': df['fonte'].value_counts().to_dict(),
            'concursos_por_escolaridade': df['escolaridade'].value_counts().head(10).to_dict(),
            'concursos_por_status': df['status'].value_counts().to_dict(),
            'top_orgaos': df['orgao'].value_counts().head(15).to_dict(),
            'salario_medio': df[df['salario_numerico'] > 0]['salario_numerico'].mean(),
            'salario_max': df['salario_numerico'].max(),
            'concursos_com_salario': len(df[df['salario_numerico'] > 0]),
            'vagas_por_escolaridade': df.groupby('escolaridade')['vagas'].sum().to_dict()
        }
        
        # Gerar relatório em texto
        relatorio = f"""
🎯 RELATÓRIO COMPLETO DE COLETA DE CONCURSOS
============================================
Data/Hora: {stats['timestamp']}

📊 RESUMO GERAL
- Total de concursos coletados: {stats['total_concursos']:,}
- Total de vagas disponíveis: {stats['total_vagas']:,}
- Concursos com informação salarial: {stats['concursos_com_salario']:,}
- Salário médio: R$ {stats['salario_medio']:.2f}
- Maior salário: R$ {stats['salario_max']:.2f}

📈 CONCURSOS POR FONTE
"""
        
        for fonte, count in stats['concursos_por_fonte'].items():
            relatorio += f"- {fonte}: {count:,} concursos\\n"
        
        relatorio += f"""
🎓 TOP 10 ESCOLARIDADES
"""
        for escol, count in list(stats['concursos_por_escolaridade'].items())[:10]:
            relatorio += f"- {escol}: {count:,} concursos\\n"
        
        relatorio += f"""
🏢 TOP 15 ÓRGÃOS/INSTITUIÇÕES
"""
        for orgao, count in list(stats['top_orgaos'].items())[:15]:
            relatorio += f"- {orgao}: {count:,} concursos\\n"
        
        relatorio += f"""
👥 VAGAS POR ESCOLARIDADE
"""
        for escol, vagas in stats['vagas_por_escolaridade'].items():
            relatorio += f"- {escol}: {vagas:,} vagas\\n"
        
        relatorio += f"""
📋 STATUS DOS CONCURSOS
"""
        for status, count in stats['concursos_por_status'].items():
            relatorio += f"- {status}: {count:,} concursos\\n"
        
        relatorio += f"""
============================================
Relatório gerado automaticamente pelo ConcursAI
Sistema de coleta e análise de concursos públicos
============================================
"""
        
        # Salvar relatório
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(relatorio)
        
        # Exibir no console
        print(relatorio)
        
        return stats
    
    def obter_ultimos_concursos(self, limite: int = 10) -> List[Dict]:
        """Retorna os últimos concursos coletados"""
        if not self.todos_concursos:
            return []
        
        # Ordenar por data de coleta (mais recentes primeiro)
        concursos_ordenados = sorted(
            self.todos_concursos, 
            key=lambda x: x.get('data_coleta', ''), 
            reverse=True
        )
        
        return concursos_ordenados[:limite]

def main():
    """Função principal para executar coleta completa"""
    
    print("🚀 SISTEMA DE COLETA COMPLETA DO CONCURSAI")
    print("=" * 60)
    
    # Criar manager
    manager = ScraperManagerCompleto()
    
    try:
        # Executar coleta completa
        resultados = manager.coletar_todos_sites(
            pci_pages=30,      # PCI Concurso: 30 páginas
            brasil_pages=25    # Concursos Brasil: 25 páginas
        )
        
        if resultados['sucesso']:
            print("\\n🎉 COLETA COMPLETA FINALIZADA COM SUCESSO!")
            print("=" * 60)
            print(f"📊 PCI Concurso: {len(resultados['pci_concurso'])} concursos")
            print(f"📊 Concursos Brasil: {len(resultados['concursos_brasil'])} concursos")
            print(f"📊 TOTAL GERAL: {resultados['total_geral']} concursos")
            
            # Gerar relatório final
            if manager.todos_concursos:
                manager.gerar_relatorio_completo()
                
        else:
            print("❌ Falha na coleta completa")
            
    except KeyboardInterrupt:
        print("\\n⏹️ Coleta interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante a coleta: {e}")

if __name__ == "__main__":
    main()
