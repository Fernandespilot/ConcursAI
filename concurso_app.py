#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ConcursAI - Aplicação Principal de Concursos Públicos"""

import sys
import io
# Força UTF-8 no stdout/stderr para suportar emojis no Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import gradio as gr
import os
from dotenv import load_dotenv
from modules.concurso_rag import responder_interface, obter_estatisticas
from modules.concurso_embeddings import df_chunks, collection

load_dotenv()

# Histórico de conversa em memória (lista de dicts)
historico_conversa = []


def _historico_para_chatbot():
    """Converte histórico interno para o formato tuples do Gradio"""
    return [(h["pergunta"], h["resposta"]) for h in historico_conversa]


def responder_com_memoria(orgao, ano, cargo, pergunta):
    """Processa pergunta, salva no histórico e retorna chat atualizado"""
    if not pergunta or not pergunta.strip():
        return _historico_para_chatbot(), ""

    try:
        contexto_extra = "\n".join([
            f"Usuário: {h['pergunta']}\nAssistente: {h['resposta']}"
            for h in historico_conversa[-5:]
        ])
        resposta = responder_interface(orgao, ano, cargo, pergunta, contexto_extra)
        historico_conversa.append({
            "orgao": orgao,
            "ano": ano,
            "cargo": cargo,
            "pergunta": pergunta,
            "resposta": resposta
        })
    except Exception as e:
        historico_conversa.append({
            "orgao": orgao, "ano": ano, "cargo": cargo,
            "pergunta": pergunta,
            "resposta": f"❌ Erro ao processar sua pergunta: {str(e)}"
        })

    return _historico_para_chatbot(), ""


def tentar_novamente():
    """Regera a resposta da última pergunta feita"""
    if not historico_conversa:
        return _historico_para_chatbot()
    ultima = historico_conversa[-1]
    try:
        nova_resposta = responder_interface(
            ultima["orgao"], ultima["ano"], ultima["cargo"],
            ultima["pergunta"], contexto_extra=""
        )
        historico_conversa[-1]["resposta"] = nova_resposta
    except Exception as e:
        historico_conversa[-1]["resposta"] = f"❌ Erro: {str(e)}"
    return _historico_para_chatbot()


def limpar_historico():
    """Limpa todo o histórico de conversa"""
    global historico_conversa
    historico_conversa = []
    return [], ""


def criar_interface():
    # Listas para os dropdowns
    try:
        orgaos = sorted(df_chunks['orgao'].dropna().unique().tolist()) if 'orgao' in df_chunks.columns else []
        anos = sorted(df_chunks['ano'].dropna().unique().tolist(), reverse=True) if 'ano' in df_chunks.columns else []
        cargos = sorted(df_chunks['cargo'].dropna().unique().tolist()) if 'cargo' in df_chunks.columns else []
    except Exception:
        orgaos, anos, cargos = [], [], []

    stats = obter_estatisticas()
    groq_status = "✅ Groq ativo" if stats.get("llm_ativo", "").startswith("Groq") else "⚠️ Sem GROQ_API_KEY — respostas limitadas"

    with gr.Blocks(title="ConcursAI - Assistente de Concursos Públicos") as app:
        gr.Markdown(f"""
# 🎯 ConcursAI — Assistente de Concursos Públicos
Seu assistente inteligente para consultas sobre editais | **{groq_status}**
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🔍 Filtros de Busca")
                orgao_input = gr.Dropdown(
                    choices=["Todos"] + orgaos,
                    value="Todos",
                    label="🏛️ Órgão/Instituição"
                )
                ano_input = gr.Dropdown(
                    choices=["Todos"] + [str(a) for a in anos],
                    value="Todos",
                    label="📅 Ano"
                )
                cargo_input = gr.Dropdown(
                    choices=["Todos"] + cargos,
                    value="Todos",
                    label="💼 Cargo"
                )

            with gr.Column(scale=2):
                gr.Markdown("### 💬 Chat com o Assistente")
                chatbot = gr.Chatbot(height=420, label="Conversa")
                pergunta_input = gr.Textbox(
                    placeholder="Digite sua pergunta sobre concursos públicos...",
                    label="❓ Sua pergunta",
                    lines=2
                )
                with gr.Row():
                    enviar_btn = gr.Button("📤 Enviar", variant="primary")
                    tentar_novamente_btn = gr.Button("🔄 Tentar Novamente")
                    limpar_btn = gr.Button("🗑️ Limpar Chat")

        with gr.Accordion("ℹ️ Informações do Sistema", open=False):
            try:
                total_collection = collection.count()
                gr.Markdown(f"""
- **Documentos carregados:** {len(df_chunks):,}
- **Chunks indexados:** {total_collection:,}
- **LLM:** {stats.get("llm_ativo", "Desconhecido")}
- **Status:** ✅ Sistema funcionando
                """)
            except Exception:
                gr.Markdown("⚠️ Não foi possível carregar dados do sistema")

        with gr.Accordion("💡 Exemplos de Perguntas", open=False):
            exemplos = [
                "Quais são os requisitos para o cargo de Analista?",
                "Qual o salário para o cargo de Técnico?",
                "Quando será a prova do concurso de 2024?",
                "Quais são as disciplinas da prova?",
                "Como fazer a inscrição?",
                "Qual o prazo de validade do concurso?",
                "Há reserva de vagas para PCD?",
                "Quais documentos preciso para a posse?"
            ]
            for exemplo in exemplos:
                gr.Button(f"💭 {exemplo}", size="sm").click(
                    fn=lambda t=exemplo: t,
                    outputs=pergunta_input
                )

        # Eventos
        enviar_btn.click(
            fn=responder_com_memoria,
            inputs=[orgao_input, ano_input, cargo_input, pergunta_input],
            outputs=[chatbot, pergunta_input]
        )
        pergunta_input.submit(
            fn=responder_com_memoria,
            inputs=[orgao_input, ano_input, cargo_input, pergunta_input],
            outputs=[chatbot, pergunta_input]
        )
        tentar_novamente_btn.click(
            fn=tentar_novamente,
            outputs=chatbot
        )
        limpar_btn.click(
            fn=limpar_historico,
            outputs=[chatbot, pergunta_input]
        )

    return app


if __name__ == "__main__":
    print("🚀 Iniciando ConcursAI...")
    try:
        app = criar_interface()
        print("✅ Interface criada com sucesso!")
        app.launch(
            server_name="0.0.0.0",
            server_port=7861,
            share=False,
            debug=False,
            show_error=True,
            theme=gr.themes.Soft()
        )
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        print("📝 Verifique as dependências e se os dados foram processados")
