"""
Enterprise-grade interactive shell for Aurelis GitHub AI Code Assistant.

This module provides a sophisticated, production-ready interactive command-line
interface with comprehensive GitHub model integration, auto-completion, syntax
highlighting, session management, and enterprise-grade functionality.

Features:
    - Rich interactive prompt with syntax highlighting
    - Intelligent auto-completion for commands and file paths
    - Session management with persistent history
    - Direct GitHub model integration via Azure AI Inference
    - Real-time code analysis and generation
    - Comprehensive documentation and help system
    - Enterprise-grade error handling and logging

Author: Gamecooler19 (Lead Developer at Kanopus)
Organization: Kanopus - Pioneering AI-driven development solutions
Project: Aurelis - Enterprise AI Code Assistant
Website: https://aurelis.kanopus.org
"""
import asyncio
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.lexers import PygmentsLexer
    from prompt_toolkit.styles import Style
    from prompt_toolkit.shortcuts import confirm
    from pygments.lexers import PythonLexer, BashLexer
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    # Create dummy classes for when prompt_toolkit is not available
    class Completer:
        pass
    class Completion:
        pass
    class Style:
        @staticmethod
        def from_dict(style_dict):
            return None
    class FileHistory:
        def __init__(self, filename):
            pass
    class AutoSuggestFromHistory:
        pass
    class KeyBindings:
        pass

from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from aurelis.core.config import get_config
from aurelis.core.logging import get_logger
from aurelis.core.session import SessionManager
from aurelis.core.context import ContextManager
from aurelis.models import get_model_orchestrator, ModelRequest
from aurelis.core.types import ModelType, TaskType, Configuration
from aurelis.analysis import CodeAnalyzer
from aurelis.tools import ToolManager


class ShellCommand(Enum):
    """Available shell commands for the Aurelis interactive interface."""
    HELP = "help"
    EXIT = "exit"
    QUIT = "quit"
    CLEAR = "clear"
    HISTORY = "history"
    CONFIG = "config"
    STATUS = "status"
    ANALYZE = "analyze"
    GENERATE = "generate"
    EXPLAIN = "explain"
    FIX = "fix"
    REFACTOR = "refactor"
    TEST = "test"
    DOCS = "docs"
    SEARCH = "search"
    SESSION = "session"
    TOOLS = "tools"
    MODELS = "models"


@dataclass
class CommandHistory:
    """Command history management."""
    commands: List[str] = field(default_factory=list)
    max_size: int = 1000
    
    def add(self, command: str) -> None:
        """Add a command to history."""
        if command and command != self.commands[-1:]:
            self.commands.append(command)
            if len(self.commands) > self.max_size:
                self.commands.pop(0)
    
    def get_recent(self, n: int = 10) -> List[str]:
        """Get recent commands."""
        return self.commands[-n:]
    
    def search(self, pattern: str) -> List[str]:
        """Search command history."""
        return [cmd for cmd in self.commands if pattern.lower() in cmd.lower()]


class AurelisCompleter(Completer):
    """Custom completer for Aurelis shell commands."""
    
    def __init__(self):
        self.commands = [cmd.value for cmd in ShellCommand]
        self.subcommands = {
            "config": ["get", "set", "list", "reset"],
            "session": ["new", "load", "save", "list", "clear"],
            "models": ["list", "info", "test", "benchmark"],
            "tools": ["list", "run", "install", "uninstall"],
        }
    
    def get_completions(self, document, complete_event):
        """Generate completions for the current input."""
        text = document.text_before_cursor
        words = text.split()
        
        if not words or (len(words) == 1 and not text.endswith(' ')):
            # Complete main commands
            word = words[0] if words else ""
            for cmd in self.commands:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))
        
        elif len(words) >= 1 and words[0] in self.subcommands:
            # Complete subcommands
            if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
                word = words[1] if len(words) == 2 else ""
                for subcmd in self.subcommands[words[0]]:
                    if subcmd.startswith(word):
                        yield Completion(subcmd, start_position=-len(word))
        
        # File path completion for file-based commands
        file_commands = ["analyze", "explain", "fix", "refactor", "test", "docs"]
        if words and words[0] in file_commands:
            # Basic file completion (can be enhanced)
            try:
                current_dir = Path.cwd()
                if len(words) > 1:
                    partial_path = words[-1]
                    base_path = Path(partial_path).parent if '/' in partial_path or '\\' in partial_path else current_dir
                    prefix = Path(partial_path).name if '/' in partial_path or '\\' in partial_path else partial_path
                else:
                    base_path = current_dir
                    prefix = ""
                
                if base_path.exists() and base_path.is_dir():
                    for item in base_path.iterdir():
                        if item.name.startswith(prefix):
                            if item.is_dir():
                                yield Completion(f"{item.name}/", start_position=-len(prefix))
                            else:
                                yield Completion(item.name, start_position=-len(prefix))
            except Exception:
                pass


