#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎓 ASSISTENTE INTELIGENTE DE ESTUDOS - RAG AVANÇADO
====================================================
Sistema conversacional que analisa bancas, recomenda estratégias de estudo
e personaliza o aprendizado baseado no perfil do usuário
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from collections import Counter, defaultdict
import re

# Importar módulos do sistema
try:
    from modules.concurso_embeddings import collection, get_embedder
    from modules.rag_banca_inteligente import get_rag_inteligente
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    print("⚠️ Módulos de embeddings não disponíveis")
    EMBEDDINGS_AVAILABLE = False

class AssistenteEstudosInteligente:
    def __init__(self):
        self.df_questoes = None
        self.perfil_usuario = {}
        self.historico_conversa = []
        self.metricas_bancas = {}
        self.recomendacoes = []
        
        if EMBEDDINGS_AVAILABLE:
            self.rag = get_rag_inteligente()
            self.embedder = get_embedder()
        
        self.carregar_dados()
        self.analisar_bancas_profundamente()
    
    def carregar_dados(self):
        """Carrega dados das questões processadas"""
        
        print("📊 Carregando base de conhecimento...")
        
        try:
            # Tentar carregar questões processadas
            if Path('concursos_questoes_respostas.csv').exists():
                self.df_questoes = pd.read_csv('concursos_questoes_respostas.csv', encoding='utf-8-sig')
                print(f"✅ {len(self.df_questoes)} questões carregadas")
            else:
                print("⚠️ Execute PROCESSAR_QUESTOES_GABARITOS.bat primeiro")
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar: {e}")
    
    def analisar_bancas_profundamente(self):
        """Análise profunda e inteligente das bancas"""
        
        if self.df_questoes is None or len(self.df_questoes) == 0:
            return
        
        print("🔍 Analisando padrões das bancas...")
        
        bancas = ['CEBRASPE', 'FGV', 'FCC']
        
        for banca in bancas:
            df_banca = self.df_questoes[self.df_questoes['banca'] == banca]
            
            if len(df_banca) == 0:
                continue
            
            # Análise multidimensional
            self.metricas_bancas[banca] = {
                'perfil_geral': self._criar_perfil_banca(df_banca),
                'areas_fortes': self._identificar_areas_fortes(df_banca),
                'padroes_cobranca': self._analisar_padroes_cobranca(df_banca),
                'nivel_dificuldade': self._calcular_nivel_dificuldade(df_banca),
                'topicos_recorrentes': self._extrair_topicos_recorrentes(df_banca),
                'estilo_questoes': self._analisar_estilo_questoes(df_banca),
                'armadilhas_comuns': self._identificar_armadilhas(df_banca),
                'distribuicao_gabaritos': self._analisar_distribuicao_gabaritos(df_banca)
            }
        
        print("✅ Análise completa!")
    
    def _criar_perfil_banca(self, df):
        """Cria perfil completo da banca"""
        
        return {
            'total_questoes': len(df),
            'areas': df['area'].value_counts().to_dict(),
            'disciplinas': df['disciplina'].value_counts().to_dict(),
            'complexidade_media': df['conteudo_questao'].str.len().mean() if 'conteudo_questao' in df.columns else 0,
            'tem_gabarito': df['tem_gabarito'].sum(),
            'periodo_analise': f"{df['ano'].min()}-{df['ano'].max()}" if 'ano' in df.columns else 'N/A'
        }
    
    def _identificar_areas_fortes(self, df):
        """Identifica áreas mais cobradas"""
        
        areas = df['area'].value_counts()
        total = len(df)
        
        areas_fortes = []
        for area, count in areas.items():
            percentual = (count / total) * 100
            if percentual >= 15:  # Área forte se >= 15%
                areas_fortes.append({
                    'area': area,
                    'questoes': int(count),
                    'percentual': round(percentual, 1),
                    'prioridade': 'ALTA' if percentual >= 30 else 'MÉDIA'
                })
        
        return sorted(areas_fortes, key=lambda x: x['percentual'], reverse=True)
    
    def _analisar_padroes_cobranca(self, df):
        """Analisa como a banca cobra os conteúdos"""
        
        padroes = {
            'cobra_teoria': 0,
            'cobra_pratica': 0,
            'cobra_jurisprudencia': 0,
            'cobra_legislacao': 0,
            'cobra_interpretacao': 0,
            'cobra_calculo': 0,
            'cobra_decoreba': 0
        }
        
        palavras_chave = {
            'teoria': ['conceito', 'definição', 'teoria', 'segundo', 'conforme'],
            'pratica': ['exemplo', 'caso', 'situação', 'aplicação', 'prática'],
            'jurisprudencia': ['jurisprudência', 'súmula', 'precedente', 'entendimento'],
            'legislacao': ['lei', 'artigo', 'inciso', 'parágrafo', 'decreto'],
            'interpretacao': ['interpreta', 'analise', 'compreens', 'significa', 'sentido'],
            'calculo': ['calcule', 'determine', 'valor', 'porcentagem', 'total'],
            'decoreba': ['ano', 'data', 'nome', 'quantidade exata', 'número de']
        }
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao']).lower()
            
            for tipo, palavras in palavras_chave.items():
                if any(palavra in texto for palavra in palavras):
                    padroes[f'cobra_{tipo}'] += 1
        
        # Calcular percentuais
        total = len(df)
        for key in padroes:
            padroes[key] = {
                'count': padroes[key],
                'percentual': round((padroes[key] / total) * 100, 1) if total > 0 else 0
            }
        
        return padroes
    
    def _calcular_nivel_dificuldade(self, df):
        """Calcula nível de dificuldade das questões"""
        
        niveis = {'facil': 0, 'medio': 0, 'dificil': 0}
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao'])
            
            # Critérios de dificuldade
            tamanho = len(texto)
            palavras_complexas = len(re.findall(r'\b\w{12,}\b', texto))
            subordinadas = texto.count(',') + texto.count(';')
            tem_calculo = bool(re.search(r'\d+[+\-*/]\d+', texto))
            
            score = (tamanho/200) + (palavras_complexas*2) + subordinadas + (tem_calculo*5)
            
            if score < 8:
                niveis['facil'] += 1
            elif score < 20:
                niveis['medio'] += 1
            else:
                niveis['dificil'] += 1
        
        total = sum(niveis.values())
        return {
            nivel: {
                'count': count,
                'percentual': round((count/total)*100, 1) if total > 0 else 0
            }
            for nivel, count in niveis.items()
        }
    
    def _extrair_topicos_recorrentes(self, df):
        """Extrai tópicos mais recorrentes"""
        
        stop_words = {'o', 'a', 'de', 'da', 'do', 'e', 'que', 'para', 'com', 'em', 
                     'é', 'um', 'uma', 'os', 'as', 'dos', 'das', 'ao', 'à', 'pelo'}
        
        todas_palavras = []
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao']).lower()
            palavras = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]{5,}\b', texto)
            palavras = [p for p in palavras if p not in stop_words]
            todas_palavras.extend(palavras)
        
        top_30 = Counter(todas_palavras).most_common(30)
        
        return [{'topico': palavra, 'frequencia': freq} for palavra, freq in top_30]
    
    def _analisar_estilo_questoes(self, df):
        """Analisa estilo de escrita das questões"""
        
        estilos = {
            'direta': 0,
            'indireta': 0,
            'assertiva': 0,
            'interrogativa': 0,
            'texto_longo': 0,
            'texto_curto': 0
        }
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao'])
            tamanho = len(texto)
            
            # Análise de estilo
            if texto.strip().endswith('?'):
                estilos['interrogativa'] += 1
            else:
                estilos['assertiva'] += 1
            
            if tamanho > 400:
                estilos['texto_longo'] += 1
            else:
                estilos['texto_curto'] += 1
            
            # Frases diretas vs indiretas
            if texto.count(',') < 2:
                estilos['direta'] += 1
            else:
                estilos['indireta'] += 1
        
        total = len(df)
        return {
            estilo: round((count/total)*100, 1) if total > 0 else 0
            for estilo, count in estilos.items()
        }
    
    def _identificar_armadilhas(self, df):
        """Identifica armadilhas comuns da banca"""
        
        armadilhas = []
        
        # Padrões de armadilhas conhecidas
        padroes_armadilha = {
            'negacao_dupla': r'não.*não|nunca.*nunca',
            'exceto': r'exceto|salvo|menos|com exceção',
            'absolutos': r'\btodos?\b|\bnenhum\b|\bsempre\b|\bnunca\b|\bjamais\b',
            'palavras_confusas': r'pode|deve|poderá|deverá',
            'detalhes_minimos': r'apenas|somente|exclusivamente|unicamente'
        }
        
        for tipo, padrao in padroes_armadilha.items():
            count = 0
            for _, row in df.iterrows():
                if pd.isna(row.get('conteudo_questao')):
                    continue
                texto = str(row['conteudo_questao']).lower()
                if re.search(padrao, texto):
                    count += 1
            
            if count > 0:
                armadilhas.append({
                    'tipo': tipo.replace('_', ' ').title(),
                    'frequencia': count,
                    'percentual': round((count/len(df))*100, 1)
                })
        
        return sorted(armadilhas, key=lambda x: x['frequencia'], reverse=True)
    
    def _analisar_distribuicao_gabaritos(self, df):
        """Analisa distribuição dos gabaritos"""
        
        df_com_gab = df[df['tem_gabarito'] == True]
        
        if len(df_com_gab) == 0:
            return {}
        
        gabaritos = df_com_gab['resposta_correta'].value_counts()
        total = len(df_com_gab)
        
        distribuicao = {}
        for letra, count in gabaritos.items():
            distribuicao[letra] = {
                'count': int(count),
                'percentual': round((count/total)*100, 1),
                'esperado': 20.0,  # 20% se fosse distribuído igualmente
                'vies': round((count/total)*100 - 20.0, 1)
            }
        
        return distribuicao
    
    def conversar(self, pergunta_usuario):
        """Conversa inteligente com análise contextual"""
        
        print(f"\n👤 Você: {pergunta_usuario}")
        
        # Adicionar ao histórico
        self.historico_conversa.append({
            'tipo': 'usuario',
            'mensagem': pergunta_usuario,
            'timestamp': datetime.now()
        })
        
        # Analisar intenção da pergunta
        intencao = self._analisar_intencao(pergunta_usuario)
        
        # Gerar resposta contextual
        resposta = self._gerar_resposta_inteligente(pergunta_usuario, intencao)
        
        # Adicionar ao histórico
        self.historico_conversa.append({
            'tipo': 'assistente',
            'mensagem': resposta,
            'timestamp': datetime.now()
        })
        
        print(f"\n🤖 Assistente: {resposta}")
        
        return resposta
    
    def _analisar_intencao(self, pergunta):
        """Analisa a intenção da pergunta do usuário"""
        
        pergunta_lower = pergunta.lower()
        
        intencoes = {
            'comparar_bancas': ['diferença', 'compara', 'versus', 'vs', 'melhor', 'pior'],
            'estrategia_estudo': ['como estudar', 'estratégia', 'plano', 'método', 'dica'],
            'area_especifica': ['direito', 'português', 'matemática', 'tecnologia', 'informática'],
            'dificuldade': ['difícil', 'fácil', 'nível', 'complexidade'],
            'o_que_mais_cai': ['mais cai', 'mais cobra', 'frequente', 'recorrente', 'comum'],
            'gabarito': ['gabarito', 'resposta', 'alternativa', 'letra'],
            'recomendacao': ['recomenda', 'sugere', 'indica', 'melhor forma'],
            'perfil_banca': ['estilo', 'perfil', 'característica', 'jeito', 'como é']
        }
        
        intencoes_detectadas = []
        
        for intencao, palavras_chave in intencoes.items():
            if any(palavra in pergunta_lower for palavra in palavras_chave):
                intencoes_detectadas.append(intencao)
        
        # Detectar banca mencionada
        banca_mencionada = None
        for banca in ['CEBRASPE', 'FGV', 'FCC', 'CESPE']:
            if banca.lower() in pergunta_lower:
                banca_mencionada = 'CEBRASPE' if banca == 'CESPE' else banca
                break
        
        return {
            'intencoes': intencoes_detectadas,
            'banca': banca_mencionada
        }
    
    def _gerar_resposta_inteligente(self, pergunta, intencao):
        """Gera resposta inteligente baseada na intenção"""
        
        # Usar RAG para buscar contexto relevante
        contexto_rag = ""
        if EMBEDDINGS_AVAILABLE:
            try:
                resultado = self.rag.responder(pergunta, retornar_detalhes=True)
                contexto_rag = resultado.get('resposta', '')
            except:
                pass
        
        banca = intencao.get('banca')
        intencoes = intencao.get('intencoes', [])
        
        # Construir resposta baseada nas intenções
        resposta_partes = []
        
        # 1. Comparação de bancas
        if 'comparar_bancas' in intencoes:
            resposta_partes.append(self._comparar_bancas())
        
        # 2. Estratégia de estudo
        if 'estrategia_estudo' in intencoes:
            resposta_partes.append(self._recomendar_estrategia(banca))
        
        # 3. O que mais cai
        if 'o_que_mais_cai' in intencoes:
            resposta_partes.append(self._informar_mais_cobrado(banca))
        
        # 4. Perfil da banca
        if 'perfil_banca' in intencoes and banca:
            resposta_partes.append(self._descrever_perfil_banca(banca))
        
        # 5. Recomendação personalizada
        if 'recomendacao' in intencoes:
            resposta_partes.append(self._gerar_recomendacao_personalizada(banca))
        
        # Se nenhuma intenção específica, usar RAG puro
        if not resposta_partes and contexto_rag:
            return contexto_rag
        
        if not resposta_partes:
            return "Desculpe, não entendi bem sua pergunta. Pode reformular? Posso ajudar com estratégias de estudo, análise de bancas, o que mais cai, etc."
        
        return "\n\n".join(resposta_partes)
    
    def _comparar_bancas(self):
        """Compara as 3 bancas principais"""
        
        if not self.metricas_bancas:
            return "Ainda não tenho dados suficientes para comparar as bancas."
        
        comparacao = "📊 **COMPARAÇÃO DAS BANCAS**\n\n"
        
        for banca, metricas in self.metricas_bancas.items():
            perfil = metricas['perfil_geral']
            dificuldade = metricas['nivel_dificuldade']
            
            nivel_predominante = max(dificuldade.items(), key=lambda x: x[1]['percentual'])
            
            comparacao += f"**{banca}:**\n"
            comparacao += f"• {perfil['total_questoes']} questões analisadas\n"
            comparacao += f"• Nível: {nivel_predominante[0].upper()} ({nivel_predominante[1]['percentual']}%)\n"
            
            if metricas['areas_fortes']:
                top_area = metricas['areas_fortes'][0]
                comparacao += f"• Área forte: {top_area['area']} ({top_area['percentual']}%)\n"
            
            comparacao += "\n"
        
        return comparacao
    
    def _recomendar_estrategia(self, banca=None):
        """Recomenda estratégia de estudo"""
        
        if not banca:
            return "🎯 **ESTRATÉGIA GERAL:**\n\nFoque nas áreas que mais caem em cada banca e pratique questões similares. Use o sistema de repetição espaçada."
        
        if banca not in self.metricas_bancas:
            return f"Ainda não tenho dados suficientes sobre {banca}."
        
        metricas = self.metricas_bancas[banca]
        estrategia = f"🎯 **ESTRATÉGIA PARA {banca}:**\n\n"
        
        # Áreas prioritárias
        if metricas['areas_fortes']:
            estrategia += "**1. PRIORIZE ESTAS ÁREAS:**\n"
            for area in metricas['areas_fortes'][:3]:
                estrategia += f"   • {area['area']}: {area['percentual']}% das questões ({area['prioridade']} prioridade)\n"
            estrategia += "\n"
        
        # Como a banca cobra
        padroes = metricas['padroes_cobranca']
        top_padroes = sorted(padroes.items(), key=lambda x: x[1]['percentual'], reverse=True)[:3]
        
        estrategia += "**2. COMO ESTUDAR:**\n"
        for padrao, dados in top_padroes:
            tipo = padrao.replace('cobra_', '').title()
            estrategia += f"   • Foque em {tipo} ({dados['percentual']}% das questões)\n"
        estrategia += "\n"
        
        # Armadilhas
        if metricas['armadilhas_comuns']:
            estrategia += "**3. CUIDADO COM:**\n"
            for armadilha in metricas['armadilhas_comuns'][:3]:
                estrategia += f"   • {armadilha['tipo']} (aparece em {armadilha['percentual']}% das questões)\n"
        
        return estrategia
    
    def _informar_mais_cobrado(self, banca=None):
        """Informa o que mais cai"""
        
        if not banca:
            banca = list(self.metricas_bancas.keys())[0] if self.metricas_bancas else None
        
        if not banca or banca not in self.metricas_bancas:
            return "Especifique qual banca você quer saber."
        
        metricas = self.metricas_bancas[banca]
        info = f"📚 **O QUE MAIS CAI NA {banca}:**\n\n"
        
        # Top 10 tópicos
        if metricas['topicos_recorrentes']:
            info += "**TOP 10 TÓPICOS:**\n"
            for i, topico in enumerate(metricas['topicos_recorrentes'][:10], 1):
                info += f"{i}. {topico['topico'].title()} ({topico['frequencia']}x)\n"
        
        return info
    
    def _descrever_perfil_banca(self, banca):
        """Descreve perfil detalhado da banca"""
        
        if banca not in self.metricas_bancas:
            return f"Ainda não analisei {banca} suficientemente."
        
        metricas = self.metricas_bancas[banca]
        perfil = f"🎭 **PERFIL DA {banca}:**\n\n"
        
        # Estilo de questões
        estilo = metricas['estilo_questoes']
        perfil += "**ESTILO:**\n"
        perfil += f"• Questões diretas: {estilo.get('direta', 0)}%\n"
        perfil += f"• Texto longo: {estilo.get('texto_longo', 0)}%\n"
        perfil += f"• Formato assertivo: {estilo.get('assertiva', 0)}%\n\n"
        
        # Dificuldade
        dificuldade = metricas['nivel_dificuldade']
        perfil += "**DIFICULDADE:**\n"
        for nivel, dados in dificuldade.items():
            perfil += f"• {nivel.title()}: {dados['percentual']}%\n"
        
        return perfil
    
    def _gerar_recomendacao_personalizada(self, banca=None):
        """Gera recomendação personalizada"""
        
        rec = "💡 **RECOMENDAÇÃO PERSONALIZADA:**\n\n"
        rec += "1. Faça questões filtradas por banca\n"
        rec += "2. Anote padrões que você observar\n"
        rec += "3. Crie resumos focados nos tópicos mais cobrados\n"
        rec += "4. Pratique com cronômetro (simule pressão da prova)\n"
        rec += "5. Revise gabaritos para entender o raciocínio da banca\n"
        
        return rec
    
    def iniciar_conversa_interativa(self):
        """Inicia conversa interativa no terminal"""
        
        print("\n" + "=" * 60)
        print("🎓 ASSISTENTE INTELIGENTE DE ESTUDOS")
        print("=" * 60)
        print("\nOlá! Sou seu assistente de estudos para concursos.")
        print("Posso ajudar com:")
        print("  • Análise de bancas (CEBRASPE, FGV, FCC)")
        print("  • Estratégias de estudo personalizadas")
        print("  • O que mais cai em cada banca")
        print("  • Comparação entre bancas")
        print("  • Dicas sobre armadilhas e padrões")
        print("\nDigite 'sair' para encerrar.")
        print("=" * 60)
        
        while True:
            try:
                pergunta = input("\n👤 Você: ").strip()
                
                if not pergunta:
                    continue
                
                if pergunta.lower() in ['sair', 'exit', 'quit', 'tchau']:
                    print("\n👋 Até logo! Bons estudos!")
                    break
                
                self.conversar(pergunta)
                
            except KeyboardInterrupt:
                print("\n\n👋 Até logo!")
                break
            except Exception as e:
                print(f"\n⚠️ Erro: {e}")


def main():
    """Função principal"""
    
    assistente = AssistenteEstudosInteligente()
    assistente.iniciar_conversa_interativa()


if __name__ == "__main__":
    main()
