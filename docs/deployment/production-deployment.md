# Production Deployment Guide

Complete guide for deploying Aurelis in production environments with enterprise-grade reliability and security.

## Pre-Deployment Checklist

### Security Requirements
- [ ] GitHub token with appropriate model access permissions
- [ ] Secure credential storage system (AWS Secrets Manager, Azure Key Vault, etc.)
- [ ] Network security policies for GitHub API access
- [ ] Audit logging and monitoring infrastructure
- [ ] SSL/TLS certificates for secure communications

### Infrastructure Requirements
- [ ] Python 3.8+ runtime environment
- [ ] Container orchestration (Kubernetes, Docker Swarm, etc.)
- [ ] Load balancing and high availability setup
- [ ] Persistent storage for cache and configuration
- [ ] Monitoring and alerting systems
- [ ] Backup and disaster recovery procedures

### Performance Requirements
- [ ] Network bandwidth for GitHub API calls
- [ ] CPU and memory sizing for concurrent requests
- [ ] Cache storage sizing and performance
- [ ] Request rate limiting and throttling
- [ ] Performance monitoring and optimization

## Production Architecture

### High-Level Architecture

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    │   (nginx/ALB)   │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐
                    │  Aurelis Pods   │
                    │ (3+ instances)  │
                    └─────────┬───────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
    ┌────────▼───────┐ ┌─────▼─────┐ ┌────────▼───────┐
    │  GitHub Models │ │   Cache   │ │   Config/      │
    │ (Azure AI Inf) │ │  (Redis)  │ │   Secrets      │
    └────────────────┘ └───────────┘ └────────────────┘
```

### Component Scaling

| Component | Min Instances | Recommended | Max Instances |
|-----------|---------------|-------------|---------------|
| Aurelis Pods | 2 | 3-5 | 10+ |
| Redis Cache | 1 | 3 (HA) | 5 |
| Load Balancer | 1 | 2 (HA) | 3 |

## Deployment Methods

### 1. Kubernetes Deployment

#### Production Deployment Manifest

```yaml
# aurelis-production.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aurelis-production
  labels:
    name: aurelis-production
    environment: production

---
apiVersion: v1
kind: Secret
metadata:
  name: aurelis-secrets
  namespace: aurelis-production
type: Opaque
data:
  github-token: <base64-encoded-token>

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: aurelis-config
  namespace: aurelis-production
data:
  config.yaml: |
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
      backend: "redis"
      redis_url: "redis://aurelis-redis:6379/0"
      ttl: 7200
      max_size: 10000
    
    logging:
      level: "INFO"
      format: "structured"
      handlers:
        - type: "stdout"
        - type: "file"
          filename: "/var/log/aurelis/aurelis.log"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurelis-deployment
  namespace: aurelis-production
  labels:
    app: aurelis
    version: v1.0.0
    environment: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: aurelis
  template:
    metadata:
      labels:
        app: aurelis
        version: v1.0.0
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: aurelis
        image: aurelis:v1.0.0-production
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: aurelis-secrets
              key: github-token
        - name: AURELIS_CONFIG
          value: "/etc/aurelis/config.yaml"
        - name: AURELIS_LOG_LEVEL
          value: "INFO"
        - name: AURELIS_ENVIRONMENT
          value: "production"
        volumeMounts:
        - name: config-volume
          mountPath: /etc/aurelis
          readOnly: true
        - name: log-volume
          mountPath: /var/log/aurelis
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      volumes:
      - name: config-volume
        configMap:
          name: aurelis-config
      - name: log-volume
        emptyDir: {}
      nodeSelector:
        aurelis-node: "true"
      tolerations:
      - key: "aurelis-workload"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"

---
apiVersion: v1
kind: Service
metadata:
  name: aurelis-service
  namespace: aurelis-production
  labels:
    app: aurelis
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: aurelis

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aurelis-ingress
  namespace: aurelis-production
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - aurelis.yourdomain.com
    secretName: aurelis-tls
  rules:
  - host: aurelis.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: aurelis-service
            port:
              number: 80

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurelis-redis
  namespace: aurelis-production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: aurelis-redis
  template:
    metadata:
      labels:
        app: aurelis-redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: aurelis-redis-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: aurelis-redis
  namespace: aurelis-production
