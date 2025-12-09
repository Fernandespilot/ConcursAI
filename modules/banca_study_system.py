"""
🎯 SISTEMA DE ESTUDO DE BANCAS - ConcursAI
==========================================
Integração completa: análise de bancas + chunking de PDFs
para gerar perfis de estudo personalizados
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import numpy as np

# Módulos internos
from modules.banca_analyzer import get_banca_analyzer, BancaAnalyzer
from modules.smart_pdf_chunker import get_smart_chunker, SmartPDFChunker

logger = logging.getLogger(__name__)


class BancaStudySystem:
    """Sistema completo de estudo de bancas"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Inicializa o sistema de estudo"""
        self.banca_analyzer = get_banca_analyzer()
        self.pdf_chunker = get_smart_chunker()
        self.ollama_url = ollama_url
        
        # Armazenar perfis de bancas gerados
        self.perfis_bancas = {}
        
        # Armazenar provas processadas por banca
        self.provas_por_banca = defaultdict(list)
        
        logger.info("✅ Sistema de Estudo de Bancas inicializado")
    
    def processar_provas_banca(
        self,
        pdf_paths: List[str],
        banca: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Processa múltiplas provas de uma banca
        
        Args:
            pdf_paths: Lista de caminhos para PDFs
            banca: Nome da banca
            metadata: Metadados adicionais
            
        Returns:
            Relatório de processamento
        """
        try:
            logger.info(f"🔄 Processando {len(pdf_paths)} provas da banca {banca}")
            
            resultados = []
            chunks_todos = []
            
            for pdf_path in pdf_paths:
                if not os.path.exists(pdf_path):
                    logger.warning(f"⚠️ Arquivo não encontrado: {pdf_path}")
                    continue
                
                # Processar PDF
                resultado = self.pdf_chunker.process_pdf(
                    pdf_path,
                    tipo_doc="prova",
                    banca=banca,
                    metadata=metadata
                )
                
                if resultado["success"]:
                    resultados.append(resultado)
                    chunks_todos.extend(resultado["chunks"])
                    
                    # Armazenar por banca
                    self.provas_por_banca[banca].append({
                        "arquivo": resultado["arquivo"],
                        "chunks": resultado["chunks"],
                        "estatisticas": resultado["estatisticas"]
                    })
            
            # Gerar perfil da banca baseado nos chunks
            perfil = self._gerar_perfil_banca(banca, chunks_todos)
            self.perfis_bancas[banca] = perfil
            
            return {
                "success": True,
                "banca": banca,
                "total_provas_processadas": len(resultados),
                "total_questoes": len(chunks_todos),
                "perfil_banca": perfil,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar provas da banca {banca}: {e}")
            return {
                "success": False,
                "erro": str(e)
            }
    
    def _gerar_perfil_banca(self, banca: str, chunks: List[Dict]) -> Dict[str, Any]:
        """
        Gera perfil completo da banca baseado nas questões processadas
        
        Args:
            banca: Nome da banca
            chunks: Lista de chunks processados
            
        Returns:
            Perfil detalhado da banca
        """
        perfil = {
            "banca": banca,
            "total_questoes_analisadas": len(chunks),
            "distribuicao_disciplinas": {},
            "distribuicao_dificuldade": {},
            "distribuicao_tipos": {},
            "temas_frequentes": [],
            "caracteristicas_predominantes": {},
            "padroes_identificados": {},
            "recomendacoes_estudo": {},
            "estatisticas_avancadas": {},
            "gerado_em": datetime.now().isoformat()
        }
        
        if not chunks:
            return perfil
        
        # 1. Distribuições básicas
        disciplinas = Counter()
        dificuldades = Counter()
        tipos_questao = Counter()
        todos_temas = []
        caracteristicas = defaultdict(int)
        
        for chunk in chunks:
            cat = chunk.get("categoria", {})
            
            if "disciplina" in cat:
                disciplinas[cat["disciplina"]] += 1
            if "dificuldade" in cat:
                dificuldades[cat["dificuldade"]] += 1
            if "tipo_questao" in cat:
                tipos_questao[cat["tipo_questao"]] += 1
            if "temas" in cat:
                todos_temas.extend(cat["temas"])
            if "caracteristicas" in cat:
                for key, value in cat["caracteristicas"].items():
                    if value:
                        caracteristicas[key] += 1
        
        # Converter para percentuais
        total = len(chunks)
        perfil["distribuicao_disciplinas"] = {
            disc: {
                "count": count,
                "percentual": round((count / total) * 100, 2)
            }
            for disc, count in disciplinas.most_common()
        }
        
        perfil["distribuicao_dificuldade"] = {
            dif: {
                "count": count,
                "percentual": round((count / total) * 100, 2)
            }
            for dif, count in dificuldades.most_common()
        }
        
        perfil["distribuicao_tipos"] = {
            tipo: {
                "count": count,
                "percentual": round((count / total) * 100, 2)
            }
            for tipo, count in tipos_questao.most_common()
        }
        
        # 2. Temas mais frequentes
        temas_counter = Counter(todos_temas)
        perfil["temas_frequentes"] = [
            {
                "tema": tema,
                "frequencia": count,
                "percentual": round((count / len(todos_temas)) * 100, 2) if todos_temas else 0
            }
            for tema, count in temas_counter.most_common(10)
        ]
        
        # 3. Características predominantes
        perfil["caracteristicas_predominantes"] = {
            carac: {
                "count": count,
                "percentual": round((count / total) * 100, 2)
            }
            for carac, count in caracteristicas.items()
        }
        
        # 4. Padrões identificados (análise com IA)
        perfil["padroes_identificados"] = self._identificar_padroes(chunks, banca)
        
        # 5. Estatísticas avançadas
        perfil["estatisticas_avancadas"] = self._calcular_estatisticas_avancadas(chunks)
        
        # 6. Recomendações personalizadas
        perfil["recomendacoes_estudo"] = self._gerar_recomendacoes_personalizadas(perfil, banca)
        
        return perfil
    
    def _identificar_padroes(self, chunks: List[Dict], banca: str) -> Dict[str, Any]:
        """Identifica padrões específicos da banca"""
        padroes = {
            "tamanho_medio_questao": 0,
            "usa_contextualizacao": 0,
            "menciona_jurisprudencia": 0,
            "tem_pegadinhas": 0,
            "questoes_longas_percentual": 0,
            "palavras_chave_frequentes": []
        }
        
        total = len(chunks)
        if total == 0:
            return padroes
        
        tamanhos = []
        contextualizacao = 0
        jurisprudencia = 0
        pegadinhas = 0
        longas = 0
        todas_palavras = []
        
        for chunk in chunks:
            # Tamanho
            tamanho = chunk["metadata"].get("tamanho_palavras", 0)
            tamanhos.append(tamanho)
            
            if tamanho > 100:
                longas += 1
            
            # Características
            carac = chunk.get("categoria", {}).get("caracteristicas", {})
            if carac.get("tem_contexto"):
                contextualizacao += 1
            if carac.get("tem_jurisprudencia"):
                jurisprudencia += 1
            if carac.get("tem_negacao") or carac.get("tem_excecao"):
                pegadinhas += 1
            
            # Palavras do conteúdo
            palavras = chunk["conteudo"].lower().split()
            todas_palavras.extend(palavras)
        
        padroes["tamanho_medio_questao"] = round(np.mean(tamanhos), 2) if tamanhos else 0
        padroes["usa_contextualizacao"] = round((contextualizacao / total) * 100, 2)
        padroes["menciona_jurisprudencia"] = round((jurisprudencia / total) * 100, 2)
        padroes["tem_pegadinhas"] = round((pegadinhas / total) * 100, 2)
        padroes["questoes_longas_percentual"] = round((longas / total) * 100, 2)
        
        # Palavras mais frequentes (excluindo stopwords básicas)
        stopwords = {'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'ao'}
        palavras_filtradas = [p for p in todas_palavras if len(p) > 3 and p not in stopwords]
        palavras_counter = Counter(palavras_filtradas)
        
        padroes["palavras_chave_frequentes"] = [
            {"palavra": palavra, "frequencia": freq}
            for palavra, freq in palavras_counter.most_common(20)
        ]
        
        return padroes
    
    def _calcular_estatisticas_avancadas(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Calcula estatísticas avançadas"""
        stats = {
            "complexidade_media": 0,
            "variacao_dificuldade": 0,
            "diversidade_tematica": 0,
            "taxa_questoes_avancadas": 0,
            "score_padrao_banca_medio": 0
        }
        
        if not chunks:
            return stats
        
        # Análises detalhadas de cada questão
        analises = []
        for chunk in chunks:
            texto = chunk["conteudo"]
            banca = chunk["metadata"].get("banca", "")
            
            analise = self.banca_analyzer.analisar_estilo_questao(texto, banca)
            analises.append(analise)
        
        # Complexidade média
        complexidades = [a["complexidade_estimada"] for a in analises]
        stats["complexidade_media"] = round(np.mean(complexidades), 2) if complexidades else 0
        stats["variacao_dificuldade"] = round(np.std(complexidades), 2) if complexidades else 0
        
        # Taxa de questões avançadas
        avancadas = sum(1 for a in analises if a["nivel_dificuldade"] == "Avançado")
        stats["taxa_questoes_avancadas"] = round((avancadas / len(analises)) * 100, 2)
        
        # Score médio de aderência ao padrão
        scores = [a["score_padrao_banca"] for a in analises if "score_padrao_banca" in a]
        stats["score_padrao_banca_medio"] = round(np.mean(scores), 2) if scores else 0
        
        # Diversidade temática (número de disciplinas únicas)
        disciplinas_unicas = set(a["disciplina_provavel"] for a in analises)
        stats["diversidade_tematica"] = len(disciplinas_unicas)
        
        return stats
    
    def _gerar_recomendacoes_personalizadas(self, perfil: Dict, banca: str) -> Dict[str, Any]:
        """Gera recomendações de estudo personalizadas"""
        recomendacoes = {
            "prioridade_disciplinas": [],
            "foco_dificuldade": "",
            "estrategias_especificas": [],
            "materiais_recomendados": [],
            "tempo_estudo_sugerido": {},
            "alertas_importantes": []
        }
        
        # 1. Prioridade de disciplinas (top 5)
        disciplinas = perfil.get("distribuicao_disciplinas", {})
        disciplinas_ordenadas = sorted(
            disciplinas.items(),
            key=lambda x: x[1]["percentual"],
            reverse=True
        )[:5]
        
        recomendacoes["prioridade_disciplinas"] = [
            {
                "disciplina": disc,
                "peso": f"{data['percentual']}%",
                "total_questoes": data["count"]
            }
            for disc, data in disciplinas_ordenadas
        ]
        
        # 2. Foco de dificuldade
        dificuldades = perfil.get("distribuicao_dificuldade", {})
        if dificuldades:
            dif_principal = max(dificuldades.items(), key=lambda x: x[1]["percentual"])
            recomendacoes["foco_dificuldade"] = f"{dif_principal[0]} ({dif_principal[1]['percentual']}% das questões)"
        
        # 3. Estratégias específicas baseadas nos padrões
        padroes = perfil.get("padroes_identificados", {})
        
        if padroes.get("questoes_longas_percentual", 0) > 50:
            recomendacoes["estrategias_especificas"].append(
                "⏱️ Pratique leitura dinâmica - mais de 50% das questões são longas"
            )
        
        if padroes.get("tem_pegadinhas", 0) > 40:
            recomendacoes["estrategias_especificas"].append(
                "🎯 ATENÇÃO: Esta banca usa muitas pegadinhas! Leia TODAS as alternativas com calma"
            )
        
        if padroes.get("menciona_jurisprudencia", 0) > 30:
            recomendacoes["estrategias_especificas"].append(
                "⚖️ Estude jurisprudência atualizada (STF/STJ) - é muito cobrada"
            )
        
        if padroes.get("usa_contextualizacao", 0) > 60:
            recomendacoes["estrategias_especificas"].append(
                "📖 Questões muito contextualizadas - pratique interpretação de cenários"
            )
        
        # 4. Materiais recomendados
        tipo_questao_principal = perfil.get("distribuicao_tipos", {})
        if tipo_questao_principal:
            tipo = max(tipo_questao_principal.items(), key=lambda x: x[1]["percentual"])[0]
            recomendacoes["materiais_recomendados"].append(
                f"📚 Foque em questões do tipo: {tipo}"
            )
        
        recomendacoes["materiais_recomendados"].extend([
            f"📝 Resolva MUITAS questões anteriores da {banca}",
            "🎓 Estude pelos temas mais frequentes identificados",
            "⏰ Faça simulados cronometrados"
        ])
        
        # 5. Tempo de estudo sugerido
        for disc, data in disciplinas_ordenadas[:5]:
            recomendacoes["tempo_estudo_sugerido"][disc] = f"{data['percentual']}% do tempo total"
        
        # 6. Alertas importantes
        stats_avanc = perfil.get("estatisticas_avancadas", {})
        if stats_avanc.get("taxa_questoes_avancadas", 0) > 50:
            recomendacoes["alertas_importantes"].append(
                "🔴 BANCA DIFÍCIL: Mais de 50% das questões são de nível avançado"
            )
        
        if stats_avanc.get("complexidade_media", 0) > 8.0:
            recomendacoes["alertas_importantes"].append(
                "⚠️ Complexidade alta - reserve tempo extra de preparação"
            )
        
        return recomendacoes
    
    def gerar_relatorio_completo_banca(self, banca: str) -> Dict[str, Any]:
        """
        Gera relatório completo de uma banca
        
        Args:
            banca: Nome da banca
            
        Returns:
            Relatório completo
        """
        if banca not in self.perfis_bancas:
            return {
                "erro": f"Banca {banca} não possui perfil gerado. Processe provas primeiro."
            }
        
        perfil = self.perfis_bancas[banca]
        provas = self.provas_por_banca.get(banca, [])
        
        # Buscar parâmetros da banca no analyzer
        parametros_banca = self.banca_analyzer.BANCA_PARAMETERS.get(banca, {})
        
        relatorio = {
            "banca": banca,
            "data_geracao": datetime.now().isoformat(),
            
            "resumo_executivo": {
                "total_provas_analisadas": len(provas),
                "total_questoes": perfil["total_questoes_analisadas"],
                "disciplina_principal": self._get_disciplina_principal(perfil),
                "nivel_dificuldade_geral": self._get_nivel_geral(perfil),
                "tipo_questao_predominante": self._get_tipo_predominante(perfil)
            },
            
            "parametros_banca": parametros_banca,
            "perfil_detalhado": perfil,
            "provas_processadas": [
                {
                    "arquivo": p["arquivo"],
                    "total_questoes": len(p["chunks"]),
                    "estatisticas": p["estatisticas"]
                }
                for p in provas
            ],
            
            "analise_comparativa": self._comparar_com_outras_bancas(banca),
            
            "plano_estudo_sugerido": self._gerar_plano_estudo(perfil, banca)
        }
        
        return relatorio
    
    def _get_disciplina_principal(self, perfil: Dict) -> str:
        """Obtém disciplina com maior percentual"""
        discs = perfil.get("distribuicao_disciplinas", {})
        if discs:
            return max(discs.items(), key=lambda x: x[1]["percentual"])[0]
        return "N/A"
    
    def _get_nivel_geral(self, perfil: Dict) -> str:
        """Obtém nível de dificuldade geral"""
        stats = perfil.get("estatisticas_avancadas", {})
        complexidade = stats.get("complexidade_media", 0)
        
        if complexidade >= 8.0:
            return "Alto"
        elif complexidade >= 6.0:
            return "Médio"
        else:
            return "Básico"
    
    def _get_tipo_predominante(self, perfil: Dict) -> str:
        """Obtém tipo de questão predominante"""
        tipos = perfil.get("distribuicao_tipos", {})
        if tipos:
            return max(tipos.items(), key=lambda x: x[1]["percentual"])[0]
        return "N/A"
    
    def _comparar_com_outras_bancas(self, banca: str) -> Dict[str, Any]:
        """Compara banca atual com outras bancas conhecidas"""
        comparacoes = {}
        
        bancas_comparar = ["CESPE/CEBRASPE", "FCC", "FGV", "VUNESP"]
        bancas_comparar = [b for b in bancas_comparar if b != banca]
        
        for outra_banca in bancas_comparar[:2]:  # Limitar a 2 comparações
            comp = self.banca_analyzer.comparar_bancas(banca, outra_banca)
            comparacoes[outra_banca] = comp
        
        return comparacoes
    
    def _gerar_plano_estudo(self, perfil: Dict, banca: str) -> Dict[str, Any]:
        """Gera plano de estudo detalhado"""
        plano = {
            "duracao_sugerida": "3-6 meses",
            "horas_semanais": "20-30 horas",
            "fases": []
        }
        
        # Fase 1: Base teórica
        disciplinas_top = perfil.get("distribuicao_disciplinas", {})
        disciplinas_ordenadas = sorted(
            disciplinas_top.items(),
            key=lambda x: x[1]["percentual"],
            reverse=True
        )[:3]
        
        plano["fases"].append({
            "fase": "1 - Base Teórica (40% do tempo)",
            "objetivo": "Dominar conceitos fundamentais",
            "disciplinas_foco": [disc for disc, _ in disciplinas_ordenadas],
            "atividades": [
                "Estudar teoria completa",
                "Fazer resumos e mapas mentais",
                "Revisar legislação atualizada"
            ]
        })
        
        # Fase 2: Prática intensiva
        plano["fases"].append({
            "fase": "2 - Prática Intensiva (40% do tempo)",
            "objetivo": "Resolver muitas questões da banca",
            "atividades": [
                f"Resolver questões anteriores da {banca}",
                "Analisar padrões de cobrança",
                "Identificar pegadinhas comuns",
                "Revisar erros sistematicamente"
            ]
        })
        
        # Fase 3: Simulados e ajustes finais
        plano["fases"].append({
            "fase": "3 - Simulados e Revisão (20% do tempo)",
            "objetivo": "Consolidar conhecimento e treinar tempo",
            "atividades": [
                "Simulados completos cronometrados",
                "Revisão dos temas mais fracos",
                "Treinar gerenciamento de tempo",
                "Reforço nas disciplinas com maior peso"
            ]
        })
        
        return plano
    
    def exportar_perfil(self, banca: str, formato: str = "json") -> str:
        """
        Exporta perfil da banca
        
        Args:
            banca: Nome da banca
            formato: "json" ou "txt"
            
        Returns:
            String com dados exportados
        """
        relatorio = self.gerar_relatorio_completo_banca(banca)
        
        if formato == "json":
            return json.dumps(relatorio, indent=2, ensure_ascii=False)
        elif formato == "txt":
            return self._formatar_relatorio_texto(relatorio)
        
        return str(relatorio)
    
    def _formatar_relatorio_texto(self, relatorio: Dict) -> str:
        """Formata relatório em texto legível"""
        linhas = []
        linhas.append("=" * 80)
        linhas.append(f"RELATÓRIO DE ANÁLISE - BANCA {relatorio['banca']}")
        linhas.append("=" * 80)
        linhas.append("")
        
        resumo = relatorio.get("resumo_executivo", {})
        linhas.append("RESUMO EXECUTIVO:")
        linhas.append(f"  Total de Provas: {resumo.get('total_provas_analisadas', 0)}")
        linhas.append(f"  Total de Questões: {resumo.get('total_questoes', 0)}")
        linhas.append(f"  Disciplina Principal: {resumo.get('disciplina_principal', 'N/A')}")
        linhas.append(f"  Nível Geral: {resumo.get('nivel_dificuldade_geral', 'N/A')}")
        linhas.append("")
        
        # Mais seções conforme necessário...
        
        return "\n".join(linhas)


# Instância global
study_system = None

def get_study_system() -> BancaStudySystem:
    """Obtém instância global do sistema de estudo"""
    global study_system
    if study_system is None:
        study_system = BancaStudySystem()
    return study_system


# Teste
if __name__ == "__main__":
    print("🎯 SISTEMA DE ESTUDO DE BANCAS - ConcursAI")
    print("=" * 60)
    
    system = get_study_system()
    print("✅ Sistema inicializado")
    
    # Exemplo de uso (requer PDFs reais)
    # pdfs = ["prova1.pdf", "prova2.pdf", "prova3.pdf"]
    # resultado = system.processar_provas_banca(pdfs, "CESPE/CEBRASPE")
    # relatorio = system.gerar_relatorio_completo_banca("CESPE/CEBRASPE")
    # print(json.dumps(relatorio, indent=2, ensure_ascii=False))
