"""
API Principal do ConcursAI - Versão Refatorada
Aplicação FastAPI com arquitetura modular e segurança implementada
"""

import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager

# Imports locais
from app.config import get_settings
from app.core.auth import (
    create_access_token, 
    verify_token, 
    get_current_user,
    hash_password,
    verify_password,
    UserCreate,
    UserLogin,
    UserResponse,
    Token
)
from app.core.cache import cache_manager, cached, get_cache_stats, clear_cache
from app.core.rate_limiting import (
    rate_limiting_middleware, 
    rate_limit, 
    get_rate_limit_stats,
    unblock_ip,
    block_ip
)

# Imports dos módulos existentes (mantendo compatibilidade)
try:
    # Adicionar path dos módulos
    import sys
    from modules.concurso_rag import ConcursoRAG
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Módulos de RAG não disponíveis: {e}")
    from app.modules_stubs import ConcursoRAGStub as ConcursoRAG
    MODULES_AVAILABLE = False

# Imports do sistema de PDFs
try:
    from modules.pdf_api import setup_pdf_routes
    from modules.pdf_processor import get_pdf_analyzer
    PDF_SYSTEM_AVAILABLE = True
    print("✅ Sistema PDF carregado com sucesso")
except ImportError as e:
    print(f"⚠️ Sistema PDF não disponível: {e}")
    PDF_SYSTEM_AVAILABLE = False
    from pathlib import Path
    modules_path = Path(__file__).parent.parent / "modules"
    if modules_path.exists():
        sys.path.insert(0, str(modules_path.parent))
    
    from modules.concurso_rag import ConcursoRAG
    from modules.monitoring import MonitoringSystem  
    from modules.dashboard import get_dashboard_data
    from modules.agendador import start_scheduler
    MODULES_AVAILABLE = True
    print("✅ Módulos legados importados com sucesso")
except ImportError as e:
    print(f"⚠️ Módulos legados não disponíveis: {e} - usando stubs")
    # Usar stubs para compatibilidade
    from app.modules_stubs import (
        ConcursoRAGStub as ConcursoRAG,
        MonitoringSystemStub as MonitoringSystem,
        get_dashboard_data_stub as get_dashboard_data,
        start_scheduler_stub as start_scheduler
    )
    MODULES_AVAILABLE = False

# Configuração
settings = get_settings()

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.log_file) if settings.log_file else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# Instâncias globais
rag_system = None
monitoring = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    logger.info("Iniciando ConcursAI API...")
    
    global rag_system, monitoring
    
    try:
        # Inicializar sistemas apenas se módulos estão disponíveis
        if MODULES_AVAILABLE:
            # Inicializar RAG
            rag_system = ConcursoRAG()
            await rag_system.initialize()
            logger.info("Sistema RAG inicializado")
            
            # Inicializar monitoring
            monitoring = MonitoringSystem()
            await monitoring.start()
            logger.info("Sistema de monitoramento inicializado")
            
            # Inicializar agendador
            if settings.enable_scheduler:
                await start_scheduler()
                logger.info("Agendador inicializado")
        
        # Configurar sistema PDF se disponível
        if PDF_SYSTEM_AVAILABLE:
            setup_pdf_routes(app)
            logger.info("✅ Sistema PDF configurado")
        
        logger.info("✅ ConcursAI API iniciada com sucesso!")
        yield
        
    except Exception as e:
        logger.error(f"Erro na inicialização: {e}")
        yield
    finally:
        # Cleanup
        if monitoring:
            await monitoring.stop()
        logger.info("ConcursAI API finalizada")

# Criar aplicação
app = FastAPI(
    title="ConcursAI API",
    description="API para busca e análise de concursos públicos com IA",
    version="2.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Middleware de segurança
security = HTTPBearer()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted Host
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.herokuapp.com"]
    )

# Rate Limiting Middleware
app.middleware("http")(rate_limiting_middleware)

# ==========================================
# ENDPOINTS DE AUTENTICAÇÃO
# ==========================================

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Registrar novo usuário"""
    try:
        # Verificar se usuário já existe (simples verificação em memória)
        # Em produção, usar banco de dados real
        
        # Hash da senha
        hashed_password = hash_password(user_data.password)
        
        # Criar token
        token = create_access_token({"sub": user_data.username})
        
        return UserResponse(
            id=1,  # Em produção, usar ID do banco
            username=user_data.username,
            email=user_data.email,
            is_active=True,
            created_at=datetime.now(),
            token=token
        )
        
    except Exception as e:
        logger.error(f"Erro no registro: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao registrar usuário"
        )

@app.post("/api/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login de usuário"""
    try:
        # Em produção, verificar credenciais no banco
        # Por agora, aceitar qualquer credencial válida
        
        if len(credentials.username) < 3 or len(credentials.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        token = create_access_token({"sub": credentials.username})
        
        return Token(
            access_token=token,
            token_type="bearer",
            expires_in=settings.jwt_expiration_hours * 3600
        )
        
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obter informações do usuário atual"""
    return UserResponse(
        id=1,
        username=current_user["sub"],
        email=f"{current_user['sub']}@example.com",
        is_active=True,
        created_at=datetime.now()
    )

# ==========================================
# ENDPOINTS PRINCIPAIS (PROTEGIDOS)
# ==========================================

@app.get("/api/health")
@rate_limit(requests_per_minute=30)
async def health_check(request: Request):
    """Health check da API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "modules_available": MODULES_AVAILABLE
    }

