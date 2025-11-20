# Purpose: Release governance procedures for workflow promotion and rollback
# Created/Updated: 2025-11-20
# Agent: ARCHITECT_AGENT

# Release Governance - Automation Hub

## Overview

This document defines the release governance process for promoting workflows through environments (dev → staging → prod) and rollback procedures.

## Release Promotion Workflow

### Environment Promotion Path

```
Development → Staging → Production
```

### Promotion Criteria

Before promoting a workflow to the next environment:

1. **Validation:**
   - All tests pass in current environment
   - Schema validation successful
   - Workflow executes successfully
   - No critical errors in execution history

2. **Documentation:**
   - Runbook updated in `docs/RUNBOOKS.md`
   - Ownership.yaml updated
   - Workflows catalog updated
   - Architecture.mdc updated if structural changes

3. **Approval:**
   - QA_AGENT approval for staging promotion
   - ARCHITECT_AGENT approval for production promotion
   - Security review for high-risk workflows

### Promotion Process

#### Dev → Staging

1. **Trigger:** Manual via GitHub Actions workflow dispatch
2. **Validation:** Run validation workflow
3. **Deployment:** Deploy to staging via `deploy-workflows.yml`
4. **Verification:** Run smoke tests in staging
5. **Approval:** QA_AGENT reviews and approves
6. **Notification:** Slack notification on completion

#### Staging → Production

1. **Trigger:** Manual via GitHub Actions workflow dispatch (requires approval)
2. **Pre-deployment:**
   - Review staging execution history
   - Verify all staging tests pass
   - Check for any staging incidents
3. **Deployment:** Deploy to production via `deploy-workflows.yml`
4. **Post-deployment:**
   - Run post-deploy checks
   - Monitor workflow health
   - Verify metrics are emitting
5. **Approval:** ARCHITECT_AGENT reviews and approves
6. **Notification:** Slack notification to production channels

## Rollback Procedures

### Automatic Rollback

Automatic rollback triggers:
- Deployment validation fails
- Post-deploy checks fail
- Critical errors detected within 5 minutes of deployment

### Manual Rollback

#### Immediate Rollback (< 15 minutes)

1. **Identify:** Determine which workflow version to rollback to
2. **Backup:** Current production state is automatically backed up
3. **Restore:** Use previous workflow version from backup
4. **Deploy:** Deploy previous version via `deploy-workflows.yml`
5. **Verify:** Run post-deploy checks
6. **Notify:** Send Slack notification about rollback

#### Delayed Rollback (> 15 minutes)

1. **Assess:** Evaluate impact and determine rollback necessity
2. **Plan:** Create rollback plan with ARCHITECT_AGENT approval
3. **Execute:** Follow immediate rollback steps
4. **Document:** Document rollback reason and lessons learned
5. **Post-mortem:** Schedule post-mortem if critical issue

### Rollback Sources

1. **Git History:** Previous workflow version from git
2. **S3 Backups:** Workflow backups from S3 (daily backups)
3. **n8n Export:** Export from n8n instance (if available)

## Release Bundles

### Bundle Structure

Release bundles contain:
- Workflow JSON files
- Schema files (if changed)
- JS snippets (if changed)
- Configuration updates
- Documentation updates

### Bundle Creation

```bash
# Create release bundle
./ops/scripts/create_release_bundle.sh --version 1.0.0 --environment prod
```

Bundle includes:
- All workflow files changed in release
- Version manifest
- Deployment instructions
- Rollback instructions

### Bundle Deployment

1. **Validate Bundle:** Verify bundle structure and contents
2. **Pre-deployment Backup:** Create backup of current state
3. **Deploy Bundle:** Deploy all components in bundle
4. **Verify Deployment:** Run validation and health checks
5. **Monitor:** Monitor for 30 minutes post-deployment

## Version Management

### Versioning Scheme

- **Workflow Versions:** Semantic versioning (1.0.0, 1.1.0, 2.0.0)
- **Schema Versions:** Semantic versioning (v1, v1.1, v2)
- **Release Versions:** Date-based (2025-11-20) or semantic (1.0.0)

### Version Tracking

- Versions tracked in `workflows/metadata/workflows_catalog.yaml`
- Version history in git commits
- Release notes in `.agents/reports/` phase reports

## Approval Gates

### Staging Promotion

**Required Approvals:**
- QA_AGENT: Test validation approval
- BACKEND_AGENT: Implementation review (if workflow changes)

### Production Promotion

**Required Approvals:**
- QA_AGENT: Test validation approval
- ARCHITECT_AGENT: Architecture and governance approval
- Security Team: Security review (for high-risk workflows)

### Emergency Deployments

For critical fixes:
1. ARCHITECT_AGENT approval required
2. Post-deployment review mandatory
3. Documentation update within 24 hours

## Compliance Requirements

### Pre-Deployment

- [ ] All tests pass
- [ ] Schema validation successful
- [ ] Documentation updated
- [ ] Runbook created/updated
- [ ] Ownership.yaml updated
- [ ] Workflows catalog updated
- [ ] Security review completed (if high-risk)

### Post-Deployment

- [ ] Post-deploy checks pass
- [ ] Metrics emitting correctly
- [ ] No critical errors
- [ ] Health checks passing
- [ ] Team notified

## Rollback Decision Matrix

| Scenario | Action | Authority |
|----------|--------|-----------|
| Critical error in first 5 min | Automatic rollback | System |
| High error rate (>10%) | Manual rollback | ARCHITECT_AGENT |
| Performance degradation | Assess and decide | ARCHITECT_AGENT + QA_AGENT |
| Data integrity issues | Immediate rollback | ARCHITECT_AGENT |
| Non-critical issues | Monitor and fix | BACKEND_AGENT |

## Release Communication

### Pre-Deployment

- Notify team via Slack (#automation-deployments)
- Include: workflow name, version, deployment time
- Request approval if required

### Post-Deployment

- Success notification with metrics
- Failure notification with rollback status
- Include: deployment summary, health status

## Release History

Release history tracked in:
- Git commit history
- Phase reports in `.agents/reports/`
- Deployment logs in GitHub Actions
- S3 backup manifests

## Best Practices

1. **Always test in dev before staging**
2. **Never skip staging for production**
3. **Always create backups before deployment**
4. **Monitor closely for first 30 minutes**
5. **Document all deployments and rollbacks**
6. **Review and learn from incidents**

## References

- See `docs/RUNBOOKS.md` for workflow-specific rollback procedures
- See `.github/workflows/deploy-workflows.yml` for deployment automation
- See `.github/workflows/backup-to-s3.yaml` for backup procedures
- See `workflows/metadata/ownership.yaml` for workflow ownership

