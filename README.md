# TradingRobots - Quant Pipeline Bootstrap

This repository now starts with **Phase 1 data infrastructure**.

## Single Source of Truth (SSOT)
`download_phase1_data.py` is the SSOT for minute-bar ingestion used by the backtesting pipeline.

## What it does
- Downloads the last N days of 1-minute bars from Alpaca.
- Pulls data for:
  - `TSLA`
  - an `/NQ` proxy (default `QQQ`, configurable via CLI)
- Adds slippage metadata (`0.05%` default = `5` bps) for downstream VectorBT simulation.
- Writes parquet + CSV + `manifest.json` under `data/phase1`.

## Setup
```bash
python -m pip install alpaca-py pandas pyarrow
export APCA_API_KEY_ID="..."
export APCA_API_SECRET_KEY="..."
```

## Run
```bash
python download_phase1_data.py --days 30 --tsla-symbol TSLA --nq-symbol QQQ
```

> Note: If your Alpaca account supports futures market data, you can pass your preferred futures symbol via `--nq-symbol`.
