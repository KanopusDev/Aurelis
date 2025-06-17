# Local Development Guide

This guide provides comprehensive instructions for setting up and developing Aurelis locally across different operating systems and development environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Development Installation](#development-installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Debugging](#debugging)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)
- [Hot Reloading](#hot-reloading)
- [Code Quality Tools](#code-quality-tools)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher (if using frontend components)
- **Git**: Latest version
- **Docker**: Optional but recommended for containerized development

### Required Tools

#### Core Development Tools
```bash
# Python and pip (usually bundled)
python --version
pip --version

# Git
git --version

# Code editor (recommended: VS Code)
code --version
```

#### Optional Tools
```bash
# Docker and Docker Compose
docker --version
docker-compose --version

# Node.js and npm (for frontend development)
node --version
npm --version
```

## Environment Setup

### Windows Setup

#### Using Windows Subsystem for Linux (WSL) - Recommended
```powershell
# Install WSL2
wsl --install

# Install Ubuntu
wsl --install -d Ubuntu

# Update WSL
wsl --update
```

#### Native Windows Setup
```powershell
# Install Python via Microsoft Store or python.org
# Install Git for Windows
# Install VS Code with Python extension

# Set up virtual environment
python -m venv aurelis-env
aurelis-env\Scripts\activate
```

### macOS Setup

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.9

# Install Git (if not already installed)
brew install git

# Install optional tools
brew install docker
brew install --cask docker
```

### Linux Setup (Ubuntu/Debian)

```bash
# Update package index
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install Git
sudo apt install git

# Install build essentials
sudo apt install build-essential

# Install optional tools
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
```

## Development Installation

### Clone Repository

```bash
# Clone the repository
git clone https://github.com/kanopusdev/aurelis.git
cd aurelis

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install Dependencies

#### Development Dependencies
```bash
# Install development dependencies
pip install -e ".[dev]"

# Or if using requirements files
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Frontend Dependencies (if applicable)
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to project root
cd ..
```

### Verify Installation

```bash
# Verify Aurelis installation
aurelis --version

# Run basic health check
aurelis health-check

# Run tests to ensure everything is working
pytest tests/
```

## Configuration

### Development Configuration File

Create `config/development.yaml`:
```yaml
# Development configuration
environment: development
debug: true

# Application settings
app:
  host: localhost
  port: 8080
  reload: true
  workers: 1

# Database settings
database:
  url: sqlite:///aurelis_dev.db
  echo: true  # Log SQL queries

# Logging configuration
logging:
  level: DEBUG
  format: detailed
  handlers:
    - console
    - file

# AI Model settings
models:
  cache_dir: ./cache/models
  download_on_startup: false
  
# Development-specific features
development:
  auto_reload: true
  debug_toolbar: true
  profiling: enabled
  mock_external_apis: true
```

### Environment-specific Configuration

Create `.env.development`:
```bash
# Development environment variables
AURELIS_ENV=development
AURELIS_DEBUG=true
AURELIS_LOG_LEVEL=DEBUG

# Database
DATABASE_URL=sqlite:///aurelis_dev.db

# API Keys (use test/development keys)
OPENAI_API_KEY=your-dev-key-here
AZURE_API_KEY=your-dev-key-here

# External Services
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200

# Development flags
ENABLE_HOT_RELOAD=true
ENABLE_DEBUG_TOOLBAR=true
MOCK_EXTERNAL_APIS=true
```

## Running the Application

### Standard Development Server

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run development server
aurelis serve --dev

# Alternative with custom configuration
aurelis serve --config config/development.yaml --debug
```

### Using Docker for Development

#### Docker Compose Setup

Create `docker-compose.dev.yml`:
```yaml
version: '3.8'

services:
  aurelis:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8080:8080"
    volumes:
      - .:/app
      - /app/venv  # Exclude virtual environment
    environment:
      - AURELIS_ENV=development
      - AURELIS_DEBUG=true
    depends_on:
      - redis
      - postgres
    command: aurelis serve --dev --host 0.0.0.0

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: aurelis_dev
      POSTGRES_USER: aurelius
      POSTGRES_PASSWORD: development
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  elasticsearch:
    image: elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

volumes:
  postgres_data:
  es_data:
```

#### Development Dockerfile

Create `Dockerfile.dev`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements*.txt ./
RUN pip install -r requirements-dev.txt

# Copy source code
COPY . .

# Install in development mode
RUN pip install -e .

# Expose port
EXPOSE 8080

# Default command
CMD ["aurelis", "serve", "--dev", "--host", "0.0.0.0"]
```

#### Run with Docker

```bash
# Build and start development environment
docker-compose -f docker-compose.dev.yml up --build

# Run in detached mode
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f aurelis

# Stop services
docker-compose -f docker-compose.dev.yml down
```

## Development Workflow

### Code Structure

```
aurelis/
├── src/aurelis/           # Main application code
│   ├── core/             # Core functionality
│   ├── models/           # AI model handling
│   ├── api/              # API endpoints
│   ├── cli/              # Command-line interface
│   └── utils/            # Utility functions
├── tests/                # Test files
├── docs/                 # Documentation
├── config/               # Configuration files
├── scripts/              # Development scripts
└── examples/             # Usage examples
```

### Development Commands

```bash
# Start development server with hot reload
aurelis serve --dev --reload

# Run specific modules
python -m aurelis.cli.main --help

# Interactive development shell
aurelis shell

# Database operations
aurelis db migrate
aurelis db upgrade
aurelis db seed  # Seed with development data
```

### Code Generation and Analysis

```bash
# Generate code documentation
aurelis docs generate --output docs/api/

# Analyze code structure
aurelis analyze --target src/aurelis/

# Generate type stubs
aurelis generate types --output types/

# Code formatting and linting
aurelis format --check
aurelis lint --fix
```

## Testing

### Test Setup

```bash
# Install test dependencies
pip install -e ".[test]"

# Set up test database
export AURELIS_ENV=test
aurelis db create-test-db
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aurelis --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run tests with specific markers
pytest -m "not slow"
pytest -m "integration"

# Run tests in parallel
pytest -n auto

# Watch mode for development
ptw -- --cov=aurelis
```

### Test Configuration

Create `pytest.ini`:
```ini
[tool:pytest]
minversion = 6.0
addopts = 
    -ra 
    --strict-markers 
    --strict-config 
    --cov=aurelis 
    --cov-report=term-missing:skip-covered 
    --cov-report=html:htmlcov 
    --cov-report=xml
testpaths = tests
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    unit: marks tests as unit tests
```

## Debugging

### VS Code Debug Configuration

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Aurelis Server",
            "type": "python",
            "request": "launch",
            "module": "aurelis.cli.main",
            "args": ["serve", "--dev"],
            "console": "integratedTerminal",
            "env": {
                "AURELIS_ENV": "development",
                "AURELIS_DEBUG": "true"
            },
            "autoReload": {
                "enable": true
            }
        },
        {
            "name": "Aurelis CLI",
            "type": "python",
            "request": "launch",
            "module": "aurelis.cli.main",
            "args": [],
            "console": "integratedTerminal"
        },
        {
            "name": "Run Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["${workspaceFolder}/tests"],
            "console": "integratedTerminal"
        }
    ]
}
```

### Python Debugging

```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use ipdb for enhanced debugging
import ipdb; ipdb.set_trace()

