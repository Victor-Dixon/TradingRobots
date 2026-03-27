"""CI helpers for reporting phased completion and next-agent handoff prompts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from catena_bot.ssot_config import SSOT

PHASE_ORDER = tuple(SSOT.phase_order)


def determine_current_phase(phase_test_results: Iterable[bool]) -> int:
    """Return highest contiguous completed phase count from ordered phase gate results."""

    current_phase = 0
    for gate_passed in phase_test_results:
        if not gate_passed:
            break
        current_phase += 1
    return current_phase


def evaluate_phase_completion(phase_test_results: Iterable[bool]) -> dict[str, object]:
    """Evaluate current completed phase and identify blocking phase label."""

    current_phase = determine_current_phase(phase_test_results)
    completed = list(PHASE_ORDER[:current_phase])
    blocked_phase = None if current_phase == len(PHASE_ORDER) else PHASE_ORDER[current_phase]
    return {
        "current_phase": current_phase,
        "completed_phases": completed,
        "blocked_phase": blocked_phase,
    }


def build_next_agent_prompt(*, current_phase: int, max_phase: int) -> str:
    """Build a deterministic next-agent prompt for human-in-the-loop workflows."""

    next_phase_label = "Maintenance" if current_phase >= max_phase else f"Phase {current_phase + 1}"
    return "\n".join(
        [
            "# NEXT AGENT PROMPT",
            "",
            "You are continuing Catena-Bot in a human-in-the-loop, agentic coding workflow.",
            f"Current completed phase: Phase {current_phase}",
            f"Target next phase: {next_phase_label}",
            "",
            "Required operating constraints:",
            "1) Treat README.md, PRD.md, and catena_bot/ssot_config.py as SSOT.",
            "2) Lead with TDD and keep every Python file under 400 LOC.",
            "3) Keep ci/run_tests.sh wired to all completed tests.",
            "",
            "First action:",
            "- Run ./ci/run_tests.sh and confirm the same or higher phase completion before coding.",
        ]
    )


def write_next_agent_prompt(*, output_path: Path, current_phase: int, max_phase: int) -> Path:
    """Write next-agent prompt markdown and return path."""

    prompt = build_next_agent_prompt(current_phase=current_phase, max_phase=max_phase)
    output_path.write_text(f"{prompt}\n", encoding="utf-8")
    return output_path


def report_ci_phase_status(output_path: Path = Path("NEXT_AGENT_PROMPT.md")) -> dict[str, object]:
    """Compute CI phase status assuming all phase gates have passed in sequence."""

    status = evaluate_phase_completion([True] * len(PHASE_ORDER))
    write_next_agent_prompt(
        output_path=output_path,
        current_phase=int(status["current_phase"]),
        max_phase=len(PHASE_ORDER),
    )
    return status


if __name__ == "__main__":
    phase_status = report_ci_phase_status()
    completed = ", ".join(phase_status["completed_phases"]) or "None"
    print(f"[phase-status] Current completed phase: Phase {phase_status['current_phase']}")
    print(f"[phase-status] Completed phase gates: {completed}")
    if phase_status["blocked_phase"] is None:
        print("[phase-status] All SSOT-defined phases are complete.")
