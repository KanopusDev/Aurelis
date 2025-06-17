# Aurelis Deployment Guide

This section provides comprehensive deployment documentation for Aurelis in various environments.

## Deployment Options

### Development Environment
- **[Local Development](local-development.md)** - Setting up Aurelis for development
- **[IDE Integration](ide-integration.md)** - Integration with VS Code and other IDEs
- **[Docker Development](docker-development.md)** - Containerized development setup

### Production Environment
- **[Production Deployment](production-deployment.md)** - Enterprise production setup
- **[Container Deployment](container-deployment.md)** - Docker/Kubernetes deployment
- **[CI/CD Integration](cicd-integration.md)** - Automated deployment pipelines

### Cloud Deployment
- **[AWS Deployment](aws-deployment.md)** - Amazon Web Services setup
- **[Azure Deployment](azure-deployment.md)** - Microsoft Azure setup
- **[GCP Deployment](gcp-deployment.md)** - Google Cloud Platform setup

## Quick Start

### Prerequisites
- Python 3.8 or higher
- GitHub token with model access
- Internet connectivity for API access

### Installation

#### Via PyPI (Recommended)
```bash
pip install aurelisai
```

#### From Source
```bash
git clone https://github.com/kanopusdev/aurelis.git
cd aurelis
pip install -e .
```

### Configuration

1. **Set GitHub Token**:
```bash
export GITHUB_TOKEN="your_github_token_here"
```

2. **Initialize Project**:
```bash
aurelis init
```

3. **Verify Setup**:
```bash
aurelis models
```

## Environment Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GITHUB_TOKEN` | Yes | GitHub token for model access | None |
| `AURELIS_CONFIG` | No | Path to configuration file | `.aurelis.yaml` |
| `AURELIS_CACHE_DIR` | No | Cache directory path | `~/.aurelis/cache` |
| `AURELIS_LOG_LEVEL` | No | Logging level | `INFO` |
| `AURELIS_ENDPOINT` | No | Custom API endpoint | GitHub Models endpoint |

### Configuration File

Create `.aurelis.yaml` in your project root:

```yaml
# Aurelis Configuration
github_token: "${GITHUB_TOKEN}"

models:
  primary: "codestral-2501"
  fallback: "gpt-4o-mini"

analysis:
  max_file_size: "1MB"
  chunk_size: 3500
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
  ttl: 3600
  max_size: 1000

logging:
  level: "INFO"
  format: "structured"
  file: "aurelis.log"
```

## Docker Deployment

### Basic Docker Setup

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Install Aurelis
RUN pip install aurelisai

# Set environment variables
ENV GITHUB_TOKEN=""
ENV AURELIS_LOG_LEVEL=INFO

# Create app directory
WORKDIR /app

# Copy configuration
COPY .aurelis.yaml .

# Set entrypoint
ENTRYPOINT ["aurelis"]
CMD ["--help"]
```

**Build and Run**:
```bash
# Build image
docker build -t aurelis:latest .

# Run container
docker run -e GITHUB_TOKEN="your_token" aurelis:latest models
```

### Docker Compose

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  aurelis:
    build: .
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - AURELIS_LOG_LEVEL=INFO
    volumes:
      - ./src:/app/src:ro
      - ./cache:/app/.aurelis/cache
    networks:
      - aurelis-net

networks:
  aurelis-net:
    driver: bridge
```

## Kubernetes Deployment

### Basic Kubernetes Setup

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurelis
  labels:
    app: aurelis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aurelis
  template:
    metadata:
      labels:
        app: aurelis
    spec:
      containers:
      - name: aurelis
        image: aurelis:latest
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: aurelis-secrets
              key: github-token
        - name: AURELIS_LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: cache-volume
          mountPath: /app/.aurelis/cache
      volumes:
      - name: cache-volume
        emptyDir: {}
---
apiVersion: v1
kind: Secret
metadata:
  name: aurelis-secrets
type: Opaque
stringData:
  github-token: "your_github_token_here"
```

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: aurelis-service
spec:
  selector:
    app: aurelis
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

## Production Deployment

### System Requirements

**Minimum Requirements**:
- CPU: 1 core
- Memory: 512MB RAM
- Storage: 1GB free space
- Network: Outbound HTTPS access

**Recommended Requirements**:
- CPU: 2+ cores
- Memory: 2GB+ RAM
- Storage: 10GB+ free space
- Network: High-speed internet connection

### Production Configuration

**Production .aurelis.yaml**:
```yaml
github_token: "${GITHUB_TOKEN}"

models:
  primary: "codestral-2501"
  fallback: "gpt-4o-mini"

processing:
  max_retries: 5
  timeout: 120
  concurrent_requests: 10

security:
  audit_logging: true
  secure_token_storage: true

cache:
  enabled: true
  ttl: 7200  # 2 hours
  max_size: 5000

logging:
  level: "WARNING"
  format: "structured"
  file: "/var/log/aurelis/aurelis.log"
  rotation: "daily"
  retention: "30d"

monitoring:
  enabled: true
  metrics_endpoint: "http://prometheus:9090"
  health_check_interval: 30
```

### Systemd Service

**aurelis.service**:
```ini
[Unit]
Description=Aurelis AI Code Assistant
After=network.target

[Service]
Type=simple
User=aurelis
Group=aurelis
WorkingDirectory=/opt/aurelis
Environment=GITHUB_TOKEN=your_token_here
Environment=AURELIS_CONFIG=/etc/aurelis/config.yaml
ExecStart=/usr/local/bin/aurelis shell
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Install and Start**:
```bash
# Install service
sudo cp aurelis.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aurelis
sudo systemctl start aurelis

# Check status
sudo systemctl status aurelis
```

