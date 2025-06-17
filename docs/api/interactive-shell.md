# Interactive Shell API Reference

The Interactive Shell API provides programmatic access to Aurelis's command-line interface, enabling integration with IDEs, automation scripts, and custom development tools.

## Overview

The Interactive Shell offers:
- Programmatic command execution
- Session management and persistence
- Rich output formatting and parsing
- Command history and auto-completion
- Integration with all Aurelis core features
- Extensible command system

## Core Classes

### InteractiveShell

Main shell interface providing command execution and session management.

```python
from aurelis.shell import InteractiveShell

shell = InteractiveShell()
```

#### Methods

##### `execute_command(command: str, args: List[str] = None) -> CommandResult`

Executes a shell command programmatically.

**Parameters:**
- `command` (str): Command name to execute
- `args` (List[str]): Command arguments

**Returns:**
- `CommandResult`: Execution results with output and status

**Example:**
```python
from aurelis.shell import InteractiveShell

shell = InteractiveShell()

# Execute analysis command
result = await shell.execute_command("analyze", ["src/main.py"])
print(f"Command: {result.command}")
print(f"Success: {result.success}")
print(f"Output: {result.output}")
```

##### `start_session(workspace_path: Path = None) -> Session`

Starts a new interactive session.

**Parameters:**
- `workspace_path` (Path): Optional workspace directory

**Returns:**
- `Session`: New session object

##### `get_command_help(command: str) -> str`

Retrieves help information for a command.

**Parameters:**
- `command` (str): Command name

**Returns:**
- `str`: Help text for the command

##### `list_available_commands() -> List[str]`

Lists all available shell commands.

**Returns:**
- `List[str]`: Available command names

##### `add_custom_command(command: CustomCommand) -> None`

Registers a custom command with the shell.

**Parameters:**
- `command` (CustomCommand): Custom command implementation

**Example:**
```python
from aurelis.shell import CustomCommand

class ProjectStatsCommand(CustomCommand):
    name = "project-stats"
    description = "Show project statistics"
    
    async def execute(self, args: List[str]) -> CommandResult:
        # Custom logic here
        stats = self.calculate_project_stats()
        return CommandResult(
            success=True,
            output=f"Lines of code: {stats['loc']}\nFiles: {stats['files']}"
        )

shell.add_custom_command(ProjectStatsCommand())
```

## Built-in Commands

### Code Analysis Commands

#### `analyze <file_path>`
Analyzes code files for issues and metrics.

```python
result = await shell.execute_command("analyze", ["src/utils.py"])
```

#### `explain <file_path>`
Provides detailed explanation of code functionality.

```python
result = await shell.execute_command("explain", ["README.md"])
```

#### `fix <file_path>`
Automatically fixes code issues.

```python
result = await shell.execute_command("fix", ["src/buggy_code.py"])
```

### Code Generation Commands

#### `generate <description>`
Generates code from natural language description.

```python
result = await shell.execute_command("generate", 
    ["python function to sort a list"]
)
```

#### `test <file_path>`
Generates unit tests for code.

```python
result = await shell.execute_command("test", ["src/calculator.py"])
```

#### `docs <file_path>`
Generates documentation for code.

```python
result = await shell.execute_command("docs", ["src/api.py"])
```

### Project Management Commands

#### `status`
Shows system and project status.

```python
result = await shell.execute_command("status")
```

#### `search <query>`
Searches through project files.

```python
result = await shell.execute_command("search", ["function_name"])
```

#### `refactor <file_path>`
Suggests code refactoring improvements.

```python
result = await shell.execute_command("refactor", ["legacy_code.py"])
```

### Configuration Commands

#### `config [get|set] [key] [value]`
Manages configuration settings.

```python
# Get configuration value
result = await shell.execute_command("config", ["get", "primary_model"])

# Set configuration value  
result = await shell.execute_command("config", ["set", "timeout", "60"])
```

#### `models [list|info|test]`
Manages AI models.

```python
# List available models
result = await shell.execute_command("models", ["list"])

# Test a specific model
result = await shell.execute_command("models", ["test", "gpt-4o"])
```

