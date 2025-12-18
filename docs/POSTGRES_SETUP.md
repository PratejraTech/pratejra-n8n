# PostgreSQL Setup Guide for n8n

**Purpose:** Comprehensive guide for PostgreSQL database configuration, deployment, and operations for n8n automation hub  
**Created/Updated:** 2025-12-17  
**Agent:** GPT-5.2

## Overview

This guide covers PostgreSQL setup for n8n across different deployment scenarios, from local development to production environments. PostgreSQL is the recommended database for production n8n instances due to its reliability, performance, and feature set.

## Table of Contents

1. [Development Setup (Docker Compose)](#development-setup-docker-compose)
2. [Production Setup (Managed Database)](#production-setup-managed-database)
3. [Connection Configuration](#connection-configuration)
4. [Schema Initialization](#schema-initialization)
5. [Backup and Restore](#backup-and-restore)
6. [Performance Tuning](#performance-tuning)
7. [Security Hardening](#security-hardening)
8. [Monitoring and Health Checks](#monitoring-and-health-checks)
9. [Troubleshooting](#troubleshooting)

## Development Setup (Docker Compose)

### Quick Start

The repository includes a self-contained Docker Compose setup for local development:

**Files:**
- `docker/docker-compose.n8n.postgres.yaml` - Docker Compose configuration
- `docker/n8n.postgres.env.example` - Environment variable template

**Steps:**

1. Copy the environment template:
```bash
cp docker/n8n.postgres.env.example docker/n8n.postgres.env
```

2. Edit `docker/n8n.postgres.env` and set minimum required values:
```bash
# Required: Stable encryption key (must persist across restarts)
N8N_ENCRYPTION_KEY=your-long-random-encryption-key-here

# Required: Postgres password
POSTGRES_PASSWORD=your-secure-password-here

# Optional: Customize database name and user
POSTGRES_DB=n8n
POSTGRES_USER=n8n
```

3. Start services:
```bash
docker compose -f docker/docker-compose.n8n.postgres.yaml up -d
```

4. Verify health:
```bash
# Check n8n health
curl -fsS http://localhost:5678/healthz

# Check Postgres health (from within container)
docker exec n8n-postgres pg_isready -U n8n -d n8n
```

### Development Configuration Details

**Postgres Container:**
- Image: `postgres:16.6-alpine`
- Port: 5432 (internal only, not exposed to host)
- Data persistence: Docker volume `postgres_data`
- Health check: `pg_isready` every 10 seconds

**n8n Container:**
- Connects to Postgres via service name `postgres`
- Database connection configured via environment variables
- Waits for Postgres health check before starting

**Important Notes:**
- `N8N_ENCRYPTION_KEY` must remain stable across restarts or encrypted credentials will break
- Default binding is localhost-only (`127.0.0.1:5678`)
- To expose externally, set `N8N_BIND_ADDR=0.0.0.0` and configure authentication

## Production Setup (Managed Database)

### AWS RDS PostgreSQL

**Recommended Configuration:**
- Engine: PostgreSQL 15.x or 16.x
- Instance class: `db.t3.medium` (minimum) or `db.t3.large` (recommended)
- Storage: 100GB+ with autoscaling enabled
- Multi-AZ: Enabled for production
- Backup retention: 7-30 days
- Encryption: At rest and in transit

**Connection Details:**
- Host: RDS endpoint (e.g., `n8n-db.xxxxx.us-east-1.rds.amazonaws.com`)
- Port: 5432
- Database: `n8n`
- User: Created via RDS (not `postgres` superuser)
- Password: Stored in AWS Secrets Manager

**Security:**
- VPC: Deploy in private subnet
- Security groups: Restrict access to n8n application servers only
- SSL/TLS: Require SSL connections (`sslmode=require`)

### Other Managed Database Services

**Google Cloud SQL:**
- Similar configuration to RDS
- Use Cloud SQL Proxy for secure connections
- Connection string format: `postgresql://user:pass@/dbname?host=/cloudsql/project:region:instance`

**Azure Database for PostgreSQL:**
- Flexible Server recommended
- Use Azure Private Link for secure connectivity
- Connection string format: `postgresql://user@servername:password@servername.postgres.database.azure.com:5432/dbname?sslmode=require`

## Connection Configuration

### Environment Variables

n8n uses the following environment variables for Postgres connection:

```bash
# Database type (must be 'postgresdb' for PostgreSQL)
DB_TYPE=postgresdb

# Connection details
DB_POSTGRESDB_HOST=your-db-host
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n_user

# Password (retrieve from secrets manager in production)
DB_POSTGRESDB_PASSWORD=your-password

# Optional: Connection pool settings
DB_POSTGRESDB_POOL_SIZE=10
DB_POSTGRESDB_TIMEOUT=30000
```

### Connection String Format

**Standard format:**
```
postgresql://{user}:{password}@{host}:{port}/{database}
```

**With SSL:**
```
postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=require
```

**Example:**
```
postgresql://n8n_user:secret@n8n-db.example.com:5432/n8n?sslmode=require
```

### Connection Pooling

For high-traffic production environments, consider using PgBouncer or similar connection pooler:

**Benefits:**
- Reduces connection overhead
- Improves performance under load
- Better resource utilization

**Configuration:**
- Pool mode: Transaction
- Max connections: 100-200 (adjust based on n8n instance count)
- Default pool size: 25 connections per n8n instance

## Schema Initialization

### n8n Core Schema

n8n automatically creates its core schema on first connection. No manual schema creation is required.

**Core Tables:**
- `credentials_entity` - Encrypted credentials storage
- `execution_entity` - Workflow execution history
- `workflow_entity` - Workflow definitions
- `settings` - n8n settings
- And other internal tables

### Webhook Registry Schema

The webhook dispatch system requires an additional table for event routing:

**File:** `ops/scripts/webhook_registry.sql`

**Apply schema:**
```bash
# Using psql
psql -h your-db-host -U n8n_user -d n8n -f ops/scripts/webhook_registry.sql

# Using Docker
docker exec -i n8n-postgres psql -U n8n -d n8n < ops/scripts/webhook_registry.sql
```

**Schema Details:**
- Table: `public.webhook_registry`
- Purpose: Routes events to workflows based on event type
- Key columns:
  - `event_type` - Event type identifier (unique)
  - `target_workflow_name` - Workflow name for routing
  - `is_active` - Enable/disable routing
  - `required_payload_fields` - JSONB array of required fields

**Verification:**
```sql
-- Check table exists
SELECT * FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'webhook_registry';

-- Check indexes
SELECT indexname, indexdef FROM pg_indexes 
WHERE tablename = 'webhook_registry';
```

## Backup and Restore

### Automated Backups

**GitHub Actions Backup:**
- Workflow: `.github/workflows/backup-to-s3.yaml`
- Frequency: Daily
- Location: `s3://automation-hub-{env}-workflows/backups/`
- Retention: 30 days (dev), 90 days (prod)

### Manual Backup Procedures

**Full Database Backup:**
```bash
# Using pg_dump
pg_dump -h your-db-host -U n8n_user -d n8n -F c -f n8n_backup_$(date +%Y%m%d).dump

# Compressed backup
pg_dump -h your-db-host -U n8n_user -d n8n -F c -Z 9 -f n8n_backup_$(date +%Y%m%d).dump.gz
```

**Workflow-Only Backup:**
```bash
# Export workflows via n8n API (recommended)
python ops/scripts/n8n_gitops.py export
```

**Postgres Data-Only Backup:**
```bash
# Backup specific tables
pg_dump -h your-db-host -U n8n_user -d n8n -t workflow_entity -t execution_entity -F c -f workflows_backup.dump
```

### Restore Procedures

**Full Database Restore:**
```bash
# Stop n8n instance first
# Restore from backup
pg_restore -h your-db-host -U n8n_user -d n8n -c n8n_backup_20251217.dump

# Verify restore
psql -h your-db-host -U n8n_user -d n8n -c "SELECT COUNT(*) FROM workflow_entity;"
```

**Workflow Restore:**
```bash
# Import workflows via n8n API
python ops/scripts/n8n_gitops.py import
```

**Important Notes:**
- Always backup before restore
- Ensure `N8N_ENCRYPTION_KEY` matches the backup environment
- Test restore procedures in non-production first
- Document restore runbooks: `ops/backups/restore_runbook_n8n_postgres.md`

## Performance Tuning

### Database Configuration

**Recommended PostgreSQL Settings (postgresql.conf):**

```ini
# Memory settings (adjust based on instance size)
shared_buffers = 256MB          # 25% of RAM for small instances
effective_cache_size = 1GB      # 50-75% of RAM
work_mem = 16MB                 # Per operation memory
maintenance_work_mem = 128MB    # For VACUUM, CREATE INDEX

# Connection settings
max_connections = 100           # Adjust based on pooler usage
max_worker_processes = 4        # CPU cores

# Query performance
random_page_cost = 1.1          # For SSD storage
effective_io_concurrency = 200  # For SSD storage

# Logging (for troubleshooting)
log_min_duration_statement = 1000  # Log slow queries (>1s)
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

### Index Optimization

**Monitor slow queries:**
```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**Common indexes for n8n:**
```sql
-- Execution history (if querying by date)
CREATE INDEX IF NOT EXISTS idx_execution_entity_started_at 
ON execution_entity(started_at);

-- Workflow lookups
CREATE INDEX IF NOT EXISTS idx_workflow_entity_name 
ON workflow_entity(name);
```

### Connection Pooling

**PgBouncer Configuration (pgbouncer.ini):**
```ini
[databases]
n8n = host=your-db-host port=5432 dbname=n8n

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
```

## Security Hardening

### Authentication

**Use strong passwords:**
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, symbols
- Store in AWS Secrets Manager or similar

**Limit user privileges:**
```sql
-- Create dedicated user (not superuser)
CREATE USER n8n_user WITH PASSWORD 'secure-password';

-- Grant only necessary privileges
GRANT CONNECT ON DATABASE n8n TO n8n_user;
GRANT USAGE ON SCHEMA public TO n8n_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO n8n_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO n8n_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO n8n_user;
```

### Network Security

**Firewall Rules:**
- Restrict access to n8n application servers only
- Use security groups (AWS) or firewall rules (GCP/Azure)
- Block public internet access

**SSL/TLS:**
- Require SSL connections: `sslmode=require`
- Use SSL certificates from trusted CAs
- Rotate certificates regularly

### Encryption

**At Rest:**
- Enable database encryption (RDS, Cloud SQL, Azure)
- Use encrypted volumes for self-managed instances

**In Transit:**
- Require SSL/TLS for all connections
- Use strong cipher suites
- Disable weak protocols (SSLv2, SSLv3)

### Audit Logging

**Enable PostgreSQL logging:**
```ini
# Log all connections
log_connections = on
log_disconnections = on

# Log authentication failures
log_authentication_failures = on

# Log DDL statements
log_statement = 'ddl'
```

**Monitor access:**
```sql
-- View recent connections
SELECT datname, usename, application_name, client_addr, state, query_start
FROM pg_stat_activity
WHERE datname = 'n8n'
ORDER BY query_start DESC;
```

## Monitoring and Health Checks

### Health Check Endpoints

**n8n Health:**
```bash
curl http://localhost:5678/healthz
```

**Postgres Health:**
```bash
# From application
psql -h your-db-host -U n8n_user -d n8n -c "SELECT 1;"

# Using pg_isready
pg_isready -h your-db-host -U n8n_user -d n8n
```

### Key Metrics to Monitor

**Database Metrics:**
- Connection count
- Query performance (p95, p99 latencies)
- Replication lag (if using replicas)
- Disk usage
- CPU and memory utilization

**n8n-Specific Metrics:**
- Workflow execution count
- Failed executions
- Average execution duration
- Database query time

### Prometheus Integration

**Postgres Exporter:**
- Deploy `prometheuscommunity/postgres-exporter`
- Scrape metrics: `postgres_exporter:9187`
- Key metrics: `pg_stat_database`, `pg_stat_statements`

**Grafana Dashboards:**
- Use provided dashboards in `docs/grafana-dashboards/`
- Monitor: `workflow-health.json`, `infra-metrics.json`

## Troubleshooting

### Common Issues

**Connection Refused:**
```bash
# Check Postgres is running
docker ps | grep postgres
# or
systemctl status postgresql

# Check firewall rules
# Check security groups (AWS)
# Verify host/port configuration
```

**Authentication Failed:**
```bash
# Verify credentials
psql -h your-db-host -U n8n_user -d n8n

# Check pg_hba.conf (if self-managed)
# Verify user exists and has correct privileges
```

**Slow Queries:**
```sql
-- Identify slow queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';

-- Check for locks
SELECT * FROM pg_locks WHERE NOT granted;
```

**Database Full:**
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('n8n'));

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Maintenance Tasks

**Vacuum:**
```sql
-- Analyze tables
ANALYZE;

-- Vacuum (reclaim space)
VACUUM;

-- Vacuum full (requires exclusive lock)
VACUUM FULL;
```

**Reindex:**
```sql
-- Reindex all tables
REINDEX DATABASE n8n;
```

## References

- n8n Configuration: `docs/N8N_CONFIGURATION.md`
- Docker Compose Setup: `docs/RUNTIME_COMPOSE_POSTGRES.md`
- Webhook Registry Schema: `ops/scripts/webhook_registry.sql`
- Backup Procedures: `ops/backups/restore_runbook_n8n_postgres.md`
- Secrets Management: `docs/SECRETS_STRATEGY.md`
