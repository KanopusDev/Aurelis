# Monitoring Guide

Comprehensive monitoring and observability setup for Aurelis production deployments.

## 📋 Table of Contents

1. [Monitoring Overview](#monitoring-overview)
2. [Metrics Collection](#metrics-collection)
3. [Health Checks](#health-checks)
4. [Alerting System](#alerting-system)
5. [Log Management](#log-management)
6. [Performance Monitoring](#performance-monitoring)
7. [Business Metrics](#business-metrics)
8. [Dashboards](#dashboards)
9. [Troubleshooting](#troubleshooting)

## 📊 Monitoring Overview

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Prometheus    │───▶│     Grafana     │
│    Metrics      │    │   (Metrics)     │    │  (Dashboards)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   AlertManager  │              │
         │              │   (Alerting)    │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ELK Stack     │    │   PagerDuty     │    │   Slack/Teams   │
│   (Logging)     │    │  (Incidents)    │    │ (Notifications) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

1. **Metrics Collection**: Prometheus, custom metrics
2. **Visualization**: Grafana dashboards
3. **Alerting**: AlertManager, PagerDuty
4. **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
5. **Tracing**: Jaeger, OpenTelemetry
6. **Health Checks**: Custom health endpoints

## 📈 Metrics Collection

### Application Metrics

```python
# metrics.py - Application metrics implementation
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
import time
import logging
from functools import wraps

# Define core metrics
REQUEST_COUNT = Counter(
    'aurelis_requests_total',
    'Total number of requests processed',
    ['method', 'endpoint', 'status_code', 'model']
)

REQUEST_DURATION = Histogram(
    'aurelis_request_duration_seconds',
    'Request processing time in seconds',
    ['method', 'endpoint', 'model'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

MODEL_REQUESTS = Counter(
    'aurelis_model_requests_total',
    'Total requests to AI models',
    ['model', 'task_type', 'status']
)

TOKEN_USAGE = Counter(
    'aurelis_tokens_total',
    'Total tokens processed',
    ['model', 'type']  # type: input/output
)

CACHE_HIT_RATE = Gauge(
    'aurelis_cache_hit_rate',
    'Cache hit rate percentage'
)

ACTIVE_CONNECTIONS = Gauge(
    'aurelis_active_connections',
    'Number of active connections'
)

QUEUE_SIZE = Gauge(
    'aurelis_queue_size',
    'Current size of processing queue'
)

ERROR_RATE = Gauge(
    'aurelis_error_rate',
    'Current error rate percentage'
)

SYSTEM_INFO = Info(
    'aurelis_system_info',
    'System information'
)

# GitHub API metrics
GITHUB_API_REQUESTS = Counter(
    'aurelis_github_api_requests_total',
    'Total GitHub API requests',
    ['endpoint', 'status_code']
)

GITHUB_RATE_LIMIT = Gauge(
    'aurelis_github_rate_limit_remaining',
    'GitHub API rate limit remaining'
)

class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        
    def start_metrics_server(self, port=9090):
        """Start Prometheus metrics server."""
        start_http_server(port)
        logging.info(f"Metrics server started on port {port}")
        
        # Set initial system info
        SYSTEM_INFO.info({
            'version': '1.0.0',
            'python_version': '3.11',
            'start_time': str(int(self.start_time))
        })
    
    def record_request(self, method, endpoint, status_code, duration, model=None):
        """Record request metrics."""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            model=model or 'unknown'
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint,
            model=model or 'unknown'
        ).observe(duration)
    
    def record_model_request(self, model, task_type, status, tokens_in=0, tokens_out=0):
        """Record model request metrics."""
        MODEL_REQUESTS.labels(
            model=model,
            task_type=task_type,
            status=status
        ).inc()
        
        if tokens_in > 0:
            TOKEN_USAGE.labels(model=model, type='input').inc(tokens_in)
        if tokens_out > 0:
            TOKEN_USAGE.labels(model=model, type='output').inc(tokens_out)
    
    def update_cache_metrics(self, hit_rate):
        """Update cache hit rate."""
        CACHE_HIT_RATE.set(hit_rate)
    
    def update_connection_count(self, count):
        """Update active connections count."""
        ACTIVE_CONNECTIONS.set(count)
    
    def update_queue_size(self, size):
        """Update processing queue size."""
        QUEUE_SIZE.set(size)
    
    def update_error_rate(self, rate):
        """Update error rate percentage."""
        ERROR_RATE.set(rate)
    
    def record_github_api_call(self, endpoint, status_code, rate_limit_remaining):
        """Record GitHub API call metrics."""
        GITHUB_API_REQUESTS.labels(
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        GITHUB_RATE_LIMIT.set(rate_limit_remaining)

# Decorator for automatic metrics collection
def monitor_requests(metrics_collector):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = getattr(e, 'status_code', 500)
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_request(
                    method=kwargs.get('method', 'unknown'),
                    endpoint=kwargs.get('endpoint', func.__name__),
                    status_code=status_code,
                    duration=duration
                )
        return wrapper
    return decorator
```

### Infrastructure Metrics

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: aurelis-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
      external_labels:
        cluster: 'aurelis-production'
        environment: 'production'
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
    
    scrape_configs:
    # Aurelis application metrics
    - job_name: 'aurelis'
      static_configs:
      - targets: ['aurelis-service:9090']
      scrape_interval: 30s
      metrics_path: /metrics
      scrape_timeout: 10s
    
    # Kubernetes cluster metrics
    - job_name: 'kubernetes-nodes'
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):10250'
        target_label: __address__
        replacement: '${1}:9100'
    
    # Pod metrics
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
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
    
    # Redis metrics
    - job_name: 'redis'
      static_configs:
      - targets: ['aurelis-redis:9121']
    
    # Nginx metrics
    - job_name: 'nginx'
      static_configs:
      - targets: ['nginx-exporter:9113']
```

## 🏥 Health Checks

### Application Health Endpoints

```python
# health.py - Comprehensive health check implementation
from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime, timedelta
import asyncio
import aiohttp
import redis
import logging
from typing import Dict, Any

app = FastAPI()

class HealthChecker:
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.redis_client = None
        self.last_health_check = {}
    
    async def check_github_api(self) -> Dict[str, Any]:
        """Check GitHub API connectivity and rate limits."""
        try:
            headers = {'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}'}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.github.com/rate_limit',
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        remaining = data['rate']['remaining']
                        reset_time = datetime.fromtimestamp(data['rate']['reset'])
                        
                        return {
                            'status': 'healthy',
                            'rate_limit_remaining': remaining,
                            'rate_limit_reset': reset_time.isoformat(),
                            'response_time': response.headers.get('X-Response-Time', 'unknown')
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'error': f'HTTP {response.status}',
                            'response_time': None
                        }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': None
            }
    
    async def check_cache(self) -> Dict[str, Any]:
        """Check Redis cache connectivity."""
        try:
            if not self.redis_client:
                self.redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    socket_timeout=5
                )
            
            start_time = time.time()
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.ping
            )
            response_time = time.time() - start_time
            
            # Get cache statistics
            info = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.info
            )
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'unknown'),
                'hit_rate': info.get('keyspace_hits', 0) / (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1))
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': None
            }
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            
            free_percent = (free / total) * 100
            status = 'healthy' if free_percent > 10 else 'warning' if free_percent > 5 else 'critical'
            
            return {
                'status': status,
                'total_gb': round(total / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'free_percent': round(free_percent, 2)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            available_percent = memory.available / memory.total * 100
            status = 'healthy' if available_percent > 20 else 'warning' if available_percent > 10 else 'critical'
            
            return {
                'status': status,
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'available_percent': round(available_percent, 2),
                'used_percent': round(memory.percent, 2)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

health_checker = HealthChecker()

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    start_time = time.time()
    
    # Run all health checks concurrently
    github_check, cache_check, disk_check, memory_check = await asyncio.gather(
        health_checker.check_github_api(),
        health_checker.check_cache(),
        health_checker.check_disk_space(),
        health_checker.check_memory(),
        return_exceptions=True
    )
    
    # Determine overall health status
    checks = {
        'github_api': github_check if not isinstance(github_check, Exception) else {'status': 'error', 'error': str(github_check)},
        'cache': cache_check if not isinstance(cache_check, Exception) else {'status': 'error', 'error': str(cache_check)},
        'disk': disk_check if not isinstance(disk_check, Exception) else {'status': 'error', 'error': str(disk_check)},
        'memory': memory_check if not isinstance(memory_check, Exception) else {'status': 'error', 'error': str(memory_check)}
    }
    
    # Calculate overall status
    statuses = [check.get('status', 'error') for check in checks.values()]
    if 'unhealthy' in statuses or 'error' in statuses:
        overall_status = 'unhealthy'
        status_code = 503
    elif 'critical' in statuses:
        overall_status = 'critical'
        status_code = 503
    elif 'warning' in statuses:
        overall_status = 'warning'
        status_code = 200
    else:
        overall_status = 'healthy'
        status_code = 200
    
    uptime = datetime.utcnow() - health_checker.start_time
    
    health_response = {
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat(),
        'version': os.getenv('AURELIS_VERSION', '1.0.0'),
        'environment': os.getenv('AURELIS_ENVIRONMENT', 'production'),
        'uptime_seconds': int(uptime.total_seconds()),
        'checks': checks,
        'check_duration': round(time.time() - start_time, 3)
    }
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=health_response)
    
    return health_response

@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    # Check critical dependencies only
    github_ok = (await health_checker.check_github_api())['status'] == 'healthy'
    cache_ok = (await health_checker.check_cache())['status'] == 'healthy'
    
    if github_ok and cache_ok:
        return {'status': 'ready'}
    else:
        raise HTTPException(status_code=503, detail={'status': 'not_ready'})

@app.get("/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    # Simple check that the application is running
    return {
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': int((datetime.utcnow() - health_checker.start_time).total_seconds())
    }

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    # This would be handled by the prometheus_client library
    pass
```

### Kubernetes Health Configuration

```yaml
# health-checks.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: health-config
  namespace: aurelis-production
data:
  health-check.sh: |
    #!/bin/bash
    
    # Health check script for containers
    set -e
    
    # Check if application is responding
    if curl -f -s http://localhost:8080/health > /dev/null; then
        echo "✓ Application health check passed"
        exit 0
    else
        echo "✗ Application health check failed"
        exit 1
    fi
  
  startup-probe.sh: |
    #!/bin/bash
    
    # Startup probe for slow-starting applications
    timeout=300  # 5 minutes
    interval=10
    
    for ((i=0; i<timeout; i+=interval)); do
        if curl -f -s http://localhost:8080/ready > /dev/null; then
            echo "✓ Application is ready"
            exit 0
        fi
        echo "Waiting for application to be ready... ($i/$timeout seconds)"
        sleep $interval
    done
    
    echo "✗ Application failed to become ready within $timeout seconds"
    exit 1

---
# Deployment with enhanced health checks
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurelis-deployment
  namespace: aurelis-production
spec:
  template:
    spec:
      containers:
      - name: aurelis
        image: aurelis:v1.0.0-production
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
        
        # Startup probe for slow-starting applications
        startupProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30  # 5 minutes total
          successThreshold: 1
        
        # Liveness probe to restart unhealthy containers
        livenessProbe:
          httpGet:
            path: /live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
          successThreshold: 1
        
        # Readiness probe to control traffic routing
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
          successThreshold: 1
```

## 🚨 Alerting System

### AlertManager Configuration

```yaml
# alertmanager-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: aurelis-monitoring
data:
  alertmanager.yml: |
    global:
      smtp_smarthost: 'localhost:587'
      smtp_from: 'alerts@aurelis.com'
      slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    
    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'default'
      routes:
      # Critical alerts go to PagerDuty
      - match:
          severity: critical
        receiver: 'pagerduty'
        continue: true
      
      # Warning alerts go to Slack
      - match:
          severity: warning
        receiver: 'slack'
        continue: true
      
      # Service-specific routing
      - match:
          service: aurelis
        receiver: 'aurelis-team'
    
    receivers:
    - name: 'default'
      email_configs:
      - to: 'ops@aurelis.com'
        subject: '[Aurelis] Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }}{{ end }}
          {{ end }}
    
    - name: 'pagerduty'
      pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .GroupLabels.instance }}'
        details:
          alertname: '{{ .GroupLabels.alertname }}'
          instance: '{{ .GroupLabels.instance }}'
          severity: '{{ .CommonLabels.severity }}'
    
    - name: 'slack'
      slack_configs:
      - channel: '#aurelis-alerts'
        title: 'Aurelis Alert'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          *Severity:* {{ .Labels.severity }}
          {{ end }}
    
    - name: 'aurelis-team'
      slack_configs:
      - channel: '#aurelis-team'
        title: 'Aurelis Service Alert'
        text: |
          {{ range .Alerts }}
          *Service:* {{ .Labels.service }}
          *Alert:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          {{ end }}
```

### Alert Rules

```yaml
# alert-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: aurelis-monitoring
data:
  aurelis-rules.yml: |
    groups:
    - name: aurelis.rules
      interval: 30s
      rules:
      
      # High error rate
      - alert: AurelisHighErrorRate
        expr: |
          (
            rate(aurelis_requests_total{status_code!~"2.."}[5m]) / 
            rate(aurelis_requests_total[5m])
          ) * 100 > 5
        for: 2m
        labels:
          severity: warning
          service: aurelis
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% over the last 5 minutes"
          runbook_url: "https://docs.aurelis.com/runbooks/high-error-rate"
      
      # Critical error rate
      - alert: AurelisCriticalErrorRate
        expr: |
          (
            rate(aurelis_requests_total{status_code!~"2.."}[5m]) / 
            rate(aurelis_requests_total[5m])
          ) * 100 > 15
        for: 1m
        labels:
          severity: critical
          service: aurelis
        annotations:
          summary: "Critical error rate detected"
          description: "Error rate is {{ $value }}% over the last 5 minutes"
          runbook_url: "https://docs.aurelis.com/runbooks/critical-error-rate"
      
      # High response time
      - alert: AurelisHighResponseTime
        expr: |
          histogram_quantile(0.95, 
            rate(aurelis_request_duration_seconds_bucket[5m])
          ) > 10
        for: 3m
        labels:
          severity: warning
          service: aurelis
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"
      
      # Service down
      - alert: AurelisServiceDown
        expr: up{job="aurelis"} == 0
        for: 1m
        labels:
          severity: critical
          service: aurelis
        annotations:
          summary: "Aurelis service is down"
          description: "Aurelis service has been down for more than 1 minute"
          runbook_url: "https://docs.aurelis.com/runbooks/service-down"
      
      # High memory usage
      - alert: AurelisHighMemoryUsage
        expr: |
          (
            container_memory_working_set_bytes{pod=~"aurelis-.*"} / 
            container_spec_memory_limit_bytes{pod=~"aurelis-.*"}
          ) * 100 > 80
        for: 5m
        labels:
          severity: warning
          service: aurelis
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"
      
      # GitHub API rate limit
      - alert: GitHubAPIRateLimitLow
        expr: aurelis_github_rate_limit_remaining < 100
        for: 1m
        labels:
          severity: warning
          service: aurelis
        annotations:
          summary: "GitHub API rate limit running low"
          description: "Only {{ $value }} requests remaining"
      
      # Cache hit rate too low
      - alert: LowCacheHitRate
        expr: aurelis_cache_hit_rate < 0.7
        for: 10m
        labels:
          severity: warning
          service: aurelis
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}%"
      
      # Queue size too large
      - alert: HighQueueSize
        expr: aurelis_queue_size > 1000
        for: 5m
        labels:
          severity: warning
          service: aurelis
        annotations:
          summary: "High queue size"
          description: "Processing queue size is {{ $value }}"
```

## 📋 Log Management

### Structured Logging Configuration

```python
# logging_config.py
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any
import traceback
import os

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': os.getpid(),
            'thread_id': record.thread,
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
        
        # Add user context if available
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Add custom fields
        if hasattr(record, 'custom_fields'):
            log_entry.update(record.custom_fields)
        
        # Add exception information
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, default=str)

