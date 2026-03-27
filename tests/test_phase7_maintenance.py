"""Phase-7 maintenance tests for prompt metadata hardening."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from catena_bot.phase_status import validate_prompt_freshness, write_next_agent_prompt


class TestPhase7Maintenance(unittest.TestCase):
    def test_current_workflow_id_falls_back_when_env_blank(self) -> None:
        from catena_bot.phase_status import current_workflow_id

        with patch.dict(os.environ, {"GITHUB_RUN_ID": "   "}, clear=False):
            workflow_id = current_workflow_id()
        self.assertTrue(workflow_id.startswith("local-"))

    def test_validate_prompt_freshness_rejects_invalid_timestamp_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "NEXT_AGENT_PROMPT.md"
            write_next_agent_prompt(
                output_path=output_path,
                current_phase=7,
                max_phase=7,
                generated_at_utc="not-a-date",
                git_sha="abc1234",
                workflow_id="workflow-1",
            )
            with self.assertRaisesRegex(AssertionError, "Invalid generated-at"):
                validate_prompt_freshness(
                    output_path=output_path,
                    expected_git_sha="abc1234",
                    expected_workflow_id="workflow-1",
                    now_utc=datetime.now(timezone.utc),
                    max_age_minutes=30,
                )

    def test_validate_prompt_freshness_rejects_future_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "NEXT_AGENT_PROMPT.md"
            future = datetime.now(timezone.utc) + timedelta(minutes=5)
            write_next_agent_prompt(
                output_path=output_path,
                current_phase=7,
                max_phase=7,
                generated_at_utc=future.isoformat(),
                git_sha="abc1234",
                workflow_id="workflow-1",
            )
            with self.assertRaisesRegex(AssertionError, "future"):
                validate_prompt_freshness(
                    output_path=output_path,
                    expected_git_sha="abc1234",
                    expected_workflow_id="workflow-1",
                    now_utc=datetime.now(timezone.utc),
                    max_age_minutes=30,
                )


if __name__ == "__main__":
    unittest.main()
