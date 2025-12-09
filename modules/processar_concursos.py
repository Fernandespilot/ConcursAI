#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo de processamento de concursos para o sistema ConcursAI"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime, timedelta
import time
import json
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Optional

class ProcessadorConcursos:
    """Classe para processar e extrair dados de editais de concursos públicos"""
    
    def __init__(self):
        self.dados_concursos = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # URLs das APIs e sites
        self.urls = {
            'pci_base': 'https://www.pciconcursos.com.br',
            'pci_api': 'https://www.pciconcursos.com.br/ajax/concursos',
            'gov_api': 'https://dados.gov.br/api/publico/conjuntos-dados',
            'concursos_abertos': 'https://dados.gov.br/dados/conjuntos-dados/concursos-publicos-abertos',
            'qconcursos': 'https://www.qconcursos.com/api/v1/contests'
        }
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def extrair_dados_api_governo(self) -> List[Dict]:
        """Extrai dados da API oficial do governo sobre concursos públicos"""
        try:
            self.logger.info("🏛️ Buscando dados na API do Governo...")
            
            # Endpoint para concursos públicos abertos
            url_concursos = "https://portaldatransparencia.gov.br/api-de-dados/servidores"
            
            # Tentar diferentes endpoints da API do governo
            endpoints_gov = [
                "https://dados.gov.br/api/publico/conjuntos-dados?q=concurso",
                "https://servicodados.ibge.gov.br/api/v1/localidades/estados",
                "https://api.gov.br/ds/v1/concursos"  # Endpoint hipotético
            ]
            
            concursos_gov = []
            
            for endpoint in endpoints_gov:
                try:
                    response = self.session.get(endpoint, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Processar dados conforme estrutura da API
                        if isinstance(data, list):
                            for item in data[:20]:  # Limitar resultados
                                concurso = self._processar_item_gov(item)
                                if concurso:
                                    concursos_gov.append(concurso)
                        elif isinstance(data, dict) and 'dados' in data:
                            for item in data['dados'][:20]:
                                concurso = self._processar_item_gov(item)
                                if concurso:
                                    concursos_gov.append(concurso)
                        
                        self.logger.info(f"✅ {len(concursos_gov)} concursos encontrados em {endpoint}")
                        break  # Usar apenas o primeiro endpoint que funcionar
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro em {endpoint}: {e}")
                    continue
            
            # Buscar dados do Portal da Transparência como alternativa
            if not concursos_gov:
                concursos_gov = self._buscar_portal_transparencia()
            
            return concursos_gov
            
        except Exception as e:
            self.logger.error(f"❌ Erro na API do Governo: {e}")
            return []
    
    def _processar_item_gov(self, item: Dict) -> Optional[Dict]:
        """Processa um item da API do governo"""
        try:
            concurso = {
                'titulo': item.get('nome', item.get('title', item.get('descricao', 'Sem título'))),
                'orgao': item.get('orgao', item.get('instituicao', item.get('organizacao', 'Governo Federal'))),
                'descricao': item.get('descricao', item.get('resumo', '')),
                'url': item.get('url', item.get('link', '')),
                'data_publicacao': item.get('data_publicacao', item.get('created', '')),
                'situacao': item.get('situacao', item.get('status', 'Aberto')),
                'fonte': 'API Governo',
                'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tipo': 'edital_oficial'
            }
            
            # Validar se tem informações mínimas
            if len(concurso['titulo']) > 5:
                return concurso
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao processar item: {e}")
        
        return None
    
    def _buscar_portal_transparencia(self) -> List[Dict]:
        """Busca dados alternativos no Portal da Transparência"""
        try:
            # URLs de editais conhecidos
            urls_editais = [
                "https://www.gov.br/gestao/pt-br/assuntos/concursos-e-selecoes/concursos",
                "https://www.gov.br/servidor/pt-br/acesso-a-informacao/faq/concursos"
            ]
            
            concursos = []
            
            for url in urls_editais:
                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Buscar links e títulos de concursos
                        elementos = soup.find_all(['a', 'h2', 'h3'], string=re.compile(r'concurso|edital', re.I))
                        
                        for elemento in elementos[:10]:
                            titulo = elemento.get_text(strip=True)
                            link = elemento.get('href', '')
                            
                            if len(titulo) > 10:
                                concurso = {
                                    'titulo': titulo,
                                    'orgao': 'Governo Federal',
                                    'url': urljoin(url, link) if link else url,
                                    'fonte': 'Portal Transparência',
                                    'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'tipo': 'edital_portal'
                                }
                                concursos.append(concurso)
                                
                except Exception as e:
                    continue
            
            return concursos
            
        except Exception as e:
            self.logger.error(f"❌ Erro no Portal da Transparência: {e}")
            return []
        
    def extrair_texto_pdf(self, url_pdf):
        """Extrai texto de um PDF a partir de uma URL"""
        try:
            import PyPDF2
            import io
            
            response = requests.get(url_pdf, timeout=30)
            if response.status_code == 200:
                pdf_file = io.BytesIO(response.content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                texto = ""
                for page in pdf_reader.pages:
                    texto += page.extract_text() + "\n"
                
                return texto.strip()
        except Exception as e:
            print(f"❌ Erro ao extrair PDF {url_pdf}: {e}")
            return ""
        
        return ""
    
    def extrair_dados_pci_avancado(self) -> List[Dict]:
        """Extrai dados avançados do PCI Concursos com múltiplas estratégias"""
        try:
            self.logger.info("🔄 Buscando concursos no PCI (Avançado)...")
            
            concursos_pci = []
            
            # Estratégia 1: Página principal de concursos
            concursos_pci.extend(self._extrair_pci_pagina_principal())
            
            # Estratégia 2: API do PCI (se disponível)
            concursos_pci.extend(self._extrair_pci_api())
            
            # Estratégia 3: Busca por categorias específicas
            categorias = ['federal', 'estadual', 'municipal', 'bancarios', 'tribunais']
            for categoria in categorias:
                concursos_pci.extend(self._extrair_pci_categoria(categoria))
                time.sleep(1)  # Pausa entre requisições
            
            # Remover duplicatas
            concursos_pci = self._remover_duplicatas(concursos_pci)
            
            self.logger.info(f"✅ {len(concursos_pci)} concursos únicos encontrados no PCI")
            return concursos_pci
            
        except Exception as e:
            self.logger.error(f"❌ Erro no PCI Avançado: {e}")
            return self.extrair_dados_pci()  # Fallback para método simples
    
    def _extrair_pci_pagina_principal(self) -> List[Dict]:
        """Extrai da página principal do PCI"""
        try:
            url = "https://www.pciconcursos.com.br/concursos/"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            concursos = []
            
            # Buscar diferentes seletores CSS do PCI
            seletores = [
                '.ca',  # Classe comum para concursos
                '.resultado_campo',
                '.resultado_item',
                'div[class*="concurso"]',
                'article[class*="contest"]'
            ]
            
            for seletor in seletores:
                elementos = soup.select(seletor)
                if elementos:
                    for elemento in elementos[:15]:  # Limitar a 15 por seletor
                        concurso = self._processar_elemento_pci(elemento, url)
                        if concurso:
                            concursos.append(concurso)
                    break  # Usar apenas o primeiro seletor que funcionar
            
            return concursos
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro na página principal PCI: {e}")
            return []
    
    def _extrair_pci_api(self) -> List[Dict]:
        """Tenta extrair dados via API do PCI"""
        try:
            # URLs de API possíveis do PCI
            api_urls = [
                "https://www.pciconcursos.com.br/ajax/concursos",
                "https://www.pciconcursos.com.br/api/concursos.json",
                "https://www.pciconcursos.com.br/concursos.json"
            ]
            
            for api_url in api_urls:
                try:
                    response = self.session.get(api_url, timeout=20)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, list):
                                return [self._processar_item_pci_api(item) for item in data[:20]]
                            elif isinstance(data, dict) and 'concursos' in data:
                                return [self._processar_item_pci_api(item) for item in data['concursos'][:20]]
                        except json.JSONDecodeError:
                            # Se não for JSON, tentar como HTML
                            soup = BeautifulSoup(response.content, 'html.parser')
                            return self._processar_html_ajax(soup)
                            
                except Exception as e:
                    continue
            
            return []
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro na API PCI: {e}")
            return []
    
    def _extrair_pci_categoria(self, categoria: str) -> List[Dict]:
        """Extrai concursos de uma categoria específica do PCI"""
        try:
            url = f"https://www.pciconcursos.com.br/concursos/{categoria}/"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                concursos = []
                
                # Buscar elementos específicos da categoria
                elementos = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'concurso|contest|edital'))
                
                for elemento in elementos[:10]:  # Limitar a 10 por categoria
                    concurso = self._processar_elemento_pci(elemento, url)
                    if concurso:
                        concurso['categoria'] = categoria
                        concursos.append(concurso)
                
                return concursos
            
            return []
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro na categoria {categoria}: {e}")
            return []
    
    def _processar_elemento_pci(self, elemento, base_url: str) -> Optional[Dict]:
        """Processa um elemento HTML do PCI"""
        try:
            # Extrair título
            titulo_elem = elemento.find(['h1', 'h2', 'h3', 'h4', 'a', 'strong'])
            titulo = titulo_elem.get_text(strip=True) if titulo_elem else ""
            
            # Extrair link
            link_elem = elemento.find('a')
            link = link_elem.get('href') if link_elem else ""
            if link and not link.startswith('http'):
                link = urljoin(base_url, link)
            
            # Extrair informações adicionais
            texto_completo = elemento.get_text(strip=True)
            
            # Extrair órgão
            orgao = self._extrair_orgao_texto(texto_completo)
            
            # Extrair data
            data_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', texto_completo)
            data = data_match.group(1) if data_match else ""
            
            if len(titulo) > 10:  # Validar título mínimo
                return {
                    'titulo': titulo,
                    'orgao': orgao,
                    'url': link,
                    'descricao': texto_completo[:500],
                    'data_publicacao': data,
                    'fonte': 'PCI Concursos',
                    'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'concurso_pci'
                }
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao processar elemento: {e}")
        
        return None
    
    def _processar_item_pci_api(self, item: Dict) -> Dict:
        """Processa item da API do PCI"""
        return {
            'titulo': item.get('titulo', item.get('nome', '')),
            'orgao': item.get('orgao', item.get('instituicao', '')),
            'url': item.get('url', item.get('link', '')),
            'descricao': item.get('descricao', ''),
            'data_publicacao': item.get('data', ''),
            'salario': item.get('salario', ''),
            'vagas': item.get('vagas', ''),
            'fonte': 'PCI API',
            'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tipo': 'concurso_api'
        }
    
    def _extrair_orgao_texto(self, texto: str) -> str:
        """Extrai órgão de um texto"""
        padroes = [
            r'PREFEITURA\s+(?:MUNICIPAL\s+)?(?:DE\s+)?([A-ZÀ-Ÿ\s]+)',
            r'CÂMARA\s+(?:MUNICIPAL\s+)?(?:DE\s+)?([A-ZÀ-Ÿ\s]+)',
            r'TRIBUNAL\s+([A-ZÀ-Ÿ\s]+)',
            r'SECRETARIA\s+(?:DE\s+)?([A-ZÀ-Ÿ\s]+)',
            r'INSTITUTO\s+([A-ZÀ-Ÿ\s]+)',
            r'FUNDAÇÃO\s+([A-ZÀ-Ÿ\s]+)',
            r'UNIVERSIDADE\s+([A-ZÀ-Ÿ\s]+)',
            r'MINISTÉRIO\s+([A-ZÀ-Ÿ\s]+)'
        ]
        
        texto_upper = texto.upper()
        for padrao in padroes:
            match = re.search(padrao, texto_upper)
            if match:
                return match.group(0).strip()
        
        # Se não encontrar padrão, pegar as primeiras palavras em maiúscula
        palavras = texto.split()[:3]
        orgao_candidato = ' '.join([p for p in palavras if p.isupper() or p.istitle()])
        
        return orgao_candidato if len(orgao_candidato) > 5 else "Órgão não identificado"
    
    def _remover_duplicatas(self, concursos: List[Dict]) -> List[Dict]:
        """Remove concursos duplicados baseado no título"""
        vistos = set()
        unicos = []
        
        for concurso in concursos:
            titulo_norm = re.sub(r'\s+', ' ', concurso['titulo'].lower().strip())
            if titulo_norm not in vistos:
                vistos.add(titulo_norm)
                unicos.append(concurso)
        
        return unicos
    
    def extrair_dados_qconcursos_avancado(self) -> List[Dict]:
        """Extrai dados avançados do QConcursos"""
        try:
            self.logger.info("🔄 Buscando concursos no QConcursos (Avançado)...")
            
            concursos = []
            
            # URLs do QConcursos para diferentes seções
            urls_qconcursos = [
                "https://www.qconcursos.com/concursos-publicos",
                "https://www.qconcursos.com/concursos-abertos",
                "https://www.qconcursos.com/concursos-previstos"
            ]
            
            for url in urls_qconcursos:
                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Seletores CSS específicos do QConcursos
                        seletores = [
                            '.contest-card',
                            '.concurso-item',
                            '.card-concurso',
                            '[data-contest-id]',
                            '.resultado-concurso'
                        ]
                        
                        for seletor in seletores:
                            elementos = soup.select(seletor)
                            if elementos:
                                for elemento in elementos[:10]:
                                    concurso = self._processar_elemento_qconcursos(elemento, url)
                                    if concurso:
                                        concursos.append(concurso)
                                break
                                
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro em {url}: {e}")
                    continue
                
                time.sleep(2)  # Pausa entre requisições
            
            # Tentar API do QConcursos
            concursos.extend(self._extrair_qconcursos_api())
            
            concursos = self._remover_duplicatas(concursos)
            self.logger.info(f"✅ {len(concursos)} concursos encontrados no QConcursos")
            return concursos
            
        except Exception as e:
            self.logger.error(f"❌ Erro no QConcursos: {e}")
            return []
    
    def _processar_elemento_qconcursos(self, elemento, base_url: str) -> Optional[Dict]:
        """Processa elemento do QConcursos"""
        try:
            # Extrair informações específicas do QConcursos
            titulo = ""
            orgao = ""
            link = ""
            vagas = ""
            salario = ""
            
            # Buscar título
            titulo_elem = elemento.find(['h1', 'h2', 'h3', '.contest-title', '.titulo'])
            if titulo_elem:
                titulo = titulo_elem.get_text(strip=True)
            
            # Buscar órgão
            orgao_elem = elemento.find(['.orgao', '.institution', '.empresa'])
            if orgao_elem:
                orgao = orgao_elem.get_text(strip=True)
            
            # Buscar link
            link_elem = elemento.find('a')
            if link_elem:
                link = link_elem.get('href', '')
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)
            
            # Buscar informações adicionais
            texto_completo = elemento.get_text()
            
            # Extrair vagas
            vagas_match = re.search(r'(\d+)\s*vagas?', texto_completo, re.I)
            if vagas_match:
                vagas = vagas_match.group(1)
            
            # Extrair salário
            salario_match = re.search(r'R\$\s*([\d.,]+)', texto_completo)
            if salario_match:
                salario = f"R$ {salario_match.group(1)}"
            
            if len(titulo) > 10:
                return {
                    'titulo': titulo,
                    'orgao': orgao or self._extrair_orgao_texto(texto_completo),
                    'url': link,
                    'vagas': vagas,
                    'salario': salario,
                    'descricao': texto_completo[:500],
                    'fonte': 'QConcursos',
                    'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'tipo': 'concurso_qconcursos'
                }
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao processar QConcursos: {e}")
        
        return None
    
    def _extrair_qconcursos_api(self) -> List[Dict]:
        """Tenta extrair via API do QConcursos"""
        try:
            # Possíveis endpoints da API
            api_endpoints = [
                "https://www.qconcursos.com/api/v1/contests",
                "https://api.qconcursos.com/contests",
                "https://www.qconcursos.com/ajax/concursos"
            ]
            
            for endpoint in api_endpoints:
                try:
                    response = self.session.get(endpoint, timeout=20)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if isinstance(data, list):
                            return [self._processar_item_qconcursos_api(item) for item in data[:15]]
                        elif isinstance(data, dict):
                            items = data.get('data', data.get('contests', data.get('results', [])))
                            return [self._processar_item_qconcursos_api(item) for item in items[:15]]
                            
                except Exception as e:
                    continue
            
            return []
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro na API QConcursos: {e}")
            return []
    
    def _processar_item_qconcursos_api(self, item: Dict) -> Dict:
        """Processa item da API do QConcursos"""
        return {
            'titulo': item.get('name', item.get('title', item.get('nome', ''))),
            'orgao': item.get('organization', item.get('orgao', item.get('empresa', ''))),
            'url': item.get('url', item.get('link', '')),
            'vagas': str(item.get('vacancies', item.get('vagas', ''))),
            'salario': item.get('salary', item.get('salario', '')),
            'nivel': item.get('level', item.get('nivel', '')),
            'area': item.get('area', ''),
            'fonte': 'QConcursos API',
            'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tipo': 'concurso_api'
        }
    
    def extrair_texto_pdf_melhorado(self, url_pdf: str) -> str:
        """Extrai texto de PDF com múltiplas estratégias"""
        try:
            response = self.session.get(url_pdf, timeout=60)
            if response.status_code != 200:
                return ""
            
            content = response.content
            texto_extraido = ""
            
            # Estratégia 1: PyPDF2
            try:
                import PyPDF2
                import io
                
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                for page in pdf_reader.pages[:10]:  # Limitar a 10 páginas
                    texto_extraido += page.extract_text() + "\n"
                
                if len(texto_extraido.strip()) > 100:
                    return texto_extraido.strip()
                    
            except Exception as e:
                self.logger.warning(f"⚠️ PyPDF2 falhou: {e}")
            
            # Estratégia 2: pdfplumber (se disponível)
            try:
                import pdfplumber
                import io
                
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    for page in pdf.pages[:10]:
                        page_text = page.extract_text()
                        if page_text:
                            texto_extraido += page_text + "\n"
                
                if len(texto_extraido.strip()) > 100:
                    return texto_extraido.strip()
                    
            except Exception as e:
                self.logger.warning(f"⚠️ pdfplumber falhou: {e}")
            
            # Estratégia 3: Salvar como texto e usar outras ferramentas
            return texto_extraido.strip()
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao extrair PDF {url_pdf}: {e}")
            return ""
    
    def processar_edital_texto(self, texto, info_concurso):
        """Processa texto de edital e extrai informações estruturadas"""
        chunks = []
        
        # Dividir texto em seções
        secoes = re.split(r'\n(?=\d+\.|\d+\s)', texto)
        
        for i, secao in enumerate(secoes):
            if len(secao.strip()) < 50:  # Ignorar seções muito pequenas
                continue
                
            # Extrair informações específicas
            orgao = self.extrair_orgao(texto, info_concurso.get('titulo', ''))
            ano = self.extrair_ano(texto, info_concurso.get('data_coleta', ''))
            cargo = self.extrair_cargo(secao)
            
            chunk = {
                'conteudo': secao.strip(),
                'orgao': orgao,
                'ano': ano,
                'cargo': cargo,
                'tipo_documento': 'edital',
                'titulo': info_concurso.get('titulo', ''),
                'url': info_concurso.get('url', ''),
                'data_publicacao': info_concurso.get('data_coleta', ''),
                'fonte': info_concurso.get('fonte', ''),
                'secao_numero': i + 1
            }
            chunks.append(chunk)
        
        return chunks
    
    def extrair_orgao(self, texto, titulo):
        """Extrai o nome do órgão do texto ou título"""
        # Padrões comuns de órgãos
        padroes_orgao = [
            r'PREFEITURA\s+(?:MUNICIPAL\s+)?(?:DE\s+)?([A-Z\s]+)',
            r'CÂMARA\s+(?:MUNICIPAL\s+)?(?:DE\s+)?([A-Z\s]+)',
            r'GOVERNO\s+(?:DO\s+ESTADO\s+)?(?:DE\s+)?([A-Z\s]+)',
            r'SECRETARIA\s+(?:DE\s+)?([A-Z\s]+)',
            r'MINISTÉRIO\s+(?:DA\s+|DO\s+)?([A-Z\s]+)',
            r'TRIBUNAL\s+([A-Z\s]+)',
            r'CONSELHO\s+([A-Z\s]+)',
            r'INSTITUTO\s+([A-Z\s]+)',
            r'FUNDAÇÃO\s+([A-Z\s]+)',
            r'AUTARQUIA\s+([A-Z\s]+)'
        ]
        
        texto_busca = (titulo + " " + texto[:1000]).upper()
        
        for padrao in padroes_orgao:
            match = re.search(padrao, texto_busca)
            if match:
                return match.group(0).strip()
        
        # Se não encontrar padrão específico, buscar no título
        palavras_titulo = titulo.split()
        if len(palavras_titulo) > 0:
            return palavras_titulo[0]
        
        return "Não identificado"
    
    def extrair_ano(self, texto, data_coleta):
        """Extrai o ano do concurso"""
        # Buscar anos no texto (2020-2030)
        anos = re.findall(r'\b(202[0-9])\b', texto)
        if anos:
            return anos[0]
        
        # Usar ano da data de coleta
        if data_coleta:
            return data_coleta.split('-')[0]
        
        return str(datetime.now().year)
    
    def extrair_cargo(self, texto):
        """Extrai cargos mencionados no texto"""
        # Padrões comuns de cargos
        padroes_cargo = [
            r'ANALISTA\s+([A-Z\s]+)',
            r'TÉCNICO\s+([A-Z\s]+)',
            r'ASSISTENTE\s+([A-Z\s]+)',
            r'AUXILIAR\s+([A-Z\s]+)',
            r'CONTADOR',
            r'ADVOGADO',
            r'ENFERMEIRO',
            r'MÉDICO',
            r'PROFESSOR',
            r'FISCAL',
            r'AUDITOR',
            r'PROCURADOR',
            r'DELEGADO',
            r'ESCRIVÃO',
            r'AGENTE\s+([A-Z\s]+)'
        ]
        
        texto_upper = texto.upper()
        
        for padrao in padroes_cargo:
            match = re.search(padrao, texto_upper)
            if match:
                return match.group(0).strip()
        
        return "Geral"
    
    def coletar_dados_completos_avancado(self) -> List[Dict]:
        """Coleta dados de múltiplas fontes com processamento avançado"""
        self.logger.info("🚀 Iniciando coleta completa de dados...")
        
        todos_concursos = []
        
        # 1. API do Governo
        self.logger.info("📊 Coletando dados da API do Governo...")
        concursos_gov = self.extrair_dados_api_governo()
        todos_concursos.extend(concursos_gov)
        self.logger.info(f"✅ {len(concursos_gov)} concursos do Governo coletados")
        
        time.sleep(3)  # Pausa respeitosa
        
        # 2. PCI Concursos Avançado
        self.logger.info("🎯 Coletando dados do PCI Concursos...")
        concursos_pci = self.extrair_dados_pci_avancado()
        todos_concursos.extend(concursos_pci)
        self.logger.info(f"✅ {len(concursos_pci)} concursos do PCI coletados")
        
        time.sleep(3)  # Pausa respeitosa
        
        # 3. QConcursos Avançado
        self.logger.info("📚 Coletando dados do QConcursos...")
        concursos_q = self.extrair_dados_qconcursos_avancado()
        todos_concursos.extend(concursos_q)
        self.logger.info(f"✅ {len(concursos_q)} concursos do QConcursos coletados")
        
        # 4. Buscar editais em PDFs (para alguns concursos)
        self.logger.info("📄 Processando editais em PDF...")
        todos_concursos = self._processar_pdfs_encontrados(todos_concursos)
        
        # 5. Remover duplicatas finais
        todos_concursos = self._remover_duplicatas(todos_concursos)
        
        # 6. Enriquecer dados
        todos_concursos = self._enriquecer_dados(todos_concursos)
        
        self.logger.info(f"🎉 Coleta finalizada: {len(todos_concursos)} concursos únicos coletados!")
        return todos_concursos
    
    def _processar_pdfs_encontrados(self, concursos: List[Dict]) -> List[Dict]:
        """Processa PDFs encontrados nos concursos"""
        concursos_processados = []
        
        for concurso in concursos:
            url = concurso.get('url', '')
            
            # Se a URL for um PDF, extrair o texto
            if url.lower().endswith('.pdf'):
                self.logger.info(f"📄 Processando PDF: {url}")
                texto_pdf = self.extrair_texto_pdf_melhorado(url)
                
                if texto_pdf:
                    # Criar chunks do PDF
                    chunks_pdf = self.processar_edital_texto(texto_pdf, concurso)
                    
                    # Adicionar informação de que veio de PDF
                    for chunk in chunks_pdf:
                        chunk['fonte_original'] = 'PDF'
                        chunk['url_pdf'] = url
                    
                    concursos_processados.extend(chunks_pdf)
                else:
                    # Manter o concurso original se não conseguir processar o PDF
                    concursos_processados.append(concurso)
            else:
                concursos_processados.append(concurso)
        
        return concursos_processados
    
    def _enriquecer_dados(self, concursos: List[Dict]) -> List[Dict]:
        """Enriquece os dados dos concursos com informações adicionais"""
        concursos_enriquecidos = []
        
        for concurso in concursos:
            # Padronizar campos
            concurso_enriquecido = {
                'conteudo': concurso.get('descricao', concurso.get('titulo', '')),
                'titulo': concurso.get('titulo', ''),
                'orgao': self._padronizar_orgao(concurso.get('orgao', '')),
                'ano': self._extrair_ano_melhorado(concurso),
                'cargo': self._extrair_cargo_melhorado(concurso),
                'url': concurso.get('url', ''),
                'fonte': concurso.get('fonte', 'Desconhecida'),
                'data_publicacao': concurso.get('data_publicacao', ''),
                'data_coleta': concurso.get('data_coleta', ''),
                'tipo_documento': 'edital',
                'salario': concurso.get('salario', ''),
                'vagas': concurso.get('vagas', ''),
                'situacao': concurso.get('situacao', 'Aberto'),
                'nivel': concurso.get('nivel', ''),
                'area': concurso.get('area', ''),
                'categoria': concurso.get('categoria', ''),
                'estado': self._extrair_estado(concurso),
                'municipio': self._extrair_municipio(concurso)
            }
            
            concursos_enriquecidos.append(concurso_enriquecido)
        
        return concursos_enriquecidos
    
    def _padronizar_orgao(self, orgao: str) -> str:
        """Padroniza o nome do órgão"""
        if not orgao:
            return "Órgão não identificado"
        
        # Remover caracteres especiais e normalizar
        orgao_limpo = re.sub(r'[^\w\s]', '', orgao).strip()
        
        # Capitalizar adequadamente
        palavras = orgao_limpo.split()
        palavras_importantes = ['PREFEITURA', 'CÂMARA', 'TRIBUNAL', 'MINISTÉRIO', 'SECRETARIA', 'INSTITUTO', 'FUNDAÇÃO']
        
        palavras_formatadas = []
        for palavra in palavras:
            if palavra.upper() in palavras_importantes:
                palavras_formatadas.append(palavra.upper())
            else:
                palavras_formatadas.append(palavra.title())
        
        return ' '.join(palavras_formatadas)
    
    def _extrair_ano_melhorado(self, concurso: Dict) -> str:
        """Extrai ano com múltiplas estratégias"""
        # Tentar da data de publicação
        data_pub = concurso.get('data_publicacao', '')
        if data_pub:
            ano_match = re.search(r'(202[0-9])', data_pub)
            if ano_match:
                return ano_match.group(1)
        
        # Tentar do título
        titulo = concurso.get('titulo', '')
        ano_match = re.search(r'(202[0-9])', titulo)
        if ano_match:
            return ano_match.group(1)
        
        # Tentar da URL
        url = concurso.get('url', '')
        ano_match = re.search(r'(202[0-9])', url)
        if ano_match:
            return ano_match.group(1)
        
        # Usar ano atual como fallback
        return str(datetime.now().year)
    
    def _extrair_cargo_melhorado(self, concurso: Dict) -> str:
        """Extrai cargo com análise avançada"""
        texto_completo = f"{concurso.get('titulo', '')} {concurso.get('descricao', '')}"
        
        # Padrões de cargos mais específicos
        padroes_cargo = [
            r'ANALISTA\s+([A-ZÀ-Ÿ\s]+?)(?:\s|$|\.|,)',
            r'TÉCNICO\s+([A-ZÀ-Ÿ\s]+?)(?:\s|$|\.|,)',
            r'ASSISTENTE\s+([A-ZÀ-Ÿ\s]+?)(?:\s|$|\.|,)',
            r'AUXILIAR\s+([A-ZÀ-Ÿ\s]+?)(?:\s|$|\.|,)',
            r'AGENTE\s+([A-ZÀ-Ÿ\s]+?)(?:\s|$|\.|,)',
            r'ESPECIALISTA\s+([A-ZÀ-Ÿ\s]+?)(?:\s|$|\.|,)',
            r'COORDENADOR\s+([A-ZÀ-Ÿ\s]+?)(?:\s|$|\.|,)',
            r'DIRETOR\s+([A-ZÀ-Ÿ\s]+?)(?:\s|$|\.|,)'
        ]
        
        # Cargos específicos comuns
        cargos_especificos = [
            'CONTADOR', 'ADVOGADO', 'ENFERMEIRO', 'MÉDICO', 'PROFESSOR', 
            'FISCAL', 'AUDITOR', 'PROCURADOR', 'DELEGADO', 'ESCRIVÃO',
            'BIBLIOTECÁRIO', 'PSICÓLOGO', 'NUTRICIONISTA', 'FARMACÊUTICO',
            'ENGENHEIRO', 'ARQUITETO', 'VETERINÁRIO', 'DENTISTA'
        ]
        
        texto_upper = texto_completo.upper()
        
        # Buscar padrões compostos primeiro
        for padrao in padroes_cargo:
            match = re.search(padrao, texto_upper)
            if match:
                cargo_completo = f"{match.group(0).split()[0]} {match.group(1).strip()}"
                return cargo_completo[:50]  # Limitar tamanho
        
        # Buscar cargos específicos
        for cargo in cargos_especificos:
            if cargo in texto_upper:
                return cargo
        
        return "Geral"
    
    def _extrair_estado(self, concurso: Dict) -> str:
        """Extrai estado do concurso"""
        texto = f"{concurso.get('titulo', '')} {concurso.get('orgao', '')} {concurso.get('descricao', '')}"
        
        estados = {
            'SP': ['SÃO PAULO', 'PAULISTA'], 'RJ': ['RIO DE JANEIRO', 'FLUMINENSE'],
            'MG': ['MINAS GERAIS', 'MINEIRO'], 'RS': ['RIO GRANDE DO SUL', 'GAÚCHO'],
            'PR': ['PARANÁ', 'PARANAENSE'], 'SC': ['SANTA CATARINA', 'CATARINENSE'],
            'BA': ['BAHIA', 'BAIANO'], 'GO': ['GOIÁS', 'GOIANO'],
            'PE': ['PERNAMBUCO', 'PERNAMBUCANO'], 'CE': ['CEARÁ', 'CEARENSE']
        }
        
        texto_upper = texto.upper()
        for sigla, nomes in estados.items():
            for nome in nomes:
                if nome in texto_upper:
                    return sigla
        
        return ""
    
    def _extrair_municipio(self, concurso: Dict) -> str:
        """Extrai município do concurso"""
        orgao = concurso.get('orgao', '')
        titulo = concurso.get('titulo', '')
        
        # Buscar padrão "PREFEITURA DE XXXXX"
        match = re.search(r'PREFEITURA\s+(?:MUNICIPAL\s+)?(?:DE\s+)?([A-ZÀ-Ÿ\s]+)', orgao.upper())
        if match:
            return match.group(1).strip()
        
        # Buscar padrão "CÂMARA DE XXXXX"
        match = re.search(r'CÂMARA\s+(?:MUNICIPAL\s+)?(?:DE\s+)?([A-ZÀ-Ÿ\s]+)', orgao.upper())
        if match:
            return match.group(1).strip()
        
        return ""
    
    def salvar_dados_csv(self, chunks, arquivo="concursos_chunks.csv"):
        """Salva os chunks processados em CSV"""
        try:
            df = pd.DataFrame(chunks)
            df.to_csv(arquivo, index=False, encoding='utf-8')
            print(f"✅ Dados salvos em {arquivo} ({len(chunks)} registros)")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar CSV: {e}")
            return False

