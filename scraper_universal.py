"""
Scraper Universal de Concursos
==============================
Scraper robusto que se adapta a diferentes estruturas de sites
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import time
import random

class UniversalConcursoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Padrões para encontrar informações
        self.patterns = {
            'concurso_keywords': [
                'concurso', 'edital', 'seleção', 'processo seletivo',
                'certame', 'teste seletivo'
            ],
            'salary_patterns': [
                r'R\$\s*[\d.,]+',
                r'até\s*R\$\s*[\d.,]+',
                r'salário.*?R\$\s*[\d.,]+',
                r'remuneração.*?R\$\s*[\d.,]+',
                r'vencimento.*?R\$\s*[\d.,]+',
                r'(\d+)\.?\d*\s*mil'
            ],
            'vagas_patterns': [
                r'(\d+)\s*vagas?',
                r'vagas?:?\s*(\d+)',
                r'total.*?(\d+).*?vagas?',
                r'(\d+)\s*oportunidades?'
            ],
            'status_patterns': [
                r'inscrições?\s+abertas?',
                r'edital\s+publicado',
                r'em\s+andamento',
                r'previsto',
                r'ativo',
                r'aberto'
            ]
        }
    
    def scrape_site(self, base_url: str, search_terms: List[str] = None) -> List[Dict]:
        """
        Faz scraping de um site de forma adaptativa
        
        Args:
            base_url: URL base do site
            search_terms: Termos para buscar (opcional)
            
        Returns:
            Lista de concursos encontrados
        """
        concursos = []
        
        print(f"🔍 Iniciando scraping de: {base_url}")
        
        try:
            # Primeira tentativa: página inicial
            concursos.extend(self._scrape_page(base_url))
            
            # Se temos termos de busca, tentar páginas de busca
            if search_terms:
                for term in search_terms[:3]:  # Limitar a 3 termos
                    search_urls = self._generate_search_urls(base_url, term)
                    
                    for url in search_urls:
                        try:
                            page_concursos = self._scrape_page(url)
                            concursos.extend(page_concursos)
                            time.sleep(2)  # Pausa entre requests
                        except Exception as e:
                            print(f"⚠️ Erro na URL {url}: {e}")
                            continue
        
        except Exception as e:
            print(f"❌ Erro geral no site {base_url}: {e}")
        
        # Remover duplicatas
        concursos_unicos = self._remove_duplicates(concursos)
        
        print(f"✅ {base_url}: {len(concursos_unicos)} concursos únicos encontrados")
        
        return concursos_unicos
    
    def _generate_search_urls(self, base_url: str, term: str) -> List[str]:
        """Gera URLs de busca possíveis"""
        search_urls = []
        
        # Padrões comuns de URL de busca
        patterns = [
            f"{base_url}/concursos/?q={term}",
            f"{base_url}/busca?termo={term}",
            f"{base_url}/search?q={term}",
            f"{base_url}/pesquisa?busca={term}",
            f"{base_url}/?s={term}",
            f"{base_url}/concursos/buscar?termo={term}"
        ]
        
        return patterns
    
    def _scrape_page(self, url: str) -> List[Dict]:
        """Faz scraping de uma página específica"""
        concursos = []
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tentar diferentes estratégias para encontrar concursos
            estrategias = [
                self._find_by_table_rows,
                self._find_by_divs,
                self._find_by_articles,
                self._find_by_lists,
                self._find_by_keywords
            ]
            
            for estrategia in estrategias:
                elementos = estrategia(soup)
                if elementos:
                    print(f"✅ Estratégia {estrategia.__name__} encontrou {len(elementos)} elementos")
                    
                    for elemento in elementos:
                        concurso = self._extract_concurso_info(elemento, url)
                        if concurso:
                            concursos.append(concurso)
                    
                    break  # Se uma estratégia funcionou, usar ela
            
        except Exception as e:
            print(f"❌ Erro ao processar {url}: {e}")
        
        return concursos
    
    def _find_by_table_rows(self, soup: BeautifulSoup) -> List:
        """Busca por linhas de tabela"""
        # Procurar tabelas com concursos
        tables = soup.find_all('table')
        rows = []
        
        for table in tables:
            table_text = table.get_text().lower()
            if any(keyword in table_text for keyword in self.patterns['concurso_keywords']):
                rows.extend(table.find_all('tr')[1:])  # Pular cabeçalho
        
        return rows
    
    def _find_by_divs(self, soup: BeautifulSoup) -> List:
        """Busca por divs com concursos"""
        selectors = [
            'div[class*="concurso"]',
            'div[class*="edital"]',
            'div[class*="card"]',
            'div[class*="item"]',
            'div[class*="resultado"]'
        ]
        
        divs = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                divs.extend(found)
        
        return divs
    
    def _find_by_articles(self, soup: BeautifulSoup) -> List:
        """Busca por articles"""
        return soup.find_all('article')
    
    def _find_by_lists(self, soup: BeautifulSoup) -> List:
        """Busca por listas"""
        lists = soup.find_all(['ul', 'ol'])
        items = []
        
        for lst in lists:
            list_text = lst.get_text().lower()
            if any(keyword in list_text for keyword in self.patterns['concurso_keywords']):
                items.extend(lst.find_all('li'))
        
        return items
    
    def _find_by_keywords(self, soup: BeautifulSoup) -> List:
        """Busca por elementos que contenham palavras-chave"""
        elements = []
        
        for keyword in self.patterns['concurso_keywords']:
            found = soup.find_all(text=re.compile(keyword, re.I))
            for text in found:
                parent = text.parent
                if parent and parent not in elements:
                    elements.append(parent)
        
        return elements
    
    def _extract_concurso_info(self, elemento, source_url: str) -> Optional[Dict]:
        """Extrai informações de um elemento"""
        try:
            text = elemento.get_text() if hasattr(elemento, 'get_text') else str(elemento)
            
            # Verificar se realmente parece ser um concurso
            if not any(keyword in text.lower() for keyword in self.patterns['concurso_keywords']):
                return None
            
            concurso = {
                'texto_completo': text.strip(),
                'fonte_url': source_url,
                'data_coleta': datetime.now().isoformat()
            }
            
            # Extrair título (primeira linha ou elemento com destaque)
            titulo = self._extract_title(elemento, text)
            if titulo:
                concurso['titulo'] = titulo
            
            # Extrair salário
            salario = self._extract_salary(text)
            if salario:
                concurso['salario'] = salario
            
            # Extrair vagas
            vagas = self._extract_vagas(text)
            if vagas:
                concurso['vagas'] = vagas
            
            # Extrair órgão/instituição
            orgao = self._extract_orgao(text)
            if orgao:
                concurso['orgao'] = orgao
            
            # Extrair status
            status = self._extract_status(text)
            if status:
                concurso['status'] = status
            
            # Extrair links
            links = self._extract_links(elemento)
            if links:
                concurso['links'] = links
            
            return concurso
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair info: {e}")
            return None
    
    def _extract_title(self, elemento, text: str) -> Optional[str]:
        """Extrai título do concurso"""
        # Procurar por elementos de título
        title_elements = elemento.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b']) if hasattr(elemento, 'find_all') else []
        
        for elem in title_elements:
            title_text = elem.get_text().strip()
            if len(title_text) > 10 and any(kw in title_text.lower() for kw in self.patterns['concurso_keywords']):
                return title_text[:200]  # Limitar tamanho
        
        # Fallback: primeira linha do texto
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and any(kw in line.lower() for kw in self.patterns['concurso_keywords']):
                return line[:200]
        
        return None
    
    def _extract_salary(self, text: str) -> Optional[str]:
        """Extrai informação de salário"""
        for pattern in self.patterns['salary_patterns']:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0).strip()
        return None
    
    def _extract_vagas(self, text: str) -> Optional[int]:
        """Extrai número de vagas"""
        for pattern in self.patterns['vagas_patterns']:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        return None
    
    def _extract_orgao(self, text: str) -> Optional[str]:
        """Extrai órgão/instituição"""
        # Procurar por padrões comuns
        patterns = [
            r'(prefeitura[^.]*)',
            r'(tribunal[^.]*)',
            r'(governo[^.]*)',
            r'(secretaria[^.]*)',
            r'(instituto[^.]*)',
            r'(fundação[^.]*)',
            r'(universidade[^.]*)',
            r'(câmara[^.]*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()[:100]
        
        return None
    
    def _extract_status(self, text: str) -> Optional[str]:
        """Extrai status do concurso"""
        for pattern in self.patterns['status_patterns']:
            if re.search(pattern, text, re.I):
                return pattern.replace('\\s+', ' ').replace('?', '').strip()
        return None
    
    def _extract_links(self, elemento) -> List[str]:
        """Extrai links do elemento"""
        links = []
        
        if hasattr(elemento, 'find_all'):
            link_elements = elemento.find_all('a')
            for link in link_elements:
                href = link.get('href')
                if href:
                    links.append(href)
        
        return links
    
    def _remove_duplicates(self, concursos: List[Dict]) -> List[Dict]:
        """Remove concursos duplicados"""
        seen = set()
        unicos = []
        
        for concurso in concursos:
            # Usar título como chave de identificação
            key = concurso.get('titulo', concurso.get('texto_completo', ''))[:50].lower()
            
            if key and key not in seen:
                seen.add(key)
                unicos.append(concurso)
        
        return unicos
    
    def save_results(self, concursos: List[Dict], filename: str = None):
        """Salva resultados em JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'concursos_coletados_{timestamp}.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(concursos, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Resultados salvos em: {filename}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")

