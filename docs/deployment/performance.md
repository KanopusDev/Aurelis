# Performance Tuning Guide

## Overview

This guide provides comprehensive performance optimization strategies for Aurelis deployments, covering system resources, caching, model optimization, and monitoring best practices.

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores, 2.0 GHz
- **Memory**: 4 GB RAM
- **Storage**: 10 GB SSD
- **Network**: 100 Mbps

### Recommended Requirements
- **CPU**: 4+ cores, 3.0+ GHz
- **Memory**: 8+ GB RAM
- **Storage**: 50+ GB NVMe SSD
- **Network**: 1 Gbps

### Enterprise Requirements
- **CPU**: 8+ cores, 3.5+ GHz
- **Memory**: 16+ GB RAM
- **Storage**: 100+ GB NVMe SSD (RAID 1)
- **Network**: 10 Gbps with redundancy

## Application Performance

### Python Optimization

#### Runtime Configuration
```python
# uvloop for better async performance
import uvloop
import asyncio

# Set uvloop as the default event loop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Optimize garbage collection
import gc
gc.set_threshold(700, 10, 10)
```

#### Memory Management
```python
# Memory pool configuration
import os

# Optimize memory allocation
os.environ['MALLOC_ARENA_MAX'] = '2'
os.environ['MALLOC_MMAP_THRESHOLD_'] = '65536'

# Use memory mapping for large files
import mmap

def process_large_file(filepath):
    with open(filepath, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
            # Process file efficiently
            pass
```

#### Concurrency Optimization
```python
# Async/await optimization
import asyncio
from asyncio import Semaphore

class OptimizedProcessor:
    def __init__(self, max_concurrent=10):
        self.semaphore = Semaphore(max_concurrent)
        
    async def process_request(self, request):
        async with self.semaphore:
            # Process with controlled concurrency
            return await self._handle_request(request)
            
    async def batch_process(self, requests):
        # Process requests in batches
        batch_size = 5
        results = []
        
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self.process_request(req) for req in batch],
                return_exceptions=True
            )
            results.extend(batch_results)
            
        return results
```

### Model Performance

#### Request Batching
```python
# Batch multiple requests for efficiency
class ModelOrchestrator:
    def __init__(self, batch_size=5, batch_timeout=0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests = []
        
    async def process_batch(self, requests):
        # Group similar requests
        grouped = self._group_by_model(requests)
        
        results = {}
        for model_type, model_requests in grouped.items():
            model_results = await self._process_model_batch(
                model_type, model_requests
            )
            results.update(model_results)
            
        return results
        
    def _group_by_model(self, requests):
        groups = {}
        for req in requests:
            model_type = req.model_type
            if model_type not in groups:
                groups[model_type] = []
            groups[model_type].append(req)
        return groups
```

#### Response Caching
```python
# Intelligent caching strategy
import hashlib
from typing import Optional
from dataclasses import dataclass

@dataclass
class CacheConfig:
    ttl_seconds: int = 3600
    max_size: int = 1000
    compression: bool = True

class ModelCache:
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache = {}
        
    def _generate_key(self, request) -> str:
        content = f"{request.prompt}:{request.model_type}:{request.task_type}"
        return hashlib.sha256(content.encode()).hexdigest()
        
    async def get(self, request) -> Optional[str]:
        key = self._generate_key(request)
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                return entry.value
            else:
                del self.cache[key]
        return None
        
    async def set(self, request, response: str):
        key = self._generate_key(request)
        if len(self.cache) >= self.config.max_size:
            # Remove oldest entries
            self._evict_oldest()
        self.cache[key] = CacheEntry(response, self.config.ttl_seconds)
```

### Database Optimization

#### Connection Pooling
```python
# Optimized database connections
import asyncpg
from contextlib import asynccontextmanager

class DatabasePool:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
        
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
            command_timeout=60,
            server_settings={
                'jit': 'off',
                'shared_preload_libraries': 'pg_stat_statements'
            }
        )
        
    @asynccontextmanager
    async def acquire(self):
        async with self.pool.acquire() as connection:
            yield connection
```

