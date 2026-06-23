#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scraper Real do PCI Concursos - Dados diretos do site"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PCIScraper:
    def __init__(self):
        self.base_url = "https://www.pciconcursos.com.br"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
    def scrape_pci_concursos(self, max_concursos=30):
        """Scraper principal do PCI Concursos - dados reais"""
        logger.info("🌐 Iniciando scraping REAL do PCI Concursos...")
        concursos = []
        
        try:
            # Tentar diferentes URLs do PCI
            urls_tentar = [
                f"{self.base_url}/",
                f"{self.base_url}/concursos",
                f"{self.base_url}/concursos/abertos"
            ]
            
            for url in urls_tentar:
                logger.info(f"🔍 Tentando URL: {url}")
                try:
                    response = self.session.get(url, timeout=20)
                    if response.status_code == 200:
                        logger.info(f"✅ Sucesso em {url}")
                        concursos.extend(self.extrair_concursos_pagina(response.text, url))
                        if len(concursos) >= max_concursos:
                            break
                        time.sleep(2)  # Pausa entre requisições
                except Exception as e:
                    logger.warning(f"⚠️ Falha em {url}: {e}")
                    continue
            
            # Se não conseguiu dados das URLs principais, tentar busca específica
            if not concursos:
                logger.info("🔄 Tentando método alternativo...")
                concursos = self.scrape_alternativo()
            
            if concursos:
                logger.info(f"✅ Scraping concluído: {len(concursos)} concursos reais coletados")
                return concursos[:max_concursos]
            else:
                logger.warning("⚠️ Nenhum concurso foi extraído")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erro no scraping: {e}")
            return []
    
    def extrair_concursos_pagina(self, html, url_base):
        """Extrai concursos de uma página HTML"""
        concursos = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Buscar diferentes padrões de elementos que podem conter concursos
        seletores = [
            'a[href*="/concurso/"]',  # Links diretos de concursos
            '.concurso',              # Classes específicas
            'div[class*="concurso"]', # Divs com "concurso" no nome da classe
            'tr[class*="concurso"]',  # Linhas de tabela
            'li[class*="concurso"]',  # Items de lista
        ]
        
        elementos_encontrados = []
        for seletor in seletores:
            elementos = soup.select(seletor)
            elementos_encontrados.extend(elementos)
            
        # Também buscar por links que mencionem palavras-chave
        links_texto = soup.find_all('a', string=re.compile(r'(concurso|edital|processo seletivo)', re.I))
        elementos_encontrados.extend(links_texto)
        
        logger.info(f"🔍 Elementos encontrados: {len(elementos_encontrados)}")
        
        for elemento in elementos_encontrados:
            try:
                dados_concurso = self.extrair_dados_elemento(elemento)
                if dados_concurso and self.validar_concurso(dados_concurso):
                    concursos.append(dados_concurso)
                    if len(concursos) >= 50:  # Limite por página
                        break
            except Exception as e:
                logger.debug(f"Erro ao processar elemento: {e}")
                continue
        
        return concursos
    
    def extrair_dados_elemento(self, elemento):
        """Extrai dados de um elemento HTML que representa um concurso"""
        try:
            # Obter texto e link
            if elemento.name == 'a':
                titulo = elemento.get_text(strip=True)
                link = elemento.get('href', '')
            else:
                link_elem = elemento.find('a')
                if link_elem:
                    titulo = link_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                else:
                    titulo = elemento.get_text(strip=True)
                    link = ''
            
            # Normalizar link
            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)
            
            # Extrair informações do texto completo do elemento
            texto_completo = elemento.get_text()
            
            # Buscar contexto adicional (elementos pai/irmãos)
            contexto = ""
            if elemento.parent:
                contexto = elemento.parent.get_text()
            
            # Extrair informações específicas
            dados = {
                'id': f"pci_{hash(link) % 100000}" if link else f"pci_{hash(titulo) % 100000}",
                'titulo': self.limpar_texto(titulo),
                'orgao': self.extrair_orgao(titulo, contexto),
                'cargo': self.extrair_cargo(titulo, contexto),
                'ano': str(datetime.now().year),
                'vagas': self.extrair_vagas(texto_completo, contexto),
                'salario': self.extrair_salario(texto_completo, contexto),
                'local': self.extrair_local(texto_completo, contexto),
                'regiao': '',  # Será calculado depois
                'estado': '',  # Será calculado depois
                'status': 'Inscrições abertas',  # Assumir aberto por padrão
                'escolaridade': self.extrair_escolaridade(titulo, contexto),
                'taxa_inscricao': 'Consultar edital',
                'data_publicacao': datetime.now().strftime("%d/%m/%Y"),
                'inicio_inscricoes': 'Consultar edital',
                'fim_inscricoes': 'Consultar edital',
                'data_prova': 'Consultar edital',
                'prazo_inscricoes': 'Consultar edital',
                'dias_restantes': 0,
                'nivel': self.extrair_escolaridade(titulo, contexto),
                'tipo': 'ABERTO',
                'urgencia': 'normal',
                'url': link,
                'fonte': 'PCI Concursos Real',
                'tipo_documento': 'edital',
                'conteudo': self.limpar_texto(titulo + " " + contexto[:200])
            }
            
            # Calcular região e estado baseado no local
            dados['regiao'] = self.calcular_regiao(dados['local'])
            dados['estado'] = self.extrair_estado_sigla(dados['local'])
            
            return dados
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dados do elemento: {e}")
            return None
    
    def validar_concurso(self, dados):
        """Valida se os dados extraídos representam um concurso válido"""
        if not dados:
            return False
            
        titulo = dados.get('titulo', '')
        if len(titulo) < 10:  # Título muito curto
            return False
            
        # Verificar se contém palavras-chave de concurso
        palavras_chave = ['concurso', 'edital', 'processo seletivo', 'seleção']
        titulo_lower = titulo.lower()
        
        if not any(palavra in titulo_lower for palavra in palavras_chave):
            return False
            
        return True
    
    def scrape_alternativo(self):
        """Método alternativo de scraping quando o principal falha"""
        logger.info("🔄 Usando método alternativo de scraping...")
        concursos = []
        
        try:
            # URLs alternativas para tentar
            urls_alt = [
                f"{self.base_url}/concursos/abertos",
                f"{self.base_url}/concursos/federais",
                f"{self.base_url}/concursos/estaduais",
                f"{self.base_url}/concursos/municipais"
            ]
            
            for url in urls_alt:
                try:
                    response = self.session.get(url, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # Buscar qualquer link que mencione concurso
                        links = soup.find_all('a', href=True)
                        for link in links:
                            texto = link.get_text(strip=True)
                            if len(texto) > 20 and any(word in texto.lower() for word in ['concurso', 'edital']):
                                dados = self.criar_concurso_basico(texto, link.get('href'))
                                if dados:
                                    concursos.append(dados)
                                    if len(concursos) >= 20:
                                        break
                    time.sleep(1)
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Erro no método alternativo: {e}")
            
        return concursos
    
    def criar_concurso_basico(self, titulo, link):
        """Cria estrutura básica de concurso com informações limitadas"""
        if not titulo or len(titulo) < 10:
            return None
            
        return {
            'id': f"pci_alt_{hash(titulo) % 100000}",
            'titulo': self.limpar_texto(titulo),
            'orgao': self.extrair_orgao_simples(titulo),
            'cargo': self.extrair_cargo_simples(titulo),
            'ano': str(datetime.now().year),
            'vagas': 'Consultar edital',
            'salario': 'Consultar edital',
            'local': 'Consultar edital',
            'regiao': 'Nacional',
            'estado': 'BR',
            'status': 'Inscrições abertas',
            'escolaridade': self.extrair_escolaridade_simples(titulo),
            'taxa_inscricao': 'Consultar edital',
            'data_publicacao': datetime.now().strftime("%d/%m/%Y"),
            'inicio_inscricoes': 'Consultar edital',
            'fim_inscricoes': 'Consultar edital',
            'data_prova': 'Consultar edital',
            'prazo_inscricoes': 'Consultar edital',
            'dias_restantes': 0,
            'nivel': self.extrair_escolaridade_simples(titulo),
            'tipo': 'ABERTO',
            'urgencia': 'normal',
            'url': urljoin(self.base_url, link) if link else '',
            'fonte': 'PCI Concursos Real',
            'tipo_documento': 'edital',
            'conteudo': self.limpar_texto(titulo)
        }
    
    # Funções auxiliares de extração
    def limpar_texto(self, texto):
        """Limpa e normaliza texto"""
        if not texto:
            return ""
        return re.sub(r'\s+', ' ', texto.strip())
    
    def extrair_orgao(self, titulo, contexto=""):
        """Extrai nome do órgão"""
        texto = f"{titulo} {contexto}".lower()
        
        # Padrões comuns de órgãos
        orgaos_conhecidos = [
            'tribunal de justiça', 'prefeitura', 'câmara municipal', 'assembleia legislativa',
            'polícia federal', 'polícia civil', 'polícia militar', 'corpo de bombeiros',
            'receita federal', 'banco central', 'inss', 'ibge', 'anvisa', 'anatel',
            'ministério público', 'defensoria pública', 'tribunal de contas',
            'universidade federal', 'instituto federal', 'cefet'
        ]
        
        for orgao in orgaos_conhecidos:
            if orgao in texto:
                return orgao.title()
        
        # Tentar extrair usando padrões
        match = re.search(r'(tribunal|prefeitura|câmara|assembleia|polícia|ministério|defensoria|universidade|instituto)[\w\s]+', texto, re.I)
        if match:
            return match.group().title()
            
        return "Órgão público"
    
    def extrair_orgao_simples(self, titulo):
        """Versão simplificada para extrair órgão"""
        return self.extrair_orgao(titulo, "")
    
    def extrair_cargo(self, titulo, contexto=""):
        """Extrai nome do cargo"""
        texto = f"{titulo} {contexto}".lower()
        
        # Padrões comuns de cargos
        cargos_conhecidos = [
            'analista', 'técnico', 'auditor', 'agente', 'escrivão', 'investigador',
            'delegado', 'professor', 'médico', 'enfermeiro', 'advogado', 'contador',
            'engenheiro', 'procurador', 'promotor', 'defensor', 'juiz'
        ]
        
        for cargo in cargos_conhecidos:
            if cargo in texto:
                return cargo.title()
                
        # Buscar padrão "cargo de X"
        match = re.search(r'cargo de ([\w\s]+)', texto, re.I)
        if match:
            return match.group(1).title()
            
        return "Servidor público"
    
    def extrair_cargo_simples(self, titulo):
        """Versão simplificada para extrair cargo"""
        return self.extrair_cargo(titulo, "")
    
    def extrair_vagas(self, texto, contexto=""):
        """Extrai número de vagas"""
        texto_completo = f"{texto} {contexto}"
        
        # Buscar padrões de vagas
        patterns = [
            r'(\d+)\s*vaga[s]?',
            r'vaga[s]?:\s*(\d+)',
            r'(\d+)\s*posto[s]?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto_completo, re.I)
            if match:
                return match.group(1)
                
        return "Consultar edital"
    
    def extrair_salario(self, texto, contexto=""):
        """Extrai valor do salário"""
        texto_completo = f"{texto} {contexto}"
        
        # Buscar padrões de salário
        patterns = [
            r'R\$\s*[\d.,]+',
            r'salário.*?R\$\s*[\d.,]+',
            r'remuneração.*?R\$\s*[\d.,]+'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto_completo, re.I)
            if match:
                return match.group()
                
        return "Consultar edital"
    
    def extrair_local(self, texto, contexto=""):
        """Extrai local/estado"""
        texto_completo = f"{texto} {contexto}"
        
        # Estados brasileiros
        estados = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
        
        for estado in estados:
            if estado in texto_completo.upper():
                return estado
                
        # Cidades conhecidas
        cidades = ['são paulo', 'rio de janeiro', 'brasília', 'belo horizonte', 'salvador', 'fortaleza', 'recife', 'porto alegre', 'curitiba']
        
        for cidade in cidades:
            if cidade in texto_completo.lower():
                return cidade.title()
                
        return "Nacional"
    
    def extrair_escolaridade(self, titulo, contexto=""):
        """Extrai nível de escolaridade"""
        texto = f"{titulo} {contexto}".lower()
        
        if any(word in texto for word in ['superior', 'graduação', 'bacharel', 'analista', 'auditor']):
            return "Ensino Superior"
        elif any(word in texto for word in ['médio', 'técnico']):
            return "Ensino Médio"
        elif any(word in texto for word in ['fundamental', 'auxiliar']):
            return "Ensino Fundamental"
        else:
            return "Consultar edital"
    
    def extrair_escolaridade_simples(self, titulo):
        """Versão simplificada para extrair escolaridade"""
        return self.extrair_escolaridade(titulo, "")
    
    def calcular_regiao(self, local):
        """Calcula região baseada no local"""
        if not local or local == "Nacional":
            return "Nacional"
            
        regioes = {
            "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
            "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
            "Centro-Oeste": ["DF", "GO", "MT", "MS"],
            "Sudeste": ["ES", "MG", "RJ", "SP"],
            "Sul": ["PR", "RS", "SC"]
        }
        
        local_upper = local.upper()
        for regiao, estados in regioes.items():
            if any(estado in local_upper for estado in estados):
                return regiao
                
        return "Nacional"
    
    def extrair_estado_sigla(self, local):
        """Extrai sigla do estado"""
        if not local:
            return "BR"
            
        estados = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
        
        for estado in estados:
            if estado in local.upper():
                return estado
                
        return "BR"
    
    def run_full_scrape(self, max_pages=3, save_csv=True):
        """Executa scraping completo do PCI Concursos"""
        logger.info("🌐 Iniciando scraping REAL do PCI Concursos...")
        
        try:
            concursos = self.scrape_pci_concursos(max_concursos=30)
            
            if not concursos:
                logger.warning("❌ Nenhum concurso foi coletado do PCI")
                return []
            
            logger.info(f"✅ Scraping concluído: {len(concursos)} concursos reais coletados")
            
            # Salvar em CSV se solicitado
            if save_csv:
                df = pd.DataFrame(concursos)
                df.to_csv("concursos_chunks.csv", index=False)
                logger.info("💾 Dados salvos em concursos_chunks.csv")
            
            return concursos
            
        except Exception as e:
            logger.error(f"❌ Erro no scraping completo: {e}")
            return []
                
                # Seletor 2: Títulos de concursos em divs específicas
                concurso_divs = soup.find_all('div', class_=re.compile(r'concurso|item-concurso'))
                concurso_items.extend(concurso_divs)
                
                # Seletor 3: Buscar por padrões de texto que indicam concursos
                all_links = soup.find_all('a')
                for link in all_links:
                    text = link.get_text(strip=True)
                    # Filtrar apenas textos que parecem ser títulos de concurso
                    if (len(text) > 20 and 
                        any(keyword in text.lower() for keyword in ['concurso', 'edital', 'seleção', 'processo seletivo']) and
                        not any(skip in text.lower() for skip in ['região', 'estado', 'cadastre-se', 'login', 'menu'])):
                        concurso_items.append(link)
                
                logger.info(f"Encontrados {len(concurso_items)} elementos na página {page}")
                
                for item in concurso_items:
                    try:
                        concurso_data = self.extract_concurso_data(item, soup)
                        if concurso_data and self.is_valid_concurso(concurso_data):
                            concursos.append(concurso_data)
                    except Exception as e:
                        logger.warning(f"Erro ao extrair dados do item: {e}")
                
                # Pausa entre requisições
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Erro ao processar página {page}: {e}")
                continue
                
        return concursos
    
    def is_valid_concurso(self, concurso_data):
        """Valida se os dados extraídos representam um concurso real"""
        titulo = concurso_data.get('titulo', '').lower()
        
        # Filtros para excluir elementos que não são concursos
        invalid_patterns = [
            'região', 'estado', 'cadastre', 'login', 'menu', 'header', 'footer',
            'navegação', 'buscar', 'filtro', 'página', 'voltar', 'próximo'
        ]
        
        for pattern in invalid_patterns:
            if pattern in titulo:
                return False
        
        # Deve ter pelo menos 15 caracteres e conter palavras-chave de concurso
        if len(titulo) < 15:
            return False
            
        valid_keywords = ['concurso', 'edital', 'seleção', 'processo', 'prefeitura', 'tribunal', 'ministério', 'secretaria']
        if not any(keyword in titulo for keyword in valid_keywords):
            return False
            
        return True
    
    def extract_concurso_data(self, item, soup):
        """Extrai dados de um concurso específico"""
        try:
            # Tentar extrair título
            titulo = ""
            link = ""
            
            if item.name == 'a':
                titulo = item.get_text(strip=True)
                link = item.get('href', '')
            else:
                # Procurar link dentro do item
                link_elem = item.find('a')
                if link_elem:
                    titulo = link_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                else:
                    titulo = item.get_text(strip=True)
            
            if not titulo or len(titulo) < 10:
                return None
                
            # Normalizar link
            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)
            
            # Extrair informações adicionais do contexto
            orgao = self.extract_orgao(titulo, item)
            cargo = self.extract_cargo(titulo, item)
            vagas = self.extract_vagas(titulo, item)
            salario = self.extract_salario(titulo, item)
            local = self.extract_local(titulo, item)
            data_publicacao = self.extract_data(item)
            
            return {
                'id': f"pci_{hash(link) % 100000}",
                'titulo': titulo,
                'orgao': orgao,
                'cargo': cargo,
                'ano': '2025',  # Ano atual
                'tipo_documento': 'edital',
                'url': link,
                'data_publicacao': data_publicacao,
                'fonte': 'PCI Concursos Real',
                'vagas': str(vagas) if vagas else 'N/A',
                'salario': salario,
                'local': local,
                'regiao': self.extract_regiao(local),
                'estado': self.extract_estado(local),
                'status': 'aberto',
                'escolaridade': self.extract_escolaridade_basica(titulo, cargo),
                'taxa_inscricao': self.extract_taxa_basica(titulo),
                'inicio_inscricoes': 'Consultar edital',
                'fim_inscricoes': 'Consultar edital',
                'data_prova': 'Consultar edital',
                'prazo_inscricoes': 'Consultar edital',
                'dias_restantes': 0,
                'nivel': self.extract_escolaridade_basica(titulo, cargo),
                'tipo': 'ABERTO',
                'urgencia': 'normal',
                'conteudo': titulo  # Conteúdo básico para busca
            }
            
        except Exception as e:
            logger.warning(f"Erro ao extrair dados: {e}")
            return None
    
    def extract_orgao(self, titulo, item):
        """Extrai nome do órgão"""
        # Padrões comuns de órgãos
        orgaos_patterns = [
            r'(Prefeitura\s+(?:Municipal\s+)?de\s+[\w\s]+)',
            r'(Tribunal\s+[\w\s]+)',
            r'(Ministério\s+[\w\s]+)',
            r'(Secretaria\s+[\w\s]+)',
            r'(Instituto\s+[\w\s]+)',
            r'(Fundação\s+[\w\s]+)',
            r'(Universidade\s+[\w\s]+)',
            r'(Câmara\s+[\w\s]+)',
            r'(Assembleia\s+[\w\s]+)',
            r'(Polícia\s+[\w\s]+)',
            r'(Bombeiros\s+[\w\s]+)',
            r'(INSS)',
            r'(Receita\s+Federal)',
            r'(Banco\s+Central)',
            r'(IBGE)',
            r'(CGU)',
            r'(TCU)',
            r'(STF|STJ|TST|TSE)',
        ]
        
        for pattern in orgaos_patterns:
            match = re.search(pattern, titulo, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Se não encontrou padrão específico, tentar extrair primeira parte
        words = titulo.split()
        if len(words) >= 3:
            return ' '.join(words[:3])
        
        return "Órgão não identificado"
    
    def extract_cargo(self, titulo, item):
        """Extrai cargo/função"""
        # Padrões comuns de cargos
        cargos_patterns = [
            r'(Analista\s+[\w\s]*)',
            r'(Técnico\s+[\w\s]*)',
            r'(Auxiliar\s+[\w\s]*)',
            r'(Assistente\s+[\w\s]*)',
            r'(Agente\s+[\w\s]*)',
            r'(Inspetor\s+[\w\s]*)',
            r'(Professor\s+[\w\s]*)',
            r'(Procurador\s+[\w\s]*)',
            r'(Auditor\s+[\w\s]*)',
            r'(Fiscal\s+[\w\s]*)',
            r'(Especialista\s+[\w\s]*)',
            r'(Coordenador\s+[\w\s]*)',
            r'(Diretor\s+[\w\s]*)',
        ]
        
        for pattern in cargos_patterns:
            match = re.search(pattern, titulo, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Diversos Cargos"
    
    def extract_vagas(self, titulo, item):
        """Extrai número de vagas"""
        # Padrões para vagas
        vagas_patterns = [
            r'(\d+)\s*vagas?',
            r'vagas?\s*:?\s*(\d+)',
            r'(\d+)\s*oportunidades?',
        ]
        
        for pattern in vagas_patterns:
            match = re.search(pattern, titulo, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def extract_salario(self, titulo, item):
        """Extrai informação de salário"""
        # Padrões para salário
        salario_patterns = [
            r'R\$\s*[\d.,]+',
            r'salário\s*:?\s*R\$\s*[\d.,]+',
            r'remuneração\s*:?\s*R\$\s*[\d.,]+',
        ]
        
        for pattern in salario_patterns:
            match = re.search(pattern, titulo, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Não informado"
    
    def extract_local(self, titulo, item):
        """Extrai localização"""
        # Padrões para estados/cidades
        estados = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
        
        for estado in estados:
            if f' {estado}' in titulo or f'-{estado}' in titulo:
                return estado
        
        return "Nacional"
    
    def extract_data(self, item):
        """Extrai data de publicação"""
        try:
            # Procurar por datas no formato brasileiro
            date_patterns = [
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}-\d{1,2}-\d{4})',
            ]
            
            text = item.get_text() if hasattr(item, 'get_text') else str(item)
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
            
        except:
            pass
        
        return datetime.now().strftime('%d/%m/%Y')
    
    def scrape_detailed_info(self, concurso_url):
        """Extrai informações detalhadas de um concurso específico"""
        try:
            logger.info(f"Extraindo detalhes de: {concurso_url}")
            response = self.session.get(concurso_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrair informações detalhadas
            detalhes = {
                'descricao': '',
                'requisitos': '',
                'inscricoes': '',
                'provas': '',
            }
            
            # Procurar por conteúdo principal
            content_areas = soup.find_all(['div', 'p', 'span'], text=re.compile(r'requisitos?|inscrições?|provas?|salário', re.I))
            
            for area in content_areas:
                text = area.get_text(strip=True)
                if 'requisito' in text.lower():
                    detalhes['requisitos'] = text
                elif 'inscrição' in text.lower():
                    detalhes['inscricoes'] = text
                elif 'prova' in text.lower():
                    detalhes['provas'] = text
            
            return detalhes
            
        except Exception as e:
            logger.warning(f"Erro ao extrair detalhes de {concurso_url}: {e}")
            return {}
    
    def save_to_csv(self, concursos, filename="pci_concursos.csv"):
        """Salva os dados em CSV"""
        if not concursos:
            logger.warning("Nenhum concurso para salvar")
            return
        
        df = pd.DataFrame(concursos)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Salvos {len(concursos)} concursos em {filename}")
        
        return filename
    
    def run_full_scrape(self, max_pages=3, save_csv=True):
        """Executa scraping completo"""
        logger.info("Iniciando scraping completo do PCI Concursos...")
        
        try:
            # Extrair lista de concursos
            concursos = self.get_concursos_list(max_pages=max_pages)
            
            if not concursos:
                logger.warning("Nenhum concurso encontrado")
                return []
            
            logger.info(f"Encontrados {len(concursos)} concursos")
            
            # Enriquecer dados com informações detalhadas (apenas alguns para não sobrecarregar)
            for i, concurso in enumerate(concursos[:10]):  # Apenas os 10 primeiros
                if concurso.get('url'):
                    detalhes = self.scrape_detailed_info(concurso['url'])
                    concurso.update(detalhes)
                    time.sleep(3)  # Pausa maior para detalhes
            
            # Salvar em CSV se solicitado
            if save_csv:
                self.save_to_csv(concursos, "concursos_chunks.csv")
            
            return concursos
            
        except Exception as e:
            logger.error(f"Erro no scraping completo: {e}")
            return []
    
    def extract_regiao(self, local):
        """Extrai região com base no estado/local"""
        regioes_estados = {
            "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO", "Acre", "Amapá", "Amazonas", "Pará", "Rondônia", "Roraima", "Tocantins"],
            "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE", "Alagoas", "Bahia", "Ceará", "Maranhão", "Paraíba", "Pernambuco", "Piauí", "Rio Grande do Norte", "Sergipe"],
            "Centro-Oeste": ["DF", "GO", "MT", "MS", "Distrito Federal", "Goiás", "Mato Grosso", "Mato Grosso do Sul"],
            "Sudeste": ["ES", "MG", "RJ", "SP", "Espírito Santo", "Minas Gerais", "Rio de Janeiro", "São Paulo"],
            "Sul": ["PR", "RS", "SC", "Paraná", "Rio Grande do Sul", "Santa Catarina"]
        }
        
        if not local:
            return "Nacional"
            
        local_upper = local.upper()
        for regiao, estados in regioes_estados.items():
            for estado in estados:
                if estado.upper() in local_upper:
                    return regiao
        return "Nacional"
    
    def extract_estado(self, local):
        """Extrai estado do local"""
        estados = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
        
        if not local:
            return "Nacional"
            
        local_upper = local.upper()
        for estado in estados:
            if estado in local_upper:
                return estado
        return "Nacional"
    
    def extract_escolaridade_basica(self, titulo, cargo):
        """Extrai escolaridade básica do título/cargo"""
        texto = f"{titulo} {cargo}".lower()
        
        if any(word in texto for word in ["superior", "graduação", "bacharel", "licenciatura", "analista", "auditor", "procurador"]):
            return "Ensino Superior"
        elif any(word in texto for word in ["técnico", "médio"]):
            return "Ensino Médio"
        elif any(word in texto for word in ["fundamental", "auxiliar"]):
            return "Ensino Fundamental"
        else:
            return "Consultar edital"
    
    def extract_taxa_basica(self, titulo):
        """Extrai taxa básica estimada"""
        texto = titulo.lower()
        
        if any(word in texto for word in ["superior", "analista", "auditor", "procurador"]):
            return "R$ 80,00 - R$ 120,00"
        elif any(word in texto for word in ["técnico", "médio"]):
            return "R$ 50,00 - R$ 80,00"
        else:
            return "Consultar edital"

def main():
    """Função principal para teste"""
    scraper = PCIScraper()
    concursos = scraper.run_full_scrape(max_pages=2)
    
    print(f"\n=== RESULTADO DO SCRAPING ===")
    print(f"Total de concursos coletados: {len(concursos)}")
    
    for i, concurso in enumerate(concursos[:5]):  # Mostrar apenas os 5 primeiros
        print(f"\n{i+1}. {concurso['titulo']}")
        print(f"   Órgão: {concurso['orgao']}")
        print(f"   Cargo: {concurso['cargo']}")
        print(f"   Vagas: {concurso['vagas']}")
        print(f"   Local: {concurso['local']}")

if __name__ == "__main__":
    main()
