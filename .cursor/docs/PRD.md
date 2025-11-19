<!--
Purpose: Product Requirements Document - Source of truth for automation platform
Created: 2025-11-19 20:18:23
Agent: PRD Agent
-->

# Product Requirements Document (PRD)
## Automation Platform - n8n Workflow Management System

**Version**: 1.0.0  
**Last Updated**: 2025-11-19 20:18:23  
**Status**: Active Development

---

## 1. Executive Summary

### 1.1 Platform Purpose and Vision

The Automation Platform is a comprehensive n8n-based workflow automation system designed to provide a structured, scalable, and maintainable approach to workflow management. The platform enables organizations to automate business processes across multiple domains while maintaining strict governance, documentation, and operational excellence.

### 1.2 Key Objectives

- **Centralized Workflow Management**: Provide a single source of truth for all automation workflows
- **Domain-Based Organization**: Organize workflows by business domains (Platform, CRM, Infrastructure, Meta)
- **Governance and Control**: Implement agent-based modification control to prevent unintended changes
- **Operational Excellence**: Ensure error handling, monitoring, and runbook documentation
- **Scalability**: Support growth through shared resources, schemas, and reusable components

### 1.3 Target Users and Stakeholders

- **Platform Engineers**: Build and maintain workflow infrastructure
- **Domain Experts**: Create and manage domain-specific workflows (CRM, Infrastructure)
- **Operations Teams**: Monitor, maintain, and troubleshoot workflows
- **Developers**: Use shared resources (JS snippets, schemas) in workflow development
- **Agents**: Automated systems that manage context, documentation, and change tracking

---

## 2. Platform Architecture

### 2.1 Directory Structure

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
├── docs/                  # Documentation
├── ci/                    # CI/CD scripts
├── .cursor/
│   └── docs/              # PRD and design docs
└── .agents/               # Agent management
    ├── contexts/          # File snapshots
    ├── logs/              # Agent action logs
    ├── prd_steps/         # Phase documentation
    └── PRD.md             # Change log