#### Query Optimization
```sql
-- Index optimization
CREATE INDEX CONCURRENTLY idx_requests_created_at 
ON requests (created_at DESC);

CREATE INDEX CONCURRENTLY idx_requests_model_type 
ON requests (model_type, created_at);

-- Partitioning for large tables
CREATE TABLE requests_2025_06 PARTITION OF requests
FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM requests 
WHERE model_type = 'gpt-4' 
AND created_at > NOW() - INTERVAL '1 hour';
```

## Caching Strategies

### Multi-Level Caching

#### L1 Cache (In-Memory)
```python
# Fast in-memory cache
from cachetools import TTLCache, LRUCache
import threading

class L1Cache:
    def __init__(self, max_size=1000, ttl=300):
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)
        self.lock = threading.RLock()
        
    def get(self, key):
        with self.lock:
            return self.cache.get(key)
            
    def set(self, key, value):
        with self.lock:
            self.cache[key] = value
```

#### L2 Cache (Redis)
```python
# Redis-based distributed cache
import redis.asyncio as redis
import json
import pickle

class L2Cache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        
    async def get(self, key: str):
        data = await self.redis.get(key)
        if data:
            return pickle.loads(data)
        return None
        
    async def set(self, key: str, value, ttl: int = 3600):
        data = pickle.dumps(value)
        await self.redis.setex(key, ttl, data)
        
    async def invalidate_pattern(self, pattern: str):
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

#### Cache Warming
```python
# Proactive cache warming
class CacheWarmer:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        
    async def warm_popular_requests(self):
        # Pre-populate cache with common requests
        popular_requests = await self._get_popular_requests()
        
        for request in popular_requests:
            if not await self.cache_manager.exists(request):
                response = await self._generate_response(request)
                await self.cache_manager.set(request, response)
                
    async def _get_popular_requests(self):
        # Analyze request patterns from logs
        return [
            "Create a Python function",
            "Explain this code",
            "Find bugs in this code"
        ]
```

### Cache Invalidation

#### Smart Invalidation
```python
# Intelligent cache invalidation
class SmartInvalidator:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        
    async def invalidate_related(self, changed_file: str):
        # Invalidate caches related to changed files
        patterns = [
            f"analysis:{changed_file}:*",
            f"generation:*:{changed_file}",
            f"explanation:{changed_file}:*"
        ]
        
        for pattern in patterns:
            await self.cache_manager.invalidate_pattern(pattern)
            
    async def schedule_cleanup(self):
        # Periodic cleanup of stale cache entries
        await self.cache_manager.cleanup_expired()
        await self.cache_manager.optimize_storage()
```

## Network Optimization

### HTTP/2 Configuration

#### Server Configuration
```python
# HTTP/2 with FastAPI
from fastapi import FastAPI
import uvicorn

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        http="h2",  # Enable HTTP/2
        loop="uvloop",
        workers=4,
        access_log=False,  # Disable for performance
        server_header=False
    )
```

#### Client Optimization
```python
# Optimized HTTP client
import httpx
import asyncio

class OptimizedHTTPClient:
    def __init__(self):
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30
        )
        
        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=httpx.Timeout(30.0),
            http2=True
        )
        
    async def make_request(self, url, data):
        async with self.client.stream("POST", url, json=data) as response:
            # Stream large responses
            content = b""
            async for chunk in response.aiter_bytes(8192):
                content += chunk
            return content
```

### Connection Pooling

#### GitHub API Optimization
```python
# Optimized GitHub API client
class GitHubAPIClient:
    def __init__(self, token: str):
        self.session = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            },
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=50
            )
        )
        
    async def batch_requests(self, requests):
        # Process multiple requests concurrently
        semaphore = asyncio.Semaphore(10)
        
        async def limited_request(req):
            async with semaphore:
                return await self.session.request(**req)
                
        results = await asyncio.gather(
            *[limited_request(req) for req in requests],
            return_exceptions=True
        )
        
        return results
```

## Resource Management

### CPU Optimization

#### Process Affinity
```python
# CPU affinity for better performance
import os
import psutil

def optimize_cpu_affinity():
    # Get available CPUs
    cpu_count = os.cpu_count()
    
    # Set CPU affinity to use specific cores
    if cpu_count >= 4:
        # Use cores 0-3 for main process
        os.sched_setaffinity(0, {0, 1, 2, 3})
        
    # Set process priority
    proc = psutil.Process()
    proc.nice(-5)  # Higher priority (requires privileges)
