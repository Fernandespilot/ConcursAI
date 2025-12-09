# scrapers/cebraspe_scraper.py
"""
Scraper para coletar editais da Cebraspe
Extrai PDFs de editais e provas automaticamente
"""

import requests
from bs4 import BeautifulSoup
import logging
import os
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CebraspeScraper:
    """
    Scraper para o site da Cebraspe
    Coleta editais e provas em PDF
    """
    
    def __init__(self, output_dir="editais"):
        self.base_url = "https://www.cebraspe.org.br"
        self.concursos_url = f"{self.base_url}/concursos"
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Cria diretório se não existir
        os.makedirs(output_dir, exist_ok=True)
        
    def get_concursos_ativos(self):
        """
        Obtém lista de concursos ativos
        Returns: list de dicts com {titulo, url, status}
        """
        try:
            response = self.session.get(self.concursos_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            concursos = []
            
            # Busca cards de concursos (ajuste seletores conforme HTML real)
            cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('concurso' in x.lower() or 'card' in x.lower()))
            
            for card in cards[:10]:  # Limita a 10 para teste
                try:
                    link = card.find('a', href=True)
                    if link:
                        titulo = link.get_text(strip=True)
                        url = urljoin(self.base_url, link['href'])
                        
                        concursos.append({
                            'titulo': titulo,
                            'url': url,
                            'banca': 'cebraspe',
                            'data_coleta': datetime.now().strftime('%Y-%m-%d')
                        })
                except Exception as e:
                    logger.debug(f"Erro ao processar card: {e}")
                    
            logger.info(f"✓ Encontrados {len(concursos)} concursos Cebraspe")
            return concursos
            
        except Exception as e:
            logger.error(f"Erro ao buscar concursos Cebraspe: {e}")
            return []
    
    def get_pdfs_from_page(self, url):
        """
        Extrai links de PDFs de uma página de concurso
        Returns: list de dicts com {titulo, url, tipo}
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            pdfs = []
            
            # Busca todos os links que terminam em .pdf
            for link in soup.find_all('a', href=lambda x: x and x.lower().endswith('.pdf')):
                pdf_url = urljoin(url, link['href'])
                titulo = link.get_text(strip=True) or link.get('title', 'documento')
                
                # Identifica tipo do documento
                tipo = 'edital'
                titulo_lower = titulo.lower()
                if 'prova' in titulo_lower or 'gabarito' in titulo_lower:
                    tipo = 'prova'
                elif 'retific' in titulo_lower:
                    tipo = 'retificacao'
                elif 'resultado' in titulo_lower:
                    tipo = 'resultado'
                
                pdfs.append({
                    'titulo': titulo[:100],
                    'url': pdf_url,
                    'tipo': tipo
                })
            
            logger.info(f"✓ Encontrados {len(pdfs)} PDFs na página")
            return pdfs
            
        except Exception as e:
            logger.error(f"Erro ao buscar PDFs de {url}: {e}")
            return []
    
    def download_pdf(self, url, titulo, banca='cebraspe', tipo='edital'):
        """
        Baixa um PDF e salva no disco
        Returns: caminho do arquivo ou None
        """
        try:
            # Nome do arquivo seguro
            safe_titulo = "".join(c for c in titulo if c.isalnum() or c in " _-")[:50]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{banca}_{tipo}_{safe_titulo}_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Verifica se já existe
            if os.path.exists(filepath):
                logger.info(f"⊗ PDF já existe: {filename}")
                return filepath
            
            # Download
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Verifica se é PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"⚠ URL não é PDF: {url}")
                return None
            
            # Salva arquivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            logger.info(f"✓ Baixado: {filename} ({size_mb:.2f} MB)")
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao baixar {url}: {e}")
            return None
    
    def coletar_tudo(self, max_concursos=5):
        """
        Coleta editais de múltiplos concursos
        Returns: list de caminhos de PDFs baixados
        """
        logger.info("🕷️ Iniciando coleta Cebraspe...")
        pdfs_baixados = []
        
        # 1. Lista concursos
        concursos = self.get_concursos_ativos()
        if not concursos:
            logger.warning("⚠ Nenhum concurso encontrado")
            return []
        
        # 2. Para cada concurso, busca PDFs
        for i, concurso in enumerate(concursos[:max_concursos], 1):
            logger.info(f"[{i}/{min(len(concursos), max_concursos)}] {concurso['titulo']}")
            
            pdfs = self.get_pdfs_from_page(concurso['url'])
            
            # 3. Baixa cada PDF
            for pdf in pdfs[:3]:  # Máximo 3 PDFs por concurso
                filepath = self.download_pdf(
                    pdf['url'],
                    pdf['titulo'],
                    banca='cebraspe',
                    tipo=pdf['tipo']
                )
                
                if filepath:
                    pdfs_baixados.append({
                        'filepath': filepath,
                        'metadata': {
                            'banca': 'cebraspe',
                            'tipo': pdf['tipo'],
                            'titulo': pdf['titulo'],
                            'concurso': concurso['titulo'],
                            'data_coleta': datetime.now().strftime('%Y-%m-%d')
                        }
                    })
                
                time.sleep(1)  # Respeita o servidor
            
            time.sleep(2)  # Pausa entre concursos
        
        logger.info(f"✅ Coleta concluída: {len(pdfs_baixados)} PDFs baixados")
        return pdfs_baixados


# Teste standalone
if __name__ == "__main__":
    scraper = CebraspeScraper()
    pdfs = scraper.coletar_tudo(max_concursos=2)
    
    print("\n📊 RESULTADO:")
    for pdf in pdfs:
        print(f"  • {pdf['metadata']['tipo']}: {pdf['filepath']}")
