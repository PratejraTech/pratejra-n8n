# Workflow Specifications

**Purpose:** Document workflow structure, requirements, and integration patterns for all domain workflows  
**Created/Updated:** 2025-11-20  
**Agent:** BACKEND_AGENT

## Overview

This document defines the specifications, requirements, and patterns for all workflows in the Automation Hub platform. Actual workflow JSON implementations will be created separately based on these specifications.

## CRM Workflow Specifications

### Workflow: lead_intake

**Purpose:** Capture and process new leads from various sources

**Location:** `workflows/domains/crm/lead_intake.json`

**Trigger:** Webhook (POST)

**Input Schema:** `contact.schema.json` (v1)

**Workflow Steps:**
1. **Webhook Node** - Receive lead data
2. **Code Node** - Validate payload using `validate_payload.js` against `contact.schema.json`
3. **Code Node** - Normalize contact data using `normalize_contact.js`
4. **Code Node** - Compute risk score using `compute_risk_score.js`
5. **HTTP Request Node** - Store in database/CRM system
6. **Error Handler** - Reference `error_central_handler` workflow
7. **Log Event Node** - Log event using `log_event` workflow

**Integration Points:**
- Uses shared schemas: `contact.schema.json`
- Uses shared snippets: `validate_payload.js`, `normalize_contact.js`, `compute_risk_score.js`
- References error handler: `error_central_handler`
- References log event: `log_event`

**Dependencies:**
- Shared schemas (Phase 1)
- Shared JS snippets (Phase 1)
- Error handler workflow (Phase 2)
- Log event workflow (Phase 2)

### Workflow: lead_enrichment

**Purpose:** Enrich lead data with additional information from external sources

**Location:** `workflows/domains/crm/lead_enrichment.json`

**Trigger:** Internal API event or webhook

**Input Schema:** `contact.schema.json` (v1) with `metadata.enrichment_status: "pending"`

**Workflow Steps:**
1. **Webhook/HTTP Request Node** - Receive contact data
2. **Code Node** - Validate payload
3. **HTTP Request Node** - Enrich from external API (e.g., Clearbit, ZoomInfo)
4. **Code Node** - Merge enriched data with original contact
5. **Code Node** - Update risk score based on enriched data
6. **HTTP Request Node** - Update contact in database
7. **Error Handler** - Reference `error_central_handler` workflow
8. **Log Event Node** - Log enrichment completion

**Integration Points:**
- Uses shared schemas: `contact.schema.json`
- Uses shared snippets: `validate_payload.js`, `compute_risk_score.js`
- References error handler: `error_central_handler`
- References log event: `log_event`

### Workflow: lead_sync_to_crm

**Purpose:** Synchronize enriched leads to external CRM systems

**Location:** `workflows/domains/crm/lead_sync_to_crm.json`

**Trigger:** Internal API event or scheduled

**Input Schema:** `contact.schema.json` (v1) with `status: "qualified"`

**Workflow Steps:**
1. **Webhook/HTTP Request Node** - Receive contact data
2. **Code Node** - Validate payload
3. **Code Node** - Transform to CRM format (e.g., Salesforce, HubSpot)
4. **HTTP Request Node** - Create/Update in CRM system
5. **Code Node** - Update sync status
6. **Error Handler** - Reference `error_central_handler` workflow
7. **Log Event Node** - Log sync completion
8. **Slack Notification** - Optional notification via `notify_slack` workflow

**Integration Points:**
- Uses shared schemas: `contact.schema.json`
- Uses shared snippets: `validate_payload.js`
- References error handler: `error_central_handler`
- References log event: `log_event`
- References Slack notification: `notify_slack` (optional)

## Infrastructure Workflow Specifications

### Workflow: infra_deploy_terraform

**Purpose:** Deploy infrastructure using Terraform triggered by GitHub Actions

**Location:** `workflows/domains/infra/infra_deploy_terraform.json`

**Trigger:** GitHub Actions webhook (POST)

**Input Schema:** `infra_deploy.schema.json` (v1)

**Workflow Steps:**
1. **Webhook Node** - Receive deployment request from GitHub Actions
2. **Code Node** - Validate payload using `validate_payload.js` against `infra_deploy.schema.json`
3. **Code Node** - Check if approval required (based on environment)
4. **Approval Node** - If required, trigger `approvals_generic` workflow
5. **HTTP Request Node** - Execute Terraform plan
6. **Code Node** - Parse Terraform output
7. **HTTP Request Node** - Execute Terraform apply (if plan successful)
8. **Error Handler** - Reference `error_central_handler` workflow
9. **Log Event Node** - Log deployment completion
10. **Slack Notification** - Notify via `notify_slack` workflow

