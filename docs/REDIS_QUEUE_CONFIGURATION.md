# Redis Queue Configuration for n8n

**Purpose:** Comprehensive guide for configuring Redis as a message queue for n8n queue mode  
**Created/Updated:** 2025-01-27  
**Agent:** BACKEND_AGENT

## Overview

This document describes how to configure Redis as a message queue for n8n's queue mode execution. Queue mode enables horizontal scaling, decouples webhook processing from workflow execution, and provides better reliability for production workloads.

### Benefits of Queue Mode

- **Horizontal Scaling:** Run multiple worker instances to process workflows in parallel
- **Decoupled Execution:** Webhook handlers don't block on workflow execution
- **Reliability:** Failed jobs can be retried without blocking the main instance
- **Zero Downtime Deployments:** Workers can be updated independently
- **Better Resource Utilization:** Long-running workflows don't block short ones

## Architecture

n8n uses the Bull queue library (built on Redis) to manage workflow execution queues. The architecture consists of:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   n8n Main  │────▶│ Redis Queue  │◀────│  n8n Worker │
│  (Webhooks) │     │  (Bull/Bull) │     │  (Execute)  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                    ┌───────▼────────┐
                    │ Queue Monitor  │
                    │   (Test Tool)  │
                    └────────────────┘
```

### Components

1. **n8n Main Instance:** Handles webhooks, API requests, and queues workflow executions
2. **Redis Queue:** Stores workflow execution jobs with Bull queue structure
3. **n8n Worker Instances:** Process queued workflow executions
4. **Queue Monitor:** Tool to monitor and test queue functionality

## Docker Compose Setup (Development/Testing)

### Prerequisites

- Docker and Docker Compose installed
- Port 5678 available for n8n (or configure custom port)

### Quick Start

1. **Copy environment file:**
   ```bash
   cd docker
   cp n8n.redis.env.example n8n.redis.env
   ```

2. **Update environment variables:**
   Edit `n8n.redis.env` and set:
   - `N8N_ENCRYPTION_KEY` (required - use a long random string)
   - `POSTGRES_PASSWORD` (change from default)
   - `REDIS_PASSWORD` (optional but recommended)

3. **Start services:**
   ```bash
   docker-compose -f docker-compose.n8n.redis.yaml up -d
   ```

4. **Verify services are running:**
   ```bash
   docker-compose -f docker-compose.n8n.redis.yaml ps
   ```

5. **Check logs:**
   ```bash
   # All services
   docker-compose -f docker-compose.n8n.redis.yaml logs -f
   
   # Specific service
   docker-compose -f docker-compose.n8n.redis.yaml logs -f n8n
   docker-compose -f docker-compose.n8n.redis.yaml logs -f n8n-worker
   docker-compose -f docker-compose.n8n.redis.yaml logs -f redis
   ```

### Service Overview

The docker-compose setup includes:

- **postgres:** PostgreSQL database for n8n workflow storage
- **redis:** Redis server for queue management
- **n8n-main:** Main n8n instance (webhooks, API, UI)
- **n8n-worker:** Worker instance for processing queued workflows

### Network Configuration

All services communicate via Docker internal network `n8n-network`. Redis port is **not exposed** to the host by default for security. To access Redis from host (for testing), uncomment the ports section in docker-compose file.

## Configuration

### Environment Variables

#### Required for Queue Mode

```bash
EXECUTIONS_MODE=queue
QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379
QUEUE_BULL_REDIS_DB=0
```

#### Optional Redis Configuration

```bash
# Redis password (recommended for production)
QUEUE_BULL_REDIS_PASSWORD=your-secure-password

# Connection timeout in milliseconds
QUEUE_BULL_REDIS_CONNECTION_TIMEOUT=10000
```

#### n8n Configuration

```bash
# Basic n8n settings
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=http
WEBHOOK_URL=http://localhost:5678/

# Encryption key (REQUIRED - keep stable across restarts)
N8N_ENCRYPTION_KEY=your-long-random-encryption-key

