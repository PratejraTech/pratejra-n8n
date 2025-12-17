<!--
Purpose: Central Webhook Dispatch architecture, contract, registry, and onboarding guide
Created/Updated: 2025-12-17 00:00
Agent: GPT-5.2
-->

## Central Webhook Dispatch

### Why this exists
If every workflow exposes its own random webhook URL, you get a fragile system that is hard to rotate, audit, and deprecate. This repo standardizes ingress by using **one dispatch endpoint** and a **DB registry** for routing.

### Single ingress endpoint
- **Endpoint**: `POST /webhook/dispatch`
- **Goal**: route requests based on **event type**, not URL.

### Supported inbound contract (hybrid)
The dispatcher accepts either:

1) **Event Schema v1** (preferred)
- Matches `shared/schemas/event.schema.json`.
- Required keys: `id`, `type`, `source`, `env`, `timestamp`, `payload`.

2) **Simplified dispatch shape** (supported for clients)

```json
{
  "event_type": "contact.created",
  "data": { "email": "user@example.com" },
  "metadata": { "source": "landing_page_v2", "env": "prod", "timestamp": "2025-12-17T00:00:00Z" }
}
```

The dispatcher normalizes the simplified shape into Event Schema v1 before validation/routing.

### Webhook registry (Postgres “phonebook”)
The dispatcher consults `public.webhook_registry` to decide whether an event is valid and where it should go.

- **Create table**: run `ops/scripts/webhook_registry.sql` against the n8n Postgres database.
- **Key fields**:
  - `event_type`: routes based on `event.type`
  - `target_workflow_name`: stable target identifier (fits GitOps upsert-by-name)
  - `required_payload_fields`: JSONB array of dot-paths enforced against `event.payload`

### Lifecycle management
- **Enable**: insert/update `webhook_registry` row with `is_active=true`.
- **Disable (deprecate)**: set `is_active=false` (dispatcher should return 404 for unknown/inactive).
- **Do not delete** worker workflows until clients have fully migrated.

### GitOps management for dispatch workflows (overlay)
Webhook-system workflows are managed via an overlay catalog to avoid editing the main catalog:
- **Catalog**: `workflows/metadata/webhooks_catalog.yaml`
- **GitOps script**: `ops/scripts/n8n_gitops_webhooks.py`

Commands (dev → git, git → target):
- `python ops/scripts/n8n_gitops_webhooks.py export`
- `python ops/scripts/n8n_gitops_webhooks.py import`
- `python ops/scripts/n8n_gitops_webhooks.py drift-check`

### Onboarding a new event (recommended path)
1. Build/confirm the worker workflow in dev n8n (name it clearly).
2. Register the event in Postgres using the generator:
   - `node ops/scripts/webhook_dispatch_generator.js --event-type contact.created --target-workflow-name "Lead Intake" --target-logical-id lead_intake --payload-schema-type contact --required email`
3. Test with the generated curl example.
4. Export the updated dispatch workflow if you changed it in dev.

### Security notes
- Prefer `Authorization: Bearer <token>` for callers.
- Keep the dispatcher on a private network / behind an authenticated gateway.
- Add rate limiting at the edge (LB/WAF) if exposed.

