#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ConcursAI - Aplicação Principal de Concursos Públicos"""

import gradio as gr
import os
import sys
from modules.concurso_rag import responder_interface
from modules.concurso_embeddings import df_chunks, collection

# 🔹 Histórico de conversa em memória
historico_conversa = []

# 🔹 Função principal com memória
def responder_com_memoria(orgao, ano, cargo, pergunta):
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
        return resposta, atualizar_chat()
    except Exception as e:
        return f"❌ Erro: {str(e)}", []

# 🔁 Correção da última resposta
def tentar_novamente():
    if not historico_conversa:
        return "⚠️ Nenhuma pergunta anterior encontrada.", []
    ultima = historico_conversa[-1]
    nova_resposta = responder_interface(
        ultima["orgao"], ultima["ano"], ultima["cargo"], ultima["pergunta"], contexto_extra=""
    )
    historico_conversa[-1]["resposta"] = nova_resposta
    return nova_resposta, atualizar_chat()

# 🔄 Atualizar histórico de chat
def atualizar_chat():
    return [[h["pergunta"], h["resposta"]] for h in historico_conversa]

# 🗑️ Limpar histórico
def limpar_historico():
    global historico_conversa
    historico_conversa = []
    return [], ""

# 🎨 Interface Gradio
def criar_interface():
    # Obter listas únicas para os dropdowns
    try:
        orgaos = sorted(df_chunks['orgao'].dropna().unique().tolist()) if 'orgao' in df_chunks.columns else ["Todos"]
        anos = sorted(df_chunks['ano'].dropna().unique().tolist(), reverse=True) if 'ano' in df_chunks.columns else ["Todos"]
        cargos = sorted(df_chunks['cargo'].dropna().unique().tolist()) if 'cargo' in df_chunks.columns else ["Todos"]
    except:
        orgaos = ["Todos"]
        anos = ["Todos"] 
        cargos = ["Todos"]

    with gr.Blocks(title="ConcursAI - Assistente de Concursos Públicos", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🎯 ConcursAI - Assistente de Concursos Públicos
        ### Seu assistente inteligente para consultas sobre editais de concursos públicos!
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
                    choices=["Todos"] + [str(ano) for ano in anos], 
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
                chatbot = gr.Chatbot(height=400, label="Conversa", type="messages")
                pergunta_input = gr.Textbox(
                    placeholder="Digite sua pergunta sobre concursos públicos...", 
                    label="❓ Sua pergunta",
                    lines=2
                )
                
                with gr.Row():
                    enviar_btn = gr.Button("📤 Enviar", variant="primary")
                    tentar_novamente_btn = gr.Button("🔄 Tentar Novamente")
                    limpar_btn = gr.Button("🗑️ Limpar Chat")

        # 📊 Informações do sistema
        with gr.Accordion("ℹ️ Informações do Sistema", open=False):
            try:
                total_docs = len(df_chunks)
                total_collection = collection.count()
                gr.Markdown(f"""
                - **Total de documentos carregados:** {total_docs:,}
                - **Total de chunks indexados:** {total_collection:,}
                - **Status:** ✅ Sistema funcionando
                """)
            except:
                gr.Markdown("⚠️ Problemas ao carregar dados do sistema")

        # 📝 Exemplos de perguntas
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
            
            for i, exemplo in enumerate(exemplos):
                def criar_exemplo(texto):
                    def preencher():
                        return texto
                    return preencher
                
                gr.Button(f"💭 {exemplo}", size="sm").click(
                    fn=criar_exemplo(exemplo),
                    outputs=pergunta_input
                )

        # 🔗 Conectar eventos
        enviar_btn.click(
            fn=responder_com_memoria,
            inputs=[orgao_input, ano_input, cargo_input, pergunta_input],
            outputs=[pergunta_input, chatbot]
        ).then(
            fn=lambda: "",
            outputs=pergunta_input
        )
        
        pergunta_input.submit(
            fn=responder_com_memoria,
            inputs=[orgao_input, ano_input, cargo_input, pergunta_input],
            outputs=[pergunta_input, chatbot]
        ).then(
            fn=lambda: "",
            outputs=pergunta_input
        )
        
        tentar_novamente_btn.click(
            fn=tentar_novamente,
            outputs=[pergunta_input, chatbot]
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
            show_error=True
        )
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        print("📝 Verifique se todas as dependências estão instaladas e os dados foram processados")
