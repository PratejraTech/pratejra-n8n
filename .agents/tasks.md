Below is the **generate-tasks.md** file written exactly in the structure you requested, aligned with the Automation Hub PRD, the architecture, and the 3-File System.
It is written so that **agents can use it directly** to produce tasks in a consistent and production-grade manner.

You can drop this file into the root of the repo:

```
generate-tasks.md
```

---

# **generate-tasks.md — TASK GENERATION LIST**

**Context:** **Automation Hub (n8n Enterprise Automation Backbone)** – use this list to generate engineering and agent tasks based on the PRD and architecture.mdc.

---

## **1. Epic / Feature**

### **Epic: Establish the Automation Hub**

* **Title:** Automation Hub Backend Platform
* **Description:**
  Build a production-grade, schema-first, GitOps-driven n8n automation platform with environment configurations, versioned internal API, shared schemas/snippets, GitHub Actions CI/CD, observability stack, and governed workflow lifecycle.
* **Associated PRD Requirement(s):** R1, R2, R3, R4, R5, R6
* **Priority:** High

---

## **2. Milestones / Phases**

### **Phase 1 – Foundation & Environment**

**Deliverable:**
Repo structure, shared schemas, JS snippets, environment configs, n8n instance prepared, GitHub integration established.

### **Phase 2 – Workflow Development & Shared System Components**

**Deliverable:**
All domain workflows (CRM, infra, meta), shared error handlers, metadata system, validation pipelines, versioned internal API v1.

### **Phase 3 – CI/CD, Observability & Release Governance**

**Deliverable:**
GitHub Actions pipelines, monitoring stack integration, workflow catalog builder, backups, release promotion streams.

---

## **3. Task Breakdown**

### **Phase 1 Tasks — Foundation & Environment**

* **Task 1:** Create base folder structure per architecture.mdc – **Owner:** ARCHITECT_AGENT – **Estimate:** 4h – **Dependencies:** folders.mdc
* **Task 2:** Add environment config system (dev/prod YAML) – **Owner:** BACKEND_AGENT – **Estimate:** 3h
* **Task 3:** Implement secrets strategy (AWS Secrets Manager references) – **Owner:** BACKEND_AGENT – **Estimate:** 4h
* **Task 4:** Prepare shared schemas (event.v1, contact.v1, incident.v1, infra_deploy.v1) – **Owner:** BACKEND_AGENT – **Estimate:** 6h
* **Task 5:** Add JS snippet utilities (validation, normalization, risk scoring) – **Owner:** BACKEND_AGENT – **Estimate:** 5h
* **Task 6:** Configure base n8n instance + health checks – **Owner:** INTEGRATION_AGENT – **Estimate:** 3h
* **Task 7:** Document Phase 1 architecture updates – **Owner:** ARCHITECT_AGENT – **Estimate:** 1h

---

### **Phase 2 Tasks — Workflow Development**

* **Task 1:** Build CRM workflows (intake, enrichment, sync) – **Owner:** BACKEND_AGENT – **Estimate:** 8h – **Dependencies:** shared schemas
* **Task 2:** Build Infra workflows triggered by GitHub Actions – **Owner:** BACKEND_AGENT – **Estimate:** 8h – **Dependencies:** GitHub integration
* **Task 3:** Build Meta workflows (catalog builder, health checks) – **Owner:** BACKEND_AGENT – **Estimate:** 6h
* **Task 4:** Implement shared workflows (error handler, log event, notify Slack, approvals) – **Owner:** BACKEND_AGENT – **Estimate:** 4h
* **Task 5:** Implement internal API v1: `/internal/api/v1/events/<type>` – **Owner:** BACKEND_AGENT – **Estimate:** 6h
* **Task 6:** Add ownership.yaml + catalog YAML generation – **Owner:** BACKEND_AGENT – **Estimate:** 2h
* **Task 7:** Write runbooks for new workflows – **Owner:** QA_AGENT – **Estimate:** 3h

---

### **Phase 3 Tasks — CI/CD, Observability & Governance**

* **Task 1:** Build CI workflow validation: linting, schema checks – **Owner:** INTEGRATION_AGENT – **Estimate:** 6h
* **Task 2:** Build deploy-workflows GitHub Action – **Owner:** INTEGRATION_AGENT – **Estimate:** 4h
* **Task 3:** Build sync_n8n_env.yml – **Owner:** INTEGRATION_AGENT – **Estimate:** 3h
* **Task 4:** Integrate Prometheus metrics exporter for n8n – **Owner:** BACKEND_AGENT – **Estimate:** 5h
* **Task 5:** Build Grafana dashboards (workflow health, error rates, infra metrics) – **Owner:** QA_AGENT – **Estimate:** 4h
* **Task 6:** Add S3 workflow backups via GitHub Actions – **Owner:** INTEGRATION_AGENT – **Estimate:** 4h
* **Task 7:** Implement release governance (promotion + rollback bundles) – **Owner:** ARCHITECT_AGENT – **Estimate:** 6h
* **Task 8:** Document governance in RUNBOOKS.md – **Owner:** ARCHITECT_AGENT – **Estimate:** 2h

---

## **4. Test / Validation Tasks**

* **Test Task 1:** Validate schema-first workflows: ensure all payloads pass JSON schema validation.
* **Test Task 2:** End-to-end infra pipeline (GitHub → n8n → Terraform → Slack).
* **Test Task 3:** Stress-test error handler with controlled failures.
* **Test Task 4:** Validate internal API v1 versioning and backward compatibility.
* **Test Task 5:** Validate workflow catalog generation consistency.

---

## **5. Documentation / Review Tasks**

* **Doc Task 1:** Update PRD with any requirement changes discovered during implementation.
* **Doc Task 2:** Update architecture.mdc when new components or directories are introduced.
* **Doc Task 3:** Write runbooks per workflow with: owners, risks, rollback steps.
* **Doc Task 4:** Agent writes summary into `.cursor/agent_notes/*` after each phase.
* **Doc Task 5:** Generate new entries in workflows_catalog.yaml and ownership.yaml.

---

## **6. Ready-For-CI/Build Gate Tasks**

* Code/workflows must pass schema validation.
* All linting and tests must pass in GitHub Actions.
* Observability metrics must be emitting properly.
* Documentation updated in `/docs`.
* `state.mdc` must be updated to mark phase complete and record final artefacts.
* All new folders validated against `folders.mdc`.
* No untracked architecture changes allowed.

---

# **Goal**

Provide a predictable and repeatable method for agents to generate tasks aligned with PRD → tasks → implementation cycles.

# **Key Takeaway**

This file is the bridge between high-level requirements and granular engineering work, ensuring alignment with architecture, governance, CI/CD, and runtime reliability.

---

### **Two Advanced Capabilities to Add Later**

1. **Automated task generator** reading prd.md + architecture.mdc to produce tasks dynamically.
