# Logging API Reference

The Logging API provides comprehensive logging capabilities for the Aurelis platform, including structured logging, multiple output formats, log aggregation, and integration with monitoring systems.

## Overview

The Aurelis logging system offers:
- Structured JSON logging with contextual information
- Multiple log levels and filtering
- Configurable output destinations (console, file, remote)
- Performance metrics and tracing
- Integration with monitoring and alerting systems
- Privacy-aware logging with data sanitization

## Core Functions

### get_logger(name: str) -> Logger

Creates or retrieves a logger instance for a specific module or component.

**Parameters:**
- `name` (str): Logger name, typically `__name__` for module-level logging

**Returns:**
- `Logger`: Configured logger instance

**Example:**
```python
from aurelis.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Application started", extra={"version": "1.0.0"})
```

### configure_logging(config: LoggingConfig) -> None

Configures the global logging system.

**Parameters:**
- `config` (LoggingConfig): Logging configuration object

## Logger Methods

### Standard Log Levels

```python
logger.debug("Debug message", extra={"context": "development"})
logger.info("Information message", extra={"user_id": "12345"})
logger.warning("Warning message", extra={"resource": "database"})
logger.error("Error occurred", extra={"error_code": "DB001"}, exc_info=True)
logger.critical("Critical system failure", extra={"system": "auth"})
```

### Structured Logging

```python
# Log with structured data
logger.info("User action completed", extra={
    "user_id": "user123",
    "action": "file_analysis",
    "file_path": "/path/to/file.py",
    "duration_ms": 1250,
    "status": "success"
})

# Log with correlation ID for tracing
logger.info("Processing request", extra={
    "correlation_id": "req-456",
    "endpoint": "/api/analyze",
    "method": "POST"
})
```

### Performance Logging

```python
import time
from aurelis.core.logging import get_logger, log_performance

logger = get_logger(__name__)

@log_performance
async def analyze_code(file_path: str):
    """Function decorator for automatic performance logging."""
    # Implementation here
    pass

# Manual performance logging
start_time = time.time()
result = await some_operation()
duration = time.time() - start_time

logger.info("Operation completed", extra={
    "operation": "code_analysis",
    "duration_seconds": duration,
    "result_count": len(result)
})
```

## Configuration

### LoggingConfig

```python
from aurelis.core.logging import LoggingConfig

config = LoggingConfig(
    level="INFO",
    format="json",  # "json" or "text"
    outputs=["console", "file"],
    file_config={
        "path": "./logs/aurelis.log",
        "max_size": "10MB",
        "backup_count": 5,
        "rotation": "time"  # "time" or "size"
    },
    structured_logging=True,
    include_correlation_id=True,
    sanitize_data=True
)
```

### Environment Configuration

```yaml
logging:
  level: INFO
  format: json
  outputs:
    - console
    - file
    - elasticsearch
  
  console:
    colored: true
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  file:
    path: "./logs/aurelis.log"
    max_size: "10MB"
    backup_count: 5
    rotation: "time"
    interval: "midnight"
  
  elasticsearch:
    hosts: ["elasticsearch:9200"]
    index_pattern: "aurelis-logs-%Y.%m.%d"
    timeout: 30
  
  filters:
    - name: "sensitive_data"
      patterns: ["password", "token", "api_key"]
      replacement: "[REDACTED]"
```

## Log Formats

### JSON Format

```json
{
  "timestamp": "2023-12-07T10:30:45.123Z",
  "level": "INFO",
  "logger": "aurelis.models.orchestrator",
  "message": "Model request processed",
  "correlation_id": "req-789",
  "user_id": "user123",
  "model_type": "gpt-4o",
  "processing_time_ms": 1500,
  "tokens_used": 150,
  "success": true
}
```

### Text Format

```
2023-12-07 10:30:45,123 - aurelis.models.orchestrator - INFO - Model request processed [correlation_id=req-789 user_id=user123 model_type=gpt-4o processing_time_ms=1500]
```

