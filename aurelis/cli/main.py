import os
import sys
import click
import logging
import asyncio
import pyperclip
from tempfile import TemporaryDirectory
from rich.live import Live
from rich.table import Table
from rich.syntax import Syntax
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler
from aurelis.core.services import AurelisServices
from aurelis.core.file import FileManager
from aurelis.core.database import VectorDB
from aurelis.core.reasoner import ReasoningResult
from aurelis.utils.config import Config
from aurelis.utils.code_utils import extract_code_blocks, format_code_block
from aurelis.utils.testing import run_static_analysis, run_unit_tests
from pathlib import Path
import datetime
from typing import Dict, Optional, Any, Tuple
from dotenv import load_dotenv
from aurelis.cli import handle_cli_arguments

# Initialize console before logging setup
console = Console()

def setup_logging(log_file: Optional[Path] = None) -> Path:
    """
    Configure application logging with file and console handlers.
    
    Args:
        log_file: Optional custom log file path. If None, default path is used.
        
    Returns:
        Path: The path where logs are being written
    """
    # Determine log file location
    if log_file is None:
        log_dir = Path.home() / ".aurelis" / "logs"
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # Use date-stamped log file for better log rotation
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"aurelis-{timestamp}.log"
    else:
        # Ensure parent directory exists
        log_file.parent.mkdir(exist_ok=True, parents=True)
    
    # Configure file handler for normal logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Configure console handler only for critical errors
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False, 
        show_path=False,
        console=console
    )
    console_handler.setLevel(logging.CRITICAL)  # Only show critical errors

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        force=True  # Override any existing configuration
    )
    
    # Get logger for this module
    logger = logging.getLogger("aurelis")
    logger.info(f"Logging initialized. Writing logs to: {log_file}")
    
    return log_file

# ASCII art welcome banner
WELCOME_ART = """
[bold blue]    _    _    _ ____  _____ _     ___ ____  [/]
[bold cyan]   / \\  | |  | |  _ \\| ____| |   |_ _/ ___| [/]
[bold green]  / _ \\ | |  | | |_) |  _| | |    | |\\___ \\ [/]
[bold yellow] / ___ \\| |__| |  _ <| |___| |___ | | ___) |[/]
[bold red]/_/   \\_\\_____/|_| \\_\\_____|_____|___|____/ [/]
[bold magenta]================================================[/]
[cyan]Enterprise-Grade Python Code Assistant[/]
[green]Type your code request below to begin...[/]
[bold magenta]================================================[/]
"""

# Global service instances
services: Optional[AurelisServices] = None
db: Optional[VectorDB] = None
logger: logging.Logger = logging.getLogger("aurelis")

def setup_services():
    """Initialize all services with proper error handling"""
    global services, db
    
    try:
        with Progress() as progress:
            task1 = progress.add_task("[green]Initializing AI services...", total=1)
            services = AurelisServices()
            progress.update(task1, advance=0.5)
            
            task2 = progress.add_task("[blue]Initializing vector database...", total=1)
            db = VectorDB()
            progress.update(task2, completed=1)
            
            # Initialize web search if keys are available
            config = Config.load()
            if "google_api_key" in config and "google_cx" in config:
                task3 = progress.add_task("[yellow]Setting up web search...", total=1)
                services.initialize_web_search(
                    config["google_api_key"],
                    config["google_cx"]
                )
                progress.update(task3, completed=1)
            
            progress.update(task1, completed=1)
        
        return True
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to initialize services: {str(e)}")
        return False

class ChatState:
    def __init__(self):
        self.reasoning_enabled = False
        self.search_enabled = False
        self.testing_enabled = True  # Auto-testing enabled by default
        self.conversation_history = []
        self.current_workspace = None
        self.last_code_block = None

@click.group(invoke_without_command=True)
@click.option('--log-file', '-l', help='Custom log file path', type=click.Path())
@click.option('--verbose', '-v', help='Enable verbose logging (show logs in console)', is_flag=True)
@click.pass_context
def cli(ctx, log_file, verbose):
    """Aurelis - Enterprise-grade AI coding assistant"""
    # Store options in context for subcommands to access
    ctx.ensure_object(dict)
    
    # Convert string path to Path object if provided
    log_path = Path(log_file) if log_file else None
    
    # Set up logging with custom file if specified
    actual_log_file = setup_logging(log_path)
    ctx.obj['log_file'] = actual_log_file
    
    # Override console logging level if verbose flag is set
    if verbose:
        console_handler = next((h for h in logging.root.handlers if isinstance(h, RichHandler)), None)
        if (console_handler):
            console_handler.setLevel(logging.INFO)
            logger.info("Verbose logging enabled")
    
    # If no command is provided, launch chat mode
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)

