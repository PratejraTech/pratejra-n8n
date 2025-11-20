# Internal API v1 Specification

**Purpose:** Design and document the internal API v1 for event-driven workflow triggers  
**Created/Updated:** 2025-11-20  
**Agent:** BACKEND_AGENT

## Overview

The Internal API v1 provides a standardized interface for triggering workflows via structured events. All events must conform to the `event.schema.json` (v1) schema and are validated before workflow execution.

## Base URL

```
{environment}/internal/api/v1
```

**Examples:**
- Development: `http://localhost:5678/internal/api/v1`
- Production: `https://n8n.automation-hub.example.com/internal/api/v1`

## API Versioning

- **Current Version:** v1
- **Version Format:** `/internal/api/v1/`
- **Future Versions:** v2, v3 (backward compatibility maintained)

## Authentication

### API Key Authentication

All requests require an API key in the Authorization header:

```
Authorization: Bearer {api_key}
```

API keys are stored in AWS Secrets Manager:
- Development: `automation-hub/dev/internal-api-key`
- Production: `automation-hub/prod/internal-api-key`

### IAM Role Authentication (Alternative)

For AWS services, IAM role-based authentication is supported:
- OIDC tokens for GitHub Actions
- IAM roles for EC2/ECS instances

## Endpoints

### POST /internal/api/v1/events/{event_type}

Trigger a workflow based on event type.

**Path Parameters:**
- `event_type` (string, required): Event type identifier (e.g., `contact.created`, `infra.deploy.started`)

**Request Headers:**
```
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request Body:**
Must conform to `event.schema.json` (v1):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "contact.created",
  "source": "backend",
  "env": "dev",
  "timestamp": "2025-11-20T12:00:00Z",
  "correlation_id": "corr-12345",
  "payload": {
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "meta": {
    "version": "v1",
    "tags": ["crm", "lead"]
  }
}
```

**Response:**
- **200 OK:** Event accepted and workflow triggered
```json
{
  "status": "accepted",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "workflow-123",
  "correlation_id": "corr-12345",
  "timestamp": "2025-11-20T12:00:00Z"
}
```

- **400 Bad Request:** Invalid event payload
```json
{
  "status": "error",
  "error": "validation_failed",
  "message": "Payload validation failed",
  "errors": [
    "Missing required field: email",
    "Invalid email format"
  ]
}
```

- **401 Unauthorized:** Invalid or missing API key
```json
{
  "status": "error",
  "error": "unauthorized",
  "message": "Invalid API key"
}
```

- **404 Not Found:** Event type not found
```json
{
  "status": "error",
  "error": "event_type_not_found",
  "message": "No workflow registered for event type: contact.created"
}
```

### GET /internal/api/v1/health

Health check endpoint for the internal API.

**Request Headers:**
```
Authorization: Bearer {api_key}
```

**Response:**
- **200 OK:**
```json
{
  "status": "ok",
  "version": "v1",
  "timestamp": "2025-11-20T12:00:00Z",
  "services": {
    "n8n": "connected",
    "database": "connected",
    "prometheus": "connected"
  }
}
```

## Event Type Mapping

Event types map to specific workflows:

| Event Type | Workflow | Domain |
|------------|----------|--------|
| `contact.created` | `lead_intake` | CRM |
| `contact.enrichment.requested` | `lead_enrichment` | CRM |
| `contact.qualified` | `lead_sync_to_crm` | CRM |
| `infra.deploy.started` | `infra_deploy_terraform` | Infra |
| `infra.deploy.completed` | `infra_post_deploy_checks` | Infra |
| `workflow.error` | `error_central_handler` | Shared |
| `event.log` | `log_event` | Shared |

## Schema Validation

All events are validated against `event.schema.json` (v1) before processing:

1. **Schema Validation:** Using `validate_payload.js` snippet
2. **Type Validation:** Event type must be registered
3. **Payload Validation:** Payload must conform to domain-specific schema (if applicable)

