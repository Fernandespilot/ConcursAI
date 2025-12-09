"""
Sistema de Rate Limiting para ConcursAI
Implementa limitação de taxa de requisições com múltiplas estratégias
"""

import time
import asyncio
from typing import Dict, Optional, Tuple, List, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class TokenBucket:
    """Implementação do algoritmo Token Bucket"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens por segundo
        self.last_refill = time.time()
    
    def _refill(self):
        """Reabastece o bucket com tokens"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """Tenta consumir tokens do bucket"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_status(self) -> Dict:
        """Retorna status atual do bucket"""
        self._refill()
        return {
            'tokens': self.tokens,
            'capacity': self.capacity,
            'refill_rate': self.refill_rate
        }

class SlidingWindowCounter:
    """Implementação de janela deslizante para contagem de requisições"""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # em segundos
        self.max_requests = max_requests
        self.requests: deque = deque()
    
    def _cleanup_old_requests(self):
        """Remove requisições antigas da janela"""
        now = time.time()
        cutoff = now - self.window_size
        
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
    
    def is_allowed(self) -> Tuple[bool, Dict]:
        """Verifica se uma nova requisição é permitida"""
        self._cleanup_old_requests()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(time.time())
            return True, {
                'allowed': True,
                'requests_in_window': len(self.requests),
                'max_requests': self.max_requests,
                'window_size': self.window_size
            }
        
        return False, {
            'allowed': False,
            'requests_in_window': len(self.requests),
            'max_requests': self.max_requests,
            'window_size': self.window_size,
            'retry_after': self.get_retry_after()
        }
    
    def get_retry_after(self) -> int:
        """Calcula quando a próxima requisição será permitida"""
        if not self.requests:
            return 0
        
        oldest_request = self.requests[0]
        return max(0, int(oldest_request + self.window_size - time.time()))