@cli.group()
def config():
    """Manage API keys and configuration"""
    pass

@config.command()
@click.argument('key_name')
@click.argument('key_value')
def set_key(key_name, key_value):
    """Set an API key (github_token, google_api_key, google_cx)"""
    try:
        config_data = Config.load()
        config_data[key_name] = key_value
        Config.save(config_data)
        console.print(f"[green]Successfully saved {key_name}[/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")

@config.command()
def show_keys():
    """Show all stored API keys"""
    try:
        config_data = Config.load()
        if not config_data:
            console.print("[yellow]No API keys configured.[/]")
            return
            
        console.print(Panel(title="Configured API Keys", renderable=""))
        for key, value in config_data.items():
            # Only show first 4 and last 4 characters of the key
            if len(value) > 8:
                masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:]
            else:
                masked_value = "****" 
            console.print(f"[cyan]{key}[/]: {masked_value}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")

@config.command()
@click.pass_context
def show_log_file(ctx):
    """Show the current log file location"""
    log_file = ctx.obj.get('log_file')
    if log_file:
        console.print(f"[green]Current log file:[/] {log_file}")
    else:
        console.print("[yellow]Log file location not available.[/]")

async def process_chat_input(prompt: str, state: ChatState) -> Tuple[str, Optional[Any]]:
    """Process chat input asynchronously"""
    try:
        # Get embeddings for conversation history
        embedding = services.get_embedding(prompt)
        
        # Safe search for similar messages - handle empty DB gracefully
        similar_messages = []
        try:
            similar_messages = db.search_similar(embedding)
        except Exception as e:
            logger.error(f"Error searching similar messages: {str(e)}")
        
        # Add conversation history to context
        context = "\n".join(f"{msg.role}: {msg.content}" for msg in similar_messages[-3:] if msg)
        
        # Process the query
        response, reasoning_result = await asyncio.to_thread(
            services.code_assist,
            prompt,
            state.reasoning_enabled,
            state.search_enabled,
            context
        )
        
        # Store conversation in vector DB - with error handling
        try:
            db.add_message("user", prompt, embedding)
            resp_embedding = services.get_embedding(response)
            db.add_message("assistant", response, resp_embedding)
        except Exception as e:
            # Log but don't raise - conversation storage is non-critical
            logger.error(f"Failed to store conversation: {str(e)}")
        
        return response, reasoning_result
    except Exception as e:
        # Log the full exception but return a simplified message to the user
        logger.exception("Error processing chat input")
        return f"I encountered a problem processing your request. Please try again.", None

def display_reasoning(reasoning_result: ReasoningResult):
    """Display reasoning results in a formatted way"""
    if not reasoning_result:
        return
        
    console.print("\n[bold yellow]Reasoning Analysis:[/]")
    
    # Display chain of thought steps
    console.print(Panel(
        "\n".join(
            f"[bold]{cot.model_name}[/]\n" + 
            "\n".join(f"  {i+1}. {step}" for i, step in enumerate(cot.steps))
            for cot in reasoning_result.chain_of_thought
        ),
        title="Chain of Thought Analysis",
        border_style="yellow"
    ))
    
    # Display confidence
    console.print(f"[yellow]Confidence:[/] {reasoning_result.confidence:.2f}")
    
    # Display alternatives if available
    if reasoning_result.alternatives:
        console.print(Panel(
            "\n".join(f"• {alt}" for alt in reasoning_result.alternatives[:3]),
            title="Alternative Approaches",
            border_style="yellow"
        ))

def handle_workspace_command(state: ChatState, path: str):
    """Handle /workspace command"""
    try:
        workspace = Path(path).resolve()
        if not workspace.exists():
            if Confirm.ask(f"Workspace {workspace} doesn't exist. Create it?"):
                workspace.mkdir(parents=True)
            else:
                return "Workspace change cancelled."
        
        state.current_workspace = workspace
        services.file_manager = FileManager(str(workspace))
        return f"[green]Workspace changed to:[/] {workspace}"
    except Exception as e:
        return f"[red]Error changing workspace:[/] {str(e)}"

