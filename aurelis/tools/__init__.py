"""Tool system for Aurelis - extensible tools for code operations."""

import asyncio
import inspect
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, Callable
from dataclasses import dataclass

from aurelis.core.types import ToolResult
from aurelis.core.config import get_config
from aurelis.core.logging import get_logger, get_audit_logger
from aurelis.core.security import get_sandbox
from aurelis.core.cache import get_cache_manager
from aurelis.core.exceptions import ToolError


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    name: str
    description: str
    category: str
    version: str = "1.0.0"
    author: str = "Aurelis"
    requires_sandbox: bool = False
    cacheable: bool = True
    max_execution_time: int = 30


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self):
        self.logger = get_logger(f"tools.{self.__class__.__name__.lower()}")
        self.config = get_config()
        self.cache_manager = get_cache_manager()
        self.audit_logger = get_audit_logger()
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate tool parameters before execution."""
        return True
    
    def _create_result(
        self,
        success: bool,
        output: Any,
        error_message: Optional[str] = None,
        execution_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Create a standardized tool result."""
        return ToolResult(
            tool_name=self.metadata.name,
            success=success,
            output=output,
            error_message=error_message,
            execution_time=execution_time,
            metadata=metadata or {}
        )


class FileOperationsTool(BaseTool):
    """Tool for file operations (read, write, create, delete)."""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_operations",
            description="Read, write, create, and delete files",
            category="file_system",
            requires_sandbox=False,
            cacheable=True
        )
    
    async def execute(self, operation: str, file_path: str, content: str = None, **kwargs) -> ToolResult:
        """Execute file operation."""
        start_time = time.time()
        
        try:
            if not self.validate_parameters(operation=operation, file_path=file_path, content=content):
                return self._create_result(
                    success=False,
                    output=None,
                    error_message="Invalid parameters",
                    execution_time=time.time() - start_time
                )
            
            path = Path(file_path)
            
            # Validate file access
            from aurelis.core.security import get_security_manager
            security_manager = get_security_manager()
            
            if not security_manager.validate_file_access(path, operation):
                return self._create_result(
                    success=False,
                    output=None,
                    error_message=f"File access denied: {file_path}",
                    execution_time=time.time() - start_time
                )
            
            result_output = None
            
            if operation == "read":
                result_output = await self._read_file(path)
            elif operation == "write":
                result_output = await self._write_file(path, content)
            elif operation == "create":
                result_output = await self._create_file(path, content or "")
            elif operation == "delete":
                result_output = await self._delete_file(path)
            else:
                raise ToolError(f"Unknown operation: {operation}")
            
            execution_time = time.time() - start_time
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.log_file_access(
                    file_path=str(path),
                    operation=operation,
                    success=True,
                    metadata={"execution_time": execution_time}
                )
            
            return self._create_result(
                success=True,
                output=result_output,
                execution_time=execution_time,
                metadata={"operation": operation, "file_path": str(path)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"File operation {operation} failed: {e}")
            
            if self.audit_logger:
                self.audit_logger.log_file_access(
                    file_path=file_path,
                    operation=operation,
                    success=False,
                    metadata={"error": str(e), "execution_time": execution_time}
                )
            
            return self._create_result(
                success=False,
                output=None,
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _read_file(self, path: Path) -> str:
        """Read file content."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def _write_file(self, path: Path, content: str) -> str:
        """Write content to file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Written {len(content)} characters to {path}"
    
    async def _create_file(self, path: Path, content: str) -> str:
        """Create new file with content."""
        if path.exists():
            raise ToolError(f"File already exists: {path}")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Created file {path}"
    
    async def _delete_file(self, path: Path) -> str:
        """Delete file."""
        if not path.exists():
            raise ToolError(f"File not found: {path}")
        
        path.unlink()
        return f"Deleted file {path}"
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate file operation parameters."""
        operation = kwargs.get("operation")
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        
        if not operation or operation not in ["read", "write", "create", "delete"]:
            return False
        
        if not file_path:
            return False
        
        if operation in ["write", "create"] and content is None:
            return False
        
        return True


class CodeExecutionTool(BaseTool):
    """Tool for safe code execution in sandbox."""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="code_execution",
            description="Execute Python code safely in sandbox",
            category="execution",
            requires_sandbox=True,
            cacheable=False,
            max_execution_time=60
        )
    
    async def execute(self, code: str, timeout: Optional[int] = None, **kwargs) -> ToolResult:
        """Execute code in sandbox."""
        start_time = time.time()
        
        try:
            if not self.validate_parameters(code=code):
                return self._create_result(
                    success=False,
                    output=None,
                    error_message="Invalid code parameter",
                    execution_time=time.time() - start_time
                )
            
            sandbox = get_sandbox()
            execution_timeout = timeout or self.metadata.max_execution_time
            
            # Execute code
            result = sandbox.execute_code(code, execution_timeout)
            
            execution_time = time.time() - start_time
            
            return self._create_result(
                success=result["success"],
                output={
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "return_code": result["return_code"]
                },
                error_message=result["stderr"] if not result["success"] else None,
                execution_time=execution_time,
                metadata={
                    "sandbox_time": result["execution_time"],
                    "return_code": result["return_code"]
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Code execution failed: {e}")
            
            return self._create_result(
                success=False,
                output=None,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate code execution parameters."""
        code = kwargs.get("code")
        return bool(code and isinstance(code, str))


class PackageManagerTool(BaseTool):
    """Tool for Python package management."""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="package_manager",
            description="Install, update, and manage Python packages",
            category="package_management",
            requires_sandbox=True,
            cacheable=False
        )
    
    async def execute(self, operation: str, packages: List[str], **kwargs) -> ToolResult:
        """Execute package management operation."""
        start_time = time.time()
        
        try:
            if not self.validate_parameters(operation=operation, packages=packages):
                return self._create_result(
                    success=False,
                    output=None,
                    error_message="Invalid parameters",
                    execution_time=time.time() - start_time
                )
            
            if operation == "install":
                result = await self._install_packages(packages)
            elif operation == "uninstall":
                result = await self._uninstall_packages(packages)
            elif operation == "list":
                result = await self._list_packages()
            elif operation == "info":
                result = await self._package_info(packages[0] if packages else "")
            else:
                raise ToolError(f"Unknown operation: {operation}")
            
            execution_time = time.time() - start_time
            
            return self._create_result(
                success=True,
                output=result,
                execution_time=execution_time,
                metadata={"operation": operation, "packages": packages}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Package operation {operation} failed: {e}")
            
            return self._create_result(
                success=False,
                output=None,
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _install_packages(self, packages: List[str]) -> Dict[str, Any]:
        """Install packages using pip."""
        cmd = ["pip", "install"] + packages
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0
        }
    
    async def _uninstall_packages(self, packages: List[str]) -> Dict[str, Any]:
        """Uninstall packages using pip."""
        cmd = ["pip", "uninstall", "-y"] + packages
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0
        }
    
    async def _list_packages(self) -> Dict[str, Any]:
        """List installed packages."""
        cmd = ["pip", "list"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0
        }
    
    async def _package_info(self, package: str) -> Dict[str, Any]:
        """Get package information."""
        cmd = ["pip", "show", package]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate package management parameters."""
        operation = kwargs.get("operation")
        packages = kwargs.get("packages")
        
        if not operation or operation not in ["install", "uninstall", "list", "info"]:
            return False
        
        if operation in ["install", "uninstall"] and (not packages or not isinstance(packages, list)):
            return False
        
        if operation == "info" and (not packages or len(packages) != 1):
            return False
        
        return True


class GitOperationsTool(BaseTool):
    """Tool for Git version control operations."""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_operations",
            description="Git version control operations",
            category="version_control",
            requires_sandbox=False,
            cacheable=False
        )
    
    async def execute(self, operation: str, repository_path: str = ".", **kwargs) -> ToolResult:
        """Execute Git operation."""
        start_time = time.time()
        
        try:
            if not self.validate_parameters(operation=operation, repository_path=repository_path):
                return self._create_result(
                    success=False,
                    output=None,
                    error_message="Invalid parameters",
                    execution_time=time.time() - start_time
                )
            
            repo_path = Path(repository_path)
            
            if operation == "status":
                result = await self._git_status(repo_path)
            elif operation == "diff":
                result = await self._git_diff(repo_path)
            elif operation == "log":
                result = await self._git_log(repo_path, kwargs.get("limit", 10))
            elif operation == "branch":
                result = await self._git_branch(repo_path)
            else:
                raise ToolError(f"Unknown Git operation: {operation}")
            
            execution_time = time.time() - start_time
            
            return self._create_result(
                success=True,
                output=result,
                execution_time=execution_time,
                metadata={"operation": operation, "repository": str(repo_path)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Git operation {operation} failed: {e}")
            
            return self._create_result(
                success=False,
                output=None,
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _git_status(self, repo_path: Path) -> Dict[str, Any]:
        """Get Git status."""
        cmd = ["git", "status", "--porcelain"]
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "output": result.stdout,
            "error": result.stderr,
            "success": result.returncode == 0,
            "modified_files": [line[3:] for line in result.stdout.splitlines() if line.strip()]
        }
    
    async def _git_diff(self, repo_path: Path) -> Dict[str, Any]:
        """Get Git diff."""
        cmd = ["git", "diff"]
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "output": result.stdout,
            "error": result.stderr,
            "success": result.returncode == 0
        }
    
    async def _git_log(self, repo_path: Path, limit: int) -> Dict[str, Any]:
        """Get Git log."""
        cmd = ["git", "log", f"--max-count={limit}", "--oneline"]
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "output": result.stdout,
            "error": result.stderr,
            "success": result.returncode == 0,
            "commits": result.stdout.splitlines() if result.returncode == 0 else []
        }
    
    async def _git_branch(self, repo_path: Path) -> Dict[str, Any]:
        """Get Git branches."""
        cmd = ["git", "branch", "-a"]
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "output": result.stdout,
            "error": result.stderr,
            "success": result.returncode == 0,
            "branches": [line.strip().lstrip("* ") for line in result.stdout.splitlines()]
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate Git operation parameters."""
        operation = kwargs.get("operation")
        repository_path = kwargs.get("repository_path")
        
        if not operation or operation not in ["status", "diff", "log", "branch"]:
            return False
        
        if not repository_path:
            return False
        
        return True


class TestGenerationTool(BaseTool):
    """Tool for generating unit tests."""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="test_generation",
            description="Generate unit tests for Python code",
            category="testing",
            requires_sandbox=False,
            cacheable=True
        )
    
    async def execute(self, source_code: str, test_framework: str = "pytest", **kwargs) -> ToolResult:
        """Generate unit tests for source code."""
        start_time = time.time()
        
        try:
            if not self.validate_parameters(source_code=source_code, test_framework=test_framework):
                return self._create_result(
                    success=False,
                    output=None,
                    error_message="Invalid parameters",
                    execution_time=time.time() - start_time
                )
            
            # Use AI model to generate tests
            from aurelis.models import get_model_orchestrator, ModelRequest
            from aurelis.core.types import TaskType, ModelType
            
            orchestrator = get_model_orchestrator()
            
            prompt = f"""Generate comprehensive unit tests for the following Python code using {test_framework}:

```python
{source_code}
```

Please generate tests that cover:
1. Normal cases
2. Edge cases
3. Error conditions
4. Input validation

Use proper test naming conventions and include docstrings."""
            
            system_prompt = f"""You are an expert Python developer specializing in test-driven development. 
Generate high-quality, comprehensive unit tests using {test_framework}. Follow testing best practices 
and ensure good code coverage."""
            
            request = ModelRequest(
                prompt=prompt,
                model_type=ModelType.CODESTRAL_2501,
                task_type=TaskType.CODE_GENERATION,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            response = await orchestrator.send_request(request)
            
            execution_time = time.time() - start_time
            
            return self._create_result(
                success=True,
                output={
                    "test_code": response.content,
                    "framework": test_framework,
                    "confidence": response.confidence
                },
                execution_time=execution_time,
                metadata={
                    "framework": test_framework,
                    "model_confidence": response.confidence,
                    "tokens_used": response.token_usage.get("total_tokens", 0)
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Test generation failed: {e}")
            
            return self._create_result(
                success=False,
                output=None,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate test generation parameters."""
        source_code = kwargs.get("source_code")
        test_framework = kwargs.get("test_framework")
        
        if not source_code or not isinstance(source_code, str):
            return False
        
        if test_framework not in ["pytest", "unittest"]:
            return False
        
        return True


class ToolManager:
    """Manages tool registration, discovery, and execution."""
    
    def __init__(self):
        self.logger = get_logger("tools.manager")
        self.config = get_config()
        self.cache_manager = get_cache_manager()
        
        # Registry of available tools
        self.tools: Dict[str, BaseTool] = {}
        self._register_built_in_tools()
    
    def _register_built_in_tools(self) -> None:
        """Register built-in tools."""
        built_in_tools = [
            FileOperationsTool(),
            CodeExecutionTool(),
            PackageManagerTool(),
            GitOperationsTool(),
            TestGenerationTool()
        ]
        
        for tool in built_in_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool."""
        tool_name = tool.metadata.name
        
        if tool_name in self.tools:
            self.logger.warning(f"Tool {tool_name} already registered, overwriting")
        
        self.tools[tool_name] = tool
        self.logger.info(f"Registered tool: {tool_name}")
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.logger.info(f"Unregistered tool: {tool_name}")
            return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[ToolMetadata]:
        """List all registered tools."""
        return [tool.metadata for tool in self.tools.values()]
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get tools by category."""
        return [tool for tool in self.tools.values() if tool.metadata.category == category]
    
    async def execute_tool(
        self,
        tool_name: str,
        use_cache: bool = True,
        **kwargs
    ) -> ToolResult:
        """Execute a tool with caching support."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error_message=f"Tool not found: {tool_name}",
                execution_time=0.0
            )
        
        # Check cache if enabled
        if use_cache and tool.metadata.cacheable:
            cache_key = self._get_tool_cache_key(tool_name, kwargs)
            cached_result = self.cache_manager.get_cached_tool_result(cache_key)
            if cached_result:
                self.logger.debug(f"Using cached result for tool: {tool_name}")
                return cached_result
        
        # Execute tool
        try:
            result = await asyncio.wait_for(
                tool.execute(**kwargs),
                timeout=tool.metadata.max_execution_time
            )
            
            # Cache successful result
            if use_cache and tool.metadata.cacheable and result.success:
                cache_key = self._get_tool_cache_key(tool_name, kwargs)
                self.cache_manager.cache_tool_result(cache_key, result)
            
            return result
            
        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error_message=f"Tool execution timed out after {tool.metadata.max_execution_time}s",
                execution_time=tool.metadata.max_execution_time
            )
        
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error_message=str(e),
                execution_time=0.0
            )
    
    async def execute_tool_chain(self, tool_chain: List[Dict[str, Any]]) -> List[ToolResult]:
        """Execute a chain of tools in sequence."""
        results = []
        
        for tool_config in tool_chain:
            tool_name = tool_config.get("tool")
            params = tool_config.get("params", {})
            
            if not tool_name:
                results.append(ToolResult(
                    tool_name="unknown",
                    success=False,
                    output=None,
                    error_message="Tool name not specified in chain",
                    execution_time=0.0
                ))
                continue
            
            result = await self.execute_tool(tool_name, **params)
            results.append(result)
            
            # Stop chain execution if tool fails and chain is configured to stop on failure
            if not result.success and tool_config.get("stop_on_failure", True):
                break
        
        return results
    
    def _get_tool_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate cache key for tool execution."""
        import json
        params_str = json.dumps(params, sort_keys=True, default=str)
        return self.cache_manager.hash_content(f"{tool_name}:{params_str}")
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics."""
        categories = {}
        for tool in self.tools.values():
            category = tool.metadata.category
            if category not in categories:
                categories[category] = []
            categories[category].append(tool.metadata.name)
        
        return {
            "total_tools": len(self.tools),
            "categories": categories,
            "tool_names": list(self.tools.keys())
        }


# Global tool manager instance
_tool_manager: Optional[ToolManager] = None


def get_tool_manager() -> ToolManager:
    """Get the global tool manager instance."""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager


def initialize_tool_manager() -> ToolManager:
    """Initialize the global tool manager."""
    global _tool_manager
    _tool_manager = ToolManager()
    return _tool_manager