spec:
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: aurelis-redis

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: aurelis-redis-pvc
  namespace: aurelis-production
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

#### Deployment Commands

```bash
# Apply production deployment
kubectl apply -f aurelis-production.yaml

# Verify deployment
kubectl get pods -n aurelis-production
kubectl get services -n aurelis-production
kubectl get ingress -n aurelis-production

# Check logs
kubectl logs -f deployment/aurelis-deployment -n aurelis-production

# Scale deployment
kubectl scale deployment aurelis-deployment --replicas=5 -n aurelis-production
```

### 2. Docker Swarm Deployment

#### Production Stack File

```yaml
# aurelis-stack.yml
version: '3.8'

services:
  aurelis:
    image: aurelis:v1.0.0-production
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
      placement:
        constraints:
          - node.role == worker
          - node.labels.aurelis == true
    environment:
      - GITHUB_TOKEN_FILE=/run/secrets/github_token
      - AURELIS_CONFIG=/etc/aurelis/config.yaml
      - AURELIS_LOG_LEVEL=INFO
      - AURELIS_ENVIRONMENT=production
    secrets:
      - github_token
    configs:
      - source: aurelis_config
        target: /etc/aurelis/config.yaml
    volumes:
      - aurelis_logs:/var/log/aurelis
    ports:
      - "8080:8080"
    networks:
      - aurelis_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  redis:
    image: redis:7-alpine
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
      placement:
        constraints:
          - node.role == worker
    volumes:
      - aurelis_redis_data:/data
    networks:
      - aurelis_network
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    ports:
      - "80:80"
      - "443:443"
    configs:
      - source: nginx_config
        target: /etc/nginx/nginx.conf
    volumes:
      - aurelis_ssl_certs:/etc/ssl/certs
    networks:
      - aurelis_network
    depends_on:
      - aurelis

networks:
  aurelis_network:
    driver: overlay
    attachable: true

volumes:
  aurelis_logs:
    driver: local
  aurelis_redis_data:
    driver: local
  aurelis_ssl_certs:
    driver: local

secrets:
  github_token:
    external: true
    name: aurelis_github_token

configs:
  aurelis_config:
    external: true
    name: aurelis_config_v1
  nginx_config:
    external: true
    name: aurelis_nginx_config_v1
```

#### Deployment Commands

```bash
# Create secrets
echo "your_github_token" | docker secret create aurelis_github_token -

# Create configs
docker config create aurelis_config_v1 config.yaml
docker config create aurelis_nginx_config_v1 nginx.conf

# Deploy stack
docker stack deploy -c aurelis-stack.yml aurelis

# Monitor deployment
docker stack services aurelis
docker stack ps aurelis

# Update service
docker service update --image aurelis:v1.0.1-production aurelis_aurelis
```

## Environment Configuration

### Production Environment Variables

```bash
# Core Configuration
GITHUB_TOKEN="your_production_github_token"
AURELIS_CONFIG="/etc/aurelis/production.yaml"
AURELIS_LOG_LEVEL="INFO"
AURELIS_ENVIRONMENT="production"

# Performance Tuning
AURELIS_MAX_WORKERS="10"
AURELIUS_WORKER_TIMEOUT="120"
AURELIS_MAX_REQUESTS_PER_WORKER="1000"

# Security
AURELIS_SECURE_MODE="true"
AURELIS_AUDIT_LOGGING="true"
AURELIS_SSL_REQUIRED="true"

# Monitoring
AURELIS_METRICS_ENABLED="true"
AURELIS_HEALTH_CHECK_INTERVAL="30"
AURELIS_PROMETHEUS_PORT="9090"

# Cache Configuration
AURELIS_CACHE_BACKEND="redis"
AURELIS_REDIS_URL="redis://aurelis-redis:6379/0"
AURELIS_CACHE_TTL="7200"
AURELIS_CACHE_MAX_SIZE="10000"

# Database (if needed)
AURELIS_DB_URL="postgresql://user:pass@db:5432/aurelis"
AURELIS_DB_POOL_SIZE="20"
AURELIS_DB_MAX_OVERFLOW="30"
```

