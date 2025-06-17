# Model Types API Reference

This document provides comprehensive information about the available model types in Aurelis, their capabilities, and configuration options.

## Table of Contents

- [Overview](#overview)
- [Model Type Enumeration](#model-type-enumeration)
- [Model Capabilities](#model-capabilities)
- [Model Configuration](#model-configuration)
- [GitHub Models](#github-models)
- [OpenAI Models](#openai-models)
- [Anthropic Models](#anthropic-models)
- [Azure AI Models](#azure-ai-models)
- [Local Models](#local-models)
- [Model Selection](#model-selection)
- [Performance Characteristics](#performance-characteristics)
- [Usage Examples](#usage-examples)

## Overview

Aurelis supports multiple AI model providers and types, each optimized for different tasks and use cases. The model system provides a unified interface for accessing various large language models through a consistent API.

## Model Type Enumeration

### ModelType Enum

```python
from aurelis.types import ModelType

class ModelType(Enum):
    """Enumeration of supported model types"""
    
    # GitHub Models
    GITHUB_GPT_4O = "github-gpt-4o"
    GITHUB_GPT_4O_MINI = "github-gpt-4o-mini"
    GITHUB_O1_PREVIEW = "github-o1-preview"
    GITHUB_O1_MINI = "github-o1-mini"
    GITHUB_GPT_35_TURBO = "github-gpt-35-turbo"
    
    # OpenAI Models
    OPENAI_GPT_4O = "openai-gpt-4o"
    OPENAI_GPT_4O_MINI = "openai-gpt-4o-mini"
    OPENAI_GPT_4_TURBO = "openai-gpt-4-turbo"
    OPENAI_GPT_35_TURBO = "openai-gpt-35-turbo"
    OPENAI_O1_PREVIEW = "openai-o1-preview"
    OPENAI_O1_MINI = "openai-o1-mini"
    
    # Anthropic Models
    ANTHROPIC_CLAUDE_35_SONNET = "anthropic-claude-3.5-sonnet"
    ANTHROPIC_CLAUDE_3_OPUS = "anthropic-claude-3-opus"
    ANTHROPIC_CLAUDE_3_HAIKU = "anthropic-claude-3-haiku"
    
    # Azure AI Models
    AZURE_GPT_4O = "azure-gpt-4o"
    AZURE_GPT_35_TURBO = "azure-gpt-35-turbo"
    AZURE_CLAUDE_35_SONNET = "azure-claude-3.5-sonnet"
    
    # Local Models
    LOCAL_LLAMA = "local-llama"
    LOCAL_MISTRAL = "local-mistral"
    LOCAL_CODELLAMA = "local-codellama"
```

### TaskType Enum

```python
from aurelis.types import TaskType

class TaskType(Enum):
    """Task types supported by models"""
    
    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    CODE_REVIEW = "code_review"
    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    TESTING = "testing"
    EXPLANATION = "explanation"
    TRANSLATION = "translation"
    GENERAL_CHAT = "general_chat"
```

## Model Capabilities

### ModelCapabilities Class

```python
from aurelis.types import ModelCapabilities

@dataclass
class ModelCapabilities:
    """Model capabilities and limitations"""
    
    max_tokens: int
    context_window: int
    supports_function_calling: bool
    supports_streaming: bool
    supports_vision: bool
    supports_code_execution: bool
    multimodal: bool
    reasoning_optimized: bool
    cost_per_input_token: float
    cost_per_output_token: float
    rate_limits: Dict[str, int]
    supported_tasks: List[TaskType]
```

### Capability Matrix

| Model | Max Tokens | Context | Function Calling | Streaming | Vision | Code Execution |
|-------|------------|---------|------------------|-----------|--------|----------------|
| GPT-4o | 4,096 | 128k | ✅ | ✅ | ✅ | ❌ |
| GPT-4o Mini | 16,384 | 128k | ✅ | ✅ | ✅ | ❌ |
| O1 Preview | 32,768 | 128k | ❌ | ❌ | ❌ | ❌ |
| O1 Mini | 65,536 | 128k | ❌ | ❌ | ❌ | ❌ |
| Claude 3.5 Sonnet | 8,192 | 200k | ✅ | ✅ | ✅ | ❌ |
| Claude 3 Opus | 4,096 | 200k | ✅ | ✅ | ✅ | ❌ |
| Claude 3 Haiku | 4,096 | 200k | ✅ | ✅ | ❌ | ❌ |

## Model Configuration

### ModelConfig Class

```python
from aurelis.types import ModelConfig

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    
    model_type: ModelType
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    custom_headers: Dict[str, str] = field(default_factory=dict)
    model_specific_params: Dict[str, Any] = field(default_factory=dict)
```

### Configuration Examples

```python
# GitHub Models Configuration
github_config = ModelConfig(
    model_type=ModelType.GITHUB_GPT_4O,
    temperature=0.1,
    max_tokens=2048,
    custom_headers={"X-GitHub-Api-Version": "2022-11-28"}
)

# OpenAI Configuration
openai_config = ModelConfig(
    model_type=ModelType.OPENAI_GPT_4O,
    temperature=0.5,
    max_tokens=4096,
    top_p=0.9,
    frequency_penalty=0.1
)

# Anthropic Configuration
anthropic_config = ModelConfig(
    model_type=ModelType.ANTHROPIC_CLAUDE_35_SONNET,
    temperature=0.3,
    max_tokens=8192,
    model_specific_params={"system": "You are a helpful coding assistant."}
)
```

## GitHub Models

### Available Models

```python
GITHUB_MODELS = {
    ModelType.GITHUB_GPT_4O: ModelCapabilities(
        max_tokens=4096,
        context_window=128000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=True,
        supports_code_execution=False,
        multimodal=True,
        reasoning_optimized=False,
        cost_per_input_token=0.0,  # Free through GitHub
        cost_per_output_token=0.0,
        rate_limits={"requests_per_minute": 15, "tokens_per_minute": 150000},
        supported_tasks=[
            TaskType.CODE_GENERATION,
            TaskType.CODE_COMPLETION,
            TaskType.CODE_REVIEW,
            TaskType.DOCUMENTATION,
            TaskType.GENERAL_CHAT
        ]
    ),
    
    ModelType.GITHUB_O1_PREVIEW: ModelCapabilities(
        max_tokens=32768,
        context_window=128000,
        supports_function_calling=False,
        supports_streaming=False,
        supports_vision=False,
        supports_code_execution=False,
        multimodal=False,
        reasoning_optimized=True,
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
        rate_limits={"requests_per_minute": 5, "tokens_per_minute": 40000},
        supported_tasks=[
            TaskType.CODE_ANALYSIS,
            TaskType.DEBUGGING,
            TaskType.REFACTORING,
            TaskType.EXPLANATION
        ]
    )
}
```

### GitHub Model Authentication

```python
from aurelis.core.security import GitHubTokenManager

# Set up GitHub authentication
token_manager = GitHubTokenManager()
token_manager.set_token("your_github_token_here")

# Verify token
if token_manager.verify_token():
    print("GitHub token is valid")
```

## OpenAI Models

### Model Specifications

```python
OPENAI_MODELS = {
    ModelType.OPENAI_GPT_4O: ModelCapabilities(
        max_tokens=4096,
        context_window=128000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=True,
        supports_code_execution=False,
        multimodal=True,
        reasoning_optimized=False,
        cost_per_input_token=0.005,
        cost_per_output_token=0.015,
        rate_limits={"requests_per_minute": 5000, "tokens_per_minute": 800000},
        supported_tasks=list(TaskType)
    ),
    
    ModelType.OPENAI_O1_PREVIEW: ModelCapabilities(
        max_tokens=32768,
        context_window=128000,
        supports_function_calling=False,
        supports_streaming=False,
        supports_vision=False,
        supports_code_execution=False,
        multimodal=False,
        reasoning_optimized=True,
        cost_per_input_token=0.015,
        cost_per_output_token=0.060,
        rate_limits={"requests_per_minute": 20, "tokens_per_minute": 150000},
        supported_tasks=[
            TaskType.CODE_ANALYSIS,
            TaskType.DEBUGGING,
            TaskType.REFACTORING
        ]
    )
}
```

## Anthropic Models

### Claude Model Family

```python
ANTHROPIC_MODELS = {
    ModelType.ANTHROPIC_CLAUDE_35_SONNET: ModelCapabilities(
        max_tokens=8192,
        context_window=200000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=True,
        supports_code_execution=False,
        multimodal=True,
        reasoning_optimized=False,
        cost_per_input_token=0.003,
        cost_per_output_token=0.015,
        rate_limits={"requests_per_minute": 1000, "tokens_per_minute": 300000},
        supported_tasks=list(TaskType)
    ),
    
    ModelType.ANTHROPIC_CLAUDE_3_HAIKU: ModelCapabilities(
        max_tokens=4096,
        context_window=200000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=False,
        supports_code_execution=False,
        multimodal=False,
        reasoning_optimized=False,
        cost_per_input_token=0.00025,
        cost_per_output_token=0.00125,
        rate_limits={"requests_per_minute": 1000, "tokens_per_minute": 300000},
        supported_tasks=[
            TaskType.CODE_COMPLETION,
            TaskType.DOCUMENTATION,
            TaskType.GENERAL_CHAT
        ]
    )
}
```

## Azure AI Models

### Azure Integration

```python
AZURE_MODELS = {
    ModelType.AZURE_GPT_4O: ModelCapabilities(
        max_tokens=4096,
        context_window=128000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=True,
        supports_code_execution=False,
        multimodal=True,
        reasoning_optimized=False,
        cost_per_input_token=0.005,  # Varies by region
        cost_per_output_token=0.015,
        rate_limits={"requests_per_minute": 300, "tokens_per_minute": 120000},
        supported_tasks=list(TaskType)
    )
}
```

### Azure Configuration

```python
azure_config = ModelConfig(
    model_type=ModelType.AZURE_GPT_4O,
    endpoint="https://your-resource.openai.azure.com/",
    model_specific_params={
        "api_version": "2024-02-15-preview",
        "deployment_name": "gpt-4o-deployment"
    }
)
```

## Local Models

### Local Model Support

```python
LOCAL_MODELS = {
    ModelType.LOCAL_LLAMA: ModelCapabilities(
        max_tokens=2048,
        context_window=4096,
        supports_function_calling=False,
        supports_streaming=True,
        supports_vision=False,
        supports_code_execution=False,
        multimodal=False,
        reasoning_optimized=False,
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
        rate_limits={},  # No external rate limits
        supported_tasks=[
            TaskType.CODE_GENERATION,
            TaskType.CODE_COMPLETION,
            TaskType.GENERAL_CHAT
        ]
    )
}
```

### Local Model Configuration

```python
local_config = ModelConfig(
    model_type=ModelType.LOCAL_LLAMA,
    endpoint="http://localhost:8000/v1",
    model_specific_params={
        "model_path": "/path/to/llama-model",
        "gpu_layers": 35,
        "context_length": 4096
    }
)
```

## Model Selection

### Model Selection Algorithm

```python
from aurelis.models import ModelSelector

class ModelSelector:
    """Intelligent model selection based on task requirements"""
    
    def select_model(
        self,
        task_type: TaskType,
        context_length: int = 0,
        performance_priority: str = "balanced",  # "speed", "quality", "cost"
        provider_preference: Optional[str] = None
    ) -> ModelType:
        """Select optimal model for the given requirements"""
        
        # Filter models by task support
        suitable_models = self._filter_by_task(task_type)
        
        # Filter by context requirements
        suitable_models = self._filter_by_context(suitable_models, context_length)
        
        # Apply provider preference
        if provider_preference:
            suitable_models = self._filter_by_provider(suitable_models, provider_preference)
        
        # Rank by performance priority
        return self._rank_by_priority(suitable_models, performance_priority)
    
    def _filter_by_task(self, task_type: TaskType) -> List[ModelType]:
        """Filter models that support the given task"""
        return [
            model for model, capabilities in ALL_MODELS.items()
            if task_type in capabilities.supported_tasks
        ]
    
    def _rank_by_priority(self, models: List[ModelType], priority: str) -> ModelType:
        """Rank models by priority criteria"""
        if priority == "speed":
            return self._fastest_model(models)
        elif priority == "quality":
            return self._highest_quality_model(models)
        elif priority == "cost":
            return self._lowest_cost_model(models)
        else:
            return self._balanced_model(models)
```

### Selection Examples

```python
selector = ModelSelector()

# Select for code generation
code_model = selector.select_model(
    task_type=TaskType.CODE_GENERATION,
    performance_priority="quality"
)

# Select for fast completion
completion_model = selector.select_model(
    task_type=TaskType.CODE_COMPLETION,
    performance_priority="speed"
)

# Select for complex reasoning
reasoning_model = selector.select_model(
    task_type=TaskType.CODE_ANALYSIS,
    context_length=50000,
    performance_priority="quality"
)
```

## Performance Characteristics

### Latency Comparison

| Model | Avg Response Time | Tokens/sec | Best Use Case |
|-------|------------------|------------|---------------|
| GPT-4o Mini | 1.2s | 85 | Fast completion |
| GPT-4o | 2.1s | 45 | High-quality generation |
| O1 Preview | 8.5s | 15 | Complex reasoning |
| Claude 3.5 Sonnet | 1.8s | 50 | Balanced performance |
| Claude 3 Haiku | 0.9s | 95 | Speed-optimized |

### Cost Analysis

```python
from aurelis.models import CostCalculator

calculator = CostCalculator()

# Calculate cost for a request
cost = calculator.calculate_cost(
    model_type=ModelType.OPENAI_GPT_4O,
    input_tokens=1500,
    output_tokens=800
)

print(f"Estimated cost: ${cost:.4f}")
```

## Usage Examples

### Basic Model Usage

```python
from aurelis.models import get_model_orchestrator
from aurelis.types import ModelType, ModelRequest

# Initialize orchestrator
orchestrator = get_model_orchestrator()

# Create request
request = ModelRequest(
    model_type=ModelType.GITHUB_GPT_4O,
    prompt="Generate a Python function to calculate fibonacci numbers",
    max_tokens=1000,
    temperature=0.1
)

# Get response
response = await orchestrator.process_request(request)
print(response.content)
```

### Multi-Model Comparison

```python
from aurelis.models import ModelComparator

comparator = ModelComparator()

# Compare models for a task
results = await comparator.compare_models(
    prompt="Explain how binary search works",
    models=[
        ModelType.GITHUB_GPT_4O,
        ModelType.ANTHROPIC_CLAUDE_35_SONNET,
        ModelType.OPENAI_GPT_4O_MINI
    ]
)

for model, response in results.items():
    print(f"{model}: {response.content[:100]}...")
```

### Model Fallback

```python
from aurelis.models import ModelFallbackChain

# Create fallback chain
fallback_chain = ModelFallbackChain([
    ModelType.GITHUB_GPT_4O,      # Primary
    ModelType.OPENAI_GPT_4O_MINI, # Secondary
    ModelType.ANTHROPIC_CLAUDE_3_HAIKU  # Tertiary
])

# Process with automatic fallback
response = await fallback_chain.process_request(request)
```

### Custom Model Registration

```python
from aurelis.models import register_custom_model

# Register a custom model
register_custom_model(
    model_type="custom-llama-7b",
    capabilities=ModelCapabilities(
        max_tokens=2048,
        context_window=4096,
        supports_function_calling=False,
        supports_streaming=True,
        # ... other capabilities
    ),
    config=ModelConfig(
        endpoint="http://localhost:8080/v1/completions",
        # ... other config
    )
)
```

## Error Handling

### Model-Specific Errors

```python
from aurelis.exceptions import (
    ModelNotAvailableError,
    RateLimitExceededError,
    TokenLimitExceededError,
    ModelConfigurationError
)

try:
    response = await orchestrator.process_request(request)
except ModelNotAvailableError as e:
    print(f"Model not available: {e}")
except RateLimitExceededError as e:
    print(f"Rate limit exceeded: {e.retry_after} seconds")
except TokenLimitExceededError as e:
    print(f"Token limit exceeded: {e.token_count}")
```

## Best Practices

### Model Selection Guidelines

1. **For Code Generation**: Use GPT-4o or Claude 3.5 Sonnet for high quality
2. **For Code Completion**: Use GPT-4o Mini or Claude 3 Haiku for speed
3. **For Complex Reasoning**: Use O1 Preview for difficult problems
4. **For Documentation**: Use any model with good language capabilities
5. **For Cost Optimization**: Use GitHub Models when available

### Configuration Best Practices

```python
# Production configuration
production_config = ModelConfig(
    model_type=ModelType.GITHUB_GPT_4O,
    temperature=0.1,  # Lower for consistency
    max_tokens=2048,  # Reasonable limit
    timeout=30,       # Adequate timeout
    retry_attempts=3, # Retry on failures
    retry_delay=1.0   # Exponential backoff
)

# Development configuration
dev_config = ModelConfig(
    model_type=ModelType.GITHUB_GPT_4O_MINI,
    temperature=0.3,  # Slightly higher for creativity
    max_tokens=1024,  # Lower for testing
    timeout=15,       # Faster feedback
    retry_attempts=1  # Fail fast in development
)
```

For more information on using specific models, see the [Model Orchestrator](model-orchestrator.md) documentation.
