# Aurelis - Enterprise AI Code Assistant

> **Powered exclusively by GitHub Models via Azure AI Inference**

Aurelis is a production-grade, enterprise AI code assistant that leverages GitHub's powerful AI models through Azure AI Inference. Developed by **Gamecooler19** at **Kanopus**, Aurelis provides intelligent code analysis, generation, optimization, and documentation capabilities for modern software development.

[![Website](https://img.shields.io/badge/Website-aurelis.kanopus.org-blue)](https://aurelis.kanopus.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![GitHub Models](https://img.shields.io/badge/Powered%20by-GitHub%20Models-purple.svg)](https://github.com/models)

## 🚀 Features

### **Enterprise-Grade AI Integration**
- **GitHub Models Exclusively**: Access to Codestral-2501, GPT-4o, GPT-4o-mini, Cohere Command-R/R+, Meta Llama 3.1, and Mistral models
- **Azure AI Inference**: Production-ready API with enterprise security and reliability
- **Single Token Authentication**: Unified GitHub token for all model access
- **Intelligent Model Routing**: Automatic model selection based on task type and performance
- **Fallback & Retry Logic**: Enterprise-grade error handling with circuit breaker patterns

### **Advanced Code Intelligence**
- **Real-time Code Analysis**: Syntax, performance, security, and style analysis
- **AI-Powered Code Generation**: Natural language to production-ready code
- **Intelligent Refactoring**: Automated code optimization and modernization
- **Documentation Generation**: Comprehensive docstrings and technical documentation
- **Context-Aware Processing**: Smart chunking for optimal model performance

### **Production-Ready Architecture**
- **Interactive Shell**: Rich CLI with auto-completion and syntax highlighting
- **Session Management**: Persistent contexts and conversation history
- **Enterprise Security**: Secure token management and audit logging
- **Performance Optimization**: Response caching and concurrent processing
- **Comprehensive Monitoring**: Health checks and performance metrics

## 🛠 Installation

### Quick Install
```bash
pip install aurelis-cli
```

### From Source
```bash
git clone https://github.com/kanopusdev/aurelis.git
cd aurelis
pip install -e .
```

## ⚡ Quick Start

### 1. Setup GitHub Token
Get your GitHub token with model access from [GitHub Settings](https://github.com/settings/tokens):

```bash
export GITHUB_TOKEN="your_github_token_here"
```

### 2. Initialize Aurelis
```bash
aurelis init
```

### 3. View Available Models
```bash
aurelis models
```

### 4. Analyze Code
```bash
aurelis analyze /path/to/your/project
```

### 5. Generate Code
```bash
aurelis generate "Create a FastAPI endpoint for user authentication"
```

### 6. Interactive Shell
```bash
aurelis shell
```

## 🏗 GitHub Models Support

Aurelis exclusively uses GitHub models via Azure AI Inference:

| Model | Provider | Best For | Context |
|-------|----------|----------|---------|
| **Codestral-2501** | Mistral | Code generation, completion, optimization | 4K tokens |
| **GPT-4o** | OpenAI | Complex reasoning, tool usage, multimodal | 4K tokens |
| **GPT-4o-mini** | OpenAI | Fast responses, documentation, simple tasks | 4K tokens |
| **Cohere Command-R** | Cohere | Documentation, explanations, summarization | 4K tokens |
| **Cohere Command-R+** | Cohere | Advanced reasoning, complex queries | 4K tokens |
| **Meta Llama 3.1 70B** | Meta | Balanced performance, general tasks | 4K tokens |
| **Meta Llama 3.1 405B** | Meta | Maximum capability, complex reasoning | 4K tokens |
| **Mistral Large** | Mistral | Enterprise applications, reasoning | 4K tokens |
| **Mistral Nemo** | Mistral | Fast inference, code completion | 4K tokens |

## ⚙️ Configuration

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
```

## 🖥 Interactive Shell Commands

The Aurelis shell provides a comprehensive set of commands:

```bash
# Model Management
models          # List available GitHub models
health          # Check model connectivity
config          # Manage configuration

# Code Analysis & Generation  
analyze <file>  # Analyze code for issues
generate <desc> # Generate code from description
explain <code>  # Explain code functionality
fix <file>      # Fix detected issues
refactor <file> # Optimize and modernize code

# Documentation
docs <file>     # Generate documentation
test <file>     # Generate test cases

# Session Management
session save    # Save current session
session load    # Load previous session
history         # Show command history
```

## 🏢 Enterprise Features

### Security & Compliance
- **Secure Token Management**: Encrypted GitHub token storage
- **Audit Logging**: Comprehensive request/response logging
- **Rate Limiting**: Intelligent request throttling
- **Data Privacy**: No code storage or external transmission beyond GitHub

### Performance & Reliability
- **Response Caching**: Intelligent caching for repeated queries
- **Load Balancing**: Automatic model selection and fallback
- **Health Monitoring**: Real-time model availability checks
- **Circuit Breaker**: Automatic failure detection and recovery

### Monitoring & Analytics
- **Usage Metrics**: Token consumption and cost tracking
- **Performance Analytics**: Response times and success rates
- **Model Statistics**: Usage patterns and optimization insights

## 📖 Documentation

Complete documentation is available at **[aurelis.kanopus.org](https://aurelis.kanopus.org)**:

- [User Guide](https://aurelis.kanopus.org/docs/user-guide)
- [API Reference](https://aurelis.kanopus.org/docs/api) 
- [Architecture Guide](https://aurelis.kanopus.org/docs/architecture)
- [GitHub Models Integration](https://aurelis.kanopus.org/docs/github-models)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://aurelis.kanopus.org/docs/contributing) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🏢 About Kanopus

**Kanopus** is pioneering AI-driven development solutions for modern software engineering. Learn more at [kanopus.org](https://kanopus.org).

---

**Developed with ❤️ by Gamecooler19 @ Kanopus**

*Aurelis - Where AI meets enterprise code development*
