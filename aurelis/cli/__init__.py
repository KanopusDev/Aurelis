"""
CLI package for Aurelis enterprise code assistant.

This package contains the command-line interface modules for the Aurelis
AI-powered coding assistant.
"""
import sys
from typing import List

__version__ = "1.0.1"

def handle_cli_arguments() -> List[str]:
    """
    Preprocess and standardize command line arguments.
    
    Returns:
        List[str]: Normalized argument list
    """
    if len(sys.argv) <= 1:
        return sys.argv
    
    normalized = []
    i = 0
    
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        # Keep program name
        if i == 0:
            normalized.append(arg)
            i += 1
            continue
            
        # Handle log file options
        if arg in ["--l", "-l"]:
            normalized.append("--log-file")
            if i + 1 < len(sys.argv) and not sys.argv[i+1].startswith("-"):
                normalized.append(sys.argv[i+1])
                i += 2
                continue
        elif arg.startswith("--l="):
            normalized.append(f"--log-file={arg[4:]}")
        # Pass through other arguments unchanged
        else:
            normalized.append(arg)
        i += 1
    
    sys.argv = normalized
    return normalized
