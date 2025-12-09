#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕷️ SCRAPER PCI CONCURSOS - VERSÃO ATUAL 2024
==============================================
Scraper atualizado para coletar dados reais do PCI Concursos
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
import logging
import re
import json
import os
from urllib.parse import urljoin, urlparse

class PCIConcursosScraperAtual:
    def __init__(self, delay_range=(1, 3)):
        """Scraper atualizado para PCI Concursos"""
        self.base_url = "https://www.pciconcursos.com.br"
        self.delay_range = delay_range
        self.session = requests.Session()
        
        # Headers realísticos
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0'
        })
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.concursos_coletados = []
        self.editais_coletados = []
    
    def _wait(self):
        """Aguarda entre requests para evitar bloqueio"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def _safe_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Request seguro com retry e tratamento de erros"""
        for attempt in range(max_retries):
            try:
                self._wait()
                response = self.session.get(url, timeout=20)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    wait_time = 30 * (attempt + 1)
                    self.logger.warning(f"Rate limit - aguardando {wait_time}s")
                    time.sleep(wait_time)
                elif response.status_code in [403, 404]:
                    self.logger.warning(f"Acesso negado ou não encontrado: {url}")
                    return None
                else:
                    self.logger.warning(f"Status {response.status_code} para {url}")
                    
            except requests.RequestException as e:
                self.logger.error(f"Erro na tentativa {attempt + 1}: {e}")
                time.sleep(5 * (attempt + 1))
        
        return None
    
    def coletar_concursos_lista(self, limite_paginas: int = 10) -> List[Dict]:
        """Coleta lista de concursos da página principal"""
        self.logger.info("🚀 Iniciando coleta de concursos do PCI...")
        
        todos_concursos = []
        
        for pagina in range(1, limite_paginas + 1):
            url = f"{self.base_url}/concursos?page={pagina}"
            
            self.logger.info(f"📄 Processando página {pagina}...")
            
            response = self._safe_request(url)
            if not response:
                self.logger.warning(f"Falha ao acessar página {pagina}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar concursos na página
            concursos_pagina = self._extrair_concursos_pagina(soup)
            
            if not concursos_pagina:
                self.logger.warning(f"Nenhum concurso encontrado na página {pagina}")
                break
            
            todos_concursos.extend(concursos_pagina)
            self.logger.info(f"✅ Página {pagina}: {len(concursos_pagina)} concursos (+{len(todos_concursos)} total)")
            
            # Pausa entre páginas
            time.sleep(2)
        
        self.logger.info(f"🎉 Coleta finalizada! Total: {len(todos_concursos)} concursos")
        return todos_concursos
    
    def _extrair_concursos_pagina(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrai concursos de uma página"""
        concursos = []
        
        # Tentar diferentes seletores para encontrar concursos
        seletores_possivel = [
            '.ca',  # Classe principal do PCI
            '.item-concurso',
            '.concurso-item',
            'article',
            '.card',
            'div[class*="concurso"]',
            'tr[class*="ca"]'
        ]
        
        items_encontrados = []
        
        for seletor in seletores_possivel:
            items = soup.select(seletor)
            if items:
                self.logger.info(f"✅ Encontrados {len(items)} itens com seletor: {seletor}")
                items_encontrados = items
                break
        
        if not items_encontrados:
            # Fallback: buscar por links que contenham "concurso"
            links_concurso = soup.find_all('a', href=re.compile(r'/concurso/'))
            self.logger.info(f"🔍 Fallback: {len(links_concurso)} links de concurso encontrados")
            
            for link in links_concurso[:20]:  # Limitar para evitar duplicatas
                concurso = self._extrair_dados_basicos_link(link)
                if concurso:
                    concursos.append(concurso)
        else:
            # Processar items encontrados
            for item in items_encontrados:
                concurso = self._extrair_dados_concurso(item)
                if concurso:
                    concursos.append(concurso)
        
        return concursos
    
    def _extrair_dados_basicos_link(self, link) -> Optional[Dict]:
        """Extrai dados básicos de um link de concurso"""
        try:
            href = link.get('href', '')
            titulo = link.get_text(strip=True)
            
            if not href or not titulo:
                return None
            
            # Extrair ID do concurso
            id_match = re.search(r'/concurso/([0-9]+)', href)
            concurso_id = id_match.group(1) if id_match else None
            
            return {
                'id': concurso_id,
                'titulo': titulo,
                'link': urljoin(self.base_url, href),
                'orgao': '',
                'vagas': 0,
                'localizacao': '',
                'salario': '',
                'escolaridade': '',
                'inscricoes': '',
                'status': 'Ativo',
                'fonte': 'PCI Concursos',
                'data_coleta': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados do link: {e}")
            return None
    
    def _extrair_dados_concurso(self, item) -> Optional[Dict]:
        """Extrai dados completos de um item de concurso"""
        try:
            concurso = {
                'id': '',
                'titulo': '',
                'orgao': '',
                'vagas': 0,
                'localizacao': '',
                'salario': '',
                'salario_numerico': 0.0,
                'escolaridade': '',
                'inscricoes': '',
                'status': 'Ativo',
                'link': '',
                'fonte': 'PCI Concursos',
                'data_coleta': datetime.now().isoformat()
            }
            
            # Buscar link e título
            link_elem = item.find('a', href=re.compile(r'/concurso/'))
            if link_elem:
                concurso['link'] = urljoin(self.base_url, link_elem.get('href', ''))
                concurso['titulo'] = link_elem.get_text(strip=True)
                
                # Extrair ID
                id_match = re.search(r'/concurso/([0-9]+)', concurso['link'])
                if id_match:
                    concurso['id'] = id_match.group(1)
            
            # Buscar informações adicionais no item
            texto_completo = item.get_text()
            
            # Extrair órgão (geralmente está em destaque)
            orgao_elem = item.find(['b', 'strong', 'span'], class_=re.compile(r'.*orgao.*|.*instituicao.*'))
            if orgao_elem:
                concurso['orgao'] = orgao_elem.get_text(strip=True)
            else:
                # Tentar extrair do texto
                linhas = [line.strip() for line in texto_completo.split('\n') if line.strip()]
                if len(linhas) > 1:
                    concurso['orgao'] = linhas[1]  # Segunda linha geralmente é o órgão
            
            # Extrair localização
            local_match = re.search(r'Local:?\s*([^\\n]+)', texto_completo)
            if local_match:
                concurso['localizacao'] = local_match.group(1).strip()
            
            # Extrair vagas
            vagas_match = re.search(r'(\\d+)\s*vaga[s]?', texto_completo, re.IGNORECASE)
            if vagas_match:
                concurso['vagas'] = int(vagas_match.group(1))
            
            # Extrair salário
            salario_match = re.search(r'R\\$\\s*([0-9,.]+)', texto_completo)
            if salario_match:
                concurso['salario'] = salario_match.group(0)
                concurso['salario_numerico'] = self._parse_salary(salario_match.group(1))
            
            # Extrair escolaridade
            escolaridade_patterns = [
                r'(Ensino\\s+(?:Fundamental|Médio|Superior))',
                r'(Nível\\s+(?:Fundamental|Médio|Superior))',
                r'(Graduação|Pós-graduação|Mestrado|Doutorado)'
            ]
            
            for pattern in escolaridade_patterns:
                escol_match = re.search(pattern, texto_completo, re.IGNORECASE)
                if escol_match:
                    concurso['escolaridade'] = escol_match.group(1)
                    break
            
            # Validar se tem dados mínimos
            if concurso['titulo'] and (concurso['orgao'] or concurso['id']):
                return concurso
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados do concurso: {e}")
            return None
    
    def _parse_salary(self, salary_str: str) -> float:
        """Converte string de salário para float"""
        try:
            # Remover caracteres não numéricos exceto pontos e vírgulas
            clean = re.sub(r'[^0-9.,]', '', salary_str)
            
            # Converter formato brasileiro (1.234,56) para float
            if ',' in clean:
                # Separar milhares e decimais
                parts = clean.split(',')
                if len(parts) == 2:
                    inteira = parts[0].replace('.', '')
                    decimal = parts[1]
                    valor = float(f"{inteira}.{decimal}")
                else:
                    valor = float(clean.replace('.', '').replace(',', '.'))
            else:
                valor = float(clean.replace('.', ''))
            
            return valor
            
        except:
            return 0.0
    
    def coletar_detalhes_concurso(self, concurso_url: str) -> Optional[Dict]:
        """Coleta detalhes completos de um concurso específico"""
        try:
            response = self._safe_request(concurso_url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            detalhes = {
                'url': concurso_url,
                'conteudo_completo': '',
                'editais': [],
                'inscricao_inicio': '',
                'inscricao_fim': '',
                'prova_data': '',
                'taxa_inscricao': '',
                'requisitos': '',
                'atribuicoes': ''
            }
            
            # Extrair conteúdo principal
            content_areas = soup.find_all(['div', 'section'], class_=re.compile(r'.*content.*|.*main.*|.*detalhes.*'))
            if content_areas:
                detalhes['conteudo_completo'] = content_areas[0].get_text(strip=True)
            
            # Buscar links de editais (PDFs)
            pdf_links = soup.find_all('a', href=re.compile(r'\\.pdf$', re.IGNORECASE))
            for link in pdf_links:
                edital = {
                    'titulo': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link.get('href', '')),
                    'tipo': 'PDF'
                }
                detalhes['editais'].append(edital)
            
            # Extrair datas importantes
            texto_completo = soup.get_text()
            
            # Padrões de data
            data_patterns = [
                r'Inscrições:?\\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',
                r'até\\s+([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',
                r'Prova:?\\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})'
            ]
            
            for pattern in data_patterns:
                match = re.search(pattern, texto_completo)
                if match:
                    if 'Inscrições' in pattern:
                        detalhes['inscricao_inicio'] = match.group(1)
                    elif 'até' in pattern:
                        detalhes['inscricao_fim'] = match.group(1)
                    elif 'Prova' in pattern:
                        detalhes['prova_data'] = match.group(1)
            
            return detalhes
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar detalhes de {concurso_url}: {e}")
            return None
    
    def salvar_dados(self, filename: str = None) -> str:
        """Salva os dados coletados em CSV e JSON"""
        if not self.concursos_coletados:
            self.logger.warning("Nenhum dado para salvar")
            return ""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if not filename:
                filename = f"pci_concursos_atuais_{timestamp}.csv"
            
            # Salvar CSV
            df = pd.DataFrame(self.concursos_coletados)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            # Salvar JSON
            json_filename = filename.replace('.csv', '.json')
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.concursos_coletados, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 Dados salvos:")
            self.logger.info(f"  📊 CSV: {filename}")
            self.logger.info(f"  📄 JSON: {json_filename}")
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados: {e}")
            return ""
    
    def executar_coleta_completa(self, max_paginas: int = 10) -> Dict:
        """Executa coleta completa e retorna estatísticas"""
        try:
            # Coletar concursos
            self.concursos_coletados = self.coletar_concursos_lista(max_paginas)
            
            if not self.concursos_coletados:
                return {'erro': 'Nenhum concurso coletado'}
            
            # Salvar dados
            filename = self.salvar_dados()
            
            # Gerar estatísticas
            df = pd.DataFrame(self.concursos_coletados)
            
            stats = {
                'total_concursos': len(df),
                'total_vagas': df['vagas'].sum(),
                'concursos_com_vagas': len(df[df['vagas'] > 0]),
                'concursos_com_salario': len(df[df['salario_numerico'] > 0]),
                'salario_medio': df[df['salario_numerico'] > 0]['salario_numerico'].mean(),
                'maior_salario': df['salario_numerico'].max(),
                'orgaos_unicos': df['orgao'].nunique(),
                'arquivo_salvo': filename,
                'data_coleta': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro na coleta completa: {e}")
            return {'erro': str(e)}

def main():
    """Função principal para teste do scraper"""
    print("🕷️ SCRAPER PCI CONCURSOS - TESTE")
    print("=" * 50)
    
    scraper = PCIConcursosScraperAtual()
    
    try:
        # Executar coleta (limitar para teste)
        resultados = scraper.executar_coleta_completa(max_paginas=5)
        
        print("\\n📊 RESULTADOS DA COLETA:")
        print("-" * 30)
        
        if 'erro' in resultados:
            print(f"❌ Erro: {resultados['erro']}")
        else:
            print(f"🎯 Total de concursos: {resultados['total_concursos']}")
            print(f"👥 Total de vagas: {resultados['total_vagas']}")
            print(f"💰 Concursos com salário: {resultados['concursos_com_salario']}")
            print(f"🏢 Órgãos únicos: {resultados['orgaos_unicos']}")
            print(f"💾 Arquivo salvo: {resultados['arquivo_salvo']}")
            
            if resultados['salario_medio'] > 0:
                print(f"📈 Salário médio: R$ {resultados['salario_medio']:.2f}")
            if resultados['maior_salario'] > 0:
                print(f"💎 Maior salário: R$ {resultados['maior_salario']:.2f}")
        
    except KeyboardInterrupt:
        print("\\n⏹️ Coleta interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")

if __name__ == "__main__":
    main()
