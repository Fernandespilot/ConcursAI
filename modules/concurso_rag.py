#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo RAG para o sistema ConcursAI"""

from modules.concurso_embeddings import get_embedder, collection, df_chunks
import json
import re

# 🔹 Função para buscar documentos relevantes
def buscar_documentos(pergunta, orgao="Todos", ano="Todos", cargo="Todos", limite=5):
    """Busca documentos relevantes usando embeddings e filtros"""
    try:
        embedder = get_embedder()
        if collection is None or embedder is None:
            return []
        
        # Preparar filtros de metadados
        where_clause = {}
        if orgao != "Todos" and orgao:
            where_clause["orgao"] = {"$eq": orgao}
        if ano != "Todos" and ano:
            where_clause["ano"] = {"$eq": str(ano)}
        if cargo != "Todos" and cargo:
            where_clause["cargo"] = {"$eq": cargo}
        
        # Buscar documentos similares
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

# 🔹 Modelo de linguagem simples (fallback quando GPT4All não estiver disponível)
def resposta_simples(pergunta, contexto):
    """Gera resposta simples baseada no contexto encontrado"""
    if not contexto:
        return """
        ❌ **Desculpe, não encontrei informações específicas sobre sua pergunta.**
        
        **💡 Dicas:**
        - Tente reformular sua pergunta
        - Verifique os filtros de órgão, ano e cargo
        - Use palavras-chave mais específicas
        
        **📞 Sugestão:** Consulte o site oficial do órgão responsável pelo concurso.
        """
    
    # Análise simples da pergunta
    pergunta_lower = pergunta.lower()
    
    # Respostas baseadas em palavras-chave
    if any(palavra in pergunta_lower for palavra in ['salário', 'remuneração', 'vencimento']):
        resposta = "💰 **Informações sobre Remuneração:**\n\n"
    elif any(palavra in pergunta_lower for palavra in ['inscrição', 'inscriçao', 'como se inscrever']):
        resposta = "📝 **Informações sobre Inscrição:**\n\n"
    elif any(palavra in pergunta_lower for palavra in ['prova', 'exame', 'teste']):
        resposta = "📚 **Informações sobre Provas:**\n\n"
    elif any(palavra in pergunta_lower for palavra in ['requisito', 'formação', 'escolaridade']):
        resposta = "🎓 **Requisitos e Qualificações:**\n\n"
    elif any(palavra in pergunta_lower for palavra in ['cronograma', 'data', 'prazo']):
        resposta = "📅 **Cronograma e Prazos:**\n\n"
    elif any(palavra in pergunta_lower for palavra in ['vaga', 'vagas', 'quantidade']):
        resposta = "👥 **Informações sobre Vagas:**\n\n"
    else:
        resposta = "ℹ️ **Informações Encontradas:**\n\n"
    
    # Adicionar contexto encontrado
    for i, doc in enumerate(contexto[:3], 1):
        doc_clean = re.sub(r'\s+', ' ', doc).strip()
        if len(doc_clean) > 300:
            doc_clean = doc_clean[:300] + "..."
        resposta += f"**{i}.** {doc_clean}\n\n"
    
    resposta += """
    ---
    **⚠️ Importante:** Esta resposta foi gerada automaticamente com base nos documentos encontrados. 
    Para informações oficiais e atualizadas, consulte sempre o edital original do concurso.
    """
    
    return resposta

# 🔹 Função principal de resposta
def responder_interface(orgao, ano, cargo, pergunta, contexto_extra=""):
    """Interface principal para responder perguntas sobre concursos"""
    try:
        if not pergunta or not pergunta.strip():
            return "❓ Por favor, digite uma pergunta sobre concursos públicos."
        
        # Buscar documentos relevantes
        documentos = buscar_documentos(pergunta, orgao, ano, cargo, limite=5)
        
        if not documentos:
            return f"""
            🔍 **Nenhum resultado encontrado para sua busca.**
            
            **Filtros aplicados:**
            - 🏛️ Órgão: {orgao}
            - 📅 Ano: {ano}  
            - 💼 Cargo: {cargo}
            
            **💡 Sugestões:**
            - Tente alterar os filtros para "Todos"
            - Use palavras-chave diferentes
            - Verifique se há dados disponíveis para os filtros selecionados
            
            **📊 Status do sistema:** {len(df_chunks)} documentos disponíveis
            """
        
        # Tentar usar GPT4All se disponível
        try:
            from gpt4all import GPT4All
            
            # Preparar contexto
            contexto_completo = "\n".join(documentos)
            if contexto_extra:
                contexto_completo += f"\n\nContexto da conversa anterior:\n{contexto_extra}"
            
            # Criar prompt estruturado
            prompt = f"""
            Contexto sobre concursos públicos:
            {contexto_completo}
            
            Pergunta do usuário: {pergunta}
            
            Instruções:
            - Responda apenas com base no contexto fornecido
            - Se não houver informação suficiente, diga que não encontrou
            - Seja claro e objetivo
            - Use formatação markdown para melhor legibilidade
            - Cite informações específicas quando disponíveis
            
            Resposta:
            """
            
            modelo = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")
            resposta = modelo.generate(prompt, max_tokens=500, temp=0.1)
            return resposta
            
        except ImportError:
            print("ℹ️ GPT4All não disponível, usando resposta simples")
            return resposta_simples(pergunta, documentos)
        except Exception as e:
            print(f"⚠️ Erro no GPT4All: {e}, usando resposta simples")
            return resposta_simples(pergunta, documentos)
            
    except Exception as e:
        return f"❌ Erro interno: {str(e)[:100]}... Por favor, tente novamente."

# 🔹 Função para obter estatísticas
def obter_estatisticas():
    """Retorna estatísticas dos dados carregados"""
    try:
        stats = {
            "total_documentos": len(df_chunks),
            "orgaos": df_chunks['orgao'].nunique() if 'orgao' in df_chunks.columns else 0,
            "anos": df_chunks['ano'].nunique() if 'ano' in df_chunks.columns else 0,
            "cargos": df_chunks['cargo'].nunique() if 'cargo' in df_chunks.columns else 0,
            "tipos_documento": df_chunks['tipo_documento'].nunique() if 'tipo_documento' in df_chunks.columns else 0
        }
        return stats
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")
        return {"erro": str(e)}
