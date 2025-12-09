#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 TESTE DE FRONTEND - ConcursAI
================================
Testes para interface web e funcionalidades frontend
"""

import unittest
import requests
import time
import json
import re
from bs4 import BeautifulSoup
import os

class TestFrontend(unittest.TestCase):
    """Classe para testes do frontend"""
    
    @classmethod
    def setUpClass(cls):
        """Setup para todos os testes"""
        cls.base_url = "http://localhost:8002"
        cls.timeout = 10
        cls.test_results = []
        
        print("🌐 INICIANDO TESTES DO FRONTEND")
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
    
    def test_01_landing_page_elements(self):
        """Teste 1: Elementos da landing page"""
        print("🔍 Teste 1: Elementos Landing Page")
        
        response = requests.get(f"{self.base_url}/", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Verificar elementos essenciais
        title = soup.find('title')
        self.assertIsNotNone(title)
        self.assertIn('ConcursAI', title.text)
        
        # Verificar se tem CSS
        css_links = soup.find_all('style')
        self.assertGreater(len(css_links), 0, "Landing page deve ter CSS")
        
        # Verificar se tem JavaScript
        scripts = soup.find_all('script')
        self.assertGreater(len(scripts), 0, "Landing page deve ter JavaScript")
        
        print("   ✅ Elementos principais presentes")
    
    def test_02_interface_editais_structure(self):
        """Teste 2: Estrutura da interface de editais"""
        print("🔍 Teste 2: Estrutura Interface Editais")
        
        response = requests.get(f"{self.base_url}/editais", timeout=self.timeout)
        self.assertEqual(response.status_code, 200)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Verificar elementos críticos
        search_input = soup.find('input', {'id': 'searchInput'})
        self.assertIsNotNone(search_input, "Campo de busca deve existir")
        
        search_button = soup.find('button', {'onclick': re.compile(r'buscarEditais')})
        self.assertIsNotNone(search_button, "Botão de busca deve existir")
        
        # Verificar botões administrativos
        btn_coletar = soup.find('button', {'onclick': re.compile(r'coletarDadosReais')})
        self.assertIsNotNone(btn_coletar, "Botão de coleta deve existir")
        
        btn_atualizar = soup.find('button', {'onclick': re.compile(r'atualizarDadosReais')})
        self.assertIsNotNone(btn_atualizar, "Botão de atualização deve existir")
        
        print("   ✅ Estrutura da interface correta")
    
    def test_03_responsive_design(self):
        """Teste 3: Design responsivo"""
        print("🔍 Teste 3: Design Responsivo")
        
        response = requests.get(f"{self.base_url}/editais", timeout=self.timeout)
        content = response.text
        
        # Verificar meta viewport
        self.assertIn('viewport', content)
        self.assertIn('width=device-width', content)
        
        # Verificar media queries
        media_query_patterns = [
            r'@media.*max-width.*768px',
            r'@media.*max-width.*1024px',
            r'@media.*min-width'
        ]
        
        media_queries_found = 0
        for pattern in media_query_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                media_queries_found += 1
        
        self.assertGreater(media_queries_found, 0, "Deve ter media queries para responsividade")
        
        print(f"   ✅ {media_queries_found} media queries encontradas")
    
    def test_04_javascript_functions(self):
        """Teste 4: Funções JavaScript essenciais"""
        print("🔍 Teste 4: Funções JavaScript")
        
        response = requests.get(f"{self.base_url}/editais", timeout=self.timeout)
        content = response.text
        
        # Funções JavaScript essenciais
        required_functions = [
            'buscarEditais',
            'coletarDadosReais',
            'atualizarDadosReais',
            'verificarStatusDados',
            'carregarEditais',
            'aplicarFiltros'
        ]
        
        functions_found = []
        for func in required_functions:
            if f'function {func}' in content or f'{func} =' in content:
                functions_found.append(func)
        
        missing_functions = set(required_functions) - set(functions_found)
        
        if missing_functions:
            print(f"   ⚠️ Funções faltando: {missing_functions}")
        
        self.assertGreaterEqual(len(functions_found), len(required_functions) * 0.8, 
                               "Pelo menos 80% das funções devem estar presentes")
        
        print(f"   ✅ {len(functions_found)}/{len(required_functions)} funções encontradas")
    
    def test_05_css_styling(self):
        """Teste 5: Estilos CSS"""
        print("🔍 Teste 5: Estilos CSS")
        
        response = requests.get(f"{self.base_url}/editais", timeout=self.timeout)
        content = response.text
        
        # Verificar se tem estilos importantes
        css_elements = [
            '.header',
            '.main',
            '.search-section',
            '.results-section',
            '.edital-card',
            '.nav-btn'
        ]
        
        styles_found = []
        for element in css_elements:
            if element in content:
                styles_found.append(element)
        
        self.assertGreater(len(styles_found), len(css_elements) * 0.7, 
                          "Pelo menos 70% dos estilos devem estar presentes")
        
        # Verificar se usa CSS moderno
        modern_css_features = [
            'flexbox' if 'display: flex' in content else None,
            'grid' if 'display: grid' in content else None,
            'transitions' if 'transition:' in content else None,
            'border-radius' if 'border-radius:' in content else None
        ]
        
        modern_features = [f for f in modern_css_features if f]
        
        print(f"   ✅ {len(styles_found)} estilos, {len(modern_features)} recursos modernos")
    
    def test_06_accessibility(self):
        """Teste 6: Acessibilidade"""
        print("🔍 Teste 6: Acessibilidade")
        
        response = requests.get(f"{self.base_url}/editais", timeout=self.timeout)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        accessibility_score = 0
        total_checks = 0
        
        # Verificar alt em imagens
        total_checks += 1
        images = soup.find_all('img')
        images_with_alt = [img for img in images if img.get('alt')]
        if not images or len(images_with_alt) == len(images):
            accessibility_score += 1
        
        # Verificar labels em inputs
        total_checks += 1
        inputs = soup.find_all('input')
        inputs_with_labels = 0
        for inp in inputs:
            inp_id = inp.get('id')
            if inp_id and soup.find('label', {'for': inp_id}):
                inputs_with_labels += 1
            elif inp.get('placeholder'):  # Placeholder como fallback
                inputs_with_labels += 1
        
        if not inputs or inputs_with_labels >= len(inputs) * 0.8:
            accessibility_score += 1
        
        # Verificar botões com texto descritivo
        total_checks += 1
        buttons = soup.find_all('button')
        buttons_with_text = [btn for btn in buttons if btn.get_text(strip=True)]
        if len(buttons_with_text) >= len(buttons) * 0.9:
            accessibility_score += 1
        
        # Verificar hierarquia de headings
        total_checks += 1
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if headings:
            accessibility_score += 1
        
        accessibility_percentage = (accessibility_score / total_checks) * 100
        
        self.assertGreaterEqual(accessibility_percentage, 70, 
                               "Acessibilidade deve ser pelo menos 70%")
        
        print(f"   ✅ Acessibilidade: {accessibility_percentage:.1f}%")
    
    def test_07_performance_assets(self):
        """Teste 7: Performance dos assets"""
        print("🔍 Teste 7: Performance Assets")
        
        # Testar carregamento de páginas principais
        pages = [
            ('/', 'Landing Page'),
            ('/editais', 'Interface Editais'),
            ('/docs', 'Documentação')
        ]
        
        performance_results = []
        
        for url, name in pages:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{url}", timeout=self.timeout)
            load_time = time.time() - start_time
            
            performance_results.append({
                'page': name,
                'url': url,
                'status': response.status_code,
                'load_time': round(load_time, 3),
                'size_kb': round(len(response.content) / 1024, 2)
            })
            
            # Páginas devem carregar em menos de 3 segundos
            self.assertLess(load_time, 3.0, f"{name} muito lenta: {load_time:.3f}s")
        
        avg_load_time = sum(r['load_time'] for r in performance_results) / len(performance_results)
        total_size = sum(r['size_kb'] for r in performance_results)
        
        print(f"   ✅ Tempo médio: {avg_load_time:.3f}s, Tamanho total: {total_size:.1f}KB")
    
    def test_08_error_handling(self):
        """Teste 8: Tratamento de erros"""
        print("🔍 Teste 8: Tratamento de Erros")
        
        response = requests.get(f"{self.base_url}/editais", timeout=self.timeout)
        content = response.text
        
        # Verificar se tem tratamento de erro em JavaScript
        error_handling_patterns = [
            r'try\s*{',
            r'catch\s*\(',
            r'\.catch\(',
            r'error',
            r'exception'
        ]
        
        error_handling_found = 0
        for pattern in error_handling_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                error_handling_found += 1
        
        self.assertGreater(error_handling_found, 2, 
                          "Deve ter tratamento básico de erros")
        
        print(f"   ✅ {error_handling_found} padrões de tratamento de erro encontrados")
    
    def test_09_interactive_elements(self):
        """Teste 9: Elementos interativos"""
        print("🔍 Teste 9: Elementos Interativos")
        
        response = requests.get(f"{self.base_url}/editais", timeout=self.timeout)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Contar elementos interativos
        interactive_elements = {
            'buttons': len(soup.find_all('button')),
            'inputs': len(soup.find_all('input')),
            'selects': len(soup.find_all('select')),
            'links': len(soup.find_all('a')),
            'forms': len(soup.find_all('form'))
        }
        
        total_interactive = sum(interactive_elements.values())
        
        self.assertGreater(total_interactive, 5, 
                          "Deve ter elementos interativos suficientes")
        
        # Verificar se botões têm eventos
        buttons_with_events = soup.find_all('button', {'onclick': True})
        self.assertGreater(len(buttons_with_events), 0, 
                          "Botões devem ter eventos associados")
        
        print(f"   ✅ {total_interactive} elementos interativos encontrados")
    
    def test_10_browser_compatibility(self):
        """Teste 10: Compatibilidade com navegadores"""
        print("🔍 Teste 10: Compatibilidade")
        
        response = requests.get(f"{self.base_url}/editais", timeout=self.timeout)
        content = response.text
        
        # Verificar se usa recursos compatíveis
        compatibility_issues = []
        
        # Verificar se não usa recursos muito modernos sem fallback
        if 'const ' in content and 'var ' not in content:
            compatibility_issues.append("Só usa const/let sem var fallback")
        
        if '=> ' in content:  # Arrow functions
            if 'function(' not in content:
                compatibility_issues.append("Só usa arrow functions")
        
        # Features que melhoram compatibilidade
        good_practices = []
        
        if 'addEventListener' in content:
            good_practices.append("Usa addEventListener")
        
        if 'querySelector' in content:
            good_practices.append("Usa querySelector")
        
        compatibility_score = len(good_practices) - len(compatibility_issues)
        
        self.assertGreaterEqual(compatibility_score, 0, 
                               "Compatibilidade deve ser neutra ou positiva")
        
        print(f"   ✅ Score compatibilidade: {compatibility_score}")
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup final e relatório"""
        print("\n📊 RESUMO DOS TESTES DO FRONTEND:")
        print("=" * 35)
        
        total_tests = len(cls.test_results)
        passed_tests = len([r for r in cls.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        
        if failed_tests == 0:
            print("\n🎉 TODOS OS TESTES DO FRONTEND PASSARAM!")
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
        
        report_path = os.path.join(os.path.dirname(__file__), 'test_frontend_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_path}")

def run_frontend_tests():
    """Executa todos os testes do frontend"""
    unittest.main(verbosity=2, exit=False)

if __name__ == "__main__":
    run_frontend_tests()
