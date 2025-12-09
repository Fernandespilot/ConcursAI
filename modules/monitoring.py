"""
Sistema de Monitoramento em Tempo Real para ConcursAI
Monitora a saúde do sistema e estatísticas de uso
"""

import json
import time
import os
import platform
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
from dataclasses import dataclass, asdict

@dataclass
class SystemStats:
    """Estatísticas do sistema"""
    timestamp: str
    active_connections: int
    total_requests: int
    api_response_time: float
    concursos_loaded: int
    embeddings_loaded: bool
    ollama_status: str
    platform: str
    python_version: str

class MonitoringSystem:
    """Sistema de monitoramento em tempo real"""
    
    def __init__(self):
        self.stats_history: List[SystemStats] = []
        self.request_count = 0
        self.start_time = datetime.now()
        self.running = False
        self.monitoring_thread = None
        
    def start_monitoring(self):
        """Inicia o monitoramento"""
        if not self.running:
            self.running = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            print("📊 Sistema de monitoramento iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        print("📊 Sistema de monitoramento parado")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.running:
            try:
                stats = self._collect_stats()
                self.stats_history.append(stats)
                
                # Manter apenas os últimos 100 registros
                if len(self.stats_history) > 100:
                    self.stats_history.pop(0)
                
                # Aguardar 30 segundos antes da próxima coleta
                time.sleep(30)
                
            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                time.sleep(10)
    
    def _collect_stats(self) -> SystemStats:
        """Coleta estatísticas do sistema"""
        try:
            # Verificar status do Ollama
            ollama_status = self._check_ollama_status()
            
            # Contar concursos carregados
            concursos_loaded = self._count_concursos()
            
            return SystemStats(
                timestamp=datetime.now().isoformat(),
                active_connections=0,  # Simplificado
                total_requests=self.request_count,
                api_response_time=0.0,  # Será atualizado pelos endpoints
                concursos_loaded=concursos_loaded,
                embeddings_loaded=True,  # Será atualizado pelo sistema
                ollama_status=ollama_status,
                platform=platform.system(),
                python_version=platform.python_version()
            )
            
        except Exception as e:
            print(f"❌ Erro ao coletar estatísticas: {e}")
            return SystemStats(
                timestamp=datetime.now().isoformat(),
                active_connections=0,
                total_requests=self.request_count,
                api_response_time=0.0,
                concursos_loaded=0,
                embeddings_loaded=False,
                ollama_status="erro",
                platform=platform.system(),
                python_version=platform.python_version()
            )
    
    def _count_concursos(self) -> int:
        """Conta quantos concursos estão carregados"""
        try:
            if os.path.exists("concursos_chunks.csv"):
                with open("concursos_chunks.csv", 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    return len(lines) - 1  # Subtrair header
            return 0
        except:
            return 0
    
    def _check_ollama_status(self) -> str:
        """Verifica se o Ollama está rodando"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                return "online"
            else:
                return "offline"
        except:
            return "offline"
    
    def increment_request_count(self):
        """Incrementa contador de requisições"""
        self.request_count += 1
    
    def get_current_stats(self) -> Dict:
        """Retorna estatísticas atuais"""
        if not self.stats_history:
            # Retornar stats básicas se não houver histórico
            return {
                "status": "online",
                "uptime_seconds": int((datetime.now() - self.start_time).total_seconds()),
                "uptime_formatted": str(datetime.now() - self.start_time).split('.')[0],
                "current_stats": {
                    "timestamp": datetime.now().isoformat(),
                    "total_requests": self.request_count,
                    "concursos_loaded": self._count_concursos(),
                    "ollama_status": self._check_ollama_status(),
                    "platform": platform.system(),
                    "python_version": platform.python_version()
                },
                "trends": {}
            }
        
        latest = self.stats_history[-1]
        uptime = datetime.now() - self.start_time
        
        return {
            "status": "online",
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_formatted": str(uptime).split('.')[0],
            "current_stats": asdict(latest),
            "trends": self._calculate_trends()
        }
    
    def _calculate_trends(self) -> Dict:
        """Calcula tendências baseadas no histórico"""
        if len(self.stats_history) < 2:
            return {}
        
        recent = self.stats_history[-5:]  # Últimos 5 registros
        older = self.stats_history[-10:-5] if len(self.stats_history) >= 10 else self.stats_history[:-5]
        
        if not older:
            return {}
        
        # Calcular tendências de requisições
        recent_requests = sum(s.total_requests for s in recent) / len(recent)
        older_requests = sum(s.total_requests for s in older) / len(older)
        
        return {
            "requests_trend": "up" if recent_requests > older_requests else "down",
            "requests_change": round(recent_requests - older_requests, 2),
            "history_size": len(self.stats_history)
        }
    
    def get_health_status(self) -> Dict:
        """Retorna status de saúde do sistema"""
        if not self.stats_history:
            return {
                "status": "online",
                "health": "iniciando",
                "issues": [],
                "last_check": datetime.now().isoformat()
            }
        
        latest = self.stats_history[-1]
        issues = []
        
        # Verificar problemas básicos
        if latest.ollama_status == "offline":
            issues.append("Ollama offline")
        
        if latest.concursos_loaded == 0:
            issues.append("Nenhum concurso carregado")
        
        # Determinar status geral
        if not issues:
            health = "excelente"
        elif len(issues) == 1:
            health = "bom"
        else:
            health = "atenção"
        
        return {
            "status": "online",
            "health": health,
            "issues": issues,
            "last_check": latest.timestamp
        }

# Instância global do sistema de monitoramento
monitoring_system = MonitoringSystem()

def start_monitoring():
    """Inicia o sistema de monitoramento"""
    monitoring_system.start_monitoring()

def stop_monitoring():
    """Para o sistema de monitoramento"""
    monitoring_system.stop_monitoring()

def get_system_stats():
    """Retorna estatísticas do sistema"""
    return monitoring_system.get_current_stats()

def get_health_status():
    """Retorna status de saúde"""
    return monitoring_system.get_health_status()

def increment_api_request():
    """Incrementa contador de requisições da API"""
    monitoring_system.increment_request_count()