def handle_test_command(state: ChatState, code: str) -> tuple[bool, str]:
    """Run tests on generated code"""
    try:
        # Create temporary test environment
        with TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test_code.py"
            with open(test_path, 'w') as f:
                f.write(code)
            
            # Run static analysis
            static_result = run_static_analysis(test_path)
            if not static_result[0]:
                return False, f"Static analysis failed:\n{static_result[1]}"
            
            # Run unit tests if present
            test_result = run_unit_tests(test_path)
            if not test_result[0]:
                return False, f"Tests failed:\n{test_result[1]}"
            
            return True, "All tests passed!"
    except Exception as e:
        return False, f"Error running tests: {str(e)}"

def display_code_block(code: str, language: str = "python"):
    """Display code block with copy button"""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    
    # Create copy button
    copy_button = "[bold cyan][[Copy]][/]"
    panel = Panel(
        Group(
            syntax,
            copy_button
        ),
        title="Generated Code",
        border_style="blue"
    )
    console.print(panel)
    
    # Handle copy functionality
    if Confirm.ask("Copy code to clipboard?"):
        try:
            pyperclip.copy(code)
            console.print("[green]Code copied to clipboard![/]")
        except Exception as e:
            console.print(f"[red]Error copying code:[/] {str(e)}")

def chat_interface():
    """Interactive chat interface with enhanced features"""
    if not services or not db:
        console.print("[bold red]Error:[/] Services not initialized. Please restart Aurelis.")
        return
        
    state = ChatState()
    console.print(WELCOME_ART)
    
    try:
        while True:
            # Show current workspace in prompt
            workspace_info = f"[{state.current_workspace or 'No workspace'}]" if state.current_workspace else ""
            prompt = console.input(f"[bold green]You{workspace_info}:[/] ")
            
            if prompt.lower() == 'exit':
                break
                
            # Handle enhanced commands
            if prompt.startswith('/'):
                cmd_parts = prompt[1:].split()
                cmd = cmd_parts[0].lower()
                
                if cmd == 'workspace':
                    if len(cmd_parts) > 1:
                        response = handle_workspace_command(state, cmd_parts[1])
                        console.print(response)
                    else:
                        console.print("[yellow]Current workspace:[/]", state.current_workspace or "None")
                    continue
                
                if cmd == 'toggle':
                    if len(cmd_parts) > 1:
                        feature = cmd_parts[1].lower()
                        if feature == 'reasoning':
                            state.reasoning_enabled = not state.reasoning_enabled
                            console.print(f"[yellow]Reasoning {'enabled' if state.reasoning_enabled else 'disabled'}[/]")
                        elif feature == 'search':
                            state.search_enabled = not state.search_enabled
                            console.print(f"[yellow]Search {'enabled' if state.search_enabled else 'disabled'}[/]")
                        elif feature == 'testing':
                            state.testing_enabled = not state.testing_enabled
                            console.print(f"[yellow]Auto-testing {'enabled' if state.testing_enabled else 'disabled'}[/]")
                    continue
                
                if cmd == 'help':
                    console.print(Panel(
                        "Commands:\n"
                        "/workspace <path> - Set working directory\n"
                        "/toggle reasoning - Toggle reasoning feature\n"
                        "/toggle search - Toggle web search\n"
                        "/toggle testing - Toggle auto-testing\n"
                        "/help - Show this help\n"
                        "exit - Exit chat\n\n"
                        "File Operations:\n"
                        "Use #filename to reference or create files\n"
                        "Files will be created in current workspace",
                        title="Aurelis Help",
                        border_style="green"
                    ))
                    continue
            
            # Process normal input with progress
            with console.status("[bold blue]Processing...[/]") as status:
                # Generate initial response
                response, reasoning_result = asyncio.run(process_chat_input(prompt, state))
                
                # Extract code blocks for testing
                code_blocks = extract_code_blocks(response)
                
                if code_blocks and state.testing_enabled:
                    status.update("[bold yellow]Testing generated code...[/]")
                    for code in code_blocks:
                        test_passed, test_result = handle_test_command(state, code)
                        if not test_passed:
                            # Regenerate with test feedback
                            status.update("[bold yellow]Fixing issues...[/]")
                            new_prompt = f"{prompt}\n\nPrevious attempt had issues:\n{test_result}\nPlease fix and ensure code passes all tests."
                            response, reasoning_result = asyncio.run(process_chat_input(new_prompt, state))
                
                # Display final response
                console.print("\n[bold purple]Aurelis:[/] ")
                console.print(Markdown(response))
                
                # Display code blocks with copy buttons
                for code in extract_code_blocks(response):
                    display_code_block(code)
                
                if reasoning_result:
                    display_reasoning(reasoning_result)
    
    except KeyboardInterrupt:
        logger.info("Chat terminated by user")
    except Exception as e:
        logger.exception("Unexpected error in chat interface")
        console.print(f"[bold red]Error:[/] {str(e)}")

