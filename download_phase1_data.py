"""Phase 1 data ingestion for Quant pipeline.

Downloads 1-minute historical bars for:
- TSLA (equity)
- /NQ proxy symbol (default: QQQ; can be changed with --nq-symbol)

SSOT note:
- This file is the single source of truth for phase-1 raw minute-bar ingestion.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: alpaca-py. Install with `pip install alpaca-py pandas pyarrow`."
    ) from exc


@dataclass(frozen=True)
class DataConfig:
    """SSOT for data download configuration."""

    tsla_symbol: str = "TSLA"
    nq_proxy_symbol: str = "QQQ"
    lookback_days: int = 30
    timeframe: TimeFrame = TimeFrame.Minute
    output_dir: str = "data/phase1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download 1-minute bars for TSLA and an /NQ proxy symbol from Alpaca and "
            "save them as parquet + CSV for VectorBT backtesting."
        )
    )
    parser.add_argument(
        "--tsla-symbol",
        default=DataConfig.tsla_symbol,
        help="Primary stock symbol (default: TSLA).",
    )
    parser.add_argument(
        "--nq-symbol",
        default=DataConfig.nq_proxy_symbol,
        help=(
            "Nasdaq futures proxy symbol (default: QQQ). "
            "If your Alpaca plan includes futures data, pass your preferred futures symbol."
        ),
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DataConfig.lookback_days,
        help="Lookback window in days (default: 30).",
    )
    parser.add_argument(
        "--output-dir",
        default=DataConfig.output_dir,
        help="Output folder for normalized files (default: data/phase1).",
    )
    parser.add_argument(
        "--slippage-bps",
        type=float,
        default=5.0,
        help=(
            "Slippage basis points for downstream backtests. 5 bps = 0.05%% "
            "(metadata only; no price mutation in this step)."
        ),
    )
    return parser.parse_args()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def build_client() -> StockHistoricalDataClient:
    key = _require_env("APCA_API_KEY_ID")
    secret = _require_env("APCA_API_SECRET_KEY")
    return StockHistoricalDataClient(api_key=key, secret_key=secret)


def fetch_minute_bars(
    client: StockHistoricalDataClient,
    symbol: str,
    start_utc: datetime,
    end_utc: datetime,
    timeframe: TimeFrame,
) -> pd.DataFrame:
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start_utc,
        end=end_utc,
        adjustment="all",
    )
    bars = client.get_stock_bars(request).df

    if bars.empty:
        raise SystemExit(
            f"No bars returned for {symbol}. Verify symbol availability and market data permissions."
        )

    # Result index is usually MultiIndex (symbol, timestamp).
    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
    else:
        bars = bars.reset_index().rename(columns={"index": "timestamp"})
        bars["symbol"] = symbol

    required_cols = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]
    missing = [c for c in required_cols if c not in bars.columns]
    if missing:
        raise SystemExit(f"Missing expected columns for {symbol}: {missing}")

    bars = bars[required_cols].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars = bars.sort_values("timestamp").reset_index(drop=True)
    return bars


def add_metadata(df: pd.DataFrame, slippage_bps: float) -> pd.DataFrame:
    out = df.copy()
    out["slippage_bps"] = slippage_bps
    out["slippage_pct"] = slippage_bps / 10_000.0
    return out


def save_symbol_frame(df: pd.DataFrame, output_dir: Path, symbol: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = symbol.replace("/", "_")
    parquet_path = output_dir / f"{stem}_1m.parquet"
    csv_path = output_dir / f"{stem}_1m.csv"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    return parquet_path, csv_path


def build_manifest(
    output_dir: Path,
    tsla_symbol: str,
    nq_symbol: str,
    start_utc: datetime,
    end_utc: datetime,
    slippage_bps: float,
) -> Path:
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timeframe": "1Min",
        "symbols": [tsla_symbol, nq_symbol],
        "window_start_utc": start_utc.isoformat(),
        "window_end_utc": end_utc.isoformat(),
        "slippage_bps_for_backtest": slippage_bps,
        "note": "Use slippage_bps during VectorBT order simulation, not data preprocessing.",
    }
    path = output_dir / "manifest.json"
    pd.Series(manifest).to_json(path, indent=2)
    return path


def main() -> None:
    args = parse_args()
    cfg = DataConfig(
        tsla_symbol=args.tsla_symbol,
        nq_proxy_symbol=args.nq_symbol,
        lookback_days=args.days,
        output_dir=args.output_dir,
    )

    end_utc = datetime.now(timezone.utc)
    start_utc = end_utc - timedelta(days=cfg.lookback_days)

    client = build_client()

    tsla = fetch_minute_bars(
        client=client,
        symbol=cfg.tsla_symbol,
        start_utc=start_utc,
        end_utc=end_utc,
        timeframe=cfg.timeframe,
    )
    nq = fetch_minute_bars(
        client=client,
        symbol=cfg.nq_proxy_symbol,
        start_utc=start_utc,
        end_utc=end_utc,
        timeframe=cfg.timeframe,
    )

    tsla = add_metadata(tsla, args.slippage_bps)
    nq = add_metadata(nq, args.slippage_bps)

    output_dir = Path(cfg.output_dir)
    tsla_parquet, tsla_csv = save_symbol_frame(tsla, output_dir, cfg.tsla_symbol)
    nq_parquet, nq_csv = save_symbol_frame(nq, output_dir, cfg.nq_proxy_symbol)
    manifest_path = build_manifest(
        output_dir=output_dir,
        tsla_symbol=cfg.tsla_symbol,
        nq_symbol=cfg.nq_proxy_symbol,
        start_utc=start_utc,
        end_utc=end_utc,
        slippage_bps=args.slippage_bps,
    )

    print("Data download complete.")
    print(f"- {cfg.tsla_symbol}: {len(tsla):,} rows -> {tsla_parquet} and {tsla_csv}")
    print(f"- {cfg.nq_proxy_symbol}: {len(nq):,} rows -> {nq_parquet} and {nq_csv}")
    print(f"- Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
