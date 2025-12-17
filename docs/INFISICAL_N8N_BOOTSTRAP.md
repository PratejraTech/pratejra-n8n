<!--
Purpose: Runbook for bootstrapping n8n Docker runtime using Infisical + Node secrets generator
Created: 2025-12-17
Author: GPT-5.2
-->

# n8n Bootstrap (Infisical)

## What this does

- Pulls secrets from **Infisical** (prod) or **dotenv-vault** (local)
- Writes `docker/n8n.env.generated`
- Starts n8n using `docker/docker-compose.n8n.infisical.yaml`

## 1) One-time setup (Infisical)

1. Create an Infisical **Project** and **Environment** (e.g., `prod`).
2. Create a **Machine Identity** with Universal Auth enabled.
3. Create secrets matching `ops/infisical/secret-map.json` (recommended: same names as env vars).

## 2) Install bootstrap tool dependencies

```bash
npm --prefix ops/infisical install
```

## 3) Generate the runtime env file (production)

```bash
INFISICAL_CLIENT_ID=... \
INFISICAL_CLIENT_SECRET=... \
INFISICAL_PROJECT_ID=... \
INFISICAL_ENV=prod \
node ops/infisical/bin/secrets-env.mjs --provider infisical
```

To validate without writing:

```bash
node ops/infisical/bin/secrets-env.mjs --provider infisical --dry-run
```

## 4) Start n8n using the Infisical compose file

```bash
docker compose -f docker/docker-compose.n8n.infisical.yaml up -d
```

Verify:

- `GET http://localhost:5678/healthz` returns `200`

## 5) Local development (dotenv-vault)

1. Create/manage `.env.vault` using dotenv-vault tooling (example):

```bash
npx dotenv-vault@latest new
npx dotenv-vault@latest build
npx dotenv-vault@latest keys development
```

2. Export your `DOTENV_KEY`, then generate env:

```bash
export DOTENV_KEY='dotenv://:...@dotenv.org/vault/.env.vault?environment=development'
node ops/infisical/bin/secrets-env.mjs --provider dotenv-vault
```

## Notes

- `docker/n8n.env.generated.example` shows the expected shape (no secrets).
- Do not rotate `N8N_ENCRYPTION_KEY` after n8n has stored credentials.
