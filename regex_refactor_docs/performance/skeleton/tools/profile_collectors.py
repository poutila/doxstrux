#!/usr/bin/env python3
"""
Performance profiling for Phase 8 Token Warehouse collectors.

Usage:
    # With Scalene (recommended - detailed memory/CPU breakdown):
    pip install scalene
    scalene --reduced-profile --outfile profile.html tools/profile_collectors.py

    # With py-spy (faster, sampling-based):
    pip install py-spy
    py-spy top -- python tools/profile_collectors.py

    # With built-in cProfile:
    python -m cProfile -o profile.stats tools/profile_collectors.py
    python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(30)"

    # Quick benchmark (no profiling):
    python tools/profile_collectors.py

What this measures:
- Warehouse index building time (O(N) single pass)
- Collector dispatch time (O(N × C_avg) routing)
- Finalization time
- Memory overhead (if using tracemalloc)

Expected results (Phase 8 baseline):
- 10K tokens: ~5-10ms total
- 100K tokens: ~50-100ms total (linear scaling)
- Memory overhead: ~20% vs token storage
"""
from __future__ import annotations
import time
import random
from typing import Any, Optional


class MockToken:
    """Minimal token mock for profiling."""

    def __init__(
        self,
        type: str,
        nesting: int = 0,
        tag: str = "",
        map_: Optional[tuple[int, int]] = None,
        info: Optional[str] = None,
        href: Optional[str] = None,
        content: str = "",
    ):
        self.type = type
        self.nesting = nesting
        self.tag = tag
        self.map = map_
        self.info = info
        self._href = href
        self.content = content

    def attrGet(self, name: str) -> Optional[str]:
        return self._href if name == "href" else None