### Session Management Commands

#### `session [new|save|load|list]`
Manages shell sessions.

```python
# Create new session
result = await shell.execute_command("session", ["new"])

# Save current session
result = await shell.execute_command("session", ["save"])

# List saved sessions
result = await shell.execute_command("session", ["list"])
```

#### `history [clear]`
Manages command history.

```python
# Show command history
result = await shell.execute_command("history")

# Clear history
result = await shell.execute_command("history", ["clear"])
```

## Data Models

### CommandResult

Contains the results of command execution.

```python
@dataclass
class CommandResult:
    command: str
    args: List[str]
    success: bool
    output: str
    error_message: Optional[str]
    execution_time: float
    metadata: Dict[str, Any]
    timestamp: datetime
```

### Session

Represents an interactive shell session.

```python
@dataclass
class Session:
    session_id: str
    workspace_path: Optional[Path]
    created_at: datetime
    last_activity: datetime
    command_history: List[str]
    variables: Dict[str, Any]
    preferences: Dict[str, Any]
```

### CustomCommand

Base class for implementing custom commands.

```python
class CustomCommand:
    name: str
    description: str
    usage: str
    
    async def execute(self, args: List[str]) -> CommandResult:
        """Execute the command with given arguments."""
        raise NotImplementedError
    
    def get_help(self) -> str:
        """Return help text for the command."""
        return f"{self.description}\n\nUsage: {self.usage}"
    
    def validate_args(self, args: List[str]) -> bool:
        """Validate command arguments."""
        return True
```

## Shell Integration

### IDE Integration

The shell can be integrated into IDEs and editors:

```python
# VS Code extension integration
class VSCodeShellIntegration:
    def __init__(self):
        self.shell = InteractiveShell()
    
    async def analyze_current_file(self, file_path: str):
        """Analyze the currently open file in VS Code."""
        result = await self.shell.execute_command("analyze", [file_path])
        return self.format_for_vscode(result)
    
    async def explain_selection(self, code: str, language: str):
        """Explain selected code."""
        # Create temporary file with selection
        temp_file = self.create_temp_file(code, language)
        result = await self.shell.execute_command("explain", [temp_file])
        return result.output
```

### CLI Wrapper

Create CLI tools that wrap the shell functionality:

```python
#!/usr/bin/env python3
"""Custom CLI tool using Aurelis shell."""

import asyncio
import sys
from aurelis.shell import InteractiveShell

async def main():
    if len(sys.argv) < 2:
        print("Usage: aurelis-cli <command> [args...]")
        return
    
    shell = InteractiveShell()
    command = sys.argv[1]
    args = sys.argv[2:]
    
    try:
        result = await shell.execute_command(command, args)
        if result.success:
            print(result.output)
        else:
            print(f"Error: {result.error_message}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Command failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## Automation Examples

### Batch Processing

Process multiple files with shell commands:

```python
async def batch_analyze_project():
    shell = InteractiveShell()
    project_files = ["src/main.py", "src/utils.py", "src/models.py"]
    
    results = []
    for file_path in project_files:
        result = await shell.execute_command("analyze", [file_path])
        results.append({
            "file": file_path,
            "success": result.success,
            "issues_found": result.metadata.get("issues_count", 0)
        })
    
    # Generate summary report
    total_files = len(results)
    successful_analyses = sum(1 for r in results if r["success"])
    total_issues = sum(r["issues_found"] for r in results)
    
    print(f"Batch Analysis Complete:")
    print(f"Files analyzed: {successful_analyses}/{total_files}")
    print(f"Total issues found: {total_issues}")
```

### Continuous Integration

Integrate shell commands into CI/CD pipelines:

```python
async def ci_code_quality_check():
    """Run code quality checks for CI/CD."""
    shell = InteractiveShell()
    
    # Analyze all Python files
    result = await shell.execute_command("analyze", ["./src"])
    if not result.success:
        print("Code analysis failed")
        return False
    
    # Check for critical issues
    analysis_data = result.metadata
    critical_issues = analysis_data.get("critical_issues", 0)
    
    if critical_issues > 0:
        print(f"Found {critical_issues} critical issues. Build failed.")
        return False
    
    # Generate documentation
    docs_result = await shell.execute_command("docs", ["./src"])
    if docs_result.success:
        print("Documentation generated successfully")
    
    print("All quality checks passed")
    return True
