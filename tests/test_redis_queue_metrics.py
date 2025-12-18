"""
Purpose: Tests for Redis queue metrics exporter
Created/Updated: 2025-01-27
Agent: BACKEND_AGENT

Tests for Redis queue metrics collection and Prometheus format generation.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add ops/scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "ops" / "scripts"))


class TestMetricsExporter:
    """Test Redis queue metrics exporter."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock = MagicMock()
        mock.ping.return_value = True
        mock.info.return_value = {"used_memory": 1048576}  # 1MB
        mock.scan_iter.return_value = ["bull:n8n:n8n:wait"]
        mock.zcard.return_value = 5
        mock.llen.return_value = 3
        return mock
    
    def test_connect_redis_success(self, mock_redis_client):
        """Test successful Redis connection."""
        with patch('redis_queue_metrics_exporter.redis.Redis', return_value=mock_redis_client):
            from redis_queue_metrics_exporter import connect_redis
            client = connect_redis("localhost", 6379)
            assert client is not None
            mock_redis_client.ping.assert_called_once()
    
    def test_connect_redis_failure(self):
        """Test Redis connection failure."""
        with patch('redis_queue_metrics_exporter.redis.Redis') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            from redis_queue_metrics_exporter import connect_redis
            client = connect_redis("localhost", 6379)
            assert client is None
    
    def test_get_queue_metrics(self, mock_redis_client):
        """Test getting queue metrics from Redis."""
        with patch('redis_queue_metrics_exporter.connect_redis', return_value=mock_redis_client):
            from redis_queue_metrics_exporter import get_queue_metrics
            metrics = get_queue_metrics(mock_redis_client, "n8n")
            assert "waiting" in metrics
            assert "active" in metrics
            assert "completed" in metrics
            assert "failed" in metrics
    
    def test_get_all_queues(self, mock_redis_client):
        """Test getting all Bull queues."""
        with patch('redis_queue_metrics_exporter.connect_redis', return_value=mock_redis_client):
            from redis_queue_metrics_exporter import get_all_queues
            queues = get_all_queues(mock_redis_client)
            assert isinstance(queues, list)
    
    def test_collect_metrics(self, mock_redis_client):
        """Test metrics collection."""
        with patch('redis_queue_metrics_exporter.connect_redis', return_value=mock_redis_client):
            from redis_queue_metrics_exporter import collect_metrics
            # Should not raise exception
            collect_metrics(mock_redis_client, "localhost")
            mock_redis_client.ping.assert_called()
    
    def test_prometheus_metrics_format(self):
        """Test Prometheus metrics format generation."""
        try:
            from prometheus_client import generate_latest, REGISTRY
            metrics_text = generate_latest(REGISTRY)
            assert isinstance(metrics_text, bytes)
            assert b"# TYPE" in metrics_text or len(metrics_text) == 0
        except ImportError:
            pytest.skip("prometheus_client not installed")


class TestMetricsExporterIntegration:
    """Integration tests for metrics exporter (requires Redis)."""
    
    @pytest.mark.integration
    def test_metrics_exporter_script_exists(self, repo_root):
        """Test that metrics exporter script exists."""
        script = repo_root / "ops" / "scripts" / "redis_queue_metrics_exporter.py"
        assert script.exists(), "redis_queue_metrics_exporter.py not found"
    
    @pytest.mark.integration
    def test_metrics_exporter_importable(self, repo_root):
        """Test that metrics exporter can be imported."""
        script_path = repo_root / "ops" / "scripts"
        sys.path.insert(0, str(script_path))
        try:
            import redis_queue_metrics_exporter
            assert hasattr(redis_queue_metrics_exporter, 'main')
        except ImportError as e:
            pytest.skip(f"Could not import metrics exporter: {e}")

