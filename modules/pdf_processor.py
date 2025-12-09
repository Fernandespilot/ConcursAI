"""
📄 PROCESSADOR DE PDFs COM LANGCHAIN E OLLAMA
===========================================
Sistema completo para upload, processamento e análise de PDFs de editais
"""

import os
import tempfile
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

# LangChain imports - versões atualizadas
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, Ollama
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.callbacks.manager import CallbackManagerForLLMRun

# PDF processing
import fitz  # PyMuPDF
import pypdf

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Processador de PDFs com múltiplas estratégias de extração"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def extract_text_from_pdf(self, pdf_path: str, method: str = "auto") -> str:
        """
        Extrai texto de PDF usando diferentes métodos
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            method: Método de extração ('pypdf', 'pymupdf', 'langchain', 'auto')
            
        Returns:
            Texto extraído do PDF
        """
        
        if method == "auto":
            # Tentar diferentes métodos até conseguir extrair texto
            methods = ["pymupdf", "pypdf", "langchain"]
            
            for m in methods:
                try:
                    text = self.extract_text_from_pdf(pdf_path, m)
                    if text and len(text.strip()) > 100:  # Verificar se extraiu texto significativo
                        logger.info(f"✅ Extração bem-sucedida com método: {m}")
                        return text
                except Exception as e:
                    logger.warning(f"⚠️ Método {m} falhou: {e}")
                    continue
            
            raise Exception("Nenhum método de extração de PDF funcionou")
        
        elif method == "pymupdf":
            return self._extract_with_pymupdf(pdf_path)
            
        elif method == "pypdf":
            return self._extract_with_pypdf(pdf_path)
            
        elif method == "langchain":
            return self._extract_with_langchain(pdf_path)
            
        else:
            raise ValueError(f"Método não suportado: {method}")
    
    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extrai texto usando PyMuPDF (mais robusto)"""
        
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            text += f"\n--- PÁGINA {page_num + 1} ---\n{page_text}"
        
        doc.close()
        return text.strip()
    
    def _extract_with_pypdf(self, pdf_path: str) -> str:
        """Extrai texto usando PyPDF"""
        
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            text = ""
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += f"\n--- PÁGINA {page_num + 1} ---\n{page_text}"
        
        return text.strip()
    
    def _extract_with_langchain(self, pdf_path: str) -> str:
        """Extrai texto usando LangChain PyPDFLoader"""
        
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        text = ""
        for i, doc in enumerate(documents):
            text += f"\n--- PÁGINA {i + 1} ---\n{doc.page_content}"
        
        return text.strip()
    
    def get_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extrai metadados do PDF"""
        
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            # Informações básicas
            info = {
                'titulo': metadata.get('title', ''),
                'autor': metadata.get('author', ''),
                'criador': metadata.get('creator', ''),
                'produtor': metadata.get('producer', ''),
                'data_criacao': metadata.get('creationDate', ''),
                'data_modificacao': metadata.get('modDate', ''),
                'paginas': len(doc),
                'tamanho_arquivo': os.path.getsize(pdf_path)
            }
            
            doc.close()
            return info
            
        except Exception as e:
            logger.error(f"Erro ao extrair metadados: {e}")
            return {'erro': str(e)}

