#!/usr/bin/env python3
"""
Purpose: GitOps tooling for webhook-system workflows using the overlay catalog (export/import/drift-check)
Created/Updated: 2025-12-17 00:00
Agent: GPT-5.2

This script is intentionally separate from ops/scripts/n8n_gitops.py so we can manage
webhook-system workflows via an overlay catalog without editing the primary catalog.

Catalog:
- workflows/metadata/webhooks_catalog.yaml

Configuration:
- N8N_BASE_URL: Base URL for n8n (default: http://localhost:5678)
- N8N_API_KEY: API key for n8n (required)
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml
import json
from ops.scripts import n8n_gitops_common
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = REPO_ROOT / "workflows" / "metadata" / "webhooks_catalog.yaml"
@dataclass(frozen=True)
class CatalogEntry:
    """Overlay catalog entry mapping a logical ID to workflow name and repo file path."""

    logical_id: str
    name: str
    file_path: Path

def _load_catalog_entries(catalog_path: Path) -> List[CatalogEntry]:
    if not catalog_path.exists():
        n8n_gitops_common._die(f"Catalog not found: {catalog_path}")

    with open(catalog_path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}

    workflows = (doc.get("catalog") or {}).get("workflows") or []
    entries: List[CatalogEntry] = []
    for wf in workflows:
        if not isinstance(wf, dict):
            continue
        logical_id = str(wf.get("id") or "").strip()
        name = str(wf.get("name") or "").strip()
        file_path_raw = str(wf.get("file_path") or "").strip()
        if not logical_id or not name or not file_path_raw:
            continue
        entries.append(
            CatalogEntry(
                logical_id=logical_id,
                name=name,
                file_path=REPO_ROOT / file_path_raw,
            )
        )
    if not entries:
        n8n_gitops_common._die(f"No workflows found in catalog: {catalog_path}")
    return entries

def cmd_export(base_url: str, api_key: str, catalog_path: Path, only: Optional[List[str]]) -> int:
    entries = _load_catalog_entries(catalog_path)
    if only:
        only_set = set(only)
        entries = [e for e in entries if e.logical_id in only_set]

    remote = n8n_gitops_common._n8n_list_workflows(base_url, api_key)
    missing: List[str] = []

    for entry in entries:
        remote_match = n8n_gitops_common._find_remote_by_name(remote, entry.name)
        if not remote_match:
            missing.append(entry.logical_id)
            continue
        remote_id = str(remote_match.get("id") or "").strip()
        if not remote_id:
            missing.append(entry.logical_id)
            continue

        full = n8n_gitops_common._n8n_get_workflow(base_url, api_key, remote_id)
        normalized = n8n_gitops_common.normalize_workflow_json(full)

        # Preserve/seed repo metadata block if present.
        existing = {}
        if entry.file_path.exists() and entry.file_path.stat().st_size > 0:
            try:
                existing = n8n_gitops_common._read_json(entry.file_path)
            except Exception:
                existing = {}
        if isinstance(existing, dict) and isinstance(existing.get("_metadata"), dict):
            normalized["_metadata"] = existing["_metadata"]
        else:
            normalized["_metadata"] = {
                "purpose": f"Managed workflow: {entry.name}",
                "created": "2025-12-17 00:00",
                "agent": "GPT-5.2",
            }

        n8n_gitops_common._write_json(entry.file_path, normalized)
        print(f"exported: {entry.logical_id} -> {entry.file_path}")

    if missing:
        print("WARN: missing remote workflows for logical IDs:", ", ".join(missing), file=sys.stderr)
        return 1
    return 0
def cmd_import(base_url: str, api_key: str, catalog_path: Path, only: Optional[List[str]]) -> int:
    entries = _load_catalog_entries(catalog_path)
    if only:
        only_set = set(only)
        entries = [e for e in entries if e.logical_id in only_set]

    remote = n8n_gitops_common._n8n_list_workflows(base_url, api_key)

    for entry in entries:
        if not entry.file_path.exists():
            n8n_gitops_common._die(f"Workflow JSON not found: {entry.file_path}")

        local = n8n_gitops_common._read_json(entry.file_path)
        if not isinstance(local, dict):
            n8n_gitops_common._die(f"Workflow JSON must be an object: {entry.file_path}")

        payload = n8n_gitops_common._strip_repo_metadata_for_import(local)
        if "nodes" not in payload or "connections" not in payload:
            n8n_gitops_common._die(f"Workflow JSON does not look like an n8n export (missing nodes/connections): {entry.file_path}")

        remote_match = n8n_gitops_common._find_remote_by_name(remote, entry.name)
        if remote_match and remote_match.get("id"):
            remote_id = str(remote_match["id"])
            n8n_gitops_common._n8n_update_workflow(base_url, api_key, remote_id, payload)
            print(f"updated: {entry.logical_id} ({entry.name})")
        else:
            n8n_gitops_common._n8n_create_workflow(base_url, api_key, payload)
            print(f"created: {entry.logical_id} ({entry.name})")

    return 0
def cmd_drift_check(base_url: str, api_key: str, catalog_path: Path, only: Optional[List[str]]) -> int:
    entries = _load_catalog_entries(catalog_path)
    if only:
        only_set = set(only)
        entries = [e for e in entries if e.logical_id in only_set]

    remote = n8n_gitops_common._n8n_list_workflows(base_url, api_key)
    drifted: List[str] = []

    for entry in entries:
        local = n8n_gitops_common._read_json(entry.file_path)
        local_norm = n8n_gitops_common.normalize_workflow_json(n8n_gitops_common._strip_repo_metadata_for_import(local))

        remote_match = n8n_gitops_common._find_remote_by_name(remote, entry.name)
        if not remote_match or not remote_match.get("id"):
            drifted.append(entry.logical_id)
            continue
        remote_full = n8n_gitops_common._n8n_get_workflow(base_url, api_key, str(remote_match["id"]))
        remote_norm = n8n_gitops_common.normalize_workflow_json(remote_full)

        if json.dumps(local_norm, sort_keys=True) != json.dumps(remote_norm, sort_keys=True):
            drifted.append(entry.logical_id)

    if drifted:
        print("DRIFT:", ", ".join(drifted), file=sys.stderr)
        return 1
    print("OK: no drift detected")
    return 0
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="GitOps for webhook-system workflows (overlay catalog).")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="Path to overlay catalog YAML.")
    parser.add_argument("--only", action="append", help="Logical workflow ID(s) to operate on (repeatable).")

    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export")
    sub.add_parser("import")
    sub.add_parser("drift-check")

    args = parser.parse_args(argv)

    base_url = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
    api_key = os.environ.get("N8N_API_KEY", "").strip()
    if not api_key:
        n8n_gitops_common._die("N8N_API_KEY is required")

    catalog_path = Path(args.catalog)

    if args.cmd == "export":
        return cmd_export(base_url, api_key, catalog_path, args.only)
    if args.cmd == "import":
        return cmd_import(base_url, api_key, catalog_path, args.only)
    if args.cmd == "drift-check":
        return cmd_drift_check(base_url, api_key, catalog_path, args.only)

    n8n_gitops_common._die(f"Unknown command: {args.cmd}")
    return 2
if __name__ == "__main__":
    raise SystemExit(main())
