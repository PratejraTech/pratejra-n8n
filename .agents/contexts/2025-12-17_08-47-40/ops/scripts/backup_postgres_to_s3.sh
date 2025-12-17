#!/usr/bin/env bash
# Purpose: Backup n8n Postgres database (pg_dump + gzip) to S3 with a consistent prefix layout
# Created/Updated: 2025-12-17 00:00
# Agent: GPT-5.2

set -euo pipefail

: "${PGHOST:?PGHOST is required}"
: "${PGPORT:=5432}"
: "${PGDATABASE:?PGDATABASE is required}"
: "${PGUSER:?PGUSER is required}"
: "${PGPASSWORD:?PGPASSWORD is required}"

: "${BACKUP_S3_BUCKET:?BACKUP_S3_BUCKET is required}"
: "${BACKUP_S3_PREFIX:=pratejra-automation-hub/postgres-backups}"
: "${AWS_REGION:=us-east-1}"

export PGPASSWORD

TS="$(date -u +"%Y-%m-%d_%H-%M-%S")"
DATE_PREFIX="${TS%_*}"
ARCHIVE="pgdump-${PGDATABASE}-${TS}.sql.gz"

echo "Creating Postgres dump: ${ARCHIVE}"
pg_dump -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" --format=plain --no-owner --no-privileges | gzip -9 > "${ARCHIVE}"

S3_KEY="${BACKUP_S3_PREFIX}/${DATE_PREFIX}/${ARCHIVE}"
echo "Uploading to s3://${BACKUP_S3_BUCKET}/${S3_KEY}"
aws s3 cp "${ARCHIVE}" "s3://${BACKUP_S3_BUCKET}/${S3_KEY}" --region "${AWS_REGION}"

echo "Done."


