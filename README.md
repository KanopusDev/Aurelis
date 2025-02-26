# Aurelis Enterprise AI Assistant

Aurelis is an enterprise-grade AI-powered coding assistant that leverages multiple language models and advanced reasoning capabilities to deliver high-quality software solutions.

## Enterprise Features

- **Multi-Modal AI Processing**
  - GPT-4 for core code generation
  - DeepSeek R1 for advanced reasoning
  - O3-mini for parallel validation
  - Cohere Multilingual embeddings for context analysis

- **Enterprise Security**
  - Secure API key management
  - Configurable logging levels
  - Audit trail for all operations
  - Encrypted credential storage

- **Advanced Capabilities**
  - Automated code testing and validation
  - Vector-based conversation history (FAISS)
  - Multi-threaded asynchronous processing
  - Integrated web search aggregation
  - Enterprise code pattern detection
  - Real-time code quality checks

- **Developer Workflow Integration**
  - Smart workspace management
  - Automatic code formatting
  - Intelligent context management
  - Real-time code analysis
  - One-click code copying
  - Built-in code testing

## Installation

### Production Environment

```bash
pip install aurelis
```

### Development Setup

```bash
git clone https://github.com/Kanopusdev/aurelis.git
cd aurelis
pip install -e .
```

## Configuration

### API Keys Setup

```bash
# Configure GitHub token for model access
aurelis config set-key github_token <YOUR_TOKEN>

# Configure search capabilities (optional)
aurelis config set-key google_api_key <YOUR_API_KEY>
aurelis config set-key google_cx <YOUR_CX_ID>
```

### Logging Configuration

```bash
# Set custom log file location
aurelis --log-file /path/to/logs/aurelis.log

# Enable verbose logging
aurelis --verbose
```

## Usage

### Interactive Mode

```bash
# Start with default settings
aurelis chat

# Start with custom workspace
aurelis chat --workspace /path/to/project
```

### Command Reference

#### Chat Interface Commands
- `/workspace <path>` - Change current workspace
- `/toggle reasoning` - Enable/disable enhanced reasoning
- `/toggle search` - Enable/disable web search integration
- `/toggle testing` - Enable/disable automatic code testing
- `/help` - Display command reference
- `exit` - Terminate session

#### Code Generation Features
- Automatic code testing
- Code quality validation
- One-click code copying
- Syntax highlighting
- Line numbers
- Automatic error fixing
- Code block extraction

#### File Operations
- Use `#filename` syntax to reference or create files
- Files are created in current workspace
- Example: `#main.py create a new Flask application`

### Enterprise Integration

#### Workspace Management
```bash
# Initialize in project directory
aurelis chat -w /path/to/project

# Change workspace during chat
/workspace /new/path

# Analyze specific file
aurelis analyze /path/to/file.py "Review code quality"

# Edit with AI assistance
aurelis edit /path/to/file.py
```

#### Code Testing & Validation
- Automatic static analysis
- Built-in unit test generation
- Code quality checks
- Error detection and fixing
- Test case extraction from docstrings

#### Search Integration
```bash
# Perform focused code search
aurelis search "enterprise design patterns in Python"
```

## System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- CUDA-compatible GPU (optional, for enhanced performance)

## Enterprise Support

- Documentation: [Full Documentation](https://aurelis.readthedocs.io)
- Issue Tracking: [GitHub Issues](https://github.com/Kanopusdev/aurelis/issues)
- Enterprise Support: [Contact Us](mailto:pradyumn.tandon@hotmail.com)

## Security

Report security vulnerabilities to pradyumn.tandon@hotmail.com

## License

MIT License - See [LICENSE](LICENSE) for details

## Acknowledgments

- Azure AI Services
- FAISS by Facebook Research
- DeepSeek AI
- O3 Labs

---

**Note**: This is an enterprise tool. Please ensure compliance with your organization's security policies when configuring API keys and file system access.
