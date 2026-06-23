#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 API PARA DASHBOARD DE BANCAS
================================
API Flask que serve dados para o dashboard interativo
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from pathlib import Path
import json
from collections import Counter, defaultdict
import re

app = Flask(__name__)
CORS(app)

class AnalisadorDashboard:
    def __init__(self):
        self.df_questoes = None
        self.carregar_dados()
    
    def carregar_dados(self):
        """Carrega dados das questões"""
        try:
            if Path('concursos_questoes_respostas.csv').exists():
                self.df_questoes = pd.read_csv('concursos_questoes_respostas.csv', encoding='utf-8-sig')
                print(f"✅ {len(self.df_questoes)} questões carregadas")
            else:
                print("⚠️ Arquivo de questões não encontrado")
        except Exception as e:
            print(f"❌ Erro ao carregar: {e}")
    
    def analisar_banca(self, banca, area=None):
        """Análise completa de uma banca"""
        
        if self.df_questoes is None:
            return None
        
        # Filtrar por banca
        df = self.df_questoes[self.df_questoes['banca'] == banca]
        
        # Filtrar por área se especificado
        if area and area != 'TODAS':
            df = df[df['area'] == area]
        
        if len(df) == 0:
            return None
        
        return {
            'estatisticas': self._calcular_estatisticas(df),
            'distribuicao_areas': self._distribuicao_areas(df),
            'padroes_cobranca': self._padroes_cobranca(df),
            'nivel_dificuldade': self._nivel_dificuldade(df),
            'top_topicos': self._top_topicos(df),
            'armadilhas': self._armadilhas(df),
            'gabaritos': self._distribuicao_gabaritos(df),
            'estilo': self._estilo_banca(df)
        }
    
    def _calcular_estatisticas(self, df):
        """Estatísticas gerais"""
        return {
            'total_questoes': len(df),
            'com_gabarito': int(df['tem_gabarito'].sum()) if 'tem_gabarito' in df.columns else 0,
            'areas_cobertas': int(df['area'].nunique()) if 'area' in df.columns else 0,
            'nivel_predominante': self._nivel_predominante(df)
        }
    
    def _distribuicao_areas(self, df):
        """Distribuição percentual por áreas"""
        if 'area' not in df.columns:
            return {}
        
        areas = df['area'].value_counts()
        total = len(df)
        
        return {area: round((count/total)*100, 1) for area, count in areas.items()}
    
    def _padroes_cobranca(self, df):
        """Analisa como a banca cobra"""
        padroes = {
            'Legislação': 0,
            'Interpretação': 0,
            'Teoria': 0,
            'Jurisprudência': 0,
            'Prática': 0
        }
        
        palavras_chave = {
            'Legislação': ['lei', 'artigo', 'inciso', 'decreto', 'constituição'],
            'Interpretação': ['interpreta', 'significa', 'sentido', 'compreens'],
            'Teoria': ['conceito', 'teoria', 'definição', 'segundo'],
            'Jurisprudência': ['jurisprudência', 'súmula', 'stf', 'stj'],
            'Prática': ['exemplo', 'caso', 'situação', 'aplicação']
        }
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao']).lower()
            
            for padrao, palavras in palavras_chave.items():
                if any(palavra in texto for palavra in palavras):
                    padroes[padrao] += 1
        
        total = len(df)
        return {p: round((v/total)*100, 1) for p, v in padroes.items()}
    
    def _nivel_dificuldade(self, df):
        """Calcula distribuição de dificuldade"""
        niveis = {'Fácil': 0, 'Médio': 0, 'Difícil': 0}
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao'])
            tamanho = len(texto)
            palavras_complexas = len(re.findall(r'\b\w{12,}\b', texto))
            
            score = (tamanho/200) + (palavras_complexas*2)
            
            if score < 8:
                niveis['Fácil'] += 1
            elif score < 20:
                niveis['Médio'] += 1
            else:
                niveis['Difícil'] += 1
        
        total = sum(niveis.values())
        return {n: round((v/total)*100, 1) for n, v in niveis.items()}
    
    def _nivel_predominante(self, df):
        """Retorna o nível predominante"""
        niveis = self._nivel_dificuldade(df)
        return max(niveis, key=niveis.get).upper()
    
    def _top_topicos(self, df):
        """Top tópicos mais cobrados"""
        stop_words = {'o', 'a', 'de', 'da', 'do', 'e', 'que', 'para', 'com', 'em'}
        
        todas_palavras = []
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao']).lower()
            palavras = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]{5,}\b', texto)
            palavras = [p for p in palavras if p not in stop_words]
            todas_palavras.extend(palavras)
        
        return [palavra.title() for palavra, _ in Counter(todas_palavras).most_common(5)]
    
    def _armadilhas(self, df):
        """Identifica armadilhas comuns"""
        armadilhas = []
        
        padroes = {
            'Negação Dupla': (r'não.*não|nunca.*nunca', 'Usa dupla negação para confundir'),
            'Termos Absolutos': (r'\btodos?\b|\bnenhum\b|\bsempre\b|\bnunca\b', 'Palavras como sempre, nunca, todo'),
            'Exceto/Salvo': (r'exceto|salvo|menos', 'Inverte a lógica da questão')
        }
        
        for nome, (padrao, desc) in padroes.items():
            count = 0
            for _, row in df.iterrows():
                if pd.isna(row.get('conteudo_questao')):
                    continue
                texto = str(row['conteudo_questao']).lower()
                if re.search(padrao, texto):
                    count += 1
            
            if count > 0:
                freq = round((count/len(df))*100, 1)
                armadilhas.append({
                    'titulo': nome,
                    'descricao': f'{desc}. Aparece em {freq}% das questões.',
                    'frequencia': freq
                })
        
        return sorted(armadilhas, key=lambda x: x['frequencia'], reverse=True)
    
    def _distribuicao_gabaritos(self, df):
        """Distribuição de gabaritos"""
        if 'resposta_correta' not in df.columns:
            return {}
        
        df_gab = df[df['tem_gabarito'] == True] if 'tem_gabarito' in df.columns else df
        
        if len(df_gab) == 0:
            return {}
        
        gabaritos = df_gab['resposta_correta'].value_counts()
        total = len(df_gab)
        
        return {letra: round((count/total)*100, 1) for letra, count in gabaritos.items()}
    
    def _estilo_banca(self, df):
        """Analisa estilo da banca"""
        estilos = {
            'Assertivas': 0,
            'Interrogativas': 0,
            'Texto Longo': 0,
            'Diretas': 0
        }
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao'])
            tamanho = len(texto)
            
            if texto.strip().endswith('?'):
                estilos['Interrogativas'] += 1
            else:
                estilos['Assertivas'] += 1
            
            if tamanho > 400:
                estilos['Texto Longo'] += 1
            
            if texto.count(',') < 2:
                estilos['Diretas'] += 1
        
        total = len(df)
        return {e: round((v/total)*100, 1) for e, v in estilos.items()}
    
    def obter_questoes(self, banca, area=None, quantidade=10):
        """Obtém questões para o gerador"""
        if self.df_questoes is None:
            return []
        
        df = self.df_questoes[self.df_questoes['banca'] == banca]
        
        if area and area != 'TODAS':
            df = df[df['area'] == area]
        
        df = df.sample(min(quantidade, len(df)))
        
        questoes = []
        for _, row in df.iterrows():
            questoes.append({
                'id': int(row.name),
                'texto': str(row.get('conteudo_questao', '')),
                'alternativas': self._extrair_alternativas(row),
                'correta': self._obter_resposta_correta(row),
                'area': str(row.get('area', '')),
                'dificuldade': self._calcular_dificuldade_questao(row),
                'explicacao': f"Resposta: {row.get('resposta_correta', 'N/A')}"
            })
        
        return questoes
    
    def _extrair_alternativas(self, row):
        """Extrai alternativas da questão"""
        # Simplificado - em produção, analisaria o texto
        texto = str(row.get('conteudo_questao', '')).lower()
        
        if 'certo' in texto or 'errado' in texto:
            return ['Certo', 'Errado']
        else:
            return [f'Alternativa {chr(65+i)}' for i in range(5)]
    
    def _obter_resposta_correta(self, row):
        """Obtém índice da resposta correta"""
        resposta = str(row.get('resposta_correta', 'A')).upper()
        
        if resposta in ['CERTO', 'C']:
            return 0
        elif resposta in ['ERRADO', 'E']:
            return 1
        else:
            return ord(resposta[0]) - 65 if resposta else 0
    
    def _calcular_dificuldade_questao(self, row):
        """Calcula dificuldade de uma questão"""
        texto = str(row.get('conteudo_questao', ''))
        tamanho = len(texto)
        palavras_complexas = len(re.findall(r'\b\w{12,}\b', texto))
        
        score = (tamanho/200) + (palavras_complexas*2)
        
        if score < 8:
            return 'Fácil'
        elif score < 20:
            return 'Médio'
        else:
            return 'Difícil'


