<!--
Purpose: Define S3 backup layout, naming conventions, and retention expectations for the Automation Hub
Created/Updated: 2025-12-17 00:00
Agent: GPT-5.2
-->

# S3 Backup Layout (Automation Hub)

## Bucket
- `pratejra-n8n-automation-31415`

## Prefix conventions
All backups are stored under a stable prefix so restores can be automated.

### 1) Git bundles (full history)
- **Producer**: `.github/workflows/backup-to-s3.yaml`
- **Key pattern**:
  - `<repo_name>/git-backups/YYYY-MM-DD/<repo_name>-YYYY-MM-DD_HH-MM-SS.bundle`

### 2) Workflow artifact tarballs (repo exports)
- **Producer**: `.github/workflows/backup-to-s3.yaml`
- **Key pattern**:
  - `<repo_name>/workflows-backups/YYYY-MM-DD/workflows-YYYY-MM-DD_HH-MM-SS.tar.gz`

### 3) Postgres database dumps (n8n DB)
- **Producer**: `ops/scripts/backup_postgres_to_s3.sh` (host scheduled)
- **Key pattern**:
  - `pratejra-automation-hub/postgres-backups/YYYY-MM-DD/pgdump-<db>-YYYY-MM-DD_HH-MM-SS.sql.gz`

### 4) Manifests
- **Producer**: `.github/workflows/backup-to-s3.yaml` (repo-side); host backup can optionally add its own manifest later
- **Key pattern**:
  - `<repo_name>/backup-manifests/YYYY-MM-DD/manifest-YYYY-MM-DD_HH-MM-SS.json`

## Retention
Recommended defaults:
- **90 days** in Standard storage for operational recovery
- Optional archive tier beyond 90 days (Glacier/Deep Archive)

## Security expectations
- Bucket **versioning enabled**
- Encryption at rest enabled (SSE-S3 or SSE-KMS)
- Least-privilege IAM scoped to required prefixes


