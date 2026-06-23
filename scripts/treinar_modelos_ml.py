#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎓 SCRIPT DE TREINAMENTO COMPLETO
==================================
Treina classificador de bancas e preditor de temas
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from modules.ml_models.banca_classifier import BancaClassifier
from modules.ml_models.theme_predictor import ThemePredictor


def main():
    """Executa treinamento completo"""
    print("=" * 70)
    print("🎓 TREINAMENTO DE MODELOS ML - ConcursAI")
    print("=" * 70)
    print()
    
    # 1. CLASSIFICADOR DE BANCAS
    print("📍 ETAPA 1/2: CLASSIFICADOR DE BANCAS")
    print("-" * 70)
    
    try:
        classifier = BancaClassifier()
        
        # Preparar dados
        print("\n🔄 Preparando dados...")
        textos, bancas = classifier.preparar_dados()
        
        # Treinar
        print("\n🎓 Iniciando treinamento...")
        metricas = classifier.treinar(textos, bancas)
        
        # Salvar modelo
        print("\n💾 Salvando modelo...")
        classifier.salvar_modelo("models/banca_classifier.pkl")
        
        print("\n✅ CLASSIFICADOR TREINADO COM SUCESSO!")
        print(f"   Acurácia Ensemble: {metricas['acuracia_ensemble']:.2%}")
        print(f"   Acurácia Random Forest: {metricas['acuracia_rf']:.2%}")
        print(f"   Acurácia MLP: {metricas['acuracia_mlp']:.2%}")
        print(f"   Acurácia SVM: {metricas['acuracia_svm']:.2%}")
        
        # Teste rápido
        print("\n🧪 TESTE DE PREVISÃO:")
        print("-" * 70)
        
        textos_teste = [
            "Julgue o item a seguir. A impessoalidade é um princípio constitucional.",
            "Segundo a Constituição Federal, compete à União legislar sobre...",
            "Analise as afirmativas sobre direito administrativo e assinale a correta."
        ]
        
        for i, texto in enumerate(textos_teste, 1):
            resultado = classifier.prever(texto)
            print(f"\n{i}. Texto: {texto[:60]}...")
            print(f"   🎯 Banca: {resultado['banca_prevista']} ({resultado['confianca']:.1%})")
            print(f"   📊 Top 3:")
            for banca, prob in resultado['top_3']:
                print(f"      {banca}: {prob:.1%}")
        
    except Exception as e:
        print(f"\n❌ Erro no classificador: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    
    # 2. PREDITOR DE TEMAS
    print("\n📍 ETAPA 2/2: PREDITOR DE TEMAS")
    print("-" * 70)
    
    try:
        predictor = ThemePredictor()
        
        # Gerar relatórios para cada banca
        bancas = ['CEBRASPE', 'FGV', 'FCC']
        
        for banca in bancas:
            print(f"\n🔍 Analisando {banca}...")
            
            relatorio = predictor.gerar_relatorio_tendencias(
                banca=banca,
                output_path=f"relatorios/tendencias_{banca.lower()}.json"
            )
            
            print(f"✅ Relatório gerado: relatorios/tendencias_{banca.lower()}.json")
        
        # Teste de previsão
        print("\n🧪 TESTE DE PREVISÕES:")
        print("-" * 70)
        
        temas_teste = [
            ('CEBRASPE', 'principios_adm'),
            ('FGV', 'direitos_fundamentais'),
            ('FCC', 'concordancia')
        ]
        
        for banca, tema in temas_teste:
            print(f"\n📈 {banca} - {tema}:")
            previsao = predictor.prever_frequencia(tema, banca, anos_futuros=2)
            
            if previsao.get('status') == 'sem_dados':
                print(f"   ⚠️ {previsao['mensagem']}")
            else:
                print(f"   📊 Média histórica: {previsao['historico']['media_historica']:.1f}")
                print(f"   📈 Tendência: {previsao['tendencia']['tipo']}")
                print(f"   {previsao['recomendacao']}")
        
        print("\n✅ PREDITOR CONFIGURADO COM SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ Erro no preditor: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🎉 TREINAMENTO COMPLETO FINALIZADO!")
    print("=" * 70)
    print()
    print("📂 Arquivos gerados:")
    print("   • models/banca_classifier.pkl")
    print("   • relatorios/tendencias_cebraspe.json")
    print("   • relatorios/tendencias_fgv.json")
    print("   • relatorios/tendencias_fcc.json")
    print()
    print("🚀 Modelos prontos para uso!")
    print()


if __name__ == "__main__":
    main()
