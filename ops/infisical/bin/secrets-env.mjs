/*
 * Purpose: CLI to generate docker/n8n.env.generated from Infisical or dotenv-vault
 * Created: 2025-12-17
 * Author: GPT-5.2
 */

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { fetchInfisicalSecrets } from "../src/infisical.js";
import { loadDotenvVault } from "../src/dotenvVault.js";
import { renderDotenv } from "../src/renderDotenv.js";
import { validateValues } from "../src/validate.js";

function parseArgs(argv) {
  const args = {
    provider: "auto",
    topology: undefined,
    output: undefined,
    map: undefined,
    path: "/",
    dryRun: false,
    help: false,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--help" || a === "-h") args.help = true;
    else if (a === "--dry-run") args.dryRun = true;
    else if (a === "--provider") args.provider = argv[++i];
    else if (a === "--topology") args.topology = argv[++i];
    else if (a === "--output") args.output = argv[++i];
    else if (a === "--map") args.map = argv[++i];
    else if (a === "--path") args.path = argv[++i];
    else throw new Error(`Unknown argument: ${a}`);
  }

  return args;
}

function printHelp({ defaultOutput, defaultMap }) {
  // Intentionally no secret output.
  // eslint-disable-next-line no-console
  console.log(`\nGenerate docker env for n8n\n\nUsage:\n  node ops/infisical/bin/secrets-env.mjs [options]\n\nOptions:\n  --provider <auto|infisical|dotenv-vault>  Provider (default: auto)\n  --topology <postgres|sqlite>             Required key set (default from secret-map)\n  --path </>                               Infisical secret path/folder (default: /)\n  --map <path>                             Secret map JSON (default: ${defaultMap})\n  --output <path>                          Output .env path (default: ${defaultOutput})\n  --dry-run                                Validate only; do not write file\n  -h, --help                               Show help\n`);
}

function resolveRepoRoot() {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  return path.resolve(__dirname, "../../..");
}

async function readSecretMap(mapPath) {
  const raw = await fs.readFile(mapPath, "utf8");
  return JSON.parse(raw);
}

function pickValuesFromSource({ secretMap, sourceSecrets }) {
  const vars = secretMap?.variables ?? {};
  const values = {};

  for (const [envVar, spec] of Object.entries(vars)) {
    const infisicalKey = spec?.infisicalKey || envVar;
    const v = sourceSecrets[infisicalKey];

    if (v !== undefined && v !== null && String(v).length > 0) {
      values[envVar] = String(v);
    } else if (spec?.default !== undefined) {
      values[envVar] = String(spec.default);
    }
  }

  return values;
}

async function main() {
  const repoRoot = resolveRepoRoot();
  const defaultOutput = path.join(repoRoot, "docker", "n8n.env.generated");
  const defaultMap = path.join(repoRoot, "ops", "infisical", "secret-map.json");

  const args = parseArgs(process.argv);
  if (args.help) {
    printHelp({ defaultOutput, defaultMap });
    return;
  }

  const mapPath = path.resolve(repoRoot, args.map || defaultMap);
  const outPath = path.resolve(repoRoot, args.output || defaultOutput);

  const secretMap = await readSecretMap(mapPath);
  const topology = args.topology || secretMap?.defaultTopology || "postgres";

  const provider = args.provider === "auto"
    ? (process.env.INFISICAL_CLIENT_ID && process.env.INFISICAL_CLIENT_SECRET ? "infisical" : "dotenv-vault")
    : args.provider;

  let sourceSecrets = {};

  if (provider === "infisical") {
    sourceSecrets = await fetchInfisicalSecrets({
      siteUrl: process.env.INFISICAL_SITE_URL,
      clientId: process.env.INFISICAL_CLIENT_ID,
      clientSecret: process.env.INFISICAL_CLIENT_SECRET,
      projectId: process.env.INFISICAL_PROJECT_ID,
      environment: process.env.INFISICAL_ENV,
      path: args.path || "/",
    });
  } else if (provider === "dotenv-vault") {
    loadDotenvVault({ repoRoot });
    sourceSecrets = { ...process.env };
  } else {
    throw new Error(`Unsupported provider: ${provider}`);
  }

  const values = pickValuesFromSource({ secretMap, sourceSecrets });

  const validation = validateValues({
    secretMap,
    topology,
    values,
  });

  if (!validation.ok) {
    throw new Error(`Missing required env vars for topology '${topology}': ${validation.missing.join(", ")}`);
  }

  const keysInOrder = Object.keys(secretMap?.variables ?? {});
  const rendered = renderDotenv({
    generatedBy: `ops/infisical (provider=${provider}, topology=${topology})`,
    values,
    keysInOrder,
  });

  if (args.dryRun) {
    // eslint-disable-next-line no-console
    console.log(`OK (dry-run). Would write: ${outPath}`);
    // eslint-disable-next-line no-console
    console.log(`Keys: ${keysInOrder.join(", ")}`);
    return;
  }

  await fs.mkdir(path.dirname(outPath), { recursive: true });
  await fs.writeFile(outPath, rendered, { encoding: "utf8" });

  // Best-effort restrictive permissions
  try {
    await fs.chmod(outPath, 0o600);
  } catch {
    // ignore (e.g., on systems without chmod semantics)
  }

  // eslint-disable-next-line no-console
  console.log(`Wrote: ${outPath}`);
}

await main();

