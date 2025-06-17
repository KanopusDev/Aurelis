# Aurelis Configuration Guide

**Enterprise-grade configuration management for production environments**

## 📋 Overview

Aurelis uses a hierarchical configuration system designed for enterprise environments with support for:
- Environment-based configuration
- Secure token management
- Team and organizational settings
- Performance optimization
- Compliance and audit requirements

## 🔧 Configuration File Structure

### Primary Configuration File: `.aurelis.yaml`

```yaml
# Aurelis Enterprise Configuration
# Version: 1.0

# GitHub Integration (Required)
github_token: "${GITHUB_TOKEN}"  # Use environment variable

# Model Configuration
models:
  primary: "gpt-4o"                    # Primary model for complex tasks
  fallback: "gpt-4o-mini"              # Fallback for reliability
  code_generation: "codestral-2501"    # Specialized for code generation
  documentation: "cohere-command-r"    # Optimized for documentation
  
  # Model routing preferences
  routing:
    prefer_speed: false                # Prefer quality over speed
    max_retries: 3                    # Maximum retry attempts
    timeout: 60                       # Request timeout in seconds
    
  # Advanced model settings
  advanced:
    temperature: 0.2                  # Lower for more consistent output
    max_tokens: 4000                  # Maximum response length
    concurrent_requests: 5            # Parallel request limit

# Analysis Configuration
analysis:
  max_file_size: "10MB"              # Maximum file size to analyze
  chunk_size: 3500                   # Optimal chunk size for 4K models
  overlap_ratio: 0.15                # Chunk overlap for context preservation
  supported_languages:
    - python
    - javascript
    - typescript
    - java
    - cpp
    - csharp
    - go
    - rust
    - php
    - ruby

# Processing Configuration
processing:
  max_retries: 3                     # Global retry limit
  timeout: 60                        # Global timeout
  concurrent_requests: 5             # Concurrent API requests
  rate_limiting:
    requests_per_minute: 60          # API rate limiting
    burst_limit: 10                  # Burst request limit

# Security Configuration
security:
  audit_logging: true                # Enable audit trails
  secure_token_storage: true         # Use secure token storage
  compliance_mode: false             # Enable for regulated environments
  encrypt_cache: false               # Encrypt cached responses
  
  # Token security
  token_validation: true             # Validate tokens on startup
  token_rotation_days: 90            # Recommend token rotation
  
  # Access control
  allowed_file_patterns:
    - "*.py"
    - "*.js"
    - "*.ts"
    - "*.java"
    - "*.cpp"
    - "*.md"
  
  blocked_file_patterns:
    - "*.key"
    - "*.pem"
    - "*.env"
    - "*secret*"

# Cache Configuration
cache:
  enabled: true                      # Enable response caching
  ttl: 3600                         # Cache TTL in seconds (1 hour)
  max_size: 1000                    # Maximum cached items
  persist: true                     # Persist cache across sessions
  
  # Cache optimization
  compression: true                  # Compress cached data
  cleanup_interval: 86400           # Cleanup interval (24 hours)
  max_disk_usage: "100MB"          # Maximum cache disk usage

# Logging Configuration
logging:
  level: "INFO"                     # Log level: DEBUG, INFO, WARNING, ERROR
  format: "json"                    # Log format: json, text
  
  # File logging
  file_logging: true
  log_directory: ".aurelis/logs"
  max_file_size: "10MB"
  backup_count: 5
  
  # Audit logging
  audit:
    enabled: true
    file: ".aurelis/logs/audit.log"
    include_content: false          # Don't log code content for privacy
    retention_days: 90

# Shell Configuration
shell:
  history_size: 1000               # Command history size
  auto_save_session: true          # Auto-save sessions
  session_timeout: 3600            # Session timeout (1 hour)
  
  # Shell features
  features:
    auto_completion: true          # Enable auto-completion
    syntax_highlighting: true      # Enable syntax highlighting
    progress_indicators: true      # Show progress for long operations
    rich_output: true             # Enable Rich formatting
  
  # Shell appearance
  theme: "monokai"                 # Syntax highlighting theme
  prompt_style: "minimal"          # Prompt style: minimal, full, custom

# Enterprise Configuration
enterprise:
  organization: "Your Organization"
  team: "Engineering"
  environment: "production"         # development, staging, production
  
  # Cost tracking
  cost_tracking: true
  budget_alerts: true
  monthly_limit: 1000              # Monthly API call limit
  
  # Analytics
  usage_analytics: true
  performance_monitoring: true
  error_reporting: true
  
  # Compliance
  data_retention_days: 90
  export_compliance: true
  audit_requirements: "SOX"        # SOX, GDPR, HIPAA, etc.

# Development Configuration
development:
  debug_mode: false                # Enable debug logging
  verbose_errors: false           # Show detailed error traces
  experimental_features: false    # Enable experimental features
  
  # Testing
  mock_responses: false           # Use mock responses for testing
  test_mode: false               # Enable test mode features
```

