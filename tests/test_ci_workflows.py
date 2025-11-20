"""
Tests for CI/CD GitHub Actions workflows.
"""
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestWorkflowYAMLSyntax:
    """Test GitHub Actions workflow YAML syntax."""
    
    def test_validate_workflows_yaml_exists(self, repo_root):
        """Test that validate-workflows.yml exists."""
        workflow_file = repo_root / ".github" / "workflows" / "validate-workflows.yml"
        assert workflow_file.exists(), "validate-workflows.yml not found"
    
    def test_deploy_workflows_yaml_exists(self, repo_root):
        """Test that deploy-workflows.yml exists."""
        workflow_file = repo_root / ".github" / "workflows" / "deploy-workflows.yml"
        assert workflow_file.exists(), "deploy-workflows.yml not found"
    
    def test_backup_workflow_yaml_exists(self, repo_root):
        """Test that backup-to-s3.yaml exists."""
        workflow_file = repo_root / ".github" / "workflows" / "backup-to-s3.yaml"
        assert workflow_file.exists(), "backup-to-s3.yaml not found"
    
    def test_validate_workflows_valid_yaml(self, repo_root):
        """Test that validate-workflows.yml is valid YAML."""
        workflow_file = repo_root / ".github" / "workflows" / "validate-workflows.yml"
        
        with open(workflow_file, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {workflow_file}: {e}")
    
    def test_deploy_workflows_valid_yaml(self, repo_root):
        """Test that deploy-workflows.yml is valid YAML."""
        workflow_file = repo_root / ".github" / "workflows" / "deploy-workflows.yml"
        
        with open(workflow_file, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {workflow_file}: {e}")
    
    def test_backup_workflow_valid_yaml(self, repo_root):
        """Test that backup-to-s3.yaml is valid YAML."""
        workflow_file = repo_root / ".github" / "workflows" / "backup-to-s3.yaml"
        
        with open(workflow_file, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {workflow_file}: {e}")


class TestWorkflowStructure:
    """Test workflow structure and required fields."""
    
    def test_validate_workflows_structure(self, repo_root):
        """Test validate-workflows.yml has required structure."""
        workflow_file = repo_root / ".github" / "workflows" / "validate-workflows.yml"
        
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        assert "name" in workflow
        # YAML parser may convert 'on' to boolean True, so check for either
        assert "on" in workflow or True in workflow or workflow.get("on") is not None
        assert "jobs" in workflow
    
    def test_deploy_workflows_structure(self, repo_root):
        """Test deploy-workflows.yml has required structure."""
        workflow_file = repo_root / ".github" / "workflows" / "deploy-workflows.yml"
        
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        assert "name" in workflow
        # YAML parser may convert 'on' to boolean True, so check for either
        assert "on" in workflow or True in workflow or workflow.get("on") is not None
        assert "jobs" in workflow
    
    def test_backup_workflow_structure(self, repo_root):
        """Test backup-to-s3.yaml has required structure."""
        workflow_file = repo_root / ".github" / "workflows" / "backup-to-s3.yaml"
        
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        assert "name" in workflow
        # YAML parser may convert 'on' to boolean True, so check for either
        assert "on" in workflow or True in workflow or workflow.get("on") is not None
        assert "jobs" in workflow


class TestWorkflowSteps:
    """Test workflow steps and actions."""
    
    def test_validate_workflows_has_checkout(self, repo_root):
        """Test validate-workflows.yml has checkout step."""
        workflow_file = repo_root / ".github" / "workflows" / "validate-workflows.yml"
        
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Check if any job has checkout action
        has_checkout = False
        for job_name, job in workflow.get("jobs", {}).items():
            for step in job.get("steps", []):
                if "uses" in step and "checkout" in step["uses"]:
                    has_checkout = True
                    break
        
        assert has_checkout, "Workflow should have checkout step"
    
    def test_validate_workflows_has_python_setup(self, repo_root):
        """Test validate-workflows.yml has Python setup."""
        workflow_file = repo_root / ".github" / "workflows" / "validate-workflows.yml"
        
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Check if any job has Python setup
        has_python = False
        for job_name, job in workflow.get("jobs", {}).items():
            for step in job.get("steps", []):
                if "uses" in step and "setup-python" in step["uses"]:
                    has_python = True
                    break
        
        assert has_python, "Workflow should have Python setup step"
    
    def test_deploy_workflows_has_deployment_steps(self, repo_root):
        """Test deploy-workflows.yml has deployment-related steps."""
        workflow_file = repo_root / ".github" / "workflows" / "deploy-workflows.yml"
        
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Check for deployment-related content
        workflow_str = yaml.dump(workflow)
        assert "deploy" in workflow_str.lower() or "import" in workflow_str.lower() or "n8n" in workflow_str.lower()


class TestWorkflowValidationLogic:
    """Test workflow validation logic."""
    
    def test_validate_workflows_has_validation_jobs(self, repo_root):
        """Test validate-workflows.yml has validation jobs."""
        workflow_file = repo_root / ".github" / "workflows" / "validate-workflows.yml"
        
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        jobs = workflow.get("jobs", {})
        assert len(jobs) > 0, "Workflow should have at least one job"
        
        # Check for validation-related job names
        job_names = [name.lower() for name in jobs.keys()]
        has_validation = any("valid" in name or "test" in name or "check" in name for name in job_names)
        assert has_validation, "Workflow should have validation jobs"


class TestMockedGitHubActions:
    """Test mocked GitHub Actions environment."""
    
    @patch.dict('os.environ', {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REPOSITORY': 'test/repo',
        'GITHUB_REF': 'refs/heads/main',
        'GITHUB_SHA': 'abc123def456'
    })
    def test_mock_github_actions_env(self):
        """Test that GitHub Actions environment can be mocked."""
        import os
        assert os.environ.get('GITHUB_ACTIONS') == 'true'
        assert os.environ.get('GITHUB_REPOSITORY') == 'test/repo'
        assert os.environ.get('GITHUB_REF') == 'refs/heads/main'

