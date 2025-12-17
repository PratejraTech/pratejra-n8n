#!/usr/bin/env bash
# Purpose: Convenience wrapper for ops/scripts/n8n_gitops.py (export/import/drift-check) with env-based config
# Created/Updated: 2025-12-17 00:00
# Agent: GPT-5.2

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ops/scripts/n8n_gitops.sh <export|import|drift-check> [--only <logical_id>]..." >&2
  exit 2
fi

CMD="$1"
shift

exec python3 "$(dirname "$0")/n8n_gitops.py" "$CMD" "$@"