# Metrics
N8N_METRICS=true
N8N_DIAGNOSTICS_ENABLED=false
```

### Redis Configuration File

The Redis configuration file (`docker/redis.conf`) includes:

- **Persistence:** AOF (Append Only File) enabled for durability
- **Memory Management:** LRU eviction policy with 256MB limit (configurable)
- **Performance:** Optimized for queue workloads
- **Security:** Protected mode enabled

To customize Redis settings, edit `docker/redis.conf` and restart the Redis container.

### Scaling Workers

To scale worker instances:

```bash
# Scale to 3 worker instances
docker-compose -f docker-compose.n8n.redis.yaml up -d --scale n8n-worker=3
```

Each worker will connect to the same Redis queue and process jobs independently.

## AWS ElastiCache Setup (Production)

For production deployments, use AWS ElastiCache for Redis instead of a self-hosted instance.

### Creating ElastiCache Redis Cluster

1. **Create ElastiCache Redis Cluster:**
   - Go to AWS Console → ElastiCache → Redis clusters
   - Click "Create Redis cluster"
   - Choose cluster configuration:
     - **Cluster mode:** Disabled (single node or replication group)
     - **Engine version:** 7.x or later
     - **Node type:** Choose based on expected load
     - **Number of replicas:** 1-2 for high availability
     - **Multi-AZ:** Enabled for production
     - **Encryption:** Enable encryption at rest and in transit

2. **Network Configuration:**
   - **VPC:** Select your n8n VPC
   - **Subnet group:** Create/select subnet group in private subnets
   - **Security groups:** Create security group allowing access from n8n instances

3. **Security:**
   - **Authentication:** Enable Redis AUTH (password)
   - **Encryption in transit:** Enable TLS
   - **Encryption at rest:** Enable for production

4. **Backup:**
   - **Snapshot retention:** Configure retention period
   - **Backup window:** Set maintenance window

### Security Group Configuration

Create security group for ElastiCache:

```yaml
Inbound Rules:
  - Type: Custom TCP
    Port: 6379
    Source: Security group of n8n instances
    Description: Allow n8n to connect to Redis
```

### Connection Configuration

Update n8n environment variables for ElastiCache:

```bash
QUEUE_BULL_REDIS_HOST=your-elasticache-endpoint.cache.amazonaws.com
QUEUE_BULL_REDIS_PORT=6379
QUEUE_BULL_REDIS_PASSWORD=<retrieve-from-aws-secrets-manager>
QUEUE_BULL_REDIS_DB=0
QUEUE_BULL_REDIS_CONNECTION_TIMEOUT=10000

# If using TLS encryption
QUEUE_BULL_REDIS_TLS=true
```

### Storing Credentials

Store Redis password in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name automation-hub/prod/redis-password \
  --secret-string "your-redis-password"
```

Reference in configuration:
```yaml
redis:
  password_secret_arn: "arn:aws:secretsmanager:REGION:ACCOUNT:secret:automation-hub/prod/redis-password"
```

### Monitoring and Alerting

Set up CloudWatch alarms for:

- **CPU Utilization:** Alert if > 80%
- **Memory Usage:** Alert if > 90%
- **Connection Count:** Alert if approaching limits
- **Cache Miss Rate:** Monitor cache efficiency
- **Network I/O:** Monitor bandwidth usage

### Backup and Restore

ElastiCache provides automated backups:

- **Backup retention:** Configure in cluster settings
- **Manual snapshots:** Create via AWS Console or CLI
- **Restore:** Create new cluster from snapshot

```bash
# Create manual snapshot
aws elasticache create-snapshot \
  --replication-group-id your-cluster-id \
  --snapshot-name backup-$(date +%Y%m%d)

# Restore from snapshot
aws elasticache create-replication-group \
  --replication-group-id restored-cluster \
  --snapshot-name backup-20250127 \
  ...
```

## Testing and Monitoring

### Queue Monitoring Script

Use the provided script to monitor queue status:

```bash
# Check queue status
python ops/scripts/test_redis_queue.py status

# Monitor queues in real-time (5 second refresh)
python ops/scripts/test_redis_queue.py monitor --interval 5

# Health check
python ops/scripts/test_redis_queue.py health

# Connect to remote Redis (ElastiCache)
python ops/scripts/test_redis_queue.py status \
  --host your-elasticache-endpoint.cache.amazonaws.com \
  --port 6379 \
  --password your-password
```

### Manual Redis CLI Testing

```bash
# Connect to Redis container
docker exec -it n8n-redis redis-cli

# Or with password
docker exec -it n8n-redis redis-cli -a your-password

# Check queue keys
KEYS bull:n8n:*

# Check waiting jobs
ZCARD bull:n8n:n8n:wait

# Check active jobs
LLEN bull:n8n:n8n:active

# Check completed jobs
LLEN bull:n8n:n8n:completed

# Check failed jobs
LLEN bull:n8n:n8n:failed
```

### Verifying Queue Mode

1. **Check n8n logs:**
   ```bash
   docker-compose -f docker-compose.n8n.redis.yaml logs n8n | grep -i queue
   ```

2. **Verify worker is processing:**
   ```bash
   docker-compose -f docker-compose.n8n.redis.yaml logs n8n-worker | grep -i processing
   ```

