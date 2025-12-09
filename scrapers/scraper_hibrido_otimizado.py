"""
🎯 SCRAPER HÍBRIDO OTIMIZADO - Requests + Selenium Fallback
========================================================
Implementação inteligente que usa a melhor estratégia para cada site
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict, Optional
import random

# Selenium imports (com fallback)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    SELENIUM_DISPONIVEL = True
    print("✅ Selenium disponível")
except ImportError:
    SELENIUM_DISPONIVEL = False
    print("⚠️ Selenium não disponível - usando apenas Requests")

class ScraperHibridoOtimizado:
    def __init__(self):
        """Scraper híbrido com estratégia adaptativa"""
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Configurações
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache'
        }
        
        # Configurações de sites
        self.sites_config = {
            'pci_concurso': {
                'urls_teste': [
                    'https://www.pciconcursos.com.br/concursos',
                    'https://www.pciconcursos.com.br/concursos/',
                    'https://www.pciconcursos.com.br',
                    'https://pciconcursos.com.br/concursos'
                ],
                'seletores_requests': [
                    'div.card',
                    'div.item',
                    'div.concurso',
                    'tr.concurso',
                    'a[href*="concurso"]'
                ],
                'seletores_selenium': [
                    'div[class*="card"]',
                    'div[class*="item"]',
                    'div[class*="concurso"]',
                    'tr[class*="concurso"]'
                ],
                'estrategia': None  # Será determinada dinamicamente
            },
            'concursos_brasil': {
                'urls_teste': [
                    'https://www.concursosbrasil.com.br/concursos',
                    'https://www.concursosbrasil.com.br/concursos/',
                    'https://concursosbrasil.com.br/concursos',
                    'https://www.concursosbrasil.com.br'
                ],
                'seletores_requests': [
                    'div.card',
                    'div.item',
                    'div.concurso',
                    'tr.concurso',
                    'a[href*="concurso"]'
                ],
                'seletores_selenium': [
                    'div[class*="card"]',
                    'div[class*="item"]', 
                    'div[class*="concurso"]',
                    'tr[class*="concurso"]'
                ],
                'estrategia': None
            }
        }
        
        # Driver Selenium (lazy loading)
        self.driver = None
        
        # Cache de estratégias
        self.cache_estrategias = {}
    
    def detectar_melhor_estrategia(self, site_name: str) -> str:
        """Detecta automaticamente a melhor estratégia para cada site"""
        
        if site_name in self.cache_estrategias:
            return self.cache_estrategias[site_name]
        
        config = self.sites_config[site_name]
        self.logger.info(f"🔍 Detectando estratégia para {site_name}")
        
        # Testar Requests primeiro (mais rápido)
        estrategia = self._testar_requests(config)
        
        if estrategia == "requests":
            self.logger.info(f"✅ {site_name}: Requests funcionou!")
        else:
            # Tentar Selenium se disponível
            if SELENIUM_DISPONIVEL:
                estrategia = self._testar_selenium(config)
                if estrategia == "selenium":
                    self.logger.info(f"🤖 {site_name}: Selenium necessário")
                else:
                    self.logger.warning(f"❌ {site_name}: Ambas estratégias falharam")
                    estrategia = "requests"  # Fallback
            else:
                self.logger.warning(f"⚠️ {site_name}: Selenium não disponível, usando Requests")
                estrategia = "requests"
        
        # Cachear resultado
        self.cache_estrategias[site_name] = estrategia
        config['estrategia'] = estrategia
        
        return estrategia
    
    def _testar_requests(self, config: Dict) -> str:
        """Testa se Requests + BeautifulSoup funciona"""
        
        for url in config['urls_teste']:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Testar seletores
                    for seletor in config['seletores_requests']:
                        elementos = soup.select(seletor)
                        if len(elementos) > 2:  # Pelo menos 3 elementos encontrados
                            config['url_funcional'] = url
                            config['seletor_funcional'] = seletor
                            return "requests"
                            
            except Exception as e:
                self.logger.debug(f"Requests falhou para {url}: {e}")
                continue
        
        return "falhou"
    
    def _testar_selenium(self, config: Dict) -> str:
        """Testa se Selenium funciona"""
        
        if not SELENIUM_DISPONIVEL:
            return "falhou"
        
        driver = self._get_selenium_driver()
        if not driver:
            return "falhou"
        
        for url in config['urls_teste']:
            try:
                driver.get(url)
                time.sleep(3)  # Aguardar carregamento
                
                # Testar seletores
                for seletor in config['seletores_selenium']:
                    elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                    if len(elementos) > 2:
                        config['url_funcional'] = url
                        config['seletor_funcional'] = seletor
                        return "selenium"
                        
            except Exception as e:
                self.logger.debug(f"Selenium falhou para {url}: {e}")
                continue
        
        return "falhou"
    
    def _get_selenium_driver(self):
        """Obter driver Selenium configurado"""
        
        if self.driver:
            return self.driver
        
        if not SELENIUM_DISPONIVEL:
            return None
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Executar sem interface
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("✅ Driver Selenium configurado")
            return self.driver
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao configurar Selenium: {e}")
            return None
    
    def coletar_com_requests(self, site_name: str, max_pages: int = 10) -> List[Dict]:
        """Coleta usando Requests + BeautifulSoup"""
        
        config = self.sites_config[site_name]
        concursos = []
        
        base_url = config['url_funcional']
        seletor = config['seletor_funcional']
        
        self.logger.info(f"🌐 Coletando {site_name} com Requests (até {max_pages} páginas)")
        
        for pagina in range(1, max_pages + 1):
            try:
                # Construir URL da página
                if '?' in base_url:
                    url_pagina = f"{base_url}&page={pagina}"
                else:
                    url_pagina = f"{base_url}?page={pagina}" if 'page' not in base_url else f"{base_url.replace('page', 'page')}/{pagina}"
                
                # Fazer requisição
                response = requests.get(url_pagina, headers=self.headers, timeout=15)
                
                if response.status_code != 200:
                    self.logger.warning(f"Status {response.status_code} para página {pagina}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                elementos = soup.select(seletor)
                
                if not elementos:
                    self.logger.warning(f"Página {pagina} vazia")
                    break
                
                # Extrair dados dos elementos
                for elemento in elementos:
                    concurso = self._extrair_dados_elemento_requests(elemento, site_name)
                    if concurso:
                        concursos.append(concurso)
                
                self.logger.info(f"📄 Página {pagina}: {len(elementos)} elementos encontrados")
                
                # Delay entre páginas
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                self.logger.error(f"Erro na página {pagina}: {e}")
                continue
        
        return concursos
    
    def coletar_com_selenium(self, site_name: str, max_pages: int = 10) -> List[Dict]:
        """Coleta usando Selenium"""
        
        config = self.sites_config[site_name]
        concursos = []
        
        driver = self._get_selenium_driver()
        if not driver:
            self.logger.error("❌ Driver Selenium não disponível")
            return []
        
        base_url = config['url_funcional']
        seletor = config['seletor_funcional']
        
        self.logger.info(f"🤖 Coletando {site_name} com Selenium (até {max_pages} páginas)")
        
        try:
            for pagina in range(1, max_pages + 1):
                try:
                    # Navegar para página
                    if pagina == 1:
                        driver.get(base_url)
                    else:
                        # Tentar encontrar botão de próxima página
                        try:
                            next_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="page"], .next, .pagination'))
                            )
                            next_button.click()
                        except:
                            # Construir URL manualmente se não encontrar botão
                            url_pagina = f"{base_url}?page={pagina}"
                            driver.get(url_pagina)
                    
                    # Aguardar carregamento
                    time.sleep(3)
                    
                    # Encontrar elementos
                    elementos = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, seletor))
                    )
                    
                    if not elementos:
                        self.logger.warning(f"Página {pagina} vazia")
                        break
                    
                    # Extrair dados
                    for elemento in elementos:
                        concurso = self._extrair_dados_elemento_selenium(elemento, site_name)
                        if concurso:
                            concursos.append(concurso)
                    
                    self.logger.info(f"📄 Página {pagina}: {len(elementos)} elementos encontrados")
                    
                except Exception as e:
                    self.logger.error(f"Erro na página {pagina}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro geral no Selenium: {e}")
        
        return concursos
    
    def _extrair_dados_elemento_requests(self, elemento, site_name: str) -> Dict:
        """Extrair dados de um elemento usando BeautifulSoup"""
        
        try:
            concurso = {
                'titulo': '',
                'orgao': '',
                'vagas': 0,
                'salario': '',
                'salario_numerico': 0,
                'escolaridade': '',
                'status': '',
                'cidade': '',
                'estado': '',
                'data_coleta': datetime.now().isoformat(),
                'fonte': site_name.replace('_', ' ').title(),
                'link': ''
            }
            
            # Extrair título
            titulo_elem = elemento.find(['h1', 'h2', 'h3', 'h4', 'a']) or elemento
            if titulo_elem:
                concurso['titulo'] = titulo_elem.get_text(strip=True)
            
            # Extrair link
            link_elem = elemento.find('a', href=True)
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('/'):
                    # URL relativa
                    base = self.sites_config[site_name]['url_funcional']
                    concurso['link'] = f"{base.split('/')[0]}//{base.split('/')[2]}{href}"
                else:
                    concurso['link'] = href
            
            # Extrair outros dados (implementação básica)
            texto_completo = elemento.get_text()
            
            # Tentar extrair vagas
            import re
            vagas_match = re.search(r'(\d+)\s*vaga', texto_completo, re.IGNORECASE)
            if vagas_match:
                concurso['vagas'] = int(vagas_match.group(1))
            
            # Tentar extrair salário
            salario_match = re.search(r'R\$\s*[\d.,]+', texto_completo)
            if salario_match:
                concurso['salario'] = salario_match.group(0)
                # Converter para numérico
                try:
                    salario_num = re.sub(r'[^\d,]', '', salario_match.group(0))
                    salario_num = float(salario_num.replace(',', '.'))
                    concurso['salario_numerico'] = salario_num
                except:
                    pass
            
            return concurso if concurso['titulo'] else None
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair dados: {e}")
            return None
    
    def _extrair_dados_elemento_selenium(self, elemento, site_name: str) -> Dict:
        """Extrair dados de um elemento usando Selenium"""
        
        try:
            concurso = {
                'titulo': '',
                'orgao': '',
                'vagas': 0,
                'salario': '',
                'salario_numerico': 0,
                'escolaridade': '',
                'status': '',
                'cidade': '',
                'estado': '',
                'data_coleta': datetime.now().isoformat(),
                'fonte': site_name.replace('_', ' ').title(),
                'link': ''
            }
            
            # Extrair título
            try:
                concurso['titulo'] = elemento.find_element(By.TAG_NAME, 'a').text.strip()
            except:
                concurso['titulo'] = elemento.text.strip()
            
            # Extrair link
            try:
                link_elem = elemento.find_element(By.TAG_NAME, 'a')
                href = link_elem.get_attribute('href')
                concurso['link'] = href or ''
            except:
                pass
            
            # Extrair outros dados do texto completo
            texto_completo = elemento.text
            
            # Tentar extrair vagas
            import re
            vagas_match = re.search(r'(\d+)\s*vaga', texto_completo, re.IGNORECASE)
            if vagas_match:
                concurso['vagas'] = int(vagas_match.group(1))
            
            # Tentar extrair salário
            salario_match = re.search(r'R\$\s*[\d.,]+', texto_completo)
            if salario_match:
                concurso['salario'] = salario_match.group(0)
                try:
                    salario_num = re.sub(r'[^\d,]', '', salario_match.group(0))
                    salario_num = float(salario_num.replace(',', '.'))
                    concurso['salario_numerico'] = salario_num
                except:
                    pass
            
            return concurso if concurso['titulo'] else None
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair dados Selenium: {e}")
            return None
    
    def coletar_site(self, site_name: str, max_pages: int = 10) -> List[Dict]:
        """Método principal para coletar um site"""
        
        self.logger.info(f"🚀 Iniciando coleta de {site_name}")
        
        # Detectar melhor estratégia
        estrategia = self.detectar_melhor_estrategia(site_name)
        
        # Executar coleta com estratégia escolhida
        if estrategia == "requests":
            concursos = self.coletar_com_requests(site_name, max_pages)
        elif estrategia == "selenium":
            concursos = self.coletar_com_selenium(site_name, max_pages)
        else:
            self.logger.error(f"❌ Nenhuma estratégia funcional para {site_name}")
            return []
        
        # Remover duplicatas
        concursos_unicos = self._remover_duplicatas(concursos)
        
        self.logger.info(f"✅ {site_name}: {len(concursos_unicos)} concursos únicos coletados")
        
        return concursos_unicos
    
    def _remover_duplicatas(self, concursos: List[Dict]) -> List[Dict]:
        """Remove concursos duplicados baseado no título"""
        
        vistos = set()
        unicos = []
        
        for concurso in concursos:
            titulo_key = concurso['titulo'].lower().strip()
            if titulo_key and titulo_key not in vistos:
                vistos.add(titulo_key)
                unicos.append(concurso)
        
        return unicos
    
    def coletar_todos_sites(self, pci_pages: int = 10, brasil_pages: int = 10) -> Dict:
        """Coletar todos os sites configurados"""
        
        self.logger.info("🎯 INICIANDO COLETA HÍBRIDA DE TODOS OS SITES")
        
        resultado = {
            'pci_concurso': [],
            'concursos_brasil': [],
            'total_geral': 0,
            'sucesso': False,
            'estrategias_usadas': {}
        }
        
        try:
            # Coletar PCI Concurso
            resultado['pci_concurso'] = self.coletar_site('pci_concurso', pci_pages)
            resultado['estrategias_usadas']['pci_concurso'] = self.cache_estrategias.get('pci_concurso', 'unknown')
            
            # Delay entre sites
            time.sleep(5)
            
            # Coletar Concursos Brasil
            resultado['concursos_brasil'] = self.coletar_site('concursos_brasil', brasil_pages)
            resultado['estrategias_usadas']['concursos_brasil'] = self.cache_estrategias.get('concursos_brasil', 'unknown')
            
            # Calcular totais
            resultado['total_geral'] = len(resultado['pci_concurso']) + len(resultado['concursos_brasil'])
            resultado['sucesso'] = resultado['total_geral'] > 0
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"❌ Erro na coleta geral: {e}")
            resultado['sucesso'] = False
            return resultado
    
    def salvar_dados(self, concursos: List[Dict], nome_arquivo: str = None) -> str:
        """Salvar dados coletados"""
        
        if not concursos:
            self.logger.warning("⚠️ Nenhum dado para salvar")
            return ""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome = nome_arquivo or f"concursos_hibrido_{timestamp}"
            
            # Salvar CSV
            df = pd.DataFrame(concursos)
            csv_file = f"{nome}.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            # Salvar JSON
            json_file = f"{nome}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(concursos, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 Dados salvos: {csv_file} e {json_file}")
            return csv_file
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar: {e}")
            return ""
    
    def __del__(self):
        """Cleanup do driver Selenium"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

