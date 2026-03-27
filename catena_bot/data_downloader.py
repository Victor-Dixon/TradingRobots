"""Phase 1 Data Scraper (SSOT-aligned).

Pulls the last N days of 1-minute bars for target symbol and NQ proxy via Alpaca.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from catena_bot.ssot_config import SSOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download 1-minute bars for Catena-Bot Phase 1.")
    parser.add_argument("--ticker", default=SSOT.default_symbol)
    parser.add_argument("--nq-symbol", default=SSOT.default_nq_proxy)
    parser.add_argument("--days", type=int, default=SSOT.default_lookback_days)
    parser.add_argument("--output-dir", default="data/phase1")
    parser.add_argument("--slippage-bps", type=float, default=SSOT.default_slippage_bps)
    return parser.parse_args()


def _env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def _alpaca_types() -> tuple[Any, Any, Any]:
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Install dependencies first: pip install -r requirements.txt") from exc
    return StockHistoricalDataClient, StockBarsRequest, TimeFrame


def _create_stock_client(api_key: str, secret_key: str):
    stock_client_cls, _, _ = _alpaca_types()
    return stock_client_cls(api_key, secret_key)


def _fetch_stock(client: Any, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    _, stock_bars_request_cls, time_frame = _alpaca_types()
    req = stock_bars_request_cls(
        symbol_or_symbols=symbol,
        timeframe=time_frame.Minute,
        start=start,
        end=end,
        adjustment="all",
    )
    frame = client.get_stock_bars(req).df
    if frame.empty:
        raise SystemExit(f"No data returned for {symbol}. Check symbol and permissions.")
    frame = frame.reset_index() if isinstance(frame.index, pd.MultiIndex) else frame.reset_index()
    if "symbol" not in frame.columns:
        frame["symbol"] = symbol
    if "timestamp" not in frame.columns:
        frame = frame.rename(columns={"index": "timestamp"})
    frame = frame[["timestamp", "symbol", "open", "high", "low", "close", "volume"]].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame.sort_values("timestamp").reset_index(drop=True)


def _save(df: pd.DataFrame, output_dir: Path, symbol: str, slippage_bps: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out["slippage_bps"] = slippage_bps
    out["slippage_pct"] = slippage_bps / 10_000.0
    stem = symbol.replace("/", "_")
    out.to_parquet(output_dir / f"{stem}_1m.parquet", index=False)
    out.to_csv(output_dir / f"{stem}_1m.csv", index=False)


def main() -> None:
    args = parse_args()
    client = _create_stock_client(_env("APCA_API_KEY_ID"), _env("APCA_API_SECRET_KEY"))
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)
    output_dir = Path(args.output_dir)

    ticker_df = _fetch_stock(client, args.ticker, start, end)
    nq_df = _fetch_stock(client, args.nq_symbol, start, end)
    _save(ticker_df, output_dir, args.ticker, args.slippage_bps)
    _save(nq_df, output_dir, args.nq_symbol, args.slippage_bps)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": SSOT.version,
        "timeframe": SSOT.default_timeframe,
        "symbols": [args.ticker, args.nq_symbol],
        "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(),
        "slippage_bps": args.slippage_bps,
    }
    pd.Series(manifest).to_json(output_dir / "manifest.json", indent=2)
    print(f"Saved phase-1 data to {output_dir}")


if __name__ == "__main__":
    main()
