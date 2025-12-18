#!/usr/bin/env python3
"""
Purpose: Supplemental Redis queue metrics exporter for n8n queue mode
Created/Updated: 2025-01-27
Agent: BACKEND_AGENT

This script exports supplemental Redis-level metrics for n8n queue mode to Prometheus.
It complements n8n's built-in metrics with deeper Bull queue insights.

Usage:
    # Run as service (exposes HTTP endpoint for Prometheus scraping)
    python redis_queue_metrics_exporter.py

    # Or push to Prometheus Push Gateway
    PROMETHEUS_PUSH_GATEWAY=http://pushgateway:9091 python redis_queue_metrics_exporter.py
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

try:
    import redis
except ImportError:
    print("Error: redis package not installed. Install with: pip install redis", file=sys.stderr)
    sys.exit(1)

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
except ImportError:
    print("Error: prometheus_client package not installed. Install with: pip install prometheus-client", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bull queue key patterns
BULL_QUEUE_PREFIX = "bull:n8n"
QUEUE_KEYS = {
    "waiting": "wait",
    "active": "active",
    "completed": "completed",
    "failed": "failed",
    "delayed": "delayed",
    "paused": "paused",
}

# Prometheus metrics
queue_depth = Gauge(
    'n8n_redis_queue_depth',
    'Number of jobs in queue by status',
    ['queue', 'status']
)

queue_jobs_total = Counter(
    'n8n_redis_queue_jobs_total',
    'Total number of jobs processed by status',
    ['queue', 'status']
)

redis_connection_status = Gauge(
    'n8n_redis_connection_status',
    'Redis connection status (1=up, 0=down)',
    ['host']
)

redis_memory_usage = Gauge(
    'n8n_redis_memory_usage_bytes',
    'Redis memory usage in bytes'
)

queue_processing_time = Histogram(
    'n8n_redis_queue_processing_time_seconds',
    'Queue processing time in seconds',
    ['queue'],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 300]
)


def connect_redis(
    host: str = "localhost",
    port: int = 6379,
    password: Optional[str] = None,
    db: int = 0
) -> Optional[redis.Redis]:
    """Connect to Redis and return client."""
    try:
        client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        # Test connection
        client.ping()
        return client
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis at {host}:{port}: {e}")
        return None
    except redis.AuthenticationError as e:
        logger.error(f"Redis authentication failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        return None


def get_queue_metrics(client: redis.Redis, queue_name: str = "n8n") -> Dict[str, int]:
    """Get metrics for a Bull queue."""
    metrics = {}
    base_key = f"{BULL_QUEUE_PREFIX}:{queue_name}"
    
    for status, key_suffix in QUEUE_KEYS.items():
        key = f"{base_key}:{key_suffix}"
        try:
            if status in ["delayed", "waiting"]:
                count = client.zcard(key)
            else:
                count = client.llen(key)
            metrics[status] = count
        except Exception as e:
            logger.warning(f"Error getting metric for {key}: {e}")
            metrics[status] = 0
    
    return metrics


def get_all_queues(client: redis.Redis) -> list:
    """Get list of all Bull queues."""
    pattern = f"{BULL_QUEUE_PREFIX}:*:wait"
    queues = set()
    try:
        for key in client.scan_iter(match=pattern):
            # Extract queue name from key pattern: bull:n8n:{queue_name}:wait
            parts = key.split(":")
            if len(parts) >= 3:
                queues.add(parts[2])
    except Exception as e:
        logger.warning(f"Error scanning for queues: {e}")
    return sorted(list(queues))


def collect_metrics(client: redis.Redis, redis_host: str):
    """Collect metrics from Redis and update Prometheus metrics."""
    try:
        # Test connection
        client.ping()
        redis_connection_status.labels(host=redis_host).set(1)
        
        # Get Redis memory info
        try:
            info_memory = client.info("memory")
            memory_bytes = info_memory.get("used_memory", 0)
            redis_memory_usage.set(memory_bytes)
        except Exception as e:
            logger.warning(f"Error getting Redis memory info: {e}")
        
        # Get all queues
        queues = get_all_queues(client)
        if not queues:
            queues = ["n8n"]  # Default queue name
        
        # Collect metrics for each queue
        for queue_name in queues:
            metrics = get_queue_metrics(client, queue_name)
            
            # Update queue depth metrics
            for status, count in metrics.items():
                queue_depth.labels(queue=queue_name, status=status).set(count)
            
            # Note: We don't track completed/failed totals here as they're cumulative
            # n8n's built-in metrics handle those better
        
        logger.debug(f"Collected metrics for {len(queues)} queue(s)")
        
    except redis.ConnectionError:
        redis_connection_status.labels(host=redis_host).set(0)
        logger.error("Redis connection lost")
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        redis_connection_status.labels(host=redis_host).set(0)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""
    
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(generate_latest(REGISTRY))
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        logger.debug(f"{self.address_string()} - {format % args}")


def run_http_server(port: int = 9090):
    """Run HTTP server for Prometheus scraping."""
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)
    logger.info(f"Starting metrics HTTP server on port {port}")
    logger.info(f"Metrics available at http://localhost:{port}/metrics")
    server.serve_forever()


def push_to_gateway(push_gateway_url: str, job_name: str = "n8n-queue-metrics"):
    """Push metrics to Prometheus Push Gateway."""
    try:
        from prometheus_client import push_to_gateway
        push_to_gateway(push_gateway_url, job=job_name, registry=REGISTRY)
        logger.debug(f"Pushed metrics to {push_gateway_url}")
    except Exception as e:
        logger.error(f"Error pushing to gateway: {e}")


def main():
    """Main entry point."""
    # Configuration from environment variables
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_db = int(os.getenv("REDIS_DB", "0"))
    scrape_interval = int(os.getenv("SCRAPE_INTERVAL_SECONDS", "30"))
    
    push_gateway = os.getenv("PROMETHEUS_PUSH_GATEWAY")
    expose_http = os.getenv("EXPOSE_HTTP_PORT")
    http_port = int(expose_http) if expose_http else None
    
    # Connect to Redis
    client = connect_redis(redis_host, redis_port, redis_password, redis_db)
    if not client:
        logger.error("Failed to connect to Redis. Exiting.")
        sys.exit(1)
    
    logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
    
    # Start HTTP server if requested
    if http_port:
        server_thread = Thread(target=run_http_server, args=(http_port,), daemon=True)
        server_thread.start()
    
    # Main loop: collect and export metrics
    logger.info(f"Starting metrics collection (interval: {scrape_interval}s)")
    
    try:
        while True:
            collect_metrics(client, redis_host)
            
            # Push to gateway if configured
            if push_gateway:
                push_to_gateway(push_gateway)
            
            time.sleep(scrape_interval)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

