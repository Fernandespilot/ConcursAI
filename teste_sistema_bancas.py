"""
🧪 TESTE COMPLETO DO SISTEMA DE ANÁLISE POR BANCA + ÁREA
===========================================================
"""

import logging
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath('.'))

from modules.banca_area_analyzer import get_banca_area_analyzer, AREAS_CONHECIMENTO
from modules.rag_banca_inteligente import get_rag_inteligente

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def teste_1_organizacao_pdfs():
    """Teste 1: Organizar PDFs existentes por área"""
    print("\n" + "="*70)
    print("🧪 TESTE 1: Organização Automática de PDFs por Área")
    print("="*70)
    
    analyzer = get_banca_area_analyzer()
    
    print("\n📁 Organizando PDFs nas pastas de bancas...")
    print("   (Vai analisar conteúdo e mover para pasta da área correta)\n")
    
    reorganizados = analyzer.organizar_pdfs_existentes()
    
    print(f"\n✅ {reorganizados} PDFs organizados automaticamente!")
    print(f"\n📂 Estrutura criada:")
    print(f"   provas/")
    print(f"   ├── cebraspe/")
    print(f"   │   ├── tecnologia/")
    print(f"   │   ├── juridica/")
    print(f"   │   ├── saude/")
    print(f"   │   └── ...")
    print(f"   ├── fcc/")
    print(f"   └── fgv/")
    
    input("\n⏸️  Pressione ENTER para continuar...")


def teste_2_processar_banca_area():
    """Teste 2: Processar uma banca + área específica"""
    print("\n" + "="*70)
    print("🧪 TESTE 2: Processar CESPE - Tecnologia")
    print("="*70)
    
    analyzer = get_banca_area_analyzer()
    
    print("\n🔄 Processando todos os PDFs de CESPE na área de Tecnologia...")
    print("   (Extrai questões, categoriza, analisa padrões)\n")
    
    try:
        perfil = analyzer.processar_banca_area("cebraspe", "Tecnologia")
        
        if "erro" in perfil:
            print(f"\n⚠️  {perfil['erro']}")
            print(f"\n💡 Dica: Adicione PDFs em provas/cebraspe/tecnologia/")
        else:
            print(f"\n✅ Processamento concluído!")
            print(f"\n📊 Estatísticas:")
            print(f"   • Provas analisadas: {perfil.get('total_provas_analisadas', 0)}")
            print(f"   • Questões extraídas: {perfil.get('total_questoes', 0)}")
            print(f"   • Disciplinas encontradas: {len(perfil.get('distribuicao_disciplinas', {}))}")
            
            # Top 3 disciplinas
            disciplinas = list(perfil.get("distribuicao_disciplinas", {}).items())[:3]
            if disciplinas:
                print(f"\n📚 Top 3 Disciplinas:")
                for i, (disc, dados) in enumerate(disciplinas, 1):
                    print(f"   {i}. {disc}: {dados['percentual']:.1f}%")
            
            # Temas mais cobrados
            temas = perfil.get("temas_mais_cobrados", [])[:5]
            if temas:
                print(f"\n🔑 Top 5 Temas:")
                for i, tema_data in enumerate(temas, 1):
                    print(f"   {i}. {tema_data['tema']} ({tema_data['frequencia']}x)")
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print(f"\n💡 Certifique-se de ter PDFs em provas/cebraspe/tecnologia/")
    
    input("\n⏸️  Pressione ENTER para continuar...")


def teste_3_consulta_perfil():
    """Teste 3: Consultar perfil gerado"""
    print("\n" + "="*70)
    print("🧪 TESTE 3: Consultar Perfil Completo")
    print("="*70)
    
    analyzer = get_banca_area_analyzer()
    
    print("\n📋 Consultando perfil do CESPE em Tecnologia...\n")
    
    resposta = analyzer.consultar_perfil("cebraspe", "Tecnologia")
    print(resposta)
    
    input("\n⏸️  Pressione ENTER para continuar...")


def teste_4_rag_inteligente():
    """Teste 4: RAG inteligente com perguntas"""
    print("\n" + "="*70)
    print("🧪 TESTE 4: RAG Inteligente - Perguntas e Respostas")
    print("="*70)
    
    rag = get_rag_inteligente()
    
    perguntas = [
        "O que o CESPE mais cobra em Tecnologia?",
        "Como estudar para CESPE em Tecnologia?",
        "Qual a dificuldade do CESPE em Tecnologia?",
        "Quanto tempo preciso estudar para CESPE em Tecnologia?"
    ]
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n{'─'*70}")
        print(f"❓ Pergunta {i}: {pergunta}")
        print(f"{'─'*70}\n")
        
        try:
            resposta = rag.responder(pergunta, usar_ollama=False)
            print(resposta)
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        if i < len(perguntas):
            input("\n⏸️  Pressione ENTER para próxima pergunta...")