# Inicializar analisador
analisador = AnalisadorDashboard()

# Rotas da API
@app.route('/api/bancas/<banca>', methods=['GET'])
def get_analise_banca(banca):
    """Retorna análise completa de uma banca"""
    area = request.args.get('area', 'TODAS')
    
    analise = analisador.analisar_banca(banca.upper(), area)
    
    if analise is None:
        return jsonify({'erro': 'Dados não disponíveis'}), 404
    
    return jsonify(analise)

@app.route('/api/questoes', methods=['GET'])
def get_questoes():
    """Retorna questões para o gerador"""
    banca = request.args.get('banca', 'CEBRASPE').upper()
    area = request.args.get('area', 'TODAS')
    quantidade = int(request.args.get('quantidade', 10))
    
    questoes = analisador.obter_questoes(banca, area, quantidade)
    
    return jsonify(questoes)

@app.route('/api/bancas', methods=['GET'])
def get_bancas():
    """Lista bancas disponíveis"""
    if analisador.df_questoes is None:
        return jsonify([])
    
    bancas = analisador.df_questoes['banca'].unique().tolist()
    return jsonify(bancas)

@app.route('/api/areas/<banca>', methods=['GET'])
def get_areas(banca):
    """Lista áreas disponíveis para uma banca"""
    if analisador.df_questoes is None:
        return jsonify([])
    
    df = analisador.df_questoes[analisador.df_questoes['banca'] == banca.upper()]
    areas = df['area'].unique().tolist() if 'area' in df.columns else []
    
    return jsonify(areas)

