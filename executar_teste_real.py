"""
🧪 TESTE REAL DO SISTEMA COM SEUS PDFs
=======================================
Executando análise completa dos PDFs existentes
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from modules.banca_area_analyzer import get_banca_area_analyzer, AREAS_CONHECIMENTO
from modules.rag_banca_inteligente import get_rag_inteligente
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def teste_real():
    """Teste real com os PDFs existentes"""
    
    print("\n" + "="*70)
    print("🎯 TESTE REAL DO SISTEMA DE ANÁLISE DE BANCAS")
    print("="*70)
    
    # Inicializar
    print("\n1️⃣  Inicializando sistema...")
    analyzer = get_banca_area_analyzer()
    print("   ✅ Analisador inicializado")
    
    # Organizar PDFs
    print("\n2️⃣  Organizando PDFs automaticamente por área...")
    print("   (Analisando conteúdo de 48 PDFs...)")
    
    try:
        reorganizados = analyzer.organizar_pdfs_existentes()
        print(f"   ✅ {reorganizados} PDFs organizados!")
    except Exception as e:
        print(f"   ⚠️  Erro na organização: {e}")
        print("   Continuando com estrutura atual...")
    
    # Processar CEBRASPE - vamos detectar qual área tem mais PDFs
    print("\n3️⃣  Processando CEBRASPE...")
    
    try:
        # Tentar processar com detecção automática
        import glob
        from pathlib import Path
        
        base_path = Path("provas/cebraspe")
        if base_path.exists():
            # Listar subpastas (áreas)
            areas_encontradas = [d.name for d in base_path.iterdir() if d.is_dir()]
            
            if areas_encontradas:
                print(f"   📁 Áreas encontradas: {', '.join(areas_encontradas)}")
                
                # Processar primeira área com PDFs
                for area in areas_encontradas:
                    pdfs = list((base_path / area).glob("*.pdf"))
                    if pdfs:
                        print(f"\n   🔄 Processando CEBRASPE - {area.title()}...")
                        print(f"      {len(pdfs)} PDFs encontrados")
                        
                        perfil = analyzer.processar_banca_area("cebraspe", area.replace("_", " ").title())
                        
                        if perfil and "erro" not in perfil:
                            print(f"      ✅ Processado com sucesso!")
                            print(f"      📊 Questões extraídas: {perfil.get('total_questoes', 0)}")
                            
                            # Mostrar top disciplinas
                            disciplinas = list(perfil.get("distribuicao_disciplinas", {}).items())[:3]
                            if disciplinas:
                                print(f"\n      📚 Top 3 Disciplinas:")
                                for i, (disc, dados) in enumerate(disciplinas, 1):
                                    print(f"         {i}. {disc}: {dados['percentual']:.1f}%")
                            
                            # Mostrar temas
                            temas = perfil.get("temas_mais_cobrados", [])[:5]
                            if temas:
                                print(f"\n      🔑 Top 5 Temas:")
                                for i, tema_data in enumerate(temas, 1):
                                    print(f"         {i}. {tema_data['tema']} ({tema_data['frequencia']}x)")
                        
                        break  # Processar só a primeira área por enquanto
            else:
                # PDFs estão diretamente na pasta cebraspe
                pdfs = list(base_path.glob("*.pdf"))
                if pdfs:
                    print(f"   📄 {len(pdfs)} PDFs encontrados diretamente na pasta")
                    print(f"   💡 Será necessário organizar por área primeiro")
    
    except Exception as e:
        print(f"   ❌ Erro ao processar: {e}")
        import traceback
        traceback.print_exc()
    
    # Teste de perguntas com RAG
    print("\n4️⃣  Testando RAG Inteligente...")
    
    rag = get_rag_inteligente()
    
    perguntas_teste = [
        "O que o CEBRASPE mais cobra em concursos?",
        "Quais bancas tenho dados disponíveis?"
    ]
    
    for i, pergunta in enumerate(perguntas_teste, 1):
        print(f"\n   ❓ Pergunta {i}: {pergunta}")
        print("   " + "─"*66)
        
        try:
            resposta = rag.responder(pergunta, usar_ollama=False)
            # Mostrar só primeiras 5 linhas da resposta
            linhas = resposta.split('\n')[:5]
            for linha in linhas:
                print(f"   {linha}")
            if len(resposta.split('\n')) > 5:
                print(f"   ... (resposta completa tem {len(resposta.split('\n'))} linhas)")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    # Resumo final
    print("\n" + "="*70)
    print("✅ TESTE CONCLUÍDO!")
    print("="*70)
    
    print("\n📊 Perfis disponíveis:")
    for banca, areas in analyzer.perfis.items():
        print(f"\n🏛️  {banca.upper()}:")
        for area, perfil in areas.items():
            if "erro" not in perfil:
                print(f"   • {area}: {perfil.get('total_questoes', 0)} questões")
    
    print("\n💡 Próximos passos:")
    print("   1. Execute: python teste_sistema_bancas.py")
    print("   2. Ou use: INICIAR_ANALISE_BANCAS.bat")
    print("   3. Faça perguntas específicas sobre as bancas!")
    
    print("\n📚 Exemplos de perguntas:")
    print('   • "O que o CEBRASPE mais cobra em Tecnologia?"')
    print('   • "Como estudar para FCC em Jurídica?"')
    print('   • "Qual a dificuldade da FGV?"')
    
    print("\n" + "="*70)

if __name__ == "__main__":
    teste_real()
