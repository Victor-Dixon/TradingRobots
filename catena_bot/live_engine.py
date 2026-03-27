"""Phase 2 live execution scaffolding.

This module is intentionally lightweight so it can be validated in unit tests
without requiring a real broker/WebSocket connection.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
import logging
from typing import Callable, Protocol

import pandas as pd

from catena_bot.ssot_config import SSOT

logger = logging.getLogger(__name__)


class Phase1SignalLogic(Protocol):
    def check_signal(self, bar_or_window: "LiveBar | pd.DataFrame") -> str: ...


@dataclass(frozen=True)
class LiveBar:
    symbol: str
    close: float
    volume: float = 0.0
    timestamp: str | None = None


class LiveExecutionEngine:
    """Small orchestration layer between live bars and Phase 1 strategy signals."""

    def __init__(
        self,
        *,
        phase_1_logic: Phase1SignalLogic,
        heartbeat_timeout_seconds: int = SSOT.phase_2_max_heartbeat_gap_seconds,
        market_dump_threshold_pct: float = SSOT.phase_2_market_dump_threshold_pct,
        max_handle_bar_latency_ms: int = SSOT.phase_2_max_handle_bar_latency_ms,
        time_fn: Callable[[], float] = time.time,
        emergency_flatten_fn: Callable[[], None] | None = None,
    ) -> None:
        self.phase_1_logic = phase_1_logic
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.market_dump_threshold_pct = market_dump_threshold_pct
        self.max_handle_bar_latency_ms = max_handle_bar_latency_ms
        self.time_fn = time_fn
        self.last_heartbeat = self.time_fn()
        self.emergency_flatten_fn = emergency_flatten_fn
        self.order_log: list[dict[str, str | float]] = []
        self.data_window = pd.DataFrame(columns=["close", "volume"])
        self.live_signal_log: list[str] = []

    def on_bar_update(self, bar: LiveBar, *, market_momentum: float = 0.0) -> None:
        start = self.time_fn()
        self.last_heartbeat = self.time_fn()
        logger.info(f"🛰️ Live Bar Received | {bar.symbol} | Price: {bar.close}")

        if _is_missing_bar_data(bar):
            logger.warning("Skipping bar due to missing data fields.")
            return

        self._append_to_window(bar)
        signal = self.phase_1_logic.check_signal(self.data_window)
        self.live_signal_log.append(signal)

        if signal == "BUY" and self._is_market_dumping(market_momentum):
            logger.warning("BUY vetoed because Nasdaq proxy momentum is in dump mode.")
            return

        if signal == "BUY":
            elapsed_ms = int((self.time_fn() - start) * 1000)
            self.execute_order(bar.symbol, "buy", signal_to_order_ms=elapsed_ms)

    def execute_order(self, symbol: str, side: str, *, signal_to_order_ms: int = 0) -> None:
        logger.warning(f"🚀 EXECUTING {side.upper()} ORDER: {symbol}")
        assert signal_to_order_ms <= self.max_handle_bar_latency_ms, (
            f"Shawn Speed breach: {signal_to_order_ms}ms exceeds "
            f"{self.max_handle_bar_latency_ms}ms."
        )
        self.order_log.append(
            {
                "symbol": symbol,
                "side": side,
                "time": self.time_fn(),
                "signal_to_order_ms": signal_to_order_ms,
            }
        )

    def check_stale_data(self) -> bool:
        age = self.time_fn() - self.last_heartbeat
        if age > self.heartbeat_timeout_seconds:
            logger.critical("🚨 STALE DATA DETECTED. Data lag > 10s. Flattening positions!")
            if self.emergency_flatten_fn is not None:
                self.emergency_flatten_fn()
            return True
        return False

    def _append_to_window(self, bar: LiveBar) -> None:
        idx = bar.timestamp if bar.timestamp is not None else len(self.data_window)
        new_row = pd.DataFrame([{"close": bar.close, "volume": bar.volume}], index=[idx])
        self.data_window = pd.concat([self.data_window, new_row]).tail(200).dropna()

    def _is_market_dumping(self, market_momentum: float) -> bool:
        return market_momentum <= -self.market_dump_threshold_pct


def _is_missing_bar_data(bar: LiveBar) -> bool:
    return pd.isna(bar.close) or pd.isna(bar.volume)


def build_live_window_from_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if "timestamp" in frame.columns:
        frame = frame.set_index("timestamp")
    required = [c for c in ("close", "volume") if c in frame.columns]
    return frame[required].dropna()


def compare_signal_parity(csv_signals: pd.Series, live_signals: pd.Series) -> bool:
    assert len(csv_signals) == len(live_signals), "Ghost Signals: CSV/live signal lengths differ."
    assert csv_signals.equals(live_signals), "Ghost Signals: CSV/live signal values differ."
    return True


def create_stock_data_stream(api_key: str, secret_key: str):
    """Create an Alpaca stock stream lazily so tests don't require alpaca imports."""

    from alpaca.data.live import StockDataStream

    return StockDataStream(api_key, secret_key)
