"""SSOT configuration for Catena-Bot.

Any module needing core trading/data constants must import from here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CatenaSSOT:
    version: str = "1.0.0-MVP"
    default_symbol: str = "TSLA"
    default_nq_proxy: str = "QQQ"
    default_lookback_days: int = 30
    default_timeframe: str = "1Min"
    default_slippage_bps: float = 5.0
    phase_1_min_win_rate: float = 0.45
    phase_1_min_profit_factor: float = 1.2
    phase_1_max_drawdown: float = 0.15
    phase_1_min_sharpe: float = 1.5
    phase_2_max_latency_seconds: float = 2.0
    phase_2_required_uptime_minutes: int = 60
    phase_2_max_heartbeat_gap_seconds: int = 10
    phase_2_vwap_parity_tolerance_pct: float = 0.0001
    phase_2_kill_switch_max_close_ms: int = 500
    phase_3_max_dist_to_vwap: float = 0.002
    phase_4_daily_loss_limit_pct: float = 0.02
    phase_4_stale_data_seconds: int = 5
    phase_4_reentry_cooldown_minutes: int = 30


SSOT = CatenaSSOT()
