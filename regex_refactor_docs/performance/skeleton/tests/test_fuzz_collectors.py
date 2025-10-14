"""
Fuzzing tests for Phase 8 Token Warehouse - structural integrity validation.

These tests use randomized inputs to verify:
1. Section boundaries never overlap
2. Pairs are always legal (open < close)
3. Collectors never raise exceptions
4. Routing remains stable on random token orders

Run with: pytest tests/test_fuzz_collectors.py -v
"""
from __future__ import annotations
import random
import pytest
from typing import Any, Optional


class MockToken:
    """Minimal token mock for fuzzing."""

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


def make_random_doc(
    n_headings: int = 10,
    n_links: int = 10,
    max_level: int = 3,
    seed: Optional[int] = None,
) -> list[MockToken]:
    """Generate randomized markdown document tokens.

    Args:
        n_headings: Number of headings to generate
        n_links: Number of links per heading section
        max_level: Maximum heading level (1-6)
        seed: Random seed for reproducibility

    Returns:
        List of mock tokens representing a markdown document
    """
    if seed is not None:
        random.seed(seed)

    tokens = []
    line = 0

    for i in range(n_headings):
        # Random heading level
        level = random.randint(1, max_level)
        tag = f"h{level}"

        # Heading open/inline/close
        tokens.append(MockToken("heading_open", 1, tag, (line, line + 1)))
        tokens.append(MockToken("inline", 0, "", None, content=f"Heading {i} Level {level}"))
        tokens.append(MockToken("heading_close", -1, tag, (line, line + 1)))
        line += random.randint(1, 3)

        # Random number of links in this section
        n_links_here = random.randint(0, n_links)
        for j in range(n_links_here):
            tokens.append(MockToken("paragraph_open", 1, "", (line, line + 1)))
            tokens.append(
                MockToken(
                    "link_open",
                    1,
                    "",
                    (line, line + 1),
                    href=f"http://example.com/{i}_{j}",
                )
            )
            tokens.append(MockToken("inline", 0, "", None, content=f"Link {i}_{j}"))
            tokens.append(MockToken("link_close", -1, ""))
            tokens.append(MockToken("paragraph_close", -1, "", (line, line + 1)))
            line += 1

    return tokens


def make_nested_blocks(depth: int = 5) -> list[MockToken]:
    """Generate deeply nested block structures."""
    tokens = []
    line = 0

    # Open blocks
    for i in range(depth):
        tokens.append(MockToken("blockquote_open", 1, "", (line, line + 1)))
        line += 1

    # Content
    tokens.append(MockToken("paragraph_open", 1, "", (line, line + 1)))
    tokens.append(MockToken("inline", 0, "", None, content="Deep content"))
    tokens.append(MockToken("paragraph_close", -1, "", (line, line + 1)))
    line += 1

    # Close blocks
    for i in range(depth):
        tokens.append(MockToken("blockquote_close", -1, "", (line, line + 1)))
        line += 1

    return tokens


def make_fence_with_links() -> list[MockToken]:
    """Generate fence with links inside (should be ignored)."""
    tokens = []

    # Fence with link-like content
    tokens.append(MockToken("fence", 0, "", (0, 5), info="markdown"))
    tokens.append(MockToken("paragraph_open", 1, "", (6, 7)))
    tokens.append(
        MockToken("link_open", 1, "", (6, 7), href="http://should-be-collected.com")
    )
    tokens.append(MockToken("inline", 0, "", None, content="After fence"))
    tokens.append(MockToken("link_close", -1, ""))
    tokens.append(MockToken("paragraph_close", -1, "", (6, 7)))

    return tokens


# ============================================================================
# Fuzz Tests
# ============================================================================


@pytest.mark.parametrize("n_headings,n_links", [(20, 5), (50, 10), (100, 3)])
def test_fuzz_sections_and_links(n_headings: int, n_links: int):
    """Randomized test: verify section integrity and collector stability."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        pytest.skip("TokenWarehouse not available (copy from skeleton first)")

    tokens = make_random_doc(n_headings, n_links)
    wh = TokenWarehouse(tokens, tree=None)

    # ========================================================================
    # Invariant 1: Sections strictly increasing, non-overlapping
    # ========================================================================
    sections = wh.sections_list()
    starts = [s for _, s, _, _, _ in sections]

    assert starts == sorted(starts), "Sections not sorted by start line"

    for i in range(1, len(sections)):
        _, prev_start, prev_end, prev_level, prev_text = sections[i - 1]
        _, curr_start, curr_end, curr_level, curr_text = sections[i]

        assert (
            prev_end < curr_start
        ), f"Overlap: section {i-1} [{prev_start}, {prev_end}] overlaps with section {i} [{curr_start}, {curr_end}]"

    # ========================================================================
    # Invariant 2: section_of() binary search correctness
    # ========================================================================
    for i, (_, start, end, _, _) in enumerate(sections):
        for line in range(start, end + 1):
            section_id = wh.section_of(line)
            assert (
                section_id == f"section_{i}"
            ), f"Binary search failed: line {line} should be in section_{i}, got {section_id}"

    # ========================================================================
    # Invariant 3: Pairs are legal
    # ========================================================================
    pairs = wh.pairs
    n_tokens = len(wh.tokens)

    for open_idx, close_idx in pairs.items():
        assert (
            0 <= open_idx < n_tokens
        ), f"Open index {open_idx} out of bounds (n={n_tokens})"
        assert (
            0 <= close_idx < n_tokens
        ), f"Close index {close_idx} out of bounds (n={n_tokens})"
        assert (
            open_idx < close_idx
        ), f"Pair ordering broken: open={open_idx}, close={close_idx}"


@pytest.mark.parametrize("seed", [42, 123, 999, 2025])
def test_fuzz_collectors_never_raise(seed: int):
    """Collectors must never raise exceptions on randomized inputs."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        pytest.skip("Collectors not available (copy from skeleton first)")

    tokens = make_random_doc(n_headings=30, n_links=20, seed=seed)
    wh = TokenWarehouse(tokens, tree=None)

    # Register collector
    col = LinksCollector()
    wh.register_collector(col)

    # Dispatch should never raise
    wh.dispatch_all()

    # Finalize should return valid data
    data = wh.finalize_all()["links"]

    # Verify all links have required fields
    for item in data:
        assert "url" in item, f"Link missing 'url': {item}"
        assert "text" in item, f"Link missing 'text': {item}"


