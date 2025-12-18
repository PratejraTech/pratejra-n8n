"""
Tests for n8n GitOps scripts (n8n_gitops.py, n8n_gitops_webhooks.py, n8n_gitops_common.py).
"""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add ops/scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "ops" / "scripts"))

try:
    import n8n_gitops_common
except ImportError:
    pytest.skip("n8n_gitops_common module not found", allow_module_level=True)


class TestGitOpsCommon:
    """Test shared GitOps common functions."""
    
    def test_normalize_workflow_json_removes_volatile_fields(self):
        """Test that normalize_workflow_json removes volatile fields."""
        workflow = {
            "id": "123",
            "name": "Test Workflow",
            "active": True,
            "createdAt": "2025-01-01T00:00:00Z",
            "updatedAt": "2025-01-02T00:00:00Z",
            "versionId": "v1",
            "nodes": [{"id": "node-1", "type": "start"}],
            "connections": {}
        }
        
        normalized = n8n_gitops_common.normalize_workflow_json(workflow)
        
        assert "id" not in normalized
        assert "active" not in normalized
        assert "createdAt" not in normalized
        assert "updatedAt" not in normalized
        assert "versionId" not in normalized
        assert "name" in normalized
        assert "nodes" in normalized
    
    def test_normalize_workflow_json_removes_node_ids(self):
        """Test that normalize_workflow_json removes node IDs."""
        workflow = {
            "name": "Test",
            "nodes": [
                {"id": "node-1", "type": "start", "parameters": {}},
                {"id": "node-2", "type": "code", "parameters": {}}
            ],
            "connections": {}
        }
        
        normalized = n8n_gitops_common.normalize_workflow_json(workflow)
        
        assert all("id" not in node for node in normalized["nodes"])
        assert len(normalized["nodes"]) == 2
    
    def test_normalize_workflow_json_strips_metadata_when_requested(self):
        """Test that normalize_workflow_json can strip _metadata."""
        workflow = {
            "name": "Test",
            "_metadata": {"purpose": "test"},
            "nodes": [],
            "connections": {}
        }
        
        normalized_with_metadata = n8n_gitops_common.normalize_workflow_json(workflow, strip_metadata=False)
        assert "_metadata" in normalized_with_metadata
        
        normalized_stripped = n8n_gitops_common.normalize_workflow_json(workflow, strip_metadata=True)
        assert "_metadata" not in normalized_stripped
    
    def test_find_remote_by_name(self):
        """Test finding workflow by name in remote list."""
        remote_list = [
            {"id": "1", "name": "Workflow A"},
            {"id": "2", "name": "Workflow B"},
            {"id": "3", "name": "Workflow C"}
        ]
        
        result = n8n_gitops_common._find_remote_by_name(remote_list, "Workflow B")
        assert result is not None
        assert result["id"] == "2"
        assert result["name"] == "Workflow B"
        
        result_not_found = n8n_gitops_common._find_remote_by_name(remote_list, "Workflow X")
        assert result_not_found is None
    
    def test_find_remote_by_name_handles_whitespace(self):
        """Test that find_remote_by_name handles whitespace in names."""
        remote_list = [
            {"id": "1", "name": "  Workflow A  "},
            {"id": "2", "name": "Workflow B"}
        ]
        
        result = n8n_gitops_common._find_remote_by_name(remote_list, "Workflow A")
        assert result is not None
        assert result["id"] == "1"
    
    def test_n8n_headers(self):
        """Test n8n API header generation."""
        api_key = "test-api-key"
        headers = n8n_gitops_common._n8n_headers(api_key)
        
        assert "X-N8N-API-KEY" in headers
        assert headers["X-N8N-API-KEY"] == api_key
        assert headers["Accept"] == "application/json"


class TestWorkflowJSONValidation:
    """Test workflow JSON validation."""
    
    def test_valid_workflow_structure(self):
        """Test that valid workflow JSON structure is recognized."""
        valid_workflow = {
            "name": "Test Workflow",
            "nodes": [
                {"type": "n8n-nodes-base.start", "parameters": {}}
            ],
            "connections": {}
        }
        
        # Should not raise
        normalized = n8n_gitops_common.normalize_workflow_json(valid_workflow)
        assert "name" in normalized
        assert "nodes" in normalized
    
    def test_workflow_with_credentials(self):
        """Test workflow with credentials is normalized correctly."""
        workflow = {
            "name": "Test",
            "nodes": [
                {
                    "type": "http",
                    "credentials": {
                        "httpBasicAuth": {
                            "id": "cred-123",
                            "name": "Basic Auth"
                        }
                    }
                }
            ],
            "connections": {}
        }
        
        normalized = n8n_gitops_common.normalize_workflow_json(workflow)
        
        # Credential IDs should be removed
        node = normalized["nodes"][0]
        if "credentials" in node:
            for cred_name, cred_obj in node["credentials"].items():
                if isinstance(cred_obj, dict):
                    assert "id" not in cred_obj


class TestGitOpsFileOperations:
    """Test file I/O operations."""
    
    def test_write_and_read_json(self, tmp_path):
        """Test writing and reading JSON files."""
        test_file = tmp_path / "test.json"
        test_data = {
            "name": "Test",
            "value": 123,
            "nested": {"key": "value"}
        }
        
        n8n_gitops_common._write_json(test_file, test_data)
        assert test_file.exists()
        
        read_data = n8n_gitops_common._read_json(test_file)
        assert read_data == test_data
    
    def test_write_json_creates_directory(self, tmp_path):
        """Test that _write_json creates parent directories."""
        test_file = tmp_path / "subdir" / "nested" / "test.json"
        test_data = {"test": "data"}
        
        n8n_gitops_common._write_json(test_file, test_data)
        assert test_file.exists()
        assert test_file.parent.exists()


class TestWorkflowNormalizationConsistency:
    """Test that workflow normalization is consistent."""
    
    def test_normalization_is_deterministic(self):
        """Test that normalization produces consistent results."""
        workflow = {
            "id": "123",
            "name": "Test",
            "active": True,
            "createdAt": "2025-01-01T00:00:00Z",
            "nodes": [{"id": "node-1", "type": "start"}],
            "connections": {}
        }
        
        result1 = n8n_gitops_common.normalize_workflow_json(workflow)
        result2 = n8n_gitops_common.normalize_workflow_json(workflow)
        
        # Results should be identical
        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)
    
    def test_normalization_preserves_structure(self):
        """Test that normalization preserves workflow structure."""
        workflow = {
            "name": "Test Workflow",
            "nodes": [
                {"type": "start", "parameters": {"key": "value"}},
                {"type": "code", "parameters": {"code": "return {};"}}
            ],
            "connections": {
                "start": {"main": [[{"node": "code", "type": "main", "index": 0}]]}
            },
            "settings": {"executionOrder": "v1"}
        }
        
        normalized = n8n_gitops_common.normalize_workflow_json(workflow)
        
        assert normalized["name"] == workflow["name"]
        assert len(normalized["nodes"]) == len(workflow["nodes"])
        assert "connections" in normalized
        assert "settings" in normalized