def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    structured: bool = True
) -> None:
    """Setup application logging configuration."""
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Create formatters
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Prevent duplicate logs
    root_logger.propagate = False

class ContextLogger:
    """Logger with request context."""
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set logging context."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear logging context."""
        self.context.clear()
    
    def _log(self, level: int, message: str, **kwargs):
        """Log with context."""
        extra = {'custom_fields': {**self.context, **kwargs}}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)

# Request logging middleware
import uuid
from contextlib import contextmanager

@contextmanager
def request_context(request_id: str = None, user_id: str = None):
    """Context manager for request logging."""
    if not request_id:
        request_id = str(uuid.uuid4())
    
    logger = ContextLogger(__name__)
    logger.set_context(request_id=request_id, user_id=user_id)
    
    try:
        yield logger
    finally:
        logger.clear_context()
```

### ELK Stack Configuration

```yaml
# elasticsearch.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: aurelis-monitoring
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
        env:
        - name: cluster.name
          value: "aurelis-logs"
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: discovery.seed_hosts
          value: "elasticsearch-0.elasticsearch,elasticsearch-1.elasticsearch,elasticsearch-2.elasticsearch"
        - name: cluster.initial_master_nodes
          value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
        - name: ES_JAVA_OPTS
          value: "-Xms1g -Xmx1g"
        - name: xpack.security.enabled
          value: "true"
        - name: xpack.security.transport.ssl.enabled
          value: "true"
        ports:
        - containerPort: 9200
          name: http
        - containerPort: 9300
          name: transport
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
        resources:
          requests:
            memory: 2Gi
            cpu: 1000m
          limits:
            memory: 4Gi
            cpu: 2000m
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi

---
# logstash.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: logstash
  namespace: aurelis-monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: logstash
  template:
    metadata:
      labels:
        app: logstash
    spec:
      containers:
      - name: logstash
        image: docker.elastic.co/logstash/logstash:8.8.0
        env:
        - name: LS_JAVA_OPTS
          value: "-Xms1g -Xmx1g"
        ports:
        - containerPort: 5044
          name: beats
        - containerPort: 9600
          name: http
        volumeMounts:
        - name: config
          mountPath: /usr/share/logstash/pipeline
        resources:
          requests:
            memory: 2Gi
            cpu: 1000m
          limits:
            memory: 4Gi
            cpu: 2000m
      volumes:
      - name: config
        configMap:
          name: logstash-config

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: logstash-config
  namespace: aurelis-monitoring
data:
  logstash.conf: |
    input {
      beats {
        port => 5044
      }
    }
    
    filter {
      if [fields][service] == "aurelis" {
        json {
          source => "message"
        }
        
        date {
          match => [ "timestamp", "ISO8601" ]
        }
        
        mutate {
          add_field => { "service" => "aurelis" }
          add_field => { "environment" => "production" }
        }
        
        # Parse correlation IDs
        if [correlation_id] {
          mutate {
            add_tag => [ "correlated" ]
          }
        }
        
        # Categorize log levels
        if [level] == "ERROR" or [level] == "CRITICAL" {
          mutate {
            add_tag => [ "error" ]
          }
        }
      }
    }
    
    output {
      elasticsearch {
        hosts => ["elasticsearch:9200"]
        index => "aurelis-logs-%{+YYYY.MM.dd}"
        template_name => "aurelis"
        template_pattern => "aurelis-*"
        template => {
          "index_patterns" => ["aurelis-*"],
          "settings" => {
            "number_of_shards" => 1,
            "number_of_replicas" => 1
          },
          "mappings" => {
            "properties" => {
              "@timestamp" => { "type" => "date" },
              "level" => { "type" => "keyword" },
              "message" => { "type" => "text" },
              "service" => { "type" => "keyword" },
              "environment" => { "type" => "keyword" },
              "correlation_id" => { "type" => "keyword" },
              "user_id" => { "type" => "keyword" },
              "request_id" => { "type" => "keyword" }
            }
          }
        }
      }
    }
