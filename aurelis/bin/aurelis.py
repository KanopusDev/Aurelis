#!/usr/bin/env python3
"""
Entry point script for Aurelis CLI with enhanced argument handling.
This provides better handling of command-line arguments than relying 
solely on Click's parser.
"""
import sys
import os
import re
from pathlib import Path

def normalize_args():
    """
    Normalize command line arguments to be compatible with Click.
    
    Handles:
    - --l => --log-file
    - --l=value => --log-file=value
    - --v => --verbose
    """
    normalized_args = []
    i = 0
    
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        # Skip the script name
        if i == 0:
            normalized_args.append(arg)
            i += 1
            continue
            
        # Handle shorthand options with equals
        if re.match(r'--l=.+', arg):
            normalized_args.append(f"--log-file={arg[4:]}")
        # Handle shorthand options
        elif arg == '--l':
            normalized_args.append('--log-file')
            if i + 1 < len(sys.argv) and not sys.argv[i+1].startswith('-'):
                normalized_args.append(sys.argv[i+1])
                i += 1  # Skip the next arg as we've already handled it
        # Handle shorthand verbose
        elif arg == '--v':
            normalized_args.append('--verbose')
        # Pass through other arguments unchanged
        else:
            normalized_args.append(arg)
        
        i += 1
    
    return normalized_args

def main():
    """
    Main entry point with argument normalization.
    """
    # Normalize the arguments before passing to Click
    sys.argv = normalize_args()
    
    # Import the CLI main function after normalizing args
    from aurelis.cli.main import main as cli_main
    cli_main()

if __name__ == "__main__":
    main()
