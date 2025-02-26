import re
from typing import List, Tuple, Optional

def extract_code_blocks(text: str) -> List[str]:
    """
    Extract code blocks from markdown-style text.
    
    Args:
        text: Text containing markdown code blocks
        
    Returns:
        List of code block contents
    """
    # Match both ``` and ```python style code blocks
    pattern = r'```(?:python)?\s*(?:#.*?)?\n(.*?)```'
    matches = re.finditer(pattern, text, re.DOTALL)
    return [match.group(1).strip() for match in matches]

def extract_file_references(text: str) -> List[Tuple[str, str]]:
    """
    Extract file references and associated code blocks.
    
    Args:
        text: Text containing file references and code blocks
        
    Returns:
        List of tuples (file_path, code_content)
    """
    # Match code blocks with file references like # filepath: or #filename:
    pattern = r'```(?:python)?\s*#\s*(?:filepath:|filename:)?\s*([\w\-./\\]+)\s*\n(.*?)```'
    matches = re.finditer(pattern, text, re.DOTALL)
    return [(match.group(1).strip(), match.group(2).strip()) for match in matches]

def extract_code_from_file(file_path: str) -> Optional[str]:
    """
    Extract code content from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File contents or None if file doesn't exist
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def format_code_block(code: str, language: str = "python") -> str:
    """
    Format code into a markdown code block.
    
    Args:
        code: Code content
        language: Programming language for syntax highlighting
        
    Returns:
        Formatted code block
    """
    return f"```{language}\n{code}\n```"
