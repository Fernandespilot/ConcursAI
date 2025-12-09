#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 EXECUTOR DE TESTES - ConcursAI
=================================
Script principal para executar todos os testes e gerar relatório
"""

import unittest
import sys
import os
import time
import json
import subprocess
from datetime import datetime

# Adicionar o diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRunner:
    """Classe para executar e coordenar todos os testes"""
    
    def __init__(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(self.test_dir)
        self.results = {}
        self.start_time = time.time()
        
    def run_all_tests(self):
        """Executa todos os testes disponíveis"""
        print("🧪 EXECUTOR DE TESTES DO CONCURSAI")
        print("=" * 50)
        print(f"📂 Diretório de testes: {self.test_dir}")
        print(f"📂 Diretório do projeto: {self.project_dir}")
        print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Lista de módulos de teste
        test_modules = [
            ('test_api', 'Testes da API'),
            ('test_scraper', 'Testes do Scraper'),
            ('test_frontend', 'Testes do Frontend'),
            ('test_integration', 'Testes de Integração')
        ]
        
        total_passed = 0
        total_failed = 0
        total_errors = 0
        
        for module_name, description in test_modules:
            print(f"🔍 Executando: {description}")
            print("-" * 30)
            
            try:
                # Importar e executar o módulo de teste
                result = self._run_test_module(module_name)
                
                self.results[module_name] = result
                total_passed += result['passed']
                total_failed += result['failed']
                total_errors += result['errors']
                
                print(f"✅ {description} concluído")
                print(f"   Passou: {result['passed']}, Falhou: {result['failed']}, Erros: {result['errors']}")
                print()
                
            except Exception as e:
                print(f"❌ Erro ao executar {description}: {e}")
                self.results[module_name] = {
                    'passed': 0,
                    'failed': 0, 
                    'errors': 1,
                    'error_message': str(e)
                }
                total_errors += 1
                print()
        
        # Resumo final
        self._print_final_summary(total_passed, total_failed, total_errors)
        
        # Gerar relatórios
        self._generate_reports()
        
        return self.results
    
    def _run_test_module(self, module_name):
        """Executa um módulo de teste específico"""
        try:
            # Importar o módulo
            module = __import__(module_name)
            
            # Configurar o test runner
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # Executar os testes
            runner = unittest.TextTestRunner(
                verbosity=1,
                stream=open(os.devnull, 'w')  # Suprimir saída detalhada
            )
            
            result = runner.run(suite)
            
            return {
                'passed': result.testsRun - len(result.failures) - len(result.errors),
                'failed': len(result.failures),
                'errors': len(result.errors),
                'total': result.testsRun
            }
            
        except ImportError as e:
            print(f"⚠️ Não foi possível importar {module_name}: {e}")
            return {'passed': 0, 'failed': 0, 'errors': 1, 'total': 0}
        except Exception as e:
            print(f"⚠️ Erro ao executar {module_name}: {e}")
            return {'passed': 0, 'failed': 0, 'errors': 1, 'total': 0}
    
    def _print_final_summary(self, total_passed, total_failed, total_errors):
        """Imprime resumo final dos testes"""
        execution_time = time.time() - self.start_time
        total_tests = total_passed + total_failed + total_errors
        
        print("🏁 RESUMO FINAL DOS TESTES")
        print("=" * 50)
        print(f"⏱️  Tempo total: {execution_time:.2f} segundos")
        print(f"📊 Total de testes: {total_tests}")
        print(f"✅ Passou: {total_passed}")
        print(f"❌ Falhou: {total_failed}")
        print(f"💥 Erros: {total_errors}")
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print("\n🎉 EXCELENTE! Sistema muito estável!")
            elif success_rate >= 75:
                print("\n✅ BOM! Sistema estável com pequenos ajustes.")
            elif success_rate >= 50:
                print("\n⚠️ ATENÇÃO! Sistema precisa de melhorias.")
            else:
                print("\n🚨 CRÍTICO! Sistema precisa de correções urgentes.")
        
        print()
    
    def _generate_reports(self):
        """Gera relatórios detalhados"""
        print("📄 GERANDO RELATÓRIOS...")
        print("-" * 25)
        
        # Relatório principal
        main_report = self._create_main_report()
        main_report_path = os.path.join(self.test_dir, 'relatorio_completo.json')
        
        with open(main_report_path, 'w', encoding='utf-8') as f:
            json.dump(main_report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Relatório principal: {main_report_path}")
        
        # Relatório em texto
        text_report_path = os.path.join(self.test_dir, 'relatorio_completo.txt')
        self._create_text_report(main_report, text_report_path)
        print(f"📝 Relatório em texto: {text_report_path}")
        
        # Análise do sistema
        analysis_report_path = os.path.join(self.test_dir, 'analise_sistema.md')
        self._create_analysis_report(analysis_report_path)
        print(f"🔍 Análise do sistema: {analysis_report_path}")
        
        print()
    
    def _create_main_report(self):
        """Cria relatório principal em JSON"""
        execution_time = time.time() - self.start_time
        
        return {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'execution_time_seconds': round(execution_time, 2),
                'project_directory': self.project_dir,
                'test_directory': self.test_dir
            },
            'summary': {
                'total_test_suites': len(self.results),
                'total_passed': sum(r.get('passed', 0) for r in self.results.values()),
                'total_failed': sum(r.get('failed', 0) for r in self.results.values()),
                'total_errors': sum(r.get('errors', 0) for r in self.results.values()),
                'success_rate': self._calculate_success_rate()
            },
            'detailed_results': self.results,
            'recommendations': self._generate_recommendations()
        }
    
    def _calculate_success_rate(self):
        """Calcula taxa de sucesso geral"""
        total_passed = sum(r.get('passed', 0) for r in self.results.values())
        total_tests = sum(r.get('total', 0) for r in self.results.values())
        
        if total_tests == 0:
            return 0
        
        return round((total_passed / total_tests) * 100, 1)
    
    def _generate_recommendations(self):
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        # Analisar cada módulo
        for module, result in self.results.items():
            if result.get('errors', 0) > 0:
                recommendations.append(f"🔧 {module}: Corrigir erros críticos")
            elif result.get('failed', 0) > result.get('passed', 0):
                recommendations.append(f"⚠️ {module}: Muitos testes falhando")
            elif result.get('passed', 0) == 0:
                recommendations.append(f"🚨 {module}: Nenhum teste passando")
        
        # Recomendações gerais
        success_rate = self._calculate_success_rate()
        if success_rate < 50:
            recommendations.append("🚨 URGENTE: Sistema precisa de revisão completa")
        elif success_rate < 75:
            recommendations.append("⚠️ Sistema precisa de melhorias significativas")
        elif success_rate < 90:
            recommendations.append("✅ Sistema bom, pequenos ajustes recomendados")
        else:
            recommendations.append("🎉 Sistema excelente, manter qualidade")
        
        return recommendations
    
    def _create_text_report(self, report_data, file_path):
        """Cria relatório em formato texto"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO COMPLETO DE TESTES - CONCURSAI\n")
            f.write("=" * 50 + "\n\n")
            
            # Metadata
            f.write("INFORMAÇÕES GERAIS:\n")
            f.write("-" * 20 + "\n")
            metadata = report_data['metadata']
            f.write(f"Data/Hora: {metadata['timestamp']}\n")
            f.write(f"Tempo de execução: {metadata['execution_time_seconds']}s\n")
            f.write(f"Diretório do projeto: {metadata['project_directory']}\n\n")
            
            # Resumo
            f.write("RESUMO EXECUTIVO:\n")
            f.write("-" * 20 + "\n")
            summary = report_data['summary']
            f.write(f"Total de suítes de teste: {summary['total_test_suites']}\n")
            f.write(f"Testes que passaram: {summary['total_passed']}\n")
            f.write(f"Testes que falharam: {summary['total_failed']}\n")
            f.write(f"Erros encontrados: {summary['total_errors']}\n")
            f.write(f"Taxa de sucesso: {summary['success_rate']}%\n\n")
            
            # Resultados detalhados
            f.write("RESULTADOS DETALHADOS:\n")
            f.write("-" * 25 + "\n")
            for module, result in report_data['detailed_results'].items():
                f.write(f"{module.upper()}:\n")
                f.write(f"  ✅ Passou: {result.get('passed', 0)}\n")
                f.write(f"  ❌ Falhou: {result.get('failed', 0)}\n")
                f.write(f"  💥 Erros: {result.get('errors', 0)}\n")
                if 'error_message' in result:
                    f.write(f"  🚨 Mensagem: {result['error_message']}\n")
                f.write("\n")
            
            # Recomendações
            f.write("RECOMENDAÇÕES:\n")
            f.write("-" * 15 + "\n")
            for rec in report_data['recommendations']:
                f.write(f"{rec}\n")
    
    def _create_analysis_report(self, file_path):
        """Cria análise detalhada do sistema"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# ANÁLISE COMPLETA DO SISTEMA CONCURSAI\n\n")
            
            f.write("## 🎯 Objetivo da Análise\n")
            f.write("Esta análise foi gerada automaticamente para avaliar a qualidade e estabilidade do sistema ConcursAI.\n\n")
            
            f.write("## 📊 Resultados dos Testes\n\n")
            
            # Tabela de resultados
            f.write("| Módulo | Passou | Falhou | Erros | Status |\n")
            f.write("|--------|--------|--------|-------|--------|\n")
            
            for module, result in self.results.items():
                passed = result.get('passed', 0)
                failed = result.get('failed', 0)
                errors = result.get('errors', 0)
                total = passed + failed + errors
                
                if total == 0:
                    status = "❌ Não executado"
                elif errors > 0:
                    status = "🚨 Erros críticos"
                elif failed > passed:
                    status = "⚠️ Instável"
                elif passed == total:
                    status = "✅ Excelente"
                else:
                    status = "✅ Bom"
                
                f.write(f"| {module} | {passed} | {failed} | {errors} | {status} |\n")
            
            f.write("\n## 🔍 Análise por Módulo\n\n")
            
            # Análise detalhada de cada módulo
            module_descriptions = {
                'test_api': 'API e endpoints REST',
                'test_scraper': 'Coleta de dados do PCI Concursos',
                'test_frontend': 'Interface web e experiência do usuário',
                'test_integration': 'Integração entre componentes'
            }
            
            for module, description in module_descriptions.items():
                if module in self.results:
                    result = self.results[module]
                    f.write(f"### {description}\n")
                    f.write(f"**Status:** {self._get_module_status(result)}\n\n")
                    f.write(f"- Testes executados: {result.get('total', 0)}\n")
                    f.write(f"- Taxa de sucesso: {self._calculate_module_success_rate(result):.1f}%\n\n")
                    
                    if result.get('errors', 0) > 0:
                        f.write("⚠️ **Atenção:** Este módulo apresentou erros críticos.\n\n")
                    elif result.get('failed', 0) > 0:
                        f.write("ℹ️ **Info:** Alguns testes falharam, revisão recomendada.\n\n")
                    else:
                        f.write("✅ **Excelente:** Todos os testes passaram!\n\n")
            
            f.write("## 🎯 Próximos Passos\n\n")
            
            # Gerar próximos passos baseados nos resultados
            success_rate = self._calculate_success_rate()
            
            if success_rate >= 90:
                f.write("1. ✅ Sistema está funcionando excelentemente\n")
                f.write("2. 🔧 Manter monitoramento contínuo\n")
                f.write("3. 📈 Considerar melhorias de performance\n")
            elif success_rate >= 75:
                f.write("1. 🔧 Corrigir testes que falharam\n")
                f.write("2. ⚠️ Investigar causas dos problemas\n")
                f.write("3. ✅ Re-executar testes após correções\n")
            else:
                f.write("1. 🚨 **URGENTE:** Revisar arquitetura do sistema\n")
                f.write("2. 🔧 Corrigir erros críticos identificados\n")
                f.write("3. 🧪 Implementar testes unitários adicionais\n")
                f.write("4. 📋 Criar plano de correções prioritárias\n")
            
            f.write("\n## 📞 Suporte\n")
            f.write("Para dúvidas sobre este relatório, consulte a documentação do sistema.\n")
    
    def _get_module_status(self, result):
        """Retorna status de um módulo"""
        passed = result.get('passed', 0)
        failed = result.get('failed', 0)
        errors = result.get('errors', 0)
        total = passed + failed + errors
        
        if total == 0:
            return "❌ Não executado"
        elif errors > 0:
            return "🚨 Erros críticos"
        elif failed > passed:
            return "⚠️ Instável"
        elif passed == total:
            return "✅ Excelente"
        else:
            return "✅ Bom"
    
    def _calculate_module_success_rate(self, result):
        """Calcula taxa de sucesso de um módulo"""
        passed = result.get('passed', 0)
        total = result.get('total', 0)
        
        if total == 0:
            return 0
        
        return (passed / total) * 100

def main():
    """Função principal"""
    runner = TestRunner()
    results = runner.run_all_tests()
    
    # Verificar se há falhas críticas
    total_errors = sum(r.get('errors', 0) for r in results.values())
    total_failed = sum(r.get('failed', 0) for r in results.values())
    
    if total_errors > 0:
        print("🚨 ATENÇÃO: Erros críticos detectados!")
        sys.exit(2)
    elif total_failed > 0:
        print("⚠️ ATENÇÃO: Alguns testes falharam!")
        sys.exit(1)
    else:
        print("🎉 SUCESSO: Todos os testes passaram!")
        sys.exit(0)

if __name__ == "__main__":
    main()