def criar_dados_exemplo_avancados():
    """Cria dados de exemplo mais realistas e diversificados"""
    chunks_exemplo = [
        {
            'conteudo': 'A Prefeitura Municipal de São Paulo torna público o presente edital para provimento de 100 vagas do cargo de Analista Administrativo, com remuneração de R$ 5.847,00. Requisitos: curso superior completo em qualquer área, conhecimentos em informática e inglês básico. Inscrições de 15/01/2024 a 15/02/2024 no site www.prefeitura.sp.gov.br.',
            'titulo': 'Concurso Prefeitura SP - Analista Administrativo 2024',
            'orgao': 'Prefeitura Municipal de São Paulo',
            'ano': '2024',
            'cargo': 'Analista Administrativo',
            'tipo_documento': 'edital',
            'url': 'https://www.prefeitura.sp.gov.br/edital2024001',
            'data_publicacao': '2024-01-10',
            'fonte': 'Site Oficial',
            'salario': 'R$ 5.847,00',
            'vagas': '100',
            'nivel': 'Superior',
            'area': 'Administrativa',
            'estado': 'SP',
            'municipio': 'São Paulo'
        },
        {
            'conteudo': 'O Tribunal Regional do Trabalho da 2ª Região realiza concurso para provimento de 50 vagas de Técnico Judiciário - Área Administrativa, com salário inicial de R$ 7.591,37. Escolaridade: ensino médio completo. Taxa de inscrição: R$ 80,00. Período de inscrições: 01/02/2024 a 28/02/2024. Provas objetivas em 15/04/2024.',
            'titulo': 'TRT 2ª Região - Técnico Judiciário 2024',
            'orgao': 'Tribunal Regional do Trabalho 2ª Região',
            'ano': '2024',
            'cargo': 'Técnico Judiciário',
            'tipo_documento': 'edital',
            'url': 'https://www.trt2.jus.br/concurso2024',
            'data_publicacao': '2024-01-20',
            'fonte': 'PCI Concursos',
            'salario': 'R$ 7.591,37',
            'vagas': '50',
            'nivel': 'Médio',
            'area': 'Judiciária',
            'estado': 'SP',
            'municipio': 'São Paulo'
        },
        {
            'conteudo': 'Ministério da Educação abre seleção para Professor de Ensino Básico, Técnico e Tecnológico. Total de 200 vagas distribuídas em diversas áreas: Matemática (50), Português (40), História (30), Geografia (25), Ciências (25), Educação Física (20), Artes (10). Vencimento básico: R$ 4.472,64, podendo chegar a R$ 6.356,02 com titulação. Requisitos: licenciatura na área específica.',
            'titulo': 'MEC - Professor EBTT - Edital 2024',
            'orgao': 'Ministério da Educação',
            'ano': '2024',
            'cargo': 'Professor',
            'tipo_documento': 'edital',
            'url': 'https://www.gov.br/mec/concurso2024',
            'data_publicacao': '2024-02-01',
            'fonte': 'API Governo',
            'salario': 'R$ 4.472,64 a R$ 6.356,02',
            'vagas': '200',
            'nivel': 'Superior',
            'area': 'Educação',
            'estado': 'DF',
            'municipio': 'Brasília'
        },
        {
            'conteudo': 'Câmara Municipal de Campinas contrata Contador através de concurso público. 1 vaga imediata + cadastro reserva. Salário: R$ 8.500,00 + benefícios (vale alimentação R$ 800,00, plano de saúde). Jornada: 40h semanais. Requisitos: curso superior em Ciências Contábeis e registro no CRC. Inscrições online de 10/03/2024 a 10/04/2024.',
            'titulo': 'Câmara Campinas - Contador 2024',
            'orgao': 'Câmara Municipal de Campinas',
            'ano': '2024',
            'cargo': 'Contador',
            'tipo_documento': 'edital',
            'url': 'https://www.campinas.sp.leg.br/concurso',
            'data_publicacao': '2024-03-01',
            'fonte': 'QConcursos',
            'salario': 'R$ 8.500,00',
            'vagas': '1',
            'nivel': 'Superior',
            'area': 'Contábil',
            'estado': 'SP',
            'municipio': 'Campinas'
        },
        {
            'conteudo': 'Instituto Brasileiro do Meio Ambiente e dos Recursos Naturais Renováveis (IBAMA) anuncia concurso para Analista Ambiental. 70 vagas distribuídas nacionalmente. Remuneração inicial: R$ 9.774,76. Atribuições: fiscalização ambiental, licenciamento, análise de impactos ambientais. Requisitos: curso superior em Engenharia Ambiental, Biologia, Geografia ou áreas afins. Prova em duas etapas: objetiva e discursiva.',
            'titulo': 'IBAMA - Analista Ambiental 2024',
            'orgao': 'Instituto Brasileiro do Meio Ambiente - IBAMA',
            'ano': '2024',
            'cargo': 'Analista Ambiental',
            'tipo_documento': 'edital',
            'url': 'https://www.ibama.gov.br/concurso2024',
            'data_publicacao': '2024-02-15',
            'fonte': 'Site Oficial',
            'salario': 'R$ 9.774,76',
            'vagas': '70',
            'nivel': 'Superior',
            'area': 'Ambiental',
            'estado': 'DF',
            'municipio': 'Brasília'
        },
        {
            'conteudo': 'Secretaria de Estado da Saúde de Minas Gerais oferece vagas para Enfermeiro. 300 vagas para atuação em hospitais e unidades básicas de saúde. Salário base: R$ 6.200,00 + gratificações. Carga horária: 40h semanais. Requisitos: curso superior em Enfermagem e registro no COREN. Reserva de vagas: 5% PcD, 20% negros. Inscrições: R$ 120,00.',
            'titulo': 'SES/MG - Enfermeiro 2024',
            'orgao': 'Secretaria de Estado da Saúde de Minas Gerais',
            'ano': '2024',
            'cargo': 'Enfermeiro',
            'tipo_documento': 'edital',
            'url': 'https://www.saude.mg.gov.br/concurso',
            'data_publicacao': '2024-03-10',
            'fonte': 'PCI Concursos',
            'salario': 'R$ 6.200,00',
            'vagas': '300',
            'nivel': 'Superior',
            'area': 'Saúde',
            'estado': 'MG',
            'municipio': 'Belo Horizonte'
        },
        {
            'conteudo': 'Banco do Brasil S.A. abre processo seletivo para Escriturário. 4.000 vagas para todo o país. Salário: R$ 3.022,37 + benefícios (PLR, previdência complementar, auxílio alimentação). Escolaridade: ensino médio completo. Disciplinas da prova: Língua Portuguesa, Inglês, Matemática, Atualidades, Conhecimentos Bancários, Informática. Inscrições online com taxa de R$ 38,00.',
            'titulo': 'Banco do Brasil - Escriturário 2024',
            'orgao': 'Banco do Brasil S.A.',
            'ano': '2024',
            'cargo': 'Escriturário',
            'tipo_documento': 'edital',
            'url': 'https://www.bb.com.br/concurso',
            'data_publicacao': '2024-04-01',
            'fonte': 'QConcursos',
            'salario': 'R$ 3.022,37',
            'vagas': '4000',
            'nivel': 'Médio',
            'area': 'Bancária',
            'estado': 'DF',
            'municipio': 'Brasília'
        },
        {
            'conteudo': 'Prefeitura de Florianópolis realiza concurso para Fiscal de Obras e Posturas. 15 vagas efetivas. Vencimento: R$ 7.439,45 para 40h semanais. Atribuições: fiscalização de obras, licenças, alvarás, posturas municipais. Requisito: curso superior em Engenharia Civil ou Arquitetura. Taxa de inscrição: R$ 150,00. Prova objetiva + prova prática. Validade: 2 anos, prorrogável por igual período.',
            'titulo': 'Prefeitura Florianópolis - Fiscal de Obras 2024',
            'orgao': 'Prefeitura Municipal de Florianópolis',
            'ano': '2024',
            'cargo': 'Fiscal de Obras e Posturas',
            'tipo_documento': 'edital',
            'url': 'https://www.pmf.sc.gov.br/concurso',
            'data_publicacao': '2024-03-20',
            'fonte': 'Site Oficial',
            'salario': 'R$ 7.439,45',
            'vagas': '15',
            'nivel': 'Superior',
            'area': 'Fiscalização',
            'estado': 'SC',
            'municipio': 'Florianópolis'
        }
    ]
    
    return chunks_exemplo

