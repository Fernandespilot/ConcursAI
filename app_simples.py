#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ConcursAI - Sistema Simplificado de Concursos Públicos"""

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

def atualizar_chat():
    return [[h["pergunta"], h["resposta"]] for h in historico_conversa]

def limpar_historico():
    global historico_conversa
    historico_conversa = []
    return [], ""

def tentar_novamente():
    if not historico_conversa:
        return "⚠️ Nenhuma pergunta anterior encontrada.", []
    ultima = historico_conversa[-1]
    nova_resposta = responder_interface(
        ultima["orgao"], ultima["ano"], ultima["cargo"], ultima["pergunta"], contexto_extra=""
    )
    historico_conversa[-1]["resposta"] = nova_resposta
    return nova_resposta, atualizar_chat()

# Obter dados únicos para dropdowns
try:
    if not df_chunks.empty:
        orgaos = sorted(df_chunks['orgao'].dropna().unique().tolist())
        anos = sorted(df_chunks['ano'].dropna().unique().tolist(), reverse=True)
        cargos = sorted(df_chunks['cargo'].dropna().unique().tolist())
    else:
        orgaos = ["Nenhum dado disponível"]
        anos = ["Nenhum dado disponível"]
        cargos = ["Nenhum dado disponível"]
except:
    orgaos = ["Erro ao carregar"]
    anos = ["Erro ao carregar"]
    cargos = ["Erro ao carregar"]

# 🎯 Interface principal
def criar_interface_completa():
    with gr.Blocks(title="🎯 ConcursAI - Sistema Simplificado", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🎯 ConcursAI - Sistema de Concursos Públicos
        ### Seu assistente inteligente para concursos públicos!
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

        # Eventos
        enviar_btn.click(
            fn=responder_com_memoria,
            inputs=[orgao_input, ano_input, cargo_input, pergunta_input],
            outputs=[pergunta_input, chatbot]
        )
        
        tentar_novamente_btn.click(
            fn=tentar_novamente,
            outputs=[pergunta_input, chatbot]
        )
        
        limpar_btn.click(
            fn=limpar_historico,
            outputs=[chatbot, pergunta_input]
        )
        
        pergunta_input.submit(
            fn=responder_com_memoria,
            inputs=[orgao_input, ano_input, cargo_input, pergunta_input],
            outputs=[pergunta_input, chatbot]
        )

    return app

if __name__ == "__main__":
    print("🚀 Iniciando ConcursAI - Sistema Simplificado...")
    try:
        app = criar_interface_completa()
        print("✅ Interface criada com sucesso!")
        
        # Tentar diferentes portas
        portas = [7861, 7864, 7865, 7866, 7867, 7868, 7869, 7870]
        app_iniciada = False
        
        for porta in portas:
            try:
                print(f"🔄 Tentando iniciar na porta {porta}...")
                app.launch(
                    server_name="0.0.0.0",
                    server_port=porta,
                    share=False,
                    debug=False,
                    show_error=True
                )
                app_iniciada = True
                break
            except Exception as e:
                print(f"⚠️ Porta {porta} ocupada, tentando próxima...")
                continue
        
        if not app_iniciada:
            print("❌ Não foi possível iniciar em nenhuma porta disponível")
            
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()
