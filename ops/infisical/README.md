<!--
Purpose: Developer guide for generating n8n env files from Infisical or dotenv-vault
Created: 2025-12-17
Author: GPT-5.2
-->

# Infisical Secrets Bootstrap (Node)

This package generates `docker/n8n.env.generated` for the n8n Docker runtime.

## Providers

- **Production (Infisical)**: uses Universal Auth (Machine Identity) via `@infisical/sdk`.
- **Local (dotenv-vault)**: use `dotenv-vault` (via `npx dotenv-vault ...`) to create/manage `.env.vault`, then set `DOTENV_KEY` so `dotenv` can decrypt it at runtime.

## Quickstart

### 1) Install dependencies

```bash
npm --prefix ops/infisical install
```

### 2) Generate env file from Infisical (recommended for prod bootstrap)

```bash
INFISICAL_CLIENT_ID=... \
INFISICAL_CLIENT_SECRET=... \
INFISICAL_PROJECT_ID=... \
INFISICAL_ENV=prod \
node ops/infisical/bin/secrets-env.mjs --provider infisical
```

### 3) Generate env file from dotenv-vault (recommended for local)

```bash
# DOTENV_KEY should point at your .env.vault (dotenv-vault keys <env>)
export DOTENV_KEY='dotenv://:...@dotenv.org/vault/.env.vault?environment=development'
node ops/infisical/bin/secrets-env.mjs --provider dotenv-vault
```

## Output

- Default output path: `docker/n8n.env.generated`
- Customize: `--output docker/n8n.env.generated`

## Secret key mapping

Edit `ops/infisical/secret-map.json`.

- By default, **Infisical secret keys match the env var names** (e.g. `N8N_ENCRYPTION_KEY`).
- Defaults are only used when a value is missing and the var is optional.

## Safety

- The CLI never prints secret values.
- Use `--dry-run` to validate without writing a file.


