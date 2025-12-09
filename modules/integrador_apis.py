#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integração com APIs externas de concursos públicos"""

import requests
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import time

# Importação opcional para aiohttp
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None
    AIOHTTP_AVAILABLE = False
    print("⚠️ aiohttp não disponível - usando requests síncronos")

class IntegradorAPIsExternas:
    """Integra com múltiplas APIs de concursos públicos"""
    
    def __init__(self):
        self.setup_logging()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # URLs das APIs
        self.concursos_brasil_base_url = "https://concursos-publicos-api.herokuapp.com"
        
        # Códigos de estados conforme a API
        self.codigos_estados = {
            'NACIONAL': 'br',
            'ACRE': 'ac',
            'ALAGOAS': 'al', 
            'AMAPA': 'ap',
            'AMAZONAS': 'am',
            'BAHIA': 'ba',
            'CEARA': 'ce',
            'DISTRITO_FEDERAL': 'df',
            'ESPIRITO_SANTO': 'es',
            'GOIAS': 'go',
            'MARANHAO': 'ma',
            'MATO_GROSSO': 'mt',
            'MATO_GROSSO_SUL': 'ms',
            'MINAS_GERAIS': 'mg',
            'PARA': 'pa',
            'PARAIBA': 'pb',
            'PARANA': 'pr',
            'PERNAMBUCO': 'pe',
            'PIAUI': 'pi',
            'RIO_JANEIRO': 'rj',
            'RIO_GRANDE_NORTE': 'rn',
            'RIO_GRANDE_SUL': 'rs',
            'RONDONIA': 'ro',
            'RORAIMA': 'rr',
            'SANTA_CATARINA': 'sc',
            'SAO_PAULO': 'sp',
            'SERGIPE': 'se',
            'TOCANTINS': 'to'
        }
    
    def setup_logging(self):
        """Configura logging"""
        self.logger = logging.getLogger(__name__)
    
    # === API CONCURSOS PÚBLICOS BRASIL ===
    # Baseado em: https://github.com/Vinimartinsc/concursosPublicosAPI
    
    def coletar_concursos_brasil_api(self, estados: List[str] = None) -> List[Dict[str, Any]]:
        """
        Coleta dados da API concursosPublicosAPI
        
        Estrutura esperada da API:
        {
          "link": "https://......",
          "organization": "Banco Estadual X",
          "status": "open|closed|expected",
          "workPlacesAvailable": "7.000"
        }
        """
        try:
            if not estados:
                estados = ['sp', 'rj', 'mg', 'rs', 'pr', 'sc', 'br']  # Estados principais
            
            concursos_coletados = []
            
            # URLs alternativas para tentar
            urls_base = [
                "https://concursos-publicos-api.herokuapp.com",
                "https://concursospublicosapi.herokuapp.com",
                # Fallback: scraping direto do site
                "direct_scraping"
            ]
            
            for estado in estados:
                try:
                    self.logger.info(f"🔍 Coletando concursos do estado: {estado.upper()}")
                    
                    sucesso = False
                    for url_base in urls_base:
                        try:
                            if url_base == "direct_scraping":
                                # Implementar scraping direto como fallback
                                concursos_estado = self._scraper_concursos_direto(estado)
                                if concursos_estado:
                                    concursos_coletados.extend(concursos_estado)
                                    sucesso = True
                                    break
                            else:
                                # Tentar API externa
                                url = f"{url_base}/concursos/{estado}"
                                
                                response = self.session.get(url, timeout=15)
                                
                                if response.status_code == 200:
                                    dados = response.json()
                                    
                                    if dados:  # Verificar se retornou dados
                                        for concurso in dados:
                                            concurso_processado = self._processar_concurso_brasil_api(concurso, estado)
                                            if concurso_processado:
                                                concursos_coletados.append(concurso_processado)
                                        
                                        self.logger.info(f"✅ Coletados {len(dados)} concursos para {estado} via {url_base}")
                                        sucesso = True
                                        break
                                    else:
                                        self.logger.warning(f"API {url_base} retornou lista vazia para {estado}")
                                else:
                                    self.logger.warning(f"API {url_base} erro {response.status_code} para {estado}")
                        
                        except Exception as e:
                            self.logger.warning(f"Erro tentando URL {url_base}: {e}")
                            continue
                    
                    if not sucesso:
                        self.logger.warning(f"❌ Nenhuma fonte funcionou para estado {estado}")
                    
                    # Pausa entre requisições
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao coletar estado {estado}: {e}")
                    continue
            
            self.logger.info(f"Coletados {len(concursos_coletados)} concursos da API Brasil")
            return concursos_coletados
            
        except Exception as e:
            self.logger.error(f"Erro geral na coleta Brasil API: {e}")
            return []
    
    def _processar_concurso_brasil_api(self, concurso: Dict, estado: str) -> Optional[Dict[str, Any]]:
        """Processa um concurso da API Brasil"""
        try:
            return {
                'titulo': f"Concurso {concurso.get('organization', 'Órgão')} - {estado.upper()}",
                'orgao': concurso.get('organization', 'Não informado'),
                'cargo': 'Múltiplos cargos',  # A API não fornece cargo específico
                'ano': str(datetime.now().year),
                'tipo_documento': 'edital',
                'url': concurso.get('link', ''),
                'data_publicacao': datetime.now().strftime('%Y-%m-%d'),
                'fonte': 'ConcursosNoBrasil.com via API',
                'conteudo': f"Concurso público para {concurso.get('organization', '')}. "
                           f"Status: {concurso.get('status', 'aberto')}. "
                           f"Vagas disponíveis: {concurso.get('workPlacesAvailable', 'Não informado')}. "
                           f"Estado: {estado.upper()}. "
                           f"Link: {concurso.get('link', '')}",
                'vagas': concurso.get('workPlacesAvailable', 'Não informado'),
                'status': concurso.get('status', 'open'),
                'estado': estado.upper()
            }
        except Exception as e:
            self.logger.error(f"Erro ao processar concurso: {e}")
            return None
    
    def _scraper_concursos_direto(self, estado: str) -> List[Dict[str, Any]]:
        """
        Scraping direto do site ConcursosNoBrasil.com como fallback
        """
        try:
            self.logger.info(f"🔄 Fazendo scraping direto para estado: {estado}")
            
            url = f"https://concursosnobrasil.com/concursos/{estado}"
            
            response = self.session.get(url, timeout=20)
            
            if response.status_code != 200:
                self.logger.warning(f"Erro no scraping direto: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Procurar pela tabela de concursos
            concursos_list = []
            
            # Tentar diferentes seletores
            tabela_concursos = soup.find('div', class_='list-concursos')
            if not tabela_concursos:
                tabela_concursos = soup.find('table', class_='table')
            
            if tabela_concursos:
                rows = tabela_concursos.find_all('tr')[1:]  # Pular header
                
                for row in rows:
                    try:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            link_element = row.find('a')
                            
                            if link_element:
                                concurso = {
                                    'organization': link_element.text.strip(),
                                    'workPlacesAvailable': cols[1].text.strip() if len(cols) > 1 else 'Não informado',
                                    'link': link_element.get('href', ''),
                                    'status': 'open'  # Assumir aberto se não especificado
                                }
                                
                                # Verificar se tem indicador de status
                                if row.find('span', class_='label-previsto'):
                                    concurso['status'] = 'expected'
                                
                                concurso_processado = self._processar_concurso_brasil_api(concurso, estado)
                                if concurso_processado:
                                    concursos_list.append(concurso_processado)
                    
                    except Exception as e:
                        self.logger.warning(f"Erro processando linha: {e}")
                        continue
            
            self.logger.info(f"✅ Scraping direto coletou {len(concursos_list)} concursos para {estado}")
            return concursos_list
            
        except Exception as e:
            self.logger.error(f"Erro no scraping direto: {e}")
            return []

    # === PCI CONCURSOS SCRAPER ===
    
    def coletar_pci_concursos_avancado(self) -> List[Dict[str, Any]]:
        """
        Coleta avançada do PCI Concursos
        Baseado em: https://github.com/luiseduardobr1/PCIConcursos
        """
        try:
            self.logger.info("Iniciando coleta avançada PCI Concursos...")
            
            # URLs principais do PCI
            urls_pci = [
                "https://www.pciconcursos.com.br/concursos/",
                "https://www.pciconcursos.com.br/concursos/federal",
                "https://www.pciconcursos.com.br/concursos/estadual",
                "https://www.pciconcursos.com.br/concursos/municipal"
            ]
            
            concursos_coletados = []
            
            for url in urls_pci:
                try:
                    concursos_pagina = self._extrair_pci_pagina(url)
                    concursos_coletados.extend(concursos_pagina)
                    time.sleep(2)  # Pausa entre páginas
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar URL {url}: {e}")
                    continue
            
            # Remover duplicatas
            concursos_unicos = self._remover_duplicatas_pci(concursos_coletados)
            
            self.logger.info(f"Coletados {len(concursos_unicos)} concursos únicos do PCI")
            return concursos_unicos
            
        except Exception as e:
            self.logger.error(f"Erro geral na coleta PCI: {e}")
            return []
    
    def _extrair_pci_pagina(self, url: str) -> List[Dict[str, Any]]:
        """Extrai concursos de uma página do PCI"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            concursos = []
            
            # Seletores baseados na estrutura do PCI
            cards_concurso = soup.find_all('div', class_='ca')  # Card de concurso
            
            for card in cards_concurso:
                try:
                    concurso = self._processar_card_pci(card)
                    if concurso:
                        concursos.append(concurso)
                except Exception as e:
                    self.logger.debug(f"Erro ao processar card: {e}")
                    continue
            
            return concursos
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair página {url}: {e}")
            return []
    
    def _processar_card_pci(self, card) -> Optional[Dict[str, Any]]:
        """Processa um card de concurso do PCI"""
        try:
            # Extrair título/órgão
            titulo_elem = card.find('h3') or card.find('a', class_='titulo')
            titulo = titulo_elem.get_text(strip=True) if titulo_elem else 'Título não encontrado'
            
            # Extrair link
            link_elem = card.find('a')
            link = link_elem.get('href', '') if link_elem else ''
            if link and not link.startswith('http'):
                link = f"https://www.pciconcursos.com.br{link}"
            
            # Extrair informações adicionais
            info_divs = card.find_all('div', class_='cs')
            
            orgao = 'Não informado'
            vagas = 'Não informado'
            salario = 'Não informado'
            inscricoes = 'Não informado'
            
            for div in info_divs:
                texto = div.get_text(strip=True).lower()
                
                if 'órgão' in texto or 'banca' in texto:
                    orgao = div.get_text(strip=True).replace('Órgão:', '').replace('Banca:', '').strip()
                elif 'vagas' in texto:
                    vagas = div.get_text(strip=True).replace('Vagas:', '').strip()
                elif 'salário' in texto or 'vencimento' in texto:
                    salario = div.get_text(strip=True).replace('Salário:', '').replace('Vencimento:', '').strip()
                elif 'inscrição' in texto:
                    inscricoes = div.get_text(strip=True)
            
            # Extrair cargo do título
            cargo = self._extrair_cargo_titulo(titulo)
            
            return {
                'titulo': titulo,
                'orgao': orgao,
                'cargo': cargo,
                'ano': str(datetime.now().year),
                'tipo_documento': 'edital',
                'url': link,
                'data_publicacao': datetime.now().strftime('%Y-%m-%d'),
                'fonte': 'PCI Concursos',
                'conteudo': f"{titulo}. Órgão: {orgao}. Vagas: {vagas}. "
                           f"Salário: {salario}. Inscrições: {inscricoes}. "
                           f"Link: {link}",
                'vagas': vagas,
                'salario': salario,
                'inscricoes': inscricoes
            }
            
        except Exception as e:
            self.logger.debug(f"Erro ao processar card PCI: {e}")
            return None
    
    def _extrair_cargo_titulo(self, titulo: str) -> str:
        """Extrai cargo do título do concurso"""
        # Palavras-chave comuns para cargos
        cargos_comuns = [
            'analista', 'técnico', 'auxiliar', 'assistente', 'professor',
            'enfermeiro', 'médico', 'advogado', 'contador', 'engenheiro',
            'auditor', 'fiscal', 'agente', 'especialista', 'consultor',
            'coordenador', 'supervisor', 'gerente', 'diretor'
        ]
        
        titulo_lower = titulo.lower()
        
        for cargo in cargos_comuns:
            if cargo in titulo_lower:
                return cargo.title()
        
        return 'Múltiplos cargos'
    
    def _remover_duplicatas_pci(self, concursos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove concursos duplicados baseado no título"""
        titulos_vistos = set()
        concursos_unicos = []
        
        for concurso in concursos:
            titulo = concurso.get('titulo', '')
            if titulo and titulo not in titulos_vistos:
                titulos_vistos.add(titulo)
                concursos_unicos.append(concurso)
        
        return concursos_unicos
    
    # === DADOS GOVERNAMENTAIS ===
    
    def coletar_dados_gov(self) -> List[Dict[str, Any]]:
        """Coleta dados de APIs governamentais (placeholder)"""
        try:
            self.logger.info("🏛️ Coletando dados governamentais...")
            
            # Placeholder para integração futura com APIs do governo
            # Pode incluir: dados.gov.br, Portal da Transparência, etc.
            
            dados_gov = [
                {
                    'titulo': 'Concurso Governamental - Exemplo',
                    'orgao': 'Órgão Federal',
                    'cargo': 'Servidor Público',
                    'ano': str(datetime.now().year),
                    'tipo_documento': 'edital',
                    'url': 'https://dados.gov.br',
                    'data_publicacao': datetime.now().strftime('%Y-%m-%d'),
                    'fonte': 'Dados.gov.br',
                    'conteudo': 'Exemplo de dados governamentais'
                }
            ]
            
            return dados_gov
            
        except Exception as e:
            self.logger.error(f"Erro na coleta governamental: {e}")
            return []
    
    # === COLETA COMBINADA ===
    
    def coletar_todas_fontes(self) -> List[Dict[str, Any]]:
        """Executa coleta de todas as fontes integradas"""
        try:
            self.logger.info("🚀 Iniciando coleta combinada de todas as fontes...")
            
            todos_concursos = []
            
            # 1. API Concursos Brasil
            try:
                concursos_brasil = self.coletar_concursos_brasil_api()
                todos_concursos.extend(concursos_brasil)
                self.logger.info(f"✅ API Brasil: {len(concursos_brasil)} concursos")
            except Exception as e:
                self.logger.error(f"❌ Erro API Brasil: {e}")
            
            # 2. PCI Concursos
            try:
                concursos_pci = self.coletar_pci_concursos_avancado()
                todos_concursos.extend(concursos_pci)
                self.logger.info(f"✅ PCI Concursos: {len(concursos_pci)} concursos")
            except Exception as e:
                self.logger.error(f"❌ Erro PCI: {e}")
            
            # 3. Dados Governamentais
            try:
                concursos_gov = self.coletar_dados_gov()
                todos_concursos.extend(concursos_gov)
                self.logger.info(f"✅ Dados Gov: {len(concursos_gov)} concursos")
            except Exception as e:
                self.logger.error(f"❌ Erro Dados Gov: {e}")
            
            # Remover duplicatas globais
            concursos_finais = self._remover_duplicatas_globais(todos_concursos)
            
            self.logger.info(f"🎯 Total final: {len(concursos_finais)} concursos únicos")
            return concursos_finais
            
        except Exception as e:
            self.logger.error(f"Erro na coleta combinada: {e}")
            return []
    
    def _remover_duplicatas_globais(self, concursos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicatas globais baseado em título e órgão"""
        chaves_vistas = set()
        concursos_unicos = []
        
        for concurso in concursos:
            chave = f"{concurso.get('titulo', '')}-{concurso.get('orgao', '')}"
            if chave not in chaves_vistas:
                chaves_vistas.add(chave)
                concursos_unicos.append(concurso)
        
        return concursos_unicos
    
    # === SALVAMENTO ===
    
    def salvar_dados_coletados(self, concursos: List[Dict[str, Any]], arquivo: str = "concursos_integrados.csv") -> bool:
        """Salva dados coletados em CSV"""
        try:
            if not concursos:
                self.logger.warning("Nenhum concurso para salvar")
                return False
            
            df = pd.DataFrame(concursos)
            df.to_csv(arquivo, index=False, encoding='utf-8')
            
            self.logger.info(f"💾 Dados salvos em {arquivo}: {len(concursos)} concursos")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados: {e}")
            return False

# === CLASSE PARA INTEGRAÇÃO COM FASTAPI ===

class IntegradorFastAPI:
    """Integra o coletor externo com a FastAPI"""
    
    def __init__(self):
        self.integrador = IntegradorAPIsExternas()
    
    async def coletar_async(self, fontes: List[str] = None) -> Dict[str, Any]:
        """Executa coleta assíncrona"""
        try:
            # Executar em thread separada para não bloquear FastAPI
            loop = asyncio.get_event_loop()
            
            if not fontes:
                fontes = ['brasil_api', 'pci']
            
            concursos = []
            
            if 'brasil_api' in fontes:
                concursos_brasil = await loop.run_in_executor(
                    None, 
                    self.integrador.coletar_concursos_brasil_api
                )
                concursos.extend(concursos_brasil)
            
            if 'pci' in fontes:
                concursos_pci = await loop.run_in_executor(
                    None,
                    self.integrador.coletar_pci_concursos_avancado
                )
                concursos.extend(concursos_pci)
            
            # Salvar dados
            sucesso_salvamento = await loop.run_in_executor(
                None,
                self.integrador.salvar_dados_coletados,
                concursos,
                "concursos_chunks.csv"
            )
            
            return {
                'total_coletado': len(concursos),
                'fontes_utilizadas': fontes,
                'salvo_com_sucesso': sucesso_salvamento,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_coletado': 0,
                'timestamp': datetime.now().isoformat()
            }

# === TESTE STANDALONE ===

if __name__ == "__main__":
    # Teste do integrador
    integrador = IntegradorAPIsExternas()
    
    print("🧪 Testando integração com APIs externas...")
    
    # Teste 1: API Brasil (se disponível)
    print("\n1️⃣ Testando API Concursos Brasil...")
    try:
        concursos_brasil = integrador.coletar_concursos_brasil_api(['sp', 'rj'])
        print(f"   📊 Coletados: {len(concursos_brasil)} concursos")
        if concursos_brasil:
            print(f"   📝 Exemplo: {concursos_brasil[0]['titulo']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 2: PCI Concursos
    print("\n2️⃣ Testando PCI Concursos...")
    try:
        concursos_pci = integrador.coletar_pci_concursos_avancado()
        print(f"   📊 Coletados: {len(concursos_pci)} concursos")
        if concursos_pci:
            print(f"   📝 Exemplo: {concursos_pci[0]['titulo']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 3: Coleta combinada
    print("\n3️⃣ Testando coleta combinada...")
    try:
        todos_concursos = integrador.coletar_todas_fontes()
        sucesso = integrador.salvar_dados_coletados(todos_concursos)
        print(f"   📊 Total coletado: {len(todos_concursos)} concursos")
        print(f"   💾 Salvamento: {'✅ Sucesso' if sucesso else '❌ Falha'}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n✅ Teste concluído!")
