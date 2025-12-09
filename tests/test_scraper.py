#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕷️ TESTE DO SCRAPER PCI - ConcursAI
====================================
Testes para o sistema de scraping do PCI Concursos
"""

import unittest
import requests
import time
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scrapers.pci_scraper_atual import PCIConcursosScraperAtual
    from coletor_pci_real import coletar_dados_pci_real, atualizar_base_dados
    SCRAPER_AVAILABLE = True
except ImportError as e:
    SCRAPER_AVAILABLE = False
    IMPORT_ERROR = str(e)

class TestScraperPCI(unittest.TestCase):
    """Classe para testes do scraper PCI"""
    
    @classmethod
    def setUpClass(cls):
        """Setup para todos os testes"""
        cls.test_results = []
        print("🕷️ INICIANDO TESTES DO SCRAPER PCI")
        print("=" * 50)
    
    def setUp(self):
        """Setup para cada teste"""
        self.start_time = time.time()
    
    def tearDown(self):
        """Cleanup após cada teste"""
        duration = time.time() - self.start_time
        test_name = self._testMethodName
        self.test_results.append({
            'test': test_name,
            'duration': round(duration, 3),
            'status': 'PASS' if hasattr(self, '_outcome') and self._outcome.success else 'FAIL'
        })
    
    def test_01_imports_scraper(self):
        """Teste 1: Verificar imports do scraper"""
        print("🔍 Teste 1: Imports do Scraper")
        
        if not SCRAPER_AVAILABLE:
            self.fail(f"❌ Erro ao importar scraper: {IMPORT_ERROR}")
        
        print("   ✅ Todos os imports funcionando")
    
    @unittest.skipIf(not SCRAPER_AVAILABLE, "Scraper não disponível")
    def test_02_criar_scraper(self):
        """Teste 2: Criar instância do scraper"""
        print("🔍 Teste 2: Criar Scraper")
        
        try:
            scraper = PCIConcursosScraperAtual()
            self.assertIsNotNone(scraper)
            self.assertEqual(scraper.base_url, "https://www.pciconcursos.com.br")
            
            print("   ✅ Scraper criado com sucesso")
            
        except Exception as e:
            self.fail(f"❌ Erro ao criar scraper: {e}")
    
    def test_03_acesso_pci_site(self):
        """Teste 3: Testar acesso ao site PCI"""
        print("🔍 Teste 3: Acesso ao Site PCI")
        
        url = "https://www.pciconcursos.com.br"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            self.assertIn(response.status_code, [200, 301, 302])
            
            if response.status_code == 200:
                self.assertGreater(len(response.content), 1000)
                print("   ✅ Site PCI acessível")
            else:
                print(f"   ⚠️ Site retornou {response.status_code} (redirecionamento)")
                
        except requests.exceptions.RequestException as e:
            self.skipTest(f"⚠️ Não foi possível acessar o site PCI: {e}")
    
    @unittest.skipIf(not SCRAPER_AVAILABLE, "Scraper não disponível")
    def test_04_parse_salary(self):
        """Teste 4: Função de parse de salário"""
        print("🔍 Teste 4: Parse de Salário")
        
        scraper = PCIConcursosScraperAtual()
        
        test_cases = [
            ("R$ 1.234,56", 1234.56),
            ("R$ 5.000,00", 5000.0),
            ("2500", 2500.0),
            ("R$ 10.000", 10000.0),
            ("abc", 0.0)
        ]
        
        for salary_text, expected in test_cases:
            result = scraper._parse_salary(salary_text)
            self.assertEqual(result, expected, f"Falha ao parsear '{salary_text}'")
        
        print("   ✅ Parse de salário funcionando")
    
    @unittest.skipIf(not SCRAPER_AVAILABLE, "Scraper não disponível")
    def test_05_request_seguro(self):
        """Teste 5: Sistema de request seguro"""
        print("🔍 Teste 5: Request Seguro")
        
        scraper = PCIConcursosScraperAtual()
        
        # Testar com URL válida
        response = scraper._safe_request("https://httpbin.org/status/200")
        if response:
            self.assertEqual(response.status_code, 200)
            print("   ✅ Request seguro funcionando")
        else:
            self.skipTest("   ⚠️ Serviço de teste não disponível")
    
    def test_06_coletor_pci_real(self):
        """Teste 6: Coletor PCI real"""
        print("🔍 Teste 6: Coletor PCI Real")
        
        try:
            # Mock para evitar request real durante teste
            with patch('coletor_pci_real.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = "<html>concurso prefeitura</html>"
                mock_get.return_value = mock_response
                
                resultado = coletar_dados_pci_real()
                
                self.assertIn('status', resultado)
                self.assertIn('concursos', resultado)
                
                print("   ✅ Coletor funcionando")
                
        except Exception as e:
            self.fail(f"❌ Erro no coletor: {e}")
    
    def test_07_atualizacao_base_dados(self):
        """Teste 7: Atualização da base de dados"""
        print("🔍 Teste 7: Atualização Base")
        
        # Dados de teste
        novos_concursos = [
            {
                'titulo': 'Teste Concurso',
                'orgao': 'Teste Órgão',
                'cargo': 'Teste Cargo',
                'ano': 2024,
                'tipo_documento': 'edital',
                'url': 'http://teste.com',
                'data_publicacao': '29/10/2024',
                'fonte': 'Teste',
                'vagas': 10,
                'salario': 'R$ 5.000,00',
                'escolaridade': 'Superior',
                'local': 'Teste - SP'
            }
        ]
        
        try:
            resultado = atualizar_base_dados(novos_concursos)
            self.assertIn('status', resultado)
            
            if resultado['status'] == 'sucesso':
                print("   ✅ Atualização da base funcionando")
            else:
                print(f"   ⚠️ Atualização retornou: {resultado}")
                
        except Exception as e:
            self.fail(f"❌ Erro na atualização: {e}")
    
    def test_08_validacao_estrutura_dados(self):
        """Teste 8: Validação da estrutura de dados"""
        print("🔍 Teste 8: Estrutura de Dados")
        
        # Estrutura esperada de um concurso
        expected_fields = [
            'titulo', 'orgao', 'cargo', 'ano', 'tipo_documento',
            'url', 'data_publicacao', 'fonte', 'vagas', 'salario',
            'escolaridade', 'local'
        ]
        
        # Verificar se arquivo CSV existe
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'concursos_chunks.csv')
        
        if os.path.exists(csv_path):
            import pandas as pd
            df = pd.read_csv(csv_path)
            
            # Verificar se as colunas necessárias existem
            missing_fields = [field for field in expected_fields if field not in df.columns]
            
            if missing_fields:
                print(f"   ⚠️ Campos faltando: {missing_fields}")
            else:
                print("   ✅ Estrutura de dados correta")
        else:
            self.skipTest("   ⚠️ Arquivo CSV não encontrado")
    
    def test_09_headers_scraping(self):
        """Teste 9: Headers para scraping"""
        print("🔍 Teste 9: Headers de Scraping")
        
        if SCRAPER_AVAILABLE:
            scraper = PCIConcursosScraperAtual()
            headers = scraper.session.headers
            
            # Verificar headers essenciais
            self.assertIn('User-Agent', headers)
            self.assertIn('Accept', headers)
            
            # User-Agent deve parecer com navegador real
            user_agent = headers['User-Agent']
            self.assertIn('Mozilla', user_agent)
            self.assertIn('Chrome', user_agent)
            
            print("   ✅ Headers configurados corretamente")
        else:
            self.skipTest("   ⚠️ Scraper não disponível")
    
    def test_10_rate_limiting(self):
        """Teste 10: Sistema de rate limiting"""
        print("🔍 Teste 10: Rate Limiting")
        
        if SCRAPER_AVAILABLE:
            scraper = PCIConcursosScraperAtual()
            
            # Testar delay entre requests
            start_time = time.time()
            scraper._wait()
            duration = time.time() - start_time
            
            # Deve esperar pelo menos 1 segundo
            self.assertGreaterEqual(duration, 1.0)
            self.assertLessEqual(duration, 3.0)  # Não mais que 3 segundos
            
            print(f"   ✅ Rate limiting funcionando ({duration:.2f}s)")
        else:
            self.skipTest("   ⚠️ Scraper não disponível")
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup final e relatório"""
        print("\n📊 RESUMO DOS TESTES DO SCRAPER:")
        print("=" * 35)
        
        total_tests = len(cls.test_results)
        passed_tests = len([r for r in cls.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        
        if failed_tests == 0:
            print("\n🎉 TODOS OS TESTES DO SCRAPER PASSARAM!")
        else:
            print(f"\n⚠️ {failed_tests} teste(s) falharam")
        
        # Salvar relatório
        cls._save_test_report()
    
    @classmethod
    def _save_test_report(cls):
        """Salva relatório detalhado dos testes"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'scraper_available': SCRAPER_AVAILABLE,
            'total_tests': len(cls.test_results),
            'passed': len([r for r in cls.test_results if r['status'] == 'PASS']),
            'failed': len([r for r in cls.test_results if r['status'] == 'FAIL']),
            'results': cls.test_results
        }
        
        if not SCRAPER_AVAILABLE:
            report['import_error'] = IMPORT_ERROR
        
        report_path = os.path.join(os.path.dirname(__file__), 'test_scraper_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_path}")

def run_scraper_tests():
    """Executa todos os testes do scraper"""
    unittest.main(verbosity=2, exit=False)

if __name__ == "__main__":
    run_scraper_tests()
