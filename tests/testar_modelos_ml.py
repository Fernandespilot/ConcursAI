#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTE DOS MODELOS ML
========================
Testa classificador de bancas e preditor de temas
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.ml_models import get_banca_classifier, get_theme_predictor


def testar_classificador():
    """Testa o classificador de bancas"""
    print("=" * 70)
    print("🧪 TESTE DO CLASSIFICADOR DE BANCAS")
    print("=" * 70)
    print()
    
    classifier = get_banca_classifier()
    
    # Tentar carregar modelo treinado
    try:
        classifier.carregar_modelo("models/banca_classifier.pkl")
        print("✅ Modelo carregado com sucesso!")
        print()
    except FileNotFoundError:
        print("⚠️ Modelo não encontrado. Execute TREINAR_MODELOS_ML.bat primeiro")
        return
    
    # Questões de teste
    questoes_teste = [
        {
            'texto': """
            Julgue o item a seguir, relativo à administração pública.
            A impessoalidade é um dos princípios constitucionais que regem
            a administração pública, estando expressamente previsto no 
            artigo 37 da Constituição Federal.
            """,
            'banca_esperada': 'CEBRASPE'
        },
        {
            'texto': """
            Segundo a doutrina majoritária, os princípios da administração
            pública podem ser explícitos ou implícitos. Nos termos da
            Constituição Federal, são princípios explícitos:
            a) Legalidade, impessoalidade e moralidade
            b) Publicidade, eficiência e supremacia do interesse público
            c) Todos os anteriores
            d) Nenhuma das anteriores
            """,
            'banca_esperada': 'FCC'
        },
        {
            'texto': """
            Analise as afirmativas a seguir sobre os princípios que regem
            a administração pública e assinale a alternativa correta.
            I. O princípio da legalidade...
            II. O princípio da moralidade...
            III. O princípio da impessoalidade...
            """,
            'banca_esperada': 'FGV'
        }
    ]
    
    print("📝 Testando previsões:")
    print("-" * 70)
    
    acertos = 0
    total = len(questoes_teste)
    
    for i, questao in enumerate(questoes_teste, 1):
        print(f"\n{i}. Questão:")
        print(f"   {questao['texto'][:80].strip()}...")
        print(f"   Banca esperada: {questao['banca_esperada']}")
        
        resultado = classifier.prever(questao['texto'])
        
        print(f"   🎯 Previsão: {resultado['banca_prevista']} ({resultado['confianca']:.1%})")
        
        if resultado['banca_prevista'] == questao['banca_esperada']:
            print("   ✅ ACERTO!")
            acertos += 1
        else:
            print("   ❌ ERRO")
        
        print(f"   📊 Top 3:")
        for banca, prob in resultado['top_3']:
            print(f"      {banca}: {prob:.1%}")
    
    print()
    print("=" * 70)
    print(f"📊 RESULTADO: {acertos}/{total} acertos ({acertos/total:.1%})")
    print("=" * 70)
    print()


def testar_preditor():
    """Testa o preditor de temas"""
    print("=" * 70)
    print("🧪 TESTE DO PREDITOR DE TEMAS")
    print("=" * 70)
    print()
    
    predictor = get_theme_predictor()
    
    # Testar para cada banca
    bancas = ['CEBRASPE', 'FGV', 'FCC']
    temas_teste = [
        'principios_adm',
        'direitos_fundamentais',
        'concordancia',
        'logica_proposicional'
    ]
    
    for banca in bancas:
        print(f"\n📊 ANÁLISE: {banca}")
        print("-" * 70)
        
        # Identificar temas emergentes
        try:
            emergentes = predictor.identificar_temas_emergentes(banca)
            
            if emergentes:
                print(f"\n🔥 Top 3 Temas Emergentes:")
                for i, tema_info in enumerate(emergentes[:3], 1):
                    print(f"   {i}. {tema_info['tema']}: +{tema_info['taxa_crescimento']:.1%}")
            else:
                print("   ⚠️ Nenhum tema emergente identificado")
        except Exception as e:
            print(f"   ⚠️ Erro na análise: {e}")
        
        # Prever alguns temas
        print(f"\n📈 Previsões de Frequência:")
        for tema in temas_teste[:2]:  # Apenas 2 para não ficar muito longo
            try:
                previsao = predictor.prever_frequencia(tema, banca, anos_futuros=1)
                
                if previsao.get('status') == 'sem_dados':
                    print(f"   • {tema}: Sem dados")
                else:
                    media_hist = previsao['historico']['media_historica']
                    tendencia = previsao['tendencia']['tipo']
                    print(f"   • {tema}: {media_hist:.1f}/ano (tendência {tendencia})")
            except Exception as e:
                print(f"   • {tema}: Erro - {e}")
        
        print()
    
    print("=" * 70)
    print("✅ TESTE CONCLUÍDO")
    print("=" * 70)
    print()


def main():
    """Executa todos os testes"""
    print("\n" + "🚀 TESTE COMPLETO DOS MODELOS ML".center(70))
    print()
    
    try:
        # Teste 1: Classificador
        testar_classificador()
        
        # Teste 2: Preditor
        testar_preditor()
        
        print("🎉 TODOS OS TESTES CONCLUÍDOS!")
        print()
        print("💡 Dicas:")
        print("   • Se o classificador não funcionou, execute TREINAR_MODELOS_ML.bat")
        print("   • Se o preditor não tem dados, execute PROCESSAR_QUESTOES_GABARITOS.bat")
        print()
        
    except Exception as e:
        print(f"\n❌ Erro nos testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
