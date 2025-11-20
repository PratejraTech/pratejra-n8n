#!/usr/bin/env python3
"""
Purpose: Generate workflows catalog and ownership metadata from workflow files
Created/Updated: 2025-11-20
Agent: BACKEND_AGENT

This script scans workflow JSON files and generates/updates:
- workflows/metadata/workflows_catalog.yaml
- workflows/metadata/ownership.yaml (if needed)

Usage:
    python ops/scripts/generate_catalog.py
    python ops/scripts/generate_catalog.py --update-ownership
"""

import argparse
import json
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Base paths
REPO_ROOT = Path(__file__).parent.parent.parent
WORKFLOWS_DIR = REPO_ROOT / "workflows"
METADATA_DIR = WORKFLOWS_DIR / "metadata"
CATALOG_FILE = METADATA_DIR / "workflows_catalog.yaml"
OWNERSHIP_FILE = METADATA_DIR / "ownership.yaml"

# Domain mappings
DOMAIN_MAPPINGS = {
    "domains/shared": "shared",
    "domains/crm": "crm",
    "domains/infra": "infra",
    "domains/meta": "meta",
    "platform": "shared",  # Legacy support
    "domain_crm": "crm",   # Legacy support
    "domain_infra": "infra", # Legacy support
}


def load_workflow_json(workflow_path: Path) -> Dict[str, Any]:
    """Load and parse a workflow JSON file."""
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not load {workflow_path}: {e}")
        return {}