## 📂 Configuration Locations

### Configuration Resolution Order
1. **Command Line Arguments** (highest priority)
2. **Environment Variables**
3. **Project Configuration** (`.aurelis.yaml` in current directory)
4. **User Configuration** (`~/.aurelis/config.yaml`)
5. **System Configuration** (`/etc/aurelis/config.yaml`)
6. **Default Configuration** (built-in defaults)

### Environment-Specific Configurations

#### Development Environment
```yaml
# .aurelis.dev.yaml
github_token: "${GITHUB_DEV_TOKEN}"

models:
  primary: "gpt-4o-mini"  # Faster/cheaper for development
  
development:
  debug_mode: true
  verbose_errors: true
  experimental_features: true

logging:
  level: "DEBUG"
  
cache:
  ttl: 300  # Shorter cache for development
```

#### Production Environment
```yaml
# .aurelis.prod.yaml
github_token: "${GITHUB_PROD_TOKEN}"

models:
  primary: "gpt-4o"
  fallback: "gpt-4o-mini"

security:
  audit_logging: true
  compliance_mode: true
  encrypt_cache: true

enterprise:
  environment: "production"
  cost_tracking: true
  usage_analytics: true

logging:
  level: "INFO"
  audit:
    enabled: true
    retention_days: 365  # Longer retention for production
```

## 🔐 Environment Variables

### Core Variables
```bash
# Required
export GITHUB_TOKEN="ghp_your_token_here"

# Optional but recommended
export AURELIS_CONFIG_PATH="/path/to/config.yaml"
export AURELIS_LOG_LEVEL="INFO"
export AURELIS_CACHE_DIR="/tmp/aurelis/cache"

# Enterprise variables
export AURELIS_ORG="YourOrganization"
export AURELIS_TEAM="Engineering"
export AURELIS_ENVIRONMENT="production"

# Security variables
export AURELIS_AUDIT_ENABLED="true"
export AURELIS_COMPLIANCE_MODE="true"
export AURELIS_ENCRYPT_CACHE="true"
```

### Environment Variable Override Examples
```bash
# Override primary model
export AURELIS_MODEL_PRIMARY="codestral-2501"

# Override cache settings
export AURELIS_CACHE_TTL="7200"
export AURELIS_CACHE_MAX_SIZE="2000"

# Override security settings
export AURELIS_SECURITY_AUDIT_LOGGING="true"
export AURELIS_SECURITY_COMPLIANCE_MODE="true"

# Override logging
export AURELIS_LOG_LEVEL="DEBUG"
export AURELIS_LOG_FORMAT="json"
```

## 🎛️ Configuration Management Commands

### View Configuration
```bash
# Show current configuration
aurelis config show

# Show specific configuration section
aurelis config show models
aurelis config show security
aurelis config show cache

# Show configuration with sources
aurelis config show --sources

# Export configuration to file
aurelis config export config.yaml
```

### Modify Configuration
```bash
# Set configuration values
aurelis config set models.primary gpt-4o
aurelis config set cache.ttl 7200
aurelis config set security.audit_logging true

# Set nested values
aurelis config set enterprise.organization "My Company"
aurelis config set logging.level DEBUG

# Remove configuration values
aurelis config unset models.fallback
aurelis config unset development.debug_mode
```

### Validate Configuration
```bash
# Validate current configuration
aurelis config validate

# Validate specific config file
aurelis config validate --config /path/to/config.yaml

# Check configuration completeness
aurelis config check

# Test GitHub token and model access
aurelis config test
```

