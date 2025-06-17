# Configuration API Reference

This document provides comprehensive information about Aurelis configuration management, including settings, environment variables, file formats, and dynamic configuration updates.

## Table of Contents

- [Overview](#overview)
- [Configuration Classes](#configuration-classes)
- [Configuration Sources](#configuration-sources)
- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)
- [Dynamic Configuration](#dynamic-configuration)
- [Validation](#validation)
- [Security](#security)
- [Advanced Features](#advanced-features)
- [Usage Examples](#usage-examples)

## Overview

Aurelis uses a hierarchical configuration system that supports multiple sources, validation, and dynamic updates. Configuration can be loaded from environment variables, YAML/JSON files, command-line arguments, and programmatic settings.

### Configuration Hierarchy

1. Command-line arguments (highest priority)
2. Environment variables
3. Configuration files
4. Default values (lowest priority)

## Configuration Classes

### AurelisConfig

```python
from aurelis.config import AurelisConfig
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class AurelisConfig:
    """Main configuration class for Aurelis"""
    
    # Application settings
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server settings
    server: ServerConfig = field(default_factory=ServerConfig)
    
    # Model settings
    models: ModelSettings = field(default_factory=ModelSettings)
    
    # Database settings
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # Cache settings
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # Security settings
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # API settings
    api: APIConfig = field(default_factory=APIConfig)
    
    # Monitoring settings
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Feature flags
    features: FeatureFlags = field(default_factory=FeatureFlags)
```

### ServerConfig

```python
@dataclass
class ServerConfig:
    """Server configuration settings"""
    
    host: str = "localhost"
    port: int = 8080
    workers: int = 1
    max_connections: int = 1000
    timeout: int = 30
    keepalive: int = 2
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    request_size_limit: int = 10 * 1024 * 1024  # 10MB
```

### ModelSettings

```python
@dataclass
class ModelSettings:
    """Model configuration settings"""
    
    default_model: str = "github-gpt-4o"
    fallback_models: List[str] = field(default_factory=lambda: ["github-gpt-4o-mini"])
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    cache_responses: bool = True
    cache_ttl: int = 3600
    
    # Provider configurations
    github: GitHubModelConfig = field(default_factory=GitHubModelConfig)
    openai: OpenAIModelConfig = field(default_factory=OpenAIModelConfig)
    anthropic: AnthropicModelConfig = field(default_factory=AnthropicModelConfig)
    azure: AzureModelConfig = field(default_factory=AzureModelConfig)
```

### DatabaseConfig

```python
@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    
    url: str = "sqlite:///aurelis.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    autocommit: bool = False
    autoflush: bool = True
    
    # Migration settings
    migration_enabled: bool = True
    migration_path: str = "migrations"
    
    # Backup settings
    backup_enabled: bool = False
    backup_interval: int = 86400  # 24 hours
    backup_retention: int = 7  # days
```

### CacheConfig

```python
@dataclass
class CacheConfig:
    """Cache configuration settings"""
    
    enabled: bool = True
    backend: str = "memory"  # "memory", "redis", "memcached"
    ttl: int = 3600
    max_size: int = 1000
    
    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    redis_connection_pool_size: int = 10
    
    # Memcached settings
    memcached_servers: List[str] = field(default_factory=lambda: ["localhost:11211"])
    
    # Cache strategies
    model_cache_enabled: bool = True
    response_cache_enabled: bool = True
    file_cache_enabled: bool = True
```

### SecurityConfig

```python
@dataclass
class SecurityConfig:
    """Security configuration settings"""
    
    secret_key: str = "development-secret-key"
    algorithm: str = "HS256"
    token_expire_minutes: int = 1440  # 24 hours
    
    # API key management
    api_keys_enabled: bool = True
    api_key_header: str = "X-API-Key"
    api_key_length: int = 32
    
    # Rate limiting
    rate_limiting_enabled: bool = True
    rate_limit_storage: str = "memory"  # "memory", "redis"
    
    # CORS settings
    cors_allow_credentials: bool = False
    cors_allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST"])
    cors_allow_headers: List[str] = field(default_factory=lambda: ["*"])
    
    # Encryption
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    encryption_algorithm: str = "AES-256-GCM"
```

## Configuration Sources

### Environment Variables

```python
from aurelis.config import load_from_environment

# Load configuration from environment variables
config = load_from_environment()

# Environment variable mapping
ENV_MAPPING = {
    "AURELIS_ENV": "environment",
    "AURELIS_DEBUG": "debug",
    "AURELIS_LOG_LEVEL": "log_level",
    "AURELIS_HOST": "server.host",
    "AURELIS_PORT": "server.port",
    "AURELIS_WORKERS": "server.workers",
    "DATABASE_URL": "database.url",
    "REDIS_URL": "cache.redis_url",
    "SECRET_KEY": "security.secret_key",
    "GITHUB_TOKEN": "models.github.api_key",
    "OPENAI_API_KEY": "models.openai.api_key",
    "ANTHROPIC_API_KEY": "models.anthropic.api_key"
}
```

### Configuration Files

#### YAML Configuration

```yaml
# config/production.yaml
environment: production
debug: false
log_level: INFO

server:
  host: 0.0.0.0
  port: 8080
  workers: 4
  ssl_enabled: true
  ssl_cert_path: /etc/ssl/certs/aurelis.crt
  ssl_key_path: /etc/ssl/private/aurelis.key

models:
  default_model: github-gpt-4o
  fallback_models:
    - github-gpt-4o-mini
    - openai-gpt-4o-mini
  max_retries: 3
  timeout: 30
  
  github:
    api_key: ${GITHUB_TOKEN}
    base_url: https://models.inference.ai.azure.com
    
  openai:
    api_key: ${OPENAI_API_KEY}
    organization: ${OPENAI_ORG_ID}

database:
  url: postgresql://user:pass@localhost:5432/aurelis
  pool_size: 10
  max_overflow: 20

cache:
  enabled: true
  backend: redis
  redis_url: redis://localhost:6379/0
  ttl: 3600

security:
  secret_key: ${SECRET_KEY}
  api_keys_enabled: true
  rate_limiting_enabled: true

monitoring:
  enabled: true
  metrics_port: 9090
  health_check_interval: 30

features:
  code_analysis: true
  auto_completion: true
  documentation_generation: true
```

#### JSON Configuration

```json
{
  "environment": "development",
  "debug": true,
  "log_level": "DEBUG",
  "server": {
    "host": "localhost",
    "port": 8080,
    "workers": 1
  },
  "models": {
    "default_model": "github-gpt-4o-mini",
    "github": {
      "api_key": "${GITHUB_TOKEN}"
    }
  },
  "database": {
    "url": "sqlite:///aurelis_dev.db",
    "echo": true
  },
  "cache": {
    "enabled": true,
    "backend": "memory"
  }
}
```

### Loading Configuration

```python
from aurelis.config import ConfigLoader

# Load from file
loader = ConfigLoader()
config = loader.load_from_file("config/production.yaml")

# Load from multiple sources
config = loader.load_from_sources([
    "config/base.yaml",
    "config/production.yaml",
    "environment",
    "command_line"
])

# Load with environment variable substitution
config = loader.load_with_substitution("config/production.yaml")
```

## Environment Variables

### Standard Environment Variables

```bash
# Core settings
export AURELIS_ENV=production
export AURELIS_DEBUG=false
export AURELIS_LOG_LEVEL=INFO

# Server settings
export AURELIS_HOST=0.0.0.0
export AURELIS_PORT=8080
export AURELIS_WORKERS=4

# Database
export DATABASE_URL=postgresql://user:pass@localhost:5432/aurelis

# Cache
export REDIS_URL=redis://localhost:6379/0

# Security
export SECRET_KEY=your-secret-key-here
export AURELIS_API_KEYS_ENABLED=true

# Model API keys
export GITHUB_TOKEN=your-github-token
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key

# Azure settings
export AZURE_OPENAI_API_KEY=your-azure-key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Monitoring
export AURELIS_METRICS_ENABLED=true
export AURELIS_METRICS_PORT=9090
```

### Environment Variable Validation

```python
from aurelis.config import EnvironmentValidator

validator = EnvironmentValidator()

# Validate required environment variables
required_vars = [
    "AURELIS_ENV",
    "SECRET_KEY",
    "DATABASE_URL"
]

validation_result = validator.validate_required(required_vars)
if not validation_result.is_valid:
    raise ConfigurationError(f"Missing variables: {validation_result.missing}")
```

## Configuration Files

### File Formats

Aurelis supports multiple configuration file formats:

- **YAML** (.yaml, .yml) - Recommended for human readability
- **JSON** (.json) - Good for programmatic generation
- **TOML** (.toml) - Alternative structured format
- **INI** (.ini) - Legacy support

### Configuration Locations

```python
# Default configuration search paths
CONFIG_SEARCH_PATHS = [
    "./aurelis.yaml",
    "./config/aurelis.yaml",
    "~/.aurelis/config.yaml",
    "/etc/aurelis/config.yaml",
    "./aurelis.json",
    "./config/aurelis.json"
]
```

### Configuration Profiles

```python
from aurelis.config import ConfigProfile

# Development profile
dev_profile = ConfigProfile(
    name="development",
    config_file="config/development.yaml",
    overrides={
        "debug": True,
        "log_level": "DEBUG",
        "database.echo": True
    }
)

# Production profile
prod_profile = ConfigProfile(
    name="production",
    config_file="config/production.yaml",
    overrides={
        "debug": False,
        "log_level": "WARNING",
        "server.workers": 4
    }
)
```

## Dynamic Configuration

### Configuration Manager

```python
from aurelis.config import ConfigManager

class ConfigManager:
    """Manages dynamic configuration updates"""
    
    def __init__(self):
        self._config = AurelisConfig()
        self._watchers = []
        self._callbacks = []
    
    async def reload_config(self, config_path: str):
        """Reload configuration from file"""
        new_config = self._load_config(config_path)
        self._update_config(new_config)
        await self._notify_callbacks()
    
    def watch_file(self, config_path: str):
        """Watch configuration file for changes"""
        watcher = FileWatcher(config_path)
        watcher.on_change(self.reload_config)
        self._watchers.append(watcher)
    
    def register_callback(self, callback: Callable):
        """Register callback for configuration changes"""
        self._callbacks.append(callback)
    
    async def update_setting(self, key: str, value: Any):
        """Update a specific setting"""
        self._set_nested_value(self._config, key, value)
        await self._notify_callbacks()
```

### Hot Reloading

```python
from aurelis.config import HotReloadManager

# Enable hot reloading
hot_reload = HotReloadManager()
hot_reload.enable()

# Register for specific configuration changes
@hot_reload.on_change("models.default_model")
def on_model_change(old_value, new_value):
    print(f"Default model changed from {old_value} to {new_value}")

@hot_reload.on_change("server.workers")
def on_workers_change(old_value, new_value):
    print(f"Worker count changed from {old_value} to {new_value}")
    # Restart workers if needed
```

## Validation

### Configuration Validation

```python
from aurelis.config import ConfigValidator
from pydantic import ValidationError

class ConfigValidator:
    """Validates configuration settings"""
    
    def validate(self, config: AurelisConfig) -> ValidationResult:
        """Validate complete configuration"""
        try:
            # Type validation
            self._validate_types(config)
            
            # Business logic validation
            self._validate_business_rules(config)
            
            # Dependency validation
            self._validate_dependencies(config)
            
            return ValidationResult(is_valid=True)
            
        except ValidationError as e:
            return ValidationResult(
                is_valid=False,
                errors=e.errors()
            )
    
    def _validate_business_rules(self, config: AurelisConfig):
        """Validate business logic rules"""
        
        # Port range validation
        if not 1024 <= config.server.port <= 65535:
            raise ValueError("Server port must be between 1024 and 65535")
        
        # Worker count validation
        if config.server.workers < 1:
            raise ValueError("Worker count must be at least 1")
        
        # SSL validation
        if config.server.ssl_enabled:
            if not config.server.ssl_cert_path:
                raise ValueError("SSL certificate path required when SSL is enabled")
            if not config.server.ssl_key_path:
                raise ValueError("SSL key path required when SSL is enabled")
```

### Schema Validation

```python
from aurelis.config import ConfigSchema

# Define configuration schema
schema = ConfigSchema({
    "type": "object",
    "properties": {
        "environment": {
            "type": "string",
            "enum": ["development", "testing", "production"]
        },
        "server": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer", "minimum": 1024, "maximum": 65535},
                "workers": {"type": "integer", "minimum": 1}
            },
            "required": ["host", "port"]
        }
    },
    "required": ["environment", "server"]
})

# Validate configuration against schema
validator = ConfigValidator(schema)
result = validator.validate(config_dict)
```

## Security

### Sensitive Data Protection

```python
from aurelis.config import SecureConfig

class SecureConfig:
    """Handles sensitive configuration data"""
    
    def __init__(self):
        self._encryption_key = self._get_encryption_key()
        self._secrets = {}
    
    def set_secret(self, key: str, value: str):
        """Store encrypted secret"""
        encrypted_value = self._encrypt(value)
        self._secrets[key] = encrypted_value
    
    def get_secret(self, key: str) -> str:
        """Retrieve and decrypt secret"""
        encrypted_value = self._secrets.get(key)
        if encrypted_value:
            return self._decrypt(encrypted_value)
        return None
    
    def _encrypt(self, value: str) -> str:
        """Encrypt sensitive value"""
        # Implementation using cryptography library
        pass
    
    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt sensitive value"""
        # Implementation using cryptography library
        pass
```

### Environment Variable Masking

```python
from aurelis.config import ConfigMasker

masker = ConfigMasker()

# Define sensitive keys
sensitive_keys = [
    "api_key",
    "password",
    "secret",
    "token",
    "private_key"
]

# Mask sensitive values in logs
masked_config = masker.mask_sensitive(config, sensitive_keys)
print(masked_config)  # API keys will show as "***"
```

## Advanced Features

### Configuration Inheritance

```python
from aurelis.config import ConfigInheritance

# Base configuration
base_config = {
    "server": {"host": "localhost", "port": 8080},
    "database": {"url": "sqlite:///base.db"},
    "features": {"feature_a": True, "feature_b": False}
}

# Environment-specific overrides
dev_overrides = {
    "debug": True,
    "database": {"echo": True},
    "features": {"feature_b": True}
}

# Merge configurations
inheritance = ConfigInheritance()
final_config = inheritance.merge(base_config, dev_overrides)
```

### Configuration Templates

```python
from aurelis.config import ConfigTemplate

# Define configuration template
template = ConfigTemplate("""
environment: {{ ENV }}
debug: {{ DEBUG | default(false) }}

server:
  host: {{ HOST | default('localhost') }}
  port: {{ PORT | default(8080) }}
  workers: {{ WORKERS | default(1) }}

models:
  github:
    api_key: {{ GITHUB_TOKEN }}
    
database:
  url: {{ DATABASE_URL | default('sqlite:///aurelis.db') }}
""")

# Render template with variables
variables = {
    "ENV": "production",
    "HOST": "0.0.0.0",
    "PORT": 8080,
    "WORKERS": 4,
    "GITHUB_TOKEN": "your-token",
    "DATABASE_URL": "postgresql://..."
}

config_yaml = template.render(variables)
```

### Configuration Diff

```python
from aurelis.config import ConfigDiff

# Compare configurations
diff = ConfigDiff()
changes = diff.compare(old_config, new_config)

for change in changes:
    print(f"{change.path}: {change.old_value} -> {change.new_value}")
```

## Usage Examples

### Basic Configuration

```python
from aurelis.config import get_config

# Get current configuration
config = get_config()

# Access configuration values
print(f"Environment: {config.environment}")
print(f"Server: {config.server.host}:{config.server.port}")
print(f"Default model: {config.models.default_model}")
```

### Configuration Initialization

```python
from aurelis import Aurelis
from aurelis.config import AurelisConfig

# Initialize with custom configuration
config = AurelisConfig(
    environment="production",
    debug=False,
    server=ServerConfig(
        host="0.0.0.0",
        port=8080,
        workers=4
    )
)

aurelis = Aurelis(config=config)
```

### Runtime Configuration Updates

```python
from aurelis.config import update_config

# Update configuration at runtime
await update_config({
    "models.default_model": "github-gpt-4o-mini",
    "cache.ttl": 7200,
    "server.workers": 6
})
```

### Configuration Validation

```python
from aurelis.config import validate_config

# Validate configuration before use
validation_result = validate_config(config)

if not validation_result.is_valid:
    for error in validation_result.errors:
        print(f"Configuration error: {error}")
    exit(1)
```

### Environment-Specific Loading

```python
from aurelis.config import load_environment_config

# Load configuration for specific environment
config = load_environment_config("production")

# Load with overrides
config = load_environment_config(
    environment="production",
    overrides={
        "debug": True,  # Enable debug in production for troubleshooting
        "log_level": "DEBUG"
    }
)
```

### Configuration Export

```python
from aurelis.config import export_config

# Export current configuration
config_dict = export_config(format="dict")
config_yaml = export_config(format="yaml")
config_json = export_config(format="json")

# Export with masked secrets
config_safe = export_config(format="yaml", mask_secrets=True)
```

For more information on specific configuration aspects, see:
- [Security Configuration](security.md)
- [Model Configuration](model-types.md)
- [Cache Configuration](cache.md)
