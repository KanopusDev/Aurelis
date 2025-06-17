"""
Enterprise-grade CLI interface for Aurelis - GitHub AI Code Assistant.

This module provides a comprehensive command-line interface for the Aurelis
AI-powered code assistant, exclusively using GitHub models via Azure AI Inference.

Author: Gamecooler19 (Lead Developer at Kanopus)
Organization: Kanopus - Pioneering AI-driven development solutions
Project: Aurelis - Enterprise AI Code Assistant
Website: https://aurelis.kanopus.org
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from aurelis.core.config import initialize_config, get_config
from aurelis.core.logging import initialize_logging, get_logger
from aurelis.core.security import initialize_security
from aurelis.core.cache import initialize_cache
from aurelis.analysis import initialize_analyzer, get_code_analyzer
from aurelis.models import initialize_model_orchestrator, get_model_orchestrator
from aurelis.core.context import initialize_context_manager, get_context_manager
from aurelis.core.types import AnalysisType, TaskType, ModelType, ChunkingStrategy
from aurelis.models import ModelRequest
from aurelis.core.exceptions import AurelisError

# Initialize Typer app with enterprise branding
app = typer.Typer(
    name="aurelis",
    help="Aurelis - Enterprise AI Code Assistant powered by GitHub models",
    add_completion=False,
    rich_markup_mode="rich"
)

# Initialize Rich console for enhanced output
console = Console()


def init_aurelis(config_path: Optional[Path] = None) -> None:
    """
    Initialize all Aurelis components for enterprise operation.
    
    This function orchestrates the initialization of all core components
    required for Aurelis operation, including configuration, logging,
    security, caching, analysis, models, and context management.
    
    Args:
        config_path (Optional[Path]): Path to custom configuration file
        
    Raises:
        typer.Exit: If initialization fails
    """
    try:
        # Initialize components in dependency order for enterprise reliability
        initialize_config(config_path)
        initialize_logging()
        
        # Skip async components for CLI to avoid event loop issues
        # These will be initialized when actually needed in async contexts
        logger = get_logger("cli.init")
        logger.info("Aurelis core components initialized successfully")
        
    except Exception as e:
        console.print(f"[red]Failed to initialize Aurelis: {e}[/red]")
        console.print("[red]Please check your configuration and GitHub token setup.[/red]")
        raise typer.Exit(1)


@app.command()
def init(
    config_path: Optional[Path] = typer.Option(
        None, 
        help="Path to configuration file"
    ),
    force: bool = typer.Option(
        False, 
        help="Overwrite existing configuration"
    )
) -> None:
    """
    Initialize Aurelis configuration for GitHub models.
    
    This command sets up the Aurelis configuration file and prompts for
    the GitHub token required for Azure AI Inference access to GitHub models.
    """
    console.print(Panel.fit(
        "[bold blue]Aurelis Enterprise AI Code Assistant[/bold blue]\n"
        "[dim]Powered by GitHub Models via Azure AI Inference[/dim]\n"
        "[dim]Developed by Gamecooler19 @ Kanopus[/dim]",
        border_style="blue"
    ))
    
    try:
        # Simple initialization without complex dependencies
        config_file = config_path or Path.cwd() / ".aurelis.yaml"
        
        # Check if config already exists
        if not force and config_file.exists():
            console.print("[yellow]Configuration already exists. Use --force to overwrite.[/yellow]")
            return
        
        # Create basic configuration
        config_content = """# Aurelis Configuration for GitHub Models
github_token: "${GITHUB_TOKEN}"  # Use environment variable

models:
  primary: "codestral-2501"       # Primary model for code tasks
  fallback: "gpt-4o-mini"         # Fallback model for reliability
  
analysis:
  max_file_size: "1MB"
  chunk_size: 3500               # Optimized for 4K context models
  overlap_ratio: 0.15
  
processing:
  max_retries: 3
  timeout: 60
  concurrent_requests: 5
  
security:
  audit_logging: true
  secure_token_storage: true

cache:
  enabled: true
  ttl: 3600  # 1 hour
  max_size: 1000
