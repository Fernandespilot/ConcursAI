"""
Scraper de Provas Anteriores PCI Concursos
Busca e baixa provas de 2023-2025 por banca
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import re
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('provas_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Diretórios
PROVAS_DIR = Path("provas")
PROVAS_DIR.mkdir(exist_ok=True)

# Links principais das bancas no PCI Concursos
BANCA_LINKS = {
    "cebraspe": "https://www.pciconcursos.com.br/provas/cebraspe",
    "fcc": "https://www.pciconcursos.com.br/provas/fcc",
    "fgv": "https://www.pciconcursos.com.br/provas/fgv"
}


class ProvasScraperPCI:
    """Scraper especializado em provas anteriores do PCI Concursos"""
    
    def __init__(self, anos_filtro=[2023, 2024, 2025]):
        self.anos_filtro = anos_filtro
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9',
        })
        
        self.stats = {
            'total_encontrados': 0,
            'total_baixados': 0,
            'erros': 0,
            'por_banca': {}
        }
    
    def extrair_ano(self, texto):
        """Extrai ano do texto (2023, 2024 ou 2025)"""
        # Procura por padrões de ano
        match = re.search(r'20(23|24|25)', texto)
        if match:
            return int(match.group(0))
        return None
    
    def scrape_provas_banca(self, banca, base_url, max_provas=20):
        """
        Scraping de provas dos últimos anos por banca
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🎯 Buscando Provas - {banca.upper()} (Anos: {self.anos_filtro})")
        logger.info(f"{'='*70}")
        
        banca_dir = PROVAS_DIR / banca
        banca_dir.mkdir(exist_ok=True)
        
        self.stats['por_banca'][banca] = {'encontrados': 0, 'baixados': 0}
        
        try:
            logger.info(f"📡 Acessando: {base_url}")
            response = self.session.get(base_url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ Erro HTTP {response.status_code}")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Busca por links de provas na TABELA
            provas_encontradas = []
            
            # A página tem uma tabela com as provas
            # Procura por linhas da tabela (tr) que contêm informações
            tabela_rows = soup.find_all('tr')
            
            logger.info(f"📋 Linhas de tabela encontradas: {len(tabela_rows)}")
            
            for row in tabela_rows:
                try:
                    # Extrai células da linha
                    colunas = row.find_all('td')
                    
                    if len(colunas) < 4:
                        continue
                    
                    # Coluna 1: Link da prova (nome do cargo)
                    link_prova = colunas[0].find('a')
                    if not link_prova:
                        continue
                    
                    titulo = link_prova.get_text(strip=True)
                    href_prova = link_prova.get('href', '')
                    
                    # Coluna 2: Ano
                    ano_texto = colunas[1].get_text(strip=True)
                    ano = self.extrair_ano(ano_texto)
                    
                    # Coluna 3: Órgão
                    orgao = colunas[2].get_text(strip=True)
                    
                    # Coluna 4: Instituição (banca)
                    instituicao = colunas[3].get_text(strip=True)
                    
                    # Filtra por ano
                    if not ano or ano not in self.anos_filtro:
                        continue
                    
                    # Monta título completo
                    titulo_completo = f"{titulo} - {orgao} ({ano})"
                    
                    # Adiciona link para buscar PDFs depois
                    if href_prova:
                        url_completa = urljoin(base_url, href_prova)
                        provas_encontradas.append({
                            'url': url_completa,
                            'titulo': titulo_completo,
                            'banca': banca,
                            'ano': ano,
                            'tipo': 'prova',
                            'orgao': orgao,
                            'cargo': titulo
                        })
                        
                except Exception as e:
                    continue
            
            logger.info(f"📋 Provas dos anos {self.anos_filtro} encontradas: {len(provas_encontradas)}")
            
            # Agora busca os PDFs de cada prova encontrada
            logger.info(f"\n🔍 Buscando PDFs das provas...\n")
            
            provas_com_pdf = []
            
            for i, prova_info in enumerate(provas_encontradas[:max_provas], 1):
                logger.info(f"  [{i}/{min(len(provas_encontradas), max_provas)}] {prova_info['cargo'][:40]}... ({prova_info['ano']})")
                
                # Busca PDFs na página da prova
                pdfs = self._buscar_pdfs_concurso(prova_info['url'], banca, prova_info['ano'], prova_info['titulo'])
                
                if pdfs:
                    provas_com_pdf.extend(pdfs)
                    logger.info(f"       ✓ {len(pdfs)} PDF(s) encontrado(s)")
                
                time.sleep(1)  # Delay entre páginas
            
            provas_encontradas = provas_com_pdf
            
            # Remove duplicatas (mesmo URL)
            urls_unicas = set()
            provas_unicas = []
            for prova in provas_encontradas:
                if prova['url'] not in urls_unicas:
                    urls_unicas.add(prova['url'])
                    provas_unicas.append(prova)
            
            logger.info(f"\n✅ Total de provas encontradas: {len(provas_unicas)}")
            self.stats['total_encontrados'] += len(provas_unicas)
            self.stats['por_banca'][banca]['encontrados'] = len(provas_unicas)
            
            # Baixa as provas
            if provas_unicas:
                logger.info(f"\n📥 Iniciando downloads...\n")
                
                for i, prova_info in enumerate(provas_unicas[:max_provas], 1):
                    logger.info(f"[{i}/{min(len(provas_unicas), max_provas)}] {prova_info['tipo'].upper()}: {prova_info['titulo'][:50]}...")
                    
                    sucesso = self.download_prova(prova_info, banca_dir)
                    if sucesso:
                        self.stats['total_baixados'] += 1
                        self.stats['por_banca'][banca]['baixados'] += 1
                    
                    time.sleep(2)  # Delay anti-ban
            else:
                logger.warning(f"⚠️  Nenhuma prova dos anos {self.anos_filtro} encontrada")
            
            self._relatorio_banca(banca)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {banca}: {e}")
            self.stats['erros'] += 1
    
    def _buscar_pdfs_concurso(self, url, banca, ano, titulo_concurso):
        """Busca PDFs em uma página específica de concurso"""
        try:
            response = self.session.get(url, timeout=20)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            pdfs = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.pdf' in href.lower():
                    url_completa = urljoin(url, href)
                    texto = link.get_text(strip=True)
                    
                    # Identifica tipo
                    texto_lower = texto.lower()
                    if 'gabarito' in texto_lower:
                        tipo = 'gabarito'
                    elif 'prova' in texto_lower or 'caderno' in texto_lower or 'questões' in texto_lower:
                        tipo = 'prova'
                    else:
                        tipo = 'prova'  # Assume prova se não identificar
                    
                    pdfs.append({
                        'url': url_completa,
                        'titulo': f"{titulo_concurso} - {texto}" if texto else titulo_concurso,
                        'banca': banca,
                        'ano': ano,
                        'tipo': tipo
                    })
            
            return pdfs
            
        except Exception as e:
            logger.warning(f"  ⚠️  Erro ao buscar PDFs: {e}")
            return []
    
    def download_prova(self, prova_info, dir_path):
        """Baixa um PDF de prova"""
        try:
            # Nome seguro para arquivo
            titulo_limpo = re.sub(r'[^\w\s-]', '', prova_info['titulo'])
            titulo_limpo = titulo_limpo[:60].strip()
            
            filename = f"{prova_info['banca']}_{prova_info['ano']}_{prova_info['tipo']}_{titulo_limpo}.pdf"
            filepath = dir_path / filename
            
            # Verifica se já existe
            if filepath.exists():
                logger.info(f"  ⏭️  Já existe")
                return True
            
            # Download
            response = self.session.get(prova_info['url'], stream=True, timeout=60)
            response.raise_for_status()
            
            # Verifica se é realmente PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and not prova_info['url'].endswith('.pdf'):
                logger.warning(f"  ⚠️  Pode não ser PDF: {content_type}")
            
            # Salva arquivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            size_mb = filepath.stat().st_size / 1024 / 1024
            logger.info(f"  ✅ Baixado ({size_mb:.2f} MB)")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Erro no download: {e}")
            self.stats['erros'] += 1
            return False
    
    def _relatorio_banca(self, banca):
        """Relatório por banca"""
        stats_banca = self.stats['por_banca'][banca]
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 RELATÓRIO - {banca.upper()}")
        logger.info(f"{'='*70}")
        logger.info(f"🔍 Provas encontradas: {stats_banca['encontrados']}")
        logger.info(f"✅ Provas baixadas: {stats_banca['baixados']}")
        logger.info(f"📁 Diretório: {PROVAS_DIR / banca}")
        logger.info(f"{'='*70}\n")
    
    def coletar_todas_bancas(self, max_por_banca=20):
        """Coleta provas de todas as bancas"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 COLETA DE PROVAS - TODAS AS BANCAS")
        logger.info(f"   Anos: {', '.join(map(str, self.anos_filtro))}")
        logger.info(f"{'='*70}\n")
        
        for i, (banca, url) in enumerate(BANCA_LINKS.items(), 1):
            logger.info(f"\n🎯 [{i}/{len(BANCA_LINKS)}] {banca.upper()}\n")
            self.scrape_provas_banca(banca, url, max_por_banca)
            
            if i < len(BANCA_LINKS):
                logger.info("\n⏸️  Aguardando 10 segundos...\n")
                time.sleep(10)
        
        self._relatorio_final()
    
    def _relatorio_final(self):
        """Relatório final completo"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 COLETA COMPLETA!")
        logger.info(f"{'='*70}")
        logger.info(f"📊 Estatísticas Gerais:")
        logger.info(f"   Total encontrado: {self.stats['total_encontrados']}")
        logger.info(f"   Total baixado: {self.stats['total_baixados']}")
        logger.info(f"   Erros: {self.stats['erros']}")
        logger.info(f"\n📊 Por Banca:")
        
        for banca, stats in self.stats['por_banca'].items():
            logger.info(f"   {banca.upper()}: {stats['baixados']} baixados de {stats['encontrados']} encontrados")
        
        logger.info(f"\n📁 Diretório: {PROVAS_DIR.absolute()}")
        logger.info(f"{'='*70}\n")


