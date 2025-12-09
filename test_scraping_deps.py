"""
Teste de dependências do sistema de scraping
"""

print("🔍 Verificando dependências do sistema de scraping...\n")

# Teste 1: Scrapy
try:
    import scrapy
    print("✅ Scrapy instalado")
except ImportError as e:
    print(f"❌ Scrapy não instalado: {e}")

# Teste 2: BeautifulSoup4
try:
    import bs4
    print("✅ BeautifulSoup4 instalado")
except ImportError as e:
    print(f"❌ BeautifulSoup4 não instalado: {e}")

# Teste 3: Requests
try:
    import requests
    print("✅ Requests instalado")
except ImportError as e:
    print(f"❌ Requests não instalado: {e}")

# Teste 4: APScheduler
try:
    import apscheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    print(f"✅ APScheduler instalado (versão {apscheduler.__version__})")
except ImportError as e:
    print(f"❌ APScheduler não instalado: {e}")

# Teste 5: lxml
try:
    import lxml
    print("✅ lxml instalado")
except ImportError as e:
    print(f"❌ lxml não instalado: {e}")

# Teste 6: Scrapers
print("\n🔍 Verificando scrapers personalizados...\n")

try:
    from scrapers.cebraspe_scraper import CebraspeScraper
    print("✅ CebraspeScraper carregado")
except ImportError as e:
    print(f"❌ CebraspeScraper não carregado: {e}")

try:
    from scrapers.fgv_scraper import FGVScraper
    print("✅ FGVScraper carregado")
except ImportError as e:
    print(f"❌ FGVScraper não carregado: {e}")

try:
    from scrapers.scraper_scheduler import ScraperScheduler, coletar_agora
    print("✅ ScraperScheduler carregado")
except ImportError as e:
    print(f"❌ ScraperScheduler não carregado: {e}")

print("\n" + "="*60)
print("✅ Teste completo!")
print("="*60)
