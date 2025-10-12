#!/bin/bash
set -euo pipefail  # Exit on error, undefined var, pipe failure

# Fast subset testing for quick iteration
SUBSET="${1:-01_edge_cases}"
TEST_DIR="tools/test_mds/$SUBSET"

# Validate test directory exists
if [[ ! -d "$TEST_DIR" ]]; then
    echo "Error: Test directory '$TEST_DIR' not found" >&2
    exit 1
fi

# Use venv Python if available, otherwise system Python
if [[ -f .venv/bin/python3 ]]; then
    PYTHON=".venv/bin/python3"
else
    PYTHON="python3"
fi

$PYTHON tools/test_feature_counts.py \
  --test-dir "$TEST_DIR" \
  --profile "${PROFILE:-moderate}"
