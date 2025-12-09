#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 CLASSIFICADOR ML DE BANCAS
==============================
Sistema de Machine Learning para classificação automática de bancas
usando ensemble de Random Forest, MLP e SVM
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re
from collections import Counter

# Scikit-learn imports
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder


class BancaClassifier:
    """
    Classificador ML de bancas examinadoras
    Usa ensemble de Random Forest, MLP e SVM para classificar questões por banca
    """
    
    def __init__(self):
        """Inicializa o classificador"""
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.8,
            strip_accents='unicode'
        )
        
        self.label_encoder = LabelEncoder()
        
        # Modelos individuais
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.mlp_model = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            activation='relu',
            max_iter=500,
            random_state=42,
            early_stopping=True
        )
        
        self.svm_model = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            probability=True,
            random_state=42
        )
        
        # Ensemble voting
        self.ensemble = VotingClassifier(
            estimators=[
                ('rf', self.rf_model),
                ('mlp', self.mlp_model),
                ('svm', self.svm_model)
            ],
            voting='soft',
            weights=[2, 1, 1]  # RF tem peso maior
        )
        
        self.is_trained = False
        self.feature_importance = None
        self.classes_ = None
        
    def extrair_features_textuais(self, texto: str) -> Dict[str, float]:
        """
        Extrai features adicionais do texto além do TF-IDF
        
        Args:
            texto: Texto da questão
            
        Returns:
            Dicionário com features
        """
        features = {}
        
        # Comprimento
        features['comprimento'] = len(texto)
        features['num_palavras'] = len(texto.split())
        
        # Complexidade
        palavras_complexas = len(re.findall(r'\b\w{12,}\b', texto))
        features['palavras_complexas'] = palavras_complexas
        
        # Estrutura
        features['num_paragrafos'] = texto.count('\n\n') + 1
        features['num_frases'] = texto.count('.') + texto.count('?') + texto.count('!')
        
        # Pontuação
        features['num_virgulas'] = texto.count(',')
        features['num_pontos_virgula'] = texto.count(';')
        features['num_dois_pontos'] = texto.count(':')
        
        # Perguntas
        features['tem_interrogacao'] = 1 if '?' in texto else 0
        features['num_interrogacoes'] = texto.count('?')
        
        # Palavras-chave por tipo de banca
        texto_lower = texto.lower()
        
        # CEBRASPE (assertivas, julgue)
        features['estilo_cebraspe'] = sum([
            'julgue' in texto_lower,
            'certo' in texto_lower or 'errado' in texto_lower,
            'assertiva' in texto_lower,
            'incorret' in texto_lower
        ])
        
        # FCC (segundo, conforme, de acordo com)
        features['estilo_fcc'] = sum([
            'segundo' in texto_lower,
            'conforme' in texto_lower,
            'de acordo com' in texto_lower,
            'nos termos' in texto_lower
        ])
        
        # FGV (analise, considere)
        features['estilo_fgv'] = sum([
            'analise' in texto_lower or 'analyse' in texto_lower,
            'considere' in texto_lower,
            'assinale' in texto_lower,
            'alternativa' in texto_lower
        ])
        
        # Termos jurídicos (indicam área)
        features['termos_juridicos'] = sum([
            'lei' in texto_lower,
            'artigo' in texto_lower,
            'código' in texto_lower,
            'jurisprudência' in texto_lower
        ])
        
        return features
    
    def preparar_dados(self, csv_path: str = "concursos_chunks.csv") -> Tuple[np.ndarray, np.ndarray]:
        """
        Carrega e prepara dados para treinamento
        
        Args:
            csv_path: Caminho para o CSV com dados
            
        Returns:
            Tupla (X, y) com features e labels
        """
        print("📊 Carregando dados...")
        
        if not Path(csv_path).exists():
            print(f"❌ Arquivo {csv_path} não encontrado")
            # Tentar arquivo alternativo
            csv_path = "concursos_questoes_respostas.csv"
            if not Path(csv_path).exists():
                raise FileNotFoundError("Nenhum arquivo de dados encontrado")
        
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"✅ {len(df)} registros carregados")
        
        # Filtrar apenas registros com banca e conteúdo
        df = df[df['banca'].notna() & df['conteudo'].notna()]
        df = df[df['conteudo'] != '']
        
        print(f"📝 {len(df)} registros válidos após filtragem")
        
        # Verificar distribuição de bancas
        print("\n📊 Distribuição de bancas:")
        distribuicao = df['banca'].value_counts()
        for banca, count in distribuicao.items():
            print(f"   {banca}: {count} questões")
        
        # Filtrar bancas com poucos exemplos (< 50)
        bancas_validas = distribuicao[distribuicao >= 50].index
        df = df[df['banca'].isin(bancas_validas)]
        
        print(f"\n✅ {len(df)} registros finais de {len(bancas_validas)} bancas")
        
        # Preparar textos e labels
        textos = df['conteudo'].values
        bancas = df['banca'].values
        
        return textos, bancas
    
    def treinar(self, textos: np.ndarray, bancas: np.ndarray, test_size: float = 0.2):
        """
        Treina o ensemble de modelos
        
        Args:
            textos: Array com textos das questões
            bancas: Array com labels das bancas
            test_size: Proporção para teste
        """
        print("\n" + "="*60)
        print("🎓 TREINAMENTO DO CLASSIFICADOR DE BANCAS")
        print("="*60)
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            textos, bancas, test_size=test_size, random_state=42, stratify=bancas
        )
        
        print(f"\n📊 Dados divididos:")
        print(f"   Treino: {len(X_train)} questões")
        print(f"   Teste: {len(X_test)} questões")
        
        # Vetorizar textos
        print("\n🔄 Vetorizando textos com TF-IDF...")
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Encode labels
        y_train_enc = self.label_encoder.fit_transform(y_train)
        y_test_enc = self.label_encoder.transform(y_test)
        
        self.classes_ = self.label_encoder.classes_
        
        print(f"✅ Vocabulário: {len(self.vectorizer.get_feature_names_out())} features")
        
        # Treinar ensemble
        print("\n🤖 Treinando ensemble (RF + MLP + SVM)...")
        self.ensemble.fit(X_train_vec, y_train_enc)
        
        print("✅ Treinamento concluído!")
        
        # Avaliar modelos individuais
        print("\n📊 Avaliação de Modelos Individuais:")
        print("-" * 60)
        
        for name, model in [('Random Forest', self.rf_model), 
                            ('MLP', self.mlp_model), 
                            ('SVM', self.svm_model)]:
            y_pred = model.predict(X_test_vec)
            acc = accuracy_score(y_test_enc, y_pred)
            print(f"   {name:20s} Acurácia: {acc:.4f} ({acc*100:.2f}%)")
        
        # Avaliar ensemble
        print("\n🎯 Avaliação do Ensemble:")
        print("-" * 60)
        y_pred_ensemble = self.ensemble.predict(X_test_vec)
        acc_ensemble = accuracy_score(y_test_enc, y_pred_ensemble)
        print(f"   Acurácia: {acc_ensemble:.4f} ({acc_ensemble*100:.2f}%)")
        
        # Cross-validation
        print("\n🔄 Validação Cruzada (5-fold):")
        cv_scores = cross_val_score(self.ensemble, X_train_vec, y_train_enc, cv=5)
        print(f"   Média: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        # Relatório detalhado
        print("\n📋 Relatório de Classificação:")
        print("-" * 60)
        y_pred_labels = self.label_encoder.inverse_transform(y_pred_ensemble)
        print(classification_report(y_test, y_pred_labels, zero_division=0))
        
        # Matriz de confusão
        print("\n📊 Matriz de Confusão:")
        cm = confusion_matrix(y_test_enc, y_pred_ensemble)
        print(cm)
        
        # Feature importance (Random Forest)
        self.feature_importance = self._calcular_feature_importance()
        
        self.is_trained = True
        
        return {
            'acuracia_ensemble': acc_ensemble,
            'acuracia_rf': accuracy_score(y_test_enc, self.rf_model.predict(X_test_vec)),
            'acuracia_mlp': accuracy_score(y_test_enc, self.mlp_model.predict(X_test_vec)),
            'acuracia_svm': accuracy_score(y_test_enc, self.svm_model.predict(X_test_vec)),
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
    
    def _calcular_feature_importance(self, top_n: int = 20) -> Dict[str, List[Tuple[str, float]]]:
        """Calcula feature importance do Random Forest"""
        feature_names = self.vectorizer.get_feature_names_out()
        importances = self.rf_model.feature_importances_
        
        # Top features globais
        indices = np.argsort(importances)[::-1][:top_n]
        top_features = [(feature_names[i], importances[i]) for i in indices]
        
        return {
            'top_features_global': top_features
        }
    
    def prever(self, texto: str) -> Dict[str, any]:
        """
        Prevê a banca de uma questão
        
        Args:
            texto: Texto da questão
            
        Returns:
            Dicionário com previsão e probabilidades
        """
        if not self.is_trained:
            raise ValueError("Modelo não treinado. Execute treinar() primeiro.")
        
        # Vetorizar
        X = self.vectorizer.transform([texto])
        
        # Prever
        y_pred = self.ensemble.predict(X)[0]
        y_proba = self.ensemble.predict_proba(X)[0]
        
        banca_prevista = self.label_encoder.inverse_transform([y_pred])[0]
        
        # Probabilidades por banca
        probabilidades = {
            banca: float(prob) 
            for banca, prob in zip(self.classes_, y_proba)
        }
        
        # Ordenar por probabilidade
        probabilidades_ordenadas = sorted(
            probabilidades.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            'banca_prevista': banca_prevista,
            'confianca': float(y_proba[y_pred]),
            'probabilidades': dict(probabilidades_ordenadas),
            'top_3': probabilidades_ordenadas[:3]
        }
    
    def salvar_modelo(self, caminho: str = "models/banca_classifier.pkl"):
        """Salva o modelo treinado"""
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        
        modelo_data = {
            'ensemble': self.ensemble,
            'vectorizer': self.vectorizer,
            'label_encoder': self.label_encoder,
            'feature_importance': self.feature_importance,
            'classes': self.classes_,
            'data_treinamento': datetime.now().isoformat()
        }
        
        joblib.dump(modelo_data, caminho)
        print(f"✅ Modelo salvo em: {caminho}")
    
    def carregar_modelo(self, caminho: str = "models/banca_classifier.pkl"):
        """Carrega modelo treinado"""
        if not Path(caminho).exists():
            raise FileNotFoundError(f"Modelo não encontrado: {caminho}")
        
        modelo_data = joblib.load(caminho)
        
        self.ensemble = modelo_data['ensemble']
        self.vectorizer = modelo_data['vectorizer']
        self.label_encoder = modelo_data['label_encoder']
        self.feature_importance = modelo_data['feature_importance']
        self.classes_ = modelo_data['classes']
        self.is_trained = True
        
        print(f"✅ Modelo carregado de: {caminho}")
        print(f"   Data de treinamento: {modelo_data['data_treinamento']}")
        print(f"   Bancas: {', '.join(self.classes_)}")


# Singleton
_banca_classifier = None

def get_banca_classifier() -> BancaClassifier:
    """Retorna instância singleton do classificador"""
    global _banca_classifier
    if _banca_classifier is None:
        _banca_classifier = BancaClassifier()
    return _banca_classifier


if __name__ == "__main__":
    print("="*60)
    print("🤖 CLASSIFICADOR ML DE BANCAS")
    print("="*60)
    
    # Criar e treinar classificador
    classifier = BancaClassifier()
    
    try:
        # Carregar dados
        textos, bancas = classifier.preparar_dados()
        
        # Treinar
        metricas = classifier.treinar(textos, bancas)
        
        # Salvar modelo
        classifier.salvar_modelo()
        
        # Teste rápido
        print("\n" + "="*60)
        print("🧪 TESTE DE PREVISÃO")
        print("="*60)
        
        texto_teste = """
        Julgue o item a seguir, relativo à administração pública.
        A impessoalidade é um dos princípios constitucionais.
        """
        
        resultado = classifier.prever(texto_teste)
        print(f"\n📝 Texto: {texto_teste[:100]}...")
        print(f"\n🎯 Banca prevista: {resultado['banca_prevista']}")
        print(f"   Confiança: {resultado['confianca']:.2%}")
        print(f"\n📊 Top 3 probabilidades:")
        for banca, prob in resultado['top_3']:
            print(f"   {banca}: {prob:.2%}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\n💡 Certifique-se de ter dados em 'concursos_chunks.csv' ou 'concursos_questoes_respostas.csv'")
