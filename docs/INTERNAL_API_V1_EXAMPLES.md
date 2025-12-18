# Internal API v1 - Examples and Usage Guide

**Purpose:** Comprehensive curl examples and usage patterns for Internal API v1  
**Created/Updated:** 2025-12-17  
**Agent:** GPT-5.2

## Overview

This document provides practical examples for using the Internal API v1, including curl commands, rate limiting details, and common usage patterns.

## Authentication

All API requests require a Bearer token in the Authorization header:

```bash
export API_KEY="your-api-key-here"
export API_BASE_URL="https://n8n.automation-hub.example.com"
```

## Rate Limiting

### Limits by Endpoint

**POST /internal/api/v1/events/{event_type}:**
- Default limit: 100 requests per minute per API key
- Burst limit: 20 requests per second
- Rate limit headers included in all responses

**GET /internal/api/v1/health:**
- Default limit: 60 requests per minute per API key
- Burst limit: 10 requests per second

### Rate Limit Headers

All responses include rate limiting information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

### Handling Rate Limits

When rate limit is exceeded (HTTP 429):

```bash
# Check reset time from headers
RESET_TIME=$(curl -sI "$API_BASE_URL/internal/api/v1/events/contact.created" \
  -H "Authorization: Bearer $API_KEY" | grep -i "X-RateLimit-Reset" | cut -d' ' -f2)

# Wait and retry
sleep $((RESET_TIME - $(date +%s)))
```

## Endpoint Examples

### POST /internal/api/v1/events/{event_type}

#### Example 1: Contact Created Event

```bash
curl -X POST "$API_BASE_URL/internal/api/v1/events/contact.created" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "contact.created",
    "source": "backend",
    "env": "prod",
    "timestamp": "2025-12-17T12:00:00Z",
    "correlation_id": "corr-12345",
    "payload": {
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company": "Acme Corp"
    },
    "meta": {
      "version": "v1",
      "tags": ["crm", "lead"]
    }
  }'
```

**Expected Response (200 OK):**
```json
{
  "status": "accepted",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "workflow-123",
  "correlation_id": "corr-12345",
  "timestamp": "2025-12-17T12:00:00Z"
}
```

#### Example 2: Infrastructure Deployment Started

```bash
curl -X POST "$API_BASE_URL/internal/api/v1/events/infra.deploy.started" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "type": "infra.deploy.started",
    "source": "github",
    "env": "prod",
    "timestamp": "2025-12-17T12:00:00Z",
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

#### Example 3: Contact Enrichment Requested

```bash
curl -X POST "$API_BASE_URL/internal/api/v1/events/contact.enrichment.requested" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "type": "contact.enrichment.requested",
    "source": "n8n",
    "env": "prod",
    "timestamp": "2025-12-17T12:00:00Z",
    "correlation_id": "enrich-12345",
    "payload": {
      "email": "user@example.com",
      "enrichment_sources": ["clearbit", "zoominfo"]
    }
  }'
```

### Error Responses

#### Example: Validation Error (400)

```bash
# Missing required field
curl -X POST "$API_BASE_URL/internal/api/v1/events/contact.created" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "contact.created",
    "source": "backend",
    "env": "prod",
    "timestamp": "2025-12-17T12:00:00Z",
    "payload": {
      "first_name": "John"
    }
  }'
```

**Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": "validation_failed",
  "message": "Payload validation failed",
  "errors": [
    "Missing required field: email"
  ]
}
```

#### Example: Unauthorized (401)

```bash
# Invalid or missing API key
curl -X POST "$API_BASE_URL/internal/api/v1/events/contact.created" \
  -H "Authorization: Bearer invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"id":"...","type":"contact.created",...}'
```

**Response (401 Unauthorized):**
```json
{
  "status": "error",
  "error": "unauthorized",
  "message": "Invalid API key"
}
```

#### Example: Event Type Not Found (404)

```bash
# Unknown event type
curl -X POST "$API_BASE_URL/internal/api/v1/events/unknown.event" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id":"...","type":"unknown.event",...}'
```

