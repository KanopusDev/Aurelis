# Aurelis CLI Reference

Complete reference for the Aurelis command-line interface. All commands work with GitHub models via Azure AI Inference.

## 🖥️ Command Overview

```bash
aurelis [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGS]
```

### Global Options

- `--help` - Show help message and exit
- `--version` - Show version information
- `--config PATH` - Use custom configuration file
- `--verbose` - Enable verbose logging
- `--quiet` - Suppress non-essential output

## 📋 Core Commands

### `aurelis init`

Initialize Aurelis configuration for GitHub models.

```bash
aurelis init [OPTIONS]
```

**Options:**
- `--config PATH` - Path to configuration file (default: `.aurelis.yaml`)
- `--force` - Overwrite existing configuration
- `--help` - Show command help

**Examples:**
```bash
# Basic initialization
aurelis init

# Force recreate configuration
aurelis init --force

# Custom config location
aurelis init --config /path/to/config.yaml
```

### `aurelis models`

Display available GitHub models and their capabilities.

```bash
aurelis models [OPTIONS]
```

**Options:**
- `--detailed` - Show detailed model information
- `--health` - Include health status for each model
- `--json` - Output in JSON format

**Examples:**
```bash
# List all models
aurelis models

# Detailed model information
aurelis models --detailed

# Health check for all models
aurelis models --health
```

**Sample Output:**
```
GitHub Models via Azure AI Inference
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Model                  ┃ Provider  ┃ Best For                             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Codestral-2501         │ Mistral   │ Code generation & optimization       │
│ GPT-4o                 │ OpenAI    │ Complex reasoning & multimodal       │
│ GPT-4o-mini            │ OpenAI    │ Fast responses & documentation       │
└────────────────────────┴───────────┴──────────────────────────────────────┘
```

### `aurelis config`

Manage Aurelis configuration and GitHub token.

```bash
aurelis config [OPTIONS]
```

**Options:**
- `--show` - Display current configuration
- `--set KEY=VALUE` - Set configuration value
- `--token TOKEN` - Set GitHub token
- `--validate` - Validate current configuration

**Examples:**
```bash
# Show current configuration
aurelis config --show

# Set primary model
aurelis config --set models.primary=gpt-4o

# Update GitHub token
aurelis config --token ghp_your_new_token

# Validate configuration
aurelis config --validate
```

## 🔍 Analysis Commands

### `aurelis analyze`

Analyze Python code for issues, improvements, and insights.

```bash
aurelis analyze [OPTIONS] PATH [PATH...]
```

**Options:**
- `--model MODEL` - Specific model to use for analysis
- `--type TYPE` - Analysis type: `security|performance|style|complexity|all`
- `--output FORMAT` - Output format: `text|json|markdown|html`
- `--recursive` - Analyze directories recursively
- `--exclude PATTERN` - Exclude files matching pattern
- `--config PATH` - Use specific configuration file

**Examples:**
```bash
# Analyze single file
aurelis analyze script.py

# Analyze directory recursively
aurelis analyze --recursive src/

# Security analysis only
aurelis analyze --type security app.py

# Use specific model
aurelis analyze --model codestral-2501 module.py

# Output as JSON
aurelis analyze --output json script.py

# Exclude test files
aurelis analyze --exclude "*_test.py" --recursive src/
```

**Sample Output:**
```
📁 Analysis Results for script.py

🔍 Code Quality Score: 85/100

📊 Metrics:
  • Lines of Code: 156
  • Cyclomatic Complexity: 12
  • Maintainability Index: 68

⚠️ Issues Found (3):
  1. Performance: O(n²) algorithm in fibonacci() (line 23)
  2. Security: Potential SQL injection in query() (line 45)
  3. Style: Missing docstring in helper() (line 67)

✅ Suggestions:
  • Use memoization for fibonacci calculation
  • Implement parameterized queries
  • Add comprehensive docstrings
```

### `aurelis generate`

Generate code from natural language descriptions.

```bash
aurelis generate [OPTIONS] DESCRIPTION
```

**Options:**
- `--model MODEL` - Specific model for generation
- `--language LANG` - Target programming language (default: python)
- `--style STYLE` - Code style: `clean|optimized|documented|minimal`
- `--output PATH` - Save generated code to file
- `--template TEMPLATE` - Use specific code template
- `--interactive` - Interactive refinement mode

