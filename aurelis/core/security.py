"""Security management for Aurelis including API key management and code sandboxing."""

import os
import secrets
import hashlib
import subprocess
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from aurelis.core.config import get_config
from aurelis.core.logging import get_logger, get_audit_logger
from aurelis.core.exceptions import SecurityError


class APIKeyManager:
    """Secure API key management with encryption and rotation."""
    
    def __init__(self, key_store_path: Optional[Path] = None):
        self.logger = get_logger("security.api_keys")
        self.audit_logger = get_audit_logger()
        
        self.key_store_path = key_store_path or Path.home() / ".aurelis" / "keys.enc"
        self.key_store_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
        self._api_keys: Dict[str, Dict[str, Any]] = {}
        self._load_keys()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for API key storage."""
        key_file = self.key_store_path.parent / ".aurelis_key"
        
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    content = f.read()
                    # Handle both new format (salt + key) and simple key
                    if len(content) > 32:
                        # New format: salt (16 bytes) + key (remaining)
                        salt = content[:16]
                        key = content[16:]
                        return key
                    else:
                        # Old format or simple key
                        return content
            except Exception as e:
                self.logger.warning(f"Failed to load encryption key, generating new one: {e}")
        
        # Generate new encryption key
        password = os.getenv("AURELIS_MASTER_PASSWORD", "aurelis-default-key").encode()
        salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        try:
            with open(key_file, 'wb') as f:
                f.write(salt + key)
            
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
        except Exception as e:
            # Fallback: generate temporary key
            self.logger.warning(f"Failed to save encryption key, using temporary key: {e}")
            return base64.urlsafe_b64encode(os.urandom(32))
    
    def _load_keys(self) -> None:
        """Load encrypted API keys from storage."""
        if not self.key_store_path.exists():
            self._api_keys = {}
            return
        
        try:
            with open(self.key_store_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._cipher.decrypt(encrypted_data)
            import json
            self._api_keys = json.loads(decrypted_data.decode())
            
            self.logger.info(f"Loaded {len(self._api_keys)} API key entries")
        except Exception as e:
            self.logger.error(f"Failed to load API keys: {e}")
            self._api_keys = {}
    
    def _save_keys(self) -> None:
        """Save encrypted API keys to storage."""
        try:
            import json
            data = json.dumps(self._api_keys).encode()
            encrypted_data = self._cipher.encrypt(data)
            
            with open(self.key_store_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.key_store_path, 0o600)
            
            self.logger.info("API keys saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save API keys: {e}")
            raise SecurityError("Failed to save API keys")
    
    def set_api_key(self, service: str, api_key: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store an encrypted API key for a service."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        
        self._api_keys[service] = {
            "key": api_key,
            "key_hash": key_hash,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "usage_count": 0,
            "metadata": metadata or {}
        }
        
        self._save_keys()
        
        if self.audit_logger:
            self.audit_logger.log_command_execution(
                f"set_api_key:{service}",
                success=True,
                metadata={"key_hash": key_hash}
            )
        
        self.logger.info(f"API key set for service: {service}")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Retrieve and decrypt an API key for a service."""
        if service not in self._api_keys:
            # Try environment variable fallback
            env_key = f"AURELIS_{service.upper()}_API_KEY"
            return os.getenv(env_key)
        
        key_data = self._api_keys[service]
        
        # Update usage statistics
        key_data["last_used"] = datetime.now().isoformat()
        key_data["usage_count"] += 1
        self._save_keys()
        
        return key_data["key"]
    
    def rotate_api_key(self, service: str, new_api_key: str) -> None:
        """Rotate an API key for a service."""
        if service not in self._api_keys:
            raise SecurityError(f"No API key found for service: {service}")
        
        old_key_hash = self._api_keys[service]["key_hash"]
        self.set_api_key(service, new_api_key)
        
        if self.audit_logger:
            self.audit_logger.log_command_execution(
                f"rotate_api_key:{service}",
                success=True,
                metadata={
                    "old_key_hash": old_key_hash,
                    "new_key_hash": self._api_keys[service]["key_hash"]
                }
            )
        
        self.logger.info(f"API key rotated for service: {service}")
    
    def delete_api_key(self, service: str) -> None:
        """Delete an API key for a service."""
        if service in self._api_keys:
            key_hash = self._api_keys[service]["key_hash"]
            del self._api_keys[service]
            self._save_keys()
            
            if self.audit_logger:
                self.audit_logger.log_command_execution(
                    f"delete_api_key:{service}",
                    success=True,
                    metadata={"key_hash": key_hash}
                )
            
            self.logger.info(f"API key deleted for service: {service}")
    
    def list_services(self) -> List[str]:
        """List services with stored API keys."""
        return list(self._api_keys.keys())
    
    def get_key_info(self, service: str) -> Optional[Dict[str, Any]]:
        """Get metadata about an API key without revealing the key."""
        if service not in self._api_keys:
            return None
        
        key_data = self._api_keys[service].copy()
        key_data.pop("key", None)  # Remove the actual key
        return key_data