**Integration Points:**
- Uses shared schemas: `infra_deploy.schema.json`
- Uses shared snippets: `validate_payload.js`
- References error handler: `error_central_handler`
- References log event: `log_event`
- References approvals: `approvals_generic`
- References Slack notification: `notify_slack`
- Triggered by GitHub Actions webhook

**Dependencies:**
- GitHub Actions integration (Phase 1)
- Shared schemas (Phase 1)
- Shared workflows (Phase 2)

### Workflow: infra_post_deploy_checks

**Purpose:** Validate infrastructure deployment and run post-deployment checks

**Location:** `workflows/domains/infra/infra_post_deploy_checks.json`

**Trigger:** Internal API event or webhook (called after infra_deploy_terraform)

**Input Schema:** `infra_deploy.schema.json` (v1) with `status: "success"`

**Workflow Steps:**
1. **Webhook/HTTP Request Node** - Receive deployment result
2. **Code Node** - Validate payload
3. **HTTP Request Node** - Run health checks on deployed resources
4. **HTTP Request Node** - Validate connectivity
5. **HTTP Request Node** - Run smoke tests
6. **Code Node** - Aggregate check results
7. **Code Node** - Update deployment status
8. **Error Handler** - Reference `error_central_handler` workflow
9. **Log Event Node** - Log check results
10. **Slack Notification** - Notify results via `notify_slack` workflow

**Integration Points:**
- Uses shared schemas: `infra_deploy.schema.json`
- Uses shared snippets: `validate_payload.js`
- References error handler: `error_central_handler`
- References log event: `log_event`
- References Slack notification: `notify_slack`

## Meta Workflow Specifications

### Workflow: automation_catalog_builder

**Purpose:** Automatically generate workflows_catalog.yaml and ownership.yaml

**Location:** `workflows/domains/meta/automation_catalog_builder.json`

**Trigger:** Scheduled (daily) or manual webhook

**Input Schema:** None (reads workflow files directly)

**Workflow Steps:**
1. **HTTP Request Node** - Fetch all workflow files from repository
2. **Code Node** - Parse workflow JSON files
3. **Code Node** - Extract metadata (name, description, domain, owner)
4. **Code Node** - Generate workflows_catalog.yaml
5. **Code Node** - Generate ownership.yaml
6. **HTTP Request Node** - Commit to repository (via GitHub API)
7. **Error Handler** - Reference `error_central_handler` workflow
8. **Log Event Node** - Log catalog generation

**Integration Points:**
- References error handler: `error_central_handler`
- References log event: `log_event`
- Outputs to: `workflows/metadata/workflows_catalog.yaml` and `workflows/metadata/ownership.yaml`

### Workflow: workflow_health_check

**Purpose:** Monitor and check health of all workflows

**Location:** `workflows/domains/meta/workflow_health_check.json`

**Trigger:** Scheduled (hourly) or manual webhook

**Input Schema:** None

**Workflow Steps:**
1. **HTTP Request Node** - Query n8n API for all workflows
2. **Code Node** - Check workflow execution status
3. **Code Node** - Identify failed workflows
4. **Code Node** - Aggregate health metrics
5. **HTTP Request Node** - Send metrics to Prometheus
6. **Code Node** - Generate health report
7. **Error Handler** - Reference `error_central_handler` workflow
8. **Log Event Node** - Log health check results
9. **Slack Notification** - Alert on critical issues via `notify_slack` workflow

**Integration Points:**
- References error handler: `error_central_handler`
- References log event: `log_event`
- References Slack notification: `notify_slack`
- Sends metrics to Prometheus

## Shared Workflow Specifications

### Workflow: error_central_handler

**Purpose:** Central error handling for all workflows

**Location:** `workflows/domains/shared/error_central_handler.json`

**Trigger:** Called by other workflows on error

**Input Schema:** `incident.schema.json` (v1)

**Workflow Steps:**
1. **Webhook Node** - Receive error/incident data
2. **Code Node** - Validate incident schema
3. **Code Node** - Categorize error severity
4. **Code Node** - Determine retry strategy
5. **HTTP Request Node** - Store incident in database
6. **Log Event Node** - Log error to Prometheus
7. **Slack Notification** - Notify on high/critical severity via `notify_slack` workflow
8. **Code Node** - Return error response