if __name__ == "__main__":
    print("🚀 Iniciando coleta avançada de dados de concursos...")
    
    # Criar dados de exemplo primeiro
    chunks = criar_dados_exemplo_avancados()
    print(f"✅ {len(chunks)} dados de exemplo criados")
    
    # Tentar coletar dados reais
    try:
        processador = ProcessadorConcursos()
        print("🌐 Iniciando coleta de dados reais...")
        
        concursos_reais = processador.coletar_dados_completos_avancado()
        
        if concursos_reais:
            print(f"✅ {len(concursos_reais)} concursos reais coletados")
            
            # Processar alguns concursos reais em chunks
            for i, concurso in enumerate(concursos_reais[:10]):  # Processar apenas os primeiros 10
                print(f"📄 Processando concurso {i+1}/{min(10, len(concursos_reais))}: {concurso.get('titulo', 'Sem título')[:50]}...")
                
                texto_para_processar = f"{concurso.get('titulo', '')} {concurso.get('descricao', concurso.get('conteudo', ''))}"
                
                if len(texto_para_processar.strip()) > 50:
                    chunks_processados = processador.processar_edital_texto(texto_para_processar, concurso)
                    chunks.extend(chunks_processados)
                else:
                    # Se não há texto suficiente, adicionar como está
                    chunks.append(concurso)
        else:
            print("⚠️ Nenhum dado real coletado, usando apenas exemplos")
            
    except Exception as e:
        print(f"⚠️ Erro na coleta automática: {e}")
        print("🔄 Usando apenas dados de exemplo")
    
    # Salvar dados finais
    try:
        processador = ProcessadorConcursos()
        sucesso = processador.salvar_dados_csv(chunks)
        
        if sucesso:
            print(f"🎉 Processamento concluído com sucesso!")
            print(f"📊 Total de registros: {len(chunks)}")
            print(f"📁 Arquivo salvo: concursos_chunks.csv")
            
            # Estatísticas dos dados
            df = pd.DataFrame(chunks)
            print("\n📈 Estatísticas dos dados:")
            print(f"   • Órgãos únicos: {df['orgao'].nunique()}")
            print(f"   • Anos únicos: {df['ano'].nunique()}")
            print(f"   • Cargos únicos: {df['cargo'].nunique()}")
            print(f"   • Fontes: {df['fonte'].unique()}")
        else:
            print("❌ Erro ao salvar dados")
            
    except Exception as e:
        print(f"❌ Erro final: {e}")
