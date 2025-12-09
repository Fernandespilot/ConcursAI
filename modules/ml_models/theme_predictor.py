#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 PREDITOR ML DE TEMAS
========================
Sistema de Machine Learning para predição de temas e tendências
baseado em análise temporal de questões
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re
from collections import Counter, defaultdict

# Scikit-learn imports
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error


class ThemePredictor:
    """
    Preditor de temas e tendências
    Analisa histórico temporal de questões para prever frequência futura
    """
    
    def __init__(self):
        """Inicializa o preditor"""
        self.scaler = StandardScaler()
        
        # Modelos de regressão
        self.lr_model = LinearRegression()
        self.rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.gb_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        
        self.is_trained = False
        self.temas_disponiveis = []
        self.historico_temas = {}
        
    def extrair_temas(self, texto: str) -> List[str]:
        """
        Extrai temas/palavras-chave do texto
        
        Args:
            texto: Texto da questão
            
        Returns:
            Lista de temas identificados
        """
        texto_lower = texto.lower()
        
        # Dicionário de temas por área
        temas_conhecidos = {
            # Direito Administrativo
            'principios_adm': ['princípio', 'impessoalidade', 'moralidade', 'legalidade', 'publicidade'],
            'atos_administrativos': ['ato administrativo', 'requisitos', 'atributos', 'vinculado', 'discricionário'],
            'licitacao': ['licitação', 'pregão', 'tomada de preços', 'concorrência', 'dispensa'],
            'contratos': ['contrato administrativo', 'rescisão', 'alteração contratual'],
            'servidores': ['servidor público', 'estabilidade', 'cargo', 'emprego público'],
            'responsabilidade': ['responsabilidade civil', 'dano', 'indenização'],
            'controle': ['controle da administração', 'tribunal de contas', 'fiscalização'],
            
            # Direito Constitucional
            'direitos_fundamentais': ['direitos fundamentais', 'garantias', 'liberdade', 'igualdade'],
            'organizacao_estado': ['federação', 'união', 'estados', 'municípios', 'competência'],
            'poder_executivo': ['presidente', 'governador', 'prefeito', 'atribuições'],
            'poder_legislativo': ['congresso', 'senado', 'câmara', 'deputado', 'senador'],
            'poder_judiciario': ['supremo', 'stf', 'stj', 'juiz', 'tribunal'],
            
            # Língua Portuguesa
            'concordancia': ['concordância', 'verbo', 'sujeito', 'plural', 'singular'],
            'regencia': ['regência', 'preposição', 'complemento'],
            'crase': ['crase', 'acento grave'],
            'pontuacao': ['pontuação', 'vírgula', 'ponto', 'dois pontos'],
            'interpretacao': ['interpretação', 'inferir', 'deduzir', 'texto'],
            
            # Raciocínio Lógico
            'logica_proposicional': ['proposição', 'conectivo', 'tabela verdade', 'equivalência'],
            'logica_argumentacao': ['argumento', 'premissa', 'conclusão', 'silogismo'],
            'matematica_basica': ['porcentagem', 'razão', 'proporção', 'regra de três'],
            'sequencias': ['sequência', 'progressão', 'padrão'],
            
            # Informática
            'hardware': ['hardware', 'processador', 'memória', 'disco'],
            'software': ['software', 'sistema operacional', 'aplicativo'],
            'redes': ['rede', 'internet', 'protocolo', 'tcp', 'ip'],
            'seguranca': ['segurança', 'vírus', 'firewall', 'criptografia'],
            'office': ['word', 'excel', 'powerpoint', 'office'],
        }
        
        temas_encontrados = []
        
        for tema, palavras_chave in temas_conhecidos.items():
            if any(palavra in texto_lower for palavra in palavras_chave):
                temas_encontrados.append(tema)
        
        return temas_encontrados if temas_encontrados else ['geral']
    
    def analisar_temporal(
        self, 
        csv_path: str = "concursos_chunks.csv",
        banca: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Analisa distribuição temporal de temas
        
        Args:
            csv_path: Caminho para CSV com dados
            banca: Filtrar por banca específica
            
        Returns:
            DataFrame com análise temporal
        """
        print("📊 Analisando distribuição temporal...")
        
        if not Path(csv_path).exists():
            csv_path = "concursos_questoes_respostas.csv"
            if not Path(csv_path).exists():
                raise FileNotFoundError("Arquivo de dados não encontrado")
        
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"✅ {len(df)} registros carregados")
        
        # Filtrar por banca se especificado
        if banca:
            df = df[df['banca'] == banca]
            print(f"🎯 Filtrado para banca {banca}: {len(df)} registros")
        
        # Extrair ano (se não existir, tentar parse de data)
        if 'ano' not in df.columns:
            if 'data_publicacao' in df.columns:
                df['ano'] = pd.to_datetime(df['data_publicacao'], errors='coerce').dt.year
            else:
                print("⚠️ Coluna 'ano' não encontrada, usando ano atual")
                df['ano'] = datetime.now().year
        
        # Extrair temas de cada questão
        print("🔍 Extraindo temas das questões...")
        df['temas'] = df['conteudo'].apply(self.extrair_temas)
        
        # Expandir temas (uma linha por tema)
        df_expanded = df.explode('temas')
        
        # Agrupar por ano e tema
        temporal = df_expanded.groupby(['ano', 'temas']).size().reset_index(name='frequencia')
        temporal = temporal.sort_values(['ano', 'frequencia'], ascending=[True, False])
        
        print(f"✅ Análise temporal concluída: {len(temporal)} registros ano-tema")
        
        return temporal
    
    def prever_frequencia(
        self,
        tema: str,
        banca: str,
        anos_historico: int = 5,
        anos_futuros: int = 2
    ) -> Dict[str, any]:
        """
        Prevê frequência futura de um tema
        
        Args:
            tema: Tema para predição
            banca: Banca examinadora
            anos_historico: Anos de histórico para análise
            anos_futuros: Anos futuros para predição
            
        Returns:
            Dicionário com previsões
        """
        print(f"\n📈 Prevendo frequência: {tema} ({banca})")
        
        # Carregar dados históricos
        try:
            df_temporal = self.analisar_temporal(banca=banca)
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return {'erro': str(e)}
        
        # Filtrar para o tema específico
        df_tema = df_temporal[df_temporal['temas'] == tema].copy()
        
        if len(df_tema) == 0:
            return {
                'tema': tema,
                'banca': banca,
                'status': 'sem_dados',
                'mensagem': f'Nenhum dado histórico encontrado para o tema "{tema}"'
            }
        
        # Preparar dados para regressão
        anos = df_tema['ano'].values.reshape(-1, 1)
        frequencias = df_tema['frequencia'].values
        
        # Treinar modelo simples de regressão linear
        self.lr_model.fit(anos, frequencias)
        
        # Gerar previsões
        ano_atual = datetime.now().year
        anos_previsao = np.array([[ano_atual + i] for i in range(1, anos_futuros + 1)])
        previsoes = self.lr_model.predict(anos_previsao)
        
        # Garantir previsões não negativas
        previsoes = np.maximum(previsoes, 0)
        
        # Calcular tendência
        if len(frequencias) > 1:
            tendencia = 'crescente' if frequencias[-1] > frequencias[0] else 'decrescente'
            variacao = ((frequencias[-1] - frequencias[0]) / frequencias[0] * 100) if frequencias[0] > 0 else 0
        else:
            tendencia = 'estavel'
            variacao = 0
        
        return {
            'tema': tema,
            'banca': banca,
            'historico': {
                'anos': anos.flatten().tolist(),
                'frequencias': frequencias.tolist(),
                'media_historica': float(frequencias.mean()),
                'max_historica': int(frequencias.max()),
                'min_historica': int(frequencias.min())
            },
            'previsoes': {
                'anos': anos_previsao.flatten().tolist(),
                'frequencias_previstas': previsoes.tolist(),
                'confianca': self._calcular_confianca(anos, frequencias)
            },
            'tendencia': {
                'tipo': tendencia,
                'variacao_percentual': float(variacao)
            },
            'recomendacao': self._gerar_recomendacao(tendencia, previsoes[0])
        }
    
    def _calcular_confianca(self, X: np.ndarray, y: np.ndarray) -> str:
        """Calcula nível de confiança da previsão"""
        if len(X) < 3:
            return 'baixa'
        
        # Calcular R²
        y_pred = self.lr_model.predict(X)
        r2 = r2_score(y, y_pred)
        
        if r2 > 0.7:
            return 'alta'
        elif r2 > 0.4:
            return 'media'
        else:
            return 'baixa'
    
    def _gerar_recomendacao(self, tendencia: str, freq_prevista: float) -> str:
        """Gera recomendação de estudo"""
        if tendencia == 'crescente' and freq_prevista > 10:
            return "🔥 ALTA PRIORIDADE - Tema em ascensão, estudar com atenção!"
        elif tendencia == 'crescente':
            return "📈 PRIORIDADE MÉDIA - Tema crescendo, vale a pena revisar"
        elif freq_prevista > 15:
            return "⚠️ PRIORIDADE ALTA - Tema frequente, estudo essencial"
        elif freq_prevista > 5:
            return "📚 PRIORIDADE MÉDIA - Tema comum, incluir no cronograma"
        else:
            return "📖 PRIORIDADE BAIXA - Tema menos frequente, revisar se houver tempo"
    
    def identificar_temas_emergentes(
        self,
        banca: str,
        threshold: float = 0.5
    ) -> List[Dict[str, any]]:
        """
        Identifica temas emergentes (crescimento acelerado)
        
        Args:
            banca: Banca para análise
            threshold: Taxa de crescimento mínima
            
        Returns:
            Lista de temas emergentes
        """
        print(f"\n🔍 Identificando temas emergentes para {banca}...")
        
        df_temporal = self.analisar_temporal(banca=banca)
        
        temas_unicos = df_temporal['temas'].unique()
        temas_emergentes = []
        
        for tema in temas_unicos:
            df_tema = df_temporal[df_temporal['temas'] == tema].sort_values('ano')
            
            if len(df_tema) < 2:
                continue
            
            # Calcular taxa de crescimento
            freq_antiga = df_tema.iloc[0]['frequencia']
            freq_recente = df_tema.iloc[-1]['frequencia']
            
            if freq_antiga > 0:
                taxa_crescimento = (freq_recente - freq_antiga) / freq_antiga
                
                if taxa_crescimento >= threshold:
                    temas_emergentes.append({
                        'tema': tema,
                        'taxa_crescimento': float(taxa_crescimento),
                        'freq_antiga': int(freq_antiga),
                        'freq_recente': int(freq_recente),
                        'anos_analisados': len(df_tema)
                    })
        
        # Ordenar por taxa de crescimento
        temas_emergentes = sorted(
            temas_emergentes, 
            key=lambda x: x['taxa_crescimento'], 
            reverse=True
        )
        
        print(f"✅ {len(temas_emergentes)} temas emergentes identificados")
        
        return temas_emergentes
    
    def gerar_relatorio_tendencias(
        self,
        banca: str,
        output_path: str = "relatorio_tendencias.json"
    ) -> Dict[str, any]:
        """
        Gera relatório completo de tendências
        
        Args:
            banca: Banca para análise
            output_path: Caminho para salvar relatório
            
        Returns:
            Dicionário com relatório completo
        """
        print("\n" + "="*60)
        print(f"📊 RELATÓRIO DE TENDÊNCIAS - {banca}")
        print("="*60)
        
        # Análise temporal
        df_temporal = self.analisar_temporal(banca=banca)
        
        # Top 10 temas mais frequentes
        top_temas = df_temporal.groupby('temas')['frequencia'].sum().sort_values(ascending=False).head(10)
        
        # Temas emergentes
        emergentes = self.identificar_temas_emergentes(banca)
        
        # Estatísticas gerais
        relatorio = {
            'banca': banca,
            'data_analise': datetime.now().isoformat(),
            'estatisticas': {
                'total_questoes': int(df_temporal['frequencia'].sum()),
                'temas_unicos': int(df_temporal['temas'].nunique()),
                'anos_analisados': df_temporal['ano'].nunique()
            },
            'top_10_temas': {
                tema: int(freq) for tema, freq in top_temas.items()
            },
            'temas_emergentes': emergentes[:5],
            'distribuicao_anual': df_temporal.groupby('ano')['frequencia'].sum().to_dict()
        }
        
        # Salvar relatório
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Relatório salvo em: {output_path}")
        
        # Imprimir resumo
        print(f"\n📊 Top 5 Temas:")
        for i, (tema, freq) in enumerate(list(top_temas.items())[:5], 1):
            print(f"   {i}. {tema}: {freq} questões")
        
        if emergentes:
            print(f"\n🔥 Top 3 Temas Emergentes:")
            for i, tema_info in enumerate(emergentes[:3], 1):
                print(f"   {i}. {tema_info['tema']}: +{tema_info['taxa_crescimento']:.1%}")
        
        return relatorio


# Singleton
_theme_predictor = None

def get_theme_predictor() -> ThemePredictor:
    """Retorna instância singleton do preditor"""
    global _theme_predictor
    if _theme_predictor is None:
        _theme_predictor = ThemePredictor()
    return _theme_predictor


if __name__ == "__main__":
    print("="*60)
    print("📈 PREDITOR ML DE TEMAS")
    print("="*60)
    
    predictor = ThemePredictor()
    
    try:
        # Gerar relatório para cada banca
        for banca in ['CEBRASPE', 'FGV', 'FCC']:
            print(f"\n{'='*60}")
            print(f"Analisando: {banca}")
            print(f"{'='*60}")
            
            relatorio = predictor.gerar_relatorio_tendencias(
                banca=banca,
                output_path=f"relatorio_tendencias_{banca.lower()}.json"
            )
            
            # Prever alguns temas específicos
            temas_teste = ['principios_adm', 'direitos_fundamentais', 'concordancia']
            
            for tema in temas_teste:
                previsao = predictor.prever_frequencia(tema, banca)
                if previsao.get('status') != 'sem_dados':
                    print(f"\n📈 {tema}:")
                    print(f"   {previsao['recomendacao']}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\n💡 Certifique-se de ter dados processados disponíveis")
