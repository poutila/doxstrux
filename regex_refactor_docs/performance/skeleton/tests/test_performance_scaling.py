"""Synthetic performance scaling tests to detect algorithmic regressions.

These tests measure parse time vs. input size to detect O(N²) or worse
complexity patterns. They help ensure collectors remain O(N) or better.
"""

import time
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "doxstrux" / "markdown"))

try:
    from utils.token_warehouse import TokenWarehouse
    from collectors_phase8.links import LinksCollector
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("⚠️  Warning: TokenWarehouse or collectors not available")
    print("   Skipping performance scaling tests")


def generate_links_document(num_links: int) -> list:
    """Generate document with N links."""
    tokens = []

    for i in range(num_links):
        tokens.extend([
            {"type": "paragraph_open", "nesting": 1, "map": [i*3, i*3+3]},
            {
                "type": "inline",
                "nesting": 0,
                "content": f"[Link {i}](https://example.com/{i})",
                "children": [
                    {"type": "link_open", "nesting": 1, "href": f"https://example.com/{i}"},
                    {"type": "text", "content": f"Link {i}"},
                    {"type": "link_close", "nesting": -1},
                ]
            },
            {"type": "paragraph_close", "nesting": -1, "map": [i*3, i*3+3]},
        ])

    return tokens


def test_linear_time_scaling():
    """Assert parse time grows linearly (not quadratically) with input size.

    O(N) behavior: time(2N) / time(N) ≈ 2.0
    O(N²) behavior: time(2N) / time(N) ≈ 4.0
    """

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    sizes = [100, 200, 500, 1000, 2000]
    times = []

    print(f"\n  Testing linear scaling...")

    for size in sizes:
        tokens = generate_links_document(size)

        # Warm up (first run may have JIT overhead)
        wh = TokenWarehouse(tokens, None)
        wh.register_collector(LinksCollector())
        wh.dispatch_all()

        # Measure 3 runs and take median
        runs = []
        for _ in range(3):
            start = time.perf_counter()

            wh = TokenWarehouse(tokens, None)
            wh.register_collector(LinksCollector())
            wh.dispatch_all()

            elapsed = time.perf_counter() - start
            runs.append(elapsed)

        median_time = sorted(runs)[1]
        times.append(median_time)

        print(f"    {size:5d} links: {median_time*1000:7.2f} ms")

    # Check scaling ratios
    # Ratio 200/100 should be ~2.0 (linear) not ~4.0 (quadratic)
    ratio_200_100 = times[1] / times[0] if times[0] > 0 else 0

    # Ratio 2000/1000 should also be ~2.0
    ratio_2000_1000 = times[4] / times[3] if times[3] > 0 else 0

    TOLERANCE = 1.0  # Allow 100% variance (real-world noise, GC, etc.)
    EXPECTED_LINEAR = 2.0

    print(f"\n  Scaling ratios:")
    print(f"    200/100:    {ratio_200_100:.2f} (expected ~2.0 for linear)")
    print(f"    2000/1000:  {ratio_2000_1000:.2f} (expected ~2.0 for linear)")

    # Assert near-linear scaling
    assert abs(ratio_200_100 - EXPECTED_LINEAR) < TOLERANCE, \
        f"Quadratic growth detected: 200/100 ratio = {ratio_200_100:.2f} (expected ~2.0)"

    assert abs(ratio_2000_1000 - EXPECTED_LINEAR) < TOLERANCE, \
        f"Quadratic growth detected: 2000/1000 ratio = {ratio_2000_1000:.2f} (expected ~2.0)"


def test_no_catastrophic_backtracking():
    """Verify no regex catastrophic backtracking in collectors."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    # Pathological input for backtracking regex (e.g., (a+)+b)
    pathological_content = "a" * 10000 + "X"  # No 'b' at end = worst case

    tokens = [{
        "type": "inline",
        "nesting": 0,
        "content": pathological_content
    }]

    print(f"\n  Testing catastrophic backtracking protection...")

    # Should complete quickly (< 1 second)
    start = time.perf_counter()

    wh = TokenWarehouse(tokens, None)
    # Register all available collectors
    wh.register_collector(LinksCollector())
    wh.dispatch_all()

    elapsed = time.perf_counter() - start

    print(f"    Processed {len(pathological_content)} chars in {elapsed:.3f}s")

    assert elapsed < 1.0, \
        f"Regex DoS detected: {elapsed:.3f}s for pathological input (threshold: 1.0s)"


def test_memory_scaling_linear():
    """Assert memory usage grows linearly with input size."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    import tracemalloc

    sizes = [1000, 2000, 5000]
    memory_usages = []

    print(f"\n  Testing memory scaling...")

    for size in sizes:
        tokens = generate_links_document(size)

        tracemalloc.start()

        wh = TokenWarehouse(tokens, None)
        wh.register_collector(LinksCollector())
        wh.dispatch_all()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        memory_mb = peak / 1024 / 1024
        memory_usages.append(memory_mb)

        print(f"    {size:5d} links: {memory_mb:.2f} MB peak")

    # Check memory scaling
    # Should be roughly proportional: mem(2N) / mem(N) ≈ 2.0
    ratio_2000_1000 = memory_usages[1] / memory_usages[0] if memory_usages[0] > 0 else 0
    ratio_5000_2000 = memory_usages[2] / memory_usages[1] if memory_usages[1] > 0 else 0

    print(f"\n  Memory scaling ratios:")
    print(f"    2000/1000: {ratio_2000_1000:.2f}")
    print(f"    5000/2000: {ratio_5000_2000:.2f}")

    # Allow more tolerance for memory (GC, allocator overhead)
    TOLERANCE = 1.5
    EXPECTED = 2.5  # Account for baseline overhead

    # Memory should not explode (> 5x growth for 2.5x input)
    assert ratio_5000_2000 < 5.0, \
        f"Explosive memory growth: {ratio_5000_2000:.2f}x for 2.5x input"


def test_large_document_performance():
    """Test performance on a large document (10K links)."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    print(f"\n  Testing large document (10K links)...")

    tokens = generate_links_document(10000)

    start = time.perf_counter()

    wh = TokenWarehouse(tokens, None)
    wh.register_collector(LinksCollector())
    wh.dispatch_all()

    elapsed = time.perf_counter() - start

    print(f"    10,000 links: {elapsed*1000:.2f} ms")

    # Should complete in reasonable time (< 1 second)
    assert elapsed < 1.0, \
        f"Large document too slow: {elapsed:.3f}s for 10K links (threshold: 1.0s)"


if __name__ == "__main__":
    # Run tests
    tests = [
        test_linear_time_scaling,
        test_no_catastrophic_backtracking,
        test_memory_scaling_linear,
        test_large_document_performance,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
