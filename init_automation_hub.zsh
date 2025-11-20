#!/usr/bin/env zsh
set -euo pipefail

# Usage:
#   ./init_automation_platform.zsh          # creates ./automation-platform
#   ./init_automation_platform.zsh my-dir   # creates ./my-dir instead
#
# This script is idempotent: re-running it won't destroy existing files.

BASE_DIR="."

echo "Initializing automation platform structure in: $BASE_DIR"

# -------------------------
# Create directories
# -------------------------
mkdir -p "$BASE_DIR"/.github/workflows

mkdir -p "$BASE_DIR"/workflows/domains/crm
mkdir -p "$BASE_DIR"/workflows/domains/infra
mkdir -p "$BASE_DIR"/workflows/domains/meta
mkdir -p "$BASE_DIR"/workflows/domains/shared

mkdir -p "$BASE_DIR"/workflows/packs
mkdir -p "$BASE_DIR"/workflows/metadata

mkdir -p "$BASE_DIR"/shared/schemas
mkdir -p "$BASE_DIR"/shared/js_snippets

mkdir -p "$BASE_DIR"/ops/envs
mkdir -p "$BASE_DIR"/ops/scripts
mkdir -p "$BASE_DIR"/ops/backups

mkdir -p "$BASE_DIR"/docs

# -------------------------
# Top-level files
# -------------------------
touch "$BASE_DIR/README.md"

# -------------------------
# .github workflows
# -------------------------
touch "$BASE_DIR/.github/workflows/validate-workflows.yml"
touch "$BASE_DIR/.github/workflows/deploy-workflows.yml"

# -------------------------
# workflows/domains/crm
# -------------------------
touch "$BASE_DIR/workflows/domains/crm/lead_intake.json"
touch "$BASE_DIR/workflows/domains/crm/lead_enrichment.json"
touch "$BASE_DIR/workflows/domains/crm/lead_sync_to_crm.json"

# -------------------------
# workflows/domains/infra
# -------------------------
touch "$BASE_DIR/workflows/domains/infra/infra_deploy_terraform.json"
touch "$BASE_DIR/workflows/domains/infra/infra_post_deploy_checks.json"

# -------------------------
# workflows/domains/meta
# -------------------------
touch "$BASE_DIR/workflows/domains/meta/automation_catalog_builder.json"
touch "$BASE_DIR/workflows/domains/meta/workflow_health_check.json"

# -------------------------
# workflows/domains/shared
# -------------------------
touch "$BASE_DIR/workflows/domains/shared/error_central_handler.json"
touch "$BASE_DIR/workflows/domains/shared/notify_slack.json"
touch "$BASE_DIR/workflows/domains/shared/log_event.json"
touch "$BASE_DIR/workflows/domains/shared/approvals_generic.json"

# -------------------------
# workflows/packs
# -------------------------
touch "$BASE_DIR/workflows/packs/crm_pack.json"
touch "$BASE_DIR/workflows/packs/infra_pack.json"
touch "$BASE_DIR/workflows/packs/core_shared_pack.json"

# -------------------------
# workflows/metadata
# -------------------------
touch "$BASE_DIR/workflows/metadata/workflows_catalog.yaml"
touch "$BASE_DIR/workflows/metadata/ownership.yaml"

# -------------------------
# shared/schemas
# -------------------------
touch "$BASE_DIR/shared/schemas/event.schema.json"
touch "$BASE_DIR/shared/schemas/contact.schema.json"
touch "$BASE_DIR/shared/schemas/incident.schema.json"
touch "$BASE_DIR/shared/schemas/infra_deploy.schema.json"

# -------------------------
# shared/js_snippets
# -------------------------
touch "$BASE_DIR/shared/js_snippets/normalize_contact.js"
touch "$BASE_DIR/shared/js_snippets/validate_payload.js"
touch "$BASE_DIR/shared/js_snippets/compute_risk_score.js"

# -------------------------
# ops/envs
# -------------------------
touch "$BASE_DIR/ops/envs/dev.env.yaml"
touch "$BASE_DIR/ops/envs/staging.env.yaml"
touch "$BASE_DIR/ops/envs/prod.env.yaml"

touch "$BASE_DIR/ops/envs/dev.n8n-targets.yaml"
touch "$BASE_DIR/ops/envs/staging.n8n-targets.yaml"
touch "$BASE_DIR/ops/envs/prod.n8n-targets.yaml"

# -------------------------
# ops/scripts
# -------------------------
touch "$BASE_DIR/ops/scripts/export_workflows.sh"
touch "$BASE_DIR/ops/scripts/import_workflows.sh"
touch "$BASE_DIR/ops/scripts/validate_workflows.py"
touch "$BASE_DIR/ops/scripts/generate_catalog.py"

# -------------------------
# ops/backups
# -------------------------
touch "$BASE_DIR/ops/backups/backup_policy.md"
touch "$BASE_DIR/ops/backups/restore_runbook.md"

# -------------------------
# docs
# -------------------------
touch "$BASE_DIR/docs/WORKFLOW_NAMING.md"
touch "$BASE_DIR/docs/DATA_CONTRACTS.md"
touch "$BASE_DIR/docs/RUNBOOKS.md"
touch "$BASE_DIR/docs/ERROR_HANDLING.md"

echo "Done. Structure created under: $BASE_DIR"
