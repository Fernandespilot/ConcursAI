"""
🔧 CORREÇÃO DE DEPENDÊNCIAS - LANGCHAIN
======================================
Script para atualizar e corrigir dependências do LangChain
"""

import subprocess
import sys
from pathlib import Path

def update_langchain_dependencies():
    """Atualiza dependências do LangChain para versões mais recentes"""
    
    print("🔧 Atualizando dependências do LangChain...")
    
    # Pacotes para atualizar
    packages_to_update = [
        "langchain>=0.3.0",
        "langchain-community>=0.3.0", 
        "langchain-ollama>=0.2.0",
        "langchain-core>=0.3.0"
    ]
    
    for package in packages_to_update:
        try:
            print(f"📦 Instalando {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-U", package
            ])
            print(f"✅ {package} atualizado")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {package}: {e}")
    
    print("✅ Dependências atualizadas!")

def test_imports():
    """Testa se as importações estão funcionando"""
    
    print("\n🧪 Testando importações...")
    
    try:
        from langchain_ollama import OllamaEmbeddings, Ollama
        print("✅ langchain_ollama: OK")
    except ImportError as e:
        print(f"❌ langchain_ollama: {e}")
    
    try:
        from langchain_community.document_loaders import PyPDFLoader
        print("✅ langchain_community: OK")
    except ImportError as e:
        print(f"❌ langchain_community: {e}")
    
    try:
        from langchain_community.vectorstores import FAISS
        print("✅ FAISS: OK")
    except ImportError as e:
        print(f"❌ FAISS: {e}")
    
    print("✅ Testes concluídos!")

def fix_additional_imports():
    """Corrige outras importações que podem ter problemas"""
    
    print("\n🔧 Verificando outras dependências...")
    
    additional_packages = [
        "faiss-cpu",  # Para FAISS
        "tiktoken",   # Para tokenização
        "sentence-transformers"  # Para embeddings alternativos
    ]
    
    for package in additional_packages:
        try:
            print(f"📦 Instalando {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
            print(f"✅ {package} instalado")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Opcional {package} falhou: {e}")

if __name__ == "__main__":
    print("🚀 CORREÇÃO DE DEPENDÊNCIAS LANGCHAIN")
    print("=" * 50)
    
    update_langchain_dependencies()
    fix_additional_imports()
    test_imports()
    
    print("\n🎉 Correções aplicadas!")
    print("💡 Se ainda houver problemas, reinicie o Python/VS Code")
