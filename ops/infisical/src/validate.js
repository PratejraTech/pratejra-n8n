/*
 * Purpose: Validate required env vars exist before writing generated env files
 * Created: 2025-12-17
 * Author: GPT-5.2
 */

function normalizeBooleanString(v) {
  if (v === undefined || v === null) return undefined;
  return String(v).trim().toLowerCase();
}

export function computeRequiredKeys({ secretMap, topology }) {
  const vars = secretMap?.variables ?? {};
  const required = new Set();

  for (const [envVar, spec] of Object.entries(vars)) {
    if (spec?.required === true) required.add(envVar);

    const topoReq = spec?.requiredForTopologies;
    if (Array.isArray(topoReq) && topoReq.includes(topology)) required.add(envVar);
  }

  return [...required];
}

export function validateValues({ secretMap, topology, values }) {
  const vars = secretMap?.variables ?? {};
  const missing = [];

  // Static requirements
  for (const key of computeRequiredKeys({ secretMap, topology })) {
    if (!values[key]) missing.push(key);
  }

  // Conditional requirements
  for (const [envVar, spec] of Object.entries(vars)) {
    const cond = spec?.requiredIf;
    if (!cond) continue;

    const other = cond.var;
    const equals = normalizeBooleanString(cond.equals);
    const actual = normalizeBooleanString(values[other]);

    if (equals !== undefined && actual === equals) {
      if (!values[envVar]) missing.push(envVar);
    }
  }

  return {
    ok: missing.length === 0,
    missing: [...new Set(missing)].sort(),
  };
}

