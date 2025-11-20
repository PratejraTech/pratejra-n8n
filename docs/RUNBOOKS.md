# Purpose: Operational runbooks and procedures documentation for automation platform
# Created/Updated: 2025-11-20
# Agent: QA_AGENT

# Runbooks - Automation Hub

This document provides operational runbooks for all workflows in the Automation Hub platform. Each runbook includes ownership, risks, rollback procedures, and troubleshooting steps.

## Runbook Template

Each workflow runbook should include:
- **Owner:** Team and primary contact
- **Purpose:** What the workflow does
- **Risk Level:** low | medium | high | critical
- **Dependencies:** Other workflows or services
- **Triggers:** How the workflow is triggered
- **Rollback Steps:** How to revert changes
- **Troubleshooting:** Common issues and solutions
- **Monitoring:** What to monitor and alert on

---

## Shared/Platform Workflows

### Error Central Handler

**Owner:** Platform Engineering (platform-team@example.com)  
**Risk Level:** Critical  
**Purpose:** Central error handling for all platform workflows. Handles errors, retries, and notifications.

**Dependencies:**
- log_event workflow
- notify_slack workflow

**Triggers:**
- Called by other workflows when errors occur
- Receives incident schema payloads

**Rollback Steps:**
1. If error handler itself fails, check n8n instance health
2. Verify log_event and notify_slack workflows are active
3. Check AWS Secrets Manager for required credentials
4. Review n8n execution logs for error handler runs

**Troubleshooting:**
- **Error handler not responding:** Check n8n instance health, verify workflow is active
- **Notifications not sending:** Verify Slack webhook URL in AWS Secrets Manager
- **Logs not appearing:** Check Prometheus endpoint configuration

**Monitoring:**
- Monitor error handler execution success rate
- Alert on error handler failures (critical)
- Track error volume and types

---

### Log Event

**Owner:** Platform Engineering (platform-team@example.com)  
**Risk Level:** High  
**Purpose:** Logs events to Prometheus and other observability systems with correlation IDs.

**Dependencies:** None (standalone)

**Triggers:**
- Called by other workflows to log events
- Receives event schema payloads

**Rollback Steps:**
1. If logging fails, workflow continues (non-blocking)
2. Check Prometheus endpoint availability
3. Verify network connectivity to observability stack

**Troubleshooting:**
- **Events not appearing in Prometheus:** Check endpoint configuration, verify network access
- **Correlation IDs missing:** Verify payload includes correlation_id field
- **High latency:** Check Prometheus endpoint performance

**Monitoring:**
- Monitor log event success rate
- Track event volume
- Alert on logging failures (high priority)

---

### Notify Slack

**Owner:** Platform Engineering (platform-team@example.com)  
**Risk Level:** Medium  
**Purpose:** Sends notifications to Slack channels with configurable formatting and routing.

**Dependencies:** None (standalone)

**Triggers:**
- Called by other workflows for notifications
- Receives notification payloads

**Rollback Steps:**
1. If Slack notification fails, workflow continues (non-blocking)
2. Verify Slack webhook URL in AWS Secrets Manager
3. Check Slack API status

**Troubleshooting:**
- **Notifications not appearing in Slack:** Verify webhook URL, check Slack channel permissions
- **Formatting issues:** Review notification payload structure
- **Rate limiting:** Check Slack API rate limits

**Monitoring:**
- Monitor notification success rate
- Track notification volume
- Alert on repeated failures

---

### Approvals Generic

**Owner:** Platform Engineering (platform-team@example.com), Security Team  
**Risk Level:** High  
**Purpose:** Generic approval workflow for high-risk operations requiring human approval via Slack.

**Dependencies:**
- notify_slack workflow
- log_event workflow

**Triggers:**
- Called by workflows requiring approval (e.g., infra deployments)
- Receives approval request payloads

**Rollback Steps:**
1. If approval workflow fails, operation is blocked (fail-safe)
2. Verify Slack integration is working
3. Check approval timeout settings
4. Manual approval may be required via n8n UI

