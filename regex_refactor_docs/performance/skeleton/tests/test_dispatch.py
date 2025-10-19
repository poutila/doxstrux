"""
Test TokenWarehouse dispatch system (Step 4).

This test file is created BEFORE refactoring to provide
immediate verification as O(N+M) dispatch is implemented.

Tests cover:
- Single-pass dispatch (exactly one iteration over tokens)
- O(N+M) complexity verification (not O(N×M))
- Routing table O(1) collector lookup
- ignore_inside constraint enforcement
- Collector timeout protection
- Error handling and collection
"""

import pytest
from pathlib import Path
import sys
import time

# Add skeleton to path for imports
SKELETON_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKELETON_ROOT))

try:
    from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    from markdown_it import MarkdownIt
    from markdown_it.tree import SyntaxTreeNode
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


@pytest.fixture
def create_warehouse():
    """Helper to create TokenWarehouse from markdown content."""
    if not IMPORTS_AVAILABLE:
        pytest.skip("TokenWarehouse not available yet")

    def _create(content: str) -> TokenWarehouse:
        md = MarkdownIt("gfm-like")
        tokens = md.parse(content)
        tree = SyntaxTreeNode(tokens)
        return TokenWarehouse(tokens, tree, content)
    return _create


# ============================================================================
# Single-Pass Dispatch Tests
# ============================================================================

def test_single_pass_dispatch(create_warehouse):
    """Test dispatch iterates tokens exactly once (Step 4).

    Verify O(N+M) complexity: N tokens + M collectors.
    """
    content = "# Title\n\n" + "Paragraph\n\n" * 100 + "[link](url)"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Instrument dispatch to count token iterations
    # iteration_count = 0
    # (register mock collector that increments counter)
    # wh.dispatch_all()
    # assert iteration_count == len(wh.tokens)  # Exactly N iterations
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


def test_dispatch_not_nested_loops(create_warehouse):
    """Test dispatch does NOT iterate collectors for each token (O(N×M) anti-pattern)."""
    content = "# H1\n\n[link](url)\n\n**bold**"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Mock multiple collectors, verify each token visited once
    # Old pattern (BAD): for tok in tokens: for col in collectors: col.process(tok)
    # New pattern (GOOD): for tok in tokens: routing_table[tok.type].process(tok)
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


# ============================================================================
# Routing Table Tests
# ============================================================================

def test_routing_table_created(create_warehouse):
    """Test routing table is built during collector registration."""
    content = "Test"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: wh._routing exists and maps token types to collectors
    # wh.register_collector(MockCollector(wants=["link_open"]))
    # assert "link_open" in wh._routing
    # assert isinstance(wh._routing["link_open"], list)
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


def test_routing_table_o1_lookup(create_warehouse):
    """Test routing table provides O(1) collector lookup per token."""
    content = "[link](url)"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Measure lookup time, verify constant regardless of collector count
    # Register 10 collectors, measure dispatch time
    # Register 100 collectors, measure dispatch time
    # assert time_100 / time_10 < 2  # Should be linear in M, not quadratic
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


def test_routing_table_tag_based(create_warehouse):
    """Test routing table supports tag-based routing (e.g., 'h1', 'h2')."""
    content = "# H1\n## H2\n### H3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Collectors can register for specific tags
    # Mock collector wants tag="h1" → only dispatched to h1 tokens
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


# ============================================================================
# ignore_inside Constraint Tests
# ============================================================================

def test_ignore_inside_code_fence(create_warehouse):
    """Test collectors skip content inside code fences when ignore_inside specified."""
    content = "```\n[link](url)\n```\n\n[real link](url2)"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: LinkCollector with ignore_inside=["fence"]
    # Should only collect "real link", not link inside code fence
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


def test_ignore_inside_html_block(create_warehouse):
    """Test collectors skip content inside HTML blocks."""
    content = "<div>\n[link](url)\n</div>\n\n[real link](url2)"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: LinkCollector with ignore_inside=["html_block"]
    # Should only collect "real link"
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


def test_ignore_inside_nested(create_warehouse):
    """Test ignore_inside handles nested structures correctly."""
    content = "> Blockquote\n> ```\n> [link](url)\n> ```"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Link inside code fence inside blockquote is ignored
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


# ============================================================================
# Collector Timeout Tests
# ============================================================================

