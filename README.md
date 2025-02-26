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
  - Vector-based conversation history (FAISS)
  - Multi-threaded asynchronous processing
  - Integrated web search aggregation
  - Enterprise code pattern detection

- **Developer Workflow Integration**
  - Smart file handling with workspace awareness
  - Automatic code formatting
  - Intelligent context management
  - Real-time code analysis

## Installation

### Production Environment

```bash
pip install aurelis-assistant
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
- `/toggle reasoning` - Enable/disable enhanced reasoning
- `/toggle search` - Enable/disable web search integration
- `/help` - Display command reference
- `exit` - Terminate session

#### File Operations
- Use `#filename` syntax to reference or create files
- Example: `#main.py create a new Flask application`

### Enterprise Integration

#### Workspace Management
```bash
# Initialize in project directory
aurelis chat -w /path/to/project

# Analyze specific file
aurelis analyze /path/to/file.py "Review code quality"

# Edit with AI assistance
aurelis edit /path/to/file.py
```

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
