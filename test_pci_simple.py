"""
Teste ISOLADO do PCI Scraper (sem dependências do core)
"""

print("🧪 Testando PCI Scraper (isolado)...")
print("="*60)

import sys
import os

# Importar diretamente o scraper sem passar pelo __init__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import direto do arquivo
    from scrapers.pci_banca_scraper import PCIBancaScraper
    print("✅ Import OK")
    
    # Criar instância
    scraper = PCIBancaScraper(download_dir='editais')
    print("✅ Instância criada")
    
    # Testar busca (sem download)
    print("\n📋 Buscando concursos Cebraspe...")
    concursos = scraper.get_concursos('cebraspe', max_concursos=3)
    
    if concursos:
        print(f"\n✅ Encontrados {len(concursos)} concursos!")
        for i, c in enumerate(concursos, 1):
            print(f"\n   {i}. {c['titulo'][:80]}...")
            print(f"      URL: {c['url']}")
            print(f"      Banca: {c['banca']}")
    else:
        print("⚠️ Nenhum concurso encontrado")
    
    print("\n" + "="*60)
    print("✅ Teste básico concluído com sucesso!")
    print("\n💡 Para testar download completo:")
    print("   python -m scrapers.pci_banca_scraper")
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("\n💡 Instale: pip install requests beautifulsoup4 lxml")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
