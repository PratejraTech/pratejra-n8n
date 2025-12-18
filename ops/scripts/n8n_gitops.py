#!/usr/bin/env python3
"""
Purpose: GitOps tooling for n8n workflows (export/import/drift-check) using the n8n REST API
Created/Updated: 2025-12-17 00:00
Agent: GPT-5.2

This script supports a version-controlled n8n workflow lifecycle:
- Export workflows from a running n8n instance into repo paths (deterministic JSON normalization)
- Import workflows from repo paths into a running n8n instance (name-based upsert)
- Drift-check by comparing normalized remote vs local workflow JSON

Configuration:
- N8N_BASE_URL: Base URL for n8n (default: http://localhost:5678)
- N8N_API_KEY: API key for n8n (required)

Usage:
  python ops/scripts/n8n_gitops.py export
  python ops/scripts/n8n_gitops.py import
  python ops/scripts/n8n_gitops.py drift-check
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from ops.scripts import n8n_gitops_common
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = REPO_ROOT / "workflows" / "metadata" / "workflows_catalog.yaml"
@dataclass(frozen=True)
class CatalogEntry:
    """Parsed catalog entry mapping workflow logical ID to file path and display name."""

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
        n8n_gitops_common._write_json(entry.file_path, normalized)
        print(f"exported: {entry.logical_id} -> {entry.file_path}")

    if missing:
        print("WARN: missing workflows in n8n (by name): " + ", ".join(missing), file=sys.stderr)
    return 0
def cmd_import(base_url: str, api_key: str, catalog_path: Path, only: Optional[List[str]]) -> int:
    entries = _load_catalog_entries(catalog_path)
    if only:
        only_set = set(only)
        entries = [e for e in entries if e.logical_id in only_set]

    remote = n8n_gitops_common._n8n_list_workflows(base_url, api_key)

    for entry in entries:
        if not entry.file_path.exists():
            print(f"skip (missing file): {entry.logical_id} -> {entry.file_path}", file=sys.stderr)
            continue

        local = n8n_gitops_common._read_json(entry.file_path)
        local_norm = n8n_gitops_common.normalize_workflow_json(local)

        # Ensure workflow name matches catalog name for stable upserts.
        local_norm["name"] = entry.name

        remote_match = n8n_gitops_common._find_remote_by_name(remote, entry.name)
        if remote_match and remote_match.get("id"):
            remote_id = str(remote_match["id"])
            n8n_gitops_common._n8n_update_workflow(base_url, api_key, remote_id, local_norm)
            print(f"updated: {entry.logical_id} ({entry.name})")
        else:
            n8n_gitops_common._n8n_create_workflow(base_url, api_key, local_norm)
            print(f"created: {entry.logical_id} ({entry.name})")

    return 0
def cmd_drift_check(base_url: str, api_key: str, catalog_path: Path, only: Optional[List[str]]) -> int:
    entries = _load_catalog_entries(catalog_path)
    if only:
        only_set = set(only)
        entries = [e for e in entries if e.logical_id in only_set]

    remote = n8n_gitops_common._n8n_list_workflows(base_url, api_key)
    drifted: List[str] = []
    missing: List[str] = []

    for entry in entries:
        remote_match = n8n_gitops_common._find_remote_by_name(remote, entry.name)
        if not remote_match or not remote_match.get("id"):
            missing.append(entry.logical_id)
            continue

        if not entry.file_path.exists():
            missing.append(entry.logical_id)
            continue

        remote_full = n8n_gitops_common._n8n_get_workflow(base_url, api_key, str(remote_match["id"]))
        remote_norm = n8n_gitops_common.normalize_workflow_json(remote_full)
        local = n8n_gitops_common.normalize_workflow_json(n8n_gitops_common._read_json(entry.file_path))

        if remote_norm != local:
            drifted.append(entry.logical_id)

    if missing:
        print("WARN: missing entries (either remote or local): " + ", ".join(missing), file=sys.stderr)
    if drifted:
        print("DRIFT DETECTED: " + ", ".join(drifted))
        return 1

    print("OK: no drift detected")
    return 0
def main() -> int:
    parser = argparse.ArgumentParser(description="n8n GitOps export/import/drift-check via API")
    parser.add_argument(
        "--base-url",
        default=os.getenv("N8N_BASE_URL", "http://localhost:5678"),
        help="n8n base URL (default: env N8N_BASE_URL or http://localhost:5678)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("N8N_API_KEY", ""),
        help="n8n API key (default: env N8N_API_KEY)",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help=f"Path to workflows catalog (default: {DEFAULT_CATALOG})",
    )
    parser.add_argument(
        "--only",
        action="append",
        help="Limit to a specific logical workflow id (repeatable)",
    )

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("export", help="Export n8n workflows into repo JSON files (normalized)")
    sub.add_parser("import", help="Import repo JSON workflows into n8n (name-based upsert)")
    sub.add_parser("drift-check", help="Detect drift between repo JSON and remote n8n workflows")

    args = parser.parse_args()

    if not args.api_key:
        n8n_gitops_common._die("N8N API key is required. Set --api-key or env N8N_API_KEY.")

    if args.command == "export":
        return cmd_export(args.base_url, args.api_key, args.catalog, args.only)
    if args.command == "import":
        return cmd_import(args.base_url, args.api_key, args.catalog, args.only)
    if args.command == "drift-check":
        return cmd_drift_check(args.base_url, args.api_key, args.catalog, args.only)

    n8n_gitops_common._die(f"Unknown command: {args.command}")
    return 2
if __name__ == "__main__":
    raise SystemExit(main())
