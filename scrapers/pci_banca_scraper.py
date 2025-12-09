"""
Scraper para PCI Concursos - Bancas Organizadoras
Coleta provas de Cebraspe, FCC e FGV do site PCI Concursos
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PCIBancaScraper:
    """Scraper para coletar provas de bancas específicas no PCI Concursos"""
    
    BASE_URL = "https://www.pciconcursos.com.br"
    
    BANCAS = {
        'cebraspe': {
            'url': '/organizadoras/cebraspe',
            'nome': 'Cebraspe',
            'alias': ['cespe', 'cebraspe', 'cespe/cebraspe']
        },
        'fcc': {
            'url': '/organizadoras/fcc',
            'nome': 'FCC',
            'alias': ['fcc', 'fundação carlos chagas']
        },
        'fgv': {
            'url': '/organizadoras/fgv',
            'nome': 'FGV',
            'alias': ['fgv', 'fundação getulio vargas']
        }
    }
    
    def __init__(self, download_dir='editais'):
        """
        Inicializa o scraper
        
        Args:
            download_dir: Diretório para salvar os PDFs
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.stats = {
            'concursos_encontrados': 0,
            'provas_encontradas': 0,
            'provas_baixadas': 0,
            'erros': 0
        }
    
    def get_concursos(self, banca, max_concursos=10):
        """
        Busca concursos de uma banca específica
        
        Args:
            banca: Nome da banca (cebraspe, fcc, fgv)
            max_concursos: Máximo de concursos a processar
            
        Returns:
            Lista de dicionários com informações dos concursos
        """
        if banca not in self.BANCAS:
            logger.error(f"❌ Banca '{banca}' não suportada. Use: {list(self.BANCAS.keys())}")
            return []
        
        banca_info = self.BANCAS[banca]
        url = f"{self.BASE_URL}{banca_info['url']}"
        
        logger.info(f"🔍 Buscando concursos da {banca_info['nome']} em: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontrar lista de concursos
            concursos = []
            concurso_items = soup.find_all('div', class_='ca')[:max_concursos]
            
            if not concurso_items:
                # Tentar outro seletor
                concurso_items = soup.find_all('article', class_='concurso')[:max_concursos]
            
            logger.info(f"📋 Encontrados {len(concurso_items)} concursos")
            
            for item in concurso_items:
                try:
                    # Extrair link do concurso
                    link_tag = item.find('a', href=True)
                    if not link_tag:
                        continue
                    
                    concurso_url = link_tag['href']
                    if not concurso_url.startswith('http'):
                        concurso_url = self.BASE_URL + concurso_url
                    
                    # Extrair título
                    titulo = link_tag.get_text(strip=True)
                    
                    concursos.append({
                        'titulo': titulo,
                        'url': concurso_url,
                        'banca': banca_info['nome']
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar item de concurso: {e}")
                    continue
            
            self.stats['concursos_encontrados'] += len(concursos)
            logger.info(f"✅ {len(concursos)} concursos extraídos com sucesso")
            
            return concursos
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar concursos: {e}")
            self.stats['erros'] += 1
            return []
    
    def get_provas_concurso(self, concurso_url):
        """
        Extrai links de provas de uma página de concurso
        
        Args:
            concurso_url: URL da página do concurso
            
        Returns:
            Lista de dicionários com informações das provas
        """
        logger.info(f"🔍 Buscando provas em: {concurso_url}")
        
        try:
            response = self.session.get(concurso_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            provas = []
            
            # Procurar por links de PDF
            pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
            
            for link in pdf_links:
                try:
                    pdf_url = link['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = self.BASE_URL + pdf_url
                    
                    # Extrair texto do link ou do elemento pai
                    texto = link.get_text(strip=True)
                    if not texto:
                        parent = link.find_parent()
                        texto = parent.get_text(strip=True) if parent else 'prova'
                    
                    # Determinar tipo
                    texto_lower = texto.lower()
                    if 'gabarito' in texto_lower:
                        tipo = 'gabarito'
                    elif 'prova' in texto_lower or 'caderno' in texto_lower or 'questões' in texto_lower or 'questoes' in texto_lower:
                        tipo = 'prova'
                    elif 'edital' in texto_lower:
                        tipo = 'edital'
                    else:
                        tipo = 'documento'
                    
                    provas.append({
                        'url': pdf_url,
                        'titulo': texto[:100],  # Limitar tamanho
                        'tipo': tipo
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar link de PDF: {e}")
                    continue
            
            self.stats['provas_encontradas'] += len(provas)
            logger.info(f"📄 {len(provas)} provas/documentos encontrados")
            
            return provas
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar provas: {e}")
            self.stats['erros'] += 1
            return []
    
    def download_pdf(self, pdf_url, titulo, banca, tipo='prova'):
        """
        Baixa um arquivo PDF
        
        Args:
            pdf_url: URL do PDF
            titulo: Título/nome do arquivo
            banca: Nome da banca
            tipo: Tipo do documento (prova, gabarito, edital)
            
        Returns:
            Caminho do arquivo salvo ou None se falhou
        """
        try:
            # Criar nome de arquivo seguro
            titulo_limpo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).strip()
            titulo_limpo = titulo_limpo[:100]  # Limitar tamanho
            
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"{banca}_{tipo}_{titulo_limpo}_{timestamp}.pdf"
            filepath = self.download_dir / filename
            
            # Verificar se já existe
            if filepath.exists():
                logger.info(f"⏭️ Arquivo já existe: {filename}")
                return str(filepath)
            
            logger.info(f"⬇️ Baixando: {filename}")
            
            response = self.session.get(pdf_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Verificar se é realmente um PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and not pdf_url.lower().endswith('.pdf'):
                logger.warning(f"⚠️ Arquivo pode não ser PDF: {content_type}")
            
            # Salvar arquivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = filepath.stat().st_size / 1024 / 1024  # MB
            logger.info(f"✅ Download concluído: {filename} ({file_size:.2f} MB)")
            
            self.stats['provas_baixadas'] += 1
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar PDF: {e}")
            self.stats['erros'] += 1
            return None
    
    def coletar_banca(self, banca, max_concursos=10, max_provas_por_concurso=5):
        """
        Coleta provas de uma banca específica
        
        Args:
            banca: Nome da banca (cebraspe, fcc, fgv)
            max_concursos: Máximo de concursos a processar
            max_provas_por_concurso: Máximo de provas por concurso
            
        Returns:
            Lista de caminhos dos arquivos baixados
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🕷️ INICIANDO COLETA - {banca.upper()}")
        logger.info(f"{'='*60}\n")
        
        arquivos_baixados = []
        
        # Buscar concursos
        concursos = self.get_concursos(banca, max_concursos)
        
        for i, concurso in enumerate(concursos, 1):
            logger.info(f"\n📚 [{i}/{len(concursos)}] Processando: {concurso['titulo']}")
            
            # Buscar provas do concurso
            provas = self.get_provas_concurso(concurso['url'])
            
            # Limitar número de provas
            provas = provas[:max_provas_por_concurso]
            
            # Priorizar provas e gabaritos
            provas_priorizadas = sorted(provas, key=lambda x: (
                0 if x['tipo'] == 'gabarito' else
                1 if x['tipo'] == 'prova' else
                2 if x['tipo'] == 'edital' else 3
            ))
            
            # Baixar cada prova
            for prova in provas_priorizadas:
                arquivo = self.download_pdf(
                    prova['url'],
                    prova['titulo'],
                    banca,
                    prova['tipo']
                )
                
                if arquivo:
                    arquivos_baixados.append(arquivo)
                
                # Delay entre downloads
                time.sleep(2)
            
            # Delay entre concursos
            if i < len(concursos):
                logger.info("⏸️ Aguardando 3 segundos...")
                time.sleep(3)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ COLETA FINALIZADA - {banca.upper()}")
        logger.info(f"📊 Estatísticas:")
        logger.info(f"   - Concursos processados: {len(concursos)}")
        logger.info(f"   - Provas baixadas: {len(arquivos_baixados)}")
        logger.info(f"   - Erros: {self.stats['erros']}")
        logger.info(f"{'='*60}\n")
        
        return arquivos_baixados
    
    def coletar_todas(self, max_concursos=10, max_provas_por_concurso=5):
        """
        Coleta provas de todas as bancas
        
        Args:
            max_concursos: Máximo de concursos por banca
            max_provas_por_concurso: Máximo de provas por concurso
            
        Returns:
            Dict com lista de arquivos por banca
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 INICIANDO COLETA DE TODAS AS BANCAS")
        logger.info(f"{'='*70}\n")
        
        resultados = {}
        
        for banca in self.BANCAS.keys():
            arquivos = self.coletar_banca(banca, max_concursos, max_provas_por_concurso)
            resultados[banca] = arquivos
            
            # Delay entre bancas
            logger.info("⏸️ Aguardando 5 segundos antes da próxima banca...\n")
            time.sleep(5)
        
        total_arquivos = sum(len(arqs) for arqs in resultados.values())
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 COLETA COMPLETA!")
        logger.info(f"📊 Resumo Geral:")
        logger.info(f"   - Total de bancas: {len(resultados)}")
        logger.info(f"   - Total de arquivos: {total_arquivos}")
        logger.info(f"   - Diretório: {self.download_dir.absolute()}")
        for banca, arquivos in resultados.items():
            logger.info(f"   - {banca.upper()}: {len(arquivos)} arquivos")
        logger.info(f"{'='*70}\n")
        
        return resultados


# Funções auxiliares para uso direto
def coletar_cebraspe(max_concursos=10):
    """Coleta provas do Cebraspe via PCI Concursos"""
    scraper = PCIBancaScraper()
    return scraper.coletar_banca('cebraspe', max_concursos)


def coletar_fcc(max_concursos=10):
    """Coleta provas da FCC via PCI Concursos"""
    scraper = PCIBancaScraper()
    return scraper.coletar_banca('fcc', max_concursos)


def coletar_fgv(max_concursos=10):
    """Coleta provas da FGV via PCI Concursos"""
    scraper = PCIBancaScraper()
    return scraper.coletar_banca('fgv', max_concursos)


def coletar_todas_bancas(max_concursos=10):
    """Coleta provas de todas as bancas via PCI Concursos"""
    scraper = PCIBancaScraper()
    return scraper.coletar_todas(max_concursos)


if __name__ == '__main__':
    # Teste do scraper
    print("🧪 Testando PCIBancaScraper...")
    print("="*60)
    
    scraper = PCIBancaScraper()
    
    # Testar com 2 concursos da Cebraspe
    arquivos = scraper.coletar_banca('cebraspe', max_concursos=2, max_provas_por_concurso=3)
    
    print(f"\n✅ Teste concluído!")
    print(f"📁 {len(arquivos)} arquivos baixados")
    print(f"📂 Diretório: {scraper.download_dir.absolute()}")
