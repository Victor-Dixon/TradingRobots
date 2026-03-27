"""Unit tests for CI phase-status reporting and next-agent handoff prompt."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from catena_bot.phase_status import (
    PHASE_ORDER,
    build_next_agent_prompt,
    determine_current_phase,
    evaluate_phase_completion,
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
        prompt = build_next_agent_prompt(current_phase=3, max_phase=len(PHASE_ORDER))
        self.assertIn("Current completed phase: Phase 3", prompt)
        self.assertIn("Target next phase: Phase 4", prompt)

    def test_build_next_agent_prompt_marks_maintenance_when_all_phases_done(self) -> None:
        prompt = build_next_agent_prompt(current_phase=len(PHASE_ORDER), max_phase=len(PHASE_ORDER))
        self.assertIn("Current completed phase: Phase 5", prompt)
        self.assertIn("Target next phase: Maintenance", prompt)

    def test_write_next_agent_prompt_persists_expected_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "NEXT_AGENT_PROMPT.md"
            written = write_next_agent_prompt(output_path=output_path, current_phase=2, max_phase=5)
            self.assertEqual(written, output_path)
            contents = output_path.read_text(encoding="utf-8")
            self.assertIn("Current completed phase: Phase 2", contents)
            self.assertIn("Target next phase: Phase 3", contents)


if __name__ == "__main__":
    unittest.main()