**Troubleshooting:**
- **Approval requests not appearing:** Check Slack integration, verify channel configuration
- **Approvals timing out:** Review timeout settings, check for approver availability
- **Approval not processing:** Verify Slack response handling

**Monitoring:**
- Monitor approval request success rate
- Track approval response times
- Alert on approval workflow failures (high priority)

---

## CRM Domain Workflows

### Lead Intake

**Owner:** CRM Engineering (crm-team@example.com)  
**Risk Level:** Medium  
**Purpose:** Captures and processes new leads from various sources with validation and normalization.

**Dependencies:**
- validate_payload.js snippet
- normalize_contact.js snippet
- log_event workflow
- error_central_handler workflow

**Triggers:**
- Webhook: `/webhook/lead-intake`
- Receives contact schema payloads

**Rollback Steps:**
1. If lead intake fails, source system should retry
2. Check webhook endpoint availability
3. Verify schema validation is working
4. Review ingested leads in n8n execution history

**Troubleshooting:**
- **Webhook not responding:** Check n8n webhook configuration, verify endpoint is active
- **Validation failures:** Review payload structure against contact.schema.json
- **Normalization errors:** Check normalize_contact.js snippet

**Monitoring:**
- Monitor lead intake success rate
- Track lead volume
- Alert on validation failures (medium priority)

---

### Lead Enrichment

**Owner:** CRM Engineering (crm-team@example.com)  
**Risk Level:** Medium  
**Purpose:** Enriches lead data with additional information from external sources and computes risk scores.

**Dependencies:**
- normalize_contact.js snippet
- compute_risk_score.js snippet
- log_event workflow
- error_central_handler workflow

**Triggers:**
- Called by lead_intake workflow
- Receives contact schema payloads

**Rollback Steps:**
1. If enrichment fails, lead remains with basic data
2. Check external enrichment service availability
3. Verify risk score computation
4. Review enriched leads in execution history

**Troubleshooting:**
- **Enrichment service unavailable:** Check external service status, verify API keys
- **Risk score errors:** Review compute_risk_score.js snippet
- **Slow enrichment:** Check external service performance

**Monitoring:**
- Monitor enrichment success rate
- Track enrichment latency
- Alert on enrichment failures (medium priority)

---

### Lead Sync to CRM

**Owner:** CRM Engineering (crm-team@example.com)  
**Risk Level:** High  
**Purpose:** Synchronizes enriched leads to external CRM systems with error handling and retry logic.

**Dependencies:**
- log_event workflow
- notify_slack workflow
- error_central_handler workflow

**Triggers:**
- Called by lead_enrichment workflow
- Receives contact schema payloads

**Rollback Steps:**
1. If sync fails, lead remains in n8n (not lost)
2. Check external CRM API availability
3. Verify CRM credentials in AWS Secrets Manager
4. Review sync status in execution history
5. Manual sync may be required for failed leads

**Troubleshooting:**
- **CRM API errors:** Check external CRM status, verify API credentials
- **Sync failures:** Review error logs, check payload structure
- **Duplicate leads:** Verify deduplication logic

**Monitoring:**
- Monitor sync success rate (critical)
- Track sync latency
- Alert on sync failures (high priority)
- Monitor for duplicate leads

---

## Infrastructure Domain Workflows

### Infrastructure Deploy (Terraform)

**Owner:** DevOps (devops-team@example.com)  
**Risk Level:** Critical  
**Purpose:** Deploys infrastructure using Terraform triggered by GitHub Actions with approval gates.

**Dependencies:**
- approvals_generic workflow
- log_event workflow
- notify_slack workflow
- error_central_handler workflow

**Triggers:**
- Webhook: `/webhook/infra-deploy`
- Triggered by GitHub Actions
- Receives infra_deploy schema payloads

**Rollback Steps:**
1. **Immediate rollback:** Use Terraform rollback workflow if available
2. **Manual rollback:** Run `terraform destroy` or `terraform apply` with previous state
3. **State recovery:** Restore Terraform state from S3 backup
4. **Infrastructure recovery:** Follow infrastructure-specific recovery procedures
5. **Notify team:** Send Slack notification about rollback

