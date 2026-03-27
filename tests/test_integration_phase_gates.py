"""Integration tests that validate phased DoD gate composition."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from catena_bot.validators import (
    ConnectionState,
    validate_phase_1_backtest,
    validate_phase_2_execution_latency,
    validate_phase_2_live_readiness,
    validate_phase_3_shawn_logic_filter,
    validate_phase_4_safety_checks,
)


class TestIntegrationPhaseGates(unittest.TestCase):
    def test_integration_all_phase_gates_pass(self) -> None:
        now = datetime.now(timezone.utc)
        phase_1 = {
            "win_rate": 0.53,
            "profit_factor": 1.4,
            "max_drawdown": 0.1,
            "sharpe_ratio": 1.9,
        }
        phase_2_logs = [{"signal_at": now, "filled_at": now + timedelta(milliseconds=700)}]
        phase_3_history = [{"stock_rel_strength": 1.15, "market_momentum": 0.65, "dist_to_vwap": 0.0016}]

        self.assertTrue(validate_phase_1_backtest(phase_1))
        self.assertTrue(
            validate_phase_2_execution_latency(
                phase_2_logs,
                ConnectionState(active=True, receiving=True),
                ConnectionState(active=True, receiving=True),
            )
        )
        self.assertTrue(
            validate_phase_2_live_readiness(
                connected_uptime_minutes=60,
                heartbeat_gap_seconds=2,
                vwap_delta_pct=0.00005,
                kill_switch_close_ms=250,
                phase_1_import_ok=True,
            )
        )
        self.assertTrue(validate_phase_3_shawn_logic_filter(phase_3_history))
        self.assertTrue(
            validate_phase_4_safety_checks(
                daily_pnl_pct=-0.01,
                seconds_since_last_tick=1,
                current_positions=1,
                open_signal_ids={"open-sig"},
                candidate_signal_id="new-sig",
                last_loss_time=now - timedelta(minutes=45),
                now_utc=now,
            )
        )

    def test_integration_fails_fast_when_any_phase_gate_fails(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaises(AssertionError):
            validate_phase_2_execution_latency(
                [{"signal_at": now, "filled_at": now + timedelta(seconds=3)}],
                ConnectionState(active=True, receiving=True),
                ConnectionState(active=True, receiving=True),
            )


if __name__ == "__main__":
    unittest.main()
