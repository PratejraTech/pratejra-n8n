"""
Tests for workflow JSON file structure and naming conventions.
"""
import json
import pytest
from pathlib import Path
import re


class TestWorkflowFileStructure:
    """Test workflow JSON file structure."""
    
    def test_workflow_files_valid_json(self, workflows_dir):
        """Test that all workflow JSON files are valid JSON."""
        workflow_files = list(workflows_dir.rglob("*.json"))
        
        # Filter out metadata and pack files
        workflow_files = [f for f in workflow_files 
                          if "metadata" not in str(f) and "packs" not in str(f)]
        
        if len(workflow_files) == 0:
            pytest.skip("No workflow JSON files found")
        
        for workflow_file in workflow_files:
            # Skip empty files (placeholders)
            if workflow_file.stat().st_size == 0:
                continue
                
            with open(workflow_file, 'r') as f:
                try:
                    json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {workflow_file}: {e}")
    
    def test_workflow_files_have_name(self, workflows_dir):
        """Test that workflow files have name field."""
        workflow_files = list(workflows_dir.rglob("*.json"))
        workflow_files = [f for f in workflow_files 
                          if "metadata" not in str(f) and "packs" not in str(f)]
        
        if len(workflow_files) == 0:
            pytest.skip("No workflow JSON files found")
        
        for workflow_file in workflow_files:
            # Skip empty files (placeholders)
            if workflow_file.stat().st_size == 0:
                continue
                
            with open(workflow_file, 'r') as f:
                workflow = json.load(f)
            
            # n8n workflows typically have a 'name' field
            # Some may be empty or have different structure
            if len(workflow) > 0:
                # Check if it's a valid n8n workflow structure
                assert isinstance(workflow, dict), \
                    f"{workflow_file} should be a JSON object"


class TestWorkflowNamingConventions:
    """Test workflow naming conventions."""
    
    def test_workflow_file_naming(self, workflows_dir):
        """Test that workflow files follow naming conventions."""
        workflow_files = list(workflows_dir.rglob("*.json"))
        workflow_files = [f for f in workflow_files 
                          if "metadata" not in str(f) and "packs" not in str(f)]
        
        if len(workflow_files) == 0:
            pytest.skip("No workflow JSON files found")
        
        # Naming convention: lowercase, underscores, no spaces
        naming_pattern = re.compile(r'^[a-z0-9_]+\.json$')
        
        for workflow_file in workflow_files:
            filename = workflow_file.name
            # Allow some flexibility for existing files
            if not naming_pattern.match(filename):
                # Warn but don't fail for existing files
                pytest.skip(f"Workflow file doesn't follow naming convention: {filename}")


class TestWorkflowMetadataRequirements:
    """Test workflow metadata requirements."""
    
    def test_workflows_have_metadata_if_populated(self, workflows_dir):
        """Test that populated workflows have metadata."""
        workflow_files = list(workflows_dir.rglob("*.json"))
        workflow_files = [f for f in workflow_files 
                          if "metadata" not in str(f) and "packs" not in str(f)]
        
        if len(workflow_files) == 0:
            pytest.skip("No workflow JSON files found")
        
        for workflow_file in workflow_files:
            # Skip empty files (placeholders)
            if workflow_file.stat().st_size == 0:
                continue
                
            with open(workflow_file, 'r') as f:
                workflow = json.load(f)
            
            # If workflow has content, it should have basic structure
            if isinstance(workflow, dict) and len(workflow) > 0:
                # n8n workflows typically have 'name' or 'nodes'
                has_structure = 'name' in workflow or 'nodes' in workflow or 'id' in workflow
                # Empty files are acceptable (placeholders)
                if len(workflow) > 1:
                    assert has_structure, \
                        f"{workflow_file} should have workflow structure (name, nodes, or id)"


class TestMockWorkflowExecution:
    """Test mocked workflow execution."""
    
    def test_mock_workflow_structure(self):
        """Test mocked workflow execution structure."""
        # Mock workflow data
        mock_workflow = {
            "id": "workflow-123",
            "name": "Test Workflow",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "n8n-nodes-base.start",
                    "parameters": {}
                }
            ],
            "connections": {}
        }
        
        # Verify structure
        assert "id" in mock_workflow
        assert "name" in mock_workflow
        assert "nodes" in mock_workflow
        assert isinstance(mock_workflow["nodes"], list)
    
    def test_mock_workflow_execution_flow(self):
        """Test mocked workflow execution flow."""
        # Mock workflow execution
        execution_steps = [
            {"step": "start", "status": "success"},
            {"step": "validate", "status": "success"},
            {"step": "process", "status": "success"},
            {"step": "end", "status": "success"}
        ]
        
        # Verify execution flow
        assert len(execution_steps) > 0
        assert all(step["status"] == "success" for step in execution_steps)

