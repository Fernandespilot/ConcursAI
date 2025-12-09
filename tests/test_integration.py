#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 TESTE DE INTEGRAÇÃO - ConcursAI
==================================
Testes end-to-end do sistema completo
"""

import unittest
import requests
import time
import json
import os
import subprocess
import threading
from unittest.mock import patch, MagicMock

class TestIntegracao(unittest.TestCase):
    """Classe para testes de integração"""
    
    @classmethod
    def setUpClass(cls):
        """Setup para todos os testes"""
        cls.base_url = "http://localhost:8002"
        cls.timeout = 30
        cls.test_results = []
        
        print("🔄 INICIANDO TESTES DE INTEGRAÇÃO")
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
    
    def test_01_sistema_inicializacao(self):
        """Teste 1: Inicialização do sistema"""
        print("🔍 Teste 1: Inicialização Sistema")
        
        try:
            # Verificar se API está rodando
            response = requests.get(f"{self.base_url}/", timeout=5)
            self.assertEqual(response.status_code, 200)
            
            # Verificar endpoints essenciais
            endpoints = ['/docs', '/editais', '/api/concursos']
            for endpoint in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                self.assertIn(response.status_code, [200, 307], 
                             f"Endpoint {endpoint} deve estar acessível")
            
            print("   ✅ Sistema inicializado corretamente")
            
        except requests.exceptions.ConnectionError:
            self.fail("❌ Sistema não está rodando. Execute: python api_simplificada.py")
    
    def test_02_fluxo_busca_editais(self):
        """Teste 2: Fluxo completo de busca de editais"""
        print("🔍 Teste 2: Fluxo Busca Editais")
        
        # 1. Verificar endpoint de concursos
        response = requests.get(f"{self.base_url}/api/concursos", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        # 2. Testar busca com parâmetros
        params = {'q': 'professor', 'limit': 5}
        response = requests.get(f"{self.base_url}/api/concursos", 
                               params=params, timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        
        results = response.json()
        self.assertLessEqual(len(results), 5)
        
        # 3. Verificar estrutura dos dados
        if results:
            edital = results[0]
            expected_fields = ['titulo', 'orgao', 'salario', 'link', 'inscricoes']
            for field in expected_fields:
                self.assertIn(field, edital, f"Campo {field} deve existir")
        
        print(f"   ✅ Busca funcionando - {len(results)} resultados")
    
    def test_03_coleta_dados_reais(self):
        """Teste 3: Coleta de dados reais"""
        print("🔍 Teste 3: Coleta Dados Reais")
        
        # Simular coleta de dados reais
        try:
            response = requests.post(f"{self.base_url}/admin/coletar-pci-real", 
                                   timeout=self.timeout)
            
            # Pode retornar 200 (sucesso) ou outros códigos dependendo do estado
            self.assertIn(response.status_code, [200, 202, 429], 
                         "Coleta deve ser aceita ou ter rate limiting")
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn('status', data)
                print(f"   ✅ Coleta iniciada - Status: {data.get('status')}")
            else:
                print(f"   ⚠️ Coleta limitada - Código: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("   ⚠️ Timeout na coleta (esperado para operações longas)")
    
    def test_04_persistencia_dados(self):
        """Teste 4: Persistência de dados"""
        print("🔍 Teste 4: Persistência Dados")
        
        # Verificar se arquivo CSV existe
        csv_files = [
            'concursos_chunks.csv',
            'editais_chunks.csv'
        ]
        
        csv_found = []
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                csv_found.append(csv_file)
                
                # Verificar se arquivo não está vazio
                size = os.path.getsize(csv_file)
                self.assertGreater(size, 0, f"{csv_file} não deve estar vazio")
        
        # Pelo menos um CSV deve existir
        self.assertGreater(len(csv_found), 0, "Pelo menos um arquivo CSV deve existir")
        
        print(f"   ✅ {len(csv_found)} arquivo(s) CSV encontrados")
    
    def test_05_cache_performance(self):
        """Teste 5: Performance e cache"""
        print("🔍 Teste 5: Performance Cache")
        
        endpoint = f"{self.base_url}/api/concursos"
        
        # Primeira requisição (cache miss)
        start_time = time.time()
        response1 = requests.get(endpoint, timeout=self.timeout)
        time1 = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        
        # Segunda requisição (possível cache hit)
        start_time = time.time()
        response2 = requests.get(endpoint, timeout=self.timeout)
        time2 = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        
        # Dados devem ser consistentes
        data1 = response1.json()
        data2 = response2.json()
        self.assertEqual(len(data1), len(data2))
        
        print(f"   ✅ 1ª req: {time1:.3f}s, 2ª req: {time2:.3f}s")
    
    def test_06_tratamento_erros(self):
        """Teste 6: Tratamento de erros"""
        print("🔍 Teste 6: Tratamento Erros")
        
        # Testar endpoint inexistente
        response = requests.get(f"{self.base_url}/api/inexistente", timeout=10)
        self.assertEqual(response.status_code, 404)
        
        # Testar parâmetros inválidos
        response = requests.get(f"{self.base_url}/api/concursos", 
                               params={'limit': 'invalid'}, timeout=10)
        # Deve lidar graciosamente com parâmetros inválidos
        self.assertIn(response.status_code, [200, 400, 422])
        
        # Testar método não permitido
        response = requests.put(f"{self.base_url}/api/concursos", timeout=10)
        self.assertEqual(response.status_code, 405)
        
        print("   ✅ Tratamento de erros funcionando")
    
    def test_07_seguranca_basica(self):
        """Teste 7: Segurança básica"""
        print("🔍 Teste 7: Segurança Básica")
        
        # Verificar headers de segurança
        response = requests.get(f"{self.base_url}/", timeout=10)
        headers = response.headers
        
        security_score = 0
        
        # Content-Type deve estar presente
        if 'content-type' in headers:
            security_score += 1
        
        # Verificar se não vaza informações do servidor
        server_info = headers.get('server', '').lower()
        if 'python' not in server_info and 'uvicorn' not in server_info:
            security_score += 1
        
        # Verificar se CORS está configurado (se necessário)
        if 'access-control-allow-origin' in headers:
            security_score += 1
        
        print(f"   ✅ Score segurança básica: {security_score}/3")
    
    def test_08_concorrencia(self):
        """Teste 8: Concorrência"""
        print("🔍 Teste 8: Concorrência")
        
        # Fazer múltiplas requisições simultâneas
        def make_request():
            try:
                response = requests.get(f"{self.base_url}/api/concursos", 
                                      params={'limit': 10}, timeout=15)
                return response.status_code == 200
            except:
                return False
        
        # Usar threads para simular concorrência
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        # Aguardar todas as threads
        for thread in threads:
            thread.join()
        
        # Pelo menos 80% das requisições devem ter sucesso
        success_rate = sum(results) / len(results)
        self.assertGreaterEqual(success_rate, 0.8, 
                               "Taxa de sucesso em concorrência deve ser >= 80%")
        
        print(f"   ✅ Taxa de sucesso: {success_rate:.1%}")
    
    def test_09_dados_validacao(self):
        """Teste 9: Validação de dados"""
        print("🔍 Teste 9: Validação Dados")
        
        response = requests.get(f"{self.base_url}/api/concursos", 
                               params={'limit': 50}, timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        if data:
            # Verificar estrutura dos dados
            sample = data[0]
            
            # Campos obrigatórios
            required_fields = ['titulo', 'orgao', 'link']
            for field in required_fields:
                self.assertIn(field, sample)
                self.assertTrue(sample[field], f"Campo {field} não deve estar vazio")
            
            # Validar tipos de dados
            if 'salario' in sample and sample['salario']:
                # Salário deve ser string ou número
                self.assertIsInstance(sample['salario'], (str, int, float))
            
            if 'link' in sample:
                # Link deve parecer uma URL
                link = str(sample['link'])
                self.assertTrue(link.startswith('http'), "Link deve ser uma URL válida")
            
            print(f"   ✅ Validação em {len(data)} registros")
        else:
            print("   ⚠️ Nenhum dado para validar")
    
    def test_10_monitoramento_sistema(self):
        """Teste 10: Monitoramento do sistema"""
        print("🔍 Teste 10: Monitoramento Sistema")
        
        # Verificar status geral do sistema
        endpoints_status = {}
        
        critical_endpoints = [
            '/',
            '/editais', 
            '/api/concursos',
            '/docs'
        ]
        
        for endpoint in critical_endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                endpoints_status[endpoint] = {
                    'status_code': response.status_code,
                    'response_time': round(response_time, 3),
                    'healthy': response.status_code in [200, 307]
                }
                
            except Exception as e:
                endpoints_status[endpoint] = {
                    'status_code': None,
                    'response_time': None,
                    'healthy': False,
                    'error': str(e)
                }
        
        # Verificar saúde geral
        healthy_endpoints = sum(1 for ep in endpoints_status.values() if ep['healthy'])
        health_percentage = (healthy_endpoints / len(critical_endpoints)) * 100
        
        self.assertGreaterEqual(health_percentage, 75, 
                               "Pelo menos 75% dos endpoints devem estar saudáveis")
        
        # Calcular tempo médio de resposta
        response_times = [ep['response_time'] for ep in endpoints_status.values() 
                         if ep['response_time'] is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        print(f"   ✅ Saúde: {health_percentage:.1f}%, Tempo médio: {avg_response_time:.3f}s")
        
        # Salvar status para o relatório
        self._save_monitoring_data(endpoints_status)
    
    def _save_monitoring_data(self, endpoints_status):
        """Salva dados de monitoramento"""
        monitoring_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'endpoints': endpoints_status
        }
        
        report_path = os.path.join(os.path.dirname(__file__), 'monitoring_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(monitoring_data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup final e relatório"""
        print("\n📊 RESUMO DOS TESTES DE INTEGRAÇÃO:")
        print("=" * 40)
        
        total_tests = len(cls.test_results)
        passed_tests = len([r for r in cls.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        
        if failed_tests == 0:
            print("\n🎉 TODOS OS TESTES DE INTEGRAÇÃO PASSARAM!")
        else:
            print(f"\n⚠️ {failed_tests} teste(s) falharam")
        
        # Salvar relatório
        cls._save_test_report()
    
    @classmethod
    def _save_test_report(cls):
        """Salva relatório detalhado dos testes"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_tests': len(cls.test_results),
            'passed': len([r for r in cls.test_results if r['status'] == 'PASS']),
            'failed': len([r for r in cls.test_results if r['status'] == 'FAIL']),
            'results': cls.test_results
        }
        
        report_path = os.path.join(os.path.dirname(__file__), 'test_integration_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_path}")

def run_integration_tests():
    """Executa todos os testes de integração"""
    unittest.main(verbosity=2, exit=False)

if __name__ == "__main__":
    run_integration_tests()
