"""
Sistema de Análise de PDFs de Provas com Upload
Permite usuário anexar PDF e receber:
- Análise automática de banca e área
- Tópicos mais cobrados
- Fluxograma de estudo personalizado
- Perguntas e respostas sobre o conteúdo
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import Counter
import PyPDF2

# Análise de bancas parametrizada
try:
    from modules.banca_area_analyzer import get_banca_area_analyzer, AREAS_CONHECIMENTO
    banca_analyzer = get_banca_area_analyzer()
    HAS_BANCA_ANALYZER = True
except ImportError:
    HAS_BANCA_ANALYZER = False
    AREAS_CONHECIMENTO = {}

# LangChain para RAG
try:
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.llms import Ollama
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain.chains import RetrievalQA
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False


class PDFAnalyzerUpload:
    """Analisa PDFs de provas enviados pelo usuário"""
    
    def __init__(self, output_dir: str = "provas/uploads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache de análises
        self.cache_file = self.output_dir / "analises_cache.json"
        self.cache = self._load_cache()
        
        # Configurar LangChain se disponível
        self.vectorstore = None
        self.qa_chain = None
        if HAS_LANGCHAIN:
            self._setup_langchain()
    
    def _load_cache(self) -> Dict:
        """Carrega cache de análises anteriores"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Salva cache de análises"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def _setup_langchain(self):
        """Configura sistema de RAG com LangChain"""
        try:
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
            self.llm = Ollama(model="llama3.2", temperature=0.7)
            print("✅ LangChain configurado para análise de PDFs")
        except Exception as e:
            print(f"⚠️ Erro ao configurar LangChain: {e}")
    
    def extrair_texto_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extrai texto do PDF e metadados básicos
        
        Returns:
            (texto_completo, metadados)
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadados = {
                    'num_paginas': len(pdf_reader.pages),
                    'titulo': pdf_reader.metadata.get('/Title', 'Sem título') if pdf_reader.metadata else 'Sem título',
                    'autor': pdf_reader.metadata.get('/Author', 'Desconhecido') if pdf_reader.metadata else 'Desconhecido',
                    'data_criacao': str(pdf_reader.metadata.get('/CreationDate', '')) if pdf_reader.metadata else '',
                }
                
                # Extrair texto de todas as páginas
                texto_completo = ""
                for page in pdf_reader.pages:
                    texto_completo += page.extract_text() + "\n\n"
                
                return texto_completo, metadados
                
        except Exception as e:
            raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")
    
    def detectar_banca(self, texto: str) -> Optional[str]:
        """Detecta qual banca organizou a prova"""
        texto_lower = texto.lower()
        
        bancas = {
            'cebraspe': ['cebraspe', 'cespe', 'universidade de brasília', 'unb'],
            'fcc': ['fcc', 'fundação carlos chagas', 'carlos chagas'],
            'fgv': ['fgv', 'fundação getulio vargas', 'getúlio vargas', 'getulio vargas'],
            'vunesp': ['vunesp', 'universidade estadual paulista', 'unesp'],
            'cesgranrio': ['cesgranrio', 'fundação cesgranrio'],
            'quadrix': ['quadrix'],
            'aocp': ['aocp'],
            'ibfc': ['ibfc', 'instituto brasileiro'],
        }
        
        for banca, keywords in bancas.items():
            if any(keyword in texto_lower for keyword in keywords):
                return banca
        
        return None
    
    def detectar_area(self, texto: str) -> Optional[str]:
        """Detecta a área de conhecimento da prova"""
        if not AREAS_CONHECIMENTO:
            return None
        
        texto_lower = texto.lower()
        
        # Contagem de keywords por área
        scores = {}
        for area, config in AREAS_CONHECIMENTO.items():
            score = 0
            keywords = config.get('keywords', [])
            
            for keyword in keywords:
                if keyword.lower() in texto_lower:
                    score += texto_lower.count(keyword.lower())
            
            scores[area] = score
        
        # Retorna área com maior score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return None
    
    def extrair_topicos(self, texto: str, area: str = None) -> Dict[str, int]:
        """
        Extrai tópicos mais mencionados no texto
        
        Returns:
            {topico: frequencia}
        """
        texto_lower = texto.lower()
        topicos = Counter()
        
        # Se área conhecida, usar disciplinas específicas
        if area and area in AREAS_CONHECIMENTO:
            disciplinas = AREAS_CONHECIMENTO[area].get('disciplinas', [])
            for disciplina in disciplinas:
                count = texto_lower.count(disciplina.lower())
                if count > 0:
                    topicos[disciplina] = count
        
        # Padrões gerais de tópicos em provas
        patterns = {
            # Tecnologia
            r'\b(python|java|javascript|c\+\+|sql|html|css|php|ruby)\b': 'Linguagens de Programação',
            r'\b(banco de dados|postgresql|mysql|oracle|sql server)\b': 'Banco de Dados',
            r'\b(rede|tcp/ip|http|dns|firewall|vpn)\b': 'Redes',
            r'\b(segurança|criptografia|ssl|tls|vulnerabilidade)\b': 'Segurança da Informação',
            r'\b(devops|docker|kubernetes|jenkins|git)\b': 'DevOps',
            
            # Jurídica
            r'\b(constituição|constitucional|cf/88)\b': 'Direito Constitucional',
            r'\b(administrativo|servidor público|licitação)\b': 'Direito Administrativo',
            r'\b(penal|crime|delito|pena)\b': 'Direito Penal',
            r'\b(processo|recurso|sentença|ação)\b': 'Direito Processual',
            
            # Português
            r'\b(concordância|regência|crase|ortografia)\b': 'Gramática',
            r'\b(interpretação|texto|compreensão)\b': 'Interpretação de Texto',
            r'\b(redação|dissertação|argumentação)\b': 'Redação',
            
            # Conhecimentos Gerais
            r'\b(história|brasil|mundo|guerra)\b': 'História',
            r'\b(geografia|clima|região|território)\b': 'Geografia',
            r'\b(política|governo|democracia|eleição)\b': 'Atualidades',
        }
        
        for pattern, topico in patterns.items():
            matches = len(re.findall(pattern, texto_lower))
            if matches > 0:
                topicos[topico] = matches
        
        return dict(topicos.most_common(15))
    
    def analisar_pdf_completo(self, pdf_path: str, nome_arquivo: str) -> Dict:
        """
        Análise completa do PDF
        
        Returns:
            {
                'banca': str,
                'area': str,
                'topicos': {topico: freq},
                'metadados': dict,
                'texto': str,
                'timestamp': str,
                'id_analise': str
            }
        """
        # Verificar cache
        cache_key = f"{nome_arquivo}_{os.path.getsize(pdf_path)}"
        if cache_key in self.cache:
            print(f"✅ Usando análise em cache para {nome_arquivo}")
            return self.cache[cache_key]
        
        print(f"🔍 Analisando PDF: {nome_arquivo}")
        
        # Extrair texto
        texto, metadados = self.extrair_texto_pdf(pdf_path)
        
        # Detectar banca e área
        banca = self.detectar_banca(texto)
        area = self.detectar_area(texto)
        
        print(f"  📋 Banca detectada: {banca or 'Desconhecida'}")
        print(f"  📚 Área detectada: {area or 'Desconhecida'}")
        
        # Extrair tópicos
        topicos = self.extrair_topicos(texto, area)
        
        # Análise contextual com banca_analyzer
        analise_contextual = None
        if HAS_BANCA_ANALYZER and banca and area:
            try:
                # Processar PDF na estrutura de bancas
                pasta_banca = self.output_dir / banca / area
                pasta_banca.mkdir(parents=True, exist_ok=True)
                
                # Copiar PDF para estrutura organizada
                import shutil
                destino_pdf = pasta_banca / nome_arquivo
                shutil.copy2(pdf_path, destino_pdf)
                
                # Processar com analyzer
                banca_analyzer.processar_banca_area(banca, area)
                
                # Consultar perfil
                analise_contextual = banca_analyzer.consultar_perfil(
                    banca, 
                    area, 
                    "O que é mais cobrado? Quais padrões específicos?"
                )
                
            except Exception as e:
                print(f"⚠️ Erro na análise contextual: {e}")
        
        # Montar resultado
        id_analise = f"{banca or 'unknown'}_{area or 'unknown'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        resultado = {
            'id_analise': id_analise,
            'nome_arquivo': nome_arquivo,
            'banca': banca,
            'area': area,
            'topicos': topicos,
            'metadados': metadados,
            'texto': texto[:5000],  # Primeiros 5000 chars para cache
            'analise_contextual': analise_contextual,
            'timestamp': datetime.now().isoformat()
        }
        
        # Salvar em cache
        self.cache[cache_key] = resultado
        self._save_cache()
        
        return resultado
    
    def gerar_fluxograma_estudo(self, analise: Dict) -> str:
        """
        Gera fluxograma de estudo em formato Mermaid baseado na análise
        
        Returns:
            Código Mermaid do fluxograma
        """
        banca = analise.get('banca', 'Banca')
        area = analise.get('area', 'Área')
        topicos = analise.get('topicos', {})
        
        # Ordenar tópicos por frequência
        topicos_ordenados = sorted(topicos.items(), key=lambda x: x[1], reverse=True)
        
        mermaid = f"""```mermaid
graph TD
    A[📋 Preparação para {banca.upper() if banca else 'Concurso'}]
    A --> B{{Área: {area or 'Conhecimento'}}}
    
"""
        
        # Adicionar tópicos prioritários (top 5)
        if topicos_ordenados:
            mermaid += f"    B --> C1[🎯 PRIORIDADE ALTA]\n"
            
            for i, (topico, freq) in enumerate(topicos_ordenados[:5], 1):
                node_id = f"T{i}"
                percentual = (freq / sum(topicos.values()) * 100) if sum(topicos.values()) > 0 else 0
                mermaid += f"    C1 --> {node_id}[{topico}<br/>📊 {percentual:.1f}% das questões]\n"
            
            # Adicionar tópicos secundários (próximos 5)
            if len(topicos_ordenados) > 5:
                mermaid += f"\n    B --> C2[📚 PRIORIDADE MÉDIA]\n"
                
                for i, (topico, freq) in enumerate(topicos_ordenados[5:10], 6):
                    node_id = f"T{i}"
                    percentual = (freq / sum(topicos.values()) * 100) if sum(topicos.values()) > 0 else 0
                    mermaid += f"    C2 --> {node_id}[{topico}<br/>📊 {percentual:.1f}%]\n"
        
        # Adicionar estratégia de estudo
        mermaid += f"""
    B --> D[📅 Estratégia de Estudo]
    D --> D1[Semana 1-2: Tópicos Prioritários]
    D --> D2[Semana 3-4: Tópicos Médios]
    D --> D3[Semana 5+: Revisão Geral]
    
    D1 -.-> E[✅ Fazer questões]
    D2 -.-> E
    D3 -.-> E
    E --> F[🎓 Pronto para Prova!]
    
    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C1 fill:#FF5722,color:#fff
    style C2 fill:#FF9800,color:#fff
    style F fill:#4CAF50,color:#fff
```"""
        
        return mermaid
    
    def criar_vectorstore_pdf(self, texto: str) -> bool:
        """Cria vectorstore para fazer perguntas sobre o PDF"""
        if not HAS_LANGCHAIN:
            return False
        
        try:
            # Split texto em chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_text(texto)
            
            # Criar vectorstore
            self.vectorstore = Chroma.from_texts(
                texts=chunks,
                embedding=self.embeddings,
                persist_directory=str(self.output_dir / "vectorstore_temp")
            )
            
            # Criar QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3})
            )
            
            return True
            
        except Exception as e:
            print(f"⚠️ Erro ao criar vectorstore: {e}")
            return False
    
    def responder_pergunta_pdf(self, pergunta: str, analise: Dict) -> str:
        """Responde pergunta específica sobre o PDF analisado"""
        
        # Tentar usar QA chain se disponível
        if self.qa_chain:
            try:
                resultado = self.qa_chain.invoke({"query": pergunta})
                return resultado['result']
            except Exception as e:
                print(f"⚠️ Erro no QA chain: {e}")
        
        # Fallback: resposta baseada em análise
        banca = analise.get('banca', 'desconhecida')
        area = analise.get('area', 'desconhecida')
        topicos = analise.get('topicos', {})
        
        resposta = f"""**Análise da Prova {banca.upper() if banca else 'Desconhecida'} - {area or 'Área Desconhecida'}**

📊 **Tópicos Mais Cobrados:**
"""
        
        for i, (topico, freq) in enumerate(list(topicos.items())[:10], 1):
            percentual = (freq / sum(topicos.values()) * 100) if sum(topicos.values()) > 0 else 0
            resposta += f"{i}. {topico}: {percentual:.1f}% ({freq} menções)\n"
        
        if analise.get('analise_contextual'):
            resposta += f"\n\n**Análise Contextual:**\n{analise['analise_contextual'][:500]}..."
        
        return resposta


