# Aurelis Interactive Shell Guide

**Complete guide to the enterprise-grade interactive development environment**

## 🚀 Overview

The Aurelis Interactive Shell is a powerful, AI-powered development environment that provides real-time access to GitHub's cutting-edge AI models for code analysis, generation, and optimization. It combines the convenience of a command-line interface with the intelligence of modern AI systems.

## 🎯 Key Features

### ✨ Core Capabilities
- **17 Production-Ready Commands** for comprehensive development workflows
- **Real-time AI Integration** with 9 GitHub models via Azure AI Inference
- **Intelligent Auto-completion** for commands, files, and context-aware suggestions
- **Rich Interactive Interface** with syntax highlighting and progress indicators
- **Session Management** with persistent history and state tracking
- **Multi-language Support** for Python, JavaScript, TypeScript, Java, C++, and more

### 🔧 Enterprise Features
- **Audit Logging** for compliance and tracking
- **Security Controls** with file filtering and access management
- **Performance Optimization** with caching and concurrent request handling
- **Error Recovery** with graceful degradation and fallback systems

## 🚀 Getting Started

### Starting the Shell
```bash
# Start interactive shell
aurelis shell

# Start with specific configuration
aurelis shell --config /path/to/config.yaml

# Start in debug mode
aurelis shell --debug
```

### First-Time Setup Verification
```bash
# Check system status
aurelis:project> status

# Verify GitHub models
aurelis:project> models

# Test AI functionality
aurelis:project> generate "simple hello world function"
```

## 📋 Command Reference

### 🆘 Help & Navigation

#### `help` - Get Command Information
```bash
# Show all available commands
aurelis:project> help

# Get detailed help for specific command
aurelis:project> help analyze
aurelis:project> help generate
aurelis:project> help search
```

#### `status` - System Status Check
```bash
# Show comprehensive system status
aurelis:project> status

# Example output:
# ┌─────────────────────┬─────────────┬─────────────────────┐
# │ Component           │ Status      │ Details             │
# ├─────────────────────┼─────────────┼─────────────────────┤
# │ Session Manager     │ ✓ Active    │                     │
# │ Model Orchestrator  │ ✓ Active    │ 9 models available  │
# │ Code Analyzer       │ ✓ Active    │                     │
# └─────────────────────┴─────────────┴─────────────────────┘
```

### 🔍 Code Analysis & Search

#### `analyze` - Comprehensive Code Analysis
```bash
# Analyze a specific file
aurelis:project> analyze src/main.py

# Example output with metrics:
# ┌─────────────────┬─────────────┐
# │ Metric          │ Value       │
# ├─────────────────┼─────────────┤
# │ Lines of Code   │ 245         │
# │ File Size       │ 8,432 bytes │
# │ Language        │ python      │
# │ Complexity      │ Medium      │
# └─────────────────┴─────────────┘
```

#### `search` - Intelligent Codebase Search
```bash
# Search for code patterns
aurelis:project> search "function definition"
aurelis:project> search "import pandas"
aurelis:project> search "class"

# Example output with highlighted matches:
# File: src/utils/helpers.py
#   42: def process_data(input_data):
#   58: def validate_input(data):
# 
# File: src/models/analyzer.py
#   15: def analyze_code(content):
#   89: def generate_report():
```

### 🤖 AI-Powered Development

#### `generate` - AI Code Generation
```bash
# Generate code from natural language
aurelis:project> generate "REST API endpoint for user authentication"
aurelius:project> generate "Python function to parse CSV files"
aurelis:project> generate "React component for file upload"

# The AI will generate complete, production-ready code with:
# - Proper error handling
# - Documentation
# - Type hints (where applicable)
# - Best practices implementation
```

#### `explain` - Code Explanation
```bash
# Get detailed explanation of code
aurelis:project> explain src/complex_algorithm.py

# Example output:
# ╭─ Code Explanation: complex_algorithm.py ─╮
# │                                          │
# │ ## Purpose                               │
# │ This module implements a sophisticated   │
# │ sorting algorithm with O(n log n)        │
# │ complexity...                            │
# │                                          │
# │ ## Key Components                        │
# │ - quicksort(): Main sorting function     │
# │ - partition(): Helper for pivot          │
# │ - median_of_three(): Optimization       │
# ╰──────────────────────────────────────────╯
```

#### `docs` - AI Documentation Generation
```bash
# Generate comprehensive documentation
aurelis:project> docs src/api/endpoints.py

# Generates professional documentation including:
# - Function/class descriptions
# - Parameter documentation  
# - Return value specifications
# - Usage examples
# - Error handling information

# Option to save to file:
# Save documentation to file? [y/N]: y
# Enter filename [generated_docs.md]: api_documentation.md
# ✓ Documentation saved to api_documentation.md
```

