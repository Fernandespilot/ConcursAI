#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo de coleta de dados em tempo real para o sistema ConcursAI"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import re
from typing import List, Dict

# Importar integrador de APIs externas
try:
    from .integrador_apis import IntegradorAPIsExternas
except ImportError:
    # Fallback para execução standalone
    try:
        from integrador_apis import IntegradorAPIsExternas
    except ImportError:
        print("⚠️ IntegradorAPIsExternas não disponível")
        IntegradorAPIsExternas = None

class ColetorConcursosRealTime:
    """Coletor de concursos em tempo real com fontes verificadas"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.dados_coletados = []
        
        # Inicializar integrador de APIs externas
        self.integrador_apis = IntegradorAPIsExternas() if IntegradorAPIsExternas else None
    
    def coletar_pci_simples(self) -> List[Dict]:
        """Coleta dados do PCI de forma mais simples e funcional"""
        try:
            print("🔄 Coletando dados do PCI Concursos...")
            
            url = "https://www.pciconcursos.com.br/concursos/"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                # Usar regex para extrair informações básicas
                html = response.text
                
                # Buscar padrões de concursos
                padroes_concursos = [
                    r'<a[^>]*href="([^"]*concurso[^"]*)"[^>]*>([^<]{20,100})</a>',
                    r'<h[1-6][^>]*>([^<]*(?:concurso|edital)[^<]*)</h[1-6]>',
                    r'title="([^"]*(?:concurso|prefeitura|tribunal)[^"]*)"'
                ]
                
                concursos = []
                for padrao in padroes_concursos:
                    matches = re.findall(padrao, html, re.IGNORECASE)
                    for match in matches[:10]:  # Limitar resultados
                        if isinstance(match, tuple) and len(match) >= 2:
                            link, titulo = match[0], match[1]
                            if len(titulo.strip()) > 15:
                                concurso = {
                                    'titulo': titulo.strip(),
                                    'url': f"https://www.pciconcursos.com.br{link}" if not link.startswith('http') else link,
                                    'fonte': 'PCI Concursos',
                                    'data_coleta': datetime.now().strftime('%Y-%m-%d'),
                                    'orgao': self._extrair_orgao_titulo(titulo),
                                    'ano': '2024'
                                }
                                concursos.append(concurso)
                
                print(f"✅ {len(concursos)} concursos encontrados no PCI")
                return concursos
            
            return []
            
        except Exception as e:
            print(f"⚠️ Erro no PCI: {e}")
            return []
    
    def coletar_gran_cursos(self) -> List[Dict]:
        """Coleta dados do Gran Cursos Online"""
        try:
            print("🔄 Coletando dados do Gran Cursos...")
            
            url = "https://www.grancursosonline.com.br/concursos"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                concursos = []
                # Buscar diferentes seletores
                elementos = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'concurso|contest'))
                
                for elem in elementos[:15]:
                    try:
                        texto = elem.get_text()
                        if len(texto) > 50 and any(palavra in texto.lower() for palavra in ['concurso', 'edital', 'vagas']):
                            titulo = texto[:100].strip()
                            
                            concurso = {
                                'titulo': titulo,
                                'url': url,
                                'fonte': 'Gran Cursos',
                                'data_coleta': datetime.now().strftime('%Y-%m-%d'),
                                'orgao': self._extrair_orgao_titulo(titulo),
                                'ano': '2024',
                                'conteudo': texto[:500]
                            }
                            concursos.append(concurso)
                    except:
                        continue
                
                print(f"✅ {len(concursos)} concursos encontrados no Gran Cursos")
                return concursos
            
            return []
            
        except Exception as e:
            print(f"⚠️ Erro no Gran Cursos: {e}")
            return []
    
    def coletar_folha_dirigida(self) -> List[Dict]:
        """Coleta dados da Folha Dirigida"""
        try:
            print("🔄 Coletando dados da Folha Dirigida...")
            
            url = "https://folhadirigida.com.br/concursos"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                concursos = []
                # Buscar links e títulos
                links = soup.find_all('a', href=re.compile(r'concurso'))
                
                for link in links[:20]:
                    try:
                        titulo = link.get_text(strip=True)
                        href = link.get('href', '')
                        
                        if len(titulo) > 20:
                            if not href.startswith('http'):
                                href = f"https://folhadirigida.com.br{href}"
                            
                            concurso = {
                                'titulo': titulo,
                                'url': href,
                                'fonte': 'Folha Dirigida',
                                'data_coleta': datetime.now().strftime('%Y-%m-%d'),
                                'orgao': self._extrair_orgao_titulo(titulo),
                                'ano': '2024'
                            }
                            concursos.append(concurso)
                    except:
                        continue
                
                print(f"✅ {len(concursos)} concursos encontrados na Folha Dirigida")
                return concursos
            
            return []
            
        except Exception as e:
            print(f"⚠️ Erro na Folha Dirigida: {e}")
            return []
    
    def _extrair_orgao_titulo(self, titulo: str) -> str:
        """Extrai órgão do título"""
        titulo_upper = titulo.upper()
        
        padroes = [
            r'(PREFEITURA[^,;.]*)',
            r'(CÂMARA[^,;.]*)',
            r'(TRIBUNAL[^,;.]*)',
            r'(MINISTÉRIO[^,;.]*)',
            r'(SECRETARIA[^,;.]*)',
            r'(INSTITUTO[^,;.]*)',
            r'(FUNDAÇÃO[^,;.]*)',
            r'(BANCO[^,;.]*)',
            r'(UNIVERSIDADE[^,;.]*)'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, titulo_upper)
            if match:
                return match.group(1).strip()
        
        # Se não encontrar, pegar as primeiras palavras
        palavras = titulo.split()[:3]
        return ' '.join(palavras) if palavras else "Órgão não identificado"
    
    def coletar_todos(self) -> List[Dict]:
        """Coleta de todas as fontes com prioridade para API ConcursosNoBrasil"""
        print("🚀 Iniciando coleta completa de todas as fontes...")
        
        todos_concursos = []
        
        # 1. API ConcursosNoBrasil (PRIORIDADE MÁXIMA)
        if self.integrador_apis:
            print("📡 Coletando da API ConcursosNoBrasil...")
            try:
                concursos_api = self.integrador_apis.coletar_concursos_brasil_api()
                if concursos_api:
                    todos_concursos.extend(concursos_api)
                    print(f"✅ API ConcursosNoBrasil: {len(concursos_api)} concursos")
                else:
                    print("⚠️ API ConcursosNoBrasil: Nenhum dado retornado")
            except Exception as e:
                print(f"❌ Erro na API ConcursosNoBrasil: {e}")
        
        # 2. PCI Concursos (Backup)
        print("📄 Coletando do PCI Concursos...")
        try:
            concursos_pci = self.coletar_pci_simples()
            if concursos_pci:
                todos_concursos.extend(concursos_pci)
                print(f"✅ PCI Concursos: {len(concursos_pci)} concursos")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Erro no PCI Concursos: {e}")
        
        # 3. Gran Cursos
        print("📚 Coletando do Gran Cursos...")
        try:
            concursos_gran = self.coletar_gran_cursos()
            if concursos_gran:
                todos_concursos.extend(concursos_gran)
                print(f"✅ Gran Cursos: {len(concursos_gran)} concursos")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Erro no Gran Cursos: {e}")
        
        # 4. Folha Dirigida
        print("📰 Coletando da Folha Dirigida...")
        try:
            concursos_folha = self.coletar_folha_dirigida()
            if concursos_folha:
                todos_concursos.extend(concursos_folha)
                print(f"✅ Folha Dirigida: {len(concursos_folha)} concursos")
        except Exception as e:
            print(f"❌ Erro na Folha Dirigida: {e}")
        
        # Remover duplicatas
        todos_concursos = self._remover_duplicatas(todos_concursos)
        
        print(f"🎉 Total coletado: {len(todos_concursos)} concursos únicos")
        return todos_concursos
    
    def coletar_apenas_api_brasil(self) -> List[Dict]:
        """Coleta dados apenas da API ConcursosNoBrasil para teste rápido"""
        print("🔥 Testando API ConcursosNoBrasil...")
        
        if not self.integrador_apis:
            print("❌ Integrador de APIs não disponível")
            return []
        
        try:
            # Testar primeiro apenas alguns estados
            estados_teste = ['sp', 'rj', 'br']  # São Paulo, Rio de Janeiro e Nacional
            concursos = self.integrador_apis.coletar_concursos_brasil_api(estados_teste)
            
            if concursos:
                print(f"✅ API funcionando! Coletados {len(concursos)} concursos")
                
                # Mostrar exemplo
                if len(concursos) > 0:
                    print("📋 Exemplo de concurso coletado:")
                    exemplo = concursos[0]
                    print(f"   Título: {exemplo.get('titulo', 'N/A')}")
                    print(f"   Órgão: {exemplo.get('orgao', 'N/A')}")
                    print(f"   Estado: {exemplo.get('estado', 'N/A')}")
                    print(f"   Status: {exemplo.get('status', 'N/A')}")
                    print(f"   URL: {exemplo.get('url', 'N/A')[:50]}...")
                
                return concursos
            else:
                print("⚠️ API não retornou dados")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao testar API: {e}")
            return []
    
    def _remover_duplicatas(self, concursos: List[Dict]) -> List[Dict]:
        """Remove duplicatas baseado no título"""
        vistos = set()
        unicos = []
        
        for concurso in concursos:
            titulo_norm = re.sub(r'\s+', ' ', concurso['titulo'].lower().strip())
            if titulo_norm not in vistos and len(titulo_norm) > 10:
                vistos.add(titulo_norm)
                unicos.append(concurso)
        
        return unicos
    
    def salvar_csv(self, concursos: List[Dict], arquivo="concursos_chunks_real.csv"):
        """Salva dados coletados em CSV"""
        try:
            if not concursos:
                print("⚠️ Nenhum concurso para salvar")
                return False
            
            # Padronizar dados
            dados_padronizados = []
            for concurso in concursos:
                dado = {
                    'conteudo': concurso.get('conteudo', concurso.get('titulo', '')),
                    'titulo': concurso.get('titulo', ''),
                    'orgao': concurso.get('orgao', ''),
                    'ano': concurso.get('ano', '2024'),
                    'cargo': self._extrair_cargo_basico(concurso.get('titulo', '')),
                    'tipo_documento': 'edital',
                    'url': concurso.get('url', ''),
                    'data_publicacao': concurso.get('data_coleta', ''),
                    'fonte': concurso.get('fonte', '')
                }
                dados_padronizados.append(dado)
            
            df = pd.DataFrame(dados_padronizados)
            df.to_csv(arquivo, index=False, encoding='utf-8')
            print(f"✅ {len(dados_padronizados)} concursos salvos em {arquivo}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            return False
    
    def coletar_apis_integradas(self) -> List[Dict]:
        """Usa o integrador de APIs externas para coleta avançada"""
        try:
            if not self.integrador_apis:
                print("⚠️ Integrador de APIs não disponível")
                return []
            
            print("🔄 Coletando com APIs integradas...")
            
            # Coletar de todas as fontes
            concursos = self.integrador_apis.coletar_todas_fontes()
            
            print(f"✅ Coletados {len(concursos)} concursos das APIs integradas")
            return concursos
            
        except Exception as e:
            print(f"❌ Erro na coleta de APIs integradas: {e}")
            return []
    
    def coletar_brasil_api(self, estados: List[str] = None) -> List[Dict]:
        """Coleta específica da API Concursos Brasil"""
        try:
            if not self.integrador_apis:
                print("⚠️ Integrador de APIs não disponível")
                return []
            
            print("🇧🇷 Coletando da API Concursos Brasil...")
            
            if not estados:
                estados = ['sp', 'rj', 'mg', 'pr', 'rs', 'sc', 'br']
            
            concursos = self.integrador_apis.coletar_concursos_brasil_api(estados)
            
            print(f"✅ Coletados {len(concursos)} concursos da API Brasil")
            return concursos
            
        except Exception as e:
            print(f"❌ Erro na coleta API Brasil: {e}")
            return []
    
    def coletar_pci_avancado(self) -> List[Dict]:
        """Coleta avançada do PCI usando o integrador"""
        try:
            if not self.integrador_apis:
                print("⚠️ Integrador de APIs não disponível - usando método simples")
                return self.coletar_pci_simples()
            
            print("🔄 Coletando PCI com método avançado...")
            
            concursos = self.integrador_apis.coletar_pci_concursos_avancado()
            
            print(f"✅ Coletados {len(concursos)} concursos do PCI (avançado)")
            return concursos
            
        except Exception as e:
            print(f"❌ Erro na coleta PCI avançada: {e}")
            # Fallback para método simples
            return self.coletar_pci_simples()
    
    def coletar_todos_melhorado(self) -> List[Dict]:
        """Método melhorado que usa todas as fontes disponíveis"""
        try:
            print("🚀 Iniciando coleta completa melhorada...")
            
            todos_concursos = []
            
            # 1. APIs integradas (Brasil API + PCI Avançado)
            if self.integrador_apis:
                try:
                    concursos_integrados = self.coletar_apis_integradas()
                    todos_concursos.extend(concursos_integrados)
                    print(f"📊 APIs integradas: {len(concursos_integrados)} concursos")
                except Exception as e:
                    print(f"⚠️ Erro nas APIs integradas: {e}")
            
            # 2. PCI Simples (fallback)
            try:
                concursos_pci = self.coletar_pci_simples()
                # Filtrar duplicatas
                concursos_pci_novos = [
                    c for c in concursos_pci 
                    if not any(c.get('titulo') == tc.get('titulo') for tc in todos_concursos)
                ]
                todos_concursos.extend(concursos_pci_novos)
                print(f"📊 PCI simples (novos): {len(concursos_pci_novos)} concursos")
            except Exception as e:
                print(f"⚠️ Erro no PCI simples: {e}")
            
            # 3. QConcursos
            try:
                concursos_q = self.coletar_qconcursos()
                # Filtrar duplicatas
                concursos_q_novos = [
                    c for c in concursos_q 
                    if not any(c.get('titulo') == tc.get('titulo') for tc in todos_concursos)
                ]
                todos_concursos.extend(concursos_q_novos)
                print(f"📊 QConcursos (novos): {len(concursos_q_novos)} concursos")
            except Exception as e:
                print(f"⚠️ Erro no QConcursos: {e}")
            
            print(f"🎯 Total coletado: {len(todos_concursos)} concursos únicos")
            return todos_concursos
            
        except Exception as e:
            print(f"❌ Erro na coleta completa melhorada: {e}")
            return []
    
    def _extrair_cargo_basico(self, titulo: str) -> str:
        """Extrai cargo básico do título"""
        titulo_upper = titulo.upper()
        
        cargos = [
            'ANALISTA', 'TÉCNICO', 'ASSISTENTE', 'AUXILIAR', 'AGENTE',
            'PROFESSOR', 'ENFERMEIRO', 'MÉDICO', 'CONTADOR', 'ADVOGADO',
            'FISCAL', 'AUDITOR', 'PROCURADOR', 'DELEGADO', 'ESCRIVÃO'
        ]
        
        for cargo in cargos:
            if cargo in titulo_upper:
                return cargo.title()
        
        return 'Geral'

if __name__ == "__main__":
    print("🚀 Iniciando coleta em tempo real...")
    
    coletor = ColetorConcursosRealTime()
    concursos = coletor.coletar_todos()
    
    if concursos:
        coletor.salvar_csv(concursos)
        print("✅ Coleta realizada com sucesso!")
    else:
        print("⚠️ Nenhum concurso coletado")