### Production Configuration File

```yaml
# production.yaml
environment: production

github_token: "${GITHUB_TOKEN}"

models:
  primary: "codestral-2501"
  fallback: "gpt-4o-mini"
  preferences:
    code_generation: "codestral-2501"
    documentation: "cohere-command-r"
    reasoning: "gpt-4o"
    performance: "gpt-4o"

processing:
  max_retries: 5
  timeout: 120
  concurrent_requests: 10
  batch_size: 50
  rate_limit:
    requests_per_minute: 500
    burst_limit: 100

security:
  audit_logging: true
  secure_token_storage: true
  ssl_required: true
  cors_origins:
    - "https://aurelis.yourdomain.com"
    - "https://app.yourdomain.com"
  api_key_rotation: true
  session_timeout: 3600

cache:
  enabled: true
  backend: "redis"
  redis_url: "${AURELIS_REDIS_URL}"
  ttl: 7200
  max_size: 10000
  compression: true
  encryption: true

logging:
  level: "INFO"
  format: "structured"
  correlation_ids: true
  handlers:
    - type: "stdout"
      level: "INFO"
    - type: "file"
      filename: "/var/log/aurelis/aurelis.log"
      rotation: "daily"
      retention: "30d"
      level: "INFO"
    - type: "elasticsearch"
      host: "elasticsearch:9200"
      index: "aurelis-logs"
      level: "WARNING"
    - type: "syslog"
      facility: "daemon"
      level: "ERROR"

monitoring:
  enabled: true
  metrics:
    prometheus:
      enabled: true
      port: 9090
      path: "/metrics"
    health_checks:
      enabled: true
      port: 8080
      paths:
        health: "/health"
        ready: "/ready"
        live: "/live"
  tracing:
    enabled: true
    jaeger_endpoint: "http://jaeger:14268/api/traces"

database:
  url: "${AURELIS_DB_URL}"
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600
  echo: false

features:
  advanced_analytics: true
  custom_models: true
  batch_processing: true
  webhook_support: true
  api_versioning: true
```

## Security Configuration

### TLS/SSL Setup

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream aurelis_backend {
        least_conn;
        server aurelis:8080 max_fails=3 fail_timeout=30s;
        server aurelis:8080 max_fails=3 fail_timeout=30s backup;
    }

    server {
        listen 80;
        server_name aurelis.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name aurelis.yourdomain.com;

        ssl_certificate /etc/ssl/certs/aurelis.crt;
        ssl_certificate_key /etc/ssl/private/aurelis.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' https:; script-src 'self'" always;

        # Rate limiting
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
        limit_req zone=api burst=20 nodelay;

        location / {
            proxy_pass http://aurelis_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 60s;
            
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }

        location /health {
            proxy_pass http://aurelis_backend/health;
            access_log off;
        }
    }
}
```

### Secret Management

#### AWS Secrets Manager Integration

```python
# secrets_aws.py
import boto3
import json
from botocore.exceptions import ClientError

def get_github_token():
    """Retrieve GitHub token from AWS Secrets Manager."""
    
    secret_name = "aurelis/production/github-token"
    region_name = "us-east-1"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret['github_token']
    except ClientError as e:
        raise Exception(f"Failed to retrieve secret: {e}")

def rotate_github_token(new_token: str):
    """Rotate GitHub token in AWS Secrets Manager."""
    
    secret_name = "aurelis/production/github-token"
    region_name = "us-east-1"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        secret_value = json.dumps({'github_token': new_token})
        response = client.update_secret(
            SecretId=secret_name,
            SecretString=secret_value
        )
        return response['VersionId']
    except ClientError as e:
        raise Exception(f"Failed to rotate secret: {e}")
