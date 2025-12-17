"""
Purpose: Validate the generated Internal API v1 OpenAPI spec and local $ref integrity
Created/Updated: 2025-12-17
Agent: BACKEND_AGENT
"""

import json
from pathlib import Path

import yaml


def _iter_refs(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                yield v
            else:
                yield from _iter_refs(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_refs(item)


class TestInternalApiOpenApi:
    """Validate OpenAPI YAML structure and local $ref integrity."""

    def test_openapi_file_exists_and_parses(self):
        repo_root = Path(__file__).parent.parent
        openapi_path = repo_root / "docs" / "INTERNAL_API_V1.openapi.yaml"
        assert openapi_path.exists(), "OpenAPI spec file not found"

        with open(openapi_path, "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f)

        assert isinstance(spec, dict)
        assert spec.get("openapi") == "3.1.0"
        assert spec.get("jsonSchemaDialect") == "http://json-schema.org/draft-07/schema#"

        paths = spec.get("paths", {})
        assert "/internal/api/v1/events/{event_type}" in paths
        assert "/internal/api/v1/health" in paths

    def test_all_schema_refs_exist_and_are_valid_json(self):
        repo_root = Path(__file__).parent.parent
        openapi_path = repo_root / "docs" / "INTERNAL_API_V1.openapi.yaml"
        with open(openapi_path, "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f)

        docs_dir = openapi_path.parent
        refs = list(_iter_refs(spec))
        assert refs, "No $ref entries found in OpenAPI spec"

        for ref in refs:
            if ref.startswith("#"):
                continue
            ref_path_str = ref.split("#", 1)[0]
            target_path = (docs_dir / ref_path_str).resolve()
            assert target_path.exists(), f"$ref target does not exist: {ref} -> {target_path}"

            # Ensure referenced artifacts are valid JSON schemas/documents
            with open(target_path, "r", encoding="utf-8") as jf:
                json.load(jf)