## Contextual Logging

### Request Context

```python
from aurelis.core.logging import LogContext, get_logger

logger = get_logger(__name__)

# Set request context
with LogContext(correlation_id="req-123", user_id="user456"):
    logger.info("Processing user request")
    
    # All logs within this context will include correlation_id and user_id
    await process_request()
    
    logger.info("Request completed")
```

### Session Context

```python
# Set session-level context
with LogContext(session_id="sess-789", workspace="/project/path"):
    logger.info("Session started")
    
    # Nested contexts merge
    with LogContext(operation="file_analysis"):
        logger.info("Starting file analysis")
        # Logs will include session_id, workspace, and operation
```

## Integration Examples

### Model Orchestrator Logging

```python
from aurelis.core.logging import get_logger, log_performance

class ModelOrchestrator:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    @log_performance
    async def process_request(self, request: ModelRequest) -> ModelResponse:
        self.logger.info("Processing model request", extra={
            "task_type": request.task_type.value,
            "model": request.preferred_model.value if request.preferred_model else None,
            "content_length": len(request.content)
        })
        
        try:
            # Select model
            model = await self._select_model(request)
            self.logger.debug("Model selected", extra={"selected_model": model.value})
            
            # Process request
            response = await self._execute_request(model, request)
            
            self.logger.info("Request completed successfully", extra={
                "model_used": model.value,
                "response_length": len(response.content),
                "processing_time": response.processing_time,
                "tokens_used": response.token_usage
            })
            
            return response
            
        except Exception as e:
            self.logger.error("Request processing failed", extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "task_type": request.task_type.value
            }, exc_info=True)
            raise
```

### Shell Command Logging

```python
from aurelis.core.logging import get_logger

class ShellCommand:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def execute(self, command: str, args: List[str]):
        with LogContext(command=command, args=args):
            self.logger.info("Executing shell command")
            
            start_time = time.time()
            try:
                result = await self._execute_command(command, args)
                duration = time.time() - start_time
                
                self.logger.info("Command completed", extra={
                    "success": result.success,
                    "duration_seconds": duration,
                    "output_length": len(result.output)
                })
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                self.logger.error("Command failed", extra={
                    "duration_seconds": duration,
                    "error": str(e)
                }, exc_info=True)
                raise
```

### Analysis Logging

```python
from aurelis.core.logging import get_logger

class CodeAnalyzer:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def analyze_file(self, file_path: Path) -> AnalysisResult:
        with LogContext(file_path=str(file_path)):
            self.logger.info("Starting file analysis")
            
            try:
                # Check file
                file_size = file_path.stat().st_size
                self.logger.debug("File info", extra={
                    "file_size": file_size,
                    "file_extension": file_path.suffix
                })
                
                # Perform analysis
                result = await self._analyze(file_path)
                
                self.logger.info("Analysis completed", extra={
                    "issues_found": len(result.issues),
                    "critical_issues": len([i for i in result.issues if i.severity == ErrorSeverity.CRITICAL]),
                    "processing_time": result.processing_time,
                    "confidence": result.confidence
                })
                
                # Log issues summary
                if result.issues:
                    severity_counts = {}
                    for issue in result.issues:
                        severity_counts[issue.severity.value] = severity_counts.get(issue.severity.value, 0) + 1
                    
                    self.logger.info("Issues by severity", extra=severity_counts)
                
                return result
                
            except Exception as e:
                self.logger.error("Analysis failed", extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }, exc_info=True)
                raise
```

## Security and Privacy

### Data Sanitization

