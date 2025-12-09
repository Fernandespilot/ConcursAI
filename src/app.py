# src/app.py - Interface Web do ConcursAI com Llama-3.1
import streamlit as st
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import indexar_pdf, perguntar, estudo_banca, listar_bancas

# Configuração da página
st.set_page_config(
    page_title="ConcursAI - Llama 3.1",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-title">📚 ConcursAI - Assistente de Editais</h1>', unsafe_allow_html=True)
st.markdown("**Powered by Meta Llama 3.1 8B Instruct (GGUF) - 100% Local**")

# Sidebar com informações
with st.sidebar:
    st.header("ℹ️ Sobre o Sistema")
    st.info("""
    **ConcursAI** usa:
    - 🤖 Llama-3.1 8B (Q4_K_M)
    - 📊 ChromaDB (vetorial)
    - 🧠 Embeddings PT-BR
    - 💻 100% local (sem internet)
    """)
    
    st.header("📊 Estatísticas")
    bancas = listar_bancas()
    if bancas:
        st.metric("Bancas Indexadas", len(bancas))
        st.write("**Bancas:**")
        for banca in bancas:
            st.write(f"- {banca.upper()}")
    else:
        st.warning("Nenhum edital indexado ainda")
    
    st.header("⚙️ Configuração")
    st.write("**Modelo:** Llama-3.1-8B Q4_K_M")
    st.write("**Threads:** 8 (i7-1255U)")
    st.write("**Contexto:** 2048 tokens")

# Tabs principais
tab1, tab2, tab3, tab4 = st.tabs(["💬 Perguntas", "📁 Adicionar PDF", "📊 Análise de Banca", "🕷️ Scraping Auto"])

# TAB 1: Perguntas
with tab1:
    st.header("💬 Faça Perguntas sobre Editais")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        pergunta = st.text_input(
            "Digite sua pergunta:",
            placeholder="Ex: Qual o salário inicial? Quais os requisitos? Quantas vagas?"
        )
    with col2:
        k_docs = st.number_input("Documentos", min_value=1, max_value=10, value=5, help="Número de trechos para buscar")
    
    if st.button("🔍 Buscar Resposta", type="primary", use_container_width=True):
        if pergunta.strip():
            with st.spinner("🤔 Consultando Llama-3.1..."):
                try:
                    resposta, fonte = perguntar(pergunta, k=k_docs)
                    
                    st.success("✅ Resposta encontrada!")
                    
                    # Exibe resposta
                    st.markdown("### 📝 Resposta:")
                    st.info(resposta)
                    
                    # Exibe fonte
                    st.markdown("### 📄 Fonte:")
                    st.code(fonte, language="text")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao processar: {e}")
        else:
            st.warning("⚠️ Digite uma pergunta primeiro!")
    
    # Exemplos de perguntas
    with st.expander("💡 Exemplos de Perguntas"):
        st.markdown("""
        - Qual o salário inicial do cargo?
        - Quais os requisitos mínimos?
        - Quantas vagas estão disponíveis?
        - Qual a carga horária?
        - Quando são as inscrições?
        - Quais disciplinas caem na prova?
        - Qual o valor da taxa de inscrição?
        """)

# TAB 2: Adicionar PDF
with tab2:
    st.header("📁 Indexar Novo Edital (PDF)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader(
            "Escolha um PDF de edital:",
            type=['pdf'],
            help="Upload de editais em PDF (máx 200 MB)"
        )
    
    with col2:
        st.markdown("### 🏷️ Metadados do Edital")
        banca = st.text_input("Banca", placeholder="Ex: cebraspe, fcc, vunesp")
        cargo = st.text_input("Cargo", placeholder="Ex: Analista TI")
        ano = st.text_input("Ano", placeholder="Ex: 2025")
        orgao = st.text_input("Órgão", placeholder="Ex: TRF, Polícia Federal")
    
    if st.button("📥 Indexar PDF", type="primary", use_container_width=True):
        if uploaded_file and banca:
            # Salva arquivo temporariamente
            temp_path = f"./temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            metadados = {
                "banca": banca.lower().strip(),
                "cargo": cargo,
                "ano": ano,
                "orgao": orgao,
                "source": uploaded_file.name
            }
            
            with st.spinner("🔄 Processando PDF... (pode levar 1-2 minutos)"):
                try:
                    num_chunks = indexar_pdf(temp_path, metadados)
                    os.remove(temp_path)  # Remove arquivo temporário
                    
                    st.success(f"✅ Sucesso! {num_chunks} trechos indexados")
                    st.balloons()
                    
                    # Mostra metadados salvos
                    st.json(metadados)
                    
                except Exception as e:
                    st.error(f"❌ Erro ao indexar: {e}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        else:
            st.warning("⚠️ Faça upload do PDF e preencha pelo menos o campo 'Banca'")
    
    # Dicas
    st.info("💡 **Dica:** Quanto mais editais da mesma banca, melhor a análise!")

# TAB 3: Análise de Banca
with tab3:
    st.header("📊 Análise de Temas por Banca")
    
    bancas_disponiveis = listar_bancas()
    
    if bancas_disponiveis:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            banca_selecionada = st.selectbox(
                "Escolha a banca:",
                options=bancas_disponiveis,
                format_func=lambda x: x.upper()
            )
        
        with col2:
            st.write("")  # Espaçamento
            st.write("")
            gerar = st.button("🔬 Gerar Análise", type="primary", use_container_width=True)
        
        if gerar:
            with st.spinner(f"🧠 Analisando editais da {banca_selecionada.upper()}..."):
                try:
                    relatorio = estudo_banca(banca_selecionada)
                    
                    st.success("✅ Análise concluída!")
                    
                    # Exibe relatório
                    st.markdown("### 📈 Relatório de Temas:")
                    st.markdown(relatorio)
                    
                    # Botão para baixar
                    st.download_button(
                        label="💾 Baixar Relatório (.txt)",
                        data=relatorio,
                        file_name=f"analise_{banca_selecionada}_{ano if 'ano' in locals() else '2025'}.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Erro ao gerar análise: {e}")
        
        # Explicação
        with st.expander("ℹ️ Como funciona?"):
            st.markdown("""
            A análise usa **Llama-3.1** para:
            1. Buscar os 10 trechos mais relevantes da banca
            2. Identificar disciplinas e temas recorrentes
            3. Estimar frequência relativa (%)
            4. Gerar relatório estruturado
            
            **Quanto mais editais, melhor a precisão!**
            """)
    else:
        st.warning("⚠️ Nenhuma banca indexada. Adicione PDFs primeiro na aba 'Adicionar PDF'!")

# TAB 4: Scraping Automático
with tab4:
    st.header("🕷️ Coleta Automática de Editais")
    
    st.info("""
    **Sistema de scraping automático** que coleta editais de sites oficiais 
    e indexa no RAG automaticamente. Funciona 100% local!
    """)
    
    # Coleta manual
    st.subheader("📥 Coleta Imediata")
    
    col1, col2 = st.columns(2)
    
    with col1:
        banca_scraping = st.selectbox(
            "Escolha a banca:",
            options=["cebraspe", "fgv"],
            format_func=lambda x: x.upper()
        )
        
        max_concursos = st.slider(
            "Máximo de concursos por banca:",
            min_value=1,
            max_value=10,
            value=3,
            help="Quanto mais, mais tempo leva"
        )
    
    with col2:
        st.metric("PDFs na pasta", len([f for f in os.listdir("editais") if f.endswith('.pdf')]) if os.path.exists("editais") else 0)
        st.metric("Espaço usado", f"{sum(os.path.getsize(os.path.join('editais', f)) for f in os.listdir('editais') if f.endswith('.pdf')) / (1024*1024):.1f} MB" if os.path.exists("editais") and os.listdir("editais") else "0 MB")
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button(f"🕷️ Coletar {banca_scraping.upper()}", type="primary", use_container_width=True):
            with st.spinner(f"Coletando editais da {banca_scraping.upper()}..."):
                try:
                    from scrapers.scraper_scheduler import coletar_agora
                    
                    # Cria área para log em tempo real
                    log_placeholder = st.empty()
                    
                    coletar_agora(banca_scraping, max_concursos)
                    
                    st.success(f"✅ Coleta da {banca_scraping.upper()} concluída!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Erro na coleta: {e}")
    
    with col_btn2:
        if st.button("🔄 Coletar TODAS", use_container_width=True):
            with st.spinner("Coletando de todas as bancas..."):
                try:
                    from scrapers.scraper_scheduler import coletar_todas_agora
                    
                    coletar_todas_agora(max_concursos=max_concursos)
                    
                    st.success("✅ Coleta de todas as bancas concluída!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
    
    with col_btn3:
        if st.button("📁 Abrir Pasta", use_container_width=True):
            import subprocess
            editais_path = os.path.abspath("editais")
            os.makedirs(editais_path, exist_ok=True)
            subprocess.Popen(f'explorer "{editais_path}"')
            st.success("✓ Pasta aberta no Explorer")
    
    st.markdown("---")
    
    # Agendamento
    st.subheader("⏰ Agendamento Automático")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Coleta Diária")
        hora_diaria = st.time_input("Horário", value=None)
        
        if st.button("📅 Agendar Coleta Diária", use_container_width=True):
            if hora_diaria:
                try:
                    from scrapers.scraper_scheduler import agendar_diario
                    
                    agendar_diario(hora=hora_diaria.hour, minuto=hora_diaria.minute)
                    
                    st.success(f"✅ Coleta agendada para {hora_diaria.strftime('%H:%M')} todos os dias!")
                    
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
            else:
                st.warning("⚠️ Selecione um horário")
    
    with col2:
        st.markdown("### Coleta Semanal")
        dia_semana = st.selectbox(
            "Dia da semana",
            options=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            format_func=lambda x: {
                "monday": "Segunda", "tuesday": "Terça", "wednesday": "Quarta",
                "thursday": "Quinta", "friday": "Sexta", "saturday": "Sábado", "sunday": "Domingo"
            }[x]
        )
        hora_semanal = st.time_input("Horário ", value=None)
        
        if st.button("📅 Agendar Coleta Semanal", use_container_width=True):
            if hora_semanal:
                try:
                    from scrapers.scraper_scheduler import agendar_semanal
                    
                    agendar_semanal(dia=dia_semana, hora=hora_semanal.hour)
                    
                    st.success(f"✅ Coleta agendada para {dia_semana} às {hora_semanal.strftime('%H:%M')}!")
                    
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
            else:
                st.warning("⚠️ Selecione um horário")
    
    # Status do scheduler
    st.markdown("---")
    st.subheader("📊 Status do Sistema")
    
    try:
        from scrapers.scraper_scheduler import obter_status
        
        status = obter_status()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status", "🟢 Ativo" if status.get('rodando') else "🔴 Parado")
        
        with col2:
            st.metric("PDFs Coletados", status.get('total_coletados', 0))
        
        with col3:
            st.metric("PDFs Indexados", status.get('total_indexados', 0))
        
        with col4:
            st.metric("Jobs Agendados", status.get('jobs_ativos', 0))
        
        if status.get('ultima_coleta'):
            st.info(f"🕐 Última coleta: {status['ultima_coleta']}")
        
        if status.get('proxima_coleta'):
            st.success(f"⏰ Próxima coleta: {status['proxima_coleta']}")
    
    except Exception as e:
        st.warning(f"⚠️ Não foi possível obter status: {e}")
    
    # Botão para parar scheduler
    if st.button("⛔ Parar Scheduler", use_container_width=True):
        try:
            from scrapers.scraper_scheduler import parar_scheduler
            parar_scheduler()
            st.success("✓ Scheduler parado")
        except Exception as e:
            st.error(f"Erro: {e}")
    
    # Informações
    with st.expander("ℹ️ Como Funciona o Scraping?"):
        st.markdown("""
        ### 🕷️ Processo de Coleta Automática
        
        1. **Navega** nos sites oficiais das bancas (Cebraspe, FGV, etc.)
        2. **Identifica** concursos ativos e editais disponíveis
        3. **Baixa** os PDFs automaticamente na pasta `editais/`
        4. **Indexa** no ChromaDB com metadados (banca, tipo, data)
        5. **Atualiza** a IA em tempo real - perguntas usam dados novos!
        
        ### ⏰ Agendamento
        - **Diário**: Coleta todos os dias no horário escolhido
        - **Semanal**: Coleta 1x por semana no dia/hora escolhido
        - **Manual**: Use os botões "Coletar" quando quiser
        
        ### 🎯 Bancas Suportadas
        - ✅ Cebraspe (CESPE)
        - ✅ FGV Conhecimento
        - 🔜 FCC (em breve)
        - 🔜 Vunesp (em breve)
        
        ### 💡 Dica
        Configure coleta diária às 6h da manhã - sempre terá editais frescos!
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>ConcursAI v2.0 + Scraping Auto | Llama-3.1 8B | Desenvolvido para concurseiros 🚀</small>
</div>
""", unsafe_allow_html=True)
