# Code Analyzer API Reference

The Code Analyzer API provides comprehensive static code analysis capabilities for the Aurelis platform, enabling automated detection of issues, quality metrics calculation, and security vulnerability scanning.

## Overview

The Code Analyzer is responsible for:
- Static code analysis across multiple programming languages
- Security vulnerability detection
- Performance bottleneck identification
- Code quality metrics calculation
- Style and convention compliance checking
- Dependency analysis and impact assessment

## Core Classes

### CodeAnalyzer

Main analyzer class providing comprehensive code analysis capabilities.

```python
from aurelis.analysis import CodeAnalyzer

analyzer = CodeAnalyzer()
```

#### Methods

##### `analyze_file(file_path: Path) -> AnalysisResult`

Performs comprehensive analysis of a single file.

**Parameters:**
- `file_path` (Path): Path to the file to analyze

**Returns:**
- `AnalysisResult`: Complete analysis results including issues, metrics, and suggestions

**Example:**
```python
from pathlib import Path
from aurelis.analysis import CodeAnalyzer

analyzer = CodeAnalyzer()
result = await analyzer.analyze_file(Path("src/main.py"))

print(f"Found {len(result.issues)} issues")
for issue in result.issues:
    print(f"{issue.severity}: {issue.message} (line {issue.location.line_number})")
```

##### `analyze_directory(directory_path: Path, recursive: bool = True) -> List[AnalysisResult]`

Analyzes all files in a directory.

**Parameters:**
- `directory_path` (Path): Directory to analyze
- `recursive` (bool): Whether to analyze subdirectories recursively

**Returns:**
- `List[AnalysisResult]`: Analysis results for each file

##### `analyze_code_string(content: str, language: str) -> AnalysisResult`

Analyzes code from a string.

**Parameters:**
- `content` (str): Code content to analyze
- `language` (str): Programming language identifier

**Returns:**
- `AnalysisResult`: Analysis results

##### `get_metrics(file_path: Path) -> Dict[str, Any]`

Calculates detailed code metrics for a file.

**Parameters:**
- `file_path` (Path): File to analyze

**Returns:**
- `Dict[str, Any]`: Comprehensive metrics including complexity, maintainability, and quality scores

**Example:**
```python
metrics = await analyzer.get_metrics(Path("src/complex_module.py"))
print(f"Cyclomatic complexity: {metrics['cyclomatic_complexity']}")
print(f"Lines of code: {metrics['lines_of_code']}")
print(f"Maintainability index: {metrics['maintainability_index']}")
```

##### `is_ready() -> bool`

Checks if the analyzer is ready for use.

**Returns:**
- `bool`: True if ready, False otherwise

## Analysis Types

### AnalysisType Enum

Defines the types of analysis that can be performed:

- `SYNTAX`: Syntax error detection
- `LOGIC`: Logic error and bug detection
- `PERFORMANCE`: Performance analysis and optimization suggestions
- `SECURITY`: Security vulnerability scanning
- `STYLE`: Code style and convention checking

### Error Severity Levels

- `INFO`: Informational messages
- `WARNING`: Potential issues that should be reviewed
- `ERROR`: Definite errors that need fixing
- `CRITICAL`: Severe issues that must be addressed immediately

## Data Models

### AnalysisResult

Contains the complete results of code analysis.

```python
@dataclass
class AnalysisResult:
    file_path: Path
    analysis_types: List[AnalysisType]
    issues: List[CodeIssue]
    metrics: Dict[str, Union[int, float, str]]
    suggestions: List[str]
    confidence: float
    processing_time: float
    timestamp: datetime
```

### CodeIssue

Represents a specific issue found during analysis.

```python
@dataclass
class CodeIssue:
    id: str
    type: AnalysisType
    severity: ErrorSeverity
    message: str
    description: str
    location: CodeLocation
    suggested_fix: Optional[str]
    rule_id: Optional[str]
    confidence: float
```

### CodeLocation

Represents a location in source code.

```python
@dataclass
class CodeLocation:
    file_path: Path
    line_number: int
    column_number: int
    end_line_number: Optional[int]
    end_column_number: Optional[int]
```

## Configuration

### Analysis Configuration

The analyzer can be configured through the main Aurelis configuration:

```yaml
analysis:
  enabled_types:
    - syntax
    - logic
    - performance
    - security
    - style
  max_file_size: 1048576  # 1MB
  timeout: 30  # seconds
  parallel_processing: true
  max_workers: 4
```

### Language Support