def extract_workflow_metadata(workflow_path: Path, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from workflow JSON file."""
    workflow_id = workflow_path.stem
    workflow_name = workflow_data.get("name", workflow_id)
    
    # Determine domain from path
    domain = "unknown"
    relative_path = workflow_path.relative_to(WORKFLOWS_DIR)
    for path_pattern, domain_name in DOMAIN_MAPPINGS.items():
        if path_pattern in str(relative_path):
            domain = domain_name
            break
    
    # Extract description from workflow data
    description = workflow_data.get("settings", {}).get("executionOrder", "")
    if "nodes" in workflow_data:
        # Try to find description in first node or workflow metadata
        for node in workflow_data.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.start":
                description = node.get("notes", "") or description
                break
    
    # Extract endpoints (webhook nodes)
    endpoints = []
    if "nodes" in workflow_data:
        for node in workflow_data.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.webhook":
                webhook_path = node.get("parameters", {}).get("path", "")
                if webhook_path:
                    endpoints.append(f"/webhook/{webhook_path}")
    
    # Extract dependencies (sub-workflow references)
    dependencies = []
    if "nodes" in workflow_data:
        for node in workflow_data.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.executeWorkflow":
                sub_workflow = node.get("parameters", {}).get("workflowId", "")
                if sub_workflow:
                    dependencies.append(sub_workflow)
    
    return {
        "id": workflow_id,
        "name": workflow_name,
        "domain": domain,
        "description": description or f"{workflow_name} workflow",
        "version": "1.0.0",
        "status": "active",
        "file_path": str(relative_path),
        "endpoints": endpoints,
        "dependencies": dependencies,
        "tags": extract_tags(workflow_data, domain),
        "schema_validation": {
            "required": True,
            "schema_type": infer_schema_type(workflow_id, domain)
        },
        "observability": {
            "metrics_enabled": True,
            "logging_enabled": True
        }
    }


def extract_tags(workflow_data: Dict[str, Any], domain: str) -> List[str]:
    """Extract tags from workflow data or infer from domain/name."""
    tags = [domain]
    
    # Try to extract from workflow metadata
    if "tags" in workflow_data:
        tags.extend(workflow_data["tags"])
    
    # Infer tags from workflow name
    workflow_name = workflow_data.get("name", "").lower()
    if "error" in workflow_name or "handler" in workflow_name:
        tags.append("error-handling")
    if "log" in workflow_name:
        tags.append("logging")
    if "slack" in workflow_name or "notify" in workflow_name:
        tags.append("notifications")
    if "approval" in workflow_name:
        tags.append("approvals")
    if "health" in workflow_name or "check" in workflow_name:
        tags.append("monitoring")
    
    return list(set(tags))  # Remove duplicates


def infer_schema_type(workflow_id: str, domain: str) -> str:
    """Infer schema type from workflow ID and domain."""
    workflow_lower = workflow_id.lower()
    
    if "contact" in workflow_lower or "lead" in workflow_lower:
        return "contact"
    if "incident" in workflow_lower or "error" in workflow_lower:
        return "incident"
    if "infra" in workflow_lower or "deploy" in workflow_lower or "terraform" in workflow_lower:
        return "infra_deploy"
    if "event" in workflow_lower or "log" in workflow_lower:
        return "event"
    
    return "event"  # Default


def scan_workflows() -> List[Dict[str, Any]]:
    """Scan workflow directories and extract metadata."""
    workflows = []
    
    # Scan domains directories
    domains_dirs = [
        WORKFLOWS_DIR / "domains" / "shared",
        WORKFLOWS_DIR / "domains" / "crm",
        WORKFLOWS_DIR / "domains" / "infra",
        WORKFLOWS_DIR / "domains" / "meta",
        WORKFLOWS_DIR / "platform",  # Legacy support
        WORKFLOWS_DIR / "domain_crm",  # Legacy support
        WORKFLOWS_DIR / "domain_infra",  # Legacy support
    ]
    
    for domain_dir in domains_dirs:
        if not domain_dir.exists():
            continue
        
        for workflow_file in domain_dir.glob("*.json"):
            workflow_data = load_workflow_json(workflow_file)
            if workflow_data:
                metadata = extract_workflow_metadata(workflow_file, workflow_data)
                workflows.append(metadata)
    
    return workflows


def generate_catalog(workflows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate catalog structure."""
    now = datetime.utcnow().isoformat() + "Z"
    
    # Calculate statistics
    by_domain = {}
    by_status = {}
    by_risk_level = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    
    for workflow in workflows:
        domain = workflow.get("domain", "unknown")
        by_domain[domain] = by_domain.get(domain, 0) + 1
        
        status = workflow.get("status", "active")
        by_status[status] = by_status.get(status, 0) + 1
    
    return {
        "catalog": {
            "version": "1.0.0",
            "generated_at": now,
            "total_workflows": len(workflows),
            "workflows": workflows,
            "statistics": {
                "by_domain": by_domain,
                "by_status": by_status,
                "by_risk_level": by_risk_level
            }
        }
    }


def load_existing_catalog() -> Dict[str, Any]:
    """Load existing catalog to preserve manual edits."""
    if not CATALOG_FILE.exists():
        return {}
    
    try:
        with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load existing catalog: {e}")
        return {}


def merge_catalog_updates(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge new catalog data with existing, preserving manual edits."""
    if not existing:
        return new
    
    # Merge workflows by ID, preserving manual edits in existing
    existing_workflows = {w.get("id"): w for w in existing.get("catalog", {}).get("workflows", [])}
    new_workflows = {w.get("id"): w for w in new.get("catalog", {}).get("workflows", [])}
    
    # Update existing workflows with new data, but preserve manual fields
    merged_workflows = []
    for workflow_id, new_workflow in new_workflows.items():
        existing_workflow = existing_workflows.get(workflow_id, {})
        # Preserve manual fields like owner, risk_level from existing
        merged = {**new_workflow}
        if existing_workflow:
            # Preserve manual edits
            for key in ["owner", "risk_level", "classification", "maintenance"]:
                if key in existing_workflow:
                    merged[key] = existing_workflow[key]
        merged_workflows.append(merged)
    
    # Add workflows that exist in existing but not in new (deprecated workflows)
    for workflow_id, existing_workflow in existing_workflows.items():
        if workflow_id not in new_workflows:
            existing_workflow["status"] = "deprecated"
            merged_workflows.append(existing_workflow)
    
    new["catalog"]["workflows"] = merged_workflows
    new["catalog"]["total_workflows"] = len(merged_workflows)
    
    return new


def save_catalog(catalog: Dict[str, Any]):
    """Save catalog to YAML file."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(catalog, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    
    print(f"Catalog generated: {CATALOG_FILE}")
    print(f"Total workflows: {catalog.get('catalog', {}).get('total_workflows', 0)}")


def main():
    parser = argparse.ArgumentParser(description="Generate workflows catalog")
    parser.add_argument(
        "--update-ownership",
        action="store_true",
        help="Also update ownership.yaml (not implemented yet)"
    )
    args = parser.parse_args()
    
    print("Scanning workflow files...")
    workflows = scan_workflows()
    
    if not workflows:
        print("Warning: No workflows found")
        return
    
    print(f"Found {len(workflows)} workflows")
    
    # Generate new catalog
    new_catalog = generate_catalog(workflows)
    
    # Load and merge with existing
    existing_catalog = load_existing_catalog()
    merged_catalog = merge_catalog_updates(existing_catalog, new_catalog)
    
    # Save catalog
    save_catalog(merged_catalog)
    
    if args.update_ownership:
        print("Note: --update-ownership not yet implemented")
    
    print("Catalog generation complete")


if __name__ == "__main__":
    main()

