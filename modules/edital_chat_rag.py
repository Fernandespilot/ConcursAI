"""
Sistema de Chat RAG para Análise de Editais
============================================
Sistema robusto de Q&A sobre editais de concursos usando RAG
(Retrieval-Augmented Generation)
"""

import os
import re
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

# Importações principais
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PyMuPDF não disponível. Instale com: pip install PyMuPDF")

try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ Sentence Transformers ou ChromaDB não disponíveis")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EditalChatRAG:
    """
    Sistema de chat conversacional sobre editais usando RAG
    """
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 llm_provider: str = "groq"):
        """
        Inicializa o sistema de chat RAG
        
        Args:
            model_name: Nome do modelo de embeddings
            chunk_size: Tamanho dos chunks de texto
            chunk_overlap: Sobreposição entre chunks
            llm_provider: Provedor de LLM ('groq', 'openai', 'local')
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.llm_provider = llm_provider
        
        # Inicializar modelo de embeddings
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(model_name)
                logger.info(f"✅ Modelo de embeddings carregado: {model_name}")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar modelo: {e}")
                self.embedding_model = None
        else:
            self.embedding_model = None
        
        # Inicializar ChromaDB
        if EMBEDDINGS_AVAILABLE:
            try:
                self.chroma_client = chromadb.Client(Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                ))
                logger.info("✅ ChromaDB inicializado")
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar ChromaDB: {e}")
                self.chroma_client = None
        else:
            self.chroma_client = None
        
        # Armazenamento de editais e histórico
        self.editais = {}  # {edital_id: {metadados, chunks, collection}}
        self.chat_history = {}  # {session_id: [{role, content, timestamp}]}
        
        # Configurar API keys
        self._setup_llm()
    
    def _setup_llm(self):
        """Configura o provedor de LLM"""
        if self.llm_provider == "groq" and GROQ_AVAILABLE:
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                self.groq_client = groq.Groq(api_key=groq_key)
                logger.info("✅ Groq API configurada")
            else:
                logger.warning("⚠️ GROQ_API_KEY não encontrada")
                self.groq_client = None
        
        elif self.llm_provider == "openai" and OPENAI_AVAILABLE:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                openai.api_key = openai_key
                logger.info("✅ OpenAI API configurada")
            else:
                logger.warning("⚠️ OPENAI_API_KEY não encontrada")
    
    def extrair_texto_pdf(self, pdf_path: str) -> str:
        """
        Extrai texto de um PDF
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Returns:
            Texto extraído
        """
        if not PDF_AVAILABLE:
            raise Exception("PyMuPDF não está instalado")
        
        try:
            texto_completo = []
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc, 1):
                texto = page.get_text()
                
                # Limpar texto
                texto = self._limpar_texto(texto)
                
                if texto.strip():
                    texto_completo.append(f"[Página {page_num}]\n{texto}")
            
            doc.close()
            
            texto_final = "\n\n".join(texto_completo)
            logger.info(f"✅ Extraído texto de {len(doc)} páginas ({len(texto_final)} caracteres)")
            
            return texto_final
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair PDF: {e}")
            raise
    
    def _limpar_texto(self, texto: str) -> str:
        """
        Limpa e normaliza texto extraído
        
        Args:
            texto: Texto bruto
            
        Returns:
            Texto limpo
        """
        # Remover quebras de linha excessivas
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        
        # Remover espaços múltiplos
        texto = re.sub(r' {2,}', ' ', texto)
        
        # Remover caracteres especiais problemáticos
        texto = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', texto)
        
        return texto.strip()
    
    def dividir_em_chunks(self, texto: str) -> List[Dict[str, Any]]:
        """
        Divide texto em chunks com overlap
        
        Args:
            texto: Texto completo
            
        Returns:
            Lista de chunks com metadados
        """
        # Separar por páginas
        paginas = texto.split('[Página ')
        
        chunks = []
        chunk_id = 0
        
        for pagina in paginas:
            if not pagina.strip():
                continue
            
            # Extrair número da página
            match = re.match(r'(\d+)\](.+)', pagina, re.DOTALL)
            if match:
                num_pagina = int(match.group(1))
                conteudo_pagina = match.group(2).strip()
            else:
                num_pagina = 0
                conteudo_pagina = pagina.strip()
            
            # Dividir página em chunks
            palavras = conteudo_pagina.split()
            
            i = 0
            while i < len(palavras):
                # Pegar chunk_size palavras
                chunk_palavras = palavras[i:i + self.chunk_size]
                chunk_texto = ' '.join(chunk_palavras)
                
                # Adicionar chunk
                chunks.append({
                    'id': f'chunk_{chunk_id}',
                    'texto': chunk_texto,
                    'pagina': num_pagina,
                    'posicao': i,
                    'tamanho': len(chunk_palavras)
                })
                
                chunk_id += 1
                i += self.chunk_size - self.chunk_overlap
        
        logger.info(f"✅ Texto dividido em {len(chunks)} chunks")
        return chunks
    
    def adicionar_edital(self, 
                         edital_id: str,
                         pdf_path: str = None,
                         texto: str = None,
                         metadados: Dict = None) -> bool:
        """
        Adiciona um edital ao sistema
        
        Args:
            edital_id: ID único do edital
            pdf_path: Caminho do PDF (opcional)
            texto: Texto direto (opcional)
            metadados: Metadados adicionais
            
        Returns:
            True se sucesso
        """
        try:
            # Extrair texto
            if pdf_path:
                texto_edital = self.extrair_texto_pdf(pdf_path)
            elif texto:
                texto_edital = texto
            else:
                raise ValueError("É necessário fornecer pdf_path ou texto")
            
            # Dividir em chunks
            chunks = self.dividir_em_chunks(texto_edital)
            
            # Criar collection no ChromaDB
            if self.chroma_client and self.embedding_model:
                try:
                    # Deletar collection se já existir
                    try:
                        self.chroma_client.delete_collection(f"edital_{edital_id}")
                    except:
                        pass
                    
                    collection = self.chroma_client.create_collection(
                        name=f"edital_{edital_id}",
                        metadata={"edital_id": edital_id}
                    )
                    
                    # Adicionar chunks à collection
                    textos = [c['texto'] for c in chunks]
                    embeddings = self.embedding_model.encode(textos).tolist()
                    
                    collection.add(
                        embeddings=embeddings,
                        documents=textos,
                        metadatas=[{'pagina': c['pagina'], 'chunk_id': c['id']} for c in chunks],
                        ids=[c['id'] for c in chunks]
                    )
                    
                    logger.info(f"✅ {len(chunks)} chunks adicionados ao ChromaDB")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao adicionar ao ChromaDB: {e}")
                    collection = None
            else:
                collection = None
            
            # Armazenar edital
            self.editais[edital_id] = {
                'texto_completo': texto_edital,
                'chunks': chunks,
                'collection': collection,
                'metadados': metadados or {},
                'data_upload': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Edital {edital_id} adicionado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar edital: {e}")
            return False
    
    def buscar_chunks_relevantes(self, 
                                   edital_id: str,
                                   pergunta: str,
                                   n_results: int = 5) -> List[Dict]:
        """
        Busca chunks relevantes para uma pergunta
        
        Args:
            edital_id: ID do edital
            pergunta: Pergunta do usuário
            n_results: Número de chunks a retornar
            
        Returns:
            Lista de chunks relevantes
        """
        if edital_id not in self.editais:
            return []
        
        edital = self.editais[edital_id]
        
        # Buscar com ChromaDB se disponível
        if edital['collection'] and self.embedding_model:
            try:
                # Gerar embedding da pergunta
                query_embedding = self.embedding_model.encode([pergunta]).tolist()
                
                # Buscar no ChromaDB
                results = edital['collection'].query(
                    query_embeddings=query_embedding,
                    n_results=min(n_results, len(edital['chunks']))
                )
                
                chunks_relevantes = []
                for i, doc in enumerate(results['documents'][0]):
                    chunks_relevantes.append({
                        'texto': doc,
                        'pagina': results['metadatas'][0][i]['pagina'],
                        'relevancia': 1.0 - (i / n_results)  # Score simples
                    })
                
                return chunks_relevantes
                
            except Exception as e:
                logger.error(f"❌ Erro na busca com ChromaDB: {e}")
        
        # Fallback: busca por palavras-chave
        palavras_chave = set(pergunta.lower().split())
        chunks_scored = []
        
        for chunk in edital['chunks']:
            texto_lower = chunk['texto'].lower()
            score = sum(1 for palavra in palavras_chave if palavra in texto_lower)
            
            if score > 0:
                chunks_scored.append({
                    'texto': chunk['texto'],
                    'pagina': chunk['pagina'],
                    'relevancia': score
                })
        
        # Ordenar por score e retornar top N
        chunks_scored.sort(key=lambda x: x['relevancia'], reverse=True)
        return chunks_scored[:n_results]
    
    def gerar_resposta(self, 
                       pergunta: str,
                       chunks_contexto: List[Dict],
                       historico: List[Dict] = None) -> str:
        """
        Gera resposta usando LLM
        
        Args:
            pergunta: Pergunta do usuário
            chunks_contexto: Chunks relevantes para contexto
            historico: Histórico de conversação
            
        Returns:
            Resposta gerada
        """
        # Preparar contexto
        contexto = "\n\n".join([
            f"[Página {c['pagina']}]\n{c['texto']}"
            for c in chunks_contexto
        ])
        
        # Preparar prompt
        prompt = f"""Você é um assistente especializado em análise de editais de concursos públicos.