def generate_tokens(n: int = 10000, density: float = 0.3) -> list[MockToken]:
    """Generate realistic token stream for profiling.

    Args:
        n: Target number of tokens
        density: Ratio of structural tokens (headings, links, etc.) to plain text

    Returns:
        List of mock tokens simulating a markdown document
    """
    tokens = []
    line = 0

    # Estimate headings needed
    tokens_per_section = 50  # Avg tokens between headings
    n_headings = max(1, n // tokens_per_section)

    for i in range(n_headings):
        # Heading
        level = random.choice([1, 2, 2, 3, 3, 3])  # More H2/H3 than H1
        tag = f"h{level}"
        tokens.append(MockToken("heading_open", 1, tag, (line, line + 1)))
        tokens.append(MockToken("inline", 0, "", None, content=f"Section {i}"))
        tokens.append(MockToken("heading_close", -1, tag, (line, line + 1)))
        line += 1

        # Content under this heading
        n_paragraphs = random.randint(3, 8)
        for _ in range(n_paragraphs):
            # Paragraph
            tokens.append(MockToken("paragraph_open", 1, "", (line, line + 2)))

            # Mix of text and links
            if random.random() < density:
                # Link
                tokens.append(
                    MockToken(
                        "link_open",
                        1,
                        "",
                        (line, line + 1),
                        href=f"https://example.com/page{len(tokens)}",
                    )
                )
                tokens.append(MockToken("inline", 0, "", None, content="link text"))
                tokens.append(MockToken("link_close", -1, ""))
            else:
                # Plain text
                tokens.append(MockToken("inline", 0, "", None, content="plain text " * 10))

            tokens.append(MockToken("paragraph_close", -1, "", (line, line + 2)))
            line += 2

            # Occasionally add a fence
            if random.random() < 0.1:
                tokens.append(MockToken("fence", 0, "", (line, line + 10), info="python"))
                line += 10

            if len(tokens) >= n:
                break

        if len(tokens) >= n:
            break

    return tokens[:n]  # Trim to exact size


def benchmark_warehouse_only(tokens: list[MockToken], runs: int = 5) -> dict[str, float]:
    """Benchmark just warehouse index building (no collectors)."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        print("ERROR: TokenWarehouse not available")
        print("Copy skeleton/doxstrux/markdown/utils/token_warehouse.py to src/ first")
        return {}

    times = []
    for _ in range(runs):
        start = time.perf_counter()
        wh = TokenWarehouse(tokens, tree=None)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    median = sorted(times)[runs // 2]
    return {"median_ms": median * 1000, "samples": times}


def benchmark_with_collectors(tokens: list[MockToken], runs: int = 5) -> dict[str, float]:
    """Benchmark full warehouse + collectors dispatch."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        print("ERROR: Collectors not available")
        print("Copy skeleton collectors to src/ first")
        return {}

    times = []
    for _ in range(runs):
        start = time.perf_counter()

        # Warehouse build
        wh = TokenWarehouse(tokens, tree=None)

        # Register collectors
        col = LinksCollector()
        wh.register_collector(col)

        # Dispatch
        wh.dispatch_all()

        # Finalize
        data = wh.finalize_all()

        elapsed = time.perf_counter() - start
        times.append(elapsed)

    median = sorted(times)[runs // 2]
    return {"median_ms": median * 1000, "samples": times, "links_found": len(data.get("links", []))}


def benchmark_scaling(sizes: list[int] = None, runs: int = 3):
    """Measure scaling characteristics (verify O(N) complexity)."""
    if sizes is None:
        sizes = [1000, 5000, 10000, 50000, 100000]

    print("\n" + "=" * 80)
    print("SCALING BENCHMARK (verifying O(N) complexity)")
    print("=" * 80)
    print(f"{'Tokens':<10} {'Warehouse (ms)':<20} {'Full Pipeline (ms)':<20} {'Links Found':<15}")
    print("-" * 80)

    for n in sizes:
        tokens = generate_tokens(n)

        # Warehouse only
        wh_result = benchmark_warehouse_only(tokens, runs=runs)
        if not wh_result:
            print(f"{n:<10} ERROR: Warehouse not available")
            continue

        # Full pipeline
        full_result = benchmark_with_collectors(tokens, runs=runs)
        if not full_result:
            print(f"{n:<10} {wh_result['median_ms']:<20.2f} ERROR: Collectors not available")
            continue

        print(
            f"{n:<10} {wh_result['median_ms']:<20.2f} {full_result['median_ms']:<20.2f} {full_result['links_found']:<15}"
        )

    print("=" * 80)
    print("\nExpected: Time should scale linearly (2x tokens → ~2x time)")
    print("If you see superlinear scaling, investigate hot loops with profiler.\n")


def profile_with_tracemalloc(n: int = 50000):
    """Profile memory usage with tracemalloc."""
    import tracemalloc

    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        print("ERROR: Warehouse/collectors not available")
        return

    tokens = generate_tokens(n)

    print("\n" + "=" * 80)
    print(f"MEMORY PROFILING ({n} tokens)")
    print("=" * 80)

    # Baseline: token storage
    tracemalloc.start()
    _ = tokens  # Just store tokens
    baseline_mb = tracemalloc.get_traced_memory()[1] / 1024 / 1024
    tracemalloc.stop()

    print(f"Tokens alone:        {baseline_mb:.2f} MB")

    # With warehouse
    tracemalloc.start()
    wh = TokenWarehouse(tokens, tree=None)
    col = LinksCollector()
    wh.register_collector(col)
    wh.dispatch_all()
    _ = wh.finalize_all()
    warehouse_mb = tracemalloc.get_traced_memory()[1] / 1024 / 1024
    tracemalloc.stop()

    overhead_mb = warehouse_mb - baseline_mb
    overhead_pct = (overhead_mb / baseline_mb) * 100 if baseline_mb > 0 else 0

    print(f"With warehouse:      {warehouse_mb:.2f} MB")
    print(f"Overhead:            {overhead_mb:.2f} MB ({overhead_pct:.1f}%)")
    print("=" * 80)
    print("\nExpected overhead: ~20% (precomputed indices)")
    print("If overhead > 50%, investigate index sizes.\n")


def main():
    """Run all benchmarks."""
    print("\n" + "=" * 80)
    print("PHASE 8 TOKEN WAREHOUSE - PERFORMANCE PROFILING")
    print("=" * 80)

    # Quick smoke test
    print("\n>>> Quick smoke test (10K tokens, 5 runs)...")
    tokens = generate_tokens(10000)
    result = benchmark_with_collectors(tokens, runs=5)

    if result:
        print(f"Median time: {result['median_ms']:.2f} ms")
        print(f"Links found: {result['links_found']}")
    else:
        print("ERROR: Could not run benchmark (warehouse/collectors not available)")
        print("\nTo fix:")
        print("  1. Copy skeleton/doxstrux/markdown/utils/token_warehouse.py → src/doxstrux/markdown/utils/")
        print(
            "  2. Copy skeleton/doxstrux/markdown/collectors_phase8/*.py → src/doxstrux/markdown/collectors_phase8/"
        )
        return

    # Scaling benchmark
    benchmark_scaling(sizes=[1000, 5000, 10000, 50000], runs=3)

    # Memory profiling
    profile_with_tracemalloc(n=50000)

    print("\n" + "=" * 80)
    print("PROFILING COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. For detailed CPU profiling: scalene --reduced-profile tools/profile_collectors.py")
    print("  2. For hot-loop analysis: py-spy top -- python tools/profile_collectors.py")
    print("  3. Compare vs Phase 7.6 baseline to verify speedup")
    print()


if __name__ == "__main__":
    main()