class LangChainPDFAnalyzer:
    """Analisador de PDFs usando LangChain e Ollama"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        self.pdf_processor = PDFProcessor()
        
        # Configurar LangChain com Ollama - versões atualizadas
        try:
            self.llm = Ollama(
                base_url=ollama_url,
                model=model,
                temperature=0.3
            )
        except Exception as e:
            logger.warning(f"Erro ao configurar Ollama LLM: {e}")
            self.llm = None
        
        # Configurar embeddings - versão atualizada
        try:
            self.embeddings = OllamaEmbeddings(
                base_url=ollama_url,
                model=model
            )
        except Exception as e:
            logger.warning(f"Erro ao configurar Ollama embeddings: {e}")
            # Fallback para embeddings locais se Ollama não estiver disponível
            try:
                from sentence_transformers import SentenceTransformer
                from langchain_community.embeddings import HuggingFaceEmbeddings
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                logger.info("Usando embeddings HuggingFace como fallback")
            except ImportError:
                logger.error("Nem Ollama nem HuggingFace embeddings disponíveis")
                self.embeddings = None
        
        # Text splitter para chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Armazenar documentos processados
        self.document_store = {}
        
    def process_pdf(self, pdf_file_path: str, document_id: str, metadata: Dict = None) -> Dict:
        """
        Processa um PDF completo: extração, chunking e indexação
        
        Args:
            pdf_file_path: Caminho para o arquivo PDF
            document_id: ID único para o documento
            metadata: Metadados adicionais
            
        Returns:
            Resultado do processamento
        """
        
        try:
            logger.info(f"🔄 Processando PDF: {document_id}")
            
            # 1. Extrair texto do PDF
            text = self.pdf_processor.extract_text_from_pdf(pdf_file_path)
            
            # 2. Extrair metadados
            pdf_metadata = self.pdf_processor.get_pdf_metadata(pdf_file_path)
            
            # 3. Combinar metadados
            full_metadata = {
                **pdf_metadata,
                **(metadata or {}),
                'document_id': document_id,
                'processed_at': datetime.now().isoformat(),
                'total_characters': len(text)
            }
            
            # 4. Fazer chunking do texto
            documents = self.text_splitter.create_documents(
                [text],
                metadatas=[full_metadata]
            )
            
            logger.info(f"📄 Criados {len(documents)} chunks do documento")
            
            # 5. Criar vector store - com verificação de embeddings
            if self.embeddings is not None:
                vectorstore = FAISS.from_documents(documents, self.embeddings)
                logger.info(f"✅ Vector store criado com {len(documents)} chunks")
            else:
                logger.warning("⚠️ Embeddings não disponíveis - usando armazenamento simples")
                vectorstore = None
            
            # 6. Armazenar no document store
            self.document_store[document_id] = {
                'vectorstore': vectorstore,
                'documents': documents,
                'metadata': full_metadata,
                'text': text,
                'processed_at': datetime.now().isoformat()
            }
            
            # 7. Análise inicial automática
            initial_analysis = self._perform_initial_analysis(text, full_metadata)
            
            result = {
                'success': True,
                'document_id': document_id,
                'chunks_created': len(documents),
                'total_characters': len(text),
                'metadata': full_metadata,
                'initial_analysis': initial_analysis,
                'processing_time': datetime.now().isoformat()
            }
            
            logger.info(f"✅ PDF processado com sucesso: {document_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar PDF {document_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }
    
    def _perform_initial_analysis(self, text: str, metadata: Dict) -> Dict:
        """Realiza análise inicial automática do documento"""
        
        try:
            # Prompt para análise inicial
            analysis_prompt = f"""
            Analise o seguinte edital de concurso público e extraia as informações principais:

            DOCUMENTO: {metadata.get('titulo', 'Documento sem título')}

            TEXTO DO EDITAL:
            {text[:3000]}...

            Por favor, extraia e organize as seguintes informações:

            1. INFORMAÇÕES GERAIS:
            - Órgão/Instituição
            - Tipo de concurso
            - Número de vagas
            - Cargos disponíveis

            2. CRONOGRAMA:
            - Data de publicação
            - Período de inscrições
            - Data das provas
            - Outras datas importantes

            3. REQUISITOS:
            - Escolaridade mínima
            - Requisitos específicos
            - Idade limite

            4. REMUNERAÇÃO:
            - Salário base
            - Benefícios
            - Jornada de trabalho

            5. PROCESSO SELETIVO:
            - Fases do concurso
            - Tipos de prova
            - Pontuação mínima

            Responda em formato JSON estruturado.
            """
            
            # Gerar análise usando Ollama
            if self.llm is not None:
                analysis_response = self.llm(analysis_prompt)
                
                # Tentar parsear como JSON, senão retornar como texto
                try:
                    analysis_json = json.loads(analysis_response)
                    return analysis_json
                except:
                    return {
                        'analysis_text': analysis_response,
                        'note': 'Análise retornada como texto livre'
                    }
            else:
                # Fallback: análise simples sem IA
                return {
                    'analysis_text': f"Documento processado: {metadata.get('titulo', 'Sem título')}",
                    'note': 'Análise básica - IA não disponível',
                    'basic_info': {
                        'title': metadata.get('titulo', ''),
                        'organization': metadata.get('orgao', ''),
                        'characters': len(text),
                        'processed_at': datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Erro na análise inicial: {e}")
            return {
                'error': f"Erro na análise: {e}",
                'status': 'failed'
            }
    
    def query_document(self, document_id: str, question: str, top_k: int = 5) -> Dict:
        """
        Faz pergunta sobre um documento específico
        
        Args:
            document_id: ID do documento
            question: Pergunta do usuário
            top_k: Número de chunks relevantes a considerar
            
        Returns:
            Resposta da IA com contexto
        """
        
        if document_id not in self.document_store:
            return {
                'success': False,
                'error': f'Documento {document_id} não encontrado'
            }
        
        # Verificar se LLM está disponível
        if self.llm is None:
            return {
                'success': False,
                'error': 'Sistema de IA não está disponível'
            }
        
        try:
            doc_data = self.document_store[document_id]
            vectorstore = doc_data['vectorstore']
            
            # Verificar se vectorstore está disponível
            if vectorstore is None:
                # Fallback: busca textual simples
                return self._simple_text_search(document_id, question, top_k)
            
            # Criar chain de pergunta-resposta
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": top_k}),
                return_source_documents=True
            )
            
            # Fazer a pergunta
            result = qa_chain({"query": question})
            
            # Processar resposta
            answer = result.get('result', '')
            source_docs = result.get('source_documents', [])
            
            sources = []
            for doc in source_docs:
                sources.append({
                    'content': doc.page_content[:200] + "...",
                    'metadata': doc.metadata
                })
            
            return {
                'success': True,
                'question': question,
                'answer': answer,
                'sources': sources,
                'document_id': document_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao consultar documento {document_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'question': question,
                'document_id': document_id
            }
    
    def _simple_text_search(self, document_id: str, question: str, top_k: int = 5) -> Dict:
        """Busca textual simples quando vector store não está disponível"""
        
        try:
            doc_data = self.document_store[document_id]
            text = doc_data['text']
            
            # Busca simples por palavras-chave
            question_words = question.lower().split()
            text_lower = text.lower()
            
            # Encontrar seções relevantes
            relevant_chunks = []
            chunks = text.split('\n\n')  # Dividir por parágrafos
            
            for chunk in chunks:
                chunk_lower = chunk.lower()
                relevance_score = sum(1 for word in question_words if word in chunk_lower)
                
                if relevance_score > 0:
                    relevant_chunks.append({
                        'content': chunk,
                        'score': relevance_score
                    })
            
            # Ordenar por relevância
            relevant_chunks.sort(key=lambda x: x['score'], reverse=True)
            top_chunks = relevant_chunks[:top_k]
            
            # Combinar chunks para resposta
            context = '\n\n'.join([chunk['content'] for chunk in top_chunks])
            
            # Resposta simples baseada no contexto encontrado
            if context:
                answer = f"Baseado no documento, encontrei as seguintes informações relevantes:\n\n{context}"
            else:
                answer = "Não encontrei informações específicas sobre sua pergunta no documento."
            
            sources = [{'content': chunk['content'][:200] + "...", 'metadata': {}} for chunk in top_chunks]
            
            return {
                'success': True,
                'question': question,
                'answer': answer,
                'sources': sources,
                'document_id': document_id,
                'timestamp': datetime.now().isoformat(),
                'method': 'simple_text_search'
            }
            
        except Exception as e:
            logger.error(f"Erro na busca textual simples: {e}")
            return {
                'success': False,
                'error': str(e),
                'question': question,
                'document_id': document_id
            }
    
    def list_documents(self) -> List[Dict]:
        """Lista todos os documentos processados"""
        
        documents = []
        for doc_id, doc_data in self.document_store.items():
            documents.append({
                'document_id': doc_id,
                'metadata': doc_data['metadata'],
                'chunks_count': len(doc_data['documents']),
                'processed_at': doc_data['processed_at'],
                'character_count': len(doc_data['text'])
            })
        
        return documents
    
    def get_document_summary(self, document_id: str) -> Dict:
        """Obtém resumo de um documento"""
        
        if document_id not in self.document_store:
            return {'error': 'Documento não encontrado'}
        
        doc_data = self.document_store[document_id]
        
        # Gerar resumo usando IA
        summary_prompt = f"""
        Faça um resumo executivo do seguinte edital de concurso:

        {doc_data['text'][:2000]}...

        O resumo deve conter:
        - Órgão e cargo principal
        - Número de vagas
        - Principais requisitos
        - Datas importantes
        - Informações sobre remuneração

        Mantenha o resumo conciso e objetivo.
        """
        
        try:
            if self.llm is not None:
                summary = self.llm(summary_prompt)
            else:
                # Fallback: resumo simples baseado no texto
                summary = self._generate_simple_summary(doc_data['text'])
            
            return {
                'document_id': document_id,
                'summary': summary,
                'metadata': doc_data['metadata'],
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f'Erro ao gerar resumo: {e}',
                'document_id': document_id
            }
    
    def _generate_simple_summary(self, text: str) -> str:
        """Gera resumo simples sem IA"""
        
        # Extrair primeiros parágrafos
        paragraphs = text.split('\n\n')[:5]
        
        summary_parts = []
        summary_parts.append("RESUMO AUTOMÁTICO:")
        summary_parts.append("=" * 30)
        
        for i, para in enumerate(paragraphs, 1):
            if len(para.strip()) > 50:  # Apenas parágrafos significativos
                summary_parts.append(f"{i}. {para.strip()[:200]}...")
        
        return '\n\n'.join(summary_parts)
    
    def cleanup(self):
        """Limpa recursos temporários"""
        try:
            import shutil
            shutil.rmtree(self.pdf_processor.temp_dir)
        except:
            pass

# Instância global do analisador
pdf_analyzer = None

def get_pdf_analyzer() -> LangChainPDFAnalyzer:
    """Obtém instância global do analisador de PDFs"""
    global pdf_analyzer
    
    if pdf_analyzer is None:
        pdf_analyzer = LangChainPDFAnalyzer()
    
    return pdf_analyzer

def test_pdf_processing():
    """Função de teste para o processamento de PDFs"""
    
    print("🧪 TESTE DO SISTEMA DE PROCESSAMENTO DE PDFs")
    print("=" * 50)
    
    analyzer = get_pdf_analyzer()
    
    # Teste básico de funcionamento
    print("✅ Analisador inicializado")
    print(f"🤖 Modelo: {analyzer.model}")
    print(f"🔗 URL Ollama: {analyzer.ollama_url}")
    
    # Listar documentos (deve estar vazio inicialmente)
    docs = analyzer.list_documents()
    print(f"📄 Documentos carregados: {len(docs)}")
    
    return analyzer

if __name__ == "__main__":
    test_pdf_processing()
