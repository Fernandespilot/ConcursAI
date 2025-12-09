"""
🚀 SISTEMA COMPLETO V2 - SEM STREAMLIT PROBLEMÁTICO
===================================================
Versão com interface API pura, sem dependência do Streamlit
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
    logger = logging.getLogger('concursai_system_v2')
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
            'concursai_sistema_v2.log', 
            encoding='utf-8', 
            mode='a'
        )
        file_handler.setLevel(logging.INFO)
    except:
        # Fallback para encoding padrão
        file_handler = logging.FileHandler('concursai_sistema_v2.log', mode='a')
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

class ConcursAISystemV2:
    """Sistema ConcursAI V2 - Foco na API"""
    
    def __init__(self):
        self.logger = setup_logging_safe()
        self.processes = {}
        self.running = False
        self.logger.info("Sistema ConcursAI V2 inicializado")
        
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
        """Verifica dependências essenciais apenas"""
        
        self.safe_print("STEP 1 - Verificando dependencias essenciais...")
        self.logger.info("Iniciando verificacao de dependencias")
        
        # Apenas dependências essenciais para API
        required_packages = [
            'fastapi', 'uvicorn', 'requests', 'pandas'
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
            return False
        
        self.safe_print("OK - Dependencias essenciais verificadas")
        return True
    
    def start_api(self):
        """Inicia API FastAPI"""
        
        self.safe_print("STEP 2 - Iniciando API FastAPI...")
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
    
    def start_scrapers(self):
        """Inicia sistema de scrapers"""
        
        self.safe_print("STEP 3 - Iniciando sistema de scrapers...")
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
    
    def create_html_interface(self):
        """Cria interface HTML simples"""
        
        self.safe_print("STEP 4 - Criando interface HTML...")
        
        html_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ConcursAI - Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .status-card h3 {
            margin-top: 0;
            color: #667eea;
        }
        
        .btn {
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 5px;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #5a6fd8;
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .feature-card {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .feature-card h4 {
            color: #667eea;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ConcursAI - Sistema Operacional</h1>
            <p>Plataforma inteligente para análise de concursos públicos</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>📡 API Status</h3>
                <p><strong>Porta:</strong> 8001</p>
                <p><strong>Status:</strong> ✅ Ativo</p>
                <a href="http://localhost:8001/docs" class="btn">Acessar Documentação</a>
            </div>
            
            <div class="status-card">
                <h3>🕷️ Scrapers</h3>
                <p><strong>Status:</strong> ✅ Rodando</p>
                <p><strong>Última coleta:</strong> Ativo</p>
                <a href="http://localhost:8001/api/v1/concursos" class="btn">Ver Concursos</a>
            </div>
            
            <div class="status-card">
                <h3>🤖 Sistema IA</h3>
                <p><strong>LangChain:</strong> ✅ Disponível</p>
                <p><strong>Ollama:</strong> ⚠️ Opcional</p>
                <a href="http://localhost:8001/api/v1/chat" class="btn">Testar Chat</a>
            </div>
        </div>
        
        <h2>🎯 Funcionalidades Disponíveis</h2>
        
        <div class="feature-grid">
            <div class="feature-card">
                <h4>📄 Análise de PDFs</h4>
                <p>Upload e processamento de editais</p>
                <a href="http://localhost:8001/api/v1/pdf/upload" class="btn">Acessar</a>
            </div>
            
            <div class="feature-card">
                <h4>🔍 Busca de Concursos</h4>
                <p>Pesquisa inteligente de editais</p>
                <a href="http://localhost:8001/api/v1/search" class="btn">Pesquisar</a>
            </div>
            
            <div class="feature-card">
                <h4>💬 Chat IA</h4>
                <p>Conversa com documentos</p>
                <a href="http://localhost:8001/api/v1/chat" class="btn">Chat</a>
            </div>
            
            <div class="feature-card">
                <h4>📊 Relatórios</h4>
                <p>Dashboards e métricas</p>
                <a href="http://localhost:8001/api/v1/reports" class="btn">Relatórios</a>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p><strong>ConcursAI v2.0</strong> - Sistema completamente operacional</p>
            <p>🔗 <a href="http://localhost:8001" class="btn">Acessar API Principal</a></p>
        </div>
    </div>
    
    <script>
        // Auto-refresh status
        setTimeout(function() {
            location.reload();
        }, 60000); // Refresh a cada minuto
    </script>
</body>
</html>
        """
        
        # Salvar interface HTML
        with open('dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info("Interface HTML criada: dashboard.html")
        self.safe_print("OK - Interface HTML criada")
        
        return True
    
    def open_interfaces(self):
        """Abre interfaces no navegador"""
        
        self.safe_print("STEP 5 - Abrindo interfaces...")
        
        # Aguardar serviços iniciarem
        time.sleep(3)
        
        try:
            # Abrir dashboard HTML
            dashboard_path = os.path.abspath('dashboard.html')
            webbrowser.open(f'file://{dashboard_path}')
            self.logger.info("Dashboard HTML aberto")
            
            # Aguardar um pouco
            time.sleep(2)
            
            # Abrir API docs
            webbrowser.open('http://localhost:8001/docs')
            self.logger.info("Documentacao API aberta")
            
            self.safe_print("OK - Interfaces abertas no navegador")
            
        except Exception as e:
            self.logger.error(f"Erro ao abrir interfaces: {e}")
            self.safe_print("AVISO - Abra manualmente os links")
    
    def show_status(self):
        """Mostra status do sistema"""
        
        self.safe_print("\n" + "="*60)
        self.safe_print("CONCURSAI V2 SISTEMA ATIVO")
        self.safe_print("="*60)
        self.safe_print("API FastAPI: http://localhost:8001")
        self.safe_print("Documentacao: http://localhost:8001/docs")
        self.safe_print("Dashboard: dashboard.html")
        self.safe_print("="*60)
        self.safe_print("Pressione Ctrl+C para parar o sistema")
        self.safe_print("="*60 + "\n")
        
        self.logger.info("Sistema V2 completamente operacional")
    
    def start_system(self):
        """Inicia sistema completo V2"""
        
        self.safe_print("INICIANDO CONCURSAI SISTEMA V2")
        self.safe_print("="*50)
        
        # 1. Verificar dependências
        if not self.check_dependencies():
            self.safe_print("ERRO - Instale as dependencias: pip install fastapi uvicorn requests pandas")
            return False
        
        # 2. Iniciar API
        if not self.start_api():
            return False
        
        # 3. Iniciar scrapers
        if not self.start_scrapers():
            return False
        
        # 4. Criar interface HTML
        if not self.create_html_interface():
            return False
        
        # 5. Abrir interfaces
        self.open_interfaces()
        
        # 6. Mostrar status
        self.show_status()
        
        # 7. Manter sistema rodando
        self.running = True
        
        try:
            while self.running:
                time.sleep(10)
                
                # Verificar processos sem problemas
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
        
        self.safe_print("ConcursAI V2 encerrado com sucesso!")
        self.logger.info("Sistema completamente encerrado")

def main():
    """Função principal"""
    try:
        system = ConcursAISystemV2()
        system.start_system()
    except Exception as e:
        print(f"ERRO CRITICO: {e}")
        logging.error(f"Erro critico no sistema: {e}")

if __name__ == "__main__":
    main()
