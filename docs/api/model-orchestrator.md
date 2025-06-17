# Model Orchestrator API

The Model Orchestrator is the central component that manages GitHub models via Azure AI Inference.

## Overview

The orchestrator provides:
- **Intelligent model routing** based on task type
- **Automatic fallback** to secondary models
- **Response caching** for performance
- **Circuit breaker** patterns for reliability
- **Token management** and rate limiting

## Basic Usage

### Initialize Orchestrator

```python
from aurelis.models import get_model_orchestrator

orchestrator = get_model_orchestrator()
```

### Process Requests

```python
from aurelis.models import ModelRequest, ModelType, TaskType

request = ModelRequest(
    prompt="Generate a Python function to calculate fibonacci numbers",
    model_type=ModelType.CODESTRAL_2501,
    task_type=TaskType.CODE_GENERATION,
    system_prompt="You are an expert Python developer.",
    temperature=0.1,
    max_tokens=1000
)

response = await orchestrator.process_request(request)
print(response.content)
```

## Available Models

### Primary Models

| Model | Provider | Best For | Context |
|-------|----------|----------|---------|
| `CODESTRAL_2501` | Mistral | Code generation & optimization | 4K |
| `GPT_4O` | OpenAI | Complex reasoning & multimodal | 4K |
| `GPT_4O_MINI` | OpenAI | Fast responses & documentation | 4K |
| `COHERE_COMMAND_R` | Cohere | Documentation & explanations | 4K |
| `COHERE_COMMAND_R_PLUS` | Cohere | Advanced reasoning | 4K |
| `META_LLAMA_70B` | Meta | Balanced performance | 4K |
| `META_LLAMA_405B` | Meta | Maximum capability | 4K |
| `MISTRAL_LARGE` | Mistral | Enterprise applications | 4K |
| `MISTRAL_NEMO` | Mistral | Fast inference | 4K |

### Task-Based Routing

The orchestrator automatically selects the best model based on task type:

```python
# Code generation tasks -> Codestral-2501
request = ModelRequest(
    prompt="Create a REST API",
    task_type=TaskType.CODE_GENERATION
)

# Documentation tasks -> Cohere Command-R
request = ModelRequest(
    prompt="Document this function",
    task_type=TaskType.DOCUMENTATION
)

# Complex reasoning -> GPT-4o
request = ModelRequest(
    prompt="Analyze this architecture",
    task_type=TaskType.ANALYSIS
)
```

## Request Types

### ModelRequest

```python
@dataclass
class ModelRequest:
    prompt: str
    model_type: Optional[ModelType] = None
    task_type: TaskType = TaskType.GENERAL
    system_prompt: Optional[str] = None
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
```

### TaskType Enum

```python
class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    CODE_OPTIMIZATION = "code_optimization"
    DOCUMENTATION = "documentation"
    EXPLANATION = "explanation"
    REFACTORING = "refactoring"
    TESTING = "testing"
    ANALYSIS = "analysis"
    GENERAL = "general"
```

## Response Types

### ModelResponse

```python
@dataclass
class ModelResponse:
    content: str
    model_used: ModelType
    tokens_used: int
    processing_time: float
    cached: bool = False
    metadata: Optional[Dict[str, Any]] = None
```

## Advanced Features

### Custom System Prompts

```python
request = ModelRequest(
    prompt="Optimize this function",
    system_prompt="""You are a senior Python performance engineer.
    Focus on algorithmic efficiency and memory optimization.
    Provide detailed explanations for your optimizations."""
)
```

### Context Injection

```python
request = ModelRequest(
    prompt="Add error handling to this function",
    context={
        "existing_code": open("function.py").read(),
        "project_structure": ["models/", "views/", "utils/"],
        "error_patterns": ["ConnectionError", "ValidationError"]
    }
)
```

### Metadata Tracking

```python
request = ModelRequest(
    prompt="Generate unit tests",
    metadata={
        "user_id": "developer_123",
        "project_id": "aurelis",
        "session_id": "session_456"
    }
)
```

## Caching

### Automatic Caching

Responses are automatically cached based on:
- **Request content hash**
- **Model type and parameters** 
- **System prompt hash**

