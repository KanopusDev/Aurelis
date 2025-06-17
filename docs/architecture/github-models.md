# GitHub Models Integration Architecture

**Technical architecture for GitHub Models integration via Azure AI Inference**

This document provides detailed technical architecture for Aurelis's exclusive integration with GitHub Models through Azure AI Inference, covering system design, data flow, security architecture, and implementation patterns.

## 📋 Table of Contents

1. [Integration Overview](#integration-overview)
2. [Authentication Architecture](#authentication-architecture)
3. [API Communication Layer](#api-communication-layer)
4. [Model Orchestration](#model-orchestration)
5. [Data Flow Architecture](#data-flow-architecture)
6. [Caching Architecture](#caching-architecture)
7. [Error Handling & Resilience](#error-handling--resilience)
8. [Performance Optimization](#performance-optimization)
9. [Security Architecture](#security-architecture)
10. [Monitoring & Observability](#monitoring--observability)

## 🔍 Integration Overview

### GitHub Models Ecosystem

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Models Platform                   │
├─────────────────────────────────────────────────────────────┤
│  Azure AI Inference Layer                                  │
│  ├── Model Endpoints (OpenAI Compatible)                   │
│  ├── Authentication & Authorization                        │
│  ├── Rate Limiting & Quotas                               │
│  └── Usage Tracking & Analytics                           │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS / OpenAI API Protocol
┌─────────────────────▼───────────────────────────────────────┐
│                 Aurelis Integration Layer                   │
├─────────────────────────────────────────────────────────────┤
│  Model Orchestrator                                        │
│  ├── Intelligent Routing                                   │
│  ├── Fallback Management                                   │
│  ├── Response Caching                                      │
│  └── Performance Monitoring                                │
└─────────────────────────────────────────────────────────────┘
```

### Supported Model Portfolio

| Provider | Models | API Endpoint | Authentication |
|----------|--------|--------------|----------------|
| **Mistral** | Codestral-2501, Large, Nemo | `models.inference.ai.azure.com` | GitHub Token |
| **OpenAI** | GPT-4o, GPT-4o-mini | `models.inference.ai.azure.com` | GitHub Token |
| **Cohere** | Command-R, Command-R+ | `models.inference.ai.azure.com` | GitHub Token |
| **Meta** | Llama 3.1 70B, 405B | `models.inference.ai.azure.com` | GitHub Token |

### Integration Benefits

1. **Unified Authentication**: Single GitHub token for all models
2. **Enterprise Reliability**: Azure infrastructure with SLA guarantees
3. **Cost Efficiency**: Centralized billing and usage tracking
4. **Developer Experience**: Familiar OpenAI-compatible API patterns
5. **Security**: Enterprise-grade security and compliance

## 🔐 Authentication Architecture

### Token Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User/System   │    │     Aurelis     │    │ GitHub Models   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ 1. Set GITHUB_TOKEN  │                      │
          ├─────────────────────►│                      │
          │                      │                      │
          │                      │ 2. Validate Token   │
          │                      ├─────────────────────►│
          │                      │                      │
          │                      │ 3. Token Valid       │
          │                      │◄─────────────────────┤
          │                      │                      │
          │                      │ 4. Store Encrypted   │
          │                      ├─┐                    │
          │                      │ │                    │
          │                      │◄┘                    │
          │                      │                      │
          │ 5. Ready for Requests│                      │
          │◄─────────────────────┤                      │
```

### Token Management Implementation

```python
class GitHubTokenManager:
    """Secure GitHub token management for model access."""
    
    def __init__(self):
        self.keyring_service = "aurelis-github-models"
        self.token_cache = {}
        self.validation_cache = {}
    
    def get_token(self) -> str:
        """Get GitHub token with fallback strategy."""
        
        # 1. Environment variable (primary)
        token = os.getenv("GITHUB_TOKEN")
        if token:
            return self._validate_and_cache(token)
        
        # 2. Configuration file
        token = self._get_config_token()
        if token:
            return self._validate_and_cache(token)
        
        # 3. System keyring (enterprise)
        token = self._get_keyring_token()
        if token:
            return self._validate_and_cache(token)
        
        raise AuthenticationError("GitHub token not found")
    
    def _validate_and_cache(self, token: str) -> str:
        """Validate token format and cache if valid."""
        
        if not token.startswith('ghp_'):
            raise AuthenticationError("Invalid GitHub token format")
        
        # Cache validation result
        if token not in self.validation_cache:
            self.validation_cache[token] = self._validate_token_with_api(token)
        
        if not self.validation_cache[token]:
            raise AuthenticationError("GitHub token validation failed")
        
        return token
    
    async def _validate_token_with_api(self, token: str) -> bool:
        """Validate token with GitHub API."""
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://models.inference.ai.azure.com/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
```

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Layers                        │
├─────────────────────────────────────────────────────────────┤
│  Application Layer                                          │
│  ├── Token Encryption at Rest                              │
│  ├── Memory Protection                                      │
│  ├── Audit Logging                                         │
│  └── Request Sanitization                                  │
├─────────────────────────────────────────────────────────────┤
│  Transport Layer                                           │
│  ├── TLS 1.3 Encryption                                    │
│  ├── Certificate Pinning                                   │
│  ├── Request Signing                                       │
│  └── Response Validation                                   │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                      │
│  ├── Azure Security Controls                               │
│  ├── GitHub Authentication                                 │
│  ├── Rate Limiting                                         │
│  └── DDoS Protection                                       │
└─────────────────────────────────────────────────────────────┘
```

## 🔌 API Communication Layer

### OpenAI-Compatible Client Implementation

```python
class GitHubModelClient:
    """OpenAI-compatible client for GitHub Models."""
    
    def __init__(self, model_type: ModelType):
        self.model_type = model_type
        self.endpoint = "https://models.inference.ai.azure.com"
        self.client = None
        
        # Model name mapping
        self.model_names = {
            ModelType.CODESTRAL_2501: "Codestral-2501",
            ModelType.GPT_4O: "gpt-4o",
            ModelType.GPT_4O_MINI: "gpt-4o-mini",
            ModelType.COHERE_COMMAND_R: "Cohere-command-r",
            ModelType.COHERE_COMMAND_R_PLUS: "Cohere-command-r-plus",
            ModelType.META_LLAMA_3_1_70B: "Meta-Llama-3.1-70B-Instruct",
            ModelType.META_LLAMA_3_1_405B: "Meta-Llama-3.1-405B-Instruct",
            ModelType.MISTRAL_LARGE: "Mistral-large",
            ModelType.MISTRAL_NEMO: "Mistral-Nemo"
        }
    
    def _get_client(self) -> openai.AsyncOpenAI:
        """Get or create OpenAI client for GitHub Models."""
        
        if self.client is None:
            self.client = openai.AsyncOpenAI(
                api_key=self.get_api_key(),
                base_url=self.endpoint,
                timeout=httpx.Timeout(60.0, connect=10.0),
                max_retries=0  # We handle retries ourselves
            )
        
        return self.client
    
    async def send_request(self, request: ModelRequest) -> ModelResponse:
        """Send request to GitHub Models API."""
        
        client = self._get_client()
        model_name = self.model_names[self.model_type]
        
        # Prepare OpenAI-format messages
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        # API call with comprehensive error handling
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False
            )
            
            return self._process_response(response, request)
            
        except openai.APIError as e:
            raise ModelError(f"GitHub Models API error: {e}")
        except openai.RateLimitError as e:
            raise RateLimitError(f"Rate limit exceeded: {e}")
        except openai.AuthenticationError as e:
            raise AuthenticationError(f"GitHub token invalid: {e}")
```

### Request/Response Protocol

```
Request Flow:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ModelRequest  │    │  GitHub Models  │    │   ModelResponse │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ 1. Request Validation│                      │
          ├─┐                    │                      │
          │ │                    │                      │
          │◄┘                    │                      │
          │                      │                      │
          │ 2. OpenAI Format     │                      │
          ├─────────────────────►│                      │
          │                      │                      │
          │                      │ 3. Model Processing  │
          │                      ├─┐                    │
          │                      │ │                    │
          │                      │◄┘                    │
          │                      │                      │
          │                      │ 4. Response Format   │
          │                      ├─────────────────────►│
          │                      │                      │
          │ 5. Response Parsing  │                      │
          │◄─────────────────────┤                      │
          │                      │                      │
          │ 6. Validated Response│                      │
          │◄─────────────────────┼──────────────────────┤
```

### Message Format Specification

```json
{
  "request": {
    "model": "Codestral-2501",
    "messages": [
      {
        "role": "system",
        "content": "You are an expert Python developer..."
      },
      {
        "role": "user", 
        "content": "Create a function to validate email addresses"
      }
    ],
    "temperature": 0.1,
    "max_tokens": 1000,
    "stream": false
  },
  "response": {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "Codestral-2501",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "def validate_email(email: str) -> bool:..."
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 25,
      "completion_tokens": 150,
      "total_tokens": 175
    }
  }
}
```

## 🎛️ Model Orchestration

### Intelligent Routing Engine

```python
class ModelRoutingEngine:
    """Intelligent model selection and routing."""
    
    def __init__(self):
        self.task_model_mapping = {
            TaskType.CODE_GENERATION: [
                ModelType.CODESTRAL_2501,
                ModelType.GPT_4O,
                ModelType.META_LLAMA_3_1_70B
            ],
            TaskType.DOCUMENTATION: [
                ModelType.COHERE_COMMAND_R,
                ModelType.COHERE_COMMAND_R_PLUS,
                ModelType.GPT_4O_MINI
            ],
            TaskType.COMPLEX_REASONING: [
                ModelType.GPT_4O,
                ModelType.META_LLAMA_3_1_405B,
                ModelType.MISTRAL_LARGE
            ]
        }
        
        self.model_performance = {}
        self.model_availability = {}
    
    def select_optimal_model(
        self, 
        task_type: TaskType, 
        context: Dict[str, Any] = None
    ) -> ModelType:
        """Select optimal model based on task and context."""
        
        candidates = self.task_model_mapping.get(task_type, [])
        
        if not candidates:
            return ModelType.GPT_4O_MINI  # Default fallback
        
        # Filter by availability
        available_candidates = [
            model for model in candidates 
            if self._is_model_available(model)
        ]
        
        if not available_candidates:
            raise ModelError(f"No available models for task type: {task_type}")
        
        # Performance-based selection
        if context and "performance_priority" in context:
            return self._select_by_performance(available_candidates, context)
        
        # Cost-based selection
        if context and "cost_priority" in context:
            return self._select_by_cost(available_candidates)
        
        # Default: First available (ordered by preference)
        return available_candidates[0]
    
    def _is_model_available(self, model_type: ModelType) -> bool:
        """Check model availability with circuit breaker."""
        
        # Check circuit breaker state
        if self._is_circuit_open(model_type):
            return False
        
        # Check recent availability
        last_check = self.model_availability.get(model_type, {}).get("last_check", 0)
        if time.time() - last_check < 60:  # Cache for 1 minute
            return self.model_availability[model_type]["available"]
        
        # Perform availability check
        return self._check_model_health(model_type)
```

### Fallback Strategy Architecture

```
Primary Model Request
         │
         ▼
    ┌─────────┐     Success    ┌─────────────┐
    │ Execute │────────────────│   Return    │
    │ Request │                │  Response   │
    └────┬────┘                └─────────────┘
         │ Failure
         ▼
    ┌─────────┐     Available  ┌─────────────┐
    │ Check   │───────────────►│   Execute   │
    │Fallback │                │   Fallback  │
    │ Model   │                └──────┬──────┘
    └────┬────┘                       │
         │ Not Available              │ Success
         ▼                            ▼
    ┌─────────┐                  ┌─────────────┐
    │ Check   │                  │   Return    │
    │Secondary│                  │  Response   │
    │Fallback │                  └─────────────┘
    └────┬────┘                       ▲
         │                            │
         ▼                            │ Success
    ┌─────────┐                       │
    │ Execute │──────────────────────┘
    │Secondary│
    │Fallback │
    └────┬────┘
         │ All Failed
         ▼
    ┌─────────┐
    │ Return  │
    │ Error   │
    └─────────┘
```

## 🔄 Data Flow Architecture

### End-to-End Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Application                         │
└─────────────────────┬───────────────────────────────────────┘
                      │ ModelRequest
┌─────────────────────▼───────────────────────────────────────┐
│               Model Orchestrator                            │
│  ├── Request Validation                                     │
│  ├── Model Selection                                        │
│  ├── Cache Check                                           │
│  └── Circuit Breaker Check                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ Validated Request
┌─────────────────────▼───────────────────────────────────────┐
│                GitHub Model Client                         │
│  ├── Authentication                                        │
│  ├── Request Formatting                                    │
│  ├── API Communication                                     │
│  └── Response Processing                                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS/OpenAI Protocol
┌─────────────────────▼───────────────────────────────────────┐
│              GitHub Models Platform                        │
│  ├── Azure AI Inference                                    │
│  ├── Model Execution                                       │
│  ├── Rate Limiting                                         │
│  └── Usage Tracking                                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ Model Response
┌─────────────────────▼───────────────────────────────────────┐
│                Response Processing                          │
│  ├── Response Validation                                   │
│  ├── Confidence Calculation                               │
│  ├── Metrics Collection                                    │
│  └── Cache Storage                                         │
└─────────────────────┬───────────────────────────────────────┘
                      │ ModelResponse
┌─────────────────────▼───────────────────────────────────────┐
│                 User Application                           │
└─────────────────────────────────────────────────────────────┘
```

### Concurrent Request Handling

```python
class ConcurrentRequestManager:
    """Manage concurrent requests with rate limiting."""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.request_queue = asyncio.Queue()
        self.active_requests = {}
        
    async def process_request(
        self, 
        request: ModelRequest,
        model_type: ModelType
    ) -> ModelResponse:
        """Process request with concurrency control."""
        
        request_id = self._generate_request_id()
        
        async with self.semaphore:
            # Track active request
            self.active_requests[request_id] = {
                "start_time": time.time(),
                "model_type": model_type,
                "task_type": request.task_type
            }
            
            try:
                client = self._get_client(model_type)
                response = await client.send_request(request)
                
                # Update request tracking
                self.active_requests[request_id]["status"] = "completed"
                self.active_requests[request_id]["end_time"] = time.time()
                
                return response
                
            except Exception as e:
                self.active_requests[request_id]["status"] = "failed"
                self.active_requests[request_id]["error"] = str(e)
                raise
                
            finally:
                # Cleanup tracking
                if request_id in self.active_requests:
                    del self.active_requests[request_id]
    
    def get_active_request_stats(self) -> Dict[str, Any]:
        """Get statistics about active requests."""
        
        current_time = time.time()
        
        return {
            "active_count": len(self.active_requests),
            "average_duration": self._calculate_average_duration(current_time),
            "requests_by_model": self._group_by_model(),
            "requests_by_task": self._group_by_task()
        }
```

## 💾 Caching Architecture

### Multi-Layer Cache Design

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
├─────────────────────────────────────────────────────────────┤
│  In-Memory Cache (L1)                                      │
│  ├── LRU Cache (1000 entries)                              │
│  ├── TTL: 5 minutes                                        │
│  ├── Size: ~50MB                                           │
│  └── Hit Rate: ~60%                                        │
├─────────────────────────────────────────────────────────────┤
│  Redis Cache (L2)                                          │
│  ├── Distributed Cache                                     │
│  ├── TTL: 1 hour                                          │
│  ├── Size: ~1GB                                           │
│  └── Hit Rate: ~30%                                        │
├─────────────────────────────────────────────────────────────┤
│  Persistent Cache (L3)                                     │
│  ├── Database Storage                                      │
│  ├── TTL: 24 hours                                        │
│  ├── Size: Unlimited                                      │
│  └── Hit Rate: ~10%                                        │
└─────────────────────────────────────────────────────────────┘
```

### Cache Key Strategy

```python
class CacheKeyManager:
    """Generate and manage cache keys for model responses."""
    
    def generate_cache_key(self, request: ModelRequest) -> str:
        """Generate deterministic cache key."""
        
        # Content components for hashing
        content_parts = [
            request.model_type.value,
            request.task_type.value,
            self._normalize_prompt(request.prompt),
            request.system_prompt or "",
            str(request.temperature),
            str(request.max_tokens or ""),
        ]
        
        # Add metadata if it affects response
        if request.metadata:
            relevant_metadata = self._extract_relevant_metadata(request.metadata)
            if relevant_metadata:
                content_parts.append(json.dumps(relevant_metadata, sort_keys=True))
        
        # Generate stable hash
        content = ":".join(content_parts)
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _normalize_prompt(self, prompt: str) -> str:
        """Normalize prompt for consistent caching."""
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', prompt.strip())
        
        # Convert to lowercase for case-insensitive caching
        # (only for documentation/explanation tasks)
        return normalized
    
    def _extract_relevant_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata that affects response generation."""
        
        relevant_keys = {
            "language", "framework", "style", "complexity",
            "target_audience", "code_style", "documentation_format"
        }
        
        return {
            key: value for key, value in metadata.items()
            if key in relevant_keys
        }
```

### Cache Invalidation Strategy

```python
class CacheInvalidationManager:
    """Manage cache invalidation and updates."""
    
    def __init__(self):
        self.invalidation_rules = {
            TaskType.CODE_GENERATION: {
                "ttl": 1800,  # 30 minutes
                "invalidate_on": ["code_style_change", "framework_update"]
            },
            TaskType.DOCUMENTATION: {
                "ttl": 3600,  # 1 hour
                "invalidate_on": ["api_change", "documentation_standard_update"]
            },
            TaskType.EXPLANATION: {
                "ttl": 7200,  # 2 hours
                "invalidate_on": ["concept_change"]
            }
        }
    
    async def invalidate_related_cache(
        self, 
        invalidation_event: str, 
        context: Dict[str, Any]
    ):
        """Invalidate cache entries based on events."""
        
        cache_keys_to_invalidate = []
        
        for task_type, rules in self.invalidation_rules.items():
            if invalidation_event in rules["invalidate_on"]:
                # Find related cache keys
                related_keys = await self._find_related_cache_keys(
                    task_type, context
                )
                cache_keys_to_invalidate.extend(related_keys)
        
        # Invalidate across all cache layers
        await self._invalidate_cache_keys(cache_keys_to_invalidate)
    
    async def _find_related_cache_keys(
        self, 
        task_type: TaskType, 
        context: Dict[str, Any]
    ) -> List[str]:
        """Find cache keys related to the invalidation context."""
        
        # Implementation would search cache metadata
        # to find keys that match the invalidation context
        pass
```

## ⚠️ Error Handling & Resilience

### Circuit Breaker Implementation

```python
class ModelCircuitBreaker:
    """Circuit breaker for model availability management."""
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.model_states = {}  # model_type -> CircuitState
        self.failure_counts = {}
        self.last_failure_time = {}
        self.half_open_calls = {}
    
    async def call_with_circuit_breaker(
        self, 
        model_type: ModelType,
        request_func: Callable,
        *args, **kwargs
    ):
        """Execute request with circuit breaker protection."""
        
        state = self._get_circuit_state(model_type)
        
        if state == CircuitState.OPEN:
            if self._should_attempt_reset(model_type):
                self._set_half_open(model_type)
            else:
                raise ModelError(f"Circuit breaker OPEN for {model_type}")
        
        if state == CircuitState.HALF_OPEN:
            if self._too_many_half_open_calls(model_type):
                raise ModelError(f"Too many half-open calls for {model_type}")
        
        try:
            result = await request_func(*args, **kwargs)
            self._on_success(model_type)
            return result
            
        except Exception as e:
            self._on_failure(model_type)
            raise e
    
    def _on_success(self, model_type: ModelType):
        """Handle successful request."""
        self.failure_counts[model_type] = 0
        self.model_states[model_type] = CircuitState.CLOSED
        self.half_open_calls[model_type] = 0
    
    def _on_failure(self, model_type: ModelType):
        """Handle failed request."""
        self.failure_counts[model_type] = (
            self.failure_counts.get(model_type, 0) + 1
        )
        self.last_failure_time[model_type] = time.time()
        
        if self.failure_counts[model_type] >= self.failure_threshold:
            self.model_states[model_type] = CircuitState.OPEN
```

### Retry Strategy with Exponential Backoff

```python
class RetryManager:
    """Advanced retry management with exponential backoff."""
    
    def __init__(self):
        self.retry_config = {
            openai.RateLimitError: {
                "max_retries": 5,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "exponential_base": 2.0,
                "jitter": True
            },
            openai.APIConnectionError: {
                "max_retries": 3,
                "base_delay": 0.5,
                "max_delay": 10.0,
                "exponential_base": 2.0,
                "jitter": True
            },
            ModelError: {
                "max_retries": 2,
                "base_delay": 0.1,
                "max_delay": 5.0,
                "exponential_base": 2.0,
                "jitter": False
            }
        }
    
    async def retry_with_backoff(
        self, 
        func: Callable,
        *args, **kwargs
    ) -> Any:
        """Execute function with intelligent retry logic."""
        
        last_exception = None
        
        for exception_type, config in self.retry_config.items():
            try:
                for attempt in range(config["max_retries"] + 1):
                    try:
                        return await func(*args, **kwargs)
                        
                    except exception_type as e:
                        last_exception = e
                        
                        if attempt == config["max_retries"]:
                            break
                        
                        delay = self._calculate_delay(
                            attempt, 
                            config["base_delay"],
                            config["max_delay"],
                            config["exponential_base"],
                            config["jitter"]
                        )
                        
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        
                        await asyncio.sleep(delay)
                        
            except Exception as e:
                # Not a retryable exception
                if not isinstance(e, tuple(self.retry_config.keys())):
                    raise e
        
        raise last_exception
    
    def _calculate_delay(
        self, 
        attempt: int,
        base_delay: float,
        max_delay: float,
        exponential_base: float,
        jitter: bool
    ) -> float:
        """Calculate delay with exponential backoff and jitter."""
        
        delay = base_delay * (exponential_base ** attempt)
        delay = min(delay, max_delay)
        
        if jitter:
            # Add random jitter (±25%)
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)
```

## 🚀 Performance Optimization

### Request Batching and Parallelization

```python
class BatchRequestProcessor:
    """Process multiple requests efficiently."""
    
    def __init__(self, max_batch_size: int = 10, max_concurrent: int = 5):
        self.max_batch_size = max_batch_size
        self.max_concurrent = max_concurrent
        self.request_queue = asyncio.Queue()
        self.batch_processor = None
    
    async def process_batch(
        self, 
        requests: List[ModelRequest]
    ) -> List[ModelResponse]:
        """Process batch of requests with optimal parallelization."""
        
        # Group requests by model type for efficiency
        model_groups = self._group_requests_by_model(requests)
        
        # Process each model group in parallel
        all_responses = []
        
        for model_type, model_requests in model_groups.items():
            # Process requests for this model in smaller batches
            batches = self._create_batches(model_requests, self.max_batch_size)
            
            # Process batches concurrently (but limited)
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def process_batch_with_semaphore(batch):
                async with semaphore:
                    return await self._process_model_batch(model_type, batch)
            
            batch_tasks = [
                process_batch_with_semaphore(batch) 
                for batch in batches
            ]
            
            batch_results = await asyncio.gather(*batch_tasks)
            
            # Flatten results
            for batch_responses in batch_results:
                all_responses.extend(batch_responses)
        
        # Restore original order
        return self._restore_original_order(requests, all_responses)
    
    def _group_requests_by_model(
        self, 
        requests: List[ModelRequest]
    ) -> Dict[ModelType, List[Tuple[int, ModelRequest]]]:
        """Group requests by model type, preserving order."""
        
        model_groups = {}
        
        for index, request in enumerate(requests):
            model_type = request.model_type or self._select_model(request.task_type)
            
            if model_type not in model_groups:
                model_groups[model_type] = []
            
            model_groups[model_type].append((index, request))
        
        return model_groups
```

### Connection Pooling and Optimization

```python
class OptimizedHTTPClient:
    """Optimized HTTP client for GitHub Models API."""
    
    def __init__(self):
        self.connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=20,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        
        self.timeout = aiohttp.ClientTimeout(
            total=60,  # Total timeout
            connect=10,  # Connection timeout
            sock_read=45  # Socket read timeout
        )
        
        self.session = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create optimized HTTP session."""
        
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": "Aurelis/2.0.0 (https://aurelis.kanopus.org)",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            }
            
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers=headers,
                json_serialize=self._json_serializer
            )
        
        return self.session
    
    def _json_serializer(self, obj) -> str:
        """Optimized JSON serialization."""
        return orjson.dumps(obj).decode()
```

## 🔐 Security Architecture

### Request Sanitization and Validation

```python
class SecurityLayer:
    """Security layer for request sanitization and validation."""
    
    def __init__(self):
        self.sensitive_patterns = [
            r'(?i)(api[_-]?key|token|secret|password)',
            r'(?i)(auth[_-]?token|bearer[_-]?token)',
            r'(?i)(private[_-]?key|secret[_-]?key)',
            r'(?i)(database[_-]?url|db[_-]?password)',
        ]
        
        self.max_prompt_length = 50000  # Prevent excessively large prompts
        self.max_system_prompt_length = 10000
    
    def sanitize_request(self, request: ModelRequest) -> ModelRequest:
        """Sanitize request for security compliance."""
        
        # Validate prompt length
        if len(request.prompt) > self.max_prompt_length:
            raise SecurityError("Prompt exceeds maximum allowed length")
        
        if request.system_prompt and len(request.system_prompt) > self.max_system_prompt_length:
            raise SecurityError("System prompt exceeds maximum allowed length")
        
        # Check for sensitive information
        if self._contains_sensitive_data(request.prompt):
            logger.warning("Potential sensitive data detected in prompt")
            if self._should_block_sensitive_data():
                raise SecurityError("Sensitive data detected in prompt")
        
        # Sanitize metadata
        if request.metadata:
            request.metadata = self._sanitize_metadata(request.metadata)
        
        return request
    
    def _contains_sensitive_data(self, text: str) -> bool:
        """Check if text contains sensitive patterns."""
        
        for pattern in self.sensitive_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata for sensitive information."""
        
        sanitized = {}
        
        for key, value in metadata.items():
            # Skip sensitive keys
            if any(pattern in key.lower() for pattern in ['password', 'secret', 'token', 'key']):
                continue
            
            # Sanitize string values
            if isinstance(value, str):
                value = self._sanitize_string_value(value)
            
            sanitized[key] = value
        
        return sanitized
```

### Audit Logging and Compliance

```python
class AuditLogger:
    """Comprehensive audit logging for compliance."""
    
    def __init__(self):
        self.audit_handler = self._setup_audit_handler()
        self.compliance_mode = self._get_compliance_mode()
    
    def log_model_request(
        self,
        request_id: str,
        model_type: str,
        task_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log model request for audit trail."""
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "model_request",
            "request_id": request_id,
            "model_type": model_type,
            "task_type": task_type,
            "user_id": user_id,
            "metadata": self._sanitize_for_audit(metadata or {}),
            "compliance_level": self.compliance_mode
        }
        
        self.audit_handler.log(audit_entry)
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log security events."""
        
        security_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "security_event",
            "security_event_type": event_type,
            "severity": severity,
            "description": description,
            "context": self._sanitize_for_audit(context or {}),
            "source": "aurelis_github_models"
        }
        
        self.audit_handler.log(security_entry)
    
    def _sanitize_for_audit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for audit logging."""
        
        sanitized = {}
        
        for key, value in data.items():
            # Never log sensitive information
            if any(sensitive in key.lower() for sensitive in ['token', 'key', 'password', 'secret']):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "...[TRUNCATED]"
            else:
                sanitized[key] = value
        
        return sanitized
```

## 📊 Monitoring & Observability

### Metrics Collection Architecture

```python
class MetricsCollector:
    """Comprehensive metrics collection for GitHub Models integration."""
    
    def __init__(self):
        self.request_counter = Counter()
        self.response_time_histogram = Histogram()
        self.token_usage_counter = Counter()
        self.error_counter = Counter()
        self.model_health_gauge = Gauge()
        
        self.custom_metrics = {}
    
    def record_request_metrics(self, response: ModelResponse):
        """Record metrics for completed request."""
        
        labels = {
            "model": response.model_used.value,
            "task_type": response.task_type.value,
            "cached": str(response.cached).lower()
        }
        
        # Request counting
        self.request_counter.labels(**labels).inc()
        
        # Response time
        self.response_time_histogram.labels(
            model=response.model_used.value
        ).observe(response.processing_time)
        
        # Token usage
        for usage_type, count in response.token_usage.items():
            self.token_usage_counter.labels(
                model=response.model_used.value,
                usage_type=usage_type
            ).inc(count)
    
    def record_error_metrics(self, error: Exception, model_type: str):
        """Record error metrics."""
        
        self.error_counter.labels(
            model=model_type,
            error_type=type(error).__name__,
            error_category=self._categorize_error(error)
        ).inc()
    
    def update_model_health(self, model_type: ModelType, health_score: float):
        """Update model health gauge."""
        
        self.model_health_gauge.labels(
            model=model_type.value
        ).set(health_score)
    
    def _categorize_error(self, error: Exception) -> str:
        """Categorize error for metrics."""
        
        if isinstance(error, openai.RateLimitError):
            return "rate_limit"
        elif isinstance(error, openai.AuthenticationError):
            return "authentication"
        elif isinstance(error, openai.APIConnectionError):
            return "connection"
        elif isinstance(error, ModelError):
            return "model_error"
        else:
            return "unknown"
```

### Health Check and Monitoring

```python
class HealthMonitor:
    """Comprehensive health monitoring for GitHub Models integration."""
    
    def __init__(self):
        self.orchestrator = get_model_orchestrator()
        self.health_history = {}
        self.alert_manager = AlertManager()
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        
        health_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {}
        }
        
        # Check individual model health
        model_health = await self._check_model_health()
        health_results["components"]["models"] = model_health
        
        # Check authentication
        auth_health = await self._check_authentication_health()
        health_results["components"]["authentication"] = auth_health
        
        # Check network connectivity
        network_health = await self._check_network_health()
        health_results["components"]["network"] = network_health
        
        # Check cache health
        cache_health = await self._check_cache_health()
        health_results["components"]["cache"] = cache_health
        
        # Determine overall status
        component_statuses = [
            comp["status"] for comp in health_results["components"].values()
        ]
        
        if all(status == "healthy" for status in component_statuses):
            health_results["overall_status"] = "healthy"
        elif any(status == "unhealthy" for status in component_statuses):
            health_results["overall_status"] = "unhealthy"
        else:
            health_results["overall_status"] = "degraded"
        
        # Store health history
        self._store_health_history(health_results)
        
        # Check for alerts
        await self._check_health_alerts(health_results)
        
        return health_results
    
    async def _check_model_health(self) -> Dict[str, Any]:
        """Check health of all GitHub models."""
        
        model_results = {}
        overall_healthy = True
        
        for model_type in ModelType:
            try:
                # Perform lightweight health check
                start_time = time.time()
                
                test_request = ModelRequest(
                    prompt="Health check",
                    model_type=model_type,
                    task_type=TaskType.GENERAL,
                    max_tokens=1
                )
                
                response = await self.orchestrator.send_request(test_request)
                response_time = time.time() - start_time
                
                model_results[model_type.value] = {
                    "status": "healthy",
                    "response_time": response_time,
                    "last_check": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                model_results[model_type.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "models": model_results
        }
```

---

## 📞 Support & Resources

### Technical Documentation
- [System Overview](system-overview.md)
- [Security Architecture](security.md)
- [Performance & Caching](performance.md)
- [Enterprise Features](enterprise.md)

### API Documentation
- [Model Orchestrator API](../api/model-orchestrator.md)
- [Core Types Reference](../api/core-types.md)
- [Configuration API](../api/configuration.md)

### GitHub Resources
- **GitHub Models**: [github.com/marketplace/models](https://github.com/marketplace/models)
- **Azure AI Inference**: [docs.github.com/github-models](https://docs.github.com/en/github-models)
- **OpenAI Compatibility**: [platform.openai.com/docs/api-reference](https://platform.openai.com/docs/api-reference)

### Enterprise Support
- **Email**: enterprise@kanopus.org
- **Documentation**: [Enterprise Installation](../deployment/enterprise.md)
- **Architecture Consulting**: [Contact Sales](https://aurelis.kanopus.org/enterprise)

---

**Last Updated**: December 2024  
**Version**: 2.0.0  
**Author**: Gamecooler19 (Lead Developer at Kanopus)

*Aurelis - Where AI meets enterprise code development*
