"""Architect phase mocked care package tests.

These tests validate offline deterministic behavior for synthetic data,
mock broker integration, and critical safety boundaries.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from catena_bot.mock_care_package import (
    MockTradingBot,
    create_mock_alpaca_client,
    generate_mock_shawn_setup,
    is_shawn_setup,
)


class TestMockDataSimulator(unittest.TestCase):
    def test_generate_mock_shawn_setup_breakout_has_late_volume_spike(self) -> None:
        df = generate_mock_shawn_setup(ticker="TSLA", scenario="breakout")

        self.assertEqual(len(df), 60)
        self.assertTrue((df["volume"].tail(4) > 1000).all())


class TestMustPassEdgeCases(unittest.TestCase):
    def test_a_futures_lead_logic_blocks_trade(self) -> None:
        trade, reason = is_shawn_setup(
            stock_rel_strength=1.3,
            market_momentum=0.7,
            dist_to_vwap=0.0015,
            futures_momentum=-0.1,
        )
        self.assertFalse(trade)
        self.assertIn("Futures were bearish", reason)

    def test_b_shawn_squeeze_accuracy_blocks_chasing_trade(self) -> None:
        trade, reason = is_shawn_setup(
            stock_rel_strength=1.3,
            market_momentum=0.7,
            dist_to_vwap=0.005,
            futures_momentum=0.2,
        )
        self.assertFalse(trade)
        self.assertIn("too far from VWAP", reason)

    def test_c_circuit_breaker_triggers_shutdown_after_three_losses(self) -> None:
        bot = MockTradingBot(alpaca_client=create_mock_alpaca_client())

        for _ in range(3):
            bot.record_trade_result(pnl_pct=-0.005)

        self.assertTrue(bot.shutdown)
        self.assertIn("PASS: Bot shut down after 3 consecutive stop losses.", bot.logs)

    def test_d_stale_data_panic_emergency_closes(self) -> None:
        client = create_mock_alpaca_client()
        client.close_all_positions = MagicMock(return_value=True)
        bot = MockTradingBot(alpaca_client=client, stale_data_seconds=15)

        bot.handle_data_gap(seconds_without_bars=15)

        client.close_all_positions.assert_called_once()
        self.assertIn("PASS: Bot emergency-closed due to stale data feed.", bot.logs)


class TestShawnSetupBranchCoverage(unittest.TestCase):
    def test_branch_coverage_for_is_shawn_setup(self) -> None:
        outcomes = [
            is_shawn_setup(0.6, 0.7, 0.001, 0.2),
            is_shawn_setup(1.2, 0.7, 0.001, -0.2),
            is_shawn_setup(1.2, 0.7, 0.005, 0.2),
            is_shawn_setup(1.2, 0.7, 0.001, 0.2),
        ]

        self.assertEqual([decision for decision, _ in outcomes], [False, False, False, True])


if __name__ == "__main__":
    unittest.main()
