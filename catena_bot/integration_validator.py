"""Phase 1 integration validation helpers for live-stream compatibility."""

from __future__ import annotations

import pandas as pd


def validate_phase_1_integration(live_data_sample: pd.DataFrame, phase_1_signal: pd.Series) -> bool:
    """Validate Phase 1 signal shape and a basic VWAP-consistency invariant."""

    assert len(phase_1_signal) == len(live_data_sample), "Data shape mismatch!"

    if not phase_1_signal.empty and phase_1_signal.iloc[-1] == "BUY":
        assert live_data_sample["close"].iloc[-1] > live_data_sample["vwap"].iloc[-1], (
            "CRITICAL: Phase 1 triggered a Buy BELOW VWAP (Logic Failure)."
        )

    return True
