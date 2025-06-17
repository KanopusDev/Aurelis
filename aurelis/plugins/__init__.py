"""
Plugin and extension system for Aurelis.
Allows dynamic loading and management of custom analyzers, tools, and models.
"""
import importlib
import importlib.util
import inspect
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Callable
from dataclasses import dataclass
from enum import Enum

from aurelis.core.types import PluginMetadata, PluginConfig
from aurelis.core.exceptions import PluginError, PluginLoadError
from aurelis.core.logging import get_logger

logger = get_logger(__name__)


class PluginType(Enum):
    """Types of plugins supported by Aurelis."""
    ANALYZER = "analyzer"
    TOOL = "tool"
    MODEL = "model"
    FORMATTER = "formatter"
    CHUNKER = "chunker"


class PluginState(Enum):
    """Plugin lifecycle states."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginInfo:
    """Information about a loaded plugin."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    entry_point: str
    dependencies: List[str]
    config_schema: Optional[Dict[str, Any]]
    state: PluginState
    error_message: Optional[str]
    module_path: Optional[str]
    instance: Optional[Any]


class PluginInterface(ABC):
    """Base interface that all plugins must implement."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description."""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources when plugin is unloaded."""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration. Override if needed."""
        return True


class AnalyzerPlugin(PluginInterface):
    """Base class for analyzer plugins."""
    
    @abstractmethod
    async def analyze(self, code: str, language: str, **kwargs) -> Dict[str, Any]:
        """Analyze code and return results."""
        pass
    
    @property
    def supported_languages(self) -> List[str]:
        """Languages supported by this analyzer."""
        return ["python"]
    
    @property
    def analysis_types(self) -> List[str]:
        """Types of analysis this plugin performs."""
        return ["custom"]


