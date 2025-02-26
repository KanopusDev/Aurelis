import os
import ast
import pytest
import pylint.lint
from pathlib import Path
from typing import Tuple, List
from tempfile import TemporaryDirectory

def run_static_analysis(file_path: Path) -> Tuple[bool, str]:
    """Run static code analysis using pylint"""
    try:
        # Parse code to check for syntax errors
        with open(file_path, 'r') as f:
            ast.parse(f.read())
        
        # Run pylint
        pylint_opts = ['--disable=C,R', '--enable=E,F,W', str(file_path)]
        reporter = pylint.lint.PyLinter()
        reporter.initialize()
        reporter.check([str(file_path)])
        
        if reporter.msg_status:
            return False, "Static analysis found issues:\n" + "\n".join(reporter.reporter.messages)
        return True, "Static analysis passed"
        
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"
    except Exception as e:
        return False, f"Static analysis error: {str(e)}"

def extract_test_cases(code: str) -> List[str]:
    """Extract test cases from code comments or docstrings"""
    tree = ast.parse(code)
    test_cases = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            if docstring and 'Example:' in docstring:
                test_cases.append(docstring)
    
    return test_cases

def generate_test_file(code: str, test_cases: List[str]) -> str:
    """Generate pytest file from code and test cases"""
    test_code = [
        "import pytest",
        code,
        "\ndef test_functionality():"
    ]
    
    for test in test_cases:
        test_code.extend([f"    {line}" for line in test.split('\n')])
    
    return "\n".join(test_code)

def run_unit_tests(file_path: Path) -> Tuple[bool, str]:
    """Run unit tests using pytest"""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        test_cases = extract_test_cases(code)
        if not test_cases:
            return True, "No test cases found"
        
        test_file = generate_test_file(code, test_cases)
        with TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test_generated.py"
            with open(test_path, 'w') as f:
                f.write(test_file)
            
            # Run pytest
            result = pytest.main(["-v", str(test_path)])
            return result == 0, "All tests passed" if result == 0 else "Some tests failed"
            
    except Exception as e:
        return False, f"Test execution error: {str(e)}"
