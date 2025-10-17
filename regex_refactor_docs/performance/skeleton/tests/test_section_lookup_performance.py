"""
Binary search performance verification test for P1-1.

Verifies that section_index_for_line() scales as O(log N), not O(N).

Per PLAN_CLOSING_IMPLEMENTATION_extended_2.md P1-1:
- Tests performance scaling across different document sizes
- Ensures binary search implementation is correct
- Provides reference for production migration
"""

import time
import pytest


def test_section_of_is_logarithmic():
    """Verify section_index_for_line() scales as O(log N), not O(N)."""
    try:
        from skeleton.doxstrux.markdown.utils.section_utils import section_index_for_line
    except ImportError:
        pytest.skip("section_utils not available in skeleton")

    def make_sections(n):
        """Create n sections with non-overlapping line ranges."""
        return [(i * 10, (i+1) * 10 - 1) for i in range(n)]

    sizes = [100, 1000, 10000]
    times = []

    for size in sizes:
        sections = make_sections(size)

        start = time.perf_counter()
        for _ in range(1000):
            # Mid-point lookup (worst case for linear, average for binary)
            section_index_for_line(sections, size * 5)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    # Check logarithmic growth
    # If O(log N): time[1] / time[0] ≈ log(1000)/log(100) ≈ 1.5
    # If O(N): time[1] / time[0] ≈ 1000/100 = 10
    ratio = times[1] / times[0] if times[0] > 0 else float('inf')

    assert ratio < 3.0, \
        f"section_index_for_line() appears O(N), not O(log N): ratio={ratio:.2f}. " \
        f"Times: {times}"

    # EVIDENCE ANCHOR
    # CLAIM-P1-1-BENCHMARK: Binary search shows O(log N) scaling
    # Source: PLAN_CLOSING_IMPLEMENTATION_extended_2.md P1-1 lines 154-188
    # Verification: Ratio < 3.0 indicates logarithmic growth


def test_section_index_correctness():
    """Verify section_index_for_line() returns correct results."""
    try:
        from skeleton.doxstrux.markdown.utils.section_utils import section_index_for_line
    except ImportError:
        pytest.skip("section_utils not available in skeleton")

    sections = [(0, 4), (5, 9), (10, 14), (15, 19)]

    # Test exact boundaries
    assert section_index_for_line(sections, 0) == 0
    assert section_index_for_line(sections, 4) == 0
    assert section_index_for_line(sections, 5) == 1
    assert section_index_for_line(sections, 9) == 1
    assert section_index_for_line(sections, 10) == 2
    assert section_index_for_line(sections, 19) == 3

    # Test out of range
    assert section_index_for_line(sections, -1) is None
    assert section_index_for_line(sections, 20) is None

    # Test empty input
    assert section_index_for_line([], 5) is None


def test_section_of_with_binary_search_correctness():
    """Verify section_of_with_binary_search() returns correct section IDs."""
    try:
        from skeleton.doxstrux.markdown.utils.section_utils import section_of_with_binary_search
    except ImportError:
        pytest.skip("section_utils not available in skeleton")

    sections = [
        {"id": "section_0", "start_line": 0, "end_line": 4, "title": "Intro"},
        {"id": "section_1", "start_line": 5, "end_line": 9, "title": "Body"},
        {"id": "section_2", "start_line": 10, "end_line": 14, "title": "Conclusion"},
    ]

    # Test lookups
    assert section_of_with_binary_search(sections, 0) == "section_0"
    assert section_of_with_binary_search(sections, 4) == "section_0"
    assert section_of_with_binary_search(sections, 7) == "section_1"
    assert section_of_with_binary_search(sections, 12) == "section_2"

    # Test out of range
    assert section_of_with_binary_search(sections, 20) is None
    assert section_of_with_binary_search(sections, -1) is None

    # Test empty input
    assert section_of_with_binary_search([], 5) is None


# EVIDENCE ANCHOR FOR P1-1 COMPLETION
# CLAIM-P1-1-IMPL-COMPLETE: Binary search reference implementation complete
# Files: skeleton/doxstrux/markdown/utils/section_utils.py (3 functions)
#        skeleton/tests/test_section_lookup_performance.py (3 tests)
# Coverage:
#   - Binary search algorithm (section_index_for_line)
#   - Section dict wrapper (section_of_with_binary_search)
#   - Performance benchmark (test_section_of_is_logarithmic)
#   - Correctness tests (test_section_index_correctness, test_section_of_with_binary_search_correctness)
# Source: PLAN_CLOSING_IMPLEMENTATION_extended_2.md lines 52-196
# Status: ✅ COMPLETE
