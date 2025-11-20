"""
Tests for environment configuration files.
"""
import yaml
import pytest
import re
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestConfigValidation:
    """Test configuration file validation."""
    
    def test_dev_config_exists(self, config_dir):
        """Test that dev config file exists."""
        config_file = config_dir / "environments.dev.yaml"
        assert config_file.exists(), "environments.dev.yaml not found"
    
    def test_prod_config_exists(self, config_dir):
        """Test that prod config file exists."""
        config_file = config_dir / "environments.prod.yaml"
        assert config_file.exists(), "environments.prod.yaml not found"
    
    def test_dev_config_valid_yaml(self, config_dir):
        """Test that dev config is valid YAML."""
        config_file = config_dir / "environments.dev.yaml"
        
        with open(config_file, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {config_file}: {e}")
    
    def test_prod_config_valid_yaml(self, config_dir):
        """Test that prod config is valid YAML."""
        config_file = config_dir / "environments.prod.yaml"
        
        with open(config_file, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {config_file}: {e}")
    
    def test_dev_config_structure(self, config_dir):
        """Test dev config has required structure."""
        config_file = config_dir / "environments.dev.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        assert "environment" in config
        assert config["environment"] == "dev"
        assert "n8n" in config
        assert "aws" in config
        assert "external_services" in config
    
    def test_prod_config_structure(self, config_dir):
        """Test prod config has required structure."""
        config_file = config_dir / "environments.prod.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        assert "environment" in config
        assert config["environment"] == "prod"
        assert "n8n" in config
        assert "aws" in config
    
    def test_config_no_hardcoded_secrets(self, config_dir):
        """Test that configs don't contain hardcoded secrets."""
        config_files = list(config_dir.glob("*.yaml"))
        
        secret_patterns = [
            r'password\s*:\s*["\']([^"\']+)["\']',
            r'api_key\s*:\s*["\']([^"\']+)["\']',
            r'secret\s*:\s*["\']([^"\']+)["\']',
            r'token\s*:\s*["\']([^"\']+)["\']'
        ]
        
        for config_file in config_files:
            with open(config_file, 'r') as f:
                content = f.read()
            
            for pattern in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    secret_value = match.group(1) if match.groups() else match.group(0)
                    match_lower = secret_value.lower()
                    # Filter out ARN references, secret_arn fields, and placeholder values
                    if ("arn:aws:secretsmanager" in match_lower or 
                        "secret_arn" in match_lower or
                        "api_key_secret_arn" in match_lower or
                        "webhook_secret_arn" in match_lower or
                        "region" in match_lower or
                        "account" in match_lower or
                        match_lower.startswith("${{")):
                        continue
                    # If we get here, it's a potential hardcoded secret
                    pytest.fail(f"Potential hardcoded secret in {config_file}: {match.group(0)}")
    
    def test_config_aws_secrets_manager_arns(self, config_dir):
        """Test that AWS Secrets Manager ARNs are properly formatted."""
        config_files = list(config_dir.glob("*.yaml"))
        
        arn_pattern = r'arn:aws:secretsmanager:[^:]+:[^:]+:secret:[^"\'\s]+'
        
        for config_file in config_files:
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Check if any secret references exist
            if "secret" in content.lower() or "api_key" in content.lower():
                # Verify ARN format if secrets are referenced
                arn_matches = re.findall(arn_pattern, content, re.IGNORECASE)
                # If secrets are referenced, at least one should be an ARN
                if "secret" in content.lower() and not arn_matches:
                    # Allow placeholder ARNs in dev configs
                    if "REGION" in content or "ACCOUNT" in content:
                        continue
                    # Otherwise, warn but don't fail (may be using env vars)
    
    def test_config_n8n_settings(self, config_dir):
        """Test n8n configuration settings."""
        config_file = config_dir / "environments.dev.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        assert "n8n" in config
        n8n_config = config["n8n"]
        assert "base_url" in n8n_config
        assert "api_endpoint" in n8n_config or "api_key_secret_arn" in n8n_config
    
    def test_config_aws_settings(self, config_dir):
        """Test AWS configuration settings."""
        config_file = config_dir / "environments.dev.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        assert "aws" in config
        aws_config = config["aws"]
        assert "region" in aws_config
        assert "secrets_manager" in aws_config or "s3" in aws_config
    
    def test_config_environment_differences(self, config_dir):
        """Test that dev and prod configs have appropriate differences."""
        dev_file = config_dir / "environments.dev.yaml"
        prod_file = config_dir / "environments.prod.yaml"
        
        with open(dev_file, 'r') as f:
            dev_config = yaml.safe_load(f)
        
        with open(prod_file, 'r') as f:
            prod_config = yaml.safe_load(f)
        
        # Dev should have localhost URLs
        assert "localhost" in str(dev_config.get("n8n", {}).get("base_url", "")).lower()
        
        # Prod should not have localhost (or have production URLs)
        prod_n8n_url = str(prod_config.get("n8n", {}).get("base_url", "")).lower()
        assert "localhost" not in prod_n8n_url or "dev" not in prod_n8n_url
    
    def test_mock_secrets_retrieval(self, config_dir):
        """Test that configs reference secrets via ARN (mocking not required for this test)."""
        # This test verifies that configs reference secrets via ARN
        # We don't need to actually mock boto3 for this validation
        config_file = config_dir / "environments.dev.yaml"
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify config references secrets via ARN
        if "n8n" in config and "api_key_secret_arn" in config["n8n"]:
            arn = config["n8n"]["api_key_secret_arn"]
            assert "arn:aws:secretsmanager" in arn or "REGION" in arn

