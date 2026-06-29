#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo RAG para o sistema ConcursAI"""

from modules.concurso_embeddings import get_embedder, collection, df_chunks
import os
import re

# Prompt do sistema — define comportamento e tom do assistente
SYSTEM_PROMPT = """Você é o ConcursAI, um assistente especializado em concursos públicos brasileiros.

Suas responsabilidades:
- Responder perguntas sobre editais, vagas, salários, requisitos e cronogramas de concursos
- Usar APENAS as informações do contexto fornecido
- Ser claro, objetivo e organizado nas respostas
- Citar os dados específicos encontrados (datas, valores, requisitos)
- Quando não houver informação suficiente no contexto, dizer claramente que não encontrou

Formato de resposta:
- Use markdown para organizar (negrito, listas, etc.)
- Destaque datas, salários e números importantes
- Seja direto e evite respostas genéricas
- Não invente informações que não estão no contexto

Lembre-se: você representa uma ferramenta confiável para candidatos a concursos públicos.
Precisão e clareza são essenciais."""


def _get_groq_client():
    """Retorna cliente Groq se GROQ_API_KEY estiver configurada"""
    try:
        import groq
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            return groq.Groq(api_key=api_key)
    except ImportError:
        pass
    return None


def buscar_documentos(pergunta, orgao="Todos", ano="Todos", cargo="Todos", limite=5):
    """Busca documentos relevantes usando embeddings e filtros"""
    try:
        embedder = get_embedder()
        if collection is None or embedder is None:
            return []

        where_clause = {}
        if orgao != "Todos" and orgao:
            where_clause["orgao"] = {"$eq": orgao}
        if ano != "Todos" and ano:
            where_clause["ano"] = {"$eq": str(ano)}
        if cargo != "Todos" and cargo:
            where_clause["cargo"] = {"$eq": cargo}

        if where_clause:
            resultados = collection.query(
                query_texts=[pergunta],
                n_results=limite,
                where=where_clause
            )
        else:
            resultados = collection.query(
                query_texts=[pergunta],
                n_results=limite
            )

        return resultados['documents'][0] if resultados['documents'] else []

    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        return []


def _gerar_resposta_groq(pergunta, contexto_completo, contexto_extra=""):
    """Gera resposta usando Groq API com o system prompt configurado"""
    cliente = _get_groq_client()
    if not cliente:
        return None

    historico_bloco = f"HISTÓRICO DA CONVERSA:\n{contexto_extra}\n" if contexto_extra else ""
    mensagem_usuario = f"""CONTEXTO DOS EDITAIS/CONCURSOS:
{contexto_completo}

{historico_bloco}PERGUNTA: {pergunta}"""

    try:
        response = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": mensagem_usuario}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"⚠️ Erro no Groq: {e}")
        return None


def _gerar_resposta_gpt4all(pergunta, contexto_completo):
    """Fallback para GPT4All local"""
    try:
        from gpt4all import GPT4All

        prompt = f"""{SYSTEM_PROMPT}

CONTEXTO:
{contexto_completo}

PERGUNTA: {pergunta}

RESPOSTA:"""

        modelo = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")
        return modelo.generate(prompt, max_tokens=500, temp=0.1)
    except Exception:
        return None


def _resposta_simples(pergunta, documentos):
    """Resposta de último recurso por palavras-chave (sem LLM)"""
    if not documentos:
        return (
            "❌ **Não encontrei informações sobre sua pergunta.**\n\n"
            "💡 **Dicas:** Reformule a pergunta, ajuste os filtros ou use palavras-chave mais específicas.\n\n"
            "📞 Para dados oficiais, consulte sempre o edital original no site do órgão."
        )

    pergunta_lower = pergunta.lower()
    if any(p in pergunta_lower for p in ['salário', 'remuneração', 'vencimento']):
        cabecalho = "💰 **Informações sobre Remuneração:**\n\n"
    elif any(p in pergunta_lower for p in ['inscrição', 'como se inscrever']):
        cabecalho = "📝 **Informações sobre Inscrição:**\n\n"
    elif any(p in pergunta_lower for p in ['prova', 'exame', 'teste']):
        cabecalho = "📚 **Informações sobre Provas:**\n\n"
    elif any(p in pergunta_lower for p in ['requisito', 'formação', 'escolaridade']):
        cabecalho = "🎓 **Requisitos e Qualificações:**\n\n"
    elif any(p in pergunta_lower for p in ['cronograma', 'data', 'prazo']):
        cabecalho = "📅 **Cronograma e Prazos:**\n\n"
    elif any(p in pergunta_lower for p in ['vaga', 'vagas']):
        cabecalho = "👥 **Informações sobre Vagas:**\n\n"
    else:
        cabecalho = "ℹ️ **Informações Encontradas:**\n\n"

    resposta = cabecalho
    for i, doc in enumerate(documentos[:3], 1):
        doc_clean = re.sub(r'\s+', ' ', doc).strip()
        if len(doc_clean) > 300:
            doc_clean = doc_clean[:300] + "..."
        resposta += f"**{i}.** {doc_clean}\n\n"

    resposta += (
        "\n---\n"
        "⚠️ *Resposta gerada automaticamente. "
        "Configure GROQ_API_KEY no arquivo .env para respostas com IA completa.*"
    )
    return resposta


def responder_interface(orgao, ano, cargo, pergunta, contexto_extra=""):
    """Interface principal para responder perguntas sobre concursos"""
    try:
        if not pergunta or not pergunta.strip():
            return "❓ Por favor, digite uma pergunta sobre concursos públicos."

        documentos = buscar_documentos(pergunta, orgao, ano, cargo, limite=5)

        if not documentos:
            return (
                f"🔍 **Nenhum resultado encontrado.**\n\n"
                f"**Filtros aplicados:** Órgão: {orgao} | Ano: {ano} | Cargo: {cargo}\n\n"
                f"💡 Tente alterar os filtros para 'Todos' ou use outras palavras-chave.\n\n"
                f"📊 Documentos disponíveis no sistema: {len(df_chunks)}"
            )

        contexto_completo = "\n\n---\n\n".join(documentos)

        # 1. Tentar Groq (LLM na nuvem, mais preciso)
        resposta = _gerar_resposta_groq(pergunta, contexto_completo, contexto_extra)
        if resposta:
            return resposta

        # 2. Tentar GPT4All (LLM local)
        resposta = _gerar_resposta_gpt4all(pergunta, contexto_completo)
        if resposta:
            return resposta

        # 3. Fallback por palavras-chave
        return _resposta_simples(pergunta, documentos)

    except Exception as e:
        return f"❌ Erro interno: {str(e)[:100]}... Por favor, tente novamente."


def obter_estatisticas():
    """Retorna estatísticas dos dados carregados"""
    try:
        stats = {
            "total_documentos": len(df_chunks),
            "orgaos": df_chunks['orgao'].nunique() if 'orgao' in df_chunks.columns else 0,
            "anos": df_chunks['ano'].nunique() if 'ano' in df_chunks.columns else 0,
            "cargos": df_chunks['cargo'].nunique() if 'cargo' in df_chunks.columns else 0,
            "llm_ativo": "Groq" if _get_groq_client() else "Fallback (sem API key)"
        }
        return stats
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")
        return {"erro": str(e)}