```

#### Thread Pool Optimization
```python
# Optimized thread pool usage
from concurrent.futures import ThreadPoolExecutor
import asyncio

class OptimizedExecutor:
    def __init__(self):
        # Optimize thread pool size based on workload
        cpu_count = os.cpu_count()
        self.io_executor = ThreadPoolExecutor(
            max_workers=min(32, cpu_count * 4),
            thread_name_prefix="aurelis-io"
        )
        self.cpu_executor = ThreadPoolExecutor(
            max_workers=cpu_count,
            thread_name_prefix="aurelis-cpu"
        )
        
    async def run_io_task(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.io_executor, func, *args)
        
    async def run_cpu_task(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.cpu_executor, func, *args)
```

### Memory Optimization

#### Memory Monitoring
```python
# Memory usage monitoring
import psutil
import gc
from pympler import tracker

class MemoryMonitor:
    def __init__(self):
        self.tracker = tracker.SummaryTracker()
        
    def check_memory_usage(self):
        process = psutil.Process()
        memory_info = process.memory_info()
        
        stats = {
            "rss": memory_info.rss / 1024 / 1024,  # MB
            "vms": memory_info.vms / 1024 / 1024,  # MB
            "percent": process.memory_percent(),
            "available": psutil.virtual_memory().available / 1024 / 1024
        }
        
        return stats
        
    def force_gc(self):
        # Force garbage collection
        collected = gc.collect()
        return collected
        
    def get_memory_diff(self):
        # Track memory changes
        return self.tracker.diff()
```

#### Memory Pool Management
```python
# Custom memory pool for frequent allocations
class MemoryPool:
    def __init__(self, block_size=4096, pool_size=100):
        self.block_size = block_size
        self.pool = [bytearray(block_size) for _ in range(pool_size)]
        self.available = list(range(pool_size))
        
    def acquire(self):
        if self.available:
            index = self.available.pop()
            return self.pool[index]
        else:
            # Pool exhausted, allocate new block
            return bytearray(self.block_size)
            
    def release(self, block):
        # Find the block in pool and mark as available
        try:
            index = self.pool.index(block)
            if index not in self.available:
                self.available.append(index)
        except ValueError:
            # Block not from pool, nothing to do
            pass
```

## Monitoring & Profiling

### Performance Metrics

#### Application Metrics
```python
# Custom metrics collection
import time
from collections import defaultdict
import asyncio

class PerformanceMetrics:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        
    def time_function(self, func_name):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    self.counters[f"{func_name}_success"] += 1
                    return result
                except Exception as e:
                    self.counters[f"{func_name}_error"] += 1
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    self.metrics[f"{func_name}_duration"].append(duration)
            return wrapper
        return decorator
        
    def get_stats(self):
        stats = {}
        for metric, values in self.metrics.items():
            if values:
                stats[metric] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "p95": sorted(values)[int(len(values) * 0.95)]
                }
        return {**stats, **dict(self.counters)}
```

#### Prometheus Integration
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
REQUEST_COUNT = Counter('aurelis_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('aurelis_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('aurelis_active_connections', 'Active connections')
MODEL_LATENCY = Histogram('aurelis_model_latency_seconds', 'Model response time', ['model'])

class MetricsCollector:
    def __init__(self):
        start_http_server(8001)  # Metrics endpoint
        
    def record_request(self, method, endpoint, duration):
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_DURATION.observe(duration)
        
    def record_model_latency(self, model, latency):
        MODEL_LATENCY.labels(model=model).observe(latency)
        
    def set_active_connections(self, count):
        ACTIVE_CONNECTIONS.set(count)
```

### Profiling Tools

#### Code Profiling
```python
# Performance profiling
import cProfile
import pstats
from contextlib import contextmanager

@contextmanager
def profile_code(sort_by='cumulative'):
    pr = cProfile.Profile()
    pr.enable()
    try:
        yield
    finally:
        pr.disable()
        stats = pstats.Stats(pr)
        stats.sort_stats(sort_by)
        stats.print_stats(20)  # Top 20 functions
```