### Validation Process

```javascript
// Pseudo-code for validation
const event = request.body;
const validationResult = validatePayload(event, 'event');

if (!validationResult.valid) {
  return 400 Bad Request with validation errors;
}

// Additional payload validation based on event type
if (event.type === 'contact.created') {
  const contactValidation = validatePayload(event.payload, 'contact');
  if (!contactValidation.valid) {
    return 400 Bad Request with contact validation errors;
  }
}
```

## Error Handling

### Validation Errors

- **Status Code:** 400 Bad Request
- **Response:** JSON with validation error details
- **Logging:** Errors logged to Prometheus with correlation_id

### Authentication Errors

- **Status Code:** 401 Unauthorized
- **Response:** JSON with error message
- **Logging:** Authentication failures logged for security monitoring

### Workflow Errors

- **Status Code:** 500 Internal Server Error
- **Response:** JSON with error details (correlation_id included)
- **Error Handler:** Errors trigger `error_central_handler` workflow
- **Logging:** All errors logged with full context

## Rate Limiting

- **Default Limit:** 100 requests per minute per API key
- **Burst Limit:** 20 requests per second
- **Response Headers:**
  - `X-RateLimit-Limit`: Request limit per minute
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

## Correlation ID

All events should include a `correlation_id` for tracing:
- Generated automatically if not provided
- Format: `corr-{timestamp}-{random}`
- Used for tracing events across workflows
- Included in all logs and error responses

## Integration Examples

### Example: Trigger CRM Workflow

```bash
curl -X POST \
  https://n8n.automation-hub.example.com/internal/api/v1/events/contact.created \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "contact.created",
    "source": "backend",
    "env": "prod",
    "timestamp": "2025-11-20T12:00:00Z",
    "payload": {
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    }
  }'
```

### Example: Trigger Infrastructure Deployment

```bash
curl -X POST \
  https://n8n.automation-hub.example.com/internal/api/v1/events/infra.deploy.started \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "type": "infra.deploy.started",
    "source": "github",
    "env": "prod",
    "timestamp": "2025-11-20T12:00:00Z",
    "correlation_id": "deploy-12345",
    "payload": {
      "deployment_type": "terraform",
      "environment": "prod",
      "triggered_by": {
        "type": "github_action",
        "source": "run-12345",
        "commit_sha": "abc123"
      }
    }
  }'
```

## Versioning Strategy

### Backward Compatibility

- v1 API will remain supported when v2 is introduced
- New endpoints added without breaking existing ones
- Schema evolution follows semantic versioning

### Migration Path

- v1 → v2: Gradual migration with deprecation notices
- v2 features: Enhanced validation, new event types, improved error handling
- Deprecation: 6-month notice before v1 removal

## Security Considerations

### API Key Management

- Keys stored in AWS Secrets Manager
- Keys rotated every 90 days
- Keys scoped by environment
- Keys can be revoked immediately

### Input Validation

- All inputs validated against schemas
- SQL injection prevention (if applicable)
- XSS prevention
- Rate limiting to prevent abuse

### Audit Logging

- All API calls logged with:
  - API key identifier (hashed)
  - Event type
  - Timestamp
  - Correlation ID
  - Response status

## Monitoring

### Metrics

Prometheus metrics exposed:
- `internal_api_requests_total{status, event_type}`
- `internal_api_request_duration_seconds{event_type}`
- `internal_api_validation_errors_total{event_type}`
- `internal_api_authentication_failures_total`

### Alerts

- High error rate (>5% failures)
- Authentication failure spike
- Rate limit exceeded frequently
- API response time degradation

## References

- Event Schema: `shared/schemas/event.schema.json`
- Validation Snippet: `shared/js_snippets/validate_payload.js`
- Environment Configs: `shared/config/environments.{env}.yaml`
- Secrets Strategy: `docs/SECRETS_STRATEGY.md`