class InteractiveShell:
    """
    Enterprise-grade interactive shell for Aurelis.
    
    Provides a sophisticated command-line interface with rich features including
    syntax highlighting, auto-completion, session management, and direct AI model
    integration for code analysis, generation, and optimization.
    """
    
    def __init__(self, config: Optional[Configuration] = None):
        """Initialize the interactive shell."""
        self.config = config or get_config()
        self.logger = get_logger(__name__)
        self.console = Console()
        self.session_manager = SessionManager()
        self.context = ContextManager()
        self.command_history = CommandHistory()
        
        # Initialize core components
        self.model_orchestrator = get_model_orchestrator()
        self.analyzer = CodeAnalyzer()
        self.tool_manager = ToolManager()
        
        # Shell state
        self.running = True
        self.current_session = None
        self.workspace_path = Path.cwd()
        
        # Command mapping
        self.command_handlers = {
            ShellCommand.HELP: self._handle_help,
            ShellCommand.EXIT: self._handle_exit,
            ShellCommand.QUIT: self._handle_exit,
            ShellCommand.CLEAR: self._handle_clear,
            ShellCommand.HISTORY: self._handle_history,
            ShellCommand.CONFIG: self._handle_config,
            ShellCommand.STATUS: self._handle_status,
            ShellCommand.ANALYZE: self._handle_analyze,
            ShellCommand.GENERATE: self._handle_generate,
            ShellCommand.EXPLAIN: self._handle_explain,
            ShellCommand.FIX: self._handle_fix,
            ShellCommand.REFACTOR: self._handle_refactor,
            ShellCommand.TEST: self._handle_test,
            ShellCommand.DOCS: self._handle_docs,
            ShellCommand.SEARCH: self._handle_search,
            ShellCommand.SESSION: self._handle_session,
            ShellCommand.TOOLS: self._handle_tools,
            ShellCommand.MODELS: self._handle_models,        }
        
        # Initialize session
        self._initialize_session()
    
    def _initialize_session(self) -> None:
        """Initialize a new shell session."""
        try:
            self.current_session = self.session_manager.create_session(
                project_path=self.workspace_path
            )
            self.logger.info(f"Shell session initialized: {self.current_session.session_id}")
        except Exception as e:
            self.logger.error(f"Failed to initialize session: {e}")
            self.console.print(f"[yellow]Warning: Session initialization failed: {e}[/yellow]")
    
    async def run(self) -> None:
        """Run the interactive shell."""
        self.console.print(Panel.fit(
            "[bold blue]Aurelis AI Code Assistant[/bold blue]\n"
            "[cyan]Enterprise-grade AI-powered development assistant[/cyan]\n"
            "Type 'help' for available commands or 'exit' to quit",
            border_style="blue"
        ))
        
        # Setup prompt toolkit if available
        if PROMPT_TOOLKIT_AVAILABLE:
            history = FileHistory('.aurelis_history')
            completer = AurelisCompleter()
            style = Style.from_dict({
                'prompt': '#00aa00 bold',
                'path': '#888888',
                'time': '#666666',
            })
            
            while self.running:
                try:
                    # Create prompt with context
                    prompt_text = self._create_prompt()
                    
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: prompt(
                            prompt_text,
                            history=history,
                            auto_suggest=AutoSuggestFromHistory(),
                            completer=completer,
                            style=style,
                            complete_while_typing=True
                        )
                    )
                    
                    if user_input.strip():
                        self.command_history.add(user_input.strip())
                        await self._process_command(user_input.strip())
                        
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Use 'exit' or 'quit' to leave the shell[/yellow]")
                except EOFError:
                    break
                except Exception as e:
                    self.logger.error(f"Shell error: {e}")
                    self.console.print(f"[red]Error: {e}[/red]")
        else:
            # Fallback for when prompt_toolkit is not available
            while self.running:
                try:
                    prompt_text = self._create_prompt()
                    user_input = input(prompt_text)
                    
                    if user_input.strip():
                        self.command_history.add(user_input.strip())
                        await self._process_command(user_input.strip())
                        
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Use 'exit' or 'quit' to leave the shell[/yellow]")
                except EOFError:
                    break
                except Exception as e:
                    self.logger.error(f"Shell error: {e}")
                    self.console.print(f"[red]Error: {e}[/red]")
        
        self.console.print("[green]Goodbye![/green]")
    
    def _create_prompt(self) -> str:
        """Create the command prompt."""
        workspace_name = self.workspace_path.name
        session_id = self.current_session.session_id[-8:] if self.current_session else "no-session"
        return f"aurelis:{workspace_name}[{session_id}]> "
    
    async def _process_command(self, command: str) -> None:
        """Process a user command."""
        parts = command.split()
        if not parts:
            return
        
        cmd_name = parts[0].lower()
        args = parts[1:]
        
        # Find matching command
        cmd_enum = None
        for cmd in ShellCommand:
            if cmd.value == cmd_name:
                cmd_enum = cmd
                break
        
        if cmd_enum and cmd_enum in self.command_handlers:
            try:
                await self.command_handlers[cmd_enum](args)
            except Exception as e:
                self.logger.error(f"Command handler error: {e}")
                self.console.print(f"[red]Command failed: {e}[/red]")
        else:
            self.console.print(f"[red]Unknown command: {cmd_name}[/red]")
            self.console.print("[yellow]Type 'help' for available commands[/yellow]")
    
    async def _handle_help(self, args: List[str]) -> None:
        """Display help information."""
        if args:
            # Help for specific command
            cmd_name = args[0].lower()
            help_text = self._get_command_help(cmd_name)
            if help_text:
                self.console.print(Panel(help_text, title=f"Help: {cmd_name}", border_style="blue"))
            else:
                self.console.print(f"[red]No help available for command: {cmd_name}[/red]")
        else:
            # General help
            help_table = Table(title="Aurelis Shell Commands")
            help_table.add_column("Command", style="cyan", no_wrap=True)
            help_table.add_column("Description", style="white")
            
            command_descriptions = {
                "help": "Show this help message or help for specific commands",
                "exit/quit": "Exit the shell",
                "clear": "Clear the terminal screen",
                "history": "Show command history",
                "config": "Manage configuration settings",
                "status": "Show system status and information",
                "analyze": "Analyze code files for issues and metrics",
                "generate": "Generate code from natural language descriptions",
                "explain": "Explain what code does and how it works",
                "fix": "Automatically fix code issues",
                "refactor": "Suggest and apply code refactoring",
                "test": "Generate unit tests for code",
                "docs": "Generate documentation for code",
                "search": "Search through code and documentation",
                "session": "Manage shell sessions",
                "tools": "Manage and execute development tools",
                "models": "Manage and configure AI models",
            }
            
            for cmd in ShellCommand:
                desc = command_descriptions.get(cmd.value, "No description available")
                help_table.add_row(cmd.value, desc)
            
            self.console.print(help_table)
            self.console.print("\n[cyan]Use 'help <command>' for detailed help on specific commands[/cyan]")
    
    def _get_command_help(self, cmd_name: str) -> Optional[str]:
        """Get detailed help for a specific command."""
        help_texts = {
            "analyze": """
[bold]analyze <file_path>[/bold]

Analyze code files for issues, metrics, and quality assessment.

[cyan]Examples:[/cyan]
  analyze main.py              - Analyze a single Python file
  analyze src/utils.py         - Analyze file with path
  analyze .                    - Analyze all files in current directory

[cyan]Features:[/cyan]
  • Syntax error detection
  • Code quality metrics
  • Security vulnerability scanning
  • Performance analysis
  • Style and formatting checks
            """,
            "generate": """
[bold]generate <description>[/bold]

Generate code from natural language descriptions.

[cyan]Examples:[/cyan]
  generate "python function to sort a list"
  generate "REST API endpoint for user authentication"
  generate "database migration script"

[cyan]Features:[/cyan]
  • Context-aware code generation
  • Multiple programming language support
  • Best practices enforcement
  • Documentation generation
            """,
            "explain": """
[bold]explain <file_path>[/bold]

Explain what code does and how it works.

[cyan]Examples:[/cyan]
  explain main.py              - Explain a Python file
  explain src/algorithm.js     - Explain JavaScript code
  explain README.md            - Explain documentation

[cyan]Features:[/cyan]
  • Line-by-line code explanation
  • Algorithm analysis
  • Architecture overview
  • Dependencies and relationships
            """,
            "fix": """
[bold]fix <file_path>[/bold]

Automatically fix code issues and errors.

[cyan]Examples:[/cyan]
  fix main.py                  - Fix issues in Python file
  fix src/                     - Fix all files in directory

[cyan]Features:[/cyan]
  • Syntax error correction
  • Logic error detection and fixes
  • Performance optimizations
  • Security vulnerability patches
  • Code style improvements
            """,
            "refactor": """
[bold]refactor <file_path>[/bold]

Suggest and apply code refactoring improvements.

[cyan]Examples:[/cyan]
  refactor legacy_code.py      - Refactor old Python code
  refactor src/utils.js        - Refactor JavaScript utilities

[cyan]Features:[/cyan]
  • Code structure improvements
  • Performance optimizations
  • Readability enhancements
  • Design pattern applications        
  • Technical debt reduction
            """,
        }
        
        return help_texts.get(cmd_name)
    
    async def _handle_exit(self, args: List[str]) -> None:
        """Exit the shell."""
        if self.current_session:
            self.session_manager.close_session(self.current_session.session_id)
        self.running = False
    
    async def _handle_clear(self, args: List[str]) -> None:
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    async def _handle_history(self, args: List[str]) -> None:
        """Show command history."""
        if args and args[0] == "clear":
            self.command_history.commands.clear()
            self.console.print("[green]Command history cleared[/green]")
            return
        
        recent_commands = self.command_history.get_recent(20)
        if not recent_commands:
            self.console.print("[yellow]No command history available[/yellow]")
            return
        
        history_table = Table(title="Recent Commands")
        history_table.add_column("#", style="cyan", width=4)
        history_table.add_column("Command", style="white")
        
        for i, cmd in enumerate(recent_commands, 1):
            history_table.add_row(str(i), cmd)
        
        self.console.print(history_table)
    
    async def _handle_config(self, args: List[str]) -> None:
        """Handle configuration management."""
        if not args:
            # Show current configuration
            config_table = Table(title="Current Configuration")
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value", style="white")
            
            config_data = self.config.model_dump()
            for key, value in config_data.items():
                config_table.add_row(key, str(value))
            
            self.console.print(config_table)
            return
        
        subcommand = args[0].lower()
        
        if subcommand == "get" and len(args) > 1:
            key = args[1]
            value = getattr(self.config, key, None)
            if value is not None:
                self.console.print(f"[cyan]{key}:[/cyan] {value}")
            else:
                self.console.print(f"[red]Configuration key not found: {key}[/red]")
        
        elif subcommand == "set" and len(args) > 2:
            key = args[1]
            value = args[2]
            try:
                setattr(self.config, key, value)
                self.console.print(f"[green]Set {key} = {value}[/green]")
            except Exception as e:
                self.console.print(f"[red]Failed to set configuration: {e}[/red]")
        
        else:
            self.console.print("[red]Usage: config [get <key>] [set <key> <value>][/red]")
    
    async def _handle_status(self, args: List[str]) -> None:
        """Show system status and information."""
        status_table = Table(title="Aurelis System Status")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="white")
        status_table.add_column("Details", style="yellow")
        
        # Model orchestrator status
        try:
            model_status = await self.model_orchestrator.health_check()
            status_table.add_row("Model Orchestrator", "✓ Ready", f"Primary: {self.config.primary_model}")
        except Exception as e:
            status_table.add_row("Model Orchestrator", "✗ Error", str(e))
        
        # Code analyzer status
        try:
            analyzer_status = self.analyzer.is_ready()
            status_table.add_row("Code Analyzer", "✓ Ready" if analyzer_status else "✗ Not Ready", "")
        except Exception as e:
            status_table.add_row("Code Analyzer", "✗ Error", str(e))
        
        # Tool manager status
        try:
            tools_count = len(self.tool_manager.get_available_tools())
            status_table.add_row("Tool Manager", "✓ Ready", f"{tools_count} tools available")
        except Exception as e:
            status_table.add_row("Tool Manager", "✗ Error", str(e))
        
        # Session status
        if self.current_session:
            session_age = datetime.now() - self.current_session.created_at
            status_table.add_row("Session", "✓ Active", f"Age: {session_age}")
        else:
            status_table.add_row("Session", "✗ No Session", "")
        
        # Workspace status
        status_table.add_row("Workspace", "✓ Active", str(self.workspace_path))
        
        self.console.print(status_table)
    
    async def _handle_analyze(self, args: List[str]) -> None:
        """Handle code analysis command."""
        if not args:
            self.console.print("[red]Usage: analyze <file_path>[/red]")
            return
        
        file_path = Path(args[0])
        if not file_path.exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        self.console.print(f"[blue]Analyzing {file_path}...[/blue]")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Analyzing code...", total=None)
                
                analysis_result = await self.analyzer.analyze_file(file_path)
                progress.update(task, completed=True)
            
            # Display analysis results
            if analysis_result.issues:
                issues_table = Table(title="Code Issues")
                issues_table.add_column("Type", style="cyan")
                issues_table.add_column("Severity", style="yellow")
                issues_table.add_column("Line", style="green")
                issues_table.add_column("Message", style="white")
                
                for issue in analysis_result.issues:
                    issues_table.add_row(
                        issue.type.value,
                        issue.severity.value,
                        str(issue.location.line_number),
                        issue.message
                    )
                
                self.console.print(issues_table)
            else:
                self.console.print("[green]No issues found![/green]")
            
            # Display metrics
            if analysis_result.metrics:
                metrics_table = Table(title="Code Metrics")
                metrics_table.add_column("Metric", style="cyan")
                metrics_table.add_column("Value", style="white")
                
                for key, value in analysis_result.metrics.items():
                    metrics_table.add_row(key, str(value))
                
                self.console.print(metrics_table)
            
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
            self.console.print(f"[red]Analysis failed: {e}[/red]")
    async def _handle_generate(self, args: List[str]) -> None:
        """Handle code generation command."""
        if not args:
            self.console.print("[red]Usage: generate <description>[/red]")
            return
        
        description = ' '.join(args)
        self.console.print(f"[blue]Generating code for: {description}[/blue]")
        
        try:
            # Use the model orchestrator to generate code
            model_request = ModelRequest(
                prompt=description,
                model_type=ModelType.CODESTRAL_2501,  # Use default model
                task_type=TaskType.CODE_GENERATION,
                metadata={"language": "python"}  # Default to Python
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:                
                task = progress.add_task("Generating code...", total=None)
                
                response = await self.model_orchestrator.send_request(model_request)
                progress.update(task, completed=True)
            
            if response and response.content:
                # Display the generated code
                syntax = Syntax(response.content, "python", theme="monokai", line_numbers=True)
                code_panel = Panel(syntax, title="Generated Code", border_style="green")
                self.console.print(code_panel)
                
                # Store in context
                self.context.last_model_response = response.content
                
                # Ask if user wants to save
                if Confirm.ask("Save generated code to file?"):
                    filename = Prompt.ask("Enter filename", default="generated_code.py")
                    with open(filename, 'w') as f:
                        f.write(response.content)
                    self.console.print(f"[green]Code saved to {filename}[/green]")
            else:
                self.console.print("[yellow]No code was generated[/yellow]")
                
        except Exception as e:
            self.logger.error(f"Generation error: {e}")
            self.console.print(f"[red]Code generation failed: {e}[/red]")
    
    async def _handle_explain(self, args: List[str]) -> None:
        """Handle code explanation command."""
        if not args:
            self.console.print("[red]Usage: explain <file_path>[/red]")
            return
        
        file_path = Path(args[0])
        if not file_path.exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        self.console.print(f"[blue]Explaining {file_path}...[/blue]")
        
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
              # Use the model orchestrator to explain the code
            model_request = ModelRequest(
                prompt=f"Provide a clear explanation of what this code does, its purpose, and how it works:\n\n{content}",
                model_type=ModelType.CODESTRAL_2501,
                task_type=TaskType.EXPLANATIONS,
                metadata={
                    "file_path": str(file_path),
                    "instruction": "Provide a clear explanation of what this code does, its purpose, and how it works."
                }
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console            ) as progress:
                task = progress.add_task("Analyzing and explaining code...", total=None)
                
                response = await self.model_orchestrator.send_request(model_request)
                progress.update(task, completed=True)
            
            if response and response.content:
                # Display the explanation
                explanation_panel = Panel(
                    Markdown(response.content),
                    title=f"Code Explanation: {file_path.name}",
                    border_style="blue"
                )
                self.console.print(explanation_panel)
            else:
                self.console.print("[yellow]No explanation was generated[/yellow]")                
        except Exception as e:
            self.logger.error(f"Explanation error: {e}")
            self.console.print(f"[red]Code explanation failed: {e}[/red]")
    
    async def _handle_fix(self, args: List[str]) -> None:
        """Handle code fixing command."""
        if not args:
            self.console.print("[red]Usage: fix <file_path>[/red]")
            return
        
        file_path = Path(args[0])
        if not file_path.exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        self.console.print(f"[blue]Analyzing and fixing {file_path}...[/blue]")
        
        try:
            # First analyze the file for issues
            analysis_result = self.analyzer.analyze_file(file_path)
            
            if not analysis_result.issues:
                self.console.print("[green]No issues found in the code![/green]")
                return
            
            # Display found issues
            issues_table = Table(title="Code Issues Found")
            issues_table.add_column("Type", style="cyan")
            issues_table.add_column("Severity", style="yellow")
            issues_table.add_column("Line", style="green")
            issues_table.add_column("Message", style="white")
            
            for issue in analysis_result.issues:
                issues_table.add_row(
                    issue.type.value,
                    issue.severity.value,
                    str(issue.location.line_number),
                    issue.message
                )
            
            self.console.print(issues_table)
            
            if Confirm.ask("Generate fixes for these issues?"):
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Prepare context with issues information
                issues_context = []
                for issue in analysis_result.issues:
                    issues_context.append({
                        "type": issue.type.value,
                        "severity": issue.severity.value,
                        "line": issue.location.line_number,
                        "message": issue.message,
                        "suggested_fix": issue.suggested_fix
                    })
                
                # Use the model orchestrator to generate fixes
                model_request = ModelRequest(
                    prompt=f"Fix the identified code issues while preserving functionality:\n\nCode:\n{content}\n\nIssues to fix:\n{issues_context}",
                    model_type=ModelType.CODESTRAL_2501,
                    task_type=TaskType.CODE_OPTIMIZATION,
                    metadata={
                        "file_path": str(file_path),
                        "instruction": "Fix the identified code issues while preserving functionality",
                        "issues": issues_context,
                        "preserve_comments": True,
                        "maintain_structure": True
                    }
                )
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console                ) as progress:
                    task = progress.add_task("Generating fixes...", total=None)
                    
                    response = await self.model_orchestrator.send_request(model_request)
                    progress.update(task, completed=True)
                
                if response and response.content:
                    # Display the fixed code
                    syntax = Syntax(response.content, file_path.suffix[1:] or "python", theme="monokai", line_numbers=True)
                    fixed_panel = Panel(syntax, title=f"Fixed Code: {file_path.name}", border_style="green")
                    self.console.print(fixed_panel)
                    
                    # Ask if user wants to save the fixes
                    if Confirm.ask("Apply these fixes to the file?"):
                        # Create backup
                        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                        backup_path.write_text(content)
                        self.console.print(f"[blue]Backup created: {backup_path}[/blue]")
                        
                        # Apply fixes
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(response.content)
                        self.console.print(f"[green]Fixes applied to {file_path}[/green]")
                else:
                    self.console.print("[yellow]No fixes were generated[/yellow]")
                    
        except Exception as e:
            self.logger.error(f"Fix error: {e}")
            self.console.print(f"[red]Code fixing failed: {e}[/red]")
    
    async def _handle_refactor(self, args: List[str]) -> None:
        """Handle code refactoring command."""
        if not args:
            self.console.print("[red]Usage: refactor <file_path>[/red]")
            return
        
        file_path = Path(args[0])
        if not file_path.exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        self.console.print(f"[blue]Analyzing refactoring opportunities for {file_path}...[/blue]")
        
        try:            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use the model orchestrator to suggest refactoring
            model_request = ModelRequest(
                prompt=f"Analyze the code and suggest refactoring improvements for better structure, performance, and maintainability:\n\n{content}",
                model_type=ModelType.CODESTRAL_2501,
                task_type=TaskType.REFACTORING,
                metadata={
                    "file_path": str(file_path),
                    "instruction": "Analyze the code and suggest refactoring improvements for better structure, performance, and maintainability",
                    "preserve_functionality": True,
                    "focus_areas": ["performance", "readability", "maintainability"]
                }
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console            ) as progress:
                task = progress.add_task("Analyzing refactoring opportunities...", total=None)
                
                response = await self.model_orchestrator.send_request(model_request)
                progress.update(task, completed=True)
            
            if response and response.content:
                # Display the refactoring suggestions
                refactor_panel = Panel(
                    Markdown(response.content),
                    title=f"Refactoring Suggestions: {file_path.name}",
                    border_style="yellow"
                )
                self.console.print(refactor_panel)
                
                # Ask if user wants to apply the refactoring
                if Confirm.ask("Apply these refactoring suggestions?"):
                    # Create backup
                    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                    backup_path.write_text(content)
                    self.console.print(f"[blue]Backup created: {backup_path}[/blue]")
                    
                    # This would need additional logic to extract and apply actual code changes
                    self.console.print("[yellow]Manual review and application of suggestions is recommended[/yellow]")
            else:
                self.console.print("[yellow]No refactoring suggestions were generated[/yellow]")
                
        except Exception as e:
            self.logger.error(f"Refactor error: {e}")
            self.console.print(f"[red]Refactoring analysis failed: {e}[/red]")
    
    async def _handle_test(self, args: List[str]) -> None:
        """Handle test generation command."""
        if not args:
            self.console.print("[red]Usage: test <file_path>[/red]")
            return
        
        file_path = Path(args[0])
        if not file_path.exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        self.console.print(f"[blue]Generating tests for {file_path}...[/blue]")
        
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
              # Use the model orchestrator to generate tests
            model_request = ModelRequest(
                prompt=f"Generate comprehensive unit tests for this code including edge cases and error scenarios:\n\n{content}",
                model_type=ModelType.CODESTRAL_2501,
                task_type=TaskType.CODE_GENERATION,
                metadata={
                    "file_path": str(file_path),
                    "instruction": "Generate comprehensive unit tests for this code including edge cases and error scenarios",
                    "test_framework": "pytest",  # Default to pytest
                    "coverage_target": "high"
                }
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console            ) as progress:
                task = progress.add_task("Generating tests...", total=None)
                
                response = await self.model_orchestrator.send_request(model_request)
                progress.update(task, completed=True)
            
            if response and response.content:
                # Display the generated tests
                syntax = Syntax(response.content, "python", theme="monokai", line_numbers=True)
                test_panel = Panel(syntax, title=f"Generated Tests: test_{file_path.stem}.py", border_style="green")
                self.console.print(test_panel)
                
                # Ask if user wants to save the tests
                if Confirm.ask("Save generated tests to file?"):
                    test_filename = f"test_{file_path.stem}.py"
                    with open(test_filename, 'w') as f:
                        f.write(response.content)
                    self.console.print(f"[green]Tests saved to {test_filename}[/green]")
            else:
                self.console.print("[yellow]No tests were generated[/yellow]")
                
        except Exception as e:
            self.logger.error(f"Test generation error: {e}")
            self.console.print(f"[red]Test generation failed: {e}[/red]")
    
    async def _handle_docs(self, args: List[str]) -> None:
        """Handle documentation generation command."""
        if not args:
            self.console.print("[red]Usage: docs <file_path>[/red]")
            return
        
        file_path = Path(args[0])
        if not file_path.exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        self.console.print(f"[blue]Generating documentation for {file_path}...[/blue]")
        
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
              # Use the model orchestrator to generate documentation
            model_request = ModelRequest(
                prompt=f"Generate comprehensive documentation for this code including purpose, parameters, return values, examples, and usage notes:\n\n{content}",
                model_type=ModelType.CODESTRAL_2501,
                task_type=TaskType.DOCUMENTATION,
                metadata={
                    "file_path": str(file_path),
                    "instruction": "Generate comprehensive documentation for this code including purpose, parameters, return values, examples, and usage notes.",
                    "format": "markdown",
                    "include_examples": True
                }
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console            ) as progress:
                task = progress.add_task("Generating documentation...", total=None)
                
                response = await self.model_orchestrator.send_request(model_request)
                progress.update(task, completed=True)
            
            if response and response.content:
                # Display the generated documentation
                doc_panel = Panel(
                    Markdown(response.content),
                    title=f"Generated Documentation: {file_path.name}",
                    border_style="green"
                )
                self.console.print(doc_panel)
                
                # Ask if user wants to save the documentation
                if Confirm.ask("Save generated documentation to file?"):
                    doc_filename = f"{file_path.stem}_docs.md"
                    with open(doc_filename, 'w') as f:
                        f.write(response.content)
                    self.console.print(f"[green]Documentation saved to {doc_filename}[/green]")
            else:
                self.console.print("[yellow]No documentation was generated[/yellow]")
                
        except Exception as e:
            self.logger.error(f"Documentation generation error: {e}")
            self.console.print(f"[red]Documentation generation failed: {e}[/red]")
    
    async def _handle_search(self, args: List[str]) -> None:
        """Handle search command."""
        if not args:
            self.console.print("[red]Usage: search <query>[/red]")
            return
        
        query = ' '.join(args)
        self.console.print(f"[blue]Searching for: {query}[/blue]")
        
        try:
            # Search in the current workspace
            search_results = []
            for file_path in self.workspace_path.rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            # Find line numbers
                            lines = content.split('\n')
                            matches = []
                            for i, line in enumerate(lines, 1):
                                if query.lower() in line.lower():
                                    matches.append((i, line.strip()))
                            search_results.append((file_path, matches))
                except Exception:
                    continue
            
            if search_results:
                for file_path, matches in search_results:
                    match_table = Table(title=f"Matches in {file_path}")
                    match_table.add_column("Line", style="cyan", width=6)
                    match_table.add_column("Content", style="white")
                    
                    for line_num, line_content in matches[:5]:  # Show first 5 matches
                        match_table.add_row(str(line_num), line_content)
                    
                    self.console.print(match_table)
                    
                    if len(matches) > 5:
                        self.console.print(f"[yellow]... and {len(matches) - 5} more matches[/yellow]")
            else:
                self.console.print(f"[yellow]No matches found for: {query}[/yellow]")
                
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            self.console.print(f"[red]Search failed: {e}[/red]")
    
    async def _handle_session(self, args: List[str]) -> None:
        """Handle session management commands."""
        if not args:
            # Show current session info
            if self.current_session:
                session_table = Table(title="Current Session")
                session_table.add_column("Property", style="cyan")
                session_table.add_column("Value", style="white")
                
                session_table.add_row("Session ID", self.current_session.session_id)
                session_table.add_row("Created", str(self.current_session.created_at))
                session_table.add_row("Last Activity", str(self.current_session.last_activity))
                session_table.add_row("Workspace", str(self.current_session.project_path))
                session_table.add_row("Active Files", str(len(self.current_session.active_files)))
                
                self.console.print(session_table)
            else:
                self.console.print("[yellow]No active session[/yellow]")
            return
        
        subcommand = args[0].lower()
        
        if subcommand == "new":
            # Create new session
            if self.current_session:
                await self.session_manager.save_session(self.current_session)
            self._initialize_session()
            self.console.print("[green]New session created[/green]")
        
        elif subcommand == "save":
            if self.current_session:
                await self.session_manager.save_session(self.current_session)
                self.console.print("[green]Session saved[/green]")
            else:
                self.console.print("[yellow]No active session to save[/yellow]")
        
        elif subcommand == "list":
            sessions = await self.session_manager.list_sessions()
            if sessions:
                sessions_table = Table(title="Available Sessions")
                sessions_table.add_column("ID", style="cyan")
                sessions_table.add_column("Created", style="yellow")
                sessions_table.add_column("Workspace", style="white")
                
                for session in sessions[-10:]:  # Show last 10 sessions
                    sessions_table.add_row(
                        session.session_id[-8:],
                        session.created_at.strftime("%Y-%m-%d %H:%M"),
                        str(session.project_path) if session.project_path else "N/A"
                    )
                
                self.console.print(sessions_table)
            else:
                self.console.print("[yellow]No saved sessions found[/yellow]")
        
        elif subcommand == "clear":
            if Confirm.ask("Clear all session data?"):
                self.current_session = None
                await self.session_manager.clear_sessions()
                self.console.print("[green]Session data cleared[/green]")
        
        else:
            self.console.print("[red]Usage: session [new|save|list|clear][/red]")
    
    async def _handle_tools(self, args: List[str]) -> None:
        """Handle tool management commands."""
        if not args:
            # List available tools
            tools = self.tool_manager.get_available_tools()
            if tools:
                tools_table = Table(title="Available Tools")
                tools_table.add_column("Name", style="cyan")
                tools_table.add_column("Description", style="white")
                tools_table.add_column("Status", style="green")
                
                for tool_name, tool_info in tools.items():
                    status = "Ready" if tool_info.get("available", False) else "Not Available"
                    tools_table.add_row(
                        tool_name,
                        tool_info.get("description", "No description"),
                        status
                    )
                
                self.console.print(tools_table)
            else:
                self.console.print("[yellow]No tools available[/yellow]")
            return
        
        subcommand = args[0].lower()
        
        if subcommand == "run" and len(args) > 1:
            tool_name = args[1]
            tool_args = args[2:] if len(args) > 2 else []
            
            try:
                result = await self.tool_manager.execute_tool(tool_name, tool_args)
                if result.success:
                    self.console.print(f"[green]Tool '{tool_name}' executed successfully[/green]")
                    if result.output:
                        self.console.print(result.output)
                else:
                    self.console.print(f"[red]Tool execution failed: {result.error_message}[/red]")
            except Exception as e:
                self.console.print(f"[red]Tool execution error: {e}[/red]")
        
        else:            self.console.print("[red]Usage: tools [run <tool_name> [args...]][/red]")
    
    async def _handle_models(self, args: List[str]) -> None:
        """Handle model management commands."""
        if not args:
            # Show available models
            models_table = Table(title="Available AI Models")
            models_table.add_column("Model", style="cyan")
            models_table.add_column("Type", style="yellow")
            models_table.add_column("Status", style="green")
            
            for model in ModelType:
                try:
                    # Check model availability (this would be implemented in the orchestrator)
                    status = "Available"
                    model_type = "Code Generation" if "codestral" in model.value else "General"
                    models_table.add_row(model.value, model_type, status)
                except Exception:
                    models_table.add_row(model.value, "Unknown", "Error")
            
            self.console.print(models_table)
            return
        
        subcommand = args[0].lower()
        
        if subcommand == "info" and len(args) > 1:
            model_name = args[1]
            try:
                model_type = ModelType(model_name)
                
                info_table = Table(title=f"Model Information: {model_name}")
                info_table.add_column("Property", style="cyan")
                info_table.add_column("Value", style="white")
                
                info_table.add_row("Name", model_type.value)
                info_table.add_row("Provider", "GitHub AI via Azure")
                info_table.add_row("Type", "Large Language Model")
                
                # Add more model-specific information here
                self.console.print(info_table)
            except ValueError:
                self.console.print(f"[red]Unknown model: {model_name}[/red]")
        
        elif subcommand == "test" and len(args) > 1:
            model_name = args[1]
            test_prompt = " ".join(args[2:]) if len(args) > 2 else "Hello, world!"
            
            try:
                model_type = ModelType(model_name)
                
                model_request = ModelRequest(
                    prompt=test_prompt,
                    model_type=model_type,
                    task_type=TaskType.CODE_GENERATION,
                    metadata={"test_mode": True}
                )
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console                ) as progress:
                    task = progress.add_task(f"Testing {model_name}...", total=None)
                    
                    response = await self.model_orchestrator.send_request(model_request)
                    progress.update(task, completed=True)
                
                if response:
                    self.console.print(f"[green]Model {model_name} is working correctly[/green]")
                    self.console.print(f"Response: {response.content[:200]}...")
                else:
                    self.console.print(f"[red]Model {model_name} test failed[/red]")
                    
            except ValueError:
                self.console.print(f"[red]Unknown model: {model_name}[/red]")
            except Exception as e:
                self.console.print(f"[red]Model test error: {e}[/red]")
        
        else:
            self.console.print("[red]Usage: models [info <model>] [test <model> [prompt]][/red]")


# Main entry point functions
async def run_shell(config: Optional[Configuration] = None) -> None:
    """Run the interactive shell."""
    shell = InteractiveShell(config)
    await shell.run()


def main() -> None:
    """Main entry point for the shell."""
    try:
        asyncio.run(run_shell())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Shell error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