#### Memory Profiling
```python
# Memory profiling with py-spy
import subprocess
import os

def profile_memory(duration=60):
    pid = os.getpid()
    cmd = [
        "py-spy", "record",
        "-o", "profile.svg",
        "-d", str(duration),
        "-p", str(pid)
    ]
    subprocess.run(cmd)
```

## Load Testing

### Test Scenarios

#### Stress Testing
```python
# Load testing with locust
from locust import HttpUser, task, between

class AurelisUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Authentication
        self.client.headers.update({
            "Authorization": "Bearer test_token"
        })
    
    @task(3)
    def analyze_code(self):
        payload = {
            "code": "def hello(): return 'world'",
            "language": "python"
        }
        self.client.post("/api/v1/analyze", json=payload)
    
    @task(2)
    def generate_code(self):
        payload = {
            "prompt": "Create a function",
            "language": "python"
        }
        self.client.post("/api/v1/generate", json=payload)
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
```

#### Performance Benchmarks
```bash
# Run load tests
locust -f load_test.py --host=http://localhost:8000 --users=100 --spawn-rate=10

# Apache Bench for simple testing
ab -n 1000 -c 10 -H "Authorization: Bearer token" http://localhost:8000/health

# wrk for advanced testing
wrk -t12 -c400 -d30s --latency http://localhost:8000/api/v1/health
```

## Configuration Optimization

### Environment Variables
```bash
# Performance-optimized environment
export PYTHONOPTIMIZE=2
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# Memory optimization
export MALLOC_ARENA_MAX=2
export MALLOC_MMAP_THRESHOLD_=65536

# Async optimization
export PYTHONASYNCIODEBUG=0
export PYTHONHASHSEED=random

# Application tuning
export AURELIS_WORKERS=4
export AURELIS_MAX_REQUESTS=1000
export AURELIS_CACHE_SIZE=10000
export AURELIS_BATCH_SIZE=5
```

### Production Settings
```yaml
# production.yaml
server:
  workers: 4
  max_requests: 1000
  keepalive: 2
  max_connections: 1000
  
cache:
  size: 10000
  ttl: 3600
  compression: true
  
database:
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  
monitoring:
  metrics_enabled: true
  profiling_enabled: false
  log_level: "INFO"
```

## Best Practices

### Performance Guidelines

1. **Async/Await**: Use async/await for I/O operations
2. **Batching**: Batch similar requests together
3. **Caching**: Implement multi-level caching
4. **Connection Pooling**: Reuse connections
5. **Resource Limits**: Set appropriate limits
6. **Monitoring**: Continuously monitor performance

### Optimization Checklist

- [ ] Enable HTTP/2
- [ ] Configure connection pooling
- [ ] Implement caching strategy
- [ ] Optimize database queries
- [ ] Set up monitoring
- [ ] Profile critical paths
- [ ] Load test before deployment
- [ ] Monitor resource usage

## Troubleshooting

### Common Performance Issues

#### High Memory Usage
```python
# Debug memory leaks
import tracemalloc

tracemalloc.start()

# Your application code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

#### Slow Response Times
```python
# Profile slow requests
import asyncio
import time

async def profile_request(request_func):
    start = time.perf_counter()
    
    # Add timing checkpoints
    checkpoint_times = {}
    
    # Database query
    db_start = time.perf_counter()
    await database_operation()
    checkpoint_times['database'] = time.perf_counter() - db_start
    
    # Model inference
    model_start = time.perf_counter()
    await model_operation()
    checkpoint_times['model'] = time.perf_counter() - model_start
    
    total_time = time.perf_counter() - start
    
    print(f"Total time: {total_time:.3f}s")
    for checkpoint, duration in checkpoint_times.items():
        print(f"{checkpoint}: {duration:.3f}s ({duration/total_time*100:.1f}%)")
```

## References

- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/manually/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Performance Best Practices](https://redis.io/topics/memory-optimization)

## Next Steps

1. Implement [Monitoring](monitoring.md) for performance tracking
2. Review [Security](security.md) considerations for optimizations
3. Check [Production Deployment](production-deployment.md) for performance settings
4. Set up [Container Deployment](container-deployment.md) with resource limits
