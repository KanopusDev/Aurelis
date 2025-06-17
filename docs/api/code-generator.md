# Code Generator API Reference

The Code Generator API provides advanced AI-powered code generation capabilities, enabling automatic creation of high-quality code from natural language descriptions, specifications, and templates.

## Overview

The Code Generator leverages GitHub's AI models to provide:
- Natural language to code translation
- Template-based code generation
- Context-aware code completion
- Multi-language code generation
- Best practices enforcement
- Documentation-driven development

## Core Classes

### CodeGenerator

Main code generation class with AI model integration.

```python
from aurelis.generation import CodeGenerator

generator = CodeGenerator()
```

#### Methods

##### `generate_from_description(description: str, language: str = "python", context: Optional[Dict] = None) -> GenerationResult`

Generates code from natural language description.

**Parameters:**
- `description` (str): Natural language description of desired code
- `language` (str): Target programming language (default: "python")
- `context` (Optional[Dict]): Additional context for generation

**Returns:**
- `GenerationResult`: Generated code with metadata

**Example:**
```python
from aurelis.generation import CodeGenerator

generator = CodeGenerator()

result = await generator.generate_from_description(
    description="Create a function that calculates the factorial of a number",
    language="python",
    context={
        "style": "functional",
        "include_docstring": True,
        "include_type_hints": True
    }
)

print(result.code)
print(f"Confidence: {result.confidence}")
```

##### `generate_from_template(template_name: str, variables: Dict[str, Any]) -> GenerationResult`

Generates code using predefined templates.

**Parameters:**
- `template_name` (str): Name of the template to use
- `variables` (Dict[str, Any]): Variables to substitute in template

**Returns:**
- `GenerationResult`: Generated code

**Example:**
```python
result = await generator.generate_from_template(
    template_name="rest_api_endpoint",
    variables={
        "endpoint_name": "users",
        "model_class": "User",
        "database_table": "users",
        "auth_required": True
    }
)
```

##### `complete_code(partial_code: str, cursor_position: int, language: str) -> CompletionResult`

Provides intelligent code completion.

**Parameters:**
- `partial_code` (str): Existing code with incomplete sections
- `cursor_position` (int): Position where completion is needed
- `language` (str): Programming language

**Returns:**
- `CompletionResult`: Multiple completion suggestions

##### `generate_tests(source_code: str, test_framework: str = "pytest") -> GenerationResult`

Generates unit tests for existing code.

**Parameters:**
- `source_code` (str): Source code to generate tests for
- `test_framework` (str): Testing framework to use

**Returns:**
- `GenerationResult`: Generated test code

**Example:**
```python
source_code = '''
def calculate_area(radius):
    """Calculate the area of a circle."""
    return 3.14159 * radius ** 2
'''

test_result = await generator.generate_tests(
    source_code=source_code,
    test_framework="pytest"
)

print(test_result.code)
```

##### `generate_documentation(code: str, format: str = "markdown") -> GenerationResult`

Generates documentation for code.

**Parameters:**
- `code` (str): Source code to document
- `format` (str): Documentation format ("markdown", "rst", "html")

**Returns:**
- `GenerationResult`: Generated documentation

##### `refactor_code(code: str, refactor_type: str, options: Dict = None) -> GenerationResult`

Refactors existing code for better structure and maintainability.

**Parameters:**
- `code` (str): Code to refactor
- `refactor_type` (str): Type of refactoring ("extract_method", "rename_variable", etc.)
- `options` (Dict): Refactoring-specific options

**Returns:**
- `GenerationResult`: Refactored code

## Data Models

### GenerationResult

Contains the results of code generation.

```python
@dataclass
class GenerationResult:
    code: str
    language: str
    confidence: float
    metadata: Dict[str, Any]
    suggestions: List[str]
    processing_time: float
    model_used: ModelType
    timestamp: datetime
```

### CompletionResult

Contains code completion suggestions.

```python
@dataclass
class CompletionResult:
    completions: List[CompletionSuggestion]
    cursor_position: int
    context: str
    processing_time: float
```

### CompletionSuggestion

Individual completion suggestion.

```python
@dataclass
class CompletionSuggestion:
    text: str
    confidence: float
    type: str  # "function", "variable", "class", etc.
    description: Optional[str]
    documentation: Optional[str]
```

## Template System

### Built-in Templates

The generator includes templates for common patterns:

#### Web Development
- `rest_api_endpoint`: RESTful API endpoints
- `database_model`: Database model classes
- `authentication_middleware`: Auth middleware
- `error_handler`: Error handling components

