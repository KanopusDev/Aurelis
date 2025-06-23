# Aurelis User Guide - Installation & Setup

**Enterprise-grade installation guide for production environments**

## 📋 Prerequisites

### System Requirements
- **Python:** 3.9+ (3.11+ recommended for optimal performance)
- **Operating System:** Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Memory:** Minimum 4GB RAM (8GB+ recommended for large codebases)
- **Storage:** 500MB for installation + workspace storage
- **Network:** Internet connection for GitHub API access

### Required Accounts
- **GitHub Account:** Active GitHub account with API access
- **GitHub Token:** Personal access token with appropriate permissions

## 🚀 Installation Methods

### Method 1: Direct Installation (Recommended)

#### From Source (Development/Enterprise)
```bash
# Clone the repository
git clone https://github.com/kanopus/aurelis.git
cd aurelis

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Aurelis in development mode
pip install -e .
```

#### Production Installation
```bash
# Install from PyPI (when available)
pip install aurelisai

# Or install from wheel
pip install aurelisai-1.0.0-py3-none-any.whl
```

## 🔧 Configuration Setup

### 1. Initialize Aurelis Configuration

```bash
# Initialize with default settings
aurelis init

# Initialize with custom config path
aurelis init --config /path/to/config.yaml

# Force overwrite existing configuration
aurelius init --force
```

### 2. GitHub Token Configuration

#### Environment Variable (Recommended)
```bash
# Windows (PowerShell)
$env:GITHUB_TOKEN="ghp_your_token_here"

# Windows (Command Prompt)
set GITHUB_TOKEN=ghp_your_token_here

# macOS/Linux (Bash/Zsh)
export GITHUB_TOKEN="ghp_your_token_here"

# Make permanent by adding to your shell profile
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
```

#### Configuration File
```yaml
# .aurelis.yaml
github_token: "ghp_your_token_here"  # Not recommended for production

# Better: Use environment variable reference
github_token: "${GITHUB_TOKEN}"
```

### 3. Verify Installation

```bash
# Check Aurelis version
aurelis --version

# Verify GitHub models access
aurelis models

# Test configuration
aurelis status
```

## 🔐 GitHub Token Setup

### Creating a GitHub Token

1. **Navigate to GitHub Settings**
   - Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
   - Click "Generate new token" > "Generate new token (classic)"

2. **Configure Token Permissions**
   - **Expiration:** Set appropriate expiration (90 days recommended)
   - **Scopes:** Select required permissions:
     - `read:user` - Read user profile information
     - `read:org` - Read organization membership (if applicable)