**Examples:**
```bash
# Basic code generation
aurelis generate "Create a FastAPI endpoint for user authentication"

# Generate with specific model
aurelis generate --model codestral-2501 "Binary search algorithm"

# Generate TypeScript code
aurelis generate --language typescript "React component for file upload"

# Save to file
aurelis generate --output auth.py "JWT token validation function"

# Interactive mode
aurelis generate --interactive "REST API for todo management"
```

**Sample Output:**
```python
# Generated by Aurelis (Codestral-2501)
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

app = FastAPI()
security = HTTPBearer()

@app.post("/auth/login")
async def authenticate_user(credentials: UserCredentials):
    """Authenticate user and return JWT token."""
    # Implementation here...
```

### `aurelis explain`

Explain code functionality and provide detailed analysis.

```bash
aurelis explain [OPTIONS] CODE_OR_FILE
```

**Options:**
- `--model MODEL` - Model for explanation
- `--level LEVEL` - Explanation level: `basic|detailed|expert`
- `--focus ASPECT` - Focus on: `algorithm|performance|security|patterns`
- `--format FORMAT` - Output format: `text|markdown|html`

**Examples:**
```bash
# Explain code snippet
aurelis explain "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"

# Explain file
aurelis explain complex_algorithm.py

# Detailed explanation
aurelis explain --level detailed --focus algorithm sort.py

# Focus on performance
aurelis explain --focus performance database.py
```

## 🛠️ Development Commands

### `aurelis fix`

Automatically fix code issues and apply improvements.

```bash
aurelis fix [OPTIONS] PATH [PATH...]
```

**Options:**
- `--model MODEL` - Model for fix suggestions
- `--type TYPE` - Fix type: `security|performance|style|bugs|all`
- `--apply` - Apply fixes automatically (with confirmation)
- `--backup` - Create backup before applying fixes
- `--dry-run` - Show fixes without applying

**Examples:**
```bash
# Show fix suggestions
aurelis fix script.py

# Apply security fixes with backup
aurelis fix --type security --apply --backup app.py

# Dry run for all fixes
aurelis fix --dry-run --type all module.py
```

### `aurelis refactor`

Refactor and optimize code for better maintainability.

```bash
aurelis refactor [OPTIONS] PATH [PATH...]
```

**Options:**
- `--model MODEL` - Model for refactoring
- `--goal GOAL` - Refactoring goal: `performance|readability|modularity|patterns`
- `--aggressive` - Enable aggressive refactoring
- `--preserve-behavior` - Ensure behavior preservation
- `--output DIR` - Output refactored code to directory

**Examples:**
```bash
# Basic refactoring
aurelis refactor legacy_code.py

# Performance-focused refactoring
aurelis refactor --goal performance slow_function.py

# Aggressive refactoring with output
aurelis refactor --aggressive --output refactored/ old_module.py
```

### `aurelis docs`

Generate comprehensive documentation for code.

```bash
aurelis docs [OPTIONS] PATH [PATH...]
```

**Options:**
- `--model MODEL` - Model for documentation
- `--format FORMAT` - Output format: `markdown|rst|html|docstring`
- `--include SECTIONS` - Include: `api|examples|usage|architecture`
- `--output PATH` - Output documentation file/directory
- `--template TEMPLATE` - Documentation template

**Examples:**
```bash
# Generate markdown docs
aurelis docs --format markdown api.py

# Comprehensive documentation
aurelis docs --include api,examples,usage --output docs/ src/

# Update docstrings in-place
aurelis docs --format docstring module.py
```

### `aurelis test`

Generate test cases and test suites for code.

```bash
aurelis test [OPTIONS] PATH [PATH...]
```

**Options:**
- `--model MODEL` - Model for test generation
- `--framework FRAMEWORK` - Test framework: `pytest|unittest|doctest`
- `--coverage TARGET` - Target coverage percentage
- `--type TYPE` - Test type: `unit|integration|performance|security`
- `--output PATH` - Output test file

**Examples:**
```bash
# Generate pytest tests
aurelis test --framework pytest calculator.py

# High coverage unit tests
aurelis test --type unit --coverage 95 core.py

# Security tests
aurelis test --type security auth.py
```

## 🖥️ Interactive Commands

### `aurelis shell`

Start interactive Aurelis shell for advanced workflows.

```bash
aurelis shell [OPTIONS]
```

**Options:**
- `--config PATH` - Configuration file
- `--history` - Load command history
- `--session SESSION` - Load saved session

**Examples:**
```bash
# Start interactive shell
aurelis shell

# Load specific session
aurelis shell --session my_project

# Start with history
aurelis shell --history
```

