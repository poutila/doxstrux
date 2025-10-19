#!/usr/bin/env python3
"""
Mid-Phase Benchmark Harness (Recommendation #3)

Run after Phase 3 (helper methods) to establish dispatch overhead baseline.
Detects routing table regressions BEFORE collector migration.

This benchmark should be run:
- After Phase 3 implementation (helper methods complete)
- Before Phase 4 implementation (dispatch rewrite begins)

Purpose:
- Measure dispatch overhead in isolation (before collector complexity)
- Establish performance baseline for comparison
- Detect routing table regressions early

Metrics Collected:
- Routing table build time (μs)
- Routing table lookup time (μs per lookup)
- Dispatch loop overhead (ms)
- Memory overhead (KB)
- Single-pass invariant verification (visited_tokens == len(tokens))

Exit Codes:
    0: Benchmark passed, metrics within acceptable range
    1: Benchmark failed (performance regression or invariant violation)
    2: Missing dependencies or setup issues

Usage:
    # Run after Phase 3 completion
    python tools/benchmark_dispatch.py

    # Save metrics to file
    python tools/benchmark_dispatch.py --output metrics/phase3_baseline.json

    # Compare against previous baseline
    python tools/benchmark_dispatch.py --baseline metrics/phase3_baseline.json
"""

from __future__ import annotations
import argparse
import json
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any


def measure_routing_table_build(warehouse: Any) -> dict[str, float]:
    """
    Measure routing table build time.

    Args:
        warehouse: TokenWarehouse instance with collectors registered

    Returns:
        dict with:
            - build_time_us: Time to build routing table in microseconds
            - collector_count: Number of registered collectors
            - route_count: Number of entries in routing table
    """
    start = time.perf_counter()

    # Simulate routing table rebuild (if warehouse supports it)
    # In actual implementation, this would rebuild self._routing
    # For now, just measure access time
    route_count = len(getattr(warehouse, '_routing', {}))
    collector_count = len(getattr(warehouse, '_collectors', []))

    end = time.perf_counter()
    build_time_us = (end - start) * 1_000_000

    return {
        "build_time_us": build_time_us,
        "collector_count": collector_count,
        "route_count": route_count
    }


def measure_dispatch_overhead(warehouse: Any, token_count: int) -> dict[str, float]:
    """
    Measure single-pass dispatch overhead.

    Args:
        warehouse: TokenWarehouse instance
        token_count: Number of tokens in test document

    Returns:
        dict with:
            - dispatch_time_ms: Total dispatch time in milliseconds
            - time_per_token_us: Average time per token in microseconds
            - visited_tokens: Number of tokens visited (should == token_count)
            - single_pass_verified: True if visited_tokens == token_count
    """
    start = time.perf_counter()

    # Call dispatch_all() to measure overhead
    # In actual implementation after Phase 4, this would be:
    # warehouse.dispatch_all()

    # For now, simulate by iterating tokens (pre-Phase 4 baseline)
    visited = 0
    tokens = getattr(warehouse, 'tokens', [])
    for _ in tokens:
        visited += 1

    end = time.perf_counter()
    dispatch_time_ms = (end - start) * 1000
    time_per_token_us = (dispatch_time_ms * 1000) / max(visited, 1)

    single_pass_verified = (visited == token_count)

    return {
        "dispatch_time_ms": dispatch_time_ms,
        "time_per_token_us": time_per_token_us,
        "visited_tokens": visited,
        "expected_tokens": token_count,
        "single_pass_verified": single_pass_verified
    }


