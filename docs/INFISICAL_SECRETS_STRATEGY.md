<!--
Purpose: Infisical-first secrets management strategy for n8n runtime bootstrap
Created: 2025-12-17
Author: GPT-5.2
-->

# Infisical Secrets Strategy (Infisical-first)

## Scope

This strategy defines how **runtime secrets** are sourced for the Automation Hub’s n8n deployments.

- **Primary (new)**: Infisical (Machine Identity / Universal Auth)
- **Legacy (superseded)**: AWS Secrets Manager approach described in `docs/SECRETS_STRATEGY.md`

## Production model

### Authentication (OAuth2-style via Universal Auth)

Use an Infisical **Machine Identity** per environment with least privilege:

- `INFISICAL_CLIENT_ID`
- `INFISICAL_CLIENT_SECRET`
- `INFISICAL_PROJECT_ID`
- `INFISICAL_ENV` (e.g., `dev`, `staging`, `prod`)
- Optional: `INFISICAL_SITE_URL`

### Secret keys

Prefer secret keys that **match env var names** exactly.

Examples (n8n bootstrap):
- `N8N_ENCRYPTION_KEY`
- `WEBHOOK_URL`
- `POSTGRES_PASSWORD`

The authoritative mapping is in `ops/infisical/secret-map.json`.

### Retrieval pattern

Secrets are retrieved **once during bootstrap** and written into a generated env file:

- Output: `docker/n8n.env.generated`
- Generation tool: `ops/infisical/bin/secrets-env.mjs`

This reduces runtime coupling to the secrets provider and avoids leaking Infisical credentials into the runtime container.

## Local development model

Use **dotenv-vault** to manage an encrypted `.env.vault` locally.

- `.env.vault` is created/managed with `dotenv-vault` tooling
- `DOTENV_KEY` is set locally
- The bootstrap CLI uses `dotenv` to decrypt/load values and generate `docker/n8n.env.generated`

## Security requirements

- **Never commit** `docker/n8n.env.generated`.
- **Never log** secret values (bootstrap prints keys only).
- **Least privilege**: Machine Identity scoped to the minimal project/env/path.
- **Rotation**:
  - Rotate `INFISICAL_CLIENT_SECRET` regularly
  - Treat `N8N_ENCRYPTION_KEY` as immutable per environment (rotating it breaks stored credentials)

## Migration notes (AWS → Infisical)

- Create Infisical secrets for all keys referenced by `ops/infisical/secret-map.json`.
- Run bootstrap to generate `docker/n8n.env.generated`.
- Start n8n using the Infisical compose file: `docker/docker-compose.n8n.infisical.yaml`.
- Keep AWS-based workflows/scripts as legacy until fully retired.

## References

- Infisical Universal Auth (Machine Identity): `https://infisical.com/docs/documentation/platform/identities/universal-auth`
- Infisical Node SDK: `https://infisical.com/docs/sdks/languages/node`

