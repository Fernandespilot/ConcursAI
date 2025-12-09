"""
🕷️ SCRAPER COMPLETO CONCURSOS BRASIL - Versão Otimizada
======================================================
Coleta TODOS os concursos disponíveis do Concursos Brasil
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

class ConcursosBrasilScraperCompleto:
    def __init__(self, delay_range=(1, 3)):
        """Scraper completo para Concursos Brasil"""
        self.base_url = "https://www.concursosnobrasil.com.br"
        self.delay_range = delay_range
        self.session = requests.Session()
        
        # Headers otimizados
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.concursosnobrasil.com.br/'
        })
        
        self.logger = logging.getLogger(__name__)
        self.concursos_coletados = []
    
    def _wait(self):
        """Aguarda entre requests"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def _safe_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Request seguro com retry"""
        for attempt in range(max_retries):
            try:
                self._wait()
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    self.logger.warning(f"Rate limit - aguardando 30s (tentativa {attempt + 1})")
                    time.sleep(30)
                else:
                    self.logger.warning(f"Status {response.status_code} para {url}")
                    
            except Exception as e:
                self.logger.error(f"Erro na tentativa {attempt + 1}: {e}")
                time.sleep(5 * (attempt + 1))
        
        return None
    
    def _parse_concurso(self, item) -> Optional[Dict]:
        """Extrai dados de um concurso"""
        try:
            concurso = {
                'id': None,
                'titulo': '',
                'orgao': '',
                'localizacao': '',
                'vagas': 0,
                'salario': '',
                'salario_numerico': 0.0,
                'escolaridade': '',
                'inscricoes': '',
                'status': '',
                'link': '',
                'fonte': 'Concursos Brasil',
                'data_coleta': datetime.now().isoformat()
            }
            
            # Buscar título (vários seletores possíveis)
            titulo_elem = (
                item.find('h2', class_='titulo') or
                item.find('h3', class_='titulo') or
                item.find('a', class_='titulo') or
                item.find('div', class_='titulo') or
                item.find('h2') or
                item.find('h3') or
                item.select_one('.title, .name, .nome')
            )
            
            if titulo_elem:
                concurso['titulo'] = titulo_elem.get_text(strip=True)
                
                # Tentar encontrar link
                if titulo_elem.name == 'a':
                    href = titulo_elem.get('href', '')
                elif titulo_elem.find('a'):
                    href = titulo_elem.find('a').get('href', '')
                else:
                    # Buscar link no item pai
                    link_elem = item.find('a')
                    href = link_elem.get('href', '') if link_elem else ''
                
                if href:
                    if href.startswith('http'):
                        concurso['link'] = href
                    else:
                        concurso['link'] = f"{self.base_url}{href}"
                    
                    # Extrair ID do link
                    id_match = re.search(r'/concurso[s]?[/-]?([0-9]+)', href)
                    if id_match:
                        concurso['id'] = id_match.group(1)
            
            # Buscar informações adicionais em spans, divs, etc.
            all_text_elements = item.find_all(['span', 'div', 'p', 'td'])
            
            for elem in all_text_elements:
                text = elem.get_text(strip=True).lower()
                original_text = elem.get_text(strip=True)
                
                # Órgão/Banca
                if any(word in text for word in ['órgão', 'orgão', 'banca', 'organizador']):
                    if ':' in original_text:
                        concurso['orgao'] = original_text.split(':', 1)[1].strip()
                    elif not concurso['orgao']:
                        concurso['orgao'] = original_text
                
                # Localização
                elif any(word in text for word in ['local', 'cidade', 'estado', 'região']):
                    if ':' in original_text:
                        concurso['localizacao'] = original_text.split(':', 1)[1].strip()
                    elif not concurso['localizacao'] and len(original_text) < 50:
                        concurso['localizacao'] = original_text
                
                # Vagas
                elif 'vaga' in text:
                    vagas_match = re.search(r'(\\d+)', original_text)
                    if vagas_match:
                        concurso['vagas'] = int(vagas_match.group(1))
                
                # Salário
                elif 'r$' in text or 'salário' in text or 'remuneração' in text:
                    concurso['salario'] = original_text
                    concurso['salario_numerico'] = self._parse_salary_value(original_text)
                
                # Escolaridade
                elif any(word in text for word in ['superior', 'médio', 'fundamental', 'técnico', 'escolaridade']):
                    if len(original_text) < 50:
                        concurso['escolaridade'] = original_text
                
                # Inscrições
                elif 'inscri' in text:
                    concurso['inscricoes'] = original_text
                
                # Status
                elif any(word in text for word in ['aberto', 'fechado', 'andamento', 'previsto']):
                    concurso['status'] = original_text
            
            # Se não encontrou órgão, tentar usar parte do título
            if not concurso['orgao'] and concurso['titulo']:
                # Extrair órgão do título (primeira parte antes de -)
                if ' - ' in concurso['titulo']:
                    possible_orgao = concurso['titulo'].split(' - ')[0]
                    if len(possible_orgao) < 100:
                        concurso['orgao'] = possible_orgao
            
            # Validar se tem dados mínimos
            if concurso['titulo']:
                return concurso
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao processar concurso: {e}")
            return None
    
    def _parse_salary_value(self, salary_text: str) -> float:
        """Converte salário em texto para valor numérico"""
        try:
            # Extrair valor numérico do salário
            valor_match = re.search(r'R?\\$?\\s*([0-9]{1,3}(?:\\.[0-9]{3})*(?:,[0-9]{2})?)', salary_text)
            if valor_match:
                valor_str = valor_match.group(1)
                # Converter formato brasileiro para float
                valor_str = valor_str.replace('.', '').replace(',', '.')
                return float(valor_str)
            
            return 0.0
        except:
            return 0.0
    
    def coletar_pagina(self, page_num: int = 1) -> List[Dict]:
        """Coleta concursos de uma página específica"""
        # URLs possíveis para paginação
        urls_possiveis = [
            f"{self.base_url}/concursos/page/{page_num}",
            f"{self.base_url}/concursos?page={page_num}",
            f"{self.base_url}/page/{page_num}",
            f"{self.base_url}/?page={page_num}"
        ]
        
        concursos_encontrados = []
        
        for url in urls_possiveis:
            self.logger.info(f"📄 Tentando página {page_num}: {url}")
            
            response = self._safe_request(url)
            if not response:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar lista de concursos com diferentes seletores
            seletores = [
                'div.concurso',
                'article.concurso',
                'div.item-concurso',
                'div.card-concurso',
                'li.concurso-item',
                'tr.concurso',
                'div.row',
                'div.item',
                'article'
            ]
            
            items = []
            for seletor in seletores:
                items = soup.select(seletor)
                if items and len(items) > 1:  # Pelo menos 2 itens
                    self.logger.info(f"✅ Encontrados {len(items)} itens com seletor: {seletor}")
                    break
            
            if items:
                for item in items:
                    concurso = self._parse_concurso(item)
                    if concurso:
                        concursos_encontrados.append(concurso)
                
                if concursos_encontrados:
                    self.logger.info(f"📊 Página {page_num}: {len(concursos_encontrados)} concursos válidos")
                    return concursos_encontrados
        
        self.logger.warning(f"⚠️ Página {page_num}: nenhum concurso encontrado")
        return []
    
    def coletar_todos_concursos(self, max_pages: int = 30) -> List[Dict]:
        """Coleta TODOS os concursos disponíveis"""
        self.logger.info("🚀 INICIANDO COLETA COMPLETA DO CONCURSOS BRASIL")
        self.logger.info("=" * 60)
        
        todos_concursos = []
        paginas_vazias = 0
        
        for page_num in range(1, max_pages + 1):
            try:
                concursos_pagina = self.coletar_pagina(page_num)
                
                if concursos_pagina:
                    todos_concursos.extend(concursos_pagina)
                    paginas_vazias = 0
                    self.logger.info(f"✅ Página {page_num}: +{len(concursos_pagina)} concursos (Total: {len(todos_concursos)})")
                else:
                    paginas_vazias += 1
                    self.logger.warning(f"⚠️ Página {page_num}: vazia ({paginas_vazias} vazias seguidas)")
                    
                    # Parar se várias páginas seguidas estão vazias
                    if paginas_vazias >= 3:
                        self.logger.info("🛑 Múltiplas páginas vazias - finalizando coleta")
                        break
                
                # Progress feedback
                if page_num % 5 == 0:
                    self.logger.info(f"📈 Progresso: {page_num} páginas processadas | {len(todos_concursos)} concursos coletados")
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Coleta interrompida pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"❌ Erro na página {page_num}: {e}")
                paginas_vazias += 1
        
        # Remover duplicatas
        if todos_concursos:
            df = pd.DataFrame(todos_concursos)
            
            # Remover duplicatas por título e órgão
            df_unique = df.drop_duplicates(subset=['titulo', 'orgao'], keep='first')
            todos_concursos = df_unique.to_dict('records')
        
        self.logger.info("=" * 60)
        self.logger.info(f"🎉 COLETA FINALIZADA!")
        self.logger.info(f"📊 Total de concursos únicos: {len(todos_concursos)}")
        self.logger.info(f"📄 Páginas processadas: {page_num}")
        
        self.concursos_coletados = todos_concursos
        return todos_concursos
    
    def salvar_dados(self, filename: str = None) -> str:
        """Salva os dados coletados"""
        if not self.concursos_coletados:
            self.logger.warning("⚠️ Nenhum dado para salvar")
            return ""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"concursos_brasil_{timestamp}.csv"
        
        try:
            df = pd.DataFrame(self.concursos_coletados)
            df.to_csv(filename, index=False, encoding='utf-8')
            
            # Salvar também em JSON
            json_filename = filename.replace('.csv', '.json')
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.concursos_coletados, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 Dados salvos em: {filename} e {json_filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar: {e}")
            return ""

def main():
    """Função principal para teste"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Criar scraper
    scraper = ConcursosBrasilScraperCompleto()
    
    try:
        # Coletar concursos (limitar a 15 páginas para teste)
        concursos = scraper.coletar_todos_concursos(max_pages=15)
        
        if concursos:
            # Salvar dados
            filename = scraper.salvar_dados()
            
            print(f"\\n📊 RESULTADOS:")
            print("=" * 40)
            print(f"🎯 Total de concursos: {len(concursos)}")
            
            if concursos:
                # Mostrar alguns exemplos
                print("\\n📝 Primeiros 3 concursos encontrados:")
                for i, concurso in enumerate(concursos[:3], 1):
                    print(f"\\n{i}. {concurso['titulo']}")
                    print(f"   📍 Órgão: {concurso['orgao']}")
                    print(f"   📍 Local: {concurso['localizacao']}")
                    print(f"   💰 Salário: {concurso['salario']}")
                    
        else:
            print("❌ Nenhum concurso foi coletado")
            
    except KeyboardInterrupt:
        print("\\n⏹️ Coleta interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante a coleta: {e}")

if __name__ == "__main__":
    main()
