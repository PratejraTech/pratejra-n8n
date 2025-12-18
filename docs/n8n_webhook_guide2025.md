<!--
Purpose: Consolidated n8n integration guide for 2025 (webhooks, Central Dispatch, GitOps, auth, and operations)
Created/Updated: 2025-12-17 00:00
Agent: GPT-5.2
-->

## n8n Integration Guide (2025)

This document consolidates the repo’s **n8n integration** patterns: how n8n is configured, how webhooks should be exposed, how to use the **Central Webhook Dispatch** architecture, and how workflows are managed via GitOps.

### Key references in this repo
- `docs/N8N_CONFIGURATION.md` (instance configuration, env vars, webhook URL patterns)
- `docs/INTERNAL_API_V1.md` (event-driven internal API contract)
- `docs/WEBHOOK_DISPATCH.md` (Central Dispatch architecture and onboarding)
- `shared/schemas/event.schema.json` (Event Schema v1)
- `workflows/metadata/workflows_catalog.yaml` (primary GitOps workflow catalog)
- `workflows/metadata/webhooks_catalog.yaml` (overlay catalog for webhook-system workflows)
- `ops/scripts/n8n_gitops.py` (primary GitOps export/import/drift-check)
- `ops/scripts/n8n_gitops_webhooks.py` (overlay GitOps export/import/drift-check for dispatch workflows)

---

## n8n instance configuration (dev/staging/prod)

### Core environment variables
Typical minimums (see `docs/N8N_CONFIGURATION.md` for the canonical list):
- `N8N_HOST`, `N8N_PORT`, `N8N_PROTOCOL`
- `WEBHOOK_URL` (important for correct webhook URL generation behind proxies/LBs)
- `N8N_METRICS=true` (if observability is enabled)

### Database (recommended: Postgres for production)
Production should use Postgres (see `docs/N8N_CONFIGURATION.md`):
- `DB_TYPE=postgresdb`
- `DB_POSTGRESDB_HOST`, `DB_POSTGRESDB_DATABASE`, `DB_POSTGRESDB_USER`, password from secrets

### Health endpoints
Common checks (see `docs/N8N_CONFIGURATION.md`):
- `GET /healthz` (basic health)
- `GET /api/v1/health` (API health, typically requires auth)

---

## Authentication and secrets

### n8n REST API (GitOps tooling)
GitOps scripts use the n8n API key header:
- `X-N8N-API-KEY: <api_key>`

Used by:
- `ops/scripts/n8n_gitops.py`
- `ops/scripts/n8n_gitops_webhooks.py`

### Webhook ingress authentication (recommended)
For webhooks (including Central Dispatch), standardize on:
- `Authorization: Bearer <token>`

Where possible:
- Store secrets in AWS Secrets Manager (see `docs/SECRETS_STRATEGY.md`).
- Scope tokens by environment and rotate regularly.

---

## Webhook strategy: Central Dispatch (recommended)

### Why Central Dispatch
Avoid “20 workflows = 20 random webhook URLs”. Instead:
- **One stable webhook endpoint**: `POST /webhook/dispatch`
- Route by **event type** and a DB registry (enable/disable without workflow edits).

This architecture is defined in:
- `docs/WEBHOOK_DISPATCH.md`
- `workflows/domains/shared/webhook_dispatch.json`

### Supported inbound contracts (hybrid)
The dispatcher accepts either:

1) Event Schema v1 (preferred)
- Conforms to `shared/schemas/event.schema.json` with keys like `id`, `type`, `source`, `env`, `timestamp`, `payload`.

2) Simplified dispatch shape (supported for clients)

```json
{
  "event_type": "contact.created",
  "data": { "email": "user@example.com" },
  "metadata": {
    "source": "landing_page_v2",
    "env": "prod",
    "timestamp": "2025-12-17T00:00:00Z"
  }
}
```

The dispatcher normalizes the simplified shape into Event Schema v1, validates it, then routes it.

### Registry (“phonebook”) in Postgres
The dispatcher looks up routes in Postgres:
- Table created by: `ops/scripts/webhook_registry.sql`
- Row schema (documentation/validation): `shared/schemas/webhook_registry.schema.json`

