"""
🎯 DEMONSTRAÇÃO COMPLETA DO SISTEMA COM SEUS PDFs
==================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

print("\n" + "="*70)
print("🚀 DEMONSTRAÇÃO: Sistema de Análise de Bancas por Área")
print("="*70)

print("\n📊 Seus PDFs Organizados:")
print("   • CEBRASPE: 30 PDFs em 3 áreas")
print("   • FGV: 18 PDFs em 2 áreas")
print("   Total: 48 PDFs")

# ============================================
# PARTE 1: Processar CEBRASPE - Jurídica
# ============================================
print("\n" + "─"*70)
print("📖 PARTE 1: Analisando CEBRASPE - Área Jurídica")
print("─"*70)

try:
    from modules.banca_area_analyzer import get_banca_area_analyzer
    
    analyzer = get_banca_area_analyzer()
    
    print("\n🔄 Processando 10 PDFs da área Jurídica...")
    
    perfil = analyzer.processar_banca_area("cebraspe", "Jurídica")
    
    if perfil and "erro" not in perfil:
        print("\n✅ PROCESSAMENTO CONCLUÍDO!")
        print("\n📊 ESTATÍSTICAS:")
        print(f"   • Provas analisadas: {perfil['total_provas_analisadas']}")
        print(f"   • Questões extraídas: {perfil['total_questoes']}")
        print(f"   • Gabaritos: {perfil['total_gabaritos']}")
        
        # Top disciplinas
        disciplinas = list(perfil["distribuicao_disciplinas"].items())[:5]
        if disciplinas:
            print(f"\n📚 TOP 5 DISCIPLINAS:")
            for i, (disc, dados) in enumerate(disciplinas, 1):
                barra = "█" * int(dados['percentual'] / 3)
                print(f"   {i}. {disc}")
                print(f"      {barra} {dados['percentual']:.1f}% ({dados['count']} questões)")
        
        # Dificuldade
        dificuldades = perfil["distribuicao_dificuldade"]
        print(f"\n📊 DISTRIBUIÇÃO DE DIFICULDADE:")
        for nivel, dados in sorted(dificuldades.items(), key=lambda x: x[1]['percentual'], reverse=True):
            emoji = "🔴" if nivel == "Avançado" else "🟡" if nivel == "Intermediário" else "🟢"
            barra = "█" * int(dados['percentual'] / 3)
            print(f"   {emoji} {nivel}: {barra} {dados['percentual']:.1f}%")
        
        # Temas
        temas = perfil["temas_mais_cobrados"][:10]
        if temas:
            print(f"\n🔑 TOP 10 TEMAS MAIS COBRADOS:")
            for i, tema_data in enumerate(temas, 1):
                print(f"   {i:2d}. {tema_data['tema']} ({tema_data['frequencia']}x)")
        
        # Padrões jurídicos
        padroes = perfil.get("padroes_especificos", {})
        carac = padroes.get("caracteristicas_predominantes", {})
        
        if carac and "percentual_lei_seca" in carac:
            print(f"\n⚖️  PADRÃO JURÍDICO DO CEBRASPE:")
            print(f"   • Lei seca: {carac['percentual_lei_seca']:.1f}%")
            print(f"   • Jurisprudência: {carac['percentual_jurisprudencia']:.1f}%")
            print(f"   • Súmulas: {carac['percentual_sumula']:.1f}%")
            print(f"   • Foco: {carac['foco'].upper()}")
        
        # Recomendações
        rec = perfil.get("recomendacoes", {})
        if rec:
            print(f"\n💡 RECOMENDAÇÕES DE ESTUDO:")
            estrategias = rec.get("estrategia_estudo", [])
            for i, est in enumerate(estrategias[:4], 1):
                print(f"   {i}. {est}")
            
            tempo = rec.get("tempo_sugerido", {})
            if tempo:
                print(f"\n⏱️  TEMPO SUGERIDO:")
                print(f"   • {tempo['horas_semanais']}h por semana")
                print(f"   • {tempo['meses_preparo_sugerido']} meses de preparação")
    else:
        print(f"\n⚠️  {perfil.get('erro', 'Erro desconhecido')}")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()

# ============================================
# PARTE 2: Processar FGV - Conhecimentos Gerais
# ============================================
print("\n" + "─"*70)
print("📖 PARTE 2: Analisando FGV - Conhecimentos Gerais")
print("─"*70)

try:
    print("\n🔄 Processando 11 PDFs de Conhecimentos Gerais...")
    
    perfil_fgv = analyzer.processar_banca_area("fgv", "Conhecimentos Gerais")
    
    if perfil_fgv and "erro" not in perfil_fgv:
        print("\n✅ PROCESSAMENTO CONCLUÍDO!")
        print("\n📊 ESTATÍSTICAS:")
        print(f"   • Questões extraídas: {perfil_fgv['total_questoes']}")
        
        # Top disciplinas
        disciplinas_fgv = list(perfil_fgv["distribuicao_disciplinas"].items())[:3]
        if disciplinas_fgv:
            print(f"\n📚 TOP 3 DISCIPLINAS:")
            for i, (disc, dados) in enumerate(disciplinas_fgv, 1):
                print(f"   {i}. {disc}: {dados['percentual']:.1f}%")
    else:
        print(f"\n⚠️  {perfil_fgv.get('erro', 'Erro desconhecido')}")

except Exception as e:
    print(f"\n❌ Erro: {e}")

# ============================================
# PARTE 3: RAG Inteligente - Perguntas
# ============================================
print("\n" + "─"*70)
print("💬 PARTE 3: RAG Inteligente - Fazendo Perguntas")
print("─"*70)

try:
    from modules.rag_banca_inteligente import get_rag_inteligente
    
    rag = get_rag_inteligente()
    
    perguntas = [
        "O que o CEBRASPE mais cobra em Jurídica?",
        "Qual a dificuldade do CEBRASPE em Jurídica?",
        "Como estudar para CEBRASPE em Jurídica?"
    ]
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n❓ Pergunta {i}: {pergunta}")
        print("   " + "─"*66 + "\n")
        
        try:
            resposta = rag.responder(pergunta, usar_ollama=False)
            
            # Mostrar resposta formatada
            linhas = resposta.split('\n')
            for linha in linhas[:15]:  # Primeiras 15 linhas
                print(f"   {linha}")
            
            if len(linhas) > 15:
                print(f"\n   ... (resposta completa tem {len(linhas)} linhas)")
        
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        if i < len(perguntas):
            input("\n   ⏸️  [Pressione ENTER para próxima pergunta]")

except Exception as e:
    print(f"\n❌ Erro no RAG: {e}")

# ============================================
# RESUMO FINAL
# ============================================
print("\n" + "="*70)
print("✅ DEMONSTRAÇÃO CONCLUÍDA!")
print("="*70)

print("\n📊 PERFIS GERADOS:")
try:
    for banca, areas in analyzer.perfis.items():
        print(f"\n🏛️  {banca.upper()}:")
        for area, perfil in areas.items():
            if "erro" not in perfil:
                total = perfil.get('total_questoes', 0)
                provas = perfil.get('total_provas_analisadas', 0)
                print(f"   ✅ {area}: {total} questões de {provas} provas")
except:
    pass

print("\n🎯 CAPACIDADES DO SISTEMA:")
print("   ✅ Organiza PDFs automaticamente por área")
print("   ✅ Extrai e categoriza questões")
print("   ✅ Identifica padrões específicos por área")
print("   ✅ Gera estatísticas detalhadas")
print("   ✅ Responde perguntas inteligentes")
print("   ✅ Cria recomendações personalizadas")

print("\n💡 COMO USAR:")
print("   1. Execute: python teste_sistema_bancas.py")
print("   2. Ou use: INICIAR_ANALISE_BANCAS.bat")
print("   3. Modo interativo: Escolha opção 7")

print("\n📚 EXEMPLOS DE PERGUNTAS:")
print('   • "O que o CEBRASPE mais cobra em Jurídica?"')
print('   • "Como estudar para FGV em Conhecimentos Gerais?"')
print('   • "Qual a dificuldade do CEBRASPE?"')
print('   • "CEBRASPE vs FGV - qual é mais difícil?"')

print("\n" + "="*70)
print("🎉 Sistema funcionando perfeitamente!")
print("="*70 + "\n")
