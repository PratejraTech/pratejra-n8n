#!/usr/bin/env python3
"""
Script: generate_task_processing_template.py
Purpose: Generate a new task-processing.md report for a phase and auto-update state.mdc.
Usage: python generate_task_processing_template.py --phase "Foundation & Environment"
"""

import argparse
import datetime
import yaml
import os

STATE_FILE = ".cursor/rules/state.mdc"
REPORTS_DIR = ".agents/reports"

TEMPLATE = """# PROCESS TASK LIST & STATE TRACKER

**Project:** Automation Hub (n8n Enterprise Automation Backbone)  
**Current Phase:** {phase_name}  
**Last Updated:** {date}

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
| Backend      | {phase_name} | NotStarted     |                                  |
| Integration  | {phase_name} | NotStarted     |                                  |
| QA           | {phase_name} | NotStarted     |                                  |

## C. Exit Criteria for Phase  
- All implementation tasks done.  
- All tests pass.  
- Documentation updated (PRD, architecture.mdc, state.mdc).  
- No open high-priority issues.  
- `state.mdc` updated to mark phase complete.

## D. Reflection & Next Steps  
- Lessons learned:  
- What to improve next phase:  
- Tasks for next phase: (see `generate-tasks.md` – next phase ≫ {next_phase})

## E. Short Report Output Path  
- Report file: {report_path}
"""

def load_state():
    with open(STATE_FILE, 'r') as f:
        content = f.read()
    
    # Handle YAML front matter (between --- markers)
    if content.startswith('---'):
        # Find the end of front matter
        parts = content.split('---', 2)
        if len(parts) >= 3:
            # Skip front matter, use the YAML content after it
            yaml_content = parts[2].strip()
        else:
            yaml_content = content
    else:
        yaml_content = content
    
    # Parse YAML content
    state = yaml.safe_load(yaml_content)
    return state

def update_state_phase_start(state, phase_id):
    now = datetime.datetime.utcnow().isoformat() + "Z"
    for phase in state.get("phases", []):
        if phase["id"] == phase_id:
            phase["status"] = "In Progress"
            if phase.get("start_date") is None:
                phase["start_date"] = now
    # Append history
    state.setdefault("history", []).append({
        "timestamp": now,
        "agent": os.getenv("USER", "script"),
        "action": f"Marked phase '{phase_id}' as In Progress."
    })
    # Update last_updated
    state["last_updated"] = datetime.datetime.utcnow().date().isoformat()
    return state

def save_state(state):
    with open(STATE_FILE, 'r') as f:
        original_content = f.read()
    
    # Preserve front matter if it exists
    front_matter = ""
    yaml_content = original_content
    
    if original_content.startswith('---'):
        parts = original_content.split('---', 2)
        if len(parts) >= 3:
            front_matter = '---' + parts[1] + '---\n\n'
            yaml_content = parts[2]
    
    # Write back with preserved front matter
    with open(STATE_FILE, 'w') as f:
        f.write(front_matter)
        yaml.dump(state, f, sort_keys=False, default_flow_style=False)

def write_report(phase_name, next_phase, report_path):
    now = datetime.date.today().isoformat()
    report_content = TEMPLATE.format(
        phase_name=phase_name,
        date=now,
        next_phase=next_phase,
        report_path=report_path
    )
    with open(report_path, 'w') as f:
        f.write(report_content)
    print(f"Wrote report to {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate task processing report and update state.")
    parser.add_argument("--phase", required=True, help="Phase ID (e.g. phase_1)")
    parser.add_argument("--phase-name", required=True, help="Phase display name")
    parser.add_argument("--next-phase", required=True, help="Next phase display name")
    args = parser.parse_args()

    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    report_filename = f"{args.phase}_{datetime.date.today().isoformat()}.md"
    report_path = os.path.join(REPORTS_DIR, report_filename)

    state = load_state()
    state = update_state_phase_start(state, args.phase)
    save_state(state)
    write_report(args.phase_name, args.next_phase, report_path)

if __name__ == "__main__":
    main()
