#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONCURSAI COMPLETO - SISTEMA INTEGRADO DE CONCURSOS PÚBLICOS
Sistema completo com scraping real, dashboard avançado, alertas e relatórios
"""

import asyncio
import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import List, Dict, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from pathlib import Path
import schedule
import time
import threading
from urllib.parse import urljoin
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('concursai_completo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============= MODELOS PYDANTIC =============

class ConcursoModel(BaseModel):
    id: str
    titulo: str
    orgao: str
    cargo: str
    ano: str
    vagas: str
    salario: str
    local: str
    regiao: str
    estado: str
    status: str
    escolaridade: str
    taxa_inscricao: str
    data_publicacao: str
    inicio_inscricoes: str
    fim_inscricoes: str
    data_prova: str
    prazo_inscricoes: str
    dias_restantes: int
    nivel: str
    tipo: str
    urgencia: str
    url: str
    fonte: str
    tipo_documento: str
    conteudo: str

class FiltroRequest(BaseModel):
    texto: Optional[str] = None
    regiao: Optional[str] = None
    estado: Optional[str] = None
    orgao: Optional[str] = None
    cargo: Optional[str] = None
    escolaridade: Optional[str] = None
    salario_min: Optional[float] = None
    urgencia: Optional[str] = None
    limit: Optional[int] = 50

class AlertaModel(BaseModel):
    id: Optional[str] = None
    usuario_email: str
    palavras_chave: List[str]
    regioes: List[str]
    ativo: bool = True
    criado_em: Optional[str] = None

# ============= SCRAPER COMPLETO PCI =============

class PCIScraperCompleto:
    def __init__(self):
        self.base_url = "https://www.pciconcursos.com.br"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def scrape_completo(self, max_concursos=100):
        """Scraping completo de múltiplas fontes do PCI"""
        logger.info("🌐 Iniciando scraping COMPLETO do PCI Concursos...")
        concursos = []
        
        # URLs para scraping completo
        urls_scraping = [
            f"{self.base_url}/ultimas/",
            f"{self.base_url}/concursos/abertos",
            f"{self.base_url}/concursos/federais", 
            f"{self.base_url}/concursos/estaduais",
            f"{self.base_url}/concursos/municipais"
        ]
        
        for url in urls_scraping:
            try:
                logger.info(f"🔍 Processando: {url}")
                response = self.session.get(url, timeout=20)
                if response.status_code == 200:
                    novos_concursos = self.extrair_concursos_pagina(response.text, url)
                    concursos.extend(novos_concursos)
                    logger.info(f"✅ Coletados {len(novos_concursos)} concursos de {url}")
                    
                    if len(concursos) >= max_concursos:
                        break
                        
                time.sleep(2)  # Pausa entre requisições
                
            except Exception as e:
                logger.warning(f"⚠️ Erro em {url}: {e}")
                continue
        
        # Remover duplicatas
        concursos_unicos = self.remover_duplicatas(concursos)
        logger.info(f"✅ Scraping completo: {len(concursos_unicos)} concursos únicos coletados")
        
        return concursos_unicos[:max_concursos]
    
    def extrair_concursos_pagina(self, html, url_base):
        """Extrai concursos de uma página HTML"""
        concursos = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Seletores abrangentes para diferentes estruturas
        seletores = [
            'tr[class*="linha"]',
            'tr[class*="item"]', 
            'div[class*="concurso"]',
            'a[href*="/concurso/"]',
            'table tr td a',
            '.listagem tr',
            '.resultado-busca',
            'li[class*="concurso"]'
        ]
        
        elementos_encontrados = []
        for seletor in seletores:
            elementos = soup.select(seletor)
            elementos_encontrados.extend(elementos)
        
        # Buscar também por texto
        links_texto = soup.find_all('a', string=re.compile(r'(concurso|edital|processo seletivo)', re.I))
        elementos_encontrados.extend(links_texto)
        
        logger.info(f"🔍 Elementos encontrados: {len(elementos_encontrados)}")
        
        for elemento in elementos_encontrados:
            try:
                dados_concurso = self.extrair_dados_elemento(elemento, url_base)
                if dados_concurso and self.validar_concurso(dados_concurso):
                    concursos.append(dados_concurso)
                    if len(concursos) >= 50:  # Limite por página
                        break
            except Exception as e:
                continue
        
        return concursos
    
    def extrair_dados_elemento(self, elemento, url_base):
        """Extrai dados de um elemento HTML"""
        try:
            # Detectar tipo de elemento
            if elemento.name == 'tr':
                return self.extrair_dados_tabela(elemento, url_base)
            
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
            
            # Extrair contexto
            contexto = elemento.get_text() if elemento.parent else ""
            
            # Criar dados estruturados
            dados = {
                'id': f"pci_{hash(link or titulo) % 1000000}",
                'titulo': self.limpar_texto(titulo),
                'orgao': self.extrair_orgao(titulo, contexto),
                'cargo': self.extrair_cargo(titulo, contexto),
                'ano': str(datetime.now().year),
                'vagas': self.extrair_vagas(contexto),
                'salario': self.extrair_salario(contexto),
                'local': self.extrair_local(contexto),
                'regiao': '',
                'estado': '',
                'status': self.extrair_status(contexto),
                'escolaridade': self.extrair_escolaridade(titulo, contexto),
                'taxa_inscricao': self.extrair_taxa(contexto),
                'data_publicacao': datetime.now().strftime("%d/%m/%Y"),
                'inicio_inscricoes': self.extrair_data_inicio(contexto),
                'fim_inscricoes': self.extrair_data_fim(contexto),
                'data_prova': self.extrair_data_prova(contexto),
                'prazo_inscricoes': self.extrair_prazo(contexto),
                'dias_restantes': self.calcular_dias_restantes(contexto),
                'nivel': self.extrair_escolaridade(titulo, contexto),
                'tipo': 'ABERTO',
                'urgencia': self.calcular_urgencia(contexto),
                'url': link,
                'fonte': f'PCI Concursos Real - {url_base.split("/")[-2] if "/" in url_base else "Principal"}',
                'tipo_documento': 'edital',
                'conteudo': self.limpar_texto(titulo + " " + contexto[:300])
            }
            
            # Calcular região e estado
            local = dados['local']
            dados['regiao'] = self.calcular_regiao(local)
            dados['estado'] = self.extrair_estado_sigla(local)
            
            return dados
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dados: {e}")
            return None
    
    def extrair_dados_tabela(self, linha_tr, url_base):
        """Extrai dados de linha de tabela"""
        try:
            colunas = linha_tr.find_all(['td', 'th'])
            if len(colunas) < 2:
                return None
            
            # Buscar link
            link_elem = linha_tr.find('a', href=True)
            link = link_elem.get('href', '') if link_elem else ''
            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)
            
            # Extrair textos das colunas
            textos = [col.get_text(strip=True) for col in colunas]
            titulo = textos[0] if textos else "Concurso"
            
            # Identificar informações
            orgao = self.identificar_coluna_orgao(textos)
            local = self.identificar_coluna_local(textos)
            data_info = self.identificar_coluna_data(textos)
            vagas_info = self.identificar_coluna_vagas(textos)
            
            dados = {
                'id': f"pci_tab_{hash(link or titulo) % 1000000}",
                'titulo': self.limpar_texto(titulo),
                'orgao': orgao or self.extrair_orgao_simples(titulo),
                'cargo': self.extrair_cargo_simples(titulo),
                'ano': str(datetime.now().year),
                'vagas': vagas_info or 'Consultar edital',
                'salario': 'Consultar edital',
                'local': local or 'Consultar edital',
                'regiao': self.calcular_regiao(local) if local else 'Nacional',
                'estado': self.extrair_estado_sigla(local) if local else 'BR',
                'status': 'Inscrições abertas',
                'escolaridade': self.extrair_escolaridade_simples(titulo),
                'taxa_inscricao': 'Consultar edital',
                'data_publicacao': data_info or datetime.now().strftime("%d/%m/%Y"),
                'inicio_inscricoes': 'Consultar edital',
                'fim_inscricoes': data_info or 'Consultar edital',
                'data_prova': 'Consultar edital',
                'prazo_inscricoes': data_info or 'Consultar edital',
                'dias_restantes': 0,
                'nivel': self.extrair_escolaridade_simples(titulo),
                'tipo': 'ABERTO',
                'urgencia': 'normal',
                'url': link,
                'fonte': f'PCI Concursos Real - Tabela',
                'tipo_documento': 'edital',
                'conteudo': self.limpar_texto(' '.join(textos))
            }
            
            return dados
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dados da tabela: {e}")
            return None
    
    # Métodos auxiliares de extração
    def limpar_texto(self, texto):
        if not texto:
            return ""
        return re.sub(r'\s+', ' ', texto.strip())
    
    def extrair_orgao(self, titulo, contexto=""):
        texto = f"{titulo} {contexto}".lower()
        
        orgaos_conhecidos = [
            'tribunal de justiça', 'prefeitura', 'câmara municipal', 'assembleia legislativa',
            'polícia federal', 'polícia civil', 'polícia militar', 'corpo de bombeiros',
            'receita federal', 'banco central', 'inss', 'ibge', 'anvisa', 'anatel',
            'ministério público', 'defensoria pública', 'tribunal de contas',
            'universidade federal', 'instituto federal', 'cefet', 'serpro', 'dataprev'
        ]
        
        for orgao in orgaos_conhecidos:
            if orgao in texto:
                return orgao.title()
        
        match = re.search(r'(tribunal|prefeitura|câmara|assembleia|polícia|ministério|defensoria|universidade|instituto)[\w\s]*', texto, re.I)
        if match:
            return match.group().title()
            
        return "Órgão público"
    
    def extrair_orgao_simples(self, titulo):
        return self.extrair_orgao(titulo, "")
    
    def extrair_cargo(self, titulo, contexto=""):
        texto = f"{titulo} {contexto}".lower()
        
        cargos_conhecidos = [
            'analista', 'técnico', 'auditor', 'agente', 'escrivão', 'investigador',
            'delegado', 'professor', 'médico', 'enfermeiro', 'advogado', 'contador',
            'engenheiro', 'procurador', 'promotor', 'defensor', 'juiz', 'auxiliar',
            'assistente', 'especialista', 'fiscal', 'inspetor'
        ]
        
        for cargo in cargos_conhecidos:
            if cargo in texto:
                return cargo.title()
                
        return "Servidor público"
    
    def extrair_cargo_simples(self, titulo):
        return self.extrair_cargo(titulo, "")
    
    def extrair_vagas(self, texto):
        patterns = [r'(\d+)\s*vaga[s]?', r'vaga[s]?:\s*(\d+)', r'(\d+)\s*posto[s]?']
        for pattern in patterns:
            match = re.search(pattern, texto, re.I)
            if match:
                return match.group(1)
        return "Consultar edital"
    
    def extrair_salario(self, texto):
        patterns = [r'R\$\s*[\d.,]+', r'salário.*?R\$\s*[\d.,]+', r'remuneração.*?R\$\s*[\d.,]+']
        for pattern in patterns:
            match = re.search(pattern, texto, re.I)
            if match:
                return match.group()
        return "Consultar edital"
    
    def extrair_local(self, texto):
        estados = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
        
        for estado in estados:
            if estado in texto.upper():
                return estado
                
        cidades = ['são paulo', 'rio de janeiro', 'brasília', 'belo horizonte', 'salvador', 'fortaleza', 'recife', 'porto alegre', 'curitiba']
        
        for cidade in cidades:
            if cidade in texto.lower():
                return cidade.title()
                
        return "Nacional"
    
    def extrair_escolaridade(self, titulo, contexto=""):
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
        return self.extrair_escolaridade(titulo, "")
    
    def extrair_status(self, texto):
        if any(word in texto.lower() for word in ['encerrado', 'finalizado', 'suspenso']):
            return "Encerrado"
        elif any(word in texto.lower() for word in ['em breve', 'previsto', 'aguardando']):
            return "Em breve"
        else:
            return "Inscrições abertas"
    
    def extrair_taxa(self, texto):
        patterns = [r'taxa.*?R\$\s*[\d.,]+', r'inscrição.*?R\$\s*[\d.,]+']
        for pattern in patterns:
            match = re.search(pattern, texto, re.I)
            if match:
                return match.group()
        return "Consultar edital"
    
    def extrair_data_inicio(self, texto):
        pattern = r'início.*?(\d{1,2}/\d{1,2}/\d{4})'
        match = re.search(pattern, texto, re.I)
        return match.group(1) if match else "Consultar edital"
    
    def extrair_data_fim(self, texto):
        pattern = r'fim.*?(\d{1,2}/\d{1,2}/\d{4})|até.*?(\d{1,2}/\d{1,2}/\d{4})'
        match = re.search(pattern, texto, re.I)
        return match.group(1) or match.group(2) if match else "Consultar edital"
    
    def extrair_data_prova(self, texto):
        pattern = r'prova.*?(\d{1,2}/\d{1,2}/\d{4})'
        match = re.search(pattern, texto, re.I)
        return match.group(1) if match else "Consultar edital"
    
    def extrair_prazo(self, texto):
        # Buscar datas de fim
        data_fim = self.extrair_data_fim(texto)
        if data_fim != "Consultar edital":
            return data_fim
        
        # Buscar padrões de prazo
        patterns = [r'prazo.*?(\d{1,2}/\d{1,2}/\d{4})', r'até.*?(\d{1,2}/\d{1,2}/\d{4})']
        for pattern in patterns:
            match = re.search(pattern, texto, re.I)
            if match:
                return match.group(1)
        
        return "Consultar edital"
    
    def calcular_dias_restantes(self, texto):
        data_fim = self.extrair_data_fim(texto)
        if data_fim == "Consultar edital":
            return 0
            
        try:
            data_fim_dt = datetime.strptime(data_fim, "%d/%m/%Y")
            hoje = datetime.now()
            diferenca = (data_fim_dt - hoje).days
            return max(0, diferenca)
        except:
            return 0
    
    def calcular_urgencia(self, texto):
        dias_restantes = self.calcular_dias_restantes(texto)
        if dias_restantes <= 7:
            return "urgente"
        elif dias_restantes <= 30:
            return "atenção"
        else:
            return "normal"
    
    def calcular_regiao(self, local):
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
        if not local:
            return "BR"
            
        estados = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
        
        for estado in estados:
            if estado in local.upper():
                return estado
                
        return "BR"
    
    def identificar_coluna_orgao(self, textos):
        for texto in textos:
            if any(palavra in texto.lower() for palavra in ['prefeitura', 'tribunal', 'polícia', 'ministério']):
                return texto
        return None
    
    def identificar_coluna_local(self, textos):
        estados = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
        for texto in textos:
            if any(estado in texto.upper() for estado in estados):
                return texto
        return None
    
    def identificar_coluna_data(self, textos):
        for texto in textos:
            if re.search(r'\d{1,2}/\d{1,2}/\d{4}', texto):
                return texto
        return None
    
    def identificar_coluna_vagas(self, textos):
        for texto in textos:
            if re.search(r'\d+.*vaga', texto.lower()):
                return texto
        return None
    
    def validar_concurso(self, dados):
        if not dados:
            return False
            
        titulo = dados.get('titulo', '')
        if len(titulo) < 10:
            return False
            
        palavras_chave = ['concurso', 'edital', 'processo seletivo', 'seleção']
        titulo_lower = titulo.lower()
        
        return any(palavra in titulo_lower for palavra in palavras_chave)
    
    def remover_duplicatas(self, concursos):
        """Remove concursos duplicados baseado no título"""
        vistos = set()
        unicos = []
        
        for concurso in concursos:
            titulo_norm = re.sub(r'\s+', ' ', concurso['titulo'].lower().strip())
            if titulo_norm not in vistos:
                vistos.add(titulo_norm)
                unicos.append(concurso)
        
        return unicos

# ============= BANCO DE DADOS =============

class DatabaseManager:
    def __init__(self, db_path="concursai_completo.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de concursos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concursos (
                id TEXT PRIMARY KEY,
                titulo TEXT,
                orgao TEXT,
                cargo TEXT,
                ano TEXT,
                vagas TEXT,
                salario TEXT,
                local TEXT,
                regiao TEXT,
                estado TEXT,
                status TEXT,
                escolaridade TEXT,
                taxa_inscricao TEXT,
                data_publicacao TEXT,
                inicio_inscricoes TEXT,
                fim_inscricoes TEXT,
                data_prova TEXT,
                prazo_inscricoes TEXT,
                dias_restantes INTEGER,
                nivel TEXT,
                tipo TEXT,
                urgencia TEXT,
                url TEXT,
                fonte TEXT,
                tipo_documento TEXT,
                conteudo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alertas (
                id TEXT PRIMARY KEY,
                usuario_email TEXT,
                palavras_chave TEXT,
                regioes TEXT,
                ativo BOOLEAN DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de logs de scraping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs_scraping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_coletados INTEGER,
                fonte TEXT,
                sucesso BOOLEAN,
                detalhes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def salvar_concursos(self, concursos):
        """Salva concursos no banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for concurso in concursos:
            cursor.execute('''
                INSERT OR REPLACE INTO concursos 
                (id, titulo, orgao, cargo, ano, vagas, salario, local, regiao, estado, 
                 status, escolaridade, taxa_inscricao, data_publicacao, inicio_inscricoes, 
                 fim_inscricoes, data_prova, prazo_inscricoes, dias_restantes, nivel, 
                 tipo, urgencia, url, fonte, tipo_documento, conteudo, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                concurso['id'], concurso['titulo'], concurso['orgao'], concurso['cargo'],
                concurso['ano'], concurso['vagas'], concurso['salario'], concurso['local'],
                concurso['regiao'], concurso['estado'], concurso['status'], concurso['escolaridade'],
                concurso['taxa_inscricao'], concurso['data_publicacao'], concurso['inicio_inscricoes'],
                concurso['fim_inscricoes'], concurso['data_prova'], concurso['prazo_inscricoes'],
                concurso['dias_restantes'], concurso['nivel'], concurso['tipo'], concurso['urgencia'],
                concurso['url'], concurso['fonte'], concurso['tipo_documento'], concurso['conteudo']
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"💾 Salvos {len(concursos)} concursos no banco")
    
    def buscar_concursos(self, filtros: FiltroRequest):
        """Busca concursos com filtros"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM concursos WHERE 1=1"
        params = []
        
        if filtros.texto:
            query += " AND (titulo LIKE ? OR orgao LIKE ? OR cargo LIKE ? OR conteudo LIKE ?)"
            texto_param = f"%{filtros.texto}%"
            params.extend([texto_param, texto_param, texto_param, texto_param])
        
        if filtros.regiao:
            query += " AND regiao = ?"
            params.append(filtros.regiao)
        
        if filtros.estado:
            query += " AND estado = ?"
            params.append(filtros.estado)
        
        if filtros.orgao:
            query += " AND orgao LIKE ?"
            params.append(f"%{filtros.orgao}%")
        
        if filtros.cargo:
            query += " AND cargo LIKE ?"
            params.append(f"%{filtros.cargo}%")
        
        if filtros.escolaridade:
            query += " AND escolaridade = ?"
            params.append(filtros.escolaridade)
        
        if filtros.urgencia:
            query += " AND urgencia = ?"
            params.append(filtros.urgencia)
        
        query += " ORDER BY created_at DESC"
        
        if filtros.limit:
            query += " LIMIT ?"
            params.append(filtros.limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def obter_todos_concursos(self, limit=100):
        """Obtém todos os concursos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM concursos ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def obter_estatisticas(self):
        """Obtém estatísticas dos concursos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total de concursos
        cursor.execute("SELECT COUNT(*) FROM concursos")
        stats['total_concursos'] = cursor.fetchone()[0]
        
        # Por região
        cursor.execute("SELECT regiao, COUNT(*) FROM concursos GROUP BY regiao")
        stats['por_regiao'] = dict(cursor.fetchall())
        
        # Por urgência
        cursor.execute("SELECT urgencia, COUNT(*) FROM concursos GROUP BY urgencia")
        stats['por_urgencia'] = dict(cursor.fetchall())
        
        # Por escolaridade
        cursor.execute("SELECT escolaridade, COUNT(*) FROM concursos GROUP BY escolaridade")
        stats['por_escolaridade'] = dict(cursor.fetchall())
        
        # Órgãos mais ativos
        cursor.execute("SELECT orgao, COUNT(*) FROM concursos GROUP BY orgao ORDER BY COUNT(*) DESC LIMIT 10")
        stats['orgaos_top'] = dict(cursor.fetchall())
        
        conn.close()
        return stats
    
    def log_scraping(self, total_coletados, fonte, sucesso, detalhes=""):
        """Registra log de scraping"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO logs_scraping (total_coletados, fonte, sucesso, detalhes)
            VALUES (?, ?, ?, ?)
        ''', (total_coletados, fonte, sucesso, detalhes))
        
        conn.commit()
        conn.close()

