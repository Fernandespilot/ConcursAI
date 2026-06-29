"""
Scraper Focado em Provas e Gabaritos
Busca diretamente em repositórios de provas de concursos
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import logging
from datetime import datetime
from pathlib import Path
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProvasGabaritosScraper:
    """
    Scraper especializado em provas e gabaritos
    Busca em múltiplas fontes especializadas
    """
    
    # Sites que hospedam provas de concursos
    FONTES = {
        'questoes_concursos': {
            'nome': 'Questões de Concursos',
            'base_url': 'https://www.qconcursos.com',
            'urls_bancas': {
                'cebraspe': '/questoes-de-concursos/bancas/cebraspe-cespe/provas',
                'fcc': '/questoes-de-concursos/bancas/fcc/provas',
                'fgv': '/questoes-de-concursos/bancas/fgv/provas'
            }
        },
        'pciconcursos': {
            'nome': 'PCI Concursos',
            'base_url': 'https://www.pciconcursos.com.br',
            'urls_bancas': {
                'cebraspe': '/provas-de-concursos?filter_banca=cebraspe',
                'fcc': '/provas-de-concursos?filter_banca=fcc',
                'fgv': '/provas-de-concursos?filter_banca=fgv'
            }
        },
        'folha_dirigida': {
            'nome': 'Folha Dirigida',
            'base_url': 'https://folhadirigida.com.br',
            'urls_bancas': {
                'cebraspe': '/provas/cebraspe',
                'fcc': '/provas/fcc',
                'fgv': '/provas/fgv'
            }
        }
    }
    
    def __init__(self, download_dir='provas_gabaritos'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        
        self.stats = {
            'provas': 0,
            'gabaritos': 0,
            'erros': 0,
            'total_tentativas': 0
        }
    
    def buscar_provas_google(self, banca, ano=2024, max_resultados=20):
        """
        Busca provas usando Google com operadores específicos
        Exemplo: "prova cebraspe 2024 filetype:pdf"
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 Busca Google - {banca.upper()} - Provas {ano}")
        logger.info(f"{'='*60}\n")
        
        queries = [
            f'"{banca}" prova {ano} filetype:pdf',
            f'"{banca}" gabarito {ano} filetype:pdf',
            f'"{banca}" caderno questões {ano} filetype:pdf',
            f'site:cespe.unb.br OR site:cebraspe.org.br prova filetype:pdf',
            f'site:fgv.br concurso prova {ano} filetype:pdf',
            f'site:fcc.org.br prova {ano} filetype:pdf',
        ]
        
        provas_encontradas = []
        
        for query in queries:
            try:
                # Usando DuckDuckGo como alternativa (não requer API)
                search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
                
                logger.info(f"📡 Buscando: {query}")
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Busca por links que contenham .pdf
                    links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
                    
                    for link in links[:5]:  # Limita por busca
                        try:
                            pdf_url = link.get('href', '')
                            if not pdf_url or pdf_url.startswith('/'):
                                continue
                            
                            # Pega o texto do link
                            texto = link.get_text(strip=True)
                            
                            # Verifica se é prova/gabarito
                            if any(palavra in texto.lower() for palavra in ['prova', 'gabarito', 'questões', 'caderno']):
                                tipo = 'gabarito' if 'gabarito' in texto.lower() else 'prova'
                                
                                provas_encontradas.append({
                                    'url': pdf_url,
                                    'titulo': texto[:100],
                                    'tipo': tipo,
                                    'banca': banca,
                                    'fonte': 'google_search'
                                })
                        except:
                            continue
                
                time.sleep(3)  # Delay entre buscas
                
            except Exception as e:
                logger.warning(f"⚠️ Erro na busca: {e}")
                continue
        
        logger.info(f"✅ Encontrados {len(provas_encontradas)} PDFs via busca")
        return provas_encontradas
    
    def buscar_provas_url_diretas(self, banca, max_provas=15):
        """
        Busca em URLs diretas conhecidas das bancas
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 Busca Direta - {banca.upper()}")
        logger.info(f"{'='*60}\n")
        
        # URLs diretas conhecidas para cada banca
        urls_diretas = {
            'cebraspe': [
                'https://www.cebraspe.org.br/concursos/',
                'https://cespe.unb.br/concursos/',
            ],
            'fcc': [
                'https://www.fcc.org.br/concursos/',
                'https://concursos.fcc.org.br/',
            ],
            'fgv': [
                'https://conhecimento.fgv.br/concursos',
                'https://concursos.fgv.br/',
            ]
        }
        
        provas_encontradas = []
        
        if banca not in urls_diretas:
            logger.warning(f"⚠️ Banca {banca} sem URLs diretas configuradas")
            return []
        
        for url in urls_diretas[banca]:
            try:
                logger.info(f"📡 Acessando: {url}")
                response = self.session.get(url, timeout=30, allow_redirects=True)
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ Status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca todos os links de PDF
                pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
                
                logger.info(f"📄 Encontrados {len(pdf_links)} links de PDF")
                
                for link in pdf_links:
                    try:
                        pdf_url = link.get('href', '')
                        if not pdf_url:
                            continue
                        
                        # Constrói URL completa
                        if not pdf_url.startswith('http'):
                            from urllib.parse import urljoin
                            pdf_url = urljoin(url, pdf_url)
                        
                        # Pega texto do link e elemento pai
                        texto = link.get_text(strip=True)
                        if not texto:
                            parent = link.find_parent()
                            texto = parent.get_text(strip=True) if parent else 'documento'
                        
                        texto_lower = texto.lower()
                        
                        # Filtra APENAS provas e gabaritos (ignora editais)
                        if 'edital' in texto_lower and 'prova' not in texto_lower:
                            continue
                        
                        if any(palavra in texto_lower for palavra in ['prova', 'gabarito', 'caderno', 'questões', 'questoes']):
                            tipo = 'gabarito' if 'gabarito' in texto_lower else 'prova'
                            
                            provas_encontradas.append({
                                'url': pdf_url,
                                'titulo': texto[:100],
                                'tipo': tipo,
                                'banca': banca,
                                'fonte': 'url_direta'
                            })
                            
                            if len(provas_encontradas) >= max_provas:
                                break
                    except:
                        continue
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"⚠️ Erro ao acessar {url}: {e}")
                continue
        
        logger.info(f"✅ Encontrados {len(provas_encontradas)} PDFs de provas/gabaritos")
        return provas_encontradas
    
    def coletar_banca(self, banca, max_provas=15, ano=2024):
        """
        Coleta provas e gabaritos de uma banca usando múltiplas estratégias
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 COLETA COMPLETA - {banca.upper()}")
        logger.info(f"{'='*70}\n")
        
        todas_provas = []
        
        # Estratégia 1: URLs diretas
        logger.info("📍 Estratégia 1: URLs diretas das bancas")
        provas_diretas = self.buscar_provas_url_diretas(banca, max_provas)
        todas_provas.extend(provas_diretas)
        
        # Estratégia 2: Busca Google/DuckDuckGo
        if len(todas_provas) < max_provas:
            logger.info("\n📍 Estratégia 2: Busca web")
            provas_busca = self.buscar_provas_google(banca, ano, max_provas - len(todas_provas))
            todas_provas.extend(provas_busca)
        
        # Remove duplicatas (mesmo URL)
        urls_vistas = set()
        provas_unicas = []
        for prova in todas_provas:
            if prova['url'] not in urls_vistas:
                urls_vistas.add(prova['url'])
                provas_unicas.append(prova)
        
        logger.info(f"\n✅ Total único: {len(provas_unicas)} PDFs")
        
        # Baixa todos
        if provas_unicas:
            self._baixar_lista(provas_unicas)
        else:
            logger.warning("⚠️ Nenhuma prova/gabarito encontrado")
        
        self._imprimir_relatorio(banca)
        return provas_unicas
    
    def _baixar_lista(self, provas):
        """Baixa lista de provas"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📥 INICIANDO DOWNLOADS")
        logger.info(f"{'='*60}\n")
        
        for i, prova in enumerate(provas, 1):
            self.stats['total_tentativas'] += 1
            
            logger.info(f"\n[{i}/{len(provas)}] {prova['tipo'].upper()}")
            logger.info(f"Título: {prova['titulo'][:70]}")
            logger.info(f"Fonte: {prova['fonte']}")
            
            arquivo = self._download_pdf(
                prova['url'],
                prova['titulo'],
                prova['banca'],
                prova['tipo']
            )
            
            if arquivo:
                if prova['tipo'] == 'gabarito':
                    self.stats['gabaritos'] += 1
                else:
                    self.stats['provas'] += 1
            
            time.sleep(3)  # Delay entre downloads
    
    def _download_pdf(self, pdf_url, titulo, banca, tipo):
        """Baixa um PDF"""
        try:
            titulo_limpo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).strip()
            titulo_limpo = titulo_limpo[:60]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{banca}_{tipo}_{titulo_limpo}_{timestamp}.pdf"
            filepath = self.download_dir / filename
            
            if filepath.exists():
                logger.info("⏭️  Já existe")
                return str(filepath)
            
            logger.info(f"⬇️  Baixando: {pdf_url[:80]}")
            
            response = self.session.get(pdf_url, stream=True, timeout=60, allow_redirects=True)
            response.raise_for_status()
            
            # Verifica content-type
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"⚠️  Content-Type: {content_type} (pode não ser PDF)")
            
            # Salva arquivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verifica tamanho
            size_mb = filepath.stat().st_size / 1024 / 1024
            
            if size_mb < 0.01:  # Menor que 10KB
                logger.warning("⚠️  Arquivo muito pequeno, pode estar vazio")
                filepath.unlink()  # Remove
                self.stats['erros'] += 1
                return None
            
            logger.info(f"✅ Sucesso! ({size_mb:.2f} MB)")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            self.stats['erros'] += 1
            return None
    
    def _imprimir_relatorio(self, banca):
        """Relatório por banca"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RELATÓRIO - {banca.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Provas baixadas: {self.stats['provas']}")
        logger.info(f"✅ Gabaritos baixados: {self.stats['gabaritos']}")
        logger.info(f"❌ Erros: {self.stats['erros']}")
        logger.info(f"📁 Diretório: {self.download_dir.absolute()}")
        logger.info(f"{'='*60}\n")
    
    def coletar_todas_bancas(self, max_por_banca=15, ano=2024):
        """Coleta de todas as bancas"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🌐 COLETA GERAL - TODAS AS BANCAS")
        logger.info(f"Foco: PROVAS e GABARITOS de {ano}")
        logger.info(f"{'='*70}\n")
        
        bancas = ['cebraspe', 'fcc', 'fgv']
        
        for i, banca in enumerate(bancas, 1):
            logger.info(f"\n🎯 Banca {i}/{len(bancas)}")
            self.coletar_banca(banca, max_por_banca, ano)
            
            if i < len(bancas):
                logger.info("\n⏸️  Aguardando 15 segundos...\n")
                time.sleep(15)
        
        # Relatório final
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 COLETA COMPLETA!")
        logger.info(f"{'='*70}")
        logger.info(f"✅ Total de provas: {self.stats['provas']}")
        logger.info(f"✅ Total de gabaritos: {self.stats['gabaritos']}")
        logger.info(f"❌ Total de erros: {self.stats['erros']}")
        logger.info(f"📊 Taxa de sucesso: {((self.stats['provas'] + self.stats['gabaritos']) / max(self.stats['total_tentativas'], 1) * 100):.1f}%")
        logger.info(f"📁 Diretório: {self.download_dir.absolute()}")
        logger.info(f"{'='*70}\n")


if __name__ == '__main__':
    import sys
    
    print("\n📚 SCRAPER DE PROVAS E GABARITOS")
    print("Busca focada apenas em provas aplicadas e gabaritos")
    print("="*70)
    print()
    
    scraper = ProvasGabaritosScraper()
    
    if len(sys.argv) > 1:
        banca = sys.argv[1].lower()
        max_provas = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        ano = int(sys.argv[3]) if len(sys.argv) > 3 else 2024
        
        scraper.coletar_banca(banca, max_provas, ano)
    else:
        scraper.coletar_todas_bancas(max_por_banca=15, ano=2024)
