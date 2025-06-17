"""Caching system for Aurelis with LRU and TTL support."""

import asyncio
import hashlib
import json
import pickle
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import OrderedDict

from aurelis.core.config import get_config
from aurelis.core.logging import get_logger
from aurelis.core.exceptions import CacheError


class LRUCache:
    """Thread-safe LRU cache with TTL support."""
    
    def __init__(self, max_size: int, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        self.logger = get_logger("cache.lru")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, timestamp = self._cache[key]
            
            # Check TTL
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self._lock:
            current_time = time.time()
            
            if key in self._cache:
                # Update existing key
                self._cache[key] = (value, current_time)
                self._cache.move_to_end(key)
            else:
                # Add new key
                if len(self._cache) >= self.max_size:
                    # Remove least recently used item
                    self._cache.popitem(last=False)
                
                self._cache[key] = (value, current_time)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired items and return count of removed items."""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, (_, timestamp) in self._cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "keys": list(self._cache.keys())
            }


class PersistentCache:
    """Persistent file-based cache with compression."""
    
    def __init__(self, cache_dir: Path, max_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.logger = get_logger("cache.persistent")
        self._lock = threading.RLock()
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _get_metadata_file(self, key: str) -> Path:
        """Get metadata file path for key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.meta"
    
    def get(self, key: str, ttl_seconds: int = 3600) -> Optional[Any]:
        """Get value from persistent cache."""
        with self._lock:
            cache_file = self._get_cache_file(key)
            metadata_file = self._get_metadata_file(key)
            
            if not cache_file.exists() or not metadata_file.exists():
                return None
            
            try:
                # Check TTL
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                created_time = datetime.fromisoformat(metadata['created_at'])
                if datetime.now() - created_time > timedelta(seconds=ttl_seconds):
                    self.delete(key)
                    return None
                
                # Load data
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
                    
            except Exception as e:
                self.logger.error(f"Failed to load cache for key {key}: {e}")
                self.delete(key)
                return None
    
    def set(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Set value in persistent cache."""
        with self._lock:
            cache_file = self._get_cache_file(key)
            metadata_file = self._get_metadata_file(key)
            
            try:
                # Save data
                with open(cache_file, 'wb') as f:
                    pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
                
                # Save metadata
                cache_metadata = {
                    'key': key,
                    'created_at': datetime.now().isoformat(),
                    'size_bytes': cache_file.stat().st_size,
                    'metadata': metadata or {}
                }
                
                with open(metadata_file, 'w') as f:
                    json.dump(cache_metadata, f)
                
                # Cleanup if cache is too large
                self._cleanup_if_needed()
                
            except Exception as e:
                self.logger.error(f"Failed to save cache for key {key}: {e}")
                # Clean up partial files
                for file_path in [cache_file, metadata_file]:
                    if file_path.exists():
                        try:
                            file_path.unlink()
                        except OSError:
                            pass
                raise CacheError(f"Failed to save cache: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete key from persistent cache."""
        with self._lock:
            cache_file = self._get_cache_file(key)
            metadata_file = self._get_metadata_file(key)
            
            deleted = False
            for file_path in [cache_file, metadata_file]:
                if file_path.exists():
                    try:
                        file_path.unlink()
                        deleted = True
                    except OSError:
                        pass
            
            return deleted
    
    def clear(self) -> None:
        """Clear all items from persistent cache."""
        with self._lock:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except OSError:
                    pass
            
            for metadata_file in self.cache_dir.glob("*.meta"):
                try:
                    metadata_file.unlink()
                except OSError:
                    pass
    
    def _cleanup_if_needed(self) -> None:
        """Clean up cache if it exceeds size limit."""
        total_size = self._get_total_size()
        
        if total_size <= self.max_size_bytes:
            return
        
        # Get all cache files with their creation times
        cache_items = []
        for metadata_file in self.cache_dir.glob("*.meta"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                cache_items.append({
                    'key': metadata['key'],
                    'created_at': datetime.fromisoformat(metadata['created_at']),
                    'size_bytes': metadata['size_bytes']
                })
            except Exception:
                continue
        
        # Sort by creation time (oldest first)
        cache_items.sort(key=lambda x: x['created_at'])
        
        # Remove items until under size limit
        for item in cache_items:
            if total_size <= self.max_size_bytes:
                break
            
            self.delete(item['key'])
            total_size -= item['size_bytes']
    
    def _get_total_size(self) -> int:
        """Get total size of cache in bytes."""
        total_size = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                total_size += cache_file.stat().st_size
            except OSError:
                pass
        return total_size
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = self._get_total_size()
            
            return {
                "item_count": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "max_size_mb": self.max_size_bytes // (1024 * 1024),
                "utilization": round(total_size / self.max_size_bytes * 100, 2)
            }


class CacheManager:
    """Central cache management for Aurelis."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.logger = get_logger("cache")
        self.config = get_config()
        
        # Initialize caches
        self.cache_dir = cache_dir or Path.home() / ".aurelis" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory caches
        self.context_cache = LRUCache(max_size=1000, ttl_seconds=self.config.cache_ttl)
        self.model_response_cache = LRUCache(max_size=500, ttl_seconds=self.config.cache_ttl)
        self.tool_result_cache = LRUCache(max_size=200, ttl_seconds=self.config.cache_ttl)
        
        # Persistent caches
        self.ast_cache = PersistentCache(
            self.cache_dir / "ast",
            max_size_mb=self.config.max_cache_size // (1024 * 1024) // 4
        )
        self.analysis_cache = PersistentCache(
            self.cache_dir / "analysis",
            max_size_mb=self.config.max_cache_size // (1024 * 1024) // 2
        )
        
        # Cleanup task reference (will be started when needed)
        self._cleanup_task = None
        self._cleanup_running = False
    
    def start_cleanup_task(self) -> None:
        """Start periodic cleanup task if event loop is available."""
        try:
            if not self._cleanup_running:
                loop = asyncio.get_running_loop()
                self._cleanup_task = loop.create_task(self._periodic_cleanup())
                self._cleanup_running = True
        except RuntimeError:
            # No event loop running, cleanup will be done manually
            self.logger.debug("No event loop available for cleanup task")
    
    def stop_cleanup_task(self) -> None:
        """Stop periodic cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        self._cleanup_running = False
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired cache entries."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Cleanup memory caches
                expired_count = 0
                expired_count += self.context_cache.cleanup_expired()
                expired_count += self.model_response_cache.cleanup_expired()
                expired_count += self.tool_result_cache.cleanup_expired()
                
                if expired_count > 0:
                    self.logger.debug(f"Cleaned up {expired_count} expired cache entries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")
    
    def manual_cleanup(self) -> int:
        """Perform manual cleanup of expired cache entries."""
        expired_count = 0
        try:
            expired_count += self.context_cache.cleanup_expired()
            expired_count += self.model_response_cache.cleanup_expired()
            expired_count += self.tool_result_cache.cleanup_expired()
            
            if expired_count > 0:
                self.logger.debug(f"Manually cleaned up {expired_count} expired cache entries")
        except Exception as e:
            self.logger.error(f"Manual cache cleanup error: {e}")
        
        return expired_count
    
    def get_context_cache_key(self, file_path: str, chunk_id: str) -> str:
        """Generate cache key for code context."""
        return f"context:{file_path}:{chunk_id}"
    
    def get_model_response_cache_key(self, model_type: str, prompt_hash: str) -> str:
        """Generate cache key for model response."""
        return f"model:{model_type}:{prompt_hash}"
    
    def get_tool_result_cache_key(self, tool_name: str, params_hash: str) -> str:
        """Generate cache key for tool result."""
        return f"tool:{tool_name}:{params_hash}"
    
    def get_ast_cache_key(self, file_path: str, file_mtime: float) -> str:
        """Generate cache key for AST."""
        return f"ast:{file_path}:{file_mtime}"
    
    def get_analysis_cache_key(self, file_path: str, analysis_type: str, file_mtime: float) -> str:
        """Generate cache key for analysis result."""
        return f"analysis:{file_path}:{analysis_type}:{file_mtime}"
    
    def hash_content(self, content: str) -> str:
        """Generate hash for content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def cache_context(self, key: str, context: Any) -> None:
        """Cache code context."""
        if self.config.cache_enabled:
            self.context_cache.set(key, context)
    
    def get_cached_context(self, key: str) -> Optional[Any]:
        """Get cached code context."""
        if self.config.cache_enabled:
            return self.context_cache.get(key)
        return None
    
    def cache_model_response(self, key: str, response: Any) -> None:
        """Cache model response."""
        if self.config.cache_enabled:
            self.model_response_cache.set(key, response)
    
    def get_cached_model_response(self, key: str) -> Optional[Any]:
        """Get cached model response."""
        if self.config.cache_enabled:
            return self.model_response_cache.get(key)
        return None
    
    def cache_tool_result(self, key: str, result: Any) -> None:
        """Cache tool result."""
        if self.config.cache_enabled:
            self.tool_result_cache.set(key, result)
    
    def get_cached_tool_result(self, key: str) -> Optional[Any]:
        """Get cached tool result."""
        if self.config.cache_enabled:
            return self.tool_result_cache.get(key)
        return None
    
    def cache_ast(self, key: str, ast_data: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Cache AST data."""
        if self.config.cache_enabled:
            self.ast_cache.set(key, ast_data, metadata)
    
    def get_cached_ast(self, key: str) -> Optional[Any]:
        """Get cached AST data."""
        if self.config.cache_enabled:
            return self.ast_cache.get(key, ttl_seconds=self.config.cache_ttl)
        return None
    
    def cache_analysis(self, key: str, analysis_result: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Cache analysis result."""
        if self.config.cache_enabled:
            self.analysis_cache.set(key, analysis_result, metadata)
    
    def get_cached_analysis(self, key: str) -> Optional[Any]:
        """Get cached analysis result."""
        if self.config.cache_enabled:
            return self.analysis_cache.get(key, ttl_seconds=self.config.cache_ttl)
        return None
    
    def invalidate_file_caches(self, file_path: str) -> None:
        """Invalidate all caches related to a file."""
        # This is a simplified invalidation - in production, you'd want more sophisticated cache invalidation
        prefix = f"context:{file_path}:"
        
        # Clear related context cache entries
        for key in list(self.context_cache._cache.keys()):
            if key.startswith(prefix):
                self.context_cache.delete(key)
    
    def clear_all_caches(self) -> None:
        """Clear all cache stores."""
        self.context_cache.clear()
        self.model_response_cache.clear()
        self.tool_result_cache.clear()
        self.ast_cache.clear()
        self.analysis_cache.clear()
        
        self.logger.info("All caches cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            "context_cache": self.context_cache.get_stats(),
            "model_response_cache": self.model_response_cache.get_stats(),
            "tool_result_cache": self.tool_result_cache.get_stats(),
            "ast_cache": self.ast_cache.get_stats(),
            "analysis_cache": self.analysis_cache.get_stats(),
            "cache_enabled": self.config.cache_enabled,
            "cache_ttl": self.config.cache_ttl
        }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def initialize_cache(cache_dir: Optional[Path] = None) -> CacheManager:
    """Initialize the global cache manager."""
    global _cache_manager
    _cache_manager = CacheManager(cache_dir)
    return _cache_manager
