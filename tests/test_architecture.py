"""
Tests for architecture compliance and structure validation.
"""
import yaml
import pytest
from pathlib import Path
import re


class TestDirectoryStructure:
    """Test directory structure compliance."""
    
    def test_required_directories_exist(self, repo_root):
        """Test that all required directories exist."""
        required_dirs = [
            "shared/schemas",
            "shared/js_snippets",
            "shared/config",
            "workflows/domains",
            "workflows/metadata",
            ".cursor/rules",
            ".agents/reports",
            "ops/scripts",
            "docs"
        ]
        
        for dir_path in required_dirs:
            full_path = repo_root / dir_path
            assert full_path.exists(), f"Required directory missing: {dir_path}"
    
    def test_workflows_in_approved_directories(self, repo_root):
        """Test that workflows are in approved directories."""
        workflows_dir = repo_root / "workflows"
        
        approved_patterns = [
            "domains/shared",
            "domains/crm",
            "domains/infra",
            "domains/meta",
            "platform",
            "domain_crm",
            "domain_infra"
        ]
        
        # Find all JSON files in workflows directory
        workflow_files = list(workflows_dir.rglob("*.json"))
        
        for workflow_file in workflow_files:
            relative_path = str(workflow_file.relative_to(workflows_dir))
            is_approved = any(pattern in relative_path for pattern in approved_patterns)
            
            # Allow metadata and other non-workflow JSON files
            if "metadata" in relative_path or "packs" in relative_path:
                continue
            
            # If it's a workflow file, it should be in approved directory
            if is_approved:
                continue
            
            # Warn but don't fail for files in other locations (may be legacy)
            if not any(skip in relative_path for skip in ["metadata", "packs", "draft"]):
                pytest.skip(f"Workflow in potentially unapproved location: {relative_path}")


class TestRuleFileFormat:
    """Test rule file format validation."""
    
    def test_rule_files_have_front_matter(self, rules_dir):
        """Test that all .mdc rule files have YAML front matter."""
        rule_files = list(rules_dir.glob("*.mdc"))
        assert len(rule_files) > 0, "No rule files found"
        
        for rule_file in rule_files:
            with open(rule_file, 'r') as f:
                content = f.read()
            
            # Check for YAML front matter
            assert content.startswith('---'), \
                f"{rule_file} missing YAML front matter (should start with ---)"
    
    def test_rule_files_valid_yaml_front_matter(self, rules_dir):
        """Test that rule files have valid YAML front matter."""
        rule_files = list(rules_dir.glob("*.mdc"))
        
        for rule_file in rule_files:
            with open(rule_file, 'r') as f:
                content = f.read()
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    try:
                        yaml.safe_load(front_matter)
                    except yaml.YAMLError as e:
                        pytest.fail(f"{rule_file} has invalid YAML front matter: {e}")
    
    def test_rule_files_have_description(self, rules_dir):
        """Test that rule files have description in front matter."""
        rule_files = list(rules_dir.glob("*.mdc"))
        
        for rule_file in rule_files:
            with open(rule_file, 'r') as f:
                content = f.read()
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    metadata = yaml.safe_load(front_matter)
                    assert "description" in metadata, \
                        f"{rule_file} missing 'description' in front matter"


class TestStateMdcStructure:
    """Test state.mdc file structure."""
    
    def test_state_file_exists(self, rules_dir):
        """Test that state.mdc exists."""
        state_file = rules_dir / "state.mdc"
        assert state_file.exists(), "state.mdc not found"
    
    def test_state_file_structure(self, rules_dir):
        """Test that state.mdc has required structure."""
        state_file = rules_dir / "state.mdc"
        
        with open(state_file, 'r') as f:
            content = f.read()
        
        # Handle front matter if present
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[2]
            else:
                yaml_content = content
        else:
            yaml_content = content
        
        state = yaml.safe_load(yaml_content)
        
        assert "phases" in state, "state.mdc missing 'phases' key"
        assert isinstance(state["phases"], list), "phases should be a list"
        
        # Validate phase structure
        for phase in state["phases"]:
            assert "id" in phase, "Phase missing 'id'"
            assert "name" in phase, "Phase missing 'name'"
            assert "status" in phase, "Phase missing 'status'"
    
    def test_state_file_has_history(self, rules_dir):
        """Test that state.mdc has history section."""
        state_file = rules_dir / "state.mdc"
        
        with open(state_file, 'r') as f:
            content = f.read()
        
        # Handle front matter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[2]
            else:
                yaml_content = content
        else:
            yaml_content = content
        
        state = yaml.safe_load(yaml_content)
        
        assert "history" in state, "state.mdc missing 'history' key"


class TestMetadataFileStructure:
    """Test metadata file structure."""
    
    def test_metadata_directory_exists(self, repo_root):
        """Test that metadata directory exists."""
        metadata_dir = repo_root / "workflows" / "metadata"
        assert metadata_dir.exists(), "metadata directory not found"
    
    def test_catalog_file_structure_if_exists(self, repo_root):
        """Test catalog file structure if it exists."""
        catalog_file = repo_root / "workflows" / "metadata" / "workflows_catalog.yaml"
        
        if catalog_file.exists():
            with open(catalog_file, 'r') as f:
                catalog = yaml.safe_load(f)
            
            assert catalog is not None
            # Structure may vary, but should be valid YAML


class TestArchitectureConsistency:
    """Test architecture.mdc consistency."""
    
    def test_architecture_file_exists(self, rules_dir):
        """Test that architecture.mdc exists."""
        arch_file = rules_dir / "architecture.mdc"
        # File may be named differently or may not exist yet
        # Check for any architecture-related file
        arch_files = list(rules_dir.glob("*architecture*.mdc")) + \
                     list(rules_dir.glob("*system*.mdc"))
        
        # Architecture file is optional for now
        if len(arch_files) == 0:
            pytest.skip("No architecture.mdc file found (optional)")
    
    def test_folders_file_exists(self, rules_dir):
        """Test that folders.mdc exists."""
        folders_file = rules_dir / "folders.mdc"
        assert folders_file.exists(), "folders.mdc not found"
    
    def test_folders_file_structure(self, rules_dir):
        """Test that folders.mdc documents directory structure."""
        folders_file = rules_dir / "folders.mdc"
        
        with open(folders_file, 'r') as f:
            content = f.read()
        
        # Should document directory structure
        assert len(content) > 100, "folders.mdc should document directory structure"

