<!--
Purpose: Error handling guidelines and patterns documentation for automation platform
Created/Updated: 2025-11-19 19:49
Agent: Init Agent
-->
# Error Handling

## Queue Mode Retry Logic

### Overview

In queue mode, failed jobs are handled at two levels:

1. **Queue-Level Retry (DLQ Manager):** Handles transient failures with exponential backoff
2. **Workflow-Level Error Handling:** Handles business logic errors via `error_central_handler`

### Queue-Level Retry Strategy

The DLQ manager (`ops/scripts/redis_queue_dlq_manager.py`) implements automatic retry with exponential backoff:

**Retry Configuration:**
- **Max Attempts:** 5 (configurable)
- **Initial Delay:** 1 second
- **Max Delay:** 300 seconds (5 minutes)
- **Backoff Multiplier:** 2.0

**Retry Formula:**
```
delay = min(initial_delay * (backoff_multiplier ^ retry_count), max_delay)
```

**Example Retry Schedule:**
- Attempt 1: 1 second delay
- Attempt 2: 2 seconds delay
- Attempt 3: 4 seconds delay
- Attempt 4: 8 seconds delay
- Attempt 5: 16 seconds delay
- After max attempts: Move to DLQ

### Retryable Errors

The following error types are automatically retried:
- `ConnectionError` - Network connectivity issues
- `TimeoutError` - Request timeouts
- `RateLimitError` - Rate limiting from external services

**Configuration:**
```yaml
queue_retry:
  retryable_errors:
    - "ConnectionError"
    - "TimeoutError"
    - "RateLimitError"
```

### Dead Letter Queue (DLQ)

Jobs that exceed maximum retry attempts are moved to DLQ:

**DLQ Features:**
- Automatic movement after max retries
- Retention period: 30 days (configurable)
- Alert threshold: 100 jobs (configurable)
- Manual recovery via `dlq_job_recovery` workflow

**DLQ Job Structure:**
- Job ID and workflow name
- Failure timestamps and retry count
- Error message and type
- Original payload for replay

See `shared/schemas/dlq_job.schema.json` for schema definition.

### Workflow-Level Error Handling

The `error_central_handler` workflow handles:
- Business logic errors
- Validation errors
- Non-retryable errors
- Error notifications and logging

**Integration:**
- Queue-level retry happens before workflow execution
- Workflow-level error handling happens during execution
- Two separate layers for different error types

### Best Practices

1. **Configure Appropriate Retry Limits:** Balance between retry attempts and DLQ size
2. **Monitor DLQ Growth:** Set up alerts for DLQ threshold
3. **Review DLQ Regularly:** Investigate patterns in failed jobs
4. **Test Retry Logic:** Verify exponential backoff works as expected
5. **Document Error Types:** Keep retryable_errors list updated

### Related Documentation

- `docs/REDIS_QUEUE_CONFIGURATION.md` - DLQ configuration details
- `docs/RUNBOOKS.md` - DLQ troubleshooting
- `ops/scripts/redis_queue_dlq_manager.py` - DLQ manager implementation

