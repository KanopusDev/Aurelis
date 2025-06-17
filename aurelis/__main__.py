"""Main Aurelis initialization and progress tracking."""

import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

from aurelis.core.config import initialize_config, get_config
from aurelis.core.logging import initialize_logging, get_logger
from aurelis.core.security import initialize_security
from aurelis.core.cache import initialize_cache
from aurelis.core.session import initialize_session_manager
from aurelis.analysis import initialize_analyzer
from aurelis.models import initialize_model_orchestrator
from aurelis.core.context import initialize_context_manager
from aurelis.tools import initialize_tool_manager
from aurelis.core.exceptions import AurelisError

console = Console()


class AurelisSystem:
    """Main system coordinator for Aurelis."""
    
    def __init__(self):
        self.logger = None
        self.initialized = False
        self.initialization_time = 0.0
        self.components = {}
    
    def initialize(self, config_path: Optional[Path] = None) -> bool:
        """Initialize all Aurelis components with progress tracking."""
        start_time = time.time()
        
        console.print("[bold blue]🚀 Initializing Aurelis Enterprise AI Code Assistant[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            # Define initialization steps
            steps = [
                ("Configuration", lambda: initialize_config(config_path)),
                ("Logging System", lambda: initialize_logging()),
                ("Security Manager", lambda: initialize_security()),
                ("Cache System", lambda: initialize_cache()),
                ("Session Manager", lambda: initialize_session_manager()),
                ("Code Analyzer", lambda: initialize_analyzer()),
                ("Model Orchestrator", lambda: initialize_model_orchestrator()),
                ("Context Manager", lambda: initialize_context_manager()),
                ("Tool Manager", lambda: initialize_tool_manager())
            ]
            
            main_task = progress.add_task("Initializing Aurelis...", total=len(steps))
            
            try:
                for step_name, init_func in steps:
                    step_task = progress.add_task(f"Loading {step_name}...", total=None)
                    
                    try:
                        component = init_func()
                        self.components[step_name.lower().replace(" ", "_")] = component
                        progress.update(step_task, description=f"✅ {step_name} loaded")
                        
                    except Exception as e:
                        progress.update(step_task, description=f"❌ {step_name} failed")
                        console.print(f"[red]Failed to initialize {step_name}: {e}[/red]")
                        return False
                    
                    progress.advance(main_task)
                    time.sleep(0.1)  # Small delay for visual effect
                
                # Final setup
                self.logger = get_logger("system")
                self.initialized = True
                self.initialization_time = time.time() - start_time
                
                progress.update(main_task, description="✅ Aurelis initialized successfully")
                
            except Exception as e:
                console.print(f"[red]System initialization failed: {e}[/red]")
                return False
        
        # Display initialization summary
        self._display_initialization_summary()
        
        return True
    
    def _display_initialization_summary(self) -> None:
        """Display initialization summary."""
        config = get_config()
        
        # System info table
        table = Table(title="🎯 Aurelis System Status", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=15)
        table.add_column("Details", width=40)
        
        # Add component status
        for component_name, component in self.components.items():
            status = "✅ Active" if component else "❌ Failed"
            details = type(component).__name__ if component else "Not available"
            table.add_row(component_name.replace("_", " ").title(), status, details)
        
        console.print(table)
        
        # Configuration summary
        config_panel = Panel(
            f"""[bold]Configuration Summary[/bold]
            
🤖 Primary Model: {config.primary_model.value}
🔄 Fallback Model: {config.fallback_model.value}
📦 Chunk Size: {config.chunk_size} tokens
🔒 Security: {'Enabled' if config.sandbox_enabled else 'Disabled'}
💾 Caching: {'Enabled' if config.cache_enabled else 'Disabled'}
⏱️  Initialization Time: {self.initialization_time:.2f}s""",
            title="System Configuration",
            border_style="green"
        )
        console.print(config_panel)
        
        # Quick start info
        console.print("\n[bold yellow]🚀 Quick Start Commands:[/bold yellow]")
        console.print("  • [cyan]aurelis analyze <path>[/cyan] - Analyze Python code")
        console.print("  • [cyan]aurelis generate \"<prompt>\"[/cyan] - Generate code")
        console.print("  • [cyan]aurelis explain <file>[/cyan] - Explain code functionality")
        console.print("  • [cyan]aurelis config --show[/cyan] - Show configuration")
        console.print("  • [cyan]aurelis shell[/cyan] - Interactive mode")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        config = get_config()
        
        # Collect component stats
        component_stats = {}
        
        # Cache stats
        if "cache_system" in self.components:
            from aurelis.core.cache import get_cache_manager
            cache_manager = get_cache_manager()
            component_stats["cache"] = cache_manager.get_cache_stats()
        
        # Model stats
        if "model_orchestrator" in self.components:
            from aurelis.models import get_model_orchestrator
            orchestrator = get_model_orchestrator()
            component_stats["models"] = orchestrator.get_model_stats()
        
        # Tool stats
        if "tool_manager" in self.components:
            from aurelis.tools import get_tool_manager
            tool_manager = get_tool_manager()
            component_stats["tools"] = tool_manager.get_tool_stats()
        
        # Session stats
        if "session_manager" in self.components:
            from aurelis.core.session import get_session_manager
            session_manager = get_session_manager()
            component_stats["sessions"] = session_manager.get_session_stats()
        
        # Context stats
        if "context_manager" in self.components:
            from aurelis.core.context import get_context_manager
            context_manager = get_context_manager()
            component_stats["context"] = context_manager.get_chunker_stats()
        
        return {
            "status": "initialized",
            "initialization_time": self.initialization_time,
            "config": {
                "primary_model": config.primary_model.value,
                "fallback_model": config.fallback_model.value,
                "chunk_size": config.chunk_size,
                "cache_enabled": config.cache_enabled,
                "sandbox_enabled": config.sandbox_enabled
            },
            "components": component_stats,
            "version": "1.0.0"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health_status = {
            "overall": "healthy",
            "components": {},
            "timestamp": time.time()
        }
        
        if not self.initialized:
            health_status["overall"] = "unhealthy"
            health_status["error"] = "System not initialized"
            return health_status
        
        # Check each component
        try:
            # Check configuration
            config = get_config()
            health_status["components"]["config"] = "healthy"
            
            # Check logging
            logger = get_logger("health_check")
            logger.debug("Health check logging test")
            health_status["components"]["logging"] = "healthy"
            
            # Check cache
            from aurelis.core.cache import get_cache_manager
            cache_manager = get_cache_manager()
            cache_stats = cache_manager.get_cache_stats()
            health_status["components"]["cache"] = "healthy"
            
            # Check models
            from aurelis.models import get_model_orchestrator
            orchestrator = get_model_orchestrator()
            available_models = orchestrator.get_available_models()
            health_status["components"]["models"] = "healthy" if available_models else "degraded"
            
            # Check tools
            from aurelis.tools import get_tool_manager
            tool_manager = get_tool_manager()
            tools = tool_manager.list_tools()
            health_status["components"]["tools"] = "healthy" if tools else "degraded"
            
        except Exception as e:
            health_status["overall"] = "unhealthy"
            health_status["error"] = str(e)
            self.logger.error(f"Health check failed: {e}")
        
        return health_status
    
    def shutdown(self) -> None:
        """Gracefully shutdown the system."""
        if not self.initialized:
            return
        
        console.print("[yellow]🔄 Shutting down Aurelis...[/yellow]")
        
        try:
            # Cleanup sessions
            if "session_manager" in self.components:
                from aurelis.core.session import get_session_manager
                session_manager = get_session_manager()
                session_manager.cleanup_expired_sessions()
            
            # Cleanup cache
            if "cache_system" in self.components:
                from aurelis.core.cache import get_cache_manager
                cache_manager = get_cache_manager()
                # Cache cleanup is handled automatically
            
            if self.logger:
                self.logger.info("Aurelis system shutdown completed")
            
            console.print("[green]✅ Aurelis shutdown completed[/green]")
            
        except Exception as e:
            console.print(f"[red]Error during shutdown: {e}[/red]")
        
        finally:
            self.initialized = False


# Global system instance
_aurelis_system: Optional[AurelisSystem] = None


def get_aurelis_system() -> AurelisSystem:
    """Get the global Aurelis system instance."""
    global _aurelis_system
    if _aurelis_system is None:
        _aurelis_system = AurelisSystem()
    return _aurelis_system


def initialize_aurelis(config_path: Optional[Path] = None) -> bool:
    """Initialize the complete Aurelis system."""
    system = get_aurelis_system()
    return system.initialize(config_path)


def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    system = get_aurelis_system()
    return system.get_system_info()


def health_check() -> Dict[str, Any]:
    """Perform system health check."""
    system = get_aurelis_system()
    return system.health_check()


def shutdown_aurelis() -> None:
    """Shutdown Aurelis system."""
    system = get_aurelis_system()
    system.shutdown()


class ProgressTracker:
    """Track progress of long-running operations."""
    
    def __init__(self, operation_name: str, total_steps: Optional[int] = None):
        self.operation_name = operation_name
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        self.completed = False
        
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        )
        
        self.task_id = None
    
    def __enter__(self):
        self.progress.start()
        self.task_id = self.progress.add_task(
            self.operation_name,
            total=self.total_steps
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.completed:
            self.complete()
        self.progress.stop()
    
    def update(self, description: str, advance: int = 1) -> None:
        """Update progress with new description."""
        if self.task_id is not None:
            self.progress.update(self.task_id, description=description, advance=advance)
        self.current_step += advance
    
    def complete(self, final_message: Optional[str] = None) -> None:
        """Mark operation as complete."""
        elapsed_time = time.time() - self.start_time
        
        if final_message:
            message = final_message
        else:
            message = f"✅ {self.operation_name} completed in {elapsed_time:.2f}s"
        
        if self.task_id is not None:
            self.progress.update(self.task_id, description=message, completed=True)
        
        self.completed = True
    
    def error(self, error_message: str) -> None:
        """Mark operation as failed."""
        if self.task_id is not None:
            self.progress.update(
                self.task_id,
                description=f"❌ {self.operation_name} failed: {error_message}"
            )
        self.completed = True


def create_progress_tracker(operation_name: str, total_steps: Optional[int] = None) -> ProgressTracker:
    """Create a progress tracker for long-running operations."""
    return ProgressTracker(operation_name, total_steps)


def main():
    """
    Main entry point for Aurelis when run as a module.
    
    This function initializes the CLI and starts the application.
    """
    try:
        from aurelis.cli.main import app
        app()
    except ImportError as e:
        console = Console()
        console.print(f"[red]Failed to import CLI components: {e}[/red]")
        console.print("[yellow]Please ensure all dependencies are installed[/yellow]")
        return 1
    except Exception as e:
        console = Console()
        console.print(f"[red]Unexpected error: {e}[/red]")
        return 1


if __name__ == "__main__":
    exit(main())
