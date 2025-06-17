"""
Documentation generation system for Aurelis.
Automatically generates API documentation, user guides, and technical documentation.
"""
import ast
import asyncio
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from aurelis.core.types import DocumentationRequest, DocumentationResult
from aurelis.core.exceptions import DocumentationError
from aurelis.core.logging import get_logger

logger = get_logger(__name__)


class DocumentationType(Enum):
    """Types of documentation that can be generated."""
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    TECHNICAL_SPEC = "technical_spec"
    TUTORIAL = "tutorial"
    CHANGELOG = "changelog"
    README = "readme"


@dataclass
class DocumentationSection:
    """Represents a section in documentation."""
    title: str
    content: str
    level: int
    metadata: Dict[str, Any]
    subsections: List['DocumentationSection']


@dataclass
class APIDocumentation:
    """Documentation for API elements."""
    name: str
    type: str  # function, class, method, property
    signature: str
    docstring: str
    parameters: List[Dict[str, Any]]
    returns: Optional[Dict[str, Any]]
    raises: List[Dict[str, Any]]
    examples: List[str]
    source_file: str
    line_number: int


class DocstringParser:
    """Parses and extracts information from docstrings."""
    
    def __init__(self):
        self.sections = {
            'Args:', 'Arguments:', 'Parameters:',
            'Returns:', 'Return:', 'Yields:', 'Yield:',
            'Raises:', 'Except:', 'Exceptions:',
            'Example:', 'Examples:', 'Usage:',
            'Note:', 'Notes:', 'Warning:', 'Todo:'
        }
    
    def parse(self, docstring: str) -> Dict[str, Any]:
        """Parse a docstring into structured components."""
        if not docstring:
            return {"description": "", "parameters": [], "returns": None, "raises": [], "examples": []}
        
        lines = docstring.strip().split('\n')
        result = {
            "description": "",
            "parameters": [],
            "returns": None,
            "raises": [],
            "examples": []
        }
        
        current_section = "description"
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            section_found = None
            for section in self.sections:
                if line.startswith(section):
                    section_found = section.lower().rstrip(':')
                    break
            
            if section_found:
                # Save previous section
                if current_section == "description":
                    result["description"] = '\n'.join(current_content).strip()
                elif current_section in ["args", "arguments", "parameters"]:
                    result["parameters"].extend(self._parse_parameters(current_content))
                elif current_section in ["returns", "return", "yields", "yield"]:
                    result["returns"] = {'description': '\n'.join(current_content).strip()}
                elif current_section in ["raises", "except", "exceptions"]:
                    result["raises"].extend(self._parse_exceptions(current_content))
                elif current_section in ["example", "examples", "usage"]:
                    result["examples"].extend(self._parse_examples(current_content))
                
                # Start new section
                current_section = section_found
                current_content = []
            else:
                current_content.append(line)
        
        # Handle last section
        if current_section == "description":
            result["description"] = '\n'.join(current_content).strip()
        elif current_section in ["args", "arguments", "parameters"]:
            result["parameters"].extend(self._parse_parameters(current_content))
        elif current_section in ["returns", "return", "yields", "yield"]:
            result["returns"] = {'description': '\n'.join(current_content).strip()}
        elif current_section in ["raises", "except", "exceptions"]:
            result["raises"].extend(self._parse_exceptions(current_content))
        elif current_section in ["example", "examples", "usage"]:
            result["examples"].extend(self._parse_examples(current_content))
        
        return result
    
    def _parse_parameters(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse parameter documentation."""
        parameters = []
        current_param = None
        
        for line in lines:
            if ':' in line and not line.startswith(' '):
                # New parameter
                if current_param:
                    parameters.append(current_param)
                
                parts = line.split(':', 1)
                param_name = parts[0].strip()
                param_desc = parts[1].strip() if len(parts) > 1 else ""
                
                current_param = {
                    'name': param_name,
                    'type': None,
                    'description': param_desc,
                    'optional': False,
                    'default': None
                }
            elif current_param and line.startswith(' '):
                # Continuation of parameter description
                current_param['description'] += ' ' + line.strip()
        
        if current_param:
            parameters.append(current_param)
        
        return parameters
    
    def _parse_exceptions(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse exception documentation."""
        exceptions = []
        current_exception = None
        
        for line in lines:
            if ':' in line and not line.startswith(' '):
                # New exception
                if current_exception:
                    exceptions.append(current_exception)
                
                parts = line.split(':', 1)
                exc_name = parts[0].strip()
                exc_desc = parts[1].strip() if len(parts) > 1 else ""
                
                current_exception = {
                    'type': exc_name,
                    'description': exc_desc
                }
            elif current_exception and line.startswith(' '):
                # Continuation of exception description
                current_exception['description'] += ' ' + line.strip()
        
        if current_exception:
            exceptions.append(current_exception)
        
        return exceptions
    
    def _parse_examples(self, lines: List[str]) -> List[str]:
        """Parse example code blocks."""
        examples = []
        current_example = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```') or line.strip().startswith('>>>'):
                if in_code_block:
                    # End of code block
                    if current_example:
                        examples.append('\n'.join(current_example))
                        current_example = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
            elif in_code_block:
                current_example.append(line)
            elif line.strip():
                # Regular example line
                current_example.append(line)
        
        if current_example:
            examples.append('\n'.join(current_example))
        
        return examples


class CodeAnalyzer:
    """Analyzes Python code to extract documentation information."""
    
    def __init__(self):
        self.docstring_parser = DocstringParser()
    
    def analyze_file(self, file_path: Path) -> List[APIDocumentation]:
        """Analyze a Python file and extract API documentation."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            api_docs = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    api_docs.append(self._analyze_function(node, file_path))
                elif isinstance(node, ast.ClassDef):
                    api_docs.append(self._analyze_class(node, file_path))
                    # Analyze class methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_doc = self._analyze_method(item, node.name, file_path)
                            api_docs.append(method_doc)
            
            return api_docs
        
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []
    
    def _analyze_function(self, node: ast.FunctionDef, file_path: Path) -> APIDocumentation:
        """Analyze a function definition."""
        docstring = ast.get_docstring(node) or ""
        parsed_doc = self.docstring_parser.parse(docstring)
        
        # Extract function signature
        signature = self._get_function_signature(node)
        
        return APIDocumentation(
            name=node.name,
            type="function",
            signature=signature,
            docstring=parsed_doc["description"],
            parameters=parsed_doc["parameters"],
            returns=parsed_doc["returns"],
            raises=parsed_doc["raises"],
            examples=parsed_doc["examples"],
            source_file=str(file_path),
            line_number=node.lineno
        )
    
    def _analyze_class(self, node: ast.ClassDef, file_path: Path) -> APIDocumentation:
        """Analyze a class definition."""
        docstring = ast.get_docstring(node) or ""
        parsed_doc = self.docstring_parser.parse(docstring)
        
        # Extract class signature
        signature = f"class {node.name}"
        if node.bases:
            base_names = [self._get_node_name(base) for base in node.bases]
            signature += f"({', '.join(base_names)})"
        
        return APIDocumentation(
            name=node.name,
            type="class",
            signature=signature,
            docstring=parsed_doc["description"],
            parameters=parsed_doc["parameters"],
            returns=None,
            raises=parsed_doc["raises"],
            examples=parsed_doc["examples"],
            source_file=str(file_path),
            line_number=node.lineno
        )
    
    def _analyze_method(self, node: ast.FunctionDef, class_name: str, file_path: Path) -> APIDocumentation:
        """Analyze a method definition."""
        docstring = ast.get_docstring(node) or ""
        parsed_doc = self.docstring_parser.parse(docstring)
        
        # Extract method signature
        signature = self._get_function_signature(node)
        
        return APIDocumentation(
            name=f"{class_name}.{node.name}",
            type="method",
            signature=signature,
            docstring=parsed_doc["description"],
            parameters=parsed_doc["parameters"],
            returns=parsed_doc["returns"],
            raises=parsed_doc["raises"],
            examples=parsed_doc["examples"],
            source_file=str(file_path),
            line_number=node.lineno
        )
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature from AST node."""
        args = []
        
        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_node_name(arg.annotation)}"
            args.append(arg_str)
        
        # Default arguments
        defaults = node.args.defaults
        if defaults:
            num_defaults = len(defaults)
            for i, default in enumerate(defaults):
                arg_index = len(args) - num_defaults + i
                if arg_index >= 0:
                    args[arg_index] += f" = {self._get_node_name(default)}"
        
        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_node_name(arg.annotation)}"
            args.append(arg_str)
        
        # Return annotation
        return_annotation = ""
        if node.returns:
            return_annotation = f" -> {self._get_node_name(node.returns)}"
        
        return f"def {node.name}({', '.join(args)}){return_annotation}"
    
    def _get_node_name(self, node) -> str:
        """Get string representation of an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        else:
            return "Unknown"


class DocumentationGenerator:
    """Main documentation generation orchestrator."""
    
    def __init__(self, config):
        self.config = config
        self.code_analyzer = CodeAnalyzer()
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load documentation templates."""
        return {
            "api_reference": """# API Reference

## {module_name}

{description}

### Functions

{functions}

### Classes

{classes}
""",
            "function_template": """#### {name}

```python
{signature}
```

{description}

{parameters}

{returns}

{raises}

{examples}
""",
            "class_template": """#### {name}

```python
{signature}
```

{description}

{methods}
"""
        }
    
    async def generate_documentation(self, request: DocumentationRequest) -> DocumentationResult:
        """Generate documentation based on request."""
        try:
            logger.info(f"Generating {request.doc_type} documentation for {request.target_path}")
            
            if request.doc_type == DocumentationType.API_REFERENCE:
                return await self._generate_api_reference(request)
            elif request.doc_type == DocumentationType.USER_GUIDE:
                return await self._generate_user_guide(request)
            elif request.doc_type == DocumentationType.README:
                return await self._generate_readme(request)
            else:
                raise DocumentationError(f"Unsupported documentation type: {request.doc_type}")
        
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            raise DocumentationError(f"Documentation generation failed: {e}")
    
    async def _generate_api_reference(self, request: DocumentationRequest) -> DocumentationResult:
        """Generate API reference documentation."""
        target_path = Path(request.target_path)
        
        if target_path.is_file():
            files_to_analyze = [target_path]
        else:
            files_to_analyze = list(target_path.rglob("*.py"))
        
        all_api_docs = []
        for file_path in files_to_analyze:
            api_docs = self.code_analyzer.analyze_file(file_path)
            all_api_docs.extend(api_docs)
        
        # Group by module
        modules = {}
        for api_doc in all_api_docs:
            module_name = Path(api_doc.source_file).stem
            if module_name not in modules:
                modules[module_name] = {"functions": [], "classes": []}
            
            if api_doc.type == "function":
                modules[module_name]["functions"].append(api_doc)
            elif api_doc.type == "class":
                modules[module_name]["classes"].append(api_doc)
        
        # Generate documentation content
        content_sections = []
        for module_name, items in modules.items():
            functions_content = self._format_functions(items["functions"])
            classes_content = self._format_classes(items["classes"])
            
            module_content = self.templates["api_reference"].format(
                module_name=module_name,
                description=f"Documentation for {module_name} module.",
                functions=functions_content,
                classes=classes_content
            )
            
            content_sections.append(DocumentationSection(
                title=module_name,
                content=module_content,
                level=1,
                metadata={"module": module_name},
                subsections=[]
            ))
        
        return DocumentationResult(
            title="API Reference",
            sections=content_sections,
            metadata={
                "generated_from": str(target_path),
                "total_modules": len(modules),
                "total_functions": sum(len(m["functions"]) for m in modules.values()),
                "total_classes": sum(len(m["classes"]) for m in modules.values())
            }
        )
    
    def _format_functions(self, functions: List[APIDocumentation]) -> str:
        """Format function documentation."""
        if not functions:
            return "No functions documented."
        
        function_docs = []
        for func in functions:
            parameters_content = self._format_parameters(func.parameters)
            returns_content = self._format_returns(func.returns)
            raises_content = self._format_raises(func.raises)
            examples_content = self._format_examples(func.examples)
            
            func_doc = self.templates["function_template"].format(
                name=func.name,
                signature=func.signature,
                description=func.docstring or "No description available.",
                parameters=parameters_content,
                returns=returns_content,
                raises=raises_content,
                examples=examples_content
            )
            function_docs.append(func_doc)
        
        return "\n\n".join(function_docs)
    
    def _format_classes(self, classes: List[APIDocumentation]) -> str:
        """Format class documentation."""
        if not classes:
            return "No classes documented."
        
        class_docs = []
        for cls in classes:
            # Find methods for this class
            methods = [doc for doc in classes if doc.name.startswith(f"{cls.name}.")]
            methods_content = self._format_methods(methods)
            
            class_doc = self.templates["class_template"].format(
                name=cls.name,
                signature=cls.signature,
                description=cls.docstring or "No description available.",
                methods=methods_content
            )
            class_docs.append(class_doc)
        
        return "\n\n".join(class_docs)
    
    def _format_parameters(self, parameters: List[Dict[str, Any]]) -> str:
        """Format parameter documentation."""
        if not parameters:
            return ""
        
        param_lines = ["**Parameters:**"]
        for param in parameters:
            param_line = f"- `{param['name']}`"
            if param.get('type'):
                param_line += f" ({param['type']})"
            if param.get('description'):
                param_line += f": {param['description']}"
            if param.get('optional'):
                param_line += " (optional)"
            if param.get('default'):
                param_line += f" (default: {param['default']})"
            param_lines.append(param_line)
        
        return "\n".join(param_lines)
    
    def _format_returns(self, returns: Optional[Dict[str, Any]]) -> str:
        """Format return value documentation."""
        if not returns:
            return ""
        
        return f"**Returns:** {returns.get('description', 'Return value not documented.')}"
    
    def _format_raises(self, raises: List[Dict[str, Any]]) -> str:
        """Format exception documentation."""
        if not raises:
            return ""
        
        raise_lines = ["**Raises:**"]
        for exc in raises:
            exc_line = f"- `{exc['type']}`"
            if exc.get('description'):
                exc_line += f": {exc['description']}"
            raise_lines.append(exc_line)
        
        return "\n".join(raise_lines)
    
    def _format_examples(self, examples: List[str]) -> str:
        """Format example documentation."""
        if not examples:
            return ""
        
        example_lines = ["**Examples:**"]
        for i, example in enumerate(examples):
            example_lines.append(f"\n```python\n{example}\n```")
        
        return "\n".join(example_lines)
    
    def _format_methods(self, methods: List[APIDocumentation]) -> str:
        """Format method documentation."""
        if not methods:
            return "No methods documented."
        
        method_docs = []
        for method in methods:
            method_name = method.name.split('.')[-1]  # Get just the method name
            parameters_content = self._format_parameters(method.parameters)
            returns_content = self._format_returns(method.returns)
            
            method_doc = f"""##### {method_name}

```python
{method.signature}
```

{method.docstring or "No description available."}

{parameters_content}

{returns_content}
"""
            method_docs.append(method_doc)
        
        return "\n".join(method_docs)
    
    async def _generate_user_guide(self, request: DocumentationRequest) -> DocumentationResult:
        """Generate user guide documentation."""
        # This would integrate with AI models to generate comprehensive user guides
        # For now, return a structured template
        
        sections = [
            DocumentationSection(
                title="Getting Started",
                content="## Getting Started\n\nThis section covers initial setup and basic usage.",
                level=1,
                metadata={},
                subsections=[]
            ),
            DocumentationSection(
                title="Advanced Usage",
                content="## Advanced Usage\n\nThis section covers advanced features and configuration.",
                level=1,
                metadata={},
                subsections=[]
            )
        ]
        
        return DocumentationResult(
            title="User Guide",
            sections=sections,
            metadata={"generated_from": str(request.target_path)}
        )
    
    async def _generate_readme(self, request: DocumentationRequest) -> DocumentationResult:
        """Generate README documentation."""
        # Analyze project structure to generate README
        target_path = Path(request.target_path)
        
        # Basic README template
        readme_content = f"""# {target_path.name}

## Overview

This project provides [brief description].

## Installation

```bash
pip install {target_path.name.lower()}
```

## Quick Start

```python
# Basic usage example
import {target_path.name.lower()}

# Your code here
```

## Documentation

For detailed documentation, see [docs/](docs/).

## Contributing

Contributions are welcome! Please read the contributing guidelines.

## License

This project is licensed under the MIT License.
"""
        
        sections = [
            DocumentationSection(
                title="README",
                content=readme_content,
                level=1,
                metadata={},
                subsections=[]
            )
        ]
        
        return DocumentationResult(
            title="README",
            sections=sections,
            metadata={"generated_from": str(target_path)}
        )


__all__ = [
    'DocumentationGenerator',
    'DocumentationType',
    'DocumentationSection',
    'APIDocumentation',
    'DocstringParser',
    'CodeAnalyzer'
]
