/*
 * Purpose: Normalize and validate Central Webhook Dispatch requests against DB-driven registry rules (NodeJS/Bun)
 * Created/Updated: 2025-12-17 00:00
 * Agent: GPT-5.2
 *
 * This snippet is designed to be pasted/used in an n8n Code node within the Webhook Dispatch workflow.
 * It supports the repo's hybrid dispatch contract:
 * - Full Event Schema v1 body (id,type,source,env,timestamp,payload,...)
 * - Simplified shape (event_type/event + data/payload + metadata) which is normalized into Event Schema v1
 *
 * It then enforces webhook_registry.required_payload_fields (supports dot-paths).
 */

const EVENT_TYPE_RE = /^[a-z0-9]+(\.[a-z0-9]+)+$/;

function nowIso() {
  return new Date().toISOString();
}

function makeCorrelationId() {
  return `corr-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getPath(obj, path) {
  return String(path)
    .split(".")
    .reduce((acc, key) => (acc && typeof acc === "object" ? acc[key] : undefined), obj);
}

function looksLikeEventSchemaV1(body) {
  return (
    body &&
    typeof body === "object" &&
    typeof body.type === "string" &&
    typeof body.source === "string" &&
    typeof body.env === "string" &&
    typeof body.timestamp === "string" &&
    body.payload &&
    typeof body.payload === "object"
  );
}

/**
 * Normalize inbound body/query into the repo's Event Schema v1 shape.
 *
 * @param {object} input - { body, query }
 * @returns {object} event
 */
function normalizeToEventV1(input) {
  const body = (input && input.body) || {};
  const query = (input && input.query) || {};

  if (looksLikeEventSchemaV1(body)) {
    return { ...body };
  }

  const type = String(body.event_type ?? query.event_type ?? body.event ?? query.event ?? "").trim();
  const payload = body.payload ?? body.data ?? {};
  const meta = body.meta ?? body.metadata ?? undefined;

  // crypto.randomUUID is available in modern Node, but not guaranteed in all runtimes.
  const id = String(body.id ?? (globalThis.crypto?.randomUUID?.() || `${Date.now()}`));

  return {
    id,
    type,
    source: String(body.source ?? meta?.source ?? "external"),
    env: String(body.env ?? meta?.env ?? "prod"),
    timestamp: String(body.timestamp ?? meta?.timestamp ?? nowIso()),
    correlation_id: String(body.correlation_id ?? meta?.correlation_id ?? makeCorrelationId()),
    payload: typeof payload === "object" && payload !== null ? payload : {},
    meta,
  };
}

/**
 * Validate an Event Schema v1 object against a webhook_registry row.
 *
 * @param {object} event - normalized event
 * @param {object|null} registryRow - row from webhook_registry (or null)
 * @returns {{event: object, registry: object}}
 */
function validateAgainstRegistry(event, registryRow) {
  if (!EVENT_TYPE_RE.test(String(event.type || ""))) {
    const err = new Error(`Invalid event.type: ${event.type}`);
    err.statusCode = 400;
    throw err;
  }

  if (!registryRow || registryRow.is_active !== true) {
    const err = new Error(`Unknown or inactive event type: ${event.type}`);
    err.statusCode = 404;
    throw err;
  }

  const required = Array.isArray(registryRow.required_payload_fields)
    ? registryRow.required_payload_fields
    : typeof registryRow.required_payload_fields === "string"
      ? JSON.parse(registryRow.required_payload_fields)
      : [];

  const missing = [];
  for (const fieldPath of required) {
    const v = getPath(event.payload, fieldPath);
    if (v === undefined || v === null || v === "") missing.push(String(fieldPath));
  }

  if (missing.length > 0) {
    const err = new Error(`Missing required payload fields: ${missing.join(", ")}`);
    err.statusCode = 400;
    throw err;
  }

  return { event, registry: registryRow };
}

module.exports = {
  normalizeToEventV1,
  validateAgainstRegistry,
  getPath,
};