3. **Trigger a workflow:**
   - Create a test workflow in n8n UI
   - Activate it
   - Trigger via webhook or manual execution
   - Monitor queue status using the test script

## Troubleshooting

### Common Issues

#### Redis Connection Failed

**Symptoms:** n8n logs show "Redis connection failed" errors

**Solutions:**
1. Verify Redis is running: `docker-compose ps redis`
2. Check Redis logs: `docker-compose logs redis`
3. Verify network connectivity: `docker-compose exec n8n ping redis`
4. Check Redis password matches in environment variables
5. Verify Redis hostname is correct (should be "redis" in Docker Compose)

#### Worker Not Processing Jobs

**Symptoms:** Jobs stuck in waiting queue, worker logs show no activity

**Solutions:**
1. Verify worker is running: `docker-compose ps n8n-worker`
2. Check worker logs: `docker-compose logs n8n-worker`
3. Verify worker has same Redis configuration as main instance
4. Check for errors in worker logs
5. Verify database connection (worker needs DB access)

#### Queue Jobs Failing

**Symptoms:** Jobs move to failed queue immediately

**Solutions:**
1. Check n8n workflow for errors
2. Verify workflow dependencies are available
3. Check worker logs for detailed error messages
4. Verify database connection
5. Check for memory/resource constraints

#### High Memory Usage

**Symptoms:** Redis using excessive memory

**Solutions:**
1. Check queue size: `ZCARD bull:n8n:n8n:wait`
2. Review completed/failed job retention
3. Adjust `maxmemory` in `redis.conf`
4. Configure appropriate `maxmemory-policy`
5. Consider increasing Redis instance size (ElastiCache)

### Debugging Commands

```bash
# Check all services status
docker-compose -f docker-compose.n8n.redis.yaml ps

# View all logs
docker-compose -f docker-compose.n8n.redis.yaml logs

# Restart a service
docker-compose -f docker-compose.n8n.redis.yaml restart n8n-worker

# Execute command in container
docker-compose -f docker-compose.n8n.redis.yaml exec redis redis-cli INFO

# Check network connectivity
docker-compose -f docker-compose.n8n.redis.yaml exec n8n ping redis
```

## Security Considerations

### Production Checklist

- [ ] Redis password configured and stored in secrets manager
- [ ] Redis port not exposed to public internet
- [ ] TLS encryption enabled (ElastiCache)
- [ ] Encryption at rest enabled (ElastiCache)
- [ ] Security groups restrict access to n8n instances only
- [ ] Regular security updates applied
- [ ] Monitoring and alerting configured
- [ ] Backup and restore procedures tested

### Best Practices

1. **Use strong passwords:** Generate secure random passwords for Redis
2. **Network isolation:** Keep Redis in private subnets, no public access
3. **Encryption:** Enable TLS for ElastiCache in production
4. **Access control:** Use IAM roles and security groups to restrict access
5. **Monitoring:** Set up alerts for suspicious activity
6. **Backups:** Regular automated backups with tested restore procedures
7. **Updates:** Keep Redis and n8n versions up to date

## Performance Tuning

### Redis Configuration

Optimize Redis for queue workloads:

```conf
# Increase max memory if needed
maxmemory 512mb

# Use allkeys-lru for queue workloads
maxmemory-policy allkeys-lru

# Optimize AOF settings
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

### Worker Scaling

- **Start with 1-2 workers** and monitor performance
- **Scale up** based on queue depth and processing time
- **Monitor worker CPU/memory** to avoid resource contention
- **Consider** different worker pools for different workflow types

### Monitoring Metrics

Key metrics to monitor:

- **Queue depth:** Number of waiting jobs
- **Processing time:** Time from queue to completion
- **Failed jobs:** Rate of job failures
- **Worker utilization:** CPU/memory usage per worker
- **Redis memory:** Memory usage and eviction rate

## Queue Metrics and Observability

### n8n Built-in Metrics

n8n exports Prometheus metrics at the `/metrics` endpoint when `N8N_METRICS_INCLUDE_QUEUE_METRICS=true` is set. These metrics include:

- Queue job counts (waiting, active, completed, failed)
- Processing times
- Worker metrics

**Configuration:**
```yaml
N8N_METRICS: "true"
N8N_METRICS_INCLUDE_QUEUE_METRICS: "true"
```

### Supplemental Redis Metrics Exporter

For deeper Redis-level observability, use the supplemental metrics exporter:

**File:** `ops/scripts/redis_queue_metrics_exporter.py`

**Metrics Exported:**
- `n8n_redis_queue_depth{queue,status}` - Queue depth by status
- `n8n_redis_connection_status{host}` - Redis connection health
- `n8n_redis_memory_usage_bytes` - Redis memory usage

**Usage:**
```bash
# Run as service (exposes HTTP endpoint)
python ops/scripts/redis_queue_metrics_exporter.py

