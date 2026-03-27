"""CI helpers for reporting phased completion and next-agent handoff prompts."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta, timezone
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


def current_git_sha() -> str:
    """Resolve git sha for CI/local workflow metadata."""

    env_sha = os.getenv("GITHUB_SHA")
    if env_sha:
        return env_sha[:12]
    result = subprocess.run(
        ["git", "rev-parse", "--short=12", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def current_workflow_id() -> str:
    """Resolve workflow id; fallback to deterministic local marker."""

    return os.getenv("GITHUB_RUN_ID") or f"local-{os.getpid()}"


def build_next_agent_prompt(
    *,
    current_phase: int,
    max_phase: int,
    generated_at_utc: str,
    git_sha: str,
    workflow_id: str,
) -> str:
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
            "Prompt freshness metadata (must match current workflow):",
            f"- Generated at (UTC): {generated_at_utc}",
            f"- Git SHA: {git_sha}",
            f"- Workflow ID: {workflow_id}",
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


def write_next_agent_prompt(
    *,
    output_path: Path,
    current_phase: int,
    max_phase: int,
    generated_at_utc: str,
    git_sha: str,
    workflow_id: str,
) -> Path:
    """Write next-agent prompt markdown and return path."""

    prompt = build_next_agent_prompt(
        current_phase=current_phase,
        max_phase=max_phase,
        generated_at_utc=generated_at_utc,
        git_sha=git_sha,
        workflow_id=workflow_id,
    )
    output_path.write_text(f"{prompt}\n", encoding="utf-8")
    return output_path


def _extract_metadata(prompt_text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in prompt_text.splitlines():
        if line.startswith("- Generated at (UTC): "):
            metadata["generated_at_utc"] = line.replace("- Generated at (UTC): ", "", 1).strip()
        elif line.startswith("- Git SHA: "):
            metadata["git_sha"] = line.replace("- Git SHA: ", "", 1).strip()
        elif line.startswith("- Workflow ID: "):
            metadata["workflow_id"] = line.replace("- Workflow ID: ", "", 1).strip()
    return metadata


def validate_prompt_freshness(
    *,
    output_path: Path,
    expected_git_sha: str,
    expected_workflow_id: str,
    now_utc: datetime,
    max_age_minutes: int,
) -> None:
    """Fail if prompt metadata is missing, mismatched, or stale for this workflow."""

    assert output_path.exists(), "NEXT_AGENT_PROMPT.md missing after CI gate execution."
    metadata = _extract_metadata(output_path.read_text(encoding="utf-8"))
    assert metadata.get("generated_at_utc"), "NEXT_AGENT_PROMPT.md missing generated-at metadata."
    assert metadata.get("git_sha"), "NEXT_AGENT_PROMPT.md missing Git SHA metadata."
    assert metadata.get("workflow_id"), "NEXT_AGENT_PROMPT.md missing workflow metadata."
    assert metadata["git_sha"] == expected_git_sha, "Git SHA mismatch: prompt does not match this commit."
    assert (
        metadata["workflow_id"] == expected_workflow_id
    ), "Workflow ID mismatch: prompt was not generated in this workflow run."

    generated_at = datetime.fromisoformat(metadata["generated_at_utc"])
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    allowed_age = timedelta(minutes=max_age_minutes)
    assert now_utc - generated_at <= allowed_age, "NEXT_AGENT_PROMPT.md is stale for this workflow run."


def report_ci_phase_status(output_path: Path = Path("NEXT_AGENT_PROMPT.md")) -> dict[str, object]:
    """Compute CI phase status, write prompt, and enforce freshness for this workflow."""

    status = evaluate_phase_completion([True] * len(PHASE_ORDER))
    now = datetime.now(timezone.utc)
    git_sha = current_git_sha()
    workflow_id = current_workflow_id()
    write_next_agent_prompt(
        output_path=output_path,
        current_phase=int(status["current_phase"]),
        max_phase=len(PHASE_ORDER),
        generated_at_utc=now.isoformat(),
        git_sha=git_sha,
        workflow_id=workflow_id,
    )
    validate_prompt_freshness(
        output_path=output_path,
        expected_git_sha=git_sha,
        expected_workflow_id=workflow_id,
        now_utc=now,
        max_age_minutes=30,
    )
    status["git_sha"] = git_sha
    status["workflow_id"] = workflow_id
    return status


if __name__ == "__main__":
    phase_status = report_ci_phase_status()
    completed = ", ".join(phase_status["completed_phases"]) or "None"
    print(f"[phase-status] Current completed phase: Phase {phase_status['current_phase']}")
    print(f"[phase-status] Completed phase gates: {completed}")
    print(f"[phase-status] Prompt metadata git_sha={phase_status['git_sha']} workflow_id={phase_status['workflow_id']}")
    if phase_status["blocked_phase"] is None:
        print("[phase-status] All SSOT-defined phases are complete.")