# Função principal para executar coleta
def executar_coleta():
    """Executa coleta em múltiplos sites"""
    
    scraper = UniversalConcursoScraper()
    
    # Sites para coletar
    sites = [
        "https://www.pciconcursos.com.br",
        "https://www.concursosnobrasil.com.br"
    ]
    
    # Termos de busca
    termos = ["programador", "analista", "desenvolvedor", "TI"]
    
    todos_concursos = []
    
    print("🚀 Iniciando coleta universal de concursos...")
    print("=" * 60)
    
    for site in sites:
        print(f"\n📍 Processando: {site}")
        
        try:
            concursos_site = scraper.scrape_site(site, termos)
            todos_concursos.extend(concursos_site)
            
            print(f"✅ {site}: {len(concursos_site)} concursos coletados")
            
        except Exception as e:
            print(f"❌ Erro em {site}: {e}")
        
        time.sleep(5)  # Pausa entre sites
    
    print(f"\n🎯 RESULTADO FINAL:")
    print(f"📊 Total coletado: {len(todos_concursos)} concursos")
    
    if todos_concursos:
        # Salvar resultados
        scraper.save_results(todos_concursos)
        
        # Mostrar exemplos
        print(f"\n📋 EXEMPLOS COLETADOS:")
        for i, concurso in enumerate(todos_concursos[:3], 1):
            print(f"\n{i}. {concurso.get('titulo', 'Sem título')}")
            if concurso.get('orgao'):
                print(f"   🏛️ {concurso['orgao']}")
            if concurso.get('salario'):
                print(f"   💰 {concurso['salario']}")
            if concurso.get('vagas'):
                print(f"   👥 {concurso['vagas']} vagas")
    
    return todos_concursos

if __name__ == "__main__":
    executar_coleta()