#### Data Science
- `data_processor`: Data processing pipelines
- `ml_model`: Machine learning model templates
- `visualization`: Data visualization code
- `statistical_analysis`: Statistical analysis functions

#### Utilities
- `config_manager`: Configuration management
- `logger_setup`: Logging configuration
- `file_processor`: File processing utilities
- `async_wrapper`: Async function wrappers

### Custom Templates

Create custom templates for project-specific patterns:

```python
# Register custom template
generator.register_template(
    name="custom_service",
    template="""
class {{service_name}}Service:
    \"\"\"{{description}}\"\"\"
    
    def __init__(self):
        self.{{resource_name}} = {{resource_type}}()
    
    async def get_{{resource_name}}(self, id: int) -> {{return_type}}:
        \"\"\"Get {{resource_name}} by ID.\"\"\"
        return await self.{{resource_name}}.get(id)
    
    async def create_{{resource_name}}(self, data: {{input_type}}) -> {{return_type}}:
        \"\"\"Create new {{resource_name}}.\"\"\"
        return await self.{{resource_name}}.create(data)
    """,
    variables=[
        "service_name", "description", "resource_name", 
        "resource_type", "return_type", "input_type"
    ]
)
```

## Language Support

### Supported Languages

- **Python**: Full support with type hints, decorators, async/await
- **JavaScript/TypeScript**: Modern ES6+ features, React components
- **Java**: Spring Boot, JPA, modern Java features
- **C#**: .NET Core, Entity Framework, LINQ
- **Go**: Goroutines, channels, modern Go idioms
- **Rust**: Memory safety, async programming, traits
- **Swift**: iOS development, SwiftUI, async/await
- **Kotlin**: Android development, coroutines

### Language-Specific Features

Each language has optimized generation patterns:

```python
# Python-specific generation
result = await generator.generate_from_description(
    "Create a REST API endpoint for user management",
    language="python",
    context={
        "framework": "fastapi",
        "async": True,
        "type_hints": True,
        "pydantic_models": True
    }
)

# JavaScript/React-specific generation
result = await generator.generate_from_description(
    "Create a React component for displaying user profiles",
    language="javascript",
    context={
        "framework": "react",
        "typescript": True,
        "hooks": True,
        "styled_components": True
    }
)
```

## Integration Examples

### Basic Code Generation

```python
import asyncio
from aurelis.generation import CodeGenerator

async def generate_basic_function():
    generator = CodeGenerator()
    
    result = await generator.generate_from_description(
        description="Create a function to validate email addresses",
        language="python",
        context={
            "include_docstring": True,
            "include_type_hints": True,
            "include_examples": True
        }
    )
    
    print("Generated Code:")
    print(result.code)
    print(f"\nConfidence: {result.confidence:.2f}")
    print(f"Model used: {result.model_used.value}")

asyncio.run(generate_basic_function())
```

### Template-Based Generation

```python
async def generate_from_template():
    generator = CodeGenerator()
    
    # Generate a REST API endpoint
    result = await generator.generate_from_template(
        template_name="rest_api_endpoint",
        variables={
            "resource_name": "products",
            "model_class": "Product",
            "database_table": "products",
            "auth_required": True,
            "validation_schema": "ProductSchema",
            "response_model": "ProductResponse"
        }
    )
    
    print("Generated API Endpoint:")
    print(result.code)
```

### Test Generation

```python
async def generate_comprehensive_tests():
    generator = CodeGenerator()
    
    source_code = '''
class Calculator:
    def add(self, a: float, b: float) -> float:
        return a + b
    
    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def calculate_compound_interest(self, principal: float, rate: float, time: float) -> float:
        return principal * (1 + rate) ** time
    '''
    
    result = await generator.generate_tests(
        source_code=source_code,
        test_framework="pytest",
        context={
            "include_edge_cases": True,
            "include_error_cases": True,
            "include_fixtures": True,
            "coverage_target": "high"
        }
    )
    
    print("Generated Tests:")
    print(result.code)
```

### Code Completion

```python
async def intelligent_completion():
    generator = CodeGenerator()
    
    partial_code = '''
import pandas as pd
import numpy as np

def analyze_sales_data(df):
    """Analyze sales data and return insights."""
    # Remove outliers
    Q1 = df['sales'].quantile(0.25)
    Q3 = df['sales'].quantile(0.75)
    IQR = Q3 - Q1
    
    # Filter data
    filtered_df = df[
    '''
    
    cursor_position = len(partial_code)
    
    completion = await generator.complete_code(
        partial_code=partial_code,
        cursor_position=cursor_position,
        language="python"
    )
    
    print("Completion suggestions:")
    for i, suggestion in enumerate(completion.completions[:3], 1):
        print(f"{i}. {suggestion.text} (confidence: {suggestion.confidence:.2f})")
        if suggestion.description:
            print(f"   Description: {suggestion.description}")
```