@app.route('/api/comparacao', methods=['GET'])
def get_comparacao():
    """Retorna comparação entre bancas"""
    bancas = ['CEBRASPE', 'FGV', 'FCC']
    comparacao = {}
    
    for banca in bancas:
        analise = analisador.analisar_banca(banca)
        if analise:
            comparacao[banca] = {
                'total_questoes': analise['estatisticas']['total_questoes'],
                'nivel': analise['estatisticas']['nivel_predominante'],
                'area_forte': list(analise['distribuicao_areas'].keys())[0] if analise['distribuicao_areas'] else 'N/A',
                'cobra_mais': list(analise['padroes_cobranca'].keys())[0] if analise['padroes_cobranca'] else 'N/A'
            }
    
    return jsonify(comparacao)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Status da API"""
    return jsonify({
        'status': 'online',
        'questoes_carregadas': len(analisador.df_questoes) if analisador.df_questoes is not None else 0,
        'bancas_disponiveis': analisador.df_questoes['banca'].nunique() if analisador.df_questoes is not None else 0
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🎯 API DASHBOARD DE BANCAS")
    print("=" * 60)
    print("\nServidor rodando em: http://localhost:5000")
    print("\nEndpoints disponíveis:")
    print("  GET /api/bancas/<banca>          - Análise da banca")
    print("  GET /api/questoes                - Questões personalizadas")
    print("  GET /api/bancas                  - Lista de bancas")
    print("  GET /api/areas/<banca>           - Áreas por banca")
    print("  GET /api/comparacao              - Comparação entre bancas")
    print("  GET /api/status                  - Status da API")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