**Shell Commands:**
```bash
# Model management
models              # List available models  
health              # Check model connectivity
switch <model>      # Switch active model

# Code operations
analyze <file>      # Analyze code
generate <desc>     # Generate code
explain <code>      # Explain code
fix <file>          # Fix issues
refactor <file>     # Refactor code

# Documentation
docs <file>         # Generate documentation
test <file>         # Generate tests

# Session management
session save <name> # Save current session
session load <name> # Load session
session list        # List saved sessions
history             # Show command history
clear               # Clear screen

# Utilities
help                # Show help
exit                # Exit shell
```

## 🔧 Utility Commands

### `aurelis validate`

Validate code syntax, style, and best practices.

```bash
aurelis validate [OPTIONS] PATH [PATH...]
```

**Options:**
- `--strict` - Enable strict validation
- `--rules RULES` - Validation rules file
- `--exclude PATTERN` - Exclude files/rules

### `aurelis optimize`

Optimize code for performance and efficiency.

```bash
aurelis optimize [OPTIONS] PATH [PATH...]
```

**Options:**
- `--target TARGET` - Optimization target: `speed|memory|size`
- `--profile` - Include performance profiling

### `aurelis security`

Perform security analysis and vulnerability detection.

```bash
aurelis security [OPTIONS] PATH [PATH...]
```

**Options:**
- `--severity LEVEL` - Minimum severity: `low|medium|high|critical`
- `--report FORMAT` - Security report format

## ⚙️ Configuration

### Global Configuration

Aurelis looks for configuration in these locations (in order):

1. `--config` command line option
2. `AURELIS_CONFIG` environment variable
3. `.aurelis.yaml` in current directory
4. `~/.aurelis/config.yaml` in home directory

### Configuration File Format

```yaml
# GitHub Models Configuration
github_token: "${GITHUB_TOKEN}"

models:
  primary: "codestral-2501"
  fallback: "gpt-4o-mini"
  preferences:
    code_generation: "codestral-2501"
    documentation: "cohere-command-r"
    reasoning: "gpt-4o"

analysis:
  max_file_size: "1MB"
  chunk_size: 3500
  overlap_ratio: 0.15
  exclude_patterns:
    - "*.pyc"
    - "__pycache__/"
    - ".git/"

processing:
  max_retries: 3
  timeout: 60
  concurrent_requests: 5
  
security:
  audit_logging: true
  secure_token_storage: true
  
cache:
  enabled: true
  ttl: 3600
  max_size: 1000
```

### Environment Variables

- `GITHUB_TOKEN` - GitHub authentication token
- `AURELIS_CONFIG` - Path to configuration file
- `AURELIS_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `AURELIS_CACHE_DIR` - Cache directory path

## 🐛 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Authentication error |
| 4 | Network error |
| 5 | File not found |
| 6 | Invalid input |
| 7 | Model error |
| 8 | Timeout error |

## 📖 Examples

### Complete Workflow

```bash
# 1. Setup
aurelis init
export GITHUB_TOKEN="your_token"

# 2. Analyze project
aurelis analyze --recursive --type all src/

# 3. Fix critical issues
aurelis fix --type security --apply src/

# 4. Generate documentation
aurelis docs --format markdown --output docs/ src/

# 5. Create tests
aurelis test --framework pytest --coverage 90 src/

# 6. Interactive refinement
aurelis shell
> load session project_review
> analyze complex_module.py
> refactor --goal performance slow_function.py
> generate "async version of process_data function"
> session save project_review_complete
```

### CI/CD Integration

```bash
#!/bin/bash
# Aurelis CI pipeline

# Validate code quality
aurelis validate --strict src/ || exit 1

# Security check
aurelis security --severity medium src/ || exit 1

# Generate documentation
aurelis docs --format markdown --output docs/ src/

# Update tests if needed
aurelis test --framework pytest --coverage 85 src/
```

## 🔗 Related Documentation

- [Getting Started](getting-started.md) - Initial setup guide
- [GitHub Models Guide](github-models.md) - Model selection and optimization
- [Configuration Guide](configuration.md) - Detailed configuration options
- [Shell Guide](shell-guide.md) - Interactive shell features
- [API Reference](../api/) - Programmatic interface

---

**Need Help?**

```bash
# Command help
aurelis COMMAND --help

# General help
aurelis --help

# Interactive help
aurelis shell
> help
```

*Master the CLI to unlock Aurelis's full potential! 🚀*
