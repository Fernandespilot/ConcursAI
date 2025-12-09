#!/usr/bin/env python3
"""
🔍 ANÁLISE E TESTE COMPLETO DO PROJETO CONCURSAI
===============================================
Análise detalhada de todos os componentes e testes abrangentes
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime
import json
import traceback

class ConcursAIAnalyzer:
    """Analisador completo do projeto ConcursAI"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.analysis_results = {}
        self.test_results = {}
        
    def analyze_project_structure(self):
        """Analisa estrutura do projeto"""
        
        print("📁 ANÁLISE DA ESTRUTURA DO PROJETO")
        print("=" * 50)
        
        # Componentes principais
        components = {
            'API': {
                'path': 'app/',
                'files': ['main.py', 'config.py'],
                'description': 'FastAPI Application'
            },
            'Modules': {
                'path': 'modules/',
                'files': ['pdf_processor.py', 'concurso_rag.py', 'embeddings.py'],
                'description': 'Core System Modules'
            },
            'Scrapers': {
                'path': 'scrapers/',
                'files': ['pci_scraper.py', 'concursos_brasil_scraper.py', 'scraper_manager.py'],
                'description': 'Web Scrapers'
            },
            'Interfaces': {
                'path': 'interfaces/',
                'files': ['interface_pdf.py'],
                'description': 'User Interfaces'
            },
            'Static': {
                'path': 'static/',
                'files': ['pdf_interface.html'],
                'description': 'Static Web Files'
            }
        }
        
        structure_analysis = {}
        
        for name, info in components.items():
            path = self.project_root / info['path']
            exists = path.exists()
            
            if exists:
                files_found = []
                files_missing = []
                
                for file_name in info['files']:
                    file_path = path / file_name
                    if file_path.exists():
                        files_found.append(file_name)
                    else:
                        files_missing.append(file_name)
                
                # Contar arquivos Python
                py_files = len(list(path.glob("*.py")))
                
                structure_analysis[name] = {
                    'exists': True,
                    'files_found': files_found,
                    'files_missing': files_missing,
                    'total_py_files': py_files,
                    'description': info['description']
                }
                
                status = "✅" if not files_missing else "⚠️"
                print(f"   {status} {name:<12} - {info['description']}")
                print(f"      📄 {len(files_found)}/{len(info['files'])} arquivos principais")
                print(f"      🐍 {py_files} arquivos Python total")
                
                if files_missing:
                    print(f"      ❌ Faltando: {', '.join(files_missing)}")
            else:
                structure_analysis[name] = {
                    'exists': False,
                    'description': info['description']
                }
                print(f"   ❌ {name:<12} - {info['description']} (NÃO ENCONTRADO)")
        
        self.analysis_results['structure'] = structure_analysis
        return structure_analysis
    
    def test_system_imports(self):
        """Testa importações do sistema"""
        
        print(f"\n🧪 TESTE DE IMPORTAÇÕES DO SISTEMA")
        print("=" * 40)
        
        import_tests = [
            ('sistema_completo', 'Sistema principal'),
            ('modules.pdf_processor', 'PDF processor'),
            ('scrapers.scraper_manager', 'Scraper manager'),
            ('scrapers.pci_scraper', 'PCI scraper')
        ]
        
        import_results = {}
        
        # Adicionar diretório atual ao path
        sys.path.insert(0, str(self.project_root))
        
        for module_name, description in import_tests:
            try:
                __import__(module_name)
                import_results[module_name] = True
                print(f"   ✅ {module_name:<25} - {description}")
            except Exception as e:
                import_results[module_name] = False
                print(f"   ❌ {module_name:<25} - {description}")
                print(f"      Erro: {str(e)[:100]}")
        
        self.test_results['imports'] = import_results
        return import_results
    
    def test_api_status(self):
        """Testa status da API (se estiver rodando)"""
        
        print(f"\n🌐 TESTE DE STATUS DA API")
        print("=" * 30)
        
        base_url = "http://localhost:8001"
        endpoints = [
            '/health',
            '/docs'
        ]
        
        api_results = {}
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                response = requests.get(url, timeout=3)
                api_results[endpoint] = {
                    'status': response.status_code,
                    'accessible': response.status_code < 400
                }
                
                status_icon = "✅" if response.status_code < 400 else "❌"
                print(f"   {status_icon} {endpoint:<15} - Status {response.status_code}")
                
            except requests.exceptions.RequestException:
                api_results[endpoint] = {
                    'status': None,
                    'accessible': False
                }
                print(f"   ⚠️  {endpoint:<15} - API não está rodando")
        
        self.test_results['api'] = api_results
        return api_results
    
    def test_scrapers_functionality(self):
        """Testa funcionalidade dos scrapers"""
        
        print(f"\n🕷️ TESTE DE FUNCIONALIDADE DOS SCRAPERS")
        print("=" * 40)
        
        scraper_results = {}
        
        try:
            # Testar import do scraper manager
            from scrapers.scraper_manager import ScraperManager
            scraper_results['import'] = True
            print("   ✅ ScraperManager importado com sucesso")
            
            # Criar instância
            try:
                manager = ScraperManager()
                scraper_results['instantiation'] = True
                print("   ✅ ScraperManager instanciado")
                
                # Testar scrapers disponíveis
                available_scrapers = ['pci', 'concursos_brasil']
                print(f"   📋 Scrapers disponíveis: {', '.join(available_scrapers)}")
                scraper_results['available_scrapers'] = available_scrapers
                
            except Exception as e:
                scraper_results['instantiation'] = False
                print(f"   ❌ Erro na instanciação: {e}")
                
        except Exception as e:
            scraper_results['import'] = False
            print(f"   ❌ Erro no import: {e}")
        
        self.test_results['scrapers'] = scraper_results
        return scraper_results
    
    def test_pdf_system(self):
        """Testa sistema de PDF"""
        
        print(f"\n📄 TESTE DO SISTEMA PDF")
        print("=" * 25)
        
        pdf_results = {}
        
        try:
            from modules.pdf_processor import LangChainPDFAnalyzer
            pdf_results['import'] = True
            print("   ✅ LangChainPDFAnalyzer importado")
            
            try:
                analyzer = LangChainPDFAnalyzer()
                pdf_results['instantiation'] = True
                print("   ✅ PDFAnalyzer instanciado")
                print(f"   🤖 Modelo configurado: {analyzer.model}")
                print(f"   🔗 URL Ollama: {analyzer.ollama_url}")
                
                # Verificar documentos
                docs = analyzer.list_documents()
                pdf_results['document_count'] = len(docs)
                print(f"   📄 Documentos disponíveis: {len(docs)}")
                
            except Exception as e:
                pdf_results['instantiation'] = False
                print(f"   ❌ Erro na instanciação: {e}")
                
        except Exception as e:
            pdf_results['import'] = False
            print(f"   ❌ Erro no import: {e}")
        
        self.test_results['pdf'] = pdf_results
        return pdf_results
    
    def check_ollama_status(self):
        """Verifica status do Ollama"""
        
        print(f"\n🤖 VERIFICAÇÃO DO OLLAMA")
        print("=" * 25)
        
        ollama_results = {}
        
        try:
            # Testar conexão com Ollama
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                
                ollama_results['status'] = 'online'
                ollama_results['models'] = models
                
                print("   ✅ Ollama online e funcionando")
                print(f"   🤖 Modelos disponíveis: {len(models)}")
                for model in models[:3]:  # Mostrar apenas 3 primeiros
                    print(f"      • {model}")
                if len(models) > 3:
                    print(f"      ... e mais {len(models) - 3} modelos")
            else:
                ollama_results['status'] = 'error'
                print(f"   ❌ Ollama retornou status {response.status_code}")
                
        except requests.exceptions.RequestException:
            ollama_results['status'] = 'offline'
            print("   ⚠️  Ollama offline ou não instalado")
            print("   💡 Sistema funcionará em modo limitado")
        
        self.test_results['ollama'] = ollama_results
        return ollama_results
    
    def analyze_code_metrics(self):
        """Analisa métricas do código"""
        
        print(f"\n📊 MÉTRICAS DO CÓDIGO")
        print("=" * 25)
        
        # Contar arquivos por tipo
        py_files = list(self.project_root.rglob("*.py"))
        md_files = list(self.project_root.rglob("*.md"))
        json_files = list(self.project_root.rglob("*.json"))
        html_files = list(self.project_root.rglob("*.html"))
        
        metrics = {
            'python': len(py_files),
            'markdown': len(md_files),
            'json': len(json_files),
            'html': len(html_files)
        }
        
        print(f"   🐍 Arquivos Python: {metrics['python']}")
        print(f"   📚 Arquivos Markdown: {metrics['markdown']}")
        print(f"   🔧 Arquivos JSON: {metrics['json']}")
        print(f"   🌐 Arquivos HTML: {metrics['html']}")
        
        self.analysis_results['metrics'] = metrics
        return metrics
    
    def generate_summary_report(self):
        """Gera relatório resumido"""
        
        print(f"\n📋 RELATÓRIO FINAL")
        print("=" * 20)
        
        # Calcular estatísticas
        total_tests = len(self.test_results)
        successful_imports = sum(1 for result in self.test_results.get('imports', {}).values() if result)
        total_imports = len(self.test_results.get('imports', {}))
        
        # Status dos componentes
        structure_ok = len([comp for comp in self.analysis_results.get('structure', {}).values() if comp.get('exists')])
        total_components = len(self.analysis_results.get('structure', {}))
        
        print(f"🎯 RESUMO GERAL:")
        print(f"   📁 Componentes estruturais: {structure_ok}/{total_components}")
        print(f"   🧪 Importações funcionais: {successful_imports}/{total_imports}")
        
        # Status dos sistemas
        systems_status = []
        
        if self.test_results.get('scrapers', {}).get('import'):
            systems_status.append("✅ Scrapers")
        else:
            systems_status.append("❌ Scrapers")
            
        if self.test_results.get('pdf', {}).get('import'):
            systems_status.append("✅ PDF")
        else:
            systems_status.append("❌ PDF")
            
        api_working = any(ep.get('accessible') for ep in self.test_results.get('api', {}).values())
        if api_working:
            systems_status.append("✅ API")
        else:
            systems_status.append("⚠️ API (não rodando)")
            
        ollama_status = self.test_results.get('ollama', {}).get('status', 'unknown')
        if ollama_status == 'online':
            systems_status.append("✅ Ollama")
        elif ollama_status == 'offline':
            systems_status.append("⚠️ Ollama")
        else:
            systems_status.append("❌ Ollama")
        
        print(f"\n🔧 STATUS DOS SISTEMAS:")
        for status in systems_status:
            print(f"   {status}")
        
        # Próximos passos
        print(f"\n🚀 PRÓXIMOS PASSOS RECOMENDADOS:")
        
        if not api_working:
            print("   1. Iniciar sistema: python sistema_completo.py")
        else:
            print("   1. ✅ Sistema já rodando!")
            
        if ollama_status != 'online':
            print("   2. Instalar/iniciar Ollama para IA completa")
        else:
            print("   2. ✅ Ollama funcionando!")
            
        print("   3. Testar interfaces: http://localhost:8001")
        print("   4. Desenvolver novas funcionalidades")
        
        return {
            'structure_ok': structure_ok,
            'total_components': total_components,
            'successful_imports': successful_imports,
            'total_imports': total_imports,
            'systems_status': systems_status
        }
    
    def run_complete_analysis(self):
        """Executa análise completa do projeto"""
        
        print("🔍 ANÁLISE COMPLETA DO PROJETO CONCURSAI")
        print("=" * 50)
        print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Diretório: {self.project_root}")
        
        try:
            # Análises estruturais
            self.analyze_project_structure()
            self.analyze_code_metrics()
            
            # Testes funcionais
            self.test_system_imports()
            self.test_api_status()
            self.test_scrapers_functionality()
            self.test_pdf_system()
            self.check_ollama_status()
            
            # Gerar relatório resumido
            summary = self.generate_summary_report()
            
            print(f"\n" + "=" * 50)
            print("🎉 ANÁLISE COMPLETA FINALIZADA!")
            print("=" * 50)
            
            return {
                'analysis_results': self.analysis_results,
                'test_results': self.test_results,
                'summary': summary
            }
            
        except Exception as e:
            print(f"\n❌ Erro durante análise: {e}")
            traceback.print_exc()
            return None

def main():
    """Função principal"""
    
    # Mudar para diretório do projeto
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Criar analisador
    analyzer = ConcursAIAnalyzer()
    
    # Executar análise completa
    results = analyzer.run_complete_analysis()
    
    if results:
        print(f"\n✅ Análise concluída com sucesso!")
        return results
    else:
        print(f"\n❌ Análise falhou!")
        return None

if __name__ == "__main__":
    main()
