# AWS Deployment Guide

Complete guide for deploying Aurelis on Amazon Web Services (AWS) with enterprise-grade security, scalability, and best practices.

## 📋 Table of Contents

1. [AWS Overview](#aws-overview)
2. [Prerequisites](#prerequisites)
3. [ECS Deployment](#ecs-deployment)
4. [EKS Deployment](#eks-deployment)
5. [Lambda Deployment](#lambda-deployment)
6. [Infrastructure as Code](#infrastructure-as-code)
7. [Security & Compliance](#security--compliance)
8. [Monitoring & Logging](#monitoring--logging)
9. [Auto Scaling](#auto-scaling)
10. [Troubleshooting](#troubleshooting)

## 🚀 AWS Overview

### Architecture Options

#### 1. Containerized Deployment (ECS/EKS)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Elastic       │───▶│   RDS/Cache     │
│   Load Balancer │    │   Container     │    │   Services      │
│   (ALB)         │    │   Service       │    │   (ElastiCache) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AWS WAF       │    │   CloudWatch    │    │   AWS Secrets   │
│   Security      │    │   Monitoring    │    │   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### 2. Serverless Deployment (Lambda)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │───▶│   Lambda        │───▶│   GitHub Models │
│   REST/HTTP     │    │   Function      │    │   API           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   DynamoDB      │    │   S3 Storage    │
│   CDN           │    │   Cache         │    │   Results       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Prerequisites

### AWS Account Setup
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Required IAM Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:*",
        "ecr:*",
        "ec2:*",
        "iam:PassRole",
        "logs:*",
        "cloudwatch:*",
        "secretsmanager:*",
        "elasticache:*",
        "rds:*",
        "elasticloadbalancing:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🐳 ECS Deployment

### 1. ECR Repository Setup

```bash
# Create ECR repository
aws ecr create-repository \
    --repository-name aurelis \
    --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS \
    --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build and push image
docker build -t aurelis:latest .
docker tag aurelis:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/aurelis:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/aurelis:latest
```

### 2. ECS Cluster Setup

```json
{
  "family": "aurelis-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/aurelis-task-role",
  "containerDefinitions": [
    {
      "name": "aurelis",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/aurelis:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AURELIS_ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "AURELIS_LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "GITHUB_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:aurelis/github-token"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/aurelis",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8080/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### 3. ECS Service Configuration

```json
{
  "serviceName": "aurelis-service",
  "cluster": "aurelis-cluster",
  "taskDefinition": "aurelis-task:1",
  "desiredCount": 3,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": [
        "subnet-12345678",
        "subnet-87654321"
      ],
      "securityGroups": [
        "sg-aurelis-app"
      ],
      "assignPublicIp": "DISABLED"
    }
  },
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/aurelis-tg/1234567890123456",
      "containerName": "aurelis",
      "containerPort": 8080
    }
  ],
  "serviceRegistries": [
    {
      "registryArn": "arn:aws:servicediscovery:us-east-1:123456789012:service/srv-aurelis"
    }
  ]
}
```

## ☸️ EKS Deployment

### 1. EKS Cluster Setup

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create EKS cluster
eksctl create cluster \
    --name aurelis-cluster \
    --version 1.28 \
    --region us-east-1 \
    --nodegroup-name aurelis-nodes \
    --node-type t3.medium \
    --nodes 3 \
    --nodes-min 2 \
    --nodes-max 5 \
    --ssh-access \
    --ssh-public-key ~/.ssh/id_rsa.pub \
    --managed
```

### 2. Kubernetes Deployment

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
stringData:
  github-token: "${GITHUB_TOKEN}"

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
    
    logging:
      level: "INFO"
      format: "structured"

---
# aurelis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurelis-deployment
  namespace: aurelis-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aurelis
  template:
    metadata:
      labels:
        app: aurelis
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      serviceAccountName: aurelis-sa
      containers:
      - name: aurelis
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/aurelis:latest
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: aurelis-secrets
              key: github-token
        - name: AURELIS_CONFIG
          value: "/etc/aurelis/config.yaml"
        volumeMounts:
        - name: config-volume
          mountPath: /etc/aurelis
        - name: cache-volume
          mountPath: /app/.aurelis/cache
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
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: config-volume
        configMap:
          name: aurelis-config
      - name: cache-volume
        persistentVolumeClaim:
          claimName: aurelis-cache-pvc

---
# aurelis-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: aurelis-service
  namespace: aurelis-production
spec:
  selector:
    app: aurelis
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: metrics
    port: 9090
    targetPort: 9090
  type: ClusterIP

---
# aurelis-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aurelis-ingress
  namespace: aurelis-production
  annotations:
    kubernetes.io/ingress.class: "aws-load-balancer-controller"
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/ssl-policy: ELBSecurityPolicy-TLS-1-2-2017-01
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
```

## ⚡ Lambda Deployment

### 1. Serverless Framework Configuration

```yaml
# serverless.yml
service: aurelis-serverless
frameworkVersion: '3'

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'prod'}
  timeout: 300
  memorySize: 1024
  
  environment:
    STAGE: ${self:provider.stage}
    AURELIS_ENVIRONMENT: production
    
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - secretsmanager:GetSecretValue
          Resource: 
            - "arn:aws:secretsmanager:${aws:region}:${aws:accountId}:secret:aurelis/*"
        - Effect: Allow
          Action:
            - dynamodb:Query
            - dynamodb:Scan
            - dynamodb:GetItem
            - dynamodb:PutItem
            - dynamodb:UpdateItem
            - dynamodb:DeleteItem
          Resource:
            - "arn:aws:dynamodb:${aws:region}:${aws:accountId}:table/aurelis-cache"

functions:
  analyze:
    handler: handlers.analyze_handler
    events:
      - http:
          path: /analyze
          method: post
          cors: true
          authorizer:
            name: aurelis-authorizer
            resultTtlInSeconds: 300
    layers:
      - ${cf:aurelis-layers-${self:provider.stage}.AurelisLayerExport}
    
  models:
    handler: handlers.models_handler
    events:
      - http:
          path: /models
          method: get
          cors: true
    
  docs:
    handler: handlers.docs_handler
    events:
      - http:
          path: /docs
          method: post
          cors: true

  authorizer:
    handler: auth.lambda_authorizer

resources:
  Resources:
    AurelisCacheTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: aurelis-cache
        BillingMode: PAY_PER_REQUEST
        AttributeDefinitions:
          - AttributeName: cache_key
            AttributeType: S
        KeySchema:
          - AttributeName: cache_key
            KeyType: HASH
        TimeToLiveSpecification:
          AttributeName: ttl
          Enabled: true
        
    AurelisApiGateway:
      Type: AWS::ApiGateway::RestApi
      Properties:
        Name: aurelis-api-${self:provider.stage}
        Description: Aurelis Code Analysis API
        EndpointConfiguration:
          Types:
            - REGIONAL

plugins:
  - serverless-python-requirements
  - serverless-plugin-warmup

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true
  warmup:
    enabled: true
    events:
      - schedule: rate(5 minutes)
    timeout: 20
```

### 2. Lambda Handlers

```python
# handlers.py
import json
import os
import boto3
from typing import Dict, Any
from aurelis.core import AurelisCore
from aurelis.models import ModelRequest
from aurelis.cache.dynamodb import DynamoDBCache

def get_aurelis_core():
    """Initialize Aurelis with AWS configuration."""
    
    # Get GitHub token from Secrets Manager
    secrets_client = boto3.client('secretsmanager')
    secret_response = secrets_client.get_secret_value(
        SecretId='aurelis/production/github-token'
    )
    github_token = json.loads(secret_response['SecretString'])['github_token']
    
    # Configure cache
    cache = DynamoDBCache(table_name='aurelis-cache')
    
    # Initialize Aurelis
    core = AurelisCore(
        github_token=github_token,
        cache=cache,
        environment='production'
    )
    
    return core

def lambda_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized Lambda response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body)
    }

def analyze_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle code analysis requests."""
    try:
        aurelis = get_aurelis_core()
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        code = body.get('code', '')
        language = body.get('language', 'python')
        
        if not code:
            return lambda_response(400, {
                'error': 'Code is required',
                'message': 'Please provide code to analyze'
            })
        
        # Perform analysis
        result = aurelis.analyze_code(
            code=code,
            language=language,
            include_suggestions=True,
            include_metrics=True
        )
        
        return lambda_response(200, {
            'success': True,
            'result': result,
            'execution_time': getattr(context, 'get_remaining_time_in_millis', lambda: 0)()
        })
        
    except Exception as e:
        return lambda_response(500, {
            'error': 'Analysis failed',
            'message': str(e)
        })

def models_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle model listing requests."""
    try:
        aurelis = get_aurelis_core()
        models = aurelis.list_available_models()
        
        return lambda_response(200, {
            'success': True,
            'models': models
        })
        
    except Exception as e:
        return lambda_response(500, {
            'error': 'Failed to list models',
            'message': str(e)
        })

def docs_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle documentation generation requests."""
    try:
        aurelis = get_aurelis_core()
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        code = body.get('code', '')
        format_type = body.get('format', 'markdown')
        
        if not code:
            return lambda_response(400, {
                'error': 'Code is required',
                'message': 'Please provide code to document'
            })
        
        # Generate documentation
        docs = aurelis.generate_documentation(
            code=code,
            format=format_type
        )
        
        return lambda_response(200, {
            'success': True,
            'documentation': docs
        })
        
    except Exception as e:
        return lambda_response(500, {
            'error': 'Documentation generation failed',
            'message': str(e)
        })
```

## 🏗️ Infrastructure as Code

### Terraform Configuration

```hcl
# main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "aurelis-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Aurelis"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "github_token" {
  description = "GitHub token for Aurelis"
  type        = string
  sensitive   = true
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Configuration
resource "aws_vpc" "aurelis_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "aurelis-vpc-${var.environment}"
  }
}

resource "aws_subnet" "aurelis_private" {
  count             = 2
  vpc_id            = aws_vpc.aurelis_vpc.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "aurelis-private-${count.index + 1}-${var.environment}"
    Type = "Private"
  }
}

resource "aws_subnet" "aurelis_public" {
  count                   = 2
  vpc_id                  = aws_vpc.aurelis_vpc.id
  cidr_block              = "10.0.${count.index + 10}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "aurelis-public-${count.index + 1}-${var.environment}"
    Type = "Public"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "aurelis_igw" {
  vpc_id = aws_vpc.aurelis_vpc.id
  
  tags = {
    Name = "aurelis-igw-${var.environment}"
  }
}

# NAT Gateway
resource "aws_eip" "aurelis_nat" {
  count  = 2
  domain = "vpc"
  
  tags = {
    Name = "aurelis-nat-eip-${count.index + 1}-${var.environment}"
  }
}

resource "aws_nat_gateway" "aurelis_nat" {
  count         = 2
  allocation_id = aws_eip.aurelis_nat[count.index].id
  subnet_id     = aws_subnet.aurelis_public[count.index].id
  
  tags = {
    Name = "aurelis-nat-${count.index + 1}-${var.environment}"
  }
}

# Route Tables
resource "aws_route_table" "aurelis_private" {
  count  = 2
  vpc_id = aws_vpc.aurelis_vpc.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.aurelis_nat[count.index].id
  }
  
  tags = {
    Name = "aurelis-private-rt-${count.index + 1}-${var.environment}"
  }
}

resource "aws_route_table" "aurelis_public" {
  vpc_id = aws_vpc.aurelis_vpc.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.aurelis_igw.id
  }
  
  tags = {
    Name = "aurelis-public-rt-${var.environment}"
  }
}

# Route Table Associations
resource "aws_route_table_association" "aurelis_private" {
  count          = 2
  subnet_id      = aws_subnet.aurelis_private[count.index].id
  route_table_id = aws_route_table.aurelis_private[count.index].id
}

resource "aws_route_table_association" "aurelis_public" {
  count          = 2
  subnet_id      = aws_subnet.aurelis_public[count.index].id
  route_table_id = aws_route_table.aurelis_public.id
}

# Security Groups
resource "aws_security_group" "aurelis_alb" {
  name_prefix = "aurelis-alb-${var.environment}-"
  vpc_id      = aws_vpc.aurelis_vpc.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "aurelis-alb-sg-${var.environment}"
  }
}

resource "aws_security_group" "aurelis_app" {
  name_prefix = "aurelis-app-${var.environment}-"
  vpc_id      = aws_vpc.aurelis_vpc.id
  
  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.aurelis_alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "aurelis-app-sg-${var.environment}"
  }
}

# Secrets Manager
resource "aws_secretsmanager_secret" "aurelis_github_token" {
  name        = "aurelis/${var.environment}/github-token"
  description = "GitHub token for Aurelis API access"
  
  tags = {
    Name = "aurelis-github-token-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "aurelis_github_token" {
  secret_id     = aws_secretsmanager_secret.aurelis_github_token.id
  secret_string = jsonencode({
    github_token = var.github_token
  })
}

# Application Load Balancer
resource "aws_lb" "aurelis_alb" {
  name               = "aurelis-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.aurelis_alb.id]
  subnets            = aws_subnet.aurelis_public[*].id
  
  enable_deletion_protection = true
  
  tags = {
    Name = "aurelis-alb-${var.environment}"
  }
}

resource "aws_lb_target_group" "aurelis_tg" {
  name     = "aurelis-tg-${var.environment}"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = aws_vpc.aurelis_vpc.id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  tags = {
    Name = "aurelis-tg-${var.environment}"
  }
}

resource "aws_lb_listener" "aurelis_listener" {
  load_balancer_arn = aws_lb.aurelis_alb.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.aurelis_tg.arn
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "aurelis_cluster" {
  name = "aurelis-cluster-${var.environment}"
  
  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.aurelis_ecs.name
      }
    }
  }
  
  tags = {
    Name = "aurelis-cluster-${var.environment}"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "aurelis_ecs" {
  name              = "/ecs/aurelis-${var.environment}"
  retention_in_days = 30
  
  tags = {
    Name = "aurelis-ecs-logs-${var.environment}"
  }
}

# IAM Roles
resource "aws_iam_role" "aurelis_execution_role" {
  name = "aurelis-execution-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "aurelis_execution_role_policy" {
  role       = aws_iam_role.aurelis_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "aurelis_secrets_policy" {
  name = "aurelis-secrets-policy-${var.environment}"
  role = aws_iam_role.aurelis_execution_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.aurelis_github_token.arn
        ]
      }
    ]
  })
}

# Outputs
output "vpc_id" {
  value = aws_vpc.aurelis_vpc.id
}

output "load_balancer_dns" {
  value = aws_lb.aurelis_alb.dns_name
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.aurelis_cluster.name
}
```

## 🔒 Security & Compliance

### WAF Configuration

```json
{
  "Name": "aurelis-waf-acl",
  "Scope": "REGIONAL",
  "DefaultAction": {
    "Allow": {}
  },
  "Rules": [
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 1,
      "OverrideAction": {
        "None": {}
      },
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "CommonRuleSetMetric"
      }
    },
    {
      "Name": "RateLimitRule",
      "Priority": 2,
      "Action": {
        "Block": {}
      },
      "Statement": {
        "RateBasedStatement": {
          "Limit": 1000,
          "AggregateKeyType": "IP"
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimitMetric"
      }
    }
  ]
}
```

### IAM Security Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:*:secret:aurelis/*"
      ],
      "Condition": {
        "StringEquals": {
          "secretsmanager:ResourceTag/Project": "Aurelis"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:us-east-1:*:log-group:/ecs/aurelis-*"
      ]
    },
    {
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

## 📊 Monitoring & Logging

### CloudWatch Dashboard

```json
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", "ServiceName", "aurelis-service"],
          [".", "MemoryUtilization", ".", "."]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "us-east-1",
        "title": "ECS Service Metrics",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "aurelis-alb"],
          [".", "TargetResponseTime", ".", "."],
          [".", "HTTPCode_Target_2XX_Count", ".", "."],
          [".", "HTTPCode_Target_4XX_Count", ".", "."],
          [".", "HTTPCode_Target_5XX_Count", ".", "."]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "us-east-1",
        "title": "Load Balancer Metrics",
        "period": 300
      }
    }
  ]
}
```

### CloudWatch Alarms

```bash
# High CPU utilization alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "aurelis-high-cpu" \
    --alarm-description "Alarm when CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ServiceName,Value=aurelis-service \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:aurelis-alerts

# High error rate alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "aurelis-high-error-rate" \
    --alarm-description "Alarm when error rate exceeds 5%" \
    --metric-name HTTPCode_Target_5XX_Count \
    --namespace AWS/ApplicationELB \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=LoadBalancer,Value=aurelis-alb \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:aurelis-alerts
```

## 📈 Auto Scaling

### ECS Auto Scaling

```json
{
  "ServiceName": "aurelis-service",
  "ClusterName": "aurelis-cluster",
  "ResourceId": "service/aurelis-cluster/aurelis-service",
  "ScalableDimension": "ecs:service:DesiredCount",
  "ServiceNamespace": "ecs",
  "MinCapacity": 2,
  "MaxCapacity": 10,
  "RoleARN": "arn:aws:iam::123456789012:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService",
  "PolicyName": "aurelis-scaling-policy",
  "PolicyType": "TargetTrackingScaling",
  "TargetTrackingScalingPolicyConfiguration": {
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 300,
    "ScaleInCooldown": 300
  }
}
```

### Lambda Auto Scaling

```yaml
# Lambda Provisioned Concurrency
resources:
  Resources:
    AnalyzeFunctionAlias:
      Type: AWS::Lambda::Alias
      Properties:
        FunctionName: !Ref AnalyzeLambdaFunction
        FunctionVersion: !GetAtt AnalyzeLambdaVersionSha256.Version
        Name: ${self:provider.stage}
        ProvisionedConcurrencyConfig:
          ProvisionedConcurrencyExecutions: 5
    
    AnalyzeFunctionScalingTarget:
      Type: AWS::ApplicationAutoScaling::ScalableTarget
      Properties:
        MaxCapacity: 50
        MinCapacity: 5
        ResourceId: !Sub "function:${AnalyzeLambdaFunction}:${self:provider.stage}"
        RoleARN: !Sub "arn:aws:iam::${AWS::AccountId}:role/aws-service-role/lambda.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_LambdaConcurrency"
        ScalableDimension: lambda:function:ProvisionedConcurrency
        ServiceNamespace: lambda
    
    AnalyzeFunctionScalingPolicy:
      Type: AWS::ApplicationAutoScaling::ScalingPolicy
      Properties:
        PolicyName: aurelis-lambda-scaling-policy
        PolicyType: TargetTrackingScaling
        ScalingTargetId: !Ref AnalyzeFunctionScalingTarget
        TargetTrackingScalingPolicyConfiguration:
          TargetValue: 0.7
          PredefinedMetricSpecification:
            PredefinedMetricType: LambdaProvisionedConcurrencyUtilization
```

## 🔧 Troubleshooting

### Common AWS Issues

#### 1. ECS Task Startup Issues

```bash
# Check ECS service events
aws ecs describe-services \
    --cluster aurelis-cluster \
    --services aurelis-service \
    --query 'services[0].events'

# Check task definition
aws ecs describe-task-definition \
    --task-definition aurelis-task:1

# Check CloudWatch logs
aws logs describe-log-streams \
    --log-group-name /ecs/aurelis

# Get recent log events
aws logs get-log-events \
    --log-group-name /ecs/aurelis \
    --log-stream-name ecs/aurelis/task-id
```

#### 2. Load Balancer Health Check Failures

```bash
# Check target group health
aws elbv2 describe-target-health \
    --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/aurelis-tg/1234567890123456

# Check security group rules
aws ec2 describe-security-groups \
    --group-ids sg-aurelis-app

# Test application health endpoint
curl -v http://internal-load-balancer-dns/health
```

#### 3. Lambda Function Errors

```bash
# Check function logs
aws logs filter-log-events \
    --log-group-name /aws/lambda/aurelis-analyze \
    --start-time $(date -d '1 hour ago' +%s)000

# Check function configuration
aws lambda get-function \
    --function-name aurelis-analyze

# Test function invocation
aws lambda invoke \
    --function-name aurelis-analyze \
    --payload '{"test": true}' \
    response.json
```

#### 4. Secrets Manager Access Issues

```bash
# Test secret access
aws secretsmanager get-secret-value \
    --secret-id aurelis/production/github-token

# Check IAM permissions
aws iam simulate-principal-policy \
    --policy-source-arn arn:aws:iam::123456789012:role/aurelis-task-role \
    --action-names secretsmanager:GetSecretValue \
    --resource-arns arn:aws:secretsmanager:us-east-1:123456789012:secret:aurelis/production/github-token
```

### Performance Optimization

#### ECS Performance Tuning

```json
{
  "family": "aurelis-task-optimized",
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "aurelis",
      "image": "aurelis:latest",
      "memoryReservation": 1024,
      "ulimits": [
        {
          "name": "nofile",
          "softLimit": 65536,
          "hardLimit": 65536
        }
      ],
      "environment": [
        {
          "name": "AURELIS_WORKER_PROCESSES",
          "value": "4"
        },
        {
          "name": "AURELIS_CACHE_SIZE",
          "value": "1000"
        }
      ]
    }
  ]
}
```

#### Lambda Performance Optimization

```python
# lambda_performance.py
import json
import os
from functools import lru_cache
from aurelis.core import AurelisCore

# Global variable for reuse across invocations
aurelis_core = None

@lru_cache(maxsize=1)
def get_cached_aurelis_core():
    """Cache Aurelis core instance."""
    global aurelius_core
    if aurelis_core is None:
        aurelis_core = AurelisCore(
            github_token=os.environ['GITHUB_TOKEN'],
            enable_caching=True,
            cache_size=500
        )
    return aurelis_core

def optimized_handler(event, context):
    """Optimized Lambda handler with caching."""
    
    # Reuse initialized core
    aurelis = get_cached_aurelis_core()
    
    # Process request
    result = aurelis.process_request(event)
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

## 📚 See Also

- [Production Deployment Guide](production-deployment.md)
- [Container Deployment Guide](container-deployment.md)
- [CI/CD Integration Guide](cicd-integration.md)
- [Monitoring Guide](monitoring.md)
- [Azure Deployment Guide](azure-deployment.md)
- [GCP Deployment Guide](gcp-deployment.md)
