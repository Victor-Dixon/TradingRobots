# Catena-Bot PRD (Phased Delivery + DoD Test Matrix)

Version: **1.0.0-MVP**

This PRD aligns with `README.md` and `catena_bot/ssot_config.py` as the implementation SSOT.

## Product Goal
Build a momentum-focused trading bot that can be validated in deterministic phases before any live-capital risk.

## Test Navigation Index (Phase -> Test File)
- Unit DoD gates: [`tests/test_validators.py`](tests/test_validators.py)
- Phase-2 live engine unit tests: [`tests/test_live_engine.py`](tests/test_live_engine.py)
- Integration phased gates: [`tests/test_integration_phase_gates.py`](tests/test_integration_phase_gates.py)
- E2E phased plan flow: [`tests/test_e2e_phased_plan.py`](tests/test_e2e_phased_plan.py)

All completed tests listed below are required to remain passing and are executed by `ci/run_tests.sh`.

## Phased Plan and Definition of Done

### Phase 1 — Quant Foundation (Backtesting)
**Objective**
- Validate baseline expectancy using 1-minute historical data.

**DoD thresholds**
- Win Rate > 45%
- Profit Factor > 1.2
- Max Drawdown < 15%
- Sharpe Ratio > 1.5

**Required tests to pass (TDD gate)**
- ✅ `test_phase_1_backtest_validity` (`tests/test_validators.py`)
- ✅ `test_phase_1_backtest_rejects_low_win_rate` (`tests/test_validators.py`)
- ✅ `test_phase_1_backtest_rejects_low_profit_factor` (`tests/test_validators.py`)
- ✅ `test_phase_1_backtest_rejects_high_drawdown` (`tests/test_validators.py`)
- ✅ `test_phase_1_backtest_rejects_low_sharpe` (`tests/test_validators.py`)

### Phase 2 — Execution Engine (Paper)
**Objective**
- Ensure connectivity and low-latency signal-to-fill performance.

**DoD thresholds**
- Signal-to-fill latency < 2 seconds
- Broker/data connectivity healthy for >= 60 minutes
- Heartbeat gap <= 10 seconds
- Live VWAP parity vs chart feed within 0.01%
- Kill-switch close latency < 500ms
- Handle-bar-to-order ("Shawn Speed") latency <= 500ms
- Broker connection active and market/futures proxy stream receiving
- Phase 1 strategy importable/runnable inside live loop
- CSV-vs-live signal parity check to prevent "Ghost Signals"
- Missing-bar data rows are sanitized (`dropna`) instead of crashing
- TSLA long signals are vetoed when Nasdaq proxy momentum is in dump mode

**Required tests to pass (TDD gate)**
- ✅ `test_phase_2_execution_latency` (`tests/test_validators.py`)
- ✅ `test_phase_2_rejects_latency_breach` (`tests/test_validators.py`)
- ✅ `test_phase_2_rejects_disconnected_broker` (`tests/test_validators.py`)
- ✅ `test_phase_2_rejects_stale_futures_stream` (`tests/test_validators.py`)
- ✅ `test_phase_2_live_readiness` (`tests/test_validators.py`)
- ✅ `test_phase_2_live_readiness_rejects_stale_heartbeat` (`tests/test_validators.py`)
- ✅ `test_phase_2_live_readiness_rejects_kill_switch_latency` (`tests/test_validators.py`)
- ✅ `test_on_bar_update_executes_order_when_phase_1_emits_buy` (`tests/test_live_engine.py`)
- ✅ `test_check_stale_data_triggers_flatten` (`tests/test_live_engine.py`)
- ✅ `test_phase_1_integration_happy_path` (`tests/test_live_engine.py`)
- ✅ `test_phase_1_integration_rejects_shape_mismatch` (`tests/test_live_engine.py`)
- ✅ `test_on_bar_update_cancels_buy_when_nq_dumps` (`tests/test_live_engine.py`)
- ✅ `test_on_bar_update_records_shawn_speed_under_threshold` (`tests/test_live_engine.py`)
- ✅ `test_on_bar_update_skips_missing_data_rows` (`tests/test_live_engine.py`)
- ✅ `test_compare_signal_parity_matches_batch_vs_live` (`tests/test_live_engine.py`)
- ✅ `test_compare_signal_parity_rejects_ghost_signal_mismatch` (`tests/test_live_engine.py`)
- ✅ `test_build_live_window_from_rows_drops_nan_rows` (`tests/test_live_engine.py`)

### Phase 3 — Shawn Intelligence Layer
**Objective**
- Enforce relative-strength and VWAP-compression entry discipline.

**DoD thresholds**
- `stock_rel_strength > market_momentum`
- `dist_to_vwap < 0.002`

**Required tests to pass (TDD gate)**
- ✅ `test_phase_3_shawn_logic_filter` (`tests/test_validators.py`)
- ✅ `test_phase_3_rejects_weak_relative_strength` (`tests/test_validators.py`)
- ✅ `test_phase_3_rejects_non_compressed_entry` (`tests/test_validators.py`)

### Phase 4 — Safety and Over-Engineering
**Objective**
- Enforce hard safety rails before any live usage.

**DoD thresholds**
- Circuit breaker at daily PnL > -2%
- Stale-data guard when feed age <= 5 seconds
- Double-entry prevention for duplicate open signal
- Wash-sale cooldown of 30 minutes

**Required tests to pass (TDD gate)**
- ✅ `test_phase_4_safety_checks` (`tests/test_validators.py`)
- ✅ `test_phase_4_rejects_daily_loss_limit_breach` (`tests/test_validators.py`)
- ✅ `test_phase_4_rejects_stale_data` (`tests/test_validators.py`)
- ✅ `test_phase_4_rejects_double_entry` (`tests/test_validators.py`)
- ✅ `test_phase_4_rejects_wash_sale_cooldown` (`tests/test_validators.py`)

## Cross-Phase Integration and E2E Coverage
- ✅ `test_integration_all_phase_gates_pass` (`tests/test_integration_phase_gates.py`)
- ✅ `test_integration_fails_fast_when_any_phase_gate_fails` (`tests/test_integration_phase_gates.py`)
- ✅ `test_e2e_nominal_phased_plan_passes` (`tests/test_e2e_phased_plan.py`)
- ✅ `test_e2e_pipeline_stops_on_phase_4_safety_failure` (`tests/test_e2e_phased_plan.py`)

## Test Command
Run all unit + integration + e2e DoD tests:

```bash
cd ci
./run_tests.sh
```