# Remote debugging with debugpy
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### Logging for Development

```python
import logging

# Configure development logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Use structured logging
logger = logging.getLogger(__name__)
logger.debug("Debug message with context", extra={
    "user_id": user_id,
    "request_id": request_id
})
```

## Database Setup

### SQLite Development Database

```bash
# Initialize database
aurelis db init

# Run migrations
aurelis db migrate

# Seed with development data
aurelis db seed --env development
```

### PostgreSQL Development Database

```bash
# Start PostgreSQL with Docker
docker run -d \
  --name aurelis-postgres \
  -e POSTGRES_DB=aurelis_dev \
  -e POSTGRES_USER=aurelius \
  -e POSTGRES_PASSWORD=development \
  -p 5432:5432 \
  postgres:14-alpine

# Configure connection
export DATABASE_URL="postgresql://aurelius:development@localhost:5432/aurelis_dev"

# Initialize and migrate
aurelis db init
aurelis db migrate
```

### Database Management Commands

```bash
# Create migration
aurelis db revision --message "Add new feature"

# Apply migrations
aurelis db upgrade

# Downgrade migration
aurelis db downgrade -1

# Reset database
aurelis db reset --confirm

# Export/Import data
aurelis db export --output data.json
aurelis db import --input data.json
```

## Environment Variables

