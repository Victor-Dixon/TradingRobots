"""Architect-phase mocked care package for deterministic offline testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Tuple
from unittest.mock import MagicMock

import numpy as np
import pandas as pd

from catena_bot.ssot_config import SSOT


def generate_mock_shawn_setup(ticker: str = "TSLA", scenario: str = "breakout") -> pd.DataFrame:
    """Generate synthetic minute bars for Shawn-style scenarios."""

    periods = 60
    base_price = 250.0
    times = [datetime.now() - timedelta(minutes=i) for i in range(periods)][::-1]

    prices = [base_price + np.sin(i / 5) * 0.2 for i in range(periods)]

    if scenario == "breakout":
        for i in range(5):
            prices[-(5 - i)] += (i + 1) * 0.5
    elif scenario == "fakeout":
        prices[-1] -= 0.6
    elif scenario == "futures_drag":
        prices[-3:] = [p - 0.3 for p in prices[-3:]]

    return pd.DataFrame(
        {
            "timestamp": times,
            "symbol": [ticker] * periods,
            "close": prices,
            "high": [p + 0.1 for p in prices],
            "low": [p - 0.1 for p in prices],
            "volume": [
                1000 + (5000 if scenario == "breakout" and idx > 55 else 0)
                for idx in range(periods)
            ],
        }
    )


def create_mock_alpaca_client() -> MagicMock:
    """Return a mocked broker client with a filled market order."""

    client = MagicMock()
    client.submit_order.return_value = MagicMock(status="filled", filled_avg_price=252.50)
    return client


def is_shawn_setup(
    stock_rel_strength: float,
    market_momentum: float,
    dist_to_vwap: float,
    futures_momentum: float,
) -> Tuple[bool, str]:
    """Evaluate Shawn setup with human-readable PASS/NO-TRADE messages."""

    if stock_rel_strength <= market_momentum:
        return False, "PASS: Bot refused trade because relative strength was weak."
    if futures_momentum < SSOT.architect_min_futures_momentum:
        return False, "PASS: Bot refused trade because Futures were bearish."
    if dist_to_vwap >= SSOT.architect_max_dist_to_vwap:
        return False, "PASS: Bot refused trade because setup was too far from VWAP."
    return True, "PASS: Bot accepted compressed Shawn setup with bullish futures confirmation."


@dataclass
class MockTradingBot:
    """Small test harness for circuit breaker and stale-data emergency logic."""

    alpaca_client: MagicMock
    stale_data_seconds: int = SSOT.architect_stale_data_seconds
    consecutive_losses: int = 0
    shutdown: bool = False
    logs: list[str] = field(default_factory=list)

    def record_trade_result(self, pnl_pct: float) -> None:
        if pnl_pct <= -SSOT.architect_stop_loss_pct:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        if self.consecutive_losses >= SSOT.architect_circuit_breaker_losses:
            self.shutdown = True
            self.logs.append("PASS: Bot shut down after 3 consecutive stop losses.")

    def handle_data_gap(self, seconds_without_bars: int) -> bool:
        if seconds_without_bars >= self.stale_data_seconds:
            self.alpaca_client.close_all_positions()
            self.logs.append("PASS: Bot emergency-closed due to stale data feed.")
            return True
        return False
