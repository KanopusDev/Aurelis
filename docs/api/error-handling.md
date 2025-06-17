# Error Handling API Reference

The Error Handling API provides comprehensive error management for the Aurelis platform, including custom exception types, error recovery strategies, and integration with logging and monitoring systems.

## Overview

Aurelis error handling provides:
- Custom exception hierarchy for specific error types
- Automatic error recovery and retry mechanisms
- Detailed error context and debugging information
- Integration with logging and monitoring systems
- User-friendly error messages and suggestions
- Graceful degradation for non-critical failures

## Exception Hierarchy

### Base Exceptions

#### AurelisError
Base exception for all Aurelis-specific errors.

```python
class AurelisError(Exception):
    """Base exception for Aurelis platform."""
    
    def __init__(self, message: str, error_code: str = None, context: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.timestamp = datetime.now()
```

#### AurelisWarning
Base warning for non-fatal issues.

```python
class AurelisWarning(UserWarning):
    """Base warning for Aurelis platform."""
    pass
```

### Model and AI Exceptions

#### ModelError
Base exception for model-related errors.

```python
class ModelError(AurelisError):
    """Base exception for model operations."""
    pass

class ModelNotAvailableError(ModelError):
    """Raised when a requested model is not available."""
    pass

class ModelTimeoutError(ModelError):
    """Raised when model request times out."""
    pass

class ModelQuotaExceededError(ModelError):
    """Raised when model usage quota is exceeded."""
    pass

class InvalidModelRequestError(ModelError):
    """Raised when model request is invalid."""
    pass
```

### Analysis Exceptions

#### AnalysisError
Base exception for code analysis errors.

```python
class AnalysisError(AurelisError):
    """Base exception for analysis operations."""
    pass

class UnsupportedLanguageError(AnalysisError):
    """Raised when language is not supported for analysis."""
    pass

class AnalysisTimeoutError(AnalysisError):
    """Raised when analysis takes too long."""
    pass

class InvalidCodeError(AnalysisError):
    """Raised when code cannot be parsed or analyzed."""
    pass
```

### Generation Exceptions

#### GenerationError
Base exception for code generation errors.

```python
class GenerationError(AurelisError):
    """Base exception for generation operations."""
    pass

class TemplateNotFoundError(GenerationError):
    """Raised when template is not found."""
    pass

class GenerationTimeoutError(GenerationError):
    """Raised when generation takes too long."""
    pass

class InvalidGenerationRequestError(GenerationError):
    """Raised when generation request is invalid."""
    pass
```

### Configuration Exceptions

#### ConfigurationError
Base exception for configuration errors.

```python
class ConfigurationError(AurelisError):
    """Base exception for configuration issues."""
    pass

class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration is invalid."""
    pass

class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""
    pass
```

### System Exceptions

#### SystemError
Base exception for system-level errors.

```python
class AurelisSystemError(AurelisError):
    """Base exception for system-level issues."""
    pass

class ResourceNotFoundError(AurelisSystemError):
    """Raised when a required resource is not found."""
    pass

class PermissionDeniedError(AurelisSystemError):
    """Raised when operation is not permitted."""
    pass

class DiskSpaceError(AurelisSystemError):
    """Raised when insufficient disk space."""
    pass
```

## Error Context

### Error Context Management

```python
from aurelis.core.errors import ErrorContext, get_error_context

# Set error context
with ErrorContext(
    operation="file_analysis",
    file_path="/path/to/file.py",
    user_id="user123"
):
    try:
        result = await analyze_file(file_path)
    except AnalysisError as e:
        # Error automatically includes context
        logger.error("Analysis failed", extra=e.context)
        raise

# Get current error context
context = get_error_context()
print(f"Current operation: {context.get('operation')}")
```

### Detailed Error Information

