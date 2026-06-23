#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 ANÁLISE COMPLETA DE BANCAS
==============================
Analisa padrões, estilos e tendências das bancas CEBRASPE, FGV e FCC
"""

import pandas as pd
import re
from collections import Counter, defaultdict
from pathlib import Path
import json
from datetime import datetime

class AnalisadorBancasCompleto:
    def __init__(self, csv_questoes='concursos_questoes_respostas.csv'):
        self.csv_questoes = csv_questoes
        self.df = None
        self.analises = {}
        
    def carregar_dados(self):
        """Carrega dados das questões e respostas"""
        
        print("\n📊 CARREGANDO DADOS")
        print("=" * 60)
        
        try:
            self.df = pd.read_csv(self.csv_questoes, encoding='utf-8-sig')
            print(f"✅ {len(self.df)} questões carregadas")
            
            # Filtrar apenas as 3 bancas principais
            self.df = self.df[self.df['banca'].isin(['CEBRASPE', 'FGV', 'FCC'])]
            print(f"✅ {len(self.df)} questões das bancas CEBRASPE, FGV, FCC")
            
            return True
            
        except FileNotFoundError:
            print("❌ Arquivo não encontrado. Execute processar_questoes_gabaritos.py primeiro!")
            return False
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return False
    
    def analisar_todas_bancas(self):
        """Análise completa de todas as bancas"""
        
        if self.df is None or len(self.df) == 0:
            print("⚠️ Nenhum dado para analisar")
            return
        
        print("\n\n🎯 INICIANDO ANÁLISE COMPLETA DAS BANCAS")
        print("=" * 60)
        
        bancas = ['CEBRASPE', 'FGV', 'FCC']
        
        for banca in bancas:
            print(f"\n\n{'='*60}")
            print(f"📋 BANCA: {banca}")
            print(f"{'='*60}")
            
            df_banca = self.df[self.df['banca'] == banca]
            
            if len(df_banca) == 0:
                print(f"⚠️ Nenhuma questão encontrada para {banca}")
                continue
            
            analise = {
                'banca': banca,
                'total_questoes': len(df_banca),
                'estatisticas_gerais': self._estatisticas_gerais(df_banca),
                'distribuicao_areas': self._analisar_areas(df_banca),
                'padroes_questoes': self._analisar_padroes_questoes(df_banca),
                'analise_gabaritos': self._analisar_gabaritos(df_banca),
                'palavras_chave': self._extrair_palavras_chave(df_banca),
                'complexidade': self._analisar_complexidade(df_banca),
                'estilo_redacao': self._analisar_estilo(df_banca)
            }
            
            self.analises[banca] = analise
            self._imprimir_analise(analise)
        
        # Análise comparativa
        self._analise_comparativa()
        
        # Salvar relatório
        self._salvar_relatorio()
    
    def _estatisticas_gerais(self, df):
        """Estatísticas gerais da banca"""
        
        stats = {
            'total_questoes': len(df),
            'com_gabarito': df['tem_gabarito'].sum(),
            'sem_gabarito': (~df['tem_gabarito']).sum(),
            'percentual_gabarito': (df['tem_gabarito'].sum() / len(df) * 100) if len(df) > 0 else 0,
            'areas_cobertas': df['area'].nunique(),
            'disciplinas': df['disciplina'].nunique(),
            'tamanho_medio_questao': df['conteudo_questao'].str.len().mean() if 'conteudo_questao' in df.columns else 0
        }
        
        return stats
    
    def _analisar_areas(self, df):
        """Analisa distribuição por áreas"""
        
        print("\n📚 DISTRIBUIÇÃO POR ÁREAS:")
        
        areas = df['area'].value_counts()
        
        distribuicao = {}
        for area, count in areas.items():
            percentual = (count / len(df) * 100)
            distribuicao[area] = {
                'quantidade': int(count),
                'percentual': round(percentual, 2)
            }
            print(f"   {area}: {count} questões ({percentual:.1f}%)")
        
        return distribuicao
    
    def _analisar_padroes_questoes(self, df):
        """Analisa padrões das questões"""
        
        print("\n🔍 PADRÕES DAS QUESTÕES:")
        
        padroes = {
            'questoes_longas': 0,
            'questoes_curtas': 0,
            'tem_tabela': 0,
            'tem_grafico': 0,
            'tem_codigo': 0,
            'tem_legislacao': 0,
            'formato_multipla_escolha': 0,
            'formato_verdadeiro_falso': 0
        }
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
                
            texto = str(row['conteudo_questao']).lower()
            tamanho = len(texto)
            
            # Tamanho
            if tamanho > 500:
                padroes['questoes_longas'] += 1
            else:
                padroes['questoes_curtas'] += 1
            
            # Elementos
            if any(palavra in texto for palavra in ['tabela', 'quadro']):
                padroes['tem_tabela'] += 1
            
            if any(palavra in texto for palavra in ['gráfico', 'grafico', 'figura']):
                padroes['tem_grafico'] += 1
            
            if any(palavra in texto for palavra in ['código', 'codigo', 'programa', 'função', 'funcao']):
                padroes['tem_codigo'] += 1
            
            if any(palavra in texto for palavra in ['lei', 'artigo', 'inciso', 'constituição', 'decreto']):
                padroes['tem_legislacao'] += 1
            
            # Formato
            if re.search(r'[a-e]\)', texto) or re.search(r'\([a-e]\)', texto):
                padroes['formato_multipla_escolha'] += 1
            
            if any(palavra in texto for palavra in ['certo', 'errado', 'verdadeiro', 'falso']):
                padroes['formato_verdadeiro_falso'] += 1
        
        # Calcular percentuais
        total = len(df)
        for key in padroes:
            percentual = (padroes[key] / total * 100) if total > 0 else 0
            print(f"   {key.replace('_', ' ').title()}: {padroes[key]} ({percentual:.1f}%)")
        
        return padroes
    
    def _analisar_gabaritos(self, df):
        """Analisa distribuição dos gabaritos"""
        
        print("\n✅ ANÁLISE DE GABARITOS:")
        
        df_com_gabarito = df[df['tem_gabarito'] == True]
        
        if len(df_com_gabarito) == 0:
            print("   ⚠️ Nenhum gabarito disponível")
            return {}
        
        gabaritos = df_com_gabarito['resposta_correta'].value_counts()
        
        analise = {}
        for letra, count in gabaritos.items():
            percentual = (count / len(df_com_gabarito) * 100)
            analise[letra] = {
                'quantidade': int(count),
                'percentual': round(percentual, 2)
            }
            print(f"   Alternativa {letra}: {count} vezes ({percentual:.1f}%)")
        
        # Detectar viés
        if analise:
            mais_comum = max(analise.items(), key=lambda x: x[1]['percentual'])
            menos_comum = min(analise.items(), key=lambda x: x[1]['percentual'])
            
            print(f"\n   💡 Mais comum: {mais_comum[0]} ({mais_comum[1]['percentual']:.1f}%)")
            print(f"   💡 Menos comum: {menos_comum[0]} ({menos_comum[1]['percentual']:.1f}%)")
            
            if mais_comum[1]['percentual'] > 25:
                print(f"   ⚠️ ATENÇÃO: Alternativa {mais_comum[0]} aparece muito!")
        
        return analise
    
    def _extrair_palavras_chave(self, df):
        """Extrai palavras-chave mais frequentes"""
        
        print("\n🔤 PALAVRAS-CHAVE MAIS COBRADAS:")
        
        # Stop words em português
        stop_words = {'o', 'a', 'de', 'da', 'do', 'e', 'que', 'para', 'com', 'em', 
                     'é', 'um', 'uma', 'os', 'as', 'dos', 'das', 'ao', 'à', 'pelo',
                     'pela', 'no', 'na', 'se', 'por', 'mais', 'como', 'mas', 'foi',
                     'ou', 'seu', 'sua', 'são', 'ser', 'tem', 'têm', 'ter', 'está'}
        
        todas_palavras = []
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao']).lower()
            palavras = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]{4,}\b', texto)
            palavras = [p for p in palavras if p not in stop_words]
            todas_palavras.extend(palavras)
        
        top_palavras = Counter(todas_palavras).most_common(20)
        
        palavras_chave = {}
        for palavra, freq in top_palavras:
            palavras_chave[palavra] = freq
            print(f"   {palavra}: {freq}x")
        
        return palavras_chave
    
    def _analisar_complexidade(self, df):
        """Analisa complexidade das questões"""
        
        print("\n📊 ANÁLISE DE COMPLEXIDADE:")
        
        complexidades = {
            'simples': 0,
            'media': 0,
            'complexa': 0
        }
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao'])
            
            # Critérios de complexidade
            tamanho = len(texto)
            palavras_complexas = len(re.findall(r'\b\w{10,}\b', texto))
            tem_subordinadas = len(re.findall(r',|;|:', texto))
            
            score = (tamanho / 100) + (palavras_complexas * 2) + tem_subordinadas
            
            if score < 10:
                complexidades['simples'] += 1
            elif score < 25:
                complexidades['media'] += 1
            else:
                complexidades['complexa'] += 1
        
        total = sum(complexidades.values())
        for nivel, count in complexidades.items():
            percentual = (count / total * 100) if total > 0 else 0
            print(f"   {nivel.title()}: {count} ({percentual:.1f}%)")
        
        return complexidades
    
    def _analisar_estilo(self, df):
        """Analisa estilo de redação da banca"""
        
        print("\n✍️ ESTILO DE REDAÇÃO:")
        
        estilos = {
            'formal': 0,
            'tecnico': 0,
            'objetivo': 0,
            'verboso': 0
        }
        
        palavras_formais = ['conforme', 'todavia', 'outrossim', 'destarte', 'portanto']
        palavras_tecnicas = ['procedimento', 'normativo', 'dispositivo', 'jurisprudência']
        
        for _, row in df.iterrows():
            if pd.isna(row.get('conteudo_questao')):
                continue
            
            texto = str(row['conteudo_questao']).lower()
            
            # Detectar estilo
            if any(palavra in texto for palavra in palavras_formais):
                estilos['formal'] += 1
            
            if any(palavra in texto for palavra in palavras_tecnicas):
                estilos['tecnico'] += 1
            
            palavras = texto.split()
            media_palavras_frase = len(palavras) / max(texto.count('.'), 1)
            
            if media_palavras_frase < 15:
                estilos['objetivo'] += 1
            else:
                estilos['verboso'] += 1
        
        total = len(df)
        for estilo, count in estilos.items():
            percentual = (count / total * 100) if total > 0 else 0
            print(f"   {estilo.title()}: {percentual:.1f}%")
        
        return estilos
    
    def _imprimir_analise(self, analise):
        """Imprime resumo da análise"""
        
        stats = analise['estatisticas_gerais']
        
        print(f"\n📈 RESUMO GERAL:")
        print(f"   Total de questões: {stats['total_questoes']}")
        print(f"   Com gabarito: {stats['com_gabarito']} ({stats['percentual_gabarito']:.1f}%)")
        print(f"   Áreas cobertas: {stats['areas_cobertas']}")
        print(f"   Tamanho médio da questão: {stats['tamanho_medio_questao']:.0f} caracteres")
    
    def _analise_comparativa(self):
        """Compara as 3 bancas"""
        
        print("\n\n" + "=" * 60)
        print("📊 ANÁLISE COMPARATIVA: CEBRASPE vs FGV vs FCC")
        print("=" * 60)
        
        if len(self.analises) < 2:
            print("⚠️ Dados insuficientes para comparação")
            return
        
        print("\n🎯 PERFIL DE CADA BANCA:\n")
        
        for banca, analise in self.analises.items():
            print(f"{'─'*60}")
            print(f"📋 {banca}:")
            
            stats = analise['estatisticas_gerais']
            print(f"   • {stats['total_questoes']} questões analisadas")
            print(f"   • Gabaritos: {stats['percentual_gabarito']:.0f}%")
            print(f"   • Tamanho médio: {stats['tamanho_medio_questao']:.0f} caracteres")
            
            # Área mais cobrada
            if analise['distribuicao_areas']:
                top_area = max(analise['distribuicao_areas'].items(), 
                             key=lambda x: x[1]['percentual'])
                print(f"   • Área mais cobrada: {top_area[0]} ({top_area[1]['percentual']:.1f}%)")
            
            # Complexidade predominante
            if analise['complexidade']:
                complexidade = max(analise['complexidade'].items(), key=lambda x: x[1])
                print(f"   • Complexidade: Predominantemente {complexidade[0]}")
            
            print()
    
    def _salvar_relatorio(self):
        """Salva relatório completo em JSON"""
        
        relatorio = {
            'data_analise': datetime.now().isoformat(),
            'total_questoes': len(self.df) if self.df is not None else 0,
            'bancas_analisadas': list(self.analises.keys()),
            'analises': self.analises
        }
        
        with open('relatorio_analise_bancas.json', 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
        
        print("\n💾 Relatório salvo em: relatorio_analise_bancas.json")
        
        # Salvar também em formato legível
        self._salvar_relatorio_markdown()
    
    def _salvar_relatorio_markdown(self):
        """Salva relatório em Markdown"""
        
        md = "# 🎯 RELATÓRIO DE ANÁLISE DAS BANCAS\n\n"
        md += f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        md += "---\n\n"
        
        for banca, analise in self.analises.items():
            md += f"## 📋 {banca}\n\n"
            
            stats = analise['estatisticas_gerais']
            md += f"### Estatísticas Gerais\n\n"
            md += f"- **Total de questões:** {stats['total_questoes']}\n"
            md += f"- **Com gabarito:** {stats['com_gabarito']} ({stats['percentual_gabarito']:.1f}%)\n"
            md += f"- **Áreas cobertas:** {stats['areas_cobertas']}\n"
            md += f"- **Tamanho médio:** {stats['tamanho_medio_questao']:.0f} caracteres\n\n"
            
            # Áreas
            md += f"### Distribuição por Áreas\n\n"
            for area, dados in analise['distribuicao_areas'].items():
                md += f"- **{area}:** {dados['quantidade']} questões ({dados['percentual']:.1f}%)\n"
            md += "\n"
            
            # Gabaritos
            if analise['analise_gabaritos']:
                md += f"### Distribuição de Gabaritos\n\n"
                for letra, dados in analise['analise_gabaritos'].items():
                    md += f"- **{letra}:** {dados['quantidade']}x ({dados['percentual']:.1f}%)\n"
                md += "\n"
            
            # Top palavras
            md += f"### Top 10 Palavras-Chave\n\n"
            top10 = list(analise['palavras_chave'].items())[:10]
            for palavra, freq in top10:
                md += f"- {palavra}: {freq}x\n"
            md += "\n"
            
            md += "---\n\n"
        
        with open('RELATORIO_ANALISE_BANCAS.md', 'w', encoding='utf-8') as f:
            f.write(md)
        
        print("💾 Relatório Markdown salvo em: RELATORIO_ANALISE_BANCAS.md")


def main():
    """Função principal"""
    
    print("=" * 60)
    print("🎯 ANÁLISE COMPLETA DE BANCAS")
    print("   CEBRASPE | FGV | FCC")
    print("=" * 60)
    
    analisador = AnalisadorBancasCompleto()
    
    if analisador.carregar_dados():
        analisador.analisar_todas_bancas()
        
        print("\n\n✅ ANÁLISE CONCLUÍDA!")
        print("\nArquivos gerados:")
        print("   📄 relatorio_analise_bancas.json")
        print("   📄 RELATORIO_ANALISE_BANCAS.md")
    else:
        print("\n⚠️ Execute primeiro:")
        print("   1. BAIXAR_PROVAS_PCI.bat (baixar provas)")
        print("   2. PROCESSAR_QUESTOES_GABARITOS.bat (processar)")
        print("   3. Este script (analisar)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Análise interrompida")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
