#!/bin/bash
set -euo pipefail

# Preflight check before starting a phase
# Usage: ./tools/preflight_check.sh <phase_number>

PHASE_NUM="${1:?Phase number required (0-6)}"
PREV_PHASE=$((PHASE_NUM - 1))

echo "=== Preflight Check: Phase $PHASE_NUM ==="
echo

# 1. Verify previous phase unlock (skip for Phase 0)
if [ "$PHASE_NUM" -gt 0 ]; then
    echo "1. Checking Phase $PREV_PHASE unlock artifact..."
    if python3 tools/validate_phase_artifact.py ".phase-$PREV_PHASE.complete.json"; then
        echo "   ✓ Phase $PREV_PHASE unlock verified"
    else
        echo "   ✗ Phase $PREV_PHASE not complete - run Phase $PREV_PHASE first"
        exit 1
    fi
    echo
fi

# 2. Check for hybrid code (G1)
echo "2. Checking for hybrid code (G1)..."
if python3 tools/ci/ci_gate_no_hybrids.py > /dev/null 2>&1; then
    echo "   ✓ No hybrid code detected"
else
    echo "   ✗ Hybrid code detected - clean up before proceeding"
    exit 1
fi
echo

# 3. Fast baseline test
echo "3. Running fast baseline test..."
if ./tools/run_tests_fast.sh 01_edge_cases > /dev/null 2>&1; then
    echo "   ✓ Fast tests pass"
else
    echo "   ✗ Fast tests failing - fix baseline before proceeding"
    exit 1
fi
echo

# 4. Check corpus count
echo "4. Verifying test corpus..."
CORPUS_COUNT=$(python3 -c "from pathlib import Path; print(len(list(Path('tools/test_mds').rglob('*.md'))))")
echo "   ✓ Found $CORPUS_COUNT test files"
echo

echo "=== Preflight Complete: Ready for Phase $PHASE_NUM ==="
exit 0
