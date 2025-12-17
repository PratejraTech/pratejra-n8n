--
-- Purpose: Create the webhook_registry table used by the Central Webhook Dispatcher (/webhook/dispatch)
-- Created/Updated: 2025-12-17 00:00
-- Agent: GPT-5.2
--
-- Notes:
-- - Intended to be applied to the same Postgres database used by n8n (DB_TYPE=postgresdb).
-- - This registry is the source of truth for routing events (event_type) to worker workflows.
-- - Uses workflow NAME (stable under GitOps upsert-by-name) rather than n8n numeric IDs.
--

BEGIN;

CREATE TABLE IF NOT EXISTS public.webhook_registry (
  id SERIAL PRIMARY KEY,

  -- Event type identifier; should match shared/schemas/event.schema.json "type" pattern.
  event_type VARCHAR(100) UNIQUE NOT NULL,

  -- Stable identities for routing.
  target_workflow_logical_id VARCHAR(100) NOT NULL,
  target_workflow_name VARCHAR(255) NOT NULL,

  -- Optional cache for operational convenience (not relied on for correctness).
  cached_n8n_workflow_id VARCHAR(50),

  description TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,

  -- Validation policy.
  payload_schema_type VARCHAR(50),
  required_payload_fields JSONB NOT NULL DEFAULT '[]'::jsonb,

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Basic sanity constraints (safe to re-run).
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'webhook_registry_required_payload_fields_is_array'
  ) THEN
    ALTER TABLE public.webhook_registry
      ADD CONSTRAINT webhook_registry_required_payload_fields_is_array
      CHECK (jsonb_typeof(required_payload_fields) = 'array');
  END IF;
END $$;

-- Helpful indexes.
CREATE INDEX IF NOT EXISTS idx_webhook_registry_active_event
  ON public.webhook_registry (event_type)
  WHERE is_active = true;

-- Auto-update updated_at.
CREATE OR REPLACE FUNCTION public.set_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_webhook_registry_set_updated_at ON public.webhook_registry;
CREATE TRIGGER trg_webhook_registry_set_updated_at
BEFORE UPDATE ON public.webhook_registry
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at_timestamp();

COMMIT;


