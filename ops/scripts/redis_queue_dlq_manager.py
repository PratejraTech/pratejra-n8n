#!/usr/bin/env python3
"""
Purpose: Dead Letter Queue (DLQ) manager for n8n queue mode with retry logic
Created/Updated: 2025-01-27
Agent: BACKEND_AGENT

This script monitors failed jobs in Redis Bull queue and implements retry logic
with exponential backoff. Jobs that exceed max retries are moved to DLQ.

Usage:
    # Run as service (continuous monitoring)
    python redis_queue_dlq_manager.py

    # Run once (process current failed jobs)
    python redis_queue_dlq_manager.py --once
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, Optional, List
from datetime import datetime, timedelta

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
RETRY_METADATA_KEY = f"{BULL_QUEUE_PREFIX}:retry_metadata"


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


def calculate_retry_delay(
    retry_count: int,
    initial_delay: int = 1,
    max_delay: int = 300,
    backoff_multiplier: float = 2.0
) -> int:
    """Calculate exponential backoff delay in seconds."""
    delay = initial_delay * (backoff_multiplier ** retry_count)
    return min(int(delay), max_delay)


def get_retry_metadata(client: redis.Redis, job_id: str) -> Dict:
    """Get retry metadata for a job."""
    key = f"{RETRY_METADATA_KEY}:{job_id}"
    try:
        data = client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Error getting retry metadata for {job_id}: {e}")
    return {"retry_count": 0, "first_failed_at": None}


def set_retry_metadata(client: redis.Redis, job_id: str, metadata: Dict):
    """Store retry metadata for a job."""
    key = f"{RETRY_METADATA_KEY}:{job_id}"
    try:
        client.setex(key, 86400 * 7, json.dumps(metadata))  # 7 days retention
    except Exception as e:
        logger.warning(f"Error setting retry metadata for {job_id}: {e}")


def get_failed_jobs(client: redis.Redis, queue_name: str = "n8n", limit: int = 100) -> List[Dict]:
    """Get failed jobs from Bull queue."""
    failed_key = f"{BULL_QUEUE_PREFIX}:{queue_name}:failed"
    jobs = []
    
    try:
        # Get job IDs from failed list
        job_ids = client.lrange(failed_key, 0, limit - 1)
        
        for job_id in job_ids:
            # Get job data
            job_key = f"{BULL_QUEUE_PREFIX}:{queue_name}:{job_id}"
            job_data = client.hgetall(job_key)
            
            if job_data:
                jobs.append({
                    "id": job_id,
                    "data": job_data,
                    "key": job_key
                })
    except Exception as e:
        logger.error(f"Error getting failed jobs: {e}")
    
    return jobs


def move_to_dlq(client: redis.Redis, job: Dict, error_message: str, error_type: str = "Unknown"):
    """Move a job to Dead Letter Queue."""
    dlq_job = {
        "job_id": job["id"],
        "workflow_name": job["data"].get("name", "unknown"),
        "failed_at": datetime.utcnow().isoformat() + "Z",
        "retry_count": get_retry_metadata(client, job["id"]).get("retry_count", 0),
        "error_message": error_message,
        "error_type": error_type,
        "original_payload": job["data"],
        "last_retry_at": datetime.utcnow().isoformat() + "Z",
        "correlation_id": job["data"].get("correlation_id"),
        "metadata": {}
    }
    
    try:
        # Store in DLQ (sorted set with timestamp as score)
        dlq_key = f"{DLQ_KEY}:jobs"
        score = time.time()
        client.zadd(dlq_key, {json.dumps(dlq_job): score})
        
        # Remove from failed queue
        failed_key = f"{BULL_QUEUE_PREFIX}:n8n:failed"
        client.lrem(failed_key, 1, job["id"])
        
        logger.info(f"Moved job {job['id']} to DLQ after {dlq_job['retry_count']} retries")
        return True
    except Exception as e:
        logger.error(f"Error moving job {job['id']} to DLQ: {e}")
        return False


def requeue_job_with_delay(
    client: redis.Redis,
    job: Dict,
    delay_seconds: int,
    queue_name: str = "n8n"
):
    """Re-queue a job with a delay (using Bull's delayed queue)."""
    try:
        # Calculate target timestamp
        target_time = time.time() + delay_seconds
        
        # Add to delayed queue
        delayed_key = f"{BULL_QUEUE_PREFIX}:{queue_name}:delayed"
        client.zadd(delayed_key, {job["id"]: target_time})
        
        # Remove from failed queue
        failed_key = f"{BULL_QUEUE_PREFIX}:{queue_name}:failed"
        client.lrem(failed_key, 1, job["id"])
        
        logger.info(f"Re-queued job {job['id']} with {delay_seconds}s delay")
        return True
    except Exception as e:
        logger.error(f"Error re-queuing job {job['id']}: {e}")
        return False


def process_failed_jobs(
    client: redis.Redis,
    max_attempts: int = 5,
    initial_delay: int = 1,
    max_delay: int = 300,
    backoff_multiplier: float = 2.0,
    retryable_errors: Optional[List[str]] = None
):
    """Process failed jobs: retry with backoff or move to DLQ."""
    if retryable_errors is None:
        retryable_errors = ["ConnectionError", "TimeoutError", "RateLimitError"]
    
    failed_jobs = get_failed_jobs(client)
    processed = 0
    
    for job in failed_jobs:
        job_id = job["id"]
        metadata = get_retry_metadata(client, job_id)
        retry_count = metadata.get("retry_count", 0)
        
        # Update metadata
        if metadata.get("first_failed_at") is None:
            metadata["first_failed_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Check if should retry
        error_message = job["data"].get("failedReason", "Unknown error")
        error_type = "Unknown"
        
        # Simple error type detection
        for err_type in retryable_errors:
            if err_type.lower() in error_message.lower():
                error_type = err_type
                break
        
        if retry_count < max_attempts:
            # Calculate delay and re-queue
            delay = calculate_retry_delay(retry_count, initial_delay, max_delay, backoff_multiplier)
            metadata["retry_count"] = retry_count + 1
            metadata["last_retry_at"] = datetime.utcnow().isoformat() + "Z"
            
            set_retry_metadata(client, job_id, metadata)
            
            if requeue_job_with_delay(client, job, delay):
                logger.info(f"Retrying job {job_id} (attempt {retry_count + 1}/{max_attempts}, delay: {delay}s)")
                processed += 1
        else:
            # Move to DLQ
            if move_to_dlq(client, job, error_message, error_type):
                # Clean up retry metadata
                retry_meta_key = f"{RETRY_METADATA_KEY}:{job_id}"
                client.delete(retry_meta_key)
                processed += 1
    
    return processed


def get_dlq_stats(client: redis.Redis) -> Dict:
    """Get DLQ statistics."""
    dlq_key = f"{DLQ_KEY}:jobs"
    try:
        count = client.zcard(dlq_key)
        return {
            "total_jobs": count,
            "dlq_key": dlq_key
        }
    except Exception as e:
        logger.error(f"Error getting DLQ stats: {e}")
        return {"total_jobs": 0}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DLQ Manager for n8n queue mode")
    parser.add_argument("--once", action="store_true", help="Process failed jobs once and exit")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds (default: 60)")
    
    args = parser.parse_args()
    
    # Configuration from environment variables
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    max_attempts = int(os.getenv("DLQ_MAX_ATTEMPTS", "5"))
    initial_delay = int(os.getenv("DLQ_INITIAL_DELAY", "1"))
    max_delay = int(os.getenv("DLQ_MAX_DELAY", "300"))
    backoff_multiplier = float(os.getenv("DLQ_BACKOFF_MULTIPLIER", "2.0"))
    retryable_errors = os.getenv("DLQ_RETRYABLE_ERRORS", "ConnectionError,TimeoutError,RateLimitError").split(",")
    
    # Connect to Redis
    client = connect_redis(redis_host, redis_port, redis_password, redis_db)
    if not client:
        logger.error("Failed to connect to Redis. Exiting.")
        sys.exit(1)
    
    logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
    logger.info(f"DLQ configuration: max_attempts={max_attempts}, initial_delay={initial_delay}s, max_delay={max_delay}s")
    
    try:
        if args.once:
            # Process once and exit
            processed = process_failed_jobs(
                client, max_attempts, initial_delay, max_delay, backoff_multiplier, retryable_errors
            )
            stats = get_dlq_stats(client)
            logger.info(f"Processed {processed} failed jobs. DLQ size: {stats['total_jobs']}")
        else:
            # Continuous monitoring
            logger.info(f"Starting DLQ manager (polling every {args.interval}s)")
            while True:
                processed = process_failed_jobs(
                    client, max_attempts, initial_delay, max_delay, backoff_multiplier, retryable_errors
                )
                if processed > 0:
                    stats = get_dlq_stats(client)
                    logger.info(f"Processed {processed} failed jobs. DLQ size: {stats['total_jobs']}")
                time.sleep(args.interval)
                
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

