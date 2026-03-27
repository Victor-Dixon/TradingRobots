"""E2E-style tests for phased-plan progression and blocking behavior."""

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


def run_phased_gate_pipeline(
    *,
    strategy_results: dict[str, float],
    order_logs: list[dict[str, datetime]],
    broker_connection: ConnectionState,
    futures_stream: ConnectionState,
    connected_uptime_minutes: int,
    heartbeat_gap_seconds: int,
    vwap_delta_pct: float,
    kill_switch_close_ms: int,
    phase_1_import_ok: bool,
    trade_history: list[dict[str, float]],
    daily_pnl_pct: float,
    seconds_since_last_tick: int,
    current_positions: int,
    open_signal_ids: set[str],
    candidate_signal_id: str,
    last_loss_time: datetime | None,
    now_utc: datetime,
) -> bool:
    """Run all phased validators in order; return True only when all gates pass."""

    return (
        validate_phase_1_backtest(strategy_results)
        and validate_phase_2_execution_latency(order_logs, broker_connection, futures_stream)
        and validate_phase_2_live_readiness(
            connected_uptime_minutes=connected_uptime_minutes,
            heartbeat_gap_seconds=heartbeat_gap_seconds,
            vwap_delta_pct=vwap_delta_pct,
            kill_switch_close_ms=kill_switch_close_ms,
            phase_1_import_ok=phase_1_import_ok,
        )
        and validate_phase_3_shawn_logic_filter(trade_history)
        and validate_phase_4_safety_checks(
            daily_pnl_pct,
            seconds_since_last_tick,
            current_positions,
            open_signal_ids,
            candidate_signal_id,
            last_loss_time,
            now_utc,
        )
    )


class TestE2EPhasedPlan(unittest.TestCase):
    def test_e2e_nominal_phased_plan_passes(self) -> None:
        now = datetime.now(timezone.utc)
        self.assertTrue(
            run_phased_gate_pipeline(
                strategy_results={
                    "win_rate": 0.51,
                    "profit_factor": 1.33,
                    "max_drawdown": 0.09,
                    "sharpe_ratio": 1.71,
                },
                order_logs=[{"signal_at": now, "filled_at": now + timedelta(milliseconds=600)}],
                broker_connection=ConnectionState(active=True, receiving=True),
                futures_stream=ConnectionState(active=True, receiving=True),
                connected_uptime_minutes=60,
                heartbeat_gap_seconds=2,
                vwap_delta_pct=0.00005,
                kill_switch_close_ms=250,
                phase_1_import_ok=True,
                trade_history=[
                    {"stock_rel_strength": 1.2, "market_momentum": 0.8, "dist_to_vwap": 0.0015}
                ],
                daily_pnl_pct=-0.01,
                seconds_since_last_tick=2,
                current_positions=1,
                open_signal_ids={"open-a"},
                candidate_signal_id="open-b",
                last_loss_time=now - timedelta(minutes=35),
                now_utc=now,
            )
        )

    def test_e2e_pipeline_stops_on_phase_4_safety_failure(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaisesRegex(AssertionError, "Circuit breaker tripped"):
            run_phased_gate_pipeline(
                strategy_results={
                    "win_rate": 0.51,
                    "profit_factor": 1.33,
                    "max_drawdown": 0.09,
                    "sharpe_ratio": 1.71,
                },
                order_logs=[{"signal_at": now, "filled_at": now + timedelta(milliseconds=600)}],
                broker_connection=ConnectionState(active=True, receiving=True),
                futures_stream=ConnectionState(active=True, receiving=True),
                connected_uptime_minutes=60,
                heartbeat_gap_seconds=2,
                vwap_delta_pct=0.00005,
                kill_switch_close_ms=250,
                phase_1_import_ok=True,
                trade_history=[
                    {"stock_rel_strength": 1.2, "market_momentum": 0.8, "dist_to_vwap": 0.0015}
                ],
                daily_pnl_pct=-0.03,
                seconds_since_last_tick=2,
                current_positions=1,
                open_signal_ids={"open-a"},
                candidate_signal_id="open-b",
                last_loss_time=now - timedelta(minutes=35),
                now_utc=now,
            )


if __name__ == "__main__":
    unittest.main()
