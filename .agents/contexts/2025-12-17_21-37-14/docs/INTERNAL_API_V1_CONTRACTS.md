# Internal API v1 Contracts

**Purpose:** Generated contract reference for Automation Hub Internal API (v1).
**Created/Updated:** 2025-12-17
**Agent:** BACKEND_AGENT

## Authentication

All requests require an API key via HTTP Bearer auth.

Example header:

```text
Authorization: Bearer {api_key}
```

## Endpoints

### POST /internal/api/v1/events/{event_type}

Accepts an event envelope and triggers the workflow registered for the event type.

#### Path parameters

- `event_type` (string, required): Event type identifier (e.g., contact.created, infra.deploy.started).

#### Request

- **Content-Type**: `application/json`
- **Schema**: `shared/schemas/event.schema.json`

Example request:

```json
{
  "correlation_id": "corr-12345",
  "env": "dev",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "meta": {
    "tags": [
      "crm",
      "lead"
    ],
    "version": "v1"
  },
  "payload": {
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "source": "backend",
  "timestamp": "2025-11-20T12:00:00Z",
  "type": "contact.created"
}
```

#### Responses

- **200**: Event accepted and workflow triggered. (schema: `shared/schemas/internal_api_v1.event_accepted.response.schema.json`)
- **400**: Invalid event payload. (schema: `shared/schemas/internal_api_v1.error.response.schema.json`)
- **401**: Invalid or missing API key. (schema: `shared/schemas/internal_api_v1.error.response.schema.json`)
- **404**: Event type not found. (schema: `shared/schemas/internal_api_v1.error.response.schema.json`)
- **500**: Unexpected workflow or server error. (schema: `shared/schemas/internal_api_v1.error.response.schema.json`)

Example response 200:

```json
{
  "correlation_id": "corr-12345",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "timestamp": "2025-11-20T12:00:00Z",
  "workflow_id": "workflow-123"
}
```

Example response 400:

```json
{
  "error": "validation_failed",
  "errors": [
    "Missing required field: email",
    "Invalid email format"
  ],
  "message": "Payload validation failed",
  "status": "error"
}
```

Example response 401:

```json
{
  "error": "unauthorized",
  "message": "Invalid API key",
  "status": "error"
}
```

Example response 404:

```json
{
  "error": "event_type_not_found",
  "message": "No workflow registered for event type: contact.created",
  "status": "error"
}
```

### GET /internal/api/v1/health

Returns API version and key dependency connectivity status.

#### Responses

- **200**: Health status. (schema: `shared/schemas/internal_api_v1.health.response.schema.json`)
- **401**: Invalid or missing API key. (schema: `shared/schemas/internal_api_v1.error.response.schema.json`)

Example response 200:

```json
{
  "services": {
    "database": "connected",
    "n8n": "connected",
    "prometheus": "connected"
  },
  "status": "ok",
  "timestamp": "2025-11-20T12:00:00Z",
  "version": "v1"
}
```
