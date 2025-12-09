"""
🌐 INTERFACE WEB PARA UPLOAD E ANÁLISE DE PDFs
==============================================
Interface Streamlit para upload, processamento e chat com PDFs de editais
"""

import streamlit as st
import os
import tempfile
import json
from datetime import datetime
from typing import Dict, List

# Importar módulos do sistema
try:
    from modules.pdf_processor import get_pdf_analyzer, LangChainPDFAnalyzer
except ImportError:
    st.error("❌ Erro ao importar módulos. Verifique se o sistema está configurado corretamente.")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="ConcursAI - Análise de PDFs",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9ff;
    }
    
    .doc-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .chat-message {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .chat-response {
        background: #e8f4fd;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    
    .error-box {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Inicializa o estado da sessão"""
    if 'pdf_analyzer' not in st.session_state:
        st.session_state.pdf_analyzer = get_pdf_analyzer()
    
    if 'uploaded_docs' not in st.session_state:
        st.session_state.uploaded_docs = {}
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = {}

def render_header():
    """Renderiza o cabeçalho da aplicação"""
    st.markdown("""
    <div class="main-header">
        <h1>📄 ConcursAI - Análise Inteligente de PDFs</h1>
        <p>Upload e converse com editais de concursos usando IA</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Renderiza a barra lateral com opções"""
    st.sidebar.markdown("## 🎛️ Painel de Controle")
    
    # Status do sistema
    st.sidebar.markdown("### 📊 Status do Sistema")
    
    try:
        analyzer = st.session_state.pdf_analyzer
        docs = analyzer.list_documents()
        
        st.sidebar.success(f"✅ Ollama conectado")
        st.sidebar.info(f"📄 {len(docs)} documentos carregados")
        
        if docs:
            st.sidebar.markdown("#### 📚 Documentos:")
            for doc in docs:
                doc_name = doc['metadata'].get('titulo', doc['document_id'])
                st.sidebar.write(f"• {doc_name[:30]}...")
                
    except Exception as e:
        st.sidebar.error(f"❌ Erro: {e}")
    
    # Configurações
    st.sidebar.markdown("### ⚙️ Configurações")
    
    model = st.sidebar.selectbox(
        "Modelo de IA:",
        ["llama3", "mistral", "gemma"],
        key="selected_model"
    )
    
    chunk_size = st.sidebar.slider(
        "Tamanho dos chunks:",
        500, 2000, 1000,
        key="chunk_size"
    )
    
    # Botão para limpar documentos
    if st.sidebar.button("🗑️ Limpar Todos os Documentos"):
        st.session_state.pdf_analyzer = get_pdf_analyzer()
        st.session_state.uploaded_docs = {}
        st.session_state.chat_history = {}
        st.sidebar.success("✅ Documentos limpos!")
        st.rerun()

def upload_pdf_section():
    """Seção para upload de PDFs"""
    st.markdown("## 📤 Upload de PDF")
    
    uploaded_file = st.file_uploader(
        "Escolha um arquivo PDF de edital",
        type="pdf",
        help="Faça upload do PDF do edital de concurso para análise"
    )
    
    if uploaded_file is not None:
        # Informações do arquivo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📄 Nome", uploaded_file.name)
        with col2:
            st.metric("📊 Tamanho", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("🗂️ Tipo", uploaded_file.type)
        
        # Metadados opcionais
        with st.expander("ℹ️ Informações Adicionais (Opcional)"):
            col1, col2 = st.columns(2)
            
            with col1:
                titulo = st.text_input("Título do concurso", key="titulo_input")
                orgao = st.text_input("Órgão/Instituição", key="orgao_input")
            
            with col2:
                estado = st.text_input("Estado/UF", key="estado_input")
                cargo = st.text_input("Cargo principal", key="cargo_input")
        
        # Botão de processamento
        if st.button("🚀 Processar PDF", type="primary"):
            process_uploaded_pdf(uploaded_file, {
                'titulo': titulo,
                'orgao': orgao,
                'estado': estado,
                'cargo': cargo
            })

def process_uploaded_pdf(uploaded_file, metadata: Dict):
    """Processa o PDF uploaded"""
    
    with st.spinner("🔄 Processando PDF... Isso pode levar alguns minutos."):
        try:
            # Salvar arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Gerar ID único para o documento
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name.replace('.pdf', '')}"
            
            # Processar com o analisador
            analyzer = st.session_state.pdf_analyzer
            result = analyzer.process_pdf(tmp_path, doc_id, metadata)
            
            # Limpar arquivo temporário
            os.unlink(tmp_path)
            
            if result['success']:
                st.session_state.uploaded_docs[doc_id] = result
                
                # Mostrar resultado do processamento
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.success("✅ PDF processado com sucesso!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Chunks criados", result['chunks_created'])
                with col2:
                    st.metric("🔤 Caracteres", result['total_characters'])
                with col3:
                    st.metric("🕐 Processado em", "agora")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Mostrar análise inicial se disponível
                if 'initial_analysis' in result and result['initial_analysis']:
                    st.markdown("### 🔍 Análise Inicial")
                    
                    analysis = result['initial_analysis']
                    if isinstance(analysis, dict) and 'analysis_text' not in analysis:
                        # Análise estruturada em JSON
                        for key, value in analysis.items():
                            if isinstance(value, (dict, list)):
                                st.json(value)
                            else:
                                st.write(f"**{key.title()}:** {value}")
                    else:
                        # Análise em texto livre
                        analysis_text = analysis.get('analysis_text', str(analysis))
                        st.write(analysis_text)
                
                st.rerun()
                
            else:
                st.markdown('<div class="error-box">', unsafe_allow_html=True)
                st.error(f"❌ Erro ao processar PDF: {result['error']}")
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown('<div class="error-box">', unsafe_allow_html=True)
            st.error(f"❌ Erro inesperado: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

def document_list_section():
    """Seção com lista de documentos processados"""
    
    analyzer = st.session_state.pdf_analyzer
    docs = analyzer.list_documents()
    
    if not docs:
        st.info("📄 Nenhum documento carregado ainda. Faça upload de um PDF acima.")
        return
    
    st.markdown("## 📚 Documentos Carregados")
    
    for doc in docs:
        doc_id = doc['document_id']
        metadata = doc['metadata']
        
        with st.expander(f"📄 {metadata.get('titulo', doc_id)}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Órgão:** {metadata.get('orgao', 'N/A')}")
                st.write(f"**Estado:** {metadata.get('estado', 'N/A')}")
                st.write(f"**Páginas:** {metadata.get('paginas', 'N/A')}")
            
            with col2:
                st.write(f"**Chunks:** {doc['chunks_count']}")
                st.write(f"**Caracteres:** {doc['character_count']:,}")
                st.write(f"**Processado:** {doc['processed_at'][:16]}")
            
            # Botões de ação
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"💬 Chat", key=f"chat_{doc_id}"):
                    st.session_state.selected_doc_for_chat = doc_id
            
            with col2:
                if st.button(f"📋 Resumo", key=f"summary_{doc_id}"):
                    show_document_summary(doc_id)
            
            with col3:
                if st.button(f"🗑️ Remover", key=f"remove_{doc_id}"):
                    remove_document(doc_id)

def show_document_summary(doc_id: str):
    """Mostra resumo de um documento"""
    
    with st.spinner("🔄 Gerando resumo..."):
        analyzer = st.session_state.pdf_analyzer
        summary = analyzer.get_document_summary(doc_id)
        
        if 'error' not in summary:
            st.markdown("### 📋 Resumo do Documento")
            st.write(summary['summary'])
        else:
            st.error(f"❌ {summary['error']}")

def remove_document(doc_id: str):
    """Remove um documento"""
    
    if doc_id in st.session_state.pdf_analyzer.document_store:
        del st.session_state.pdf_analyzer.document_store[doc_id]
    
    if doc_id in st.session_state.uploaded_docs:
        del st.session_state.uploaded_docs[doc_id]
    
    st.success("✅ Documento removido!")
    st.rerun()

def chat_section():
    """Seção de chat com documentos"""
    
    st.markdown("## 💬 Chat com Documentos")
    
    analyzer = st.session_state.pdf_analyzer
    docs = analyzer.list_documents()
    
    if not docs:
        st.info("📄 Nenhum documento disponível para chat. Faça upload de um PDF primeiro.")
        return
    
    # Seletor de documento
    doc_options = {doc['document_id']: doc['metadata'].get('titulo', doc['document_id']) for doc in docs}
    
    selected_doc_id = st.selectbox(
        "Escolha um documento para conversar:",
        options=list(doc_options.keys()),
        format_func=lambda x: doc_options[x],
        key="chat_doc_selector"
    )
    
    if selected_doc_id:
        # Histórico de chat para este documento
        if selected_doc_id not in st.session_state.chat_history:
            st.session_state.chat_history[selected_doc_id] = []
        
        # Mostrar histórico
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history[selected_doc_id]:
                # Pergunta do usuário
                st.markdown(f'<div class="chat-message">👤 **Você:** {message["question"]}</div>', unsafe_allow_html=True)
                
                # Resposta da IA
                st.markdown(f'<div class="chat-response">🤖 **IA:** {message["answer"]}</div>', unsafe_allow_html=True)
                
                # Fontes (se disponíveis)
                if message.get('sources'):
                    with st.expander("📚 Fontes utilizadas"):
                        for i, source in enumerate(message['sources'], 1):
                            st.write(f"**Fonte {i}:** {source['content']}")
        
        # Input para nova pergunta
        with st.form("chat_form"):
            question = st.text_area(
                "Faça uma pergunta sobre o documento:",
                placeholder="Ex: Quais são os requisitos para o cargo? Qual é o salário? Quando são as inscrições?",
                height=100
            )
            
            submitted = st.form_submit_button("🚀 Enviar Pergunta", type="primary")
            
            if submitted and question.strip():
                process_chat_question(selected_doc_id, question.strip())

def process_chat_question(doc_id: str, question: str):
    """Processa uma pergunta do chat"""
    
    with st.spinner("🤖 Processando pergunta..."):
        analyzer = st.session_state.pdf_analyzer
        result = analyzer.query_document(doc_id, question)
        
        if result['success']:
            # Adicionar ao histórico
            chat_entry = {
                'question': question,
                'answer': result['answer'],
                'sources': result.get('sources', []),
                'timestamp': result['timestamp']
            }
            
            st.session_state.chat_history[doc_id].append(chat_entry)
            
            st.rerun()
        else:
            st.error(f"❌ Erro ao processar pergunta: {result['error']}")

def main():
    """Função principal da aplicação"""
    
    # Inicializar estado
    init_session_state()
    
    # Renderizar interface
    render_header()
    render_sidebar()
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "📚 Documentos", "💬 Chat"])
    
    with tab1:
        upload_pdf_section()
    
    with tab2:
        document_list_section()
    
    with tab3:
        chat_section()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🤖 **ConcursAI** - Sistema inteligente para análise de editais de concursos | "
        "Powered by LangChain + Ollama"
    )

if __name__ == "__main__":
    main()
