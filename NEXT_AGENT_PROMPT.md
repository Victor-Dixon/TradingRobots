# NEXT AGENT PROMPT

You are continuing Catena-Bot in a human-in-the-loop, agentic coding workflow.
Current completed phase: Phase 7
Target next phase: Maintenance

Prompt freshness metadata (must match current workflow):
- Generated at (UTC): 2026-03-27T16:04:45.920177+00:00
- Git SHA: 9314579913ff
- Workflow ID: local-6842

Required operating constraints:
1) Treat README.md, PRD.md, and catena_bot/ssot_config.py as SSOT.
2) Lead with TDD and keep every Python file under 400 LOC.
3) Keep ci/run_tests.sh wired to all completed tests.

Execution process for this run:
1) Read NEXT_AGENT_PROMPT.md before coding and restate the task you are completing.
2) Complete one scoped task for the target next phase with tests first (TDD).
3) Set up the next day handoff by rerunning ./ci/run_tests.sh and committing refreshed prompt metadata.
