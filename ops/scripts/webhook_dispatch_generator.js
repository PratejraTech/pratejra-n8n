/*
 * Purpose: CLI generator for Central Webhook Dispatch (register events, emit SQL upserts, and scaffold worker stubs)
 * Created/Updated: 2025-12-17 00:00
 * Agent: GPT-5.2
 *
 * NodeJS/Bun usage:
 *   node ops/scripts/webhook_dispatch_generator.js --event-type contact.created --target-workflow-name "Lead Intake" --target-logical-id lead_intake --payload-schema-type contact --required email,first_name
 *   bun ops/scripts/webhook_dispatch_generator.js --event-type contact.created --target-workflow-name "Lead Intake" --target-logical-id lead_intake
 */

const fs = require("fs");
const path = require("path");

function die(msg) {
  console.error(`ERROR: ${msg}`);
  process.exit(2);
}

function nowIso() {
  return new Date().toISOString();
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    const isFlag = !next || next.startsWith("--");
    args[key] = isFlag ? true : next;
    if (!isFlag) i++;
  }
  return args;
}

function csvToArray(s) {
  if (!s) return [];
  return String(s)
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

function jsonbArrayLiteral(arr) {
  return `'${JSON.stringify(arr)}'::jsonb`;
}

function escapeSqlString(s) {
  return String(s).replace(/'/g, "''");
}

function normalizeWorkflowFileName(eventType) {
  return String(eventType)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80);
}

function buildUpsertSql({
  eventType,
  targetWorkflowLogicalId,
  targetWorkflowName,
  cachedN8nWorkflowId,
  description,
  payloadSchemaType,
  requiredFields,
  isActive,
}) {
  const descSql = description ? `'${escapeSqlString(description)}'` : "NULL";
  const schemaSql = payloadSchemaType ? `'${escapeSqlString(payloadSchemaType)}'` : "NULL";
  const activeSql = isActive ? "true" : "false";
  const cachedIdSql = cachedN8nWorkflowId ? `'${escapeSqlString(cachedN8nWorkflowId)}'` : "NULL";

  return [
    "-- Upsert webhook_registry entry",
    "INSERT INTO public.webhook_registry (",
    "  event_type,",
    "  target_workflow_logical_id,",
    "  target_workflow_name,",
    "  cached_n8n_workflow_id,",
    "  description,",
    "  is_active,",
    "  payload_schema_type,",
    "  required_payload_fields",
    ") VALUES (",
    `  '${escapeSqlString(eventType)}',`,
    `  '${escapeSqlString(targetWorkflowLogicalId)}',`,
    `  '${escapeSqlString(targetWorkflowName)}',`,
    `  ${cachedIdSql},`,
    `  ${descSql},`,
    `  ${activeSql},`,
    `  ${schemaSql},`,
    `  ${jsonbArrayLiteral(requiredFields)}`,
    ")",
    "ON CONFLICT (event_type) DO UPDATE SET",
    "  target_workflow_logical_id = EXCLUDED.target_workflow_logical_id,",
    "  target_workflow_name = EXCLUDED.target_workflow_name,",
    "  cached_n8n_workflow_id = EXCLUDED.cached_n8n_workflow_id,",
    "  description = EXCLUDED.description,",
    "  is_active = EXCLUDED.is_active,",
    "  payload_schema_type = EXCLUDED.payload_schema_type,",
    "  required_payload_fields = EXCLUDED.required_payload_fields,",
    "  updated_at = NOW();",
  ].join("\n");
}

function buildCurlExample({ baseUrl, apiKey, eventType, payloadExample }) {
  const body = {
    event_type: eventType,
    data: payloadExample || { example: true },
    metadata: {
      source: "external_client",
      env: "prod",
      timestamp: nowIso(),
    },
  };

  return [
    "# Example: send simplified shape (hybrid contract)",
    "curl -X POST \\",
    `  '${baseUrl.replace(/\/+$/, "")}/webhook/dispatch' \\`,
    "  -H 'Content-Type: application/json' \\",
    `  -H 'Authorization: Bearer ${apiKey || "REPLACE_ME"}' \\`,
    `  -d '${JSON.stringify(body)}'`,
  ].join("\n");
}

function buildClientSdkSnippet({ baseUrl }) {
  return [
    "// Minimal client helper (Node/Browser)",
    `const DISPATCH_URL = "${baseUrl.replace(/\/+$/, "")}/webhook/dispatch";`,
    "",
    "export async function sendDispatchEvent({ eventType, data, metadata, apiKey }) {",
    "  const res = await fetch(DISPATCH_URL, {",
    "    method: 'POST',",
    "    headers: {",
    "      'Content-Type': 'application/json',",
    "      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),",
    "    },",
    "    body: JSON.stringify({",
    "      event_type: eventType,",
    "      data,",
    "      metadata,",
    "    }),",
    "  });",
    "  if (!res.ok) throw new Error(`dispatch failed: ${res.status}`);",
    "  return await res.json().catch(() => ({}));",
    "}",
  ].join("\n");
}

function scaffoldWorkerStub({ repoRoot, domain, workerName, outPath, force }) {
  const filePath = outPath
    ? path.resolve(repoRoot, outPath)
    : path.resolve(repoRoot, "workflows", "domains", domain, `${workerName}.json`);

  if (fs.existsSync(filePath) && !force) {
    die(`Refusing to overwrite existing file: ${filePath} (use --force to overwrite)`);
  }

  const stub = {
    _metadata: {
      purpose: "Worker workflow stub for Central Webhook Dispatch (replace with n8n-exported workflow JSON)",
      created: "2025-12-17 00:00",
      agent: "GPT-5.2",
      id: workerName,
      version: "1.0.0",
      domain,
      description: "Worker stub generated by webhook_dispatch_generator.js",
      steps: [
        "Start node receives normalized event",
        "Implement domain logic",
        "Log event + error handling",
      ],
    },
    name: `Worker: ${workerName}`,
    nodes: [
      {
        parameters: {},
        id: "00000000-0000-0000-0000-000000000000",
        name: "Start",
        type: "n8n-nodes-base.start",
        typeVersion: 1,
        position: [-520, 0],
      },
    ],
    connections: {},
    settings: {},
    staticData: null,
  };

  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(stub, null, 2) + "\n", "utf-8");

  return filePath;
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  const eventType = String(args["event-type"] || "").trim();
  const targetWorkflowName = String(args["target-workflow-name"] || "").trim();
  const targetWorkflowLogicalId = String(args["target-logical-id"] || "").trim();

  if (!eventType) die("--event-type is required (e.g., contact.created)");
  if (!targetWorkflowName) die("--target-workflow-name is required (matches n8n workflow name)");
  if (!targetWorkflowLogicalId) die("--target-logical-id is required (e.g., lead_intake)");

  const description = args["description"] ? String(args["description"]) : "";
  const payloadSchemaType = args["payload-schema-type"] ? String(args["payload-schema-type"]) : "";
  const requiredFields = csvToArray(args["required"]);
  const isActive = args["inactive"] ? false : true;
  const cachedN8nWorkflowId = args["cached-n8n-workflow-id"] ? String(args["cached-n8n-workflow-id"]).trim() : "";

  const baseUrl = String(args["base-url"] || "https://n8n.automation-hub.example.com").trim();
  const apiKey = String(args["api-key"] || "").trim();

  const sql = buildUpsertSql({
    eventType,
    targetWorkflowLogicalId,
    targetWorkflowName,
    cachedN8nWorkflowId,
    description,
    payloadSchemaType,
    requiredFields,
    isActive,
  });

  const curl = buildCurlExample({
    baseUrl,
    apiKey,
    eventType,
    payloadExample: requiredFields.length ? Object.fromEntries(requiredFields.map((k) => [k, "REPLACE_ME"])) : { example: true },
  });

  const sdk = buildClientSdkSnippet({ baseUrl });

  console.log(["# Central Webhook Dispatch: Registration Output", "", sql, "", curl, "", sdk, ""].join("\n"));

  if (args["scaffold-worker"]) {
    const repoRoot = path.resolve(__dirname, "..", "..");
    const domain = String(args["domain"] || "shared").trim();
    const outPath = args["worker-file"] ? String(args["worker-file"]).trim() : "";
    const force = Boolean(args["force"]);
    const workerName = args["worker-name"] ? String(args["worker-name"]).trim() : normalizeWorkflowFileName(eventType);
    const written = scaffoldWorkerStub({ repoRoot, domain, workerName, outPath, force });
    console.error(`scaffolded worker stub: ${written}`);
  }
}

if (require.main === module) {
  main();
}


