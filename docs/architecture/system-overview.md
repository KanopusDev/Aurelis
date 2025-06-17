# System Overview

Aurelis is an enterprise-grade AI code assistant built exclusively for GitHub models via Azure AI Inference.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                         │
├─────────────────────────────────────────────────────────────┤
│  CLI Commands  │  Interactive Shell  │  Future: IDE Plugin │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    Application Layer                       │
├─────────────────────────────────────────────────────────────┤
│           Model Orchestrator (Core Engine)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │    Task     │ │   Model     │ │   Cache     │           │
│  │   Router    │ │  Manager    │ │  Manager    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                   Integration Layer                        │
├─────────────────────────────────────────────────────────────┤
│                Azure AI Inference API                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Codestral │ │    GPT-4o   │ │   Cohere    │           │
│  │    2501     │ │    Models   │ │  Command-R  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐                           │
│  │    Meta     │ │   Mistral   │                           │
│  │ Llama 3.1   │ │   Models    │                           │
│  └─────────────┘ └─────────────┘                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                  Infrastructure Layer                      │
├─────────────────────────────────────────────────────────────┤
│  Configuration  │   Security    │   Logging   │   Monitoring│
│   Management    │  & Auth       │  & Metrics  │  & Health   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Model Orchestrator
**Purpose**: Central engine for GitHub model interaction
**Responsibilities**:
- Request routing to appropriate models
- Response caching and optimization
- Error handling and circuit breaking
- Token usage tracking and optimization

**Key Features**:
- Intelligent model selection based on task type
- Automatic fallback to secondary models
- Response caching with TTL and size limits
- Rate limiting and quota management

### 2. Task Router
**Purpose**: Intelligent model selection based on request context
**Responsibilities**:
- Analyze request type and content
- Select optimal model for the task
- Provide fallback model recommendations
- Track model performance metrics

**Routing Logic**:
```python
Code Generation    → Codestral-2501 (Primary) → GPT-4o (Fallback)
Documentation     → Cohere Command-R → GPT-4o-mini
Complex Reasoning → GPT-4o → Meta Llama 405B
Performance Opt   → Codestral-2501 → Meta Llama 70B
```

### 3. Cache Manager
**Purpose**: Optimize performance through intelligent response caching
**Responsibilities**:
- Cache model responses based on request signatures
- Implement TTL and size-based eviction
- Provide cache statistics and monitoring
- Handle cache invalidation scenarios

**Cache Strategy**:
- **Key Generation**: Hash of prompt + model + system prompt
- **TTL**: 1 hour default, configurable
- **Size Limit**: 1000 items default, configurable
- **Eviction**: LRU with TTL expiration

### 4. Configuration System
**Purpose**: Centralized configuration management
**Responsibilities**:
- Load configuration from multiple sources
- Environment variable integration
- Secure credential storage
- Configuration validation and defaults

**Configuration Sources** (in priority order):
1. Command-line arguments
2. Environment variables
3. Project configuration file (`.aurelis.yaml`)
4. User configuration file (`~/.aurelis/config.yaml`)
5. System defaults

### 5. Security Manager
**Purpose**: Handle authentication and secure credential storage
**Responsibilities**:
- GitHub token management
- Secure credential storage using system keyring
- API request authentication
- Token validation and refresh

**Security Features**:
- Encrypted credential storage
- Automatic token validation
- Secure API communication (HTTPS only)
- No sensitive data in logs

## Data Flow

### Request Processing Flow

```
1. User Input (CLI/Shell)
   │
   ▼
2. Request Validation
   │
   ▼
3. Cache Lookup
   │
   ├── Cache Hit ──────────────┐
   │                           │
   ▼                           │
4. Task Analysis               │
   │                           │
   ▼                           │
5. Model Selection             │
   │                           │
   ▼                           │
6. API Request (GitHub Models) │
   │                           │
   ▼                           │
7. Response Processing         │
   │                           │
   ▼                           │
8. Cache Storage               │
   │                           │
   ▼                           ▼
9. Response to User ←──────────┘
```

### Configuration Loading Flow

```
1. Application Start
   │
   ▼
2. Load System Defaults
   │
   ▼
3. Load User Config (~/.aurelis/config.yaml)
   │
   ▼
4. Load Project Config (.aurelis.yaml)
   │
   ▼
5. Apply Environment Variables
   │
   ▼
6. Apply CLI Arguments
   │
   ▼
7. Validate Configuration
   │
   ▼
8. Initialize Components
```