```

### Development Workflow

Automate common development tasks:

```python
async def development_workflow(feature_branch: str):
    """Automated development workflow."""
    shell = InteractiveShell()
    
    # 1. Analyze new/modified files
    print("Step 1: Analyzing code...")
    modified_files = get_modified_files(feature_branch)
    
    for file_path in modified_files:
        result = await shell.execute_command("analyze", [file_path])
        if not result.success:
            print(f"Analysis failed for {file_path}")
            continue
        
        # Fix critical issues automatically
        if result.metadata.get("critical_issues", 0) > 0:
            print(f"Fixing critical issues in {file_path}")
            fix_result = await shell.execute_command("fix", [file_path])
            if fix_result.success:
                print(f"Issues fixed in {file_path}")
    
    # 2. Generate tests for new functions
    print("Step 2: Generating tests...")
    for file_path in modified_files:
        if file_path.endswith('.py') and not file_path.startswith('test_'):
            test_result = await shell.execute_command("test", [file_path])
            if test_result.success:
                print(f"Tests generated for {file_path}")
    
    # 3. Update documentation
    print("Step 3: Updating documentation...")
    docs_result = await shell.execute_command("docs", ["./src"])
    if docs_result.success:
        print("Documentation updated")
    
    print("Development workflow completed")
```

## Custom Command Development

### Simple Custom Command

```python
from aurelis.shell import CustomCommand, CommandResult

class GitStatusCommand(CustomCommand):
    name = "git-status"
    description = "Show enhanced git status with AI insights"
    usage = "git-status [options]"
    
    async def execute(self, args: List[str]) -> CommandResult:
        import subprocess
        
        try:
            # Get git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return CommandResult(
                    command=self.name,
                    args=args,
                    success=False,
                    error_message="Failed to get git status"
                )
            
            # Parse modified files
            modified_files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    status = line[:2]
                    filename = line[3:]
                    modified_files.append((status, filename))
            
            # Generate insights for modified Python files
            insights = []
            for status, filename in modified_files:
                if filename.endswith('.py'):
                    # Use shell to analyze file
                    shell = InteractiveShell()
                    analysis = await shell.execute_command("analyze", [filename])
                    if analysis.success:
                        issues = analysis.metadata.get("issues_count", 0)
                        insights.append(f"{filename}: {issues} issues found")
            
            output = "Git Status with AI Insights:\n"
            output += f"Modified files: {len(modified_files)}\n"
            output += "\nAI Analysis:\n"
            output += "\n".join(insights) if insights else "No Python files to analyze"
            
            return CommandResult(
                command=self.name,
                args=args,
                success=True,
                output=output,
                metadata={"modified_files": len(modified_files)}
            )
            
        except Exception as e:
            return CommandResult(
                command=self.name,
                args=args,
                success=False,
                error_message=str(e)
            )
