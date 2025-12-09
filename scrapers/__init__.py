"""
Módulo de scrapers do ConcursAI
Contém todos os coletores de dados de concursos
"""

from .pci_scraper_completo import PCIConcursoScraperCompleto
from .concursos_brasil_scraper_completo import ConcursosBrasilScraperCompleto
from .scraper_manager_completo import ScraperManagerCompleto

# Novos scrapers de editais
try:
    from .cebraspe_scraper import CebraspeScraper
    from .fgv_scraper import FGVScraper
    from .scraper_scheduler import ScraperScheduler, coletar_agora, coletar_todas_agora, agendar_diario, agendar_semanal
    SCRAPING_DISPONIVEL = True
except ImportError as e:
    print(f"⚠️  Scrapers de editais não disponíveis: {e}")
    CebraspeScraper = None
    FGVScraper = None
    ScraperScheduler = None
    SCRAPING_DISPONIVEL = False

__all__ = [
    'PCIConcursoScraperCompleto',
    'ConcursosBrasilScraperCompleto', 
    'ScraperManagerCompleto',
    'CebraspeScraper',
    'FGVScraper',
    'ScraperScheduler',
    'SCRAPING_DISPONIVEL'
]
