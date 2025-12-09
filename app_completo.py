#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ConcursAI - Sistema Completo de Concursos Públicos"""

import gradio as gr
import os
import sys
from modules.concurso_rag import responder_interface
from modules.concurso_embeddings import df_chunks, collection

# Lazy loading para módulos pesados
def get_dashboard_interface():
    try:
        from modules.dashboard import criar_dashboard_interface
        return criar_dashboard_interface
    except Exception as e:
        print(f"⚠️ Dashboard não disponível: {e}")
        return None

def get_agendador_interface():
    try:
        from modules.agendador import criar_interface_agendador
        return criar_interface_agendador
    except Exception as e:
        print(f"⚠️ Agendador não disponível: {e}")
        return None

def get_coletor():
    try:
        from modules.coletor_realtime import ColetorConcursosRealTime
        return ColetorConcursosRealTime()
    except Exception as e:
        print(f"⚠️ Coletor não disponível: {e}")
        return None

def get_sistema_notificacoes():
    try:
        from modules.sistema_notificacoes import SistemaNotificacoes
        return SistemaNotificacoes()
    except Exception as e:
        print(f"⚠️ Sistema de notificações não disponível: {e}")
        return None

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

# 🔄 Função para coletar dados em tempo real
def executar_coleta_dados():
    try:
        coletor = get_coletor()
        if coletor is None:
            return "❌ Coletor não disponível"
        
        concursos = coletor.coletar_todos()
        
        if concursos:
            sucesso = coletor.salvar_csv(concursos)
            if sucesso:
                return f"✅ Coleta concluída! {len(concursos)} concursos coletados e salvos."
            else:
                return "❌ Erro ao salvar dados coletados."
        else:
            return "⚠️ Nenhum concurso foi coletado. Verifique sua conexão com a internet."
    except Exception as e:
        return f"❌ Erro na coleta: {str(e)}"

# 🔔 Função para configurar notificações
def configurar_notificacoes_simples(email, orgaos, cargos):
    try:
        # Temporariamente desabilitado devido a problemas de import
        return "⚠️ Sistema de notificações temporariamente indisponível. Será ativado em breve."
        
        # notificador = SistemaNotificacoes()
        
        # if email:
        #     # Configuração básica de email
        #     notificador.config["email"]["emails_destino"] = [email]
        #     notificador.config["email"]["habilitado"] = True
        
        # if orgaos:
        #     orgaos_lista = [o.strip() for o in orgaos.split(',')]
        #     notificador.config["filtros"]["orgaos_interesse"] = orgaos_lista
        
        # if cargos:
        #     cargos_lista = [c.strip() for c in cargos.split(',')]
        #     notificador.config["filtros"]["cargos_interesse"] = cargos_lista
        
        # notificador.salvar_config()
        # return "✅ Configurações de notificação salvas com sucesso!"
        
    except Exception as e:
        return f"❌ Erro ao configurar notificações: {str(e)}"

