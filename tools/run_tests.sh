#!/bin/bash
set -euo pipefail

# Bridge script matching spec commands to actual tools
PROFILE="${PROFILE:-moderate}"
python3 tools/baseline_test_runner.py --profile "$PROFILE" "$@"
