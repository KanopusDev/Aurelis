# Aurelis API Reference

This section contains comprehensive API documentation for all Aurelis components.

## Core APIs

### Model Orchestrator
- **[Model System](model-orchestrator.md)** - GitHub model management and routing
- **[Request/Response](request-response.md)** - Request and response handling
- **[Model Types](model-types.md)** - Available models and their capabilities

### Configuration & Security
- **[Configuration](configuration.md)** - Configuration management API
- **[Security](security.md)** - Token management and encryption
- **[Cache](cache.md)** - Caching system and strategies

### Analysis & Generation
- **[Code Analyzer](code-analyzer.md)** - Code analysis and quality checks
- **[Code Generator](code-generator.md)** - Code generation and completion
- **[Documentation Generator](docs-generator.md)** - Documentation generation

### Utilities
- **[File System](filesystem.md)** - File operations and utilities
- **[Logging](logging.md)** - Logging and monitoring
- **[Error Handling](error-handling.md)** - Exception management

## Integration APIs

### CLI Interface
- **[CLI Commands](cli-commands.md)** - Command-line interface
- **[Interactive Shell](interactive-shell.md)** - Shell mode APIs

### External Integrations
- **[GitHub Integration](github-integration.md)** - GitHub API integration
- **[Azure AI Inference](azure-ai.md)** - Azure AI Inference endpoints

## Quick Reference

### Authentication
```python
from aurelis.core.security import get_api_key_manager

# Set GitHub token
api_key_manager = get_api_key_manager()
api_key_manager.set_api_key("github", "your_github_token")
```

### Basic Usage
```python
from aurelis.models import get_model_orchestrator, ModelRequest, ModelType, TaskType

# Create orchestrator
orchestrator = get_model_orchestrator()

# Make request
request = ModelRequest(
    prompt="Generate a Python class for user management",
    model_type=ModelType.CODESTRAL_2501,
    task_type=TaskType.CODE_GENERATION
)

response = await orchestrator.process_request(request)
print(response.content)
```

### Configuration
```python
from aurelis.core.config import get_config

config = get_config()
print(f"Primary model: {config.primary_model}")
```

## Error Handling

All APIs use structured error handling with custom exception types:

```python
from aurelis.core.exceptions import (
    AurelisError,
    ModelError,
    ConfigurationError,
    AuthenticationError
)

try:
    response = await orchestrator.process_request(request)
except ModelError as e:
    print(f"Model error: {e}")
except AuthenticationError as e:
    print(f"Auth error: {e}")
```

## Type Safety

Aurelis uses comprehensive type hints and Pydantic models for all APIs:

```python
from aurelis.models.types import ModelRequest, ModelResponse
from aurelis.core.types import AnalysisResult, CodeIssue

# All parameters and returns are type-safe
def analyze_code(content: str) -> AnalysisResult:
    # Implementation...
    pass
```

## Performance & Caching

- **Automatic caching** for model responses
- **Request deduplication** to prevent duplicate calls
- **Circuit breaker** pattern for reliability
- **Async/await** support throughout

## Rate Limiting

GitHub model usage is automatically rate-limited according to GitHub's policies:

- **Requests per minute**: Automatically managed
- **Token usage**: Tracked and optimized
- **Retry logic**: Exponential backoff on failures

## Next Steps

1. Read the [Model Orchestrator Guide](model-orchestrator.md)
2. Review [Configuration Options](configuration.md) 
3. Check [Error Handling Best Practices](error-handling.md)
4. Explore [Code Examples](../user-guide/examples.md)
