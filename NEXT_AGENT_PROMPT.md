# NEXT AGENT PROMPT

You are continuing Catena-Bot in a human-in-the-loop, agentic coding workflow.
Current completed phase: Phase 5
Target next phase: Maintenance

Prompt freshness metadata (must match current workflow):
- Generated at (UTC): 2026-03-27T14:57:56.670913+00:00
- Git SHA: 781b94912137
- Workflow ID: local-6104

Required operating constraints:
1) Treat README.md, PRD.md, and catena_bot/ssot_config.py as SSOT.
2) Lead with TDD and keep every Python file under 400 LOC.
3) Keep ci/run_tests.sh wired to all completed tests.

First action:
- Run ./ci/run_tests.sh and confirm the same or higher phase completion before coding.
