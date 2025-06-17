# Docker Development Guide

This guide provides comprehensive instructions for developing Aurelis using Docker containers, including development environments, multi-stage builds, and production-ready images.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Environment](#development-environment)
- [Docker Images](#docker-images)
- [Docker Compose](#docker-compose)
- [Multi-stage Builds](#multi-stage-builds)
- [Volume Management](#volume-management)
- [Networking](#networking)
- [Environment Configuration](#environment-configuration)
- [Debugging in Containers](#debugging-in-containers)
- [Performance Optimization](#performance-optimization)
- [Security Best Practices](#security-best-practices)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+
- Git
- Code editor with Docker support

### System Requirements
- **Memory**: 4GB+ available to Docker
- **Disk**: 10GB+ free space
- **CPU**: 2+ cores recommended

### Docker Configuration

```bash
# Verify Docker installation
docker --version
docker-compose --version

# Configure Docker daemon (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Test Docker installation
docker run hello-world
```

## Development Environment

### Quick Start

```bash
# Clone repository
git clone https://github.com/kanopusdev/aurelis.git
cd aurelis

# Start development environment
docker-compose -f docker-compose.dev.yml up --build
```

### Development Dockerfile

Create `Dockerfile.dev`:
```dockerfile
# Development Dockerfile for Aurelis
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    vim \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user
RUN groupadd -r aurelis && useradd -r -g aurelis aurelis

# Install Python dependencies
COPY requirements*.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements-dev.txt

# Copy source code
COPY . .

# Install Aurelis in development mode
RUN pip install -e .

# Change ownership
RUN chown -R aurelis:aurelis /app

# Switch to non-root user
USER aurelis

# Expose ports
EXPOSE 8080 5678

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["aurelis", "serve", "--dev", "--host", "0.0.0.0"]
```

### Production Dockerfile

Create `Dockerfile`:
```dockerfile
# Multi-stage production Dockerfile for Aurelis

# Build stage
FROM python:3.9-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Copy source code
COPY src/ src/
COPY setup.py README.md ./

# Build package
RUN pip install --user --no-warn-script-location .

# Production stage
FROM python:3.9-slim as production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH=/home/aurelis/.local/bin:$PATH

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r aurelis && useradd -r -g aurelis -d /home/aurelis aurelis

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder --chown=aurelis:aurelis /root/.local /home/aurelis/.local

# Copy application files
COPY --chown=aurelis:aurelis config/ config/
COPY --chown=aurelis:aurelis LICENSE .

# Switch to non-root user
USER aurelis

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Command
CMD ["aurelis", "serve", "--host", "0.0.0.0", "--workers", "4"]
```

## Docker Compose

### Development Compose File

Create `docker-compose.dev.yml`:
```yaml
version: '3.8'

services:
  aurelis:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: aurelis-dev
    ports:
      - "8080:8080"
      - "5678:5678"  # Debug port
    volumes:
      - .:/app
      - /app/venv  # Exclude virtual environment
      - aurelis-cache:/app/cache
    environment:
      - AURELIS_ENV=development
      - AURELIS_DEBUG=true
      - AURELIS_LOG_LEVEL=DEBUG
      - DATABASE_URL=postgresql://aurelius:development@postgres:5432/aurelis_dev
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
      - elasticsearch
    networks:
      - aurelis-network
    restart: unless-stopped
    stdin_open: true
    tty: true

  postgres:
    image: postgres:14-alpine
    container_name: aurelis-postgres
    environment:
      POSTGRES_DB: aurelis_dev
      POSTGRES_USER: aurelius
      POSTGRES_PASSWORD: development
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - aurelis-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: aurelis-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - aurelis-network
    restart: unless-stopped
    command: redis-server --appendonly yes

  elasticsearch:
    image: elasticsearch:8.5.0
    container_name: aurelis-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    networks:
      - aurelis-network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: aurelis-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/dev.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - aurelis
    networks:
      - aurelis-network
    restart: unless-stopped

  adminer:
    image: adminer:latest
    container_name: aurelis-adminer
    ports:
      - "8081:8080"
    depends_on:
      - postgres
    networks:
      - aurelis-network
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:
  elasticsearch-data:
  aurelis-cache:

networks:
  aurelis-network:
    driver: bridge
```

### Production Compose File

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  aurelis:
    build:
      context: .
      dockerfile: Dockerfile
    image: aurelis:latest
    container_name: aurelis-prod
    ports:
      - "8080:8080"
    environment:
      - AURELIS_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - aurelis-logs:/app/logs
      - aurelis-cache:/app/cache
    networks:
      - aurelis-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  nginx:
    image: nginx:alpine
    container_name: aurelis-nginx-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
      - aurelis-static:/var/www/static:ro
    depends_on:
      - aurelis
    networks:
      - aurelis-network
    restart: unless-stopped

volumes:
  aurelis-logs:
  aurelis-cache:
  aurelis-static:

networks:
  aurelis-network:
    driver: bridge
```

### Testing Compose File

Create `docker-compose.test.yml`:
```yaml
version: '3.8'

services:
  aurelis-test:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: aurelis-test
    environment:
      - AURELIS_ENV=test
      - DATABASE_URL=postgresql://aurelius:test@postgres-test:5432/aurelis_test
    volumes:
      - .:/app
      - test-cache:/app/cache
    depends_on:
      - postgres-test
      - redis-test
    networks:
      - test-network
    command: ["pytest", "tests/", "--cov=aurelis", "--cov-report=xml"]

  postgres-test:
    image: postgres:14-alpine
    container_name: aurelis-postgres-test
    environment:
      POSTGRES_DB: aurelis_test
      POSTGRES_USER: aurelius
      POSTGRES_PASSWORD: test
    volumes:
      - postgres-test-data:/var/lib/postgresql/data
    networks:
      - test-network
    tmpfs:
      - /var/lib/postgresql/data

  redis-test:
    image: redis:7-alpine
    container_name: aurelis-redis-test
    networks:
      - test-network
    tmpfs:
      - /data

volumes:
  postgres-test-data:
  test-cache:

networks:
  test-network:
    driver: bridge
```

## Multi-stage Builds

### Optimized Multi-stage Dockerfile

```dockerfile
# Optimized multi-stage build for minimal production image

# Base stage with common dependencies
FROM python:3.9-slim as base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependencies stage
FROM base as dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Development stage
FROM dependencies as development
COPY requirements-dev.txt .
RUN pip install --user -r requirements-dev.txt
COPY . .
RUN pip install --user -e .
CMD ["aurelis", "serve", "--dev", "--host", "0.0.0.0"]

# Test stage
FROM development as test
RUN pytest tests/ --cov=aurelis
CMD ["pytest", "tests/"]

# Build stage
FROM dependencies as build
COPY src/ src/
COPY setup.py README.md ./
RUN pip install --user .

# Production stage
FROM base as production
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r aurelis \
    && useradd -r -g aurelis -d /home/aurelis aurelis

WORKDIR /app
COPY --from=build --chown=aurelis:aurelis /root/.local /home/aurelis/.local
COPY --chown=aurelis:aurelis config/ config/

USER aurelis
ENV PATH=/home/aurelis/.local/bin:$PATH

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["aurelis", "serve", "--host", "0.0.0.0"]
```

### Build Targets

```bash
# Build development image
docker build --target development -t aurelis:dev .

# Build test image
docker build --target test -t aurelis:test .

# Build production image
docker build --target production -t aurelis:prod .

# Build with build arguments
docker build --build-arg PYTHON_VERSION=3.9 --target production -t aurelis:prod .
```

## Volume Management

### Development Volumes

```yaml
# Development volume configuration
volumes:
  # Source code volume (bind mount)
  - .:/app
  
  # Named volume for dependencies (faster)
  - node-modules:/app/node_modules
  - python-packages:/app/venv
  
  # Cache volumes
  - aurelis-cache:/app/cache
  - pip-cache:/root/.cache/pip
  
  # Database volumes
  - postgres-data:/var/lib/postgresql/data
  - redis-data:/data
```

### Volume Backup and Restore

```bash
# Backup volume
docker run --rm -v aurelis_postgres-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v aurelis_postgres-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /data

# Copy files from container
docker cp aurelis-dev:/app/logs ./local-logs/

# Copy files to container
docker cp ./config aurelis-dev:/app/config
```

## Networking

### Custom Networks

```yaml
networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
  
  backend:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.21.0.0/16
```

### Service Communication

```yaml
services:
  aurelis:
    networks:
      - frontend
      - backend
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - REDIS_URL=redis://redis:6379/0
  
  postgres:
    networks:
      - backend
  
  nginx:
    networks:
      - frontend
```

### External Access

```bash
# Access service from host
curl http://localhost:8080/health

# Access service from another container
docker exec -it aurelis-dev curl http://aurelis:8080/health

# Port forwarding
docker port aurelis-dev 8080
```

## Environment Configuration

### Environment Files

Create `.env.docker`:
```bash
# Docker environment configuration
COMPOSE_PROJECT_NAME=aurelis
COMPOSE_FILE=docker-compose.dev.yml

# Database
POSTGRES_DB=aurelis_dev
POSTGRES_USER=aurelius
POSTGRES_PASSWORD=development

# Application
AURELIS_ENV=development
AURELIS_DEBUG=true
AURELIS_LOG_LEVEL=DEBUG

# External services
REDIS_URL=redis://redis:6379/0
ELASTICSEARCH_URL=http://elasticsearch:9200

# Volumes
POSTGRES_DATA_PATH=./data/postgres
REDIS_DATA_PATH=./data/redis
```

### Environment Variable Injection

```yaml
# Environment variable sources
environment:
  # Direct assignment
  - AURELIS_ENV=development
  
  # From .env file
  - DATABASE_URL=${DATABASE_URL}
  
  # From external file
env_file:
  - .env.docker
  - .env.secrets
```

### Secrets Management

```yaml
# Using Docker secrets
secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true

services:
  aurelis:
    secrets:
      - db_password
      - api_key
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
```

## Debugging in Containers

### Remote Debugging Setup

```python
# Add to your application for remote debugging
import debugpy

if os.getenv('AURELIS_DEBUG') == 'true':
    debugpy.listen(("0.0.0.0", 5678))
    print("Waiting for debugger attach...")
    debugpy.wait_for_client()
```

### VS Code Debug Configuration

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Docker: Attach to Aurelis",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}/src",
          "remoteRoot": "/app/src"
        }
      ],
      "justMyCode": false
    }
  ]
}
```

### Interactive Debugging

```bash
# Attach to running container
docker exec -it aurelis-dev bash

# Run interactive Python shell
docker exec -it aurelis-dev aurelis shell

# Run debugger
docker exec -it aurelis-dev python -m pdb -m aurelis.cli.main serve --dev
```

### Log Management

```yaml
# Logging configuration
services:
  aurelis:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
        labels: "service,environment"
```

```bash
# View logs
docker logs aurelis-dev
docker logs -f aurelis-dev --tail 100

# View logs from compose
docker-compose logs aurelis
docker-compose logs -f --tail 100
```

## Performance Optimization

### Image Optimization

```dockerfile
# Optimize image size
FROM python:3.9-alpine as base

# Use multi-stage builds
FROM python:3.9-slim as builder
# Build dependencies
FROM python:3.9-alpine as production

# Minimize layers
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*

# Use .dockerignore
# Add .dockerignore file
```

Create `.dockerignore`:
```
# Version control
.git
.gitignore
.github

# Development files
.vscode
.idea
*.swp
*.swo

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
.pytest_cache
.coverage
htmlcov

# Dependencies
node_modules
venv
env

# Documentation
docs
*.md
!README.md

# Test files
tests
test_*

# Build artifacts
build
dist
*.egg-info

# OS
.DS_Store
Thumbs.db

# Temporary files
tmp
temp
*.tmp
*.log
```

### Resource Limits

```yaml
# Resource constraints
services:
  aurelis:
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    
    # Memory swappiness
    sysctls:
      - vm.swappiness=1
    
    # Ulimits
    ulimits:
      nproc: 65535
      nofile:
        soft: 65535
        hard: 65535
```

### Caching Strategies

```dockerfile
# Layer caching optimization
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code last
COPY src/ src/
```

```yaml
# Volume caching
volumes:
  - pip-cache:/root/.cache/pip
  - ./src:/app/src:cached
```

## Security Best Practices

### User Management

```dockerfile
# Create non-root user
RUN groupadd -r aurelis && useradd -r -g aurelis aurelis

# Set ownership
COPY --chown=aurelis:aurelis . /app

# Switch to non-root user
USER aurelis
```

### Secrets and Credentials

```bash
# Use Docker secrets
echo "my-secret-password" | docker secret create db_password -

# Use environment variables for non-sensitive config
# Use secrets/files for sensitive data
```

### Network Security

```yaml
# Internal networks
networks:
  backend:
    driver: bridge
    internal: true  # No external access

# Limit exposed ports
ports:
  - "127.0.0.1:8080:8080"  # Bind to localhost only
```

### Image Security

```dockerfile
# Use specific tags, not 'latest'
FROM python:3.9.15-slim

# Scan for vulnerabilities
RUN apt-get update && apt-get upgrade -y

# Remove unnecessary packages
RUN apt-get autoremove -y && apt-get clean
```

### Security Scanning

```bash
# Scan images for vulnerabilities
docker scan aurelis:latest

# Use security linting
hadolint Dockerfile

# Container security
docker run --security-opt no-new-privileges:true aurelis:latest
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/docker.yml`:
```yaml
name: Docker Build and Push

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run tests
      run: |
        docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
        docker-compose -f docker-compose.test.yml down

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push
      uses: docker/build-push-action@v3
      with:
        context: .
        push: true
        tags: |
          ghcr.io/${{ github.repository }}:latest
          ghcr.io/${{ github.repository }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

### GitLab CI

Create `.gitlab-ci.yml`:
```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

services:
  - docker:20.10.16-dind

test:
  stage: test
  script:
    - docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    - docker-compose -f docker-compose.test.yml down

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - main
```

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
docker logs aurelis-dev

# Inspect container configuration
docker inspect aurelis-dev

# Check if ports are available
netstat -tulpn | grep 8080

# Verify image
docker images | grep aurelis
```

#### Permission Issues

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Container user issues
docker exec -it aurelis-dev whoami
docker exec -it aurelis-dev id

# Volume permission issues
docker exec -it aurelis-dev ls -la /app
```

#### Network Connectivity

```bash
# Test network connectivity
docker exec -it aurelis-dev ping postgres
docker exec -it aurelis-dev curl http://redis:6379

# Inspect networks
docker network ls
docker network inspect aurelis_aurelis-network

# Port binding issues
docker port aurelis-dev
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats aurelis-dev

# Check disk usage
docker system df
docker images
docker volume ls

# Clean up resources
docker system prune -a
docker volume prune
```

#### Database Connection Issues

```bash
# Check database container
docker logs aurelis-postgres

# Test database connection
docker exec -it aurelis-dev aurelis db status

# Manual database connection
docker exec -it aurelis-postgres psql -U aurelius -d aurelis_dev
```

### Debug Commands

```bash
# Container inspection
docker exec -it aurelis-dev bash
docker exec -it aurelis-dev ps aux
docker exec -it aurelis-dev netstat -tlnp

# Environment check
docker exec -it aurelis-dev env
docker exec -it aurelis-dev cat /etc/hosts

# File system check
docker exec -it aurelis-dev ls -la /app
docker exec -it aurelis-dev df -h
```

### Maintenance Tasks

```bash
# Update images
docker-compose pull
docker-compose up -d

# Rebuild images
docker-compose build --no-cache

# Clean up
docker-compose down -v
docker system prune -a

# Backup volumes
./scripts/backup-volumes.sh

# Health checks
docker-compose ps
docker-compose logs --tail 50
```

### Performance Monitoring

```bash
# Container metrics
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# System resources
docker system df
docker system events

# Application metrics
docker exec -it aurelis-dev aurelis metrics
```

This comprehensive Docker development guide provides everything needed to develop, test, and deploy Aurelis using containerized environments, from basic setup to advanced production configurations.
