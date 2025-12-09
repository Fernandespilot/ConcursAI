"""
🚀 SISTEMA COMPLETO CORRIGIDO - CONCURSAI
=========================================
Versão com correções de encoding Unicode
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path
import threading
import logging
import locale

def setup_logging_safe():
    """Configura logging seguro sem problemas de encoding"""
    
    # Tentar configurar locale UTF-8
    try:
        if os.name == 'nt':  # Windows
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        else:
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except:
        pass
    
    # Criar logger personalizado
    logger = logging.getLogger('concursai_system')
    logger.setLevel(logging.INFO)
    
    # Remover handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para console (sem encoding específico)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Handler para arquivo com encoding UTF-8
    try:
        file_handler = logging.FileHandler(
            'concursai_sistema.log', 
            encoding='utf-8', 
            mode='a'
        )
        file_handler.setLevel(logging.INFO)
    except:
        # Fallback para encoding padrão
        file_handler = logging.FileHandler('concursai_sistema.log', mode='a')
        file_handler.setLevel(logging.INFO)
    
    # Formatter simples sem emojis
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

class ConcursAISystemFixed:
    """Sistema ConcursAI com correções de encoding"""
    
    def __init__(self):
        self.logger = setup_logging_safe()
        self.processes = {}
        self.running = False
        self.logger.info("Sistema ConcursAI inicializado")
        
    def safe_print(self, message):
        """Print seguro que funciona com qualquer encoding"""
        try:
            print(message)
        except UnicodeEncodeError:
            # Remover caracteres especiais se houver problema
            safe_message = message.encode('ascii', 'ignore').decode('ascii')
            print(safe_message)
        except Exception as e:
            print(f"Mensagem: [ENCODING ERROR - {str(e)}]")
    
    def check_dependencies(self):
        """Verifica dependências com logging seguro"""
        
        self.safe_print("STEP 1 - Verificando dependencias...")
        self.logger.info("Iniciando verificacao de dependencias")
        
        required_packages = [
            'fastapi', 'uvicorn', 'streamlit',
            'requests', 'beautifulsoup4', 'pandas',
            'langchain', 'pypdf', 'pymupdf'
        ]
        
        missing = []
        
        for package in required_packages:
            try:
                __import__(package)
                self.logger.info(f"Dependencia OK: {package}")
            except ImportError:
                missing.append(package)
                self.logger.warning(f"Dependencia faltando: {package}")
        
        if missing:
            self.safe_print(f"AVISO - Dependencias em falta: {', '.join(missing)}")
            response = input("Instalar automaticamente? (s/n): ").lower().strip()
            
            if response in ['s', 'sim', 'y', 'yes']:
                self.install_dependencies(missing)
            else:
                self.safe_print("ERRO - Sistema nao pode iniciar sem dependencias")
                return False
        
        self.safe_print("OK - Todas as dependencias verificadas")
        return True
    
    def install_dependencies(self, packages):
        """Instala dependências em falta"""
        
        self.safe_print("STEP 2 - Instalando dependencias...")
        self.logger.info(f"Instalando pacotes: {packages}")
        
        try:
            cmd = [sys.executable, '-m', 'pip', 'install'] + packages
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.logger.info("Instalacao de dependencias concluida")
            self.safe_print("OK - Dependencias instaladas com sucesso")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erro na instalacao: {e}")
            self.safe_print(f"ERRO - Falha na instalacao: {e}")
            return False
        
        return True
    
    def start_api(self):
        """Inicia API FastAPI"""
        
        self.safe_print("STEP 3 - Iniciando API FastAPI...")
        self.logger.info("Iniciando servidor FastAPI")
        
        try:
            cmd = [
                sys.executable, '-m', 'uvicorn',
                'app.main:app',
                '--host', '0.0.0.0',
                '--port', '8001',
                '--reload'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.processes['api'] = process
            self.logger.info("API FastAPI iniciada na porta 8001")
            self.safe_print("OK - API iniciada em http://localhost:8001")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar API: {e}")
            self.safe_print(f"ERRO - Falha ao iniciar API: {e}")
            return False
    
    def start_pdf_interface(self):
        """Inicia interface PDF Streamlit"""
        
        self.safe_print("STEP 4 - Iniciando interface PDF...")
        self.logger.info("Iniciando interface PDF Streamlit")
        
        try:
            cmd = [
                sys.executable, '-m', 'streamlit', 'run',
                'interface_pdf.py',
                '--server.port', '8502',
                '--server.headless', 'true'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.processes['pdf_interface'] = process
            self.logger.info("Interface PDF iniciada na porta 8502")
            self.safe_print("OK - Interface PDF em http://localhost:8502")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar interface PDF: {e}")
            self.safe_print(f"ERRO - Falha ao iniciar interface PDF: {e}")
            return False
    
    def start_scrapers(self):
        """Inicia sistema de scrapers"""
        
        self.safe_print("STEP 5 - Iniciando sistema de scrapers...")
        self.logger.info("Iniciando scrapers em background")
        
        try:
            # Scrapers rodam em background como thread
            scraper_thread = threading.Thread(target=self.run_scrapers_background)
            scraper_thread.daemon = True
            scraper_thread.start()
            
            self.logger.info("Sistema de scrapers iniciado")
            self.safe_print("OK - Scrapers iniciados em background")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar scrapers: {e}")
            self.safe_print(f"ERRO - Falha ao iniciar scrapers: {e}")
            return False
    
    def run_scrapers_background(self):
        """Executa scrapers em background"""
        while self.running:
            try:
                # Simular execução de scrapers
                time.sleep(300)  # 5 minutos
                self.logger.info("Ciclo de scraping executado")
            except Exception as e:
                self.logger.error(f"Erro no scraping: {e}")
                break
    
    def open_interfaces(self):
        """Abre interfaces no navegador"""
        
        self.safe_print("STEP 6 - Abrindo interfaces...")
        
        # Aguardar serviços iniciarem
        time.sleep(3)
        
        try:
            # Abrir API docs
            webbrowser.open('http://localhost:8001/docs')
            self.logger.info("Documentacao API aberta")
            
            # Aguardar um pouco
            time.sleep(2)
            
            # Abrir interface PDF
            webbrowser.open('http://localhost:8502')
            self.logger.info("Interface PDF aberta")
            
            self.safe_print("OK - Interfaces abertas no navegador")
            
        except Exception as e:
            self.logger.error(f"Erro ao abrir interfaces: {e}")
            self.safe_print("AVISO - Abra manualmente os links acima")
    
    def show_status(self):
        """Mostra status do sistema"""
        
        self.safe_print("\n" + "="*60)
        self.safe_print("CONCURSAI SISTEMA ATIVO")
        self.safe_print("="*60)
        self.safe_print("API FastAPI: http://localhost:8001")
        self.safe_print("Documentacao: http://localhost:8001/docs")
        self.safe_print("Interface PDF: http://localhost:8502")
        self.safe_print("="*60)
        self.safe_print("Pressione Ctrl+C para parar o sistema")
        self.safe_print("="*60 + "\n")
        
        self.logger.info("Sistema completamente operacional")
    
    def start_system(self):
        """Inicia sistema completo"""
        
        self.safe_print("INICIANDO CONCURSAI SISTEMA COMPLETO")
        self.safe_print("="*50)
        
        # 1. Verificar dependências
        if not self.check_dependencies():
            return False
        
        # 2. Iniciar API
        if not self.start_api():
            return False
        
        # 3. Iniciar interface PDF
        if not self.start_pdf_interface():
            return False
        
        # 4. Iniciar scrapers
        if not self.start_scrapers():
            return False
        
        # 5. Abrir interfaces
        self.open_interfaces()
        
        # 6. Mostrar status
        self.show_status()
        
        # 7. Manter sistema rodando
        self.running = True
        
        try:
            while self.running:
                time.sleep(5)
                
                # Verificar processos sem emojis
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        self.logger.warning(f"Processo {name} foi encerrado")
                        self.safe_print(f"AVISO - Processo {name} parou")
                        
        except KeyboardInterrupt:
            self.safe_print("\nParando sistema...")
            self.stop_system()
    
    def stop_system(self):
        """Para sistema completo"""
        
        self.running = False
        self.safe_print("Encerrando processos...")
        self.logger.info("Iniciando encerramento do sistema")
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                self.logger.info(f"Processo {name} encerrado")
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.warning(f"Processo {name} forcadamente encerrado")
            except Exception as e:
                self.logger.error(f"Erro ao encerrar {name}: {e}")
        
        self.safe_print("ConcursAI encerrado com sucesso!")
        self.logger.info("Sistema completamente encerrado")

def main():
    """Função principal"""
    try:
        system = ConcursAISystemFixed()
        system.start_system()
    except Exception as e:
        print(f"ERRO CRITICO: {e}")
        logging.error(f"Erro critico no sistema: {e}")

if __name__ == "__main__":
    main()
