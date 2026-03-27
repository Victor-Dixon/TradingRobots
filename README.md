# Catena-Bot (Shawn Momentum Engine)

Version: **1.0.0-MVP**

This README is the **project SSOT** for architecture, safety rails, and Definition of Done.

Detailed phased delivery requirements and the test gate matrix live in `PRD.md` and must stay aligned with this README.


## Project Structure (ASCII SSOT)
```text
TradingRobots/
├── .github/workflows/
│   ├── ci.yml                     # CI gate (LOC guard + phased tests)
│   └── cd.yml                     # CD artifact delivery workflow
├── catena_bot/                     # Primary Catena-Bot logic (SSOT code location)
│   ├── __init__.py
│   ├── ssot_config.py              # Central thresholds/config constants
│   ├── validators.py               # Phase DoD validation logic
│   ├── data_downloader.py          # Phase-1 data ingestion implementation
│   ├── live_engine.py              # Phase-2 live stream + heartbeat orchestration
│   ├── integration_validator.py    # Phase-1/Phase-2 compatibility checks
│   ├── mock_care_package.py        # Phase-5 architect mocking package
│   └── phase_status.py             # CI phase reporter + next-agent prompt writer
├── tests/
│   ├── test_validators.py          # Unit tests for all phase gates
│   ├── test_live_engine.py         # Unit tests for live execution integration
│   ├── test_data_downloader.py    # Unit tests for offline data acquisition logic
│   ├── test_integration_phase_gates.py
│   ├── test_e2e_phased_plan.py
│   ├── test_mock_care_package.py   # Unit tests for architect mocked package
│   ├── test_phase_status.py        # Unit tests for CI phase report + handoff prompt
│   └── test_phase6_handoff_coverage.py # Phase-6 integration/UX-edge/e2e prompt-flow tests
├── ci/
│   └── run_tests.sh                # Unit + integration + e2e release gate
├── scripts/
│   └── setup_env.sh
├── PRD.md                          # Phased plan + DoD test matrix
├── NEXT_AGENT_PROMPT.md            # Generated deterministic handoff prompt
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
  - Handle-bar-to-order ("Shawn Speed") <= 500ms.
  - Phase 1 strategy importable inside live loop.
  - CSV/live signal parity required to block "Ghost Signals."
  - Missing bar fields are sanitized (`dropna`) before strategy evaluation.
  - Long entries are vetoed when Nasdaq proxy momentum dumps.

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

### Phase 6 — Test Coverage Improvement (Integration + UX Edge Cases + E2E)
- Goal: Improve coverage quality around agent handoff process reliability and user-facing workflow clarity.
- Success thresholds:
  - Integration coverage verifies prompt generation and metadata freshness checks together.
  - User-experience edge-case coverage enforces read → complete task → next-day setup guidance in prompts.
  - E2E coverage validates deterministic prompt regeneration through CI phase-status reporting.

## TDD Validation Suite (First-Class)
Validation logic is codified in:
- `catena_bot/validators.py`
- `tests/test_validators.py`
- `tests/test_data_downloader.py`
- `PRD.md` (phase-by-phase required test gates)

For each phase, both happy-path and boundary/failure tests must pass before marking the phase complete.

`ci/run_tests.sh` is the release gate and runs unit, integration, and e2e tests that map to the phased DoD plan.

`ci/run_tests.sh` also prints the current SSOT phase completion, rewrites `NEXT_AGENT_PROMPT.md` every run, validates fresh metadata (`Generated at`, `Git SHA`, `Workflow ID`), and echoes the prompt body in CI logs for handoff visibility.

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

## CI/CD
- CI is defined in `.github/workflows/ci.yml` and runs:
  - dependency install,
  - Python LOC guard (`< 400` lines),
  - phased release gate via `./ci/run_tests.sh`.
- CD is defined in `.github/workflows/cd.yml` and runs on release/manual dispatch:
  - full phased release gate tests,
  - build + upload of a delivery artifact tarball.

## Definition of Done (DoD)
A phase is done only when:
- Code is modular and symbol-swappable via one argument.
- Validation tests for that phase (as listed in `PRD.md`) are passing.
- Bot decisions are loggable to `bot_history.log` in runtime layers.
- Error handling and reconnect logic are covered before live capital.
