"""
Test forbid wh.tokens iteration - RED TEAM BLOCKER TEST 5.

CRITICAL: Collectors must NOT iterate over wh.tokens directly.

Direct iteration breaks the O(N+M) complexity guarantee:
- Warehouse dispatches in O(N+M) where N=tokens, M=collectors
- If collector iterates wh.tokens, it becomes O(N*M) - catastrophic

Collectors should use:
- wh.by_type[type] - O(1) lookup, O(K) iteration where K=matches
- wh.tokens_between(start, end, filter) - O(log N + K)
- wh.children[idx] - O(K) where K=children count

Never:
- for tok in wh.tokens - O(N) per collector = O(N*M) total

Red-Team Scenario:
A "naughty" collector that iterates wh.tokens can cause performance regression
from O(N+M) to O(N*M), defeating the entire dispatch optimization.
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


def test_collector_must_not_iterate_tokens(monkeypatch):
    """
    CRITICAL: Forbid collectors from iterating wh.tokens.

    We monkeypatch tokens.__iter__ to raise an error if iteration is attempted.
    """
    md = "# Heading\n\nParagraph\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Monkeypatch tokens list to detect iteration attempts
    original_tokens = wh.tokens
    iteration_attempted = [False]

    class IterationDetector:
        """Wrapper that raises if __iter__ is called."""

        def __init__(self, tokens):
            self._tokens = tokens

        def __iter__(self):
            iteration_attempted[0] = True
            raise RuntimeError(
                "FORBIDDEN: Collector must not iterate wh.tokens directly. "
                "Use wh.by_type[type], wh.tokens_between(), or wh.children instead."
            )

        def __getitem__(self, idx):
            # Allow index access (wh.tokens[idx] is OK)
            return self._tokens[idx]

        def __len__(self):
            return len(self._tokens)

    wh.tokens = IterationDetector(original_tokens)

    class NaughtyCollector:
        """Collector that tries to iterate wh.tokens (BAD)."""
        name = "Naughty"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            # This should raise because we monkeypatched __iter__
            for tok in wh.tokens:  # FORBIDDEN
                pass

        def finalize(self, wh):
            return {}

    wh.register_collector(NaughtyCollector())

    # Dispatch should raise because collector iterates tokens
    with pytest.raises(RuntimeError, match="FORBIDDEN.*iterate wh.tokens"):
        wh.dispatch_all()

    # Verify iteration was attempted
    assert iteration_attempted[0], "Iteration was not detected"


def test_collector_can_use_by_type():
    """
    Verify collectors CAN use wh.by_type[] (this is allowed and efficient).

    by_type provides O(1) lookup + O(K) iteration where K=matches.
    """
    md = "# H1\n\n## H2\n\n### H3\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    headings_found = []

    class WellBehavedCollector:
        """Collector that uses by_type (GOOD)."""
        name = "WellBehaved"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            # Use by_type to find all headings (efficient)
            all_headings = wh.by_type.get("heading_open", [])
            headings_found.append(len(all_headings))

        def finalize(self, wh):
            return {}

    wh.register_collector(WellBehavedCollector())
    wh.dispatch_all()

    # Should have found 3 headings
    assert all(count == 3 for count in headings_found), \
        f"Expected all counts to be 3, got {headings_found}"


def test_collector_can_use_tokens_between():
    """
    Verify collectors CAN use wh.tokens_between() (allowed and efficient).

    tokens_between() uses bisect for O(log N + K) performance.
    """
    md = "# Heading with **bold** and `code`\n\nParagraph\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    inline_tokens_found = []

    class EfficientCollector:
        """Collector that uses tokens_between (GOOD)."""
        name = "Efficient"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            # Find closing token for this heading
            close_idx = wh.pairs.get(idx)
            if close_idx:
                # Get inline tokens between heading_open and heading_close
                inline_indices = wh.tokens_between(
                    idx, close_idx, type_filter="inline"
                )
                inline_tokens_found.append(len(inline_indices))

        def finalize(self, wh):
            return {}

    wh.register_collector(EfficientCollector())
    wh.dispatch_all()

    # Should have found inline tokens in heading
    assert len(inline_tokens_found) > 0, "Should have processed heading"
    assert inline_tokens_found[0] > 0, "Should have found inline tokens"


def test_collector_can_use_children():
    """
    Verify collectors CAN use wh.children property (allowed and efficient).

    children is lazy-built and provides O(K) access where K=children count.
    """
    md = "# Heading\n\nParagraph\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    children_counts = []

    class ChildrenCollector:
        """Collector that uses children property (GOOD)."""
        name = "ChildrenCollector"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            # Access children (lazy-built on first access)
            child_indices = wh.children.get(idx, [])
            children_counts.append(len(child_indices))

        def finalize(self, wh):
            return {}

    wh.register_collector(ChildrenCollector())
    wh.dispatch_all()

    # Should have found children for heading
    assert len(children_counts) > 0, "Should have processed heading"


def test_collector_can_index_tokens():
    """
    Verify collectors CAN index tokens (wh.tokens[idx] is allowed).

    Index access is O(1) and doesn't iterate the entire list.
    """
    md = "# Heading\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    indexed_ok = [False]

    class IndexCollector:
        """Collector that indexes tokens (GOOD)."""
        name = "IndexCollector"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            # Index access is OK
            tok = wh.tokens[idx]
            indexed_ok[0] = (getattr(tok, 'type', None) == 'heading_open')

        def finalize(self, wh):
            return {}

    wh.register_collector(IndexCollector())
    wh.dispatch_all()

    assert indexed_ok[0], "Index access should work"


def test_len_tokens_is_allowed():
    """
    Verify collectors CAN call len(wh.tokens) (this is allowed).

    len() is O(1) and doesn't iterate the list.
    """
    md = "# Heading\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    token_count = [0]

    class LenCollector:
        """Collector that calls len(wh.tokens) (GOOD)."""
        name = "LenCollector"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            # len() is OK
            token_count[0] = len(wh.tokens)

        def finalize(self, wh):
            return {}

    wh.register_collector(LenCollector())
    wh.dispatch_all()

    assert token_count[0] > 0, "len() should work"


def test_enumerate_tokens_is_forbidden(monkeypatch):
    """
    Verify collectors CANNOT use enumerate(wh.tokens).

    enumerate() calls __iter__, which should be forbidden.
    """
    md = "# Heading\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Monkeypatch to detect iteration
    original_tokens = wh.tokens
    iteration_attempted = [False]

    class IterationDetector:
        def __init__(self, tokens):
            self._tokens = tokens

        def __iter__(self):
            iteration_attempted[0] = True
            raise RuntimeError("FORBIDDEN: enumerate() requires iteration")

        def __getitem__(self, idx):
            return self._tokens[idx]

        def __len__(self):
            return len(self._tokens)

    wh.tokens = IterationDetector(original_tokens)

    class EnumerateCollector:
        name = "Enumerate"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            # enumerate() should raise
            for i, tok in enumerate(wh.tokens):  # FORBIDDEN
                pass

        def finalize(self, wh):
            return {}

    wh.register_collector(EnumerateCollector())

    with pytest.raises(RuntimeError, match="FORBIDDEN"):
        wh.dispatch_all()

    assert iteration_attempted[0], "Iteration was not detected"
