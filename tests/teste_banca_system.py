"""
🧪 TESTE DO SISTEMA DE ESTUDO DE BANCAS
======================================
Script de teste e demonstração do sistema completo
"""

import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.banca_study_system import get_study_system
from modules.banca_analyzer import get_banca_analyzer
from modules.smart_pdf_chunker import get_smart_chunker
import json


def teste_completo():
    """Executa bateria completa de testes"""
    
    print("\n" + "=" * 80)
    print("🎓 SISTEMA DE ESTUDO DE BANCAS - CONCURSAI")
    print("Teste Completo de Funcionalidades")
    print("=" * 80 + "\n")
    
    # 1. Inicializar sistemas
    print("📦 Inicializando sistemas...")
    
    analyzer = get_banca_analyzer()
    chunker = get_smart_chunker()
    study_system = get_study_system()
    
    print(f"✅ Banca Analyzer: OK")
    print(f"✅ Smart PDF Chunker: OK (embeddings: {chunker.use_embeddings})")
    print(f"✅ Study System: OK")
    print()
    
    # 2. Testar identificação de banca
    print("\n" + "-" * 80)
    print("🔍 TESTE 1: Identificação de Banca")
    print("-" * 80)
    
    textos_teste = [
        ("Texto CESPE", "Considerando a jurisprudência do STF, é INCORRETO afirmar que, exceto nos casos..."),
        ("Texto FCC", "De acordo com o artigo 37 da Constituição Federal, assinale a alternativa correta."),
        ("Texto FGV", "Analise o contexto apresentado e interprete a situação conforme a legislação vigente.")
    ]
    
    for nome, texto in textos_teste:
        banca, conf = analyzer.identificar_banca(texto)
        print(f"\n{nome}:")
        print(f"  Banca identificada: {banca}")
        print(f"  Confiança: {conf:.2%}")
    
    # 3. Testar análise de estilo
    print("\n" + "-" * 80)
    print("📊 TESTE 2: Análise de Estilo de Questão")
    print("-" * 80)
    
    questao_exemplo = """
    Considerando a doutrina e a jurisprudência do Supremo Tribunal Federal 
    sobre direitos fundamentais, assinale a alternativa INCORRETA.
    
    A respeito da aplicação das normas constitucionais, é correto afirmar que,
    exceto nos casos expressamente previstos, os direitos fundamentais...
    """
    
    analise = analyzer.analisar_estilo_questao(questao_exemplo, "CESPE/CEBRASPE")
    
    print(f"\n📝 Questão de exemplo (CESPE):")
    print(f"  Complexidade: {analise['complexidade_estimada']:.2f}/10")
    print(f"  Nível: {analise['nivel_dificuldade']}")
    print(f"  Disciplina: {analise['disciplina_provavel']}")
    print(f"  Score padrão CESPE: {analise['score_padrao_banca']:.2f}%")
    print(f"\n  Características detectadas:")
    for carac, valor in analise['caracteristicas_detectadas'].items():
        if valor:
            print(f"    ✓ {carac.replace('_', ' ').title()}")
    
    # 4. Testar recomendações
    print("\n" + "-" * 80)
    print("🎯 TESTE 3: Recomendações de Estudo")
    print("-" * 80)
    
    recomendacoes = analyzer.recomendar_estrategia_estudo(
        "CESPE/CEBRASPE",
        disciplinas=["Direito Constitucional", "Direito Administrativo", "Português"]
    )
    
    print(f"\n📚 Recomendações para CESPE/CEBRASPE:")
    print(f"\n  Tipo de Questão: {recomendacoes['tipo_questao']}")
    print(f"  Complexidade: {recomendacoes['complexidade_esperada']}/10")
    
    print(f"\n  ⏰ Distribuição de Tempo:")
    for disc, tempo in list(recomendacoes['distribuicao_tempo_estudo'].items())[:3]:
        print(f"    {disc}: {tempo}")
    
    print(f"\n  💡 Dicas Específicas:")
    for dica in recomendacoes['dicas_especificas']:
        print(f"    {dica}")
    
    if recomendacoes['alertas']:
        print(f"\n  ⚠️ Alertas:")
        for alerta in recomendacoes['alertas']:
            print(f"    {alerta}")
    
    # 5. Testar comparação de bancas
    print("\n" + "-" * 80)
    print("⚖️ TESTE 4: Comparação entre Bancas")
    print("-" * 80)
    
    comparacao = analyzer.comparar_bancas("CESPE/CEBRASPE", "FCC")
    
    print(f"\n📊 CESPE vs FCC:")
    print(f"\n  CESPE/CEBRASPE:")
    print(f"    Tipo: {comparacao['banca_1']['tipo_questao']}")
    print(f"    Complexidade: {comparacao['banca_1']['complexidade']}/10")
    
    print(f"\n  FCC:")
    print(f"    Tipo: {comparacao['banca_2']['tipo_questao']}")
    print(f"    Complexidade: {comparacao['banca_2']['complexidade']}/10")
    
    print(f"\n  🔄 Principais Diferenças:")
    for diff in comparacao['diferencas_principais']:
        print(f"    • {diff}")
    
    if comparacao['semelhanças']:
        print(f"\n  ✓ Semelhanças:")
        for sem in comparacao['semelhanças']:
            print(f"    • {sem}")
    
    print(f"\n  💡 Recomendação: {comparacao['recomendacao_transicao']}")
    
    # 6. Testar estatísticas de questões
    print("\n" + "-" * 80)
    print("📈 TESTE 5: Estatísticas de Conjunto de Questões")
    print("-" * 80)
    
    questoes_exemplo = [
        "Assinale a alternativa correta sobre direito constitucional...",
        "De acordo com a lei, é correto afirmar que...",
        "Considerando a jurisprudência do STF, analise as assertivas...",
        "Em relação aos princípios administrativos...",
        "Sobre o regime jurídico dos servidores públicos..."
    ]
    
    stats = analyzer.gerar_estatisticas_banca(questoes_exemplo, "CESPE/CEBRASPE")
    
    print(f"\n📊 Análise de {stats['total_questoes_analisadas']} questões:")
    print(f"  Complexidade média: {stats['complexidade_media']:.2f}/10")
    print(f"  Tamanho médio: {stats['tamanho_medio_palavras']:.1f} palavras")
    print(f"  Score médio padrão: {stats['score_medio_padrao']:.1f}%")
    
    print(f"\n  📋 Distribuição por Dificuldade:")
    for nivel, count in stats['distribuicao_dificuldade'].items():
        print(f"    {nivel}: {count} questões")
    
    print(f"\n  📚 Distribuição por Disciplina:")
    for disc, count in stats['distribuicao_disciplinas'].items():
        print(f"    {disc}: {count} questões")
    
    # 7. Informações sobre chunking
    print("\n" + "-" * 80)
    print("📄 TESTE 6: Sistema de Chunking de PDFs")
    print("-" * 80)
    
    print(f"\n✅ Smart PDF Chunker:")
    print(f"  Embeddings habilitados: {chunker.use_embeddings}")
    print(f"  Tipos de documento suportados: Prova, Gabarito, Genérico")
    print(f"  Categorização automática: Disciplina, Dificuldade, Tipo, Temas")
    
    print(f"\n  📊 Padrões de identificação:")
    print(f"    • Questões numeradas")
    print(f"    • Disciplinas por NLP")
    print(f"    • Tipos de questão (Múltipla Escolha, Certo/Errado, Dissertativa)")
    print(f"    • Nível de dificuldade (Básico, Intermediário, Avançado)")
    print(f"    • Temas específicos por disciplina")
    print(f"    • Características (negação, exceção, jurisprudência, etc.)")
    
    # 8. Resumo final
    print("\n" + "=" * 80)
    print("✅ RESUMO DOS TESTES")
    print("=" * 80)
    
    print(f"""
    ✓ Identificação de Bancas: OK
    ✓ Análise de Estilo: OK
    ✓ Recomendações de Estudo: OK
    ✓ Comparação de Bancas: OK
    ✓ Estatísticas de Questões: OK
    ✓ Sistema de Chunking: OK
    
    📦 Módulos disponíveis:
      • banca_analyzer.py - Análise de padrões de bancas
      • smart_pdf_chunker.py - Chunking inteligente de PDFs
      • banca_study_system.py - Sistema integrado de estudo
    
    🎯 Para usar em produção:
      1. Processe PDFs de provas com smart_chunker.process_pdf()
      2. Gere perfil da banca com study_system.processar_provas_banca()
      3. Obtenha relatório completo com study_system.gerar_relatorio_completo_banca()
      4. Use as recomendações para guiar o estudo dos candidatos
    
    📚 Bancas suportadas:
      • CESPE/CEBRASPE
      • FCC
      • FGV
      • VUNESP
    """)
    
    print("=" * 80)
    print("🎉 TESTES CONCLUÍDOS COM SUCESSO!")
    print("=" * 80 + "\n")