def test_collector_timeout_protection(create_warehouse):
    """Test timeout protection prevents runaway collectors."""
    content = "Test content"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Register slow collector that sleeps > timeout
    # class SlowCollector:
    #     def wants(self): return ["paragraph_open"]
    #     def collect(self, tok, wh): time.sleep(10)  # Exceeds timeout
    # wh.register_collector(SlowCollector())
    # wh.dispatch_all(timeout=1)
    # assert wh.errors  # Timeout error recorded
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


def test_collector_timeout_platform_check(create_warehouse):
    """Test timeout uses correct mechanism (SIGALRM on Unix, threading.Timer on Windows)."""
    content = "Test"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 Windows portability + Step 4
    # Expected: On Unix, uses signal.SIGALRM
    # On Windows, uses threading.Timer
    # import platform
    # if platform.system() == "Windows":
    #     assert wh._timeout_mechanism == "threading"
    # else:
    #     assert wh._timeout_mechanism == "signal"
    pytest.skip("Implement after Step 3: Windows portability")


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_dispatch_errors_collected(create_warehouse):
    """Test dispatch collects errors from failing collectors."""
    content = "Test"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Register collector that raises exception
    # class FailingCollector:
    #     def wants(self): return ["paragraph_open"]
    #     def collect(self, tok, wh): raise ValueError("Boom")
    # wh.register_collector(FailingCollector())
    # wh.dispatch_all()
    # assert len(wh.errors) == 1
    # assert "Boom" in wh.errors[0]
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


def test_dispatch_continues_after_error(create_warehouse):
    """Test dispatch continues processing after collector error."""
    content = "# H1\n\nParagraph"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Register 2 collectors, first fails, second succeeds
    # Both should be dispatched (error doesn't halt dispatch)
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


# ============================================================================
# Reentrancy Guard Tests
# ============================================================================

def test_dispatch_reentrancy_guard(create_warehouse):
    """Test dispatch prevents concurrent execution (reentrancy guard)."""
    content = "Test"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Attempting to call dispatch_all() while already dispatching raises error
    # class ReentrantCollector:
    #     def collect(self, tok, wh):
    #         wh.dispatch_all()  # Try to re-enter
    # wh.register_collector(ReentrantCollector())
    # with pytest.raises(RuntimeError, match="already dispatching"):
    #     wh.dispatch_all()
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


# ============================================================================
# Performance Verification Tests
# ============================================================================

def test_dispatch_complexity_verification(create_warehouse):
    """Test dispatch complexity is O(N+M), not O(N×M)."""
    # TODO: Implement after Step 4 completes
    # Expected: Measure dispatch time with varying N and M
    # N=1000, M=1: t1
    # N=1000, M=10: t10
    # N=10000, M=1: t2
    # assert t10 / t1 < 2  # Linear in M
    # assert t2 / t1 < 15  # Linear in N (with some overhead)
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


def test_dispatch_scales_with_collectors(create_warehouse):
    """Test dispatch time scales linearly with collector count."""
    content = "# Title\n\n" + "Paragraph\n\n" * 100
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Measure time with 1, 10, 50 collectors
    # Verify linear scaling (not quadratic)
    pytest.skip("Implement after Step 4: O(N+M) dispatch")


# ============================================================================
# Integration Tests
# ============================================================================

def test_dispatch_with_real_collectors(create_warehouse):
    """Test dispatch with actual collectors (links, headings, paragraphs)."""
    content = "# Title\n\n[link](url)\n\nParagraph text."
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 + Step 5 (collector migration)
    # Expected: Register real collectors, verify correct output
    # from skeleton.doxstrux.markdown.collectors_phase8.links import LinksCollector
    # from skeleton.doxstrux.markdown.collectors_phase8.headings import HeadingsCollector
    # wh.register_collector(LinksCollector())
    # wh.register_collector(HeadingsCollector())
    # wh.dispatch_all()
    # results = wh.finalize_all()
    # assert len(results["links"]) == 1
    # assert len(results["headings"]) == 1
    pytest.skip("Implement after Step 5: Collector migration")


def test_dispatch_preserves_order(create_warehouse):
    """Test dispatch processes tokens in document order."""
    content = "# H1\n\nPara 1\n\n# H2\n\nPara 2"
    wh = create_warehouse(content)

    # TODO: Implement after Step 4 completes
    # Expected: Collectors receive tokens in order
    # Mock collector records token indices → verify monotonically increasing
    pytest.skip("Implement after Step 4: O(N+M) dispatch")
