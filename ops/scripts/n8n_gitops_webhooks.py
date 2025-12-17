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
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = REPO_ROOT / "workflows" / "metadata" / "webhooks_catalog.yaml"


@dataclass(frozen=True)
class CatalogEntry:
    """Overlay catalog entry mapping a logical ID to workflow name and repo file path."""

    logical_id: str
    name: str
    file_path: Path


def _die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def _load_catalog_entries(catalog_path: Path) -> List[CatalogEntry]:
    if not catalog_path.exists():
        _die(f"Catalog not found: {catalog_path}")

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
        _die(f"No workflows found in catalog: {catalog_path}")
    return entries


def _http_json(
    method: str,
    url: str,
    headers: Dict[str, str],
    body: Optional[Dict[str, Any]] = None,
) -> Any:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}

    req = urllib.request.Request(url=url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8")
            if not payload:
                return None
            return json.loads(payload)
    except urllib.error.HTTPError as e:
        try:
            details = e.read().decode("utf-8")
        except Exception:
            details = ""
        _die(f"{method} {url} failed: HTTP {e.code}. {details}")
    except urllib.error.URLError as e:
        _die(f"{method} {url} failed: {e}")


def _n8n_headers(api_key: str) -> Dict[str, str]:
    return {"X-N8N-API-KEY": api_key, "Accept": "application/json"}


def _n8n_list_workflows(base_url: str, api_key: str) -> List[Dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/api/v1/workflows"
    data = _http_json("GET", url, _n8n_headers(api_key))

    if isinstance(data, list):
        return [w for w in data if isinstance(w, dict)]
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return [w for w in data["data"] if isinstance(w, dict)]
    if isinstance(data, dict) and isinstance(data.get("workflows"), list):
        return [w for w in data["workflows"] if isinstance(w, dict)]
    return []


def _n8n_get_workflow(base_url: str, api_key: str, workflow_id: str) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/workflows/{workflow_id}"
    data = _http_json("GET", url, _n8n_headers(api_key))
    return data if isinstance(data, dict) else {}


def _n8n_create_workflow(base_url: str, api_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/workflows"
    data = _http_json("POST", url, _n8n_headers(api_key), body=payload)
    return data if isinstance(data, dict) else {}


def _n8n_update_workflow(base_url: str, api_key: str, workflow_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/workflows/{workflow_id}"
    data = _http_json("PUT", url, _n8n_headers(api_key), body=payload)
    return data if isinstance(data, dict) else {}


def _find_remote_by_name(remote_list: Iterable[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    for wf in remote_list:
        if str(wf.get("name") or "").strip() == name:
            return wf
    return None


def normalize_workflow_json(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize an n8n workflow JSON document for deterministic diffs and environment portability.

    Notes:
    - Removes volatile identifiers/timestamps.
    - Removes repo-only '_metadata' before writing (import/export portability).
    """

    wf = json.loads(json.dumps(workflow))  # deep copy via JSON roundtrip

    for key in ("id", "active", "createdAt", "updatedAt", "versionId", "meta", "staticData"):
        wf.pop(key, None)

    # Strip repo-only metadata if present.
    wf.pop("_metadata", None)

    nodes = wf.get("nodes")
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node.pop("id", None)
            creds = node.get("credentials")
            if isinstance(creds, dict):
                for _, cred_obj in creds.items():
                    if isinstance(cred_obj, dict):
                        cred_obj.pop("id", None)

    return wf


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))
        f.write("\n")


def _read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _strip_repo_metadata_for_import(workflow: Dict[str, Any]) -> Dict[str, Any]:
    wf = json.loads(json.dumps(workflow))
    wf.pop("_metadata", None)
    return wf


def cmd_export(base_url: str, api_key: str, catalog_path: Path, only: Optional[List[str]]) -> int:
    entries = _load_catalog_entries(catalog_path)
    if only:
        only_set = set(only)
        entries = [e for e in entries if e.logical_id in only_set]

    remote = _n8n_list_workflows(base_url, api_key)
    missing: List[str] = []

    for entry in entries:
        remote_match = _find_remote_by_name(remote, entry.name)
        if not remote_match:
            missing.append(entry.logical_id)
            continue
        remote_id = str(remote_match.get("id") or "").strip()
        if not remote_id:
            missing.append(entry.logical_id)
            continue

        full = _n8n_get_workflow(base_url, api_key, remote_id)
        normalized = normalize_workflow_json(full)

        # Preserve/seed repo metadata block if present.
        existing = {}
        if entry.file_path.exists() and entry.file_path.stat().st_size > 0:
            try:
                existing = _read_json(entry.file_path)
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

        _write_json(entry.file_path, normalized)
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

    remote = _n8n_list_workflows(base_url, api_key)

    for entry in entries:
        if not entry.file_path.exists():
            _die(f"Workflow JSON not found: {entry.file_path}")

        local = _read_json(entry.file_path)
        if not isinstance(local, dict):
            _die(f"Workflow JSON must be an object: {entry.file_path}")

        payload = _strip_repo_metadata_for_import(local)
        if "nodes" not in payload or "connections" not in payload:
            _die(f"Workflow JSON does not look like an n8n export (missing nodes/connections): {entry.file_path}")

        remote_match = _find_remote_by_name(remote, entry.name)
        if remote_match and remote_match.get("id"):
            remote_id = str(remote_match["id"])
            _n8n_update_workflow(base_url, api_key, remote_id, payload)
            print(f"updated: {entry.logical_id} ({entry.name})")
        else:
            _n8n_create_workflow(base_url, api_key, payload)
            print(f"created: {entry.logical_id} ({entry.name})")

    return 0


def cmd_drift_check(base_url: str, api_key: str, catalog_path: Path, only: Optional[List[str]]) -> int:
    entries = _load_catalog_entries(catalog_path)
    if only:
        only_set = set(only)
        entries = [e for e in entries if e.logical_id in only_set]

    remote = _n8n_list_workflows(base_url, api_key)
    drifted: List[str] = []

    for entry in entries:
        local = _read_json(entry.file_path)
        local_norm = normalize_workflow_json(_strip_repo_metadata_for_import(local))

        remote_match = _find_remote_by_name(remote, entry.name)
        if not remote_match or not remote_match.get("id"):
            drifted.append(entry.logical_id)
            continue
        remote_full = _n8n_get_workflow(base_url, api_key, str(remote_match["id"]))
        remote_norm = normalize_workflow_json(remote_full)

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
        _die("N8N_API_KEY is required")

    catalog_path = Path(args.catalog)

    if args.cmd == "export":
        return cmd_export(base_url, api_key, catalog_path, args.only)
    if args.cmd == "import":
        return cmd_import(base_url, api_key, catalog_path, args.only)
    if args.cmd == "drift-check":
        return cmd_drift_check(base_url, api_key, catalog_path, args.only)

    _die(f"Unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


