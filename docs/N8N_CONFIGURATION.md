# n8n Configuration Guide

**Purpose:** Document n8n instance configuration, health checks, and GitHub Actions integration  
**Created/Updated:** 2025-11-20  
**Agent:** INTEGRATION_AGENT

## Overview

This document describes the configuration and setup of n8n instances for the Automation Hub platform, including environment setup, health checks, and integration with GitHub Actions.

## n8n Instance Configuration

### Environment Variables

n8n instances are configured via environment variables. All sensitive values must be retrieved from AWS Secrets Manager.

#### Required Environment Variables

```bash
# n8n Basic Configuration
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=http  # or https for production

# Database Configuration (if using external database)
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=your-db-host
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n_user
# Password from AWS Secrets Manager

# Security
N8N_ENCRYPTION_KEY=<from-aws-secrets-manager>
N8N_USER_MANAGEMENT_DISABLED=false

# Webhook Configuration
WEBHOOK_URL=https://n8n.automation-hub.example.com/
N8N_METRICS=true

# AWS Integration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<from-aws-secrets-manager>
AWS_SECRET_ACCESS_KEY=<from-aws-secrets-manager>
```

### Configuration Files

Environment-specific configurations are stored in:
- `shared/config/environments.dev.yaml`
- `shared/config/environments.prod.yaml`

These files reference AWS Secrets Manager ARNs for all sensitive values.

## Health Check Endpoints

### Health Check Endpoint

**URL:** `{n8n_base_url}/healthz`  
**Method:** GET  
**Response:** HTTP 200 if healthy, HTTP 503 if unhealthy

**Example Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-20T12:00:00Z"
}
```

### API Health Check

**URL:** `{n8n_base_url}/api/v1/health`  
**Method:** GET  
**Authentication:** Required (API key)

**Example Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-11-20T12:00:00Z"
}
```

### Monitoring Integration

Health checks should be configured in:
- **Prometheus:** Scrape endpoint for metrics
- **Grafana:** Dashboard for health status
- **GitHub Actions:** Pre-deployment health validation

## Webhook Endpoints

### GitHub Actions Integration

n8n webhooks are configured to receive events from GitHub Actions workflows.

**Webhook URL Pattern:**
```
{n8n_base_url}/webhook/{workflow_name}
```

**Example:**
```
https://n8n.automation-hub.example.com/webhook/infra-deploy
```

### Webhook Security

- Webhooks use authentication tokens stored in AWS Secrets Manager
- Tokens are environment-specific
- Webhook URLs are not publicly exposed (internal network only)

### Webhook Configuration

Webhooks are configured in n8n workflow definitions:
- **Trigger Type:** Webhook
- **HTTP Method:** POST
- **Path:** `/webhook/{workflow_name}`
- **Authentication:** Header-based token

## Environment Setup

### Development Environment

**Base URL:** `http://localhost:5678`  
**Configuration:** `shared/config/environments.dev.yaml`

**Setup Steps:**
1. Start n8n Docker container
2. Configure environment variables from `environments.dev.yaml`
3. Retrieve secrets from AWS Secrets Manager
4. Verify health check endpoint
5. Test webhook endpoints

### Production Environment

**Base URL:** `https://n8n.automation-hub.example.com`  
**Configuration:** `shared/config/environments.prod.yaml`

**Setup Steps:**
1. Deploy n8n instance (EC2, ECS, or Kubernetes)
2. Configure SSL/TLS certificates
3. Set up load balancer with health checks
4. Configure environment variables from `environments.prod.yaml`
5. Retrieve secrets from AWS Secrets Manager
6. Verify health check endpoint
7. Configure monitoring and alerting

## GitHub Actions Integration

### Webhook Trigger Configuration

GitHub Actions workflows trigger n8n workflows via webhooks:

```yaml
# .github/workflows/infra-deploy.yml
- name: Trigger n8n Workflow
  run: |
    curl -X POST \
      -H "Authorization: Bearer ${{ secrets.N8N_WEBHOOK_TOKEN }}" \
      -H "Content-Type: application/json" \
      -d '{"event": "infra.deploy.started", "data": {...}}' \
      ${{ env.N8N_WEBHOOK_URL }}/webhook/infra-deploy
```

### n8n Webhook Node Configuration

In n8n workflows, webhook nodes are configured to:
- Accept POST requests
- Validate authentication token
- Parse incoming payload
- Trigger workflow execution

## API Authentication

### API Key Authentication

n8n API keys are stored in AWS Secrets Manager and referenced via ARN in configuration files.

**Retrieval:**
```bash
aws secretsmanager get-secret-value \
  --secret-id automation-hub/dev/n8n-api-key \
  --query SecretString --output text
```

### API Usage

**Base URL:** `{n8n_base_url}/api/v1`

**Common Endpoints:**
- `GET /workflows` - List workflows
- `POST /workflows` - Create workflow
- `PUT /workflows/{id}` - Update workflow
- `DELETE /workflows/{id}` - Delete workflow
- `POST /workflows/{id}/activate` - Activate workflow
- `POST /workflows/{id}/deactivate` - Deactivate workflow

## Database Configuration

### PostgreSQL (Recommended for Production)

**Connection String:**
```
postgresql://{user}:{password}@{host}:5432/{database}
```

**Credentials:** Stored in AWS Secrets Manager

### SQLite (Development Only)

For development, n8n can use SQLite (default). Production should use PostgreSQL.

## Backup Configuration

### Workflow Backups

Workflows are backed up to S3 via GitHub Actions:
- **Frequency:** Daily
- **Location:** `s3://automation-hub-{env}-workflows/backups/`
- **Retention:** 30 days (dev), 90 days (prod)

See `.github/workflows/backup-to-s3.yaml` for backup automation.

## Monitoring and Observability

### Metrics Endpoint

n8n exposes metrics at:
```
{n8n_base_url}/metrics
```

**Metrics:**
- `n8n_workflow_executions_total`
- `n8n_workflow_executions_failed_total`
- `n8n_workflow_execution_duration_seconds`

### Logging

n8n logs are configured to:
- Output JSON format
- Include correlation IDs
- Send to Prometheus for metrics
- Send to CloudWatch (production)

## Security Considerations

### Network Security

- n8n instances should be in private subnets
- Access via load balancer only
- No direct public internet access

### Authentication

- API keys stored in AWS Secrets Manager
- Webhook tokens rotated regularly
- IAM roles with least-privilege access

### Encryption

- Data encrypted at rest (database)
- Data encrypted in transit (TLS)
- Encryption keys in AWS Secrets Manager

## Troubleshooting

### Health Check Failures

1. Check n8n container/process status
2. Verify database connectivity
3. Check environment variables
4. Review n8n logs
5. Verify AWS Secrets Manager access

### Webhook Failures

1. Verify webhook URL is correct
2. Check authentication token
3. Validate payload format
4. Review n8n workflow logs
5. Check network connectivity

### API Authentication Issues

1. Verify API key from AWS Secrets Manager
2. Check IAM role permissions
3. Validate token format
4. Review API request logs

## References

- n8n Documentation: https://docs.n8n.io
- Environment Configs: `shared/config/environments.{env}.yaml`
- Secrets Strategy: `docs/SECRETS_STRATEGY.md`
- Backup Workflow: `.github/workflows/backup-to-s3.yaml`