```

## 📊 Performance Monitoring

### Application Performance Monitoring

```python
# apm.py - Application Performance Monitoring
import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics

@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)

class PerformanceMonitor:
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.active_traces: Dict[str, float] = {}
        
    def start_trace(self, trace_id: str) -> str:
        """Start a performance trace."""
        self.active_traces[trace_id] = time.time()
        return trace_id
    
    def end_trace(self, trace_id: str, tags: Dict[str, str] = None) -> float:
        """End a performance trace and record duration."""
        if trace_id not in self.active_traces:
            return 0.0
        
        duration = time.time() - self.active_traces.pop(trace_id)
        
        metric = PerformanceMetric(
            name=f"trace.{trace_id}",
            value=duration,
            unit="seconds",
            tags=tags or {}
        )
        self.metrics.append(metric)
        
        return duration
    
    def record_metric(self, name: str, value: float, unit: str = "", tags: Dict[str, str] = None):
        """Record a custom metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        self.metrics.append(metric)
    
    def get_metrics_summary(self, time_window: timedelta = timedelta(minutes=5)) -> Dict:
        """Get performance metrics summary."""
        cutoff = datetime.utcnow() - time_window
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff]
        
        if not recent_metrics:
            return {}
        
        # Group metrics by name
        grouped = {}
        for metric in recent_metrics:
            if metric.name not in grouped:
                grouped[metric.name] = []
            grouped[metric.name].append(metric.value)
        
        # Calculate statistics
        summary = {}
        for name, values in grouped.items():
            summary[name] = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
                'p99': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)
            }
        
        return summary
    
    def cleanup_old_metrics(self, max_age: timedelta = timedelta(hours=1)):
        """Remove old metrics to prevent memory leaks."""
        cutoff = datetime.utcnow() - max_age
        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff]

# Performance monitoring decorators
def monitor_performance(monitor: PerformanceMonitor, metric_name: str = None):
    """Decorator to monitor function performance."""
    def decorator(func):
        nonlocal metric_name
        if not metric_name:
            metric_name = f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                trace_id = monitor.start_trace(metric_name)
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    monitor.end_trace(trace_id, {'function': func.__name__})
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                trace_id = monitor.start_trace(metric_name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    monitor.end_trace(trace_id, {'function': func.__name__})
            return sync_wrapper
    return decorator

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Example usage in application
@monitor_performance(performance_monitor, "github_api_call")
async def call_github_api(endpoint: str):
    # Simulate API call
    await asyncio.sleep(0.1)
    return {"status": "success"}

@monitor_performance(performance_monitor, "code_analysis")
async def analyze_code(code: str):
    # Simulate code analysis
    await asyncio.sleep(0.5)
    return {"analysis": "complete"}
```

## 💼 Business Metrics

### Usage Analytics

```python
# analytics.py - Business metrics and usage analytics
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class AnalyticsCollector:
    def __init__(self):
        self.events: List[Dict] = []
    
    def track_event(self, event_type: str, properties: Dict = None, user_id: str = None):
        """Track a business event."""
        event = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'properties': properties or {},
            'user_id': user_id
        }
        self.events.append(event)
    
    def track_model_usage(self, model: str, task_type: str, tokens_used: int, 
                         user_id: str = None, duration: float = None):
        """Track AI model usage."""
        self.track_event('model_usage', {
            'model': model,
            'task_type': task_type,
            'tokens_used': tokens_used,
            'duration': duration,
            'cost_estimate': self._calculate_cost(model, tokens_used)
        }, user_id)
    
    def track_feature_usage(self, feature: str, user_id: str = None):
        """Track feature usage."""
        self.track_event('feature_usage', {
            'feature': feature
        }, user_id)
    
    def track_error(self, error_type: str, error_message: str, context: Dict = None):
        """Track application errors."""
        self.track_event('error', {
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {}
        })
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate estimated cost based on model and token usage."""
        # Cost per 1000 tokens (example rates)
        rates = {
            'gpt-4o': 0.03,
            'gpt-4o-mini': 0.0015,
            'codestral-2501': 0.02,
            'cohere-command-r': 0.025
        }
        
        rate = rates.get(model, 0.02)  # Default rate
        return (tokens / 1000) * rate
    
    def get_usage_summary(self, time_window: timedelta = timedelta(days=1)) -> Dict:
        """Get usage summary for the specified time window."""
        cutoff = datetime.utcnow() - time_window
        recent_events = [
            e for e in self.events 
            if datetime.fromisoformat(e['timestamp']) >= cutoff
        ]
        
        # Model usage summary
        model_usage = {}
        total_tokens = 0
        total_cost = 0.0
        
        for event in recent_events:
            if event['event_type'] == 'model_usage':
                props = event['properties']
                model = props['model']
                tokens = props['tokens_used']
                cost = props.get('cost_estimate', 0)
                
                if model not in model_usage:
                    model_usage[model] = {
                        'requests': 0,
                        'tokens': 0,
                        'cost': 0.0
                    }
                
                model_usage[model]['requests'] += 1
                model_usage[model]['tokens'] += tokens
                model_usage[model]['cost'] += cost
                
                total_tokens += tokens
                total_cost += cost
        
        # Feature usage summary
        feature_usage = {}
        for event in recent_events:
            if event['event_type'] == 'feature_usage':
                feature = event['properties']['feature']
                feature_usage[feature] = feature_usage.get(feature, 0) + 1
        
        # Error summary
        error_summary = {}
        for event in recent_events:
            if event['event_type'] == 'error':
                error_type = event['properties']['error_type']
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        # User activity
        unique_users = len(set(
            e['user_id'] for e in recent_events 
            if e['user_id'] is not None
        ))
        
        return {
            'time_window': str(time_window),
            'total_events': len(recent_events),
            'unique_users': unique_users,
            'model_usage': model_usage,
            'feature_usage': feature_usage,
            'error_summary': error_summary,
            'total_tokens': total_tokens,
            'total_cost': round(total_cost, 4)
        }