## Authentication Architecture

### GitHub Token Flow

```
1. Token Discovery
   ├── Environment Variable (GITHUB_TOKEN)
   ├── Configuration File
   └── System Keyring
   │
   ▼
2. Token Validation
   ├── Format Validation
   ├── Permission Check
   └── API Test Call
   │
   ▼
3. Secure Storage
   ├── Encrypt Token
   ├── Store in Keyring
   └── Clear Memory
   │
   ▼
4. API Authentication
   ├── Bearer Token Header
   ├── Request Signing
   └── Response Validation
```

## Error Handling Strategy

### Error Categories

1. **Configuration Errors**
   - Missing or invalid configuration
   - Authentication failures
   - Permission issues

2. **Model Errors**  
   - Model unavailable or overloaded
   - Rate limit exceeded
   - API timeout or connectivity issues

3. **Processing Errors**
   - Invalid input format
   - Parsing failures
   - Resource exhaustion

### Recovery Mechanisms

1. **Automatic Retry**
   - Exponential backoff for transient failures
   - Maximum retry count limits
   - Different strategies per error type

2. **Fallback Models**
   - Primary model failure triggers fallback
   - Graceful degradation of capabilities
   - User notification of model switching

3. **Circuit Breaker**
   - Detect persistent failures
   - Temporarily disable failing components
   - Automatic recovery testing

## Performance Characteristics

### Latency Targets
- **Cache Hit**: < 10ms
- **Model Request**: < 30s (depending on complexity)
- **Configuration Load**: < 100ms
- **Authentication**: < 500ms

### Throughput Capabilities
- **Concurrent Requests**: 5 (configurable)
- **Cache Size**: 1000 items (configurable)
- **Request Queue**: 100 items (configurable)

### Resource Requirements
- **Memory**: ~50MB baseline + cache storage
- **CPU**: Low (I/O bound operations)
- **Network**: GitHub API access required
- **Storage**: ~10MB for configuration and cache

## Monitoring & Observability

### Metrics Collection
- **Request Metrics**: Count, latency, error rate
- **Model Metrics**: Token usage, model selection frequency
- **Cache Metrics**: Hit rate, eviction count, size
- **System Metrics**: Memory usage, connection pool status

### Logging Strategy
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: Configurable verbosity
- **Context Preservation**: Request tracking across components
- **Security**: No sensitive data exposure

### Health Checks
- **Component Health**: Configuration, authentication, models
- **Dependency Health**: GitHub API connectivity
- **Performance Health**: Response times, error rates
- **Resource Health**: Memory usage, cache status

## Scalability Considerations

### Current Limitations
- Single-process execution
- Local cache storage
- GitHub API rate limits
- Memory-based cache

### Future Scaling Options
- **Horizontal Scaling**: Load balancing across instances
- **Persistent Cache**: Redis or similar for shared cache
- **Database Integration**: Configuration and metrics storage
- **Microservices**: Component separation for large deployments

## Integration Points

### Current Integrations
- **GitHub Models**: Via Azure AI Inference API
- **System Keyring**: For secure credential storage
- **File System**: Configuration and cache storage
- **Environment**: Configuration and token injection

### Future Integration Opportunities
- **IDE Plugins**: VS Code, JetBrains IDEs
- **CI/CD Systems**: GitHub Actions, Jenkins
- **Development Tools**: Git hooks, pre-commit
- **Monitoring Systems**: Prometheus, Grafana

## Quality Attributes

### Reliability
- Circuit breaker patterns prevent cascade failures
- Automatic retry with exponential backoff
- Fallback model selection for continuity
- Comprehensive error handling and recovery

### Security
- Encrypted credential storage using system keyring
- No sensitive data in logs or temporary files
- HTTPS-only API communication
- Token validation and secure handling

### Performance
- Response caching reduces API calls
- Async processing prevents blocking
- Connection pooling for efficiency
- Intelligent model selection minimizes latency

### Maintainability
- Clean architecture with separation of concerns
- Comprehensive type hints and documentation
- Modular design enables isolated testing
- Clear error messages aid troubleshooting

### Usability
- Simple CLI interface with helpful output
- Interactive shell mode for exploration
- Automatic configuration with sensible defaults
- Clear documentation and examples

## See Also

- [Component Diagram](component-diagram.md)
- [Data Flow](data-flow.md)
- [Model System](model-system.md)
- [Security Architecture](security-architecture.md)
