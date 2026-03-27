"""Phase-6 coverage tests for next-agent handoff workflow behavior."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from catena_bot.phase_status import (
    PHASE_ORDER,
    build_next_agent_prompt,
    report_ci_phase_status,
    validate_prompt_freshness,
    write_next_agent_prompt,
)


class TestPhase6HandoffCoverage(unittest.TestCase):
    def test_phase_6_prompt_contains_required_process_steps(self) -> None:
        prompt = build_next_agent_prompt(
            current_phase=5,
            max_phase=len(PHASE_ORDER),
            generated_at_utc="2026-03-27T00:00:00+00:00",
            git_sha="abc1234",
            workflow_id="workflow-1",
        )
        self.assertIn("Read NEXT_AGENT_PROMPT.md before coding", prompt)
        self.assertIn("Complete one scoped task", prompt)
        self.assertIn("Set up the next day handoff", prompt)

    def test_phase_6_integration_prompt_write_and_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "NEXT_AGENT_PROMPT.md"
            now = datetime.now(timezone.utc)
            write_next_agent_prompt(
                output_path=output_path,
                current_phase=5,
                max_phase=len(PHASE_ORDER),
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
            contents = output_path.read_text(encoding="utf-8")
            self.assertIn("Execution process for this run:", contents)

    def test_phase_6_e2e_report_ci_phase_status_writes_fresh_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "NEXT_AGENT_PROMPT.md"
            status = report_ci_phase_status(output_path=output_path)
            self.assertEqual(status["current_phase"], len(PHASE_ORDER))
            self.assertIsNone(status["blocked_phase"])
            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