Key columns:
- `event_type`: match to `event.type`
- `target_workflow_name`: stable routing key (fits GitOps upsert-by-name)
- `cached_n8n_workflow_id`: optional cache for routing by numeric id
- `required_payload_fields`: JSONB array of dot-paths enforced against `event.payload`

### Dispatch validation snippet (NodeJS/Bun)
Reusable logic for Code nodes:
- `shared/js_snippets/webhook_dispatch_validator.js`

---

## Implementing the dispatcher workflow in n8n (recommended node outline)

The repo includes an import-safe baseline workflow in:
- `workflows/domains/shared/webhook_dispatch.json`

Typical node sequence:
- **Webhook (POST /dispatch)**: receives inbound request
- **Code**: auth check + normalize hybrid input to Event Schema v1
- **Postgres**: `SELECT * FROM public.webhook_registry WHERE event_type = $1 AND is_active = true`
- **Code**: enforce `required_payload_fields`
- **Execute Workflow**: run worker workflow **asynchronously** (do not block sender)
- **Respond to Webhook**: return `202 Accepted` + `{status:"queued", type, correlation_id}`

Operational notes:
- Prefer “queue immediately” responses to avoid external sender timeouts.
- Log/emit events via your existing `log_event` workflow if you extend the dispatcher with observability.

---

## Worker workflows (how routing is intended to work)

Worker workflows are internal and should not expose public webhook URLs.
- Template: `workflows/domains/shared/webhook_worker_template.json`

Input expectations:
- Receive normalized Event Schema v1-ish object (at minimum: `type`, `correlation_id`, `payload`).

Best practice:
- Validate payload using `shared/js_snippets/validate_payload.js` and the relevant schema (`contact`, `infra_deploy`, etc.).
- Use the shared error/log workflows where applicable (`error_central_handler`, `log_event`).

---

## GitOps: exporting/importing workflows

### Primary workflow GitOps (most workflows)
- Script: `ops/scripts/n8n_gitops.py`
- Catalog: `workflows/metadata/workflows_catalog.yaml`
- Behavior: upserts workflows by **name** into n8n; exports normalized JSON for stable diffs.

### Webhook-system overlay GitOps (dispatch workflows)
To avoid editing the primary catalog, webhook-system workflows are managed via an overlay:
- Script: `ops/scripts/n8n_gitops_webhooks.py`
- Catalog: `workflows/metadata/webhooks_catalog.yaml`

Commands:
- `python ops/scripts/n8n_gitops_webhooks.py export`
- `python ops/scripts/n8n_gitops_webhooks.py import`
- `python ops/scripts/n8n_gitops_webhooks.py drift-check`

---

## Generator: registering new dispatch events

Use the generator to standardize onboarding:
- Script: `ops/scripts/webhook_dispatch_generator.js`

Example (prints SQL upsert + curl + minimal client helper):

```bash
node ops/scripts/webhook_dispatch_generator.js \
  --event-type contact.created \
  --target-workflow-name "Lead Intake" \
  --target-logical-id lead_intake \
  --payload-schema-type contact \
  --required email,first_name
```

If your dispatcher routes by numeric workflow id, you can include:
- `--cached-n8n-workflow-id <id>`

---

## Testing and troubleshooting

### Quick smoke test (dispatch)
Use the curl snippet printed by the generator to POST to `/webhook/dispatch`.

Expected outcomes:
- **401**: missing/invalid `Authorization: Bearer ...`
- **404**: unknown or inactive `event_type`
- **400**: missing required payload fields (per registry)
- **202**: queued successfully

### Running repo tests deterministically
Some environments have globally-installed pytest plugins that can fail import-time dependencies.
Use the repo runner:
- `ops/scripts/run_pytest.sh`

---

## Notes on compatibility and governance
- Prefer **one public webhook endpoint** (`/webhook/dispatch`) + registry-based routing.
- Keep worker workflows internal; route by event types and schemas.
- Treat Git as source of truth; export from dev n8n before importing into staging/prod.


