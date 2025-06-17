"""Logging system for Aurelis with structured logging and audit trails."""

import json
import logging
import logging.handlers
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from aurelis.core.config import get_config


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if present
        if hasattr(record, 'correlation_id'):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add session ID if present
        if hasattr(record, 'session_id'):
            log_entry["session_id"] = record.session_id
        
        # Add user ID if present
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_entry["extra"] = record.extra
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class AuditLogger:
    """Specialized logger for audit events."""
    
    def __init__(self, log_dir: Path):
        self.logger = logging.getLogger("aurelis.audit")
        self.logger.setLevel(logging.INFO)
        
        # Create audit log file handler
        audit_file = log_dir / "audit.log"
        handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def log_command_execution(
        self,
        command: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log command execution for audit trail."""
        event = {
            "event_type": "command_execution",
            "command": command,
            "success": success,
            "metadata": metadata or {}
        }
        
        if error_message:
            event["error_message"] = error_message
        
        extra = {"extra": event}
        if user_id:
            extra["user_id"] = user_id
        if session_id:
            extra["session_id"] = session_id
        
        self.logger.info("Command executed", extra=extra)
    
    def log_file_access(
        self,
        file_path: str,
        operation: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log file access for audit trail."""
        event = {
            "event_type": "file_access",
            "file_path": file_path,
            "operation": operation,
            "success": success,
            "metadata": metadata or {}
        }
        
        extra = {"extra": event}
        if user_id:
            extra["user_id"] = user_id
        if session_id:
            extra["session_id"] = session_id
        
        self.logger.info("File accessed", extra=extra)
    
    def log_model_request(
        self,
        model_type: str,
        task_type: str,
        token_usage: Dict[str, int],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log AI model requests for audit trail."""
        event = {
            "event_type": "model_request",
            "model_type": model_type,
            "task_type": task_type,
            "token_usage": token_usage,
            "success": success,
            "metadata": metadata or {}
        }
        
        extra = {"extra": event}
        if user_id:
            extra["user_id"] = user_id
        if session_id:
            extra["session_id"] = session_id
        
        self.logger.info("Model request", extra=extra)


class LoggerManager:
    """Centralized logging management for Aurelis."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".aurelis" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_root_logger()
        self._setup_audit_logger()
        self._correlation_id: Optional[str] = None
    
    def _setup_root_logger(self) -> None:
        """Setup the root logger for the application."""
        root_logger = logging.getLogger("aurelis")
        root_logger.setLevel(logging.INFO)
        
        # Console handler with colored output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with structured logging
        log_file = self.log_dir / "aurelis.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_file = self.log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)
    
    def _setup_audit_logger(self) -> None:
        """Setup the audit logger."""
        config = get_config()
        if config.audit_logging:
            self.audit_logger = AuditLogger(self.log_dir)
        else:
            self.audit_logger = None
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with the given name."""
        logger = logging.getLogger(f"aurelis.{name}")
        
        # Add correlation ID if available
        if self._correlation_id:
            logger = logging.LoggerAdapter(logger, {"correlation_id": self._correlation_id})
        
        return logger
    
    def set_correlation_id(self, correlation_id: Optional[str] = None) -> str:
        """Set correlation ID for request tracing."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        self._correlation_id = correlation_id
        return correlation_id
    
    def clear_correlation_id(self) -> None:
        """Clear the current correlation ID."""
        self._correlation_id = None
    
    def get_audit_logger(self) -> Optional[AuditLogger]:
        """Get the audit logger instance."""
        return self.audit_logger
    
    def set_log_level(self, level: str) -> None:
        """Set the log level for all loggers."""
        log_level = getattr(logging, level.upper())
        logging.getLogger("aurelis").setLevel(log_level)
    
    def cleanup_old_logs(self, days: int = 30) -> None:
        """Clean up log files older than specified days."""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                except OSError:
                    pass  # File might be in use


# Global logger manager instance
_logger_manager: Optional[LoggerManager] = None


def get_logger_manager() -> LoggerManager:
    """Get the global logger manager instance."""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return get_logger_manager().get_logger(name)


def get_audit_logger() -> Optional[AuditLogger]:
    """Get the audit logger instance."""
    return get_logger_manager().get_audit_logger()


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for request tracing."""
    return get_logger_manager().set_correlation_id(correlation_id)


def clear_correlation_id() -> None:
    """Clear the current correlation ID."""
    get_logger_manager().clear_correlation_id()


def initialize_logging(log_dir: Optional[Path] = None) -> LoggerManager:
    """Initialize the global logging system."""
    global _logger_manager
    _logger_manager = LoggerManager(log_dir)
    return _logger_manager
