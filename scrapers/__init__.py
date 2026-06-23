"""
Módulo de scrapers do ConcursAI
Contém todos os coletores de dados de concursos
"""

# Scrapers principais — tudo em try/except para não quebrar o backend
PCIConcursoScraperCompleto = None
ConcursosBrasilScraperCompleto = None
ScraperManagerCompleto = None
CebraspeScraper = None
FGVScraper = None
ScraperScheduler = None
coletar_agora = None
coletar_todas_agora = None
agendar_diario = None
agendar_semanal = None
SCRAPING_DISPONIVEL = False

try:
    from .pci_scraper_main import PCIScraper as PCIConcursoScraperCompleto
except ImportError as e:
    print(f"⚠️  PCI scraper indisponível: {e}")

try:
    from .concursos_brasil_scraper import ConcursosBrasilScraper as ConcursosBrasilScraperCompleto
except ImportError as e:
    print(f"⚠️  Brasil scraper indisponível: {e}")

try:
    from .scraper_manager_v3 import ScraperManager as ScraperManagerCompleto
except ImportError as e:
    print(f"⚠️  Scraper manager indisponível: {e}")

try:
    from .cebraspe_scraper import CebraspeScraper
    from .fgv_scraper import FGVScraper
    from .scraper_scheduler import ScraperScheduler, coletar_agora, coletar_todas_agora, agendar_diario, agendar_semanal
    SCRAPING_DISPONIVEL = True
except ImportError as e:
    print(f"⚠️  Scrapers de editais indisponíveis: {e}")

__all__ = [
    'PCIConcursoScraperCompleto',
    'ConcursosBrasilScraperCompleto',
    'ScraperManagerCompleto',
    'CebraspeScraper',
    'FGVScraper',
    'ScraperScheduler',
    'SCRAPING_DISPONIVEL'
]
