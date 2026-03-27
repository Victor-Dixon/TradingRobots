"""TDD-first validator tests for Catena-Bot phases."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from catena_bot.validators import (
    ConnectionState,
    validate_phase_1_backtest,
    validate_phase_2_execution_latency,
    validate_phase_3_shawn_logic_filter,
    validate_phase_4_safety_checks,
)


class TestPhase1Validator(unittest.TestCase):
    def test_phase_1_backtest_validity(self) -> None:
        strategy_results = {
            "win_rate": 0.52,
            "profit_factor": 1.35,
            "max_drawdown": 0.1,
            "sharpe_ratio": 1.8,
        }
        self.assertTrue(validate_phase_1_backtest(strategy_results))


class TestPhase2Validator(unittest.TestCase):
    def test_phase_2_execution_latency(self) -> None:
        now = datetime.now(timezone.utc)
        logs = [
            {"signal_at": now, "filled_at": now + timedelta(milliseconds=800)},
            {"signal_at": now, "filled_at": now + timedelta(seconds=1, milliseconds=200)},
        ]
        broker = ConnectionState(active=True, receiving=True)
        futures = ConnectionState(active=True, receiving=True)
        self.assertTrue(validate_phase_2_execution_latency(logs, broker, futures))


class TestPhase3Validator(unittest.TestCase):
    def test_phase_3_shawn_logic_filter(self) -> None:
        history = [
            {"stock_rel_strength": 1.2, "market_momentum": 0.7, "dist_to_vwap": 0.0013},
            {"stock_rel_strength": 0.8, "market_momentum": 0.3, "dist_to_vwap": 0.0019},
        ]
        self.assertTrue(validate_phase_3_shawn_logic_filter(history))


class TestPhase4Safety(unittest.TestCase):
    def test_phase_4_safety_checks(self) -> None:
        now = datetime.now(timezone.utc)
        self.assertTrue(
            validate_phase_4_safety_checks(
                daily_pnl_pct=-0.01,
                seconds_since_last_tick=2,
                current_positions=1,
                open_signal_ids={"sig-a"},
                candidate_signal_id="sig-b",
                last_loss_time=now - timedelta(minutes=40),
                now_utc=now,
            )
        )


if __name__ == "__main__":
    unittest.main()