def display_welcome_panel():
    """Display welcome panel with version info and status"""
    try:
        # Get version info
        import pkg_resources
        version = pkg_resources.get_distribution("aurelis").version
    except:
        version = "DEV"
    
    console.print(WELCOME_ART)
    console.print(Panel(
        f"[cyan]Version:[/] {version}\n"
        f"[yellow]Status:[/] Active\n"
        f"[green]Models:[/] GPT-4o, DeepSeek-R1, O3-mini\n"
        f"[magenta]Embeddings:[/] Cohere Multilingual v3",
        title="Aurelis Enterprise AI Assistant",
        border_style="blue"
    ))

@cli.command()
@click.option('--workspace', '-w', help='Set workspace directory', type=click.Path(exists=True))
@click.pass_context
def chat(ctx, workspace):
    """Start an AI-powered coding assistant with enhanced reasoning and search capabilities"""
    if not setup_services():
        return
        
    try:
        if workspace:
            services.file_manager = FileManager(workspace)
            console.print(f"[green]Working directory set to:[/] {workspace}")
            logger.info(f"Working directory set to: {workspace}")
        
        # Display welcome message and start chat
        chat_interface()
    finally:
        if services:
            services.cleanup()

@cli.command()
@click.argument('query')
def search(query):
    """Search and analyze coding problems using multiple search engines"""
    if not setup_services():
        return
        
    try:
        with console.status("[bold blue]Searching...[/]"):
            response = services.search_and_assist(query)
        
        console.print(Markdown(response))
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('query')
@click.option('--reasoning/--no-reasoning', default=False, help='Enable reasoning analysis')
def analyze(file_path, query, reasoning):
    """Analyze a file with AI assistance"""
    if not setup_services():
        return
        
    try:
        with console.status(f"[bold blue]Analyzing {file_path}...[/]"):
            response, reasoning_result = services.analyze_file(file_path, query, reasoning)
        
        console.print("\n[bold purple]Analysis:[/] ")
        console.print(Markdown(response))
        
        if reasoning_result:
            display_reasoning(reasoning_result)
    
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def edit(file_path):
    """Edit a file with AI assistance"""
    if not setup_services():
        return
        
    try:
        console.print(Panel(f"Editing file: {file_path}", border_style="blue"))
        instructions = console.input("[bold green]Enter edit instructions:[/] ")
        
        with console.status("[bold blue]Applying edits...[/]"):
            modified_content = services.edit_file(file_path, instructions)
        
        # Show preview
        console.print("\n[bold yellow]Preview of changes:[/]")
        console.print(Panel(modified_content, border_style="dim"))
        
        if click.confirm("Do you want to apply these changes?"):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            console.print("[bold green]Changes applied successfully![/]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")

def main():
    """Main entry point for the CLI application"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Process and standardize CLI arguments
        handle_cli_arguments()
        
        # Check for custom log path in environment variable
        env_log_path = os.environ.get("AURELIS_LOG_FILE")
        if env_log_path and not any(arg in sys.argv for arg in ["--log-file", "-l"]):
            sys.argv[1:1] = ["--log-file", env_log_path]
        
        # Handle --aurelis flag
        if "--aurelis" in sys.argv:
            sys.argv.remove("--aurelis")
        
        # Run CLI
        cli(obj={})
        
    except KeyboardInterrupt:
        logger.info("Aurelis terminated by user")
        console.print("\n[yellow]Aurelis terminated.[/]")
    except Exception as e:
        # Log the full exception but show a cleaner message to the user
        if logger:
            logger.exception("Unexpected error in main")
        console.print("\n[bold red]An unexpected error occurred.[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