**Integration Points:**
- Uses shared schemas: `incident.schema.json`
- Uses shared snippets: `validate_payload.js`
- References log event: `log_event`
- References Slack notification: `notify_slack`
- Called by all domain workflows

### Workflow: log_event

**Purpose:** Central event logging to Prometheus and other observability systems

**Location:** `workflows/domains/shared/log_event.json`

**Trigger:** Called by other workflows for logging

**Input Schema:** `event.schema.json` (v1)

**Workflow Steps:**
1. **Webhook Node** - Receive event data
2. **Code Node** - Validate event schema
3. **Code Node** - Add correlation_id if missing
4. **HTTP Request Node** - Send to Prometheus metrics endpoint
5. **HTTP Request Node** - Send to CloudWatch (production)
6. **Code Node** - Return success response

**Integration Points:**
- Uses shared schemas: `event.schema.json`
- Uses shared snippets: `validate_payload.js`
- Sends to Prometheus
- Sends to CloudWatch (production)
- Called by all domain workflows

### Workflow: notify_slack

**Purpose:** Send notifications to Slack channels

**Location:** `workflows/domains/shared/notify_slack.json`

**Trigger:** Called by other workflows for notifications

**Input Schema:** Custom (channel, message, severity)

**Workflow Steps:**
1. **Webhook Node** - Receive notification request
2. **Code Node** - Format Slack message
3. **Code Node** - Determine channel based on severity/environment
4. **HTTP Request Node** - Send to Slack webhook (from AWS Secrets Manager)
5. **Code Node** - Return success response

**Integration Points:**
- Uses Slack webhook from AWS Secrets Manager
- Called by workflows requiring notifications
- Supports different channels per environment/severity

### Workflow: approvals_generic

**Purpose:** Generic approval workflow for sensitive operations

**Location:** `workflows/domains/shared/approvals_generic.json`

**Trigger:** Called by workflows requiring approval

**Input Schema:** Custom (approval_type, requester, details)

**Workflow Steps:**
1. **Webhook Node** - Receive approval request
2. **Code Node** - Format approval message
3. **Slack Notification** - Send approval request to designated channel via `notify_slack`
4. **Wait Node** - Wait for approval response (timeout: 24 hours)
5. **Code Node** - Parse approval response
6. **Code Node** - Return approval status

**Integration Points:**
- References Slack notification: `notify_slack`
- Called by workflows requiring human approval
- Used for high-risk operations (e.g., production deployments)

## Workflow Templates and Patterns

### Standard Workflow Pattern

All workflows should follow this pattern:
1. **Trigger** (Webhook/HTTP Request/Scheduled)
2. **Validation** (Code node with `validate_payload.js`)
3. **Business Logic** (Domain-specific processing)
4. **Error Handling** (Reference `error_central_handler`)
5. **Logging** (Reference `log_event`)
6. **Notification** (Optional: Reference `notify_slack`)

### Error Handling Pattern

All workflows must:
- Catch errors in try-catch blocks
- Call `error_central_handler` workflow on error
- Include correlation_id for tracing
- Log errors with appropriate severity

### Schema Validation Pattern

All workflows must:
- Validate input payloads against schemas
- Use `validate_payload.js` snippet
- Reject invalid payloads with clear error messages
- Log validation failures

## Integration Dependencies

### Phase 1 Dependencies (Required)
- Shared schemas (event, contact, incident, infra_deploy)
- Shared JS snippets (validate_payload, normalize_contact, compute_risk_score)
- Environment configuration
- AWS Secrets Manager integration

### Phase 2 Dependencies (Required)
- Shared workflows (error_central_handler, log_event, notify_slack, approvals_generic)
- Internal API v1 endpoints
- Metadata structures (ownership.yaml, workflows_catalog.yaml)

### Phase 3 Dependencies (Required)
- Prometheus integration
- Grafana dashboards
- CI/CD pipelines
- Backup systems

## References

- Schema Definitions: `shared/schemas/`
- JS Snippets: `shared/js_snippets/`
- Environment Configs: `shared/config/environments.{env}.yaml`
- Workflow Naming: `docs/WORKFLOW_NAMING.md`
- Error Handling: `docs/ERROR_HANDLING.md`
- Data Contracts: `docs/DATA_CONTRACTS.md`

