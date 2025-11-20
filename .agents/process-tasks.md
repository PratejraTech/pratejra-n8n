# PROCESS TASK LIST & STATE TRACKER (TEMPLATE)

> **Note:** This is a template file. Actual phase reports are generated automatically in `.agents/reports/{phase_id}_{YYYY-MM-DD}.md` when a phase is kicked off via GitHub Action. This file serves as a reference for the report structure.

**Project:** Automation Hub (n8n Enterprise Automation Backbone)  
**Current Phase:** {Phase Name}  
**Last Updated:** {Date}
## A. Phase Checklist  
- [ ] Phase kickoff documented in `state.mdc`.  
- [ ] Tasks generated (see `generate-tasks.md`).  
- [ ] Agents assigned (backend_agent, integration_agent, QA_agent, etc.).  
- [ ] Implementation tasks started.  
- [ ] Tests created/queued.  
- [ ] Documentation updates queued.  
- [ ] Code review scheduled.

## B. State Summary  
| Module       | Phase        | Status        | Blockers                          |
|--------------|--------------|---------------|----------------------------------|
| Backend      | {Phase Name} | {NotStarted/InProgress/Done} | {List blockers} |
| Integration  | {Phase Name} | {NotStarted/InProgress/Done} | {List blockers} |
| QA           | {Phase Name} | {NotStarted/InProgress/Done} | {List blockers} |

## C. Exit Criteria for Phase  
- All implementation tasks done.  
- All tests pass (unit, integration, E2E).  
- Documentation updated (PRD, architecture.mdc, state.mdc).  
- No open high-priority issues.  
- `state.mdc` updated to mark phase complete.

## D. Reflection & Next Steps  
- Lessons learned: {Short notes}  
- What to improve next phase: {Short notes}  
- Tasks for next phase: (see `generate-tasks.md` – next phase ≫ {Next Phase Name})

## E. Short Report Output Path  
- Reports will be written to `.agents/reports/{phase_id}_{YYYY-MM-DD}.md`

---

## How to Use This Template

### Phase Kickoff
Reports are automatically generated when ARCHITECT_AGENT triggers the "Phase Kickoff – Task Processing Report Generation" GitHub Action. The report is created in `.agents/reports/{phase_id}_{YYYY-MM-DD}.md` with the current phase name and date filled in.

### During Phase Execution
Agents update the phase report (not this template) continuously:
- Mark subtasks as started or complete in Phase Checklist
- Update State Summary table with current status and blockers
- Document blockers immediately in State Summary table
- Update progress as work progresses

### Milestone Completion
When a milestone is completed, the following actions are **required**:

1. **Update state.mdc:**
   - Mark milestone status as "Completed"
   - Set `completed_date` to current date (YYYY-MM-DD)
   - Location: `.cursor/rules/state.mdc`

2. **Commit changes:**
   - Commit message format: `"Complete milestone {milestone_id} – {milestone_title}"`
   - Include state.mdc and any related implementation files

3. **Update process-tasks.md (phase report):**
   - Update State Summary table with milestone completion
   - Mark milestone-related tasks as complete
   - Document any lessons learned

See `.cursor/rules/milestone-completion.mdc` for detailed milestone completion process.

### Phase Completion
Upon phase completion:
1. QA_AGENT validates all exit criteria are met
2. Fill in Exit Criteria checkboxes in the phase report
3. Complete Reflection & Next Steps section
4. ARCHITECT_AGENT updates `state.mdc` to mark phase status as "Completed"
5. ARCHITECT_AGENT sets `end_date` and adds history entry
6. Report is archived in `.agents/reports/` for traceability

### File Paths Reference
- **State file:** `.cursor/rules/state.mdc` (maintained by ARCHITECT_AGENT)
- **Phase reports:** `.agents/reports/{phase_id}_{YYYY-MM-DD}.md` (generated automatically)
- **Tasks reference:** `.agents/tasks.md` (static task list)
- **PRD:** `.agents/prd.md` (product requirements)

### Important Notes
- This file (`.agents/process-tasks.md`) is a **template** - do not update it directly
- Actual phase reports are in `.agents/reports/` directory
- State file location is `.cursor/rules/state.mdc` (not root)
- Report naming follows pattern: `{phase_id}_{YYYY-MM-DD}.md`
- All milestone completions require: state update, commit, and process-tasks.md update

See `.cursor/rules/workflow-governance.mdc` for complete phase workflow details.