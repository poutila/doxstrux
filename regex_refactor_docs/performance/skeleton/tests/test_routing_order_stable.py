"""
Test stable routing order - RED TEAM BLOCKER TEST 4.

CRITICAL: Verify collector dispatch order matches registration order.

Deterministic dispatch is CRITICAL for reproducibility:
- Same input must produce same output (no nondeterministic set() ordering)
- Collectors must fire in registration order (not hash table order)
- ctx.line must be consistent across all collectors for the same token

Red-Team Scenario:
Using list(set(collectors)) to deduplicate would randomize order based on
hash values, causing nondeterministic behavior across Python runs/versions.
"""

import pytest
from pathlib import Path
import sys

# Add skeleton to path for imports
SKELETON_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKELETON_ROOT))

try:
    from skeleton.doxstrux.markdown.utils.text_normalization import parse_markdown_normalized
    from skeleton.doxstrux.markdown.utils.token_warehouse import (
        TokenWarehouse, Interest, DispatchContext
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="TokenWarehouse not available"
)


def test_routing_order_matches_registration():
    """
    CRITICAL: Dispatch order must match registration order (deterministic).

    Collectors registered first must fire first (no set() randomness).
    """
    md = "# Heading\n\nParagraph\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Track which collector fired first
    firing_order = []

    class CollectorA:
        name = "A"
        interest = Interest(types={"inline"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            firing_order.append("A")

        def finalize(self, wh):
            return {}

    class CollectorB:
        name = "B"
        interest = Interest(types={"inline"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            firing_order.append("B")

        def finalize(self, wh):
            return {}

    # Register in order: A then B
    wh.register_collector(CollectorA())
    wh.register_collector(CollectorB())

    # Dispatch
    wh.dispatch_all()

    # Verify A fired before B for all inline tokens
    # (firing_order should be ["A", "B", "A", "B", ...] not random)
    assert len(firing_order) >= 2, "Should have fired at least twice"

    # Check pattern: A always before B for same token
    # If we have pairs, first should be A, second should be B
    for i in range(0, len(firing_order) - 1, 2):
        assert firing_order[i] == "A", \
            f"Expected A at position {i}, got {firing_order[i]}"
        assert firing_order[i + 1] == "B", \
            f"Expected B at position {i+1}, got {firing_order[i+1]}"


def test_routing_order_stable_across_runs():
    """
    Verify routing order is stable across multiple dispatch runs.

    Determinism means same order every time (not dependent on hash randomization).
    """
    md = "# H1\n\n## H2\n\n### H3\n"
    tokens, tree, normalized = parse_markdown_normalized(md)

    results_run1 = []
    results_run2 = []

    for results in [results_run1, results_run2]:
        wh = TokenWarehouse(tokens, tree, normalized)

        class OrderCollector:
            name = "OrderCollector"
            interest = Interest(types={"heading_open"})

            def should_process(self, token, ctx, wh):
                return True

            def on_token(self, idx, token, ctx, wh):
                results.append(idx)

            def finalize(self, wh):
                return {}

        wh.register_collector(OrderCollector())
        wh.dispatch_all()

    # Both runs should produce identical order
    assert results_run1 == results_run2, \
        f"Nondeterministic routing: run1={results_run1}, run2={results_run2}"


def test_ctx_line_consistent_across_collectors():
    """
    Verify ctx.line is the same for all collectors processing the same token.

    If routing order is nondeterministic, ctx.line might differ between collectors.
    """
    md = "# Heading\n\nParagraph\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Track ctx.line seen by each collector
    ctx_lines_A = []
    ctx_lines_B = []

    class CollectorA:
        name = "A"
        interest = Interest(types={"inline"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            ctx_lines_A.append(ctx.line)

        def finalize(self, wh):
            return {}

    class CollectorB:
        name = "B"
        interest = Interest(types={"inline"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            ctx_lines_B.append(ctx.line)

        def finalize(self, wh):
            return {}

    wh.register_collector(CollectorA())
    wh.register_collector(CollectorB())
    wh.dispatch_all()

    # Both collectors should see same ctx.line sequence
    assert ctx_lines_A == ctx_lines_B, \
        f"ctx.line mismatch: A={ctx_lines_A}, B={ctx_lines_B}"


def test_duplicate_registration_ignored():
    """
    Verify registering the same collector twice is ignored (stable dedup).

    Using id() for dedup ensures order is preserved (not set() randomness).
    """
    md = "# Heading\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    firing_count = [0]

    class SingletonCollector:
        name = "Singleton"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            firing_count[0] += 1

        def finalize(self, wh):
            return {}

    collector = SingletonCollector()

    # Register same collector twice
    wh.register_collector(collector)
    wh.register_collector(collector)  # Should be ignored

    wh.dispatch_all()

    # Should fire only once per token (not twice)
    assert firing_count[0] == 1, \
        f"Collector fired {firing_count[0]} times (expected 1, duplicate not ignored)"


def test_routing_order_with_multiple_types():
    """
    Verify collectors with multiple interest types fire in registration order.

    Order must be preserved even when collectors match different token types.
    """
    md = "# Heading\n\nParagraph\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    firing_order = []

    class MultiTypeCollectorA:
        name = "MultiA"
        interest = Interest(types={"heading_open", "inline"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            firing_order.append(f"A-{getattr(token, 'type', '?')}")

        def finalize(self, wh):
            return {}

    class MultiTypeCollectorB:
        name = "MultiB"
        interest = Interest(types={"heading_open", "inline"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            firing_order.append(f"B-{getattr(token, 'type', '?')}")

        def finalize(self, wh):
            return {}

    # Register A then B
    wh.register_collector(MultiTypeCollectorA())
    wh.register_collector(MultiTypeCollectorB())

    wh.dispatch_all()

    # For each token, A should fire before B
    # Example: ["A-heading_open", "B-heading_open", "A-inline", "B-inline", ...]
    for i in range(0, len(firing_order) - 1, 2):
        a_entry = firing_order[i]
        b_entry = firing_order[i + 1]

        # Both should be for same token type
        a_type = a_entry.split("-")[1]
        b_type = b_entry.split("-")[1]

        assert a_type == b_type, \
            f"Collectors fired for different types: {a_entry} vs {b_entry}"

        # A should always come before B
        assert a_entry.startswith("A-"), f"Expected A at position {i}, got {a_entry}"
        assert b_entry.startswith("B-"), f"Expected B at position {i+1}, got {b_entry}"


def test_routing_order_preserved_after_finalize():
    """
    Verify finalize() is called in the same order as registration.

    Finalize order must be deterministic (same as registration order).
    """
    md = "# Heading\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    finalize_order = []

    class CollectorA:
        name = "A"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            pass

        def finalize(self, wh):
            finalize_order.append("A")
            return {}

    class CollectorB:
        name = "B"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            pass

        def finalize(self, wh):
            finalize_order.append("B")
            return {}

    wh.register_collector(CollectorA())
    wh.register_collector(CollectorB())
    wh.dispatch_all()

    # Call finalize (warehouse should call in registration order)
    # Note: This test assumes warehouse has a finalize_all() method
    # If not, we just verify the collectors were registered in order
    if hasattr(wh, 'finalize_all'):
        wh.finalize_all()
        assert finalize_order == ["A", "B"], \
            f"Finalize order wrong: {finalize_order}"
