# Catena-Bot PRD (Phased Delivery + DoD Test Matrix)

Version: **1.0.0-MVP**

This PRD aligns with `README.md` and `catena_bot/ssot_config.py` as the implementation SSOT.

## Product Goal
Build a momentum-focused trading bot that can be validated in deterministic phases before any live-capital risk.

## Test Navigation Index (Phase -> Test File)
- Unit DoD gates: [`tests/test_validators.py`](tests/test_validators.py)
- Phase-1 data acquisition unit tests: [`tests/test_data_downloader.py`](tests/test_data_downloader.py)
- Phase-2 live engine unit tests: [`tests/test_live_engine.py`](tests/test_live_engine.py)
- Integration phased gates: [`tests/test_integration_phase_gates.py`](tests/test_integration_phase_gates.py)
- E2E phased plan flow: [`tests/test_e2e_phased_plan.py`](tests/test_e2e_phased_plan.py)
- Architect mocked package: [`tests/test_mock_care_package.py`](tests/test_mock_care_package.py)
- CI phase status + handoff prompt tests: [`tests/test_phase_status.py`](tests/test_phase_status.py)
- Phase-6 handoff coverage tests: [`tests/test_phase6_handoff_coverage.py`](tests/test_phase6_handoff_coverage.py)
- Phase-7 maintenance hardening tests: [`tests/test_phase7_maintenance.py`](tests/test_phase7_maintenance.py)

All completed tests listed below are required to remain passing and are executed by `ci/run_tests.sh`. The same gate also reports the current SSOT phase, rewrites `NEXT_AGENT_PROMPT.md` each run, and enforces fresh prompt metadata (`Generated at`, `Git SHA`, `Workflow ID`) to prevent stale handoff files.

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
- ✅ `test_env_raises_when_missing` (`tests/test_data_downloader.py`)
- ✅ `test_fetch_stock_normalizes_columns_and_sorts` (`tests/test_data_downloader.py`)
- ✅ `test_save_writes_symbol_files_and_slippage_columns` (`tests/test_data_downloader.py`)

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


### Phase 5 — Architect Mocked Care Package
**Objective**
- Provide an offline deterministic simulation package so Shawn logic, broker actions, and safety rails can be validated without live keys or feeds.

**DoD thresholds**
- Zero external dependencies for mocked tests
- 100% branch coverage in `is_shawn_setup` decision function
- Human-readable logs for refusal/acceptance and safety-trigger outcomes
- Futures-lead bearish market blocks trade
- Shawn squeeze rejects entries with `dist_to_vwap >= 0.002`
- Circuit breaker halts after 3 consecutive losses at or below -0.5% each
- Stale data panic emergency-closes positions at 15 seconds without bars

**Required tests to pass (TDD gate)**
- ✅ `test_generate_mock_shawn_setup_breakout_has_late_volume_spike` (`tests/test_mock_care_package.py`)
- ✅ `test_a_futures_lead_logic_blocks_trade` (`tests/test_mock_care_package.py`)
- ✅ `test_b_shawn_squeeze_accuracy_blocks_chasing_trade` (`tests/test_mock_care_package.py`)
- ✅ `test_c_circuit_breaker_triggers_shutdown_after_three_losses` (`tests/test_mock_care_package.py`)
- ✅ `test_d_stale_data_panic_emergency_closes` (`tests/test_mock_care_package.py`)
- ✅ `test_branch_coverage_for_is_shawn_setup` (`tests/test_mock_care_package.py`)

### Phase 6 — Test Coverage Improvement (Integration + UX Edge Cases + E2E)
**Objective**
- Improve quality and confidence of next-agent workflow behavior through targeted coverage expansion.

**DoD thresholds**
- Integration test validates generated prompt includes fresh metadata and process steps.
- UX edge-case test validates prompt instructions always include:
  - read the handoff prompt first,
  - complete one scoped task,
  - set up next-day handoff.
- E2E test validates `report_ci_phase_status` writes a prompt file that passes freshness checks.

**Required tests to pass (TDD gate)**
- ✅ `test_phase_6_prompt_contains_required_process_steps` (`tests/test_phase6_handoff_coverage.py`)
- ✅ `test_phase_6_integration_prompt_write_and_freshness` (`tests/test_phase6_handoff_coverage.py`)
- ✅ `test_phase_6_e2e_report_ci_phase_status_writes_fresh_prompt` (`tests/test_phase6_handoff_coverage.py`)

### Phase 7 — Maintenance (Prompt Metadata Hardening)
**Objective**
- Strengthen handoff prompt metadata handling so CI prompt freshness checks fail fast on malformed or suspicious metadata.

**DoD thresholds**
- Blank `GITHUB_RUN_ID` values are sanitized and fallback to deterministic local workflow IDs.
- Invalid `Generated at (UTC)` metadata fails validation with explicit assertion messaging.
- Future-dated prompt timestamps beyond SSOT skew tolerance are rejected.

**Required tests to pass (TDD gate)**
- ✅ `test_current_workflow_id_falls_back_when_env_blank` (`tests/test_phase7_maintenance.py`)
- ✅ `test_validate_prompt_freshness_rejects_invalid_timestamp_format` (`tests/test_phase7_maintenance.py`)
- ✅ `test_validate_prompt_freshness_rejects_future_timestamp` (`tests/test_phase7_maintenance.py`)

## Cross-Phase Integration and E2E Coverage
- ✅ `test_integration_all_phase_gates_pass` (`tests/test_integration_phase_gates.py`)
- ✅ `test_integration_fails_fast_when_any_phase_gate_fails` (`tests/test_integration_phase_gates.py`)
- ✅ `test_e2e_nominal_phased_plan_passes` (`tests/test_e2e_phased_plan.py`)
- ✅ `test_e2e_pipeline_stops_on_phase_4_safety_failure` (`tests/test_e2e_phased_plan.py`)
- ✅ `test_evaluate_phase_completion_marks_only_contiguous_gates_complete` (`tests/test_phase_status.py`)
- ✅ `test_write_next_agent_prompt_persists_expected_text` (`tests/test_phase_status.py`)
- ✅ `test_validate_prompt_freshness_accepts_recent_matching_metadata` (`tests/test_phase_status.py`)
- ✅ `test_validate_prompt_freshness_rejects_stale_prompt` (`tests/test_phase_status.py`)
- ✅ `test_validate_prompt_freshness_rejects_git_sha_mismatch` (`tests/test_phase_status.py`)
- ✅ `test_phase_6_prompt_contains_required_process_steps` (`tests/test_phase6_handoff_coverage.py`)
- ✅ `test_phase_6_integration_prompt_write_and_freshness` (`tests/test_phase6_handoff_coverage.py`)
- ✅ `test_phase_6_e2e_report_ci_phase_status_writes_fresh_prompt` (`tests/test_phase6_handoff_coverage.py`)
- ✅ `test_current_workflow_id_falls_back_when_env_blank` (`tests/test_phase7_maintenance.py`)
- ✅ `test_validate_prompt_freshness_rejects_invalid_timestamp_format` (`tests/test_phase7_maintenance.py`)
- ✅ `test_validate_prompt_freshness_rejects_future_timestamp` (`tests/test_phase7_maintenance.py`)

## Test Command
Run all unit + integration + e2e DoD tests:

```bash
cd ci
./run_tests.sh
```

## CI/CD Gate
- CI workflow: `.github/workflows/ci.yml`
  - Runs dependency installation.
  - Enforces Python LOC `< 400`.
  - Executes `./ci/run_tests.sh` as the merge gate.
- CD workflow: `.github/workflows/cd.yml`
  - Executes the same phased gate prior to artifact delivery.