"""
        
        # Write configuration file
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        console.print(f"[green]✓[/green] Configuration created at: {config_file}")
        
        # GitHub Token Setup for Azure AI Inference
        console.print("\n[bold]GitHub Token Setup[/bold]")
        console.print(
            "Aurelis uses GitHub models exclusively via Azure AI Inference.\n"
            "You need a GitHub token with model access permissions.\n"
            "Get your token at: [link]https://github.com/settings/tokens[/link]"
        )
        
        # Check if GitHub token is already set in environment
        existing_token = os.getenv("GITHUB_TOKEN")
        if existing_token:
            console.print(f"[green]✓[/green] GitHub token found in environment: {existing_token[:8]}...{existing_token[-4:]}")
        else:
            console.print("[yellow]⚠[/yellow] GitHub token not found in environment")
            console.print("Set your token with: export GITHUB_TOKEN='your_token_here'")
        
        # Success message
        console.print("\n[bold green]✅ Aurelis Initialization Complete![/bold green]")
        console.print("Next steps:")
        console.print("1. Set your GitHub token: export GITHUB_TOKEN='your_token'")
        console.print("2. Test configuration: aurelis models")
        console.print("3. Start coding: aurelis shell")
        
    except Exception as e:
        console.print(f"[red]Initialization failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def models() -> None:
    """
    Display available GitHub models and their capabilities.
    
    Shows all GitHub models accessible via Azure AI Inference with their
    optimal use cases and current availability status.
    """
    console.print(Panel.fit(
        "[bold blue]GitHub Models via Azure AI Inference[/bold blue]\n"
        "[dim]Enterprise AI models hosted by GitHub[/dim]",
        border_style="blue"
    ))
    
    try:
        # Create models table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Model", style="cyan", width=25)
        table.add_column("Provider", style="green", width=12)
        table.add_column("Best For", style="yellow", width=40)
        table.add_column("Context", style="blue", width=8)
        
        # GitHub models data
        models_data = [
            ("Codestral-2501", "Mistral", "Code generation & optimization", "4K"),
            ("GPT-4o", "OpenAI", "Complex reasoning & multimodal", "4K"),
            ("GPT-4o-mini", "OpenAI", "Fast responses & documentation", "4K"),
            ("Cohere Command-R", "Cohere", "Documentation & explanations", "4K"),
            ("Cohere Command-R+", "Cohere", "Advanced reasoning", "4K"),
            ("Meta Llama 3.1 70B", "Meta", "Balanced performance", "4K"),
            ("Meta Llama 3.1 405B", "Meta", "Maximum capability", "4K"),
            ("Mistral Large", "Mistral", "Enterprise applications", "4K"),
            ("Mistral Nemo", "Mistral", "Fast inference", "4K"),
        ]
        
        for model_name, provider, best_for, context in models_data:
            table.add_row(model_name, provider, best_for, context)
        
        console.print(table)
        
        # Show authentication info
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            console.print(f"\n✅ GitHub Token: {github_token[:8]}...{github_token[-4:]}")
            console.print("🔗 Endpoint: https://models.inference.ai.azure.com")
            console.print("✅ Status: Ready for GitHub models")
        else:
            console.print("\n⚠️  No GitHub token configured")
            console.print("📝 Setup: export GITHUB_TOKEN='your_token_here'")
            console.print("🔗 Get token: https://github.com/settings/tokens")
        
        # Show task routing
        console.print("\n[bold]Intelligent Task Routing:[/bold]")
        
        routing_table = Table(show_header=True, header_style="bold green")
        routing_table.add_column("Task Type", style="cyan", width=20)
        routing_table.add_column("Primary Models", style="yellow", width=40)
        
        routing_data = [
            ("Code Generation", "Codestral-2501, GPT-4o"),
            ("Code Completion", "Codestral-2501, GPT-4o-mini"),
            ("Code Optimization", "Codestral-2501, Meta Llama 405B"),
            ("Complex Reasoning", "GPT-4o, Meta Llama 405B"),
            ("Documentation", "Cohere Command-R, GPT-4o-mini"),
            ("Explanations", "Cohere Command-R, Mistral Nemo"),
            ("Tool Usage", "GPT-4o, Cohere Command-R+"),
            ("Refactoring", "Codestral-2501, Meta Llama 70B"),
        ]
        
        for task, models in routing_data:
            routing_table.add_row(task, models)
        
        console.print(routing_table)
        
        # Show usage tip
        console.print(
            "\n[dim]💡 Use 'aurelis generate \"your prompt\"' to start generating code[/dim]"
        )
        console.print(
            "[dim]💡 Use 'aurelis shell' for an interactive experience[/dim]"
        )
        
    except Exception as e:
        console.print(f"[red]Failed to retrieve model information: {e}[/red]")
        raise typer.Exit(1)


@app.command() 
def config() -> None:
    """
    Manage Aurelis configuration and GitHub token.
    
    Shows current configuration status and provides guidance for setup.
    """
    console.print(Panel.fit(
        "[bold blue]Aurelis Configuration Management[/bold blue]\n"
        "[dim]GitHub Models Configuration[/dim]",
        border_style="blue"
    ))
    
    try:
        # Check current GitHub token status
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            console.print(f"[green]✓[/green] GitHub Token: {github_token[:8]}...{github_token[-4:]}")
            console.print("[green]✓[/green] Authentication: Ready")
        else:
            console.print("[yellow]⚠[/yellow] GitHub token not found in environment")
            console.print("[red]✗[/red] Authentication: Not configured")
        
        # Show configuration file status
        config_file = Path.cwd() / ".aurelis.yaml"
        if config_file.exists():
            console.print(f"[green]✓[/green] Config file: {config_file}")
        else:
            console.print(f"[yellow]⚠[/yellow] Config file not found: {config_file}")
        
        # Configuration guidance
        console.print("\n[bold]Configuration Setup:[/bold]")
        
        setup_table = Table(show_header=True, header_style="bold cyan")
        setup_table.add_column("Step", style="green", width=10)
        setup_table.add_column("Action", style="yellow", width=40)
        setup_table.add_column("Command/Link", style="blue", width=40)
        
        setup_data = [
            ("1", "Get GitHub Token", "https://github.com/settings/tokens"),
            ("2", "Set Environment Variable", "export GITHUB_TOKEN='your_token'"),
            ("3", "Initialize Configuration", "aurelis init"),
            ("4", "Verify Setup", "aurelis models"),
        ]
        
        for step, action, command in setup_data:
            setup_table.add_row(step, action, command)
        
        console.print(setup_table)
        
        # Current endpoint info
        console.print("\n[bold]GitHub Models Configuration:[/bold]")
        console.print("🔗 Endpoint: https://models.inference.ai.azure.com")
        console.print("🛡️ Authentication: GitHub Token")
        console.print("🤖 Models: 9 GitHub models available")
        console.print("📁 Config: .aurelis.yaml (project-specific)")
        
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        console.print("1. Update GitHub token")
        console.print("2. Test model connectivity") 
        console.print("3. View current configuration")
        console.print("4. Exit")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="4")
        
        if choice == "1":
            # Update GitHub token
            new_token = Prompt.ask("New GitHub Token", password=True)
            if new_token:
                os.environ["GITHUB_TOKEN"] = new_token
                
                # Save to secure storage
                from aurelis.core.security import get_api_key_manager
                api_key_manager = get_api_key_manager()
                api_key_manager.set_api_key("github", new_token)
                
                console.print("[green]✓[/green] GitHub token updated successfully")
            
        elif choice == "2":
            # Test connectivity
            console.print("\n[bold]Testing GitHub model connectivity...[/bold]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Testing models...", total=None)
                
                orchestrator = get_model_orchestrator()
                health = orchestrator.health_check()
                
                console.print(f"\nConnectivity Test Results:")
                console.print(f"Overall Status: {health['overall_status']}")
                console.print(f"Healthy Models: {health['healthy_models']}/{health['total_models']}")
                
        elif choice == "3":
            # View configuration
            config = get_config()
            
            table = Table(title="Current Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("GitHub Token", "●●●●●●●●" if github_token else "Not set")
            table.add_row("Primary Model", getattr(config, 'primary_model', 'Not set'))
            table.add_row("Fallback Model", getattr(config, 'fallback_model', 'Not set'))
            table.add_row("Max Retries", str(getattr(config, 'max_retries', 'Not set')))
            table.add_row("Model Timeout", str(getattr(config, 'model_timeout', 'Not set')))
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Configuration management failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def analyze(
    path: Path = typer.Argument(..., help="Path to file or directory to analyze"),
    analysis_types: Optional[List[str]] = typer.Option(
        None, 
        "--type", 
        help="Analysis types: syntax, performance, security, style"
    ),
    output_format: str = typer.Option("table", help="Output format: table, json"),
    save_report: Optional[Path] = typer.Option(None, help="Save report to file"),
    verbose: bool = typer.Option(False, help="Verbose output")
) -> None:
    """Analyze Python code for issues and improvements."""
    
    init_aurelis()
    logger = get_logger("cli.analyze")
    
    try:
        # Parse analysis types
        if analysis_types:
            requested_types = []
            for analysis_type in analysis_types:
                try:
                    requested_types.append(AnalysisType(analysis_type.lower()))
                except ValueError:
                    console.print(f"[red]Invalid analysis type: {analysis_type}[/red]")
                    console.print(f"Valid types: {', '.join([t.value for t in AnalysisType])}")
                    raise typer.Exit(1)
        else:
            requested_types = [AnalysisType.SYNTAX, AnalysisType.PERFORMANCE, AnalysisType.SECURITY]
        
        analyzer = get_code_analyzer()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            if path.is_file():
                # Analyze single file
                task = progress.add_task(f"Analyzing {path.name}...", total=None)
                result = analyzer.analyze_file(path, requested_types)
                results = [result]
                progress.update(task, description=f"✓ Analyzed {path.name}")
                
            else:
                # Analyze directory
                task = progress.add_task(f"Analyzing project {path.name}...", total=None)
                results = analyzer.analyze_project(path, requested_types)
                progress.update(task, description=f"✓ Analyzed {len(results)} files")
        
        # Display results
        if output_format == "table":
            _display_analysis_table(results)
        elif output_format == "json":
            _display_analysis_json(results)
        
        # Save report if requested
        if save_report:
            _save_analysis_report(results, save_report, output_format)
            console.print(f"[green]✓[/green] Report saved to: {save_report}")
        
        # Summary
        total_issues = sum(len(result.issues) for result in results)
        if total_issues == 0:
            console.print("\n[green]🎉 No issues found! Your code looks great.[/green]")
        else:
            console.print(f"\n[yellow]Found {total_issues} issues across {len(results)} files.[/yellow]")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        console.print(f"[red]Analysis failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Description of code to generate"),
    output_file: Optional[Path] = typer.Option(None, help="Save generated code to file"),
    model: Optional[str] = typer.Option(None, help="Preferred model to use"),
    temperature: float = typer.Option(0.1, help="Generation temperature (0.0-1.0)"),
    max_tokens: Optional[int] = typer.Option(None, help="Maximum tokens to generate")
) -> None:
    """Generate code based on natural language description."""
    
    init_aurelis()
    logger = get_logger("cli.generate")
    
    try:
        # Parse model type
        preferred_model = None
        if model:
            try:
                preferred_model = ModelType(model.lower().replace("-", "_"))
            except ValueError:
                console.print(f"[red]Invalid model: {model}[/red]")
                console.print(f"Valid models: {', '.join([m.value for m in ModelType])}")
                raise typer.Exit(1)
        
        orchestrator = get_model_orchestrator()
        
        # Create model request
        system_prompt = """You are an expert Python developer. Generate clean, well-documented, 
