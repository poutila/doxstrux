#!/usr/bin/env python3
"""
Check if canary meets promotion gates.

CRITICAL INVARIANT: Baseline mismatch rate must be 0.00% (zero tolerance).

This tool validates canary metrics against BINDING gates before promotion.
Any gate failure triggers automatic rollback.

Usage:
    python tools/check_canary_promotion.py

Reads:
    - metrics/canary_current.json: Current canary metrics
    - metrics/baseline.json: Baseline metrics for comparison

Gates (BINDING - automatic rollback on failure):
    1. Mismatch rate = 0.00% (any non-zero → rollback)
    2. Error rate ≤ 0.1%
    3. p50 latency ≤ baseline + 3%
    4. p95 latency ≤ baseline + 8%
    5. Sample size ≥ 1000 parses

Exit Codes:
    0: All gates passed - PROMOTE
    1: One or more gates failed - ROLLBACK
"""

from __future__ import annotations
import json
import sys
from pathlib import Path


def check_promotion_gates(current_metrics: dict, baseline_metrics: dict) -> tuple[bool, list[str]]:
    """
    Validate canary against BINDING gates.

    Args:
        current_metrics: Metrics from canary deployment
        baseline_metrics: Baseline metrics for comparison

    Returns:
        (should_promote, errors):
            should_promote: True if all gates passed
            errors: List of error messages for failed gates

    Example:
        >>> current = {"baseline_mismatch_rate_pct": 0.0, "error_rate_pct": 0.0, ...}
        >>> baseline = {"latency_p50_ms": 10.0, "latency_p95_ms": 25.0}
        >>> should_promote, errors = check_promotion_gates(current, baseline)
        >>> should_promote
        True
    """
    errors = []

    # GATE 1: Zero baseline mismatches (BINDING - 0.00% tolerance)
    mismatch_rate = current_metrics.get("baseline_mismatch_rate_pct", 100.0)
    if mismatch_rate > 0.0:
        errors.append(
            f"❌ GATE 1 FAILED: Baseline mismatch rate {mismatch_rate:.2f}% "
            f"(required: 0.00%)"
        )

    # GATE 2: Error rate threshold
    error_rate = current_metrics.get("error_rate_pct", 100.0)
    if error_rate > 0.1:
        errors.append(
            f"❌ GATE 2 FAILED: Error rate {error_rate:.2f}% (threshold: 0.1%)"
        )

    # GATE 3: Performance p50 aggregate
    current_p50 = current_metrics.get("latency_p50_ms", 0)
    baseline_p50 = baseline_metrics.get("latency_p50_ms", 1)

    if baseline_p50 > 0:
        delta_p50 = ((current_p50 - baseline_p50) / baseline_p50) * 100
        if delta_p50 > 3.0:
            errors.append(
                f"❌ GATE 3 FAILED: p50 regression {delta_p50:.1f}% (threshold: 3%)"
            )

    # GATE 4: Performance p95 aggregate
    current_p95 = current_metrics.get("latency_p95_ms", 0)
    baseline_p95 = baseline_metrics.get("latency_p95_ms", 1)

    if baseline_p95 > 0:
        delta_p95 = ((current_p95 - baseline_p95) / baseline_p95) * 100
        if delta_p95 > 8.0:
            errors.append(
                f"❌ GATE 4 FAILED: p95 regression {delta_p95:.1f}% (threshold: 8%)"
            )

    # GATE 5: Sample size
    parse_count = current_metrics.get("parse_count", 0)
    if parse_count < 1000:
        errors.append(
            f"❌ GATE 5 FAILED: Insufficient sample size {parse_count} (minimum: 1000)"
        )

    should_promote = len(errors) == 0
    return should_promote, errors


def main() -> int:
    """
    Main entry point for canary promotion check.

    Returns:
        0 if all gates passed, 1 if any gate failed
    """
    import argparse

    parser = argparse.ArgumentParser(description="Check canary promotion gates")
    parser.add_argument(
        "--current",
        default="metrics/canary_current.json",
        help="Path to current canary metrics JSON (default: metrics/canary_current.json)"
    )
    parser.add_argument(
        "--baseline",
        default="metrics/baseline.json",
        help="Path to baseline metrics JSON (default: metrics/baseline.json)"
    )
    args = parser.parse_args()

    current_path = Path(args.current)
    baseline_path = Path(args.baseline)

    # Check if metrics files exist
    if not current_path.exists():
        print(f"❌ Missing current metrics: {current_path}", file=sys.stderr)
        return 1

    if not baseline_path.exists():
        print(f"❌ Missing baseline metrics: {baseline_path}", file=sys.stderr)
        return 1

    # Load metrics
    try:
        current = json.loads(current_path.read_text())
    except Exception as e:
        print(f"❌ Failed to load current metrics: {e}", file=sys.stderr)
        return 1

    try:
        baseline = json.loads(baseline_path.read_text())
    except Exception as e:
        print(f"❌ Failed to load baseline metrics: {e}", file=sys.stderr)
        return 1

    # Check gates
    should_promote, errors = check_promotion_gates(current, baseline)

    if should_promote:
        print("✅ All promotion gates passed - PROMOTE")
        return 0
    else:
        print("❌ Promotion gates failed - ROLLBACK")
        for error in errors:
            print(error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