# 🎨 Interface Principal Unificada
def criar_interface_completa():
    # Obter listas únicas para os dropdowns
    try:
        orgaos = sorted(df_chunks['orgao'].dropna().unique().tolist()) if 'orgao' in df_chunks.columns else ["Todos"]
        anos = sorted(df_chunks['ano'].dropna().unique().tolist(), reverse=True) if 'ano' in df_chunks.columns else ["Todos"]
        cargos = sorted(df_chunks['cargo'].dropna().unique().tolist()) if 'cargo' in df_chunks.columns else ["Todos"]
    except:
        orgaos = ["Todos"]
        anos = ["Todos"] 
        cargos = ["Todos"]

    with gr.Blocks(title="🎯 ConcursAI - Sistema Completo", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🎯 ConcursAI - Sistema Completo de Concursos Públicos
        ### Seu assistente inteligente completo para concursos públicos!
        """)
        
        with gr.Tabs():
            # ===================== ABA PRINCIPAL - CHAT =====================
            with gr.Tab("💬 Assistente Virtual"):
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
                        total_collection = collection.count() if collection else 0
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
            
            # ===================== ABA COLETA DE DADOS =====================
            with gr.Tab("🌐 Coleta de Dados"):
                gr.Markdown("### 📊 Coleta Automática de Dados")
                gr.Markdown("""
                Esta seção permite coletar dados atualizados de concursos de múltiplas fontes:
                - **PCI Concursos**: Fonte principal de concursos
                - **Gran Cursos**: Concursos e informações
                - **Folha Dirigida**: Portal de concursos
                """)
                
                with gr.Row():
                    with gr.Column():
                        btn_coletar = gr.Button("🔄 Coletar Dados Agora", variant="primary", size="lg")
                        
                        gr.Markdown("### ⚙️ Status da Coleta")
                        status_coleta = gr.Textbox(
                            label="Status",
                            value="Aguardando comando...",
                            interactive=False,
                            lines=3
                        )
                    
                    with gr.Column():
                        gr.Markdown("### 📋 Última Coleta")
                        try:
                            if os.path.exists("concursos_chunks.csv"):
                                import pandas as pd
                                df_info = pd.read_csv("concursos_chunks.csv")
                                info_text = f"""
                                **Total de registros:** {len(df_info)}
                                **Órgãos únicos:** {df_info['orgao'].nunique() if 'orgao' in df_info.columns else 'N/A'}
                                **Cargos únicos:** {df_info['cargo'].nunique() if 'cargo' in df_info.columns else 'N/A'}
                                """
                            else:
                                info_text = "Nenhum dado encontrado. Execute uma coleta primeiro."
                        except:
                            info_text = "Erro ao carregar informações dos dados."
                        
                        gr.Markdown(info_text)
                
                btn_coletar.click(
                    fn=executar_coleta_dados,
                    outputs=status_coleta
                )
            
            # ===================== ABA NOTIFICAÇÕES =====================
            with gr.Tab("🔔 Notificações"):
                gr.Markdown("### 📧 Sistema de Notificações")
                gr.Markdown("Configure alertas personalizados para novos concursos de seu interesse.")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 📧 Configuração de Email")
                        email_input = gr.Textbox(
                            label="📧 Seu Email",
                            placeholder="seu.email@gmail.com"
                        )
                        
                        gr.Markdown("#### 🎯 Filtros de Interesse")
                        orgaos_interesse = gr.Textbox(
                            label="🏛️ Órgãos (separados por vírgula)",
                            placeholder="PREFEITURA, TRIBUNAL, MINISTÉRIO",
                            value="PREFEITURA, TRIBUNAL, MINISTÉRIO"
                        )
                        
                        cargos_interesse = gr.Textbox(
                            label="💼 Cargos (separados por vírgula)",
                            placeholder="ANALISTA, TÉCNICO, PROFESSOR",
                            value="ANALISTA, TÉCNICO, PROFESSOR"
                        )
                        
                        btn_config_notif = gr.Button("💾 Salvar Configurações", variant="primary")
                    
                    with gr.Column():
                        gr.Markdown("#### ℹ️ Como Funciona")
                        gr.Markdown("""
                        1. **Configure seu email** para receber notificações
                        2. **Defina filtros** para os tipos de concursos de interesse
                        3. **O sistema verificará automaticamente** novos concursos
                        4. **Você receberá emails** quando houver matches
                        
                        **Nota:** Para funcionamento completo do email, configure também:
                        - Servidor SMTP
                        - Senha de aplicativo (Gmail, Outlook, etc.)
                        """)
                        
                        status_notif = gr.Textbox(
                            label="Status das Configurações",
                            value="Aguardando configuração...",
                            interactive=False,
                            lines=3
                        )
                
                btn_config_notif.click(
                    fn=configurar_notificacoes_simples,
                    inputs=[email_input, orgaos_interesse, cargos_interesse],
                    outputs=status_notif
                )
            
            # ===================== ABA DASHBOARD =====================
            with gr.Tab("📊 Dashboard"):
                gr.Markdown("### 📈 Análise de Dados de Concursos")
                
                # Integrar dashboard aqui ou usar iframe
                gr.Markdown("""
                **Dashboard Completo Disponível em Porta Separada**
                
                Para acessar o dashboard completo com gráficos interativos:
                1. Execute: `python modules/dashboard.py`
                2. Acesse: `http://localhost:7862`
                
                **Funcionalidades do Dashboard:**
                - 📊 Gráficos interativos
                - 📈 Estatísticas detalhadas
                - 🏆 Ranking de oportunidades
                - 📄 Relatórios exportáveis
                """)
                
                # Estatísticas básicas
                try:
                    if not df_chunks.empty:
                        total_concursos = len(df_chunks)
                        orgaos_unicos = df_chunks['orgao'].nunique() if 'orgao' in df_chunks.columns else 0
                        cargos_unicos = df_chunks['cargo'].nunique() if 'cargo' in df_chunks.columns else 0
                        
                        gr.Markdown(f"""
                        ### 📋 Estatísticas Rápidas
                        - **Total de Concursos:** {total_concursos}
                        - **Órgãos Únicos:** {orgaos_unicos}
                        - **Cargos Únicos:** {cargos_unicos}
                        """)
                except:
                    gr.Markdown("⚠️ Dados não disponíveis para estatísticas")
            
            # ===================== ABA AGENDADOR =====================
            with gr.Tab("⏰ Agendamento"):
                gr.Markdown("### 🤖 Coleta Automática Agendada")
                gr.Markdown("""
                Configure coletas automáticas para manter os dados sempre atualizados.
                
                **Agendador Completo Disponível**
                
                Para controle avançado do agendamento:
                1. Execute: `python modules/agendador.py --interface`
                2. Acesse: `http://localhost:7863`
                
                **Funcionalidades:**
                - ⏰ Agendamento customizável
                - 📊 Coleta completa vs rápida
                - 🔔 Notificações automáticas
                - 📝 Logs detalhados
                """)
                
                with gr.Row():
                    gr.Markdown("""
                    ### 🎯 Agendamentos Sugeridos
                    - **Coleta Completa:** 2x por dia (8h e 18h)
                    - **Coleta Rápida:** A cada 2 horas (horário comercial)
                    - **Notificações:** A cada hora
                    - **Limpeza:** Uma vez por semana
                    """)

        # 🔗 Conectar eventos da aba principal
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
    print("🚀 Iniciando ConcursAI - Sistema Completo...")
    try:
        app = criar_interface_completa()
        print("✅ Interface criada com sucesso!")
        
        # Tentar diferentes portas
        portas = [7861, 7864, 7865, 7866, 7867, 7868, 7869, 7870, 7871, 7872]
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
        print("📝 Verifique se todas as dependências estão instaladas")
