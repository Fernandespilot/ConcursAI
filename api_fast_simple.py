"""
ConcursAI API v2.0 - Versão Ultra Simplificada
Funciona sem dependências externas complexas
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

# Criar app
app = FastAPI(
    title="ConcursAI API v2.0",
    description="API para busca de concursos - Versão Simplificada",
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

# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/")
async def root():
    return {
        "message": "🎉 ConcursAI API v2.0 - FUNCIONANDO!",
        "status": "online",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/api/health",
            "search": "/api/concursos/search",
            "dashboard": "/api/dashboard/data"
        }
    }

@app.get("/api/health")
async def health():
    return {
        "status": "✅ HEALTHY",
        "version": "2.0.0",
        "uptime": "OK",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/concursos/search")
async def search_concursos(query: str = "programador", limit: int = 10):
    """Busca concursos - dados simulados"""
    results = [
        {
            "id": i,
            "titulo": f"Concurso {query.title()} #{i}",
            "orgao": f"Órgão Público {i}",
            "cargo": f"{query.title()} - Nível Superior",
            "salario": f"R$ {5000 + i*500:,.2f}",
            "vagas": 5 + i,
            "status": "Aberto" if i % 2 == 0 else "Previsto",
            "inscricoes": "2025-11-30",
            "relevancia": round(0.9 - i*0.1, 2)
        }
        for i in range(1, min(limit + 1, 6))
    ]
    
    return {
        "query": query,
        "results": results,
        "total": len(results),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/auth/login")
async def login(credentials: dict):
    """Login simplificado"""
    username = credentials.get("username", "")
    password = credentials.get("password", "")
    
    # Validação simples
    if len(username) >= 3 and len(password) >= 3:
        return {
            "access_token": f"token_{username}_{datetime.now().timestamp()}",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "username": username,
                "message": "Login realizado com sucesso!"
            }
        }
    else:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

@app.get("/api/dashboard/data")
async def dashboard():
    """Dashboard com estatísticas simuladas"""
    return {
        "estatisticas": {
            "total_concursos": 1250,
            "concursos_abertos": 85,
            "novos_esta_semana": 12,
            "editais_analisados": 450
        },
        "concursos_em_destaque": [
            {
                "titulo": "TRF 3ª Região",
                "vagas": 15,
                "salario": "R$ 12.000,00",
                "inscricoes_ate": "2025-12-15"
            },
            {
                "titulo": "Prefeitura São Paulo",
                "vagas": 50,
                "salario": "R$ 8.500,00",
                "inscricoes_ate": "2025-11-30"
            },
            {
                "titulo": "Governo Federal",
                "vagas": 25,
                "salario": "R$ 15.000,00",
                "inscricoes_ate": "2025-12-31"
            }
        ],
        "areas_mais_procuradas": [
            {"area": "Tecnologia", "concursos": 45},
            {"area": "Administração", "concursos": 38},
            {"area": "Saúde", "concursos": 32},
            {"area": "Educação", "concursos": 28}
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/concursos/analyze")
async def analyze_edital(data: dict):
    """Análise de edital simulada"""
    url = data.get("url", "")
    
    return {
        "url": url,
        "analise": {
            "resumo": "Concurso público para área de TI com excelentes oportunidades",
            "cargo": "Analista de Sistemas",
            "vagas": 10,
            "salario": "R$ 8.500,00",
            "requisitos": [
                "Ensino superior completo em área correlata",
                "Experiência mínima de 2 anos",
                "Conhecimentos em programação"
            ],
            "etapas": [
                "Prova objetiva (eliminatória)",
                "Prova discursiva (classificatória)",
                "Análise de títulos"
            ],
            "cronograma": {
                "inscricoes": "01/11/2025 a 30/11/2025",
                "prova_objetiva": "15/01/2026",
                "resultado": "15/02/2026"
            },
            "dicas": [
                "Foque em algoritmos e estruturas de dados",
                "Estude frameworks web modernos",
                "Pratique exercícios de lógica"
            ]
        },
        "confiabilidade": 0.95,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/admin/stats")
async def system_stats():
    """Estatísticas do sistema"""
    return {
        "sistema": {
            "versao": "2.0.0",
            "status": "Operacional",
            "uptime": "100%",
            "ultima_atualizacao": "2025-10-11"
        },
        "uso": {
            "requests_hoje": 1247,
            "usuarios_ativos": 45,
            "buscas_realizadas": 892,
            "editais_analisados": 67
        },
        "performance": {
            "tempo_resposta_medio": "120ms",
            "disponibilidade": "99.9%",
            "cache_hit_rate": "85%"
        },
        "timestamp": datetime.now().isoformat()
    }

# ==========================================
# INICIALIZAÇÃO
# ==========================================

if __name__ == "__main__":
    print("🚀 Iniciando ConcursAI API v2.0 - Versão Simplificada")
    print("📡 Servidor será executado em: http://localhost:8001")
    print("📖 Documentação disponível em: http://localhost:8001/docs")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )
