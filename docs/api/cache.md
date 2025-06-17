# Cache API Reference

This document provides comprehensive information about Aurelis caching system, including cache strategies, backends, configuration, and optimization techniques.

## Table of Contents

- [Overview](#overview)
- [Cache Architecture](#cache-architecture)
- [Cache Backends](#cache-backends)
- [Cache Strategies](#cache-strategies)
- [Cache Manager](#cache-manager)
- [Cache Decorators](#cache-decorators)
- [Model Response Caching](#model-response-caching)
- [File System Caching](#file-system-caching)
- [Cache Invalidation](#cache-invalidation)
- [Performance Optimization](#performance-optimization)
- [Monitoring](#monitoring)
- [Usage Examples](#usage-examples)

## Overview

Aurelis implements a multi-layered caching system designed to improve performance and reduce external API calls. The caching system supports multiple backends, intelligent cache strategies, and automatic invalidation.

### Cache Benefits

- **Reduced Latency**: Faster response times for repeated requests
- **Cost Optimization**: Fewer external API calls
- **Improved Reliability**: Fallback for when external services are unavailable
- **Better User Experience**: Consistent performance under load

## Cache Architecture

### Cache Layers

```python
from aurelis.cache import CacheManager
from dataclasses import dataclass
from typing import Any, Optional, Dict, List

@dataclass
class CacheLayer:
    """Represents a cache layer"""
    
    name: str
    backend: str
    ttl: int
    max_size: Optional[int] = None
    priority: int = 0  # Higher priority = checked first

class CacheManager:
    """Manages multi-layered caching system"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.layers = self._initialize_layers()
        self.stats = CacheStats()
    
    def _initialize_layers(self) -> List[CacheLayer]:
        """Initialize cache layers in priority order"""
        return [
            CacheLayer("L1_memory", "memory", ttl=300, max_size=1000, priority=3),
            CacheLayer("L2_redis", "redis", ttl=3600, priority=2),
            CacheLayer("L3_disk", "disk", ttl=86400, priority=1)
        ]
```

### Cache Key Strategy

```python
from aurelis.cache import CacheKeyBuilder
import hashlib
import json

class CacheKeyBuilder:
    """Builds consistent cache keys"""
    
    def __init__(self, namespace: str = "aurelis"):
        self.namespace = namespace
    
    def build_key(
        self,
        category: str,
        identifier: str,
        params: Optional[Dict[str, Any]] = None,
        version: str = "v1"
    ) -> str:
        """Build cache key with consistent format"""
        
        key_parts = [self.namespace, version, category, identifier]
        
        if params:
            # Sort parameters for consistent keys
            sorted_params = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
        
        return ":".join(key_parts)
    
    def build_model_key(
        self,
        model_type: str,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Build cache key for model requests"""
        
        # Hash the prompt for consistent length
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        
        return self.build_key(
            category="model",
            identifier=f"{model_type}:{prompt_hash}",
            params=parameters
        )
```

## Cache Backends

### Memory Backend

```python
from aurelis.cache import MemoryBackend
import threading
from collections import OrderedDict
import time

class MemoryBackend:
    """In-memory cache backend using LRU eviction"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = ttl
        self.cache = OrderedDict()
        self.expiry = {}
        self.lock = threading.RLock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check expiry
            if key in self.expiry and time.time() > self.expiry[key]:
                del self.cache[key]
                del self.expiry[key]
                return None
            
            # Move to end (most recently used)
            value = self.cache[key]
            del self.cache[key]
            self.cache[key] = value
            
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        with self.lock:
            # Remove oldest items if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.expiry.pop(oldest_key, None)
            
            self.cache[key] = value
            
            if ttl or self.default_ttl:
                self.expiry[key] = time.time() + (ttl or self.default_ttl)
            
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.expiry.pop(key, None)
                return True
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.expiry.clear()
            return True
```

### Redis Backend

```python
from aurelis.cache import RedisBackend
import redis.asyncio as redis
import json
import pickle

class RedisBackend:
    """Redis cache backend"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis = None
        self.serialization = config.get("serialization", "json")
    
    async def connect(self):
        """Connect to Redis"""
        self.redis = redis.from_url(
            self.config.redis_url,
            password=self.config.redis_password,
            ssl=self.config.redis_ssl,
            encoding="utf-8",
            decode_responses=False  # Handle binary data
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            data = await self.redis.get(key)
            if data is None:
                return None
            
            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in Redis"""
        try:
            data = self._serialize(value)
            
            if ttl:
                await self.redis.setex(key, ttl, data)
            else:
                await self.redis.set(key, data)
            
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if self.serialization == "json":
            return json.dumps(value).encode()
        elif self.serialization == "pickle":
            return pickle.dumps(value)
        else:
            return str(value).encode()
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        if self.serialization == "json":
            return json.loads(data.decode())
        elif self.serialization == "pickle":
            return pickle.loads(data)
        else:
            return data.decode()
```

### Disk Backend

```python
from aurelis.cache import DiskBackend
import os
import json
import time
import hashlib
from pathlib import Path

class DiskBackend:
    """File system cache backend"""
    
    def __init__(self, cache_dir: str = "./cache", max_size: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check expiry
            if cache_data.get("expires_at") and time.time() > cache_data["expires_at"]:
                file_path.unlink(missing_ok=True)
                return None
            
            return cache_data["value"]
        except Exception as e:
            logger.error(f"Disk cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in disk cache"""
        try:
            # Clean up if at capacity
            await self._cleanup_if_needed()
            
            file_path = self._get_file_path(key)
            
            cache_data = {
                "value": value,
                "created_at": time.time(),
                "expires_at": time.time() + ttl if ttl else None
            }
            
            with open(file_path, 'w') as f:
                json.dump(cache_data, f)
            
            return True
        except Exception as e:
            logger.error(f"Disk cache set error: {e}")
            return False
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    async def _cleanup_if_needed(self):
        """Remove old files if at capacity"""
        cache_files = list(self.cache_dir.glob("*.json"))
        
        if len(cache_files) >= self.max_size:
            # Sort by modification time and remove oldest
            cache_files.sort(key=lambda f: f.stat().st_mtime)
            for file_path in cache_files[:len(cache_files) - self.max_size + 1]:
                file_path.unlink(missing_ok=True)
```

## Cache Strategies

### Cache-Aside Strategy

```python
from aurelis.cache import CacheAside

class CacheAside:
    """Cache-aside (lazy loading) strategy"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    async def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
        ttl: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """Get from cache or compute and cache result"""
        
        # Try to get from cache
        result = await self.cache.get(key)
        if result is not None:
            return result
        
        # Compute result
        result = await compute_func(*args, **kwargs)
        
        # Cache result
        await self.cache.set(key, result, ttl)
        
        return result
```

### Write-Through Strategy

```python
from aurelis.cache import WriteThrough

class WriteThrough:
    """Write-through cache strategy"""
    
    def __init__(self, cache_manager: CacheManager, data_store):
        self.cache = cache_manager
        self.data_store = data_store
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache, fallback to data store"""
        
        # Try cache first
        result = await self.cache.get(key)
        if result is not None:
            return result
        
        # Fallback to data store
        result = await self.data_store.get(key)
        if result is not None:
            await self.cache.set(key, result)
        
        return result
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Write to both cache and data store"""
        
        # Write to data store first
        await self.data_store.set(key, value)
        
        # Then write to cache
        await self.cache.set(key, value, ttl)
```

### Write-Behind Strategy

```python
from aurelis.cache import WriteBehind
import asyncio
from queue import Queue

class WriteBehind:
    """Write-behind (write-back) cache strategy"""
    
    def __init__(self, cache_manager: CacheManager, data_store):
        self.cache = cache_manager
        self.data_store = data_store
        self.write_queue = Queue()
        self.batch_size = 10
        self.flush_interval = 30  # seconds
        self._start_background_writer()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Write to cache immediately, queue for data store"""
        
        # Write to cache immediately
        await self.cache.set(key, value, ttl)
        
        # Queue for background write to data store
        self.write_queue.put((key, value))
    
    def _start_background_writer(self):
        """Start background task to flush writes"""
        asyncio.create_task(self._background_writer())
    
    async def _background_writer(self):
        """Background task to write queued items to data store"""
        while True:
            items = []
            
            # Collect batch of items
            while len(items) < self.batch_size and not self.write_queue.empty():
                items.append(self.write_queue.get())
            
            # Write batch to data store
            if items:
                await self._write_batch(items)
            
            await asyncio.sleep(self.flush_interval)
```

## Cache Manager

### Unified Cache Manager

```python
from aurelis.cache import UnifiedCacheManager

class UnifiedCacheManager:
    """Unified interface for all cache operations"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.backends = self._initialize_backends()
        self.key_builder = CacheKeyBuilder()
        self.stats = CacheStats()
    
    async def get(
        self,
        category: str,
        identifier: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Get value from cache with automatic key building"""
        
        key = self.key_builder.build_key(category, identifier, params)
        
        # Try each backend in priority order
        for backend_name, backend in self.backends.items():
            try:
                value = await backend.get(key)
                if value is not None:
                    await self.stats.record_hit(backend_name)
                    return value
            except Exception as e:
                logger.error(f"Cache get error in {backend_name}: {e}")
        
        await self.stats.record_miss()
        return None
    
    async def set(
        self,
        category: str,
        identifier: str,
        value: Any,
        ttl: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Set value in cache with automatic key building"""
        
        key = self.key_builder.build_key(category, identifier, params)
        
        # Write to all backends
        success = True
        for backend_name, backend in self.backends.items():
            try:
                await backend.set(key, value, ttl)
            except Exception as e:
                logger.error(f"Cache set error in {backend_name}: {e}")
                success = False
        
        if success:
            await self.stats.record_write()
        
        return success
    
    async def invalidate(
        self,
        category: str,
        identifier: Optional[str] = None,
        pattern: Optional[str] = None
    ):
        """Invalidate cache entries"""
        
        if identifier:
            # Invalidate specific key
            key = self.key_builder.build_key(category, identifier)
            for backend in self.backends.values():
                await backend.delete(key)
        elif pattern:
            # Invalidate by pattern
            await self._invalidate_by_pattern(pattern)
        else:
            # Invalidate entire category
            await self._invalidate_category(category)
```

## Cache Decorators

### Function Caching

```python
from aurelis.cache import cached
from functools import wraps

def cached(
    ttl: int = 3600,
    key_func: Optional[Callable] = None,
    category: str = "function"
):
    """Decorator for caching function results"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Build cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = await cache_manager.get(category, cache_key)
            if result is not None:
                return result
            
            # Compute result
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(category, cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# Usage examples
@cached(ttl=3600, category="model_responses")
async def get_model_response(model_type: str, prompt: str):
    """Cached model response function"""
    pass

@cached(ttl=1800, key_func=lambda user_id, options: f"user:{user_id}:{hash(str(options))}")
async def get_user_data(user_id: str, options: Dict[str, Any]):
    """Cached user data with custom key function"""
    pass
```

### Class Method Caching

```python
from aurelis.cache import cached_method

class ModelService:
    """Service with cached methods"""
    
    @cached_method(ttl=3600, category="models")
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get model information with caching"""
        # Expensive operation to get model info
        return await self._fetch_model_info(model_type)
    
    @cached_method(ttl=600, invalidate_on=["model_config_updated"])
    async def get_model_config(self, model_type: str) -> ModelConfig:
        """Get model configuration with cache invalidation"""
        return await self._load_model_config(model_type)
```

## Model Response Caching

### Model Response Cache

```python
from aurelis.cache import ModelResponseCache

class ModelResponseCache:
    """Specialized cache for model responses"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.key_builder = CacheKeyBuilder()
    
    async def get_response(
        self,
        model_type: str,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> Optional[ModelResponse]:
        """Get cached model response"""
        
        cache_key = self.key_builder.build_model_key(
            model_type, prompt, parameters
        )
        
        return await self.cache.get("model_responses", cache_key)
    
    async def cache_response(
        self,
        model_type: str,
        prompt: str,
        parameters: Dict[str, Any],
        response: ModelResponse,
        ttl: Optional[int] = None
    ):
        """Cache model response"""
        
        cache_key = self.key_builder.build_model_key(
            model_type, prompt, parameters
        )
        
        # Don't cache error responses
        if response.status == "error":
            return
        
        # Use longer TTL for successful responses
        cache_ttl = ttl or (3600 if response.status == "success" else 300)
        
        await self.cache.set(
            "model_responses",
            cache_key,
            response,
            cache_ttl
        )
    
    async def invalidate_model_cache(self, model_type: str):
        """Invalidate all cached responses for a model"""
        pattern = f"aurelis:*:model_responses:{model_type}:*"
        await self.cache.invalidate(pattern=pattern)
```

### Response Similarity Detection

```python
from aurelis.cache import SimilarityCache
import difflib

class SimilarityCache:
    """Cache with semantic similarity detection"""
    
    def __init__(self, cache_manager: CacheManager, similarity_threshold: float = 0.85):
        self.cache = cache_manager
        self.similarity_threshold = similarity_threshold
    
    async def find_similar_response(
        self,
        prompt: str,
        model_type: str
    ) -> Optional[ModelResponse]:
        """Find cached response for similar prompt"""
        
        # Get recent cached prompts for this model
        recent_prompts = await self._get_recent_prompts(model_type)
        
        # Find most similar prompt
        best_match = None
        best_similarity = 0.0
        
        for cached_prompt in recent_prompts:
            similarity = difflib.SequenceMatcher(
                None, prompt.lower(), cached_prompt.lower()
            ).ratio()
            
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = cached_prompt
        
        if best_match:
            # Get cached response for similar prompt
            return await self.cache.get("model_responses", best_match)
        
        return None
```

## File System Caching

### File Cache Manager

```python
from aurelis.cache import FileCacheManager
import os
import hashlib
from pathlib import Path

class FileCacheManager:
    """Manages file system caching"""
    
    def __init__(self, cache_dir: str = "./file_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def cache_file(
        self,
        file_path: str,
        category: str = "files"
    ) -> str:
        """Cache file and return cache key"""
        
        # Generate cache key from file content
        with open(file_path, 'rb') as f:
            content = f.read()
            file_hash = hashlib.sha256(content).hexdigest()
        
        # Create cached file path
        cache_key = f"{category}:{file_hash}"
        cached_file_path = self.cache_dir / category / f"{file_hash}.cache"
        cached_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file to cache if not exists
        if not cached_file_path.exists():
            with open(cached_file_path, 'wb') as f:
                f.write(content)
        
        return cache_key
    
    async def get_cached_file(self, cache_key: str) -> Optional[Path]:
        """Get cached file path"""
        
        category, file_hash = cache_key.split(':', 1)
        cached_file_path = self.cache_dir / category / f"{file_hash}.cache"
        
        if cached_file_path.exists():
            return cached_file_path
        
        return None
```

## Cache Invalidation

### Invalidation Strategies

```python
from aurelis.cache import CacheInvalidator

class CacheInvalidator:
    """Handles cache invalidation strategies"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.invalidation_rules = {}
    
    def register_invalidation_rule(
        self,
        trigger: str,
        targets: List[str]
    ):
        """Register cache invalidation rule"""
        self.invalidation_rules[trigger] = targets
    
    async def invalidate_on_event(self, event: str, context: Dict[str, Any] = None):
        """Invalidate cache based on event"""
        
        if event in self.invalidation_rules:
            targets = self.invalidation_rules[event]
            
            for target in targets:
                if target.startswith("pattern:"):
                    # Pattern-based invalidation
                    pattern = target[8:]  # Remove "pattern:" prefix
                    await self._invalidate_by_pattern(pattern, context)
                elif target.startswith("category:"):
                    # Category-based invalidation
                    category = target[9:]  # Remove "category:" prefix
                    await self.cache.invalidate_category(category)
                else:
                    # Direct key invalidation
                    await self.cache.delete(target)
    
    async def _invalidate_by_pattern(
        self,
        pattern: str,
        context: Dict[str, Any] = None
    ):
        """Invalidate cache entries matching pattern"""
        
        # Replace context variables in pattern
        if context:
            for key, value in context.items():
                pattern = pattern.replace(f"{{{key}}}", str(value))
        
        # Implementation depends on backend
        await self.cache.invalidate_pattern(pattern)

# Usage example
invalidator = CacheInvalidator(cache_manager)

# Register rules
invalidator.register_invalidation_rule(
    trigger="model_updated",
    targets=["category:model_responses", "pattern:model_info:{model_type}"]
)

invalidator.register_invalidation_rule(
    trigger="user_settings_changed",
    targets=["pattern:user_data:{user_id}"]
)

# Trigger invalidation
await invalidator.invalidate_on_event(
    "model_updated",
    context={"model_type": "gpt-4o"}
)
```

## Performance Optimization

### Cache Warming

```python
from aurelis.cache import CacheWarmer

class CacheWarmer:
    """Pre-loads frequently accessed data into cache"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    async def warm_model_responses(self, common_prompts: List[str]):
        """Pre-cache responses for common prompts"""
        
        for prompt in common_prompts:
            for model_type in ["github-gpt-4o", "github-gpt-4o-mini"]:
                # Generate response and cache it
                response = await self._generate_response(model_type, prompt)
                await self.cache.set(
                    "model_responses",
                    f"{model_type}:{hash(prompt)}",
                    response,
                    ttl=3600
                )
    
    async def warm_user_data(self, active_users: List[str]):
        """Pre-cache data for active users"""
        
        for user_id in active_users:
            user_data = await self._load_user_data(user_id)
            await self.cache.set(
                "user_data",
                user_id,
                user_data,
                ttl=1800
            )
```

### Cache Compression

```python
from aurelis.cache import CompressedCache
import gzip
import json

class CompressedCache:
    """Cache with automatic compression for large values"""
    
    def __init__(self, cache_manager: CacheManager, compression_threshold: int = 1024):
        self.cache = cache_manager
        self.compression_threshold = compression_threshold
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Set value with compression if above threshold"""
        
        # Serialize value
        serialized = json.dumps(value).encode()
        
        # Compress if above threshold
        if len(serialized) > self.compression_threshold:
            compressed = gzip.compress(serialized)
            cache_value = {
                "compressed": True,
                "data": compressed
            }
        else:
            cache_value = {
                "compressed": False,
                "data": serialized
            }
        
        await self.cache.set(key, cache_value, ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value with automatic decompression"""
        
        cache_value = await self.cache.get(key)
        if cache_value is None:
            return None
        
        # Decompress if needed
        if cache_value["compressed"]:
            decompressed = gzip.decompress(cache_value["data"])
            return json.loads(decompressed)
        else:
            return json.loads(cache_value["data"])
```

## Monitoring

### Cache Statistics

```python
from aurelis.cache import CacheStats
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    
    hits: int = 0
    misses: int = 0
    writes: int = 0
    deletes: int = 0
    errors: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0
    average_response_time: float = 0.0
    cache_size: int = 0
    memory_usage: int = 0

class CacheStats:
    """Tracks cache performance statistics"""
    
    def __init__(self):
        self.metrics = CacheMetrics()
        self.detailed_stats = {}
        self.response_times = []
    
    async def record_hit(self, backend: str = "default"):
        """Record cache hit"""
        self.metrics.hits += 1
        self.metrics.total_requests += 1
        self._update_hit_rate()
        
        # Track per-backend stats
        if backend not in self.detailed_stats:
            self.detailed_stats[backend] = CacheMetrics()
        self.detailed_stats[backend].hits += 1
    
    async def record_miss(self, backend: str = "default"):
        """Record cache miss"""
        self.metrics.misses += 1
        self.metrics.total_requests += 1
        self._update_hit_rate()
        
        if backend not in self.detailed_stats:
            self.detailed_stats[backend] = CacheMetrics()
        self.detailed_stats[backend].misses += 1
    
    def _update_hit_rate(self):
        """Update hit rate calculation"""
        if self.metrics.total_requests > 0:
            self.metrics.hit_rate = self.metrics.hits / self.metrics.total_requests
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        return {
            "overall_metrics": self.metrics,
            "backend_metrics": self.detailed_stats,
            "performance_summary": {
                "hit_rate_percentage": self.metrics.hit_rate * 100,
                "total_requests": self.metrics.total_requests,
                "cache_efficiency": "Good" if self.metrics.hit_rate > 0.8 else "Needs Improvement"
            }
        }
```

## Usage Examples

### Basic Cache Usage

```python
from aurelis.cache import get_cache_manager

# Get cache manager
cache = get_cache_manager()

# Cache a value
await cache.set("user_data", "user123", {"name": "John", "role": "developer"}, ttl=3600)

# Get cached value
user_data = await cache.get("user_data", "user123")
print(user_data)  # {"name": "John", "role": "developer"}

# Cache with parameters
await cache.set(
    "search_results",
    "query123",
    search_results,
    params={"page": 1, "limit": 10},
    ttl=1800
)
```

### Model Response Caching

```python
from aurelis.cache import ModelResponseCache
from aurelis.models import get_model_orchestrator

# Initialize caches
model_cache = ModelResponseCache(cache_manager)
orchestrator = get_model_orchestrator()

async def get_cached_model_response(
    model_type: str,
    prompt: str,
    parameters: Dict[str, Any]
) -> ModelResponse:
    """Get model response with caching"""
    
    # Try cache first
    cached_response = await model_cache.get_response(
        model_type, prompt, parameters
    )
    
    if cached_response:
        return cached_response
    
    # Generate new response
    request = ModelRequest(
        model_type=model_type,
        prompt=prompt,
        **parameters
    )
    
    response = await orchestrator.process_request(request)
    
    # Cache the response
    await model_cache.cache_response(
        model_type, prompt, parameters, response
    )
    
    return response
```

### Cache Invalidation

```python
from aurelis.cache import CacheInvalidator

# Set up invalidation
invalidator = CacheInvalidator(cache_manager)

# Register invalidation rules
invalidator.register_invalidation_rule(
    trigger="model_config_updated",
    targets=["category:model_responses", "category:model_info"]
)

# Trigger invalidation when config changes
async def update_model_config(model_type: str, new_config: Dict[str, Any]):
    """Update model config and invalidate related cache"""
    
    # Update configuration
    await config_manager.update_model_config(model_type, new_config)
    
    # Invalidate related cache entries
    await invalidator.invalidate_on_event(
        "model_config_updated",
        context={"model_type": model_type}
    )
```

### Performance Monitoring

```python
from aurelis.cache import CacheMonitor

# Monitor cache performance
monitor = CacheMonitor(cache_manager)

# Get real-time stats
stats = await monitor.get_current_stats()
print(f"Hit rate: {stats.hit_rate * 100:.2f}%")
print(f"Total requests: {stats.total_requests}")

# Generate performance report
report = monitor.get_performance_report()
print(json.dumps(report, indent=2))
```

For more information on caching in specific contexts, see:
- [Model Orchestrator Caching](model-orchestrator.md)
- [Configuration Caching](configuration.md)
- [Performance Optimization](../guides/performance-optimization.md)