## 🏢 Enterprise Configuration Templates

### Small Team Template
```yaml
# Small team (5-20 developers)
github_token: "${GITHUB_TOKEN}"

models:
  primary: "gpt-4o-mini"
  fallback: "codestral-2501"

processing:
  concurrent_requests: 3
  rate_limiting:
    requests_per_minute: 30

cache:
  enabled: true
  ttl: 3600
  max_size: 500

enterprise:
  team: "Engineering"
  cost_tracking: true
  monthly_limit: 500

security:
  audit_logging: true
```

### Large Enterprise Template
```yaml
# Large enterprise (100+ developers)
github_token: "${GITHUB_TOKEN}"

models:
  primary: "gpt-4o"
  fallback: "gpt-4o-mini"
  code_generation: "codestral-2501"

processing:
  concurrent_requests: 10
  rate_limiting:
    requests_per_minute: 120

cache:
  enabled: true
  ttl: 7200
  max_size: 5000
  persist: true
  compression: true

enterprise:
  organization: "Enterprise Corp"
  environment: "production"
  cost_tracking: true
  usage_analytics: true
  monthly_limit: 10000

security:
  audit_logging: true
  compliance_mode: true
  encrypt_cache: true
  token_validation: true

logging:
  level: "INFO"
  audit:
    enabled: true
    retention_days: 365
```

### Regulated Industry Template
```yaml
# Healthcare/Finance/Government
github_token: "${GITHUB_TOKEN}"

models:
  primary: "gpt-4o"
  fallback: "gpt-4o-mini"

security:
  audit_logging: true
  compliance_mode: true
  encrypt_cache: true
  secure_token_storage: true
  
  # Strict file filtering
  allowed_file_patterns:
    - "*.py"
    - "*.js"
    - "*.md"
  
  blocked_file_patterns:
    - "*.key"
    - "*.pem"
    - "*.env"
    - "*secret*"
    - "*config*"
    - "*credential*"

enterprise:
  audit_requirements: "HIPAA"  # or SOX, GDPR
  data_retention_days: 2555    # 7 years
  export_compliance: true

logging:
  audit:
    enabled: true
    include_content: false     # Never log sensitive content
    retention_days: 2555       # Long-term audit retention

cache:
  enabled: false              # Disable caching for compliance
```

## 🔍 Configuration Troubleshooting

### Common Issues

#### 1. Token Issues
```bash
# Verify token format
echo $GITHUB_TOKEN | grep -E '^ghp_[a-zA-Z0-9]{36}$'

# Test token validity
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Check token permissions
aurelis config test
```

#### 2. Configuration Conflicts
```bash
# Check configuration sources
aurelis config show --sources

# Validate configuration
aurelis config validate

# Reset to defaults
aurelis config reset
```

#### 3. Performance Issues
```bash
# Check current settings
aurelis config show processing
aurelis config show cache

# Optimize for your environment
aurelis config set processing.concurrent_requests 3
aurelis config set cache.max_size 2000
```

#### 4. Security Compliance
```bash
# Enable all security features
aurelis config set security.audit_logging true
aurelis config set security.compliance_mode true
aurelis config set security.encrypt_cache true

# Verify security configuration
aurelis config show security
```

## 📊 Configuration Best Practices

### Security Best Practices
1. **Never hardcode tokens** - Always use environment variables
2. **Enable audit logging** for production environments
3. **Use compliance mode** for regulated industries
4. **Regularly rotate tokens** (every 90 days recommended)
5. **Encrypt sensitive data** including cache files

### Performance Best Practices
1. **Tune concurrent requests** based on your API limits
2. **Optimize cache settings** for your usage patterns
3. **Use appropriate models** for different tasks
4. **Monitor rate limits** and adjust accordingly

### Maintenance Best Practices
1. **Regular configuration audits**
2. **Version control your config templates**
3. **Document environment-specific settings**
4. **Monitor configuration drift**
5. **Test configuration changes** in staging first

---

**📚 Next Steps:**
- [CLI Reference](cli-reference.md) - Learn about command-line usage
- [Shell Guide](shell-guide.md) - Master the interactive shell
- [GitHub Models](github-models.md) - Understand model integration
- [Enterprise Features](../architecture/enterprise.md) - Explore enterprise capabilities
