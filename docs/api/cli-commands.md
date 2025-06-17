# CLI Commands API Reference

Complete API reference for Aurelis command-line interface commands.

## Core Command Functions

### `init_aurelis()`

Initializes the Aurelis environment for CLI operations.

```python
def init_aurelis(config_path: Optional[Path] = None) -> None:
    """
    Initialize Aurelis for CLI usage.
    
    Args:
        config_path: Optional path to configuration file
        
    Sets up:
    - Configuration management
    - Logging system  
    - Error handling
    """
```

### Main CLI Commands

#### `init()`

```python
@app.command()
def init(
    config_path: Optional[Path] = None,
    force: bool = False
) -> None:
    """Initialize Aurelis configuration for GitHub models."""
```

**Features:**
- Creates `.aurelis.yaml` configuration file
- Sets up GitHub token guidance
- Provides next steps for user

#### `models()`

```python
@app.command()
def models() -> None:
    """Display available GitHub models and their capabilities."""
```

**Features:**
- Lists all GitHub models with capabilities
- Shows authentication status
- Displays intelligent task routing information
- Provides usage tips

#### `analyze()`

```python
@app.command()
def analyze(
    path: Path,
    analysis_types: Optional[List[str]] = None,
    output_format: str = "table",
    save_report: Optional[Path] = None,
    model: Optional[str] = None
) -> None:
    """Analyze Python code for issues and improvements."""
```

**Analysis Types:**
- `syntax` - Syntax and structural issues
- `performance` - Performance optimization opportunities
- `security` - Security vulnerabilities and concerns
- `style` - Code style and best practices

**Output Formats:**
- `table` - Rich formatted table output
- `json` - Structured JSON for automation

#### `generate()`

```python
@app.command()
def generate(
    prompt: str,
    output_file: Optional[Path] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: Optional[int] = None
) -> None:
    """Generate code based on natural language description."""
```

**Features:**
- Natural language to code generation
- Model selection and temperature control
- Optional file output
- Metadata display (tokens, timing)

#### `explain()`

```python
@app.command()
def explain(
    file_path: Path,
    model: Optional[str] = None,
    detailed: bool = False
) -> None:
    """Explain Python code functionality."""
```

**Features:**
- File-based code explanation
- Basic or detailed explanation levels
- Optimized for education and documentation

#### `fix()`

```python
@app.command()
def fix(
    path: Path,
    fix_type: List[str] = ["all"],
    apply_fixes: bool = False,
    backup: bool = True,
    dry_run: bool = False,
    model: Optional[str] = None
) -> None:
    """Automatically fix code issues and apply improvements."""
```

**Fix Types:**
- `security` - Security vulnerability fixes
- `performance` - Performance optimizations
- `style` - Code style improvements
- `bugs` - Bug fixes and corrections
- `all` - All fix types

**Features:**
- Dry run mode for safe preview
- Automatic backup creation
- Selective fix type application

#### `refactor()`

```python
@app.command()
def refactor(
    path: Path,
    goal: str = "readability",
    aggressive: bool = False,
    preserve_behavior: bool = True,
    output_dir: Optional[Path] = None,
    model: Optional[str] = None
) -> None:
    """Refactor and optimize code for better maintainability."""
```

**Refactor Goals:**
- `performance` - Speed and efficiency optimization
- `readability` - Code clarity and maintainability
- `modularity` - Better structure and separation
- `patterns` - Modern Python patterns and practices

**Features:**
- Conservative or aggressive refactoring
- Behavior preservation guarantee
- Optional output directory

#### `docs()`

```python
@app.command()
def docs(
    path: Path,
    format_type: str = "markdown",
    include_sections: List[str] = ["api"],
    output: Optional[Path] = None,
    template: Optional[str] = None,
    model: Optional[str] = None
) -> None:
    """Generate comprehensive documentation for code."""
```

**Format Types:**
- `markdown` - Markdown documentation
- `rst` - reStructuredText format
- `html` - HTML documentation
- `docstring` - Python docstring format

**Include Sections:**
- `api` - API reference documentation
- `examples` - Usage examples
- `usage` - Usage instructions
- `architecture` - Design and architecture

#### `test()`

```python
@app.command()
def test(
    path: Path,
    framework: str = "pytest",
    coverage: int = 80,
    test_type: str = "unit",
    output: Optional[Path] = None,
    model: Optional[str] = None
) -> None:
    """Generate test cases and test suites for code."""
```

**Test Frameworks:**
- `pytest` - pytest framework (recommended)
- `unittest` - Python unittest framework
- `doctest` - Doctest integration

**Test Types:**
- `unit` - Unit tests for individual functions
- `integration` - Integration tests for components
- `performance` - Performance and benchmarking tests
- `security` - Security-focused tests

#### `shell()`

```python
@app.command()
def shell() -> None:
    """Start interactive Aurelis shell."""
```

**Features:**
- Interactive command environment
- Session management
- Rich terminal interface
- Command history and completion

## Helper Functions

### Display Functions

#### `_display_analysis_table()`

```python
def _display_analysis_table(results) -> None:
    """Display analysis results in table format."""
```

Renders analysis results as a rich-formatted table with:
- File-by-file breakdown
- Issue categorization by type and severity
- Color-coded severity levels
- Line number references

#### `_display_analysis_json()`

```python
def _display_analysis_json(results) -> None:
    """Display analysis results in JSON format."""
```

Outputs structured JSON for:
- CI/CD integration
- Automated processing
- Tool integration
- Reporting systems

### Configuration Functions

#### `_show_configuration()`

```python
def _show_configuration() -> None:
    """Show current configuration."""
```

Displays:
- Model preferences
- Processing settings
- Cache configuration
- Security settings

#### `_list_models()`

```python
def _list_models() -> None:
    """List available models."""
```

Shows all available GitHub models with their identifiers.

#### `_save_analysis_report()`

```python
def _save_analysis_report(
    results, 
    file_path: Path, 
    format_type: str
) -> None:
    """Save analysis report to file."""
```

Supports multiple output formats:
- JSON for automation
- Markdown for documentation
- Custom formats as needed

## Error Handling

### Exception Management

All CLI commands use consistent error handling:

```python
try:
    # Command implementation
    pass
except Exception as e:
    logger.error(f"Command failed: {e}")
    console.print(f"[red]Command failed: {e}[/red]")
    raise typer.Exit(1)
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Authentication error |
| 4 | Network error |
| 5 | File not found |

## Integration Examples

### Programmatic Usage

```python
from aurelis.cli.main import app
import typer

# Run commands programmatically
if __name__ == "__main__":
    app()
```

### Custom CLI Extension

```python
from aurelis.cli.main import app
import typer

@app.command()
def custom_command():
    """Custom command extension."""
    # Implementation
    pass
```

## Best Practices

### Command Design

1. **Consistent Interface**: All commands follow similar parameter patterns
2. **Progress Indication**: Long operations show progress with rich indicators
3. **Helpful Output**: Clear, actionable messages and suggestions
4. **Error Recovery**: Graceful error handling with recovery suggestions

### Model Selection

1. **Task-Optimized**: Commands automatically select optimal models
2. **User Override**: `--model` parameter allows manual selection
3. **Fallback Logic**: Automatic fallback on model failures

### Output Formatting

1. **Rich Display**: Color-coded, formatted output for readability
2. **JSON Support**: Machine-readable output for automation
3. **File Output**: Optional file output for reports and results

## See Also

- [Interactive Shell API](interactive-shell.md)
- [Model Orchestrator API](model-orchestrator.md)
- [Configuration API](configuration.md)
- [CLI Reference Guide](../user-guide/cli-reference.md)
