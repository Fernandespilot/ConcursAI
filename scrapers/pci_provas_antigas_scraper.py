"""
Scraper PCI Concursos - Provas Anteriores
Busca provas e gabaritos de concursos já realizados
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


class PCIProvasAnterioresScraper:
    """Scraper especializado em provas e gabaritos de concursos realizados"""
    
    BASE_URL = "https://www.pciconcursos.com.br"
    
    # URLs para provas por banca
    URLS_PROVAS = {
        'cebraspe': '/provas/cebraspe',
        'fcc': '/provas/fcc',
        'fgv': '/provas/fgv'
    }
    
    def __init__(self, download_dir='provas_anteriores'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        self.stats = {'baixados': 0, 'erros': 0}
    
    def buscar_provas_banca(self, banca, max_provas=20):
        """Busca provas anteriores de uma banca"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 Buscando provas anteriores - {banca.upper()}")
        logger.info(f"{'='*60}\n")
        
        # Tenta diferentes URLs de busca
        urls_tentar = [
            f"{self.BASE_URL}/provas/{banca}",
            f"{self.BASE_URL}/provas?banca={banca}",
            f"{self.BASE_URL}/organizadoras/{banca}/provas",
        ]
        
        provas_encontradas = []
        
        for url in urls_tentar:
            try:
                logger.info(f"📡 Tentando: {url}")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar links de PDF
                    pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
                    
                    if pdf_links:
                        logger.info(f"✅ Encontrados {len(pdf_links)} links de PDF!")
                        
                        for link in pdf_links[:max_provas]:
                            pdf_url = link['href']
                            if not pdf_url.startswith('http'):
                                pdf_url = self.BASE_URL + pdf_url
                            
                            texto = link.get_text(strip=True)
                            
                            # Determinar tipo
                            texto_lower = texto.lower()
                            if 'gabarito' in texto_lower:
                                tipo = 'gabarito'
                            elif 'prova' in texto_lower or 'caderno' in texto_lower or 'questões' in texto_lower:
                                tipo = 'prova'
                            else:
                                tipo = 'prova'  # Assume prova por padrão
                            
                            provas_encontradas.append({
                                'url': pdf_url,
                                'titulo': texto[:80],
                                'tipo': tipo,
                                'banca': banca
                            })
                        
                        break  # Sucesso, não precisa tentar outras URLs
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro em {url}: {e}")
                continue
        
        if not provas_encontradas:
            logger.warning(f"⚠️ Nenhuma prova encontrada para {banca}")
            logger.info("💡 Tentando busca alternativa...")
            provas_encontradas = self._busca_alternativa(banca, max_provas)
        
        # Baixar provas encontradas
        if provas_encontradas:
            logger.info(f"\n📥 Baixando {len(provas_encontradas)} arquivos...\n")
            
            for i, prova in enumerate(provas_encontradas, 1):
                logger.info(f"[{i}/{len(provas_encontradas)}] {prova['tipo'].upper()}: {prova['titulo'][:60]}...")
                
                arquivo = self._download_pdf(
                    prova['url'],
                    prova['titulo'],
                    prova['banca'],
                    prova['tipo']
                )
                
                if arquivo:
                    self.stats['baixados'] += 1
                
                time.sleep(2)  # Delay entre downloads
        
        self._imprimir_relatorio(banca)
        return provas_encontradas
    
    def _busca_alternativa(self, banca, max_provas):
        """Busca alternativa usando concursos recentes"""
        logger.info(f"🔄 Buscando concursos recentes de {banca}...")
        
        try:
            url = f"{self.BASE_URL}/organizadoras/{banca}?pagina=2"  # Página 2 pode ter concursos mais antigos
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar todos os links de concursos
                concurso_links = soup.find_all('a', href=lambda x: x and '/concurso/' in x)
                
                provas = []
                
                for link in concurso_links[:10]:  # Limita a 10 concursos
                    concurso_url = link['href']
                    if not concurso_url.startswith('http'):
                        concurso_url = self.BASE_URL + concurso_url
                    
                    # Busca PDFs na página do concurso
                    try:
                        resp = self.session.get(concurso_url, timeout=20)
                        if resp.status_code == 200:
                            soup2 = BeautifulSoup(resp.content, 'html.parser')
                            pdfs = soup2.find_all('a', href=lambda x: x and '.pdf' in x.lower())
                            
                            for pdf in pdfs:
                                if len(provas) >= max_provas:
                                    break
                                
                                pdf_url = pdf['href']
                                if not pdf_url.startswith('http'):
                                    pdf_url = self.BASE_URL + pdf_url
                                
                                texto = pdf.get_text(strip=True)
                                texto_lower = texto.lower()
                                
                                # Filtra apenas provas e gabaritos
                                if any(palavra in texto_lower for palavra in ['prova', 'gabarito', 'caderno', 'questões']):
                                    tipo = 'gabarito' if 'gabarito' in texto_lower else 'prova'
                                    provas.append({
                                        'url': pdf_url,
                                        'titulo': texto[:80],
                                        'tipo': tipo,
                                        'banca': banca
                                    })
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        continue
                    
                    if len(provas) >= max_provas:
                        break
                
                if provas:
                    logger.info(f"✅ Busca alternativa encontrou {len(provas)} arquivos!")
                
                return provas
                
        except Exception as e:
            logger.error(f"❌ Erro na busca alternativa: {e}")
            return []
    
    def _download_pdf(self, pdf_url, titulo, banca, tipo):
        """Baixa um PDF"""
        try:
            titulo_limpo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).strip()
            titulo_limpo = titulo_limpo[:80]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{banca}_{tipo}_{titulo_limpo}_{timestamp}.pdf"
            filepath = self.download_dir / filename
            
            if filepath.exists():
                logger.info(f"⏭️  Já existe: {filename}")
                return str(filepath)
            
            response = self.session.get(pdf_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            size_mb = filepath.stat().st_size / 1024 / 1024
            logger.info(f"✅ Baixado: {filename} ({size_mb:.2f} MB)")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar: {e}")
            self.stats['erros'] += 1
            return None
    
    def _imprimir_relatorio(self, banca):
        """Imprime relatório"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RELATÓRIO - {banca.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Arquivos baixados: {self.stats['baixados']}")
        logger.info(f"❌ Erros: {self.stats['erros']}")
        logger.info(f"📁 Diretório: {self.download_dir.absolute()}")
        logger.info(f"{'='*60}\n")
    
    def coletar_todas_bancas(self, max_por_banca=20):
        """Coleta provas de todas as bancas"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 COLETA DE PROVAS ANTERIORES - TODAS AS BANCAS")
        logger.info(f"{'='*70}\n")
        
        bancas = ['cebraspe', 'fcc', 'fgv']
        
        for i, banca in enumerate(bancas, 1):
            logger.info(f"\n🎯 [{i}/{len(bancas)}] Banca: {banca.upper()}\n")
            self.buscar_provas_banca(banca, max_por_banca)
            
            if i < len(bancas):
                logger.info("\n⏸️  Aguardando 10 segundos...\n")
                time.sleep(10)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 COLETA COMPLETA!")
        logger.info(f"📊 Total baixado: {self.stats['baixados']} arquivos")
        logger.info(f"📁 Diretório: {self.download_dir.absolute()}")
        logger.info(f"{'='*70}\n")


if __name__ == '__main__':
    print("\n🎯 SCRAPER DE PROVAS ANTERIORES")
    print("="*60)
    print()
    
    scraper = PCIProvasAnterioresScraper()
    
    # Tenta coletar provas de todas as bancas
    scraper.coletar_todas_bancas(max_por_banca=15)
