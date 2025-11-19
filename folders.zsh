#!/usr/bin/env zsh
set -e

ROOT="automation-platform"

# Create base directory structure
mkdir -p ${ROOT}/workflows/platform
mkdir -p ${ROOT}/workflows/domain_crm
mkdir -p ${ROOT}/workflows/domain_infra
mkdir -p ${ROOT}/workflows/meta
mkdir -p ${ROOT}/shared/js_snippets
mkdir -p ${ROOT}/shared/schemas
mkdir -p ${ROOT}/shared/config
mkdir -p ${ROOT}/docs
mkdir -p ${ROOT}/ci
mkdir -p ${ROOT}/.github/workflows

# Create empty JSON and code/config files (no content for now)
touch ${ROOT}/workflows/platform/error_central_handler.json
touch ${ROOT}/workflows/platform/notify_slack.json
touch ${ROOT}/workflows/platform/log_event.json
touch ${ROOT}/workflows/platform/approvals_generic.json

touch ${ROOT}/workflows/domain_crm/lead_intake.json
touch ${ROOT}/workflows/domain_crm/lead_enrichment.json
touch ${ROOT}/workflows/domain_crm/lead_sync_to_crm.json

touch ${ROOT}/workflows/domain_infra/infra_deploy_terraform.json
touch ${ROOT}/workflows/domain_infra/infra_post_deploy_checks.json

touch ${ROOT}/workflows/meta/automation_catalog_builder.json
touch ${ROOT}/workflows/meta/workflow_health_check.json

touch ${ROOT}/shared/js_snippets/normalize_contact.js
touch ${ROOT}/shared/js_snippets/validate_payload.js
touch ${ROOT}/shared/js_snippets/compute_risk_score.js

touch ${ROOT}/shared/schemas/contact.schema.json
touch ${ROOT}/shared/schemas/incident.schema.json

touch ${ROOT}/shared/config/environments.dev.yaml
touch ${ROOT}/shared/config/environments.prod.yaml

# Create docs files and populate with placeholders
cat > ${ROOT}/docs/WORKFLOW_NAMING.md << 'EOF'
# Workflow Naming Guidelines

This guideline covers how to name workflow files in the automation‐platform.

## Structure
Use: <domain>_<purpose>[_<detail>].json  
Where:
- domain: platform | domain_crm | domain_infra | meta  
- purpose: a short verb or noun describing the action  
- detail: optional qualifier if needed  

## Location
Place workflow files under:
