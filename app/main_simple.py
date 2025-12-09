"""
API Principal ConcursAI v2.0 - Versão Simplificada
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Optional

# Adicionar paths
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

# Imports locais simplificados
try:
    from app.config import get_settings
    settings = get_settings()
except:
    # Fallback se config não funcionar
    class SimpleSettings:
        debug = True
        allowed_origins = ["*"]
        log_level = "INFO"
    settings = SimpleSettings()

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar app
app = FastAPI(
    title="ConcursAI API v2.0",
    description="API para busca de concursos com IA",
    version="2.0.0"
)

# CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Dados simulados para teste
fake_users = {
    "admin": {"password": "admin123", "id": 1},
    "user": {"password": "user123", "id": 2}
}

def get_current_user(token: Optional[str] = Depends(security)):
    """Autenticação simplificada para teste"""
    if not token:
        return {"sub": "anonymous", "id": 0}
    return {"sub": "authenticated", "id": 1}

# ==========================================
# ENDPOINTS BÁSICOS
# ==========================================

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "ConcursAI API v2.0 - Funcionando!",
        "status": "online",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "ok",
            "database": "ok",
            "cache": "ok"
        }
    }

@app.post("/api/auth/login")
async def login(request: Request):
    """Login simplificado"""
    try:
        body = await request.json()
        username = body.get("username", "")
        password = body.get("password", "")
        
        if username in fake_users and fake_users[username]["password"] == password:
            return {
                "access_token": f"fake-token-{username}",
                "token_type": "bearer",
                "user": {
                    "id": fake_users[username]["id"],
                    "username": username
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
            
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(status_code=400, detail="Erro no login")

@app.get("/api/concursos/search")
async def search_concursos(
    query: str = "programador",
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Busca de concursos simulada"""
    
    # Dados simulados
    fake_results = [
        {
            "id": 1,
            "titulo": f"Concurso para {query.title()}",
            "orgao": "Prefeitura Municipal",
            "cargo": f"{query.title()} - Nível Superior",
            "salario": "R$ 5.000,00",
            "vagas": 10,
            "inscricoes_ate": "2025-12-31",
            "prova": "2026-02-15",
            "status": "Aberto",
            "relevancia": 0.95
        },
        {
            "id": 2,
            "titulo": f"Processo Seletivo {query.title()}",
            "orgao": "Governo do Estado",
            "cargo": f"Analista de Sistemas - {query.title()}",
            "salario": "R$ 7.500,00",
            "vagas": 5,
            "inscricoes_ate": "2025-11-30",
            "prova": "2026-01-20",
            "status": "Aberto",
            "relevancia": 0.87
        }
    ]
    
    return {
        "query": query,
        "results": fake_results[:limit],
        "total": len(fake_results),
        "timestamp": datetime.now().isoformat(),
        "user": current_user.get("sub", "anonymous")
    }

@app.get("/api/dashboard/data")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """Dashboard com dados simulados"""
    return {
        "estatisticas": {
            "total_concursos": 1250,
            "concursos_abertos": 85,
            "concursos_novos_semana": 12,
            "editais_analisados": 450
        },
        "concursos_recentes": [
            {
                "titulo": "Concurso TRF 3ª Região",
                "data": "2025-10-10",
                "vagas": 15
            },
            {
                "titulo": "Prefeitura de São Paulo",
                "data": "2025-10-08",
                "vagas": 50
            }
        ],
        "user": current_user.get("sub", "anonymous"),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/concursos/analyze")
async def analyze_edital(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Análise de edital simulada"""
    try:
        body = await request.json()
        url = body.get("url", "")
        
        return {
            "url": url,
            "analise": {
                "resumo": "Concurso para área de TI com 10 vagas",
                "requisitos": [
                    "Curso superior em área correlata",
                    "Experiência de 2 anos",
                    "Conhecimento em Python/FastAPI"
                ],
                "salario": "R$ 6.500,00",
                "data_prova": "2026-03-15",
                "pontos_importantes": [
                    "Prova objetiva e discursiva",
                    "Análise de títulos",
                    "Período de experiência de 3 anos"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        raise HTTPException(status_code=400, detail="Erro na análise do edital")

@app.get("/api/admin/stats")
async def get_system_stats(current_user: dict = Depends(get_current_user)):
    """Estatísticas do sistema"""
    return {
        "sistema": {
            "version": "2.0.0",
            "uptime": "5 minutes",
            "requests_today": 42,
            "users_online": 3
        },
        "performance": {
            "response_time_avg": "150ms",
            "memory_usage": "45%",
            "cpu_usage": "12%"
        },
        "user": current_user.get("sub", "anonymous"),
        "timestamp": datetime.now().isoformat()
    }

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Erro interno do servidor",
            "timestamp": datetime.now().isoformat()
        }
    )

# ==========================================
# STARTUP
# ==========================================

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 ConcursAI API v2.0 iniciada!")
    logger.info("📊 Modo de demonstração ativo")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 ConcursAI API v2.0 finalizada")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