```

#### Azure Key Vault Integration

```python
# secrets_azure.py
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_github_token():
    """Retrieve GitHub token from Azure Key Vault."""
    
    vault_url = "https://aurelis-keyvault.vault.azure.net/"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    
    try:
        secret = client.get_secret("github-token")
        return secret.value
    except Exception as e:
        raise Exception(f"Failed to retrieve secret: {e}")

def rotate_github_token(new_token: str):
    """Rotate GitHub token in Azure Key Vault."""
    
    vault_url = "https://aurelis-keyvault.vault.azure.net/"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    
    try:
        secret = client.set_secret("github-token", new_token)
        return secret.id
    except Exception as e:
        raise Exception(f"Failed to rotate secret: {e}")
```

## Monitoring & Observability

### Health Checks

```python
# health.py
from fastapi import FastAPI, HTTPException
from datetime import datetime
import asyncio

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": "production"
    }
    
    # Check critical dependencies
    checks = {
        "github_api": await check_github_api(),
        "cache": await check_cache(),
        "database": await check_database()
    }
    
    if not all(checks.values()):
        health_status["status"] = "unhealthy"
        health_status["checks"] = checks
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    
    # Check if service is ready to handle requests
    if not await is_service_ready():
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "ready"}

@app.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes."""
    
    # Check if service is alive
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

async def check_github_api():
    """Check GitHub API connectivity."""
    try:
        # Implementation to test GitHub API
        return True
    except:
        return False

async def check_cache():
    """Check cache connectivity."""
    try:
        # Implementation to test cache
        return True
    except:
        return False

async def check_database():
    """Check database connectivity."""
    try:
        # Implementation to test database
        return True
    except:
        return False

async def is_service_ready():
    """Check if service is ready."""
    # Implementation to check service readiness
    return True
```

### Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Define metrics
REQUEST_COUNT = Counter(
    'aurelis_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'aurelis_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

MODEL_REQUESTS = Counter(
    'aurelis_model_requests_total',
    'Total model requests',
    ['model', 'task_type', 'status']
)

CACHE_HIT_RATE = Gauge(
    'aurelis_cache_hit_rate',
    'Cache hit rate percentage'
)

ACTIVE_CONNECTIONS = Gauge(
    'aurelis_active_connections',
    'Number of active connections'
)

def start_metrics_server(port=9090):
    """Start Prometheus metrics server."""
    start_http_server(port)

def record_request(method, endpoint, status, duration):
    """Record request metrics."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

def record_model_request(model, task_type, status):
    """Record model request metrics."""
    MODEL_REQUESTS.labels(model=model, task_type=task_type, status=status).inc()

def update_cache_hit_rate(rate):
    """Update cache hit rate."""
    CACHE_HIT_RATE.set(rate)

def update_active_connections(count):
    """Update active connections count."""
    ACTIVE_CONNECTIONS.set(count)
```

## Deployment Automation

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
    
    - name: Setup Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=tag
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.production
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v1
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Deploy to Kubernetes
      run: |
        # Update image tag in deployment
        kubectl set image deployment/aurelis-deployment aurelis=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.ref_name }} -n aurelis-production
        
        # Wait for rollout to complete
        kubectl rollout status deployment/aurelis-deployment -n aurelis-production --timeout=300s
        
        # Verify deployment
        kubectl get pods -n aurelis-production
    
    - name: Run post-deployment tests
      run: |
        # Wait for pods to be ready
        sleep 30
        
        # Health check
        kubectl exec -n aurelis-production deployment/aurelis-deployment -- curl -f http://localhost:8080/health
        
        # Integration tests
        pytest tests/integration/ --production
    
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'Aurelis production deployment completed'
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Production Dockerfile

```dockerfile
# Dockerfile.production
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r aurelis \
    && useradd -r -g aurelis aurelis

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=aurelis:aurelis . /app
WORKDIR /app

# Create required directories
RUN mkdir -p /var/log/aurelis \
    && chown -R aurelis:aurelis /var/log/aurelis \
    && chmod 755 /var/log/aurelis

# Security hardening
RUN chmod +x /app/entrypoint.sh \
    && chown aurelis:aurelis /app/entrypoint.sh

