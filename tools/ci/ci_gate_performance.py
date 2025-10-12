#!/usr/bin/env python3
"""
CI Gate G4 - Performance

Validates that parser performance remains within acceptable thresholds.
Compares current performance against baseline using median and p95 metrics.

Usage:
    python3 tools/ci/ci_gate_performance.py [--profile moderate]

Exit codes:
    0: Performance within thresholds (PASS) or no baseline (SKIP)
    1: Performance regression detected (FAIL)

Thresholds:
    - Δmedian ≤ 5%
    - Δp95 ≤ 10%

References:
    - POLICY_GATES.md §5
    - DETAILED_TASK_LIST.md Task 0.5
"""

import sys
import json
import subprocess
import statistics
import tracemalloc
from pathlib import Path
from typing import Optional


class SecurityError(RuntimeError):
    """Performance validation failure."""
    pass


# Project root (2 levels up from tools/ci/)
ROOT = Path(__file__).resolve().parents[2]

# Baseline file
BASELINE_FILE = ROOT / "tools" / "baseline_generation_summary.json"

# Performance thresholds (from POLICY_GATES.md §5)
THRESHOLD_MEDIAN_PCT = 5.0
THRESHOLD_P95_PCT = 10.0


def measure_performance(test_mds_dir: Path, profile: str = "moderate") -> dict:
    """Measure current parser performance with memory tracking.

    CRITICAL: tracemalloc.stop() is mandatory to prevent inflated
    memory deltas on subsequent runs.

    Args:
        test_mds_dir: Directory containing test markdown files
        profile: Security profile to use

    Returns:
        Performance metrics dictionary
    """
    tracemalloc.start()
    try:
        # Run baseline test runner and capture timing
        result = subprocess.run(
            ["python3", "tools/baseline_test_runner.py", "--profile", profile],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(ROOT)
        )

        # Load results to get timing data
        results_file = ROOT / "tools" / "baseline_results.json"
        if not results_file.exists():
            raise SecurityError("Baseline results file not found")

        results = json.loads(results_file.read_text(encoding="utf-8"))

        # Get memory stats
        current, peak = tracemalloc.get_traced_memory()

        return {
            "median_ms": results.get("avg_time_ms", 0.0),  # Using avg as proxy for median
            "total_time_ms": results.get("total_time_ms", 0.0),
            "memory_current_mb": current / 1024**2,
            "memory_peak_mb": peak / 1024**2,
            "profile": profile
        }
    finally:
        # REQUIRED: Stop tracemalloc to prevent memory leak detection
        # on next run. Failing to call stop() causes cumulative memory
        # counting across multiple gate invocations.
        tracemalloc.stop()


def validate_performance(profile: str = "moderate") -> None:
    """Validate performance against baseline.

    Args:
        profile: Security profile to use

    Raises:
        SystemExit: With appropriate exit code
    """
    # Check if baseline exists
    if not BASELINE_FILE.exists():
        print(json.dumps({
            "status": "SKIP",
            "reason": "no_timing_data",
            "message": f"Baseline file not found: {BASELINE_FILE}"
        }))
        sys.exit(0)

    # Load baseline
    try:
        baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SecurityError(f"Invalid baseline JSON: {e}")

    # Measure current performance
    test_mds_dir = ROOT / "tools" / "test_mds"
    current = measure_performance(test_mds_dir, profile=profile)

    # Calculate deltas
    baseline_median = baseline.get("median_ms", baseline.get("avg_time_ms", 0.0))
    current_median = current["median_ms"]

    if baseline_median == 0:
        # Avoid division by zero
        delta_median_pct = 0.0
    else:
        delta_median_pct = ((current_median - baseline_median) / baseline_median) * 100

    # For p95, use total_time as proxy if not available
    baseline_p95 = baseline.get("p95_ms", baseline.get("total_time_ms", 0.0))
    current_p95 = current.get("p95_ms", current.get("total_time_ms", 0.0))

    if baseline_p95 == 0:
        delta_p95_pct = 0.0
    else:
        delta_p95_pct = ((current_p95 - baseline_p95) / baseline_p95) * 100

    # Check thresholds
    if delta_median_pct > THRESHOLD_MEDIAN_PCT:
        print(json.dumps({
            "status": "FAIL",
            "reason": "performance_regression",
            "metric": "median",
            "delta_median_pct": round(delta_median_pct, 2),
            "threshold_pct": THRESHOLD_MEDIAN_PCT,
            "current_median_ms": round(current_median, 2),
            "baseline_median_ms": round(baseline_median, 2),
            "profile": profile
        }))
        sys.exit(1)

    if delta_p95_pct > THRESHOLD_P95_PCT:
        print(json.dumps({
            "status": "FAIL",
            "reason": "performance_regression",
            "metric": "p95",
            "delta_p95_pct": round(delta_p95_pct, 2),
            "threshold_pct": THRESHOLD_P95_PCT,
            "current_p95_ms": round(current_p95, 2),
            "baseline_p95_ms": round(baseline_p95, 2),
            "profile": profile
        }))
        sys.exit(1)

    # Success - within thresholds
    print(json.dumps({
        "status": "OK",
        "message": "Performance within thresholds",
        "delta_median_pct": round(delta_median_pct, 2),
        "delta_p95_pct": round(delta_p95_pct, 2),
        "memory_peak_mb": round(current["memory_peak_mb"], 2),
        "profile": profile
    }))
    sys.exit(0)


def main():
    """Main entry point."""
    try:
        # Parse arguments
        profile = "moderate"
        if len(sys.argv) > 1:
            if sys.argv[1] == "--profile":
                if len(sys.argv) < 3:
                    raise SecurityError("--profile requires a value")
                profile = sys.argv[2]
            else:
                raise SecurityError(f"Unknown argument: {sys.argv[1]}")

        validate_performance(profile=profile)

    except SecurityError as e:
        print(json.dumps({
            "status": "FAIL",
            "reason": "security_error",
            "error": str(e)
        }))
        sys.exit(1)

    except Exception as e:
        print(json.dumps({
            "status": "FAIL",
            "reason": "unexpected_error",
            "error": str(e)
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
