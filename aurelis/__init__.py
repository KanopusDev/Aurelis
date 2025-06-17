"""
Aurelis Enterprise AI Code Assistant

An enterprise-grade CLI-based AI code assistant that provides intelligent code analysis,
error detection, and AI-powered code generation for Python projects.
"""

__version__ = "1.0.0"
__author__ = "Aurelis Development Team"
__email__ = "support@kanopus.org"
__license__ = "MIT"

from aurelis.core.exceptions import AurelisError, ConfigurationError, ModelError, AnalysisError
from aurelis.core.types import AnalysisResult, ModelResponse, ToolResult

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__license__",
    "AurelisError",
    "ConfigurationError", 
    "ModelError",
    "AnalysisError",
    "AnalysisResult",
    "ModelResponse",
    "ToolResult",
]
