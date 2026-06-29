#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 SISTEMA DE MÉTRICAS AVANÇADAS E APRENDIZADO CONTÍNUO
========================================================
Analisa performance, identifica gaps e otimiza o modelo continuamente
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict
import re

class SistemaMetricasAvancadas:
    def __init__(self):
        self.df_questoes = None
        self.metricas_performance = {}
        self.gaps_conhecimento = []
        self.recomendacoes_melhoria = []
        
    def carregar_dados(self):
        """Carrega todos os dados disponíveis"""
        
        print("📊 SISTEMA DE MÉTRICAS AVANÇADAS")
        print("=" * 60)
        
        arquivos = {
            'questoes': 'concursos_questoes_respostas.csv',
            'chunks': 'concursos_chunks.csv'
        }
        
        dados_carregados = {}
        
        for tipo, arquivo in arquivos.items():
            if Path(arquivo).exists():
                try:
                    df = pd.read_csv(arquivo, encoding='utf-8-sig')
                    dados_carregados[tipo] = df
                    print(f"✅ {tipo.title()}: {len(df)} registros")
                except Exception as e:
                    print(f"⚠️ Erro ao carregar {tipo}: {e}")
        
        return dados_carregados
    
    def analisar_cobertura_conteudo(self, dados):
        """Analisa cobertura de conteúdo por banca e área"""
        
        print("\n📚 ANÁLISE DE COBERTURA DE CONTEÚDO")
        print("=" * 60)
        
        if 'questoes' not in dados:
            print("⚠️ Dados de questões não disponíveis")
            return {}
        
        df = dados['questoes']
        
        cobertura = {
            'por_banca': self._cobertura_por_banca(df),
            'por_area': self._cobertura_por_area(df),
            'por_disciplina': self._cobertura_por_disciplina(df),
            'temporal': self._cobertura_temporal(df),
            'gaps_identificados': self._identificar_gaps(df)
        }
        
        self._imprimir_cobertura(cobertura)
        
        return cobertura
    
    def _cobertura_por_banca(self, df):
        """Analisa cobertura por banca"""
        
        bancas = df['banca'].value_counts()
        total = len(df)
        
        cobertura = {}
        for banca, count in bancas.items():
            cobertura[banca] = {
                'questoes': int(count),
                'percentual': round((count/total)*100, 2),
                'com_gabarito': int(df[df['banca']==banca]['tem_gabarito'].sum()) if 'tem_gabarito' in df.columns else 0,
                'areas_cobertas': int(df[df['banca']==banca]['area'].nunique()) if 'area' in df.columns else 0
            }
        
        return cobertura
    
    def _cobertura_por_area(self, df):
        """Analisa cobertura por área de conhecimento"""
        
        areas = df['area'].value_counts() if 'area' in df.columns else pd.Series()
        total = len(df)
        
        cobertura = {}
        for area, count in areas.items():
            cobertura[area] = {
                'questoes': int(count),
                'percentual': round((count/total)*100, 2),
                'bancas': list(df[df['area']==area]['banca'].unique())
            }
        
        return cobertura
    
    def _cobertura_por_disciplina(self, df):
        """Analisa cobertura por disciplina"""
        
        if 'disciplina' not in df.columns:
            return {}
        
        disciplinas = df['disciplina'].value_counts()
        
        return {disc: int(count) for disc, count in disciplinas.items()}
    
    def _cobertura_temporal(self, df):
        """Analisa distribuição temporal das questões"""
        
        if 'ano' not in df.columns:
            return {}
        
        anos = df['ano'].value_counts().sort_index()
        
        return {int(ano): int(count) for ano, count in anos.items()}
    
    def _identificar_gaps(self, df):
        """Identifica gaps de conteúdo"""
        
        gaps = []
        
        # Gap 1: Bancas com poucas questões
        bancas = df['banca'].value_counts()
        for banca, count in bancas.items():
            if count < 50:
                gaps.append({
                    'tipo': 'banca_insuficiente',
                    'banca': banca,
                    'questoes_atuais': int(count),
                    'questoes_recomendadas': 100,
                    'prioridade': 'ALTA' if count < 20 else 'MÉDIA'
                })
        
        # Gap 2: Áreas pouco cobertas
        if 'area' in df.columns:
            areas = df['area'].value_counts()
            for area, count in areas.items():
                if count < 30:
                    gaps.append({
                        'tipo': 'area_insuficiente',
                        'area': area,
                        'questoes_atuais': int(count),
                        'questoes_recomendadas': 50,
                        'prioridade': 'MÉDIA'
                    })
        
        # Gap 3: Questões sem gabarito
        if 'tem_gabarito' in df.columns:
            sem_gabarito = (~df['tem_gabarito']).sum()
            if sem_gabarito > 0:
                gaps.append({
                    'tipo': 'gabaritos_faltantes',
                    'quantidade': int(sem_gabarito),
                    'percentual': round((sem_gabarito/len(df))*100, 2),
                    'prioridade': 'ALTA'
                })
        
        return gaps
    
    def _imprimir_cobertura(self, cobertura):
        """Imprime resumo da cobertura"""
        
        print("\n🎯 COBERTURA POR BANCA:")
        for banca, dados in cobertura['por_banca'].items():
            print(f"   {banca}: {dados['questoes']} questões ({dados['percentual']}%)")
            print(f"      Com gabarito: {dados['com_gabarito']}")
            print(f"      Áreas cobertas: {dados['areas_cobertas']}")
        
        if cobertura['por_area']:
            print("\n📚 COBERTURA POR ÁREA:")
            for area, dados in list(cobertura['por_area'].items())[:10]:
                print(f"   {area}: {dados['questoes']} questões ({dados['percentual']}%)")
        
        if cobertura['gaps_identificados']:
            print("\n⚠️ GAPS IDENTIFICADOS:")
            for gap in cobertura['gaps_identificados']:
                tipo = gap['tipo'].replace('_', ' ').title()
                print(f"   [{gap['prioridade']}] {tipo}")
                if 'banca' in gap:
                    print(f"      Banca: {gap['banca']}")
                    print(f"      Atual: {gap['questoes_atuais']} | Recomendado: {gap['questoes_recomendadas']}")
                elif 'area' in gap:
                    print(f"      Área: {gap['area']}")
                    print(f"      Atual: {gap['questoes_atuais']} | Recomendado: {gap['questoes_recomendadas']}")
    
    def calcular_metricas_qualidade(self, dados):
        """Calcula métricas de qualidade do conteúdo"""
        
        print("\n\n🎯 MÉTRICAS DE QUALIDADE")
        print("=" * 60)
        
        if 'questoes' not in dados:
            print("⚠️ Dados insuficientes")
            return {}
        
        df = dados['questoes']
        
        metricas = {
            'completude': self._calcular_completude(df),
            'diversidade': self._calcular_diversidade(df),
            'atualidade': self._calcular_atualidade(df),
            'riqueza_conteudo': self._calcular_riqueza_conteudo(df),
            'score_geral': 0
        }
        
        # Calcular score geral (média ponderada)
        pesos = {
            'completude': 0.30,
            'diversidade': 0.25,
            'atualidade': 0.20,
            'riqueza_conteudo': 0.25
        }
        
        metricas['score_geral'] = sum(
            metricas[metrica] * peso 
            for metrica, peso in pesos.items()
        )
        
        self._imprimir_metricas_qualidade(metricas)
        
        return metricas
    
    def _calcular_completude(self, df):
        """Calcula completude dos dados (0-100)"""
        
        scores = []
        
        # Tem gabarito?
        if 'tem_gabarito' in df.columns:
            score_gabarito = (df['tem_gabarito'].sum() / len(df)) * 100
            scores.append(score_gabarito)
        
        # Campos preenchidos?
        campos_importantes = ['conteudo_questao', 'banca', 'area', 'ano']
        for campo in campos_importantes:
            if campo in df.columns:
                preenchido = (~df[campo].isna()).sum() / len(df) * 100
                scores.append(preenchido)
        
        return round(np.mean(scores), 2) if scores else 0
    
    def _calcular_diversidade(self, df):
        """Calcula diversidade de conteúdo (0-100)"""
        
        scores = []
        
        # Diversidade de bancas
        if 'banca' in df.columns:
            n_bancas = df['banca'].nunique()
            score_bancas = min((n_bancas / 5) * 100, 100)  # Ideal: 5+ bancas
            scores.append(score_bancas)
        
        # Diversidade de áreas
        if 'area' in df.columns:
            n_areas = df['area'].nunique()
            score_areas = min((n_areas / 10) * 100, 100)  # Ideal: 10+ áreas
            scores.append(score_areas)
        
        # Distribuição balanceada?
        if 'banca' in df.columns:
            distribuicao = df['banca'].value_counts()
            cv = distribuicao.std() / distribuicao.mean()  # Coeficiente de variação
            score_balanco = max(0, 100 - (cv * 50))  # Penaliza desbalanceamento
            scores.append(score_balanco)
        
        return round(np.mean(scores), 2) if scores else 0
    
    def _calcular_atualidade(self, df):
        """Calcula atualidade do conteúdo (0-100)"""
        
        if 'ano' not in df.columns:
            return 50  # Score neutro
        
        ano_atual = datetime.now().year
        anos = df['ano'].dropna()
        
        if len(anos) == 0:
            return 50
        
        # Questões dos últimos 3 anos
        ultimos_3_anos = (anos >= ano_atual - 3).sum()
        score = (ultimos_3_anos / len(df)) * 100
        
        return round(score, 2)
    
    def _calcular_riqueza_conteudo(self, df):
        """Calcula riqueza/profundidade do conteúdo (0-100)"""
        
        scores = []
        
        if 'conteudo_questao' in df.columns:
            # Tamanho médio das questões
            tamanho_medio = df['conteudo_questao'].str.len().mean()
            score_tamanho = min((tamanho_medio / 500) * 100, 100)  # Ideal: 500+ chars
            scores.append(score_tamanho)
            
            # Variedade de conteúdo
            vocabulario_total = set()
            for texto in df['conteudo_questao'].dropna():
                palavras = re.findall(r'\b\w+\b', str(texto).lower())
                vocabulario_total.update(palavras)
            
            score_vocabulario = min((len(vocabulario_total) / 5000) * 100, 100)
            scores.append(score_vocabulario)
        
        return round(np.mean(scores), 2) if scores else 0
    
    def _imprimir_metricas_qualidade(self, metricas):
        """Imprime métricas de qualidade"""
        
        print(f"\n📊 SCORE GERAL: {metricas['score_geral']:.1f}/100")
        print(f"\nDetalhamento:")
        print(f"   • Completude: {metricas['completude']:.1f}/100")
        print(f"   • Diversidade: {metricas['diversidade']:.1f}/100")
        print(f"   • Atualidade: {metricas['atualidade']:.1f}/100")
        print(f"   • Riqueza de Conteúdo: {metricas['riqueza_conteudo']:.1f}/100")
        
        # Interpretação
        score = metricas['score_geral']
        if score >= 80:
            print(f"\n✅ EXCELENTE! Base de conhecimento muito boa.")
        elif score >= 60:
            print(f"\n👍 BOM! Há espaço para melhorias.")
        elif score >= 40:
            print(f"\n⚠️ REGULAR. Recomenda-se adicionar mais conteúdo.")
        else:
            print(f"\n❌ INSUFICIENTE. É necessário mais conteúdo.")
    
    def gerar_plano_melhoria(self, cobertura, metricas):
        """Gera plano de melhoria baseado nas análises"""
        
        print("\n\n🎯 PLANO DE MELHORIA")
        print("=" * 60)
        
        plano = {
            'prioridades': [],
            'acoes_recomendadas': [],
            'metas': {}
        }
        
        # Prioridade 1: Gaps críticos
        if cobertura.get('gaps_identificados'):
            for gap in cobertura['gaps_identificados']:
                if gap['prioridade'] == 'ALTA':
                    plano['prioridades'].append({
                        'tipo': gap['tipo'],
                        'descricao': self._descrever_gap(gap),
                        'prioridade': 'ALTA'
                    })
        
        # Prioridade 2: Métricas baixas
        for metrica, valor in metricas.items():
            if metrica != 'score_geral' and valor < 60:
                plano['prioridades'].append({
                    'tipo': 'metrica_baixa',
                    'metrica': metrica,
                    'valor_atual': valor,
                    'valor_alvo': 80,
                    'prioridade': 'MÉDIA'
                })
        
        # Gerar ações recomendadas
        plano['acoes_recomendadas'] = self._gerar_acoes_recomendadas(cobertura, metricas)
        
        # Definir metas
        plano['metas'] = {
            'score_geral_alvo': 80,
            'questoes_por_banca': 100,
            'cobertura_areas': 10,
            'prazo': '30 dias'
        }
        
        self._imprimir_plano_melhoria(plano)
        
        return plano
    
    def _descrever_gap(self, gap):
        """Descreve um gap identificado"""
        
        tipo = gap['tipo']
        
        if tipo == 'banca_insuficiente':
            return f"Baixa cobertura da banca {gap['banca']} ({gap['questoes_atuais']} questões). Meta: {gap['questoes_recomendadas']}."
        elif tipo == 'area_insuficiente':
            return f"Área {gap['area']} com poucas questões ({gap['questoes_atuais']}). Meta: {gap['questoes_recomendadas']}."
        elif tipo == 'gabaritos_faltantes':
            return f"{gap['quantidade']} questões sem gabarito ({gap['percentual']}%). Priorize obter gabaritos."
        
        return "Gap não especificado"
    
    def _gerar_acoes_recomendadas(self, cobertura, metricas):
        """Gera lista de ações recomendadas"""
        
        acoes = []
        
        # Ação 1: Baixar mais provas
        if metricas.get('completude', 0) < 70:
            acoes.append({
                'acao': 'Baixar mais provas e gabaritos',
                'comando': 'BAIXAR_PROVAS_PCI.bat',
                'impacto': 'Aumenta completude e diversidade',
                'prioridade': 1
            })
        
        # Ação 2: Processar PDFs existentes
        acoes.append({
            'acao': 'Processar PDFs em chunks',
            'comando': 'PROCESSAR_QUESTOES_GABARITOS.bat',
            'impacto': 'Melhora qualidade da base',
            'prioridade': 2
        })
        
        # Ação 3: Indexar no ChromaDB
        acoes.append({
            'acao': 'Indexar no ChromaDB',
            'comando': 'python -m modules.concurso_embeddings',
            'impacto': 'Habilita busca semântica',
            'prioridade': 3
        })
        
        # Ação 4: Analisar bancas
        acoes.append({
            'acao': 'Executar análise completa de bancas',
            'comando': 'ANALISAR_BANCAS.bat',
            'impacto': 'Gera insights estratégicos',
            'prioridade': 4
        })
        
        return acoes
    
    def _imprimir_plano_melhoria(self, plano):
        """Imprime o plano de melhoria"""
        
        if plano['prioridades']:
            print("\n🎯 PRIORIDADES:")
            for i, prioridade in enumerate(plano['prioridades'], 1):
                print(f"\n{i}. [{prioridade['prioridade']}] {prioridade.get('descricao', prioridade['tipo'])}")
        
        print("\n\n💡 AÇÕES RECOMENDADAS:")
        for acao in plano['acoes_recomendadas']:
            print(f"\n{acao['prioridade']}. {acao['acao']}")
            print(f"   Comando: {acao['comando']}")
            print(f"   Impacto: {acao['impacto']}")
        
        print("\n\n🎯 METAS:")
        for meta, valor in plano['metas'].items():
            print(f"   • {meta.replace('_', ' ').title()}: {valor}")
    
    def salvar_relatorio_completo(self, cobertura, metricas, plano):
        """Salva relatório completo em JSON"""
        
        relatorio = {
            'data_analise': datetime.now().isoformat(),
            'cobertura': cobertura,
            'metricas_qualidade': metricas,
            'plano_melhoria': plano
        }
        
        with open('relatorio_metricas_sistema.json', 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
        
        print("\n\n💾 Relatório salvo: relatorio_metricas_sistema.json")


def main():
    """Função principal"""
    
    sistema = SistemaMetricasAvancadas()
    
    # Carregar dados
    dados = sistema.carregar_dados()
    
    if not dados:
        print("\n⚠️ Nenhum dado disponível para análise.")
        print("\nExecute primeiro:")
        print("   1. BAIXAR_PROVAS_PCI.bat")
        print("   2. PROCESSAR_QUESTOES_GABARITOS.bat")
        return
    
    # Analisar cobertura
    cobertura = sistema.analisar_cobertura_conteudo(dados)
    
    # Calcular métricas de qualidade
    metricas = sistema.calcular_metricas_qualidade(dados)
    
    # Gerar plano de melhoria
    plano = sistema.gerar_plano_melhoria(cobertura, metricas)
    
    # Salvar relatório
    sistema.salvar_relatorio_completo(cobertura, metricas, plano)
    
    print("\n\n✅ ANÁLISE COMPLETA FINALIZADA!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Análise interrompida")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
