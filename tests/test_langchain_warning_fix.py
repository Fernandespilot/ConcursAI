#!/usr/bin/env python3
"""
🧪 TESTE PARA VERIFICAR CORREÇÃO DO WARNING LANGCHAIN
=====================================================
Verifica se o warning de OllamaEmbeddings foi corrigido
"""

import warnings
import sys
import os

# Capturar warnings
warnings.filterwarnings('default')

print("🔍 TESTANDO CORREÇÃO DO WARNING LANGCHAIN")
print("=" * 50)

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.abspath('.'))

try:
    print("📦 Importando langchain_ollama...")
    from langchain_ollama import OllamaEmbeddings, OllamaLLM
    print("✅ langchain_ollama importado com sucesso")
    
    print("\n📄 Importando pdf_processor...")
    
    # Capturar warnings específicos
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        from modules.pdf_processor import LangChainPDFAnalyzer
        
        # Verificar se houve warnings
        if w:
            print(f"⚠️  {len(w)} warning(s) detectado(s):")
            for warning in w:
                print(f"   • {warning.category.__name__}: {warning.message}")
                print(f"     Arquivo: {warning.filename}:{warning.lineno}")
        else:
            print("✅ Nenhum warning detectado!")
    
    print("\n🧪 Testando inicialização do LangChainPDFAnalyzer...")
    
    # Testar inicialização
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        try:
            analyzer = LangChainPDFAnalyzer()
            print("✅ LangChainPDFAnalyzer inicializado sem warnings")
            
            # Verificar se houve warnings durante inicialização
            if w:
                print(f"⚠️  {len(w)} warning(s) durante inicialização:")
                for warning in w:
                    if "OllamaEmbeddings" in str(warning.message):
                        print(f"   ❌ WARNING LANGCHAIN AINDA PRESENTE: {warning.message}")
                    else:
                        print(f"   • {warning.category.__name__}: {warning.message}")
            else:
                print("✅ Inicialização sem warnings!")
                
        except Exception as e:
            print(f"⚠️  Erro na inicialização (normal se Ollama não estiver rodando): {e}")
    
    print("\n📊 RESULTADO:")
    print("=" * 30)
    
    # Verificar versões
    try:
        import langchain_ollama
        print(f"📦 langchain-ollama versão: {langchain_ollama.__version__}")
    except:
        print("⚠️  Não foi possível determinar versão do langchain-ollama")
    
    print("✅ Teste de warning concluído")
    print("🔧 Se ainda houver warnings, pode ser necessário reiniciar o ambiente Python")
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("💡 Execute: pip install -U langchain-ollama")
    
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 PRÓXIMOS PASSOS:")
print("1. Se warnings persistirem, reinicie o kernel Python")
print("2. Teste o sistema completo: python sistema_completo.py")
print("3. Verifique funcionalidade PDF: streamlit run interfaces/interface_pdf.py")
