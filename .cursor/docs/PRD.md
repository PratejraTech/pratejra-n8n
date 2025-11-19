<!--
Purpose: Product Requirements Document - Source of Truth for Automation Platform
Created: 2025-11-19 19:57:09
Agent: Init Agent
-->
# Product Requirements Document
## Automation Platform - n8n Workflow Management System

**Version:** 1.0.0  
**Last Updated:** 2025-11-19 19:57:09  
**Status:** Foundation Phase

---

## Executive Summary

### Platform Purpose and Vision
The Automation Platform is a comprehensive n8n-based workflow automation system designed to provide a structured, scalable foundation for managing business processes across multiple domains. The platform enables organizations to standardize workflow creation, management, and operations through a domain-driven architecture with shared resources and governance mechanisms.

### Key Objectives
1. **Standardization**: Establish consistent patterns for workflow creation, naming, and organization
2. **Governance**: Implement agent-based modification control to prevent unintended changes
3. **Scalability**: Support multiple domains (CRM, Infrastructure, Platform, Meta) with shared resources
4. **Maintainability**: Provide clear documentation, schemas, and operational runbooks
5. **Traceability**: Enable comprehensive change tracking and system state documentation

### Target Users/Stakeholders
- **Workflow Developers**: Create and maintain n8n workflows
- **Platform Administrators**: Manage platform configuration and operations
- **Domain Owners**: Oversee domain-specific workflows (CRM, Infrastructure)
- **Operations Teams**: Execute runbooks and handle incidents
- **Agents/Automation**: Automated systems that maintain platform integrity

---

## Platform Architecture

### Directory Structure
The platform follows a strict directory structure defined in `.cursor/rules/folders.mdc`:

```
automation-platform/
├── workflows/
│   ├── platform/          # Platform-wide workflows
│   ├── domain_crm/        # CRM domain workflows
│   ├── domain_infra/      # Infrastructure domain workflows
│   └── meta/              # Meta-level workflows
├── shared/
│   ├── js_snippets/       # Reusable JavaScript code
│   ├── schemas/           # JSON schema definitions
│   └── config/            # Environment configurations
├── docs/                   # Documentation
├── ci/                     # CI/CD scripts
└── .agents/                # Agent tracking and context
```

### Domain Organization

#### Platform Domain (`workflows/platform/`)
Core platform workflows that provide foundational capabilities:
- **error_central_handler.json**: Central error handling for platform-wide error management
- **notify_slack.json**: Slack notification system for alerts and communications
- **log_event.json**: Event logging for platform activity tracking
- **approvals_generic.json**: Generic approval workflow for platform-wide processes

#### CRM Domain (`workflows/domain_crm/`)
Customer relationship management workflows:
- **lead_intake.json**: Capture and process new leads
- **lead_enrichment.json**: Enhance lead data with additional information
- **lead_sync_to_crm.json**: Synchronize leads to CRM systems

#### Infrastructure Domain (`workflows/domain_infra/`)
Infrastructure management workflows:
- **infra_deploy_terraform.json**: Deploy infrastructure using Terraform
- **infra_post_deploy_checks.json**: Post-deployment validation checks

#### Meta Domain (`workflows/meta/`)
Meta-level workflows for platform management:
- **automation_catalog_builder.json**: Build and maintain automation catalog
- **workflow_health_check.json**: Monitor and validate workflow health

### Shared Resources

#### JavaScript Snippets (`shared/js_snippets/`)
Reusable code snippets for common operations:
- **normalize_contact.js**: Normalize contact data structures
- **validate_payload.js**: Validate payload structure and integrity
- **compute_risk_score.js**: Calculate risk scores based on parameters

#### Schemas (`shared/schemas/`)
JSON schema definitions for data validation:
- **contact.schema.json**: Contact data structure schema
- **incident.schema.json**: Incident data structure schema

#### Configuration (`shared/config/`)
Environment-specific configuration files:
- **environments.dev.yaml**: Development environment settings
- **environments.prod.yaml**: Production environment settings

### CI/CD Infrastructure
Scripts for workflow management and environment synchronization:
- **export_workflows.sh**: Export n8n workflows from platform
- **import_workflows.sh**: Import workflows into platform
- **sync_n8n_env.yml**: Synchronize n8n environment configuration

---

## Workflow System

### n8n Workflow Structure
Workflows are defined as JSON files following n8n's workflow format. Each workflow includes:
- **Metadata**: Purpose, creation date, agent information
- **Nodes**: Workflow steps and operations
- **Connections**: Data flow between nodes
- **Credentials**: Required authentication (stored separately)

### Domain-Based Organization
Workflows are organized by domain to:
- Enable domain ownership and responsibility
- Facilitate discovery and maintenance
- Support domain-specific patterns and conventions
- Allow independent evolution of domains