### Documentation Generation

```python
async def generate_api_docs():
    generator = CodeGenerator()
    
    code = '''
class UserService:
    def __init__(self, database: Database):
        self.db = database
    
    async def create_user(self, user_data: UserCreateRequest) -> User:
        user = User(**user_data.dict())
        await self.db.save(user)
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.db.get(User, user_id)
    
    async def update_user(self, user_id: int, updates: UserUpdateRequest) -> User:
        user = await self.get_user(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        for field, value in updates.dict(exclude_unset=True).items():
            setattr(user, field, value)
        
        await self.db.save(user)
        return user
    '''
    
    result = await generator.generate_documentation(
        code=code,
        format="markdown",
        context={
            "include_examples": True,
            "include_api_endpoints": True,
            "include_error_responses": True
        }
    )
    
    print("Generated Documentation:")
    print(result.code)
```

## Configuration

### Generator Configuration

```yaml
code_generator:
  default_language: "python"
  max_generation_time: 30
  temperature: 0.7  # Creativity level (0.0-1.0)
  max_tokens: 2000
  include_comments: true
  include_type_hints: true
  
  templates:
    directory: "./templates"
    auto_reload: true
  
  language_configs:
    python:
      style: "pep8"
      async_preferred: true
      type_hints: true
    
    javascript:
      style: "airbnb"
      typescript: true
      react_hooks: true
```

### Model Selection

Configure which models to use for different tasks:

```python
generator.configure_models({
    "code_generation": ModelType.CODESTRAL_2501,
    "completion": ModelType.GPT_4O,
    "documentation": ModelType.COHERE_COMMAND_R,
    "refactoring": ModelType.META_LLAMA_3_1_70B
})
```

## Advanced Features

### Context-Aware Generation

The generator can use project context for better results:

```python
# Set project context
generator.set_project_context({
    "framework": "django",
    "database": "postgresql", 
    "architecture": "microservices",
    "coding_standards": "./standards.md",
    "existing_models": ["User", "Product", "Order"]
})

# Generate with context
result = await generator.generate_from_description(
    "Create a service to handle order processing",
    language="python"
)
```

### Iterative Refinement

Improve generated code through iterations:

```python
initial_result = await generator.generate_from_description(
    "Create a caching decorator",
    language="python"
)

# Refine based on feedback
refined_result = await generator.refine_code(
    code=initial_result.code,
    feedback="Add TTL support and async compatibility",
    requirements=["thread-safe", "configurable backend"]
)
```

### Batch Generation

Generate multiple related components:

```python
components = await generator.generate_batch([
    {
        "type": "model",
        "description": "User model with authentication",
        "context": {"orm": "sqlalchemy"}
    },
    {
        "type": "schema", 
        "description": "Pydantic schemas for User model",
        "context": {"validation": "strict"}
    },
    {
        "type": "service",
        "description": "User service with CRUD operations",
        "context": {"async": True}
    },
    {
        "type": "controller",
        "description": "FastAPI controller for User endpoints",
        "context": {"auth": "JWT"}
    }
])
```

## Best Practices

1. **Clear Descriptions**: Provide detailed, specific descriptions for better results
2. **Context Usage**: Always provide relevant context for domain-specific generation
3. **Iterative Development**: Start simple and refine through iterations
4. **Template Standardization**: Use templates for consistent code patterns
5. **Review Generated Code**: Always review and test generated code
6. **Performance Monitoring**: Monitor generation times and adjust timeouts
7. **Version Control**: Track generated code changes like any other code

## Error Handling

```python
from aurelis.generation.exceptions import (
    GenerationError,
    TemplateNotFoundError,
    UnsupportedLanguageError,
    GenerationTimeoutError
)

try:
    result = await generator.generate_from_description(description, language)
except UnsupportedLanguageError:
    print(f"Language {language} is not supported")
except GenerationTimeoutError:
    print("Generation timed out, try simplifying the request")
except TemplateNotFoundError:
    print("Requested template not found")
except GenerationError as e:
    print(f"Generation failed: {e}")
```

## Performance Optimization

- Use caching for frequently generated patterns
- Leverage templates for common code structures
- Batch related generations when possible
- Set appropriate timeouts for complex generations
- Monitor token usage and costs

For detailed implementation examples and advanced use cases, refer to the main Aurelis documentation.
