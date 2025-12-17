<!--
Purpose: Disaster recovery runbook for restoring a Postgres-backed n8n instance from S3 + git artifacts
Created/Updated: 2025-12-17 00:00
Agent: GPT-5.2
-->

# Restore Runbook: n8n + Postgres (Single-host)

## Objective
Restore a functional n8n instance (workflows + credentials) on a clean host using:
- `s3://pratejra-n8n-automation-31415/` backups
- This repository (or a git bundle from S3)

## Critical invariants
- **`N8N_ENCRYPTION_KEY` must be identical** to the original instance.
If this key changes, encrypted credentials in the database cannot be decrypted.

## Inputs
- **Postgres dump**: `pratejra-automation-hub/postgres-backups/YYYY-MM-DD/pgdump-<db>-<timestamp>.sql.gz`
- **Repo workflow artifacts** (optional if you restore from git): `<repo>/workflows-backups/YYYY-MM-DD/workflows-<timestamp>.tar.gz`
- **Git bundle** (optional): `<repo>/git-backups/YYYY-MM-DD/<repo>-<timestamp>.bundle`

## Prerequisites
- Docker + Docker Compose installed
- AWS CLI configured with access to `pratejra-n8n-automation-31415`
- The original `N8N_ENCRYPTION_KEY` available securely (Secrets Manager/Vault/offline escrow)

## Procedure

### 1) Restore the repository (optional if repo already present)
Option A: use the existing repo checkout.
Option B: restore from a git bundle:

```bash
aws s3 cp "s3://pratejra-n8n-automation-31415/<repo>/git-backups/YYYY-MM-DD/<repo>-<ts>.bundle" ./repo.bundle
git clone ./repo.bundle pratejra-automation-hub
cd pratejra-automation-hub
```

### 2) Bring up Postgres (empty)
Use the Postgres-backed compose topology:

```bash
cp docker/n8n.postgres.env.example docker/n8n.postgres.env
```

Edit `docker/n8n.postgres.env` and set:
- `POSTGRES_PASSWORD`
- `N8N_ENCRYPTION_KEY` (the original)

Start Postgres only:

```bash
docker compose -f docker/docker-compose.n8n.postgres.yaml --env-file docker/n8n.postgres.env up -d postgres
```

### 3) Restore the database dump
Download the dump and restore into the running Postgres container.

```bash
aws s3 cp "s3://pratejra-n8n-automation-31415/pratejra-automation-hub/postgres-backups/YYYY-MM-DD/pgdump-n8n-<ts>.sql.gz" ./pgdump.sql.gz
gunzip -c ./pgdump.sql.gz | docker exec -i n8n-postgres psql -U n8n -d n8n
```

### 4) Start n8n

```bash
docker compose -f docker/docker-compose.n8n.postgres.yaml --env-file docker/n8n.postgres.env up -d n8n
```

### 5) Verify health

```bash
curl -fsS http://localhost:5678/healthz
```

### 6) Verify workflows and credentials
- Log into n8n UI, confirm workflows exist.\n
- Log into n8n UI, confirm workflows exist.
- Confirm credentials decrypt correctly (this validates `N8N_ENCRYPTION_KEY`).

### 7) Optional: re-import workflows from git
If you restore only DB or only repo artifacts, use the GitOps import tooling:

```bash
export N8N_BASE_URL="http://localhost:5678"
export N8N_API_KEY="..."
python ops/scripts/n8n_gitops.py import
```

## Post-restore checklist
- [ ] Health endpoint returns 200
- [ ] Workflows visible
- [ ] Credentials usable
- [ ] Drift check passes: `python ops/scripts/n8n_gitops.py drift-check`
- [ ] Backups scheduled (repo backup action + pg_dump job)


