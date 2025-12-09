"""
Scraper Multi-Fonte para Provas de Concursos
Busca em múltiplos sites: Questões de Concursos, Qconcursos, etc.
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProvasConcursosScraper:
    """
    Scraper multi-fonte para provas de concursos
    Busca nos sites oficiais das bancas onde as provas ficam disponíveis
    """
    
    URLS_BANCAS = {
        'cebraspe': {
            'nome': 'Cebraspe',
            'url_provas': 'https://www.cebraspe.org.br/concursos/',
            'url_busca': 'https://www.cebraspe.org.br/concursos/?action=search&query='
        },
        'fcc': {
            'nome': 'FCC',
            'url_provas': 'https://www.fcc.org.br/concursos/',
            'url_busca': 'https://concursos.fcc.org.br/'
        },
        'fgv': {
            'nome': 'FGV',
            'url_provas': 'https://conhecimento.fgv.br/concursos',
            'url_busca': 'https://conhecimento.fgv.br/concursos'
        }
    }
    
    def __init__(self, download_dir='provas_concursos'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        self.stats = {'provas': 0, 'gabaritos': 0, 'erros': 0}
    
    def buscar_provas_direto(self, banca, max_provas=10):
        """Busca provas diretamente no site da banca"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 Buscando provas no site oficial - {banca.upper()}")
        logger.info(f"{'='*60}\n")
        
        if banca not in self.URLS_BANCAS:
            logger.error(f"❌ Banca {banca} não suportada")
            return []
        
        banca_info = self.URLS_BANCAS[banca]
        
        try:
            logger.info(f"📡 Acessando: {banca_info['url_provas']}")
            response = self.session.get(banca_info['url_provas'], timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"⚠️  Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar todos os links de PDF
            pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
            
            logger.info(f"📄 Encontrados {len(pdf_links)} links de PDF")
            
            provas_encontradas = []
            
            for link in pdf_links[:max_provas * 2]:  # Pega mais para filtrar depois
                try:
                    pdf_url = link['href']
                    if not pdf_url.startswith('http'):
                        # Constrói URL completa
                        from urllib.parse import urljoin
                        pdf_url = urljoin(banca_info['url_provas'], pdf_url)
                    
                    texto = link.get_text(strip=True) or link.get('title', '') or 'documento'
                    texto_lower = texto.lower()
                    
                    # Filtra apenas provas e gabaritos (ignora editais)
                    if any(palavra in texto_lower for palavra in ['prova', 'gabarito', 'caderno', 'questões', 'questoes']):
                        tipo = 'gabarito' if 'gabarito' in texto_lower else 'prova'
                        
                        provas_encontradas.append({
                            'url': pdf_url,
                            'titulo': texto[:80],
                            'tipo': tipo,
                            'banca': banca
                        })
                        
                        if len(provas_encontradas) >= max_provas:
                            break
                            
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar link: {e}")
                    continue
            
            logger.info(f"✅ Filtrados {len(provas_encontradas)} arquivos de provas/gabaritos")
            
            # Baixar provas
            if provas_encontradas:
                self._baixar_lista(provas_encontradas, banca)
            
            return provas_encontradas
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar provas: {e}")
            return []
    
    def _baixar_lista(self, provas, banca):
        """Baixa lista de provas"""
        logger.info(f"\n📥 Baixando {len(provas)} arquivos...\n")
        
        for i, prova in enumerate(provas, 1):
            logger.info(f"[{i}/{len(provas)}] {prova['tipo'].upper()}: {prova['titulo'][:50]}...")
            
            arquivo = self._download_pdf(
                prova['url'],
                prova['titulo'],
                banca,
                prova['tipo']
            )
            
            if arquivo:
                if prova['tipo'] == 'gabarito':
                    self.stats['gabaritos'] += 1
                else:
                    self.stats['provas'] += 1
            
            time.sleep(2)
    
    def _download_pdf(self, pdf_url, titulo, banca, tipo):
        """Baixa um PDF"""
        try:
            titulo_limpo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).strip()
            titulo_limpo = titulo_limpo[:60]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{banca}_{tipo}_{titulo_limpo}_{timestamp}.pdf"
            filepath = self.download_dir / filename
            
            if filepath.exists():
                logger.info(f"  ⏭️ Já existe")
                return str(filepath)
            
            response = self.session.get(pdf_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Verifica se é realmente PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and not pdf_url.endswith('.pdf'):
                logger.warning(f"  ⚠️ Pode não ser PDF: {content_type}")
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            size_mb = filepath.stat().st_size / 1024 / 1024
            logger.info(f"  ✅ Baixado ({size_mb:.2f} MB)")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"  ❌ Erro: {e}")
            self.stats['erros'] += 1
            return None
    
    def coletar_todas_bancas(self, max_por_banca=10):
        """Coleta provas de todas as bancas"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 COLETA DE PROVAS E GABARITOS - SITES OFICIAIS")
        logger.info(f"{'='*70}\n")
        
        for banca in self.URLS_BANCAS.keys():
            self.buscar_provas_direto(banca, max_por_banca)
            logger.info("\n⏸️ Aguardando 10 segundos...\n")
            time.sleep(10)
        
        self._relatorio_final()
    
    def _relatorio_final(self):
        """Relatório final"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 COLETA COMPLETA!")
        logger.info(f"{'='*70}")
        logger.info(f"✅ Provas: {self.stats['provas']}")
        logger.info(f"✅ Gabaritos: {self.stats['gabaritos']}")
        logger.info(f"❌ Erros: {self.stats['erros']}")
        logger.info(f"📁 Diretório: {self.download_dir.absolute()}")
        logger.info(f"{'='*70}\n")


if __name__ == '__main__':
    print("\n📚 SCRAPER DE PROVAS E GABARITOS")
    print("Busca direta nos sites oficiais das bancas")
    print("="*60)
    print()
    
    scraper = ProvasConcursosScraper()
    
    import sys
    if len(sys.argv) > 1:
        banca = sys.argv[1].lower()
        max_provas = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        scraper.buscar_provas_direto(banca, max_provas)
    else:
        scraper.coletar_todas_bancas(max_por_banca=10)