```python
# First call - hits the model
response1 = await orchestrator.process_request(request)
print(f"Cached: {response1.cached}")  # False

# Second identical call - hits cache
response2 = await orchestrator.process_request(request)
print(f"Cached: {response2.cached}")  # True
```

### Cache Configuration

```python
from aurelis.core.config import get_config

config = get_config()
config.cache_enabled = True
config.cache_ttl = 3600  # 1 hour
config.cache_max_size = 1000
```

## Error Handling

### Model Errors

```python
from aurelis.core.exceptions import ModelError, AuthenticationError

try:
    response = await orchestrator.process_request(request)
except AuthenticationError as e:
    print(f"GitHub token invalid: {e}")
except ModelError as e:
    print(f"Model processing failed: {e}")
    # Automatic fallback will be attempted
```

### Circuit Breaker

The orchestrator includes circuit breaker patterns:

```python
# Automatic fallback on model failures
request = ModelRequest(
    prompt="Generate code",
    model_type=ModelType.CODESTRAL_2501  # Primary
)

# If Codestral fails, automatically tries GPT-4o-mini
response = await orchestrator.process_request(request)
print(f"Used model: {response.model_used}")
```

## Performance Monitoring

### Token Usage

```python
response = await orchestrator.process_request(request)
print(f"Tokens used: {response.tokens_used}")
print(f"Processing time: {response.processing_time:.2f}s")
```

### Batch Processing

```python
requests = [
    ModelRequest(prompt="Generate function A"),
    ModelRequest(prompt="Generate function B"),
    ModelRequest(prompt="Generate function C")
]

responses = await orchestrator.process_batch(requests)
for response in responses:
    print(f"Response: {response.content[:100]}...")
```

## Rate Limiting

GitHub model access is automatically rate-limited:

```python
# Automatic rate limiting and retry
response = await orchestrator.process_request(request)

# Rate limit information in metadata
if response.metadata:
    print(f"Rate limit remaining: {response.metadata.get('rate_limit_remaining')}")
    print(f"Reset time: {response.metadata.get('rate_limit_reset')}")
```

## Best Practices

### 1. Use Appropriate Models

```python
# For code generation
request = ModelRequest(
    prompt="Create a web scraper",
    model_type=ModelType.CODESTRAL_2501
)

# For documentation
request = ModelRequest(
    prompt="Document this API",
    model_type=ModelType.COHERE_COMMAND_R
)
```

### 2. Optimize Prompts

```python
# Good: Specific and clear
request = ModelRequest(
    prompt="Create a Python function that validates email addresses using regex"
)

# Better: Include context and requirements
request = ModelRequest(
    prompt="Create a Python function that validates email addresses using regex",
    system_prompt="Write production-ready code with proper error handling",
    context={"framework": "FastAPI", "testing": "pytest"}
)
```

### 3. Handle Errors Gracefully

```python
async def generate_code(prompt: str) -> str:
    try:
        request = ModelRequest(prompt=prompt)
        response = await orchestrator.process_request(request)
        return response.content
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        return "# Code generation failed, please try again"
```

### 4. Use Caching Effectively

```python
# Enable caching for repetitive tasks
request = ModelRequest(
    prompt="Explain Python decorators",
    task_type=TaskType.EXPLANATION
)

# Disable caching for unique generations
request = ModelRequest(
    prompt=f"Generate unique code for user {user_id}",
    metadata={"cache_disabled": True}
)
```

## Integration Examples

### CLI Integration

```python
# Used in CLI commands
async def cli_generate(prompt: str, model: str = None):
    orchestrator = get_model_orchestrator()
    
    request = ModelRequest(
        prompt=prompt,
        model_type=ModelType(model) if model else None
    )
    
    response = await orchestrator.process_request(request)
    return response.content
```

### Interactive Shell

```python
# Used in interactive shell
class AurelisShell:
    def __init__(self):
        self.orchestrator = get_model_orchestrator()
    
    async def process_command(self, command: str):
        request = ModelRequest(
            prompt=command,
            task_type=self._detect_task_type(command)
        )
        
        return await self.orchestrator.process_request(request)
```

## See Also

- [Request/Response API](request-response.md)
- [Model Types Reference](model-types.md)
- [Configuration Guide](configuration.md)
- [Error Handling](error-handling.md)
