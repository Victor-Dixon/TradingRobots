"""Unit tests for CI phase-status reporting and next-agent handoff prompt."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from catena_bot.phase_status import (
    PHASE_ORDER,
    build_next_agent_prompt,
    determine_current_phase,
    evaluate_phase_completion,
    validate_prompt_freshness,
    write_next_agent_prompt,
)


class TestPhaseStatus(unittest.TestCase):
    def test_determine_current_phase_stops_on_first_failure(self) -> None:
        self.assertEqual(determine_current_phase([True, True, False, True]), 2)

    def test_determine_current_phase_returns_zero_when_phase_1_fails(self) -> None:
        self.assertEqual(determine_current_phase([False, True, True]), 0)

    def test_evaluate_phase_completion_marks_only_contiguous_gates_complete(self) -> None:
        status = evaluate_phase_completion([True, True, False, True, True])
        self.assertEqual(status["current_phase"], 2)
        self.assertEqual(status["completed_phases"], ["Phase 1", "Phase 2"])
        self.assertEqual(status["blocked_phase"], "Phase 3")

    def test_build_next_agent_prompt_recommends_next_phase_when_not_done(self) -> None:
        prompt = build_next_agent_prompt(
            current_phase=3,
            max_phase=len(PHASE_ORDER),
            generated_at_utc="2026-03-27T00:00:00+00:00",
            git_sha="abc1234",
            workflow_id="workflow-1",
        )
        self.assertIn("Current completed phase: Phase 3", prompt)
        self.assertIn("Target next phase: Phase 4", prompt)

    def test_build_next_agent_prompt_marks_maintenance_when_all_phases_done(self) -> None:
        prompt = build_next_agent_prompt(
            current_phase=len(PHASE_ORDER),
            max_phase=len(PHASE_ORDER),
            generated_at_utc="2026-03-27T00:00:00+00:00",
            git_sha="abc1234",
            workflow_id="workflow-1",
        )
        self.assertIn("Current completed phase: Phase 5", prompt)
        self.assertIn("Target next phase: Maintenance", prompt)

    def test_write_next_agent_prompt_persists_expected_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "NEXT_AGENT_PROMPT.md"
            written = write_next_agent_prompt(
                output_path=output_path,
                current_phase=2,
                max_phase=5,
                generated_at_utc="2026-03-27T00:00:00+00:00",
                git_sha="abc1234",
                workflow_id="workflow-1",
            )
            self.assertEqual(written, output_path)
            contents = output_path.read_text(encoding="utf-8")
            self.assertIn("Current completed phase: Phase 2", contents)
            self.assertIn("Target next phase: Phase 3", contents)
            self.assertIn("Git SHA: abc1234", contents)
            self.assertIn("Workflow ID: workflow-1", contents)

    def test_validate_prompt_freshness_accepts_recent_matching_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "NEXT_AGENT_PROMPT.md"
            now = datetime.now(timezone.utc)
            write_next_agent_prompt(
                output_path=output_path,
                current_phase=5,
                max_phase=5,
                generated_at_utc=now.isoformat(),
                git_sha="abc1234",
                workflow_id="workflow-1",
            )
            validate_prompt_freshness(
                output_path=output_path,
                expected_git_sha="abc1234",
                expected_workflow_id="workflow-1",
                now_utc=now,
                max_age_minutes=30,
            )

    def test_validate_prompt_freshness_rejects_stale_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "NEXT_AGENT_PROMPT.md"
            old = datetime.now(timezone.utc) - timedelta(minutes=120)
            write_next_agent_prompt(
                output_path=output_path,
                current_phase=5,
                max_phase=5,
                generated_at_utc=old.isoformat(),
                git_sha="abc1234",
                workflow_id="workflow-1",
            )
            with self.assertRaisesRegex(AssertionError, "stale"):
                validate_prompt_freshness(
                    output_path=output_path,
                    expected_git_sha="abc1234",
                    expected_workflow_id="workflow-1",
                    now_utc=datetime.now(timezone.utc),
                    max_age_minutes=30,
                )

    def test_validate_prompt_freshness_rejects_git_sha_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "NEXT_AGENT_PROMPT.md"
            now = datetime.now(timezone.utc)
            write_next_agent_prompt(
                output_path=output_path,
                current_phase=5,
                max_phase=5,
                generated_at_utc=now.isoformat(),
                git_sha="abc1234",
                workflow_id="workflow-1",
            )
            with self.assertRaisesRegex(AssertionError, "Git SHA"):
                validate_prompt_freshness(
                    output_path=output_path,
                    expected_git_sha="def5678",
                    expected_workflow_id="workflow-1",
                    now_utc=now,
                    max_age_minutes=30,
                )


if __name__ == "__main__":
    unittest.main()
