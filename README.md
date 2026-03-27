# Catena-Bot (Shawn Momentum Engine)

Version: **1.0.0-MVP**

This README is the **project SSOT** for architecture, safety rails, and Definition of Done.

## Strategy Overview
Catena-Bot targets momentum scalps by combining:
- VWAP compression/breakout behavior
- MACD curl/crossover timing
- Relative strength of target stock vs. Nasdaq proxy (`/NQ` proxy symbol)

## Phased Architecture
### Phase 1 — Quant Foundation (Backtesting)
- Goal: Validate expectancy on 1-minute historical data.
- Success thresholds:
  - Win Rate > 45%
  - Profit Factor > 1.2
  - Max Drawdown < 15%
  - Sharpe Ratio > 1.5

### Phase 2 — Execution Engine (Paper)
- Goal: Stable market-data + broker connectivity with low latency.
- Success threshold: Signal-to-fill latency < 2 seconds.

### Phase 3 — Shawn Intelligence Layer
- Goal: Enforce Relative Strength + VWAP compression filters.
- Success threshold: Strict filter compliance for all entries.

### Phase 4 — Safety and Over-Engineering
- Circuit Breaker: Halt trading at -2% daily PnL.
- Stale Data Guard: Trigger safety action if feed is stale > 5s.
- Double Entry Guard: Prevent duplicate entries for same signal.
- Wash-Sale Cooldown: Prevent immediate revenge re-entry after a loss.

## TDD Validation Suite (First-Class)
Validation logic is codified in:
- `catena_bot/validators.py`
- `tests/test_validators.py`

## Data Scraper (Phase 1)
`data_downloader.py` is the active scraper.
- Pulls last `N` days of 1-minute bars for ticker + `/NQ` proxy.
- Saves parquet + CSV + `manifest.json` under `data/phase1`.
- Includes slippage metadata for backtest simulation.

Backward compatibility:
- `download_phase1_data.py` is a wrapper that calls `data_downloader.py`.

## Environment Setup
```bash
bash scripts/setup_env.sh
source .venv/bin/activate
cp .env.example .env
```

Set environment variables:
```bash
export APCA_API_KEY_ID="your_key"
export APCA_API_SECRET_KEY="your_secret"
```

## Run
```bash
python data_downloader.py --ticker TSLA --nq-symbol QQQ --days 30
cd ci
./run_tests.sh
```

## Definition of Done (DoD)
A phase is done only when:
- Code is modular and symbol-swappable via one argument.
- Validation tests are passing.
- Bot decisions are loggable to `bot_history.log` in runtime layers.
- Error handling and reconnect logic are covered before live capital.
