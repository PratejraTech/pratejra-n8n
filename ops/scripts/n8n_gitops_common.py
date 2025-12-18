#!/usr/bin/env python3
"""
Purpose: Shared utilities for n8n GitOps scripts (n8n_gitops.py and n8n_gitops_webhooks.py)
Created/Updated: 2025-12-17
Agent: GPT-5.2

This module contains common functions used by both GitOps scripts to avoid code duplication.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _die(msg: str) -> None:
    """Print error message and exit with code 2."""
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def _http_json(
    method: str,
    url: str,
    headers: Dict[str, str],
    body: Optional[Dict[str, Any]] = None,
) -> Any:
    """Make HTTP request and return JSON response."""
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
    """Generate n8n API headers with API key authentication."""
    return {"X-N8N-API-KEY": api_key, "Accept": "application/json"}


def _n8n_list_workflows(base_url: str, api_key: str) -> List[Dict[str, Any]]:
    """List all workflows from n8n instance."""
    url = f"{base_url.rstrip('/')}/api/v1/workflows"
    data = _http_json("GET", url, _n8n_headers(api_key))

    # n8n response shape can vary; handle common patterns.
    if isinstance(data, list):
        return [w for w in data if isinstance(w, dict)]
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return [w for w in data["data"] if isinstance(w, dict)]
    if isinstance(data, dict) and isinstance(data.get("workflows"), list):
        return [w for w in data["workflows"] if isinstance(w, dict)]
    return []


def _n8n_get_workflow(base_url: str, api_key: str, workflow_id: str) -> Dict[str, Any]:
    """Get a specific workflow by ID from n8n instance."""
    url = f"{base_url.rstrip('/')}/api/v1/workflows/{workflow_id}"
    data = _http_json("GET", url, _n8n_headers(api_key))
    return data if isinstance(data, dict) else {}


def _n8n_create_workflow(base_url: str, api_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new workflow in n8n instance."""
    url = f"{base_url.rstrip('/')}/api/v1/workflows"
    data = _http_json("POST", url, _n8n_headers(api_key), body=payload)
    return data if isinstance(data, dict) else {}


def _n8n_update_workflow(base_url: str, api_key: str, workflow_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing workflow in n8n instance."""
    url = f"{base_url.rstrip('/')}/api/v1/workflows/{workflow_id}"
    data = _http_json("PUT", url, _n8n_headers(api_key), body=payload)
    return data if isinstance(data, dict) else {}


def _find_remote_by_name(remote_list: Iterable[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    """Find a workflow in remote list by name."""
    for wf in remote_list:
        if str(wf.get("name") or "").strip() == name:
            return wf
    return None


def normalize_workflow_json(workflow: Dict[str, Any], strip_metadata: bool = False) -> Dict[str, Any]:
    """
    Normalize an n8n workflow JSON document for deterministic diffs and environment portability.

    Args:
        workflow: The workflow JSON to normalize
        strip_metadata: If True, remove repo-only '_metadata' field (for import)

    Notes:
        - Removes volatile identifiers/timestamps.
        - Optionally removes repo-only '_metadata' before writing (import/export portability).
    """
    wf = json.loads(json.dumps(workflow))  # deep copy via JSON roundtrip

    # Remove volatile top-level fields (these frequently differ across instances).
    for key in ("id", "active", "createdAt", "updatedAt", "versionId", "meta", "staticData"):
        wf.pop(key, None)

    # Strip repo-only metadata if requested (for import operations).
    if strip_metadata:
        wf.pop("_metadata", None)

    # Normalize node IDs and credential IDs while keeping credential names.
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
    """Write JSON object to file with consistent formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))
        f.write("\n")


def _read_json(path: Path) -> Dict[str, Any]:
    """Read JSON object from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _strip_repo_metadata_for_import(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Strip repo-only metadata from workflow before importing to n8n."""
    wf = json.loads(json.dumps(workflow))
    wf.pop("_metadata", None)
    return wf