# Switch to non-root user
USER aurelis

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["aurelis", "server", "--host", "0.0.0.0", "--port", "8080"]
```

### Production Entrypoint Script

```bash
#!/bin/bash
# entrypoint.sh

set -e

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ENTRYPOINT] $1"
}

# Function to wait for dependencies
wait_for_dependency() {
    local host=$1
    local port=$2
    local service=$3
    
    log "Waiting for $service at $host:$port..."
    
    while ! nc -z "$host" "$port"; do
        log "Waiting for $service to be ready..."
        sleep 2
    done
    
    log "$service is ready!"
}

# Environment validation
if [ -z "$GITHUB_TOKEN" ]; then
    log "ERROR: GITHUB_TOKEN environment variable is required"
    exit 1
fi

# Wait for dependencies
if [ "$AURELIS_CACHE_BACKEND" = "redis" ]; then
    REDIS_HOST=$(echo "$AURELIS_REDIS_URL" | sed 's/redis:\/\/\([^:]*\):.*/\1/')
    REDIS_PORT=$(echo "$AURELIS_REDIS_URL" | sed 's/.*:\([0-9]*\)\/.*/\1/')
    wait_for_dependency "$REDIS_HOST" "$REDIS_PORT" "Redis"
fi

# Database migration (if needed)
if [ -n "$AURELIS_DB_URL" ]; then
    log "Running database migrations..."
    aurelis db migrate
fi

# Cache warmup (if needed)
if [ "$AURELIS_CACHE_WARMUP" = "true" ]; then
    log "Warming up cache..."
    aurelis cache warmup
fi

# Start application
log "Starting Aurelis application..."
exec "$@"
```

## Backup & Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/aurelis"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration
kubectl get configmap aurelis-config -n aurelis-production -o yaml > "$BACKUP_DIR/config_$DATE.yaml"

# Backup secrets (encrypted)
kubectl get secret aurelis-secrets -n aurelis-production -o yaml > "$BACKUP_DIR/secrets_$DATE.yaml.enc"

# Backup cache data
kubectl exec -n aurelis-production deployment/aurelis-redis -- redis-cli BGSAVE
kubectl cp aurelis-production/$(kubectl get pods -n aurelis-production -l app=aurelis-redis -o jsonpath='{.items[0].metadata.name}'):/data/dump.rdb "$BACKUP_DIR/cache_$DATE.rdb"

# Backup logs
kubectl logs deployment/aurelis-deployment -n aurelis-production --since=24h > "$BACKUP_DIR/logs_$DATE.log"

# Cleanup old backups
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

# Verify backup
if [ -f "$BACKUP_DIR/config_$DATE.yaml" ]; then
    echo "Backup completed successfully: $DATE"
else
    echo "Backup failed: $DATE"
    exit 1
fi
```

### Disaster Recovery

```bash
#!/bin/bash
# disaster_recovery.sh

BACKUP_DIR="/backup/aurelis"
RESTORE_DATE=${1:-"latest"}

if [ "$RESTORE_DATE" = "latest" ]; then
    CONFIG_FILE=$(ls -t "$BACKUP_DIR"/config_*.yaml | head -n1)
    CACHE_FILE=$(ls -t "$BACKUP_DIR"/cache_*.rdb | head -n1)
else
    CONFIG_FILE="$BACKUP_DIR/config_$RESTORE_DATE.yaml"
    CACHE_FILE="$BACKUP_DIR/cache_$RESTORE_DATE.rdb"
fi

echo "Restoring from backup: $RESTORE_DATE"

# Restore configuration
kubectl apply -f "$CONFIG_FILE"

# Restore cache data
kubectl cp "$CACHE_FILE" aurelis-production/$(kubectl get pods -n aurelis-production -l app=aurelis-redis -o jsonpath='{.items[0].metadata.name}'):/data/dump.rdb

# Restart Redis to load data
kubectl rollout restart deployment/aurelis-redis -n aurelis-production

# Restart Aurelis deployment
kubectl rollout restart deployment/aurelis-deployment -n aurelis-production

# Wait for deployment to be ready
kubectl rollout status deployment/aurelis-deployment -n aurelis-production --timeout=300s

# Verify recovery
kubectl exec -n aurelis-production deployment/aurelis-deployment -- curl -f http://localhost:8080/health

echo "Disaster recovery completed successfully"
```

