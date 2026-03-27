"""Unit tests for Phase 2 live execution utilities."""

from __future__ import annotations

import unittest

import pandas as pd

from catena_bot.integration_validator import validate_phase_1_integration
from catena_bot.live_engine import LiveBar, LiveExecutionEngine


class StubPhase1Logic:
    def __init__(self, signal: str = "HOLD") -> None:
        self.signal = signal

    def check_signal(self, bar: LiveBar) -> str:
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
