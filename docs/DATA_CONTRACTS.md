# Purpose: Data contracts and schema definitions documentation for automation platform
# Created/Updated: 2025-11-20
# Agent: BACKEND_AGENT

# Data Contracts - Automation Hub

## Overview

This document defines the data contracts (JSON schemas) used across the Automation Hub platform. All workflows must validate payloads against these schemas to ensure data consistency and integrity.

## Schema Versioning

All schemas follow semantic versioning:
- **v1:** Initial schema version
- **v1.1, v1.2, etc.:** Backward-compatible additions (new optional fields)
- **v2:** Breaking changes (requires PRD update and migration plan)

## Schema Location

All schema files are located in `shared/schemas/`:
- `event.schema.json` (v1)
- `contact.schema.json` (v1)
- `incident.schema.json` (v1)
- `infra_deploy.schema.json` (v1)

## Schema Definitions

### Event Schema (v1)

**File:** `shared/schemas/event.schema.json`

**Purpose:** Internal event structure for all automation events

**Required Fields:**
- `id`: Unique event identifier (UUID)
- `type`: Event type (e.g., "contact.created", "infra.deploy.started")
- `source`: Source system (n8n, backend, frontend, infra, github, external)
- `env`: Environment (dev, staging, prod)
- `timestamp`: ISO 8601 timestamp
- `payload`: Event-specific payload data

**Optional Fields:**
- `correlation_id`: Correlation ID for tracing
- `meta`: Additional metadata (raw data, tags, version)

**Usage:**
- All workflows log events using this schema
- Internal API v1 uses this schema for event payloads
- Prometheus metrics are derived from events

**Example:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "workflow.execution.completed",
  "source": "n8n",
  "env": "prod",
  "timestamp": "2025-11-20T12:00:00Z",
  "correlation_id": "corr-12345",
  "payload": {
    "workflow_name": "lead_intake",
    "status": "success",
    "duration_ms": 1250
  }
}
```

### Contact Schema (v1)

**File:** `shared/schemas/contact.schema.json`

**Purpose:** Contact/lead data structure for CRM workflows

**Required Fields:**
- `email`: Contact email address

**Optional Fields:**
- `id`: Unique contact identifier (UUID)
- `first_name`, `last_name`: Contact name
- `company`: Company name
- `phone`: Phone number (E.164 format)
- `title`: Job title
- `source`: Lead source
- `status`: Contact status (new, contacted, qualified, converted, lost)
- `tags`: Array of tags
- `custom_fields`: Custom organization-specific fields
- `created_at`, `updated_at`: Timestamps
- `metadata`: Additional metadata (risk_score, enrichment_status)

**Usage:**
- CRM workflows (lead_intake, lead_enrichment, lead_sync_to_crm)
- Data normalization via `normalize_contact.js`
- Risk scoring via `compute_risk_score.js`

**Example:**
```json
{
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Example Corp",
  "phone": "+1234567890",
  "source": "website",
  "status": "new",
  "metadata": {
    "risk_score": 25
  }
}
```

### Incident Schema (v1)

**File:** `shared/schemas/incident.schema.json`

**Purpose:** Error/incident tracking structure for error handling workflows

**Required Fields:**
- `id`: Unique incident identifier (UUID)
- `source`: Source system
- `severity`: Severity level (low, medium, high, critical)
- `status`: Incident status (open, investigating, mitigated, resolved, closed)
- `event_type`: Type of event that triggered the incident
- `error`: Error details (message required)
- `context`: Contextual information (env required)
- `created_at`: ISO 8601 timestamp

**Optional Fields:**
- `workflow`: Workflow context (id, name, run_id)
- `updated_at`, `resolved_at`: Timestamps
- `metadata`: Additional metadata (retry_count, notified, runbook_url)

**Usage:**
- Error central handler workflow
- Incident tracking and resolution
- Error reporting to observability systems

**Example:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "source": "n8n",
  "severity": "high",
  "status": "open",
  "event_type": "workflow.execution.failed",
  "error": {
    "message": "Validation failed: missing required field 'email'",
    "type": "ValidationError"
  },
  "context": {
    "env": "prod",
    "service": "lead_intake",
    "correlation_id": "corr-12345"
  },
  "created_at": "2025-11-20T12:00:00Z"
}
```

### Infrastructure Deployment Schema (v1)

**File:** `shared/schemas/infra_deploy.schema.json`

**Purpose:** Infrastructure deployment events triggered by GitHub Actions

**Required Fields:**
- `id`: Unique deployment identifier (UUID)
- `deployment_type`: Type (terraform, kubernetes, docker, cloudformation, other)
- `environment`: Target environment (dev, staging, prod)
- `status`: Deployment status (pending, in_progress, success, failed, rolled_back, cancelled)
- `triggered_by`: Trigger information (type, source required)
- `created_at`: ISO 8601 timestamp

**Optional Fields:**
- `target`: Deployment target information (resource_type, resource_name, region, terraform_workspace)
- `started_at`, `completed_at`: Timestamps
- `duration_seconds`: Deployment duration
- `output`: Deployment output/results
- `error`: Error information if deployment failed
- `post_deploy_checks`: Post-deployment validation results
- `metadata`: Additional metadata (approval_required, approved_by, notified_channels)

**Usage:**
- Infrastructure deployment workflows
- GitHub Actions integration
- Terraform deployment tracking

**Example:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "deployment_type": "terraform",
  "environment": "prod",
  "status": "in_progress",
  "triggered_by": {
    "type": "github_action",
    "source": "run-12345",
    "commit_sha": "abc123",
    "branch": "main"
  },
  "target": {
    "resource_type": "ec2",
    "region": "us-east-1",
    "terraform_workspace": "prod"
  },
  "created_at": "2025-11-20T12:00:00Z"
}
```

## Schema Validation

### Validation Process

1. **Payload Receipt:** Workflow receives payload
2. **Schema Selection:** Determine appropriate schema based on workflow/endpoint
3. **Validation:** Use `validate_payload.js` snippet to validate against schema
4. **Error Handling:** If validation fails, trigger error handler workflow
5. **Processing:** If validation passes, proceed with workflow execution

### Validation Implementation

All workflows must use `validate_payload.js` snippet:

```javascript
// In n8n Code node
const validationResult = validatePayload($input.item.json, 'contact');
if (!validationResult.valid) {
  throw new Error(`Validation failed: ${validationResult.errors.join(', ')}`);
}
```

## Schema Evolution

### Adding Fields (v1 → v1.1)

1. Add new fields as optional (not in `required` array)
2. Update schema file with new version
3. Update documentation
4. Test backward compatibility
5. Deploy schema update

### Breaking Changes (v1 → v2)

1. Update PRD with breaking change justification
2. Create migration plan
3. Update schema to v2
4. Update all workflows using the schema
5. Deploy with migration window
6. Deprecate v1 after migration period

## Schema Documentation

Each schema file includes:
- Title and description
- Version information
- Required and optional fields
- Field types and constraints
- Validation rules (patterns, enums, formats)
- Examples (in this document)

## Best Practices

1. **Always validate:** Never skip schema validation
2. **Version carefully:** Use semantic versioning
3. **Document changes:** Update this document with schema changes
4. **Test compatibility:** Ensure backward compatibility for minor versions
5. **Migrate gradually:** Plan migration for breaking changes

## References

- Schema files: `shared/schemas/*.schema.json`
- Validation snippet: `shared/js_snippets/validate_payload.js`
- Normalization snippet: `shared/js_snippets/normalize_contact.js`
- Event flow: See `architecture.mdc` section 3.1
