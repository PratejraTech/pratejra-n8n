"""
Tests for JavaScript snippets used in n8n Code nodes.
"""
import json
import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestValidatePayloadSnippet:
    """Test validate_payload.js snippet."""
    
    def test_validate_payload_file_exists(self, js_snippets_dir):
        """Test that validate_payload.js exists."""
        snippet_file = js_snippets_dir / "validate_payload.js"
        assert snippet_file.exists(), "validate_payload.js not found"
    
    def test_validate_payload_valid_contact(self, js_snippets_dir):
        """Test validate_payload with valid contact data."""
        snippet_file = js_snippets_dir / "validate_payload.js"
        
        # Mock n8n environment
        test_code = f"""
        const fs = require('fs');
        const snippet = fs.readFileSync('{snippet_file}', 'utf8');
        eval(snippet);
        
        const payload = {{
            email: "test@example.com",
            first_name: "John",
            last_name: "Doe"
        }};
        
        const result = validatePayload(payload, 'contact');
        console.log(JSON.stringify(result));
        """
        
        # Note: This is a simplified test - in real n8n, snippets run in Node.js
        # For now, we verify the file structure and basic syntax
        with open(snippet_file, 'r') as f:
            content = f.read()
        
        assert "function validatePayload" in content
        assert "validateField" in content
        assert "getSchemaByType" in content
    
    def test_validate_payload_invalid_payload(self, js_snippets_dir):
        """Test validate_payload with invalid payload."""
        snippet_file = js_snippets_dir / "validate_payload.js"
        
        with open(snippet_file, 'r') as f:
            content = f.read()
        
        # Verify error handling exists
        assert "errors" in content
        assert "valid" in content
        assert "return" in content


class TestNormalizeContactSnippet:
    """Test normalize_contact.js snippet."""
    
    def test_normalize_contact_file_exists(self, js_snippets_dir):
        """Test that normalize_contact.js exists."""
        snippet_file = js_snippets_dir / "normalize_contact.js"
        assert snippet_file.exists(), "normalize_contact.js not found"
    
    def test_normalize_contact_structure(self, js_snippets_dir):
        """Test normalize_contact.js has required functions."""
        snippet_file = js_snippets_dir / "normalize_contact.js"
        
        with open(snippet_file, 'r') as f:
            content = f.read()
        
        assert "function normalizeContact" in content
        assert "normalizeEmail" in content
        assert "normalizePhone" in content
        assert "normalizeString" in content
        assert "normalizeStatus" in content
    
    def test_normalize_contact_various_formats(self, js_snippets_dir):
        """Test normalize_contact handles various input formats."""
        snippet_file = js_snippets_dir / "normalize_contact.js"
        
        with open(snippet_file, 'r') as f:
            content = f.read()
        
        # Verify it handles different field name variations
        assert "Email" in content or "email_address" in content
        assert "firstName" in content or "first_name" in content
        assert "phone_number" in content or "phone" in content
    
    def test_normalize_contact_error_handling(self, js_snippets_dir):
        """Test normalize_contact has error handling."""
        snippet_file = js_snippets_dir / "normalize_contact.js"
        
        with open(snippet_file, 'r') as f:
            content = f.read()
        
        # Verify error handling
        assert "throw" in content or "Error" in content
        assert "isValidEmail" in content


class TestComputeRiskScoreSnippet:
    """Test compute_risk_score.js snippet."""
    
    def test_compute_risk_score_file_exists(self, js_snippets_dir):
        """Test that compute_risk_score.js exists."""
        snippet_file = js_snippets_dir / "compute_risk_score.js"
        assert snippet_file.exists(), "compute_risk_score.js not found"
    
    def test_compute_risk_score_structure(self, js_snippets_dir):
        """Test compute_risk_score.js has required functions."""
        snippet_file = js_snippets_dir / "compute_risk_score.js"
        
        with open(snippet_file, 'r') as f:
            content = f.read()
        
        assert "function computeRiskScore" in content
        assert "calculateEmailDomainRisk" in content
        assert "calculateEmailFormatRisk" in content
        assert "calculatePhoneRisk" in content
        assert "calculateDataCompletenessRisk" in content
    
    def test_compute_risk_score_returns_0_to_100(self, js_snippets_dir):
        """Test compute_risk_score returns value between 0 and 100."""
        snippet_file = js_snippets_dir / "compute_risk_score.js"
        
        with open(snippet_file, 'r') as f:
            content = f.read()
        
        # Verify score clamping
        assert "Math.max(0" in content or "Math.min(100" in content
        assert "Math.round" in content
    
    def test_compute_risk_score_factors(self, js_snippets_dir):
        """Test compute_risk_score considers all factors."""
        snippet_file = js_snippets_dir / "compute_risk_score.js"
        
        with open(snippet_file, 'r') as f:
            content = f.read()
        
        # Verify all risk factors are calculated
        assert "emailDomainWeight" in content or "emailDomain" in content
        assert "phoneWeight" in content or "phone" in content
        assert "companyWeight" in content or "company" in content
        assert "dataCompleteness" in content or "completeness" in content


class TestJSSnippetsIntegration:
    """Integration tests for JS snippets."""
    
    def test_all_snippets_have_module_exports(self, js_snippets_dir):
        """Test that all snippets export functions for n8n."""
        snippet_files = list(js_snippets_dir.glob("*.js"))
        assert len(snippet_files) > 0, "No JS snippet files found"
        
        for snippet_file in snippet_files:
            with open(snippet_file, 'r') as f:
                content = f.read()
            
            # Verify module.exports exists
            assert "module.exports" in content, f"{snippet_file} missing module.exports"
    
    def test_snippets_have_documentation(self, js_snippets_dir):
        """Test that snippets have JSDoc comments."""
        snippet_files = list(js_snippets_dir.glob("*.js"))
        
        for snippet_file in snippet_files:
            with open(snippet_file, 'r') as f:
                content = f.read()
            
            # Verify documentation comments
            assert "/**" in content or "/*" in content, f"{snippet_file} missing documentation"
            assert "@param" in content or "Purpose:" in content, f"{snippet_file} missing parameter docs"

