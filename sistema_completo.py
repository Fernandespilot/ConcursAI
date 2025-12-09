"""
🚀 SISTEMA COMPLETO INTEGRADO - CONCURSAI
=========================================
Launcher unificado para todo o sistema ConcursAI
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path
import threading
import logging

def setup_logging():
    """Configura logging para o sistema"""
    # Configurar encoding UTF-8 para evitar problemas com emojis
    import locale
    
    # Handler para console com encoding UTF-8
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Handler para arquivo com encoding UTF-8
    file_handler = logging.FileHandler('concursai_sistema.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Formatter sem emojis para evitar problemas de encoding
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Configurar logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

class ConcursAISystem:
    """Gerenciador do sistema completo ConcursAI"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        
    def check_dependencies(self):
        """Verifica se todas as dependências estão instaladas"""
        
        required_packages = [
            'fastapi', 'uvicorn', 'streamlit',
            'requests', 'beautifulsoup4', 'pandas',
            'langchain', 'pypdf', 'pymupdf'
        ]
        
        missing = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        return missing
    
    def check_ollama_status(self):
        """Verifica status do Ollama"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                return True, len(models)
            else:
                return False, 0
                
        except Exception:
            return False, 0
    
    def start_api_server(self):
        """Inicia o servidor FastAPI principal"""
        
        logger.info("🚀 Iniciando API Principal...")
        
        try:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8001",
                "--reload"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=Path(__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['api'] = process
            logger.info("✅ API iniciada na porta 8001")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar API: {e}")
            return False
    
    def start_pdf_interface(self):
        """Inicia a interface PDF Streamlit"""
        
        logger.info("📄 Iniciando Interface PDF...")
        
        try:
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                "interface_pdf.py",
                "--server.port", "8502",
                "--server.headless", "true"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=Path(__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['pdf_interface'] = process
            logger.info("✅ Interface PDF iniciada na porta 8502")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar Interface PDF: {e}")
            return False
    
    def start_scrapers(self):
        """Inicia os scrapers em background"""
        
        logger.info("🕷️ Iniciando Scrapers...")
        
        try:
            cmd = [
                sys.executable,
                "coleta_ativa.py"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=Path(__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['scrapers'] = process
            logger.info("✅ Scrapers iniciados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar Scrapers: {e}")
            return False
    
    def wait_for_services(self):
        """Aguarda os serviços iniciarem"""
        
        print("⏳ Aguardando serviços iniciarem...")
        
        # Aguardar API
        for i in range(30):
            try:
                import requests
                response = requests.get("http://localhost:8001/api/health", timeout=2)
                if response.status_code == 200:
                    print("✅ API Principal pronta")
                    break
            except:
                time.sleep(1)
        
        # Aguardar Interface PDF
        for i in range(30):
            try:
                import requests
                response = requests.get("http://localhost:8502", timeout=2)
                if response.status_code == 200:
                    print("✅ Interface PDF pronta")
                    break
            except:
                time.sleep(1)
    
    def open_interfaces(self):
        """Abre as interfaces no navegador"""
        
        urls = [
            ("🌐 API Principal", "http://localhost:8001"),
            ("📄 Interface PDF", "http://localhost:8502"),
            ("📚 Documentação", "http://localhost:8001/docs")
        ]
        
        print("\n🌐 Abrindo interfaces...")
        
        for name, url in urls:
            try:
                webbrowser.open(url)
                print(f"✅ {name}: {url}")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Erro ao abrir {name}: {e}")
    
    def show_status(self):
        """Mostra status do sistema"""
        
        print("\n" + "="*60)
        print("🎉 CONCURSAI SISTEMA COMPLETO INICIADO!")
        print("="*60)
        
        # Status dos serviços
        print("\n📊 SERVIÇOS ATIVOS:")
        print("✅ API Principal:     http://localhost:8001")
        print("✅ Interface PDF:     http://localhost:8502")
        print("✅ Documentação:      http://localhost:8001/docs")
        
        if 'scrapers' in self.processes:
            print("✅ Scrapers:          Coletando dados em background")
        
        # Status do Ollama
        ollama_status, models = self.check_ollama_status()
        if ollama_status:
            print(f"✅ Ollama:            Online com {models} modelos")
        else:
            print("⚠️ Ollama:            Offline (IA limitada)")
        
        print("\n🎯 FUNCIONALIDADES DISPONÍVEIS:")
        print("📤 Upload e análise de PDFs")
        print("💬 Chat conversacional com editais")
        print("🕷️ Coleta automática de concursos")
        print("🔍 Busca inteligente")
        print("📊 Análise de dados")
        print("🤖 IA integrada (se Ollama ativo)")
        
        print("\n⌨️ Pressione Ctrl+C para parar o sistema")
        print("="*60)
    
    def start_system(self):
        """Inicia o sistema completo"""
        
        print("🚀 INICIANDO CONCURSAI SISTEMA COMPLETO")
        print("="*50)
        
        # 1. Verificar dependências
        print("\n1️⃣ Verificando dependências...")
        missing = self.check_dependencies()
        
        if missing:
            print(f"⚠️ Dependências em falta: {', '.join(missing)}")
            install = input("📦 Instalar automaticamente? (s/n): ").lower()
            
            if install == 's':
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install"
                    ] + missing)
                    print("✅ Dependências instaladas")
                except:
                    print("❌ Erro na instalação")
                    return False
            else:
                print("❌ Sistema não pode iniciar sem dependências")
                return False
        else:
            print("✅ Todas as dependências OK")
        
        # 2. Verificar Ollama
        print("\n2️⃣ Verificando Ollama...")
        ollama_status, models = self.check_ollama_status()
        
        if ollama_status:
            print(f"✅ Ollama online com {models} modelos")
        else:
            print("⚠️ Ollama offline - IA funcionará em modo limitado")
        
        # 3. Iniciar serviços
        print("\n3️⃣ Iniciando serviços...")
        
        services = [
            ("API Principal", self.start_api_server),
            ("Interface PDF", self.start_pdf_interface),
            ("Scrapers", self.start_scrapers)
        ]
        
        for name, start_func in services:
            if start_func():
                print(f"✅ {name} iniciado")
            else:
                print(f"⚠️ {name} falhou (continuando...)")
        
        # 4. Aguardar serviços
        self.wait_for_services()
        
        # 5. Abrir interfaces
        self.open_interfaces()
        
        # 6. Mostrar status
        self.show_status()
        
        # 7. Manter sistema rodando
        self.running = True
        
        try:
            while self.running:
                time.sleep(5)
                
                # Verificar se processos ainda estão rodando
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        logger.warning(f"AVISO - Processo {name} parou")
                        
        except KeyboardInterrupt:
            print("\n🛑 Parando sistema...")
            self.stop_system()
    
    def stop_system(self):
        """Para o sistema completo"""
        
        self.running = False
        
        print("🛑 Encerrando processos...")
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} encerrado")
            except:
                try:
                    process.kill()
                    print(f"🔨 {name} forçadamente encerrado")
                except:
                    print(f"⚠️ Erro ao encerrar {name}")
        
        print("👋 ConcursAI encerrado com sucesso!")

def main():
    """Função principal"""
    
    system = ConcursAISystem()
    
    try:
        system.start_system()
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        print(f"❌ Erro crítico: {e}")
    finally:
        system.stop_system()

if __name__ == "__main__":
    main()
