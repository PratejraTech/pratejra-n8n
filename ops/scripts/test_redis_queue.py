#!/usr/bin/env python3
"""
Purpose: Monitor and test Redis queue functionality for n8n queue mode
Created/Updated: 2025-01-27
Agent: BACKEND_AGENT

This script provides tools to monitor and test the Redis queue used by n8n in queue mode.
It connects to Redis and displays Bull queue metrics, job statuses, and can simulate
job creation for testing purposes.

Usage:
    python ops/scripts/test_redis_queue.py status
    python ops/scripts/test_redis_queue.py monitor [--interval 5]
    python ops/scripts/test_redis_queue.py test-job
    python ops/scripts/test_redis_queue.py health
"""

import argparse
import sys
import time
from typing import Dict, List, Optional

try:
    import redis
except ImportError:
    print("Error: redis package not installed. Install with: pip install redis", file=sys.stderr)
    sys.exit(1)


# n8n uses Bull queue library which creates specific Redis key patterns
BULL_QUEUE_PREFIX = "bull:n8n"
DLQ_KEY = f"{BULL_QUEUE_PREFIX}:dlq"
QUEUE_KEYS = {
    "waiting": "wait",
    "active": "active",
    "completed": "completed",
    "failed": "failed",
    "delayed": "delayed",
    "paused": "paused",
}


def connect_redis(host: str = "localhost", port: int = 6379, password: Optional[str] = None, db: int = 0):
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
        print(f"Error: Failed to connect to Redis at {host}:{port}: {e}", file=sys.stderr)
        sys.exit(1)
    except redis.AuthenticationError as e:
        print(f"Error: Redis authentication failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error connecting to Redis: {e}", file=sys.stderr)
        sys.exit(1)


def get_queue_metrics(client: redis.Redis, queue_name: str = "n8n") -> Dict[str, int]:
    """Get metrics for a Bull queue."""
    metrics = {}
    base_key = f"{BULL_QUEUE_PREFIX}:{queue_name}"
    
    for status, key_suffix in QUEUE_KEYS.items():
        key = f"{base_key}:{key_suffix}"
        try:
            count = client.zcard(key) if status in ["delayed", "waiting"] else client.llen(key)
            metrics[status] = count
        except Exception:
            metrics[status] = 0
    
    return metrics


def get_all_queues(client: redis.Redis) -> List[str]:
    """Get list of all Bull queues."""
    pattern = f"{BULL_QUEUE_PREFIX}:*:wait"
    queues = set()
    for key in client.scan_iter(match=pattern):
        # Extract queue name from key pattern: bull:n8n:{queue_name}:wait
        parts = key.split(":")
        if len(parts) >= 3:
            queues.add(parts[2])
    return sorted(list(queues))


def display_queue_status(client: redis.Redis, queue_name: Optional[str] = None):
    """Display status of queue(s)."""
    if queue_name:
        queues = [queue_name]
    else:
        queues = get_all_queues(client)
    
    if not queues:
        print("No Bull queues found.")
        return
    
    print(f"\n{'='*60}")
    print("n8n Redis Queue Status")
    print(f"{'='*60}\n")
    
    for q in queues:
        metrics = get_queue_metrics(client, q)
        print(f"Queue: {q}")
        print(f"  Waiting:   {metrics.get('waiting', 0)}")
        print(f"  Active:    {metrics.get('active', 0)}")
        print(f"  Completed: {metrics.get('completed', 0)}")
        print(f"  Failed:    {metrics.get('failed', 0)}")
        print(f"  Delayed:   {metrics.get('delayed', 0)}")
        print(f"  Paused:    {metrics.get('paused', 0)}")
        print()


