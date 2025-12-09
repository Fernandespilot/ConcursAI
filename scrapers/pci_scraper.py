"""
Scraper para PCI Concurso
========================
Coleta informações de concursos do site pciconcursos.com.br
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

class PCIConcursoScraper:
    def __init__(self, delay_range=(1, 3)):
        """
        Inicializa o scraper para PCI Concurso
        
        Args:
            delay_range: Tupla com tempo mínimo e máximo entre requests (em segundos)
        """
        self.base_url = "https://www.pciconcursos.com.br"
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
            title_elem = concurso_element.find('a', class_='ca')
            if title_elem:
                data['titulo'] = title_elem.get_text(strip=True)
                data['link'] = urljoin(self.base_url, title_elem.get('href', ''))
            else:
                return None
            
            # Órgão
            orgao_elem = concurso_element.find('span', class_='orgao')
            if orgao_elem:
                data['orgao'] = orgao_elem.get_text(strip=True)
            
            # Localização
            local_elem = concurso_element.find('span', class_='local')
            if local_elem:
                data['localizacao'] = local_elem.get_text(strip=True)
            
            # Escolaridade
            escol_elem = concurso_element.find('span', class_='escolaridade')
            if escol_elem:
                data['escolaridade'] = escol_elem.get_text(strip=True)
            
            # Número de vagas
            vagas_elem = concurso_element.find('span', class_='vagas')
            if vagas_elem:
                vagas_text = vagas_elem.get_text(strip=True)
                # Extrair número de vagas
                vagas_match = re.search(r'(\d+)', vagas_text)
                if vagas_match:
                    data['vagas'] = int(vagas_match.group(1))
                else:
                    data['vagas'] = 0
            
            # Salário
            salario_elem = concurso_element.find('span', class_='salario')
            if salario_elem:
                salario_text = salario_elem.get_text(strip=True)
                # Limpar e extrair valor do salário
                data['salario'] = self._parse_salary(salario_text)
            
            # Data de inscrição
            inscr_elem = concurso_element.find('span', class_='inscricao')
            if inscr_elem:
                data['inscricoes'] = inscr_elem.get_text(strip=True)
            
            # Status
            status_elem = concurso_element.find('span', class_='situacao')
            if status_elem:
                data['status'] = status_elem.get_text(strip=True)
            
            # Adicionar metadados
            data['fonte'] = 'PCI Concurso'
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
        
        return salary_clean
    
    def search_concursos(self, 
                        query: str = "", 
                        pages: int = 3,
                        filters: Dict = None) -> List[Dict]:
        """
        Busca concursos no PCI Concurso
        
        Args:
            query: Termo de busca
            pages: Número de páginas para coletar (padrão: 3)
            filters: Filtros adicionais (localização, escolaridade, etc.)
            
        Returns:
            Lista de dicionários com dados dos concursos
        """
        concursos = []
        
        try:
            # Construir URL de busca
            search_url = f"{self.base_url}/concursos/"
            
            if query:
                search_url += f"?q={query}"
            
            self.logger.info(f"🔍 Iniciando busca: {query or 'todos os concursos'}")
            self.logger.info(f"📄 Coletando {pages} páginas")
            
            for page in range(1, pages + 1):
                page_url = f"{search_url}&page={page}" if '?' in search_url else f"{search_url}?page={page}"
                
                self.logger.info(f"📄 Coletando página {page}/{pages}...")
                
                soup = self._get_page(page_url)
                if not soup:
                    self.logger.warning(f"⚠️ Falha ao carregar página {page}")
                    continue
                
                # Encontrar elementos de concursos
                concurso_elements = soup.find_all('tr', class_=['cw', 'ca'])
                
                if not concurso_elements:
                    self.logger.warning(f"Nenhum concurso encontrado na página {page}")
                    continue
                
                page_concursos = 0
                for element in concurso_elements:
                    concurso_data = self._extract_concurso_data(element)
                    if concurso_data:
                        concursos.append(concurso_data)
                        page_concursos += 1
                
                self.logger.info(f"✅ Coletados {page_concursos} concursos da página {page}")
                
                # Verificar se há próxima página
                next_link = soup.find('a', string='Próxima')
                if not next_link and page < pages:
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
            # Extrair informações detalhadas
            # Isso dependeria da estrutura específica da página de detalhes
            
            # Descrição
            desc_elem = soup.find('div', class_='descricao')
            if desc_elem:
                details['descricao'] = desc_elem.get_text(strip=True)
            
            # Edital
            edital_elem = soup.find('a', string=re.compile('edital', re.I))
            if edital_elem:
                details['edital_url'] = urljoin(self.base_url, edital_elem.get('href', ''))
            
            # Cronograma
            cronograma_elem = soup.find('table', class_='cronograma')
            if cronograma_elem:
                cronograma = []
                for row in cronograma_elem.find_all('tr')[1:]:  # Pular cabeçalho
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        cronograma.append({
                            'evento': cols[0].get_text(strip=True),
                            'data': cols[1].get_text(strip=True)
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
            filename = f"pci_concursos_{timestamp}.csv"
        
        try:
            df = pd.DataFrame(concursos)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            self.logger.info(f"💾 Dados salvos em: {filename}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV: {e}")

# Exemplo de uso
if __name__ == "__main__":
    scraper = PCIConcursoScraper()
    
    # Buscar concursos de tecnologia
    concursos = scraper.search_concursos(
        query="programador",
        pages=3
    )
    
    # Salvar em CSV
    scraper.save_to_csv(concursos)
    
    print(f"Coletados {len(concursos)} concursos!")
