"""
🎯 SCRAPER MANAGER V3 - HÍBRIDO INTELIGENTE
==========================================
Sistema adaptativo que detecta automaticamente a melhor estratégia
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import time
import random
import re
from pathlib import Path

# Selenium com fallback
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_DISPONIVEL = True
except ImportError:
    SELENIUM_DISPONIVEL = False

class ScraperManagerV3:
    def __init__(self, output_dir: str = "data"):
        """Manager inteligente com estratégia híbrida"""
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Headers otimizados
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Configurações de sites atualizadas
        self.sites_config = {
            'pci_concurso': {
                'nome': 'PCI Concurso',
                'urls_candidatas': [
                    'https://www.pciconcursos.com.br/concursos',
                    'https://www.pciconcursos.com.br/concursos/abertos',
                    'https://www.pciconcursos.com.br/concursos/previstos',
                    'https://www.pciconcursos.com.br/',
                    'https://pciconcursos.com.br/concursos',
                    'https://www.pciconcursos.com.br/busca',
                ],
                'seletores_teste': [
                    'div.ca',  # Seletor conhecido do PCI
                    'div.card',
                    'div.concurso-item',
                    'tr[id*="concurso"]',
                    'div[class*="resultado"]',
                    'a[href*="/concurso/"]'
                ],
                'url_funcional': None,
                'estrategia': None
            },
            'concursos_brasil': {
                'nome': 'Concursos Brasil',
                'urls_candidatas': [
                    'https://www.concursosbrasil.com.br/concursos',
                    'https://www.concursosbrasil.com.br/concursos/abertos',
                    'https://www.concursosbrasil.com.br/',
                    'https://concursosbrasil.com.br/concursos',
                    'https://www.concursosbrasil.com.br/buscar',
                ],
                'seletores_teste': [
                    'div.card',
                    'div.item-concurso',
                    'div.concurso',
                    'tr.concurso',
                    'div[class*="list"]',
                    'a[href*="/concurso"]'
                ],
                'url_funcional': None,
                'estrategia': None
            }
        }
        
        # Cache de configurações funcionais
        self.cache_funcionais = {}
        
        # Driver Selenium (lazy loading)
        self.selenium_driver = None
        
        # Dados coletados
        self.concursos_coletados = []
        
        self.logger.info("🚀 ScraperManagerV3 inicializado")
        self.logger.info(f"📁 Diretório de output: {self.output_dir}")
        self.logger.info(f"🤖 Selenium disponível: {SELENIUM_DISPONIVEL}")
    
    def descobrir_urls_funcionais(self) -> Dict[str, bool]:
        """Descobre automaticamente quais URLs estão funcionais"""
        
        self.logger.info("🔍 DESCOBRINDO URLs FUNCIONAIS")
        self.logger.info("=" * 50)
        
        resultados = {}
        
        for site_nome, config in self.sites_config.items():
            self.logger.info(f"🌐 Testando {config['nome']}")
            
            melhor_url = None
            melhor_score = 0
            melhor_seletor = None
            
            for i, url in enumerate(config['urls_candidatas'], 1):
                self.logger.info(f"   {i}. Testando: {url}")
                
                try:
                    # Fazer requisição de teste
                    response = requests.get(url, headers=self.headers, timeout=15)
                    
                    if response.status_code != 200:
                        self.logger.warning(f"      ❌ Status {response.status_code}")
                        continue
                    
                    # Analisar conteúdo
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Testar seletores
                    score_url = 0
                    seletor_funcional = None
                    
                    for seletor in config['seletores_teste']:
                        elementos = soup.select(seletor)
                        if elementos:
                            score_atual = len(elementos)
                            self.logger.info(f"      ✅ {seletor}: {score_atual} elementos")
                            
                            if score_atual > score_url:
                                score_url = score_atual
                                seletor_funcional = seletor
                    
                    # Verificações adicionais
                    texto_completo = response.text.lower()
                    
                    # Bonus por palavras-chave relacionadas a concursos
                    palavras_concurso = ['concurso', 'edital', 'inscrições', 'vagas', 'seleção']
                    bonus_palavras = sum(1 for palavra in palavras_concurso if palavra in texto_completo)
                    score_url += bonus_palavras
                    
                    # Penalidade se parecer página de erro
                    if any(erro in texto_completo for erro in ['404', 'not found', 'erro', 'error']):
                        score_url -= 10
                    
                    self.logger.info(f"      📊 Score total: {score_url}")
                    
                    # Atualizar melhor opção
                    if score_url > melhor_score:
                        melhor_score = score_url
                        melhor_url = url
                        melhor_seletor = seletor_funcional
                        
                except Exception as e:
                    self.logger.warning(f"      ❌ Erro: {e}")
                    continue
            
            # Salvar melhor configuração encontrada
            if melhor_url and melhor_score > 0:
                config['url_funcional'] = melhor_url
                config['seletor_funcional'] = melhor_seletor
                config['score'] = melhor_score
                resultados[site_nome] = True
                
                self.logger.info(f"   🎉 SUCESSO: {melhor_url}")
                self.logger.info(f"      🎯 Seletor: {melhor_seletor}")
                self.logger.info(f"      📈 Score: {melhor_score}")
            else:
                resultados[site_nome] = False
                self.logger.warning(f"   ❌ FALHOU: Nenhuma URL funcional encontrada")
        
        return resultados
    
    def determinar_estrategia(self, site_nome: str) -> str:
        """Determina automaticamente a melhor estratégia para um site"""
        
        config = self.sites_config[site_nome]
        
        if not config.get('url_funcional'):
            return 'selenium'  # Fallback se não conseguiu com requests
        
        try:
            # Fazer análise mais detalhada da página
            response = requests.get(config['url_funcional'], headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Critérios para determinar se precisa de Selenium
            criterios_js = 0
            
            # 1. Verificar scripts que indicam carregamento dinâmico
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_text = script.string.lower()
                    if any(keyword in script_text for keyword in ['ajax', 'fetch', 'json', 'api']):
                        criterios_js += 1
            
            # 2. Verificar se há elementos de loading/spinner
            if soup.find(text=re.compile(r'(loading|carregando)', re.I)):
                criterios_js += 1
            
            # 3. Verificar meta tags de SPA
            if soup.find('meta', {'name': 'generator', 'content': re.compile(r'(react|angular|vue)', re.I)}):
                criterios_js += 2
            
            # 4. Testar se o seletor retorna elementos úteis
            elementos = soup.select(config['seletor_funcional'])
            if len(elementos) < 3:  # Poucos elementos podem indicar carregamento dinâmico
                criterios_js += 1
            
            # Decidir estratégia
            if criterios_js >= 2 and SELENIUM_DISPONIVEL:
                estrategia = 'selenium'
                self.logger.info(f"🤖 {site_nome}: JavaScript detectado - usando Selenium")
            else:
                estrategia = 'requests'
                self.logger.info(f"🌐 {site_nome}: Conteúdo estático - usando Requests")
            
            config['estrategia'] = estrategia
            return estrategia
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao analisar {site_nome}: {e}")
            return 'requests'  # Fallback seguro
    
    def obter_selenium_driver(self):
        """Obtém driver Selenium configurado"""
        
        if self.selenium_driver:
            return self.selenium_driver
        
        if not SELENIUM_DISPONIVEL:
            self.logger.error("❌ Selenium não está disponível")
            return None
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            self.selenium_driver = webdriver.Chrome(options=options)
            self.logger.info("✅ Driver Selenium configurado")
            return self.selenium_driver
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao configurar Selenium: {e}")
            return None
    
    def coletar_com_requests(self, site_nome: str, max_pages: int = 10) -> List[Dict]:
        """Coleta dados usando Requests + BeautifulSoup"""
        
        config = self.sites_config[site_nome]
        concursos = []
        
        self.logger.info(f"🌐 Coletando {config['nome']} com Requests")
        
        base_url = config['url_funcional']
        seletor = config['seletor_funcional']
        
        for pagina in range(1, max_pages + 1):
            try:
                # Construir URL da página
                if pagina == 1:
                    url_pagina = base_url
                else:
                    # Tentar diferentes padrões de paginação
                    padroes_paginacao = [
                        f"{base_url}?pagina={pagina}",
                        f"{base_url}?page={pagina}",
                        f"{base_url}/pagina/{pagina}",
                        f"{base_url}/page/{pagina}",
                        f"{base_url}&pagina={pagina}" if '?' in base_url else f"{base_url}?pagina={pagina}"
                    ]
                    
                    url_pagina = padroes_paginacao[0]  # Começar com o primeiro padrão
                
                self.logger.info(f"   📄 Página {pagina}: {url_pagina}")
                
                # Fazer requisição
                response = requests.get(url_pagina, headers=self.headers, timeout=15)
                
                if response.status_code != 200:
                    self.logger.warning(f"      ⚠️ Status {response.status_code}")
                    if pagina > 1:  # Se não é a primeira página, pode ter acabado
                        break
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                elementos = soup.select(seletor)
                
                if not elementos:
                    self.logger.warning(f"      ⚠️ Nenhum elemento encontrado")
                    if pagina > 1:
                        break
                    continue
                
                # Processar elementos encontrados
                concursos_pagina = 0
                for elemento in elementos:
                    concurso = self._extrair_dados_requests(elemento, site_nome)
                    if concurso and self._validar_concurso(concurso):
                        concursos.append(concurso)
                        concursos_pagina += 1
                
                self.logger.info(f"      ✅ {concursos_pagina} concursos válidos extraídos")
                
                # Se não encontrou nada, pode ter chegado ao fim
                if concursos_pagina == 0 and pagina > 1:
                    break
                
                # Delay entre páginas
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                self.logger.error(f"      ❌ Erro na página {pagina}: {e}")
                continue
        
        # Remover duplicatas
        concursos_unicos = self._remover_duplicatas(concursos)
        self.logger.info(f"🎉 {config['nome']}: {len(concursos_unicos)} concursos únicos coletados")
        
        return concursos_unicos
    
    def coletar_com_selenium(self, site_nome: str, max_pages: int = 10) -> List[Dict]:
        """Coleta dados usando Selenium"""
        
        config = self.sites_config[site_nome]
        concursos = []
        
        driver = self.obter_selenium_driver()
        if not driver:
            self.logger.error(f"❌ Não foi possível obter driver Selenium para {site_nome}")
            return []
        
        self.logger.info(f"🤖 Coletando {config['nome']} com Selenium")
        
        try:
            driver.get(config['url_funcional'])
            time.sleep(5)  # Aguardar carregamento inicial
            
            for pagina in range(1, max_pages + 1):
                try:
                    self.logger.info(f"   📄 Página {pagina}")
                    
                    # Aguardar elementos carregarem
                    elementos = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, config['seletor_funcional']))
                    )
                    
                    if not elementos:
                        self.logger.warning(f"      ⚠️ Nenhum elemento encontrado")
                        break
                    
                    # Processar elementos
                    concursos_pagina = 0
                    for elemento in elementos:
                        concurso = self._extrair_dados_selenium(elemento, site_nome)
                        if concurso and self._validar_concurso(concurso):
                            concursos.append(concurso)
                            concursos_pagina += 1
                    
                    self.logger.info(f"      ✅ {concursos_pagina} concursos válidos extraídos")
                    
                    # Tentar ir para próxima página
                    if pagina < max_pages:
                        try:
                            # Procurar botão de próxima página
                            next_selectors = ['a.next', 'a[rel="next"]', '.pagination .next', 'button.next']
                            next_clicked = False
                            
                            for selector in next_selectors:
                                try:
                                    next_button = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                    driver.execute_script("arguments[0].click();", next_button)
                                    time.sleep(3)
                                    next_clicked = True
                                    break
                                except:
                                    continue
                            
                            if not next_clicked:
                                self.logger.info(f"      ℹ️ Não encontrou botão de próxima página")
                                break
                                
                        except Exception as e:
                            self.logger.warning(f"      ⚠️ Erro ao navegar para próxima página: {e}")
                            break
                    
                except Exception as e:
                    self.logger.error(f"      ❌ Erro na página {pagina}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"❌ Erro geral no Selenium para {site_nome}: {e}")
        
        # Remover duplicatas
        concursos_unicos = self._remover_duplicatas(concursos)
        self.logger.info(f"🎉 {config['nome']}: {len(concursos_unicos)} concursos únicos coletados")
        
        return concursos_unicos
    
    def _extrair_dados_requests(self, elemento, site_nome: str) -> Dict:
        """Extrai dados de um elemento usando BeautifulSoup"""
        
        try:
            concurso = {
                'titulo': '',
                'orgao': '',
                'vagas': 0,
                'salario': '',
                'salario_numerico': 0.0,
                'escolaridade': '',
                'status': '',
                'cidade': '',
                'estado': '',
                'data_coleta': datetime.now().isoformat(),
                'fonte': self.sites_config[site_nome]['nome'],
                'link': ''
            }
            
            # Extrair texto completo do elemento
            texto_completo = elemento.get_text(' ', strip=True)
            
            # Extrair título (primeiro texto significativo ou link)
            titulo_elem = elemento.find(['h1', 'h2', 'h3', 'h4', 'a']) or elemento
            concurso['titulo'] = titulo_elem.get_text(strip=True)[:200]  # Limitar tamanho
            
            # Extrair link
            link_elem = elemento.find('a', href=True)
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('/'):
                    # URL relativa - construir URL completa
                    base_url = self.sites_config[site_nome]['url_funcional']
                    domain = f"{base_url.split('/')[0]}//{base_url.split('/')[2]}"
                    concurso['link'] = domain + href
                else:
                    concurso['link'] = href
            
            # Extrair dados usando regex no texto completo
            self._extrair_com_regex(texto_completo, concurso)
            
            return concurso if concurso['titulo'] else None
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair dados (requests): {e}")
            return None
    
    def _extrair_dados_selenium(self, elemento, site_nome: str) -> Dict:
        """Extrai dados de um elemento usando Selenium"""
        
        try:
            concurso = {
                'titulo': '',
                'orgao': '',
                'vagas': 0,
                'salario': '',
                'salario_numerico': 0.0,
                'escolaridade': '',
                'status': '',
                'cidade': '',
                'estado': '',
                'data_coleta': datetime.now().isoformat(),
                'fonte': self.sites_config[site_nome]['nome'],
                'link': ''
            }
            
            # Extrair texto completo
            texto_completo = elemento.text
            
            # Extrair título
            try:
                titulo_elem = elemento.find_element(By.TAG_NAME, 'a')
                concurso['titulo'] = titulo_elem.text.strip()[:200]
            except:
                concurso['titulo'] = texto_completo.split('\n')[0].strip()[:200]
            
            # Extrair link
            try:
                link_elem = elemento.find_element(By.TAG_NAME, 'a')
                href = link_elem.get_attribute('href')
                concurso['link'] = href or ''
            except:
                pass
            
            # Extrair outros dados usando regex
            self._extrair_com_regex(texto_completo, concurso)
            
            return concurso if concurso['titulo'] else None
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair dados (selenium): {e}")
            return None
    
    def _extrair_com_regex(self, texto: str, concurso: Dict):
        """Extrai dados usando expressões regulares"""
        
        # Extrair número de vagas
        vagas_patterns = [
            r'(\d+)\s*vagas?',
            r'vagas?\s*[:=]\s*(\d+)',
            r'(\d+)\s*postos?'
        ]
        
        for pattern in vagas_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                try:
                    concurso['vagas'] = int(match.group(1))
                    break
                except:
                    pass
        
        # Extrair salário
        salario_patterns = [
            r'R\$\s*[\d.,]+',
            r'salário\s*[:=]\s*R\$\s*[\d.,]+',
            r'remuneração\s*[:=]\s*R\$\s*[\d.,]+'
        ]
        
        for pattern in salario_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                concurso['salario'] = match.group(0)
                # Converter para numérico
                try:
                    numero_str = re.sub(r'[^\d,]', '', match.group(0))
                    numero_str = numero_str.replace(',', '.')
                    concurso['salario_numerico'] = float(numero_str)
                except:
                    pass
                break
        
        # Extrair escolaridade
        escolaridade_patterns = [
            r'(superior|graduação|ensino\s*superior)',
            r'(médio|ensino\s*médio)',
            r'(fundamental|ensino\s*fundamental)',
            r'(técnico|curso\s*técnico)'
        ]
        
        for pattern in escolaridade_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                concurso['escolaridade'] = match.group(1).title()
                break
        
        # Extrair status
        status_patterns = [
            r'(inscrições?\s*abertas?)',
            r'(aberto)',
            r'(previsto)',
            r'(encerrado)',
            r'(suspenso)'
        ]
        
        for pattern in status_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                concurso['status'] = match.group(1).title()
                break
    
    def _validar_concurso(self, concurso: Dict) -> bool:
        """Valida se o concurso extraído tem dados mínimos"""
        
        # Título é obrigatório e deve ter pelo menos 10 caracteres
        if not concurso.get('titulo') or len(concurso['titulo']) < 10:
            return False
        
        # Filtrar títulos muito genéricos ou suspeitos
        titulo_lower = concurso['titulo'].lower()
        palavras_suspeitas = ['error', '404', 'not found', 'carregando', 'loading']
        if any(palavra in titulo_lower for palavra in palavras_suspeitas):
            return False
        
        return True
    
    def _remover_duplicatas(self, concursos: List[Dict]) -> List[Dict]:
        """Remove concursos duplicados baseado no título"""
        
        vistos = set()
        unicos = []
        
        for concurso in concursos:
            # Criar chave única baseada no título normalizado
            titulo_key = re.sub(r'[^\w\s]', '', concurso['titulo'].lower()).strip()
            titulo_key = ' '.join(titulo_key.split())  # Normalizar espaços
            
            if titulo_key and titulo_key not in vistos:
                vistos.add(titulo_key)
                unicos.append(concurso)
        
        return unicos
    
    def coletar_todos_sites(self, pci_pages: int = 10, brasil_pages: int = 10) -> Dict:
        """Método principal para coletar todos os sites"""
        
        self.logger.info("🎯 INICIANDO COLETA HÍBRIDA INTELIGENTE")
        self.logger.info("=" * 60)
        
        # 1. Descobrir URLs funcionais
        urls_funcionais = self.descobrir_urls_funcionais()
        
        resultado = {
            'pci_concurso': [],
            'concursos_brasil': [],
            'total_geral': 0,
            'sucesso': False,
            'estrategias_usadas': {},
            'urls_funcionais': {}
        }
        
        try:
            # 2. Coletar PCI Concurso
            if urls_funcionais.get('pci_concurso'):
                estrategia_pci = self.determinar_estrategia('pci_concurso')
                resultado['estrategias_usadas']['pci_concurso'] = estrategia_pci
                resultado['urls_funcionais']['pci_concurso'] = self.sites_config['pci_concurso'].get('url_funcional')
                
                if estrategia_pci == 'requests':
                    resultado['pci_concurso'] = self.coletar_com_requests('pci_concurso', pci_pages)
                else:
                    resultado['pci_concurso'] = self.coletar_com_selenium('pci_concurso', pci_pages)
            else:
                self.logger.warning("⚠️ PCI Concurso: Nenhuma URL funcional encontrada")
            
            # Delay entre sites
            time.sleep(5)
            
            # 3. Coletar Concursos Brasil
            if urls_funcionais.get('concursos_brasil'):
                estrategia_brasil = self.determinar_estrategia('concursos_brasil')
                resultado['estrategias_usadas']['concursos_brasil'] = estrategia_brasil
                resultado['urls_funcionais']['concursos_brasil'] = self.sites_config['concursos_brasil'].get('url_funcional')
                
                if estrategia_brasil == 'requests':
                    resultado['concursos_brasil'] = self.coletar_com_requests('concursos_brasil', brasil_pages)
                else:
                    resultado['concursos_brasil'] = self.coletar_com_selenium('concursos_brasil', brasil_pages)
            else:
                self.logger.warning("⚠️ Concursos Brasil: Nenhuma URL funcional encontrada")
            
            # 4. Calcular resultados finais
            resultado['total_geral'] = len(resultado['pci_concurso']) + len(resultado['concursos_brasil'])
            resultado['sucesso'] = resultado['total_geral'] > 0
            
            # 5. Salvar dados se houver
            if resultado['total_geral'] > 0:
                todos_concursos = resultado['pci_concurso'] + resultado['concursos_brasil']
                self.concursos_coletados = todos_concursos
                self.salvar_dados_unificados()
            
            # 6. Relatório final
            self.logger.info("=" * 60)
            self.logger.info("🎉 COLETA FINALIZADA")
            self.logger.info(f"📊 PCI Concurso: {len(resultado['pci_concurso'])} concursos")
            self.logger.info(f"📊 Concursos Brasil: {len(resultado['concursos_brasil'])} concursos")
            self.logger.info(f"📊 TOTAL: {resultado['total_geral']} concursos")
            self.logger.info("=" * 60)
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"❌ Erro na coleta geral: {e}")
            resultado['sucesso'] = False
            return resultado
    
    def salvar_dados_unificados(self) -> str:
        """Salva todos os dados coletados"""
        
        if not self.concursos_coletados:
            return ""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Salvar CSV
            csv_file = self.output_dir / f"concursos_v3_{timestamp}.csv"
            df = pd.DataFrame(self.concursos_coletados)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            # Salvar JSON
            json_file = self.output_dir / f"concursos_v3_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.concursos_coletados, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 Dados salvos: {csv_file.name} e {json_file.name}")
            return str(csv_file)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar: {e}")
            return ""
    
    def __del__(self):
        """Cleanup automático"""
        if self.selenium_driver:
            try:
                self.selenium_driver.quit()
            except:
                pass

def main():
    """Função principal de teste"""
    
    print("🎯 SCRAPER MANAGER V3 - HÍBRIDO INTELIGENTE")
    print("=" * 60)
    
    # Criar manager
    manager = ScraperManagerV3()
    
    try:
        # Executar coleta completa
        resultado = manager.coletar_todos_sites(pci_pages=3, brasil_pages=3)  # Teste com poucas páginas
        
        print("\n📊 RESULTADO FINAL:")
        print(f"Sucesso: {resultado['sucesso']}")
        print(f"Total de concursos: {resultado['total_geral']}")
        print(f"Estratégias usadas: {resultado['estrategias_usadas']}")
        print(f"URLs funcionais: {resultado['urls_funcionais']}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Coleta interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    main()
