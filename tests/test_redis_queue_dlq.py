"""
Purpose: Tests for Redis queue DLQ manager
Created/Updated: 2025-01-27
Agent: BACKEND_AGENT

Tests for DLQ retry logic, exponential backoff, and job recovery.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
from datetime import datetime

# Add ops/scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "ops" / "scripts"))


class TestDLQManager:
    """Test DLQ manager functionality."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock = MagicMock()
        mock.ping.return_value = True
        mock.lrange.return_value = ["job-1", "job-2"]
        mock.hgetall.return_value = {
            "id": "job-1",
            "name": "test-workflow",
            "failedReason": "ConnectionError: Connection timeout"
        }
        mock.get.return_value = None
        mock.zcard.return_value = 0
        return mock
    
    def test_calculate_retry_delay(self):
        """Test exponential backoff delay calculation."""
        from redis_queue_dlq_manager import calculate_retry_delay
        
        # Test initial delay
        delay1 = calculate_retry_delay(0, initial_delay=1, max_delay=300, backoff_multiplier=2.0)
        assert delay1 == 1
        
        # Test exponential growth
        delay2 = calculate_retry_delay(1, initial_delay=1, max_delay=300, backoff_multiplier=2.0)
        assert delay2 == 2
        
        delay3 = calculate_retry_delay(2, initial_delay=1, max_delay=300, backoff_multiplier=2.0)
        assert delay3 == 4
        
        # Test max delay cap
        delay_large = calculate_retry_delay(10, initial_delay=1, max_delay=300, backoff_multiplier=2.0)
        assert delay_large == 300
    
    def test_get_retry_metadata(self, mock_redis_client):
        """Test getting retry metadata."""
        with patch('redis_queue_dlq_manager.connect_redis', return_value=mock_redis_client):
            from redis_queue_dlq_manager import get_retry_metadata
            metadata = get_retry_metadata(mock_redis_client, "job-1")
            assert "retry_count" in metadata
            assert metadata["retry_count"] == 0
    
    def test_set_retry_metadata(self, mock_redis_client):
        """Test setting retry metadata."""
        with patch('redis_queue_dlq_manager.connect_redis', return_value=mock_redis_client):
            from redis_queue_dlq_manager import set_retry_metadata
            metadata = {"retry_count": 1, "first_failed_at": datetime.utcnow().isoformat()}
            set_retry_metadata(mock_redis_client, "job-1", metadata)
            mock_redis_client.setex.assert_called_once()
    
    def test_get_failed_jobs(self, mock_redis_client):
        """Test getting failed jobs from queue."""
        with patch('redis_queue_dlq_manager.connect_redis', return_value=mock_redis_client):
            from redis_queue_dlq_manager import get_failed_jobs
            jobs = get_failed_jobs(mock_redis_client, "n8n")
            assert isinstance(jobs, list)
            mock_redis_client.lrange.assert_called()
    
    def test_move_to_dlq(self, mock_redis_client):
        """Test moving job to DLQ."""
        with patch('redis_queue_dlq_manager.connect_redis', return_value=mock_redis_client):
            from redis_queue_dlq_manager import move_to_dlq, get_retry_metadata
            job = {
                "id": "job-1",
                "data": {"name": "test-workflow", "correlation_id": "corr-123"},
                "key": "bull:n8n:n8n:job-1"
            }
            result = move_to_dlq(mock_redis_client, job, "Test error", "ConnectionError")
            assert result is True
            mock_redis_client.zadd.assert_called()
            mock_redis_client.lrem.assert_called()
    
    def test_requeue_job_with_delay(self, mock_redis_client):
        """Test re-queuing job with delay."""
        with patch('redis_queue_dlq_manager.connect_redis', return_value=mock_redis_client):
            from redis_queue_dlq_manager import requeue_job_with_delay
            job = {
                "id": "job-1",
                "data": {},
                "key": "bull:n8n:n8n:job-1"
            }
            result = requeue_job_with_delay(mock_redis_client, job, 10)
            assert result is True
            mock_redis_client.zadd.assert_called()
            mock_redis_client.lrem.assert_called()


class TestDLQMonitor:
    """Test DLQ monitor functionality."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock = MagicMock()
        mock.ping.return_value = True
        mock.zcard.return_value = 50
        mock.zrevrange.return_value = [
            (json.dumps({"job_id": "job-1", "workflow_name": "test", "error_type": "ConnectionError"}), 1234567890.0)
        ]
        return mock
    
    def test_get_dlq_jobs(self, mock_redis_client):
        """Test getting DLQ jobs."""
        with patch('redis_queue_dlq_monitor.connect_redis', return_value=mock_redis_client):
            from redis_queue_dlq_monitor import get_dlq_jobs
            jobs = get_dlq_jobs(mock_redis_client, limit=10)
            assert isinstance(jobs, list)
            mock_redis_client.zrevrange.assert_called()
    
    def test_get_dlq_stats(self, mock_redis_client):
        """Test getting DLQ statistics."""
        with patch('redis_queue_dlq_monitor.connect_redis', return_value=mock_redis_client):
            from redis_queue_dlq_monitor import get_dlq_stats
            stats = get_dlq_stats(mock_redis_client)
            assert "total_jobs" in stats
            assert stats["total_jobs"] == 50


class TestDLQSchema:
    """Test DLQ job schema."""
    
    def test_dlq_schema_exists(self, repo_root):
        """Test that DLQ schema file exists."""
        schema_file = repo_root / "shared" / "schemas" / "dlq_job.schema.json"
        assert schema_file.exists(), "dlq_job.schema.json not found"
    
    def test_dlq_schema_valid_json(self, repo_root):
        """Test that DLQ schema is valid JSON."""
        schema_file = repo_root / "shared" / "schemas" / "dlq_job.schema.json"
        with open(schema_file, 'r') as f:
            try:
                schema = json.load(f)
                assert "properties" in schema
                assert "job_id" in schema["properties"]
                assert "workflow_name" in schema["properties"]
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in dlq_job.schema.json: {e}")


class TestDLQIntegration:
    """Integration tests for DLQ (requires Redis)."""
    
    @pytest.mark.integration
    def test_dlq_manager_script_exists(self, repo_root):
        """Test that DLQ manager script exists."""
        script = repo_root / "ops" / "scripts" / "redis_queue_dlq_manager.py"
        assert script.exists(), "redis_queue_dlq_manager.py not found"
    
    @pytest.mark.integration
    def test_dlq_monitor_script_exists(self, repo_root):
        """Test that DLQ monitor script exists."""
        script = repo_root / "ops" / "scripts" / "redis_queue_dlq_monitor.py"
        assert script.exists(), "redis_queue_dlq_monitor.py not found"
    
    @pytest.mark.integration
    def test_dlq_recovery_workflow_exists(self, repo_root):
        """Test that DLQ recovery workflow exists."""
        workflow = repo_root / "workflows" / "domains" / "shared" / "dlq_job_recovery.json"
        assert workflow.exists(), "dlq_job_recovery.json not found"