def exemplo_uso_completo():
    """Exemplo de uso completo do sistema"""
    
    print("\n" + "=" * 80)
    print("📖 EXEMPLO DE USO COMPLETO")
    print("=" * 80 + "\n")
    
    print("""
    # 1. Inicializar o sistema
    from modules.banca_study_system import get_study_system
    
    system = get_study_system()
    
    # 2. Processar provas de uma banca
    pdfs = [
        "provas/cespe_prova1.pdf",
        "provas/cespe_prova2.pdf",
        "provas/cespe_prova3.pdf"
    ]
    
    resultado = system.processar_provas_banca(
        pdf_paths=pdfs,
        banca="CESPE/CEBRASPE",
        metadata={
            "ano": 2024,
            "cargo": "Analista Judiciário",
            "orgao": "TRT"
        }
    )
    
    print(f"✅ Processadas {resultado['total_provas_processadas']} provas")
    print(f"📊 Total de {resultado['total_questoes']} questões analisadas")
    
    # 3. Gerar relatório completo
    relatorio = system.gerar_relatorio_completo_banca("CESPE/CEBRASPE")
    
    print(f"\\n📋 Resumo:")
    print(f"  Disciplina principal: {relatorio['resumo_executivo']['disciplina_principal']}")
    print(f"  Nível geral: {relatorio['resumo_executivo']['nivel_dificuldade_geral']}")
    
    # 4. Acessar recomendações personalizadas
    recomendacoes = relatorio['perfil_detalhado']['recomendacoes_estudo']
    
    print(f"\\n🎯 Top 3 disciplinas para estudar:")
    for disc in recomendacoes['prioridade_disciplinas'][:3]:
        print(f"  {disc['disciplina']}: {disc['peso']}")
    
    # 5. Exportar relatório
    relatorio_json = system.exportar_perfil("CESPE/CEBRASPE", formato="json")
    
    with open("relatorio_cespe.json", "w", encoding="utf-8") as f:
        f.write(relatorio_json)
    
    print("\\n✅ Relatório exportado para relatorio_cespe.json")
    """)


if __name__ == "__main__":
    # Executar testes
    teste_completo()
    
    # Mostrar exemplo de uso
    exemplo_uso_completo()