3. **GitHub Models Access**
   - Ensure your account has access to GitHub Models
   - Visit [GitHub Models](https://github.com/marketplace/models) to verify access

4. **Copy and Secure Token**
   - Copy the generated token immediately
   - Store securely (password manager recommended)
   - Never commit tokens to version control

### Token Security Best Practices

#### Environment Variables
```bash
# Store in secure environment variables
export GITHUB_TOKEN="ghp_your_token_here"

# Use in your shell
aurelis generate "Create a REST API"
```

#### Configuration Security
```yaml
# ✅ Good: Environment variable reference
github_token: "${GITHUB_TOKEN}"

# ❌ Bad: Hardcoded token
github_token: "ghp_your_token_here"
```

#### Enterprise Token Management
```yaml
# Enterprise configuration with secure token storage
security:
  token_storage: "environment"  # or "keyring", "vault"
  audit_logging: true
  secure_config: true
```

## 📁 Directory Structure Setup

### Recommended Project Structure
```
your-project/
├── .aurelis.yaml          # Aurelis configuration
├── .env                   # Environment variables (optional)
├── .gitignore            # Include .aurelis/ in gitignore
├── src/                  # Your source code
├── tests/                # Your tests
├── docs/                 # Project documentation
└── .aurelis/             # Aurelis working directory
    ├── sessions/         # Shell sessions
    ├── cache/           # Model response cache
    └── logs/            # Audit and error logs
```

### .gitignore Recommendations
```gitignore
# Aurelis working directory
.aurelis/

# Environment files
.env
.env.local

# Sensitive configuration
config/secrets.yaml
```

## 🧪 Verification & Testing

### Installation Verification
```bash
# 1. Check version and basic functionality
aurelis --version
aurelis --help

# 2. Verify GitHub token and model access
aurelis models
aurelis models test

# 3. Test basic AI functionality
aurelis generate "Hello World function in Python"

# 4. Start interactive shell
aurelis shell
```

### Health Check Commands
```bash
# System status check
aurelis status

# GitHub API connectivity
aurelis models health

# Configuration validation
aurelis config show
```

### Troubleshooting Installation

#### Common Issues

**1. Python Version Incompatibility**
```bash
# Check Python version
python --version
python3 --version

# Use specific Python version
python3.11 -m pip install aurelisai
```

**2. GitHub Token Issues**
```bash
# Verify token format (should start with 'ghp_')
echo $GITHUB_TOKEN

# Test token with curl
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

**3. Network/Proxy Issues**
```bash
# Configure pip for proxy
pip install --proxy https://proxy.company.com:8080 aurelis

# Configure git for proxy
git config --global http.proxy https://proxy.company.com:8080
```

**4. Permission Issues**
```bash
# Use user installation
pip install --user aurelis

# Fix permissions (Linux/macOS)
sudo chown -R $USER:$USER ~/.local
```

## 🏢 Enterprise Installation

### Corporate Environment Setup

#### 1. Enterprise Configuration Template
```yaml
# enterprise.aurelis.yaml
github_token: "${GITHUB_TOKEN}"

models:
  primary: "gpt-4o"
  fallback: "gpt-4o-mini"
  enterprise_routing: true

security:
  audit_logging: true
  secure_token_storage: true
  compliance_mode: true

cache:
  enabled: true
  shared_cache: true
  ttl: 7200  # 2 hours

logging:
  level: "INFO"
  audit_file: "/var/log/aurelis/audit.log"
  error_file: "/var/log/aurelis/error.log"

enterprise:
  team_name: "Engineering"
  cost_tracking: true
  usage_analytics: true
```

#### 2. Multi-User Installation
```bash
# System-wide installation
sudo pip install aurelisai

# Create shared configuration
sudo mkdir -p /etc/aurelis
sudo cp enterprise.aurelis.yaml /etc/aurelis/config.yaml

# Set appropriate permissions
sudo chmod 644 /etc/aurelis/config.yaml
```

#### 3. Service Configuration
```bash
# Create systemd service (Linux)
sudo tee /etc/systemd/system/aurelis.service << EOF
[Unit]
Description=Aurelis AI Code Assistant
After=network.target

[Service]
Type=simple
User=aurelis
Group=aurelis
EnvironmentFile=/etc/aurelis/environment
ExecStart=/usr/local/bin/aurelis server
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable aurelis
sudo systemctl start aurelis
```

## 🎯 Next Steps

After successful installation:

1. **📖 Read the User Guide:** [CLI Reference](cli-reference.md) and [Shell Guide](shell-guide.md)
2. **🔧 Configure for your workflow:** [Configuration Guide](configuration.md)
3. **🚀 Start developing:** Launch `aurelis shell` for interactive development
4. **🏢 Enterprise setup:** Review [Enterprise Features](../architecture/enterprise.md)
5. **📊 Monitor usage:** Review [Performance Guide](../architecture/performance.md)

## 📞 Support

- **Documentation:** [Aurelis Docs](../README.md)
- **Issues:** [GitHub Issues](https://github.com/kanopus/aurelis/issues)
- **Enterprise Support:** contact@kanopus.org

---

**🎉 Welcome to Aurelis - Your Enterprise AI Code Assistant!**
