"""Unit tests for Phase 2 live execution utilities."""

from __future__ import annotations

import unittest

import pandas as pd

from catena_bot.integration_validator import validate_phase_1_integration
from catena_bot.live_engine import (
    LiveBar,
    LiveExecutionEngine,
    build_live_window_from_rows,
    compare_signal_parity,
)


class StubPhase1Logic:
    def __init__(self, signal: str = "HOLD") -> None:
        self.signal = signal

    def check_signal(self, bar: LiveBar) -> str:
        return self.signal


class DataFrameSignalLogic:
    def __init__(self, signal: str = "HOLD") -> None:
        self.signal = signal

    def check_signal(self, live_window: pd.DataFrame) -> str:
        return self.signal


class TestLiveExecutionEngine(unittest.TestCase):
    def test_on_bar_update_executes_order_when_phase_1_emits_buy(self) -> None:
        logic = StubPhase1Logic(signal="BUY")
        engine = LiveExecutionEngine(phase_1_logic=logic, heartbeat_timeout_seconds=10)

        bar = LiveBar(symbol="TSLA", close=250.12)
        engine.on_bar_update(bar)

        self.assertEqual(len(engine.order_log), 1)
        self.assertEqual(engine.order_log[0]["symbol"], "TSLA")
        self.assertEqual(engine.order_log[0]["side"], "buy")

    def test_check_stale_data_triggers_flatten(self) -> None:
        logic = StubPhase1Logic(signal="HOLD")
        fake_now = {"value": 100.0}

        def fake_time() -> float:
            return fake_now["value"]

        flatten_calls = []

        def on_flatten() -> None:
            flatten_calls.append("flatten")

        engine = LiveExecutionEngine(
            phase_1_logic=logic,
            heartbeat_timeout_seconds=10,
            time_fn=fake_time,
            emergency_flatten_fn=on_flatten,
        )

        engine.last_heartbeat = 85.0
        self.assertTrue(engine.check_stale_data())
        self.assertEqual(flatten_calls, ["flatten"])

    def test_on_bar_update_cancels_buy_when_nq_dumps(self) -> None:
        logic = DataFrameSignalLogic(signal="BUY")
        engine = LiveExecutionEngine(
            phase_1_logic=logic,
            heartbeat_timeout_seconds=10,
            market_dump_threshold_pct=0.01,
        )

        safe = LiveBar(symbol="TSLA", close=250.12, volume=1000, timestamp="2026-03-27T12:00:00Z")
        dumped = LiveBar(symbol="TSLA", close=251.0, volume=1100, timestamp="2026-03-27T12:01:00Z")

        engine.on_bar_update(safe, market_momentum=-0.005)
        engine.on_bar_update(dumped, market_momentum=-0.02)

        self.assertEqual(len(engine.order_log), 1)
        self.assertEqual(engine.order_log[0]["symbol"], "TSLA")

    def test_on_bar_update_records_shawn_speed_under_threshold(self) -> None:
        logic = DataFrameSignalLogic(signal="BUY")
        fake_now = {"value": 100.0}

        def fake_time() -> float:
            current = fake_now["value"]
            fake_now["value"] += 0.2
            return current

        engine = LiveExecutionEngine(
            phase_1_logic=logic,
            heartbeat_timeout_seconds=10,
            time_fn=fake_time,
            max_handle_bar_latency_ms=500,
        )
        bar = LiveBar(symbol="TSLA", close=250.12, volume=1000, timestamp="2026-03-27T12:00:00Z")
        engine.on_bar_update(bar, market_momentum=0.0)

        self.assertEqual(len(engine.order_log), 1)
        self.assertLessEqual(engine.order_log[0]["signal_to_order_ms"], 500)

    def test_on_bar_update_skips_missing_data_rows(self) -> None:
        logic = DataFrameSignalLogic(signal="BUY")
        engine = LiveExecutionEngine(phase_1_logic=logic, heartbeat_timeout_seconds=10)
        bar_missing_close = LiveBar(
            symbol="TSLA",
            close=float("nan"),
            volume=1000,
            timestamp="2026-03-27T12:00:00Z",
        )
        engine.on_bar_update(bar_missing_close, market_momentum=0.0)
        self.assertEqual(len(engine.order_log), 0)
        self.assertTrue(engine.data_window.empty)


class TestPhase2ValidationUtilities(unittest.TestCase):
    def test_compare_signal_parity_matches_batch_vs_live(self) -> None:
        csv_signals = pd.Series(["HOLD", "BUY", "HOLD"])
        live_signals = pd.Series(["HOLD", "BUY", "HOLD"])
        self.assertTrue(compare_signal_parity(csv_signals, live_signals))

    def test_compare_signal_parity_rejects_ghost_signal_mismatch(self) -> None:
        csv_signals = pd.Series(["HOLD", "BUY", "HOLD"])
        live_signals = pd.Series(["HOLD", "SELL", "HOLD"])
        with self.assertRaisesRegex(AssertionError, "Ghost Signals"):
            compare_signal_parity(csv_signals, live_signals)

    def test_build_live_window_from_rows_drops_nan_rows(self) -> None:
        rows = [
            {"close": 100.0, "volume": 1_000, "timestamp": "2026-03-27T12:00:00Z"},
            {"close": None, "volume": 1_200, "timestamp": "2026-03-27T12:01:00Z"},
            {"close": 101.0, "volume": 900, "timestamp": "2026-03-27T12:02:00Z"},
        ]
        window = build_live_window_from_rows(rows)
        self.assertEqual(len(window), 2)
        self.assertListEqual(window["close"].tolist(), [100.0, 101.0])


class TestPhase1IntegrationValidator(unittest.TestCase):
    def test_phase_1_integration_happy_path(self) -> None:
        sample = pd.DataFrame(
            {
                "close": [100, 101, 102],
                "vwap": [99.5, 100.5, 101.5],
            }
        )
        signal = pd.Series(["HOLD", "HOLD", "BUY"])
        self.assertTrue(validate_phase_1_integration(sample, signal))

    def test_phase_1_integration_rejects_shape_mismatch(self) -> None:
        sample = pd.DataFrame({"close": [100, 101], "vwap": [99.5, 100.5]})
        signal = pd.Series(["BUY"])
        with self.assertRaisesRegex(AssertionError, "Data shape mismatch"):
            validate_phase_1_integration(sample, signal)


if __name__ == "__main__":
    unittest.main()
