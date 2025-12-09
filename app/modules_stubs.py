"""
Stubs para módulos legados - compatibilidade v1.0 → v2.0
=========================================================
"""

class ConcursoRAGStub:
    """Stub para ConcursoRAG quando módulo não está disponível"""
    
    async def initialize(self):
        pass
    
    async def search(self, query: str, limit: int = 10):
        return {
            "message": "Sistema RAG não disponível - execute em modo de compatibilidade",
            "query": query,
            "results": [],
            "stub": True
        }
    
    async def analyze_edital(self, url: str):
        return {
            "message": "Análise de edital não disponível - sistema em modo limitado",
            "url": url,
            "stub": True
        }

class MonitoringSystemStub:
    """Stub para MonitoringSystem quando módulo não está disponível"""
    
    async def start(self):
        pass
    
    async def stop(self):
        pass
    
    async def get_stats(self):
        return {
            "message": "Monitoramento não disponível",
            "stub": True
        }

async def get_dashboard_data_stub():
    """Stub para dashboard quando módulo não está disponível"""
    return {
        "message": "Dashboard em modo limitado - módulos legados não disponíveis",
        "stub": True,
        "concursos_total": 0,
        "concursos_novos": 0,
        "editais_analisados": 0
    }

async def start_scheduler_stub():
    """Stub para agendador quando módulo não está disponível"""
    print("⚠️ Agendador não disponível - sistema em modo limitado")
    pass