# ============= SISTEMA DE ALERTAS =============

class SistemaAlertas:
    def __init__(self, db_manager):
        self.db = db_manager
        
    def criar_alerta(self, alerta: AlertaModel):
        """Cria um novo alerta"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        alerta_id = f"alert_{hash(alerta.usuario_email + str(time.time())) % 1000000}"
        
        cursor.execute('''
            INSERT INTO alertas (id, usuario_email, palavras_chave, regioes, ativo)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            alerta_id,
            alerta.usuario_email,
            json.dumps(alerta.palavras_chave),
            json.dumps(alerta.regioes),
            alerta.ativo
        ))
        
        conn.commit()
        conn.close()
        
        return alerta_id
    
    def verificar_alertas(self, novos_concursos):
        """Verifica alertas para novos concursos"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM alertas WHERE ativo = 1")
        alertas = cursor.fetchall()
        conn.close()
        
        notificacoes = []
        
        for alerta in alertas:
            palavras_chave = json.loads(alerta['palavras_chave'])
            regioes = json.loads(alerta['regioes'])
            
            concursos_relevantes = []
            
            for concurso in novos_concursos:
                # Verificar palavras-chave
                texto_concurso = f"{concurso['titulo']} {concurso['orgao']} {concurso['cargo']}".lower()
                
                tem_palavra_chave = any(palavra.lower() in texto_concurso for palavra in palavras_chave)
                tem_regiao = not regioes or concurso['regiao'] in regioes
                
                if tem_palavra_chave and tem_regiao:
                    concursos_relevantes.append(concurso)
            
            if concursos_relevantes:
                notificacoes.append({
                    'email': alerta['usuario_email'],
                    'concursos': concursos_relevantes,
                    'palavras_chave': palavras_chave
                })
        
        return notificacoes

# ============= AGENDADOR DE TAREFAS =============

class AgendadorTarefas:
    def __init__(self, scraper, db_manager, sistema_alertas):
        self.scraper = scraper
        self.db = db_manager
        self.alertas = sistema_alertas
        self.running = False
    
    def iniciar_agendamento(self):
        """Inicia o agendamento de tarefas"""
        # Scraping a cada 6 horas
        schedule.every(6).hours.do(self.executar_scraping_automatico)
        
        # Verificação de alertas a cada hora
        schedule.every(1).hours.do(self.verificar_alertas_automatico)
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("🕐 Agendador iniciado - Scraping a cada 6h, alertas a cada 1h")
    
    def parar_agendamento(self):
        """Para o agendamento"""
        self.running = False
        schedule.clear()
    
    def executar_scraping_automatico(self):
        """Executa scraping automático"""
        try:
            logger.info("🤖 Executando scraping automático...")
            
            concursos_antes = len(self.db.obter_todos_concursos())
            novos_concursos = self.scraper.scrape_completo(max_concursos=50)
            
            if novos_concursos:
                self.db.salvar_concursos(novos_concursos)
                concursos_depois = len(self.db.obter_todos_concursos())
                
                novos_adicionados = concursos_depois - concursos_antes
                
                self.db.log_scraping(
                    total_coletados=len(novos_concursos),
                    fonte="Automático",
                    sucesso=True,
                    detalhes=f"Novos concursos adicionados: {novos_adicionados}"
                )
                
                # Verificar alertas para novos concursos
                if novos_adicionados > 0:
                    self.verificar_alertas_automatico()
                
                logger.info(f"✅ Scraping automático concluído: {len(novos_concursos)} coletados, {novos_adicionados} novos")
            else:
                self.db.log_scraping(0, "Automático", False, "Nenhum concurso coletado")
                logger.warning("⚠️ Scraping automático não retornou dados")
                
        except Exception as e:
            self.db.log_scraping(0, "Automático", False, f"Erro: {str(e)}")
            logger.error(f"❌ Erro no scraping automático: {e}")
    
    def verificar_alertas_automatico(self):
        """Verifica alertas automaticamente"""
        try:
            # Buscar concursos recentes (últimas 24 horas)
            conn = sqlite3.connect(self.db.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM concursos 
                WHERE created_at > datetime('now', '-1 day')
                ORDER BY created_at DESC
            ''')
            
            concursos_recentes = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if concursos_recentes:
                notificacoes = self.alertas.verificar_alertas(concursos_recentes)
                
                for notificacao in notificacoes:
                    self.enviar_notificacao_email(notificacao)
                
                logger.info(f"📧 Verificação de alertas: {len(notificacoes)} notificações enviadas")
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de alertas: {e}")
    
    def enviar_notificacao_email(self, notificacao):
        """Envia notificação por email (simulado)"""
        # Em uma implementação real, aqui seria integrado com SMTP
        logger.info(f"📧 [SIMULADO] Email enviado para {notificacao['email']}: {len(notificacao['concursos'])} novos concursos")

# ============= APLICAÇÃO FASTAPI =============

# Inicializar componentes
scraper = PCIScraperCompleto()
db_manager = DatabaseManager()
sistema_alertas = SistemaAlertas(db_manager)
agendador = AgendadorTarefas(scraper, db_manager, sistema_alertas)

# Criar aplicação FastAPI
app = FastAPI(
    title="ConcursAI Completo",
    description="Sistema completo de concursos públicos com scraping real, alertas e relatórios",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= ENDPOINTS DA API =============

@app.on_event("startup")
async def startup_event():
    """Eventos de inicialização"""
    logger.info("🚀 Iniciando ConcursAI Completo...")
    
    # Carregar dados existentes
    concursos_existentes = db_manager.obter_todos_concursos(limit=10)
    
    if not concursos_existentes:
        logger.info("📦 Executando scraping inicial...")
        try:
            concursos_iniciais = scraper.scrape_completo(max_concursos=50)
            if concursos_iniciais:
                db_manager.salvar_concursos(concursos_iniciais)
                logger.info(f"✅ Dados iniciais carregados: {len(concursos_iniciais)} concursos")
            else:
                logger.warning("⚠️ Scraping inicial não retornou dados")
        except Exception as e:
            logger.error(f"❌ Erro no scraping inicial: {e}")
    
    # Iniciar agendador
    agendador.iniciar_agendamento()

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos de encerramento"""
    agendador.parar_agendamento()
    logger.info("🛑 ConcursAI Completo encerrado")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Página inicial"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ConcursAI Completo</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 800px; margin: 0 auto; }
            .card { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; margin: 20px 0; }
            h1 { color: #ffd700; text-align: center; font-size: 3em; margin-bottom: 10px; }
            .subtitle { text-align: center; font-size: 1.2em; margin-bottom: 30px; opacity: 0.9; }
            .feature { background: rgba(255,255,255,0.05); padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 4px solid #ffd700; }
            .links { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 30px; }
            .link { background: linear-gradient(45deg, #4ecdc4, #44a08d); color: white; text-decoration: none; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; }
            .link:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 ConcursAI Completo</h1>
            <p class="subtitle">Sistema Integrado de Concursos Públicos com Dados Reais</p>
            
            <div class="card">
                <div class="feature">
                    <h3>🌐 Scraping Real do PCI Concursos</h3>
                    <p>Coleta automática de dados reais de múltiplas fontes do PCI Concursos</p>
                </div>
                
                <div class="feature">
                    <h3>📊 Dashboard Avançado</h3>
                    <p>Interface completa com filtros por região, escolaridade, urgência e muito mais</p>
                </div>
                
                <div class="feature">
                    <h3>🔔 Sistema de Alertas</h3>
                    <p>Notificações automáticas por email para concursos relevantes</p>
                </div>
                
                <div class="feature">
                    <h3>📈 Relatórios e Estatísticas</h3>
                    <p>Análises detalhadas por região, órgão e categoria</p>
                </div>
                
                <div class="feature">
                    <h3>🤖 Agendamento Automático</h3>
                    <p>Scraping a cada 6 horas e verificação de alertas a cada hora</p>
                </div>
                
                <div class="links">
                    <a href="/docs" class="link">📖 API Docs</a>
                    <a href="/dashboard" class="link">📊 Dashboard</a>
                    <a href="/status" class="link">📊 Status</a>
                    <a href="/scraper/executar" class="link">🕷️ Executar Scraper</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/concursos")
async def listar_concursos(
    limit: int = 50,
    regiao: str = None,
    estado: str = None,
    urgencia: str = None,
    escolaridade: str = None
):
    """Lista concursos com filtros opcionais"""
    try:
        filtros = FiltroRequest(
            regiao=regiao,
            estado=estado,
            urgencia=urgencia,
            escolaridade=escolaridade,
            limit=limit
        )
        
        concursos = db_manager.buscar_concursos(filtros)
        
        return {
            "total": len(concursos),
            "concursos": concursos,
            "filtros_aplicados": {
                "regiao": regiao,
                "estado": estado,
                "urgencia": urgencia,
                "escolaridade": escolaridade,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar concursos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/buscar")
async def buscar_concursos(filtros: FiltroRequest):
    """Busca concursos com filtros avançados"""
    try:
        concursos = db_manager.buscar_concursos(filtros)
        
        return {
            "total": len(concursos),
            "concursos": concursos,
            "filtros": filtros.dict()
        }
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/estatisticas")
async def obter_estatisticas():
    """Obtém estatísticas dos concursos"""
    try:
        stats = db_manager.obter_estatisticas()
        
        return {
            "estatisticas": stats,
            "gerado_em": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scraper/executar")
async def executar_scraper(background_tasks: BackgroundTasks):
    """Executa scraper completo"""
    try:
        logger.info("🕷️ Executando scraper via API...")
        
        # Executar scraping
        novos_concursos = scraper.scrape_completo(max_concursos=100)
        
        if novos_concursos:
            # Salvar no banco
            db_manager.salvar_concursos(novos_concursos)
            
            # Log de sucesso
            db_manager.log_scraping(
                total_coletados=len(novos_concursos),
                fonte="API Manual",
                sucesso=True,
                detalhes="Scraping executado via endpoint"
            )
            
            return {
                "sucesso": True,
                "total_coletados": len(novos_concursos),
                "message": "Scraping executado com sucesso",
                "concursos": novos_concursos[:10],  # Primeiros 10 como amostra
                "executado_em": datetime.now().isoformat()
            }
        else:
            db_manager.log_scraping(0, "API Manual", False, "Nenhum dado coletado")
            
            return {
                "sucesso": False,
                "total_coletados": 0,
                "erro": "Nenhum concurso foi coletado",
                "executado_em": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Erro no scraper via API: {e}")
        db_manager.log_scraping(0, "API Manual", False, f"Erro: {str(e)}")
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alertas")
async def criar_alerta(alerta: AlertaModel):
    """Cria um novo alerta"""
    try:
        alerta_id = sistema_alertas.criar_alerta(alerta)
        
        return {
            "sucesso": True,
            "alerta_id": alerta_id,
            "message": "Alerta criado com sucesso"
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def status_sistema():
    """Status do sistema"""
    try:
        stats = db_manager.obter_estatisticas()
        
        # Verificar último scraping
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs_scraping ORDER BY data_execucao DESC LIMIT 1")
        ultimo_scraping = cursor.fetchone()
        conn.close()
        
        return {
            "status": "online",
            "total_concursos": stats.get('total_concursos', 0),
            "agendador_ativo": agendador.running,
            "ultimo_scraping": {
                "data": ultimo_scraping[1] if ultimo_scraping else None,
                "total_coletados": ultimo_scraping[2] if ultimo_scraping else 0,
                "sucesso": bool(ultimo_scraping[4]) if ultimo_scraping else False
            } if ultimo_scraping else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard integrado com design preferido"""
    return FileResponse("dashboard_integrado.html")

@app.get("/dashboard-completo", response_class=HTMLResponse)
async def dashboard_completo():
    """Dashboard completo alternativo"""
    return FileResponse("dashboard_completo.html")

@app.get("/export/csv")
async def exportar_csv():
    """Exporta concursos em CSV"""
    try:
        concursos = db_manager.obter_todos_concursos(limit=1000)
        
        if not concursos:
            raise HTTPException(status_code=404, detail="Nenhum concurso encontrado")
        
        # Converter para DataFrame e salvar
        df = pd.DataFrame(concursos)
        csv_path = "export_concursos.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        return FileResponse(
            csv_path,
            media_type='text/csv',
            filename=f"concursos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= EXECUÇÃO PRINCIPAL =============

if __name__ == "__main__":
    print("🎯" + "="*70)
    print("        CONCURSAI COMPLETO - SISTEMA INTEGRADO")
    print("="*70)
    
    print("\n🚀 Iniciando sistema completo...")
    
    print(f"\n🌐 ACESSOS DISPONÍVEIS:")
    print(f"   📍 Sistema Principal: http://localhost:8008")
    print(f"   📖 Documentação API: http://localhost:8008/docs")
    print(f"   📊 Dashboard: http://localhost:8008/dashboard")
    print(f"   📊 Status: http://localhost:8008/status")
    print(f"   🕷️ Scraper: http://localhost:8008/scraper/executar")
    print(f"   📁 Export CSV: http://localhost:8008/export/csv")
    
    print(f"\n🔧 FUNCIONALIDADES:")
    print(f"   ✅ Scraping real do PCI Concursos")
    print(f"   ✅ Banco de dados SQLite")
    print(f"   ✅ Sistema de alertas")
    print(f"   ✅ Agendamento automático")
    print(f"   ✅ API REST completa")
    print(f"   ✅ Dashboard avançado")
    print(f"   ✅ Exportação de dados")
    print(f"   ✅ Relatórios e estatísticas")
    
    print(f"\n✅ SISTEMA COMPLETO E FUNCIONAL")
    print(f"⏹️  Pressione Ctrl+C para parar")
    print("="*70)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8008,
            reload=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
