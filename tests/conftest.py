"""
Pytest configuration and shared fixtures for Automation Hub tests.
"""
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Base paths
REPO_ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = REPO_ROOT / "shared" / "schemas"
JS_SNIPPETS_DIR = REPO_ROOT / "shared" / "js_snippets"
CONFIG_DIR = REPO_ROOT / "shared" / "config"
WORKFLOWS_DIR = REPO_ROOT / "workflows"
RULES_DIR = REPO_ROOT / ".cursor" / "rules"


@pytest.fixture
def repo_root():
    """Return repository root path."""
    return REPO_ROOT


@pytest.fixture
def schemas_dir():
    """Return schemas directory path."""
    return SCHEMAS_DIR


@pytest.fixture
def js_snippets_dir():
    """Return JS snippets directory path."""
    return JS_SNIPPETS_DIR


@pytest.fixture
def config_dir():
    """Return config directory path."""
    return CONFIG_DIR


@pytest.fixture
def workflows_dir():
    """Return workflows directory path."""
    return WORKFLOWS_DIR


@pytest.fixture
def rules_dir():
    """Return rules directory path."""
    return RULES_DIR


@pytest.fixture
def mock_n8n_api():
    """Mock n8n API client."""
    mock = MagicMock()
    mock.get_workflow.return_value = {"id": "test-workflow", "name": "Test Workflow"}
    mock.create_workflow.return_value = {"id": "new-workflow", "name": "New Workflow"}
    mock.update_workflow.return_value = {"id": "updated-workflow", "name": "Updated Workflow"}
    mock.delete_workflow.return_value = True
    return mock


@pytest.fixture
def mock_aws_secrets_manager():
    """Mock AWS Secrets Manager client."""
    mock = MagicMock()
    mock.get_secret_value.return_value = {
        "SecretString": json.dumps({"api_key": "test-api-key", "webhook_url": "https://test.slack.com/webhook"})
    }
    return mock


@pytest.fixture
def mock_prometheus():
    """Mock Prometheus Push Gateway."""
    mock = MagicMock()
    mock.push_to_gateway.return_value = True
    return mock


@pytest.fixture
def mock_slack():
    """Mock Slack API."""
    mock = MagicMock()
    mock.post_message.return_value = {"ok": True, "ts": "1234567890.123456"}
    return mock


@pytest.fixture
def mock_github_actions_env():
    """Mock GitHub Actions environment variables."""
    with patch.dict('os.environ', {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REPOSITORY': 'test/repo',
        'GITHUB_REF': 'refs/heads/main',
        'GITHUB_SHA': 'abc123def456',
        'GITHUB_WORKFLOW': 'test-workflow',
        'GITHUB_RUN_ID': '123456789'
    }):
        yield


@pytest.fixture
def valid_event_payload():
    """Valid event schema payload."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "type": "contact.created",
        "source": "n8n",
        "env": "dev",
        "timestamp": "2025-11-20T10:00:00Z",
        "correlation_id": "corr-123",
        "payload": {"contact_id": "contact-123"},
        "meta": {
            "tags": ["crm", "contact"],
            "version": "v1"
        }
    }


@pytest.fixture
def valid_contact_payload():
    """Valid contact schema payload."""
    return {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Example Corp",
        "phone": "+1234567890",
        "status": "new",
        "source": "website",
        "tags": ["lead", "qualified"],
        "created_at": "2025-11-20T10:00:00Z"
    }


@pytest.fixture
def valid_incident_payload():
    """Valid incident schema payload."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "source": "n8n",
        "severity": "high",
        "status": "open",
        "event_type": "workflow.error",
        "error": {
            "message": "Workflow execution failed",
            "type": "ValidationError"
        },
        "context": {
            "env": "dev",
            "service": "n8n",
            "correlation_id": "corr-123"
        },
        "created_at": "2025-11-20T10:00:00Z"
    }


@pytest.fixture
def valid_infra_deploy_payload():
    """Valid infra_deploy schema payload."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "deployment_type": "terraform",
        "environment": "dev",
        "status": "in_progress",
        "triggered_by": {
            "type": "github_action",
            "source": "run-123",
            "commit_sha": "abc123def456"
        },
        "created_at": "2025-11-20T10:00:00Z"
    }