Seu papel é responder perguntas sobre o edital de forma clara, precisa e objetiva.
Use APENAS as informações do contexto fornecido. Se a informação não estiver no contexto, diga que não encontrou.

CONTEXTO DO EDITAL:
{contexto}

PERGUNTA DO USUÁRIO:
{pergunta}

INSTRUÇÕES:
- Responda de forma direta e objetiva
- Cite números de páginas quando relevante
- Se houver listas (cargos, requisitos, etc.), organize-as claramente
- Se não encontrar a informação, diga claramente
- Não invente informações que não estão no contexto

RESPOSTA:"""
        
        try:
            # Tentar Groq primeiro
            if self.llm_provider == "groq" and hasattr(self, 'groq_client') and self.groq_client:
                try:
                    response = self.groq_client.chat.completions.create(
                        model="mixtral-8x7b-32768",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"❌ Erro com Groq: {e}")
            
            # Fallback OpenAI
            if self.llm_provider == "openai" or not hasattr(self, 'groq_client'):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"❌ Erro com OpenAI: {e}")
            
            # Fallback final: resposta baseada em regras
            return self._resposta_fallback(pergunta, chunks_contexto)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta: {e}")
            return self._resposta_fallback(pergunta, chunks_contexto)
    
    def _resposta_fallback(self, pergunta: str, chunks: List[Dict]) -> str:
        """Resposta fallback quando LLM não está disponível"""
        if not chunks:
            return "Desculpe, não encontrei informações relevantes sobre sua pergunta no edital."
        
        # Resposta simples mostrando os trechos relevantes
        resposta = f"Encontrei as seguintes informações relevantes:\n\n"
        
        for i, chunk in enumerate(chunks[:3], 1):
            resposta += f"{i}. [Página {chunk['pagina']}]\n{chunk['texto'][:300]}...\n\n"
        
        return resposta
    
    def chat(self, 
             session_id: str,
             edital_id: str,
             pergunta: str) -> Dict[str, Any]:
        """
        Interface principal de chat
        
        Args:
            session_id: ID da sessão de chat
            edital_id: ID do edital
            pergunta: Pergunta do usuário
            
        Returns:
            Dicionário com resposta e metadados
        """
        try:
            # Validar edital
            if edital_id not in self.editais:
                return {
                    'success': False,
                    'error': f'Edital {edital_id} não encontrado'
                }
            
            # Buscar chunks relevantes
            chunks = self.buscar_chunks_relevantes(edital_id, pergunta, n_results=5)
            
            if not chunks:
                return {
                    'success': True,
                    'resposta': 'Não encontrei informações relevantes sobre sua pergunta no edital.',
                    'chunks_usados': 0,
                    'paginas_referenciadas': []
                }
            
            # Obter histórico
            historico = self.chat_history.get(session_id, [])
            
            # Gerar resposta
            resposta = self.gerar_resposta(pergunta, chunks, historico)
            
            # Atualizar histórico
            if session_id not in self.chat_history:
                self.chat_history[session_id] = []
            
            self.chat_history[session_id].append({
                'role': 'user',
                'content': pergunta,
                'timestamp': datetime.now().isoformat()
            })
            
            self.chat_history[session_id].append({
                'role': 'assistant',
                'content': resposta,
                'timestamp': datetime.now().isoformat()
            })
            
            # Preparar resposta
            return {
                'success': True,
                'resposta': resposta,
                'chunks_usados': len(chunks),
                'paginas_referenciadas': sorted(set(c['pagina'] for c in chunks)),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no chat: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def obter_historico(self, session_id: str) -> List[Dict]:
        """Retorna histórico de uma sessão"""
        return self.chat_history.get(session_id, [])
    
    def limpar_historico(self, session_id: str):
        """Limpa histórico de uma sessão"""
        if session_id in self.chat_history:
            del self.chat_history[session_id]
    
    def listar_editais(self) -> List[Dict]:
        """Lista todos os editais carregados"""
        return [
            {
                'edital_id': edital_id,
                'metadados': edital['metadados'],
                'num_chunks': len(edital['chunks']),
                'data_upload': edital['data_upload']
            }
            for edital_id, edital in self.editais.items()
        ]


# Exemplo de uso
if __name__ == "__main__":
    print("🤖 Sistema de Chat RAG para Editais\n")
    
    # Criar sistema
    chat_system = EditalChatRAG(llm_provider="groq")
    
    # Simular edital
    texto_exemplo = """
    EDITAL DE CONCURSO PÚBLICO
    
    [Página 1]
    TRIBUNAL REGIONAL DO TRABALHO
    
    1. CARGOS DISPONÍVEIS:
    - Analista Judiciário - Área Administrativa
    - Analista Judiciário - Tecnologia da Informação
    - Técnico Judiciário - Área Administrativa
    
    2. REQUISITOS:
    - Analista: Ensino Superior Completo
    - Técnico: Ensino Médio Completo
    
    [Página 2]
    3. REMUNERAÇÃO:
    - Analista: R$ 12.455,30
    - Técnico: R$ 7.920,50
    
    4. INSCRIÇÕES:
    - Período: 01/12/2025 a 31/12/2025
    - Taxa: R$ 120,00 (Analista) / R$ 80,00 (Técnico)
    """
    
    # Adicionar edital
    success = chat_system.adicionar_edital(
        edital_id="trt_2025",
        texto=texto_exemplo,
        metadados={'orgao': 'TRT', 'ano': 2025}
    )
    
    if success:
        print("✅ Edital adicionado\n")
        
        # Fazer perguntas
        perguntas = [
            "Quais são os cargos disponíveis?",
            "Qual o salário do Analista?",
            "Quando são as inscrições?"
        ]
        
        for pergunta in perguntas:
            print(f"❓ {pergunta}")
            resultado = chat_system.chat(
                session_id="teste_001",
                edital_id="trt_2025",
                pergunta=pergunta
            )
            
            if resultado['success']:
                print(f"💬 {resultado['resposta']}")
                print(f"📄 Páginas: {resultado['paginas_referenciadas']}\n")
            else:
                print(f"❌ Erro: {resultado['error']}\n")
