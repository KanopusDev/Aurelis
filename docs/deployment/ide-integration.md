# IDE Integration Guide

This guide provides comprehensive instructions for integrating Aurelis with popular IDEs and code editors, including configuration, extensions, and productivity enhancements.

## Table of Contents

- [Visual Studio Code](#visual-studio-code)
- [PyCharm](#pycharm)
- [Vim/Neovim](#vimneovim)
- [Emacs](#emacs)
- [Sublime Text](#sublime-text)
- [Atom](#atom)
- [Jupyter Lab/Notebook](#jupyter-labnotebook)
- [Cloud IDEs](#cloud-ides)
- [Language Server Protocol](#language-server-protocol)
- [Development Tools Integration](#development-tools-integration)

## Visual Studio Code

### Recommended Extensions

#### Core Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-toolsai.jupyter",
    "ms-vscode.vscode-typescript-next",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-json"
  ]
}
```

#### Aurelis-specific Extensions
```json
{
  "recommendations": [
    "ms-python.debugpy",
    "ms-vscode.test-adapter-converter",
    "littlefoxteam.vscode-python-test-adapter",
    "wholroyd.jinja",
    "redhat.vscode-yaml",
    "ms-vscode.cmake-tools"
  ]
}
```

### Workspace Configuration

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ],
  
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/node_modules": true,
    "**/.coverage": true,
    "**/htmlcov": true
  },
  
  "search.exclude": {
    "**/node_modules": true,
    "**/bower_components": true,
    "**/*.code-search": true,
    "**/venv": true,
    "**/__pycache__": true
  },
  
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll": true
  },
  
  "emmet.includeLanguages": {
    "jinja": "html"
  },
  
  "files.associations": {
    "*.j2": "jinja",
    "*.jinja": "jinja",
    "*.jinja2": "jinja"
  },
  
  "terminal.integrated.env.linux": {
    "AURELIS_ENV": "development"
  },
  "terminal.integrated.env.osx": {
    "AURELIS_ENV": "development"
  },
  "terminal.integrated.env.windows": {
    "AURELIS_ENV": "development"
  }
}
```

### Launch Configuration

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
      },
      "django": false,
      "justMyCode": false
    },
    {
      "name": "Aurelis CLI",
      "type": "python",
      "request": "launch",
      "module": "aurelis.cli.main",
      "args": [],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Current Test File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "All Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v", "--cov=aurelis"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Debug Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### Tasks Configuration

Create `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Aurelis Server",
      "type": "shell",
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["-m", "aurelis.cli.main", "serve", "--dev"],
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "isBackground": true,
      "problemMatcher": "$gcc",
      "options": {
        "env": {
          "AURELIS_ENV": "development"
        }
      }
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["-m", "pytest", "tests/", "--cov=aurelis"],
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Format Code",
      "type": "shell",
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["-m", "black", "src/", "tests/"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "silent",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Lint Code",
      "type": "shell",
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["-m", "flake8", "src/", "tests/"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Type Check",
      "type": "shell",
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["-m", "mypy", "src/"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Generate Docs",
      "type": "shell",
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["-m", "aurelis.cli.main", "docs", "generate"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    }
  ]
}
```

### Code Snippets

Create `.vscode/aurelis.code-snippets`:
```json
{
  "Aurelis Model Definition": {
    "prefix": "aurelis-model",
    "body": [
      "from aurelis.models import BaseModel",
      "from aurelis.types import ModelConfig",
      "",
      "class ${1:ModelName}(BaseModel):",
      "    \"\"\"${2:Model description}\"\"\"",
      "    ",
      "    def __init__(self, config: ModelConfig):",
      "        super().__init__(config)",
      "        ${3:# Initialize model-specific attributes}",
      "    ",
      "    async def process(self, input_data: ${4:InputType}) -> ${5:OutputType}:",
      "        \"\"\"${6:Process input and return output}\"\"\"",
      "        ${7:# Implementation}",
      "        return result"
    ],
    "description": "Create a new Aurelis model class"
  },
  
  "Aurelis API Endpoint": {
    "prefix": "aurelis-endpoint",
    "body": [
      "from fastapi import APIRouter, Depends",
      "from aurelis.api.dependencies import get_current_user",
      "from aurelis.schemas import ${1:RequestSchema}, ${2:ResponseSchema}",
      "",
      "router = APIRouter(prefix=\"/${3:endpoint}\")",
      "",
      "@router.${4|get,post,put,delete|}(\"/${5:path}\")",
      "async def ${6:endpoint_function}(",
      "    ${7:request: $1,}",
      "    current_user: User = Depends(get_current_user)",
      ") -> $2:",
      "    \"\"\"${8:Endpoint description}\"\"\"",
      "    ${9:# Implementation}",
      "    return response"
    ],
    "description": "Create a new API endpoint"
  },
  
  "Aurelis Test Case": {
    "prefix": "aurelis-test",
    "body": [
      "import pytest",
      "from aurelis.testing import TestClient",
      "",
      "class Test${1:ClassName}:",
      "    \"\"\"${2:Test class description}\"\"\"",
      "    ",
      "    def setup_method(self):",
      "        \"\"\"Set up test fixtures\"\"\"",
      "        ${3:# Setup code}",
      "    ",
      "    def test_${4:test_name}(self):",
      "        \"\"\"${5:Test description}\"\"\"",
      "        # Arrange",
      "        ${6:# Test setup}",
      "        ",
      "        # Act",
      "        ${7:# Test execution}",
      "        ",
      "        # Assert",
      "        ${8:# Test assertions}"
    ],
    "description": "Create a new test case"
  }
}
```

### Keybindings

Create `.vscode/keybindings.json`:
```json
[
  {
    "key": "ctrl+shift+t",
    "command": "workbench.action.tasks.runTask",
    "args": "Run Tests"
  },
  {
    "key": "ctrl+shift+f",
    "command": "workbench.action.tasks.runTask",
    "args": "Format Code"
  },
  {
    "key": "ctrl+shift+l",
    "command": "workbench.action.tasks.runTask",
    "args": "Lint Code"
  },
  {
    "key": "ctrl+shift+s",
    "command": "workbench.action.tasks.runTask",
    "args": "Start Aurelis Server"
  }
]
```

## PyCharm

### Project Configuration

#### Interpreter Setup
1. File → Settings → Project → Python Interpreter
2. Add New Environment → Virtualenv Environment
3. Base interpreter: Python 3.9+
4. Location: `./venv`

#### Run Configurations

**Aurelis Server Configuration**:
- Script path: `aurelis/cli/main.py`
- Parameters: `serve --dev`
- Environment variables: `AURELIS_ENV=development;AURELIS_DEBUG=true`
- Working directory: Project root

**Test Configuration**:
- Target: Custom
- Additional Arguments: `--cov=aurelis --cov-report=html`
- Working directory: Project root

### Code Style Settings

#### Python Code Style
1. File → Settings → Editor → Code Style → Python
2. Import settings from `.editorconfig`
3. Configure line length: 88 (Black standard)

#### Import Optimization
1. Settings → Editor → Code Style → Python → Imports
2. Enable "Optimize imports on the fly"
3. Configure import sorting to match isort

### External Tools

#### Black Formatter
- Program: `$PROJECT_DIR$/venv/bin/black`
- Arguments: `$FilePathRelativeToProjectRoot$`
- Working directory: `$ProjectFileDir$`

#### Flake8 Linter
- Program: `$PROJECT_DIR$/venv/bin/flake8`
- Arguments: `$FilePathRelativeToProjectRoot$`
- Working directory: `$ProjectFileDir$`

### Live Templates

Create live templates for common Aurelis patterns:

**Model Template** (`aurelis-model`):
```python
from aurelis.models import BaseModel
from aurelis.types import ModelConfig

class $CLASS_NAME$(BaseModel):
    """$DESCRIPTION$"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        $INIT_CODE$
    
    async def process(self, input_data: $INPUT_TYPE$) -> $OUTPUT_TYPE$:
        """$PROCESS_DESCRIPTION$"""
        $IMPLEMENTATION$
        return result
```

### Database Tools

1. Configure database connection
2. Add data source for development database
3. Enable SQL dialect detection

## Vim/Neovim

### Configuration for Neovim

Create `~/.config/nvim/lua/aurelis.lua`:
```lua
-- Aurelis development configuration for Neovim

-- Python LSP configuration
require('lspconfig').pylsp.setup({
  settings = {
    pylsp = {
      plugins = {
        pycodestyle = {
          ignore = {'W503', 'E203'},
          maxLineLength = 88
        },
        flake8 = {
          enabled = true,
          ignore = {'W503', 'E203'},
          maxLineLength = 88
        },
        mypy = {
          enabled = true,
          live_mode = false
        },
        isort = {
          enabled = true,
          profile = 'black'
        },
        black = {
          enabled = true,
          line_length = 88
        }
      }
    }
  }
})

-- Aurelis-specific key mappings
local function map(mode, lhs, rhs, opts)
  local options = { noremap = true, silent = true }
  if opts then
    options = vim.tbl_extend('force', options, opts)
  end
  vim.api.nvim_set_keymap(mode, lhs, rhs, options)
end

-- Aurelis development shortcuts
map('n', '<leader>as', ':!aurelis serve --dev<CR>')
map('n', '<leader>at', ':!pytest tests/<CR>')
map('n', '<leader>af', ':!black %<CR>')
map('n', '<leader>al', ':!flake8 %<CR>')

-- Auto-format on save
vim.cmd([[
  augroup AurelisFormat
    autocmd!
    autocmd BufWritePre *.py execute ':Black'
  augroup END
]])
```

### Plugin Recommendations

Add to your plugin manager (e.g., vim-plug):
```vim
" Language Server Protocol
Plug 'neovim/nvim-lspconfig'
Plug 'hrsh7th/nvim-cmp'
Plug 'hrsh7th/cmp-nvim-lsp'

" Python development
Plug 'psf/black', { 'branch': 'stable' }
Plug 'fisadev/vim-isort'
Plug 'nvie/vim-flake8'

" Testing
Plug 'vim-test/vim-test'
Plug 'janko/vim-test'

" File navigation
Plug 'nvim-telescope/telescope.nvim'
Plug 'nvim-tree/nvim-tree.lua'

" Git integration
Plug 'tpope/vim-fugitive'
Plug 'lewis6991/gitsigns.nvim'
```

### Test Integration

Configure vim-test for pytest:
```vim
let test#strategy = "neovim"
let test#python#pytest#options = '--cov=aurelis'

" Test mappings
nmap <silent> <leader>tn :TestNearest<CR>
nmap <silent> <leader>tf :TestFile<CR>
nmap <silent> <leader>ts :TestSuite<CR>
nmap <silent> <leader>tl :TestLast<CR>
```

## Emacs

### Configuration

Add to your Emacs configuration:
```elisp
;; Aurelis development configuration

;; Python development
(use-package python-mode
  :ensure t
  :config
  (setq python-shell-interpreter "python3"))

;; LSP support
(use-package lsp-mode
  :ensure t
  :init
  (setq lsp-keymap-prefix "C-c l")
  :hook ((python-mode . lsp))
  :commands lsp)

(use-package lsp-pyright
  :ensure t
  :hook (python-mode . (lambda ()
                         (require 'lsp-pyright)
                         (lsp))))

;; Company completion
(use-package company
  :ensure t
  :config
  (global-company-mode t))

;; Flycheck
(use-package flycheck
  :ensure t
  :init (global-flycheck-mode))

;; Black formatting
(use-package python-black
  :ensure t
  :after python
  :hook (python-mode . python-black-on-save-mode))

;; Project management
(use-package projectile
  :ensure t
  :init
  (projectile-mode +1)
  :bind (:map projectile-mode-map
              ("s-p" . projectile-command-map)
              ("C-c p" . projectile-command-map)))

;; Aurelis-specific functions
(defun aurelis-serve ()
  "Start Aurelis development server"
  (interactive)
  (async-shell-command "aurelis serve --dev"))

(defun aurelis-test ()
  "Run Aurelis tests"
  (interactive)
  (async-shell-command "pytest tests/"))

;; Key bindings
(global-set-key (kbd "C-c a s") 'aurelis-serve)
(global-set-key (kbd "C-c a t") 'aurelis-test)
```

## Sublime Text

### Package Control Setup

Install packages:
- LSP
- LSP-pyright
- Python Black
- SublimeLinter
- SublimeLinter-flake8
- Git
- GitGutter

### Project Configuration

Create `aurelis.sublime-project`:
```json
{
  "folders": [
    {
      "path": ".",
      "folder_exclude_patterns": [
        "__pycache__",
        "*.egg-info",
        ".pytest_cache",
        "htmlcov",
        "node_modules"
      ]
    }
  ],
  "settings": {
    "python_interpreter": "./venv/bin/python",
    "LSP": {
      "pyright": {
        "enabled": true,
        "settings": {
          "python.analysis.typeCheckingMode": "basic"
        }
      }
    },
    "SublimeLinter.linters.flake8.args": [
      "--max-line-length=88",
      "--extend-ignore=E203,W503"
    ]
  },
  "build_systems": [
    {
      "name": "Aurelis Server",
      "cmd": ["./venv/bin/python", "-m", "aurelis.cli.main", "serve", "--dev"],
      "working_dir": "$project_path",
      "env": {
        "AURELIS_ENV": "development"
      }
    },
    {
      "name": "Aurelis Tests",
      "cmd": ["./venv/bin/python", "-m", "pytest", "tests/"],
      "working_dir": "$project_path"
    }
  ]
}
```

### Key Bindings

Create custom key bindings:
```json
[
  {
    "keys": ["ctrl+shift+f"],
    "command": "python_black"
  },
  {
    "keys": ["ctrl+shift+t"],
    "command": "build",
    "args": {"variant": "Aurelis Tests"}
  },
  {
    "keys": ["ctrl+shift+s"],
    "command": "build",
    "args": {"variant": "Aurelis Server"}
  }
]
```

## Atom

### Package Installation

```bash
apm install atom-ide-ui
apm install ide-python
apm install python-black
apm install linter-flake8
apm install git-plus
apm install file-icons
```

### Configuration

Add to `config.cson`:
```cson
"*":
  "atom-ide-ui":
    "atom-ide-diagnostics-ui":
      autoVisibility: true
  "ide-python":
    pylsPath: "./venv/bin/pyls"
  "python-black":
    binPath: "./venv/bin/black"
    fmtOnSave: true
  "linter-flake8":
    executablePath: "./venv/bin/flake8"
    maxLineLength: 88
```

## Jupyter Lab/Notebook

### Installation and Setup

```bash
# Install Jupyter Lab
pip install jupyterlab

# Install Aurelis kernel
pip install ipykernel
python -m ipykernel install --user --name=aurelis --display-name="Aurelis"

# Start Jupyter Lab
jupyter lab
```

### Extensions

```bash
# Install useful extensions
jupyter labextension install @jupyterlab/toc
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install jupyterlab-plotly
```

### Aurelis Integration

Create notebook template for Aurelis development:
```python
# Aurelis Development Notebook

import sys
sys.path.append('./src')

from aurelis import Aurelis
from aurelis.models import load_model
from aurelis.utils import configure_logging

# Configure logging for notebook
configure_logging(level='INFO')

# Initialize Aurelis
aurelis = Aurelis()

# Load a model for experimentation
model = load_model('your-model-name')

# Development utilities
def reload_aurelis():
    """Reload Aurelis modules for development"""
    import importlib
    import aurelis
    importlib.reload(aurelis)
    
%load_ext autoreload
%autoreload 2
```

## Cloud IDEs

### GitHub Codespaces

Create `.devcontainer/devcontainer.json`:
```json
{
  "name": "Aurelis Development",
  "image": "mcr.microsoft.com/vscode/devcontainers/python:3.9",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/node:1": {
      "version": "16"
    }
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "ms-toolsai.jupyter"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.formatting.provider": "black"
      }
    }
  },
  "postCreateCommand": "pip install -e .[dev]",
  "forwardPorts": [8080],
  "portsAttributes": {
    "8080": {
      "label": "Aurelis Server",
      "onAutoForward": "notify"
    }
  }
}
```

### GitPod

Create `.gitpod.yml`:
```yaml
image:
  file: .gitpod.Dockerfile

ports:
  - port: 8080
    onOpen: notify

tasks:
  - init: |
      pip install -e .[dev]
      pre-commit install
    command: |
      aurelis serve --dev --host 0.0.0.0

vscode:
  extensions:
    - ms-python.python
    - ms-python.vscode-pylance
    - ms-python.black-formatter
    - ms-toolsai.jupyter
```

Create `.gitpod.Dockerfile`:
```dockerfile
FROM gitpod/workspace-python

USER gitpod

RUN pip install --upgrade pip
RUN pip install black isort flake8 mypy pytest
```

### Replit

Create `.replit`:
```toml
language = "python3"
run = "python -m aurelis.cli.main serve --dev --host 0.0.0.0"

[nix]
channel = "stable-21_11"

[env]
AURELIS_ENV = "development"
PYTHONPATH = "./src"

[deployment]
run = ["sh", "-c", "python -m aurelis.cli.main serve --host 0.0.0.0 --port 8080"]
deploymentTarget = "cloudrun"
```

## Language Server Protocol

### Custom Aurelis LSP Features

For advanced IDE integration, consider implementing custom LSP features:

#### Model Schema Validation
```python
# LSP extension for Aurelis model validation
class AurelisLanguageServer:
    def validate_model_config(self, uri: str, config: dict):
        """Validate Aurelis model configuration"""
        diagnostics = []
        
        # Validate required fields
        required_fields = ['name', 'type', 'parameters']
        for field in required_fields:
            if field not in config:
                diagnostics.append({
                    'range': get_field_range(uri, field),
                    'message': f'Missing required field: {field}',
                    'severity': DiagnosticSeverity.Error
                })
        
        return diagnostics
```

#### Code Completion
```python
def provide_completions(self, uri: str, position: Position):
    """Provide Aurelis-specific completions"""
    completions = []
    
    # Model type completions
    if in_model_definition(uri, position):
        completions.extend([
            CompletionItem('transformers', CompletionItemKind.Class),
            CompletionItem('openai', CompletionItemKind.Class),
            CompletionItem('anthropic', CompletionItemKind.Class),
        ])
    
    return completions
```

## Development Tools Integration

### Git Hooks

Create `.githooks/pre-commit`:
```bash
#!/bin/bash
# Pre-commit hook for Aurelis

# Run code formatting
black --check src/ tests/
if [ $? -ne 0 ]; then
    echo "Code formatting check failed. Run 'black src/ tests/' to fix."
    exit 1
fi

# Run linting
flake8 src/ tests/
if [ $? -ne 0 ]; then
    echo "Linting failed. Fix the issues above."
    exit 1
fi

# Run type checking
mypy src/
if [ $? -ne 0 ]; then
    echo "Type checking failed. Fix the issues above."
    exit 1
fi

# Run tests
pytest tests/ --cov=aurelis --cov-fail-under=80
if [ $? -ne 0 ]; then
    echo "Tests failed or coverage too low."
    exit 1
fi

echo "All checks passed!"
```

### Makefile Integration

Create `Makefile`:
```makefile
.PHONY: help install dev test format lint type-check clean docs

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -e .

dev:  ## Install development dependencies
	pip install -e .[dev]

test:  ## Run tests
	pytest tests/ --cov=aurelis

format:  ## Format code
	black src/ tests/
	isort src/ tests/

lint:  ## Lint code
	flake8 src/ tests/

type-check:  ## Run type checking
	mypy src/

clean:  ## Clean cache files
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage

docs:  ## Generate documentation
	aurelis docs generate

serve:  ## Start development server
	aurelis serve --dev

shell:  ## Start interactive shell
	aurelis shell
```

### Docker Development Integration

Create `docker-compose.dev.yml` for IDE integration:
```yaml
version: '3.8'
services:
  aurelis-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/workspace
      - vscode-extensions:/root/.vscode-server/extensions
      - vscode-settings:/root/.vscode-server/data/User
    ports:
      - "8080:8080"
      - "5678:5678"  # Debug port
    environment:
      - AURELIS_ENV=development
      - PYTHONPATH=/workspace/src
    command: sleep infinity

volumes:
  vscode-extensions:
  vscode-settings:
```

This comprehensive IDE integration guide provides configuration and setup instructions for all major development environments, ensuring developers can work efficiently with Aurelis regardless of their preferred tools.