## Performance Optimization

### Resource Sizing Guidelines

| Load Level | CPU | Memory | Instances | Cache Size |
|------------|-----|--------|-----------|------------|
| Light (< 100 req/min) | 0.5 CPU | 512MB | 2 | 1GB |
| Medium (100-500 req/min) | 1 CPU | 1GB | 3 | 2GB |
| Heavy (500-1000 req/min) | 2 CPU | 2GB | 5 | 4GB |
| Enterprise (> 1000 req/min) | 4 CPU | 4GB | 10+ | 8GB+ |

### Autoscaling Configuration

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aurelis-hpa
  namespace: aurelis-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aurelis-deployment
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: aurelis_requests_per_second
      target:
        type: AverageValue
        averageValue: "10"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
```

## Troubleshooting

### Common Production Issues

#### 1. High Memory Usage

```bash
# Check memory usage
kubectl top pods -n aurelis-production

# Check memory limits
kubectl describe pod <pod-name> -n aurelis-production

# Adjust memory limits
kubectl patch deployment aurelis-deployment -n aurelis-production -p '{"spec":{"template":{"spec":{"containers":[{"name":"aurelis","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
```

#### 2. GitHub API Rate Limiting

```bash
# Check rate limit status
kubectl logs deployment/aurelis-deployment -n aurelis-production | grep "rate.limit"

# Implement exponential backoff
# Update configuration to increase retry delays
```

#### 3. Cache Performance Issues

```bash
# Check Redis performance
kubectl exec -n aurelis-production deployment/aurelis-redis -- redis-cli info stats

# Monitor cache hit rates
kubectl exec -n aurelis-production deployment/aurelis-redis -- redis-cli info keyspace

# Increase cache size if needed
kubectl patch deployment aurelis-redis -n aurelis-production -p '{"spec":{"template":{"spec":{"containers":[{"name":"redis","args":["redis-server","--maxmemory","2gb"]}]}}}}'
```

#### 4. Network Connectivity Issues

```bash
# Test GitHub API connectivity
kubectl exec -n aurelis-production deployment/aurelis-deployment -- curl -I https://api.github.com

# Check DNS resolution
kubectl exec -n aurelis-production deployment/aurelis-deployment -- nslookup api.github.com

# Verify network policies
kubectl get networkpolicies -n aurelis-production
```

### Emergency Procedures

#### 1. Emergency Scale Down

```bash
# Scale to minimum replicas
kubectl scale deployment aurelis-deployment --replicas=1 -n aurelis-production

# Stop processing
kubectl patch deployment aurelis-deployment -n aurelis-production -p '{"spec":{"template":{"spec":{"containers":[{"name":"aurelis","env":[{"name":"AURELIS_MAINTENANCE_MODE","value":"true"}]}]}}}}'
```

#### 2. Emergency Rollback

```bash
# Check rollout history
kubectl rollout history deployment/aurelis-deployment -n aurelis-production

# Rollback to previous version
kubectl rollout undo deployment/aurelis-deployment -n aurelis-production

# Rollback to specific revision
kubectl rollout undo deployment/aurelis-deployment --to-revision=2 -n aurelis-production
```

#### 3. Emergency Maintenance

```bash
# Enable maintenance mode
kubectl patch configmap aurelis-config -n aurelis-production -p '{"data":{"maintenance_mode":"true"}}'

# Restart deployment to pick up config
kubectl rollout restart deployment/aurelis-deployment -n aurelis-production

# Disable maintenance mode
kubectl patch configmap aurelis-config -n aurelis-production -p '{"data":{"maintenance_mode":"false"}}'
```

## See Also

- [Container Deployment Guide](container-deployment.md)
- [Monitoring Guide](monitoring.md)
- [Security Best Practices](security.md)
- [Performance Tuning](performance.md)
