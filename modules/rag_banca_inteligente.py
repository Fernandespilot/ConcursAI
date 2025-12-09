"""
🤖 RAG INTELIGENTE COM ANÁLISE DE BANCAS POR ÁREA
===================================================
Integração do BancaAreaAnalyzer com o sistema RAG
para responder perguntas específicas sobre padrões de cada banca
"""

import logging
from typing import Dict, List, Optional, Any
import requests
import json
import time

from modules.banca_area_analyzer import get_banca_area_analyzer, AREAS_CONHECIMENTO
from modules.concurso_embeddings import get_embedder, collection
from modules.model_metrics import get_model_metrics

logger = logging.getLogger(__name__)


class RAGBancaInteligente:
    """RAG com análise inteligente de bancas por área"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Inicializa o RAG inteligente"""
        self.ollama_url = ollama_url
        self.banca_analyzer = get_banca_area_analyzer()
        self.embedder = get_embedder()
        
        # Cache de contextos já consultados
        self.cache_contexto = {}
        
        # Sistema de métricas do modelo
        self.metrics = get_model_metrics()
        
        logger.info("✅ RAG Inteligente inicializado com métricas")
    
    
    def processar_pergunta(self, pergunta: str) -> Dict[str, Any]:
        """
        Processa pergunta do usuário e identifica intenção
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            Dicionário com análise da pergunta
        """
        pergunta_lower = pergunta.lower()
        
        # Identificar banca mencionada
        banca = None
        for b in ["cebraspe", "cespe", "fcc", "fgv", "vunesp"]:
            if b in pergunta_lower:
                banca = "CESPE/CEBRASPE" if b in ["cebraspe", "cespe"] else b.upper()
                break
        
        # Identificar área mencionada
        area = None
        for area_nome in AREAS_CONHECIMENTO.keys():
            if area_nome.lower() in pergunta_lower:
                area = area_nome
                break
        
        # Identificar tipo de pergunta
        tipo_pergunta = self._identificar_tipo_pergunta(pergunta_lower)
        
        return {
            "banca": banca,
            "area": area,
            "tipo": tipo_pergunta,
            "pergunta_original": pergunta
        }
    
    
    def _identificar_tipo_pergunta(self, pergunta: str) -> str:
        """Identifica o tipo de pergunta"""
        
        if any(palavra in pergunta for palavra in ["mais cai", "mais cobra", "mais cobrado", "mais frequente"]):
            return "o_que_mais_cai"
        
        elif any(palavra in pergunta for palavra in ["como estudar", "estratégia", "dica", "recomendação"]):
            return "como_estudar"
        
        elif any(palavra in pergunta for palavra in ["dificuldade", "difícil", "nível"]):
            return "dificuldade"
        
        elif any(palavra in pergunta for palavra in ["tempo", "quanto tempo", "duração"]):
            return "tempo_estudo"
        
        elif any(palavra in pergunta for palavra in ["tipo de questão", "formato", "estilo"]):
            return "tipo_questao"
        
        elif any(palavra in pergunta for palavra in ["diferença", "comparar", "vs"]):
            return "comparacao"
        
        else:
            return "geral"
    
    
    def responder(
        self,
        pergunta: str,
        usar_ollama: bool = True,
        limite_contexto: int = 5
    ) -> str:
        """
        Responde pergunta usando análise de bancas + RAG tradicional
        
        Args:
            pergunta: Pergunta do usuário
            usar_ollama: Se True, usa Ollama para gerar resposta
            limite_contexto: Número de documentos para buscar
            
        Returns:
            Resposta formatada
        """
        logger.info(f"🤔 Pergunta: {pergunta}")
        
        # ⏱️ Iniciar rastreamento de tempo total
        start_total = time.time()
        
        # Analisar pergunta
        analise = self.processar_pergunta(pergunta)
        
        banca = analise["banca"]
        area = analise["area"]
        tipo = analise["tipo"]
        
        logger.info(f"📊 Análise: Banca={banca}, Área={area}, Tipo={tipo}")
        
        # Gerar resposta
        resposta = None
        
        # Se banca + área foram identificados, usar análise específica
        if banca and area:
            resposta = self._responder_com_perfil_banca(banca, area, tipo, pergunta)
        
        # Se apenas banca foi identificada
        elif banca:
            resposta = self._responder_apenas_banca(banca, tipo, pergunta)
        
        # Se apenas área foi identificada
        elif area:
            resposta = self._responder_apenas_area(area, tipo, pergunta)
        
        # Resposta genérica usando RAG tradicional
        else:
            resposta = self._responder_rag_tradicional(pergunta, limite_contexto, usar_ollama)
        
        # ⏱️ Calcular tempo total
        total_latency = (time.time() - start_total) * 1000
        
        # 📊 Rastrear métricas (simplificado para respostas diretas)
        self.metrics.track_rag_query(
            pergunta=pergunta,
            resposta=resposta,
            banca=banca or "desconhecida",
            area=area or "geral",
            embedding_latency_ms=0,  # Respostas diretas não usam embedding
            retrieval_latency_ms=0,
            llm_latency_ms=total_latency,
            num_chunks=0,
            avg_similarity=0,
            has_source=True,
            tokens_generated=len(resposta.split()) if resposta else 0
        )
        
        # Tentar validar contra ground truth
        try:
            validation = self.metrics.validator.validate_response(pergunta, resposta)
            if validation:
                logger.info(f"✅ Validação: Keyword Score={validation['keyword_match_score']:.2f}")
        except:
            pass  # Ground truth opcional
        
        return resposta
    
    
    def _responder_com_perfil_banca(
        self,
        banca: str,
        area: str,
        tipo_pergunta: str,
        pergunta: str
    ) -> str:
        """Responde usando perfil específico de banca + área"""
        
        try:
            # Processar se ainda não foi processado
            banca_lower = banca.lower().replace("cespe/cebraspe", "cebraspe")
            
            if banca_lower not in self.banca_analyzer.perfis or \
               area not in self.banca_analyzer.perfis.get(banca_lower, {}):
                logger.info(f"🔄 Processando perfil: {banca} - {area}")
                self.banca_analyzer.processar_banca_area(banca_lower, area)
            
            # Obter perfil
            perfil = self.banca_analyzer.perfis.get(banca_lower, {}).get(area)
            
            if not perfil or "erro" in perfil:
                return f"""
❌ **Ainda não tenho dados suficientes sobre {banca} na área de {area}.**

💡 **O que posso fazer:**
1. Adicione PDFs de provas desta banca em: `provas/{banca_lower}/{area.lower()}/`
2. Execute: `python -c "from modules.banca_area_analyzer import *; get_banca_area_analyzer().processar_banca_area('{banca_lower}', '{area}')"`
3. Faça sua pergunta novamente!

📊 Bancas disponíveis: {', '.join(self.banca_analyzer.perfis.keys())}
                """
            
            # Gerar resposta baseada no tipo de pergunta
            if tipo_pergunta == "o_que_mais_cai":
                return self._resposta_mais_cai(perfil)
            
            elif tipo_pergunta == "como_estudar":
                return self._resposta_como_estudar(perfil)
            
            elif tipo_pergunta == "dificuldade":
                return self._resposta_dificuldade(perfil)
            
            elif tipo_pergunta == "tempo_estudo":
                return self._resposta_tempo(perfil)
            
            elif tipo_pergunta == "tipo_questao":
                return self._resposta_tipo_questao(perfil)
            
            else:
                # Resposta completa
                return self.banca_analyzer._formatar_resumo_perfil(perfil)
        
        except Exception as e:
            logger.error(f"❌ Erro ao responder com perfil: {e}")
            return f"❌ Erro ao processar sua pergunta: {e}"
    
    
    def _resposta_mais_cai(self, perfil: Dict) -> str:
        """Formata resposta sobre o que mais cai"""
        
        banca = perfil["banca"]
        area = perfil["area"]
        
        resposta = f"""
🎯 **O QUE MAIS CAI: {banca.upper()} - {area}**
{'='*70}

📊 **Baseado na análise de {perfil['total_questoes']} questões de {perfil['total_provas_analisadas']} provas**

📚 **TOP 5 DISCIPLINAS:**
"""
        
        disciplinas = list(perfil["distribuicao_disciplinas"].items())[:5]
        for i, (disc, dados) in enumerate(disciplinas, 1):
            barra = "█" * int(dados['percentual'] / 2)
            resposta += f"\n{i}. **{disc}**\n"
            resposta += f"   {barra} {dados['percentual']:.1f}% ({dados['count']} questões)\n"
        
        resposta += f"\n🔑 **TOP 10 TEMAS MAIS COBRADOS:**\n"
        temas = perfil["temas_mais_cobrados"][:10]
        for i, tema_data in enumerate(temas, 1):
            resposta += f"{i:2d}. {tema_data['tema']} (apareceu {tema_data['frequencia']}x)\n"
        
        # Padrões específicos
        padroes = perfil.get("padroes_especificos", {})
        carac = padroes.get("caracteristicas_predominantes", {})
        
        if area == "Tecnologia" and carac:
            resposta += f"\n💻 **TECNOLOGIAS MAIS COBRADAS:**\n"
            
            if "linguagens_mais_cobradas" in carac:
                resposta += f"\n📝 Linguagens:\n"
                for ling, freq in list(carac["linguagens_mais_cobradas"].items())[:5]:
                    resposta += f"  • {ling.upper()}: {freq} menções\n"
            
            if "frameworks_mencionados" in carac:
                resposta += f"\n🛠️ Frameworks:\n"
                for fw, freq in list(carac["frameworks_mencionados"].items())[:5]:
                    resposta += f"  • {fw}: {freq} menções\n"
        
        elif area == "Jurídica" and carac:
            resposta += f"\n⚖️ **PADRÃO JURÍDICO:**\n"
            resposta += f"  • Lei seca: {carac.get('percentual_lei_seca', 0):.1f}%\n"
            resposta += f"  • Jurisprudência: {carac.get('percentual_jurisprudencia', 0):.1f}%\n"
            resposta += f"  • Súmulas: {carac.get('percentual_sumula', 0):.1f}%\n"
            resposta += f"  • **Foco principal: {carac.get('foco', 'N/A').upper()}**\n"
        
        # Recomendação
        resposta += f"\n💡 **RECOMENDAÇÃO:**\n"
        rec = perfil.get("recomendacoes", {})
        foco = rec.get("foco_disciplinas", [])[:3]
        resposta += f"Foque nestas 3 disciplinas: **{', '.join(foco)}**\n"
        
        return resposta
    
    
    def _resposta_como_estudar(self, perfil: Dict) -> str:
        """Formata resposta sobre como estudar"""
        
        banca = perfil["banca"]
        area = perfil["area"]
        
        resposta = f"""
📖 **COMO ESTUDAR: {banca.upper()} - {area}**
{'='*70}

🎯 **ESTRATÉGIAS ESPECÍFICAS:**

"""
        
        rec = perfil.get("recomendacoes", {})
        estrategias = rec.get("estrategia_estudo", [])
        
        for est in estrategias:
            resposta += f"{est}\n"
        
        # Tempo
        tempo = rec.get("tempo_sugerido", {})
        resposta += f"""

⏱️ **CRONOGRAMA SUGERIDO:**
  • **{tempo.get('horas_semanais', 0)} horas por semana**
  • **{tempo.get('meses_preparo_sugerido', 0)} meses de preparação**
  • Distribuição: {tempo.get('distribuicao', 'N/A')}

"""
        
        # Materiais
        materiais = rec.get("materiais_recomendados", [])
        if materiais:
            resposta += f"📚 **MATERIAIS RECOMENDADOS:**\n"
            for mat in materiais:
                resposta += f"{mat}\n"
        
        # Disciplinas prioritárias
        foco_disc = rec.get("foco_disciplinas", [])
        if foco_disc:
            resposta += f"\n🎯 **FOQUE NESTAS DISCIPLINAS:**\n"
            for i, disc in enumerate(foco_disc, 1):
                resposta += f"{i}. {disc}\n"
        
        # Temas prioritários
        temas_prior = rec.get("temas_prioritarios", [])
        if temas_prior:
            resposta += f"\n🔑 **TEMAS PRIORITÁRIOS:**\n"
            for tema in temas_prior:
                resposta += f"  • {tema}\n"
        
        return resposta
    
    
    def _resposta_dificuldade(self, perfil: Dict) -> str:
        """Formata resposta sobre dificuldade"""
        
        resposta = f"""
📊 **NÍVEL DE DIFICULDADE: {perfil['banca'].upper()} - {perfil['area']}**
{'='*70}

"""
        
        dificuldades = perfil["distribuicao_dificuldade"]
        
        for nivel, dados in sorted(dificuldades.items(), key=lambda x: x[1]['percentual'], reverse=True):
            emoji = "🔴" if nivel == "Avançado" else "🟡" if nivel == "Intermediário" else "🟢"
            barra = "█" * int(dados['percentual'] / 2)
            
            resposta += f"{emoji} **{nivel}**: {barra} {dados['percentual']:.1f}%\n"
        
        # Identificar predominante
        dif_predominante = max(dificuldades.items(), key=lambda x: x[1]['percentual'])
        
        resposta += f"\n**Nível predominante: {dif_predominante[0]}** ({dif_predominante[1]['percentual']:.1f}%)\n"
        
        # Recomendação
        rec = perfil.get("recomendacoes", {})
        resposta += f"\n💡 **Preparação esperada:** {rec.get('dificuldade_esperada', 'Média')}\n"
        
        return resposta
    
    
    def _resposta_tempo(self, perfil: Dict) -> str:
        """Formata resposta sobre tempo de estudo"""
        
        rec = perfil.get("recomendacoes", {})
        tempo = rec.get("tempo_sugerido", {})
        
        resposta = f"""
⏱️ **TEMPO DE ESTUDO RECOMENDADO: {perfil['banca'].upper()} - {perfil['area']}**
{'='*70}

📅 **CRONOGRAMA:**
  • **{tempo.get('horas_semanais', 0)} horas por semana**
  • **{tempo.get('meses_preparo_sugerido', 0)} meses de preparação total**

📊 **DISTRIBUIÇÃO:**
  {tempo.get('distribuicao', 'N/A')}

💡 **RECOMENDAÇÕES:**
  • Estude TODOS OS DIAS, mesmo que sejam 30min
  • Revise conteúdos antigos a cada 3 dias
  • Faça simulados semanalmente nas últimas 4 semanas
  • Reserve 1 dia por semana para descanso

🎯 **FOCO:**
"""
        
        # Disciplinas prioritárias
        foco = rec.get("foco_disciplinas", [])[:3]
        for i, disc in enumerate(foco, 1):
            resposta += f"  {i}. {disc}\n"
        
        return resposta
    
    
    def _resposta_tipo_questao(self, perfil: Dict) -> str:
        """Formata resposta sobre tipos de questão"""
        
        resposta = f"""
📝 **TIPOS DE QUESTÃO: {perfil['banca'].upper()} - {perfil['area']}**
{'='*70}

"""
        
        tipos = perfil["distribuicao_tipos"]
        
        for tipo, dados in sorted(tipos.items(), key=lambda x: x[1]['percentual'], reverse=True):
            barra = "█" * int(dados['percentual'] / 2)
            resposta += f"• **{tipo}**: {barra} {dados['percentual']:.1f}% ({dados['count']} questões)\n"
        
        # Dica específica por tipo predominante
        tipo_predominante = max(tipos.items(), key=lambda x: x[1]['percentual'])[0]
        
        resposta += f"\n💡 **DICA para {tipo_predominante}:**\n"
        
        if "Certo/Errado" in tipo_predominante or "Certo ou Errado" in tipo_predominante:
            resposta += """
  ⚠️ Atenção a palavras como: SEMPRE, NUNCA, APENAS, SOMENTE
  ⚠️ Cuidado com NEGAÇÃO DUPLA (INCORRETO, EXCETO)
  ✅ Marque ERRADO se tiver UMA palavra errada
  ✅ Se tiver dúvida, deixe em branco (não perde ponto)
"""
        elif "Múltipla Escolha" in tipo_predominante:
            resposta += """
  ✅ Elimine alternativas absurdas primeiro
  ✅ Fique entre 2 alternativas e escolha a mais completa
  ✅ Cuidado com alternativas com palavras absolutas
  ✅ A alternativa correta geralmente é a mais longa
"""
        
        return resposta
    
    
    def _responder_apenas_banca(self, banca: str, tipo: str, pergunta: str) -> str:
        """Responde quando apenas banca foi identificada"""
        
        # Listar áreas disponíveis para esta banca
        banca_lower = banca.lower().replace("cespe/cebraspe", "cebraspe")
        
        areas_disponiveis = self.banca_analyzer.perfis.get(banca_lower, {}).keys()
        
        if not areas_disponiveis:
            return f"""
❓ **Você perguntou sobre {banca}, mas não especificou a área.**

💡 **Especifique a área para uma resposta mais precisa:**
  • Tecnologia
  • Jurídica
  • Saúde
  • Administrativa
  • Conhecimentos Gerais

**Exemplo:** "O que a {banca} mais cobra em Tecnologia?"
            """
        
        # Se há áreas processadas, listar
        resposta = f"""
📊 **PERFIL GERAL DA BANCA: {banca.upper()}**
{'='*60}

Tenho dados sobre esta banca nas seguintes áreas:
"""
        
        for area in areas_disponiveis:
            perfil = self.banca_analyzer.perfis[banca_lower][area]
            resposta += f"\n✅ **{area}**: {perfil.get('total_questoes', 0)} questões analisadas"
        
        resposta += f"\n\n💡 **Faça uma pergunta específica sobre alguma área!**"
        resposta += f"\nExemplo: 'O que a {banca} mais cobra em {list(areas_disponiveis)[0]}?'"
        
        return resposta
    
    
    def _responder_apenas_area(self, area: str, tipo: str, pergunta: str) -> str:
        """Responde quando apenas área foi identificada"""
        
        return f"""
❓ **Você perguntou sobre {area}, mas não especificou a banca.**

💡 **Especifique a banca para uma resposta precisa:**
  • CESPE/CEBRASPE
  • FCC
  • FGV
  • VUNESP

**Exemplo:** "O que o CESPE mais cobra em {area}?"

📊 Cada banca tem padrões MUITO diferentes, mesmo na mesma área!
        """
    
    
    def _responder_rag_tradicional(
        self,
        pergunta: str,
        limite: int,
        usar_ollama: bool
    ) -> str:
        """Responde usando RAG tradicional (embeddings + Ollama)"""
        
        logger.info("🔍 Usando RAG tradicional...")
        
        try:
            # ⏱️ Fase 1: Embedding
            start_embedding = time.time()
            
            # Buscar documentos relevantes
            if collection is None:
                return "❌ Sistema RAG tradicional não está configurado. Use perguntas sobre bancas específicas!"
            
            resultados = collection.query(
                query_texts=[pergunta],
                n_results=limite
            )
            
            embedding_latency = (time.time() - start_embedding) * 1000
            
            # 📊 Rastrear embedding
            self.metrics.track_embedding(
                text=pergunta,
                model="nomic-embed-text",
                start_time=start_embedding,
                dimensions=384,
                success=True
            )
            
            # ⏱️ Fase 2: Retrieval
            start_retrieval = time.time()
            
            documentos = resultados['documents'][0] if resultados['documents'] else []
            distances = resultados.get('distances', [[]])[0] if resultados.get('distances') else []
            
            retrieval_latency = (time.time() - start_retrieval) * 1000
            
            if not documentos:
                return """
❓ **Não encontrei informações específicas.**

💡 **Dica:** Faça perguntas sobre bancas e áreas específicas:
  • "O que o CESPE mais cobra em Tecnologia?"
  • "Como estudar para FCC na área Jurídica?"
  • "Qual a dificuldade da FGV em Saúde?"
                """
            
            # Calcular similarity média
            avg_similarity = (1 - (sum(distances) / len(distances))) if distances else 0.5
            
            # ⏱️ Fase 3: LLM Generation
            start_llm = time.time()
            
            # Usar Ollama se disponível
            if usar_ollama:
                resposta = self._gerar_resposta_ollama(pergunta, documentos)
            else:
                resposta = self._gerar_resposta_simples(documentos)
            
            llm_latency = (time.time() - start_llm) * 1000
            
            # 📊 Rastrear query RAG completa
            self.metrics.track_rag_query(
                pergunta=pergunta,
                resposta=resposta,
                banca="geral",
                area="geral",
                embedding_latency_ms=embedding_latency,
                retrieval_latency_ms=retrieval_latency,
                llm_latency_ms=llm_latency,
                num_chunks=len(documentos),
                avg_similarity=avg_similarity,
                has_source=True,
                tokens_generated=len(resposta.split())
            )
            
            logger.info(f"⏱️ Latências: Embedding={embedding_latency:.0f}ms, Retrieval={retrieval_latency:.0f}ms, LLM={llm_latency:.0f}ms")
            
            return resposta
        
        except Exception as e:
            logger.error(f"❌ Erro no RAG tradicional: {e}")
            return f"❌ Erro: {e}"
    
    
    def _gerar_resposta_ollama(self, pergunta: str, contexto: List[str]) -> str:
        """Gera resposta usando Ollama"""
        
        try:
            start_llm = time.time()
            
            contexto_texto = "\n\n".join(contexto[:3])
            
            prompt = f"""Você é um assistente especializado em concursos públicos.

Contexto:
{contexto_texto}

Pergunta: {pergunta}

Responda de forma clara e objetiva, usando apenas as informações do contexto fornecido.
Se não houver informação suficiente, seja honesto e diga isso.
"""
            
            # Calcular tokens do prompt (aproximação)
            prompt_tokens = len(prompt.split())
            
            resposta = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.1:8b-instruct-q4_K_M",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                },
                timeout=30
            )
            
            if resposta.status_code == 200:
                resposta_texto = resposta.json()["response"]
                
                # 📊 Rastrear métricas do LLM
                self.metrics.track_llm_query(
                    pergunta=pergunta,
                    resposta=resposta_texto,
                    model="llama3.1:8b-instruct-q4_K_M",
                    start_time=start_llm,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=len(resposta_texto.split()),
                    temperature=0.3
                )
                
                return resposta_texto
            else:
                return self._gerar_resposta_simples(contexto)
        
        except Exception as e:
            logger.error(f"❌ Erro no Ollama: {e}")
            return self._gerar_resposta_simples(contexto)
    
    
    def _gerar_resposta_simples(self, contexto: List[str]) -> str:
        """Gera resposta simples sem LLM"""
        
        resposta = "📚 **Informações encontradas:**\n\n"
        
        for i, doc in enumerate(contexto[:3], 1):
            doc_clean = doc.strip()
            if len(doc_clean) > 300:
                doc_clean = doc_clean[:300] + "..."
            
            resposta += f"**{i}.** {doc_clean}\n\n"
        
        return resposta


# ============================================
# 🔧 FUNÇÃO AUXILIAR
# ============================================

def get_rag_inteligente(ollama_url: str = "http://localhost:11434") -> RAGBancaInteligente:
    """Retorna instância do RAG inteligente"""
    return RAGBancaInteligente(ollama_url=ollama_url)


if __name__ == "__main__":
    # Teste
    logging.basicConfig(level=logging.INFO)
    
    rag = get_rag_inteligente()
    
    perguntas_teste = [
        "O que o CESPE mais cobra em Tecnologia?",
        "Como estudar para FCC em Jurídica?",
        "Qual a dificuldade da FGV?",
        "Quanto tempo preciso estudar para VUNESP em Administrativa?"
    ]
    
    for pergunta in perguntas_teste:
        print(f"\n{'='*70}")
        print(f"❓ {pergunta}")
        print("="*70)
        
        resposta = rag.responder(pergunta, usar_ollama=False)
        print(resposta)