# Global analytics collector
analytics = AnalyticsCollector()

# Middleware to track API usage
async def analytics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Track API usage
    analytics.track_event('api_request', {
        'endpoint': str(request.url.path),
        'method': request.method,
        'status_code': response.status_code,
        'duration': duration
    })
    
    return response
```

## 📈 Dashboards

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "id": null,
    "title": "Aurelis Production Dashboard",
    "tags": ["aurelis", "production"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Overview",
        "type": "stat",
        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "up{job=\"aurelis\"}",
            "legendFormat": "Service Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"options": {"0": {"text": "Down", "color": "red"}}, "type": "value"},
              {"options": {"1": {"text": "Up", "color": "green"}}, "type": "value"}
            ]
          }
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 6},
        "targets": [
          {
            "expr": "rate(aurelis_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "yAxes": [
          {"label": "Requests/sec", "min": 0}
        ]
      },
      {
        "id": 3,
        "title": "Response Time",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 6},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(aurelis_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(aurelis_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.99, rate(aurelis_request_duration_seconds_bucket[5m]))",
            "legendFormat": "99th percentile"
          }
        ],
        "yAxes": [
          {"label": "Seconds", "min": 0}
        ]
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "stat",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 14},
        "targets": [
          {
            "expr": "rate(aurelis_requests_total{status_code!~\"2..\"}[5m]) / rate(aurelis_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 1},
                {"color": "red", "value": 5}
              ]
            }
          }
        }
      },
      {
        "id": 5,
        "title": "Model Usage",
        "type": "piechart",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": 14},
        "targets": [
          {
            "expr": "increase(aurelis_model_requests_total[1h])",
            "legendFormat": "{{model}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "Cache Hit Rate",
        "type": "stat",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": 14},
        "targets": [
          {
            "expr": "aurelis_cache_hit_rate * 100",
            "legendFormat": "Cache Hit Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 50},
                {"color": "green", "value": 80}
              ]
            }
          }
        }
      },
      {
        "id": 7,
        "title": "GitHub API Rate Limit",
        "type": "gauge",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 20},
        "targets": [
          {
            "expr": "aurelis_github_rate_limit_remaining",
            "legendFormat": "Remaining Requests"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 5000,
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 500},
                {"color": "green", "value": 1000}
              ]
            }
          }
        }
      },
      {
        "id": 8,
        "title": "System Resources",
        "type": "graph",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 20},
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{pod=~\"aurelis-.*\"}[5m]) * 100",
            "legendFormat": "CPU Usage %"
          },
          {
            "expr": "container_memory_working_set_bytes{pod=~\"aurelis-.*\"} / container_spec_memory_limit_bytes{pod=~\"aurelis-.*\"} * 100",
            "legendFormat": "Memory Usage %"
          }
        ],
        "yAxes": [
          {"label": "Percentage", "min": 0, "max": 100}
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

## 🔧 Troubleshooting

### Common Monitoring Issues

#### 1. Missing Metrics

```bash
# Check if metrics endpoint is accessible
curl http://localhost:9090/metrics