```python
from aurelis.core.logging import sanitize_log_data

# Automatic sanitization of sensitive fields
user_data = {
    "username": "john_doe",
    "password": "secret123",
    "api_key": "sk-1234567890",
    "email": "john@example.com"
}

# Sanitized automatically when logging
logger.info("User login", extra=user_data)
# Output: {"username": "john_doe", "password": "[REDACTED]", "api_key": "[REDACTED]", "email": "john@example.com"}

# Manual sanitization
sanitized_data = sanitize_log_data(user_data)
logger.info("User data", extra=sanitized_data)
```

### Custom Sanitization Rules

```python
from aurelis.core.logging import add_sanitization_rule

# Add custom sanitization pattern
add_sanitization_rule(
    name="credit_card",
    pattern=r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    replacement="[CARD-REDACTED]"
)

add_sanitization_rule(
    name="github_token",
    pattern=r'ghp_[a-zA-Z0-9]{36}',
    replacement="[GITHUB-TOKEN-REDACTED]"
)
```

## Monitoring Integration

### Metrics Collection

```python
from aurelis.core.logging import MetricsLogger

metrics = MetricsLogger()

# Log metrics
metrics.counter("requests_total", {"endpoint": "/analyze", "method": "POST"})
metrics.histogram("request_duration", 1.5, {"endpoint": "/analyze"})
metrics.gauge("active_sessions", 42)

# Automatic metrics from decorators
@metrics.time_execution("code_analysis_duration")
async def analyze_code(file_path: str):
    # Function implementation
    pass
```

### Health Check Logging

```python
from aurelis.core.logging import HealthLogger

health = HealthLogger()

# Log component health
health.check("database", status="healthy", response_time=0.05)
health.check("model_api", status="degraded", response_time=2.1, error="high_latency")
health.check("file_system", status="healthy", disk_usage=0.75)
```

### Alerting Integration

```python
from aurelis.core.logging import AlertLogger

alert = AlertLogger()

# Critical alerts
alert.critical("Model API down", {
    "service": "github_models",
    "last_success": "2023-12-07T09:30:00Z",
    "error_count": 15
})

# Warning alerts
alert.warning("High error rate", {
    "service": "code_analyzer", 
    "error_rate": 0.15,
    "threshold": 0.10
})
```

## Performance Optimization

### Asynchronous Logging

```python
from aurelis.core.logging import AsyncLogger

# Non-blocking logging for high-throughput applications
async_logger = AsyncLogger()

# Logs are queued and processed asynchronously
await async_logger.info("High frequency event", extra={"event_id": "evt123"})
```

### Log Sampling

```python
from aurelius.core.logging import SampledLogger

# Sample debug logs to reduce volume
sampled_logger = SampledLogger(sample_rate=0.1)  # Log 10% of debug messages

for i in range(1000):
    sampled_logger.debug(f"Debug message {i}")  # Only ~100 will be logged
```

### Batch Logging

```python
from aurelis.core.logging import BatchLogger

batch_logger = BatchLogger(batch_size=100, flush_interval=5.0)

# Logs are batched and sent in groups
for event in events:
    batch_logger.info("Event processed", extra={"event_id": event.id})

# Manually flush if needed
await batch_logger.flush()
```

## Error Handling

```python
from aurelis.core.logging.exceptions import (
    LoggingConfigError,
    LogFormatError,
    LogDestinationError
)

try:
    configure_logging(config)
except LoggingConfigError as e:
    print(f"Invalid logging configuration: {e}")
except LogDestinationError as e:
    print(f"Cannot write to log destination: {e}")
```

## Best Practices

1. **Structured Logging**: Always use structured data for better searchability
2. **Context Management**: Use log contexts for request/session correlation
3. **Performance Logging**: Log execution times for performance monitoring
4. **Error Logging**: Include stack traces for error debugging
5. **Data Privacy**: Sanitize sensitive information automatically
6. **Log Levels**: Use appropriate log levels for different information types
7. **Monitoring Integration**: Connect logs to metrics and alerts
8. **Log Rotation**: Configure proper log rotation to manage disk space

For advanced logging patterns and enterprise integrations, refer to the main Aurelis documentation.