```

### Advanced Custom Command

```python
class ProjectHealthCommand(CustomCommand):
    name = "project-health"
    description = "Comprehensive project health analysis"
    usage = "project-health [--detailed] [--output-format=json|text]"
    
    def __init__(self):
        self.shell = InteractiveShell()
    
    async def execute(self, args: List[str]) -> CommandResult:
        detailed = "--detailed" in args
        output_format = "text"
        
        # Parse output format
        for arg in args:
            if arg.startswith("--output-format="):
                output_format = arg.split("=")[1]
        
        try:
            health_data = await self.analyze_project_health(detailed)
            
            if output_format == "json":
                import json
                output = json.dumps(health_data, indent=2)
            else:
                output = self.format_health_report(health_data, detailed)
            
            return CommandResult(
                command=self.name,
                args=args,
                success=True,
                output=output,
                metadata=health_data
            )
            
        except Exception as e:
            return CommandResult(
                command=self.name,
                args=args,
                success=False,
                error_message=str(e)
            )
    
    async def analyze_project_health(self, detailed: bool) -> Dict[str, Any]:
        """Analyze overall project health."""
        health_data = {
            "code_quality": {},
            "test_coverage": {},
            "documentation": {},
            "dependencies": {},
            "security": {}
        }
        
        # Analyze code quality
        analyze_result = await self.shell.execute_command("analyze", ["./src"])
        if analyze_result.success:
            health_data["code_quality"] = analyze_result.metadata
        
        # Check test coverage
        test_files = list(Path("./tests").glob("**/*.py")) if Path("./tests").exists() else []
        src_files = list(Path("./src").glob("**/*.py")) if Path("./src").exists() else []
        
        if src_files:
            coverage_ratio = len(test_files) / len(src_files)
            health_data["test_coverage"] = {
                "ratio": coverage_ratio,
                "test_files": len(test_files),
                "source_files": len(src_files)
            }
        
        # Check documentation
        docs_files = list(Path("./docs").glob("**/*.md")) if Path("./docs").exists() else []
        health_data["documentation"] = {
            "files_count": len(docs_files),
            "has_readme": Path("README.md").exists()
        }
        
        return health_data
    
    def format_health_report(self, data: Dict[str, Any], detailed: bool) -> str:
        """Format health data as human-readable report."""
        report = "Project Health Report\n"
        report += "=" * 50 + "\n\n"
        
        # Code Quality
        cq = data.get("code_quality", {})
        report += f"Code Quality: {cq.get('score', 'N/A')}/100\n"
        report += f"Issues: {cq.get('issues_count', 0)}\n"
        report += f"Critical: {cq.get('critical_issues', 0)}\n\n"
        
        # Test Coverage
        tc = data.get("test_coverage", {})
        if tc:
            ratio = tc.get("ratio", 0)
            report += f"Test Coverage: {ratio:.1%}\n"
            report += f"Test Files: {tc.get('test_files', 0)}\n"
            report += f"Source Files: {tc.get('source_files', 0)}\n\n"
        
        # Documentation
        docs = data.get("documentation", {})
        report += f"Documentation Files: {docs.get('files_count', 0)}\n"
        report += f"Has README: {'Yes' if docs.get('has_readme') else 'No'}\n"
        
        return report
```

## Configuration

### Shell Configuration

```yaml
shell:
  prompt_format: "aurelis:{workspace}[{session}]> "
  history_size: 1000
  auto_save_session: true
  command_timeout: 60
  
  completion:
    enabled: true
    fuzzy_matching: true
    max_suggestions: 10
  
  output:
    color_scheme: "monokai"
    paging: true
    max_lines: 100
  
  aliases:
    a: "analyze"
    g: "generate"
    e: "explain"
    f: "fix"
```

### Custom Command Registration

```python
# Register commands programmatically
shell = InteractiveShell()

# Register single command
shell.add_custom_command(ProjectHealthCommand())

# Register multiple commands
commands = [
    GitStatusCommand(),
    ProjectHealthCommand(),
    CustomDeployCommand()
]

for command in commands:
    shell.add_custom_command(command)
```

## Error Handling

```python
from aurelis.shell.exceptions import (
    CommandNotFoundError,
    InvalidArgumentsError,
    CommandExecutionError,
    SessionError
)

try:
    result = await shell.execute_command("unknown-command")
except CommandNotFoundError:
    print("Command not found")
except InvalidArgumentsError as e:
    print(f"Invalid arguments: {e}")
except CommandExecutionError as e:
    print(f"Command execution failed: {e}")
except SessionError as e:
    print(f"Session error: {e}")
```

## Best Practices

1. **Command Validation**: Always validate arguments before execution
2. **Error Handling**: Implement comprehensive error handling
3. **Session Management**: Use sessions for stateful operations
4. **Output Formatting**: Provide both human-readable and machine-readable output
5. **Performance**: Implement timeouts for long-running commands
6. **Documentation**: Document custom commands thoroughly
7. **Testing**: Test custom commands with various inputs

For more advanced integration patterns and examples, refer to the main Aurelis documentation.
