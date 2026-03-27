"""Phase 2 live execution scaffolding.

This module is intentionally lightweight so it can be validated in unit tests
without requiring a real broker/WebSocket connection.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
import logging
from typing import Callable, Protocol

from catena_bot.ssot_config import SSOT

logger = logging.getLogger(__name__)


class Phase1SignalLogic(Protocol):
    def check_signal(self, bar: "LiveBar") -> str: ...


@dataclass(frozen=True)
class LiveBar:
    symbol: str
    close: float


class LiveExecutionEngine:
    """Small orchestration layer between live bars and Phase 1 strategy signals."""

    def __init__(
        self,
        *,
        phase_1_logic: Phase1SignalLogic,
        heartbeat_timeout_seconds: int = SSOT.phase_2_max_heartbeat_gap_seconds,
        time_fn: Callable[[], float] = time.time,
        emergency_flatten_fn: Callable[[], None] | None = None,
    ) -> None:
        self.phase_1_logic = phase_1_logic
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.time_fn = time_fn
        self.last_heartbeat = self.time_fn()
        self.emergency_flatten_fn = emergency_flatten_fn
        self.order_log: list[dict[str, str | float]] = []

    def on_bar_update(self, bar: LiveBar) -> None:
        self.last_heartbeat = self.time_fn()
        logger.info(f"🛰️ Live Bar Received | {bar.symbol} | Price: {bar.close}")

        signal = self.phase_1_logic.check_signal(bar)
        if signal == "BUY":
            self.execute_order(bar.symbol, "buy")

    def execute_order(self, symbol: str, side: str) -> None:
        logger.warning(f"🚀 EXECUTING {side.upper()} ORDER: {symbol}")
        self.order_log.append({"symbol": symbol, "side": side, "time": self.time_fn()})

    def check_stale_data(self) -> bool:
        age = self.time_fn() - self.last_heartbeat
        if age > self.heartbeat_timeout_seconds:
            logger.critical("🚨 STALE DATA DETECTED. Data lag > 10s. Flattening positions!")
            if self.emergency_flatten_fn is not None:
                self.emergency_flatten_fn()
            return True
        return False


def create_stock_data_stream(api_key: str, secret_key: str):
    """Create an Alpaca stock stream lazily so tests don't require alpaca imports."""

    from alpaca.data.live import StockDataStream

    return StockDataStream(api_key, secret_key)
