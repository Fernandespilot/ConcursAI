#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔽 BAIXADOR DE PROVAS PCI CONCURSOS
====================================
Baixa provas do PCI Concursos e processa para análise de bancas
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import json
from datetime import datetime
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
import pandas as pd

class BaixadorProvasPCI:
    def __init__(self, provas_dir="provas"):
        self.provas_dir = Path(provas_dir)
        self.provas_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Referer': 'https://www.pciconcursos.com.br/'
        })
        
        self.stats = {
            'concursos_encontrados': 0,
            'provas_baixadas': 0,
            'provas_falhadas': 0,
            'bancas': {}
        }
    
    def buscar_concursos(self, banca=None, area=None, max_paginas=5):
        """Busca concursos no PCI"""
        
        print(f"\n🔍 BUSCANDO CONCURSOS NO PCI")
        print(f"   Banca: {banca or 'Todas'}")
        print(f"   Área: {area or 'Todas'}")
        print(f"   Max páginas: {max_paginas}")
        
        concursos = []
        
        # URL base do PCI
        base_url = "https://www.pciconcursos.com.br/concursos"
        
        # Construir filtros
        filtros = []
        if banca:
            filtros.append(f"banca={banca.lower()}")
        if area:
            filtros.append(f"area={area.lower()}")
        
        for pagina in range(1, max_paginas + 1):
            try:
                url = f"{base_url}?page={pagina}"
                if filtros:
                    url += "&" + "&".join(filtros)
                
                print(f"\n📄 Página {pagina}: {url}")
                
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    print(f"   ⚠️ Status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Encontrar concursos na página
                concursos_page = self._extrair_concursos_pagina(soup, url)
                concursos.extend(concursos_page)
                
                print(f"   ✅ {len(concursos_page)} concursos encontrados")
                
                time.sleep(2)  # Respeitar rate limit
                
            except Exception as e:
                print(f"   ❌ Erro na página {pagina}: {e}")
                continue
        
        self.stats['concursos_encontrados'] = len(concursos)
        print(f"\n✅ Total de concursos encontrados: {len(concursos)}")
        
        return concursos
    
    def _extrair_concursos_pagina(self, soup, url_base):
        """Extrai informações dos concursos de uma página"""
        
        concursos = []
        
        # Buscar diferentes estruturas HTML do PCI
        # Estrutura 1: Divs com classe 'ca'
        concursos_divs = soup.find_all('div', class_='ca')
        
        if not concursos_divs:
            # Estrutura 2: Artigos
            concursos_divs = soup.find_all('article')
        
        if not concursos_divs:
            # Estrutura 3: Qualquer div com link
            concursos_divs = soup.find_all('div', class_=re.compile(r'concurso|item'))
        
        for div in concursos_divs:
            try:
                concurso = {}
                
                # Extrair título
                titulo_elem = div.find(['h3', 'h2', 'h4', 'a'])
                if titulo_elem:
                    concurso['titulo'] = titulo_elem.get_text(strip=True)
                    
                    # Extrair link
                    if titulo_elem.name == 'a':
                        concurso['url'] = urljoin(url_base, titulo_elem.get('href', ''))
                    else:
                        link = div.find('a')
                        if link:
                            concurso['url'] = urljoin(url_base, link.get('href', ''))
                
                # Extrair informações adicionais
                texto_completo = div.get_text()
                
                # Extrair banca
                banca_match = re.search(r'(CESPE|CEBRASPE|FCC|FGV|VUNESP|CESGRANRIO|FUNDATEC|IBFC|AOCP|QUADRIX|IDECAN)', 
                                       texto_completo, re.IGNORECASE)
                if banca_match:
                    concurso['banca'] = banca_match.group(1).upper()
                    if concurso['banca'] == 'CESPE':
                        concurso['banca'] = 'CEBRASPE'
                
                # Extrair órgão
                if '|' in texto_completo:
                    partes = texto_completo.split('|')
                    if len(partes) > 0:
                        concurso['orgao'] = partes[0].strip()
                
                # Extrair número de vagas
                vagas_match = re.search(r'(\d+)\s*vagas?', texto_completo, re.IGNORECASE)
                if vagas_match:
                    concurso['vagas'] = int(vagas_match.group(1))
                
                # Extrair salário
                salario_match = re.search(r'R\$\s*([\d.,]+)', texto_completo)
                if salario_match:
                    concurso['salario'] = salario_match.group(0)
                
                # Adicionar data de coleta
                concurso['data_coleta'] = datetime.now().strftime('%Y-%m-%d')
                
                if concurso.get('titulo') and concurso.get('url'):
                    concursos.append(concurso)
                
            except Exception as e:
                print(f"      ⚠️ Erro ao processar concurso: {e}")
                continue
        
        return concursos
    
    def baixar_provas_concurso(self, concurso):
        """Baixa as provas de um concurso específico"""
        
        print(f"\n📥 Baixando provas: {concurso.get('titulo', 'Sem título')}")
        
        if 'url' not in concurso:
            print("   ⚠️ URL não encontrada")
            return []
        
        try:
            response = self.session.get(concurso['url'], timeout=15)
            
            if response.status_code != 200:
                print(f"   ⚠️ Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar links de PDF na página do concurso
            pdf_links = []
            
            # Método 1: Links com texto "prova", "gabarito", "caderno"
            for link in soup.find_all('a', href=True):
                texto = link.get_text().lower()
                href = link.get('href', '')
                
                if any(palavra in texto for palavra in ['prova', 'gabarito', 'caderno', 'questões']):
                    if href.endswith('.pdf') or '/download/' in href:
                        pdf_links.append({
                            'url': urljoin(concurso['url'], href),
                            'tipo': self._identificar_tipo_documento(texto),
                            'titulo': link.get_text(strip=True)
                        })
            
            # Método 2: Todos os links .pdf
            if not pdf_links:
                for link in soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE)):
                    pdf_links.append({
                        'url': urljoin(concurso['url'], link.get('href')),
                        'tipo': 'prova',
                        'titulo': link.get_text(strip=True) or 'Documento'
                    })
            
            print(f"   📄 {len(pdf_links)} PDFs encontrados")
            
            # Baixar cada PDF
            provas_baixadas = []
            
            for i, pdf_info in enumerate(pdf_links, 1):
                prova_path = self._baixar_pdf(pdf_info, concurso, i)
                if prova_path:
                    provas_baixadas.append({
                        'arquivo': str(prova_path),
                        'tipo': pdf_info['tipo'],
                        'titulo': pdf_info['titulo'],
                        'banca': concurso.get('banca', 'desconhecida'),
                        'orgao': concurso.get('orgao', ''),
                        'data_coleta': concurso.get('data_coleta', '')
                    })
            
            return provas_baixadas
            
        except Exception as e:
            print(f"   ❌ Erro ao baixar provas: {e}")
            self.stats['provas_falhadas'] += 1
            return []
    
    def _identificar_tipo_documento(self, texto):
        """Identifica o tipo de documento pelo texto"""
        texto = texto.lower()
        
        if 'gabarito' in texto:
            return 'gabarito'
        elif 'caderno' in texto or 'prova' in texto or 'questões' in texto:
            return 'prova'
        else:
            return 'documento'
    
    def _baixar_pdf(self, pdf_info, concurso, numero):
        """Baixa um PDF específico"""
        
        try:
            banca = concurso.get('banca', 'desconhecida').lower()
            
            # Criar diretório da banca
            banca_dir = self.provas_dir / banca
            banca_dir.mkdir(exist_ok=True)
            
            # Gerar nome do arquivo
            titulo_limpo = re.sub(r'[^\w\s-]', '', concurso.get('titulo', 'prova'))
            titulo_limpo = re.sub(r'\s+', '_', titulo_limpo)[:50]
            
            tipo = pdf_info['tipo']
            ano = datetime.now().year
            
            filename = f"{banca}_{titulo_limpo}_{tipo}_{ano}_{numero}.pdf"
            filepath = banca_dir / filename
            
            # Verificar se já existe
            if filepath.exists():
                print(f"      ⏩ Já existe: {filename}")
                return filepath
            
            # Baixar PDF
            print(f"      ⬇️ Baixando: {filename}")
            
            response = self.session.get(pdf_info['url'], timeout=30, stream=True)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verificar tamanho
                tamanho = os.path.getsize(filepath)
                
                if tamanho < 1024:  # Menos de 1KB
                    print(f"      ⚠️ Arquivo muito pequeno ({tamanho} bytes), removendo")
                    filepath.unlink()
                    return None
                
                print(f"      ✅ Baixado: {tamanho/1024:.1f} KB")
                self.stats['provas_baixadas'] += 1
                
                # Atualizar stats de banca
                if banca not in self.stats['bancas']:
                    self.stats['bancas'][banca] = 0
                self.stats['bancas'][banca] += 1
                
                return filepath
            
            else:
                print(f"      ⚠️ Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"      ❌ Erro ao baixar PDF: {e}")
            self.stats['provas_falhadas'] += 1
            return None
    
    def processar_provas(self):
        """Processa todas as provas baixadas em chunks"""
        
        print("\n\n🔄 PROCESSANDO PROVAS PARA CHUNKS")
        print("=" * 60)
        
        # Importar o processador de PDFs
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from processar_pdfs_chunks import processar_todos_pdfs
            
            # Processar todas as provas
            df_chunks = processar_todos_pdfs(str(self.provas_dir))
            
            return df_chunks
            
        except ImportError:
            print("⚠️ Módulo de processamento não encontrado")
            print("   Execute: python processar_pdfs_chunks.py")
            return None
        except Exception as e:
            print(f"❌ Erro ao processar: {e}")
            return None
    
    def salvar_relatorio(self):
        """Salva relatório da coleta"""
        
        relatorio = {
            'data': datetime.now().isoformat(),
            'estatisticas': self.stats,
            'bancas': list(self.stats['bancas'].keys())
        }
        
        with open('relatorio_coleta_pci.json', 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        print("\n\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)
        print(f"Concursos encontrados: {self.stats['concursos_encontrados']}")
        print(f"Provas baixadas: {self.stats['provas_baixadas']}")
        print(f"Provas com erro: {self.stats['provas_falhadas']}")
        print(f"\nProvas por banca:")
        for banca, count in sorted(self.stats['bancas'].items()):
            print(f"   {banca.upper()}: {count} provas")
        print("\n✅ Relatório salvo em: relatorio_coleta_pci.json")


def main():
    """Função principal"""
    
    print("=" * 60)
    print("🔽 BAIXADOR DE PROVAS PCI CONCURSOS")
    print("=" * 60)
    
    baixador = BaixadorProvasPCI()
    
    # Configurações - FOCO NAS 3 PRINCIPAIS BANCAS
    BANCAS = ['CEBRASPE', 'FGV', 'FCC']
    MAX_PAGINAS = 10  # Mais páginas para coletar mais provas
    MAX_CONCURSOS_POR_BANCA = 30  # 30 concursos por banca = ~90 concursos total
    
    # Buscar concursos de cada banca
    todos_concursos = []
    
    for banca in BANCAS:
        print(f"\n\n{'='*60}")
        print(f"🎯 BANCA: {banca}")
        print(f"{'='*60}")
        
        concursos = baixador.buscar_concursos(banca=banca, max_paginas=MAX_PAGINAS)
        todos_concursos.extend(concursos)
        
        print(f"\n📥 Baixando provas de {min(len(concursos), MAX_CONCURSOS_POR_BANCA)} concursos...")
        
        # Baixar provas dos concursos encontrados
        for i, concurso in enumerate(concursos[:MAX_CONCURSOS_POR_BANCA], 1):
            print(f"\n[{i}/{min(len(concursos), MAX_CONCURSOS_POR_BANCA)}] {concurso.get('titulo', 'Sem título')[:60]}")
            baixador.baixar_provas_concurso(concurso)
            time.sleep(1.5)  # Reduzido para 1.5s
    
    # Salvar relatório
    baixador.salvar_relatorio()
    
    # Perguntar se quer processar
    print("\n\n" + "=" * 60)
    resposta = input("\n🤔 Deseja processar as provas em chunks agora? (s/n): ")
    
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        df_chunks = baixador.processar_provas()
        
        if df_chunks is not None:
            print(f"\n✅ Processamento concluído!")
            print(f"   Total de chunks: {len(df_chunks)}")
            print(f"   Arquivo: concursos_chunks.csv")
            
            # Indexar no ChromaDB
            resposta_indexar = input("\n🤔 Deseja indexar no ChromaDB agora? (s/n): ")
            
            if resposta_indexar.lower() in ['s', 'sim', 'y', 'yes']:
                print("\n🔄 Indexando no ChromaDB...")
                os.system("python -m modules.concurso_embeddings")
    
    print("\n\n✅ PROCESSO CONCLUÍDO!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
