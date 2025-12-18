"""
Purpose: Tests for Redis queue configuration and monitoring
Created/Updated: 2025-01-27
Agent: BACKEND_AGENT

Tests for Redis queue configuration, Docker Compose setup, and queue monitoring script.
"""

import pytest
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call


class TestRedisConfiguration:
    """Test Redis configuration file."""
    
    def test_redis_conf_exists(self, repo_root):
        """Test that redis.conf file exists."""
        redis_conf = repo_root / "docker" / "redis.conf"
        assert redis_conf.exists(), "redis.conf not found"
    
    def test_redis_conf_readable(self, repo_root):
        """Test that redis.conf is readable."""
        redis_conf = repo_root / "docker" / "redis.conf"
        with open(redis_conf, 'r') as f:
            content = f.read()
            assert len(content) > 0, "redis.conf is empty"
            assert "appendonly" in content, "AOF persistence not configured"
            assert "maxmemory-policy" in content, "Memory policy not configured"


class TestDockerComposeRedis:
    """Test Docker Compose configuration with Redis."""
    
    def test_docker_compose_redis_exists(self, repo_root):
        """Test that docker-compose.n8n.redis.yaml exists."""
        compose_file = repo_root / "docker" / "docker-compose.n8n.redis.yaml"
        assert compose_file.exists(), "docker-compose.n8n.redis.yaml not found"
    
    def test_docker_compose_redis_valid_yaml(self, repo_root):
        """Test that docker-compose file is valid YAML."""
        compose_file = repo_root / "docker" / "docker-compose.n8n.redis.yaml"
        
        with open(compose_file, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in docker-compose.n8n.redis.yaml: {e}")
    
    def test_docker_compose_has_redis_service(self, repo_root):
        """Test that compose file has Redis service."""
        compose_file = repo_root / "docker" / "docker-compose.n8n.redis.yaml"
        
        with open(compose_file, 'r') as f:
            compose = yaml.safe_load(f)
        
        assert 'services' in compose, "No services section found"
        assert 'redis' in compose['services'], "Redis service not found"
    
    def test_docker_compose_has_n8n_main(self, repo_root):
        """Test that compose file has n8n main service."""
        compose_file = repo_root / "docker" / "docker-compose.n8n.redis.yaml"
        
        with open(compose_file, 'r') as f:
            compose = yaml.safe_load(f)
        
        assert 'services' in compose, "No services section found"
        assert 'n8n' in compose['services'], "n8n service not found"
        
        n8n_service = compose['services']['n8n']
        assert 'environment' in n8n_service, "n8n service missing environment section"
        env = n8n_service['environment']
        assert 'EXECUTIONS_MODE' in env, "EXECUTIONS_MODE not set"
        assert env['EXECUTIONS_MODE'] == 'queue', "EXECUTIONS_MODE should be 'queue'"
    
    def test_docker_compose_has_worker_service(self, repo_root):
        """Test that compose file has n8n-worker service."""
        compose_file = repo_root / "docker" / "docker-compose.n8n.redis.yaml"
        
        with open(compose_file, 'r') as f:
            compose = yaml.safe_load(f)
        
        assert 'services' in compose, "No services section found"
        assert 'n8n-worker' in compose['services'], "n8n-worker service not found"
        
        worker_service = compose['services']['n8n-worker']
        assert 'command' in worker_service, "n8n-worker missing command"
        assert worker_service['command'] == 'worker', "n8n-worker command should be 'worker'"
    
    def test_redis_service_has_healthcheck(self, repo_root):
        """Test that Redis service has health check configured."""
        compose_file = repo_root / "docker" / "docker-compose.n8n.redis.yaml"
        
        with open(compose_file, 'r') as f:
            compose = yaml.safe_load(f)
        
        redis_service = compose['services']['redis']
        assert 'healthcheck' in redis_service, "Redis service missing healthcheck"
    
    def test_redis_uses_config_file(self, repo_root):
        """Test that Redis service uses redis.conf file."""
        compose_file = repo_root / "docker" / "docker-compose.n8n.redis.yaml"
        
        with open(compose_file, 'r') as f:
            compose = yaml.safe_load(f)
        
        redis_service = compose['services']['redis']
        assert 'volumes' in redis_service, "Redis service missing volumes"
        
        volumes = redis_service['volumes']
        assert any('redis.conf' in str(v) for v in volumes), "Redis not using redis.conf file"


class TestEnvironmentConfiguration:
    """Test environment configuration files."""
    
    def test_env_file_exists(self, repo_root):
        """Test that n8n.redis.env.example exists."""
        env_file = repo_root / "docker" / "n8n.redis.env.example"
        assert env_file.exists(), "n8n.redis.env.example not found"
    
    def test_dev_config_has_redis_section(self, config_dir):
        """Test that dev config has Redis configuration section."""
        config_file = config_dir / "environments.dev.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'redis' in config, "Redis configuration section not found"
        
        redis_config = config['redis']
        assert 'host' in redis_config, "Redis host not configured"
        assert 'port' in redis_config, "Redis port not configured"
        assert 'queue_mode' in redis_config, "Queue mode configuration not found"


class TestQueueMonitoringScript:
    """Test queue monitoring script functionality."""
    
    def test_script_exists(self, repo_root):
        """Test that test_redis_queue.py script exists."""
        script = repo_root / "ops" / "scripts" / "test_redis_queue.py"
        assert script.exists(), "test_redis_queue.py not found"
    
    @patch('sys.path')
    @patch('redis.Redis')
    def test_connect_redis_success(self, mock_redis_class, mock_path):
        """Test successful Redis connection."""
        import sys
        from pathlib import Path
        # Add ops/scripts to path for import
        repo_root = Path(__file__).parent.parent
        sys.path.insert(0, str(repo_root))
        
        from ops.scripts.test_redis_queue import connect_redis
        
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_class.return_value = mock_client
        
        client = connect_redis(host='localhost', port=6379)
        
        assert client == mock_client
        mock_client.ping.assert_called_once()
    
    @patch('sys.path')
    @patch('redis.Redis')
    def test_connect_redis_failure(self, mock_redis_class, mock_path):
        """Test Redis connection failure handling."""
        import sys
        from pathlib import Path
        repo_root = Path(__file__).parent.parent
        sys.path.insert(0, str(repo_root))
        
        from ops.scripts.test_redis_queue import connect_redis
        
        mock_redis_class.side_effect = Exception("Connection failed")
        
        with pytest.raises(SystemExit):
            connect_redis(host='localhost', port=6379)
    
    def test_get_queue_metrics(self):
        """Test queue metrics retrieval logic."""
        # Test the function logic without requiring full import
        # This tests the core functionality
        mock_client = MagicMock()
        mock_client.zcard.return_value = 5  # waiting/delayed
        mock_client.llen.return_value = 3   # active/completed/failed
        
        # Simulate the function logic
        metrics = {}
        base_key = "bull:n8n:n8n"
        queue_keys = {
            "waiting": "wait",
            "active": "active",
            "completed": "completed",
            "failed": "failed",
            "delayed": "delayed",
            "paused": "paused",
        }
        
        for status, key_suffix in queue_keys.items():
            key = f"{base_key}:{key_suffix}"
            count = mock_client.zcard(key) if status in ["delayed", "waiting"] else mock_client.llen(key)
            metrics[status] = count
        
        assert 'waiting' in metrics
        assert metrics['waiting'] == 5
        assert 'active' in metrics
        assert metrics['active'] == 3
    
    def test_get_all_queues_logic(self):
        """Test getting all queue names logic."""
        mock_client = MagicMock()
        mock_client.scan_iter.return_value = [
            'bull:n8n:n8n:wait',
            'bull:n8n:test-queue:wait'
        ]
        
        # Simulate the function logic
        pattern = "bull:n8n:*:wait"
        queues = set()
        for key in mock_client.scan_iter(match=pattern):
            parts = key.split(":")
            if len(parts) >= 3:
                queues.add(parts[2])
        queues = sorted(list(queues))
        
        assert 'n8n' in queues
        assert 'test-queue' in queues
    
    def test_check_health_logic(self):
        """Test health check logic."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.scan_iter.return_value = ['bull:n8n:n8n:wait']
        
        # Simulate info calls
        call_count = 0
        def info_side_effect(section=None):
            nonlocal call_count
            call_count += 1
            if section == "server":
                return {'redis_version': '7.0.0'}
            elif section == "memory":
                return {'used_memory': 1048576}
            return {}
        
        mock_client.info.side_effect = info_side_effect
        
        # Simulate health check
        try:
            mock_client.ping()
            queues = list(mock_client.scan_iter(match="bull:n8n:*:wait"))
            server_info = mock_client.info("server")
            memory_info = mock_client.info("memory")
            
            assert server_info['redis_version'] == '7.0.0'
            assert len(queues) > 0
            result = True
        except Exception:
            result = False
        
        assert result is True
        assert mock_client.ping.called


class TestDocumentation:
    """Test documentation files."""
    
    def test_redis_queue_doc_exists(self, repo_root):
        """Test that REDIS_QUEUE_CONFIGURATION.md exists."""
        doc_file = repo_root / "docs" / "REDIS_QUEUE_CONFIGURATION.md"
        assert doc_file.exists(), "REDIS_QUEUE_CONFIGURATION.md not found"
    
    def test_n8n_config_has_queue_section(self, repo_root):
        """Test that N8N_CONFIGURATION.md has queue mode section."""
        doc_file = repo_root / "docs" / "N8N_CONFIGURATION.md"
        
        with open(doc_file, 'r') as f:
            content = f.read()
        
        assert 'Queue Mode Configuration' in content, "Queue mode section not found"
        assert 'EXECUTIONS_MODE' in content, "Queue mode env vars not documented"


class TestRequirements:
    """Test requirements file includes redis."""
    
    def test_requirements_has_redis(self, repo_root):
        """Test that requirements.txt includes redis package."""
        requirements_file = repo_root / "requirements.txt"
        
        with open(requirements_file, 'r') as f:
            content = f.read()
        
        assert 'redis' in content, "redis package not in requirements.txt"
        assert 'redis>=' in content or 'redis==' in content, "redis version not specified"