def main():
    """Função principal de demonstração"""
    
    print("🎯 SCRAPER HÍBRIDO OTIMIZADO")
    print("=" * 50)
    print("🌐 Requests + BeautifulSoup (rápido)")
    print("🤖 Selenium (para sites dinâmicos)")
    print("⚡ Estratégia adaptativa automática")
    print("=" * 50)
    
    # Criar scraper
    scraper = ScraperHibridoOtimizado()
    
    try:
        # Executar coleta
        resultado = scraper.coletar_todos_sites(pci_pages=5, brasil_pages=5)
        
        print(f"\n📊 RESULTADOS:")
        print(f"PCI Concurso: {len(resultado['pci_concurso'])} concursos ({resultado['estrategias_usadas'].get('pci_concurso', 'unknown')})")
        print(f"Concursos Brasil: {len(resultado['concursos_brasil'])} concursos ({resultado['estrategias_usadas'].get('concursos_brasil', 'unknown')})")
        print(f"Total: {resultado['total_geral']} concursos")
        
        # Salvar se tiver dados
        if resultado['total_geral'] > 0:
            todos_concursos = resultado['pci_concurso'] + resultado['concursos_brasil']
            scraper.salvar_dados(todos_concursos, "teste_hibrido")
            
        print(f"\n✅ Coleta finalizada com {'sucesso' if resultado['sucesso'] else 'falhas'}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Coleta interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    main()
