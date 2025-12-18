/*
 * Purpose: Render a safe .env file from a key/value map
 * Created: 2025-12-17
 * Author: GPT-5.2
 */

function escapeValue(value) {
  const v = String(value);

  // Keep plain strings when safe.
  if (/^[A-Za-z0-9_./:@+-]*$/.test(v)) return v;

  // Otherwise quote and escape.
  const escaped = v
    .replace(/\\/g, "\\\\")
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "\\r")
    .replace(/\t/g, "\\t")
    .replace(/\"/g, "\\\"");

  return `\"${escaped}\"`;
}

export function renderDotenv({
  generatedBy = "ops/infisical",
  values,
  keysInOrder,
}) {
  const lines = [];

  lines.push(`# Purpose: Generated runtime env for n8n (DO NOT COMMIT)`);
  lines.push(`# Generated: ${new Date().toISOString()}`);
  lines.push(`# Generated-By: ${generatedBy}`);
  lines.push("");

  for (const key of keysInOrder) {
    if (!(key in values)) continue;
    const value = values[key];
    if (value === undefined || value === null) continue;
    lines.push(`${key}=${escapeValue(value)}`);
  }

  lines.push("");
  return lines.join("\n");
}

