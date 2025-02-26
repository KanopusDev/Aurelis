"""Utility modules for Aurelis"""
from .code_utils import extract_code_blocks, format_code_block
from .testing import run_static_analysis, run_unit_tests

__all__ = [
    'extract_code_blocks',
    'format_code_block',
    'run_static_analysis',
    'run_unit_tests'
]
