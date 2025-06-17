"""Core type definitions for Aurelis."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict


class ModelType(str, Enum):
    """
    Supported GitHub AI model types via Azure AI Inference.
    
    All models are accessed through GitHub's model inference endpoint
    using a single GitHub token for authentication.
    """
    # Mistral Models
    CODESTRAL_2501 = "codestral-2501"
    MISTRAL_LARGE = "mistral-large"
    MISTRAL_NEMO = "mistral-nemo"
    
    # OpenAI Models  
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    
    # Cohere Models
    COHERE_COMMAND_R = "cohere-command-r"
    COHERE_COMMAND_R_PLUS = "cohere-command-r-plus"
    
    # Meta Models
    META_LLAMA_3_1_70B = "meta-llama-3.1-70b-instruct"
    META_LLAMA_3_1_405B = "meta-llama-3.1-405b-instruct"


class TaskType(str, Enum):
    """Task types for model routing."""
    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    CODE_OPTIMIZATION = "code_optimization"
    COMPLEX_REASONING = "complex_reasoning"
    ARCHITECTURAL_DECISIONS = "architectural_decisions"
    TOOL_USAGE = "tool_usage"
    MULTIMODAL_ANALYSIS = "multimodal_analysis"
    DOCUMENTATION = "documentation"
    EXPLANATIONS = "explanations"
    REFACTORING = "refactoring"


class AnalysisType(str, Enum):
    """Types of code analysis."""
    SYNTAX = "syntax"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"


class ChunkingStrategy(str, Enum):
    """Code chunking strategies."""
    SLIDING_WINDOW = "sliding_window"
    SEMANTIC = "semantic"
    DEPENDENCY_AWARE = "dependency_aware"
    PRIORITY = "priority"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ModelCapability(str, Enum):
    """Model capabilities for routing decisions."""
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    ERROR_DETECTION = "error_detection"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    TESTING = "testing"
    OPTIMIZATION = "optimization"


class ChunkPriority(str, Enum):
    """Priority levels for code chunks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CodeLocation(BaseModel):
    """Represents a location in source code."""
    model_config = ConfigDict(frozen=True)
    
    file_path: Path
    line_number: int
    column_number: int
    end_line_number: Optional[int] = None
    end_column_number: Optional[int] = None


class CodeIssue(BaseModel):
    """Represents a code issue found during analysis."""
    model_config = ConfigDict(frozen=True)
    
    id: str
    type: AnalysisType
    severity: ErrorSeverity
    message: str
    description: str
    location: CodeLocation
    suggested_fix: Optional[str] = None
    rule_id: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class CodeChunk(BaseModel):
    """Represents a chunk of code for processing."""
    model_config = ConfigDict(frozen=True)
    
    id: str
    content: str
    file_path: Path
    start_line: int
    end_line: int
    dependencies: List[str] = Field(default_factory=list)
    priority: float = Field(ge=0.0, le=1.0, default=0.5)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    """Response from an AI model."""
    model_config = ConfigDict(frozen=True)
    
    model_type: ModelType
    task_type: TaskType
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    processing_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolResult(BaseModel):
    """Result from tool execution."""
    model_config = ConfigDict(frozen=True)
    
    tool_name: str
    success: bool
    output: Any
    error_message: Optional[str] = None
    execution_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalysisResult(BaseModel):
    """Result of code analysis."""
    model_config = ConfigDict(frozen=True)
    
    file_path: Path
    analysis_types: List[AnalysisType]
    issues: List[CodeIssue] = Field(default_factory=list)
    metrics: Dict[str, Union[int, float, str]] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionContext(BaseModel):
    """Context for a user session."""
    
    session_id: str
    user_id: Optional[str] = None
    project_path: Optional[Path] = None
    active_files: List[Path] = Field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)


class Configuration(BaseModel):
    """System configuration."""
    
    # Model settings
    primary_model: ModelType = ModelType.CODESTRAL_2501
    fallback_model: ModelType = ModelType.GPT_4O
    model_timeout: int = 30
    max_retries: int = 3
    
    # Analysis settings
    max_file_size: int = 1024 * 1024  # 1MB
    chunk_size: int = 4000
    overlap_ratio: float = Field(ge=0.0, le=1.0, default=0.1)
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    
    # Security settings
    sandbox_enabled: bool = True
    api_key_rotation: bool = True
    audit_logging: bool = True
    max_execution_time: int = 60
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_cache_size: int = 100 * 1024 * 1024  # 100MB
    
    # Tool settings
    max_tool_execution_time: int = 30
    concurrent_tool_limit: int = 5
    
    # Performance settings
    max_concurrent_requests: int = 10
    request_rate_limit: int = 100  # requests per minute
    memory_limit: int = 512 * 1024 * 1024  # 512MB


class GenerationRequest(BaseModel):
    """Request for code generation."""
    prompt: str
    language: str
    context: str
    max_tokens: int = 2000
    temperature: float = 0.7
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    """Request for code analysis."""
    code: str
    language: str
    analysis_type: str
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentationRequest(BaseModel):
    """Request for documentation generation."""
    target_path: str
    doc_type: str
    format: str = "markdown"
    include_private: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentationResult(BaseModel):
    """Result of documentation generation."""
    title: str
    sections: List['DocumentationSection']
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentationSection(BaseModel):
    """A section in generated documentation."""
    title: str
    content: str
    level: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    subsections: List['DocumentationSection'] = Field(default_factory=list)


class PluginMetadata(BaseModel):
    """Metadata for plugins."""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = Field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None


class PluginConfig(BaseModel):
    """Configuration for plugins."""
    enabled: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 50