Currently supported languages:
- Python
- JavaScript/TypeScript
- Java
- C/C++
- Go
- Rust
- PHP
- Ruby

## Integration Examples

### Basic File Analysis

```python
import asyncio
from pathlib import Path
from aurelis.analysis import CodeAnalyzer

async def analyze_project():
    analyzer = CodeAnalyzer()
    
    # Analyze a specific file
    result = await analyzer.analyze_file(Path("src/main.py"))
    
    # Print summary
    print(f"Analysis completed for {result.file_path}")
    print(f"Issues found: {len(result.issues)}")
    print(f"Processing time: {result.processing_time:.2f}s")
    
    # Show issues by severity
    for severity in ['CRITICAL', 'ERROR', 'WARNING', 'INFO']:
        issues = [i for i in result.issues if i.severity.value == severity]
        if issues:
            print(f"\n{severity} ({len(issues)}):")
            for issue in issues:
                print(f"  Line {issue.location.line_number}: {issue.message}")

asyncio.run(analyze_project())
```

### Batch Analysis

```python
async def analyze_entire_project():
    analyzer = CodeAnalyzer()
    project_root = Path("./src")
    
    results = await analyzer.analyze_directory(project_root)
    
    # Aggregate statistics
    total_issues = sum(len(r.issues) for r in results)
    critical_issues = sum(
        len([i for i in r.issues if i.severity == ErrorSeverity.CRITICAL])
        for r in results
    )
    
    print(f"Analyzed {len(results)} files")
    print(f"Total issues: {total_issues}")
    print(f"Critical issues: {critical_issues}")
    
    # Files with most issues
    results.sort(key=lambda r: len(r.issues), reverse=True)
    print("\nFiles with most issues:")
    for result in results[:5]:
        print(f"  {result.file_path}: {len(result.issues)} issues")
```

### Custom Analysis Pipeline

```python
from aurelis.analysis import CodeAnalyzer
from aurelis.core.types import AnalysisType, ErrorSeverity

async def custom_security_scan():
    analyzer = CodeAnalyzer()
    
    # Focus on security analysis
    results = await analyzer.analyze_directory(
        Path("./src"),
        analysis_types=[AnalysisType.SECURITY]
    )
    
    security_issues = []
    for result in results:
        for issue in result.issues:
            if issue.type == AnalysisType.SECURITY:
                security_issues.append((result.file_path, issue))
    
    # Generate security report
    print("Security Analysis Report")
    print("=" * 50)
    
    for file_path, issue in security_issues:
        print(f"File: {file_path}")
        print(f"Issue: {issue.message}")
        print(f"Severity: {issue.severity.value}")
        print(f"Location: Line {issue.location.line_number}")
        if issue.suggested_fix:
            print(f"Suggested fix: {issue.suggested_fix}")
        print("-" * 30)
```

## Error Handling

The analyzer implements comprehensive error handling:

```python
try:
    result = await analyzer.analyze_file(file_path)
except FileNotFoundError:
    print(f"File not found: {file_path}")
except PermissionError:
    print(f"Permission denied: {file_path}")
except UnsupportedLanguageError:
    print(f"Language not supported for: {file_path}")
except AnalysisTimeoutError:
    print(f"Analysis timed out for: {file_path}")
except Exception as e:
    print(f"Unexpected error during analysis: {e}")
```

## Performance Considerations

- Large files are automatically chunked for analysis
- Parallel processing is used for directory analysis
- Results are cached to avoid redundant analysis
- Memory usage is optimized for large codebases
- Configurable timeouts prevent hanging operations

## Best Practices

1. **Regular Analysis**: Run analysis regularly as part of CI/CD pipeline
2. **Incremental Analysis**: Focus on changed files in large projects
3. **Configuration Tuning**: Adjust analysis types based on project needs
4. **Issue Prioritization**: Address critical and error-level issues first
5. **Custom Rules**: Configure custom analysis rules for project-specific requirements
6. **Performance Monitoring**: Monitor analysis performance and adjust timeouts as needed

## Troubleshooting

### Common Issues

**Analysis takes too long:**
- Increase timeout in configuration
- Enable parallel processing
- Exclude large binary files
- Use incremental analysis

**Out of memory errors:**
- Reduce max_workers in configuration
- Analyze smaller directories at a time
- Increase system memory limits

**False positives:**
- Configure custom rules to exclude specific patterns
- Adjust confidence thresholds
- Use language-specific configuration

**Language not supported:**
- Check supported languages list
- Ensure file extensions are correct
- Add custom language configuration if needed

For additional support, see the main Aurelis documentation or contact the development team.
