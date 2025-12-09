"""
Configurações do ConcursAI v2.0
"""

import os
from typing import List, Optional

class Settings:
    """Configurações simples para inicialização"""
    
    # Aplicação
    app_name: str = "ConcursAI"
    app_version: str = "2.0.0"
    debug: bool = True
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Segurança
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-development-only")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Cache
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Rate Limiting
    enable_rate_limiting: bool = True
    global_rate_limit_per_minute: int = 100
    global_rate_limit_per_hour: int = 1000
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000", 
        "http://127.0.0.1:8000"
    ]
    
    # Logs
    log_level: str = "INFO"
    log_file: Optional[str] = "./logs/concursai.log"
    
    # Features
    enable_scheduler: bool = True
    enable_monitoring: bool = True

def get_settings() -> Settings:
    """Retorna configurações"""
    return Settings()

# Instância global
settings = get_settings()