# Funções auxiliares
def coletar_provas_banca(banca, anos=[2023, 2024, 2025], max_provas=20):
    """Coleta provas de uma banca específica"""
    scraper = ProvasScraperPCI(anos_filtro=anos)
    if banca in BANCA_LINKS:
        scraper.scrape_provas_banca(banca, BANCA_LINKS[banca], max_provas)
    else:
        logger.error(f"Banca {banca} não suportada. Use: {list(BANCA_LINKS.keys())}")


def coletar_todas_provas(anos=[2023, 2024, 2025], max_por_banca=20):
    """Coleta provas de todas as bancas"""
    scraper = ProvasScraperPCI(anos_filtro=anos)
    scraper.coletar_todas_bancas(max_por_banca)


if __name__ == '__main__':
    import sys
    
    print("\n📚 SCRAPER DE PROVAS ANTERIORES PCI CONCURSOS")
    print("="*70)
    print()
    
    if len(sys.argv) > 1:
        banca = sys.argv[1].lower()
        max_provas = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        
        if banca == 'todas':
            coletar_todas_provas(max_por_banca=max_provas)
        else:
            coletar_provas_banca(banca, max_provas=max_provas)
    else:
        # Modo padrão: coleta todas
        coletar_todas_provas(max_por_banca=15)
