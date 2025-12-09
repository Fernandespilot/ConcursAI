"""
🚀 API ENDPOINTS PARA UPLOAD E ANÁLISE DE PDFs
==============================================
Endpoints REST para integração com sistema de PDFs + LangChain + Ollama
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import tempfile
import os
import logging
from datetime import datetime

# Importar módulos do sistema
try:
    from modules.pdf_processor import get_pdf_analyzer
    from app.core.auth import get_current_user
    from app.core.rate_limiting import rate_limit
    from app.core.cache import cached
except ImportError as e:
    logging.error(f"Erro ao importar módulos: {e}")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos Pydantic
class ChatRequest(BaseModel):
    """Modelo para requisição de chat"""
    document_id: str = Field(..., description="ID do documento")
    question: str = Field(..., description="Pergunta do usuário")
    top_k: int = Field(default=5, description="Número de chunks relevantes")

class ChatResponse(BaseModel):
    """Modelo para resposta de chat"""
    success: bool
    question: str
    answer: str
    sources: List[Dict]
    document_id: str
    timestamp: str

class DocumentUploadResponse(BaseModel):
    """Modelo para resposta de upload"""
    success: bool
    document_id: str
    chunks_created: int
    total_characters: int
    metadata: Dict
    initial_analysis: Optional[Dict]
    processing_time: str

class DocumentListResponse(BaseModel):
    """Modelo para lista de documentos"""
    documents: List[Dict]
    total: int

class DocumentSummaryResponse(BaseModel):
    """Modelo para resumo de documento"""
    document_id: str
    summary: str
    metadata: Dict
    generated_at: str

def create_pdf_routes(app: FastAPI):
    """Adiciona rotas de PDF à aplicação FastAPI"""
    
    @app.post("/api/pdf/upload", response_model=DocumentUploadResponse)
    @rate_limit(requests_per_minute=10, burst_capacity=5)
    async def upload_pdf(
        file: UploadFile = File(..., description="Arquivo PDF do edital"),
        titulo: Optional[str] = Form(None, description="Título do concurso"),
        orgao: Optional[str] = Form(None, description="Órgão/Instituição"),
        estado: Optional[str] = Form(None, description="Estado/UF"),
        cargo: Optional[str] = Form(None, description="Cargo principal"),
        current_user: dict = Depends(get_current_user)
    ):
        """
        Upload e processamento de PDF de edital
        
        Args:
            file: Arquivo PDF
            titulo: Título do concurso (opcional)
            orgao: Órgão/Instituição (opcional)
            estado: Estado/UF (opcional)
            cargo: Cargo principal (opcional)
            
        Returns:
            Resultado do processamento
        """
        
        # Validar arquivo
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Apenas arquivos PDF são aceitos"
            )
        
        if file.size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=400,
                detail="Arquivo muito grande. Máximo 50MB"
            )
        
        try:
            logger.info(f"📤 Upload de PDF iniciado: {file.filename}")
            
            # Salvar arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            # Gerar ID único
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename.replace('.pdf', '')}"
            
            # Metadados
            metadata = {
                'titulo': titulo,
                'orgao': orgao,
                'estado': estado,
                'cargo': cargo,
                'filename': file.filename,
                'uploaded_by': current_user.get('user_id', 'anonymous'),
                'upload_timestamp': datetime.now().isoformat()
            }
            
            # Processar PDF
            analyzer = get_pdf_analyzer()
            result = analyzer.process_pdf(tmp_path, doc_id, metadata)
            
            # Limpar arquivo temporário
            os.unlink(tmp_path)
            
            if result['success']:
                logger.info(f"✅ PDF processado com sucesso: {doc_id}")
                return DocumentUploadResponse(**result)
            else:
                logger.error(f"❌ Erro no processamento: {result['error']}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro no processamento: {result['error']}"
                )
                
        except Exception as e:
            logger.error(f"❌ Erro no upload de PDF: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno: {str(e)}"
            )
    
    @app.get("/api/pdf/documents", response_model=DocumentListResponse)
    @rate_limit(requests_per_minute=30, burst_capacity=15)
    @cached(prefix="pdf_documents", ttl=300)  # Cache por 5 minutos
    async def list_documents(
        current_user: dict = Depends(get_current_user)
    ):
        """
        Lista todos os documentos PDF processados
        
        Returns:
            Lista de documentos com metadados
        """
        
        try:
            analyzer = get_pdf_analyzer()
            documents = analyzer.list_documents()
            
            return DocumentListResponse(
                documents=documents,
                total=len(documents)
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar documentos: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno: {str(e)}"
            )
    
    @app.post("/api/pdf/chat", response_model=ChatResponse)
    @rate_limit(requests_per_minute=20, burst_capacity=10)
    async def chat_with_document(
        request: ChatRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Conversa com um documento PDF usando IA
        
        Args:
            request: Dados da pergunta e documento
            
        Returns:
            Resposta da IA com contexto
        """
        
        try:
            analyzer = get_pdf_analyzer()
            
            # Verificar se documento existe
            docs = analyzer.list_documents()
            doc_exists = any(doc['document_id'] == request.document_id for doc in docs)
            
            if not doc_exists:
                raise HTTPException(
                    status_code=404,
                    detail=f"Documento {request.document_id} não encontrado"
                )
            
            # Processar pergunta
            result = analyzer.query_document(
                request.document_id,
                request.question,
                request.top_k
            )
            
            if result['success']:
                return ChatResponse(**result)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=result['error']
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Erro no chat: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno: {str(e)}"
            )
    
    @app.get("/api/pdf/document/{document_id}/summary", response_model=DocumentSummaryResponse)
    @rate_limit(requests_per_minute=15, burst_capacity=8)
    @cached(prefix="pdf_summary", ttl=1800)  # Cache por 30 minutos
    async def get_document_summary(
        document_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Obtém resumo de um documento específico
        
        Args:
            document_id: ID do documento
            
        Returns:
            Resumo gerado pela IA
        """
        
        try:
            analyzer = get_pdf_analyzer()
            summary = analyzer.get_document_summary(document_id)
            
            if 'error' in summary:
                raise HTTPException(
                    status_code=404,
                    detail=summary['error']
                )
            
            return DocumentSummaryResponse(**summary)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resumo: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno: {str(e)}"
            )
    
    @app.delete("/api/pdf/document/{document_id}")
    @rate_limit(requests_per_minute=10, burst_capacity=5)
    async def delete_document(
        document_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Remove um documento do sistema
        
        Args:
            document_id: ID do documento a ser removido
            
        Returns:
            Confirmação da remoção
        """
        
        try:
            analyzer = get_pdf_analyzer()
            
            if document_id not in analyzer.document_store:
                raise HTTPException(
                    status_code=404,
                    detail=f"Documento {document_id} não encontrado"
                )
            
            # Remover documento
            del analyzer.document_store[document_id]
            
            logger.info(f"🗑️ Documento removido: {document_id}")
            
            return {
                "success": True,
                "message": f"Documento {document_id} removido com sucesso",
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao remover documento: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno: {str(e)}"
            )
    
    @app.get("/api/pdf/status")
    @rate_limit(requests_per_minute=60, burst_capacity=30)
    async def get_pdf_system_status():
        """
        Obtém status do sistema de PDFs
        
        Returns:
            Status dos componentes do sistema
        """
        
        try:
            analyzer = get_pdf_analyzer()
            docs = analyzer.list_documents()
            
            # Verificar conectividade com Ollama
            ollama_status = "offline"
            try:
                import requests
                response = requests.get(f"{analyzer.ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    ollama_status = "online"
            except:
                pass
            
            status = {
                "pdf_processor": "online",
                "ollama_status": ollama_status,
                "langchain": "online",
                "documents_loaded": len(docs),
                "model": analyzer.model,
                "system_ready": ollama_status == "online",
                "timestamp": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {e}")
            return {
                "pdf_processor": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Função para integrar com app principal
def setup_pdf_routes(app: FastAPI):
    """Configura todas as rotas de PDF na aplicação"""
    create_pdf_routes(app)
    logger.info("✅ Rotas de PDF configuradas")