```python
try:
    await model_orchestrator.process_request(request)
except ModelError as e:
    print(f"Error: {e.message}")
    print(f"Code: {e.error_code}")
    print(f"Context: {e.context}")
    print(f"Timestamp: {e.timestamp}")
    
    # Check for specific error types
    if isinstance(e, ModelTimeoutError):
        print("Suggestion: Try reducing request complexity or increasing timeout")
    elif isinstance(e, ModelQuotaExceededError):
        print("Suggestion: Check usage limits or upgrade plan")
```

## Error Recovery

### Retry Mechanisms

```python
from aurelis.core.errors import retry_on_error, RetryConfig

# Automatic retry with exponential backoff
@retry_on_error(
    exceptions=[ModelTimeoutError, ModelNotAvailableError],
    max_attempts=3,
    backoff_factor=2.0,
    initial_delay=1.0
)
async def robust_model_request(request: ModelRequest):
    return await model_orchestrator.process_request(request)

# Manual retry with custom logic
async def manual_retry_example():
    retry_config = RetryConfig(
        max_attempts=5,
        exceptions=[ModelError],
        backoff_strategy="exponential"
    )
    
    for attempt in range(retry_config.max_attempts):
        try:
            result = await model_request()
            return result
        except ModelError as e:
            if attempt == retry_config.max_attempts - 1:
                raise
            
            delay = retry_config.calculate_delay(attempt)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s", 
                         extra={"error": str(e)})
            await asyncio.sleep(delay)
```

### Fallback Strategies

```python
from aurelis.core.errors import fallback_on_error

class ModelOrchestrator:
    @fallback_on_error([ModelNotAvailableError])
    async def process_request_with_fallback(self, request: ModelRequest):
        try:
            # Try primary model
            return await self._process_with_primary_model(request)
        except ModelNotAvailableError:
            # Automatic fallback to secondary model
            logger.warning("Primary model unavailable, using fallback")
            return await self._process_with_fallback_model(request)
```

### Circuit Breaker Pattern

```python
from aurelis.core.errors import CircuitBreaker

class ExternalService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,  # Open after 5 failures
            timeout=60,          # Stay open for 60 seconds
            expected_exceptions=[ModelError]
        )
    
    async def call_external_api(self, data):
        async with self.circuit_breaker:
            return await self._make_api_call(data)
```

## Error Handling Patterns

### Model Request Error Handling

```python
from aurelis.models import ModelOrchestrator
from aurelis.core.errors import *

class SafeModelOrchestrator:
    def __init__(self):
        self.orchestrator = ModelOrchestrator()
        self.logger = get_logger(__name__)
    
    async def safe_process_request(self, request: ModelRequest) -> Optional[ModelResponse]:
        try:
            return await self.orchestrator.process_request(request)
            
        except ModelNotAvailableError as e:
            self.logger.warning("Model not available, trying fallback", 
                              extra={"requested_model": request.preferred_model})
            # Try with fallback model
            fallback_request = request.copy()
            fallback_request.preferred_model = None  # Let orchestrator choose
            return await self.orchestrator.process_request(fallback_request)
            
        except ModelTimeoutError as e:
            self.logger.error("Model request timed out", 
                            extra={"timeout": e.context.get("timeout")})
            # Return partial result if available
            return e.context.get("partial_response")
            
        except ModelQuotaExceededError as e:
            self.logger.error("Model quota exceeded", 
                            extra={"quota_reset": e.context.get("reset_time")})
            # Could implement queue for later processing
            raise
            
        except Exception as e:
            self.logger.error("Unexpected error in model request", 
                            exc_info=True)
            raise AurelisSystemError(f"Unexpected error: {str(e)}")
```

### Analysis Error Handling