**Troubleshooting:**
- **Terraform apply fails:** Check Terraform state, verify AWS credentials, review Terraform logs
- **Approval not received:** Verify Slack integration, check approver availability
- **State lock issues:** Check for concurrent Terraform runs, release state lock if needed

**Monitoring:**
- Monitor deployment success rate (critical)
- Track deployment duration
- Alert on deployment failures (critical)
- Monitor infrastructure health post-deployment

---

### Infrastructure Post-Deploy Checks

**Owner:** DevOps (devops-team@example.com)  
**Risk Level:** High  
**Purpose:** Validates infrastructure deployment success through health checks and validation tests.

**Dependencies:**
- log_event workflow
- notify_slack workflow
- error_central_handler workflow

**Triggers:**
- Called by infra_deploy_terraform workflow
- Receives infra_deploy schema payloads

**Rollback Steps:**
1. If checks fail, trigger rollback in infra_deploy_terraform workflow
2. Review check results in execution logs
3. Manually verify infrastructure if needed
4. Re-run checks after fixes

**Troubleshooting:**
- **Health checks failing:** Verify infrastructure is actually deployed, check endpoint availability
- **Check timeouts:** Review timeout settings, check network connectivity
- **False positives:** Review check logic, verify test endpoints

**Monitoring:**
- Monitor check success rate
- Track check duration
- Alert on check failures (high priority)

---

## Meta Domain Workflows

### Automation Catalog Builder

**Owner:** Platform Engineering (platform-team@example.com)  
**Risk Level:** Low  
**Purpose:** Automatically generates and updates the workflows catalog and ownership metadata.

**Dependencies:** None (standalone)

**Triggers:**
- Scheduled (daily)
- Manual trigger
- Triggered on workflow file changes

**Rollback Steps:**
1. If catalog generation fails, previous catalog remains
2. Manually run `ops/scripts/generate_catalog.py`
3. Review catalog generation logs

**Troubleshooting:**
- **Catalog not updating:** Check script execution, verify workflow file structure
- **Metadata errors:** Review workflow JSON files for structure issues
- **Generation failures:** Check Python dependencies, verify file permissions

**Monitoring:**
- Monitor catalog generation success
- Track catalog update frequency
- Alert on generation failures (low priority)

---

### Workflow Health Check

**Owner:** Platform Engineering (platform-team@example.com)  
**Risk Level:** Medium  
**Purpose:** Monitors workflow health, execution success rates, and triggers alerts for degraded workflows.

**Dependencies:**
- log_event workflow
- notify_slack workflow

**Triggers:**
- Scheduled (hourly)
- Manual trigger

**Rollback Steps:**
1. If health check fails, review n8n instance health
2. Check Prometheus metrics availability
3. Verify workflow execution history access

**Troubleshooting:**
- **Health check not running:** Verify schedule configuration, check n8n instance
- **False alerts:** Review alert thresholds, verify metric calculations
- **Missing metrics:** Check Prometheus integration, verify metric export

**Monitoring:**
- Monitor health check execution
- Track workflow health metrics
- Alert on health check failures (medium priority)

---

## General Troubleshooting

### Workflow Not Executing

1. Check workflow is active in n8n
2. Verify webhook endpoint is configured
3. Check n8n instance health
4. Review execution history for errors
5. Verify credentials and secrets

### Schema Validation Failures

1. Review payload against schema definition
2. Check schema version compatibility
3. Verify validate_payload.js snippet
4. Review validation error messages

### External Service Integration Issues

1. Check external service status
2. Verify API credentials in AWS Secrets Manager
3. Review network connectivity
4. Check rate limits and quotas

### Performance Issues

1. Review workflow execution duration
2. Check for bottlenecks in workflow nodes
3. Verify external service performance
4. Review n8n instance resource usage

---

## Emergency Contacts

- **Platform Engineering:** platform-team@example.com
- **DevOps:** devops-team@example.com
- **CRM Engineering:** crm-team@example.com
- **On-Call:** See PagerDuty rotation

---

## Change Log

- 2025-11-20: Initial runbooks created (QA_AGENT)