class ToolPlugin(PluginInterface):
    """Base class for tool plugins."""
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        pass
    
    @property
    def tool_schema(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {}
    
    @property
    def required_permissions(self) -> List[str]:
        """Permissions required by this tool."""
        return []


class ModelPlugin(PluginInterface):
    """Base class for model plugins."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate content using the model."""
        pass
    
    @abstractmethod
    async def analyze(self, content: str, **kwargs) -> Dict[str, Any]:
        """Analyze content using the model."""
        pass
    
    @property
    def model_capabilities(self) -> List[str]:
        """Capabilities of this model."""
        return []
    
    @property
    def context_limit(self) -> int:
        """Maximum context size for this model."""
        return 4096


class FormatterPlugin(PluginInterface):
    """Base class for output formatter plugins."""
    
    @abstractmethod
    async def format(self, data: Any, format_type: str, **kwargs) -> str:
        """Format data according to the specified format."""
        pass
    
    @property
    def supported_formats(self) -> List[str]:
        """Output formats supported by this formatter."""
        return ["text"]


class ChunkerPlugin(PluginInterface):
    """Base class for content chunking plugins."""
    
    @abstractmethod
    def chunk(self, content: str, language: str, **kwargs) -> List[str]:
        """Chunk content according to plugin strategy."""
        pass
    
    @property
    def chunking_strategy(self) -> str:
        """Strategy used by this chunker."""
        return "custom"


class PluginLoader:
    """Loads and manages plugins from various sources."""
    
    def __init__(self, plugin_dirs: List[Path]):
        self.plugin_dirs = plugin_dirs
        self.discovered_plugins: Dict[str, PluginInfo] = {}
    
    def discover_plugins(self) -> List[PluginInfo]:
        """Discover all available plugins in plugin directories."""
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
            
            # Look for Python files and packages
            for item in plugin_dir.iterdir():
                if item.is_file() and item.suffix == '.py' and item.stem != '__init__':
                    plugin_info = self._discover_file_plugin(item)
                    if plugin_info:
                        discovered.append(plugin_info)
                        self.discovered_plugins[plugin_info.name] = plugin_info
                
                elif item.is_dir() and (item / '__init__.py').exists():
                    plugin_info = self._discover_package_plugin(item)
                    if plugin_info:
                        discovered.append(plugin_info)
                        self.discovered_plugins[plugin_info.name] = plugin_info
        
        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered
    
    def _discover_file_plugin(self, file_path: Path) -> Optional[PluginInfo]:
        """Discover plugin from a single Python file."""
        try:
            # Load module temporarily to inspect it
            spec = importlib.util.spec_from_file_location("temp_plugin", file_path)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                return None
            
            # Get plugin metadata
            metadata = self._extract_plugin_metadata(plugin_class, module)
            if not metadata:
                return None
            
            return PluginInfo(
                name=metadata.get('name', file_path.stem),
                version=metadata.get('version', '1.0.0'),
                description=metadata.get('description', 'No description'),
                author=metadata.get('author', 'Unknown'),
                plugin_type=PluginType(metadata.get('type', 'analyzer')),
                entry_point=plugin_class.__name__,
                dependencies=metadata.get('dependencies', []),
                config_schema=metadata.get('config_schema'),
                state=PluginState.UNLOADED,
                error_message=None,
                module_path=str(file_path),
                instance=None
            )
        
        except Exception as e:
            logger.warning(f"Failed to discover plugin from {file_path}: {e}")
            return None
    
    def _discover_package_plugin(self, package_path: Path) -> Optional[PluginInfo]:
        """Discover plugin from a Python package."""
        try:
            # Look for plugin.py or __init__.py with plugin info
            plugin_file = package_path / 'plugin.py'
            if not plugin_file.exists():
                plugin_file = package_path / '__init__.py'
            
            if not plugin_file.exists():
                return None
            
            # Load the plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{package_path.name}", plugin_file
            )
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                return None
            
            # Get plugin metadata
            metadata = self._extract_plugin_metadata(plugin_class, module)
            if not metadata:
                return None
            
            return PluginInfo(
                name=metadata.get('name', package_path.name),
                version=metadata.get('version', '1.0.0'),
                description=metadata.get('description', 'No description'),
                author=metadata.get('author', 'Unknown'),
                plugin_type=PluginType(metadata.get('type', 'analyzer')),
                entry_point=plugin_class.__name__,
                dependencies=metadata.get('dependencies', []),
                config_schema=metadata.get('config_schema'),
                state=PluginState.UNLOADED,
                error_message=None,
                module_path=str(plugin_file),
                instance=None
            )
        
        except Exception as e:
            logger.warning(f"Failed to discover plugin from {package_path}: {e}")
            return None
    
    def _find_plugin_class(self, module) -> Optional[Type[PluginInterface]]:
        """Find the main plugin class in a module."""
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, PluginInterface) and 
                obj != PluginInterface and 
                not obj.__name__.endswith('Plugin')):
                return obj
            
            # Also check for specific plugin types
            if (issubclass(obj, (AnalyzerPlugin, ToolPlugin, ModelPlugin, 
                                FormatterPlugin, ChunkerPlugin)) and
                obj not in (AnalyzerPlugin, ToolPlugin, ModelPlugin, 
                           FormatterPlugin, ChunkerPlugin)):
                return obj
        
        return None
    
    def _extract_plugin_metadata(self, plugin_class: Type, module) -> Optional[Dict[str, Any]]:
        """Extract metadata from plugin class or module."""
        metadata = {}
        
        # Check for module-level metadata
        if hasattr(module, 'PLUGIN_METADATA'):
            metadata.update(module.PLUGIN_METADATA)
        
        # Check for class-level metadata
        if hasattr(plugin_class, 'PLUGIN_METADATA'):
            metadata.update(plugin_class.PLUGIN_METADATA)
        
        # Extract from docstring if available
        if plugin_class.__doc__:
            lines = plugin_class.__doc__.strip().split('\n')
            if lines:
                metadata.setdefault('description', lines[0])
        
        # Determine plugin type from class hierarchy
        if issubclass(plugin_class, AnalyzerPlugin):
            metadata.setdefault('type', 'analyzer')
        elif issubclass(plugin_class, ToolPlugin):
            metadata.setdefault('type', 'tool')
        elif issubclass(plugin_class, ModelPlugin):
            metadata.setdefault('type', 'model')
        elif issubclass(plugin_class, FormatterPlugin):
            metadata.setdefault('type', 'formatter')
        elif issubclass(plugin_class, ChunkerPlugin):
            metadata.setdefault('type', 'chunker')
        
        return metadata if metadata else None
    
    async def load_plugin(self, plugin_info: PluginInfo) -> Optional[PluginInterface]:
        """Load and instantiate a specific plugin."""
        try:
            plugin_info.state = PluginState.LOADING
            
            # Check dependencies
            if not self._check_dependencies(plugin_info.dependencies):
                raise PluginLoadError(f"Missing dependencies for plugin {plugin_info.name}")
            
            # Load the module
            if plugin_info.module_path:
                spec = importlib.util.spec_from_file_location(
                    f"plugin_{plugin_info.name}", plugin_info.module_path
                )
                if not spec or not spec.loader:
                    raise PluginLoadError(f"Failed to load module for plugin {plugin_info.name}")
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get the plugin class
                plugin_class = getattr(module, plugin_info.entry_point)
                
                # Instantiate the plugin
                plugin_instance = plugin_class()
                
                # Validate that it implements the interface correctly
                if not isinstance(plugin_instance, PluginInterface):
                    raise PluginLoadError(f"Plugin {plugin_info.name} does not implement PluginInterface")
                
                plugin_info.instance = plugin_instance
                plugin_info.state = PluginState.LOADED
                
                logger.info(f"Successfully loaded plugin: {plugin_info.name}")
                return plugin_instance
            
            else:
                raise PluginLoadError(f"No module path for plugin {plugin_info.name}")
        
        except Exception as e:
            plugin_info.state = PluginState.ERROR
            plugin_info.error_message = str(e)
            logger.error(f"Failed to load plugin {plugin_info.name}: {e}")
            return None
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if all plugin dependencies are available."""
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                logger.warning(f"Missing dependency: {dep}")
                return False
        return True
    
    async def unload_plugin(self, plugin_info: PluginInfo) -> bool:
        """Unload a plugin and cleanup its resources."""
        try:
            if plugin_info.instance:
                await plugin_info.instance.cleanup()
                plugin_info.instance = None
            
            plugin_info.state = PluginState.UNLOADED
            plugin_info.error_message = None
            
            logger.info(f"Successfully unloaded plugin: {plugin_info.name}")
            return True
        
        except Exception as e:
            plugin_info.state = PluginState.ERROR
            plugin_info.error_message = str(e)
            logger.error(f"Failed to unload plugin {plugin_info.name}: {e}")
            return False


class PluginManager:
    """Main plugin management system."""
    
    def __init__(self, config):
        self.config = config
        self.plugin_dirs = self._get_plugin_directories()
        self.loader = PluginLoader(self.plugin_dirs)
        self.loaded_plugins: Dict[str, PluginInfo] = {}
        self.active_plugins: Dict[PluginType, Dict[str, PluginInterface]] = {
            plugin_type: {} for plugin_type in PluginType
        }
    
    def _get_plugin_directories(self) -> List[Path]:
        """Get list of plugin directories to search."""
        dirs = []
        
        # System plugin directory
        system_dir = Path(__file__).parent.parent / 'plugins'
        dirs.append(system_dir)
        
        # User plugin directory
        user_dir = Path.home() / '.aurelis' / 'plugins'
        dirs.append(user_dir)
        
        # Project plugin directory
        if hasattr(self.config, 'plugin_dirs'):
            for dir_path in self.config.plugin_dirs:
                dirs.append(Path(dir_path))
        
        # Environment variable
        import os
        if 'AURELIS_PLUGIN_PATH' in os.environ:
            for dir_path in os.environ['AURELIS_PLUGIN_PATH'].split(':'):
                dirs.append(Path(dir_path))
        
        return dirs
    
    async def initialize(self) -> None:
        """Initialize the plugin manager and discover plugins."""
        logger.info("Initializing plugin manager")
        
        # Create plugin directories if they don't exist
        for plugin_dir in self.plugin_dirs:
            plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Discover available plugins
        discovered = self.loader.discover_plugins()
        
        # Auto-load enabled plugins
        enabled_plugins = getattr(self.config, 'enabled_plugins', [])
        for plugin_name in enabled_plugins:
            if plugin_name in self.loader.discovered_plugins:
                await self.load_plugin(plugin_name)
    
    async def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Load a specific plugin by name."""
        if plugin_name in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_name} is already loaded")
            return True
        
        if plugin_name not in self.loader.discovered_plugins:
            logger.error(f"Plugin {plugin_name} not found")
            return False
        
        plugin_info = self.loader.discovered_plugins[plugin_name]
        plugin_instance = await self.loader.load_plugin(plugin_info)
        
        if plugin_instance:
            # Initialize the plugin
            plugin_config = config or {}
            await plugin_instance.initialize(plugin_config)
            
            # Register the plugin
            self.loaded_plugins[plugin_name] = plugin_info
            self.active_plugins[plugin_info.plugin_type][plugin_name] = plugin_instance
            
            plugin_info.state = PluginState.ACTIVE
            logger.info(f"Plugin {plugin_name} is now active")
            return True
        
        return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin by name."""
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_name} is not loaded")
            return True
        
        plugin_info = self.loaded_plugins[plugin_name]
        
        # Remove from active plugins
        if plugin_name in self.active_plugins[plugin_info.plugin_type]:
            del self.active_plugins[plugin_info.plugin_type][plugin_name]
        
        # Unload the plugin
        success = await self.loader.unload_plugin(plugin_info)
        
        if success:
            del self.loaded_plugins[plugin_name]
            logger.info(f"Plugin {plugin_name} has been unloaded")
        
        return success
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> Dict[str, PluginInterface]:
        """Get all active plugins of a specific type."""
        return self.active_plugins.get(plugin_type, {})
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get a specific active plugin by name."""
        for plugins_by_type in self.active_plugins.values():
            if plugin_name in plugins_by_type:
                return plugins_by_type[plugin_name]
        return None
    
    def list_available_plugins(self) -> List[PluginInfo]:
        """List all discovered plugins."""
        return list(self.loader.discovered_plugins.values())
    
    def list_loaded_plugins(self) -> List[PluginInfo]:
        """List all loaded plugins."""
        return list(self.loaded_plugins.values())
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin (unload and load again)."""
        if plugin_name in self.loaded_plugins:
            await self.unload_plugin(plugin_name)
        
        # Rediscover the plugin
        self.loader.discover_plugins()
        
        return await self.load_plugin(plugin_name)
    
    async def cleanup(self) -> None:
        """Cleanup all loaded plugins."""
        logger.info("Cleaning up plugin manager")
        
        for plugin_name in list(self.loaded_plugins.keys()):
            await self.unload_plugin(plugin_name)


__all__ = [
    'PluginManager',
    'PluginInterface',
    'AnalyzerPlugin',
    'ToolPlugin', 
    'ModelPlugin',
    'FormatterPlugin',
    'ChunkerPlugin',
    'PluginType',
    'PluginState',
    'PluginInfo',
    'PluginLoader'
]
