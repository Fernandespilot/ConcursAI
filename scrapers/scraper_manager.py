"""
Gerenciador Unificado de Scrapers
=================================
Coordena e executa múltiplos scrapers de forma eficiente
"""

import asyncio
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from pci_scraper import PCIConcursoScraper
from concursos_brasil_scraper import ConcursoNoBrasilScraper

class ScraperManager:
    def __init__(self, max_workers: int = 2):
        """
        Inicializa o gerenciador de scrapers
        
        Args:
            max_workers: Número máximo de scrapers executando simultaneamente
        """
        self.max_workers = max_workers
        self.scrapers = {
            'pci': PCIConcursoScraper(delay_range=(2, 4)),  # Delays maiores para ser mais respeitoso
            'concursos_brasil': ConcursoNoBrasilScraper(delay_range=(2, 4))
        }
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def run_single_scraper(self, scraper_name: str, query: str, pages: int = 3) -> List[Dict]:
        """
        Executa um scraper específico
        
        Args:
            scraper_name: Nome do scraper ('pci' ou 'concursos_brasil')
            query: Termo de busca
            pages: Número de páginas
            
        Returns:
            Lista de concursos coletados
        """
        if scraper_name not in self.scrapers:
            self.logger.error(f"Scraper '{scraper_name}' não encontrado")
            return []
        
        scraper = self.scrapers[scraper_name]
        
        try:
            self.logger.info(f"🚀 Iniciando scraper: {scraper_name}")
            start_time = time.time()
            
            concursos = scraper.search_concursos(query=query, pages=pages)
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.logger.info(f"✅ {scraper_name} finalizado: {len(concursos)} concursos em {duration:.2f}s")
            
            # Adicionar identificador da fonte
            for concurso in concursos:
                concurso['scraper_fonte'] = scraper_name
            
            return concursos
            
        except Exception as e:
            self.logger.error(f"❌ Erro no scraper {scraper_name}: {e}")
            return []
    
    def run_all_scrapers(self, query: str, pages: int = 3) -> Dict[str, List[Dict]]:
        """
        Executa todos os scrapers em paralelo
        
        Args:
            query: Termo de busca
            pages: Número de páginas por scraper
            
        Returns:
            Dicionário com resultados de cada scraper
        """
        results = {}
        
        self.logger.info(f"🔍 Iniciando coleta em todos os sites para: '{query}'")
        self.logger.info(f"📄 {pages} páginas por site")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submeter tarefas
            future_to_scraper = {
                executor.submit(self.run_single_scraper, scraper_name, query, pages): scraper_name
                for scraper_name in self.scrapers.keys()
            }
            
            # Coletar resultados
            for future in as_completed(future_to_scraper):
                scraper_name = future_to_scraper[future]
                try:
                    concursos = future.result()
                    results[scraper_name] = concursos
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro no scraper {scraper_name}: {e}")
                    results[scraper_name] = []
        
        # Resumo
        total_concursos = sum(len(concursos) for concursos in results.values())
        self.logger.info(f"🎉 Coleta finalizada! Total: {total_concursos} concursos")
        
        for scraper_name, concursos in results.items():
            self.logger.info(f"  📊 {scraper_name}: {len(concursos)} concursos")
        
        return results
    
    def merge_results(self, results: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Mescla resultados de múltiplos scrapers removendo duplicatas
        
        Args:
            results: Dicionário com resultados dos scrapers
            
        Returns:
            Lista unificada de concursos sem duplicatas
        """
        all_concursos = []
        seen_titles = set()
        
        for scraper_name, concursos in results.items():
            for concurso in concursos:
                # Usar título como chave de deduplicação
                title = concurso.get('titulo', '').strip().lower()
                
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_concursos.append(concurso)
                elif title:
                    self.logger.debug(f"Duplicata removida: {title}")
        
        self.logger.info(f"📝 Após deduplicação: {len(all_concursos)} concursos únicos")
        return all_concursos
    
    def save_results(self, results: Dict[str, List[Dict]], query: str = ""):
        """
        Salva resultados em diferentes formatos
        
        Args:
            results: Resultados dos scrapers
            query: Termo de busca (para nome do arquivo)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_clean = query.replace(" ", "_").replace("/", "_") if query else "todos"
        
        # Salvar resultados individuais
        for scraper_name, concursos in results.items():
            if concursos:
                filename = f"concursos_{scraper_name}_{query_clean}_{timestamp}.csv"
                try:
                    df = pd.DataFrame(concursos)
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                    self.logger.info(f"💾 {scraper_name}: {filename}")
                except Exception as e:
                    self.logger.error(f"Erro ao salvar {scraper_name}: {e}")
        
        # Salvar resultado unificado
        all_concursos = self.merge_results(results)
        if all_concursos:
            unified_filename = f"concursos_unificado_{query_clean}_{timestamp}.csv"
            try:
                df = pd.DataFrame(all_concursos)
                df.to_csv(unified_filename, index=False, encoding='utf-8-sig')
                self.logger.info(f"💾 Unificado: {unified_filename}")
            except Exception as e:
                self.logger.error(f"Erro ao salvar unificado: {e}")
        
        # Salvar resumo em JSON
        summary = {
            'timestamp': timestamp,
            'query': query,
            'total_scrapers': len(results),
            'total_concursos': sum(len(concursos) for concursos in results.values()),
            'concursos_unicos': len(all_concursos),
            'por_fonte': {
                scraper: len(concursos) 
                for scraper, concursos in results.items()
            }
        }
        
        summary_filename = f"resumo_coleta_{query_clean}_{timestamp}.json"
        try:
            with open(summary_filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            self.logger.info(f"📊 Resumo: {summary_filename}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar resumo: {e}")
    
    def search_by_categories(self, categories: List[str], pages: int = 2) -> Dict:
        """
        Busca concursos por múltiplas categorias
        
        Args:
            categories: Lista de categorias/termos para buscar
            pages: Páginas por categoria
            
        Returns:
            Resultados organizados por categoria
        """
        all_results = {}
        
        for category in categories:
            self.logger.info(f"🏷️ Buscando categoria: {category}")
            
            category_results = self.run_all_scrapers(query=category, pages=pages)
            all_results[category] = category_results
            
            # Pequena pausa entre categorias
            time.sleep(5)
        
        return all_results
    
    def generate_report(self, results: Dict[str, List[Dict]]) -> str:
        """
        Gera relatório da coleta
        
        Args:
            results: Resultados dos scrapers
            
        Returns:
            String com relatório formatado
        """
        report = []
        report.append("=" * 60)
        report.append("RELATÓRIO DE COLETA DE CONCURSOS")
        report.append("=" * 60)
        report.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        report.append("")
        
        total_concursos = sum(len(concursos) for concursos in results.values())
        
        report.append(f"📊 RESUMO GERAL:")
        report.append(f"  Total de Scrapers: {len(results)}")
        report.append(f"  Total de Concursos: {total_concursos}")
        report.append("")
        
        report.append(f"📈 POR FONTE:")
        for scraper_name, concursos in results.items():
            report.append(f"  {scraper_name.upper()}: {len(concursos)} concursos")
            
            if concursos:
                # Estatísticas básicas
                com_salario = sum(1 for c in concursos if c.get('salario'))
                com_vagas = sum(1 for c in concursos if c.get('vagas', 0) > 0)
                
                report.append(f"    - Com salário informado: {com_salario}")
                report.append(f"    - Com vagas informadas: {com_vagas}")
        
        report.append("")
        report.append("🎯 PRÓXIMOS PASSOS:")
        report.append("  1. Revisar dados coletados")
        report.append("  2. Processar e indexar no sistema")
        report.append("  3. Atualizar base de conhecimento")
        report.append("=" * 60)
        
        return "\n".join(report)

# Funções de conveniência para uso direto
def buscar_concursos_tecnologia(pages: int = 3):
    """Busca específica para concursos de tecnologia"""
    manager = ScraperManager()
    
    termos_tecnologia = ["programador", "analista de sistemas", "desenvolvedor", "TI"]
    
    for termo in termos_tecnologia:
        print(f"\n🔍 Buscando: {termo}")
        results = manager.run_all_scrapers(query=termo, pages=pages)
        manager.save_results(results, termo)
        
        # Relatório
        report = manager.generate_report(results)
        print(report)
        
        # Pausa entre buscas
        time.sleep(10)

def buscar_todos_concursos(pages: int = 5):
    """Busca geral de concursos"""
    manager = ScraperManager()
    
    results = manager.run_all_scrapers(query="", pages=pages)
    manager.save_results(results, "geral")
    
    report = manager.generate_report(results)
    print(report)

# Exemplo de uso
if __name__ == "__main__":
    print("🚀 Iniciando coleta de concursos...")
    
    manager = ScraperManager()
    
    # Buscar concursos de programação
    results = manager.run_all_scrapers(query="programador", pages=2)
    
    # Salvar resultados
    manager.save_results(results, "programador")
    
    # Exibir relatório
    report = manager.generate_report(results)
    print(report)
