#!/usr/bin/env python3
"""
Purpose: Generate Internal API v1 OpenAPI and contract documentation from a single endpoint manifest
Created/Updated: 2025-12-17
Agent: BACKEND_AGENT

This script reads `docs/internal_api_v1.contracts.yaml` and generates:
- `docs/INTERNAL_API_V1.openapi.yaml` (OpenAPI 3.1)
- `docs/INTERNAL_API_V1_CONTRACTS.md` (human-readable contracts)

It also validates that all referenced JSON schema files exist and are valid JSON.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml


REPO_ROOT = Path(__file__).parent.parent.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "docs" / "internal_api_v1.contracts.yaml"
DEFAULT_OUT_OPENAPI_PATH = REPO_ROOT / "docs" / "INTERNAL_API_V1.openapi.yaml"
DEFAULT_OUT_DOCS_PATH = REPO_ROOT / "docs" / "INTERNAL_API_V1_CONTRACTS.md"


class ContractError(Exception):
    """Raised when the manifest or referenced artifacts are invalid."""


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ContractError(f"Manifest not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ContractError("Manifest root must be a YAML mapping/object.")
    return data


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ContractError(f"Schema not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ContractError(f"Invalid JSON in {path}: {e}") from e
    if not isinstance(data, dict):
        raise ContractError(f"Schema root must be a JSON object: {path}")
    return data


def _ref_from_docs(schema_ref_repo_relative: str) -> str:
    """
    Convert a repo-relative schema path (e.g. shared/schemas/event.schema.json)
    into an OpenAPI $ref path relative to docs/ (e.g. ../shared/schemas/event.schema.json).
    """
    schema_ref_repo_relative = schema_ref_repo_relative.lstrip("/")
    return str(PurePosixPath("..") / PurePosixPath(schema_ref_repo_relative))


def _ensure_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"Field '{field}' must be a non-empty string.")
    return value


def _ensure_mapping(value: Any, field: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"Field '{field}' must be a mapping/object.")
    return value


def _ensure_list(value: Any, field: str) -> List[Any]:
    if not isinstance(value, list):
        raise ContractError(f"Field '{field}' must be a list/array.")
    return value


def _iter_refs(openapi_obj: Any) -> Iterable[str]:
    """Yield all $ref strings in a nested OpenAPI object."""
    if isinstance(openapi_obj, dict):
        for k, v in openapi_obj.items():
            if k == "$ref" and isinstance(v, str):
                yield v
            else:
                yield from _iter_refs(v)
    elif isinstance(openapi_obj, list):
        for item in openapi_obj:
            yield from _iter_refs(item)


@dataclass(frozen=True)
class Endpoint:
    id: str
    method: str
    path: str
    summary: str
    description: str
    path_params: Dict[str, Any]
    request: Optional[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    examples: Dict[str, Any]


def _parse_manifest(manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Endpoint]]:
    api = _ensure_mapping(manifest.get("api", {}), "api")
    endpoints_raw = _ensure_list(manifest.get("endpoints", []), "endpoints")

    endpoints: List[Endpoint] = []
    for i, ep_raw in enumerate(endpoints_raw):
        if not isinstance(ep_raw, dict):
            raise ContractError(f"endpoints[{i}] must be an object.")

        ep_id = _ensure_str(ep_raw.get("id"), f"endpoints[{i}].id")
        method = _ensure_str(ep_raw.get("method"), f"endpoints[{i}].method").upper()
        path = _ensure_str(ep_raw.get("path"), f"endpoints[{i}].path")
        summary = _ensure_str(ep_raw.get("summary"), f"endpoints[{i}].summary")
        description = str(ep_raw.get("description") or summary)

        path_params = ep_raw.get("path_params") or {}
        if not isinstance(path_params, dict):
            raise ContractError(f"endpoints[{i}].path_params must be an object if provided.")

        request = ep_raw.get("request")
        if request is not None and not isinstance(request, dict):
            raise ContractError(f"endpoints[{i}].request must be an object if provided.")

        responses = _ensure_mapping(ep_raw.get("responses", {}), f"endpoints[{i}].responses")
        if not responses:
            raise ContractError(f"endpoints[{i}].responses must not be empty.")

        examples = ep_raw.get("examples") or {}
        if not isinstance(examples, dict):
            raise ContractError(f"endpoints[{i}].examples must be an object if provided.")

        endpoints.append(
            Endpoint(
                id=ep_id,
                method=method,
                path=path,
                summary=summary,
                description=description,
                path_params=path_params,
                request=request,
                responses=responses,
                examples=examples,
            )
        )

    return api, endpoints


def _validate_schema_refs(repo_root: Path, endpoints: List[Endpoint]) -> None:
    schema_paths: List[Path] = []

    for ep in endpoints:
        if ep.request and "schema_ref" in ep.request:
            schema_paths.append(repo_root / _ensure_str(ep.request["schema_ref"], f"{ep.id}.request.schema_ref"))

        for code, resp in ep.responses.items():
            if not isinstance(resp, dict):
                raise ContractError(f"{ep.id}.responses[{code}] must be an object.")
            schema_ref = resp.get("schema_ref")
            if schema_ref:
                schema_paths.append(repo_root / _ensure_str(schema_ref, f"{ep.id}.responses[{code}].schema_ref"))

    # Load each schema once (and fail fast on invalid JSON)
    for p in sorted(set(schema_paths)):
        _load_json(p)


def _build_openapi(api: Dict[str, Any], endpoints: List[Endpoint]) -> Dict[str, Any]:
    title = str(api.get("title") or "Internal API")
    version = str(api.get("version") or "v1")

    openapi: Dict[str, Any] = {
        "openapi": "3.1.0",
        "jsonSchemaDialect": "http://json-schema.org/draft-07/schema#",
        "info": {
            "title": title,
            "version": version,
            "description": "Generated from docs/internal_api_v1.contracts.yaml",
        },
        "servers": [
            {"url": "http://localhost:5678", "description": "Local (default n8n)"},
            {"url": "https://n8n.automation-hub.example.com", "description": "Production"},
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                }
            }
        },
        "paths": {},
    }

    paths: Dict[str, Any] = {}
    for ep in endpoints:
        op: Dict[str, Any] = {
            "operationId": ep.id,
            "summary": ep.summary,
            "description": ep.description,
            "security": [{"bearerAuth": []}],
            "responses": {},
        }

        # Path parameters
        parameters: List[Dict[str, Any]] = []
        for name, spec in (ep.path_params or {}).items():
            if not isinstance(spec, dict):
                raise ContractError(f"{ep.id}.path_params.{name} must be an object.")
            parameters.append(
                {
                    "name": name,
                    "in": "path",
                    "required": bool(spec.get("required", True)),
                    "description": str(spec.get("description") or ""),
                    "schema": {"type": str(spec.get("type") or "string")},
                }
            )
        if parameters:
            op["parameters"] = parameters

        # Request body
        if ep.request:
            content_type = str(ep.request.get("content_type") or "application/json")
            schema_ref = ep.request.get("schema_ref")
            if schema_ref:
                op["requestBody"] = {
                    "required": True,
                    "content": {
                        content_type: {
                            "schema": {"$ref": _ref_from_docs(str(schema_ref))},
                            "examples": {},
                        }
                    },
                }
                if "request" in ep.examples:
                    op["requestBody"]["content"][content_type]["examples"]["request"] = {
                        "value": ep.examples["request"]
                    }

        # Responses
        responses: Dict[str, Any] = {}
        for code, resp in ep.responses.items():
            if not isinstance(resp, dict):
                raise ContractError(f"{ep.id}.responses[{code}] must be an object.")
            desc = str(resp.get("description") or "")
            content_type = str(resp.get("content_type") or "application/json")
            schema_ref = resp.get("schema_ref")

            response_obj: Dict[str, Any] = {"description": desc}
            if schema_ref:
                response_obj["content"] = {
                    content_type: {
                        "schema": {"$ref": _ref_from_docs(str(schema_ref))},
                        "examples": {},
                    }
                }

                # Map examples like response_200 -> 200
                example_key = f"response_{code}"
                if example_key in ep.examples:
                    response_obj["content"][content_type]["examples"][example_key] = {
                        "value": ep.examples[example_key]
                    }

            responses[str(code)] = response_obj
        op["responses"] = responses

        method_key = ep.method.lower()
        paths.setdefault(ep.path, {})[method_key] = op

    openapi["paths"] = paths
    return openapi


def _json_block(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True)


def _build_contract_markdown(api: Dict[str, Any], endpoints: List[Endpoint]) -> str:
    title = str(api.get("title") or "Internal API")
    version = str(api.get("version") or "v1")
    auth = api.get("auth") or {}

    lines: List[str] = []
    lines.append("# Internal API v1 Contracts")
    lines.append("")
    lines.append(f"**Purpose:** Generated contract reference for {title} ({version}).")
    lines.append("**Created/Updated:** 2025-12-17")
    lines.append("**Agent:** BACKEND_AGENT")
    lines.append("")
    lines.append("## Authentication")
    lines.append("")
    lines.append(str(auth.get("description") or "HTTP Bearer authentication is required."))
    lines.append("")
    lines.append("Example header:")
    lines.append("")
    lines.append("```text")
    lines.append(f"{auth.get('header', 'Authorization')}: {auth.get('value_format', 'Bearer {api_key}')}")
    lines.append("```")
    lines.append("")
    lines.append("## Endpoints")
    lines.append("")

    for ep in endpoints:
        lines.append(f"### {ep.method} {ep.path}")
        lines.append("")
        lines.append(ep.description)
        lines.append("")

        if ep.path_params:
            lines.append("#### Path parameters")
            lines.append("")
            for name, spec in ep.path_params.items():
                spec = spec if isinstance(spec, dict) else {}
                required = bool(spec.get("required", True))
                lines.append(f"- `{name}` ({spec.get('type', 'string')}, {'required' if required else 'optional'}): {spec.get('description', '')}")
            lines.append("")

        if ep.request and ep.request.get("schema_ref"):
            lines.append("#### Request")
            lines.append("")
            lines.append(f"- **Content-Type**: `{ep.request.get('content_type', 'application/json')}`")
            lines.append(f"- **Schema**: `{ep.request.get('schema_ref')}`")
            lines.append("")
            if "request" in ep.examples:
                lines.append("Example request:")
                lines.append("")
                lines.append("```json")
                lines.append(_json_block(ep.examples["request"]))
                lines.append("```")
                lines.append("")

        lines.append("#### Responses")
        lines.append("")
        for code, resp in ep.responses.items():
            resp = resp if isinstance(resp, dict) else {}
            schema_ref = resp.get("schema_ref")
            desc = resp.get("description") or ""
            if schema_ref:
                lines.append(f"- **{code}**: {desc} (schema: `{schema_ref}`)")
            else:
                lines.append(f"- **{code}**: {desc}")
        lines.append("")

        # Examples
        example_codes = sorted(
            [k for k in ep.examples.keys() if k.startswith("response_")],
            key=lambda s: int(s.split("_", 1)[1]) if s.split("_", 1)[1].isdigit() else 999,
        )
        for ex_key in example_codes:
            lines.append(f"Example {ex_key.replace('_', ' ')}:")
            lines.append("")
            lines.append("```json")
            lines.append(_json_block(ep.examples[ex_key]))
            lines.append("```")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )


def _write_yaml_with_header(path: Path, header_lines: List[str], data: Dict[str, Any]) -> None:
    """
    Write a YAML file with leading comment header lines.

    This is used to keep generated artifacts self-describing without breaking YAML parsing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for line in header_lines:
            f.write(f"{line}\n")
        yaml.dump(
            data,
            f,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Internal API v1 OpenAPI + contract docs.")
    parser.add_argument("--manifest", type=str, default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--out-openapi", type=str, default=str(DEFAULT_OUT_OPENAPI_PATH))
    parser.add_argument("--out-docs", type=str, default=str(DEFAULT_OUT_DOCS_PATH))
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    out_openapi_path = Path(args.out_openapi)
    out_docs_path = Path(args.out_docs)

    manifest = _load_yaml(manifest_path)
    api, endpoints = _parse_manifest(manifest)

    _validate_schema_refs(REPO_ROOT, endpoints)

    openapi = _build_openapi(api, endpoints)

    # Validate all $ref targets exist relative to docs/
    docs_dir = out_openapi_path.parent
    for ref in _iter_refs(openapi):
        if ref.startswith("#"):
            continue
        ref_path_str = ref.split("#", 1)[0]
        ref_path = (docs_dir / ref_path_str).resolve()
        if not ref_path.exists():
            raise ContractError(f"OpenAPI $ref target not found: {ref} -> {ref_path}")

    _write_yaml_with_header(
        out_openapi_path,
        [
            "# Purpose: Generated OpenAPI 3.1 specification for Automation Hub Internal API v1",
            "# Created/Updated: 2025-12-17",
            "# Agent: BACKEND_AGENT",
            "#",
            "# Source of truth: docs/internal_api_v1.contracts.yaml",
        ],
        openapi,
    )
    _write_text(out_docs_path, _build_contract_markdown(api, endpoints))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