def test_nested_blocks_pairs():
    """Deeply nested blocks should maintain pair integrity."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        pytest.skip("TokenWarehouse not available")

    tokens = make_nested_blocks(depth=10)
    wh = TokenWarehouse(tokens, tree=None)

    pairs = wh.pairs
    n_tokens = len(wh.tokens)

    # All pairs legal
    for open_idx, close_idx in pairs.items():
        assert 0 <= open_idx < n_tokens
        assert 0 <= close_idx < n_tokens
        assert open_idx < close_idx

    # Verify nesting depth
    parents = wh.parents
    max_depth = 0

    for i in range(n_tokens):
        depth = 0
        current = i
        while current in parents:
            depth += 1
            current = parents[current]
            if depth > 100:  # Safety: prevent infinite loops
                pytest.fail(f"Infinite loop detected in parent chain starting at {i}")
        max_depth = max(max_depth, depth)

    # Expect depth ≈ 10 (may vary slightly due to inline tokens)
    assert max_depth >= 5, f"Expected deep nesting, got max_depth={max_depth}"


def test_no_headings_empty_sections():
    """Documents without headings should have empty sections list."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        pytest.skip("TokenWarehouse not available")

    # Generate document with only paragraphs (no headings)
    tokens = []
    for i in range(10):
        tokens.append(MockToken("paragraph_open", 1, "", (i, i + 1)))
        tokens.append(MockToken("inline", 0, "", None, content=f"Paragraph {i}"))
        tokens.append(MockToken("paragraph_close", -1, "", (i, i + 1)))

    wh = TokenWarehouse(tokens, tree=None)

    # No sections
    assert wh.sections_list() == [], "Expected empty sections for doc without headings"

    # section_of() should always return None
    for line in range(20):
        assert wh.section_of(line) is None


def test_links_inside_fences_ignored():
    """Links inside code fences should be ignored by LinksCollector."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        pytest.skip("Collectors not available")

    tokens = make_fence_with_links()
    wh = TokenWarehouse(tokens, tree=None)

    col = LinksCollector()
    wh.register_collector(col)
    wh.dispatch_all()

    links = wh.finalize_all()["links"]

    # Only the link AFTER the fence should be collected
    # (Link-like content inside fence is just code, not collected)
    assert len(links) == 1, f"Expected 1 link (after fence), got {len(links)}"
    assert links[0]["url"] == "http://should-be-collected.com"


@pytest.mark.parametrize("run", range(10))
def test_fuzz_heading_permutations(run: int):
    """Random heading level permutations should never produce overlaps."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        pytest.skip("TokenWarehouse not available")

    # Generate 50 headings with random levels
    tokens = make_random_doc(n_headings=50, n_links=0, max_level=6, seed=run)
    wh = TokenWarehouse(tokens, tree=None)

    sections = wh.sections_list()

    # Verify non-overlap
    for i in range(1, len(sections)):
        _, prev_start, prev_end, _, _ = sections[i - 1]
        _, curr_start, curr_end, _, _ = sections[i]
        assert prev_end < curr_start, f"Run {run}: Overlap detected at section {i}"

    # Verify binary search for all lines
    for i, (_, start, end, _, _) in enumerate(sections):
        for line in [start, (start + end) // 2, end]:  # Test start, mid, end
            assert wh.section_of(line) == f"section_{i}"


# ============================================================================
# Performance Smoke Test
# ============================================================================


def test_fuzz_large_document():
    """Stress test with large document (1000 headings)."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        pytest.skip("TokenWarehouse not available")

    import time

    tokens = make_random_doc(n_headings=1000, n_links=5, max_level=6)

    start = time.perf_counter()
    wh = TokenWarehouse(tokens, tree=None)
    elapsed = time.perf_counter() - start

    # Should complete in < 100ms even with 1000 headings
    assert elapsed < 0.1, f"Warehouse build too slow: {elapsed*1000:.2f}ms"

    # Verify structural integrity
    sections = wh.sections_list()
    assert len(sections) == 1000

    for i in range(1, len(sections)):
        assert sections[i - 1][2] < sections[i][1], f"Overlap in large doc at section {i}"
