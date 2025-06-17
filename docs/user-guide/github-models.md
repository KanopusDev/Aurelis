# GitHub Models Integration Guide

**Complete guide to GitHub Models integration via Azure AI Inference**

Aurelis exclusively uses GitHub Models through Azure AI Inference, providing enterprise-grade AI capabilities with a single authentication token and unified API access.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication Setup](#authentication-setup)
3. [Available Models](#available-models)
4. [Model Selection](#model-selection)
5. [API Usage](#api-usage)
6. [Performance & Optimization](#performance--optimization)
7. [Security & Compliance](#security--compliance)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## 🔍 Overview

### What are GitHub Models?

GitHub Models provides access to cutting-edge AI models through a unified, OpenAI-compatible API via Azure AI Inference. This integration offers:

- **Enterprise Reliability**: Production-grade infrastructure with 99.9% uptime SLA
- **Single Token Authentication**: Unified GitHub token for all model access
- **Cost-Effective**: Competitive pricing with transparent usage tracking
- **OpenAI Compatibility**: Familiar API patterns for easy integration

### Why GitHub Models Only?

Aurelis exclusively uses GitHub Models for strategic reasons:

1. **Simplified Authentication**: Single GitHub token vs. multiple provider APIs
2. **Enterprise Support**: Professional support and SLA guarantees
3. **Developer Integration**: Seamless GitHub ecosystem integration
4. **Cost Efficiency**: Centralized billing and usage tracking
5. **Security**: Unified security model and compliance standards

## 🔐 Authentication Setup

### 1. GitHub Token Requirements

#### Prerequisites
- GitHub account with model access
- Personal access token with appropriate permissions

#### Token Permissions
Your GitHub token needs these scopes:
- `read:user` - Basic user information
- `read:org` - Organization membership (if applicable)

### 2. Creating Your GitHub Token

#### Step-by-Step Process

1. **Navigate to GitHub Settings**
   ```
   GitHub Profile → Settings → Developer settings → Personal access tokens
   ```

2. **Generate New Token**
   - Click "Generate new token (classic)"
   - Provide a descriptive name: "Aurelis AI Models"
   - Set expiration (recommended: 90 days)

3. **Select Scopes**
   ```
   ✅ read:user
   ✅ read:org (if using in organization context)
   ```

4. **Generate and Copy Token**
   - Click "Generate token"
   - **Important**: Copy immediately - you won't see it again!

#### GitHub Models Access Verification

Visit [GitHub Models Marketplace](https://github.com/marketplace/models) to verify your account has model access.

### 3. Token Configuration

#### Environment Variable (Recommended)

```bash
# Linux/macOS
export GITHUB_TOKEN="ghp_your_token_here"

# Windows PowerShell
$env:GITHUB_TOKEN="ghp_your_token_here"

# Windows Command Prompt
set GITHUB_TOKEN=ghp_your_token_here
```

#### Configuration File

```yaml
# .aurelis.yaml
github_token: "${GITHUB_TOKEN}"  # Use environment variable
```

#### Verification

```bash
# Test your token
aurelis models

# Should show:
# ✅ GitHub Token: ghp_1234...5678
# ✅ Status: Ready for GitHub models
```

## 🤖 Available Models

### Primary Model Portfolio

| Model | Provider | Specialty | Context Window | Best For |
|-------|----------|-----------|----------------|----------|
| **Codestral-2501** | Mistral | Code generation & optimization | 4K tokens | Production code, refactoring |
| **GPT-4o** | OpenAI | Complex reasoning & multimodal | 4K tokens | Architecture, complex analysis |
| **GPT-4o-mini** | OpenAI | Fast responses & documentation | 4K tokens | Quick tasks, documentation |
| **Cohere Command-R** | Cohere | Documentation & explanations | 4K tokens | Technical writing, explanations |
| **Cohere Command-R+** | Cohere | Advanced reasoning | 4K tokens | Complex problem solving |
| **Meta Llama 3.1 70B** | Meta | Balanced performance | 4K tokens | General development tasks |
| **Meta Llama 3.1 405B** | Meta | Maximum capability | 4K tokens | Enterprise applications |
| **Mistral Large** | Mistral | Enterprise applications | 4K tokens | Production systems |
| **Mistral Nemo** | Mistral | Fast inference | 4K tokens | Real-time applications |

### Model Capabilities Matrix

```
Code Generation:      Codestral-2501 → GPT-4o → Llama 70B
Documentation:        Command-R → GPT-4o-mini → Command-R+
Complex Reasoning:    GPT-4o → Llama 405B → Mistral Large
Performance Opt:      Codestral-2501 → Llama 70B → GPT-4o
Quick Tasks:          GPT-4o-mini → Mistral Nemo → Command-R
```

## 🎯 Model Selection

### Automatic Task-Based Routing

Aurelis automatically selects the optimal model based on task type:

```python
from aurelis.models import ModelRequest, TaskType

# Code generation automatically uses Codestral-2501
request = ModelRequest(
    prompt="Create a REST API for user management",
    task_type=TaskType.CODE_GENERATION
)

# Documentation automatically uses Cohere Command-R
request = ModelRequest(
    prompt="Document this API endpoint",
    task_type=TaskType.DOCUMENTATION
)
```

### Manual Model Selection

```python
from aurelis.models import ModelRequest, ModelType

# Force specific model
request = ModelRequest(
    prompt="Optimize this algorithm for performance",
    model_type=ModelType.CODESTRAL_2501,
    task_type=TaskType.CODE_OPTIMIZATION
)
```

### Intelligent Fallback Strategy

```
Primary Model Fails → Automatic Fallback → Retry Logic
    ↓                        ↓                ↓
Codestral-2501      →    GPT-4o        →   3 attempts
GPT-4o              →    Llama 405B     →   3 attempts
Command-R           →    GPT-4o-mini    →   3 attempts
```

## 🔧 API Usage

### Basic Model Request

```python
from aurelis.models import get_model_orchestrator, ModelRequest, TaskType

# Initialize orchestrator
orchestrator = get_model_orchestrator()

# Create request
request = ModelRequest(
    prompt="Generate a Python function to validate email addresses",
    task_type=TaskType.CODE_GENERATION,
    temperature=0.1,  # Deterministic for code
    max_tokens=1000
)

# Send request
response = await orchestrator.send_request(request)
print(response.content)
```

### Advanced Configuration

```python
request = ModelRequest(
    prompt="Optimize this database query",
    task_type=TaskType.CODE_OPTIMIZATION,
    system_prompt="""You are a database performance expert.
    Focus on query efficiency and index usage.
    Provide detailed explanations for optimizations.""",
    temperature=0.1,
    max_tokens=2000,
    metadata={
        "project": "aurelis",
        "database": "postgresql",
        "user_id": "developer_123"
    }
)
```

### Batch Processing

```python
requests = [
    ModelRequest(prompt="Generate user model", task_type=TaskType.CODE_GENERATION),
    ModelRequest(prompt="Generate user controller", task_type=TaskType.CODE_GENERATION),
    ModelRequest(prompt="Generate user tests", task_type=TaskType.TESTING)
]

responses = await orchestrator.batch_request(requests)
for response in responses:
    print(f"Model used: {response.model_used}")
    print(f"Content: {response.content[:100]}...")
```

## 🚀 Performance & Optimization

### Response Caching

```python
# First request hits the model
response1 = await orchestrator.send_request(request)
print(f"Cached: {response1.cached}")  # False

# Identical request hits cache
response2 = await orchestrator.send_request(request)
print(f"Cached: {response2.cached}")  # True
```

### Cache Configuration

```yaml
# .aurelis.yaml
cache:
  enabled: true
  ttl: 3600  # 1 hour
  max_size: 1000
  strategy: "lru"  # Least recently used
```

### Token Usage Optimization

```python
# Monitor token usage
response = await orchestrator.send_request(request)
print(f"Tokens used: {response.token_usage}")
print(f"Processing time: {response.processing_time:.2f}s")

# Optimize for cost
request = ModelRequest(
    prompt="Brief explanation of Python decorators",
    max_tokens=200,  # Limit response length
    temperature=0.1  # Deterministic responses
)
```

### Performance Monitoring

```python
# Get model statistics
stats = orchestrator.get_model_stats()
print(f"Available models: {stats['available_models']}")
print(f"Task mappings: {stats['task_mappings']}")

# Health check
health = orchestrator.health_check()
print(f"Overall status: {health['overall_status']}")
for model, status in health['models'].items():
    print(f"{model}: {status['status']}")
```

## 🔒 Security & Compliance

### Token Security

#### Secure Storage Options

```yaml
# Environment variable (recommended)
github_token: "${GITHUB_TOKEN}"

# System keyring (enterprise)
security:
  token_storage: "keyring"
  keyring_service: "aurelis"
  keyring_username: "github_models"
```

#### Token Rotation

```bash
# Regular token rotation (every 90 days)
1. Generate new GitHub token
2. Update environment variable
3. Restart Aurelis services
4. Revoke old token
```

### Audit Logging

```yaml
# .aurelis.yaml
security:
  audit_logging: true
  log_level: "INFO"
  log_requests: true
  log_responses: false  # Never log response content
```

### Enterprise Compliance

```yaml
# Enterprise configuration
security:
  compliance_mode: true
  data_retention_days: 90
  encryption_at_rest: true
  secure_headers: true
```

### API Request Security

```python
# Secure request headers
request = ModelRequest(
    prompt="Generate secure authentication code",
    metadata={
        "security_level": "high",
        "compliance": "sox_hip",
        "data_classification": "confidential"
    }
)
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Error**: `GitHub token not found`
```bash
# Verify environment variable
echo $GITHUB_TOKEN  # Linux/macOS
echo $env:GITHUB_TOKEN  # Windows PowerShell

# Set if missing
export GITHUB_TOKEN="your_token_here"
```

**Error**: `Invalid token format`
```bash
# GitHub tokens start with 'ghp_'
✅ Good: ghp_1234567890abcdef...
❌ Bad: gho_1234567890abcdef...
```

#### 2. Model Access Issues

**Error**: `Model not available`
```bash
# Check model status
aurelis models

# Expected output:
# ✅ Codestral-2501: Available
# ✅ GPT-4o: Available
```

**Error**: `Rate limit exceeded`
```python
# Check rate limits in response metadata
if 'rate_limit_remaining' in response.metadata:
    print(f"Remaining: {response.metadata['rate_limit_remaining']}")
    print(f"Reset time: {response.metadata['rate_limit_reset']}")
```

#### 3. Performance Issues

**Issue**: Slow response times
```yaml
# Optimize configuration
processing:
  timeout: 30  # Reduce timeout
  concurrent_requests: 3  # Reduce concurrency
  
cache:
  enabled: true  # Enable caching
  ttl: 1800  # 30 minutes
```

**Issue**: High token usage
```python
# Optimize requests
request = ModelRequest(
    prompt="Brief: " + your_prompt,  # Add "Brief:" prefix
    max_tokens=500,  # Limit response
    temperature=0.1  # Deterministic
)
```

### Diagnostic Commands

```bash
# Full health check
aurelis health

# Model availability
aurelis models --verbose

# Token validation
aurelis auth status

# Configuration check
aurelis config validate
```

### Debug Logging

```yaml
# .aurelis.yaml
logging:
  level: "DEBUG"
  handlers:
    - "console"
    - "file"
  file_path: "aurelis_debug.log"
```

## 🎯 Best Practices

### 1. Model Selection Strategy

```python
# Use task-specific models
CODE_TASKS = [TaskType.CODE_GENERATION, TaskType.CODE_OPTIMIZATION]
DOCS_TASKS = [TaskType.DOCUMENTATION, TaskType.EXPLANATIONS]
COMPLEX_TASKS = [TaskType.ARCHITECTURAL_DECISIONS, TaskType.COMPLEX_REASONING]

# Let Aurelis choose automatically
request = ModelRequest(
    prompt=your_prompt,
    task_type=detected_task_type  # Aurelis selects optimal model
)
```

### 2. Cost Optimization

```python
# Use appropriate models for task complexity
simple_request = ModelRequest(
    prompt="Fix this typo",
    model_type=ModelType.GPT_4O_MINI  # Cheaper for simple tasks
)

complex_request = ModelRequest(
    prompt="Design microservices architecture",
    model_type=ModelType.GPT_4O  # Worth the cost for complex tasks
)
```

### 3. Caching Strategy

```python
# Cache documentation requests
docs_request = ModelRequest(
    prompt="Document this function",
    task_type=TaskType.DOCUMENTATION
    # Caching enabled by default
)

# Disable cache for unique generation
unique_request = ModelRequest(
    prompt=f"Generate unique UUID implementation {timestamp}",
    metadata={"cache_disabled": True}
)
```

### 4. Error Handling

```python
async def robust_request(prompt: str) -> str:
    try:
        request = ModelRequest(prompt=prompt)
        response = await orchestrator.send_request(request)
        return response.content
    except ModelError as e:
        logger.error(f"Model request failed: {e}")
        # Fallback logic
        return await fallback_handler(prompt)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "Error: Unable to process request"
```

### 5. Monitoring & Analytics

```python
# Track usage patterns
response = await orchestrator.send_request(request)

# Log metrics
metrics = {
    "model_used": response.model_used,
    "tokens_used": response.token_usage.get("total_tokens", 0),
    "processing_time": response.processing_time,
    "cached": response.cached,
    "confidence": response.confidence
}

analytics_logger.info(json.dumps(metrics))
```

### 6. Security Best Practices

```yaml
# Production security configuration
security:
  token_storage: "keyring"
  audit_logging: true
  request_timeout: 30
  max_retries: 3
  
# Never log sensitive data
logging:
  exclude_patterns:
    - "github_token"
    - "api_key"
    - "password"
```

## 📊 Usage Examples

### Code Generation

```python
request = ModelRequest(
    prompt="""
    Create a Python class for user authentication with:
    - Email/password login
    - Token-based sessions
    - Rate limiting
    - Audit logging
    """,
    task_type=TaskType.CODE_GENERATION,
    system_prompt="Generate production-ready code with proper error handling",
    temperature=0.1
)

response = await orchestrator.send_request(request)
```

### Documentation Generation

```python
request = ModelRequest(
    prompt=f"""
    Document this function:
    
    {function_code}
    
    Include: purpose, parameters, return value, examples, and edge cases.
    """,
    task_type=TaskType.DOCUMENTATION,
    model_type=ModelType.COHERE_COMMAND_R
)
```

### Code Review & Optimization

```python
request = ModelRequest(
    prompt=f"""
    Review and optimize this code for:
    - Performance improvements
    - Security vulnerabilities
    - Code style and best practices
    
    {code_to_review}
    """,
    task_type=TaskType.CODE_OPTIMIZATION,
    system_prompt="You are a senior software engineer conducting a code review"
)
```

## 📈 Advanced Features

### Custom Model Routing

```python
# Override default routing
custom_orchestrator = GitHubModelOrchestrator()
custom_orchestrator.task_model_mapping[TaskType.CODE_GENERATION] = [
    ModelType.GPT_4O,  # Use GPT-4o first
    ModelType.CODESTRAL_2501  # Fallback to Codestral
]
```

### Response Streaming

```python
# Stream responses for long generations
async for chunk in orchestrator.stream_request(request):
    print(chunk.content, end="", flush=True)
```

### Batch Optimization

```python
# Efficient batch processing
requests = [
    ModelRequest(prompt=p, task_type=TaskType.CODE_GENERATION)
    for p in prompts
]

# Process in parallel with rate limiting
responses = await orchestrator.batch_request(
    requests,
    max_concurrent=5,
    rate_limit=10  # requests per second
)
```

## 🔗 Integration Examples

### CLI Integration

```python
@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Generation prompt"),
    model: Optional[str] = typer.Option(None, help="Specific model to use")
):
    """Generate code using GitHub models."""
    orchestrator = get_model_orchestrator()
    
    request = ModelRequest(
        prompt=prompt,
        model_type=ModelType(model) if model else None,
        task_type=TaskType.CODE_GENERATION
    )
    
    response = asyncio.run(orchestrator.send_request(request))
    console.print(response.content)
```

### Interactive Shell Integration

```python
class AurelisShell:
    def __init__(self):
        self.orchestrator = get_model_orchestrator()
    
    async def process_input(self, user_input: str) -> str:
        task_type = self._detect_task_type(user_input)
        
        request = ModelRequest(
            prompt=user_input,
            task_type=task_type,
            temperature=0.1
        )
        
        response = await self.orchestrator.send_request(request)
        return response.content
```

### API Integration

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()
orchestrator = get_model_orchestrator()

@app.post("/api/generate")
async def generate_code(request: GenerationRequest):
    try:
        model_request = ModelRequest(
            prompt=request.prompt,
            task_type=request.task_type,
            temperature=request.temperature or 0.1
        )
        
        response = await orchestrator.send_request(model_request)
        
        return {
            "content": response.content,
            "model_used": response.model_used,
            "tokens_used": response.token_usage,
            "processing_time": response.processing_time
        }
    except ModelError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 📞 Support & Resources

### Documentation
- [API Reference](../api/model-orchestrator.md)
- [Configuration Guide](configuration.md)
- [Installation Guide](installation.md)

### GitHub Resources
- [GitHub Models Marketplace](https://github.com/marketplace/models)
- [Azure AI Inference Docs](https://docs.github.com/en/github-models)
- [Token Management Guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

### Support Channels
- **Issues**: [GitHub Issues](https://github.com/kanopusdev/aurelis/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kanopusdev/aurelis/discussions)
- **Enterprise**: enterprise@kanopus.org

---

**Last Updated**: December 2024  
**Version**: 2.0.0  
**Author**: Gamecooler19 (Lead Developer at Kanopus)

*Aurelis - Where AI meets enterprise code development*