```python
from aurelis.analysis import CodeAnalyzer
from aurelis.core.errors import *

class SafeCodeAnalyzer:
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.logger = get_logger(__name__)
    
    async def safe_analyze_file(self, file_path: Path) -> Optional[AnalysisResult]:
        try:
            return await self.analyzer.analyze_file(file_path)
            
        except UnsupportedLanguageError as e:
            self.logger.warning(f"Language not supported: {file_path.suffix}")
            # Return basic file info instead
            return self._create_basic_analysis(file_path)
            
        except AnalysisTimeoutError as e:
            self.logger.warning(f"Analysis timed out: {file_path}")
            # Return partial results if available
            return e.context.get("partial_result")
            
        except InvalidCodeError as e:
            self.logger.error(f"Invalid code in file: {file_path}", 
                            extra={"syntax_errors": e.context.get("errors")})
            # Return syntax error information
            return self._create_error_analysis(file_path, e)
            
        except PermissionDeniedError as e:
            self.logger.error(f"Permission denied: {file_path}")
            return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error analyzing {file_path}", 
                            exc_info=True)
            return None
    
    def _create_basic_analysis(self, file_path: Path) -> AnalysisResult:
        """Create basic analysis for unsupported files."""
        return AnalysisResult(
            file_path=file_path,
            analysis_types=[],
            issues=[],
            metrics={"file_size": file_path.stat().st_size},
            suggestions=["File type not supported for detailed analysis"],
            confidence=0.0,
            processing_time=0.0
        )
```

### Shell Command Error Handling

```python
from aurelis.shell import InteractiveShell
from aurelis.core.errors import *

class SafeShell:
    def __init__(self):
        self.shell = InteractiveShell()
        self.logger = get_logger(__name__)
    
    async def safe_execute_command(self, command: str, args: List[str]) -> CommandResult:
        try:
            return await self.shell.execute_command(command, args)
            
        except CommandNotFoundError as e:
            suggestion = self._suggest_similar_command(command)
            return CommandResult(
                command=command,
                args=args,
                success=False,
                error_message=f"Command '{command}' not found",
                suggestions=[f"Did you mean '{suggestion}'?"] if suggestion else []
            )
            
        except InvalidArgumentsError as e:
            help_text = await self.shell.get_command_help(command)
            return CommandResult(
                command=command,
                args=args,
                success=False,
                error_message=str(e),
                suggestions=[f"Usage: {help_text}"]
            )
            
        except Exception as e:
            self.logger.error(f"Command execution failed: {command}", 
                            exc_info=True)
            return CommandResult(
                command=command,
                args=args,
                success=False,
                error_message="Internal error occurred",
                suggestions=["Try again or contact support"]
            )
```

## Error Reporting and Monitoring

### Error Aggregation

```python
from aurelis.core.errors import ErrorCollector

class ErrorMetrics:
    def __init__(self):
        self.collector = ErrorCollector()
    
    def track_error(self, error: Exception, context: Dict = None):
        """Track error for metrics and monitoring."""
        self.collector.add_error(
            error_type=type(error).__name__,
            message=str(error),
            context=context,
            timestamp=datetime.now()
        )
    
    def get_error_summary(self, time_window: timedelta = None) -> Dict:
        """Get error summary for monitoring."""
        return self.collector.get_summary(time_window)
    
    async def send_error_metrics(self):
        """Send error metrics to monitoring system."""
        summary = self.get_error_summary()
        await self._send_to_monitoring(summary)
```

### User-Friendly Error Messages

```python
from aurelis.core.errors import ErrorFormatter

class UserErrorHandler:
    def __init__(self):
        self.formatter = ErrorFormatter()
    
    def format_error_for_user(self, error: Exception) -> Dict[str, str]:
        """Format error for user display."""
        if isinstance(error, ModelNotAvailableError):
            return {
                "title": "AI Model Unavailable",
                "message": "The requested AI model is currently unavailable.",
                "suggestion": "Try again in a few minutes or use a different model.",
                "action": "Switch to fallback model"
            }
        
        elif isinstance(error, ModelQuotaExceededError):
            return {
                "title": "Usage Limit Reached",
                "message": "You have reached your monthly usage limit.",
                "suggestion": "Upgrade your plan or wait for next billing cycle.",
                "action": "View pricing plans"
            }
        
        elif isinstance(error, UnsupportedLanguageError):
            return {
                "title": "Language Not Supported",
                "message": f"Analysis for {error.context.get('language')} files is not supported.",
                "suggestion": "Check supported languages in documentation.",
                "action": "View supported languages"
            }
        
        else:
            return {
                "title": "Unexpected Error",
                "message": "An unexpected error occurred.",
                "suggestion": "Please try again or contact support.",
                "action": "Report issue"
            }
```

