"""Code analysis system with AST processing and error detection."""

import ast
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum

try:
    import tree_sitter
    import tree_sitter_python
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from aurelis.core.types import (
    AnalysisResult, AnalysisType, CodeIssue, CodeLocation, ErrorSeverity
)
from aurelis.core.config import get_config
from aurelis.core.logging import get_logger
from aurelis.core.cache import get_cache_manager
from aurelis.core.exceptions import AnalysisError


@dataclass
class PerformanceMetrics:
    """Performance metrics for code analysis."""
    cyclomatic_complexity: int
    lines_of_code: int
    logical_lines: int
    comment_lines: int
    blank_lines: int
    function_count: int
    class_count: int
    import_count: int
    maintainability_index: float


class SecurityVulnerability(Enum):
    """Types of security vulnerabilities."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    WEAK_CRYPTO = "weak_crypto"
    HARDCODED_SECRET = "hardcoded_secret"
    UNSAFE_DESERIALIZATION = "unsafe_deserialization"


class SyntaxAnalyzer:
    """Analyzes Python code for syntax errors and inconsistencies."""
    
    def __init__(self):
        self.logger = get_logger("analysis.syntax")
    
    def analyze(self, code: str, file_path: Path) -> List[CodeIssue]:
        """Analyze code for syntax issues."""
        issues = []
        
        try:
            # Parse AST
            tree = ast.parse(code)
            
            # Check for syntax patterns
            issues.extend(self._check_unused_imports(tree, file_path))
            issues.extend(self._check_undefined_variables(tree, file_path))
            issues.extend(self._check_duplicate_code(tree, file_path))
            issues.extend(self._check_naming_conventions(tree, file_path))
            
        except SyntaxError as e:
            issues.append(CodeIssue(
                id=f"syntax_error_{e.lineno}",
                type=AnalysisType.SYNTAX,
                severity=ErrorSeverity.ERROR,
                message="Syntax error",
                description=str(e),
                location=CodeLocation(
                    file_path=file_path,
                    line_number=e.lineno or 1,
                    column_number=e.offset or 1
                ),
                confidence=1.0,
                rule_id="SYNTAX_001"
            ))
        
        return issues
    
    def _check_unused_imports(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for unused imports."""
        issues = []
        
        # Collect all imports
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = (node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.names:
                    for alias in node.names:
                        name = alias.asname or alias.name
                        imports[name] = (node.lineno, f"{node.module}.{alias.name}")
        
        # Check usage
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        # Find unused imports
        for name, (line_no, full_name) in imports.items():
            if name not in used_names and not name.startswith('_'):
                issues.append(CodeIssue(
                    id=f"unused_import_{line_no}",
                    type=AnalysisType.SYNTAX,
                    severity=ErrorSeverity.WARNING,
                    message=f"Unused import: {name}",
                    description=f"Import '{full_name}' is not used in the code",
                    location=CodeLocation(
                        file_path=file_path,
                        line_number=line_no,
                        column_number=1
                    ),
                    suggested_fix=f"Remove unused import: {name}",
                    confidence=0.9,
                    rule_id="SYNTAX_002"
                ))
        
        return issues
    
    def _check_undefined_variables(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for potentially undefined variables."""
        issues = []
        
        # This is a simplified check - in production, you'd want proper scope analysis
        defined_names = set()
        used_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    defined_names.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    used_names.append((node.id, node.lineno))
        
        # Check for undefined variables
        builtins = {
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'open', 'range', 'enumerate', 'zip', 'map', 'filter', 'sum', 'min', 'max',
            'abs', 'round', 'sorted', 'reversed', 'isinstance', 'hasattr', 'getattr'
        }
        
        for name, line_no in used_names:
            if name not in defined_names and name not in builtins:
                issues.append(CodeIssue(
                    id=f"undefined_var_{line_no}_{name}",
                    type=AnalysisType.SYNTAX,
                    severity=ErrorSeverity.WARNING,
                    message=f"Potentially undefined variable: {name}",
                    description=f"Variable '{name}' may not be defined before use",
                    location=CodeLocation(
                        file_path=file_path,
                        line_number=line_no,
                        column_number=1
                    ),
                    confidence=0.7,
                    rule_id="SYNTAX_003"
                ))
        
        return issues
    
    def _check_duplicate_code(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for duplicate code blocks."""
        issues = []
        
        # Simplified duplicate detection based on AST structure
        function_bodies = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_str = ast.dump(ast.Module(body=node.body, type_ignores=[]))
                function_bodies.append((node.name, node.lineno, body_str))
        
        # Check for duplicate function bodies
        seen_bodies = {}
        for name, line_no, body_str in function_bodies:
            if body_str in seen_bodies:
                original_name, original_line = seen_bodies[body_str]
                issues.append(CodeIssue(
                    id=f"duplicate_code_{line_no}",
                    type=AnalysisType.SYNTAX,
                    severity=ErrorSeverity.INFO,
                    message=f"Duplicate code detected",
                    description=f"Function '{name}' has similar implementation to '{original_name}' at line {original_line}",
                    location=CodeLocation(
                        file_path=file_path,
                        line_number=line_no,
                        column_number=1
                    ),
                    suggested_fix="Consider extracting common functionality into a shared function",
                    confidence=0.8,
                    rule_id="SYNTAX_004"
                ))
            else:
                seen_bodies[body_str] = (name, line_no)
        
        return issues
    
    def _check_naming_conventions(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for naming convention violations."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not self._is_snake_case(node.name) and not node.name.startswith('__'):
                    issues.append(CodeIssue(
                        id=f"naming_function_{node.lineno}",
                        type=AnalysisType.STYLE,
                        severity=ErrorSeverity.INFO,
                        message=f"Function name should be snake_case: {node.name}",
                        description="Function names should follow snake_case convention",
                        location=CodeLocation(
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset
                        ),
                        suggested_fix=f"Rename to: {self._to_snake_case(node.name)}",
                        confidence=0.9,
                        rule_id="STYLE_001"
                    ))
            
            elif isinstance(node, ast.ClassDef):
                if not self._is_pascal_case(node.name):
                    issues.append(CodeIssue(
                        id=f"naming_class_{node.lineno}",
                        type=AnalysisType.STYLE,
                        severity=ErrorSeverity.INFO,
                        message=f"Class name should be PascalCase: {node.name}",
                        description="Class names should follow PascalCase convention",
                        location=CodeLocation(
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset
                        ),
                        suggested_fix=f"Rename to: {self._to_pascal_case(node.name)}",
                        confidence=0.9,
                        rule_id="STYLE_002"
                    ))
        
        return issues
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention."""
        return re.match(r'^[a-z_][a-z0-9_]*$', name) is not None
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention."""
        return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None
    
    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        return ''.join(word.capitalize() for word in name.split('_'))


class PerformanceAnalyzer:
    """Analyzes code for performance issues."""
    
    def __init__(self):
        self.logger = get_logger("analysis.performance")
    
    def analyze(self, code: str, file_path: Path) -> Tuple[List[CodeIssue], PerformanceMetrics]:
        """Analyze code for performance issues."""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            # Calculate metrics
            metrics = self._calculate_metrics(tree, code)
            
            # Performance checks
            issues.extend(self._check_complexity(tree, file_path))
            issues.extend(self._check_inefficient_patterns(tree, file_path))
            issues.extend(self._check_memory_usage(tree, file_path))
            
            return issues, metrics
            
        except Exception as e:
            self.logger.error(f"Performance analysis failed for {file_path}: {e}")
            return [], PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0.0)
    
    def _calculate_metrics(self, tree: ast.AST, code: str) -> PerformanceMetrics:
        """Calculate code metrics."""
        lines = code.split('\n')
        total_lines = len(lines)
        
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        blank_lines = sum(1 for line in lines if not line.strip())
        logical_lines = total_lines - comment_lines - blank_lines
        
        function_count = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        class_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        import_count = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)))
        
        complexity = self._calculate_cyclomatic_complexity(tree)
        maintainability = self._calculate_maintainability_index(logical_lines, complexity, comment_lines)
        
        return PerformanceMetrics(
            cyclomatic_complexity=complexity,
            lines_of_code=total_lines,
            logical_lines=logical_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=function_count,
            class_count=class_count,
            import_count=import_count,
            maintainability_index=maintainability
        )
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_maintainability_index(self, loc: int, complexity: int, comments: int) -> float:
        """Calculate maintainability index."""
        if loc == 0:
            return 100.0
        
        # Simplified maintainability index calculation
        volume = loc * 4.32  # Simplified volume calculation
        effort = complexity * volume
        comment_ratio = comments / loc if loc > 0 else 0
        
        mi = max(0, 171 - 5.2 * (effort ** 0.23) - 0.23 * complexity - 16.2 * (loc ** 0.5) + 50 * comment_ratio)
        return round(min(100, mi), 2)
    
    def _check_complexity(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for high complexity functions."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_complexity = self._calculate_function_complexity(node)
                
                if func_complexity > 10:
                    severity = ErrorSeverity.ERROR if func_complexity > 20 else ErrorSeverity.WARNING
                    issues.append(CodeIssue(
                        id=f"high_complexity_{node.lineno}",
                        type=AnalysisType.PERFORMANCE,
                        severity=severity,
                        message=f"High cyclomatic complexity: {func_complexity}",
                        description=f"Function '{node.name}' has high complexity ({func_complexity}). Consider refactoring.",
                        location=CodeLocation(
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset
                        ),
                        suggested_fix="Break down into smaller functions",
                        confidence=0.9,
                        rule_id="PERF_001"
                    ))
        
        return issues
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate complexity for a specific function."""
        complexity = 1
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _check_inefficient_patterns(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for inefficient code patterns."""
        issues = []
        
        for node in ast.walk(tree):
            # Check for string concatenation in loops
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        if isinstance(child.target, ast.Name):
                            issues.append(CodeIssue(
                                id=f"string_concat_loop_{child.lineno}",
                                type=AnalysisType.PERFORMANCE,
                                severity=ErrorSeverity.WARNING,
                                message="String concatenation in loop",
                                description="String concatenation in loops is inefficient. Consider using join() or list accumulation.",
                                location=CodeLocation(
                                    file_path=file_path,
                                    line_number=child.lineno,
                                    column_number=child.col_offset
                                ),
                                suggested_fix="Use list.append() and ''.join() or str.join()",
                                confidence=0.8,
                                rule_id="PERF_002"
                            ))
            
            # Check for inefficient list operations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if (isinstance(node.func.value, ast.Name) and 
                        node.func.attr in ['append', 'extend'] and
                        len(node.args) > 0):
                        # This is a simplified check
                        pass
        
        return issues
    
    def _check_memory_usage(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for potential memory issues."""
        issues = []
        
        for node in ast.walk(tree):
            # Check for large list comprehensions
            if isinstance(node, ast.ListComp):
                # Check if it's in a nested structure that might indicate large data
                for generator in node.generators:
                    if isinstance(generator.iter, ast.Call):
                        if (isinstance(generator.iter.func, ast.Name) and 
                            generator.iter.func.id == 'range' and 
                            len(generator.iter.args) > 0):
                            # Check if range is large
                            if isinstance(generator.iter.args[-1], ast.Constant):
                                if isinstance(generator.iter.args[-1].value, int) and generator.iter.args[-1].value > 10000:
                                    issues.append(CodeIssue(
                                        id=f"large_list_comp_{node.lineno}",
                                        type=AnalysisType.PERFORMANCE,
                                        severity=ErrorSeverity.WARNING,
                                        message="Large list comprehension",
                                        description="Large list comprehensions can consume significant memory. Consider using generator expressions.",
                                        location=CodeLocation(
                                            file_path=file_path,
                                            line_number=node.lineno,
                                            column_number=node.col_offset
                                        ),
                                        suggested_fix="Use generator expression instead: (... for ... in ...)",
                                        confidence=0.7,
                                        rule_id="PERF_003"
                                    ))
        
        return issues


class SecurityAnalyzer:
    """Analyzes code for security vulnerabilities."""
    
    def __init__(self):
        self.logger = get_logger("analysis.security")
        
        # Security patterns to check
        self.dangerous_functions = {
            'eval', 'exec', 'compile', '__import__', 'open', 'file',
            'input', 'raw_input', 'subprocess.call', 'os.system'
        }
        
        self.crypto_patterns = [
            r'md5\(',
            r'sha1\(',
            r'des\(',
            r'rc4\(',
            r'password\s*=\s*["\'][^"\']*["\']',
            r'secret\s*=\s*["\'][^"\']*["\']',
            r'key\s*=\s*["\'][^"\']*["\']',
        ]
    
    def analyze(self, code: str, file_path: Path) -> List[CodeIssue]:
        """Analyze code for security issues."""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            issues.extend(self._check_dangerous_functions(tree, file_path))
            issues.extend(self._check_hardcoded_secrets(code, file_path))
            issues.extend(self._check_weak_crypto(code, file_path))
            issues.extend(self._check_sql_injection(tree, file_path))
            issues.extend(self._check_path_traversal(tree, file_path))
            
        except Exception as e:
            self.logger.error(f"Security analysis failed for {file_path}: {e}")
        
        return issues
    
    def _check_dangerous_functions(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for dangerous function calls."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        func_name = f"{node.func.value.id}.{node.func.attr}"
                
                if func_name in self.dangerous_functions:
                    issues.append(CodeIssue(
                        id=f"dangerous_func_{node.lineno}",
                        type=AnalysisType.SECURITY,
                        severity=ErrorSeverity.ERROR,
                        message=f"Dangerous function call: {func_name}",
                        description=f"Function '{func_name}' can be dangerous and should be used with caution",
                        location=CodeLocation(
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset
                        ),
                        suggested_fix="Validate all inputs and consider safer alternatives",
                        confidence=0.9,
                        rule_id="SEC_001"
                    ))
        
        return issues
    
    def _check_hardcoded_secrets(self, code: str, file_path: Path) -> List[CodeIssue]:
        """Check for hardcoded secrets."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in self.crypto_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        id=f"hardcoded_secret_{i}",
                        type=AnalysisType.SECURITY,
                        severity=ErrorSeverity.ERROR,
                        message="Potential hardcoded secret",
                        description="Hardcoded secrets should be stored in environment variables or secure configuration",
                        location=CodeLocation(
                            file_path=file_path,
                            line_number=i,
                            column_number=1
                        ),
                        suggested_fix="Use environment variables or secure configuration management",
                        confidence=0.8,
                        rule_id="SEC_002"
                    ))
        
        return issues
    
    def _check_weak_crypto(self, code: str, file_path: Path) -> List[CodeIssue]:
        """Check for weak cryptographic algorithms."""
        issues = []
        lines = code.split('\n')
        
        weak_crypto = ['md5', 'sha1', 'des', 'rc4']
        
        for i, line in enumerate(lines, 1):
            for crypto in weak_crypto:
                if crypto in line.lower():
                    issues.append(CodeIssue(
                        id=f"weak_crypto_{i}",
                        type=AnalysisType.SECURITY,
                        severity=ErrorSeverity.WARNING,
                        message=f"Weak cryptographic algorithm: {crypto}",
                        description=f"Algorithm '{crypto}' is considered weak. Use stronger alternatives.",
                        location=CodeLocation(
                            file_path=file_path,
                            line_number=i,
                            column_number=1
                        ),
                        suggested_fix="Use SHA-256, SHA-3, or other strong cryptographic algorithms",
                        confidence=0.7,
                        rule_id="SEC_003"
                    ))
        
        return issues
    
    def _check_sql_injection(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for potential SQL injection vulnerabilities."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for string formatting with SQL-like operations
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'format' or node.func.attr == 'execute':
                        # Check if the target contains SQL keywords
                        if isinstance(node.func.value, ast.Constant):
                            if any(keyword in str(node.func.value.value).upper() 
                                   for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                                issues.append(CodeIssue(
                                    id=f"sql_injection_{node.lineno}",
                                    type=AnalysisType.SECURITY,
                                    severity=ErrorSeverity.ERROR,
                                    message="Potential SQL injection vulnerability",
                                    description="Dynamic SQL construction can lead to SQL injection. Use parameterized queries.",
                                    location=CodeLocation(
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        column_number=node.col_offset
                                    ),
                                    suggested_fix="Use parameterized queries or ORM",
                                    confidence=0.8,
                                    rule_id="SEC_004"
                                ))
        
        return issues
    
    def _check_path_traversal(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Check for path traversal vulnerabilities."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    # Check if path comes from user input (simplified check)
                    if len(node.args) > 0:
                        issues.append(CodeIssue(
                            id=f"path_traversal_{node.lineno}",
                            type=AnalysisType.SECURITY,
                            severity=ErrorSeverity.WARNING,
                            message="Potential path traversal vulnerability",
                            description="File operations with user-controlled paths can lead to path traversal attacks",
                            location=CodeLocation(
                                file_path=file_path,
                                line_number=node.lineno,
                                column_number=node.col_offset
                            ),
                            suggested_fix="Validate and sanitize file paths, use os.path.join() and check against allowed directories",
                            confidence=0.6,
                            rule_id="SEC_005"
                        ))
        
        return issues


class CodeAnalyzer:
    """Main code analyzer that orchestrates all analysis types."""
    
    def __init__(self):
        self.logger = get_logger("analysis")
        self.cache_manager = get_cache_manager()
        self.config = get_config()
        
        # Initialize analyzers
        self.syntax_analyzer = SyntaxAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
    
    def analyze_file(
        self, 
        file_path: Path, 
        analysis_types: Optional[List[AnalysisType]] = None
    ) -> AnalysisResult:
        """Analyze a single file."""
        if analysis_types is None:
            analysis_types = [AnalysisType.SYNTAX, AnalysisType.PERFORMANCE, AnalysisType.SECURITY]
        
        start_time = time.time()
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Check file size
            if len(code.encode()) > self.config.max_file_size:
                raise AnalysisError(f"File {file_path} exceeds maximum size limit")
            
            # Check cache
            file_mtime = file_path.stat().st_mtime
            cache_key = self.cache_manager.get_analysis_cache_key(
                str(file_path), "_".join(analysis_types), file_mtime
            )
            
            cached_result = self.cache_manager.get_cached_analysis(cache_key)
            if cached_result:
                self.logger.debug(f"Using cached analysis for {file_path}")
                return cached_result
            
            # Perform analysis
            all_issues = []
            metrics = {}
            suggestions = []
            
            if AnalysisType.SYNTAX in analysis_types:
                syntax_issues = self.syntax_analyzer.analyze(code, file_path)
                all_issues.extend(syntax_issues)
            
            if AnalysisType.PERFORMANCE in analysis_types:
                perf_issues, perf_metrics = self.performance_analyzer.analyze(code, file_path)
                all_issues.extend(perf_issues)
                metrics.update({
                    "cyclomatic_complexity": perf_metrics.cyclomatic_complexity,
                    "lines_of_code": perf_metrics.lines_of_code,
                    "maintainability_index": perf_metrics.maintainability_index,
                    "function_count": perf_metrics.function_count,
                    "class_count": perf_metrics.class_count
                })
            
            if AnalysisType.SECURITY in analysis_types:
                security_issues = self.security_analyzer.analyze(code, file_path)
                all_issues.extend(security_issues)
            
            # Calculate overall confidence
            if all_issues:
                confidence = sum(issue.confidence for issue in all_issues) / len(all_issues)
            else:
                confidence = 1.0
            
            # Generate suggestions
            if all_issues:
                error_count = sum(1 for issue in all_issues if issue.severity == ErrorSeverity.ERROR)
                warning_count = sum(1 for issue in all_issues if issue.severity == ErrorSeverity.WARNING)
                
                if error_count > 0:
                    suggestions.append(f"Fix {error_count} critical error(s)")
                if warning_count > 0:
                    suggestions.append(f"Address {warning_count} warning(s)")
            else:
                suggestions.append("No issues found - code looks good!")
            
            # Create result
            processing_time = time.time() - start_time
            result = AnalysisResult(
                file_path=file_path,
                analysis_types=analysis_types,
                issues=all_issues,
                metrics=metrics,
                suggestions=suggestions,
                confidence=confidence,
                processing_time=processing_time
            )
            
            # Cache result
            self.cache_manager.cache_analysis(cache_key, result)
            
            self.logger.info(f"Analysis completed for {file_path} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Analysis failed for {file_path}: {e}")
            raise AnalysisError(f"Failed to analyze {file_path}: {e}")
    
    def analyze_project(
        self, 
        project_path: Path, 
        analysis_types: Optional[List[AnalysisType]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[AnalysisResult]:
        """Analyze an entire project."""
        if include_patterns is None:
            include_patterns = ["*.py"]
        
        if exclude_patterns is None:
            exclude_patterns = ["*/__pycache__/*", "*/venv/*", "*/.venv/*", "*/node_modules/*"]
        
        # Find Python files
        python_files = []
        for pattern in include_patterns:
            python_files.extend(project_path.rglob(pattern))
        
        # Filter out excluded files
        filtered_files = []
        for file_path in python_files:
            relative_path = file_path.relative_to(project_path)
            
            excluded = False
            for exclude_pattern in exclude_patterns:
                if relative_path.match(exclude_pattern):
                    excluded = True
                    break
            
            if not excluded:
                filtered_files.append(file_path)
        
        # Analyze each file
        results = []
        for file_path in filtered_files:
            try:
                result = self.analyze_file(file_path, analysis_types)
                results.append(result)
            except AnalysisError as e:
                self.logger.warning(f"Skipping file {file_path}: {e}")
        
        self.logger.info(f"Project analysis completed: {len(results)} files analyzed")
        return results


# Global analyzer instance
_code_analyzer: Optional[CodeAnalyzer] = None


def get_code_analyzer() -> CodeAnalyzer:
    """Get the global code analyzer instance."""
    global _code_analyzer
    if _code_analyzer is None:
        _code_analyzer = CodeAnalyzer()
    return _code_analyzer


def initialize_analyzer() -> CodeAnalyzer:
    """Initialize the global code analyzer."""
    global _code_analyzer
    _code_analyzer = CodeAnalyzer()
    return _code_analyzer