# Verify Prometheus scraping
kubectl logs -f deployment/prometheus -n aurelis-monitoring

# Check service discovery
kubectl get endpoints aurelis-service -n aurelis-production
```

#### 2. High Cardinality Metrics

```python
# Avoid high cardinality labels
# BAD: Using user IDs as labels
REQUEST_COUNT.labels(user_id=user_id, endpoint=endpoint).inc()

# GOOD: Use limited set of labels
REQUEST_COUNT.labels(endpoint=endpoint, method=method).inc()
# Track user metrics separately with sampling
```

#### 3. Alert Fatigue

```yaml
# Use proper alert thresholds and timing
- alert: HighErrorRate
  expr: rate(errors[5m]) > 0.05  # 5% error rate
  for: 2m  # Wait 2 minutes before firing
  
# Group related alerts
route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
```

#### 4. Dashboard Performance

```yaml
# Use appropriate time ranges and intervals
targets:
- expr: rate(aurelius_requests_total[5m])  # Use 5m rate
  interval: 30s  # Query every 30 seconds
  
# Limit series in dashboards
- expr: topk(10, rate(aurelis_requests_total[5m]))  # Top 10 only
```

### Debugging Commands

```bash
# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets

# Query metrics directly
curl "http://prometheus:9090/api/v1/query?query=up"

# Check AlertManager status
curl http://alertmanager:9093/api/v1/status

# Verify log shipping
kubectl logs -f daemonset/filebeat -n aurelis-monitoring

# Test health endpoints
curl -f http://aurelis-service/health
curl -f http://aurelis-service/ready
```

## 📚 See Also

- [Production Deployment Guide](production-deployment.md)
- [Container Deployment Guide](container-deployment.md)
- [Security Best Practices](security.md)
- [Performance Tuning](performance.md)