### Development Environment Variables

Create `.env`:
```bash
# Core settings
AURELIS_ENV=development
AURELIS_DEBUG=true
AURELIS_LOG_LEVEL=DEBUG

# Server settings
AURELIS_HOST=localhost
AURELIS_PORT=8080
AURELIS_WORKERS=1

# Database
DATABASE_URL=sqlite:///aurelis_dev.db

# Caching
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300

# AI Model APIs
OPENAI_API_KEY=sk-dev-key-here
ANTHROPIC_API_KEY=sk-ant-dev-key
AZURE_OPENAI_API_KEY=your-azure-dev-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Development features
ENABLE_HOT_RELOAD=true
ENABLE_DEBUG_TOOLBAR=true
ENABLE_PROFILING=true
MOCK_EXTERNAL_APIS=true

# Security (development only)
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Environment Variable Management

```bash
# Load environment variables
source .env

# Or use python-dotenv
pip install python-dotenv
```

```python
# In your application
from dotenv import load_dotenv
load_dotenv()

import os
debug = os.getenv('AURELIS_DEBUG', 'false').lower() == 'true'
```

## Hot Reloading

### Application Hot Reload

```bash
# Enable hot reload in development server
aurelis serve --dev --reload

# Watch specific directories
aurelis serve --dev --reload --watch-dirs src/aurelis,config/
```

### Frontend Hot Reload (if applicable)

```bash
# Start frontend development server
cd frontend
npm run dev

# With proxy to backend
npm run dev -- --proxy-config proxy.conf.json
```

Create `frontend/proxy.conf.json`:
```json
{
  "/api/*": {
    "target": "http://localhost:8080",
    "secure": false,
    "changeOrigin": true
  }
}
```

## Code Quality Tools

### Pre-commit Hooks

Install and configure pre-commit:
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.4
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
```

### Code Formatting

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Run together
black src/ tests/ && isort src/ tests/
```

### Linting

```bash
# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/

# Security scanning with bandit
bandit -r src/
```

### Code Analysis

```bash
# Generate complexity report
radon cc src/ --show-complexity

# Generate maintainability index
radon mi src/

# Dependency analysis
aurelis analyze dependencies --output deps.json
```

## Troubleshooting

### Common Issues

#### Python Environment Issues

```bash
# Check Python version
python --version

# Check virtual environment
which python
pip list

# Recreate virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

#### Database Connection Issues

```bash
# Check database connectivity
aurelis db status

# Reset database
aurelis db reset --confirm

# Check database migrations
aurelis db current
aurelis db history
```

#### Port Conflicts

```bash
# Check what's using port 8080
# On Linux/macOS:
lsof -i :8080
# On Windows:
netstat -ano | findstr :8080

# Use different port
aurelis serve --dev --port 8081
```

#### Memory Issues

```bash
# Monitor memory usage
aurelis monitor --memory

# Reduce memory usage
export AURELIS_WORKERS=1
export AURELIS_MEMORY_LIMIT=512M
```

### Debug Information

```bash
# System information
aurelis info system

# Environment information
aurelis info env

# Dependency information
aurelis info deps

# Configuration dump
aurelis config dump --env development
```

### Performance Profiling

```bash
# Enable profiling
export ENABLE_PROFILING=true

# Run with profiler
aurelis serve --dev --profile

# Generate performance report
aurelis profile report --output performance.html
```

### Logs and Monitoring

```bash
# View application logs
tail -f logs/aurelis.log

# View error logs
tail -f logs/error.log

# Monitor metrics
aurelis metrics --watch
```

### Getting Help

- Check the [main documentation](../README.md)
- Review [API documentation](../api/README.md)
- Search [GitHub issues](https://github.com/kanopusdev/aurelis/issues)
- Join the development [Discord/Slack channel](#)
- Contact the development team

### Development Resources

- [Contributing Guidelines](../CONTRIBUTING.md)
- [Code Style Guide](../CODE_STYLE.md)
- [Architecture Documentation](../ARCHITECTURE.md)
- [API Reference](../api/README.md)
- [Deployment Guides](./README.md)
