"""
🕷️ SCRAPER COMPLETO PCI CONCURSO - Versão Otimizada
===================================================
Coleta TODOS os concursos disponíveis do PCI Concurso
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

class PCIConcursoScraperCompleto:
    def __init__(self, delay_range=(1, 2)):
        """Scraper completo para PCI Concurso"""
        self.base_url = "https://www.pciconcursos.com.br"
        self.delay_range = delay_range
        self.session = requests.Session()
        
        # Headers otimizados
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.pciconcursos.com.br/'
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
                'fonte': 'PCI Concurso',
                'data_coleta': datetime.now().isoformat()
            }
            
            # Título e link
            titulo_elem = item.find('a', class_='cn')
            if titulo_elem:
                concurso['titulo'] = titulo_elem.get_text(strip=True)
                href = titulo_elem.get('href', '')
                if href:
                    concurso['link'] = f"https://www.pciconcursos.com.br{href}"
                    # Extrair ID do link
                    id_match = re.search(r'/concurso/([0-9]+)', href)
                    if id_match:
                        concurso['id'] = id_match.group(1)
            
            # Informações detalhadas
            info_spans = item.find_all('span')
            for span in info_spans:
                class_name = span.get('class', [])
                text = span.get_text(strip=True)
                
                if 'orgao' in class_name:
                    concurso['orgao'] = text
                elif 'local' in class_name:
                    concurso['localizacao'] = text
                elif 'vagas' in class_name:
                    # Extrair número de vagas
                    vagas_match = re.search(r'(\\d+)', text)
                    if vagas_match:
                        concurso['vagas'] = int(vagas_match.group(1))
                elif 'salario' in class_name:
                    concurso['salario'] = text
                    # Extrair valor numérico do salário
                    concurso['salario_numerico'] = self._parse_salary_value(text)
                elif 'escolaridade' in class_name:
                    concurso['escolaridade'] = text
                elif 'inscricao' in class_name:
                    concurso['inscricoes'] = text
                elif 'situacao' in class_name:
                    concurso['status'] = text
            
            # Validar se tem dados mínimos
            if concurso['titulo'] and concurso['orgao']:
                return concurso
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao processar concurso: {e}")
            return None
    
    def _parse_salary_value(self, salary_text: str) -> float:
        """Converte salário em texto para valor numérico"""
        try:
            # Remover texto e manter apenas números e símbolos
            clean = re.sub(r'[^0-9.,R$]', '', salary_text)
            
            # Extrair valor numérico
            valor_match = re.search(r'R?\\$?\\s*([0-9]{1,3}(?:\\.[0-9]{3})*(?:,[0-9]{2})?)', clean)
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
        url = f"{self.base_url}/concursos/page/{page_num}"
        
        self.logger.info(f"📄 Coletando página {page_num}: {url}")
        
        response = self._safe_request(url)
        if not response:
            self.logger.error(f"❌ Falha ao acessar página {page_num}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar lista de concursos
        concursos_encontrados = []
        
        # Diferentes seletores possíveis
        seletores = [
            'div.ca',  # Selector principal
            'article.concurso',
            'div.item-concurso',
            'tr.concurso',
            'li.concurso-item'
        ]
        
        items = []
        for seletor in seletores:
            items = soup.select(seletor)
            if items:
                self.logger.info(f"✅ Encontrados {len(items)} itens com seletor: {seletor}")
                break
        
        if not items:
            # Fallback: buscar qualquer div que contenha links de concurso
            items = soup.find_all('div', class_=re.compile(r'.*concurso.*|.*item.*|.*ca.*'))
            self.logger.info(f"🔍 Fallback: encontrados {len(items)} itens")
        
        for item in items:
            concurso = self._parse_concurso(item)
            if concurso:
                concursos_encontrados.append(concurso)
        
        self.logger.info(f"📊 Página {page_num}: {len(concursos_encontrados)} concursos válidos")
        return concursos_encontrados
    
    def coletar_todos_concursos(self, max_pages: int = 50) -> List[Dict]:
        """Coleta TODOS os concursos disponíveis"""
        self.logger.info("🚀 INICIANDO COLETA COMPLETA DO PCI CONCURSO")
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
        
        # Remover duplicatas baseado no ID
        if todos_concursos:
            df = pd.DataFrame(todos_concursos)
            
            # Remover duplicatas por ID (se existir) ou título
            if 'id' in df.columns:
                df_unique = df.drop_duplicates(subset=['id'], keep='first')
            else:
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
            filename = f"pci_concursos_{timestamp}.csv"
        
        try:
            df = pd.DataFrame(self.concursos_coletados)
            df.to_csv(filename, index=False, encoding='utf-8')
            
            # Salvar também em JSON para backup
            json_filename = filename.replace('.csv', '.json')
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.concursos_coletados, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 Dados salvos em: {filename} e {json_filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar: {e}")
            return ""
    
    def obter_estatisticas(self) -> Dict:
        """Gera estatísticas dos dados coletados"""
        if not self.concursos_coletados:
            return {}
        
        df = pd.DataFrame(self.concursos_coletados)
        
        stats = {
            'total_concursos': len(df),
            'total_vagas': df['vagas'].sum(),
            'concursos_por_escolaridade': df['escolaridade'].value_counts().to_dict(),
            'concursos_por_status': df['status'].value_counts().to_dict(),
            'top_10_orgaos': df['orgao'].value_counts().head(10).to_dict(),
            'salario_medio': df[df['salario_numerico'] > 0]['salario_numerico'].mean(),
            'salario_max': df['salario_numerico'].max(),
            'concursos_com_salario': len(df[df['salario_numerico'] > 0])
        }
        
        return stats

def main():
    """Função principal para teste"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Criar scraper
    scraper = PCIConcursoScraperCompleto()
    
    try:
        # Coletar todos os concursos (limitar a 20 páginas para teste)
        concursos = scraper.coletar_todos_concursos(max_pages=20)
        
        if concursos:
            # Salvar dados
            filename = scraper.salvar_dados()
            
            # Mostrar estatísticas
            stats = scraper.obter_estatisticas()
            
            print("\\n📊 ESTATÍSTICAS FINAIS:")
            print("=" * 40)
            print(f"🎯 Total de concursos: {stats['total_concursos']}")
            print(f"👥 Total de vagas: {stats['total_vagas']}")
            print(f"💰 Salário médio: R$ {stats['salario_medio']:.2f}")
            print(f"💎 Maior salário: R$ {stats['salario_max']:.2f}")
            
            print("\\n🎓 Top 5 Escolaridades:")
            for escol, count in list(stats['concursos_por_escolaridade'].items())[:5]:
                print(f"   • {escol}: {count} concursos")
            
            print("\\n🏢 Top 5 Órgãos:")
            for orgao, count in list(stats['top_10_orgaos'].items())[:5]:
                print(f"   • {orgao}: {count} concursos")
                
        else:
            print("❌ Nenhum concurso foi coletado")
            
    except KeyboardInterrupt:
        print("\\n⏹️ Coleta interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante a coleta: {e}")

if __name__ == "__main__":
    main()
