#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"

echo "[unit] Running validator unit tests"
python -m unittest tests.test_validators -v

echo "[integration] Running phased gate integration tests"
python -m unittest tests.test_integration_phase_gates -v

echo "[e2e] Running phased plan e2e tests"
python -m unittest tests.test_e2e_phased_plan -v
