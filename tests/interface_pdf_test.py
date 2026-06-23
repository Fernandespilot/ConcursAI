"""
🌐 INTERFACE PDF SIMPLIFICADA - TESTE
=====================================
Versão simplificada para diagnosticar problemas
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="ConcursAI - PDF Test",
    page_icon="📄",
    layout="wide"
)

def test_imports():
    """Testa todas as importações necessárias"""
    imports_status = {}
    
    try:
        import streamlit
        imports_status['streamlit'] = f"✅ OK - {streamlit.__version__}"
    except Exception as e:
        imports_status['streamlit'] = f"❌ ERRO - {e}"
    
    try:
        import pandas
        imports_status['pandas'] = f"✅ OK - {pandas.__version__}"
    except Exception as e:
        imports_status['pandas'] = f"❌ ERRO - {e}"
    
    try:
        from modules.pdf_processor import get_pdf_analyzer
        imports_status['pdf_processor'] = "✅ OK"
    except Exception as e:
        imports_status['pdf_processor'] = f"❌ ERRO - {e}"
    
    try:
        import tempfile
        imports_status['tempfile'] = "✅ OK"
    except Exception as e:
        imports_status['tempfile'] = f"❌ ERRO - {e}"
    
    return imports_status

def main():
    """Função principal simplificada"""
    
    st.title("🧪 ConcursAI - Teste de Interface PDF")
    st.markdown("---")
    
    st.header("📊 Status dos Módulos")
    
    # Testar importações
    imports = test_imports()
    
    for module, status in imports.items():
        st.write(f"**{module}:** {status}")
    
    st.markdown("---")
    
    # Informações do sistema
    st.header("🖥️ Informações do Sistema")
    st.write(f"**Python:** {sys.version}")
    st.write(f"**Diretório atual:** {os.getcwd()}")
    st.write(f"**Arquivos Python encontrados:** {len(list(Path('.').rglob('*.py')))}")
    
    # Teste de funcionalidade básica
    st.header("🧪 Teste Básico")
    
    if st.button("Testar Funcionalidade"):
        try:
            # Teste simples de upload
            uploaded_file = st.file_uploader("Teste de Upload", type=['pdf'])
            if uploaded_file:
                st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
            else:
                st.info("📁 Selecione um arquivo PDF para testar")
        except Exception as e:
            st.error(f"❌ Erro no teste: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("🔧 **Interface de Teste** - Diagnosticando problemas do sistema")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ ERRO CRÍTICO: {e}")
        st.write("**Stack trace:**")
        import traceback
        st.code(traceback.format_exc())
