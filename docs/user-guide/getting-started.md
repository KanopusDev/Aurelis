# Getting Started with Aurelis

**Aurelis** is an enterprise-grade AI code assistant that exclusively uses GitHub models via Azure AI Inference. This guide will get you up and running in minutes.

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed on your system
- **GitHub Account** with access to GitHub models
- **GitHub Token** with appropriate model access permissions

### 1. Installation

```bash
# Install from PyPI (recommended)
pip install aurelis-cli

# Or install from source
git clone https://github.com/kanopusdev/aurelis.git
cd aurelis
pip install -e .
```

### 2. GitHub Token Setup

Aurelis uses GitHub models exclusively through Azure AI Inference. You need a GitHub token with model access.

#### Get Your GitHub Token

1. Go to [GitHub Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select appropriate scopes for model access
4. Copy the generated token

#### Set Environment Variable

```bash
# Linux/macOS
export GITHUB_TOKEN="your_github_token_here"

# Windows PowerShell
$env:GITHUB_TOKEN="your_github_token_here"

# Windows Command Prompt
set GITHUB_TOKEN=your_github_token_here
```

### 3. Initialize Aurelis

```bash
# Initialize configuration
aurelis init

# Verify setup
aurelis models
```

### 4. First Commands

```bash
# List available GitHub models
aurelis models

# Analyze a Python file
aurelis analyze script.py

# Generate code from description
aurelis generate "Create a FastAPI endpoint for user authentication"

# Start interactive shell
aurelis shell
```

## 🖥️ Interactive Shell

The Aurelis shell provides the most powerful experience:

```bash
aurelis shell
```

Inside the shell, you can use these commands:

```bash
# Model management
models          # List available models
health          # Check model connectivity
config          # View configuration

# Code operations
analyze file.py         # Analyze code
generate "description"  # Generate code
explain "code snippet"  # Explain code
fix file.py            # Fix issues
refactor file.py       # Optimize code

# Documentation
docs file.py           # Generate docs
test file.py           # Create tests

# Session management
session save name      # Save session
session load name      # Load session
history               # Command history
help                  # Show all commands
exit                  # Exit shell
```

## 📁 Project Configuration

Create a `.aurelis.yaml` file in your project root:

```yaml
# GitHub Models Configuration
github_token: "${GITHUB_TOKEN}"  # Use environment variable

models:
  primary: "codestral-2501"       # Primary model for code tasks
  fallback: "gpt-4o-mini"         # Fallback model for reliability
  
analysis:
  max_file_size: "1MB"
  chunk_size: 3500               # Optimized for 4K context models
  overlap_ratio: 0.15
  
processing:
  max_retries: 3
  timeout: 60
  concurrent_requests: 5
  
security:
  audit_logging: true
  secure_token_storage: true

cache:
  enabled: true
  ttl: 3600  # 1 hour
  max_size: 1000
```

## 🤖 Understanding GitHub Models

Aurelis intelligently routes tasks to the best GitHub model:

### Code Generation Tasks
- **Primary**: Codestral-2501 (specialized for coding)
- **Fallback**: GPT-4o (complex reasoning)

### Documentation Tasks
- **Primary**: Cohere Command-R (optimized for explanations)
- **Fallback**: GPT-4o-mini (fast responses)

### Complex Reasoning
- **Primary**: GPT-4o (advanced reasoning)
- **Fallback**: Meta Llama 3.1 405B (maximum capability)

### Performance Tasks
- **Primary**: Mistral Nemo (fast inference)
- **Fallback**: GPT-4o-mini (efficient responses)

## ✅ Verification

Test your setup with these commands:

```bash
# Check configuration
aurelis config

# Verify token and connectivity
aurelis models

# Test code analysis
echo "def hello(): print('world')" > test.py
aurelis analyze test.py

# Test code generation
aurelis generate "Python function to calculate fibonacci"

# Test shell
aurelis shell
```

## 🐛 Troubleshooting

### Common Issues

#### "GitHub token not configured"
```bash
# Verify token is set
echo $GITHUB_TOKEN  # Linux/macOS
echo $env:GITHUB_TOKEN  # Windows PowerShell

# Set token if missing
export GITHUB_TOKEN="your_token_here"
```

#### "Failed to initialize Aurelis"
```bash
# Check configuration
aurelis config

# Recreate configuration
aurelis init --force
```

#### "Model not responding"
```bash
# Check model health
aurelis models

# Verify network connectivity
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://models.inference.ai.azure.com/health
```

#### "Import errors"
```bash
# Reinstall dependencies
pip install --upgrade aurelis

# Or install from source
pip install -e .
```

### Getting Help

```bash
# CLI help
aurelis --help

# Command-specific help
aurelis analyze --help
aurelis generate --help

# Shell help
aurelis shell
> help
```

## 🏢 Enterprise Setup

For enterprise setups, see:

- [Enterprise Architecture](../architecture/enterprise.md)
- [Security Configuration](../architecture/security.md)
- [Performance Configuration](../architecture/performance.md)

## 📖 Next Steps

Now that you have Aurelis running:

1. **Explore Commands**: Try all CLI commands with your code
2. **Master the Shell**: Use the interactive shell for complex tasks
3. **Configure Models**: Customize model preferences for your workflow
4. **Integrate in IDE**: Set up IDE integration for seamless development
5. **Team Setup**: Configure for team collaboration

### Learning Resources

- [User Guide](../user-guide/) - Comprehensive usage documentation
- [CLI Reference](cli-reference.md) - Complete command reference
- [GitHub Models Guide](github-models.md) - Model selection and optimization
- [Best Practices](best-practices.md) - Production tips and patterns

---

**Need Help?**

- 📖 [Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/kanopusdev/aurelis/issues)
- 💬 [Discussions](https://github.com/kanopusdev/aurelis/discussions)
- 🏢 [Enterprise Support](mailto:enterprise@kanopus.org)

*Ready to supercharge your development with AI? Let's code! 🚀*