# Singleton
_pdf_analyzer_instance = None

def get_pdf_analyzer() -> PDFAnalyzerUpload:
    """Retorna instância única do analisador de PDFs"""
    global _pdf_analyzer_instance
    if _pdf_analyzer_instance is None:
        _pdf_analyzer_instance = PDFAnalyzerUpload()
    return _pdf_analyzer_instance


# Teste rápido
if __name__ == "__main__":
    analyzer = get_pdf_analyzer()
    print("✅ PDFAnalyzerUpload inicializado")
    print(f"📁 Diretório de saída: {analyzer.output_dir}")
    
    # Teste com PDF se disponível
    provas_dir = Path("provas")
    if provas_dir.exists():
        pdfs = list(provas_dir.rglob("*.pdf"))
        if pdfs:
            print(f"\n🔍 Testando com: {pdfs[0].name}")
            analise = analyzer.analisar_pdf_completo(str(pdfs[0]), pdfs[0].name)
            print(f"📋 Banca: {analise['banca']}")
            print(f"📚 Área: {analise['area']}")
            print(f"🎯 Top 5 tópicos:")
            for topico, freq in list(analise['topicos'].items())[:5]:
                print(f"   - {topico}: {freq}")
            
            print("\n📊 Gerando fluxograma...")
            fluxograma = analyzer.gerar_fluxograma_estudo(analise)
            print(fluxograma[:500] + "...")