class RateLimitManager:
    """Gerenciador central de rate limiting"""
    
    def __init__(self):
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_activities: Dict[str, List[datetime]] = defaultdict(list)
    
    def _get_client_id(self, request: Request) -> str:
        """Obtém identificador único do cliente"""
        # Prioridade: JWT user_id > IP address
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Usar IP como fallback
        client_ip = request.client.host
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        
        return f"ip:{client_ip}"
    
    def _is_ip_blocked(self, client_id: str) -> bool:
        """Verifica se IP está bloqueado"""
        if client_id in self.blocked_ips:
            if datetime.now() < self.blocked_ips[client_id]:
                return True
            else:
                # Remover IP da lista de bloqueados
                del self.blocked_ips[client_id]
        return False
    
    def _block_ip(self, client_id: str, duration_minutes: int = 15):
        """Bloqueia IP por tempo determinado"""
        block_until = datetime.now() + timedelta(minutes=duration_minutes)
        self.blocked_ips[client_id] = block_until
        logger.warning(f"IP {client_id} bloqueado até {block_until}")
    
    def _detect_suspicious_activity(self, client_id: str) -> bool:
        """Detecta atividade suspeita baseada em padrões"""
        now = datetime.now()
        
        # Limpar atividades antigas (últimas 24 horas)
        cutoff = now - timedelta(hours=24)
        self.suspicious_activities[client_id] = [
            activity for activity in self.suspicious_activities[client_id]
            if activity > cutoff
        ]
        
        # Adicionar atividade atual
        self.suspicious_activities[client_id].append(now)
        
        activities = self.suspicious_activities[client_id]
        
        # Detectar padrões suspeitos
        if len(activities) > 100:  # Mais de 100 requests em 24h
            recent_activities = [a for a in activities if a > now - timedelta(hours=1)]
            if len(recent_activities) > 50:  # Mais de 50 requests na última hora
                return True
        
        return False
    
    def get_token_bucket(self, client_id: str, capacity: int, refill_rate: float) -> TokenBucket:
        """Obtém ou cria token bucket para cliente"""
        key = f"{client_id}:bucket:{capacity}:{refill_rate}"
        
        if key not in self.token_buckets:
            self.token_buckets[key] = TokenBucket(capacity, refill_rate)
        
        return self.token_buckets[key]
    
    def get_sliding_window(self, client_id: str, window_size: int, max_requests: int) -> SlidingWindowCounter:
        """Obtém ou cria sliding window para cliente"""
        key = f"{client_id}:window:{window_size}:{max_requests}"
        
        if key not in self.sliding_windows:
            self.sliding_windows[key] = SlidingWindowCounter(window_size, max_requests)
        
        return self.sliding_windows[key]
    
    def check_rate_limit(self, request: Request, 
                        requests_per_minute: int = None,
                        requests_per_hour: int = None,
                        burst_capacity: int = None) -> Tuple[bool, Dict]:
        """Verifica todos os limites de taxa configurados"""
        
        client_id = self._get_client_id(request)
        
        # Verificar se IP está bloqueado
        if self._is_ip_blocked(client_id):
            return False, {
                'error': 'IP_BLOCKED',
                'message': 'IP temporariamente bloqueado por atividade suspeita',
                'retry_after': 900  # 15 minutos
            }
        
        # Detectar atividade suspeita
        if self._detect_suspicious_activity(client_id):
            self._block_ip(client_id)
            return False, {
                'error': 'SUSPICIOUS_ACTIVITY',
                'message': 'Atividade suspeita detectada',
                'retry_after': 900
            }
        
        results = []
        
        # Rate limit por minuto
        if requests_per_minute:
            window = self.get_sliding_window(client_id, 60, requests_per_minute)
            allowed, info = window.is_allowed()
            if not allowed:
                return False, {
                    'error': 'RATE_LIMIT_EXCEEDED',
                    'message': f'Limite de {requests_per_minute} requisições por minuto excedido',
                    'retry_after': info.get('retry_after', 60),
                    'window': 'minute'
                }
            results.append(info)
        
        # Rate limit por hora
        if requests_per_hour:
            window = self.get_sliding_window(client_id, 3600, requests_per_hour)
            allowed, info = window.is_allowed()
            if not allowed:
                return False, {
                    'error': 'RATE_LIMIT_EXCEEDED',
                    'message': f'Limite de {requests_per_hour} requisições por hora excedido',
                    'retry_after': info.get('retry_after', 3600),
                    'window': 'hour'
                }
            results.append(info)
        
        # Token bucket para burst
        if burst_capacity:
            bucket = self.get_token_bucket(client_id, burst_capacity, burst_capacity / 60)
            if not bucket.consume():
                return False, {
                    'error': 'BURST_LIMIT_EXCEEDED',
                    'message': f'Limite de burst de {burst_capacity} requisições excedido',
                    'retry_after': 60,
                    'bucket_status': bucket.get_status()
                }
            results.append(bucket.get_status())
        
        return True, {
            'allowed': True,
            'client_id': client_id,
            'limits_checked': results
        }
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do rate limiting"""
        return {
            'active_buckets': len(self.token_buckets),
            'active_windows': len(self.sliding_windows),
            'blocked_ips': len(self.blocked_ips),
            'suspicious_activities': len(self.suspicious_activities),
            'blocked_ips_list': {
                ip: block_until.isoformat() 
                for ip, block_until in self.blocked_ips.items()
            }
        }

# Instância global do rate limiter
rate_limiter = RateLimitManager()

def rate_limit(requests_per_minute: int = None,
               requests_per_hour: int = None,
               burst_capacity: int = None):
    """Decorator para aplicar rate limiting a endpoints"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            
            # Aplicar rate limiting apenas se habilitado
            if settings.enable_rate_limiting:
                allowed, info = rate_limiter.check_rate_limit(
                    request, 
                    requests_per_minute, 
                    requests_per_hour, 
                    burst_capacity
                )
                
                if not allowed:
                    logger.warning(f"Rate limit exceeded: {info}")
                    raise HTTPException(
                        status_code=429,
                        detail=info,
                        headers={'Retry-After': str(info.get('retry_after', 60))}
                    )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

# Middleware para rate limiting global
async def rate_limiting_middleware(request: Request, call_next):
    """Middleware para aplicar rate limiting global"""
    
    if settings.enable_rate_limiting:
        # Rate limiting global básico
        allowed, info = rate_limiter.check_rate_limit(
            request,
            requests_per_minute=settings.global_rate_limit_per_minute,
            requests_per_hour=settings.global_rate_limit_per_hour
        )
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content=info,
                headers={'Retry-After': str(info.get('retry_after', 60))}
            )
    
    response = await call_next(request)
    return response

# Funções utilitárias
async def get_rate_limit_stats() -> Dict:
    """Retorna estatísticas do rate limiting"""
    return rate_limiter.get_stats()

async def unblock_ip(client_id: str) -> bool:
    """Remove IP da lista de bloqueados"""
    try:
        if client_id in rate_limiter.blocked_ips:
            del rate_limiter.blocked_ips[client_id]
            logger.info(f"IP {client_id} desbloqueado")
            return True
        return False
    except Exception as e:
        logger.error(f"Erro ao desbloquear IP: {e}")
        return False

async def block_ip(client_id: str, duration_minutes: int = 15) -> bool:
    """Bloqueia IP manualmente"""
    try:
        rate_limiter._block_ip(client_id, duration_minutes)
        return True
    except Exception as e:
        logger.error(f"Erro ao bloquear IP: {e}")
        return False