def teste_5_comparacao_bancas():
    """Teste 5: Comparar diferentes bancas na mesma área"""
    print("\n" + "="*70)
    print("🧪 TESTE 5: Comparação de Bancas - Tecnologia")
    print("="*70)
    
    analyzer = get_banca_area_analyzer()
    
    bancas = ["cebraspe", "fcc", "fgv"]
    area = "Tecnologia"
    
    print(f"\n📊 Comparando bancas na área de {area}...\n")
    
    resultados = {}
    
    for banca in bancas:
        try:
            if banca not in analyzer.perfis or area not in analyzer.perfis.get(banca, {}):
                print(f"🔄 Processando {banca.upper()}...")
                analyzer.processar_banca_area(banca, area)
            
            perfil = analyzer.perfis.get(banca, {}).get(area)
            
            if perfil and "erro" not in perfil:
                resultados[banca] = perfil
                print(f"✅ {banca.upper()}: {perfil['total_questoes']} questões")
        
        except Exception as e:
            print(f"⚠️  {banca.upper()}: Sem dados ({e})")
    
    # Comparar
    if len(resultados) >= 2:
        print(f"\n{'='*70}")
        print(f"📊 COMPARATIVO - {area}")
        print(f"{'='*70}\n")
        
        for banca, perfil in resultados.items():
            print(f"\n🏛️  **{banca.upper()}**")
            
            # Top disciplina
            disciplinas = perfil.get("distribuicao_disciplinas", {})
            if disciplinas:
                top = list(disciplinas.items())[0]
                print(f"   Disciplina #1: {top[0]} ({top[1]['percentual']:.1f}%)")
            
            # Dificuldade predominante
            dificuldades = perfil.get("distribuicao_dificuldade", {})
            if dificuldades:
                dif = max(dificuldades.items(), key=lambda x: x[1]['percentual'])
                print(f"   Dificuldade: {dif[0]} ({dif[1]['percentual']:.1f}%)")
            
            # Tipo de questão
            tipos = perfil.get("distribuicao_tipos", {})
            if tipos:
                tipo = max(tipos.items(), key=lambda x: x[1]['percentual'])
                print(f"   Tipo principal: {tipo[0]}")
    
    else:
        print("\n⚠️  Precisa de pelo menos 2 bancas com dados para comparar")
        print("💡 Adicione mais PDFs nas pastas das bancas")
    
    input("\n⏸️  Pressione ENTER para continuar...")


def teste_6_processar_todas():
    """Teste 6: Processar todas as bancas e áreas"""
    print("\n" + "="*70)
    print("🧪 TESTE 6: Processar TODAS as Bancas e Áreas")
    print("="*70)
    
    analyzer = get_banca_area_analyzer()
    
    print("\n🚀 Iniciando processamento completo...")
    print("   (Pode demorar alguns minutos dependendo do número de PDFs)\n")
    
    confirmacao = input("❓ Tem certeza? (s/n): ")
    
    if confirmacao.lower() != 's':
        print("❌ Cancelado")
        return
    
    resultado = analyzer.processar_todas_bancas_areas()
    
    print(f"\n✅ Processamento concluído!")
    print(f"\n📊 Resumo:")
    print(f"   • Status: {resultado['status']}")
    print(f"   • Total de perfis gerados: {resultado['total_perfis']}")
    
    print(f"\n📂 Detalhes por banca:")
    for banca, areas in resultado['resultados'].items():
        print(f"\n   {banca.upper()}:")
        for area, status in areas.items():
            icone = "✅" if status['status'] == "sucesso" else "❌"
            questoes = status.get('questoes', 0)
            print(f"      {icone} {area}: {questoes} questões")


def teste_interativo():
    """Teste interativo - usuário faz perguntas"""
    print("\n" + "="*70)
    print("💬 MODO INTERATIVO - Faça suas perguntas!")
    print("="*70)
    
    rag = get_rag_inteligente()
    
    print("\n💡 Exemplos de perguntas:")
    print("   • O que o CESPE mais cobra em Tecnologia?")
    print("   • Como estudar para FCC em Jurídica?")
    print("   • Qual a dificuldade da FGV em Saúde?")
    print("   • (digite 'sair' para voltar ao menu)\n")
    
    while True:
        pergunta = input("\n❓ Sua pergunta: ").strip()
        
        if not pergunta:
            continue
        
        if pergunta.lower() in ['sair', 'exit', 'quit']:
            break
        
        print(f"\n{'─'*70}\n")
        
        try:
            resposta = rag.responder(pergunta, usar_ollama=False)
            print(resposta)
        except Exception as e:
            print(f"❌ Erro: {e}")


def menu_principal():
    """Menu principal"""
    
    while True:
        print("\n" + "="*70)
        print("🎯 SISTEMA DE ANÁLISE DE BANCAS POR ÁREA - ConcursAI")
        print("="*70)
        print("\nEscolha um teste:")
        print("\n1️⃣  Organizar PDFs por área (automático)")
        print("2️⃣  Processar CESPE - Tecnologia")
        print("3️⃣  Consultar perfil gerado")
        print("4️⃣  RAG Inteligente - Perguntas e Respostas")
        print("5️⃣  Comparar bancas na mesma área")
        print("6️⃣  Processar TODAS as bancas (demorado)")
        print("7️⃣  Modo Interativo (faça suas perguntas)")
        print("\n0️⃣  Sair")
        
        escolha = input("\n➡️  Digite o número: ").strip()
        
        if escolha == '1':
            teste_1_organizacao_pdfs()
        elif escolha == '2':
            teste_2_processar_banca_area()
        elif escolha == '3':
            teste_3_consulta_perfil()
        elif escolha == '4':
            teste_4_rag_inteligente()
        elif escolha == '5':
            teste_5_comparacao_bancas()
        elif escolha == '6':
            teste_6_processar_todas()
        elif escolha == '7':
            teste_interativo()
        elif escolha == '0':
            print("\n👋 Até logo!")
            break
        else:
            print("\n❌ Opção inválida!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 INICIANDO TESTES DO SISTEMA")
    print("="*70)
    
    print("\n📋 Áreas de Conhecimento Suportadas:")
    for area in AREAS_CONHECIMENTO.keys():
        print(f"   • {area}")
    
    print("\n🏛️  Bancas Suportadas:")
    print("   • CESPE/CEBRASPE")
    print("   • FCC")
    print("   • FGV")
    print("   • VUNESP")
    
    input("\n⏸️  Pressione ENTER para começar...")
    
    menu_principal()
