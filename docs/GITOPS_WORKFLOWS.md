<!--
Purpose: Operator guide for GitOps workflow export/import and drift detection using ops/scripts/n8n_gitops.py
Created/Updated: 2025-12-17 00:00
Agent: GPT-5.2
-->

# GitOps: Export/Import Workflows + Drift Detection

## Overview
This repo treats **Git as the source of truth** for n8n workflows. The expected lifecycle is:
- Edit workflows in a **dev** n8n instance
- **Export** to the repo (normalized JSON for stable diffs)
- PR/CI validation
- **Import** into the target n8n instance (staging/prod)
- Continuous **drift detection**

This is implemented by:
- `ops/scripts/n8n_gitops.py` (export, import, drift-check)
- `workflows/metadata/workflows_catalog.yaml` (maps logical IDs to file paths and workflow names)

## Prerequisites
- n8n reachable at `N8N_BASE_URL` (default `http://localhost:5678`)
- `N8N_API_KEY` set (n8n API key)

## Environment variables
- `N8N_BASE_URL`: e.g. `http://localhost:5678`
- `N8N_API_KEY`: n8n API key (required)

## Export from n8n (dev → git)
Exports workflows found in `workflows/metadata/workflows_catalog.yaml` by matching **workflow name** in n8n, then writes normalized JSON to each `file_path`.

```bash
export N8N_BASE_URL="http://localhost:5678"
export N8N_API_KEY="..."
python ops/scripts/n8n_gitops.py export
```

Export a single workflow by logical ID:

```bash
python ops/scripts/n8n_gitops.py --only lead_intake export
```

## Import into n8n (git → target n8n)
Imports local workflow JSON files and **upserts by name**:
- If a workflow with the same name exists: `PUT /api/v1/workflows/{id}`
- Otherwise: `POST /api/v1/workflows`

```bash
export N8N_BASE_URL="http://localhost:5678"
export N8N_API_KEY="..."
python ops/scripts/n8n_gitops.py import
```

## Drift detection (target n8n ↔ git)
Compares normalized remote workflow JSON with normalized local JSON.
Exit code is non-zero on drift.

```bash
export N8N_BASE_URL="http://localhost:5678"
export N8N_API_KEY="..."
python ops/scripts/n8n_gitops.py drift-check
```

## Deployment notes
- **Keep `N8N_ENCRYPTION_KEY` stable** across restarts/restores, or encrypted credentials will break.
- For production, do not expose n8n publicly without network controls + auth.