## Configuration

### Error Handling Configuration

```yaml
error_handling:
  retry:
    max_attempts: 3
    backoff_factor: 2.0
    initial_delay: 1.0
    jitter: true
  
  circuit_breaker:
    failure_threshold: 5
    timeout: 60
    half_open_max_calls: 3
  
  reporting:
    enabled: true
    include_stack_trace: false  # In production
    sanitize_data: true
    aggregation_window: 300  # 5 minutes
  
  fallback:
    model_fallback_enabled: true
    analysis_fallback_enabled: true
    graceful_degradation: true
```

### Custom Error Handlers

```python
from aurelis.core.errors import register_error_handler

@register_error_handler(ModelError)
async def handle_model_error(error: ModelError, context: Dict):
    """Custom handler for model errors."""
    # Log error with context
    logger.error("Model error occurred", extra={
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context
    })
    
    # Send to monitoring
    await send_error_to_monitoring(error, context)
    
    # Attempt recovery
    if isinstance(error, ModelTimeoutError):
        return await retry_with_shorter_timeout(context["request"])
    elif isinstance(error, ModelNotAvailableError):
        return await use_fallback_model(context["request"])
    
    # Re-raise if no recovery possible
    raise error
```

## Best Practices

### Error Handling Guidelines

1. **Specific Exceptions**: Use specific exception types for different error conditions
2. **Error Context**: Always include relevant context information
3. **Graceful Degradation**: Provide fallback behavior where possible
4. **User-Friendly Messages**: Translate technical errors to user-friendly messages
5. **Logging Integration**: Ensure all errors are properly logged
6. **Monitoring**: Track error rates and patterns
7. **Recovery Strategies**: Implement automatic recovery where appropriate

### Example Implementation

```python
from aurelis.core.errors import *
from aurelis.core.logging import get_logger

class RobustFileProcessor:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.error_collector = ErrorCollector()
    
    async def process_file(self, file_path: Path) -> ProcessingResult:
        """Robust file processing with comprehensive error handling."""
        
        try:
            # Validate file
            await self._validate_file(file_path)
            
            # Process with retry and fallback
            with ErrorContext(file_path=str(file_path), operation="file_processing"):
                result = await self._process_with_retry(file_path)
                
            self.logger.info("File processed successfully", 
                           extra={"file_path": str(file_path)})
            return result
            
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            self.logger.error(error_msg)
            raise ResourceNotFoundError(error_msg, context={"file_path": str(file_path)})
            
        except PermissionError:
            error_msg = f"Permission denied: {file_path}"
            self.logger.error(error_msg)
            raise PermissionDeniedError(error_msg, context={"file_path": str(file_path)})
            
        except UnsupportedLanguageError as e:
            self.logger.warning(f"Unsupported language: {file_path}")
            # Return basic processing result
            return self._create_basic_result(file_path)
            
        except Exception as e:
            # Track unexpected errors
            self.error_collector.add_error(
                error_type=type(e).__name__,
                message=str(e),
                context={"file_path": str(file_path)}
            )
            
            self.logger.error("Unexpected error processing file", 
                            extra={"file_path": str(file_path)}, 
                            exc_info=True)
            
            # Re-raise as system error
            raise AurelisSystemError(f"Failed to process file: {e}")
    
    @retry_on_error([AnalysisTimeoutError], max_attempts=2)
    async def _process_with_retry(self, file_path: Path):
        """Process file with automatic retry on timeout."""
        return await self._actual_processing(file_path)
```

For comprehensive error handling strategies and advanced patterns, refer to the main Aurelis documentation.
