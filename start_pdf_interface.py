"""
🎯 LAUNCHER - INICIALIZADOR DO SISTEMA PDF
=========================================
Script para iniciar a interface Streamlit do sistema de análise de PDFs
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    
    required_packages = [
        'streamlit',
        'langchain',
        'pypdf',
        'pymupdf',
        'requests'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def install_missing_packages(packages):
    """Instala pacotes em falta"""
    
    if not packages:
        return True
    
    print(f"📦 Instalando pacotes em falta: {', '.join(packages)}")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install"
        ] + packages)
        
        print("✅ Pacotes instalados com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar pacotes: {e}")
        return False

def check_ollama():
    """Verifica se o Ollama está rodando"""
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama conectado com {len(models)} modelos")
            return True
        else:
            print("⚠️ Ollama não está respondendo")
            return False
            
    except Exception as e:
        print(f"❌ Ollama não está rodando: {e}")
        print("💡 Execute: ollama serve")
        return False

def start_streamlit():
    """Inicia a interface Streamlit"""
    
    # Caminho para o arquivo da interface
    interface_path = Path(__file__).parent / "interface_pdf.py"
    
    if not interface_path.exists():
        print(f"❌ Arquivo da interface não encontrado: {interface_path}")
        return False
    
    # Configurações do Streamlit
    config = {
        "server.port": 8502,
        "server.headless": True,
        "browser.gatherUsageStats": False,
        "server.enableCORS": False,
        "server.enableXsrfProtection": False
    }
    
    # Construir comando
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(interface_path),
        "--server.port", str(config["server.port"]),
        "--server.headless", str(config["server.headless"]).lower(),
        "--browser.gatherUsageStats", str(config["browser.gatherUsageStats"]).lower()
    ]
    
    print(f"🚀 Iniciando interface Streamlit...")
    print(f"🌐 URL: http://localhost:{config['server.port']}")
    
    try:
        # Iniciar Streamlit
        process = subprocess.Popen(cmd)
        
        # Aguardar um pouco para o servidor iniciar
        time.sleep(3)
        
        # Abrir navegador
        url = f"http://localhost:{config['server.port']}"
        print(f"🌐 Abrindo navegador: {url}")
        webbrowser.open(url)
        
        print("\n" + "="*60)
        print("🎉 INTERFACE PDF INICIADA COM SUCESSO!")
        print("="*60)
        print(f"📱 Acesse: {url}")
        print("⌨️ Pressione Ctrl+C para parar")
        print("="*60)
        
        # Aguardar interrupção
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Parando interface...")
            process.terminate()
            process.wait()
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao iniciar Streamlit: {e}")
        return False

def main():
    """Função principal do launcher"""
    
    print("🚀 ConcursAI - LAUNCHER DO SISTEMA PDF")
    print("="*50)
    
    # 1. Verificar dependências
    print("\n1️⃣ Verificando dependências...")
    missing = check_dependencies()
    
    if missing:
        print(f"⚠️ Pacotes em falta: {', '.join(missing)}")
        
        install = input("📦 Instalar automaticamente? (s/n): ").lower()
        if install == 's':
            if not install_missing_packages(missing):
                print("❌ Falha na instalação. Execute manualmente:")
                print(f"pip install {' '.join(missing)}")
                return False
        else:
            print("❌ Dependências necessárias não instaladas")
            return False
    else:
        print("✅ Todas as dependências estão instaladas")
    
    # 2. Verificar Ollama
    print("\n2️⃣ Verificando Ollama...")
    ollama_ok = check_ollama()
    
    if not ollama_ok:
        print("⚠️ Ollama não está rodando ou configurado")
        print("💡 O sistema funcionará em modo limitado")
        
        continue_anyway = input("🤔 Continuar mesmo assim? (s/n): ").lower()
        if continue_anyway != 's':
            print("❌ Configure o Ollama primeiro:")
            print("   1. Instale: https://ollama.ai/download")
            print("   2. Execute: ollama serve")
            print("   3. Baixe um modelo: ollama pull llama3")
            return False
    
    # 3. Iniciar interface
    print("\n3️⃣ Iniciando interface...")
    
    success = start_streamlit()
    
    if success:
        print("\n✅ Sistema encerrado com sucesso!")
    else:
        print("\n❌ Erro ao iniciar sistema")
    
    return success

if __name__ == "__main__":
    success = main()
    
    if not success:
        input("\n⏸️ Pressione Enter para sair...")
        sys.exit(1)