#### `fix` - Automated Code Fixing
```bash
# Analyze and fix code issues
aurelis:project> fix src/buggy_code.py

# AI will identify and suggest fixes for:
# - Syntax errors
# - Logic issues
# - Performance problems
# - Security vulnerabilities
# - Code style violations
```

#### `refactor` - Intelligent Refactoring
```bash
# Get refactoring suggestions
aurelis:project> refactor src/legacy_code.py

# AI provides suggestions for:
# - Code structure improvements
# - Performance optimizations
# - Readability enhancements
# - Design pattern applications
# - Maintainability improvements
```

#### `test` - Test Generation
```bash
# Generate comprehensive tests
aurelis:project> test src/calculator.py

# AI generates:
# - Unit tests with multiple scenarios
# - Edge case testing
# - Mock implementations
# - Test data fixtures
# - Performance benchmarks
```

### 🎛️ Configuration & Management

#### `config` - Configuration Management
```bash
# Show current configuration
aurelis:project> config

# Show specific configuration section
aurelis:project> config models
aurelis:project> config security

# Modify configuration
aurelis:project> config set models.primary gpt-4o
aurelis:project> config set cache.ttl 7200
```

#### `models` - AI Model Management
```bash
# List available GitHub models
aurelis:project> models

# Example output:
# ┌─────────────────────┬──────────┬─────────────────────────────┐
# │ Model               │ Provider │ Best For                    │
# ├─────────────────────┼──────────┼─────────────────────────────┤
# │ codestral-2501      │ Mistral  │ Code generation             │
# │ gpt-4o              │ OpenAI   │ Complex reasoning           │
# │ gpt-4o-mini         │ OpenAI   │ Fast responses              │
# │ cohere-command-r    │ Cohere   │ Documentation               │
# └─────────────────────┴──────────┴─────────────────────────────┘

# Test model connectivity
aurelis:project> models health

# Switch primary model
aurelis:project> models switch gpt-4o
```

#### `session` - Session Management
```bash
# Show current session information
aurelis:project> session

# List all available sessions
aurelis:project> session list

# Session management operations
aurelis:project> session save current_work
aurelis:project> session load previous_session
aurelis:project> session clear
aurelis:project> session export session_backup.json
```

#### `tools` - Available Tools
```bash
# List registered development tools
aurelis:project> tools

# Example output:
# ┌──────────────────┬─────────────────────────────────────┬────────┐
# │ Tool             │ Description                         │ Status │
# ├──────────────────┼─────────────────────────────────────┼────────┤
# │ Code Analyzer    │ Static analysis and quality check   │ Active │
# │ Model Router     │ AI model routing and management     │ Active │
# │ Session Manager  │ Development session persistence     │ Active │
# │ Context Manager  │ Code context and file tracking      │ Active │
# └──────────────────┴─────────────────────────────────────┴────────┘
```

### 🛠️ Utility Commands

#### `history` - Command History
```bash
# Show recent command history
aurelis:project> history

# Example output:
# ┌───────┬─────────────────────────────────────┐
# │ Index │ Command                             │
# ├───────┼─────────────────────────────────────┤
# │   1   │ analyze src/main.py                 │
# │   2   │ generate "API endpoint"             │
# │   3   │ search "function"                   │
# │   4   │ docs src/utils.py                   │
# └───────┴─────────────────────────────────────┘
```

#### `clear` - Clear Screen
```bash
# Clear screen and redisplay welcome
aurelis:project> clear
```

#### `exit` / `quit` - Exit Shell
```bash
# Exit shell with session saving
aurelis:project> exit
aurelis:project> quit

# Output:
# Saving session...
# ✓ Session saved successfully
# Goodbye!
```

## 🎨 Shell Features

### Auto-completion
The shell provides intelligent auto-completion for:

```bash
# Command completion
aurelis:project> gen<TAB>
generate

# File path completion  
aurelis:project> analyze src/<TAB>
src/main.py    src/utils.py    src/config.py

# Context-aware completion
aurelis:project> config <TAB>
show    set    get    models    cache    security

aurelis:project> session <TAB>
list    load    save    clear    info    export    import
```

### Syntax Highlighting
- **Commands** appear in cyan
- **File paths** appear in blue  
- **Success messages** appear in green
- **Error messages** appear in red
- **Code blocks** have language-specific highlighting

### Progress Indicators
Long-running operations show progress:

```bash
aurelis:project> generate "complex algorithm"
⠋ Generating code... 

aurelius:project> search "large codebase query"
⠙ Searching... [████████████████████████████████] 1,247 files scanned
```

### Rich Output Formatting
Results are displayed in professional tables and panels:

```bash
# Tables for structured data
┌─────────────────┬─────────────┐
│ Metric          │ Value       │
├─────────────────┼─────────────┤
│ Lines of Code   │ 1,247       │
└─────────────────┴─────────────┘

# Panels for detailed information
╭─ Generated Code ─╮
│                  │
│ def authenticate │
│   # Complete     │
│   # implementation
╰──────────────────╯

# Syntax-highlighted code blocks
import pandas as pd
import numpy as np

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process the input dataframe."""
    return df.dropna()
```

## 🔧 Advanced Usage

### Workflow Integration

#### Development Workflow Example
```bash
# 1. Start new development session
aurelis:project> session clear

# 2. Analyze existing codebase
aurelis:project> search "TODO"
aurelis:project> analyze src/main.py

# 3. Generate new functionality
aurelis:project> generate "user authentication middleware"

# 4. Create documentation
aurelis:project> docs src/auth/middleware.py

# 5. Generate tests
aurelis:project> test src/auth/middleware.py

# 6. Save session for later
aurelis:project> session save auth_implementation
```

#### Code Review Workflow
```bash
# 1. Analyze code quality
aurelis:project> analyze src/new_feature.py

# 2. Get refactoring suggestions
aurelis:project> refactor src/new_feature.py

# 3. Identify potential issues
aurelis:project> fix src/new_feature.py

# 4. Generate comprehensive documentation
aurelis:project> docs src/new_feature.py

# 5. Create test coverage
aurelis:project> test src/new_feature.py
```

### Batch Operations
```bash
# Search and analyze multiple files
aurelis:project> search "deprecated"
# Then analyze each file found:
aurelis:project> analyze src/legacy/old_api.py
aurelis:project> refactor src/legacy/old_api.py

# Generate documentation for entire module
aurelis:project> docs src/api/
aurelius:project> docs src/models/
aurelis:project> docs src/utils/
```

### Session Management Best Practices
```bash
# Create themed sessions for different work
aurelis:project> session save frontend_work
aurelis:project> session save backend_api
aurelis:project> session save testing_suite

# Export sessions for backup
aurelis:project> session export frontend_backup.json

# Load specific session for context
aurelis:project> session load backend_api
```

## 🛡️ Security & Compliance

### Secure File Handling
```bash
# The shell automatically filters sensitive files
aurelis:project> analyze config/secrets.yaml
# ❌ Access denied: File contains sensitive information

# Safe file patterns are allowed
aurelius:project> analyze src/main.py
# ✓ Analysis complete

# Check security settings
aurelis:project> config security
```

### Audit Trail
```bash
# All commands are logged for audit purposes
aurelis:project> analyze src/financial_data.py
# Logged: User analyzed financial_data.py at 2025-06-17 14:30:00

# Session activities are tracked
aurelis:project> session info
# Session ID: abc123-def456
# Commands executed: 15
# Files accessed: 8
# Start time: 2025-06-17 14:00:00
```

## 🚨 Troubleshooting

### Common Issues

#### 1. AI Model Connectivity
```bash
# Check model status
aurelis:project> models health

# If models are unavailable:
# ❌ Model connectivity issue: Check GitHub token

# Test GitHub token
aurelis:project> config test
```

#### 2. File Access Issues
```bash
# If file cannot be accessed:
aurelis:project> analyze /restricted/file.py
# ❌ File not found or access denied

# Check current directory
aurelis:project> pwd
# Check file permissions and paths
```

#### 3. Performance Issues
```bash
# Check current configuration
aurelis:project> config processing

# Adjust concurrent requests if needed
aurelis:project> config set processing.concurrent_requests 3

# Clear cache if needed
aurelis:project> config set cache.enabled false
```

#### 4. Session Issues
```bash
# If session fails to save:
aurelis:project> session clear
aurelis:project> session save new_session

# Check session directory permissions
aurelis:project> config show | grep session
```

## 📊 Performance Tips

### Optimization Strategies
1. **Use specific commands** instead of general analysis for better performance
2. **Enable caching** for frequently accessed operations
3. **Limit concurrent requests** based on your API quotas
4. **Use appropriate models** for different tasks (e.g., gpt-4o-mini for quick responses)

### Recommended Workflows
1. **Start with search** to understand codebase structure
2. **Use analyze** for specific files rather than entire directories
3. **Generate documentation** incrementally rather than all at once
4. **Save sessions** to preserve context between work periods

---

**🎯 Next Steps:**
- [GitHub Models Integration](github-models.md) - Deep dive into AI capabilities
- [Best Practices](best-practices.md) - Optimize your workflow
- [CLI Reference](cli-reference.md) - Learn command-line usage
- [Enterprise Features](../architecture/enterprise.md) - Explore advanced capabilities