# Or push to Prometheus Push Gateway
PROMETHEUS_PUSH_GATEWAY=http://pushgateway:9091 python ops/scripts/redis_queue_metrics_exporter.py
```

**Grafana Dashboard:**
- Import `docs/grafana-dashboards/queue-health.json` for queue health visualization

**Prometheus Alerts:**
- See `docs/prometheus-alerts/queue-alerts.yml` for alerting rules

For more details, see `docs/PROMETHEUS_INTEGRATION.md`.

## Dead Letter Queue (DLQ) Management

### Overview

The DLQ system provides automated retry logic with exponential backoff for failed jobs. Jobs that exceed maximum retry attempts are moved to a Dead Letter Queue for manual review and recovery.

### Architecture

```
Failed Job → Retry Logic (Exponential Backoff) → Max Retries Exceeded → DLQ → Alert & Manual Recovery
```

### Configuration

Configure retry and DLQ settings in environment config files:

```yaml
queue_retry:
  enabled: true
  max_attempts: 5
  initial_delay_seconds: 1
  max_delay_seconds: 300
  backoff_multiplier: 2
  retryable_errors:
    - "ConnectionError"
    - "TimeoutError"
    - "RateLimitError"

dlq:
  enabled: true
  max_size: 1000
  alert_threshold: 100
  retention_days: 30
  notification_workflow: "notify_slack"
```

### DLQ Manager

**File:** `ops/scripts/redis_queue_dlq_manager.py`

Monitors failed jobs and implements retry logic:

```bash
# Run as continuous service
python ops/scripts/redis_queue_dlq_manager.py

# Process failed jobs once
python ops/scripts/redis_queue_dlq_manager.py --once
```

**Features:**
- Exponential backoff retry (configurable delays)
- Automatic DLQ movement after max retries
- Retry metadata tracking

### DLQ Monitor

**File:** `ops/scripts/redis_queue_dlq_monitor.py`

Monitors DLQ size and sends alerts:

```bash
# Run as continuous service
python ops/scripts/redis_queue_dlq_monitor.py

# Check DLQ status
python ops/scripts/redis_queue_dlq_monitor.py --status
```

**Features:**
- DLQ size monitoring
- Alert threshold detection
- Integration with `notify_slack` workflow

### DLQ Job Recovery

**Workflow:** `workflows/domains/shared/dlq_job_recovery.json`

n8n workflow for manual job recovery:
- List DLQ jobs
- Filter by workflow name, error type, date range
- Replay selected jobs back to queue
- Delete jobs from DLQ after successful replay

**CLI Commands:**
```bash
# Check DLQ status
python ops/scripts/test_redis_queue.py dlq-status

# List DLQ jobs
python ops/scripts/test_redis_queue.py dlq-list

# Replay job from DLQ
python ops/scripts/test_redis_queue.py dlq-replay --job-id job-123
```

### DLQ Schema

**File:** `shared/schemas/dlq_job.schema.json`

Defines the structure of DLQ job entries including:
- Job ID and workflow name
- Failure timestamps and retry count
- Error message and type
- Original payload for replay

For troubleshooting, see `docs/RUNBOOKS.md` DLQ section.

## References

- [n8n Queue Mode Documentation](https://docs.n8n.io/hosting/scaling/queue-mode/)
- [Bull Queue Documentation](https://github.com/OptimalBits/bull)
- [Redis Documentation](https://redis.io/docs/)
- [AWS ElastiCache Documentation](https://docs.aws.amazon.com/elasticache/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## Related Documentation

- `docs/N8N_CONFIGURATION.md` - General n8n configuration guide
- `docs/PROMETHEUS_INTEGRATION.md` - Prometheus metrics integration
- `docs/RUNBOOKS.md` - DLQ troubleshooting runbook
- `docs/ERROR_HANDLING.md` - Queue retry logic
- `docker/docker-compose.n8n.redis.yaml` - Docker Compose configuration
- `docker/redis.conf` - Redis configuration file
- `ops/scripts/test_redis_queue.py` - Queue monitoring script
- `ops/scripts/redis_queue_metrics_exporter.py` - Metrics exporter
- `ops/scripts/redis_queue_dlq_manager.py` - DLQ manager
- `ops/scripts/redis_queue_dlq_monitor.py` - DLQ monitor