### Workflow Naming Conventions
As defined in `docs/WORKFLOW_NAMING.md`:
- **Format**: `<domain>_<purpose>[_<detail>].json`
- **Domain Values**: `platform`, `domain_crm`, `domain_infra`, `meta`
- **Purpose**: Short verb or noun describing the action
- **Detail**: Optional qualifier for specificity

**Examples:**
- `platform_error_central_handler.json`
- `domain_crm_lead_intake.json`
- `domain_infra_deploy_terraform.json`

### Workflow Lifecycle
1. **Draft**: Workflows in `workflows/draft-workflows/` are under development
2. **Active**: Workflows in `workflows/active-workflows/` are operational
3. **Production**: Workflows in `workflows/prod-workflows/` are production-ready
4. **Archived**: Deprecated workflows moved to archive

---

## Agent System

### Agent Responsibilities
As defined in `AGENTS.md`, agents have two core responsibilities:

1. **Context Capture**: Snapshot files into `.agents/contexts/<timestamp>/<path>`
2. **Header Management**: Ensure header docstrings are present and up-to-date

### Context Capture Mechanism
- On file creation or modification, agents save snapshots preserving directory structure
- Snapshots are timestamped for versioning: `.agents/contexts/YYYY-MM-DD/<relative-path>`
- All actions are logged to `.agents/logs/agent-actions.log`

### Header/Docstring Management
Agents ensure all files have appropriate headers:

**JSON Files**: `_metadata` field at top of object
```json
{
  "_metadata": {
    "purpose": "<description>",
    "created": "YYYY-MM-DD HH:MM",
    "agent": "Agent Name"
  }
}
```

**JavaScript Files**: Comment header
```javascript
/*
 * Purpose: <description>
 * Created/Updated: YYYY-MM-DD HH:MM
 * Agent: Agent Name
 */
```

**YAML Files**: Comment header
```yaml
# Purpose: <description>
# Created/Updated: YYYY-MM-DD HH:MM
# Agent: Agent Name
```

**Markdown Files**: HTML comment header
```markdown
<!--
Purpose: <description>
Created/Updated: YYYY-MM-DD HH:MM
Agent: Agent Name
-->
```

### Modification Restrictions
Agents are strictly constrained:
- ✅ **Allowed**: Adding/updating header docstrings
- ✅ **Allowed**: Creating snapshots
- ❌ **Prohibited**: Modifying business logic
- ❌ **Prohibited**: Changing JSON schema content
- ❌ **Prohibited**: Altering config settings
- ❌ **Prohibited**: Modifying documentation body

### Idempotency
- Re-running agents must not create duplicate snapshots for unchanged files
- Headers are only updated if missing or outdated
- System maintains consistency across multiple agent runs

---

## Data Management

### Schema Definitions
The platform uses JSON schemas for data validation:

#### Contact Schema (`shared/schemas/contact.schema.json`)
Defines the structure for contact data, ensuring consistency across workflows that handle contact information.

#### Incident Schema (`shared/schemas/incident.schema.json`)
Defines the structure for incident data, standardizing incident reporting and tracking.

### Data Contracts
As documented in `docs/DATA_CONTRACTS.md`, data contracts define:
- Expected data structures
- Required fields and types
- Validation rules
- Transformation requirements

### Validation Patterns
- **Schema Validation**: Use JSON schemas to validate data structures
- **Payload Validation**: Use `validate_payload.js` snippet for runtime validation
- **Data Normalization**: Use `normalize_contact.js` for consistent data formats

---

## Configuration Management

### Environment-Specific Configs
Configuration is separated by environment:
- **Development** (`environments.dev.yaml`): Development environment settings
- **Production** (`environments.prod.yaml`): Production environment settings

### Configuration Structure
Configuration files follow YAML format and include:
- API endpoints and credentials
- Environment variables
- Feature flags
- Resource limits and quotas

### Environment Sync Processes
The `ci/sync_n8n_env.yml` script synchronizes configuration across environments, ensuring:
- Consistent configuration structure
- Controlled promotion of changes
- Environment-specific overrides

---

## Error Handling & Operations

### Error Handling Patterns
As documented in `docs/ERROR_HANDLING.md`, the platform implements:

1. **Central Error Handler**: `workflows/platform/error_central_handler.json`
   - Captures all platform-wide errors
   - Routes errors to appropriate handlers
   - Logs errors for analysis

2. **Error Logging**: All errors are logged via `log_event.json` workflow
3. **Error Notification**: Critical errors trigger `notify_slack.json` workflow

### Central Error Handler Workflow
The central error handler provides:
- Unified error processing
- Error categorization and routing
- Error aggregation and reporting
- Integration with monitoring systems

