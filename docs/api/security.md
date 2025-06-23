# Security API Reference

This document provides comprehensive information about Aurelis security features, including authentication, authorization, encryption, and security best practices.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Authorization](#authorization)
- [API Key Management](#api-key-management)
- [Token Management](#token-management)
- [Encryption](#encryption)
- [Rate Limiting](#rate-limiting)
- [Input Validation](#input-validation)
- [Audit Logging](#audit-logging)
- [Security Middleware](#security-middleware)
- [Best Practices](#best-practices)
- [Usage Examples](#usage-examples)

## Overview

Aurelis implements comprehensive security measures to protect against common vulnerabilities and ensure secure operation in enterprise environments. The security system includes multiple layers of protection.

### Security Architecture

```python
from aurelis.security import SecurityManager

class SecurityManager:
    """Central security management system"""
    
    def __init__(self):
        self.auth_manager = AuthenticationManager()
        self.authz_manager = AuthorizationManager()
        self.token_manager = TokenManager()
        self.encryption_manager = EncryptionManager()
        self.rate_limiter = RateLimiter()
        self.audit_logger = AuditLogger()
```

## Authentication

### Authentication Manager

```python
from aurelis.security import AuthenticationManager
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AuthenticationResult:
    """Result of authentication attempt"""
    
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    token: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

class AuthenticationManager:
    """Handles user authentication"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.token_manager = TokenManager(config)
        self.user_store = UserStore(config)
    
    async def authenticate_api_key(self, api_key: str) -> AuthenticationResult:
        """Authenticate using API key"""
        try:
            key_info = await self.user_store.get_api_key_info(api_key)
            if not key_info or not key_info.is_active:
                return AuthenticationResult(
                    success=False,
                    error_message="Invalid or inactive API key"
                )
            
            return AuthenticationResult(
                success=True,
                user_id=key_info.user_id,
                username=key_info.username,
                roles=key_info.roles,
                permissions=key_info.permissions
            )
            
        except Exception as e:
            return AuthenticationResult(
                success=False,
                error_message=f"Authentication failed: {str(e)}"
            )
    
    async def authenticate_token(self, token: str) -> AuthenticationResult:
        """Authenticate using JWT token"""
        try:
            payload = self.token_manager.decode_token(token)
            user_info = await self.user_store.get_user(payload["user_id"])
            
            return AuthenticationResult(
                success=True,
                user_id=user_info.id,
                username=user_info.username,
                roles=user_info.roles,
                permissions=user_info.permissions,
                token=token,
                expires_at=datetime.fromtimestamp(payload["exp"])
            )
            
        except Exception as e:
            return AuthenticationResult(
                success=False,
                error_message=f"Token authentication failed: {str(e)}"
            )
```

### User Management

```python
from aurelis.security import User, UserStore

@dataclass
class User:
    """User entity"""
    
    id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    password_hash: Optional[str] = None
    api_keys: List[str] = field(default_factory=list)

class UserStore:
    """User data storage and management"""
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        password_hash = self._hash_password(user_data["password"])
        
        user = User(
            id=self._generate_user_id(),
            username=user_data["username"],
            email=user_data["email"],
            roles=user_data.get("roles", ["user"]),
            permissions=user_data.get("permissions", []),
            password_hash=password_hash
        )
        
        await self._save_user(user)
        return user
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password"""
        user = await self.get_user_by_username(username)
        if user and self._verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow()
            await self._update_user(user)
            return user
        return None
```

## Authorization

### Authorization Manager

```python
from aurelis.security import AuthorizationManager, Permission, Role

@dataclass
class Permission:
    """Represents a specific permission"""
    
    name: str
    resource: str
    action: str
    conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Role:
    """Represents a user role"""
    
    name: str
    permissions: List[Permission]
    description: str = ""

class AuthorizationManager:
    """Handles authorization and permissions"""
    
    def __init__(self):
        self.roles = {}
        self.permissions = {}
        self._load_default_roles()
    
    def check_permission(
        self,
        user_permissions: List[str],
        required_permission: str,
        resource: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user has required permission"""
        
        # Check direct permission
        if required_permission in user_permissions:
            return True
        
        # Check wildcard permissions
        for permission in user_permissions:
            if self._matches_wildcard(permission, required_permission):
                return True
        
        # Check conditional permissions
        if resource and context:
            return self._check_conditional_permission(
                user_permissions, required_permission, resource, context
            )
        
        return False
    
    def _load_default_roles(self):
        """Load default role definitions"""
        self.roles = {
            "admin": Role(
                name="admin",
                permissions=[
                    Permission("*", "*", "*"),  # Full access
                ],
                description="System administrator"
            ),
            "developer": Role(
                name="developer",
                permissions=[
                    Permission("code.generate", "code", "generate"),
                    Permission("code.analyze", "code", "analyze"),
                    Permission("models.use", "models", "use"),
                    Permission("api.read", "api", "read"),
                ],
                description="Developer user"
            ),
            "readonly": Role(
                name="readonly",
                permissions=[
                    Permission("api.read", "api", "read"),
                    Permission("docs.read", "docs", "read"),
                ],
                description="Read-only access"
            )
        }
```

### Decorators

```python
from aurelis.security import require_permission, require_role

@require_permission("code.generate")
async def generate_code(request: CodeGenerationRequest):
    """Generate code - requires code.generate permission"""
    pass

@require_role("developer")
async def advanced_analysis(request: AnalysisRequest):
    """Advanced analysis - requires developer role"""
    pass

@require_permission("models.use", resource="github-models")
async def use_github_model(request: ModelRequest):
    """Use GitHub models - requires specific model permission"""
    pass
```

## API Key Management

### API Key Manager

```python
from aurelis.security import APIKeyManager
import secrets
import hashlib

@dataclass
class APIKey:
    """API key entity"""
    
    id: str
    key_hash: str
    name: str
    user_id: str
    permissions: List[str]
    is_active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    usage_count: int = 0

class APIKeyManager:
    """Manages API keys"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.key_store = APIKeyStore()
    
    def generate_api_key(
        self,
        user_id: str,
        name: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None
    ) -> Tuple[str, APIKey]:
        """Generate a new API key"""
        
        # Generate random key
        raw_key = secrets.token_urlsafe(32)
        key_hash = self._hash_key(raw_key)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create API key record
        api_key = APIKey(
            id=secrets.token_urlsafe(16),
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            permissions=permissions,
            expires_at=expires_at
        )
        
        return raw_key, api_key
    
    async def validate_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Validate API key and return key info"""
        key_hash = self._hash_key(raw_key)
        api_key = await self.key_store.get_by_hash(key_hash)
        
        if not api_key:
            return None
        
        # Check if key is active
        if not api_key.is_active:
            return None
        
        # Check if key is expired
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None
        
        # Update usage statistics
        api_key.last_used = datetime.utcnow()
        api_key.usage_count += 1
        await self.key_store.update(api_key)
        
        return api_key
    
    def _hash_key(self, raw_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(raw_key.encode()).hexdigest()
```

### Key Rotation

```python
from aurelis.security import KeyRotationManager

class KeyRotationManager:
    """Manages API key rotation"""
    
    def __init__(self, api_key_manager: APIKeyManager):
        self.api_key_manager = api_key_manager
    
    async def rotate_key(self, old_key_id: str) -> Tuple[str, APIKey]:
        """Rotate an existing API key"""
        
        # Get old key info
        old_key = await self.api_key_manager.key_store.get(old_key_id)
        if not old_key:
            raise ValueError("API key not found")
        
        # Generate new key with same permissions
        new_raw_key, new_key = self.api_key_manager.generate_api_key(
            user_id=old_key.user_id,
            name=f"{old_key.name} (rotated)",
            permissions=old_key.permissions,
            expires_in_days=365
        )
        
        # Save new key
        await self.api_key_manager.key_store.save(new_key)
        
        # Mark old key as inactive (don't delete for audit trail)
        old_key.is_active = False
        await self.api_key_manager.key_store.update(old_key)
        
        return new_raw_key, new_key
```

## Token Management

### JWT Token Manager

```python
from aurelis.security import TokenManager
import jwt
from datetime import datetime, timedelta

class TokenManager:
    """Manages JWT tokens"""
    
    def __init__(self, config: SecurityConfig):
        self.secret_key = config.secret_key
        self.algorithm = config.algorithm
        self.expire_minutes = config.token_expire_minutes
    
    def create_token(self, user_id: str, permissions: List[str]) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "permissions": permissions,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise SecurityError("Token has expired")
        except jwt.InvalidTokenError:
            raise SecurityError("Invalid token")
    
    def refresh_token(self, token: str) -> str:
        """Refresh JWT token"""
        try:
            payload = self.decode_token(token)
            # Create new token with same payload but new expiration
            return self.create_token(
                user_id=payload["user_id"],
                permissions=payload["permissions"]
            )
        except SecurityError:
            raise SecurityError("Cannot refresh invalid token")
```

### Token Blacklist

```python
from aurelis.security import TokenBlacklist

class TokenBlacklist:
    """Manages blacklisted tokens"""
    
    def __init__(self):
        self.blacklisted_tokens = set()
        self.blacklisted_users = set()
    
    async def blacklist_token(self, token: str):
        """Add token to blacklist"""
        self.blacklisted_tokens.add(token)
        await self._persist_blacklist()
    
    async def blacklist_user(self, user_id: str):
        """Blacklist all tokens for a user"""
        self.blacklisted_users.add(user_id)
        await self._persist_blacklist()
    
    def is_blacklisted(self, token: str, user_id: str) -> bool:
        """Check if token is blacklisted"""
        return (
            token in self.blacklisted_tokens or
            user_id in self.blacklisted_users
        )
```

## Encryption

### Encryption Manager

```python
from aurelis.security import EncryptionManager
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionManager:
    """Handles data encryption and decryption"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.fernet = self._create_cipher()
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        data_bytes = data.encode('utf-8')
        encrypted_bytes = self.fernet.encrypt(data_bytes)
        return base64.b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        data_bytes = self.fernet.decrypt(encrypted_bytes)
        return data_bytes.decode('utf-8')
    
    def encrypt_dict(self, data: Dict[str, Any], sensitive_keys: List[str]) -> Dict[str, Any]:
        """Encrypt sensitive fields in a dictionary"""
        result = data.copy()
        for key in sensitive_keys:
            if key in result:
                result[key] = self.encrypt(str(result[key]))
        return result
    
    def _create_cipher(self) -> Fernet:
        """Create Fernet cipher instance"""
        if self.config.encryption_key:
            key = self.config.encryption_key.encode()
        else:
            # Generate key from password
            password = self.config.secret_key.encode()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return Fernet(key)
```

### Field-Level Encryption

```python
from aurelis.security import EncryptedField

@dataclass
class SecureUserData:
    """User data with encrypted fields"""
    
    id: str
    username: str
    email: EncryptedField[str]
    phone: EncryptedField[str]
    api_keys: EncryptedField[List[str]]
    
    def __post_init__(self):
        # Automatically encrypt sensitive fields
        if isinstance(self.email, str):
            self.email = EncryptedField(self.email)
        if isinstance(self.phone, str):
            self.phone = EncryptedField(self.phone)
        if isinstance(self.api_keys, list):
            self.api_keys = EncryptedField(self.api_keys)
```

## Rate Limiting

### Rate Limiter

```python
from aurelis.security import RateLimiter
from typing import Dict, Tuple
import time

class RateLimiter:
    """Implements rate limiting for API requests"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.requests = {}  # {key: [(timestamp, count), ...]}
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limit"""
        
        current_time = time.time()
        window_start = current_time - window
        
        # Clean up old entries
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries()
        
        # Get requests for this key
        key_requests = self.requests.get(key, [])
        
        # Filter requests within window
        recent_requests = [
            (timestamp, count) for timestamp, count in key_requests
            if timestamp > window_start
        ]
        
        # Count total requests in window
        total_requests = sum(count for _, count in recent_requests)
        
        # Check if limit exceeded
        if total_requests >= limit:
            return False, {
                "allowed": False,
                "limit": limit,
                "window": window,
                "current": total_requests,
                "reset_at": max(timestamp for timestamp, _ in recent_requests) + window
            }
        
        # Add current request
        recent_requests.append((current_time, 1))
        self.requests[key] = recent_requests
        
        return True, {
            "allowed": True,
            "limit": limit,
            "window": window,
            "current": total_requests + 1,
            "remaining": limit - total_requests - 1
        }
    
    def _cleanup_old_entries(self):
        """Remove old rate limit entries"""
        current_time = time.time()
        max_age = 86400  # 24 hours
        
        for key in list(self.requests.keys()):
            self.requests[key] = [
                (timestamp, count) for timestamp, count in self.requests[key]
                if current_time - timestamp < max_age
            ]
            
            if not self.requests[key]:
                del self.requests[key]
        
        self.last_cleanup = current_time
```

### Rate Limiting Decorators

```python
from aurelis.security import rate_limit

@rate_limit(requests=100, window=3600)  # 100 requests per hour
async def expensive_operation(request):
    """Rate-limited expensive operation"""
    pass

@rate_limit(requests=10, window=60, key_func=lambda req: req.user_id)
async def user_specific_limit(request):
    """User-specific rate limiting"""
    pass
```

## Input Validation

### Input Validator

```python
from aurelis.security import InputValidator
import re
from typing import Any, List, Dict

class InputValidator:
    """Validates and sanitizes user input"""
    
    def __init__(self):
        self.patterns = {
            "sql_injection": [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
                r"(--|\#|\/\*)",
                r"(\bUNION\b.*\bSELECT\b)"
            ],
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*="
            ],
            "command_injection": [
                r"[;&|`$(){}[\]\\]",
                r"\b(rm|cat|ls|ps|kill|sudo)\b"
            ]
        }
    
    def validate_input(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """Validate input data against rules"""
        errors = []
        
        if isinstance(data, str):
            errors.extend(self._validate_string(data, rules))
        elif isinstance(data, dict):
            errors.extend(self._validate_dict(data, rules))
        elif isinstance(data, list):
            errors.extend(self._validate_list(data, rules))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def sanitize_input(self, data: str) -> str:
        """Sanitize input string"""
        # Remove potential XSS patterns
        for pattern in self.patterns["xss"]:
            data = re.sub(pattern, "", data, flags=re.IGNORECASE)
        
        # Remove potential SQL injection patterns
        for pattern in self.patterns["sql_injection"]:
            data = re.sub(pattern, "", data, flags=re.IGNORECASE)
        
        return data.strip()
    
    def _validate_string(self, value: str, rules: Dict[str, Any]) -> List[str]:
        """Validate string value"""
        errors = []
        
        # Check for malicious patterns
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    errors.append(f"Potential {category} detected")
        
        # Check length constraints
        if "max_length" in rules and len(value) > rules["max_length"]:
            errors.append(f"Value too long (max: {rules['max_length']})")
        
        if "min_length" in rules and len(value) < rules["min_length"]:
            errors.append(f"Value too short (min: {rules['min_length']})")
        
        # Check regex pattern
        if "pattern" in rules and not re.match(rules["pattern"], value):
            errors.append("Value doesn't match required pattern")
        
        return errors
```

## Audit Logging

### Audit Logger

```python
from aurelis.security import AuditLogger
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class AuditEvent:
    """Represents an audit event"""
    
    event_id: str
    timestamp: datetime
    user_id: Optional[str]
    action: str
    resource: str
    result: str  # "success", "failure", "warning"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"  # "low", "medium", "high", "critical"

class AuditLogger:
    """Logs security-related events"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger("aurelis.audit")
    
    async def log_authentication(
        self,
        user_id: Optional[str],
        success: bool,
        method: str,
        ip_address: str,
        details: Dict[str, Any] = None
    ):
        """Log authentication attempt"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=f"authentication.{method}",
            resource="auth",
            result="success" if success else "failure",
            ip_address=ip_address,
            details=details or {},
            risk_level="medium" if not success else "low"
        )
        
        await self._log_event(event)
    
    async def log_authorization(
        self,
        user_id: str,
        action: str,
        resource: str,
        success: bool,
        details: Dict[str, Any] = None
    ):
        """Log authorization check"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=f"authorization.{action}",
            resource=resource,
            result="success" if success else "failure",
            details=details or {},
            risk_level="high" if not success else "low"
        )
        
        await self._log_event(event)
    
    async def log_data_access(
        self,
        user_id: str,
        data_type: str,
        operation: str,
        record_count: int = 1
    ):
        """Log data access"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=f"data.{operation}",
            resource=data_type,
            result="success",
            details={"record_count": record_count},
            risk_level="low"
        )
        
        await self._log_event(event)
```

## Security Middleware

### Security Middleware

```python
from aurelis.security import SecurityMiddleware
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for HTTP requests"""
    
    def __init__(self, app, security_manager: SecurityManager):
        super().__init__(app)
        self.security_manager = security_manager
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks"""
        
        # Rate limiting
        rate_limit_result = await self._check_rate_limit(request)
        if not rate_limit_result["allowed"]:
            return self._rate_limit_response(rate_limit_result)
        
        # Input validation
        if request.method in ["POST", "PUT", "PATCH"]:
            validation_result = await self._validate_input(request)
            if not validation_result.is_valid:
                return self._validation_error_response(validation_result)
        
        # Authentication
        auth_result = await self._authenticate_request(request)
        if not auth_result.success and self._requires_auth(request):
            return self._auth_error_response()
        
        # Authorization
        if auth_result.success:
            authz_result = await self._authorize_request(request, auth_result)
            if not authz_result:
                return self._authz_error_response()
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        # Log audit event
        await self._log_request(request, response, auth_result)
        
        return response
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
```

## Best Practices

### Security Configuration

```python
# Production security configuration
PRODUCTION_SECURITY_CONFIG = {
    "secret_key": os.environ["SECRET_KEY"],  # Use environment variable
    "algorithm": "HS256",
    "token_expire_minutes": 60,  # Short expiration
    "api_keys_enabled": True,
    "rate_limiting_enabled": True,
    "encryption_enabled": True,
    "audit_logging_enabled": True,
    "cors_allow_credentials": False,
    "cors_allow_origins": ["https://yourdomain.com"],  # Specific origins only
}
```

### Secure Coding Guidelines

```python
# DO: Use parameterized queries
async def get_user_by_id(user_id: str) -> User:
    query = "SELECT * FROM users WHERE id = $1"
    result = await database.fetch_one(query, user_id)
    return User(**result) if result else None

# DON'T: Use string formatting for queries
# query = f"SELECT * FROM users WHERE id = '{user_id}'"  # SQL injection risk

# DO: Validate and sanitize input
validator = InputValidator()
sanitized_input = validator.sanitize_input(user_input)

# DO: Use constant-time comparison for secrets
import hmac
def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    return hmac.compare_digest(provided_key, stored_hash)

# DO: Log security events
await audit_logger.log_authentication(
    user_id=user.id,
    success=True,
    method="api_key",
    ip_address=request.client.host
)
```

## Usage Examples

### Basic Authentication

```python
from aurelis.security import SecurityManager

# Initialize security manager
security_manager = SecurityManager(config)

# Authenticate API key
auth_result = await security_manager.authenticate_api_key("user-api-key")
if auth_result.success:
    print(f"Authenticated user: {auth_result.username}")
```

### Authorization Check

```python
# Check permission
has_permission = security_manager.check_permission(
    user_permissions=auth_result.permissions,
    required_permission="code.generate"
)

if has_permission:
    # Proceed with code generation
    result = await generate_code(request)
```

### Rate Limiting

```python
# Check rate limit
rate_limit_ok, rate_info = await security_manager.check_rate_limit(
    key=f"user:{user_id}",
    limit=100,
    window=3600
)

if not rate_limit_ok:
    raise RateLimitExceededError(
        f"Rate limit exceeded. Reset at: {rate_info['reset_at']}"
    )
```

### Encryption

```python
# Encrypt sensitive data
encrypted_data = security_manager.encrypt("sensitive information")

# Decrypt when needed
decrypted_data = security_manager.decrypt(encrypted_data)
```

### Complete Security Flow

```python
from aurelis.security import secure_endpoint

@secure_endpoint(
    require_auth=True,
    require_permission="models.use",
    rate_limit={"requests": 50, "window": 3600}
)
async def process_model_request(request: ModelRequest):
    """Secure endpoint with full security checks"""
    
    # Request is automatically authenticated and authorized
    # Rate limiting is applied
    # Input is validated
    # All events are logged
    
    result = await model_orchestrator.process(request)
    return result
```

For more information on security-related topics, see:
- [Configuration Security](configuration.md)
- [Security Architecture](../architecture/security.md)
- [Best Practices Guide](../user-guide/best-practices.md)