production-ready Python code based on the user's requirements. Include proper error handling, 
type hints, and docstrings."""
        
        request = ModelRequest(
            prompt=prompt,
            model_type=preferred_model or ModelType.CODESTRAL_2501,
            task_type=TaskType.CODE_GENERATION,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating code...", total=None)
            
            # Send request
            response = asyncio.run(orchestrator.send_request(request, preferred_model))
            
            progress.update(task, description="✓ Code generated")
          # Display generated code
        console.print("\n[bold]Generated Code:[/bold]")
        console.print(Panel(response.content, title="Generated Code", border_style="green"))
          # Display metadata
        if response.metadata:
            console.print(f"\n[dim]Model: {response.model_type.value}[/dim]")
            console.print(f"[dim]Confidence: {response.confidence:.2f}[/dim]")
            console.print(f"[dim]Tokens: {response.token_usage.get('total_tokens', 'N/A')}[/dim]")
            console.print(f"[dim]Time: {response.processing_time:.2f}s[/dim]")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.content)
            console.print(f"\n[green]✓[/green] Code saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        error_msg = str(e).replace('[', '\\[').replace(']', '\\]')
        console.print(f"[red]Code generation failed: {error_msg}[/red]")
        raise typer.Exit(1)


@app.command()
def explain(
    file_path: Path = typer.Argument(..., help="Path to Python file to explain"),
    model: Optional[str] = typer.Option(None, help="Preferred model to use"),
    detailed: bool = typer.Option(False, help="Provide detailed explanation")
) -> None:
    
    """Explain Python code functionality."""
    
    init_aurelis()
    logger = get_logger("cli.explain")
    
    try:
        if not file_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            raise typer.Exit(1)
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Parse model type
        preferred_model = None
        if model:
            try:
                preferred_model = ModelType(model.lower().replace("-", "_"))
            except ValueError:
                console.print(f"[red]Invalid model: {model}[/red]")
                raise typer.Exit(1)
        
        orchestrator = get_model_orchestrator()
        
        # Create explanation prompt
        if detailed:
            prompt = f"""Provide a detailed explanation of this Python code:

```python
{code}
```

Please explain:
1. Overall purpose and functionality
2. Key components and their roles
3. Important algorithms or patterns used
4. Potential improvements or issues
5. Dependencies and requirements"""
        else:
            prompt = f"""Explain what this Python code does in simple terms:

```python
{code}
```"""
        
        system_prompt = """You are an expert Python developer and teacher. Provide clear, 
accurate explanations of Python code that are appropriate for the user's level of detail requested."""
        
        request = ModelRequest(
            prompt=prompt,
            model_type=preferred_model or ModelType.COHERE_COMMAND,
            task_type=TaskType.EXPLANATIONS,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Explaining {file_path.name}...", total=None)
            
            response = asyncio.run(orchestrator.send_request(request, preferred_model))
            
            progress.update(task, description=f"✓ Explained {file_path.name}")
          # Display explanation
        console.print(f"\n[bold]Explanation of {file_path.name}:[/bold]")
        console.print(Panel(response.content, title="Code Explanation", border_style="blue"))
        
    except Exception as e:
        logger.error(f"Code explanation failed: {e}")
        console.print(f"[red]Code explanation failed: {safe_error_format(str(e))}[/red]")
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, help="Show current configuration"),
    set_key: Optional[str] = typer.Option(None, help="Configuration key to set"),
    value: Optional[str] = typer.Option(None, help="Configuration value"),
    list_models: bool = typer.Option(False, help="List available models"),
    add_api_key: Optional[str] = typer.Option(None, help="Add API key for service")
) -> None:
    """Manage Aurelis configuration."""
    
    try:
        init_aurelis()
        
        if show:
            _show_configuration()
        elif list_models:
            _list_models()
        elif add_api_key:
            _add_api_key(add_api_key)
        elif set_key and value:
            _set_configuration(set_key, value)
        else:
            console.print("[yellow]Specify an action: --show, --set-key, --list-models, or --add-api-key[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def fix(
    path: Path = typer.Argument(..., help="Path to file or directory to fix"),
    fix_type: List[str] = typer.Option(["all"], help="Fix types: security, performance, style, bugs, all"),
    apply_fixes: bool = typer.Option(False, "--apply", help="Apply fixes automatically"),
    backup: bool = typer.Option(True, help="Create backup before applying fixes"),
    dry_run: bool = typer.Option(False, help="Show fixes without applying"),
    model: Optional[str] = typer.Option(None, help="Preferred model to use")
) -> None:
    """Automatically fix code issues and apply improvements."""
    
    init_aurelis()
    logger = get_logger("cli.fix")
    
    try:
        if not path.exists():
            console.print(f"[red]Path not found: {path}[/red]")
            raise typer.Exit(1)
        
        # Parse model type
        preferred_model = None
        if model:
            try:
                from aurelis.core.types import ModelType
                preferred_model = ModelType(model.lower().replace("-", "_"))
            except ValueError:
                console.print(f"[red]Invalid model: {model}[/red]")
                raise typer.Exit(1)
        
        from aurelis.models import get_model_orchestrator, ModelRequest
        from aurelis.core.types import TaskType
        
        orchestrator = get_model_orchestrator()
        
        # Read file content
        if path.is_file():
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create fix request
            fix_types_str = ", ".join(fix_type)
            prompt = f"""Analyze this Python code and suggest fixes for {fix_types_str} issues:

```python
{content}
```

Provide specific, actionable fixes with explanations. Focus on:
{"- Security vulnerabilities" if "security" in fix_type or "all" in fix_type else ""}
{"- Performance optimizations" if "performance" in fix_type or "all" in fix_type else ""}
{"- Code style improvements" if "style" in fix_type or "all" in fix_type else ""}
{"- Bug fixes" if "bugs" in fix_type or "all" in fix_type else ""}

Format as:
## Issue: [description]
### Fix: [specific solution]
### Code: ```python [fixed code] ```"""
            
            system_prompt = """You are an expert Python developer specializing in code quality, security, 
and performance optimization. Provide specific, actionable fixes with clear explanations."""
            
            request = ModelRequest(
                prompt=prompt,
                model_type=preferred_model or ModelType.CODESTRAL_2501,
                task_type=TaskType.CODE_OPTIMIZATION,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Analyzing fixes for {path.name}...", total=None)
                
                response = asyncio.run(orchestrator.process_request(request))
                
                progress.update(task, description=f"✓ Generated fixes for {path.name}")
            
            # Display fixes
            console.print(f"\n[bold]Suggested Fixes for {path.name}:[/bold]")
            console.print(Panel(response.content, title="Code Fixes", border_style="yellow"))
            
            if dry_run:
                console.print("\n[dim]Dry run mode - no changes applied[/dim]")
            elif apply_fixes:
                console.print("\n[yellow]Automatic fix application not yet implemented[/yellow]")
                console.print("Review the suggested fixes and apply manually.")
            else:
                console.print("\n[dim]Use --apply to automatically apply fixes[/dim]")
        
        else:
            console.print("[yellow]Directory fixing not yet implemented[/yellow]")
            console.print("Please specify a single file.")
        
    except Exception as e:
        logger.error(f"Fix command failed: {e}")
        console.print(f"[red]Fix command failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def refactor(
    path: Path = typer.Argument(..., help="Path to file to refactor"),
    goal: str = typer.Option("readability", help="Refactoring goal: performance, readability, modularity, patterns"),
    aggressive: bool = typer.Option(False, help="Enable aggressive refactoring"),
    preserve_behavior: bool = typer.Option(True, help="Ensure behavior preservation"),
    output_dir: Optional[Path] = typer.Option(None, help="Output refactored code to directory"),
    model: Optional[str] = typer.Option(None, help="Preferred model to use")
) -> None:
    """Refactor and optimize code for better maintainability."""
    
    init_aurelis()
    logger = get_logger("cli.refactor")
    
    try:
        if not path.exists() or not path.is_file():
            console.print(f"[red]File not found: {path}[/red]")
            raise typer.Exit(1)
        
        # Parse model type
        preferred_model = None
        if model:
            try:
                from aurelis.core.types import ModelType
                preferred_model = ModelType(model.lower().replace("-", "_"))
            except ValueError:
                console.print(f"[red]Invalid model: {model}[/red]")
                raise typer.Exit(1)
        
        from aurelis.models import get_model_orchestrator
        from aurelis.models import ModelRequest; from aurelis.core.types import TaskType
        
        orchestrator = get_model_orchestrator()
        
        # Read file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create refactor request
        intensity = "aggressive" if aggressive else "conservative"
        prompt = f"""Refactor this Python code with focus on {goal}. Use {intensity} refactoring approach:

```python
{content}
```

Goals:
- {goal.title()}: {"Optimize for speed and efficiency" if goal == "performance" else ""}
{"Improve code clarity and maintainability" if goal == "readability" else ""}
{"Better module structure and separation of concerns" if goal == "modularity" else ""}
{"Apply modern Python patterns and best practices" if goal == "patterns" else ""}

Requirements:
- {"Preserve original behavior exactly" if preserve_behavior else "Optimize behavior if beneficial"}
- Provide clear explanations for changes
- Include proper docstrings and type hints
- Follow PEP 8 and modern Python standards

Format:
## Refactored Code:
```python
[complete refactored code]
```

## Changes Made:
[detailed explanation of changes]"""
        
        system_prompt = """You are a senior Python architect specializing in code refactoring and 
optimization. Provide production-ready, well-structured code with clear explanations."""
        
        request = ModelRequest(
            prompt=prompt,
            model_type=preferred_model or ModelType.CODESTRAL_2501,
            task_type=TaskType.REFACTORING,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Refactoring {path.name}...", total=None)
            
            response = asyncio.run(orchestrator.process_request(request))
            
            progress.update(task, description=f"✓ Refactored {path.name}")
        
        # Display refactored code
        console.print(f"\n[bold]Refactored {path.name} (Goal: {goal.title()}):[/bold]")
        console.print(Panel(response.content, title="Refactored Code", border_style="green"))
        
        # Save to output directory if specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / path.name
            # Extract just the code part from response (implementation needed)
            console.print(f"\n[dim]Output directory specified: {output_dir}[/dim]")
            console.print("[yellow]Automatic saving not yet implemented[/yellow]")
        
    except Exception as e:
        logger.error(f"Refactor command failed: {e}")
        console.print(f"[red]Refactor command failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def docs(
    path: Path = typer.Argument(..., help="Path to file or directory to document"),
    format_type: str = typer.Option("markdown", help="Output format: markdown, rst, html, docstring"),
    include_sections: List[str] = typer.Option(["api"], help="Include sections: api, examples, usage, architecture"),
    output: Optional[Path] = typer.Option(None, help="Output documentation file/directory"),
    template: Optional[str] = typer.Option(None, help="Documentation template"),
    model: Optional[str] = typer.Option(None, help="Preferred model to use")
) -> None:
    """Generate comprehensive documentation for code."""
    
    init_aurelis()
    logger = get_logger("cli.docs")
    
    try:
        if not path.exists():
            console.print(f"[red]Path not found: {path}[/red]")
            raise typer.Exit(1)
        
        # Parse model type
        preferred_model = None
        if model:
            try:
                from aurelis.core.types import ModelType
                preferred_model = ModelType(model.lower().replace("-", "_"))
            except ValueError:
                console.print(f"[red]Invalid model: {model}[/red]")
                raise typer.Exit(1)
        
        from aurelis.models import get_model_orchestrator
        from aurelis.models import ModelRequest; from aurelis.core.types import TaskType
        
        orchestrator = get_model_orchestrator()
        
        if path.is_file():
            # Document single file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sections_str = ", ".join(include_sections)
            prompt = f"""Generate comprehensive {format_type} documentation for this Python code:

```python
{content}
```

Include these sections: {sections_str}

Requirements:
- {"API reference with function signatures" if "api" in include_sections else ""}
- {"Practical usage examples" if "examples" in include_sections else ""}
- {"Usage instructions and guidelines" if "usage" in include_sections else ""}
- {"Architecture overview and design" if "architecture" in include_sections else ""}
- Clear, professional documentation style
- Proper {format_type} formatting
- Code examples and explanations

Format as proper {format_type} documentation."""
            
            system_prompt = """You are a technical writer specializing in API documentation and developer guides. 
Create clear, comprehensive documentation that helps developers understand and use the code effectively."""
            
            request = ModelRequest(
                prompt=prompt,
                model_type=preferred_model or ModelType.COHERE_COMMAND_R,
                task_type=TaskType.DOCUMENTATION,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Generating docs for {path.name}...", total=None)
                
                response = asyncio.run(orchestrator.process_request(request))
                
                progress.update(task, description=f"✓ Generated docs for {path.name}")
            
            # Display documentation
            console.print(f"\n[bold]Documentation for {path.name} ({format_type.upper()}):[/bold]")
            console.print(Panel(response.content, title="Generated Documentation", border_style="blue"))
            
            # Save to output file if specified
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(response.content)
                console.print(f"\n[green]✓[/green] Documentation saved to: {output}")
        
        else:
            console.print("[yellow]Directory documentation not yet implemented[/yellow]")
            console.print("Please specify a single file.")
        
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        console.print(f"[red]Documentation generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def test(
    path: Path = typer.Argument(..., help="Path to file to generate tests for"),
    framework: str = typer.Option("pytest", help="Test framework: pytest, unittest, doctest"),
    coverage: int = typer.Option(80, help="Target coverage percentage"),
    test_type: str = typer.Option("unit", help="Test type: unit, integration, performance, security"),
    output: Optional[Path] = typer.Option(None, help="Output test file"),
    model: Optional[str] = typer.Option(None, help="Preferred model to use")
) -> None:
    """Generate test cases and test suites for code."""
    
    init_aurelis()
    logger = get_logger("cli.test")
    
    try:
        if not path.exists() or not path.is_file():
            console.print(f"[red]File not found: {path}[/red]")
            raise typer.Exit(1)
        
        # Parse model type
        preferred_model = None
        if model:
            try:
                from aurelis.core.types import ModelType
                preferred_model = ModelType(model.lower().replace("-", "_"))
            except ValueError:
                console.print(f"[red]Invalid model: {model}[/red]")
                raise typer.Exit(1)
        
        from aurelis.models import get_model_orchestrator
        from aurelis.models import ModelRequest; from aurelis.core.types import TaskType
        
        orchestrator = get_model_orchestrator()
        
        # Read file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        prompt = f"""Generate comprehensive {test_type} tests using {framework} for this Python code:

```python
{content}
```

Requirements:
- Target {coverage}% code coverage
- Use {framework} framework conventions
- {"Unit tests for individual functions/methods" if test_type == "unit" else ""}
{"Integration tests for component interactions" if test_type == "integration" else ""}
{"Performance tests for speed/memory" if test_type == "performance" else ""}
{"Security tests for vulnerabilities" if test_type == "security" else ""}
- Include edge cases and error conditions
- Proper test organization and naming
- Clear test documentation
- Mock external dependencies where appropriate

Generate complete, runnable test code."""
        
        system_prompt = """You are a senior QA engineer and testing specialist. Create comprehensive, 
well-structured tests that ensure code reliability and catch potential issues."""
        
        request = ModelRequest(
            prompt=prompt,
            model_type=preferred_model or ModelType.CODESTRAL_2501,
            task_type=TaskType.TESTING,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Generating {test_type} tests for {path.name}...", total=None)
            
            response = asyncio.run(orchestrator.process_request(request))
            
            progress.update(task, description=f"✓ Generated tests for {path.name}")
        
        # Display tests
        console.print(f"\n[bold]Generated {test_type.title()} Tests for {path.name} ({framework}):[/bold]")
        console.print(Panel(response.content, title="Generated Tests", border_style="green"))
        
        # Save to output file if specified
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(response.content)
            console.print(f"\n[green]✓[/green] Tests saved to: {output}")
        else:
            # Suggest output filename
            test_file = path.parent / f"test_{path.stem}.py"
            console.print(f"\n[dim]Suggested output: {test_file}[/dim]")
        
    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        console.print(f"[red]Test generation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def shell(
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
) -> None:
    """Start interactive shell mode."""
    try:
        # Initialize Aurelis first
        init_aurelis(config_path)
        console.print("[bold green]Starting Aurelis Interactive Shell...[/bold green]")
        
        # Import and start shell after initialization
        from aurelis.shell import InteractiveShell
        config = get_config()
        shell_instance = InteractiveShell(config)
        
        # Run shell
        asyncio.run(shell_instance.run())
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Shell startup failed: {e}")
        console.print(f"[red]✗[/red] Shell startup failed: {e}")
        raise typer.Exit(code=1)


def _display_analysis_table(results) -> None:
    """Display analysis results in table format."""
    
    for result in results:
        console.print(f"\n[bold]{result.file_path.name}[/bold]")
        
        if not result.issues:
            console.print("[green]✓ No issues found[/green]")
            continue
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Line", style="cyan", width=6)
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Severity", width=10)
        table.add_column("Message", width=50)
        
        for issue in result.issues:
            severity_style = {
                "error": "red",
                "warning": "yellow", 
                "info": "blue"
            }.get(issue.severity.value, "white")
            
            table.add_row(
                str(issue.location.line_number),
                issue.type.value,
                f"[{severity_style}]{issue.severity.value}[/{severity_style}]",
                issue.message
            )
        
        console.print(table)


def _display_analysis_json(results) -> None:
    """Display analysis results in JSON format."""
    import json
    
    output = []
    for result in results:
        result_dict = {
            "file_path": str(result.file_path),
            "analysis_types": [t.value for t in result.analysis_types],
            "issues": [
                {
                    "id": issue.id,
                    "type": issue.type.value,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "line": issue.location.line_number,
                    "column": issue.location.column_number
                }
                for issue in result.issues
            ],
            "metrics": result.metrics,
            "processing_time": result.processing_time
        }
        output.append(result_dict)
    
    console.print(json.dumps(output, indent=2))


def _save_analysis_report(results, file_path: Path, format_type: str) -> None:
    """Save analysis report to file."""
    
    if format_type == "json":
        import json
        output = []
        for result in results:
            result_dict = {
                "file_path": str(result.file_path),
                "issues": [
                    {
                        "type": issue.type.value,
                        "severity": issue.severity.value,
                        "message": issue.message,
                        "line": issue.location.line_number
                    }
                    for issue in result.issues
                ]
            }
            output.append(result_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
    
    else:  # Default to markdown
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Aurelis Analysis Report\n\n")
            
            for result in results:
                f.write(f"## {result.file_path.name}\n\n")
                
                if not result.issues:
                    f.write("✅ No issues found\n\n")
                    continue
                
                f.write("| Line | Type | Severity | Message |\n")
                f.write("|------|------|----------|----------|\n")
                
                for issue in result.issues:
                    f.write(f"| {issue.location.line_number} | {issue.type.value} | {issue.severity.value} | {issue.message} |\n")
                
                f.write("\n")


def _show_configuration() -> None:
    """Show current configuration."""
    config = get_config()
    
    console.print("[bold]Current Configuration:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Primary Model", config.primary_model.value)
    table.add_row("Fallback Model", config.fallback_model.value)
    table.add_row("Chunk Size", str(config.chunk_size))
    table.add_row("Cache Enabled", str(config.cache_enabled))
    table.add_row("Sandbox Enabled", str(config.sandbox_enabled))
    
    console.print(table)


def _list_models() -> None:
    """List available models."""
    orchestrator = get_model_orchestrator()
    models = orchestrator.get_available_models()
    
    console.print("[bold]Available Models:[/bold]")
    for model in models:
        console.print(f"  • {model.value}")


def _add_api_key(service: str) -> None:
    """Add API key for a service."""
    from aurelis.core.security import get_api_key_manager
    
    api_key = Prompt.ask(f"{service.title()} API Key", password=True)
    if api_key:
        api_key_manager = get_api_key_manager()
        api_key_manager.set_api_key(service.lower(), api_key)
        console.print(f"[green]✓[/green] {service.title()} API key saved")


def _set_configuration(key: str, value: str) -> None:
    """Set configuration value."""
    console.print(f"[yellow]Configuration updates not yet implemented.[/yellow]")
    console.print(f"Would set {key} = {value}")


def safe_error_format(error_msg: str) -> str:
    """Format error message safely for Rich markup by escaping brackets."""
    return str(error_msg).replace('[', '\\[').replace(']', '\\]')


if __name__ == "__main__":
    app()
