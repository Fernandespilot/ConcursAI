#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo de dashboard para o sistema ConcursAI"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gradio as gr
from datetime import datetime, timedelta
import json
from typing import Dict, List

class DashboardConcursos:
    """Dashboard para análise de dados de concursos"""
    
    def __init__(self, arquivo_dados="concursos_chunks.csv"):
        self.arquivo_dados = arquivo_dados
        self.df = self.carregar_dados()
    
    def carregar_dados(self) -> pd.DataFrame:
        """Carrega dados dos concursos"""
        try:
            df = pd.read_csv(self.arquivo_dados)
            
            # Processar dados
            df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
            df['ano'] = df['ano'].astype(str)
            
            # Extrair salário numérico
            df['salario_numerico'] = df['salario'].apply(self._extrair_salario_numerico)
            
            # Extrair número de vagas
            df['vagas_numericas'] = df['vagas'].apply(self._extrair_vagas_numericas)
            
            return df
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return pd.DataFrame()
    
    def _extrair_salario_numerico(self, salario_str) -> float:
        """Extrai valor numérico do salário"""
        try:
            if pd.isna(salario_str) or not isinstance(salario_str, str):
                return 0
            
            import re
            # Remover símbolos e extrair números
            numeros = re.findall(r'[\d.,]+', str(salario_str).replace('.', '').replace(',', '.'))
            if numeros:
                return float(numeros[0])
            return 0
        except:
            return 0
    
    def _extrair_vagas_numericas(self, vagas_str) -> int:
        """Extrai número de vagas"""
        try:
            if pd.isna(vagas_str):
                return 0
            
            import re
            numeros = re.findall(r'\d+', str(vagas_str))
            if numeros:
                return int(numeros[0])
            return 0
        except:
            return 0
    
    def criar_grafico_orgaos(self) -> go.Figure:
        """Cria gráfico de concursos por órgão"""
        try:
            orgaos_count = self.df['orgao'].value_counts().head(10)
            
            fig = px.bar(
                x=orgaos_count.values,
                y=orgaos_count.index,
                orientation='h',
                title="🏛️ Top 10 Órgãos com Mais Concursos",
                labels={'x': 'Número de Concursos', 'y': 'Órgão'}
            )
            
            fig.update_layout(
                height=500,
                xaxis_title="Número de Concursos",
                yaxis_title="Órgão"
            )
            
            return fig
            
        except Exception as e:
            print(f"❌ Erro no gráfico de órgãos: {e}")
            return go.Figure()
    
    def criar_grafico_cargos(self) -> go.Figure:
        """Cria gráfico de concursos por cargo"""
        try:
            cargos_count = self.df['cargo'].value_counts().head(15)
            
            fig = px.pie(
                values=cargos_count.values,
                names=cargos_count.index,
                title="💼 Distribuição de Concursos por Cargo"
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=600)
            
            return fig
            
        except Exception as e:
            print(f"❌ Erro no gráfico de cargos: {e}")
            return go.Figure()
    
    def criar_grafico_salarios(self) -> go.Figure:
        """Cria gráfico de distribuição de salários"""
        try:
            df_salarios = self.df[self.df['salario_numerico'] > 0].copy()
            
            if df_salarios.empty:
                return go.Figure().add_annotation(text="Dados de salário não disponíveis")
            
            fig = px.histogram(
                df_salarios,
                x='salario_numerico',
                nbins=20,
                title="💰 Distribuição de Salários",
                labels={'salario_numerico': 'Salário (R$)', 'count': 'Quantidade'}
            )
            
            # Adicionar linha da média
            media_salario = df_salarios['salario_numerico'].mean()
            fig.add_vline(
                x=media_salario, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Média: R$ {media_salario:,.2f}"
            )
            
            fig.update_layout(height=400)
            
            return fig
            
        except Exception as e:
            print(f"❌ Erro no gráfico de salários: {e}")
            return go.Figure()
    
    def criar_grafico_timeline(self) -> go.Figure:
        """Cria gráfico de timeline de publicações"""
        try:
            df_data = self.df.dropna(subset=['data_publicacao']).copy()
            
            if df_data.empty:
                return go.Figure().add_annotation(text="Dados de data não disponíveis")
            
            # Agrupar por mês
            df_data['mes_ano'] = df_data['data_publicacao'].dt.to_period('M')
            timeline_data = df_data.groupby('mes_ano').size().reset_index(name='count')
            timeline_data['mes_ano_str'] = timeline_data['mes_ano'].astype(str)
            
            fig = px.line(
                timeline_data,
                x='mes_ano_str',
                y='count',
                title="📅 Timeline de Publicação de Editais",
                labels={'mes_ano_str': 'Mês/Ano', 'count': 'Número de Editais'}
            )
            
            fig.update_layout(height=400)
            fig.update_xaxes(tickangle=45)
            
            return fig
            
        except Exception as e:
            print(f"❌ Erro no gráfico de timeline: {e}")
            return go.Figure()
    
    def criar_tabela_estatisticas(self) -> pd.DataFrame:
        """Cria tabela de estatísticas gerais"""
        try:
            stats = {
                'Métrica': [
                    'Total de Concursos',
                    'Órgãos Únicos',
                    'Cargos Únicos',
                    'Salário Médio',
                    'Salário Máximo',
                    'Total de Vagas',
                    'Média de Vagas por Concurso'
                ],
                'Valor': [
                    len(self.df),
                    self.df['orgao'].nunique(),
                    self.df['cargo'].nunique(),
                    f"R$ {self.df[self.df['salario_numerico'] > 0]['salario_numerico'].mean():,.2f}" if self.df['salario_numerico'].sum() > 0 else "N/A",
                    f"R$ {self.df['salario_numerico'].max():,.2f}" if self.df['salario_numerico'].max() > 0 else "N/A",
                    int(self.df['vagas_numericas'].sum()),
                    f"{self.df[self.df['vagas_numericas'] > 0]['vagas_numericas'].mean():.1f}" if self.df['vagas_numericas'].sum() > 0 else "N/A"
                ]
            }
            
            return pd.DataFrame(stats)
            
        except Exception as e:
            print(f"❌ Erro nas estatísticas: {e}")
            return pd.DataFrame({'Erro': ['Erro ao calcular estatísticas']})
    
    def criar_top_oportunidades(self) -> pd.DataFrame:
        """Cria lista das melhores oportunidades"""
        try:
            df_oportunidades = self.df[
                (self.df['salario_numerico'] > 0) | (self.df['vagas_numericas'] > 0)
            ].copy()
            
            if df_oportunidades.empty:
                return pd.DataFrame({'Mensagem': ['Nenhuma oportunidade com dados completos']})
            
            # Calcular score de oportunidade
            df_oportunidades['score'] = (
                df_oportunidades['salario_numerico'] / 1000 +  # Peso para salário
                df_oportunidades['vagas_numericas'] * 10  # Peso para vagas
            )
            
            # Top 10 oportunidades
            top_10 = df_oportunidades.nlargest(10, 'score')[
                ['titulo', 'orgao', 'cargo', 'salario', 'vagas', 'url']
            ].reset_index(drop=True)
            
            return top_10
            
        except Exception as e:
            print(f"❌ Erro nas oportunidades: {e}")
            return pd.DataFrame({'Erro': ['Erro ao calcular oportunidades']})
    
    def gerar_relatorio_json(self) -> Dict:
        """Gera relatório completo em JSON"""
        try:
            relatorio = {
                'data_geracao': datetime.now().isoformat(),
                'estatisticas_gerais': {
                    'total_concursos': len(self.df),
                    'orgaos_unicos': self.df['orgao'].nunique(),
                    'cargos_unicos': self.df['cargo'].nunique(),
                    'periodo_analise': {
                        'data_inicio': str(self.df['data_publicacao'].min()) if not self.df['data_publicacao'].isna().all() else 'N/A',
                        'data_fim': str(self.df['data_publicacao'].max()) if not self.df['data_publicacao'].isna().all() else 'N/A'
                    }
                },
                'top_orgaos': self.df['orgao'].value_counts().head(5).to_dict(),
                'top_cargos': self.df['cargo'].value_counts().head(5).to_dict(),
                'estatisticas_salario': {
                    'salario_medio': float(self.df[self.df['salario_numerico'] > 0]['salario_numerico'].mean()) if self.df['salario_numerico'].sum() > 0 else 0,
                    'salario_maximo': float(self.df['salario_numerico'].max()),
                    'salario_minimo': float(self.df[self.df['salario_numerico'] > 0]['salario_numerico'].min()) if self.df['salario_numerico'].sum() > 0 else 0
                },
                'estatisticas_vagas': {
                    'total_vagas': int(self.df['vagas_numericas'].sum()),
                    'media_vagas': float(self.df[self.df['vagas_numericas'] > 0]['vagas_numericas'].mean()) if self.df['vagas_numericas'].sum() > 0 else 0,
                    'max_vagas': int(self.df['vagas_numericas'].max())
                }
            }
            
            return relatorio
            
        except Exception as e:
            print(f"❌ Erro no relatório: {e}")
            return {'erro': str(e)}

