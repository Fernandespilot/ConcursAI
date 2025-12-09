# test_setup.py - Teste rápido do ConcursAI
"""
Script para verificar se todas as dependências e o modelo estão instalados corretamente.
"""

import sys
import os

def test_imports():
    """Testa importação de todas as bibliotecas necessárias"""
    print("🔍 Testando imports...")
    
    try:
        import langchain
        print("  ✓ langchain")
    except ImportError as e:
        print(f"  ✗ langchain: {e}")
        return False
    
    try:
        import langchain_community
        print("  ✓ langchain_community")
    except ImportError as e:
        print(f"  ✗ langchain_community: {e}")
        return False
    
    try:
        import chromadb
        print("  ✓ chromadb")
    except ImportError as e:
        print(f"  ✗ chromadb: {e}")
        return False
    
    try:
        import sentence_transformers
        print("  ✓ sentence-transformers")
    except ImportError as e:
        print(f"  ✗ sentence-transformers: {e}")
        return False
    
    try:
        import pypdf
        print("  ✓ pypdf")
    except ImportError as e:
        print(f"  ✗ pypdf: {e}")
        return False
    
    try:
        import streamlit
        print("  ✓ streamlit")
    except ImportError as e:
        print(f"  ✗ streamlit: {e}")
        return False
    
    try:
        from llama_cpp import Llama
        print("  ✓ llama-cpp-python")
    except ImportError as e:
        print(f"  ✗ llama-cpp-python: {e}")
        return False
    
    return True

def test_model():
    """Verifica se o modelo GGUF existe"""
    print("\n🔍 Verificando modelo...")
    
    model_path = "./models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    
    if os.path.exists(model_path):
        size_gb = os.path.getsize(model_path) / (1024**3)
        print(f"  ✓ Modelo encontrado: {size_gb:.2f} GB")
        
        if size_gb < 4.5:
            print(f"  ⚠ AVISO: Tamanho menor que esperado (deveria ser ~4.92 GB)")
            print(f"    O download pode estar incompleto!")
            return False
        
        return True
    else:
        print(f"  ✗ Modelo NÃO encontrado em: {model_path}")
        print(f"\n  Baixe com:")
        print(f'  python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id=\'bartowski/Meta-Llama-3.1-8B-Instruct-GGUF\', filename=\'Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf\', local_dir=\'./models\')"')
        return False

def test_core():
    """Testa importação do módulo core"""
    print("\n🔍 Testando módulo core...")
    
    try:
        # Adiciona src ao path se necessário
        if os.path.exists('./src'):
            sys.path.insert(0, './src')
        
        # Tenta importar (mas não inicializar o LLM ainda)
        import core
        print("  ✓ Módulo core.py importado com sucesso")
        return True
    except Exception as e:
        print(f"  ✗ Erro ao importar core.py: {e}")
        return False

def main():
    print("="*50)
    print("  ConcursAI - Teste de Configuração")
    print("  Llama-3.1 8B + RAG Local")
    print("="*50)
    
    results = {
        "imports": test_imports(),
        "model": test_model(),
        "core": test_core()
    }
    
    print("\n" + "="*50)
    print("  RESULTADO DO TESTE")
    print("="*50)
    
    all_ok = all(results.values())
    
    for test, passed in results.items():
        status = "✅ OK" if passed else "❌ FALHOU"
        print(f"  {test.capitalize()}: {status}")
    
    if all_ok:
        print("\n🎉 TUDO CERTO! Sistema pronto para uso!")
        print("\nPróximos passos:")
        print("  1. Execute: streamlit run src/app.py")
        print("  2. Ou clique duas vezes em: INICIAR_CONCURSAI.bat")
        print("\n✨ Boa sorte nos estudos!")
        return 0
    else:
        print("\n⚠️  ATENÇÃO: Alguns testes falharam!")
        print("Verifique os erros acima e instale os componentes faltantes.")
        return 1

if __name__ == "__main__":
    exit(main())
