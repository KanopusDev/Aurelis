"""
ASCII art and fancy display utilities for Aurelis CLI.

This module contains ASCII art, banners, and related display functions
used by the Aurelis CLI interface.
"""

import sys
from rich.console import Console

# Initialize rich console
console = Console()

# ASCII art for Aurelis banner
AURELIS_BANNER = """
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

# ASCII art for errors
ERROR_BANNER = """
[bold red]  _____                    [/]
[bold red] | ____|_ __ _ __ ___  _ __[/]
[bold red] |  _| | '__| '__/ _ \\| '__|[/]
[bold red] | |___| |  | | | (_) | |   [/]
[bold red] |_____|_|  |_|  \\___/|_|   [/]
"""

def display_banner():
    """Display the Aurelis ASCII art banner."""
    console.print(AURELIS_BANNER)

def display_terminal_version():
    """Display ASCII art adapted to terminal colors if in standard terminal."""
    # ANSI color codes for standard terminals
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # ASCII art for welcome banner
    banner = f"""
    {BLUE}{BOLD}    _    _    _ ____  _____ _     ___ ____  {RESET}
    {CYAN}{BOLD}   / \\  | |  | |  _ \\| ____| |   |_ _/ ___| {RESET}
    {GREEN}{BOLD}  / _ \\ | |  | | |_) |  _| | |    | |\\___ \\ {RESET}
    {YELLOW}{BOLD} / ___ \\| |__| |  _ <| |___| |___ | | ___) |{RESET}
    {RED}{BOLD}/_/   \\_\\_____/|_| \\_\\_____|_____|___|____/ {RESET}
    {PURPLE}{BOLD}================================================{RESET}
    {CYAN}Enterprise-Grade Python Code Assistant{RESET}
    {GREEN}Type your code request below to begin...{RESET}
    {PURPLE}{BOLD}================================================{RESET}
    """
    
    print(banner)

def display_welcome(use_rich=True):
    """
    Display welcome ASCII art in the appropriate format.
    
    Args:
        use_rich: Whether to use Rich formatting or terminal ANSI codes
    """
    if use_rich:
        display_banner()
    else:
        display_terminal_version()

if __name__ == "__main__":
    display_welcome()
