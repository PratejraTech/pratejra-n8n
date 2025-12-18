#!/usr/bin/env python3
"""
Purpose: Monitor Dead Letter Queue (DLQ) and send alerts when threshold exceeded
Created/Updated: 2025-01-27
Agent: BACKEND_AGENT

This script monitors DLQ size and growth rate, and sends alerts via n8n webhook
when DLQ exceeds configured thresholds.

Usage:
    # Run as service (continuous monitoring)
    python redis_queue_dlq_monitor.py

    # Check DLQ status once
    python redis_queue_dlq_monitor.py --status
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from typing import Dict, Optional, List
from datetime import datetime

try:
    import redis
except ImportError:
    print("Error: redis package not installed. Install with: pip install redis", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bull queue key patterns
BULL_QUEUE_PREFIX = "bull:n8n"
DLQ_KEY = f"{BULL_QUEUE_PREFIX}:dlq"


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
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None


def get_dlq_jobs(client: redis.Redis, limit: int = 100) -> List[Dict]:
    """Get jobs from DLQ."""
    dlq_key = f"{DLQ_KEY}:jobs"
    jobs = []
    
    try:
        # Get jobs from sorted set (most recent first)
        job_strings = client.zrevrange(dlq_key, 0, limit - 1, withscores=True)
        
        for job_str, score in job_strings:
            try:
                job = json.loads(job_str)
                job["dlq_timestamp"] = score
                jobs.append(job)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in DLQ job: {job_str}")
    except Exception as e:
        logger.error(f"Error getting DLQ jobs: {e}")
    
    return jobs


def get_dlq_stats(client: redis.Redis) -> Dict:
    """Get DLQ statistics."""
    dlq_key = f"{DLQ_KEY}:jobs"
    try:
        count = client.zcard(dlq_key)
        
        # Get error type breakdown
        jobs = get_dlq_jobs(client, limit=1000)
        error_types = {}
        workflow_names = {}
        
        for job in jobs:
            error_type = job.get("error_type", "Unknown")
            workflow_name = job.get("workflow_name", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
            workflow_names[workflow_name] = workflow_names.get(workflow_name, 0) + 1
        
        return {
            "total_jobs": count,
            "error_types": error_types,
            "workflow_names": workflow_names,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Error getting DLQ stats: {e}")
        return {"total_jobs": 0}


def send_alert(
    n8n_webhook_url: str,
    dlq_size: int,
    threshold: int,
    stats: Dict
):
    """Send alert to n8n webhook (notify_slack workflow)."""
    payload = {
        "event": "dlq.threshold_exceeded",
        "source": "dlq_monitor",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "dlq_size": dlq_size,
            "threshold": threshold,
            "error_types": stats.get("error_types", {}),
            "top_workflows": dict(list(stats.get("workflow_names", {}).items())[:5]),
            "message": f"DLQ size ({dlq_size}) exceeded threshold ({threshold})"
        }
    }
    
    try:
        response = requests.post(
            n8n_webhook_url,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info(f"Alert sent to {n8n_webhook_url}")
        return True
    except Exception as e:
        logger.error(f"Error sending alert: {e}")
        return False


def monitor_dlq(
    client: redis.Redis,
    alert_threshold: int = 100,
    n8n_webhook_url: Optional[str] = None,
    check_interval: int = 300
):
    """Monitor DLQ and send alerts when threshold exceeded."""
    last_alert_time = 0
    alert_cooldown = 3600  # 1 hour between alerts
    
    logger.info(f"Starting DLQ monitoring (threshold: {alert_threshold}, interval: {check_interval}s)")
    
    try:
        while True:
            stats = get_dlq_stats(client)
            dlq_size = stats["total_jobs"]
            
            logger.info(f"DLQ size: {dlq_size} jobs")
            
            if dlq_size >= alert_threshold:
                current_time = time.time()
                
                # Check cooldown to avoid spam
                if current_time - last_alert_time > alert_cooldown:
                    logger.warning(f"DLQ threshold exceeded: {dlq_size} >= {alert_threshold}")
                    
                    if n8n_webhook_url:
                        if send_alert(n8n_webhook_url, dlq_size, alert_threshold, stats):
                            last_alert_time = current_time
                    else:
                        logger.warning("n8n webhook URL not configured, skipping alert")
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def print_dlq_status(client: redis.Redis):
    """Print DLQ status to console."""
    stats = get_dlq_stats(client)
    
    print("\n" + "="*60)
    print("DLQ Status")
    print("="*60)
    print(f"Total Jobs: {stats['total_jobs']}")
    print(f"Last Updated: {stats.get('last_updated', 'N/A')}")
    
    if stats.get("error_types"):
        print("\nError Types:")
        for error_type, count in sorted(stats["error_types"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count}")
    
    if stats.get("workflow_names"):
        print("\nTop Workflows:")
        for workflow, count in sorted(stats["workflow_names"].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {workflow}: {count}")
    
    print("="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DLQ Monitor for n8n queue mode")
    parser.add_argument("--status", action="store_true", help="Print DLQ status and exit")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    
    args = parser.parse_args()
    
    # Configuration from environment variables
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    alert_threshold = int(os.getenv("DLQ_ALERT_THRESHOLD", "100"))
    n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")  # URL to notify_slack workflow
    
    # Connect to Redis
    client = connect_redis(redis_host, redis_port, redis_password, redis_db)
    if not client:
        logger.error("Failed to connect to Redis. Exiting.")
        sys.exit(1)
    
    logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
    
    if args.status:
        print_dlq_status(client)
    else:
        monitor_dlq(client, alert_threshold, n8n_webhook_url, args.interval)


if __name__ == "__main__":
    main()

