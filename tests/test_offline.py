#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTE OFFLINE - ConcursAI
===========================
Testes que podem ser executados sem servidor rodando
"""

import os
import sys
import json
import pandas as pd
import time
from datetime import datetime

# Adicionar diretório do projeto ao path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

class TestadorOffline:
    """Testador para análises que não precisam do servidor"""
    
    def __init__(self):
        self.project_dir = project_dir
        self.results = {}
        self.start_time = time.time()
        
    def run_offline_tests(self):
        """Executa todos os testes offline"""
        print("🧪 TESTADOR OFFLINE DO CONCURSAI")
        print("=" * 50)
        print(f"📂 Diretório: {self.project_dir}")
        print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Lista de testes offline
        tests = [
            ('estrutura_arquivos', 'Estrutura de Arquivos'),
            ('analise_scraper', 'Análise do Scraper'),
            ('validacao_api', 'Validação da API'),
            ('analise_frontend', 'Análise do Frontend'),
            ('qualidade_codigo', 'Qualidade do Código'),
            ('documentacao', 'Documentação'),
            ('configuracao', 'Configuração do Projeto'),
            ('dependencias', 'Dependências'),
            ('performance_estimada', 'Performance Estimada'),
            ('seguranca_basica', 'Segurança Básica')
        ]
        
        for test_name, description in tests:
            print(f"🔍 {description}")
            print("-" * 30)
            
            try:
                method = getattr(self, f'test_{test_name}')
                result = method()
                self.results[test_name] = result
                
                # Status visual
                status = "✅" if result['status'] == 'pass' else "⚠️" if result['status'] == 'warning' else "❌"
                print(f"{status} {result['summary']}")
                
                if result.get('details'):
                    for detail in result['details'][:3]:  # Mostrar apenas 3 primeiros
                        print(f"   • {detail}")
                
                print()
                
            except Exception as e:
                print(f"❌ Erro no teste: {e}")
                self.results[test_name] = {
                    'status': 'error',
                    'summary': f'Erro: {str(e)}',
                    'details': []
                }
                print()
        
        # Resumo final
        self._print_summary()
        self._save_report()
        
        return self.results
    
    def test_estrutura_arquivos(self):
        """Teste 1: Estrutura de arquivos do projeto"""
        required_files = [
            'api_simplificada.py',
            'coletor_pci_real.py',
            'static/interface_editais.html',
            'scrapers/pci_scraper_atual.py',
            'integrador_pci.py',
            'requirements.txt'
        ]
        
        found_files = []
        missing_files = []
        
        for file_path in required_files:
            full_path = os.path.join(self.project_dir, file_path)
            if os.path.exists(full_path):
                found_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        # Verificar diretórios importantes
        important_dirs = ['static', 'scrapers', 'tests']
        existing_dirs = [d for d in important_dirs if os.path.exists(os.path.join(self.project_dir, d))]
        
        status = 'pass' if len(missing_files) == 0 else 'warning' if len(missing_files) <= 2 else 'fail'
        
        return {
            'status': status,
            'summary': f'{len(found_files)}/{len(required_files)} arquivos essenciais encontrados',
            'details': [
                f'Arquivos encontrados: {len(found_files)}',
                f'Arquivos faltando: {len(missing_files)}',
                f'Diretórios: {", ".join(existing_dirs)}',
                f'Faltando: {", ".join(missing_files)}' if missing_files else 'Todos os arquivos presentes'
            ],
            'data': {
                'found_files': found_files,
                'missing_files': missing_files,
                'existing_dirs': existing_dirs
            }
        }
    
    def test_analise_scraper(self):
        """Teste 2: Análise do scraper PCI"""
        scraper_file = os.path.join(self.project_dir, 'scrapers', 'pci_scraper_atual.py')
        
        if not os.path.exists(scraper_file):
            return {
                'status': 'fail',
                'summary': 'Arquivo do scraper não encontrado',
                'details': ['scrapers/pci_scraper_atual.py não existe']
            }
        
        # Ler e analisar o arquivo
        with open(scraper_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar características importantes
        features = {
            'requests_import': 'import requests' in content,
            'beautifulsoup_import': 'BeautifulSoup' in content,
            'rate_limiting': 'time.sleep' in content or 'rate_limit' in content.lower(),
            'error_handling': 'try:' in content and 'except' in content,
            'user_agent': 'user-agent' in content.lower() or 'User-Agent' in content,
            'class_definition': 'class ' in content,
            'pci_url': 'pciconcursos' in content.lower(),
            'data_parsing': 'find(' in content or 'select(' in content
        }
        
        score = sum(features.values())
        total_features = len(features)
        
        status = 'pass' if score >= total_features * 0.8 else 'warning' if score >= total_features * 0.6 else 'fail'
        
        return {
            'status': status,
            'summary': f'Scraper: {score}/{total_features} características implementadas',
            'details': [
                f'Score: {score}/{total_features} ({(score/total_features)*100:.1f}%)',
                f'Imports corretos: {"✅" if features["requests_import"] and features["beautifulsoup_import"] else "❌"}',
                f'Rate limiting: {"✅" if features["rate_limiting"] else "❌"}',
                f'Error handling: {"✅" if features["error_handling"] else "❌"}',
                f'PCI integration: {"✅" if features["pci_url"] else "❌"}'
            ],
            'data': features
        }
    
    def test_validacao_api(self):
        """Teste 3: Validação da estrutura da API"""
        api_file = os.path.join(self.project_dir, 'api_simplificada.py')
        
        if not os.path.exists(api_file):
            return {
                'status': 'fail',
                'summary': 'Arquivo da API não encontrado',
                'details': ['api_simplificada.py não existe']
            }
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar endpoints e características
        api_features = {
            'fastapi_import': 'from fastapi import' in content,
            'app_creation': 'app = FastAPI' in content,
            'cors_enabled': 'CORSMiddleware' in content,
            'static_files': 'StaticFiles' in content,
            'concursos_endpoint': '@app.get' in content and '/concursos' in content,
            'admin_endpoints': '/admin/' in content,
            'error_handling': 'HTTPException' in content,
            'pydantic_models': 'BaseModel' in content,
            'background_tasks': 'BackgroundTasks' in content or 'background' in content.lower()
        }
        
        score = sum(api_features.values())
        total_features = len(api_features)
        
        status = 'pass' if score >= total_features * 0.8 else 'warning' if score >= total_features * 0.6 else 'fail'
        
        return {
            'status': status,
            'summary': f'API: {score}/{total_features} características implementadas',
            'details': [
                f'Score: {score}/{total_features} ({(score/total_features)*100:.1f}%)',
                f'FastAPI: {"✅" if api_features["fastapi_import"] else "❌"}',
                f'CORS: {"✅" if api_features["cors_enabled"] else "❌"}',
                f'Endpoints: {"✅" if api_features["concursos_endpoint"] else "❌"}',
                f'Admin features: {"✅" if api_features["admin_endpoints"] else "❌"}'
            ],
            'data': api_features
        }
    
    def test_analise_frontend(self):
        """Teste 4: Análise do frontend"""
        frontend_file = os.path.join(self.project_dir, 'static', 'interface_editais.html')
        
        if not os.path.exists(frontend_file):
            return {
                'status': 'fail',
                'summary': 'Interface não encontrada',
                'details': ['static/interface_editais.html não existe']
            }
        
        with open(frontend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Análise do HTML/CSS/JS
        frontend_features = {
            'html5_doctype': '<!DOCTYPE html>' in content,
            'responsive_viewport': 'viewport' in content,
            'css_grid_flexbox': 'display: grid' in content or 'display: flex' in content,
            'javascript_functions': 'function ' in content,
            'api_integration': 'fetch(' in content,
            'search_functionality': 'buscarEditais' in content,
            'modern_css': 'border-radius:' in content and 'transition:' in content,
            'accessibility_basics': 'aria-' in content or 'alt=' in content,
            'admin_buttons': 'coletarDadosReais' in content
        }
        
        file_size = len(content)
        
        score = sum(frontend_features.values())
        total_features = len(frontend_features)
        
        status = 'pass' if score >= total_features * 0.8 else 'warning' if score >= total_features * 0.6 else 'fail'
        
        return {
            'status': status,
            'summary': f'Frontend: {score}/{total_features} características modernas',
            'details': [
                f'Score: {score}/{total_features} ({(score/total_features)*100:.1f}%)',
                f'Tamanho: {file_size/1024:.1f}KB',
                f'HTML5: {"✅" if frontend_features["html5_doctype"] else "❌"}',
                f'Responsivo: {"✅" if frontend_features["responsive_viewport"] else "❌"}',
                f'Modern CSS: {"✅" if frontend_features["modern_css"] else "❌"}'
            ],
            'data': frontend_features
        }
    
    def test_qualidade_codigo(self):
        """Teste 5: Qualidade geral do código"""
        python_files = []
        
        # Encontrar arquivos Python
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    python_files.append(os.path.join(root, file))
        
        if not python_files:
            return {
                'status': 'fail',
                'summary': 'Nenhum arquivo Python encontrado',
                'details': []
            }
        
        total_lines = 0
        total_comments = 0
        total_functions = 0
        total_classes = 0
        files_with_docstrings = 0
        
        for py_file in python_files[:10]:  # Limitar a 10 arquivos
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    total_lines += len(lines)
                    total_comments += sum(1 for line in lines if line.strip().startswith('#'))
                    total_functions += content.count('def ')
                    total_classes += content.count('class ')
                    
                    if '"""' in content or "'''" in content:
                        files_with_docstrings += 1
                        
            except Exception:
                continue
        
        comment_ratio = (total_comments / total_lines * 100) if total_lines > 0 else 0
        docstring_ratio = (files_with_docstrings / len(python_files) * 100) if python_files else 0
        
        status = 'pass' if comment_ratio >= 10 and docstring_ratio >= 50 else 'warning' if comment_ratio >= 5 else 'fail'
        
        return {
            'status': status,
            'summary': f'Código: {len(python_files)} arquivos, {comment_ratio:.1f}% comentários',
            'details': [
                f'Arquivos Python: {len(python_files)}',
                f'Total de linhas: {total_lines}',
                f'Comentários: {total_comments} ({comment_ratio:.1f}%)',
                f'Funções: {total_functions}',
                f'Classes: {total_classes}',
                f'Arquivos com docstrings: {files_with_docstrings} ({docstring_ratio:.1f}%)'
            ],
            'data': {
                'files_count': len(python_files),
                'total_lines': total_lines,
                'comment_ratio': comment_ratio,
                'docstring_ratio': docstring_ratio
            }
        }
    
    def test_documentacao(self):
        """Teste 6: Documentação do projeto"""
        doc_files = ['README.md', 'README', 'docs/', 'DOCS.md']
        
        found_docs = []
        for doc in doc_files:
            doc_path = os.path.join(self.project_dir, doc)
            if os.path.exists(doc_path):
                found_docs.append(doc)
        
        # Verificar se há arquivos de análise/relatórios
        analysis_files = []
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if any(keyword in file.lower() for keyword in ['analise', 'relatorio', 'report', 'analysis']):
                    analysis_files.append(file)
        
        status = 'pass' if len(found_docs) >= 2 else 'warning' if len(found_docs) >= 1 else 'fail'
        
        return {
            'status': status,
            'summary': f'Documentação: {len(found_docs)} arquivos principais',
            'details': [
                f'Docs encontrados: {", ".join(found_docs)}' if found_docs else 'Nenhuma documentação principal',
                f'Arquivos de análise: {len(analysis_files)}',
                f'Exemplos: {", ".join(analysis_files[:3])}' if analysis_files else 'Nenhuma análise'
            ],
            'data': {
                'doc_files': found_docs,
                'analysis_files': analysis_files
            }
        }
    
    def test_configuracao(self):
        """Teste 7: Configuração do projeto"""
        config_files = ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile']
        
        found_configs = []
        for config in config_files:
            if os.path.exists(os.path.join(self.project_dir, config)):
                found_configs.append(config)
        
        # Verificar requirements.txt se existe
        dependencies = []
        if 'requirements.txt' in found_configs:
            req_path = os.path.join(self.project_dir, 'requirements.txt')
            try:
                with open(req_path, 'r') as f:
                    dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            except Exception:
                pass
        
        status = 'pass' if 'requirements.txt' in found_configs else 'warning'
        
        return {
            'status': status,
            'summary': f'Configuração: {len(found_configs)} arquivos, {len(dependencies)} dependências',
            'details': [
                f'Arquivos de config: {", ".join(found_configs)}',
                f'Dependências: {len(dependencies)}',
                f'Principais: {", ".join(dependencies[:5])}' if dependencies else 'Nenhuma dependência listada'
            ],
            'data': {
                'config_files': found_configs,
                'dependencies': dependencies
            }
        }
    
    def test_dependencias(self):
        """Teste 8: Análise de dependências"""
        req_file = os.path.join(self.project_dir, 'requirements.txt')
        
        if not os.path.exists(req_file):
            return {
                'status': 'warning',
                'summary': 'requirements.txt não encontrado',
                'details': ['Arquivo de dependências não existe']
            }
        
        try:
            with open(req_file, 'r') as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception:
            return {
                'status': 'fail',
                'summary': 'Erro ao ler requirements.txt',
                'details': ['Não foi possível ler o arquivo']
            }
        
        # Dependências essenciais esperadas
        essential_deps = ['fastapi', 'requests', 'beautifulsoup4', 'pandas', 'uvicorn']
        found_essential = [dep for dep in essential_deps 
                          if any(dep.lower() in d.lower() for d in deps)]
        
        status = 'pass' if len(found_essential) >= 4 else 'warning' if len(found_essential) >= 3 else 'fail'
        
        return {
            'status': status,
            'summary': f'Dependências: {len(deps)} total, {len(found_essential)}/{len(essential_deps)} essenciais',
            'details': [
                f'Total de dependências: {len(deps)}',
                f'Essenciais encontradas: {", ".join(found_essential)}',
                f'Faltando: {", ".join(set(essential_deps) - set(found_essential))}' if len(found_essential) < len(essential_deps) else 'Todas essenciais presentes'
            ],
            'data': {
                'total_deps': len(deps),
                'essential_found': found_essential,
                'all_deps': deps
            }
        }
    
    def test_performance_estimada(self):
        """Teste 9: Estimativa de performance"""
        # Análise baseada no tamanho dos arquivos e estrutura
        
        file_sizes = {}
        total_size = 0
        
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(('.py', '.html', '.css', '.js')):
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        file_sizes[file] = size
                        total_size += size
                    except Exception:
                        continue
        
        # Análise da interface HTML
        html_file = os.path.join(self.project_dir, 'static', 'interface_editais.html')
        html_size = file_sizes.get('interface_editais.html', 0)
        
        # Estimativas baseadas em tamanho
        estimated_load_time = (html_size / 1024) * 0.1  # Estimativa simplificada
        
        performance_score = 0
        if html_size < 50000:  # < 50KB
            performance_score += 2
        elif html_size < 100000:  # < 100KB
            performance_score += 1
        
        if total_size < 500000:  # < 500KB total
            performance_score += 2
        elif total_size < 1000000:  # < 1MB total
            performance_score += 1
        
        status = 'pass' if performance_score >= 3 else 'warning' if performance_score >= 2 else 'fail'
        
        return {
            'status': status,
            'summary': f'Performance: {total_size/1024:.1f}KB total, score {performance_score}/4',
            'details': [
                f'Tamanho total: {total_size/1024:.1f}KB',
                f'Interface HTML: {html_size/1024:.1f}KB',
                f'Arquivos analisados: {len(file_sizes)}',
                f'Tempo estimado de carregamento: {estimated_load_time:.1f}s',
                f'Score de performance: {performance_score}/4'
            ],
            'data': {
                'total_size_kb': total_size/1024,
                'html_size_kb': html_size/1024,
                'estimated_load_time': estimated_load_time,
                'performance_score': performance_score
            }
        }
    
    def test_seguranca_basica(self):
        """Teste 10: Verificação básica de segurança"""
        security_issues = []
        security_score = 0
        
        # Verificar arquivo da API
        api_file = os.path.join(self.project_dir, 'api_simplificada.py')
        if os.path.exists(api_file):
            with open(api_file, 'r', encoding='utf-8') as f:
                api_content = f.read()
            
            # Verificações básicas
            if 'CORSMiddleware' in api_content:
                security_score += 1
            else:
                security_issues.append('CORS não configurado')
            
            if 'HTTPException' in api_content:
                security_score += 1
            else:
                security_issues.append('Tratamento de erro HTTP básico ausente')
            
            if any(word in api_content.lower() for word in ['secret', 'password', 'key']):
                if any(word in api_content for word in ['getenv', 'environ']):
                    security_score += 1
                else:
                    security_issues.append('Possíveis credenciais hardcoded')
            else:
                security_score += 1  # Nenhuma credencial aparente
        
        # Verificar se há arquivos de configuração sensíveis
        sensitive_files = ['.env', 'config.py', 'secrets.json']
        exposed_files = [f for f in sensitive_files 
                        if os.path.exists(os.path.join(self.project_dir, f))]
        
        if not exposed_files:
            security_score += 1
        else:
            security_issues.append(f'Arquivos sensíveis expostos: {", ".join(exposed_files)}')
        
        status = 'pass' if security_score >= 3 and len(security_issues) == 0 else 'warning' if security_score >= 2 else 'fail'
        
        return {
            'status': status,
            'summary': f'Segurança: {security_score}/4 pontos, {len(security_issues)} issues',
            'details': [
                f'Score de segurança: {security_score}/4',
                f'Issues encontrados: {len(security_issues)}',
                *security_issues[:3]  # Mostrar até 3 issues
            ],
            'data': {
                'security_score': security_score,
                'issues': security_issues
            }
        }
    
    def _print_summary(self):
        """Imprime resumo final"""
        execution_time = time.time() - self.start_time
        
        total_tests = len(self.results)
        passed = len([r for r in self.results.values() if r['status'] == 'pass'])
        warnings = len([r for r in self.results.values() if r['status'] == 'warning'])
        failed = len([r for r in self.results.values() if r['status'] == 'fail'])
        errors = len([r for r in self.results.values() if r['status'] == 'error'])
        
        print("🏁 RESUMO FINAL DOS TESTES OFFLINE")
        print("=" * 45)
        print(f"⏱️  Tempo total: {execution_time:.2f} segundos")
        print(f"📊 Total de testes: {total_tests}")
        print(f"✅ Passou: {passed}")
        print(f"⚠️ Aviso: {warnings}")
        print(f"❌ Falhou: {failed}")
        print(f"💥 Erros: {errors}")
        
        if total_tests > 0:
            health_score = ((passed * 1.0 + warnings * 0.7) / total_tests) * 100
            print(f"📈 Score de saúde: {health_score:.1f}%")
            
            if health_score >= 90:
                print("\n🎉 EXCELENTE! Projeto muito bem estruturado!")
            elif health_score >= 75:
                print("\n✅ BOM! Projeto bem organizado com pequenos ajustes.")
            elif health_score >= 50:
                print("\n⚠️ ATENÇÃO! Projeto funcional mas precisa de melhorias.")
            else:
                print("\n🚨 CRÍTICO! Projeto precisa de reestruturação.")
        
        print()
    
    def _save_report(self):
        """Salva relatório detalhado"""
        execution_time = time.time() - self.start_time
        
        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'execution_time_seconds': round(execution_time, 2),
                'project_directory': self.project_dir,
                'test_type': 'offline_analysis'
            },
            'summary': {
                'total_tests': len(self.results),
                'passed': len([r for r in self.results.values() if r['status'] == 'pass']),
                'warnings': len([r for r in self.results.values() if r['status'] == 'warning']),
                'failed': len([r for r in self.results.values() if r['status'] == 'fail']),
                'errors': len([r for r in self.results.values() if r['status'] == 'error'])
            },
            'detailed_results': self.results
        }
        
        # Salvar relatório
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        report_path = os.path.join(tests_dir, 'relatorio_offline.json')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório offline salvo em: {report_path}")

def main():
    """Função principal"""
    testador = TestadorOffline()
    results = testador.run_offline_tests()
    
    # Código de saída baseado nos resultados
    failed = len([r for r in results.values() if r['status'] == 'fail'])
    errors = len([r for r in results.values() if r['status'] == 'error'])
    
    if errors > 0:
        sys.exit(2)
    elif failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
