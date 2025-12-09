"""
Teste rápido dos scrapers - versão de validação
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pci_scraper_completo import PCIConcursoScraperCompleto
from concursos_brasil_scraper_completo import ConcursosBrasilScraperCompleto

def teste_pci_rapido():
    """Teste rápido do PCI Concurso"""
    print("🧪 TESTANDO PCI CONCURSO - Primeira página")
    print("=" * 50)
    
    try:
        scraper = PCIConcursoScraperCompleto()
        concursos = scraper.coletar_todos_concursos(max_pages=1)  # Apenas 1 página
        
        if concursos:
            print(f"✅ Sucesso! Coletados {len(concursos)} concursos")
            
            # Mostrar primeiro concurso
            primeiro = concursos[0]
            print("\n📋 PRIMEIRO CONCURSO ENCONTRADO:")
            for key, value in primeiro.items():
                if key != 'link':  # Não mostrar link completo
                    print(f"   {key}: {value}")
            
            return True
        else:
            print("❌ Nenhum concurso coletado")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def teste_brasil_rapido():
    """Teste rápido do Concursos Brasil"""
    print("\n🧪 TESTANDO CONCURSOS BRASIL - Primeira página")
    print("=" * 50)
    
    try:
        scraper = ConcursosBrasilScraperCompleto()
        concursos = scraper.coletar_todos_concursos(max_pages=1)  # Apenas 1 página
        
        if concursos:
            print(f"✅ Sucesso! Coletados {len(concursos)} concursos")
            
            # Mostrar primeiro concurso
            primeiro = concursos[0]
            print("\n📋 PRIMEIRO CONCURSO ENCONTRADO:")
            for key, value in primeiro.items():
                if key != 'link':  # Não mostrar link completo
                    print(f"   {key}: {value}")
            
            return True
        else:
            print("❌ Nenhum concurso coletado")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Teste principal"""
    print("🚀 TESTE RÁPIDO DOS SCRAPERS")
    print("=" * 60)
    
    # Teste PCI
    pci_ok = teste_pci_rapido()
    
    # Teste Concursos Brasil
    brasil_ok = teste_brasil_rapido()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES:")
    print(f"   PCI Concurso: {'✅ OK' if pci_ok else '❌ FALHOU'}")
    print(f"   Concursos Brasil: {'✅ OK' if brasil_ok else '❌ FALHOU'}")
    
    if pci_ok and brasil_ok:
        print("\n🎉 TODOS OS SCRAPERS FUNCIONANDO!")
        print("Agora você pode executar a coleta completa com:")
        print("python scraper_manager_completo.py")
    else:
        print("\n⚠️ Alguns scrapers falharam. Verifique os erros acima.")

if __name__ == "__main__":
    main()
