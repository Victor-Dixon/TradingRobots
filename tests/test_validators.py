"""TDD-first validator tests for Catena-Bot phases."""

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


class TestPhase1Validator(unittest.TestCase):
    def test_phase_1_backtest_validity(self) -> None:
        strategy_results = {
            "win_rate": 0.52,
            "profit_factor": 1.35,
            "max_drawdown": 0.1,
            "sharpe_ratio": 1.8,
        }
        self.assertTrue(validate_phase_1_backtest(strategy_results))

    def test_phase_1_backtest_rejects_low_win_rate(self) -> None:
        with self.assertRaisesRegex(AssertionError, "Win rate too low"):
            validate_phase_1_backtest(
                {
                    "win_rate": 0.45,
                    "profit_factor": 1.35,
                    "max_drawdown": 0.1,
                    "sharpe_ratio": 1.8,
                }
            )

    def test_phase_1_backtest_rejects_low_profit_factor(self) -> None:
        with self.assertRaisesRegex(AssertionError, "yielding enough"):
            validate_phase_1_backtest(
                {
                    "win_rate": 0.52,
                    "profit_factor": 1.2,
                    "max_drawdown": 0.1,
                    "sharpe_ratio": 1.8,
                }
            )

    def test_phase_1_backtest_rejects_high_drawdown(self) -> None:
        with self.assertRaisesRegex(AssertionError, "drawdown exceeds"):
            validate_phase_1_backtest(
                {
                    "win_rate": 0.52,
                    "profit_factor": 1.35,
                    "max_drawdown": 0.15,
                    "sharpe_ratio": 1.8,
                }
            )

    def test_phase_1_backtest_rejects_low_sharpe(self) -> None:
        with self.assertRaisesRegex(AssertionError, "Risk-adjusted return"):
            validate_phase_1_backtest(
                {
                    "win_rate": 0.52,
                    "profit_factor": 1.35,
                    "max_drawdown": 0.1,
                    "sharpe_ratio": 1.5,
                }
            )


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

    def test_phase_2_rejects_latency_breach(self) -> None:
        now = datetime.now(timezone.utc)
        logs = [{"signal_at": now, "filled_at": now + timedelta(seconds=2)}]
        broker = ConnectionState(active=True, receiving=True)
        futures = ConnectionState(active=True, receiving=True)
        with self.assertRaisesRegex(AssertionError, "Latency too high"):
            validate_phase_2_execution_latency(logs, broker, futures)

    def test_phase_2_rejects_disconnected_broker(self) -> None:
        now = datetime.now(timezone.utc)
        logs = [{"signal_at": now, "filled_at": now + timedelta(milliseconds=500)}]
        broker = ConnectionState(active=False, receiving=True)
        futures = ConnectionState(active=True, receiving=True)
        with self.assertRaisesRegex(AssertionError, "Broker WebSocket is disconnected"):
            validate_phase_2_execution_latency(logs, broker, futures)

    def test_phase_2_rejects_stale_futures_stream(self) -> None:
        now = datetime.now(timezone.utc)
        logs = [{"signal_at": now, "filled_at": now + timedelta(milliseconds=500)}]
        broker = ConnectionState(active=True, receiving=True)
        futures = ConnectionState(active=True, receiving=False)
        with self.assertRaisesRegex(AssertionError, "Nasdaq Futures data feed is lagging"):
            validate_phase_2_execution_latency(logs, broker, futures)

    def test_phase_2_live_readiness(self) -> None:
        self.assertTrue(
            validate_phase_2_live_readiness(
                connected_uptime_minutes=60,
                heartbeat_gap_seconds=5,
                vwap_delta_pct=0.00009,
                kill_switch_close_ms=420,
                phase_1_import_ok=True,
            )
        )

    def test_phase_2_live_readiness_rejects_stale_heartbeat(self) -> None:
        with self.assertRaisesRegex(AssertionError, "Stale heartbeat detected"):
            validate_phase_2_live_readiness(
                connected_uptime_minutes=60,
                heartbeat_gap_seconds=11,
                vwap_delta_pct=0.00009,
                kill_switch_close_ms=420,
                phase_1_import_ok=True,
            )

    def test_phase_2_live_readiness_rejects_kill_switch_latency(self) -> None:
        with self.assertRaisesRegex(AssertionError, "Kill switch close-out exceeded"):
            validate_phase_2_live_readiness(
                connected_uptime_minutes=60,
                heartbeat_gap_seconds=5,
                vwap_delta_pct=0.00009,
                kill_switch_close_ms=500,
                phase_1_import_ok=True,
            )


class TestPhase3Validator(unittest.TestCase):
    def test_phase_3_shawn_logic_filter(self) -> None:
        history = [
            {"stock_rel_strength": 1.2, "market_momentum": 0.7, "dist_to_vwap": 0.0013},
            {"stock_rel_strength": 0.8, "market_momentum": 0.3, "dist_to_vwap": 0.0019},
        ]
        self.assertTrue(validate_phase_3_shawn_logic_filter(history))

    def test_phase_3_rejects_weak_relative_strength(self) -> None:
        history = [{"stock_rel_strength": 0.5, "market_momentum": 0.7, "dist_to_vwap": 0.0013}]
        with self.assertRaisesRegex(AssertionError, "weak stock"):
            validate_phase_3_shawn_logic_filter(history)

    def test_phase_3_rejects_non_compressed_entry(self) -> None:
        history = [{"stock_rel_strength": 1.1, "market_momentum": 0.7, "dist_to_vwap": 0.002}]
        with self.assertRaisesRegex(AssertionError, "chasing trade"):
            validate_phase_3_shawn_logic_filter(history)


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

    def test_phase_4_rejects_daily_loss_limit_breach(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaisesRegex(AssertionError, "Circuit breaker tripped"):
            validate_phase_4_safety_checks(
                daily_pnl_pct=-0.02,
                seconds_since_last_tick=2,
                current_positions=0,
                open_signal_ids=set(),
                candidate_signal_id="sig-a",
                last_loss_time=None,
                now_utc=now,
            )

    def test_phase_4_rejects_stale_data(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaisesRegex(AssertionError, "Stale data guard triggered"):
            validate_phase_4_safety_checks(
                daily_pnl_pct=-0.01,
                seconds_since_last_tick=6,
                current_positions=0,
                open_signal_ids=set(),
                candidate_signal_id="sig-a",
                last_loss_time=None,
                now_utc=now,
            )

    def test_phase_4_rejects_double_entry(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaisesRegex(AssertionError, "Double entry prevention"):
            validate_phase_4_safety_checks(
                daily_pnl_pct=-0.01,
                seconds_since_last_tick=2,
                current_positions=1,
                open_signal_ids={"sig-a"},
                candidate_signal_id="sig-a",
                last_loss_time=None,
                now_utc=now,
            )

    def test_phase_4_rejects_wash_sale_cooldown(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaisesRegex(AssertionError, "Wash-sale cooldown is active"):
            validate_phase_4_safety_checks(
                daily_pnl_pct=-0.01,
                seconds_since_last_tick=2,
                current_positions=0,
                open_signal_ids=set(),
                candidate_signal_id="sig-a",
                last_loss_time=now - timedelta(minutes=29),
                now_utc=now,
            )


if __name__ == "__main__":
    unittest.main()