### Runbooks and Operational Procedures
As documented in `docs/RUNBOOKS.md`, runbooks provide:
- Step-by-step operational procedures
- Troubleshooting guides
- Recovery procedures
- Maintenance schedules

### Health Check Mechanisms
The `workflows/meta/workflow_health_check.json` workflow:
- Monitors workflow execution status
- Validates workflow configurations
- Checks dependencies and integrations
- Reports health metrics

---

## Development Workflow

### File Modification Rules
As defined in `.cursorrules`:
- **Only headers/docstrings** can be added to existing files
- **No business logic changes** without explicit user request
- **New files** can be created following naming conventions
- **Versioning** through new files or explicit versioning

### Header/Docstring Requirements
All files must have appropriate headers:
- **Purpose**: Clear description of file purpose
- **Created/Updated**: Timestamp of creation or last update
- **Agent**: Name of agent that created/modified the file

### Version Control Practices
- All changes tracked in version control
- Commit messages reference PRD changes when applicable
- Branch strategy follows domain organization
- Pull requests require review for major changes

### CI/CD Pipeline
The CI/CD pipeline includes:
1. **Export Workflows** (`ci/export_workflows.sh`): Extract workflows from n8n
2. **Import Workflows** (`ci/import_workflows.sh`): Deploy workflows to n8n
3. **Environment Sync** (`ci/sync_n8n_env.yml`): Synchronize configurations
4. **Validation**: Schema validation and workflow health checks

---

## Change Management Process

### PRD as Source of Truth
- `.cursor/docs/PRD.md` is the authoritative source for all platform requirements
- All changes to the platform should be reflected in the PRD
- PRD updates require tracking in `.agents/PRD.md`

### Change Tracking
All PRD changes must be logged in `.agents/PRD.md` with:
- **Timestamp**: YYYY-MM-DD HH:MM:SS
- **Agent Name**: Name of agent making the change
- **Region**: Geographic or logical region (if applicable)
- **Change Description**: Detailed description of the change
- **Approval Status**: Pending, Approved, or Rejected

### Approval Workflow
- **Major Changes**: Require user confirmation before implementation
  - Architecture changes
  - New domain additions
  - Breaking changes to workflows
  - Schema modifications
- **Minor Changes**: Auto-tracked but still logged
  - Typo corrections
  - Formatting improvements
  - Documentation clarifications

### Timestamp and Agent Tracking
Every change is tracked with:
- Precise timestamp for audit trail
- Agent identification for accountability
- Change categorization for impact analysis
- Approval workflow for governance

### Phase Step Documentation
System state is documented after each phase in `.agents/prd_steps/`:
- `phase1-directory-structure.md`: Directory creation state
- `phase2-prd-creation.md`: PRD creation state
- `phase3-change-management.md`: Change management setup state
- Additional phases documented as needed

---

## Future Roadmap

### Planned Enhancements
1. **Workflow Versioning**: Implement semantic versioning for workflows
2. **Testing Framework**: Automated testing for workflow validation
3. **Monitoring Integration**: Enhanced monitoring and alerting
4. **Multi-Region Support**: Support for multiple geographic regions
5. **Workflow Templates**: Reusable workflow templates for common patterns

### Integration Opportunities
1. **External Systems**: Integration with external CRM, ticketing, and monitoring systems
2. **API Gateway**: Centralized API management for workflow triggers
3. **Event Streaming**: Real-time event processing capabilities
4. **Analytics**: Workflow performance analytics and optimization

### Scalability Considerations
1. **Horizontal Scaling**: Support for multiple n8n instances
2. **Workflow Distribution**: Load balancing across instances
3. **Resource Management**: Efficient resource utilization
4. **Performance Optimization**: Workflow execution optimization

---

## Appendix

### Related Documentation
- `AGENTS.md`: Agent responsibilities and behavior
- `docs/WORKFLOW_NAMING.md`: Workflow naming conventions
- `docs/ERROR_HANDLING.md`: Error handling patterns
- `docs/DATA_CONTRACTS.md`: Data contract definitions
- `docs/RUNBOOKS.md`: Operational runbooks
- `.cursor/rules/folders.mdc`: Directory structure specification
- `.cursor/rules/001-init_agent.mdc`: Agent behavior rules

### Glossary
- **Agent**: Automated system that maintains platform integrity
- **Domain**: Logical grouping of related workflows (CRM, Infrastructure, etc.)
- **Workflow**: n8n workflow definition in JSON format
- **Schema**: JSON schema for data validation
- **Snippet**: Reusable JavaScript code
- **PRD**: Product Requirements Document

---

**Document Status**: Active  
**Next Review**: As needed for major changes  
**Maintained By**: Platform Team

