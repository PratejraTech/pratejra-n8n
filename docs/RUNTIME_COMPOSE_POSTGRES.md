<!--
Purpose: Runbook for operating the self-contained single-host n8n + Postgres Docker Compose runtime
Created/Updated: 2025-12-17 00:00
Agent: GPT-5.2
-->

# Single-host n8n + Postgres (Docker Compose)

## Overview
This repository supports a **self-contained** runtime for n8n backed by **Postgres** using Docker Compose.

## Files
- `docker/docker-compose.n8n.postgres.yaml`: n8n + Postgres topology with health checks
- `docker/n8n.postgres.env.example`: example environment file (copy before use)

## Quick start
1. Copy the env template:

```bash
cp docker/n8n.postgres.env.example docker/n8n.postgres.env
```

2. Edit `docker/n8n.postgres.env` and set **at minimum**:
- `N8N_ENCRYPTION_KEY` (must be stable across restarts/restores)
- `POSTGRES_PASSWORD`

3. Start services:

```bash
docker compose -f docker/docker-compose.n8n.postgres.yaml up -d
```

4. Verify health:

```bash
curl -fsS http://localhost:5678/healthz
```

## Deployment notes
- Default binding is **localhost-only**. To expose externally, set `N8N_BIND_ADDR=0.0.0.0` and protect the UI with auth + network controls.



## Additional Resources

For comprehensive PostgreSQL setup including production deployment, performance tuning, security, and troubleshooting, see:
- **Full Guide:** `docs/POSTGRES_SETUP.md`