def criar_dashboard_interface():
    """Cria interface do dashboard"""
    
    dashboard = DashboardConcursos()
    
    with gr.Blocks(title="📊 Dashboard ConcursAI", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 📊 Dashboard de Análise de Concursos")
        
        with gr.Tabs():
            with gr.Tab("📈 Visão Geral"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 📊 Estatísticas Gerais")
                        stats_table = gr.Dataframe(
                            value=dashboard.criar_tabela_estatisticas(),
                            label="Métricas Principais"
                        )
                    
                    with gr.Column():
                        gr.Markdown("### 🏆 Melhores Oportunidades")
                        oportunidades_table = gr.Dataframe(
                            value=dashboard.criar_top_oportunidades(),
                            label="Top 10 Oportunidades"
                        )
            
            with gr.Tab("📊 Gráficos"):
                with gr.Row():
                    grafico_orgaos = gr.Plot(
                        value=dashboard.criar_grafico_orgaos(),
                        label="Concursos por Órgão"
                    )
                
                with gr.Row():
                    with gr.Column():
                        grafico_cargos = gr.Plot(
                            value=dashboard.criar_grafico_cargos(),
                            label="Distribuição por Cargo"
                        )
                    
                    with gr.Column():
                        grafico_salarios = gr.Plot(
                            value=dashboard.criar_grafico_salarios(),
                            label="Distribuição de Salários"
                        )
                
                with gr.Row():
                    grafico_timeline = gr.Plot(
                        value=dashboard.criar_grafico_timeline(),
                        label="Timeline de Publicações"
                    )
            
            with gr.Tab("📄 Relatório"):
                gr.Markdown("### 📋 Relatório Completo")
                
                def gerar_relatorio():
                    relatorio = dashboard.gerar_relatorio_json()
                    return json.dumps(relatorio, indent=2, ensure_ascii=False)
                
                relatorio_json = gr.Textbox(
                    value=gerar_relatorio(),
                    label="Relatório JSON",
                    lines=20,
                    max_lines=30
                )
                
                btn_atualizar = gr.Button("🔄 Atualizar Relatório")
                btn_atualizar.click(fn=gerar_relatorio, outputs=relatorio_json)
        
        # Botão para atualizar todos os dados
        with gr.Row():
            btn_refresh = gr.Button("🔄 Atualizar Dashboard", variant="primary")
            
            def atualizar_dashboard():
                dashboard.df = dashboard.carregar_dados()
                return (
                    dashboard.criar_tabela_estatisticas(),
                    dashboard.criar_top_oportunidades(),
                    dashboard.criar_grafico_orgaos(),
                    dashboard.criar_grafico_cargos(),
                    dashboard.criar_grafico_salarios(),
                    dashboard.criar_grafico_timeline()
                )
            
            btn_refresh.click(
                fn=atualizar_dashboard,
                outputs=[stats_table, oportunidades_table, grafico_orgaos, 
                        grafico_cargos, grafico_salarios, grafico_timeline]
            )
    
    return app

if __name__ == "__main__":
    dashboard_app = criar_dashboard_interface()
    dashboard_app.launch(server_port=7862, share=False)
