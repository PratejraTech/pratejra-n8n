<!--
Purpose: Agent responsibilities documentation for automation platform
Created/Updated: 2025-11-19 19:49
Agent: Init Agent
-->
# Agent Responsibilities – Automation Platform

## Scope  
These agents have two core tasks:  
1. Capture system context by snapshotting files into `.agents/contexts/`.  
2. Insert or ensure a header docstring at the top of any touched file.

## Workflow  
- On detection of file creation or modification (across `/automation-platform/` tree):  
  - Save snapshot under `.agents/contexts/<timestamp>/<path>`.  
  - If file has no header or header is outdated, add/update header.  
- No other file content changes permitted.  
- Log all actions to `.agents/logs/agent‐actions.log`.

## Directory Structure  
Read ```.cursor/rules/folders.mdc``` for all directory queries.

## Guidelines  
- Header format:  
  ```text
  /*  
   * Purpose: <short description>  
   * Created/Updated: <YYYY-MM-DD HH:MM>  
   * Agent: Init Agent  
   */
Do not modify business logic, JSON schema, config content, or docs body.

Maintain idempotency: unchanged file = no new snapshot or header update.

Use timestamps in folder names for versioning of snapshots.

yaml
Copy code

---

### Goal:  
Provide a clear rule-file (`.mdc`) for Cursor that governs agent behaviour, and a concise `AGENTS.md` explaining the agent’s role in the system.

### Key Takeaway:  
With these rules in place, your “Agent” is tightly scoped: context capture + header docstrings only — no unintended file modifications.
::contentReference[oaicite:1]{index=1}