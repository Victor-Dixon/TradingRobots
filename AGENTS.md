# AGENTS.md

## SSOT + TDD Operating Rules
- `README.md`, `PRD.md`, and `catena_bot/ssot_config.py` are the SSOT references for phased scope and thresholds.
- Any change to phase behavior must update SSOT docs and tests in the same change.
- All completed/passing tests must remain wired into `ci/run_tests.sh` so regressions are caught immediately.

## Feature Scope Rule
- If a new feature is outside the currently defined phased plan in `PRD.md`, it must be added as a **new phase** in `PRD.md` before implementation proceeds.
- That new phase must include the same testing standard:
  - unit tests,
  - integration tests,
  - e2e tests,
  - and explicit DoD thresholds.
- Lead with TDD: create/update tests first, then implement code.

## Python LOC Rule
- Every Python file must remain under 400 LOC.
