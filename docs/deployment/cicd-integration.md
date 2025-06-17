# CI/CD Integration Guide

Complete guide for integrating Aurelis into CI/CD pipelines with automated code analysis, quality gates, and deployment workflows.

## 📋 Table of Contents

1. [CI/CD Overview](#cicd-overview)
2. [GitHub Actions](#github-actions)
3. [GitLab CI](#gitlab-ci)
4. [Jenkins Pipeline](#jenkins-pipeline)
5. [Azure DevOps](#azure-devops)
6. [Quality Gates](#quality-gates)
7. [Security Scanning](#security-scanning)
8. [Deployment Automation](#deployment-automation)
9. [Best Practices](#best-practices)

## 🔄 CI/CD Overview

### Integration Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Code Commit   │───▶│   Aurelis       │───▶│   Quality       │
│   (Git Push)    │    │   Analysis      │    │   Gates         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Build &       │    │   Generate      │    │   Deploy to     │
│   Test          │    │   Reports       │    │   Environment   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Features

1. **Automated Code Analysis**: Continuous code quality monitoring
2. **Quality Gates**: Fail builds based on quality thresholds
3. **Report Generation**: Automated documentation and analysis reports
4. **Security Scanning**: Integration with security analysis tools
5. **Deployment Automation**: Automated deployment based on quality metrics

## 🚀 GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/aurelis-analysis.yml
name: Aurelis Code Analysis

on:
  push:
    branches: [main, develop, feature/*]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

env:
  AURELIS_VERSION: latest
  PYTHON_VERSION: '3.11'

jobs:
  code-analysis:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      pull-requests: write
      checks: write
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for better analysis
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'
    
    - name: Install Aurelis
      run: |
        pip install --upgrade pip
        pip install aurelisai==${{ env.AURELIS_VERSION }}
    
    - name: Initialize Aurelis
      run: |
        aurelis init --force --config-file .aurelis.yml
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Analyze Changed Files
      if: github.event_name == 'pull_request'
      run: |
        # Get list of changed files
        git diff --name-only origin/${{ github.base_ref }}...HEAD > changed_files.txt
        
        # Analyze only changed files for PR
        aurelis analyze \
          --files-from changed_files.txt \
          --format json \
          --output analysis-pr.json \
          --verbose
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Analyze Full Codebase
      if: github.event_name != 'pull_request'
      run: |
        aurelis analyze \
          --recursive src/ tests/ \
          --format json \
          --output analysis-full.json \
          --include-metrics \
          --generate-suggestions
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Generate Documentation
      run: |
        aurelis docs \
          --source src/ \
          --output docs/generated/ \
          --format markdown \
          --include-examples \
          --update-readme
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Security Scan
      run: |
        aurelis security-scan \
          --recursive src/ \
          --output security-report.json \
          --check-dependencies \
          --check-secrets
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Quality Gate Check
      run: |
        python .github/scripts/quality_gate.py \
          --analysis-file analysis-*.json \
          --security-file security-report.json \
          --fail-on-critical \
          --max-complexity 10 \
          --min-coverage 80
    
    - name: Upload Analysis Results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: aurelis-analysis-${{ github.sha }}
        path: |
          analysis-*.json
          security-report.json
          docs/generated/
        retention-days: 30
    
    - name: Comment PR with Results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          
          // Read analysis results
          let analysisData = {};
          try {
            analysisData = JSON.parse(fs.readFileSync('analysis-pr.json', 'utf8'));
          } catch (e) {
            console.log('No analysis file found');
            return;
          }
          
          // Create comment body
          const issues = analysisData.issues || [];
          const metrics = analysisData.metrics || {};
          
          let commentBody = `## 🤖 Aurelis Code Analysis Results\n\n`;
          commentBody += `**Files Analyzed:** ${analysisData.files_analyzed || 0}\n`;
          commentBody += `**Issues Found:** ${issues.length}\n`;
          commentBody += `**Code Quality Score:** ${metrics.quality_score || 'N/A'}\n\n`;
          
          if (issues.length > 0) {
            commentBody += `### Issues Found:\n\n`;
            issues.slice(0, 10).forEach(issue => {
              commentBody += `- **${issue.severity}**: ${issue.message} (${issue.file}:${issue.line})\n`;
            });
            
            if (issues.length > 10) {
              commentBody += `\n... and ${issues.length - 10} more issues. Check the full report for details.\n`;
            }
          }
          
          commentBody += `\n---\n*Analysis powered by Aurelis AI*`;
          
          // Post comment
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: commentBody
          });
    
    - name: Update Status Check
      if: always()
      uses: actions/github-script@v6
      with:
        script: |
          const state = '${{ job.status }}' === 'success' ? 'success' : 'failure';
          const description = state === 'success' 
            ? 'Code analysis passed' 
            : 'Code analysis failed - check details';
          
          github.rest.repos.createCommitStatus({
            owner: context.repo.owner,
            repo: context.repo.repo,
            sha: context.sha,
            state: state,
            target_url: `${context.payload.repository.html_url}/actions/runs/${context.runId}`,
            description: description,
            context: 'aurelis/code-analysis'
          });

  security-analysis:
    runs-on: ubuntu-latest
    needs: code-analysis
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [code-analysis, security-analysis]
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - name: Deploy to Staging
      run: |
        echo "Deploying to staging environment..."
        # Add deployment commands here
    
    - name: Run Integration Tests
      run: |
        # Run integration tests against staging
        aurelis test --environment staging --suite integration
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        STAGING_URL: ${{ secrets.STAGING_URL }}

  deploy-production:
    runs-on: ubuntu-latest
    needs: [code-analysis, security-analysis]
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - name: Deploy to Production
      run: |
        echo "Deploying to production environment..."
        # Add production deployment commands here
```

### Quality Gate Script

```python
# .github/scripts/quality_gate.py
#!/usr/bin/env python3
"""Quality gate script for Aurelis CI/CD pipeline."""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any

class QualityGate:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.issues = []
        
    def check_analysis_results(self, analysis_file: Path) -> bool:
        """Check code analysis results against quality gates."""
        try:
            with open(analysis_file) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error reading analysis file: {e}")
            return False
        
        # Check complexity
        max_complexity = self.config.get('max_complexity', 10)
        if 'metrics' in data and 'complexity' in data['metrics']:
            complexity = data['metrics']['complexity']
            if complexity > max_complexity:
                self.issues.append(f"Code complexity ({complexity}) exceeds threshold ({max_complexity})")
        
        # Check coverage
        min_coverage = self.config.get('min_coverage', 80)
        if 'metrics' in data and 'coverage' in data['metrics']:
            coverage = data['metrics']['coverage']
            if coverage < min_coverage:
                self.issues.append(f"Code coverage ({coverage}%) below threshold ({min_coverage}%)")
        
        # Check critical issues
        if self.config.get('fail_on_critical', True):
            critical_issues = [
                issue for issue in data.get('issues', [])
                if issue.get('severity') == 'critical'
            ]
            if critical_issues:
                self.issues.append(f"Found {len(critical_issues)} critical issues")
        
        # Check quality score
        min_quality_score = self.config.get('min_quality_score', 70)
        if 'metrics' in data and 'quality_score' in data['metrics']:
            quality_score = data['metrics']['quality_score']
            if quality_score < min_quality_score:
                self.issues.append(f"Quality score ({quality_score}) below threshold ({min_quality_score})")
        
        return len(self.issues) == 0
    
    def check_security_results(self, security_file: Path) -> bool:
        """Check security scan results."""
        try:
            with open(security_file) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error reading security file: {e}")
            return False
        
        # Check for high/critical vulnerabilities
        if self.config.get('fail_on_security_issues', True):
            high_vuln = data.get('high_vulnerabilities', 0)
            critical_vuln = data.get('critical_vulnerabilities', 0)
            
            if high_vuln > 0 or critical_vuln > 0:
                self.issues.append(f"Found {critical_vuln} critical and {high_vuln} high vulnerabilities")
        
        return len(self.issues) == 0 if not self.issues else True
    
    def run(self, analysis_files: List[Path], security_file: Path = None) -> bool:
        """Run all quality gate checks."""
        print("🚦 Running Quality Gate Checks...")
        
        # Check analysis results
        passed = True
        for analysis_file in analysis_files:
            if not self.check_analysis_results(analysis_file):
                passed = False
        
        # Check security results
        if security_file and security_file.exists():
            if not self.check_security_results(security_file):
                passed = False
        
        # Print results
        if passed:
            print("✅ All quality gate checks passed!")
        else:
            print("❌ Quality gate checks failed:")
            for issue in self.issues:
                print(f"  - {issue}")
        
        return passed

def main():
    parser = argparse.ArgumentParser(description='Aurelis Quality Gate')
    parser.add_argument('--analysis-file', action='append', help='Analysis result files')
    parser.add_argument('--security-file', help='Security scan result file')
    parser.add_argument('--max-complexity', type=int, default=10, help='Maximum complexity threshold')
    parser.add_argument('--min-coverage', type=int, default=80, help='Minimum coverage percentage')
    parser.add_argument('--min-quality-score', type=int, default=70, help='Minimum quality score')
    parser.add_argument('--fail-on-critical', action='store_true', help='Fail on critical issues')
    parser.add_argument('--fail-on-security-issues', action='store_true', help='Fail on security issues')
    
    args = parser.parse_args()
    
    config = {
        'max_complexity': args.max_complexity,
        'min_coverage': args.min_coverage,
        'min_quality_score': args.min_quality_score,
        'fail_on_critical': args.fail_on_critical,
        'fail_on_security_issues': args.fail_on_security_issues
    }
    
    gate = QualityGate(config)
    
    analysis_files = []
    if args.analysis_file:
        analysis_files = [Path(f) for f in args.analysis_file]
    
    security_file = Path(args.security_file) if args.security_file else None
    
    success = gate.run(analysis_files, security_file)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

## 🦊 GitLab CI

### GitLab CI Configuration

```yaml
# .gitlab-ci.yml
stages:
  - analysis
  - test
  - security
  - deploy

variables:
  PYTHON_VERSION: "3.11"
  AURELIS_VERSION: "latest"
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/

before_script:
  - python --version
  - pip install --upgrade pip
  - pip install aurelisai==$AURELIS_VERSION

aurelis_analysis:
  stage: analysis
  image: python:$PYTHON_VERSION
  script:
    - aurelis init --force
    - |
      if [ "$CI_PIPELINE_SOURCE" = "merge_request_event" ]; then
        # Analyze only changed files for MR
        git diff --name-only origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...HEAD > changed_files.txt
        aurelis analyze --files-from changed_files.txt --format json --output analysis-mr.json
      else
        # Full analysis for main branch
        aurelis analyze --recursive src/ tests/ --format json --output analysis-full.json
      fi
    - aurelius docs --source src/ --output docs/generated/ --format markdown
  artifacts:
    reports:
      junit: test-reports/junit.xml
    paths:
      - analysis-*.json
      - docs/generated/
    expire_in: 1 week
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
    - if: '$CI_COMMIT_BRANCH == "develop"'

quality_gate:
  stage: test
  image: python:$PYTHON_VERSION
  script:
    - python .gitlab/quality_gate.py --analysis-file analysis-*.json
  dependencies:
    - aurelis_analysis
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
    - if: '$CI_COMMIT_BRANCH == "develop"'

security_scan:
  stage: security
  image: 
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy fs --exit-code 0 --format json --output trivy-report.json .
    - trivy fs --exit-code 1 --severity HIGH,CRITICAL .
  artifacts:
    reports:
      security: trivy-report.json
    paths:
      - trivy-report.json
    expire_in: 1 week
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

deploy_staging:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache curl
  script:
    - echo "Deploying to staging..."
    - curl -X POST "$STAGING_DEPLOY_WEBHOOK"
  environment:
    name: staging
    url: https://staging.aurelis.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'

deploy_production:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache curl
  script:
    - echo "Deploying to production..."
    - curl -X POST "$PRODUCTION_DEPLOY_WEBHOOK"
  environment:
    name: production
    url: https://aurelis.com
  when: manual
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### GitLab Quality Gate Script

```python
# .gitlab/quality_gate.py
"""GitLab specific quality gate implementation."""

import json
import sys
import os
from pathlib import Path

def create_gitlab_report(analysis_data, output_file="gl-code-quality-report.json"):
    """Create GitLab Code Quality report format."""
    issues = []
    
    for issue in analysis_data.get('issues', []):
        # Map severity levels
        severity_map = {
            'critical': 'blocker',
            'high': 'critical',
            'medium': 'major',
            'low': 'minor',
            'info': 'info'
        }
        
        gitlab_issue = {
            "description": issue.get('message', ''),
            "check_name": issue.get('rule', 'aurelis-check'),
            "fingerprint": issue.get('id', ''),
            "severity": severity_map.get(issue.get('severity', 'medium'), 'major'),
            "location": {
                "path": issue.get('file', ''),
                "lines": {
                    "begin": issue.get('line', 1)
                }
            }
        }
        issues.append(gitlab_issue)
    
    with open(output_file, 'w') as f:
        json.dump(issues, f, indent=2)
    
    print(f"Created GitLab Code Quality report: {output_file}")

def main():
    analysis_files = sys.argv[1:] if len(sys.argv) > 1 else ['analysis-*.json']
    
    for pattern in analysis_files:
        for analysis_file in Path('.').glob(pattern):
            try:
                with open(analysis_file) as f:
                    data = json.load(f)
                
                # Create GitLab report
                create_gitlab_report(data)
                
                # Check quality gates
                issues = data.get('issues', [])
                critical_issues = [i for i in issues if i.get('severity') == 'critical']
                
                if critical_issues:
                    print(f"❌ Found {len(critical_issues)} critical issues")
                    sys.exit(1)
                
                print(f"✅ Quality gate passed for {analysis_file}")
                
            except Exception as e:
                print(f"❌ Error processing {analysis_file}: {e}")
                sys.exit(1)

if __name__ == '__main__':
    main()
```

## 🏗️ Jenkins Pipeline

### Jenkinsfile

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        AURELIS_VERSION = 'latest'
        GITHUB_TOKEN = credentials('github-token')
        QUALITY_GATE_THRESHOLD = '80'
    }
    
    parameters {
        choice(
            name: 'ANALYSIS_SCOPE',
            choices: ['full', 'incremental'],
            description: 'Scope of code analysis'
        )
        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Skip test execution'
        )
        booleanParam(
            name: 'DEPLOY_TO_STAGING',
            defaultValue: false,
            description: 'Deploy to staging after successful build'
        )
    }
    
    stages {
        stage('Setup') {
            steps {
                echo "Setting up environment..."
                sh '''
                    python${PYTHON_VERSION} -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install aurelisai==${AURELIS_VERSION}
                '''
            }
        }
        
        stage('Code Analysis') {
            parallel {
                stage('Aurelis Analysis') {
                    steps {
                        script {
                            def analysisScope = params.ANALYSIS_SCOPE
                            
                            sh '''
                                . venv/bin/activate
                                aurelis init --force
                            '''
                            
                            if (analysisScope == 'incremental' && env.CHANGE_ID) {
                                // Analyze only changed files for PR
                                sh '''
                                    . venv/bin/activate
                                    git diff --name-only origin/main...HEAD > changed_files.txt
                                    aurelis analyze --files-from changed_files.txt \\
                                        --format json \\
                                        --output analysis-incremental.json
                                '''
                            } else {
                                // Full analysis
                                sh '''
                                    . venv/bin/activate
                                    aurelis analyze --recursive src/ tests/ \\
                                        --format json \\
                                        --output analysis-full.json \\
                                        --include-metrics
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'analysis-*.json', fingerprint: true
                        }
                    }
                }
                
                stage('Documentation Generation') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            aurelis docs --source src/ \\
                                --output docs/generated/ \\
                                --format markdown \\
                                --update-readme
                        '''
                    }
                    post {
                        always {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'docs/generated',
                                reportFiles: 'index.html',
                                reportName: 'Generated Documentation'
                            ])
                        }
                    }
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                script {
                    def qualityGateResult = sh(
                        script: '''
                            . venv/bin/activate
                            python scripts/quality_gate.py \\
                                --analysis-file analysis-*.json \\
                                --threshold ${QUALITY_GATE_THRESHOLD}
                        ''',
                        returnStatus: true
                    )
                    
                    if (qualityGateResult != 0) {
                        currentBuild.result = 'UNSTABLE'
                        error("Quality gate failed")
                    }
                }
            }
        }
        
        stage('Security Scan') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                sh '''
                    # Run Trivy security scan
                    docker run --rm -v $(pwd):/workspace \\
                        aquasec/trivy:latest fs \\
                        --format json \\
                        --output /workspace/security-report.json \\
                        /workspace
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'security-report.json', fingerprint: true
                }
            }
        }
        
        stage('Tests') {
            when {
                not { params.SKIP_TESTS }
            }
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            python -m pytest tests/unit/ \\
                                --junitxml=test-results/unit-tests.xml \\
                                --cov=src/ \\
                                --cov-report=xml:coverage.xml
                        '''
                    }
                    post {
                        always {
                            junit 'test-results/unit-tests.xml'
                            publishCoverage(
                                adapters: [coberturaAdapter('coverage.xml')],
                                sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                            )
                        }
                    }
                }
                
                stage('Integration Tests') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            python -m pytest tests/integration/ \\
                                --junitxml=test-results/integration-tests.xml
                        '''
                    }
                    post {
                        always {
                            junit 'test-results/integration-tests.xml'
                        }
                    }
                }
            }
        }
        
        stage('Build Artifacts') {
            steps {
                sh '''
                    . venv/bin/activate
                    python setup.py sdist bdist_wheel
                '''
            }
            post {
                success {
                    archiveArtifacts artifacts: 'dist/*', fingerprint: true
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                anyOf {
                    params.DEPLOY_TO_STAGING
                    branch 'develop'
                }
            }
            steps {
                script {
                    def deployResult = build(
                        job: 'deploy-to-staging',
                        parameters: [
                            string(name: 'BUILD_NUMBER', value: env.BUILD_NUMBER),
                            string(name: 'GIT_COMMIT', value: env.GIT_COMMIT)
                        ],
                        wait: true
                    )
                    
                    if (deployResult.result != 'SUCCESS') {
                        error("Deployment to staging failed")
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo "Pipeline completed"
            
            // Clean up workspace
            cleanWs(
                cleanWhenAborted: true,
                cleanWhenFailure: true,
                cleanWhenNotBuilt: false,
                cleanWhenSuccess: true,
                cleanWhenUnstable: true,
                deleteDirs: true
            )
        }
        
        success {
            echo "✅ Pipeline succeeded"
            
            // Send success notification
            slackSend(
                channel: '#ci-cd',
                color: 'good',
                message: "✅ Build succeeded: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
        
        failure {
            echo "❌ Pipeline failed"
            
            // Send failure notification
            slackSend(
                channel: '#ci-cd',
                color: 'danger',
                message: "❌ Build failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
        
        unstable {
            echo "⚠️ Pipeline unstable"
            
            // Send unstable notification
            slackSend(
                channel: '#ci-cd',
                color: 'warning',
                message: "⚠️ Build unstable: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
    }
}
```

### Jenkins Shared Library

```groovy
// vars/aurelisAnalysis.groovy
/**
 * Shared library function for Aurelis code analysis
 */
def call(Map config = [:]) {
    def analysisScope = config.scope ?: 'full'
    def outputFormat = config.format ?: 'json'
    def includeMetrics = config.includeMetrics ?: true
    def failOnCritical = config.failOnCritical ?: true
    
    pipeline {
        agent any
        
        stages {
            stage('Aurelis Analysis') {
                steps {
                    script {
                        // Initialize Aurelis
                        sh 'aurelis init --force'
                        
                        // Run analysis based on scope
                        def analysisCmd = "aurelis analyze"
                        
                        if (analysisScope == 'incremental' && env.CHANGE_ID) {
                            analysisCmd += " --changed-only"
                        } else {
                            analysisCmd += " --recursive src/ tests/"
                        }
                        
                        analysisCmd += " --format ${outputFormat}"
                        analysisCmd += " --output analysis-result.${outputFormat}"
                        
                        if (includeMetrics) {
                            analysisCmd += " --include-metrics"
                        }
                        
                        sh analysisCmd
                        
                        // Check for critical issues
                        if (failOnCritical) {
                            def result = sh(
                                script: "python scripts/check_critical_issues.py analysis-result.${outputFormat}",
                                returnStatus: true
                            )
                            
                            if (result != 0) {
                                error("Critical issues found in code analysis")
                            }
                        }
                    }
                }
                
                post {
                    always {
                        archiveArtifacts artifacts: "analysis-result.${outputFormat}", fingerprint: true
                        
                        // Publish results
                        if (outputFormat == 'junit') {
                            junit "analysis-result.${outputFormat}"
                        }
                    }
                }
            }
        }
    }
}
```

## 🔷 Azure DevOps

### Azure Pipelines YAML

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
    - main
    - develop
    - feature/*
  paths:
    exclude:
    - docs/*
    - README.md

pr:
  branches:
    include:
    - main
    - develop

variables:
  pythonVersion: '3.11'
  aurelisVersion: 'latest'

stages:
- stage: Analysis
  displayName: 'Code Analysis'
  jobs:
  - job: AurelisAnalysis
    displayName: 'Aurelis Code Analysis'
    pool:
      vmImage: 'ubuntu-latest'
    
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
        displayName: 'Use Python $(pythonVersion)'
    
    - script: |
        python -m pip install --upgrade pip
        pip install aurelisai==$(aurelisVersion)
      displayName: 'Install Aurelis'
    
    - script: |
        aurelis init --force
      displayName: 'Initialize Aurelis'
      env:
        GITHUB_TOKEN: $(github.token)
    
    - script: |
        if [ "$(Build.Reason)" = "PullRequest" ]; then
          # Analyze changed files for PR
          git diff --name-only origin/$(System.PullRequest.TargetBranch)...HEAD > changed_files.txt
          aurelis analyze --files-from changed_files.txt --format json --output analysis-pr.json
        else
          # Full analysis for main/develop
          aurelis analyze --recursive src/ tests/ --format json --output analysis-full.json
        fi
      displayName: 'Run Code Analysis'
      env:
        GITHUB_TOKEN: $(github.token)
    
    - script: |
        aurelis docs --source src/ --output docs/generated/ --format markdown
      displayName: 'Generate Documentation'
      env:
        GITHUB_TOKEN: $(github.token)
    
    - task: PublishTestResults@2
      condition: always()
      inputs:
        testResultsFormat: 'JUnit'
        testResultsFiles: 'analysis-*.xml'
        failTaskOnFailedTests: false
        displayName: 'Publish Analysis Results'
    
    - task: PublishCodeCoverageResults@1
      inputs:
        codeCoverageTool: 'Cobertura'
        summaryFileLocation: 'coverage.xml'
        displayName: 'Publish Coverage Results'
    
    - task: PublishBuildArtifacts@1
      inputs:
        pathToPublish: 'analysis-*.json'
        artifactName: 'analysis-results'
        displayName: 'Publish Analysis Artifacts'

- stage: QualityGate
  displayName: 'Quality Gate'
  dependsOn: Analysis
  jobs:
  - job: QualityCheck
    displayName: 'Quality Gate Check'
    pool:
      vmImage: 'ubuntu-latest'
    
    steps:
    - task: DownloadBuildArtifacts@0
      inputs:
        buildType: 'current'
        artifactName: 'analysis-results'
        downloadPath: '$(System.ArtifactsDirectory)'
    
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
    
    - script: |
        python scripts/quality_gate.py \
          --analysis-file $(System.ArtifactsDirectory)/analysis-results/analysis-*.json \
          --max-complexity 10 \
          --min-coverage 80 \
          --fail-on-critical
      displayName: 'Run Quality Gate'

- stage: Security
  displayName: 'Security Scan'
  dependsOn: QualityGate
  condition: and(succeeded(), in(variables['Build.SourceBranch'], 'refs/heads/main', 'refs/heads/develop'))
  jobs:
  - job: SecurityScan
    displayName: 'Security Analysis'
    pool:
      vmImage: 'ubuntu-latest'
    
    steps:
    - script: |
        docker run --rm -v $(Build.SourcesDirectory):/workspace \
          aquasec/trivy:latest fs \
          --format json \
          --output /workspace/security-report.json \
          /workspace
      displayName: 'Run Trivy Security Scan'
    
    - task: PublishBuildArtifacts@1
      inputs:
        pathToPublish: 'security-report.json'
        artifactName: 'security-results'

- stage: Deploy
  displayName: 'Deploy'
  dependsOn: [QualityGate, Security]
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - deployment: DeployToStaging
    displayName: 'Deploy to Staging'
    environment: 'staging'
    strategy:
      runOnce:
        deploy:
          steps:
          - script: echo "Deploying to staging..."
            displayName: 'Deploy Application'
```

## 🚦 Quality Gates

### Quality Gate Configuration

```yaml
# quality-gates.yml
quality_gates:
  code_quality:
    max_complexity: 10
    min_maintainability_index: 70
    max_code_duplication: 5  # percentage
    
  test_coverage:
    min_line_coverage: 80
    min_branch_coverage: 75
    min_function_coverage: 90
    
  security:
    max_critical_vulnerabilities: 0
    max_high_vulnerabilities: 2
    max_medium_vulnerabilities: 10
    
  performance:
    max_response_time: 2000  # milliseconds
    min_requests_per_second: 100
    
  code_style:
    max_style_violations: 50
    enforce_naming_conventions: true
    require_documentation: true

thresholds:
  blocking:
    - critical_vulnerabilities > 0
    - line_coverage < 70
    - complexity > 15
    
  warning:
    - high_vulnerabilities > 5
    - line_coverage < 80
    - complexity > 10
    - code_duplication > 10

notifications:
  slack:
    webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    channels:
      - "#quality-gates"
    
  email:
    recipients:
      - "dev-team@company.com"
      - "qa-team@company.com"
```

### Advanced Quality Gate Script

```python
# scripts/advanced_quality_gate.py
"""Advanced quality gate implementation with multiple checks."""

import json
import yaml
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class Severity(Enum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"

@dataclass
class QualityIssue:
    category: str
    message: str
    severity: Severity
    value: float
    threshold: float
    
class AdvancedQualityGate:
    def __init__(self, config_file: str):
        self.config = self._load_config(config_file)
        self.issues: List[QualityIssue] = []
        self.logger = self._setup_logging()
        
    def _load_config(self, config_file: str) -> Dict:
        """Load quality gate configuration."""
        with open(config_file) as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def check_code_quality(self, analysis_data: Dict) -> bool:
        """Check code quality metrics."""
        self.logger.info("Checking code quality metrics...")
        
        metrics = analysis_data.get('metrics', {})
        quality_config = self.config['quality_gates']['code_quality']
        
        passed = True
        
        # Check complexity
        complexity = metrics.get('complexity', 0)
        max_complexity = quality_config['max_complexity']
        if complexity > max_complexity:
            self.issues.append(QualityIssue(
                category="code_quality",
                message=f"Code complexity ({complexity}) exceeds threshold",
                severity=Severity.BLOCKING,
                value=complexity,
                threshold=max_complexity
            ))
            passed = False
        
        # Check maintainability
        maintainability = metrics.get('maintainability_index', 100)
        min_maintainability = quality_config['min_maintainability_index']
        if maintainability < min_maintainability:
            self.issues.append(QualityIssue(
                category="code_quality",
                message=f"Maintainability index ({maintainability}) below threshold",
                severity=Severity.WARNING,
                value=maintainability,
                threshold=min_maintainability
            ))
        
        # Check code duplication
        duplication = metrics.get('code_duplication', 0)
        max_duplication = quality_config['max_code_duplication']
        if duplication > max_duplication:
            self.issues.append(QualityIssue(
                category="code_quality",
                message=f"Code duplication ({duplication}%) exceeds threshold",
                severity=Severity.WARNING,
                value=duplication,
                threshold=max_duplication
            ))
        
        return passed
    
    def check_test_coverage(self, coverage_data: Dict) -> bool:
        """Check test coverage metrics."""
        self.logger.info("Checking test coverage...")
        
        coverage_config = self.config['quality_gates']['test_coverage']
        passed = True
        
        # Check line coverage
        line_coverage = coverage_data.get('line_coverage', 0)
        min_line_coverage = coverage_config['min_line_coverage']
        if line_coverage < min_line_coverage:
            severity = Severity.BLOCKING if line_coverage < 70 else Severity.WARNING
            self.issues.append(QualityIssue(
                category="test_coverage",
                message=f"Line coverage ({line_coverage}%) below threshold",
                severity=severity,
                value=line_coverage,
                threshold=min_line_coverage
            ))
            if severity == Severity.BLOCKING:
                passed = False
        
        # Check branch coverage
        branch_coverage = coverage_data.get('branch_coverage', 0)
        min_branch_coverage = coverage_config['min_branch_coverage']
        if branch_coverage < min_branch_coverage:
            self.issues.append(QualityIssue(
                category="test_coverage",
                message=f"Branch coverage ({branch_coverage}%) below threshold",
                severity=Severity.WARNING,
                value=branch_coverage,
                threshold=min_branch_coverage
            ))
        
        return passed
    
    def check_security(self, security_data: Dict) -> bool:
        """Check security vulnerabilities."""
        self.logger.info("Checking security vulnerabilities...")
        
        security_config = self.config['quality_gates']['security']
        passed = True
        
        # Check critical vulnerabilities
        critical_vulns = security_data.get('critical_vulnerabilities', 0)
        max_critical = security_config['max_critical_vulnerabilities']
        if critical_vulns > max_critical:
            self.issues.append(QualityIssue(
                category="security",
                message=f"Critical vulnerabilities ({critical_vulns}) exceed threshold",
                severity=Severity.BLOCKING,
                value=critical_vulns,
                threshold=max_critical
            ))
            passed = False
        
        # Check high vulnerabilities
        high_vulns = security_data.get('high_vulnerabilities', 0)
        max_high = security_config['max_high_vulnerabilities']
        if high_vulns > max_high:
            self.issues.append(QualityIssue(
                category="security",
                message=f"High vulnerabilities ({high_vulns}) exceed threshold",
                severity=Severity.WARNING,
                value=high_vulns,
                threshold=max_high
            ))
        
        return passed
    
    def check_performance(self, performance_data: Dict) -> bool:
        """Check performance metrics."""
        self.logger.info("Checking performance metrics...")
        
        performance_config = self.config['quality_gates']['performance']
        passed = True
        
        # Check response time
        response_time = performance_data.get('average_response_time', 0)
        max_response_time = performance_config['max_response_time']
        if response_time > max_response_time:
            self.issues.append(QualityIssue(
                category="performance",
                message=f"Response time ({response_time}ms) exceeds threshold",
                severity=Severity.WARNING,
                value=response_time,
                threshold=max_response_time
            ))
        
        return passed
    
    def generate_report(self) -> Dict:
        """Generate quality gate report."""
        blocking_issues = [i for i in self.issues if i.severity == Severity.BLOCKING]
        warning_issues = [i for i in self.issues if i.severity == Severity.WARNING]
        
        passed = len(blocking_issues) == 0
        
        report = {
            'timestamp': '2024-01-15T10:30:00Z',
            'status': 'PASSED' if passed else 'FAILED',
            'summary': {
                'total_issues': len(self.issues),
                'blocking_issues': len(blocking_issues),
                'warning_issues': len(warning_issues)
            },
            'issues': [
                {
                    'category': issue.category,
                    'message': issue.message,
                    'severity': issue.severity.value,
                    'value': issue.value,
                    'threshold': issue.threshold
                }
                for issue in self.issues
            ]
        }
        
        return report
    
    def run(self, analysis_file: str, coverage_file: str = None, 
            security_file: str = None, performance_file: str = None) -> bool:
        """Run all quality gate checks."""
        self.logger.info("Starting quality gate checks...")
        
        # Load analysis data
        with open(analysis_file) as f:
            analysis_data = json.load(f)
        
        passed = True
        
        # Run code quality checks
        if not self.check_code_quality(analysis_data):
            passed = False
        
        # Run coverage checks
        if coverage_file and Path(coverage_file).exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)
            if not self.check_test_coverage(coverage_data):
                passed = False
        
        # Run security checks
        if security_file and Path(security_file).exists():
            with open(security_file) as f:
                security_data = json.load(f)
            if not self.check_security(security_data):
                passed = False
        
        # Run performance checks
        if performance_file and Path(performance_file).exists():
            with open(performance_file) as f:
                performance_data = json.load(f)
            if not self.check_performance(performance_data):
                passed = False
        
        # Generate and save report
        report = self.generate_report()
        with open('quality-gate-report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        if passed:
            self.logger.info("✅ All quality gate checks passed!")
        else:
            self.logger.error("❌ Quality gate checks failed!")
            for issue in self.issues:
                if issue.severity == Severity.BLOCKING:
                    self.logger.error(f"  - {issue.message}")
        
        return passed

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Quality Gate')
    parser.add_argument('--config', required=True, help='Quality gate configuration file')
    parser.add_argument('--analysis-file', required=True, help='Analysis results file')
    parser.add_argument('--coverage-file', help='Coverage results file')
    parser.add_argument('--security-file', help='Security scan results file')
    parser.add_argument('--performance-file', help='Performance test results file')
    
    args = parser.parse_args()
    
    gate = AdvancedQualityGate(args.config)
    success = gate.run(
        args.analysis_file,
        args.coverage_file,
        args.security_file,
        args.performance_file
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

## 🔒 Security Scanning

### Security Integration

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  security-scan:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
    
    - name: Run Bandit security linter
      run: |
        pip install bandit[toml]
        bandit -r src/ -f json -o bandit-report.json
    
    - name: Run Safety dependency check
      run: |
        pip install safety
        safety check --json --output safety-report.json
    
    - name: Combine security reports
      run: |
        python scripts/combine_security_reports.py \
          --trivy trivy-results.sarif \
          --bandit bandit-report.json \
          --safety safety-report.json \
          --output combined-security-report.json
    
    - name: Upload security artifacts
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          trivy-results.sarif
          bandit-report.json
          safety-report.json
          combined-security-report.json
```

## 🚀 Deployment Automation

### Multi-Environment Deployment

```yaml
# .github/workflows/deploy.yml
name: Deploy Application

on:
  workflow_run:
    workflows: ["Aurelis Code Analysis"]
    types:
      - completed
    branches: [main, develop]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' && github.ref == 'refs/heads/develop' }}
    environment: staging
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment..."
        # Add actual deployment commands
    
    - name: Run smoke tests
      run: |
        aurelis test --environment staging --suite smoke
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        STAGING_URL: ${{ vars.STAGING_URL }}
    
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        text: 'Staging deployment completed'

  deploy-production:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' && github.ref == 'refs/heads/main' }}
    environment: production
    needs: []  # Add staging deployment as dependency if needed
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Deploy to production
      run: |
        echo "Deploying to production environment..."
        # Add actual deployment commands
    
    - name: Run health checks
      run: |
        aurelis health-check --url ${{ vars.PRODUCTION_URL }}
    
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        text: 'Production deployment completed'
```

## 📋 Best Practices

### 1. Pipeline Optimization

```yaml
# Optimize CI/CD performance
strategy:
  matrix:
    python-version: [3.9, 3.10, 3.11]
    
cache:
  paths:
    - ~/.cache/pip
    - node_modules/
    - .aurelis/cache/

# Use parallel execution
parallel:
  matrix:
    - ANALYSIS_TYPE: [complexity, security, style]
```

### 2. Environment Management

```yaml
# Environment-specific configurations
environments:
  staging:
    variables:
      AURELIS_LOG_LEVEL: DEBUG
      GITHUB_TOKEN: ${{ secrets.STAGING_GITHUB_TOKEN }}
      
  production:
    variables:
      AURELIS_LOG_LEVEL: INFO
      GITHUB_TOKEN: ${{ secrets.PRODUCTION_GITHUB_TOKEN }}
    protection_rules:
      required_reviewers: 2
      wait_timer: 5  # minutes
```

### 3. Monitoring and Alerting

```yaml
# Monitor pipeline health
notifications:
  slack:
    on_success: false
    on_failure: true
    on_cancel: true
    
  email:
    recipients:
      - devops@company.com
    on_failure: true
```

### 4. Security Best Practices

```yaml
# Secure CI/CD practices
secrets:
  GITHUB_TOKEN:
    required: true
    description: "GitHub token for API access"
    
permissions:
  contents: read
  security-events: write
  pull-requests: write

# Least privilege access
steps:
  - name: Run analysis
    with:
      token: ${{ secrets.READONLY_TOKEN }}
```

## 📚 See Also

- [Production Deployment Guide](production-deployment.md)
- [Container Deployment Guide](container-deployment.md)
- [Monitoring Guide](monitoring.md)
- [Security Best Practices](security.md)
