# Secrets Management Strategy

**Purpose:** Document AWS Secrets Manager integration pattern and secrets management approach  
**Created/Updated:** 2025-11-20  
**Agent:** BACKEND_AGENT

## Overview

All secrets and sensitive configuration values must be stored in AWS Secrets Manager. No secrets should be hardcoded in configuration files, workflow definitions, or source code.

## AWS Secrets Manager Integration

### Secret Naming Convention

Secrets follow a hierarchical naming pattern:
```
automation-hub/{environment}/{service}/{secret-name}
```

**Examples:**
- `automation-hub/dev/n8n-api-key`
- `automation-hub/prod/slack-webhook`
- `automation-hub/dev/terraform-state`

### Secret ARN Format

All secrets are referenced by their ARN in configuration files:
```
arn:aws:secretsmanager:{region}:{account-id}:secret:{secret-name}
```

### Environment-Specific Secrets

Secrets are organized by environment:
- **Development:** `automation-hub/dev/*`
- **Staging:** `automation-hub/staging/*`
- **Production:** `automation-hub/prod/*`

## Secret Types

### 1. API Keys
- n8n API keys
- Grafana API keys
- External service API keys

**Storage:** AWS Secrets Manager  
**Access:** Via IAM roles with least-privilege permissions

### 2. Webhook URLs
- Slack webhook URLs
- External service webhooks

**Storage:** AWS Secrets Manager  
**Access:** Via IAM roles

### 3. Database Credentials
- Connection strings
- Usernames and passwords

**Storage:** AWS Secrets Manager  
**Access:** Via IAM roles

### 4. Infrastructure Secrets
- Terraform state bucket credentials
- AWS access keys (if required)

**Storage:** AWS Secrets Manager  
**Access:** Via IAM roles

## Configuration File Integration

### Environment Config Files

Secrets are referenced in `shared/config/environments.{env}.yaml`:

```yaml
n8n:
  api_key_secret_arn: "arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/dev/n8n-api-key"

external_services:
  slack:
    webhook_secret_arn: "arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/dev/slack-webhook"
```

### Retrieval Pattern

Secrets are retrieved at runtime using AWS SDK:

```javascript
// Example: Retrieving secret in n8n Code node
const AWS = require('aws-sdk');
const secretsManager = new AWS.SecretsManager({ region: 'us-east-1' });

const secretArn = $env.SECRET_ARN;
const secret = await secretsManager.getSecretValue({ SecretId: secretArn }).promise();
const secretValue = JSON.parse(secret.SecretString);
```

## IAM Roles and Permissions

### n8n Execution Role

The n8n execution role must have permissions to:
- Read secrets from Secrets Manager
- Access S3 buckets for backups
- Assume roles for cross-account access (if needed)

**Policy Example:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:automation-hub/*"
    }
  ]
}
```

### Least-Privilege Principle

- Each service/role only has access to secrets it needs
- Secrets are scoped by environment
- No cross-environment secret access

## Secret Rotation

### Rotation Policy

- API keys: Rotate every 90 days
- Webhook URLs: Rotate on security incident or service change
- Database credentials: Rotate every 60 days

### Rotation Process

1. Create new secret version in Secrets Manager
2. Update workflows to use new secret version
3. Test in development environment
4. Promote to staging, then production
5. Deprecate old secret version after verification

## Security Best Practices

### ✅ DO

- Store all secrets in AWS Secrets Manager
- Reference secrets by ARN in configuration files
- Use IAM roles with least-privilege permissions
- Rotate secrets regularly
- Use environment-specific secrets
- Encrypt secrets at rest (AWS default)

### ❌ DON'T

- Hardcode secrets in source code
- Commit secrets to version control
- Share secrets via email or chat
- Use the same secrets across environments
- Store secrets in environment variables in code
- Log secret values

## Secret Mapping Reference

### Development Environment

| Service | Secret Name | ARN Pattern |
|---------|-------------|-------------|
| n8n API Key | `automation-hub/dev/n8n-api-key` | `arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/dev/n8n-api-key` |
| Slack Webhook | `automation-hub/dev/slack-webhook` | `arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/dev/slack-webhook` |
| Grafana API Key | `automation-hub/dev/grafana-api-key` | `arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/dev/grafana-api-key` |

### Production Environment

| Service | Secret Name | ARN Pattern |
|---------|-------------|-------------|
| n8n API Key | `automation-hub/prod/n8n-api-key` | `arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/prod/n8n-api-key` |
| Slack Webhook | `automation-hub/prod/slack-webhook` | `arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/prod/slack-webhook` |
| Grafana API Key | `automation-hub/prod/grafana-api-key` | `arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/prod/grafana-api-key` |

## Integration with n8n

### Environment Variables

n8n environment variables reference secret ARNs:
```
N8N_API_KEY_SECRET_ARN=arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/dev/n8n-api-key
SLACK_WEBHOOK_SECRET_ARN=arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/dev/slack-webhook
```

### Workflow Usage

Workflows retrieve secrets at runtime using AWS SDK in Code nodes or HTTP Request nodes with IAM authentication.

## Compliance

- All secrets must comply with organizational security policies
- Secrets must be encrypted at rest (AWS default)
- Access to secrets must be logged and audited
- Secret access must follow least-privilege principle

## References

- AWS Secrets Manager Documentation
- IAM Role Configuration: `infra/IAM/github-n8n-actions-iam.json`
- Environment Configs: `shared/config/environments.{env}.yaml`

