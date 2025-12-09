"""
🎓 ANALISADOR AVANÇADO DE BANCAS - ConcursAI
=============================================
Sistema completo de análise de padrões de bancas organizadoras
com Machine Learning e Deep Learning
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import Counter, defaultdict
import re

# ML e NLP
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class BancaAnalyzer:
    """Analisador avançado de padrões de bancas"""
    
    # Parâmetros específicos por banca
    BANCA_PARAMETERS = {
        "CESPE/CEBRASPE": {
            "tipo_questao": "certo_errado",
            "complexidade_media": 8.5,  # escala 1-10
            "tamanho_medio_questao": 150,  # palavras
            "caracteristicas": {
                "usa_negacao_dupla": True,
                "contextualiza_muito": True,
                "exige_jurisprudencia": True,
                "pegadinhas_frequentes": True,
                "atualizado_legislacao": True
            },
            "disciplinas_peso": {
                "direito_constitucional": 25,
                "direito_administrativo": 22,
                "portugues": 18,
                "raciocinio_logico": 12,
                "conhecimentos_especificos": 23
            },
            "palavras_chave": [
                "exceto", "incorreto", "assinale", "conforme", 
                "segundo", "jurisprudência", "súmula"
            ],
            "padroes_texto": [
                r"(Considerando|Acerca|A respeito|Com relação)",
                r"(exceto|EXCETO|à exceção)",
                r"(incorreto|INCORRETO|errado|ERRADO)"
            ],
            "nivel_dificuldade_chunks": {
                "basico": 15,  # % de chunks básicos
                "intermediario": 35,
                "avancado": 50
            }
        },
        
        "FCC": {
            "tipo_questao": "multipla_escolha",
            "complexidade_media": 7.0,
            "tamanho_medio_questao": 80,
            "caracteristicas": {
                "usa_negacao_dupla": False,
                "contextualiza_muito": False,
                "exige_jurisprudencia": False,
                "pegadinhas_frequentes": False,
                "atualizado_legislacao": True
            },
            "disciplinas_peso": {
                "direito": 30,
                "portugues": 20,
                "raciocinio_logico": 15,
                "conhecimentos_especificos": 35
            },
            "palavras_chave": [
                "de acordo com", "segundo", "conforme", "artigo", "lei"
            ],
            "padroes_texto": [
                r"(De acordo com|Segundo|Conforme)",
                r"(artigo|Art\.|Lei nº)",
                r"(Assinale a alternativa)"
            ],
            "nivel_dificuldade_chunks": {
                "basico": 25,
                "intermediario": 50,
                "avancado": 25
            }
        },
        
        "FGV": {
            "tipo_questao": "multipla_escolha_interpretativa",
            "complexidade_media": 8.0,
            "tamanho_medio_questao": 120,
            "caracteristicas": {
                "usa_negacao_dupla": True,
                "contextualiza_muito": True,
                "exige_jurisprudencia": True,
                "pegadinhas_frequentes": True,
                "atualizado_legislacao": True
            },
            "disciplinas_peso": {
                "direito": 28,
                "portugues": 22,
                "administracao": 20,
                "conhecimentos_especificos": 30
            },
            "palavras_chave": [
                "analise", "interprete", "considerando", "contexto", "situação"
            ],
            "padroes_texto": [
                r"(Analise|Interprete|Considerando)",
                r"(contexto|situação|cenário)",
                r"(É correto|É incorreto)"
            ],
            "nivel_dificuldade_chunks": {
                "basico": 20,
                "intermediario": 40,
                "avancado": 40
            }
        },
        
        "VUNESP": {
            "tipo_questao": "multipla_escolha",
            "complexidade_media": 6.5,
            "tamanho_medio_questao": 70,
            "caracteristicas": {
                "usa_negacao_dupla": False,
                "contextualiza_muito": False,
                "exige_jurisprudencia": False,
                "pegadinhas_frequentes": False,
                "atualizado_legislacao": True
            },
            "disciplinas_peso": {
                "conhecimentos_especificos": 40,
                "portugues": 20,
                "raciocinio_logico": 15,
                "conhecimentos_gerais": 25
            },
            "palavras_chave": [
                "assinale", "de acordo", "conforme", "correto", "incorreto"
            ],
            "padroes_texto": [
                r"(Assinale a alternativa)",
                r"(É correto afirmar)",
                r"(De acordo com)"
            ],
            "nivel_dificuldade_chunks": {
                "basico": 30,
                "intermediario": 50,
                "avancado": 20
            }
        }
    }
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Inicializa o analisador de bancas"""
        self.ollama_url = ollama_url
        self.vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 3))
        self.patterns_learned = {}
        logger.info("✅ BancaAnalyzer inicializado")
    
    def identificar_banca(self, texto: str) -> Tuple[str, float]:
        """
        Identifica a banca organizadora a partir do texto
        
        Args:
            texto: Texto da prova/questão
            
        Returns:
            Tupla (nome_banca, confianca)
        """
        texto_upper = texto.upper()
        scores = {}
        
        # Buscar por menções diretas
        for banca_nome in self.BANCA_PARAMETERS.keys():
            sigla = banca_nome.split('/')[0]
            if sigla in texto_upper:
                return (banca_nome, 0.95)
        
        # Análise de padrões linguísticos
        for banca_nome, params in self.BANCA_PARAMETERS.items():
            score = 0
            
            # Verificar palavras-chave
            palavras_encontradas = sum(
                1 for palavra in params["palavras_chave"]
                if palavra.lower() in texto.lower()
            )
            score += (palavras_encontradas / len(params["palavras_chave"])) * 0.4
            
            # Verificar padrões regex
            padroes_encontrados = sum(
                1 for padrao in params["padroes_texto"]
                if re.search(padrao, texto, re.IGNORECASE)
            )
            score += (padroes_encontrados / len(params["padroes_texto"])) * 0.3
            
            # Analisar tamanho médio
            palavras = len(texto.split())
            diff_tamanho = abs(palavras - params["tamanho_medio_questao"]) / params["tamanho_medio_questao"]
            score += max(0, (1 - diff_tamanho)) * 0.3
            
            scores[banca_nome] = score
        
        # Retornar banca com maior score
        if scores:
            melhor_banca = max(scores.items(), key=lambda x: x[1])
            return (melhor_banca[0], melhor_banca[1])
        
        return ("Desconhecida", 0.0)
    
    def analisar_estilo_questao(self, texto_questao: str, banca: str) -> Dict[str, Any]:
        """
        Analisa o estilo de uma questão específica
        
        Args:
            texto_questao: Texto da questão
            banca: Nome da banca
            
        Returns:
            Análise detalhada do estilo
        """
        params = self.BANCA_PARAMETERS.get(banca, {})
        
        analise = {
            "banca": banca,
            "tamanho_palavras": len(texto_questao.split()),
            "tamanho_caracteres": len(texto_questao),
            "complexidade_estimada": self._calcular_complexidade(texto_questao),
            "caracteristicas_detectadas": {},
            "nivel_dificuldade": "",
            "disciplina_provavel": "",
            "score_padrao_banca": 0.0
        }
        
        # Detectar características
        if params:
            carac = params["caracteristicas"]
            analise["caracteristicas_detectadas"] = {
                "negacao_dupla": self._tem_negacao_dupla(texto_questao) if carac.get("usa_negacao_dupla") else False,
                "muito_contextualizado": len(texto_questao.split()) > 100 if carac.get("contextualiza_muito") else False,
                "menciona_jurisprudencia": bool(re.search(r"(jurisprudência|súmula|STF|STJ)", texto_questao, re.I)),
                "tem_pegadinha": self._detectar_pegadinha(texto_questao),
            }
            
            # Calcular score de aderência ao padrão da banca
            analise["score_padrao_banca"] = self._calcular_score_padrao(texto_questao, params)
            
            # Inferir nível de dificuldade
            analise["nivel_dificuldade"] = self._inferir_nivel_dificuldade(
                analise["complexidade_estimada"],
                params["complexidade_media"]
            )
        
        # Inferir disciplina
        analise["disciplina_provavel"] = self._inferir_disciplina(texto_questao)
        
        return analise
    
    def _calcular_complexidade(self, texto: str) -> float:
        """Calcula complexidade textual (escala 1-10)"""
        # Fatores de complexidade
        palavras = texto.split()
        n_palavras = len(palavras)
        
        # Tamanho médio das palavras
        tamanho_medio_palavra = sum(len(p) for p in palavras) / max(n_palavras, 1)
        
        # Contagem de vírgulas e pontuações (indicador de períodos compostos)
        pontuacoes = texto.count(',') + texto.count(';')
        
        # Palavras técnicas/complexas (> 12 letras)
        palavras_complexas = sum(1 for p in palavras if len(p) > 12)
        
        # Fórmula de complexidade
        complexidade = (
            (n_palavras / 100) * 2 +  # Tamanho do texto
            (tamanho_medio_palavra / 10) * 3 +  # Tamanho médio das palavras
            (pontuacoes / 10) * 2 +  # Complexidade sintática
            (palavras_complexas / n_palavras) * 3 if n_palavras > 0 else 0  # Vocabulário técnico
        )
        
        return min(10.0, max(1.0, complexidade))
    
    def _tem_negacao_dupla(self, texto: str) -> bool:
        """Detecta presença de negação dupla"""
        padroes_negacao = [
            r"não.*(?:incorreto|errado)",
            r"exceto.*(?:não|nunca)",
            r"(?:sem|nem).*(?:sem|nem)"
        ]
        return any(re.search(p, texto, re.I) for p in padroes_negacao)
    
    def _detectar_pegadinha(self, texto: str) -> bool:
        """Detecta possíveis pegadinhas na questão"""
        indicadores_pegadinha = [
            r"(?:sempre|nunca|jamais|todo|nenhum)",  # Absolutos
            r"(?:exceto|à exceção|salvo)",  # Exceções
            r"(?:pode|deve|deve sempre|pode sempre)",  # Modalidades
            r"(?:somente|apenas|exclusivamente)"  # Restrições
        ]
        return any(re.search(p, texto, re.I) for p in indicadores_pegadinha)
    
    def _calcular_score_padrao(self, texto: str, params: Dict) -> float:
        """Calcula score de aderência ao padrão da banca"""
        score = 0.0
        total_checks = 0
        
        # Check palavras-chave
        palavras_chave_presentes = sum(
            1 for palavra in params["palavras_chave"]
            if palavra.lower() in texto.lower()
        )
        score += (palavras_chave_presentes / max(len(params["palavras_chave"]), 1)) * 40
        total_checks += 40
        
        # Check padrões regex
        padroes_presentes = sum(
            1 for padrao in params["padroes_texto"]
            if re.search(padrao, texto, re.I)
        )
        score += (padroes_presentes / max(len(params["padroes_texto"]), 1)) * 30
        total_checks += 30
        
        # Check tamanho
        n_palavras = len(texto.split())
        tamanho_esperado = params["tamanho_medio_questao"]
        diff = abs(n_palavras - tamanho_esperado) / tamanho_esperado
        score += max(0, (1 - diff) * 30)
        total_checks += 30
        
        return (score / total_checks) * 100 if total_checks > 0 else 0.0
    
    def _inferir_nivel_dificuldade(self, complexidade_calc: float, complexidade_banca: float) -> str:
        """Infere nível de dificuldade da questão"""
        ratio = complexidade_calc / complexidade_banca if complexidade_banca > 0 else 1.0
        
        if ratio < 0.7:
            return "Básico"
        elif ratio < 1.2:
            return "Intermediário"
        else:
            return "Avançado"
    
    def _inferir_disciplina(self, texto: str) -> str:
        """Infere a disciplina provável da questão"""
        disciplinas_keywords = {
            "Direito Constitucional": ["constituição", "constitucional", "direitos fundamentais", "CF/88", "artigo 5º"],
            "Direito Administrativo": ["administrativo", "servidor público", "licitação", "contrato administrativo"],
            "Português": ["oração", "verbo", "sujeito", "predicado", "concordância", "regência", "ortografia"],
            "Raciocínio Lógico": ["lógica", "premissa", "conclusão", "silogismo", "sequência", "padrão"],
            "Matemática": ["equação", "função", "porcentagem", "regra de três", "probabilidade"],
            "Informática": ["computador", "software", "hardware", "internet", "sistema", "rede"],
            "Conhecimentos Gerais": ["história", "geografia", "atualidades", "política", "economia"]
        }
        
        texto_lower = texto.lower()
        scores = {}
        
        for disciplina, keywords in disciplinas_keywords.items():
            score = sum(1 for kw in keywords if kw in texto_lower)
            if score > 0:
                scores[disciplina] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return "Conhecimentos Específicos"
    
    def gerar_estatisticas_banca(self, questoes: List[str], banca: str) -> Dict[str, Any]:
        """
        Gera estatísticas completas sobre um conjunto de questões de uma banca
        
        Args:
            questoes: Lista de textos de questões
            banca: Nome da banca
            
        Returns:
            Estatísticas detalhadas
        """
        if not questoes:
            return {"erro": "Nenhuma questão fornecida"}
        
        analises = [self.analisar_estilo_questao(q, banca) for q in questoes]
        
        # Compilar estatísticas
        stats = {
            "banca": banca,
            "total_questoes_analisadas": len(questoes),
            "complexidade_media": np.mean([a["complexidade_estimada"] for a in analises]),
            "tamanho_medio_palavras": np.mean([a["tamanho_palavras"] for a in analises]),
            "distribuicao_dificuldade": Counter([a["nivel_dificuldade"] for a in analises]),
            "distribuicao_disciplinas": Counter([a["disciplina_provavel"] for a in analises]),
            "score_medio_padrao": np.mean([a["score_padrao_banca"] for a in analises]),
            "caracteristicas_predominantes": self._agregar_caracteristicas(analises),
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
    
    def _agregar_caracteristicas(self, analises: List[Dict]) -> Dict[str, float]:
        """Agrega características de múltiplas análises"""
        carac_total = defaultdict(int)
        n_analises = len(analises)
        
        for analise in analises:
            for key, value in analise["caracteristicas_detectadas"].items():
                if value:
                    carac_total[key] += 1
        
        # Converter para percentuais
        return {
            key: (count / n_analises) * 100
            for key, count in carac_total.items()
        }
    
    def recomendar_estrategia_estudo(self, banca: str, disciplinas: List[str] = None) -> Dict[str, Any]:
        """
        Recomenda estratégia de estudo baseada na banca
        
        Args:
            banca: Nome da banca
            disciplinas: Lista de disciplinas de interesse (opcional)
            
        Returns:
            Recomendações de estudo
        """
        params = self.BANCA_PARAMETERS.get(banca)
        
        if not params:
            return {"erro": f"Banca {banca} não reconhecida"}
        
        recomendacoes = {
            "banca": banca,
            "tipo_questao": params["tipo_questao"],
            "complexidade_esperada": params["complexidade_media"],
            "estrategias_principais": [],
            "distribuicao_tempo_estudo": {},
            "dicas_especificas": [],
            "alertas": []
        }
        
        # Estratégias baseadas no tipo de questão
        if params["tipo_questao"] == "certo_errado":
            recomendacoes["estrategias_principais"].extend([
                "Praticar muitas questões de Certo/Errado",
                "Atenção redobrada aos detalhes do enunciado",
                "Identificar palavras absolutas (sempre, nunca, todo)",
                "Cuidado com negações duplas"
            ])
        elif params["tipo_questao"] == "multipla_escolha":
            recomendacoes["estrategias_principais"].extend([
                "Ler todas as alternativas antes de responder",
                "Eliminar alternativas claramente erradas",
                "Buscar a alternativa mais completa e precisa"
            ])
        
        # Distribuição de tempo por disciplina
        if disciplinas:
            total_peso = sum(params["disciplinas_peso"].get(d, 10) for d in disciplinas)
            recomendacoes["distribuicao_tempo_estudo"] = {
                disc: f"{(params['disciplinas_peso'].get(disc, 10) / total_peso) * 100:.1f}%"
                for disc in disciplinas
            }
        else:
            recomendacoes["distribuicao_tempo_estudo"] = {
                disc: f"{peso}%"
                for disc, peso in sorted(params["disciplinas_peso"].items(), key=lambda x: x[1], reverse=True)
            }
        
        # Dicas específicas baseadas em características
        carac = params["caracteristicas"]
        if carac.get("usa_negacao_dupla"):
            recomendacoes["dicas_especificas"].append("⚠️ Atenção a negações duplas - leia COM CALMA")
        if carac.get("contextualiza_muito"):
            recomendacoes["dicas_especificas"].append("📖 Questões longas - pratique leitura dinâmica")
        if carac.get("exige_jurisprudencia"):
            recomendacoes["dicas_especificas"].append("⚖️ Estude jurisprudência atualizada (STF/STJ)")
        if carac.get("pegadinhas_frequentes"):
            recomendacoes["dicas_especificas"].append("🎯 Banca com pegadinhas - treine MUITO com questões anteriores")
        
        # Alertas baseados em complexidade
        if params["complexidade_media"] > 8.0:
            recomendacoes["alertas"].append("🔴 BANCA DE ALTA DIFICULDADE - reserve tempo extra de preparação")
        elif params["complexidade_media"] < 6.0:
            recomendacoes["alertas"].append("🟢 Banca de dificuldade moderada - foco em disciplinas básicas")
        
        return recomendacoes
    
    def comparar_bancas(self, banca1: str, banca2: str) -> Dict[str, Any]:
        """
        Compara duas bancas em detalhes
        
        Args:
            banca1: Nome da primeira banca
            banca2: Nome da segunda banca
            
        Returns:
            Comparação detalhada
        """
        params1 = self.BANCA_PARAMETERS.get(banca1)
        params2 = self.BANCA_PARAMETERS.get(banca2)
        
        if not params1 or not params2:
            return {"erro": "Uma ou ambas as bancas não foram encontradas"}
        
        comparacao = {
            "banca_1": {
                "nome": banca1,
                "tipo_questao": params1["tipo_questao"],
                "complexidade": params1["complexidade_media"],
                "tamanho_medio": params1["tamanho_medio_questao"]
            },
            "banca_2": {
                "nome": banca2,
                "tipo_questao": params2["tipo_questao"],
                "complexidade": params2["complexidade_media"],
                "tamanho_medio": params2["tamanho_medio_questao"]
            },
            "diferencas_principais": [],
            "semelhanças": [],
            "recomendacao_transicao": ""
        }
        
        # Identificar diferenças
        if params1["tipo_questao"] != params2["tipo_questao"]:
            comparacao["diferencas_principais"].append(
                f"Tipo de questão: {params1['tipo_questao']} vs {params2['tipo_questao']}"
            )
        
        diff_complexidade = abs(params1["complexidade_media"] - params2["complexidade_media"])
        if diff_complexidade > 1.0:
            mais_dificil = banca1 if params1["complexidade_media"] > params2["complexidade_media"] else banca2
            comparacao["diferencas_principais"].append(
                f"Complexidade: {mais_dificil} é significativamente mais difícil"
            )
        
        # Identificar semelhanças
        carac1 = params1["caracteristicas"]
        carac2 = params2["caracteristicas"]
        
        for key in carac1.keys():
            if carac1.get(key) == carac2.get(key) and carac1.get(key):
                comparacao["semelhanças"].append(f"Ambas {key.replace('_', ' ')}")
        
        # Recomendação de transição
        if params1["complexidade_media"] > params2["complexidade_media"]:
            comparacao["recomendacao_transicao"] = f"Transição de {banca1} para {banca2}: Ajustar para questões mais diretas e objetivas"
        else:
            comparacao["recomendacao_transicao"] = f"Transição de {banca1} para {banca2}: Preparar-se para maior complexidade e interpretação"
        
        return comparacao


# Instância global
banca_analyzer = None

def get_banca_analyzer() -> BancaAnalyzer:
    """Obtém instância global do analisador de bancas"""
    global banca_analyzer
    if banca_analyzer is None:
        banca_analyzer = BancaAnalyzer()
    return banca_analyzer


# Testes
if __name__ == "__main__":
    print("🎓 TESTE DO ANALISADOR DE BANCAS\n")
    
    analyzer = get_banca_analyzer()
    
    # Teste 1: Identificar banca
    texto_cespe = """
    Considerando a jurisprudência do STF sobre direitos fundamentais,
    é INCORRETO afirmar que, exceto nos casos previstos em lei...
    """
    
    banca, conf = analyzer.identificar_banca(texto_cespe)
    print(f"✅ Banca identificada: {banca} (confiança: {conf:.2f})")
    
    # Teste 2: Analisar estilo
    analise = analyzer.analisar_estilo_questao(texto_cespe, "CESPE/CEBRASPE")
    print(f"\n📊 Análise de estilo:")
    print(f"  Complexidade: {analise['complexidade_estimada']:.2f}")
    print(f"  Nível: {analise['nivel_dificuldade']}")
    print(f"  Disciplina: {analise['disciplina_provavel']}")
    
    # Teste 3: Recomendações
    recom = analyzer.recomendar_estrategia_estudo("CESPE/CEBRASPE")
    print(f"\n🎯 Recomendações CESPE:")
    for dica in recom["dicas_especificas"][:3]:
        print(f"  {dica}")