class CodeSandbox:
    """Secure code execution sandbox."""
    
    def __init__(self):
        self.logger = get_logger("security.sandbox")
        self.audit_logger = get_audit_logger()
        self.config = get_config()
        
        # Forbidden imports and operations
        self.forbidden_imports = {
            'os', 'subprocess', 'sys', 'importlib', '__builtin__', 'builtins',
            'eval', 'exec', 'compile', 'open', 'file', 'input', 'raw_input'
        }
        
        self.forbidden_functions = {
            'eval', 'exec', 'compile', 'globals', 'locals', 'vars', 'dir',
            'getattr', 'setattr', 'delattr', 'hasattr', '__import__'
        }
    
    def validate_code(self, code: str) -> bool:
        """Validate code for security issues before execution."""
        # Check for forbidden imports
        import ast
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in code validation: {e}")
            return False
        
        for node in ast.walk(tree):
            # Check for forbidden imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.forbidden_imports:
                        self.logger.warning(f"Forbidden import detected: {alias.name}")
                        return False
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.forbidden_imports:
                    self.logger.warning(f"Forbidden import detected: {node.module}")
                    return False
            
            # Check for forbidden function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.forbidden_functions:
                        self.logger.warning(f"Forbidden function call detected: {node.func.id}")
                        return False
        
        return True
    
    def execute_code(
        self,
        code: str,
        timeout: Optional[int] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute code in a secure sandbox environment."""
        if not self.config.sandbox_enabled:
            raise SecurityError("Code execution sandbox is disabled")
        
        if not self.validate_code(code):
            raise SecurityError("Code failed security validation")
        
        execution_timeout = timeout or self.config.max_execution_time
        
        # Create temporary file for code execution
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)
        
        try:
            # Execute code in subprocess with timeout
            start_time = datetime.now()
            
            result = subprocess.run(
                [self._get_python_executable(), str(temp_file)],
                capture_output=True,
                text=True,
                timeout=execution_timeout,
                cwd=tempfile.gettempdir()
            )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Log execution attempt
            if self.audit_logger:
                self.audit_logger.log_command_execution(
                    "execute_code",
                    user_id=user_id,
                    session_id=session_id,
                    success=result.returncode == 0,
                    metadata={
                        "execution_time": execution_time,
                        "return_code": result.returncode,
                        "code_hash": hashlib.sha256(code.encode()).hexdigest()[:16]
                    }
                )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "execution_time": execution_time
            }
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Code execution timeout after {execution_timeout}s")
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timeout after {execution_timeout}s",
                "return_code": -1,
                "execution_time": execution_timeout
            }
        
        except Exception as e:
            self.logger.error(f"Code execution failed: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "execution_time": 0
            }
        
        finally:
            # Clean up temporary file
            try:
                temp_file.unlink()
            except OSError:
                pass
    
    def _get_python_executable(self) -> str:
        """Get the Python executable path for sandbox execution."""
        # Use the same Python interpreter but in a restricted environment
        import sys
        return sys.executable


class SecurityManager:
    """Central security management for Aurelis."""
    
    def __init__(self):
        self.logger = get_logger("security")
        self.api_key_manager = APIKeyManager()
        self.sandbox = CodeSandbox()
        
        # Rate limiting
        self._request_counts: Dict[str, List[datetime]] = {}
        self._rate_limit_lock = threading.Lock()
    
    def check_rate_limit(self, identifier: str, limit: int = 100, window_minutes: int = 1) -> bool:
        """Check if request is within rate limits."""
        with self._rate_limit_lock:
            now = datetime.now()
            window_start = now - timedelta(minutes=window_minutes)
            
            # Clean up old requests
            if identifier in self._request_counts:
                self._request_counts[identifier] = [
                    req_time for req_time in self._request_counts[identifier]
                    if req_time > window_start
                ]
            else:
                self._request_counts[identifier] = []
            
            # Check if under limit
            if len(self._request_counts[identifier]) >= limit:
                self.logger.warning(f"Rate limit exceeded for {identifier}")
                return False
            
            # Add current request
            self._request_counts[identifier].append(now)
            return True
    
    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '`', '$', '(', ')', ';', '|']
        sanitized = user_input
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    def validate_file_access(self, file_path: Path, operation: str) -> bool:
        """Validate if file access is allowed."""
        # Convert to absolute path
        abs_path = file_path.resolve()
        
        # Check if path is within allowed directories
        allowed_dirs = [
            Path.cwd(),  # Current working directory
            Path.home() / ".aurelis",  # Aurelis config directory
            Path("/tmp") if os.name != 'nt' else Path(os.environ.get('TEMP', ''))  # Temp directory
        ]
        
        for allowed_dir in allowed_dirs:
            try:
                abs_path.relative_to(allowed_dir.resolve())
                return True
            except ValueError:
                continue
        
        self.logger.warning(f"File access denied: {abs_path} ({operation})")
        return False
    
    def get_api_key_manager(self) -> APIKeyManager:
        """Get the API key manager instance."""
        return self.api_key_manager
    
    def get_sandbox(self) -> CodeSandbox:
        """Get the code sandbox instance."""
        return self.sandbox


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get the global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def get_api_key_manager() -> APIKeyManager:
    """Get the API key manager instance."""
    return get_security_manager().get_api_key_manager()


def get_sandbox() -> CodeSandbox:
    """Get the code sandbox instance."""
    return get_security_manager().get_sandbox()


def initialize_security() -> SecurityManager:
    """Initialize the global security manager."""
    global _security_manager
    _security_manager = SecurityManager()
    return _security_manager
