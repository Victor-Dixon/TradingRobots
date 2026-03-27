# Catena-Bot (Shawn Momentum Engine)

Version: **1.0.0-MVP**

This README is the **project SSOT** for architecture, safety rails, and Definition of Done.

Detailed phased delivery requirements and the test gate matrix live in `PRD.md` and must stay aligned with this README.


## Project Structure (ASCII SSOT)
```text
TradingRobots/
├── catena_bot/                     # Primary Catena-Bot logic (SSOT code location)
│   ├── __init__.py
│   ├── ssot_config.py              # Central thresholds/config constants
│   ├── validators.py               # Phase DoD validation logic
│   ├── data_downloader.py          # Phase-1 data ingestion implementation
│   ├── live_engine.py              # Phase-2 live stream + heartbeat orchestration
│   ├── integration_validator.py    # Phase-1/Phase-2 compatibility checks
│   └── mock_care_package.py        # Phase-5 architect mocking package
├── tests/
│   ├── test_validators.py          # Unit tests for all phase gates
│   ├── test_live_engine.py         # Unit tests for live execution integration
│   ├── test_integration_phase_gates.py
│   ├── test_e2e_phased_plan.py
│   └── test_mock_care_package.py   # Unit tests for architect mocked package
├── ci/
│   └── run_tests.sh                # Unit + integration + e2e release gate
├── scripts/
│   └── setup_env.sh
├── PRD.md                          # Phased plan + DoD test matrix
├── AGENTS.md                       # Agent guardrails for SSOT/TDD/phase expansion
├── data_downloader.py              # Compatibility wrapper
└── download_phase1_data.py         # Compatibility wrapper
```

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
- Success thresholds:
  - Signal-to-fill latency < 2 seconds.
  - Connectivity uptime >= 60 minutes.
  - Heartbeat gap <= 10 seconds.
  - VWAP parity drift <= 0.01%.
  - Kill-switch close-out < 500ms.
  - Phase 1 strategy importable inside live loop.

### Phase 3 — Shawn Intelligence Layer
- Goal: Enforce Relative Strength + VWAP compression filters.
- Success threshold: Strict filter compliance for all entries.

### Phase 4 — Safety and Over-Engineering
- Circuit Breaker: Halt trading at -2% daily PnL.
- Stale Data Guard: Trigger safety action if feed is stale > 5s.
- Double Entry Guard: Prevent duplicate entries for same signal.
- Wash-Sale Cooldown: Prevent immediate revenge re-entry after a loss.

### Phase 5 — Architect Mocked Care Package
- Goal: Provide deterministic synthetic Shawn scenarios and mock broker fills with zero external dependencies.
- Success thresholds:
  - Futures-lead bearish condition blocks entries.
  - Shawn squeeze requires `dist_to_vwap < 0.002`.
  - Circuit breaker shuts down bot after 3 consecutive -0.5% stop losses.
  - Stale stream panic closes all positions after 15 seconds without bars.

## TDD Validation Suite (First-Class)
Validation logic is codified in:
- `catena_bot/validators.py`
- `tests/test_validators.py`
- `PRD.md` (phase-by-phase required test gates)

For each phase, both happy-path and boundary/failure tests must pass before marking the phase complete.

`ci/run_tests.sh` is the release gate and runs unit, integration, and e2e tests that map to the phased DoD plan.

## Data Scraper (Phase 1)
`catena_bot/data_downloader.py` is the active scraper (root scripts are compatibility wrappers).
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
python -m catena_bot.data_downloader --ticker TSLA --nq-symbol QQQ --days 30
cd ci
./run_tests.sh
```

## Definition of Done (DoD)
A phase is done only when:
- Code is modular and symbol-swappable via one argument.
- Validation tests for that phase (as listed in `PRD.md`) are passing.
- Bot decisions are loggable to `bot_history.log` in runtime layers.
- Error handling and reconnect logic are covered before live capital.
