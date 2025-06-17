"""Core exception classes for Aurelis."""

from typing import Any, Dict, Optional


class AurelisError(Exception):
    """Base exception class for all Aurelis errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}


class ConfigurationError(AurelisError):
    """Raised when there's an issue with configuration."""
    pass


class ModelError(AurelisError):
    """Raised when there's an issue with AI model operations."""
    pass


class AnalysisError(AurelisError):
    """Raised when code analysis fails."""
    pass


class ChunkingError(AurelisError):
    """Raised when code chunking fails."""
    pass


class ToolError(AurelisError):
    """Raised when tool execution fails."""
    pass


class SecurityError(AurelisError):
    """Raised when security validation fails."""
    pass


class CacheError(AurelisError):
    """Raised when cache operations fail."""
    pass


class ValidationError(AurelisError):
    """Raised when input validation fails."""
    pass
