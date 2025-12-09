"""
Sistema de Cache Inteligente para ConcursAI
Implementa cache Redis com fallback para cache em memória
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import asyncio
import logging

try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class MemoryCache:
    """Cache em memória como fallback"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._access_times: Dict[str, datetime] = {}
        self.max_size = 1000
    
    def _cleanup_old_entries(self):
        """Remove entradas antigas para evitar crescimento descontrolado"""
        if len(self._cache) > self.max_size:
            # Remove 20% das entradas mais antigas
            sorted_keys = sorted(
                self._access_times.keys(), 
                key=lambda k: self._access_times[k]
            )
            
            keys_to_remove = sorted_keys[:len(sorted_keys) // 5]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._access_times.pop(key, None)
    
    async def get(self, key: str) -> Optional[Any]:
        """Busca valor no cache"""
        if key in self._cache:
            entry = self._cache[key]
            
            # Verificar expiração
            if entry['expires_at'] and datetime.now() > entry['expires_at']:
                del self._cache[key]
                del self._access_times[key]
                return None
            
            # Atualizar tempo de acesso
            self._access_times[key] = datetime.now()
            return entry['value']
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Armazena valor no cache"""
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        self._access_times[key] = datetime.now()
        
        # Cleanup periódico
        self._cleanup_old_entries()
    
    async def delete(self, key: str):
        """Remove valor do cache"""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
    
    async def clear(self):
        """Limpa todo o cache"""
        self._cache.clear()
        self._access_times.clear()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        total_entries = len(self._cache)
        expired_entries = 0
        
        now = datetime.now()
        for entry in self._cache.values():
            if entry['expires_at'] and now > entry['expires_at']:
                expired_entries += 1
        
        return {
            'type': 'memory',
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'max_size': self.max_size
        }

class RedisCache:
    """Cache Redis"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._connected = False
    
    async def _get_redis(self) -> aioredis.Redis:
        """Obtém conexão Redis com lazy loading"""
        if not self._redis or not self._connected:
            try:
                self._redis = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={}
                )
                
                # Testar conexão
                await self._redis.ping()
                self._connected = True
                logger.info("Conexão Redis estabelecida")
                
            except Exception as e:
                logger.error(f"Erro ao conectar Redis: {e}")
                self._connected = False
                raise
        
        return self._redis
    
    async def get(self, key: str) -> Optional[Any]:
        """Busca valor no cache Redis"""
        try:
            redis = await self._get_redis()
            value = await redis.get(key)
            
            if value is not None:
                return pickle.loads(value)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar no Redis: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Armazena valor no cache Redis"""
        try:
            redis = await self._get_redis()
            serialized_value = pickle.dumps(value)
            
            if ttl > 0:
                await redis.setex(key, ttl, serialized_value)
            else:
                await redis.set(key, serialized_value)
                
        except Exception as e:
            logger.error(f"Erro ao armazenar no Redis: {e}")
    
    async def delete(self, key: str):
        """Remove valor do cache Redis"""
        try:
            redis = await self._get_redis()
            await redis.delete(key)
        except Exception as e:
            logger.error(f"Erro ao deletar do Redis: {e}")
    
    async def clear(self):
        """Limpa todo o cache Redis"""
        try:
            redis = await self._get_redis()
            await redis.flushdb()
        except Exception as e:
            logger.error(f"Erro ao limpar Redis: {e}")
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do cache Redis"""
        return {
            'type': 'redis',
            'connected': self._connected,
            'url': self.redis_url
        }

class CacheManager:
    """Gerenciador de cache com fallback automático"""
    
    def __init__(self):
        self.memory_cache = MemoryCache()
        self.redis_cache = None
        
        # Tentar inicializar Redis se disponível
        if REDIS_AVAILABLE and settings.enable_cache:
            try:
                self.redis_cache = RedisCache(settings.redis_url)
                logger.info("Cache Redis configurado")
            except Exception as e:
                logger.warning(f"Redis não disponível, usando cache em memória: {e}")
        else:
            logger.info("Usando apenas cache em memória")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Gera chave única para o cache"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Busca valor no cache (Redis primeiro, depois memória)"""
        if self.redis_cache:
            try:
                value = await self.redis_cache.get(key)
                if value is not None:
                    return value
            except Exception as e:
                logger.error(f"Erro no Redis cache, usando memória: {e}")
        
        return await self.memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = None):
        """Armazena valor no cache"""
        if ttl is None:
            ttl = settings.cache_ttl_seconds
        
        # Tentar Redis primeiro
        if self.redis_cache:
            try:
                await self.redis_cache.set(key, value, ttl)
            except Exception as e:
                logger.error(f"Erro ao armazenar no Redis: {e}")
        
        # Sempre armazenar em memória como backup
        await self.memory_cache.set(key, value, ttl)
    
    async def delete(self, key: str):
        """Remove valor do cache"""
        if self.redis_cache:
            try:
                await self.redis_cache.delete(key)
            except Exception as e:
                logger.error(f"Erro ao deletar do Redis: {e}")
        
        await self.memory_cache.delete(key)
    
    async def clear(self):
        """Limpa todo o cache"""
        if self.redis_cache:
            try:
                await self.redis_cache.clear()
            except Exception as e:
                logger.error(f"Erro ao limpar Redis: {e}")
        
        await self.memory_cache.clear()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        stats = {
            'memory': self.memory_cache.get_stats(),
            'redis': self.redis_cache.get_stats() if self.redis_cache else None,
            'settings': {
                'enabled': settings.enable_cache,
                'ttl_seconds': settings.cache_ttl_seconds
            }
        }
        return stats

# Instância global do cache
cache_manager = CacheManager()

def cached(prefix: str = "default", ttl: int = None):
    """Decorator para cache automático de funções"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not settings.enable_cache:
                return await func(*args, **kwargs)
            
            # Gerar chave única
            key = cache_manager._generate_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            
            # Tentar buscar no cache
            cached_result = await cache_manager.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit para {func.__name__}")
                return cached_result
            
            # Executar função e cachear resultado
            result = await func(*args, **kwargs)
            await cache_manager.set(key, result, ttl)
            logger.debug(f"Cache miss para {func.__name__} - resultado cacheado")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not settings.enable_cache:
                return func(*args, **kwargs)
            
            # Para funções síncronas, usar cache simples
            key = cache_manager._generate_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            
            # Executar de forma síncrona (não ideal, mas funcional)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                cached_result = loop.run_until_complete(cache_manager.get(key))
                if cached_result is not None:
                    return cached_result
                
                result = func(*args, **kwargs)
                loop.run_until_complete(cache_manager.set(key, result, ttl))
                return result
            finally:
                loop.close()
        
        # Detectar se é função async ou sync
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Funções de conveniência
async def get_cache_stats() -> Dict:
    """Retorna estatísticas do cache"""
    return cache_manager.get_stats()

async def clear_cache() -> bool:
    """Limpa todo o cache"""
    try:
        await cache_manager.clear()
        logger.info("Cache limpo com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        return False
