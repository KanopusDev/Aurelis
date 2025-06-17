"""Configuration management for Aurelis."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from aurelis.core.types import Configuration, ModelType, ChunkingStrategy
from aurelis.core.exceptions import ConfigurationError


class ConfigurationManager:
    """Manages application configuration with environment variable support."""
    
    DEFAULT_CONFIG_PATHS = [
        Path.cwd() / ".aurelis.yaml",
        Path.cwd() / ".aurelis.yml", 
        Path.home() / ".aurelis" / "config.yaml",
        Path.home() / ".config" / "aurelis" / "config.yaml"
    ]
    
    def __init__(self, config_path: Optional[Path] = None):
        self._config_path = config_path
        self._config: Optional[Configuration] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        config_data = self._load_config_file()
        env_overrides = self._load_environment_variables()
        
        # Merge configuration with environment overrides
        merged_config = {**config_data, **env_overrides}
        
        try:
            self._config = Configuration(**merged_config)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}")
    
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_file = self._find_config_file()
        
        if not config_file:
            return self._get_default_config()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {config_file}: {e}")
    
    def _find_config_file(self) -> Optional[Path]:
        """Find the first available configuration file."""
        if self._config_path and self._config_path.exists():
            return self._config_path
        
        for config_path in self.DEFAULT_CONFIG_PATHS:
            if config_path.exists():
                return config_path
        
        return None
    
    def _load_environment_variables(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # GitHub token (primary authentication)
        if 'GITHUB_TOKEN' in os.environ:
            env_config.setdefault('auth', {})['github_token'] = os.environ['GITHUB_TOKEN']
        
        # Model preferences
        if 'AURELIS_PRIMARY_MODEL' in os.environ:
            env_config.setdefault('model_preferences', {})['primary'] = os.environ['AURELIS_PRIMARY_MODEL']
        
        if 'AURELIS_FALLBACK_MODEL' in os.environ:
            env_config.setdefault('model_preferences', {})['fallback'] = os.environ['AURELIS_FALLBACK_MODEL']
        
        # Cache configuration
        if 'AURELIS_CACHE_ENABLED' in os.environ:
            env_config.setdefault('cache', {})['enabled'] = os.environ['AURELIS_CACHE_ENABLED'].lower() == 'true'
        
        if 'AURELIS_CACHE_TTL' in os.environ:
            env_config.setdefault('cache', {})['ttl'] = int(os.environ['AURELIS_CACHE_TTL'])
        
        # Logging configuration
        if 'AURELIS_LOG_LEVEL' in os.environ:
            env_config.setdefault('logging', {})['level'] = os.environ['AURELIS_LOG_LEVEL']
        
        return env_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'auth': {
                'github_token': None
            },            'model_preferences': {
                'primary': ModelType.CODESTRAL_2501,
                'fallback': ModelType.GPT_4O_MINI,
                'tools_model': ModelType.GPT_4O,
                'explanation_model': ModelType.COHERE_COMMAND_R
            },
            'cache': {
                'enabled': True,
                'ttl': 3600,  # 1 hour
                'max_size': 1000,
                'backend': 'memory'
            },
            'security': {
                'sandbox_enabled': True,
                'max_file_size': 10485760,  # 10MB
                'allowed_extensions': ['.py', '.js', '.ts', '.java', '.cpp', '.h', '.md'],
                'restricted_paths': ['/etc', '/usr', '/bin', '/sys', '/proc']
            },
            'logging': {
                'level': 'INFO',
                'format': 'structured',
                'file': 'aurelis.log',
                'max_size': 52428800,  # 50MB
                'backup_count': 5
            },
            'analysis': {
                'default_types': ['syntax', 'logic', 'style', 'security'],
                'security_enabled': True,
                'performance_thresholds': {
                    'complexity': 10,
                    'nesting': 4,
                    'line_length': 100
                }
            },
            'chunking': {
                'default_strategy': ChunkingStrategy.SEMANTIC,
                'max_chunk_size': 3000,  # GitHub models 4K limit
                'overlap_size': 300,
                'priority_boost': 0.3
            },
            'github_models': {
                'endpoint': 'https://models.github.ai/inference',
                'temperature': 0.7,
                'max_tokens': 3000,  # Leave room for input
                'timeout': 30,
                'retry_count': 3,
                'retry_delay': 1.0
            }
        }
        raise ConfigurationError(f"Failed to load config file {config_file}: {e}")
    
    def _find_config_file(self) -> Optional[Path]:
        """Find the configuration file to use."""
        if self._config_path:
            if self._config_path.exists():
                return self._config_path
            else:
                raise ConfigurationError(f"Config file not found: {self._config_path}")
        
        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                return path
        
        return None
    
    def _load_environment_variables(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Model settings
        if primary_model := os.getenv("AURELIS_PRIMARY_MODEL"):
            try:
                env_config["primary_model"] = ModelType(primary_model)
            except ValueError:
                raise ConfigurationError(f"Invalid primary model: {primary_model}")
        
        if fallback_model := os.getenv("AURELIS_FALLBACK_MODEL"):
            try:
                env_config["fallback_model"] = ModelType(fallback_model)
            except ValueError:
                raise ConfigurationError(f"Invalid fallback model: {fallback_model}")
        
        if model_timeout := os.getenv("AURELIS_MODEL_TIMEOUT"):
            try:
                env_config["model_timeout"] = int(model_timeout)
            except ValueError:
                raise ConfigurationError(f"Invalid model timeout: {model_timeout}")
        
        # Analysis settings
        if max_file_size := os.getenv("AURELIS_MAX_FILE_SIZE"):
            try:
                env_config["max_file_size"] = int(max_file_size)
            except ValueError:
                raise ConfigurationError(f"Invalid max file size: {max_file_size}")
        
        if chunk_size := os.getenv("AURELIS_CHUNK_SIZE"):
            try:
                env_config["chunk_size"] = int(chunk_size)
            except ValueError:
                raise ConfigurationError(f"Invalid chunk size: {chunk_size}")
        
        if overlap_ratio := os.getenv("AURELIS_OVERLAP_RATIO"):
            try:
                env_config["overlap_ratio"] = float(overlap_ratio)
            except ValueError:
                raise ConfigurationError(f"Invalid overlap ratio: {overlap_ratio}")
        
        if chunking_strategy := os.getenv("AURELIS_CHUNKING_STRATEGY"):
            try:
                env_config["chunking_strategy"] = ChunkingStrategy(chunking_strategy)
            except ValueError:
                raise ConfigurationError(f"Invalid chunking strategy: {chunking_strategy}")
        
        # Security settings
        if sandbox_enabled := os.getenv("AURELIS_SANDBOX_ENABLED"):
            env_config["sandbox_enabled"] = sandbox_enabled.lower() in ("true", "1", "yes")
        
        if api_key_rotation := os.getenv("AURELIS_API_KEY_ROTATION"):
            env_config["api_key_rotation"] = api_key_rotation.lower() in ("true", "1", "yes")
        
        if audit_logging := os.getenv("AURELIS_AUDIT_LOGGING"):
            env_config["audit_logging"] = audit_logging.lower() in ("true", "1", "yes")
        
        # Cache settings
        if cache_enabled := os.getenv("AURELIS_CACHE_ENABLED"):
            env_config["cache_enabled"] = cache_enabled.lower() in ("true", "1", "yes")
        
        if cache_ttl := os.getenv("AURELIS_CACHE_TTL"):
            try:
                env_config["cache_ttl"] = int(cache_ttl)
            except ValueError:
                raise ConfigurationError(f"Invalid cache TTL: {cache_ttl}")
        
        return env_config
    
    @property
    def config(self) -> Configuration:
        """Get the current configuration."""
        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        return self._config
    
    def save_config(self, config_path: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        target_path = config_path or self._config_path or self.DEFAULT_CONFIG_PATHS[0]
        
        # Ensure directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert configuration to dictionary
        config_dict = self._config.model_dump() if self._config else self._get_default_config()
        
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config to {target_path}: {e}")
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        if not self._config:
            raise ConfigurationError("Configuration not loaded")
        
        # Deep merge updates
        config_dict = self._config.model_dump()
        self._deep_merge(config_dict, updates)
        
        try:
            self._config = Configuration(**config_dict)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration update: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Deep merge two dictionaries."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get_github_token(self) -> str:
        """Get GitHub token from configuration or environment."""
        # First check environment variable
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            return token
        
        # Then check configuration
        if self._config and self._config.auth and self._config.auth.get('github_token'):
            return self._config.auth['github_token']
        
        raise ConfigurationError(
            "GitHub token not found. Please set GITHUB_TOKEN environment variable "
            "or configure it using: aurelis config auth.github_token <your-token>"
        )
    
    def validate_configuration(self) -> bool:
        """Validate current configuration."""
        if not self._config:
            return False
        
        try:
            # Validate GitHub token exists
            self.get_github_token()
            
            # Validate model preferences
            primary_model = self._config.model_preferences.get('primary')
            if primary_model and primary_model not in [m.value for m in ModelType]:
                raise ConfigurationError(f"Invalid primary model: {primary_model}")
            
            # Validate cache settings
            cache_config = self._config.cache
            if cache_config.get('ttl', 0) < 0:
                raise ConfigurationError("Cache TTL must be non-negative")
            
            if cache_config.get('max_size', 0) < 0:
                raise ConfigurationError("Cache max_size must be non-negative")
            
            return True
        
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")


# Global configuration instance
_config_manager: Optional[ConfigurationManager] = None


def initialize_config(config_path: Optional[Path] = None) -> ConfigurationManager:
    """Initialize the global configuration manager."""
    global _config_manager
    _config_manager = ConfigurationManager(config_path)
    return _config_manager


def get_config() -> Configuration:
    """Get the current configuration."""
    if _config_manager is None:
        raise ConfigurationError("Configuration not initialized. Call initialize_config() first.")
    return _config_manager.config


def get_config_manager() -> ConfigurationManager:
    """Get the configuration manager instance."""
    if _config_manager is None:
        raise ConfigurationError("Configuration not initialized. Call initialize_config() first.")
    return _config_manager


__all__ = [
    'ConfigurationManager',
    'initialize_config',
    'get_config',
    'get_config_manager'
]
