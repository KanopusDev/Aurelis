# Request/Response API Reference

API documentation for Aurelis request and response handling system.

## 📋 Table of Contents

1. [Request System](#request-system)
2. [Response System](#response-system)
3. [Request Types](#request-types)
4. [Response Types](#response-types)
5. [Error Handling](#error-handling)
6. [Validation](#validation)
7. [Examples](#examples)

## 📤 Request System

### Base Request Class

```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class BaseRequest:
    """Base class for all Aurelis requests."""
    
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        return {
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'session_id': self.session_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create request from dictionary."""
        return cls(
            request_id=data.get('request_id', str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat())),
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            metadata=data.get('metadata', {})
        )
```

### Analysis Request

```python
@dataclass
class AnalysisRequest(BaseRequest):
    """Request for code analysis."""
    
    source_code: str
    language: str
    file_path: Optional[str] = None
    analysis_type: List[str] = field(default_factory=lambda: ['quality', 'complexity', 'style'])
    options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate request after initialization."""
        if not self.source_code.strip():
            raise ValueError("Source code cannot be empty")
        
        if not self.language:
            raise ValueError("Language must be specified")
        
        valid_analysis_types = ['quality', 'complexity', 'style', 'security', 'performance']
        for analysis_type in self.analysis_type:
            if analysis_type not in valid_analysis_types:
                raise ValueError(f"Invalid analysis type: {analysis_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'source_code': self.source_code,
            'language': self.language,
            'file_path': self.file_path,
            'analysis_type': self.analysis_type,
            'options': self.options
        })
        return base_dict
```

### Generation Request

```python
@dataclass
class GenerationRequest(BaseRequest):
    """Request for code generation."""
    
    prompt: str
    language: str
    context: Optional[str] = None
    style: str = 'standard'
    max_tokens: int = 2000
    temperature: float = 0.7
    
    def __post_init__(self):
        """Validate request after initialization."""
        if not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        if self.max_tokens <= 0 or self.max_tokens > 8000:
            raise ValueError("max_tokens must be between 1 and 8000")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'prompt': self.prompt,
            'language': self.language,
            'context': self.context,
            'style': self.style,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        })
        return base_dict
```

### Documentation Request

```python
@dataclass
class DocumentationRequest(BaseRequest):
    """Request for documentation generation."""
    
    source_code: str
    language: str
    doc_type: str = 'comprehensive'
    include_examples: bool = True
    format: str = 'markdown'
    
    def __post_init__(self):
        """Validate request after initialization."""
        if not self.source_code.strip():
            raise ValueError("Source code cannot be empty")
        
        valid_doc_types = ['brief', 'comprehensive', 'api', 'tutorial']
        if self.doc_type not in valid_doc_types:
            raise ValueError(f"Invalid doc_type: {self.doc_type}")
        
        valid_formats = ['markdown', 'rst', 'html', 'plain']
        if self.format not in valid_formats:
            raise ValueError(f"Invalid format: {self.format}")
```

## 📥 Response System

### Base Response Class

```python
@dataclass
class BaseResponse:
    """Base class for all Aurelis responses."""
    
    request_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = 'success'
    processing_time: float = 0.0
    model_used: Optional[str] = None
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'processing_time': self.processing_time,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create response from dictionary."""
        return cls(
            request_id=data['request_id'],
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat())),
            status=data.get('status', 'success'),
            processing_time=data.get('processing_time', 0.0),
            model_used=data.get('model_used'),
            tokens_used=data.get('tokens_used', 0),
            metadata=data.get('metadata', {})
        )
```

### Analysis Response

```python
@dataclass
class Issue:
    """Represents a code issue found during analysis."""
    
    id: str
    type: str
    severity: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    rule: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'severity': self.severity,
            'message': self.message,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'column_number': self.column_number,
            'rule': self.rule,
            'suggestion': self.suggestion
        }

@dataclass
class Metrics:
    """Code metrics from analysis."""
    
    complexity: float = 0.0
    maintainability_index: float = 0.0
    lines_of_code: int = 0
    test_coverage: float = 0.0
    code_duplication: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'complexity': self.complexity,
            'maintainability_index': self.maintainability_index,
            'lines_of_code': self.lines_of_code,
            'test_coverage': self.test_coverage,
            'code_duplication': self.code_duplication
        }

@dataclass
class AnalysisResponse(BaseResponse):
    """Response for code analysis requests."""
    
    issues: List[Issue] = field(default_factory=list)
    metrics: Optional[Metrics] = None
    suggestions: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'issues': [issue.to_dict() for issue in self.issues],
            'metrics': self.metrics.to_dict() if self.metrics else None,
            'suggestions': self.suggestions,
            'quality_score': self.quality_score
        })
        return base_dict
    
    def get_issues_by_severity(self, severity: str) -> List[Issue]:
        """Get issues filtered by severity."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_critical_issues(self) -> List[Issue]:
        """Get critical issues."""
        return self.get_issues_by_severity('critical')
    
    def has_blocking_issues(self) -> bool:
        """Check if there are blocking issues."""
        return len(self.get_critical_issues()) > 0
```

### Generation Response

```python
@dataclass
class GenerationResponse(BaseResponse):
    """Response for code generation requests."""
    
    generated_code: str = ""
    explanation: str = ""
    confidence_score: float = 0.0
    alternatives: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'generated_code': self.generated_code,
            'explanation': self.explanation,
            'confidence_score': self.confidence_score,
            'alternatives': self.alternatives
        })
        return base_dict
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if generation has high confidence."""
        return self.confidence_score >= threshold
```

### Documentation Response

```python
@dataclass
class DocumentationResponse(BaseResponse):
    """Response for documentation generation requests."""
    
    documentation: str = ""
    sections: Dict[str, str] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'documentation': self.documentation,
            'sections': self.sections,
            'examples': self.examples
        })
        return base_dict
```

## 🎯 Request Types

### HTTP Request Format

```python
class HTTPRequestHandler:
    """Handler for HTTP requests to Aurelis API."""
    
    @staticmethod
    def create_analysis_request(data: Dict[str, Any]) -> AnalysisRequest:
        """Create analysis request from HTTP data."""
        return AnalysisRequest(
            source_code=data['source_code'],
            language=data['language'],
            file_path=data.get('file_path'),
            analysis_type=data.get('analysis_type', ['quality']),
            options=data.get('options', {}),
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            metadata=data.get('metadata', {})
        )
    
    @staticmethod
    def create_generation_request(data: Dict[str, Any]) -> GenerationRequest:
        """Create generation request from HTTP data."""
        return GenerationRequest(
            prompt=data['prompt'],
            language=data['language'],
            context=data.get('context'),
            style=data.get('style', 'standard'),
            max_tokens=data.get('max_tokens', 2000),
            temperature=data.get('temperature', 0.7),
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            metadata=data.get('metadata', {})
        )
```

### CLI Request Format

```python
class CLIRequestHandler:
    """Handler for CLI requests to Aurelis."""
    
    @staticmethod
    def create_analysis_request(
        file_path: str,
        analysis_types: List[str],
        options: Dict[str, Any]
    ) -> AnalysisRequest:
        """Create analysis request from CLI arguments."""
        with open(file_path, 'r') as f:
            source_code = f.read()
        
        # Detect language from file extension
        language = CLIRequestHandler._detect_language(file_path)
        
        return AnalysisRequest(
            source_code=source_code,
            language=language,
            file_path=file_path,
            analysis_type=analysis_types,
            options=options
        )
    
    @staticmethod
    def _detect_language(file_path: str) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.rs': 'rust'
        }
        
        from pathlib import Path
        extension = Path(file_path).suffix.lower()
        return extension_map.get(extension, 'unknown')
```

## 📤 Response Types

### Success Response

```python
@dataclass
class SuccessResponse(BaseResponse):
    """Standard success response."""
    
    data: Any = None
    message: str = "Request completed successfully"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'data': self.data,
            'message': self.message
        })
        return base_dict
```

### Error Response

```python
@dataclass
class ErrorResponse(BaseResponse):
    """Standard error response."""
    
    error_code: str = "UNKNOWN_ERROR"
    error_message: str = "An unknown error occurred"
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set status to error after initialization."""
        self.status = 'error'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'error_code': self.error_code,
            'error_message': self.error_message,
            'error_details': self.error_details
        })
        return base_dict
```

## ❌ Error Handling

### Error Codes

```python
class ErrorCodes:
    """Standard error codes for Aurelis API."""
    
    # Request validation errors
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    
    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Rate limiting errors
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    
    # Processing errors
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    GENERATION_FAILED = "GENERATION_FAILED"
    MODEL_ERROR = "MODEL_ERROR"
    TIMEOUT = "TIMEOUT"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    MAINTENANCE_MODE = "MAINTENANCE_MODE"
```

### Error Handler

```python
class RequestErrorHandler:
    """Handler for request processing errors."""
    
    @staticmethod
    def handle_validation_error(request_id: str, error: Exception) -> ErrorResponse:
        """Handle validation errors."""
        return ErrorResponse(
            request_id=request_id,
            error_code=ErrorCodes.INVALID_REQUEST,
            error_message=f"Request validation failed: {str(error)}",
            error_details={'validation_error': str(error)}
        )
    
    @staticmethod
    def handle_processing_error(request_id: str, error: Exception) -> ErrorResponse:
        """Handle processing errors."""
        return ErrorResponse(
            request_id=request_id,
            error_code=ErrorCodes.ANALYSIS_FAILED,
            error_message=f"Request processing failed: {str(error)}",
            error_details={'processing_error': str(error)}
        )
    
    @staticmethod
    def handle_model_error(request_id: str, error: Exception) -> ErrorResponse:
        """Handle model-related errors."""
        return ErrorResponse(
            request_id=request_id,
            error_code=ErrorCodes.MODEL_ERROR,
            error_message=f"Model processing failed: {str(error)}",
            error_details={'model_error': str(error)}
        )
```

## ✅ Validation

### Request Validator

```python
from typing import Union
import re

class RequestValidator:
    """Validator for Aurelis requests."""
    
    @staticmethod
    def validate_source_code(source_code: str) -> None:
        """Validate source code input."""
        if not source_code or not source_code.strip():
            raise ValueError("Source code cannot be empty")
        
        if len(source_code) > 100000:  # 100KB limit
            raise ValueError("Source code too large (max 100KB)")
    
    @staticmethod
    def validate_language(language: str) -> None:
        """Validate programming language."""
        supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'cpp',
            'c', 'csharp', 'go', 'ruby', 'php', 'swift', 'kotlin', 'rust'
        ]
        
        if language.lower() not in supported_languages:
            raise ValueError(f"Unsupported language: {language}")
    
    @staticmethod
    def validate_analysis_types(analysis_types: List[str]) -> None:
        """Validate analysis types."""
        valid_types = ['quality', 'complexity', 'style', 'security', 'performance']
        
        for analysis_type in analysis_types:
            if analysis_type not in valid_types:
                raise ValueError(f"Invalid analysis type: {analysis_type}")
    
    @staticmethod
    def validate_user_id(user_id: str) -> None:
        """Validate user ID format."""
        if user_id and not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            raise ValueError("Invalid user ID format")
    
    @staticmethod
    def validate_request(request: Union[AnalysisRequest, GenerationRequest]) -> None:
        """Validate any request type."""
        if isinstance(request, AnalysisRequest):
            RequestValidator.validate_source_code(request.source_code)
            RequestValidator.validate_language(request.language)
            RequestValidator.validate_analysis_types(request.analysis_type)
            
        elif isinstance(request, GenerationRequest):
            if not request.prompt.strip():
                raise ValueError("Generation prompt cannot be empty")
            RequestValidator.validate_language(request.language)
            
        if request.user_id:
            RequestValidator.validate_user_id(request.user_id)
```

## 💻 Examples

### Analysis Request Example

```python
# Create analysis request
request = AnalysisRequest(
    source_code="""
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
""",
    language='python',
    file_path='fibonacci.py',
    analysis_type=['quality', 'complexity', 'performance'],
    options={
        'max_complexity': 10,
        'include_suggestions': True
    },
    user_id='user123'
)

# Validate request
RequestValidator.validate_request(request)

# Convert to dict for API
request_dict = request.to_dict()
print(json.dumps(request_dict, indent=2))
```

### Analysis Response Example

```python
# Create analysis response
response = AnalysisResponse(
    request_id=request.request_id,
    status='success',
    processing_time=1.25,
    model_used='codestral-2501',
    tokens_used=150,
    issues=[
        Issue(
            id='issue_1',
            type='performance',
            severity='high',
            message='Inefficient recursive algorithm detected',
            line_number=4,
            rule='recursive_complexity',
            suggestion='Consider using memoization or iterative approach'
        )
    ],
    metrics=Metrics(
        complexity=8.5,
        maintainability_index=65.0,
        lines_of_code=4,
        test_coverage=0.0
    ),
    suggestions=[
        'Add input validation for negative numbers',
        'Consider using dynamic programming for better performance'
    ],
    quality_score=75.0
)

# Convert to dict for API response
response_dict = response.to_dict()
print(json.dumps(response_dict, indent=2))
```

### Generation Request Example

```python
# Create generation request
request = GenerationRequest(
    prompt="Create a function that calculates the factorial of a number",
    language='python',
    context="This function will be used in a math library",
    style='documented',
    max_tokens=500,
    temperature=0.3,
    user_id='user123'
)

# Process and create response
response = GenerationResponse(
    request_id=request.request_id,
    status='success',
    processing_time=2.1,
    model_used='gpt-4o',
    tokens_used=245,
    generated_code="""
def factorial(n: int) -> int:
    \"\"\"
    Calculate the factorial of a non-negative integer.
    
    Args:
        n (int): A non-negative integer
        
    Returns:
        int: The factorial of n
        
    Raises:
        ValueError: If n is negative
    \"\"\"
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result
""",
    explanation="This function calculates factorial using an iterative approach for better performance than recursion.",
    confidence_score=0.92,
    alternatives=[
        "# Recursive implementation",
        "# Using math.factorial() from standard library"
    ]
)
```

### Error Response Example

```python
# Create error response for invalid request
error_response = ErrorResponse(
    request_id='req_123',
    error_code=ErrorCodes.INVALID_PARAMETER,
    error_message="Invalid language specified",
    error_details={
        'parameter': 'language',
        'value': 'unknown_lang',
        'supported_languages': ['python', 'javascript', 'java']
    }
)

print(json.dumps(error_response.to_dict(), indent=2))
```

## 📚 See Also

- [Model Orchestrator API](model-orchestrator.md)
- [Configuration API](configuration.md)
- [Error Handling API](error-handling.md)
- [CLI Commands Reference](cli-commands.md)