## CI/CD Integration

### GitHub Actions

**.github/workflows/aurelis.yml**:
```yaml
name: Aurelis Code Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  analyze:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Aurelis
      run: |
        pip install aurelisai
    
    - name: Initialize Aurelis
      run: |
        aurelis init --force
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Analyze Code
      run: |
        aurelis analyze src/ --format json --save-report analysis.json
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Upload Analysis Results
      uses: actions/upload-artifact@v3
      with:
        name: code-analysis
        path: analysis.json
```

### Jenkins Pipeline

**Jenkinsfile**:
```groovy
pipeline {
    agent any
    
    environment {
        GITHUB_TOKEN = credentials('github-token')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install aurelisai'
                sh 'aurelis init --force'
            }
        }
        
        stage('Analyze') {
            steps {
                sh 'aurelis analyze src/ --format json --save-report analysis.json'
            }
        }
        
        stage('Generate Docs') {
            steps {
                sh 'aurelis docs src/ --output docs/'
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '*.json, docs/**/*', fingerprint: true
        }
    }
}
```

## Monitoring & Logging

### Log Configuration

**Structured Logging Setup**:
```yaml
logging:
  level: "INFO"
  format: "structured"
  handlers:
    - type: "file"
      filename: "/var/log/aurelis/aurelis.log"
      rotation: "daily"
      retention: "30d"
    - type: "syslog"
      facility: "daemon"
    - type: "elasticsearch"
      host: "elasticsearch:9200"
      index: "aurelis-logs"
```

### Health Monitoring

**Health Check Script**:
```bash
#!/bin/bash
# aurelis-health-check.sh

# Check if Aurelis is responding
if aurelis models > /dev/null 2>&1; then
    echo "✓ Aurelis is healthy"
    exit 0
else
    echo "✗ Aurelis is unhealthy"
    exit 1
fi
```

### Prometheus Metrics

**Metrics Configuration**:
```yaml
monitoring:
  prometheus:
    enabled: true
    port: 9090
    metrics:
      - request_count
      - request_duration
      - model_usage
      - cache_hit_rate
      - error_rate
```

## Security Considerations

### Production Security

1. **Token Management**:
   - Use environment variables or secret management systems
   - Rotate tokens regularly
   - Monitor token usage

2. **Network Security**:
   - Use HTTPS for all API communications
   - Implement firewall rules for outbound access
   - Use VPN or private networks in enterprise environments

3. **Access Control**:
   - Run Aurelis with dedicated user account
   - Implement proper file permissions
   - Use container security best practices

4. **Audit Logging**:
   - Enable comprehensive audit logging
   - Monitor for unusual activity
   - Implement log retention policies

### Secret Management

**Using AWS Secrets Manager**:
```python
import boto3

def get_github_token():
    session = boto3.session.Session()
    client = session.client('secretsmanager', region_name='us-east-1')
    
    response = client.get_secret_value(SecretId='aurelis/github-token')
    return response['SecretString']
```

**Using Azure Key Vault**:
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_github_token():
    credential = DefaultAzureCredential()
    client = SecretClient(
        vault_url="https://aurelis.vault.azure.net/",
        credential=credential
    )
    
    secret = client.get_secret("github-token")
    return secret.value
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   ```bash
   # Verify token
   echo $GITHUB_TOKEN
   
   # Test token
   curl -H "Authorization: Bearer $GITHUB_TOKEN" \
        https://api.github.com/user
   ```

2. **Network Issues**:
   ```bash
   # Test connectivity
   aurelis models --debug
   
   # Check proxy settings
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   ```

3. **Configuration Issues**:
   ```bash
   # Validate configuration
   aurelis config
   
   # Reset configuration
   aurelis init --force
   ```

### Debug Mode

Enable debug logging for troubleshooting:
```bash
export AURELIS_LOG_LEVEL=DEBUG
aurelis models
```

## Performance Optimization

### Cache Optimization

1. **Increase Cache Size**:
```yaml
cache:
  max_size: 10000  # Increase for better hit rate
  ttl: 14400       # 4 hours
```

2. **Persistent Cache**:
```yaml
cache:
  backend: "redis"
  redis_url: "redis://localhost:6379/0"
```

### Model Selection Optimization

1. **Use Faster Models for Simple Tasks**:
```yaml
models:
  primary: "gpt-4o-mini"     # Faster for simple tasks
  complex: "gpt-4o"          # Use for complex reasoning
  code: "codestral-2501"     # Best for code generation
```

## Backup & Recovery

### Configuration Backup

```bash
# Backup configuration
cp .aurelis.yaml .aurelis.yaml.backup
tar -czf aurelis-config-$(date +%Y%m%d).tar.gz .aurelis.yaml

# Backup cache
tar -czf aurelis-cache-$(date +%Y%m%d).tar.gz ~/.aurelis/cache/
```

### Disaster Recovery

```bash
# Restore configuration
tar -xzf aurelis-config-20240101.tar.gz

# Restore cache
tar -xzf aurelis-cache-20240101.tar.gz -C ~/

# Verify restoration
aurelis config
aurelis models
```

## See Also

- [Production Deployment](production-deployment.md)
- [Container Deployment](container-deployment.md)
- [CI/CD Integration](cicd-integration.md)
- [Monitoring Guide](monitoring.md)
