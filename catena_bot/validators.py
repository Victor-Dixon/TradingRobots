"""Validation suite for Catena-Bot phases.

This module is intentionally deterministic and unit-test friendly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Mapping

from catena_bot.ssot_config import SSOT


@dataclass(frozen=True)
class ConnectionState:
    active: bool
    receiving: bool


def validate_phase_1_backtest(strategy_results: Mapping[str, float]) -> bool:
    assert strategy_results["win_rate"] > SSOT.phase_1_min_win_rate, "Win rate too low for scalping."
    assert (
        strategy_results["profit_factor"] > SSOT.phase_1_min_profit_factor
    ), "Strategy is not yielding enough per $ risked."
    assert (
        strategy_results["max_drawdown"] < SSOT.phase_1_max_drawdown
    ), "Risk is too high; drawdown exceeds 15%."
    assert (
        strategy_results["sharpe_ratio"] > SSOT.phase_1_min_sharpe
    ), "Risk-adjusted return is insufficient."
    return True


def validate_phase_2_execution_latency(
    order_logs: Iterable[Mapping[str, datetime]],
    broker_connection: ConnectionState,
    futures_stream: ConnectionState,
) -> bool:
    for order in order_logs:
        latency = order["filled_at"] - order["signal_at"]
        assert latency.total_seconds() < SSOT.phase_2_max_latency_seconds, (
            f"Latency too high: {latency.total_seconds()}s"
        )

    assert broker_connection.active, "Broker WebSocket is disconnected."
    assert futures_stream.receiving, "Nasdaq Futures data feed is lagging."
    return True


def validate_phase_3_shawn_logic_filter(trade_history: Iterable[Mapping[str, float]]) -> bool:
    for trade in trade_history:
        assert trade["stock_rel_strength"] > trade["market_momentum"], "Bot entered a weak stock."
        assert trade["dist_to_vwap"] < 0.002, "Bot entered a chasing trade (not compressed)."
    return True


def validate_phase_4_safety_checks(
    daily_pnl_pct: float,
    seconds_since_last_tick: int,
    current_positions: int,
    open_signal_ids: set[str],
    candidate_signal_id: str,
    last_loss_time: datetime | None,
    now_utc: datetime,
) -> bool:
    assert daily_pnl_pct > -SSOT.phase_4_daily_loss_limit_pct, "Circuit breaker tripped at -2% daily loss."
    assert seconds_since_last_tick <= SSOT.phase_4_stale_data_seconds, "Stale data guard triggered."

    if candidate_signal_id in open_signal_ids and current_positions > 0:
        raise AssertionError("Double entry prevention triggered for identical signal.")

    if last_loss_time is not None:
        cool_off = timedelta(minutes=SSOT.phase_4_reentry_cooldown_minutes)
        assert now_utc - last_loss_time >= cool_off, "Wash-sale cooldown is active."
    return True
