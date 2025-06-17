# Google Cloud Platform Deployment Guide

This guide provides comprehensive instructions for deploying Aurelis on Google Cloud Platform (GCP) using various services and deployment strategies.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Google Kubernetes Engine (GKE)](#google-kubernetes-engine-gke)
- [Cloud Run](#cloud-run)
- [Cloud Functions](#cloud-functions)
- [Compute Engine](#compute-engine)
- [Infrastructure as Code](#infrastructure-as-code)
- [Security Configuration](#security-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Auto-scaling](#auto-scaling)
- [Networking](#networking)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Docker](https://docs.docker.com/get-docker/)
- [Terraform](https://www.terraform.io/downloads.html) (optional)

### GCP Setup
```bash
# Install gcloud CLI
# Authentication
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

## Google Kubernetes Engine (GKE)

### Standard GKE Cluster

#### Create Cluster
```bash
# Create GKE cluster
gcloud container clusters create aurelis-cluster \
  --machine-type=n1-standard-2 \
  --num-nodes=3 \
  --zone=us-central1-a \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10 \
  --disk-size=50GB \
  --disk-type=pd-ssd

# Get credentials
gcloud container clusters get-credentials aurelis-cluster --zone=us-central1-a
```

#### Kubernetes Manifests

**Deployment (`k8s/deployment.yaml`)**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurelis-app
  namespace: aurelis
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
        image: gcr.io/YOUR_PROJECT_ID/aurelis:latest
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "info"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Service (`k8s/service.yaml`)**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: aurelis-service
  namespace: aurelis
spec:
  selector:
    app: aurelis
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

**Ingress (`k8s/ingress.yaml`)**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aurelis-ingress
  namespace: aurelis
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "aurelis-ip"
    networking.gke.io/managed-certificates: "aurelis-ssl"
spec:
  rules:
  - host: api.aurelis.example.com
    http:
      paths:
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: aurelis-service
            port:
              number: 80
```

#### Deploy to GKE
```bash
# Create namespace
kubectl create namespace aurelis

# Apply manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n aurelis
kubectl get services -n aurelis
```

### GKE Autopilot

```bash
# Create Autopilot cluster
gcloud container clusters create-auto aurelis-autopilot \
  --region=us-central1 \
  --release-channel=regular

# Get credentials
gcloud container clusters get-credentials aurelis-autopilot --region=us-central1
```

## Cloud Run

### Deploy to Cloud Run

#### Build and Deploy
```bash
# Build and push image
docker build -t gcr.io/YOUR_PROJECT_ID/aurelis:latest .
docker push gcr.io/YOUR_PROJECT_ID/aurelis:latest

# Deploy to Cloud Run
gcloud run deploy aurelis \
  --image=gcr.io/YOUR_PROJECT_ID/aurelis:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=100 \
  --concurrency=80 \
  --timeout=300 \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=info"
```

#### Cloud Run Configuration (`cloud-run.yaml`)
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: aurelis
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/execution-environment: gen2
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "100"
        autoscaling.knative.dev/minScale: "0"
        run.googleapis.com/cpu-throttling: "true"
        run.googleapis.com/memory: "512Mi"
        run.googleapis.com/cpu: "1000m"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/YOUR_PROJECT_ID/aurelis:latest
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "info"
        resources:
          limits:
            memory: "512Mi"
            cpu: "1000m"
```

```bash
# Deploy with configuration file
gcloud run services replace cloud-run.yaml --region=us-central1
```

## Cloud Functions

### HTTP Function Deployment

```bash
# Deploy HTTP function
gcloud functions deploy aurelis-function \
  --runtime=python39 \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=540s \
  --max-instances=100 \
  --set-env-vars="ENVIRONMENT=production"
```

### Event-driven Function

```bash
# Deploy Pub/Sub triggered function
gcloud functions deploy aurelis-processor \
  --runtime=python39 \
  --trigger-topic=aurelis-events \
  --memory=1024MB \
  --timeout=540s \
  --max-instances=50
```

## Compute Engine

### VM Instance Deployment

```bash
# Create VM instance
gcloud compute instances create aurelis-vm \
  --zone=us-central1-a \
  --machine-type=n1-standard-2 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --tags=aurelis-server \
  --metadata-from-file startup-script=startup.sh
```

**Startup Script (`startup.sh`)**:
```bash
#!/bin/bash
apt-get update
apt-get install -y docker.io

# Start Docker service
systemctl start docker
systemctl enable docker

# Pull and run Aurelis
docker pull gcr.io/YOUR_PROJECT_ID/aurelis:latest
docker run -d -p 80:8080 \
  --name aurelis \
  --restart unless-stopped \
  -e ENVIRONMENT=production \
  gcr.io/YOUR_PROJECT_ID/aurelis:latest
```

### Managed Instance Group

```bash
# Create instance template
gcloud compute instance-templates create aurelis-template \
  --machine-type=n1-standard-2 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --tags=aurelis-server \
  --metadata-from-file startup-script=startup.sh

# Create managed instance group
gcloud compute instance-groups managed create aurelis-group \
  --template=aurelis-template \
  --size=3 \
  --zone=us-central1-a

# Set up autoscaling
gcloud compute instance-groups managed set-autoscaling aurelis-group \
  --max-num-replicas=10 \
  --min-num-replicas=3 \
  --target-cpu-utilization=0.7 \
  --zone=us-central1-a
```

## Infrastructure as Code

### Terraform Configuration

**Main Configuration (`main.tf`)**:
```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}

# GKE Cluster
resource "google_container_cluster" "aurelis" {
  name     = "aurelis-cluster"
  location = var.zone

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.aurelis.name
  subnetwork = google_compute_subnetwork.aurelis.name

  master_auth {
    username = ""
    password = ""

    client_certificate_config {
      issue_client_certificate = false
    }
  }
}

resource "google_container_node_pool" "aurelis_nodes" {
  name       = "aurelis-node-pool"
  location   = var.zone
  cluster    = google_container_cluster.aurelis.name
  node_count = 3

  node_config {
    preemptible  = false
    machine_type = "n1-standard-2"

    metadata = {
      disable-legacy-endpoints = "true"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]
  }

  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Cloud Run Service
resource "google_cloud_run_service" "aurelis" {
  name     = "aurelis"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/aurelis:latest"
        
        resources {
          limits = {
            memory = "512Mi"
            cpu    = "1000m"
          }
        }

        env {
          name  = "ENVIRONMENT"
          value = "production"
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "100"
        "run.googleapis.com/cpu-throttling" = "true"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# IAM for Cloud Run
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.aurelis.name
  location = google_cloud_run_service.aurelis.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Load Balancer
resource "google_compute_global_address" "aurelis" {
  name = "aurelis-ip"
}

# SSL Certificate
resource "google_compute_managed_ssl_certificate" "aurelis" {
  name = "aurelis-ssl"

  managed {
    domains = ["api.aurelis.example.com"]
  }
}
```

**Variables (`variables.tf`)**:
```hcl
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}
```

### Deploy with Terraform
```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="project_id=YOUR_PROJECT_ID"

# Apply configuration
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

## Security Configuration

### Identity and Access Management (IAM)

```bash
# Create service account
gcloud iam service-accounts create aurelis-sa \
  --display-name="Aurelis Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:aurelis-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:aurelis-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"
```

### Network Security

```bash
# Create firewall rules
gcloud compute firewall-rules create aurelis-allow-http \
  --allow tcp:80,tcp:443 \
  --source-ranges 0.0.0.0/0 \
  --target-tags aurelis-server

gcloud compute firewall-rules create aurelis-allow-health \
  --allow tcp:8080 \
  --source-ranges 130.211.0.0/22,35.191.0.0/16 \
  --target-tags aurelis-server
```

### Secret Management

```bash
# Store secrets in Secret Manager
gcloud secrets create aurelis-config --data-file=config.json

# Grant access to service account
gcloud secrets add-iam-policy-binding aurelis-config \
  --member="serviceAccount:aurelis-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Monitoring and Logging

### Cloud Monitoring Setup

```bash
# Install monitoring agent (for Compute Engine)
curl -sSO https://dl.google.com/cloudagents/add-monitoring-agent-repo.sh
sudo bash add-monitoring-agent-repo.sh
sudo apt-get update
sudo apt-get install stackdriver-agent
```

### Custom Metrics

```python
# Python code for custom metrics
from google.cloud import monitoring_v3

def send_custom_metric(project_id, metric_value):
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"
    
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/aurelis/requests"
    series.resource.type = "global"
    
    point = series.points.add()
    point.value.double_value = metric_value
    point.interval.end_time.seconds = int(time.time())
    
    client.create_time_series(project_name, [series])
```

### Log Configuration

```yaml
# Fluent Bit configuration for GKE
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: aurelis
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Path              /var/log/containers/*aurelis*.log
        Parser            docker
        Tag               aurelis.*
        Refresh_Interval  5

    [OUTPUT]
        Name  stackdriver
        Match aurelis.*
        google_service_credentials /var/secrets/google/key.json
        resource k8s_container
```

## Auto-scaling

### Horizontal Pod Autoscaler (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aurelis-hpa
  namespace: aurelis
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aurelis-app
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
```

### Vertical Pod Autoscaler (VPA)

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: aurelis-vpa
  namespace: aurelis
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aurelis-app
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: aurelis
      maxAllowed:
        cpu: 1
        memory: 2Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
```

## Networking

### VPC Setup

```bash
# Create VPC network
gcloud compute networks create aurelis-vpc --subnet-mode regional

# Create subnet
gcloud compute networks subnets create aurelis-subnet \
  --network aurelis-vpc \
  --range 10.0.0.0/24 \
  --region us-central1
```

### Load Balancing

```bash
# HTTP(S) Load Balancer
gcloud compute url-maps create aurelis-map \
  --default-service aurelis-backend-service

gcloud compute target-http-proxies create aurelis-proxy \
  --url-map aurelis-map

gcloud compute forwarding-rules create aurelis-rule \
  --global \
  --target-http-proxy aurelis-proxy \
  --ports 80
```

## Cost Optimization

### Best Practices

1. **Right-sizing Resources**:
   ```bash
   # Use preemptible instances for non-critical workloads
   gcloud compute instances create aurelis-preemptible \
     --preemptible \
     --machine-type=n1-standard-1
   ```

2. **Committed Use Discounts**:
   ```bash
   # Purchase committed use contracts
   gcloud compute commitments create aurelis-commitment \
     --plan=12-month \
     --resources=VCPU=10,MEMORY=40GB
   ```

3. **Auto-scaling Configuration**:
   - Set appropriate minimum and maximum replicas
   - Use CPU and memory targets based on actual usage
   - Implement custom metrics for better scaling decisions

### Cost Monitoring

```bash
# Set up budget alerts
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Aurelis Budget" \
  --budget-amount=1000USD \
  --threshold-rules-percent=50,90 \
  --threshold-rules-spend-basis=CURRENT_SPEND
```

## Troubleshooting

### Common Issues

#### GKE Cluster Issues

```bash
# Check cluster status
gcloud container clusters describe aurelis-cluster --zone=us-central1-a

# Check node status
kubectl get nodes
kubectl describe node NODE_NAME

# Check pod logs
kubectl logs -f deployment/aurelis-app -n aurelis
```

#### Cloud Run Issues

```bash
# Check service status
gcloud run services describe aurelis --region=us-central1

# View logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50
```

#### Network Connectivity

```bash
# Test connectivity
gcloud compute ssh aurelis-vm --zone=us-central1-a --command="curl -I http://localhost:8080"

# Check firewall rules
gcloud compute firewall-rules list --filter="name~aurelis"
```

### Debug Commands

```bash
# Container debugging
kubectl exec -it POD_NAME -n aurelis -- /bin/bash

# Port forwarding for local testing
kubectl port-forward service/aurelis-service 8080:80 -n aurelis

# Resource usage monitoring
kubectl top pods -n aurelis
kubectl top nodes
```

### Performance Optimization

1. **Image Optimization**:
   ```dockerfile
   # Multi-stage build for smaller images
   FROM python:3.9-slim as builder
   COPY requirements.txt .
   RUN pip install --user -r requirements.txt

   FROM python:3.9-slim
   COPY --from=builder /root/.local /root/.local
   COPY . .
   CMD ["python", "app.py"]
   ```

2. **Resource Tuning**:
   - Monitor actual resource usage
   - Adjust CPU and memory requests/limits
   - Use node affinity for performance-critical workloads

3. **Caching Strategies**:
   - Implement Redis/Memorystore for caching
   - Use CDN for static content
   - Enable HTTP/2 and compression

### Support Resources

- [GCP Documentation](https://cloud.google.com/docs)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/best-practices)
- [GCP Architecture Center](https://cloud.google.com/architecture)
- [GCP Support](https://cloud.google.com/support)

For additional support, consult the [main deployment documentation](./README.md) or contact the Aurelis development team.
