#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTE DE API - ConcursAI
===========================
Testes completos para a API FastAPI
"""

import unittest
import requests
import json
import time
from typing import Dict, Any
import pandas as pd
import os
import sys

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestConcursAIAPI(unittest.TestCase):
    """Classe para testes da API ConcursAI"""
    
    @classmethod
    def setUpClass(cls):
        """Setup para todos os testes"""
        cls.base_url = "http://localhost:8002"
        cls.timeout = 10
        cls.test_results = []
        
        print("🧪 INICIANDO TESTES DA API ConcursAI")
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
    
    def test_01_servidor_online(self):
        """Teste 1: Verificar se o servidor está online"""
        print("🔍 Teste 1: Servidor Online")
        
        try:
            response = requests.get(f"{self.base_url}/status", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('status', data)
            self.assertEqual(data['status'], 'online')
            
            print("   ✅ Servidor online e respondendo")
            
        except requests.exceptions.ConnectionError:
            self.fail("❌ Servidor não está rodando na porta 8002")
        except Exception as e:
            self.fail(f"❌ Erro inesperado: {e}")
    
    def test_02_landing_page(self):
        """Teste 2: Landing page carrega corretamente"""
        print("🔍 Teste 2: Landing Page")
        
        response = requests.get(f"{self.base_url}/", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers.get('content-type', ''))
        
        print("   ✅ Landing page carregada")
    
    def test_03_interface_editais(self):
        """Teste 3: Interface de editais carrega"""
        print("🔍 Teste 3: Interface de Editais")
        
        response = requests.get(f"{self.base_url}/editais", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers.get('content-type', ''))
        
        # Verificar se contém elementos esperados
        content = response.text
        self.assertIn('ConcursAI', content)
        self.assertIn('Visualizar Editais', content)
        
        print("   ✅ Interface de editais carregada")
    
    def test_04_documentacao_api(self):
        """Teste 4: Documentação da API disponível"""
        print("🔍 Teste 4: Documentação API")
        
        response = requests.get(f"{self.base_url}/docs", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        
        print("   ✅ Documentação da API disponível")
    
    def test_05_listar_concursos(self):
        """Teste 5: Endpoint de listar concursos"""
        print("🔍 Teste 5: Listar Concursos")
        
        response = requests.get(f"{self.base_url}/concursos", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('concursos', data)
        self.assertIsInstance(data['concursos'], list)
        
        if data['concursos']:
            concurso = data['concursos'][0]
            expected_fields = ['titulo', 'orgao', 'cargo']
            for field in expected_fields:
                self.assertIn(field, concurso)
        
        print(f"   ✅ {len(data['concursos'])} concursos listados")
    
    def test_06_busca_concursos(self):
        """Teste 6: Busca de concursos"""
        print("🔍 Teste 6: Busca de Concursos")
        
        payload = {
            "pergunta": "prefeitura"
        }
        
        response = requests.post(
            f"{self.base_url}/buscar", 
            json=payload, 
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('documentos_relevantes', data)
        
        print(f"   ✅ Busca realizada, {len(data['documentos_relevantes'])} resultados")
    
    def test_07_filtros_concursos(self):
        """Teste 7: Filtros de concursos"""
        print("🔍 Teste 7: Filtros de Concursos")
        
        # Teste com filtro por órgão
        response = requests.get(
            f"{self.base_url}/concursos?orgao=Prefeitura&limit=5", 
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('concursos', data)
        
        print("   ✅ Filtros funcionando")
    
    def test_08_status_dados(self):
        """Teste 8: Status dos dados"""
        print("🔍 Teste 8: Status dos Dados")
        
        response = requests.get(f"{self.base_url}/admin/status-dados", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('api', data)
        
        print("   ✅ Status dos dados disponível")
    
    def test_09_validacao_dados_csv(self):
        """Teste 9: Validação dos dados CSV"""
        print("🔍 Teste 9: Validação Dados CSV")
        
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'concursos_chunks.csv')
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            
            # Verificar se tem dados
            self.assertGreater(len(df), 0, "CSV não pode estar vazio")
            
            # Verificar colunas obrigatórias
            required_columns = ['titulo', 'orgao', 'cargo']
            for col in required_columns:
                self.assertIn(col, df.columns, f"Coluna '{col}' obrigatória")
            
            # Verificar se não há muitos valores nulos
            null_percentage = df.isnull().sum().sum() / (len(df) * len(df.columns))
            self.assertLess(null_percentage, 0.5, "Muitos valores nulos nos dados")
            
            print(f"   ✅ CSV válido com {len(df)} registros")
        else:
            self.fail("❌ Arquivo CSV não encontrado")
    
    def test_10_performance_endpoints(self):
        """Teste 10: Performance dos endpoints"""
        print("🔍 Teste 10: Performance")
        
        endpoints = [
            '/status',
            '/concursos?limit=10',
            '/editais'
        ]
        
        performance_results = []
        
        for endpoint in endpoints:
            start = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
            duration = time.time() - start
            
            performance_results.append({
                'endpoint': endpoint,
                'status': response.status_code,
                'duration': round(duration, 3)
            })
            
            # Endpoint deve responder em menos de 5 segundos
            self.assertLess(duration, 5.0, f"Endpoint {endpoint} muito lento: {duration}s")
        
        avg_time = sum(r['duration'] for r in performance_results) / len(performance_results)
        print(f"   ✅ Performance OK (média: {avg_time:.3f}s)")
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup final e relatório"""
        print("\n📊 RESUMO DOS TESTES:")
        print("=" * 30)
        
        total_tests = len(cls.test_results)
        passed_tests = len([r for r in cls.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        
        if failed_tests == 0:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
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
        
        report_path = os.path.join(os.path.dirname(__file__), 'test_api_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_path}")

def run_api_tests():
    """Executa todos os testes da API"""
    unittest.main(verbosity=2, exit=False)

if __name__ == "__main__":
    run_api_tests()