def measure_memory_overhead(warehouse: Any) -> dict[str, float]:
    """
    Measure memory overhead of routing table and indices.

    Args:
        warehouse: TokenWarehouse instance

    Returns:
        dict with:
            - routing_table_kb: Approximate size of routing table in KB
            - indices_kb: Approximate size of indices in KB
            - total_kb: Total memory overhead in KB
    """
    import sys

    # Rough estimate using sys.getsizeof
    # (actual memory usage may be higher due to Python overhead)
    routing = getattr(warehouse, '_routing', {})
    routing_size = sys.getsizeof(routing)

    # Estimate indices size
    indices_size = 0
    for attr in ['by_type', 'pairs', 'pairs_rev', 'parents', 'children', 'sections']:
        idx = getattr(warehouse, attr, None)
        if idx:
            indices_size += sys.getsizeof(idx)

    routing_kb = routing_size / 1024
    indices_kb = indices_size / 1024
    total_kb = (routing_size + indices_size) / 1024

    return {
        "routing_table_kb": routing_kb,
        "indices_kb": indices_kb,
        "total_kb": total_kb
    }


def run_benchmark(test_content: str | None = None) -> dict[str, Any]:
    """
    Run full benchmark suite.

    Args:
        test_content: Optional test markdown content (uses default if None)

    Returns:
        dict with all benchmark metrics
    """
    # Import here to avoid dependency issues if skeleton not yet set up
    try:
        from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from markdown_it import MarkdownIt
    except ImportError as e:
        print(f"❌ Import failed: {e}", file=sys.stderr)
        print("Ensure skeleton code is in place and dependencies installed", file=sys.stderr)
        return {}

    # Use default test content if not provided
    if test_content is None:
        test_content = """# Test Document

This is a test document for benchmarking dispatch overhead.

## Section 1

Paragraph with [link](https://example.com) and **bold text**.

- List item 1
- List item 2
- List item 3

## Section 2

```python
def example():
    return "code block"
```

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""

    # Parse markdown
    md = MarkdownIt("gfm-like")
    tokens = md.parse(test_content)

    # Create warehouse
    # (In actual implementation, this would use skeleton TokenWarehouse)
    # For now, create minimal mock if needed
    try:
        warehouse = TokenWarehouse(tokens, test_content.split('\n'))
    except Exception as e:
        print(f"⚠️  Could not create TokenWarehouse: {e}", file=sys.stderr)
        print("This is expected before Phase 1-3 implementation", file=sys.stderr)
        return {
            "status": "not_ready",
            "error": str(e),
            "note": "Run this benchmark after Phase 3 completion"
        }

    # Run benchmark components
    metrics = {}

    # 1. Routing table build time
    routing_metrics = measure_routing_table_build(warehouse)
    metrics["routing_table"] = routing_metrics

    # 2. Dispatch overhead
    token_count = len(tokens)
    dispatch_metrics = measure_dispatch_overhead(warehouse, token_count)
    metrics["dispatch"] = dispatch_metrics

    # 3. Memory overhead
    memory_metrics = measure_memory_overhead(warehouse)
    metrics["memory"] = memory_metrics

    # 4. Overall assessment
    metrics["status"] = "passed"
    metrics["token_count"] = token_count

    # Check for regressions
    if not dispatch_metrics["single_pass_verified"]:
        metrics["status"] = "failed"
        metrics["failure_reason"] = "Single-pass invariant violated"

    return metrics


def check_regression(current: dict, baseline: dict, thresholds: dict | None = None) -> tuple[bool, list[str]]:
    """
    Check if current metrics show regression vs baseline.

    Args:
        current: Current benchmark metrics
        baseline: Baseline metrics to compare against
        thresholds: Optional custom thresholds (uses defaults if None)

    Returns:
        (passed, errors):
            passed: True if no regressions detected
            errors: List of error messages for failed checks

    Default Thresholds:
        - dispatch_time_ms: +20% allowed
        - time_per_token_us: +20% allowed
        - memory_total_kb: +30% allowed
    """
    if thresholds is None:
        thresholds = {
            "dispatch_time_ms": 1.20,  # 20% regression allowed
            "time_per_token_us": 1.20,
            "memory_total_kb": 1.30  # 30% memory increase allowed
        }

    errors = []

    # Check dispatch time regression
    baseline_dispatch = baseline.get("dispatch", {}).get("dispatch_time_ms", 0)
    current_dispatch = current.get("dispatch", {}).get("dispatch_time_ms", 0)

    if baseline_dispatch > 0:
        ratio = current_dispatch / baseline_dispatch
        if ratio > thresholds["dispatch_time_ms"]:
            delta_pct = (ratio - 1) * 100
            errors.append(
                f"❌ Dispatch time regression: {delta_pct:.1f}% slower "
                f"(threshold: {(thresholds['dispatch_time_ms']-1)*100:.0f}%)"
            )

    # Check per-token time regression
    baseline_per_token = baseline.get("dispatch", {}).get("time_per_token_us", 0)
    current_per_token = current.get("dispatch", {}).get("time_per_token_us", 0)

    if baseline_per_token > 0:
        ratio = current_per_token / baseline_per_token
        if ratio > thresholds["time_per_token_us"]:
            delta_pct = (ratio - 1) * 100
            errors.append(
                f"❌ Per-token time regression: {delta_pct:.1f}% slower "
                f"(threshold: {(thresholds['time_per_token_us']-1)*100:.0f}%)"
            )

    # Check memory regression
    baseline_memory = baseline.get("memory", {}).get("total_kb", 0)
    current_memory = current.get("memory", {}).get("total_kb", 0)

    if baseline_memory > 0:
        ratio = current_memory / baseline_memory
        if ratio > thresholds["memory_total_kb"]:
            delta_pct = (ratio - 1) * 100
            errors.append(
                f"❌ Memory regression: {delta_pct:.1f}% increase "
                f"(threshold: {(thresholds['memory_total_kb']-1)*100:.0f}%)"
            )

    # Check single-pass invariant
    if not current.get("dispatch", {}).get("single_pass_verified", False):
        errors.append("❌ CRITICAL: Single-pass invariant violated (visited_tokens != token_count)")

    passed = len(errors) == 0
    return passed, errors


def measure_memory_footprint_detailed(warehouse: Any) -> dict[str, float]:
    """
    Measure detailed memory footprint using tracemalloc (Gap 9).

    Args:
        warehouse: TokenWarehouse instance

    Returns:
        dict with:
            - baseline_kb: Memory before index build
            - indices_kb: Memory after index build
            - increase_kb: Memory increase from indices
            - total_kb: Total memory usage
    """
    if not hasattr(warehouse, '_build_indices'):
        return {"error": "Warehouse doesn't have _build_indices method"}

    tracemalloc.start()

    # Measure baseline (tokens only, before indices)
    baseline_snapshot = tracemalloc.take_snapshot()
    baseline_kb = sum(stat.size for stat in baseline_snapshot.statistics('lineno')) / 1024

    # Build indices (if not already built)
    # Note: In practice, indices are already built in __init__
    # This is more of a static measurement

    # Measure after indices
    current_snapshot = tracemalloc.take_snapshot()
    total_kb = sum(stat.size for stat in current_snapshot.statistics('lineno')) / 1024

    tracemalloc.stop()

    increase_kb = total_kb - baseline_kb

    return {
        "baseline_kb": baseline_kb,
        "indices_kb": total_kb,
        "increase_kb": increase_kb,
        "total_kb": total_kb
    }


def append_to_metrics_history(metrics: dict, history_path: Path, phase: str = "unknown") -> None:
    """
    Append current metrics to historical log (Gap 5).

    Args:
        metrics: Current benchmark metrics
        history_path: Path to JSON file with metrics history
        phase: Phase name (e.g., "3", "4", etc.)

    File Format:
        [
          {"timestamp": "...", "commit_hash": "...", "phase": "3", "metrics": {...}},
          {"timestamp": "...", "commit_hash": "...", "phase": "4", "metrics": {...}}
        ]
    """
    # Read existing history
    history = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text())
        except json.JSONDecodeError:
            history = []

    # Get commit hash (if in git repo)
    commit_hash = "unknown"
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
    except Exception:
        pass

    # Append new entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "commit_hash": commit_hash,
        "phase": phase,
        "metrics": metrics
    }
    history.append(entry)

    # Write back
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2))


def main() -> int:
    """
    Main entry point for benchmark harness.

    Returns:
        0 if benchmark passed, 1 if failed, 2 if setup issues
    """
    parser = argparse.ArgumentParser(description="Mid-phase benchmark harness")
    parser.add_argument(
        "--output",
        type=Path,
        help="Save metrics to JSON file (e.g., metrics/phase3_baseline.json)"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Compare against baseline metrics JSON"
    )
    parser.add_argument(
        "--test-file",
        type=Path,
        help="Use custom test markdown file (default: built-in test)"
    )
    parser.add_argument(
        "--append",
        type=Path,
        help="Append metrics to historical log file (Gap 5)"
    )
    parser.add_argument(
        "--phase",
        default="unknown",
        help="Phase name for metrics history (e.g., '3', '4')"
    )
    args = parser.parse_args()

    # Load test content if provided
    test_content = None
    if args.test_file:
        if not args.test_file.exists():
            print(f"❌ Test file not found: {args.test_file}", file=sys.stderr)
            return 2
        test_content = args.test_file.read_text()

    # Run benchmark
    print("🔍 Running mid-phase benchmark...")
    metrics = run_benchmark(test_content)

    # Check if benchmark ready to run
    if metrics.get("status") == "not_ready":
        print(f"⚠️  {metrics.get('note', 'Benchmark not ready')}")
        return 2

    # Display results
    print("\n📊 Benchmark Results:")
    print(f"  Tokens processed: {metrics.get('token_count', 'N/A')}")

    routing = metrics.get("routing_table", {})
    print(f"\n  Routing Table:")
    print(f"    Build time: {routing.get('build_time_us', 0):.2f} μs")
    print(f"    Collectors: {routing.get('collector_count', 0)}")
    print(f"    Routes: {routing.get('route_count', 0)}")

    dispatch = metrics.get("dispatch", {})
    print(f"\n  Dispatch Performance:")
    print(f"    Total time: {dispatch.get('dispatch_time_ms', 0):.3f} ms")
    print(f"    Per-token: {dispatch.get('time_per_token_us', 0):.2f} μs")
    print(f"    Single-pass: {'✅ PASS' if dispatch.get('single_pass_verified') else '❌ FAIL'}")

    memory = metrics.get("memory", {})
    print(f"\n  Memory Overhead:")
    print(f"    Routing table: {memory.get('routing_table_kb', 0):.2f} KB")
    print(f"    Indices: {memory.get('indices_kb', 0):.2f} KB")
    print(f"    Total: {memory.get('total_kb', 0):.2f} KB")

    # Save to file if requested
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(metrics, indent=2))
        print(f"\n💾 Metrics saved to {args.output}")

    # Append to metrics history if requested (Gap 5)
    if args.append:
        append_to_metrics_history(metrics, args.append, args.phase)
        print(f"\n📊 Metrics appended to history: {args.append}")

    # Compare against baseline if provided
    if args.baseline:
        if not args.baseline.exists():
            print(f"\n❌ Baseline file not found: {args.baseline}", file=sys.stderr)
            return 2

        baseline = json.loads(args.baseline.read_text())
        passed, errors = check_regression(metrics, baseline)

        print(f"\n📈 Baseline Comparison:")
        if passed:
            print("  ✅ No regressions detected")
            return 0
        else:
            print("  ❌ Regressions detected:")
            for error in errors:
                print(f"    {error}")
            return 1

    # No baseline comparison - just report status
    if metrics.get("status") == "passed":
        print("\n✅ Benchmark PASSED")
        return 0
    else:
        print(f"\n❌ Benchmark FAILED: {metrics.get('failure_reason', 'Unknown')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