**Response (404 Not Found):**
```json
{
  "status": "error",
  "error": "event_type_not_found",
  "message": "No workflow registered for event type: unknown.event"
}
```

### GET /internal/api/v1/health

```bash
curl -X GET "$API_BASE_URL/internal/api/v1/health" \
  -H "Authorization: Bearer $API_KEY"
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "version": "v1",
  "timestamp": "2025-12-17T12:00:00Z",
  "services": {
    "n8n": "connected",
    "database": "connected",
    "prometheus": "connected"
  }
}
```

## Usage Patterns

### Batch Event Processing

```bash
#!/bin/bash
# Process multiple events in sequence

EVENTS=(
  '{"id":"...","type":"contact.created",...}'
  '{"id":"...","type":"contact.created",...}'
  '{"id":"...","type":"contact.created",...}'
)

for event in "${EVENTS[@]}"; do
  curl -X POST "$API_BASE_URL/internal/api/v1/events/contact.created" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$event"
  sleep 0.1  # Small delay to respect rate limits
done
```

### Error Handling with Retry

```bash
#!/bin/bash
# Retry logic for transient failures

MAX_RETRIES=3
RETRY_DELAY=2

send_event() {
  local event_type=$1
  local payload=$2
  local retry_count=0

  while [ $retry_count -lt $MAX_RETRIES ]; do
    response=$(curl -s -w "\n%{http_code}" -X POST \
      "$API_BASE_URL/internal/api/v1/events/$event_type" \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" \
      -d "$payload")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 202 ]; then
      echo "Success: $body"
      return 0
    elif [ "$http_code" -eq 429 ]; then
      echo "Rate limited, waiting..."
      sleep $RETRY_DELAY
      retry_count=$((retry_count + 1))
    elif [ "$http_code" -ge 400 ] && [ "$http_code" -lt 500 ]; then
      echo "Client error: $body"
      return 1
    else
      echo "Server error, retrying..."
      sleep $RETRY_DELAY
      retry_count=$((retry_count + 1))
    fi
  done
  
  echo "Failed after $MAX_RETRIES attempts"
  return 1
}
```

### Python Example

```python
import requests
import time
from typing import Dict, Any

class InternalAPI:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def send_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an event to the Internal API."""
        url = f"{self.base_url}/internal/api/v1/events/{event_type}"
        response = requests.post(url, json=event_data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        url = f"{self.base_url}/internal/api/v1/health"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

# Usage
api = InternalAPI("https://n8n.automation-hub.example.com", "your-api-key")

event = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "contact.created",
    "source": "backend",
    "env": "prod",
    "timestamp": "2025-12-17T12:00:00Z",
    "payload": {
        "email": "user@example.com",
        "first_name": "John"
    }
}

result = api.send_event("contact.created", event)
print(result)
```

## Testing

### Health Check Test

```bash
#!/bin/bash
# Simple health check test

if curl -sf -H "Authorization: Bearer $API_KEY" \
  "$API_BASE_URL/internal/api/v1/health" > /dev/null; then
  echo "API is healthy"
  exit 0
else
  echo "API health check failed"
  exit 1
fi
```

### Event Validation Test

```bash
#!/bin/bash
# Test event validation

# Valid event
curl -X POST "$API_BASE_URL/internal/api/v1/events/contact.created" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "contact.created",
    "source": "backend",
    "env": "prod",
    "timestamp": "2025-12-17T12:00:00Z",
    "payload": {"email": "test@example.com"}
  }' | jq .

# Invalid event (missing email)
curl -X POST "$API_BASE_URL/internal/api/v1/events/contact.created" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "contact.created",
    "source": "backend",
    "env": "prod",
    "timestamp": "2025-12-17T12:00:00Z",
    "payload": {}
  }' | jq .
```

## References

- API Specification: `docs/INTERNAL_API_V1.md`
- OpenAPI Spec: `docs/INTERNAL_API_V1.openapi.yaml`
- Event Schema: `shared/schemas/event.schema.json`
- Contracts: `docs/INTERNAL_API_V1_CONTRACTS.md`
