# Agent Reports Directory

## Purpose
This directory contains phase reports generated during the Automation Hub project lifecycle. Reports track task progress, state summaries, blockers, and phase completion.

## Naming Convention
Reports follow the naming pattern: `{phase_id}_{YYYY-MM-DD}.md`

**Examples:**
- `phase_1_2025-11-20.md` - Phase 1 report from November 20, 2025
- `phase_2_2025-12-15.md` - Phase 2 report from December 15, 2025

## Report Generation
Reports are automatically generated when:
- ARCHITECT_AGENT triggers the "Phase Kickoff – Task Processing Report Generation" GitHub Action
- The `ops/scripts/generating_task_processing_template.py` script runs
- A new phase is initiated

## Report Lifecycle
1. **Generated:** At phase kickoff via GitHub Action workflow
2. **Updated:** Continuously during phase execution by agents
3. **Finalized:** At phase completion with exit criteria and reflection
4. **Archived:** Permanently stored here for traceability

## Report Structure
Each report contains:
- **Phase Checklist:** Task completion tracking
- **State Summary:** Module status and blockers table
- **Exit Criteria:** Phase completion requirements
- **Reflection & Next Steps:** Lessons learned and future planning
- **Report Output Path:** File location reference

## Access
- Reports are generated in this directory automatically
- Agents update reports during phase execution
- Reports are archived here permanently for audit trail

## References
- See `.agents/process-tasks.md` for report template
- See `.cursor/rules/workflow-governance.mdc` for phase workflow details
- See `.github/workflows/phase-kickoff.yaml` for report generation automation

