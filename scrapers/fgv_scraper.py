# scrapers/fgv_scraper.py
"""
Scraper para coletar editais da FGV Conhecimento
"""

import requests
from bs4 import BeautifulSoup
import logging
import os
from urllib.parse import urljoin
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FGVScraper:
    """
    Scraper para FGV Conhecimento
    Coleta editais de concursos públicos
    """
    
    def __init__(self, output_dir="editais"):
        self.base_url = "https://conhecimento.fgv.br"
        self.concursos_url = f"{self.base_url}/concursos"
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        os.makedirs(output_dir, exist_ok=True)
    
    def get_concursos_ativos(self):
        """Obtém concursos ativos da FGV"""
        try:
            response = self.session.get(self.concursos_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            concursos = []
            
            # Busca links de concursos
            for link in soup.find_all('a', href=lambda x: x and 'concurso' in x.lower()):
                titulo = link.get_text(strip=True)
                if len(titulo) > 10:  # Filtra títulos muito curtos
                    url = urljoin(self.base_url, link['href'])
                    concursos.append({
                        'titulo': titulo,
                        'url': url,
                        'banca': 'fgv',
                        'data_coleta': datetime.now().strftime('%Y-%m-%d')
                    })
            
            # Remove duplicatas
            concursos = list({c['url']: c for c in concursos}.values())
            
            logger.info(f"✓ Encontrados {len(concursos)} concursos FGV")
            return concursos[:10]  # Limita a 10
            
        except Exception as e:
            logger.error(f"Erro ao buscar concursos FGV: {e}")
            return []
    
    def get_pdfs_from_page(self, url):
        """Extrai PDFs de uma página de concurso"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            pdfs = []
            
            # Busca links de PDF
            for link in soup.find_all('a', href=lambda x: x and x.lower().endswith('.pdf')):
                pdf_url = urljoin(url, link['href'])
                titulo = link.get_text(strip=True) or 'documento'
                
                # Detecta tipo
                tipo = 'edital'
                if any(palavra in titulo.lower() for palavra in ['prova', 'gabarito', 'questão']):
                    tipo = 'prova'
                elif 'retific' in titulo.lower():
                    tipo = 'retificacao'
                
                pdfs.append({
                    'titulo': titulo[:100],
                    'url': pdf_url,
                    'tipo': tipo
                })
            
            logger.info(f"✓ Encontrados {len(pdfs)} PDFs")
            return pdfs
            
        except Exception as e:
            logger.error(f"Erro ao buscar PDFs: {e}")
            return []
    
    def download_pdf(self, url, titulo, tipo='edital'):
        """Baixa um PDF"""
        try:
            safe_titulo = "".join(c for c in titulo if c.isalnum() or c in " _-")[:50]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fgv_{tipo}_{safe_titulo}_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            if os.path.exists(filepath):
                logger.info(f"⊗ Já existe: {filename}")
                return filepath
            
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            if 'pdf' not in response.headers.get('Content-Type', '').lower():
                return None
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            logger.info(f"✓ Baixado: {filename} ({size_mb:.2f} MB)")
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao baixar: {e}")
            return None
    
    def coletar_tudo(self, max_concursos=5):
        """Coleta editais da FGV"""
        logger.info("🕷️ Iniciando coleta FGV...")
        pdfs_baixados = []
        
        concursos = self.get_concursos_ativos()
        if not concursos:
            return []
        
        for i, concurso in enumerate(concursos[:max_concursos], 1):
            logger.info(f"[{i}/{min(len(concursos), max_concursos)}] {concurso['titulo']}")
            
            pdfs = self.get_pdfs_from_page(concurso['url'])
            
            for pdf in pdfs[:2]:  # Máx 2 PDFs por concurso
                filepath = self.download_pdf(pdf['url'], pdf['titulo'], pdf['tipo'])
                
                if filepath:
                    pdfs_baixados.append({
                        'filepath': filepath,
                        'metadata': {
                            'banca': 'fgv',
                            'tipo': pdf['tipo'],
                            'titulo': pdf['titulo'],
                            'concurso': concurso['titulo'],
                            'data_coleta': datetime.now().strftime('%Y-%m-%d')
                        }
                    })
                
                time.sleep(1)
            
            time.sleep(2)
        
        logger.info(f"✅ Coleta FGV concluída: {len(pdfs_baixados)} PDFs")
        return pdfs_baixados


if __name__ == "__main__":
    scraper = FGVScraper()
    pdfs = scraper.coletar_tudo(max_concursos=2)
    print(f"\n📊 Total: {len(pdfs)} PDFs")