def monitor_queues(client: redis.Redis, interval: int = 5, queue_name: Optional[str] = None):
    """Continuously monitor queue status with refresh interval."""
    print(f"Monitoring queues (refresh every {interval}s). Press Ctrl+C to stop.\n")
    
    try:
        while True:
            # Clear screen (works on most terminals)
            print("\033[2J\033[H", end="")
            display_queue_status(client, queue_name)
            print(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


def check_health(client: redis.Redis) -> bool:
    """Perform health check on Redis connection and queue structure."""
    print("Performing Redis queue health check...\n")
    
    # Check Redis connection
    try:
        client.ping()
        print("✓ Redis connection: OK")
    except Exception as e:
        print(f"✗ Redis connection: FAILED ({e})")
        return False
    
    # Check if queues exist
    queues = get_all_queues(client)
    if queues:
        print(f"✓ Found {len(queues)} queue(s): {', '.join(queues)}")
    else:
        print("⚠ No Bull queues found (this is normal if no workflows have been queued yet)")
    
    # Check Redis info
    try:
        info = client.info("server")
        print(f"✓ Redis version: {info.get('redis_version', 'unknown')}")
        
        info_memory = client.info("memory")
        used_memory_mb = info_memory.get("used_memory", 0) / 1024 / 1024
        print(f"✓ Redis memory usage: {used_memory_mb:.2f} MB")
    except Exception as e:
        print(f"⚠ Could not retrieve Redis info: {e}")
    
    print("\nHealth check completed.")
    return True


def create_test_job(client: redis.Redis, queue_name: str = "n8n"):
    """Create a test job in the queue (simulation)."""
    print(f"Creating test job in queue '{queue_name}'...")
    
    base_key = f"{BULL_QUEUE_PREFIX}:{queue_name}"
    wait_key = f"{base_key}:wait"
    
    try:
        # Create a simple test job
        job_id = f"test-{int(time.time())}"
        job_data = {
            "id": job_id,
            "name": "test-job",
            "data": {"test": True, "timestamp": time.time()},
            "timestamp": int(time.time() * 1000),
        }
        
        # Add to waiting queue (sorted set with timestamp as score)
        client.zadd(wait_key, {str(job_id): time.time()})
        
        # Store job data
        job_key = f"{base_key}:{job_id}"
        client.hset(job_key, mapping={
            "id": job_id,
            "name": "test-job",
            "data": str(job_data),
        })
        
        print(f"✓ Test job created with ID: {job_id}")
        print(f"  Queue key: {wait_key}")
        print(f"  Job key: {job_key}")
        print("\nNote: This is a basic simulation. Real n8n jobs have more complex structure.")
        
    except Exception as e:
        print(f"✗ Failed to create test job: {e}", file=sys.stderr)
        sys.exit(1)


def display_dlq_status(client: redis.Redis):
    """Display DLQ status."""
    dlq_key = f"{DLQ_KEY}:jobs"
    try:
        count = client.zcard(dlq_key)
        print(f"\n{'='*60}")
        print("Dead Letter Queue Status")
        print(f"{'='*60}\n")
        print(f"Total DLQ Jobs: {count}")
        print()
    except Exception as e:
        print(f"Error getting DLQ status: {e}", file=sys.stderr)
        sys.exit(1)


def list_dlq_jobs(client: redis.Redis, limit: int = 20):
    """List jobs in DLQ."""
    dlq_key = f"{DLQ_KEY}:jobs"
    try:
        import json
        job_strings = client.zrevrange(dlq_key, 0, limit - 1, withscores=True)
        
        print(f"\n{'='*60}")
        print(f"DLQ Jobs (showing {min(len(job_strings), limit)})")
        print(f"{'='*60}\n")
        
        if not job_strings:
            print("No jobs in DLQ.")
            return
        
        for idx, (job_str, score) in enumerate(job_strings, 1):
            try:
                job = json.loads(job_str)
                print(f"{idx}. Job ID: {job.get('job_id', 'unknown')}")
                print(f"   Workflow: {job.get('workflow_name', 'unknown')}")
                print(f"   Failed At: {job.get('failed_at', 'unknown')}")
                print(f"   Retry Count: {job.get('retry_count', 0)}")
                print(f"   Error: {job.get('error_message', 'unknown')[:50]}...")
                print()
            except json.JSONDecodeError:
                print(f"{idx}. Invalid job data")
                print()
    except Exception as e:
        print(f"Error listing DLQ jobs: {e}", file=sys.stderr)
        sys.exit(1)


def replay_dlq_job(client: redis.Redis, job_id: str):
    """Replay a job from DLQ back to waiting queue."""
    dlq_key = f"{DLQ_KEY}:jobs"
    base_key = f"{BULL_QUEUE_PREFIX}:n8n"
    wait_key = f"{base_key}:wait"
    
    try:
        import json
        # Find job in DLQ
        job_strings = client.zrange(dlq_key, 0, -1, withscores=True)
        job_to_replay = None
        
        for job_str, score in job_strings:
            job = json.loads(job_str)
            if job.get("job_id") == job_id:
                job_to_replay = job
                break
        
        if not job_to_replay:
            print(f"Job {job_id} not found in DLQ", file=sys.stderr)
            sys.exit(1)
        
        # Re-queue to waiting queue
        client.zadd(wait_key, {job_id: time.time()})
        
        # Remove from DLQ
        client.zrem(dlq_key, json.dumps(job_to_replay))
        
        print(f"✓ Job {job_id} replayed to waiting queue")
        
    except Exception as e:
        print(f"Error replaying job: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor and test Redis queue for n8n queue mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check queue status
  python test_redis_queue.py status

  # Monitor queues with 5 second refresh
  python test_redis_queue.py monitor --interval 5

  # Create a test job
  python test_redis_queue.py test-job

  # Health check
  python test_redis_queue.py health

  # DLQ status
  python test_redis_queue.py dlq-status

  # List DLQ jobs
  python test_redis_queue.py dlq-list

  # Replay job from DLQ
  python test_redis_queue.py dlq-replay --job-id job-123

  # Connect to remote Redis
  python test_redis_queue.py status --host redis.example.com --port 6379 --password mypass
        """
    )
    
    parser.add_argument(
        "command",
        choices=["status", "monitor", "test-job", "health", "dlq-status", "dlq-list", "dlq-replay"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Redis host (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=6379,
        help="Redis port (default: 6379)"
    )
    
    parser.add_argument(
        "--password",
        default=None,
        help="Redis password (default: none)"
    )
    
    parser.add_argument(
        "--db",
        type=int,
        default=0,
        help="Redis database number (default: 0)"
    )
    
    parser.add_argument(
        "--queue",
        default=None,
        help="Specific queue name to monitor (default: all queues)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Refresh interval in seconds for monitor mode (default: 5)"
    )
    
    parser.add_argument(
        "--job-id",
        default=None,
        help="Job ID for dlq-replay command"
    )
    
    args = parser.parse_args()
    
    # Connect to Redis
    client = connect_redis(
        host=args.host,
        port=args.port,
        password=args.password,
        db=args.db
    )
    
    # Execute command
    if args.command == "status":
        display_queue_status(client, args.queue)
    elif args.command == "monitor":
        monitor_queues(client, args.interval, args.queue)
    elif args.command == "health":
        success = check_health(client)
        sys.exit(0 if success else 1)
    elif args.command == "test-job":
        queue_name = args.queue or "n8n"
        create_test_job(client, queue_name)
    elif args.command == "dlq-status":
        display_dlq_status(client)
    elif args.command == "dlq-list":
        list_dlq_jobs(client)
    elif args.command == "dlq-replay":
        if not args.job_id:
            print("Error: --job-id required for dlq-replay command", file=sys.stderr)
            sys.exit(1)
        replay_dlq_job(client, args.job_id)


if __name__ == "__main__":
    main()


