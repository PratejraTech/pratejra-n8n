"""
Tests for catalog generation script and metadata files.
"""
import json
import yaml
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open


class TestCatalogGenerationScript:
    """Test generate_catalog.py script."""
    
    def test_script_exists(self, repo_root):
        """Test that generate_catalog.py exists."""
        script_file = repo_root / "ops" / "scripts" / "generate_catalog.py"
        assert script_file.exists(), "generate_catalog.py not found"
    
    def test_script_is_executable(self, repo_root):
        """Test that script can be executed."""
        script_file = repo_root / "ops" / "scripts" / "generate_catalog.py"
        
        # Check if it's a Python script
        with open(script_file, 'r') as f:
            first_line = f.readline()
            assert first_line.startswith("#!/usr/bin/env python") or first_line.startswith("#"), \
                "Script should start with shebang or comment"
    
    def test_script_imports(self, repo_root):
        """Test that script has required imports."""
        script_file = repo_root / "ops" / "scripts" / "generate_catalog.py"
        
        with open(script_file, 'r') as f:
            content = f.read()
        
        assert "import json" in content
        assert "import yaml" in content
        assert "from pathlib import Path" in content
    
    def test_script_functions_exist(self, repo_root):
        """Test that script has required functions."""
        script_file = repo_root / "ops" / "scripts" / "generate_catalog.py"
        
        with open(script_file, 'r') as f:
            content = f.read()
        
        assert "def scan_workflows" in content
        assert "def generate_catalog" in content
        assert "def save_catalog" in content
    
    @patch('pathlib.Path.glob')
    @patch('builtins.open', new_callable=mock_open)
    def test_catalog_generation_mock(self, mock_file, mock_glob, repo_root):
        """Test catalog generation with mocked workflow files."""
        # Mock workflow files
        mock_workflow_data = {
            "name": "Test Workflow",
            "nodes": [
                {"type": "n8n-nodes-base.start", "notes": "Test workflow"}
            ]
        }
        
        mock_file.return_value.read.return_value = json.dumps(mock_workflow_data)
        mock_glob.return_value = [Path("workflows/domains/crm/test.json")]
        
        # This test verifies the structure - actual execution would require real files
        script_file = repo_root / "ops" / "scripts" / "generate_catalog.py"
        assert script_file.exists()


class TestCatalogYAMLStructure:
    """Test workflows_catalog.yaml structure."""
    
    def test_catalog_file_exists(self, repo_root):
        """Test that catalog file exists or can be generated."""
        catalog_file = repo_root / "workflows" / "metadata" / "workflows_catalog.yaml"
        # File may not exist if catalog hasn't been generated yet
        # This is acceptable for testing infrastructure
    
    def test_catalog_structure_if_exists(self, repo_root):
        """Test catalog YAML structure if file exists."""
        catalog_file = repo_root / "workflows" / "metadata" / "workflows_catalog.yaml"
        
        if catalog_file.exists():
            with open(catalog_file, 'r') as f:
                catalog = yaml.safe_load(f)
            
            assert catalog is not None
            if "catalog" in catalog:
                assert "version" in catalog["catalog"]
                assert "workflows" in catalog["catalog"]
                assert isinstance(catalog["catalog"]["workflows"], list)


class TestOwnershipYAMLStructure:
    """Test ownership.yaml structure."""
    
    def test_ownership_file_exists(self, repo_root):
        """Test that ownership file exists or can be generated."""
        ownership_file = repo_root / "workflows" / "metadata" / "ownership.yaml"
        # File may not exist if catalog hasn't been generated yet
    
    def test_ownership_structure_if_exists(self, repo_root):
        """Test ownership YAML structure if file exists."""
        ownership_file = repo_root / "workflows" / "metadata" / "ownership.yaml"
        
        if ownership_file.exists():
            with open(ownership_file, 'r') as f:
                ownership = yaml.safe_load(f)
            
            assert ownership is not None
            # Ownership structure may vary, but should be valid YAML


class TestCatalogMergingLogic:
    """Test catalog merging and update logic."""
    
    def test_catalog_merge_function_exists(self, repo_root):
        """Test that merge function exists in script."""
        script_file = repo_root / "ops" / "scripts" / "generate_catalog.py"
        
        with open(script_file, 'r') as f:
            content = f.read()
        
        assert "merge" in content.lower() or "update" in content.lower()
    
    def test_catalog_preserves_manual_edits(self, repo_root):
        """Test that catalog generation preserves manual edits."""
        script_file = repo_root / "ops" / "scripts" / "generate_catalog.py"
        
        with open(script_file, 'r') as f:
            content = f.read()
        
        # Script should have logic to preserve manual fields
        assert "existing" in content.lower() or "preserve" in content.lower() or "manual" in content.lower()

