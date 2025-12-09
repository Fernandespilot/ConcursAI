"""
Scraper para Concurso no Brasil
===============================
Coleta informações de concursos do site concursosnobrasil.com.br
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import re
import json

class ConcursoNoBrasilScraper:
    def __init__(self, delay_range=(1, 3)):
        """
        Inicializa o scraper para Concurso no Brasil
        
        Args:
            delay_range: Tupla com tempo mínimo e máximo entre requests (em segundos)
        """
        self.base_url = "https://www.concursosnobrasil.com.br"
        self.delay_range = delay_range
        self.session = requests.Session()
        
        # Headers para parecer um navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.concursosnobrasil.com.br/',
        })
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _wait(self):
        """Aguarda um tempo aleatório entre requests"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def _get_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Faz request para uma página com retry automático
        
        Args:
            url: URL da página
            max_retries: Número máximo de tentativas
            
        Returns:
            BeautifulSoup object ou None se falhar
        """
        for attempt in range(max_retries):
            try:
                self._wait()
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Verificar se não é uma página de erro
                if "erro" in response.url.lower() or response.status_code != 200:
                    self.logger.warning(f"Página de erro detectada: {url}")
                    return None
                
                soup = BeautifulSoup(response.content, 'html.parser')
                self.logger.info(f"✅ Página carregada: {url}")
                return soup
                
            except requests.RequestException as e:
                self.logger.error(f"Erro no request (tentativa {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponencial
                
        self.logger.error(f"❌ Falha ao carregar página após {max_retries} tentativas: {url}")
        return None
    
    def _extract_concurso_data(self, concurso_element) -> Optional[Dict]:
        """
        Extrai dados de um elemento de concurso
        
        Args:
            concurso_element: Elemento BeautifulSoup do concurso
            
        Returns:
            Dicionário com dados do concurso ou None se falhar
        """
        try:
            data = {}
            
            # Título/Nome do concurso
            title_elem = concurso_element.find('h3') or concurso_element.find('h2') or concurso_element.find('a', class_='titulo')
            if title_elem:
                data['titulo'] = title_elem.get_text(strip=True)
                # Tentar encontrar link
                link_elem = title_elem.find('a') or concurso_element.find('a')
                if link_elem:
                    data['link'] = urljoin(self.base_url, link_elem.get('href', ''))
            else:
                return None
            
            # Órgão/Instituição
            orgao_elem = concurso_element.find('span', class_='orgao') or \
                        concurso_element.find('div', class_='instituicao') or \
                        concurso_element.find(text=re.compile(r'Órgão|Instituição'))
            
            if orgao_elem:
                if hasattr(orgao_elem, 'get_text'):
                    data['orgao'] = orgao_elem.get_text(strip=True)
                else:
                    # Se for texto, pegar o elemento pai
                    parent = orgao_elem.parent
                    if parent:
                        data['orgao'] = parent.get_text(strip=True)
            
            # Localização/Estado
            local_elem = concurso_element.find('span', class_='local') or \
                        concurso_element.find('div', class_='localizacao') or \
                        concurso_element.find(text=re.compile(r'Estado|UF|Local'))
            
            if local_elem:
                if hasattr(local_elem, 'get_text'):
                    data['localizacao'] = local_elem.get_text(strip=True)
                else:
                    parent = local_elem.parent
                    if parent:
                        data['localizacao'] = parent.get_text(strip=True)
            
            # Escolaridade
            escol_elem = concurso_element.find('span', class_='escolaridade') or \
                        concurso_element.find('div', class_='nivel') or \
                        concurso_element.find(text=re.compile(r'Escolaridade|Nível'))
            
            if escol_elem:
                if hasattr(escol_elem, 'get_text'):
                    data['escolaridade'] = escol_elem.get_text(strip=True)
                else:
                    parent = escol_elem.parent
                    if parent:
                        data['escolaridade'] = parent.get_text(strip=True)
            
            # Número de vagas
            vagas_elem = concurso_element.find('span', class_='vagas') or \
                        concurso_element.find('div', class_='vagas') or \
                        concurso_element.find(text=re.compile(r'Vagas?'))
            
            if vagas_elem:
                if hasattr(vagas_elem, 'get_text'):
                    vagas_text = vagas_elem.get_text(strip=True)
                else:
                    parent = vagas_elem.parent
                    vagas_text = parent.get_text(strip=True) if parent else str(vagas_elem)
                
                # Extrair número de vagas
                vagas_match = re.search(r'(\d+)', vagas_text)
                if vagas_match:
                    data['vagas'] = int(vagas_match.group(1))
                else:
                    data['vagas'] = 0
            
            # Salário
            salario_elem = concurso_element.find('span', class_='salario') or \
                          concurso_element.find('div', class_='remuneracao') or \
                          concurso_element.find(text=re.compile(r'Salário|Remuneração|R\$'))
            
            if salario_elem:
                if hasattr(salario_elem, 'get_text'):
                    salario_text = salario_elem.get_text(strip=True)
                else:
                    parent = salario_elem.parent
                    salario_text = parent.get_text(strip=True) if parent else str(salario_elem)
                
                data['salario'] = self._parse_salary(salario_text)
            
            # Datas importantes
            data_elem = concurso_element.find('span', class_='data') or \
                       concurso_element.find('div', class_='cronograma')
            
            if data_elem:
                data['datas_importantes'] = data_elem.get_text(strip=True)
            
            # Status/Situação
            status_elem = concurso_element.find('span', class_='status') or \
                         concurso_element.find('div', class_='situacao')
            
            if status_elem:
                data['status'] = status_elem.get_text(strip=True)
            else:
                data['status'] = 'Ativo'  # Assumir ativo se não especificado
            
            # Banca organizadora
            banca_elem = concurso_element.find('span', class_='banca') or \
                        concurso_element.find('div', class_='organizadora')
            
            if banca_elem:
                data['banca'] = banca_elem.get_text(strip=True)
            
            # Adicionar metadados
            data['fonte'] = 'Concurso no Brasil'
            data['data_coleta'] = datetime.now().isoformat()
            data['url_fonte'] = self.base_url
            
            return data
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados do concurso: {e}")
            return None
    
    def _parse_salary(self, salary_text: str) -> str:
        """
        Limpa e padroniza texto de salário
        
        Args:
            salary_text: Texto do salário
            
        Returns:
            Salário limpo
        """
        if not salary_text:
            return ""
        
        # Remover espaços extras e normalizar
        salary_clean = re.sub(r'\s+', ' ', salary_text.strip())
        
        # Substituir abreviações comuns
        salary_clean = salary_clean.replace('R$', 'R$ ')
        salary_clean = re.sub(r'(\d+)mil', r'R$ \1.000,00', salary_clean)
        salary_clean = re.sub(r'até\s*R\$\s*(\d+\.?\d*)', r'até R$ \1', salary_clean)
        
        return salary_clean
    
    def search_concursos(self, 
                        query: str = "", 
                        pages: int = 5,
                        categoria: str = "",
                        estado: str = "") -> List[Dict]:
        """
        Busca concursos no Concurso no Brasil
        
        Args:
            query: Termo de busca
            pages: Número de páginas para coletar
            categoria: Categoria do concurso
            estado: Estado/UF
            
        Returns:
            Lista de dicionários com dados dos concursos
        """
        concursos = []
        
        try:
            # Construir URL de busca
            search_url = f"{self.base_url}/concursos"
            params = []
            
            if query:
                params.append(f"q={query}")
            if categoria:
                params.append(f"categoria={categoria}")
            if estado:
                params.append(f"estado={estado}")
            
            if params:
                search_url += "?" + "&".join(params)
            
            self.logger.info(f"🔍 Iniciando busca: {query or 'todos os concursos'}")
            self.logger.info(f"📄 Coletando {pages} páginas")
            
            for page in range(1, pages + 1):
                page_url = f"{search_url}&page={page}" if '?' in search_url else f"{search_url}?page={page}"
                
                self.logger.info(f"📄 Coletando página {page}/{pages}")
                
                soup = self._get_page(page_url)
                if not soup:
                    self.logger.warning(f"Falha ao carregar página {page}")
                    continue
                
                # Encontrar elementos de concursos - múltiplos seletores
                concurso_elements = (
                    soup.find_all('div', class_='concurso-item') or
                    soup.find_all('div', class_='card-concurso') or
                    soup.find_all('article', class_='concurso') or
                    soup.find_all('li', class_='concurso-lista') or
                    soup.find_all('tr', class_='concurso-row')
                )
                
                if not concurso_elements:
                    # Tentar seletores mais genéricos
                    concurso_elements = soup.find_all('div', class_=re.compile(r'concurso|card|item'))
                
                if not concurso_elements:
                    self.logger.warning(f"Nenhum concurso encontrado na página {page}")
                    continue
                
                page_concursos = 0
                for element in concurso_elements:
                    concurso_data = self._extract_concurso_data(element)
                    if concurso_data and concurso_data.get('titulo'):
                        concursos.append(concurso_data)
                        page_concursos += 1
                
                self.logger.info(f"✅ Coletados {page_concursos} concursos da página {page}")
                
                # Verificar se há próxima página
                next_links = soup.find_all('a', string=re.compile(r'Próxima|Next|»|>'))
                if not next_links and page < pages:
                    self.logger.info("Não há mais páginas disponíveis")
                    break
            
            self.logger.info(f"🎉 Coleta finalizada! Total: {len(concursos)} concursos")
            
        except Exception as e:
            self.logger.error(f"Erro durante a busca: {e}")
        
        return concursos
    
    def get_concurso_details(self, concurso_url: str) -> Dict:
        """
        Obtém detalhes completos de um concurso específico
        
        Args:
            concurso_url: URL do concurso
            
        Returns:
            Dicionário com detalhes do concurso
        """
        soup = self._get_page(concurso_url)
        if not soup:
            return {}
        
        details = {}
        
        try:
            # Descrição completa
            desc_selectors = [
                'div.descricao',
                'div.content',
                'div.detalhes',
                'section.informacoes'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    details['descricao'] = desc_elem.get_text(strip=True)
                    break
            
            # Link do edital
            edital_links = soup.find_all('a', string=re.compile(r'edital|regulamento', re.I))
            if edital_links:
                details['edital_url'] = urljoin(self.base_url, edital_links[0].get('href', ''))
            
            # Informações de cargos
            cargos_section = soup.find('section', class_='cargos') or soup.find('div', class_='cargos')
            if cargos_section:
                cargos = []
                cargo_items = cargos_section.find_all(['div', 'li'], class_=re.compile(r'cargo|item'))
                
                for item in cargo_items:
                    cargo_data = {
                        'nome': '',
                        'vagas': '',
                        'salario': '',
                        'requisitos': ''
                    }
                    
                    nome_elem = item.find(['h3', 'h4', 'strong'])
                    if nome_elem:
                        cargo_data['nome'] = nome_elem.get_text(strip=True)
                    
                    # Extrair outras informações do cargo
                    text = item.get_text()
                    
                    vagas_match = re.search(r'(\d+)\s*vagas?', text, re.I)
                    if vagas_match:
                        cargo_data['vagas'] = vagas_match.group(1)
                    
                    salario_match = re.search(r'R\$\s*[\d.,]+', text)
                    if salario_match:
                        cargo_data['salario'] = salario_match.group(0)
                    
                    if cargo_data['nome']:
                        cargos.append(cargo_data)
                
                details['cargos'] = cargos
            
            # Cronograma
            cronograma_section = soup.find('section', class_='cronograma') or \
                               soup.find('div', class_='cronograma') or \
                               soup.find('table', class_='cronograma')
            
            if cronograma_section:
                cronograma = []
                
                if cronograma_section.name == 'table':
                    rows = cronograma_section.find_all('tr')[1:]  # Pular cabeçalho
                    for row in rows:
                        cols = row.find_all(['td', 'th'])
                        if len(cols) >= 2:
                            cronograma.append({
                                'evento': cols[0].get_text(strip=True),
                                'data': cols[1].get_text(strip=True)
                            })
                else:
                    # Tentar extrair de texto
                    text = cronograma_section.get_text()
                    lines = text.split('\n')
                    for line in lines:
                        if ':' in line and any(month in line.lower() for month in 
                                             ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                                              'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']):
                            parts = line.split(':', 1)
                            if len(parts) == 2:
                                cronograma.append({
                                    'evento': parts[0].strip(),
                                    'data': parts[1].strip()
                                })
                
                details['cronograma'] = cronograma
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair detalhes: {e}")
        
        return details
    
    def save_to_csv(self, concursos: List[Dict], filename: str = None):
        """
        Salva concursos em arquivo CSV
        
        Args:
            concursos: Lista de concursos
            filename: Nome do arquivo (opcional)
        """
        if not concursos:
            self.logger.warning("Nenhum concurso para salvar")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"concursos_brasil_{timestamp}.csv"
        
        try:
            df = pd.DataFrame(concursos)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            self.logger.info(f"💾 Dados salvos em: {filename}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV: {e}")

# Exemplo de uso
if __name__ == "__main__":
    scraper = ConcursoNoBrasilScraper()
    
    # Buscar concursos de tecnologia
    concursos = scraper.search_concursos(
        query="analista de sistemas",
        pages=3
    )
    
    # Salvar em CSV
    scraper.save_to_csv(concursos)
    
    print(f"Coletados {len(concursos)} concursos!")
