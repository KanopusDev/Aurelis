# Container Deployment Guide

Enterprise-grade containerized deployment options for Aurelis with Docker, Kubernetes, and orchestration platforms.

## 📋 Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Docker Compose](#docker-compose)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Helm Charts](#helm-charts)
5. [Container Security](#container-security)
6. [Performance Optimization](#performance-optimization)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)

## 🐳 Docker Deployment

### Production Dockerfile

```dockerfile
# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set build arguments
ARG AURELIS_VERSION=latest
ARG BUILD_DATE
ARG VCS_REF

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set metadata labels
LABEL org.opencontainers.image.title="Aurelis AI Code Assistant" \
      org.opencontainers.image.description="Enterprise AI-powered code analysis and generation platform" \
      org.opencontainers.image.version="${AURELIS_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/aurelis/aurelis" \
      org.opencontainers.image.documentation="https://docs.aurelis.dev" \
      org.opencontainers.image.vendor="Aurelis Technologies"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r aurelis \
    && useradd -r -g aurelis -s /bin/bash aurelis

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=aurelis:aurelis . /app

# Create required directories
RUN mkdir -p /var/log/aurelis /app/.aurelis/cache /app/data \
    && chown -R aurelis:aurelis /var/log/aurelis /app/.aurelis /app/data \
    && chmod 755 /var/log/aurelis /app/.aurelis /app/data

# Copy entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh \
    && chown aurelis:aurelis /usr/local/bin/entrypoint.sh

# Switch to non-root user
USER aurelis

# Set environment variables
ENV AURELIS_CONFIG=/app/.aurelis.yaml \
    AURELIS_LOG_LEVEL=INFO \
    AURELIS_CACHE_DIR=/app/.aurelis/cache \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080 9090

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["aurelis", "server", "--host", "0.0.0.0", "--port", "8080"]
```

### Entrypoint Script

```bash
#!/bin/bash
# entrypoint.sh - Production container entrypoint

set -euo pipefail

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ENTRYPOINT] $*" >&2
}

# Error handling
trap 'log "ERROR: Script failed on line $LINENO"' ERR

# Environment validation
validate_environment() {
    log "Validating environment..."
    
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        log "ERROR: GITHUB_TOKEN environment variable is required"
        exit 1
    fi
    
    if [[ ! -f "${AURELIS_CONFIG:-/app/.aurelis.yaml}" ]]; then
        log "WARNING: Configuration file not found, using defaults"
    fi
}

# Wait for dependencies
wait_for_service() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local timeout="${4:-60}"
    
    log "Waiting for $service_name at $host:$port (timeout: ${timeout}s)..."
    
    local count=0
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [[ $count -ge $timeout ]]; then
            log "ERROR: Timeout waiting for $service_name"
            exit 1
        fi
        sleep 1
        ((count++))
    done
    
    log "$service_name is ready!"
}

# Initialize application
initialize_app() {
    log "Initializing Aurelis..."
    
    # Create necessary directories
    mkdir -p /app/.aurelis/cache /var/log/aurelis
    
    # Initialize configuration if needed
    if [[ ! -f "${AURELIS_CONFIG}" ]]; then
        log "Creating default configuration..."
        cat > "${AURELIS_CONFIG}" << EOF
github_token: "\${GITHUB_TOKEN}"
models:
  primary: "codestral-2501"
  fallback: "gpt-4o-mini"
cache:
  enabled: true
  backend: "\${AURELIS_CACHE_BACKEND:-memory}"
  ttl: 3600
logging:
  level: "\${AURELIS_LOG_LEVEL:-INFO}"
  format: "structured"
EOF
    fi
    
    # Test GitHub API connectivity
    log "Testing GitHub API connectivity..."
    if ! timeout 10 curl -s -f -H "Authorization: Bearer ${GITHUB_TOKEN}" \
         "https://api.github.com/user" > /dev/null; then
        log "WARNING: Cannot connect to GitHub API"
    else
        log "GitHub API connectivity confirmed"
    fi
}

# Health check function
health_check() {
    local max_attempts=5
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
            log "Application health check passed"
            return 0
        fi
        
        log "Health check attempt $attempt failed, retrying..."
        sleep 2
        ((attempt++))
    done
    
    log "ERROR: Application failed health checks"
    return 1
}

# Main execution
main() {
    log "Starting Aurelis container..."
    
    # Validate environment
    validate_environment
    
    # Wait for dependencies if configured
    if [[ -n "${REDIS_HOST:-}" && -n "${REDIS_PORT:-}" ]]; then
        wait_for_service "${REDIS_HOST}" "${REDIS_PORT}" "Redis" 30
    fi
    
    if [[ -n "${DB_HOST:-}" && -n "${DB_PORT:-}" ]]; then
        wait_for_service "${DB_HOST}" "${DB_PORT}" "Database" 30
    fi
    
    # Initialize application
    initialize_app
    
    # Start application
    log "Starting application with command: $*"
    exec "$@"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

## 🔧 Docker Compose

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  aurelis:
    build:
      context: .
      dockerfile: Dockerfile.prod
      args:
        AURELIS_VERSION: ${AURELIS_VERSION:-latest}
        BUILD_DATE: ${BUILD_DATE}
        VCS_REF: ${VCS_REF}
    image: aurelis:${AURELIS_VERSION:-latest}
    container_name: aurelis-app
    restart: unless-stopped
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - AURELIS_CONFIG=/app/config/production.yaml
      - AURELIS_LOG_LEVEL=${LOG_LEVEL:-INFO}
      - AURELIS_ENVIRONMENT=production
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DB_HOST=postgres
      - DB_PORT=5432
    volumes:
      - ./config:/app/config:ro
      - aurelis_logs:/var/log/aurelis
      - aurelis_cache:/app/.aurelis/cache
      - aurelis_data:/app/data
    ports:
      - "8080:8080"
      - "9090:9090"  # Metrics port
    networks:
      - aurelis_network
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G

  redis:
    image: redis:7-alpine
    container_name: aurelis-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf:ro
    ports:
      - "6379:6379"
    networks:
      - aurelis_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
        reservations:
          cpus: '0.1'
          memory: 256M

  postgres:
    image: postgres:15-alpine
    container_name: aurelis-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-aurelis}
      - POSTGRES_USER=${POSTGRES_USER:-aurelis}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./config/postgres:/docker-entrypoint-initdb.d:ro
    ports:
      - "5432:5432"
    networks:
      - aurelis_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-aurelis} -d ${POSTGRES_DB:-aurelis}"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.2'
          memory: 512M

  nginx:
    image: nginx:alpine
    container_name: aurelis-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/nginx/ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    networks:
      - aurelis_network
    depends_on:
      - aurelis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    container_name: aurelis-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9091:9090"
    volumes:
      - ./config/prometheus:/etc/prometheus:ro
      - prometheus_data:/prometheus
    networks:
      - aurelis_network

  grafana:
    image: grafana/grafana:latest
    container_name: aurelis-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana:/etc/grafana/provisioning:ro
    networks:
      - aurelis_network

volumes:
  aurelis_logs:
    driver: local
  aurelis_cache:
    driver: local
  aurelis_data:
    driver: local
  redis_data:
    driver: local
  postgres_data:
    driver: local
  nginx_logs:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  aurelis_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Environment Configuration

```bash
# .env.prod
# Production environment variables

# Application Configuration
AURELIS_VERSION=1.0.0
AURELIS_ENVIRONMENT=production
LOG_LEVEL=INFO
BUILD_DATE=2024-01-15T10:30:00Z
VCS_REF=abc123

# GitHub Integration
GITHUB_TOKEN=your_production_github_token

# Database Configuration
POSTGRES_DB=aurelis
POSTGRES_USER=aurelis
POSTGRES_PASSWORD=secure_password_here

# Monitoring
GRAFANA_PASSWORD=secure_grafana_password

# Security
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
```

## ☸️ Kubernetes Deployment

### Production Namespace Configuration

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aurelis-production
  labels:
    name: aurelis-production
    environment: production
    app.kubernetes.io/name: aurelis
    app.kubernetes.io/part-of: aurelis-platform

---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: aurelis-quota
  namespace: aurelis-production
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "50"
    limits.memory: 100Gi
    persistentvolumeclaims: "10"
    services: "20"
    secrets: "10"
    configmaps: "10"

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: aurelis-network-policy
  namespace: aurelis-production
spec:
  podSelector:
    matchLabels:
      app: aurelis
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: aurelis-production
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS to GitHub API
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

### Application Deployment

```yaml
# deployment.yaml
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
      maxSurge: 2
  selector:
    matchLabels:
      app: aurelis
  template:
    metadata:
      labels:
        app: aurelis
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: aurelis-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: aurelis
        image: aurelis:v1.0.0-production
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        - containerPort: 9090
          name: metrics
          protocol: TCP
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
        - name: AURELIUS_ENVIRONMENT
          value: "production"
        - name: REDIS_HOST
          value: "aurelis-redis"
        - name: REDIS_PORT
          value: "6379"
        volumeMounts:
        - name: config-volume
          mountPath: /etc/aurelis
          readOnly: true
        - name: cache-volume
          mountPath: /app/.aurelis/cache
        - name: log-volume
          mountPath: /var/log/aurelis
        - name: tmp-volume
          mountPath: /tmp
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
            ephemeral-storage: "1Gi"
          limits:
            memory: "2Gi"
            cpu: "2000m"
            ephemeral-storage: "5Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
          successThreshold: 1
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
          successThreshold: 1
        startupProbe:
          httpGet:
            path: /health
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30
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
          defaultMode: 0644
      - name: cache-volume
        persistentVolumeClaim:
          claimName: aurelis-cache-pvc
      - name: log-volume
        emptyDir:
          sizeLimit: 1Gi
      - name: tmp-volume
        emptyDir:
          sizeLimit: 1Gi
      nodeSelector:
        kubernetes.io/arch: amd64
        node-type: compute
      tolerations:
      - key: "aurelis-workload"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - aurelis
              topologyKey: kubernetes.io/hostname
```

### Service and Ingress

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: aurelis-service
  namespace: aurelis-production
  labels:
    app: aurelis
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  - port: 9090
    targetPort: 9090
    protocol: TCP
    name: metrics
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
    nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Frame-Options: DENY";
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "X-XSS-Protection: 1; mode=block";
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
```

## ⚗️ Helm Charts

### Chart Structure

```yaml
# Chart.yaml
apiVersion: v2
name: aurelis
description: Enterprise AI-powered code analysis and generation platform
type: application
version: 1.0.0
appVersion: "1.0.0"
home: https://aurelis.dev
sources:
  - https://github.com/aurelis/aurelis
keywords:
  - ai
  - code-analysis
  - developer-tools
  - github-models
maintainers:
  - name: Aurelis Team
    email: support@aurelis.dev
dependencies:
  - name: redis
    version: 17.x.x
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
  - name: postgresql
    version: 12.x.x
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
```

### Values Configuration

```yaml
# values.yaml
# Default values for aurelis

global:
  imageRegistry: ""
  imagePullSecrets: []
  storageClass: ""

image:
  registry: ghcr.io
  repository: aurelis/aurelis
  tag: "1.0.0"
  pullPolicy: IfNotPresent
  debug: false

nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

replicaCount: 3

strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 2

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9090"
  prometheus.io/path: "/metrics"

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL

service:
  type: ClusterIP
  port: 80
  targetPort: 8080
  annotations: {}

ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: aurelis.local
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: aurelis-tls
      hosts:
        - aurelis.local

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
    ephemeral-storage: 5Gi
  requests:
    cpu: 500m
    memory: 512Mi
    ephemeral-storage: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

nodeSelector: {}

tolerations: []

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app.kubernetes.io/name
            operator: In
            values:
            - aurelis
        topologyKey: kubernetes.io/hostname

persistence:
  enabled: true
  storageClass: ""
  accessMode: ReadWriteOnce
  size: 10Gi

config:
  github_token: ""
  models:
    primary: "codestral-2501"
    fallback: "gpt-4o-mini"
  cache:
    enabled: true
    backend: "redis"
    ttl: 3600
  logging:
    level: "INFO"
    format: "structured"

redis:
  enabled: true
  auth:
    enabled: false
  master:
    persistence:
      enabled: true
      size: 8Gi

postgresql:
  enabled: false
  auth:
    postgresPassword: ""
    database: "aurelis"
  primary:
    persistence:
      enabled: true
      size: 8Gi

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
```

## 🔒 Container Security

### Security Best Practices

#### 1. Image Security Scanning

```yaml
# .github/workflows/security-scan.yml
name: Container Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Build image
      run: docker build -t aurelis:scan .
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'aurelis:scan'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
```

#### 2. Runtime Security

```yaml
# security-policies.yaml
apiVersion: v1
kind: SecurityContextConstraints
metadata:
  name: aurelis-scc
allowHostDirVolumePlugin: false
allowHostIPC: false
allowHostNetwork: false
allowHostPID: false
allowHostPorts: false
allowPrivilegedContainer: false
allowedCapabilities: []
defaultAddCapabilities: []
readOnlyRootFilesystem: true
requiredDropCapabilities:
- ALL
runAsUser:
  type: MustRunAsRange
  uidRangeMin: 1000
  uidRangeMax: 2000
```

#### 3. Network Security

```yaml
# network-security.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: aurelis-network-policy
  namespace: aurelis-production
spec:
  podSelector:
    matchLabels:
      app: aurelis
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # GitHub API
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

## ⚡ Performance Optimization

### Resource Management

#### 1. Container Resources

```yaml
# Performance-optimized resource configuration
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
    ephemeral-storage: "2Gi"
  limits:
    memory: "4Gi"
    cpu: "2000m"
    ephemeral-storage: "10Gi"

# JVM tuning for Java-based components
env:
- name: JAVA_OPTS
  value: "-Xms1g -Xmx3g -XX:+UseG1GC -XX:MaxGCPauseMillis=200"

# Python optimization
- name: PYTHONOPTIMIZE
  value: "2"
- name: PYTHONUNBUFFERED
  value: "1"
```

#### 2. Horizontal Pod Autoscaler

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
  maxReplicas: 50
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
        value: 5
        periodSeconds: 60
      selectPolicy: Max
```

#### 3. Vertical Pod Autoscaler

```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: aurelis-vpa
  namespace: aurelis-production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aurelis-deployment
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: aurelis
      maxAllowed:
        cpu: 4
        memory: 8Gi
      minAllowed:
        cpu: 100m
        memory: 256Mi
      mode: Auto
```

## 📊 Monitoring & Logging

### Prometheus Configuration

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: aurelis-production
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "aurelis_rules.yml"
    
    scrape_configs:
    - job_name: 'aurelis'
      static_configs:
      - targets: ['aurelis-service:9090']
      scrape_interval: 30s
      metrics_path: /metrics
      
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - aurelis-production
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "id": null,
    "title": "Aurelis Performance Dashboard",
    "tags": ["aurelis", "performance"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(aurelis_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, aurelis_request_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(aurelis_requests_total{status!~\"2..\"}[5m]) / rate(aurelis_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      }
    ]
  }
}
```

## 🔧 Troubleshooting

### Common Container Issues

#### 1. Container Startup Problems

```bash
# Check container logs
docker logs aurelis-app --tail=100 -f

# Inspect container
docker inspect aurelis-app

# Debug with shell access
docker exec -it aurelis-app /bin/bash

# Check resource usage
docker stats aurelis-app
```

#### 2. Kubernetes Pod Issues

```bash
# Check pod status
kubectl get pods -n aurelis-production

# Describe pod for events
kubectl describe pod <pod-name> -n aurelis-production

# Check logs
kubectl logs -f <pod-name> -n aurelis-production

# Debug with shell
kubectl exec -it <pod-name> -n aurelis-production -- /bin/bash

# Check resource usage
kubectl top pods -n aurelis-production
```

#### 3. Performance Issues

```bash
# Monitor container performance
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Check memory usage
kubectl exec <pod-name> -n aurelis-production -- cat /proc/meminfo

# Monitor CPU usage
kubectl exec <pod-name> -n aurelis-production -- top -bn1

# Check disk usage
kubectl exec <pod-name> -n aurelis-production -- df -h
```

### Emergency Procedures

#### 1. Scale Down

```bash
# Scale down deployment
kubectl scale deployment aurelis-deployment --replicas=1 -n aurelis-production

# Stop all containers
docker-compose down
```

#### 2. Rollback

```bash
# Check rollout history
kubectl rollout history deployment/aurelis-deployment -n aurelis-production

# Rollback to previous version
kubectl rollout undo deployment/aurelis-deployment -n aurelis-production
```

#### 3. Emergency Restart

```bash
# Restart deployment
kubectl rollout restart deployment/aurelis-deployment -n aurelis-production

# Restart specific container
docker restart aurelis-app
```

## 📚 See Also

- [Production Deployment Guide](production-deployment.md)
- [Monitoring Guide](monitoring.md)
- [Security Best Practices](security.md)
- [Performance Tuning](performance.md)
