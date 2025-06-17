# Azure Deployment Guide

Complete guide for deploying Aurelis on Microsoft Azure with enterprise-grade security, scalability, and best practices.

## 📋 Table of Contents

1. [Azure Overview](#azure-overview)
2. [Prerequisites](#prerequisites)
3. [Container Instances](#container-instances)
4. [Kubernetes Service (AKS)](#kubernetes-service-aks)
5. [App Service](#app-service)
6. [Function Apps](#function-apps)
7. [Infrastructure as Code](#infrastructure-as-code)
8. [Security & Compliance](#security--compliance)
9. [Monitoring & Logging](#monitoring--logging)
10. [Auto Scaling](#auto-scaling)
11. [Troubleshooting](#troubleshooting)

## 🚀 Azure Overview

### Architecture Options

#### 1. AKS Deployment (Recommended for Production)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Azure         │───▶│   Azure Cache   │
│   Gateway       │    │   Kubernetes    │    │   for Redis     │
│   (WAF)         │    │   Service       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Azure Front   │    │   Azure         │    │   Azure Key     │
│   Door          │    │   Monitor       │    │   Vault         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### 2. Serverless Deployment (Function Apps)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API           │───▶│   Azure         │───▶│   GitHub Models │
│   Management    │    │   Functions     │    │   API           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Azure CDN     │    │   Cosmos DB     │    │   Blob Storage  │
│                 │    │   Cache         │    │   Results       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Prerequisites

### Azure CLI Setup
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"

# Verify login
az account show
```

### Required Service Principals
```bash
# Create service principal for deployment
az ad sp create-for-rbac \
    --name "aurelis-deployment-sp" \
    --role "Contributor" \
    --scopes "/subscriptions/your-subscription-id" \
    --sdk-auth

# Create service principal for AKS
az ad sp create-for-rbac \
    --name "aurelis-aks-sp" \
    --role "Contributor" \
    --scopes "/subscriptions/your-subscription-id/resourceGroups/aurelis-rg"
```

## 🐳 Container Instances

### Azure Container Registry (ACR)

```bash
# Create resource group
az group create \
    --name aurelis-rg \
    --location eastus

# Create container registry
az acr create \
    --resource-group aurelis-rg \
    --name aurelisacr \
    --sku Premium \
    --admin-enabled true

# Login to ACR
az acr login --name aurelisacr

# Build and push image
docker build -t aurelis:latest .
docker tag aurelis:latest aurelisacr.azurecr.io/aurelis:latest
docker push aurelisacr.azurecr.io/aurelis:latest
```

### Container Instances Deployment

```yaml
# aurelis-aci.yaml
apiVersion: 2019-12-01
location: eastus
name: aurelis-container-group
properties:
  containers:
  - name: aurelis
    properties:
      image: aurelisacr.azurecr.io/aurelis:latest
      resources:
        requests:
          cpu: 1.0
          memoryInGb: 2.0
      ports:
      - port: 8080
        protocol: TCP
      environmentVariables:
      - name: AURELIS_ENVIRONMENT
        value: production
      - name: AURELIS_LOG_LEVEL
        value: INFO
      - name: GITHUB_TOKEN
        secureValue: ${GITHUB_TOKEN}
      volumeMounts:
      - name: cache-volume
        mountPath: /app/.aurelis/cache
        readOnly: false
  imageRegistryCredentials:
  - server: aurelisacr.azurecr.io
    username: aurelisacr
    password: ${ACR_PASSWORD}
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8080
    dnsNameLabel: aurelis-api
  volumes:
  - name: cache-volume
    azureFile:
      shareName: aurelis-cache
      storageAccountName: aurelisstorageaccount
      storageAccountKey: ${STORAGE_ACCOUNT_KEY}
tags:
  Environment: production
  Project: Aurelis
type: Microsoft.ContainerInstance/containerGroups
```

```bash
# Deploy container instance
az container create \
    --resource-group aurelis-rg \
    --file aurelis-aci.yaml

# Get container logs
az container logs \
    --resource-group aurelis-rg \
    --name aurelis-container-group \
    --container-name aurelis

# Get container status
az container show \
    --resource-group aurelis-rg \
    --name aurelis-container-group \
    --query "{FQDN:ipAddress.fqdn,ProvisioningState:provisioningState}" \
    --output table
```

## ☸️ Kubernetes Service (AKS)

### AKS Cluster Setup

```bash
# Create AKS cluster
az aks create \
    --resource-group aurelis-rg \
    --name aurelis-aks \
    --node-count 3 \
    --node-vm-size Standard_DS2_v2 \
    --enable-addons monitoring \
    --enable-managed-identity \
    --attach-acr aurelisacr \
    --kubernetes-version 1.28.3 \
    --zones 1 2 3

# Get credentials
az aks get-credentials \
    --resource-group aurelis-rg \
    --name aurelis-aks

# Verify connection
kubectl get nodes
```

### AKS Deployment Manifests

```yaml
# aurelis-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aurelis-production
  labels:
    name: aurelis-production
    environment: production

---
# aurelis-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: aurelis-secrets
  namespace: aurelis-production
type: Opaque
data:
  github-token: ${GITHUB_TOKEN_B64}

---
# aurelis-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aurelis-config
  namespace: aurelis-production
data:
  config.yaml: |
    github_token: "${GITHUB_TOKEN}"
    environment: "production"
    
    models:
      primary: "codestral-2501"
      fallback: "gpt-4o-mini"
    
    cache:
      enabled: true
      backend: "redis"
      redis_host: "aurelis-redis"
      redis_port: 6379
    
    azure:
      tenant_id: "${AZURE_TENANT_ID}"
      subscription_id: "${AZURE_SUBSCRIPTION_ID}"
      resource_group: "aurelis-rg"
      
    monitoring:
      enabled: true
      azure_monitor: true
      log_analytics_workspace: "aurelis-workspace"

---
# aurelis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurelis-deployment
  namespace: aurelis-production
  labels:
    app: aurelis
    version: v1.0.0
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
      containers:
      - name: aurelis
        image: aurelisacr.azurecr.io/aurelis:latest
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
        - name: AURELIS_ENVIRONMENT
          value: "production"
        - name: AZURE_CLIENT_ID
          value: "${AZURE_CLIENT_ID}"
        volumeMounts:
        - name: config-volume
          mountPath: /etc/aurelis
          readOnly: true
        - name: cache-volume
          mountPath: /app/.aurelis/cache
        - name: tmp-volume
          mountPath: /tmp
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
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
      - name: tmp-volume
        emptyDir:
          sizeLimit: 1Gi

---
# aurelis-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: aurelis-service
  namespace: aurelis-production
  labels:
    app: aurelis
spec:
  selector:
    app: aurelis
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP
  - name: metrics
    port: 9090
    targetPort: 9090
    protocol: TCP
  type: ClusterIP

---
# aurelis-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aurelis-ingress
  namespace: aurelis-production
  annotations:
    kubernetes.io/ingress.class: "azure/application-gateway"
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
    appgw.ingress.kubernetes.io/backend-protocol: "http"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - aurelis.yourdomain.com
    secretName: aurelis-tls-secret
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
# aurelis-hpa.yaml
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
  maxReplicas: 10
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
```

## 🌐 App Service

### App Service Plan

```bash
# Create App Service Plan
az appservice plan create \
    --name aurelis-plan \
    --resource-group aurelis-rg \
    --location eastus \
    --sku P1V3 \
    --is-linux

# Create Web App
az webapp create \
    --resource-group aurelis-rg \
    --plan aurelis-plan \
    --name aurelis-webapp \
    --deployment-container-image-name aurelisacr.azurecr.io/aurelis:latest

# Configure container settings
az webapp config container set \
    --name aurelis-webapp \
    --resource-group aurelis-rg \
    --docker-custom-image-name aurelisacr.azurecr.io/aurelis:latest \
    --docker-registry-server-url https://aurelisacr.azurecr.io \
    --docker-registry-server-user aurelisacr \
    --docker-registry-server-password ${ACR_PASSWORD}
```

### App Service Configuration

```bash
# Set environment variables
az webapp config appsettings set \
    --resource-group aurelis-rg \
    --name aurelis-webapp \
    --settings \
        GITHUB_TOKEN="@Microsoft.KeyVault(SecretUri=https://aurelis-keyvault.vault.azure.net/secrets/github-token/)" \
        AURELIS_ENVIRONMENT="production" \
        AURELIS_LOG_LEVEL="INFO" \
        WEBSITES_PORT="8080" \
        WEBSITES_CONTAINER_START_TIME_LIMIT="1800"

# Enable logging
az webapp log config \
    --resource-group aurelis-rg \
    --name aurelis-webapp \
    --application-logging filesystem \
    --detailed-error-messages true \
    --failed-request-tracing true \
    --web-server-logging filesystem

# Configure custom domain
az webapp config hostname add \
    --webapp-name aurelis-webapp \
    --resource-group aurelis-rg \
    --hostname aurelis.yourdomain.com

# Enable SSL
az webapp config ssl bind \
    --certificate-thumbprint ${CERT_THUMBPRINT} \
    --ssl-type SNI \
    --name aurelis-webapp \
    --resource-group aurelis-rg
```

## ⚡ Function Apps

### Function App Setup

```bash
# Create storage account
az storage account create \
    --name aurelisstorageaccount \
    --location eastus \
    --resource-group aurelis-rg \
    --sku Standard_LRS

# Create Function App
az functionapp create \
    --resource-group aurelis-rg \
    --consumption-plan-location eastus \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --name aurelis-functions \
    --storage-account aurelisstorageaccount \
    --os-type Linux

# Configure application settings
az functionapp config appsettings set \
    --name aurelis-functions \
    --resource-group aurelis-rg \
    --settings \
        GITHUB_TOKEN="@Microsoft.KeyVault(SecretUri=https://aurelis-keyvault.vault.azure.net/secrets/github-token/)" \
        AURELIS_ENVIRONMENT="production" \
        AzureWebJobsFeatureFlags="EnableWorkerIndexing"
```

### Function Implementation

```python
# function_app.py
import azure.functions as func
import json
import logging
import os
from typing import Dict, Any
from aurelis.core import AurelisCore
from aurelis.cache.cosmosdb import CosmosDBCache

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Global variable for connection reuse
aurelis_core = None

def get_aurelis_core():
    """Initialize Aurelis with Azure configuration."""
    global aurelis_core
    
    if aurelis_core is None:
        # Get GitHub token from environment (Key Vault reference)
        github_token = os.environ.get('GITHUB_TOKEN')
        
        # Configure cache with Cosmos DB
        cache = CosmosDBCache(
            endpoint=os.environ.get('COSMOS_DB_ENDPOINT'),
            key=os.environ.get('COSMOS_DB_KEY'),
            database_name='aurelis-cache',
            container_name='cache-items'
        )
        
        # Initialize Aurelis
        aurelis_core = AurelisCore(
            github_token=github_token,
            cache=cache,
            environment='production'
        )
    
    return aurelis_core

@app.route(route="analyze", methods=["POST"])
def analyze_code(req: func.HttpRequest) -> func.HttpResponse:
    """Analyze code using Aurelis."""
    logging.info('Code analysis request received')
    
    try:
        aurelis = get_aurelis_core()
        
        # Parse request body
        req_body = req.get_json()
        
        if not req_body:
            return func.HttpResponse(
                json.dumps({
                    'error': 'Request body is required',
                    'message': 'Please provide JSON body with code and language'
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        code = req_body.get('code', '')
        language = req_body.get('language', 'python')
        analysis_types = req_body.get('analysis_types', ['quality', 'complexity'])
        
        if not code:
            return func.HttpResponse(
                json.dumps({
                    'error': 'Code is required',
                    'message': 'Please provide code to analyze'
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Perform analysis
        result = aurelis.analyze_code(
            code=code,
            language=language,
            analysis_types=analysis_types,
            include_suggestions=True,
            include_metrics=True
        )
        
        return func.HttpResponse(
            json.dumps({
                'success': True,
                'result': result
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                'error': 'Analysis failed',
                'message': str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="models", methods=["GET"])
def list_models(req: func.HttpRequest) -> func.HttpResponse:
    """List available models."""
    logging.info('Models list request received')
    
    try:
        aurelis = get_aurelis_core()
        models = aurelis.list_available_models()
        
        return func.HttpResponse(
            json.dumps({
                'success': True,
                'models': models
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Failed to list models: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                'error': 'Failed to list models',
                'message': str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="docs", methods=["POST"])
def generate_docs(req: func.HttpRequest) -> func.HttpResponse:
    """Generate documentation."""
    logging.info('Documentation generation request received')
    
    try:
        aurelis = get_aurelis_core()
        
        # Parse request body
        req_body = req.get_json()
        
        if not req_body:
            return func.HttpResponse(
                json.dumps({
                    'error': 'Request body is required',
                    'message': 'Please provide JSON body with code'
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        code = req_body.get('code', '')
        format_type = req_body.get('format', 'markdown')
        include_examples = req_body.get('include_examples', True)
        
        if not code:
            return func.HttpResponse(
                json.dumps({
                    'error': 'Code is required',
                    'message': 'Please provide code to document'
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Generate documentation
        docs = aurelis.generate_documentation(
            code=code,
            format=format_type,
            include_examples=include_examples
        )
        
        return func.HttpResponse(
            json.dumps({
                'success': True,
                'documentation': docs
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Documentation generation failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                'error': 'Documentation generation failed',
                'message': str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    try:
        return func.HttpResponse(
            json.dumps({
                'status': 'healthy',
                'timestamp': func.datetime.datetime.utcnow().isoformat(),
                'version': '1.0.0'
            }),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                'status': 'unhealthy',
                'error': str(e)
            }),
            status_code=503,
            mimetype="application/json"
        )
```

## 🏗️ Infrastructure as Code

### ARM Template

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "projectName": {
      "type": "string",
      "defaultValue": "aurelis"
    },
    "environment": {
      "type": "string",
      "defaultValue": "production"
    },
    "githubToken": {
      "type": "securestring"
    },
    "location": {
      "type": "string",
      "defaultValue": "[resourceGroup().location]"
    }
  },
  "variables": {
    "uniqueId": "[substring(uniqueString(resourceGroup().id), 0, 6)]",
    "acrName": "[concat(parameters('projectName'), 'acr', variables('uniqueId'))]",
    "aksName": "[concat(parameters('projectName'), '-aks-', parameters('environment'))]",
    "keyVaultName": "[concat(parameters('projectName'), '-kv-', variables('uniqueId'))]",
    "logAnalyticsName": "[concat(parameters('projectName'), '-logs-', parameters('environment'))]",
    "appInsightsName": "[concat(parameters('projectName'), '-ai-', parameters('environment'))]"
  },
  "resources": [
    {
      "type": "Microsoft.ContainerRegistry/registries",
      "apiVersion": "2021-06-01-preview",
      "name": "[variables('acrName')]",
      "location": "[parameters('location')]",
      "sku": {
        "name": "Premium"
      },
      "properties": {
        "adminUserEnabled": true,
        "networkRuleSet": {
          "defaultAction": "Allow"
        },
        "policies": {
          "quarantinePolicy": {
            "status": "enabled"
          },
          "trustPolicy": {
            "type": "Notary",
            "status": "enabled"
          },
          "retentionPolicy": {
            "days": 30,
            "status": "enabled"
          }
        }
      }
    },
    {
      "type": "Microsoft.KeyVault/vaults",
      "apiVersion": "2021-04-01-preview",
      "name": "[variables('keyVaultName')]",
      "location": "[parameters('location')]",
      "properties": {
        "sku": {
          "family": "A",
          "name": "standard"
        },
        "tenantId": "[subscription().tenantId]",
        "accessPolicies": [],
        "enabledForDeployment": false,
        "enabledForDiskEncryption": false,
        "enabledForTemplateDeployment": true,
        "enableSoftDelete": true,
        "softDeleteRetentionInDays": 90,
        "enableRbacAuthorization": true,
        "networkAcls": {
          "defaultAction": "Allow",
          "bypass": "AzureServices"
        }
      }
    },
    {
      "type": "Microsoft.KeyVault/vaults/secrets",
      "apiVersion": "2021-04-01-preview",
      "name": "[concat(variables('keyVaultName'), '/github-token')]",
      "dependsOn": [
        "[resourceId('Microsoft.KeyVault/vaults', variables('keyVaultName'))]"
      ],
      "properties": {
        "value": "[parameters('githubToken')]",
        "contentType": "GitHub API Token",
        "attributes": {
          "enabled": true
        }
      }
    },
    {
      "type": "Microsoft.OperationalInsights/workspaces",
      "apiVersion": "2021-06-01",
      "name": "[variables('logAnalyticsName')]",
      "location": "[parameters('location')]",
      "properties": {
        "sku": {
          "name": "PerGB2018"
        },
        "retentionInDays": 30,
        "features": {
          "enableLogAccessUsingOnlyResourcePermissions": true
        }
      }
    },
    {
      "type": "Microsoft.Insights/components",
      "apiVersion": "2020-02-02",
      "name": "[variables('appInsightsName')]",
      "location": "[parameters('location')]",
      "kind": "web",
      "dependsOn": [
        "[resourceId('Microsoft.OperationalInsights/workspaces', variables('logAnalyticsName'))]"
      ],
      "properties": {
        "Application_Type": "web",
        "WorkspaceResourceId": "[resourceId('Microsoft.OperationalInsights/workspaces', variables('logAnalyticsName'))]"
      }
    },
    {
      "type": "Microsoft.ContainerService/managedClusters",
      "apiVersion": "2021-05-01",
      "name": "[variables('aksName')]",
      "location": "[parameters('location')]",
      "dependsOn": [
        "[resourceId('Microsoft.OperationalInsights/workspaces', variables('logAnalyticsName'))]"
      ],
      "identity": {
        "type": "SystemAssigned"
      },
      "properties": {
        "kubernetesVersion": "1.21.2",
        "dnsPrefix": "[variables('aksName')]",
        "agentPoolProfiles": [
          {
            "name": "nodepool1",
            "count": 3,
            "vmSize": "Standard_DS2_v2",
            "osType": "Linux",
            "mode": "System",
            "availabilityZones": [
              "1",
              "2",
              "3"
            ]
          }
        ],
        "networkProfile": {
          "networkPlugin": "azure",
          "serviceCidr": "10.0.0.0/16",
          "dnsServiceIP": "10.0.0.10"
        },
        "addonProfiles": {
          "omsagent": {
            "enabled": true,
            "config": {
              "logAnalyticsWorkspaceResourceID": "[resourceId('Microsoft.OperationalInsights/workspaces', variables('logAnalyticsName'))]"
            }
          },
          "azureKeyvaultSecretsProvider": {
            "enabled": true
          }
        }
      }
    }
  ],
  "outputs": {
    "acrLoginServer": {
      "type": "string",
      "value": "[reference(resourceId('Microsoft.ContainerRegistry/registries', variables('acrName'))).loginServer]"
    },
    "aksClusterName": {
      "type": "string",
      "value": "[variables('aksName')]"
    },
    "keyVaultName": {
      "type": "string",
      "value": "[variables('keyVaultName')]"
    }
  }
}
```

### Bicep Template

```bicep
// main.bicep
@description('Project name')
param projectName string = 'aurelis'

@description('Environment name')
param environment string = 'production'

@description('GitHub token for Aurelis API access')
@secure()
param githubToken string

@description('Location for all resources')
param location string = resourceGroup().location

var uniqueId = substring(uniqueString(resourceGroup().id), 0, 6)
var acrName = '${projectName}acr${uniqueId}'
var aksName = '${projectName}-aks-${environment}'
var keyVaultName = '${projectName}-kv-${uniqueId}'
var logAnalyticsName = '${projectName}-logs-${environment}'
var appInsightsName = '${projectName}-ai-${environment}'

// Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2021-06-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Premium'
  }
  properties: {
    adminUserEnabled: true
    networkRuleSet: {
      defaultAction: 'Allow'
    }
    policies: {
      quarantinePolicy: {
        status: 'enabled'
      }
      trustPolicy: {
        type: 'Notary'
        status: 'enabled'
      }
      retentionPolicy: {
        days: 30
        status: 'enabled'
      }
    }
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2021-04-01-preview' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Key Vault Secret
resource githubTokenSecret 'Microsoft.KeyVault/vaults/secrets@2021-04-01-preview' = {
  parent: keyVault
  name: 'github-token'
  properties: {
    value: githubToken
    contentType: 'GitHub API Token'
    attributes: {
      enabled: true
    }
  }
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// AKS Cluster
resource aks 'Microsoft.ContainerService/managedClusters@2021-05-01' = {
  name: aksName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: '1.21.2'
    dnsPrefix: aksName
    agentPoolProfiles: [
      {
        name: 'nodepool1'
        count: 3
        vmSize: 'Standard_DS2_v2'
        osType: 'Linux'
        mode: 'System'
        availabilityZones: [
          '1'
          '2'
          '3'
        ]
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      serviceCidr: '10.0.0.0/16'
      dnsServiceIP: '10.0.0.10'
    }
    addonProfiles: {
      omsagent: {
        enabled: true
        config: {
          logAnalyticsWorkspaceResourceID: logAnalytics.id
        }
      }
      azureKeyvaultSecretsProvider: {
        enabled: true
      }
    }
  }
}

// Role assignment for ACR access
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(resourceGroup().id, aks.id, 'acrPull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: aks.properties.identityProfile.kubeletidentity.objectId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output acrLoginServer string = acr.properties.loginServer
output aksClusterName string = aks.name
output keyVaultName string = keyVault.name
```

## 🔒 Security & Compliance

### Azure Security Center Integration

```json
{
  "policyDefinitionId": "/providers/Microsoft.Authorization/policyDefinitions/febd0533-8e55-448f-b837-bd0e06f16469",
  "displayName": "Aurelis Security Policy",
  "description": "Security policy for Aurelis deployment",
  "policyRule": {
    "if": {
      "allOf": [
        {
          "field": "type",
          "equals": "Microsoft.ContainerService/managedClusters"
        },
        {
          "field": "name",
          "like": "aurelis-*"
        }
      ]
    },
    "then": {
      "effect": "audit",
      "details": {
        "type": "Microsoft.Security/assessments",
        "name": "cluster-security-assessment"
      }
    }
  }
}
```

### Network Security Groups

```bash
# Create NSG for AKS
az network nsg create \
    --resource-group aurelis-rg \
    --name aurelis-aks-nsg

# Allow HTTPS traffic
az network nsg rule create \
    --resource-group aurelis-rg \
    --nsg-name aurelis-aks-nsg \
    --name AllowHTTPS \
    --protocol tcp \
    --priority 1000 \
    --destination-port-range 443 \
    --access allow

# Allow HTTP traffic (redirect to HTTPS)
az network nsg rule create \
    --resource-group aurelis-rg \
    --nsg-name aurelis-aks-nsg \
    --name AllowHTTP \
    --protocol tcp \
    --priority 1001 \
    --destination-port-range 80 \
    --access allow

# Deny all other inbound traffic
az network nsg rule create \
    --resource-group aurelis-rg \
    --nsg-name aurelis-aks-nsg \
    --name DenyAllInbound \
    --protocol '*' \
    --priority 4096 \
    --destination-port-range '*' \
    --access deny
```

## 📊 Monitoring & Logging

### Azure Monitor Configuration

```bash
# Create action group
az monitor action-group create \
    --resource-group aurelis-rg \
    --name aurelis-alerts \
    --short-name aurelis \
    --email-receivers \
        name=admin \
        email=admin@yourdomain.com

# Create CPU usage alert
az monitor metrics alert create \
    --name "High CPU Usage" \
    --resource-group aurelis-rg \
    --scopes "/subscriptions/{subscription-id}/resourceGroups/aurelis-rg/providers/Microsoft.ContainerService/managedClusters/aurelis-aks" \
    --condition "avg Percentage CPU > 80" \
    --description "Alert when CPU usage is high" \
    --evaluation-frequency 5m \
    --window-size 15m \
    --severity 2 \
    --action aurelis-alerts

# Create memory usage alert
az monitor metrics alert create \
    --name "High Memory Usage" \
    --resource-group aurelis-rg \
    --scopes "/subscriptions/{subscription-id}/resourceGroups/aurelis-rg/providers/Microsoft.ContainerService/managedClusters/aurelis-aks" \
    --condition "avg Percentage Memory > 85" \
    --description "Alert when memory usage is high" \
    --evaluation-frequency 5m \
    --window-size 15m \
    --severity 2 \
    --action aurelis-alerts
```

### Application Insights Integration

```python
# monitoring.py
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
import logging
import os

class AzureMonitoring:
    def __init__(self):
        # Configure Application Insights
        connection_string = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = AzureLogHandler(connection_string=connection_string)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Setup metrics
        self.stats = stats_module.stats
        self.view_manager = self.stats.view_manager
        self.stats_recorder = self.stats.stats_recorder
        
        # Create measures
        self.request_count_measure = measure_module.MeasureInt(
            "aurelis_requests", "Number of requests", "1"
        )
        self.request_duration_measure = measure_module.MeasureFloat(
            "aurelis_request_duration", "Request duration", "ms"
        )
        
        # Create views
        request_count_view = view_module.View(
            "aurelis_request_count",
            "Number of requests",
            [],
            self.request_count_measure,
            aggregation_module.CountAggregation()
        )
        
        request_duration_view = view_module.View(
            "aurelis_request_duration_distribution",
            "Request duration distribution",
            [],
            self.request_duration_measure,
            aggregation_module.DistributionAggregation([0, 100, 500, 1000, 2000, 5000])
        )
        
        # Register views
        self.view_manager.register_view(request_count_view)
        self.view_manager.register_view(request_duration_view)
        
        # Setup metrics exporter
        exporter = metrics_exporter.new_metrics_exporter(
            connection_string=connection_string
        )
        self.view_manager.register_exporter(exporter)
    
    def log_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Log request information."""
        self.logger.info(
            f"Request processed",
            extra={
                'custom_dimensions': {
                    'method': method,
                    'endpoint': endpoint,
                    'status_code': status_code,
                    'duration_ms': duration
                }
            }
        )
        
        # Record metrics
        mmap = self.stats_recorder.new_measurement_map()
        mmap.measure_int_put(self.request_count_measure, 1)
        mmap.measure_float_put(self.request_duration_measure, duration)
        mmap.record()
    
    def log_error(self, error: Exception, context: dict = None):
        """Log error information."""
        self.logger.exception(
            f"Error occurred: {str(error)}",
            extra={
                'custom_dimensions': context or {}
            }
        )
```

## 📈 Auto Scaling

### AKS Cluster Autoscaler

```bash
# Enable cluster autoscaler
az aks update \
    --resource-group aurelis-rg \
    --name aurelis-aks \
    --enable-cluster-autoscaler \
    --min-count 3 \
    --max-count 10

# Update autoscaler settings
az aks update \
    --resource-group aurelis-rg \
    --name aurelis-aks \
    --cluster-autoscaler-profile \
        scale-down-delay-after-add=10m \
        scale-down-unneeded-time=10m \
        scale-down-delay-after-failure=3m \
        scale-down-utilization-threshold=0.5
```

### KEDA for Event-Driven Scaling

```yaml
# keda-scaler.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: aurelis-scaler
  namespace: aurelis-production
spec:
  scaleTargetRef:
    name: aurelis-deployment
  minReplicaCount: 3
  maxReplicaCount: 20
  triggers:
  - type: azure-servicebus
    metadata:
      queueName: aurelis-requests
      connectionFromEnv: SERVICEBUS_CONNECTION_STRING
      queueLength: '5'
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: aurelis_request_rate
      threshold: '100'
      query: rate(aurelis_requests_total[1m])
```

## 🔧 Troubleshooting

### Common Azure Issues

#### 1. AKS Connectivity Issues

```bash
# Check AKS cluster status
az aks show \
    --resource-group aurelis-rg \
    --name aurelis-aks \
    --query powerState

# Get cluster credentials
az aks get-credentials \
    --resource-group aurelis-rg \
    --name aurelis-aks \
    --overwrite-existing

# Check node status
kubectl get nodes -o wide

# Check pod logs
kubectl logs -n aurelis-production \
    deployment/aurelis-deployment \
    --previous

# Check events
kubectl get events -n aurelis-production \
    --sort-by='.metadata.creationTimestamp'
```

#### 2. ACR Authentication Issues

```bash
# Check ACR login
az acr login --name aurelisacr

# Get ACR credentials
az acr credential show --name aurelisacr

# Test image pull
docker pull aurelisacr.azurecr.io/aurelis:latest

# Check AKS ACR integration
az aks check-acr \
    --resource-group aurelis-rg \
    --name aurelis-aks \
    --acr aurelisacr
```

#### 3. Key Vault Access Issues

```bash
# Check Key Vault access policies
az keyvault show \
    --name aurelis-keyvault \
    --query properties.accessPolicies

# Test secret retrieval
az keyvault secret show \
    --vault-name aurelis-keyvault \
    --name github-token

# Check managed identity permissions
az role assignment list \
    --assignee $(az aks show --resource-group aurelis-rg --name aurelis-aks --query identity.principalId -o tsv)
```

#### 4. Function App Issues

```bash
# Check function app status
az functionapp show \
    --resource-group aurelis-rg \
    --name aurelis-functions \
    --query state

# Stream function logs
az webapp log tail \
    --resource-group aurelis-rg \
    --name aurelis-functions

# Check function app settings
az functionapp config appsettings list \
    --resource-group aurelis-rg \
    --name aurelis-functions
```

### Performance Optimization

#### AKS Performance Tuning

```yaml
# performance-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aurelis-performance-config
  namespace: aurelis-production
data:
  nginx.conf: |
    worker_processes auto;
    worker_rlimit_nofile 65535;
    
    events {
        worker_connections 4096;
        use epoll;
        multi_accept on;
    }
    
    http {
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        keepalive_requests 1000;
        
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types
            text/plain
            text/css
            application/json
            application/javascript
            text/xml
            application/xml
            application/xml+rss
            text/javascript;
    }
```

#### Function App Optimization

```json
{
  "functionTimeout": "00:05:00",
  "extensions": {
    "http": {
      "routePrefix": "",
      "maxConcurrentRequests": 100,
      "maxOutstandingRequests": 200
    },
    "cosmosDB": {
      "connectionMode": "Direct",
      "protocol": "Tcp"
    }
  },
  "managedDependency": {
    "enabled": true
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[3.*, 4.0.0)"
  }
}
```

## 📚 See Also

- [Production Deployment Guide](production-deployment.md)
- [Container Deployment Guide](container-deployment.md)
- [CI/CD Integration Guide](cicd-integration.md)
- [Monitoring Guide](monitoring.md)
- [AWS Deployment Guide](aws-deployment.md)
- [GCP Deployment Guide](gcp-deployment.md)