@app.get("/api/concursos/search")
@rate_limit(requests_per_minute=20, burst_capacity=10)
@cached(prefix="concursos_search", ttl=1800)  # Cache por 30 minutos
async def search_concursos(
    request: Request,
    query: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Buscar concursos com IA"""
    try:
        if not MODULES_AVAILABLE or not rag_system:
            raise HTTPException(
                status_code=503,
                detail="Sistema RAG não disponível"
            )
        
        # Buscar concursos
        results = await rag_system.search(query, limit=limit)
        
        return {
            "query": query,
            "results": results,
            "total": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno na busca"
        )

@app.post("/api/concursos/analyze")
@rate_limit(requests_per_minute=10, burst_capacity=5)
async def analyze_edital(
    request: Request,
    edital_url: str,
    current_user: dict = Depends(get_current_user)
):
    """Analisar edital com IA"""
    try:
        if not MODULES_AVAILABLE or not rag_system:
            raise HTTPException(
                status_code=503,
                detail="Sistema de análise não disponível"
            )
        
        # Analisar edital
        analysis = await rag_system.analyze_edital(edital_url)
        
        return {
            "url": edital_url,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno na análise"
        )

@app.get("/api/dashboard/data")
@rate_limit(requests_per_minute=15)
@cached(prefix="dashboard", ttl=300)  # Cache por 5 minutos
async def get_dashboard_info(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Obter dados do dashboard"""
    try:
        if not MODULES_AVAILABLE:
            return {
                "message": "Dashboard em modo limitado",
                "modules_available": False
            }
        
        data = await get_dashboard_data()
        return data
        
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno no dashboard"
        )

# ==========================================
# ENDPOINTS ADMINISTRATIVOS
# ==========================================

@app.get("/api/admin/stats")
@rate_limit(requests_per_minute=5)
async def get_system_stats(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Obter estatísticas do sistema (requer autenticação)"""
    try:
        stats = {
            "cache": await get_cache_stats(),
            "rate_limiting": await get_rate_limit_stats(),
            "system": {
                "modules_available": MODULES_AVAILABLE,
                "debug_mode": settings.debug,
                "version": "2.0.0"
            }
        }
        
        if monitoring:
            stats["monitoring"] = await monitoring.get_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Erro nas estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno nas estatísticas"
        )

@app.post("/api/admin/cache/clear")
async def clear_system_cache(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Limpar cache do sistema"""
    try:
        success = await clear_cache()
        return {
            "success": success,
            "message": "Cache limpo com sucesso" if success else "Erro ao limpar cache"
        }
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao limpar cache"
        )

@app.post("/api/admin/ip/block")
async def block_ip_address(
    request: Request,
    ip_address: str,
    duration_minutes: int = 15,
    current_user: dict = Depends(get_current_user)
):
    """Bloquear endereço IP"""
    try:
        success = await block_ip(f"ip:{ip_address}", duration_minutes)
        return {
            "success": success,
            "message": f"IP {ip_address} bloqueado por {duration_minutes} minutos"
        }
    except Exception as e:
        logger.error(f"Erro ao bloquear IP: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao bloquear IP"
        )

@app.post("/api/admin/ip/unblock")
async def unblock_ip_address(
    request: Request,
    ip_address: str,
    current_user: dict = Depends(get_current_user)
):
    """Desbloquear endereço IP"""
    try:
        success = await unblock_ip(f"ip:{ip_address}")
        return {
            "success": success,
            "message": f"IP {ip_address} desbloqueado"
        }
    except Exception as e:
        logger.error(f"Erro ao desbloquear IP: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao desbloquear IP"
        )

# ==========================================
# HANDLERS DE ERRO
# ==========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para exceções HTTP"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções gerais"""
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Erro interno do servidor",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

# ==========================================
# ENDPOINT ROOT
# ==========================================

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "ConcursAI API v2.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "version": "2.0.0",
        "features": {
            "rag_system": MODULES_AVAILABLE,
            "pdf_system": PDF_SYSTEM_AVAILABLE,
            "auth": True,
            "cache": True,
            "rate_limiting": True
        },
        "pdf_interface": "http://localhost:8502" if PDF_SYSTEM_AVAILABLE else None,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