```

### 2.2 Domain Organization

#### 2.2.1 Platform Domain
**Location**: `workflows/platform/`

Core platform workflows that provide foundational services:
- `error_central_handler.json`: Central error handling for all workflows
- `notify_slack.json`: Slack notification service
- `log_event.json`: Event logging service
- `approvals_generic.json`: Generic approval workflow

#### 2.2.2 CRM Domain
**Location**: `workflows/domain_crm/`

Customer relationship management workflows:
- `lead_intake.json`: Capture and process new leads
- `lead_enrichment.json`: Enrich lead data with additional information
- `lead_sync_to_crm.json`: Synchronize leads to CRM systems

#### 2.2.3 Infrastructure Domain
**Location**: `workflows/domain_infra/`

Infrastructure automation workflows:
- `infra_deploy_terraform.json`: Terraform-based infrastructure deployment
- `infra_post_deploy_checks.json`: Post-deployment validation and checks

#### 2.2.4 Meta Domain
**Location**: `workflows/meta/`

Meta-level workflows for platform management:
- `automation_catalog_builder.json`: Build and maintain automation catalog
- `workflow_health_check.json`: Monitor and check workflow health

### 2.3 Shared Resources

#### 2.3.1 JavaScript Snippets
**Location**: `shared/js_snippets/`

Reusable JavaScript functions for workflows:
- `normalize_contact.js`: Normalize contact data structures
- `validate_payload.js`: Validate payload structure and integrity
- `compute_risk_score.js`: Calculate risk scores based on parameters

#### 2.3.2 JSON Schemas
**Location**: `shared/schemas/`

Data structure definitions:
- `contact.schema.json`: Contact data schema
- `incident.schema.json`: Incident data schema

#### 2.3.3 Configuration Files
**Location**: `shared/config/`

Environment-specific configurations:
- `environments.dev.yaml`: Development environment settings
- `environments.prod.yaml`: Production environment settings

### 2.4 CI/CD Infrastructure

**Location**: `ci/`

Automation scripts for workflow management:
- `export_workflows.sh`: Export workflows from n8n
- `import_workflows.sh`: Import workflows into n8n
- `sync_n8n_env.yml`: Synchronize n8n environment configuration

---

## 3. Workflow System

### 3.1 n8n Workflow Structure

All workflows are n8n-compatible JSON files containing:
- **Metadata**: Purpose, creation date, agent information
- **Nodes**: Workflow nodes defining the automation logic
- **Connections**: Node connections defining workflow execution flow
- **Credentials**: Required authentication credentials (stored separately)

### 3.2 Domain-Based Organization

Workflows are organized by business domain to:
- Improve discoverability
- Enable domain-specific governance
- Support team ownership models
- Facilitate maintenance and updates

### 3.3 Workflow Naming Conventions

**Format**: `<domain>_<purpose>[_<detail>].json`

**Examples**:
- `platform_error_central_handler.json`
- `domain_crm_lead_intake.json`
- `domain_infra_deploy_terraform.json`
- `meta_automation_catalog_builder.json`

**Rules**:
- Use lowercase with underscores
- Domain prefix indicates workflow category
- Purpose describes the primary function
- Optional detail provides additional context

### 3.4 Workflow Lifecycle

1. **Draft**: Workflows in development (`workflows/draft-workflows/`)
2. **Active**: Production-ready workflows in domain directories
3. **Production**: Deployed and monitored workflows (`workflows/prod-workflows/`)

---

## 4. Agent System

### 4.1 Agent Responsibilities

Agents have two core responsibilities:
1. **Context Capture**: Snapshot files into `.agents/contexts/` for versioning
2. **Header Management**: Ensure all files have proper docstring headers

### 4.2 Context Capture Mechanism

- **Trigger**: On file creation or modification
- **Storage**: `.agents/contexts/<timestamp>/<relative-path>`
- **Purpose**: Maintain version history and enable rollback
- **Idempotency**: No duplicate snapshots for unchanged files

### 4.3 Header/Docstring Management

All files must include headers with:
- **Purpose**: Short description of file purpose
- **Created/Updated**: Timestamp (YYYY-MM-DD HH:MM)
- **Agent**: Name of agent that created/updated the file

**Format by file type**:
- **JSON**: `_metadata` object at root level
- **JavaScript**: Multi-line comment block
- **YAML**: Comment lines
- **Markdown**: HTML comment block

### 4.4 Modification Restrictions

**Strict Rules**:
- ✅ **Allowed**: Adding/updating headers only
- ❌ **Prohibited**: 
  - Modifying business logic
  - Changing JSON schema content
  - Altering config settings
  - Modifying documentation body
  - Structural changes

**Enforcement**: Agents self-check and reject prohibited modifications

---

## 5. Data Management

### 5.1 Schema Definitions

**Location**: `shared/schemas/`

JSON Schema files define data structures:
- **contact.schema.json**: Contact data validation schema
- **incident.schema.json**: Incident data validation schema

**Usage**: Workflows reference schemas for data validation

### 5.2 Data Contracts

**Documentation**: `docs/DATA_CONTRACTS.md`

Defines:
- Data structure requirements
- Field definitions and types
- Validation rules
- Contract versioning

### 5.3 Validation Patterns

- **Schema Validation**: Use JSON schemas for structure validation
- **Payload Validation**: Use `validate_payload.js` snippet
- **Data Normalization**: Use `normalize_contact.js` for consistency

---

## 6. Configuration Management

### 6.1 Environment-Specific Configs

**Locations**:
- `shared/config/environments.dev.yaml`: Development settings
- `shared/config/environments.prod.yaml`: Production settings

### 6.2 Configuration Structure

YAML files contain:
- Environment variables
- API endpoints
- Credential references
- Feature flags
- Resource limits

### 6.3 Environment Sync Processes

**Script**: `ci/sync_n8n_env.yml`

Synchronizes:
- Environment configurations
- Credential mappings
- Variable definitions
- Workflow settings

---

## 7. Error Handling & Operations

### 7.1 Error Handling Patterns

**Documentation**: `docs/ERROR_HANDLING.md`

**Central Handler**: `workflows/platform/error_central_handler.json`
- Catches and processes all workflow errors
- Routes errors to appropriate handlers
- Logs errors for analysis
- Notifies stakeholders

### 7.2 Central Error Handler Workflow

**Purpose**: Unified error management across all workflows

**Features**:
- Error categorization
- Retry logic
- Escalation paths
- Notification routing

### 7.3 Runbooks and Operational Procedures

**Documentation**: `docs/RUNBOOKS.md`

Contains:
- Operational procedures
- Troubleshooting guides
- Recovery procedures
- Maintenance schedules

### 7.4 Health Check Mechanisms

**Workflow**: `workflows/meta/workflow_health_check.json`

**Functionality**:
- Monitor workflow execution
- Detect failures and anomalies
- Generate health reports
- Alert on degradation

---

## 8. Development Workflow

### 8.1 File Modification Rules

**Core Principle**: Only headers can be modified by agents

**Process**:
1. Agent detects file change
2. Creates snapshot in `.agents/contexts/`
3. Adds/updates header if needed
4. Logs action in `.agents/logs/agent-actions.log`
5. No other modifications allowed

### 8.2 Header/Docstring Requirements

**Mandatory Fields**:
- Purpose (required)
- Created/Updated timestamp (required)
- Agent name (required)

**Format Compliance**: Must match file type conventions

### 8.3 Version Control Practices

- All changes tracked in git
- Snapshots stored in `.agents/contexts/`
- Change log in `.agents/PRD.md`
- Phase documentation in `.agents/prd_steps/`

### 8.4 CI/CD Pipeline

**Scripts**:
- `export_workflows.sh`: Export for version control
- `import_workflows.sh`: Import to n8n instances
- `sync_n8n_env.yml`: Environment synchronization

---

## 9. Change Management Process

### 9.1 PRD as Source of Truth

**Location**: `.cursor/docs/PRD.md`

- Authoritative document for all platform decisions
- All changes must align with PRD
- PRD updates require formal process

### 9.2 Change Tracking

**Location**: `.agents/PRD.md`

**Required Fields**:
- **Timestamp**: YYYY-MM-DD HH:MM:SS
- **Agent**: Name of agent making change
- **Region**: Geographic or logical region (if applicable)
- **Change Description**: Detailed description of change
- **Approval Status**: Pending/Approved/Rejected

### 9.3 Approval Workflow for Major Changes

**Major Changes** (require user confirmation):
- Architecture changes
- New domain additions
- Process modifications
- Governance rule changes

**Minor Changes** (auto-tracked):
- Typo corrections
- Formatting improvements
- Documentation clarifications

### 9.4 Timestamp and Agent Tracking

All changes logged with:
- Precise timestamp
- Agent identification
- Change classification
- Approval workflow status

---

## 10. Future Roadmap

### 10.1 Planned Enhancements

- **Workflow Templates**: Reusable workflow templates
- **Advanced Monitoring**: Enhanced health check capabilities
- **Multi-Environment Support**: Additional environment configurations
- **API Integration**: REST API for workflow management
- **Workflow Versioning**: Formal versioning system

### 10.2 Integration Opportunities

- **External Systems**: Integration with external APIs
- **Cloud Services**: AWS, Azure, GCP integrations
- **Monitoring Tools**: Integration with monitoring platforms
- **Notification Systems**: Additional notification channels

### 10.3 Scalability Considerations

- **Horizontal Scaling**: Support for multiple n8n instances
- **Workflow Distribution**: Load balancing across instances
- **Resource Optimization**: Efficient resource utilization
- **Performance Monitoring**: Performance metrics and optimization

---

## Appendix A: File Structure Reference

See `.cursor/rules/folders.mdc` for complete directory structure.

## Appendix B: Agent Rules Reference

See `AGENTS.md` and `.cursor/rules/001-init_agent.mdc` for agent behavior rules.

## Appendix C: Documentation Index

- **Workflow Naming**: `docs/WORKFLOW_NAMING.md`
- **Error Handling**: `docs/ERROR_HANDLING.md`
- **Data Contracts**: `docs/DATA_CONTRACTS.md`
- **Runbooks**: `docs/RUNBOOKS.md`
- **Agent Responsibilities**: `AGENTS.md`

---

**Document Control**:
- **Source of Truth**: `.cursor/docs/PRD.md`
- **Change Log**: `.agents/PRD.md`
- **Version History**: `.agents/prd_steps/`
