"""
Teste rápido do PCI Scraper
"""

print("🧪 Testando PCI Banca Scraper...")
print("="*60)

try:
    from scrapers.pci_banca_scraper import PCIBancaScraper
    print("✅ Import do scraper OK")
    
    # Criar instância
    scraper = PCIBancaScraper(download_dir='editais_teste')
    print("✅ Instância criada")
    
    # Testar busca de concursos
    print("\n📋 Testando busca de concursos Cebraspe...")
    concursos = scraper.get_concursos('cebraspe', max_concursos=2)
    
    if concursos:
        print(f"✅ Encontrados {len(concursos)} concursos!")
        for i, c in enumerate(concursos, 1):
            print(f"   {i}. {c['titulo']}")
    else:
        print("⚠️ Nenhum concurso encontrado")
    
    print("\n✅ Teste básico concluído!")
    print("\n📝 Para teste completo com download:")
    print("   python -c \"from scrapers.pci_banca_scraper import coletar_cebraspe; coletar_cebraspe(2)\"")
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("\n💡 Execute: instalar_scraping.bat")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
