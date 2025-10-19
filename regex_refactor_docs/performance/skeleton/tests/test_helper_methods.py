"""
Test TokenWarehouse helper methods (Step 3).

This test file is created BEFORE refactoring to provide
immediate verification as helper methods are implemented.

Tests cover:
- find_close(idx) - Find closing token from opening token
- find_parent(idx) - Find parent token
- find_children(idx) - Find child tokens
- tokens_between(a, b) - Get tokens in range
- text_between(a, b) - Extract text between tokens
- get_line_range(start, end) - Get lines in range
- get_token_text(idx) - Extract text from token
"""

import pytest
from pathlib import Path
import sys

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
# find_close() Tests
# ============================================================================

def test_find_close_basic(create_warehouse):
    """Test find_close() returns correct closing token index."""
    content = "# Hello"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected:
    # heading_open_idx = wh.by_type["heading_open"][0]
    # heading_close_idx = wh.find_close(heading_open_idx)
    # assert wh.tokens[heading_close_idx].type == "heading_close"
    pytest.skip("Implement after Step 3: Helper methods")


def test_find_close_nested(create_warehouse):
    """Test find_close() works with nested structures."""
    content = "- Item\n  - Nested"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: Each list_open maps to its corresponding list_close
    pytest.skip("Implement after Step 3: Helper methods")


def test_find_close_uses_pairs_index(create_warehouse):
    """Test find_close() uses pairs index (O(1) lookup)."""
    content = "# Title"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: find_close() should just return wh.pairs[idx]
    pytest.skip("Implement after Step 3: Helper methods")


# ============================================================================
# find_parent() Tests
# ============================================================================

def test_find_parent_basic(create_warehouse):
    """Test find_parent() returns correct parent token index."""
    content = "> Blockquote content"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: Content tokens have blockquote as parent
    pytest.skip("Implement after Step 3: Helper methods")


def test_find_parent_nested(create_warehouse):
    """Test find_parent() with deeply nested content."""
    content = "> Level 1\n>> Level 2\n>>> Level 3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: Each level has correct parent
    pytest.skip("Implement after Step 3: Helper methods")


def test_find_parent_uses_parents_index(create_warehouse):
    """Test find_parent() uses parents index (O(1) lookup)."""
    content = "# Title"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: find_parent() should just return wh.parents[idx]
    pytest.skip("Implement after Step 3: Helper methods")


# ============================================================================
# find_children() Tests
# ============================================================================

def test_find_children_basic(create_warehouse):
    """Test find_children() returns list of child token indices."""
    content = "- Item\n  - Child"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected:
    # list_open_idx = wh.by_type["bullet_list_open"][0]
    # children = wh.find_children(list_open_idx)
    # assert isinstance(children, list)
    # assert len(children) > 0
    pytest.skip("Implement after Step 3: Helper methods")


def test_find_children_nested_lists(create_warehouse):
    """Test find_children() with nested lists."""
    content = "- L1\n  - L2\n    - L3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: Each list has children containing nested list
    pytest.skip("Implement after Step 3: Helper methods")


def test_find_children_uses_children_index(create_warehouse):
    """Test find_children() uses children index (O(1) lookup)."""
    content = "- Item"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: find_children() should return wh.children.get(idx, [])
    pytest.skip("Implement after Step 3: Helper methods")


# ============================================================================
# tokens_between() Tests
# ============================================================================

def test_tokens_between_basic(create_warehouse):
    """Test tokens_between() returns tokens in range."""
    content = "# Title\n\nParagraph"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected:
    # tokens = wh.tokens_between(0, 5)
    # assert len(tokens) == 5
    # assert all(isinstance(t, dict) for t in tokens)
    pytest.skip("Implement after Step 3: Helper methods")


def test_tokens_between_with_type_filter(create_warehouse):
    """Test tokens_between() with type filter."""
    content = "# H1\n## H2\n### H3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected:
    # headings = wh.tokens_between(0, len(wh.tokens), type="heading_open")
    # assert len(headings) == 3
    pytest.skip("Implement after Step 3: Helper methods")


def test_tokens_between_empty_range(create_warehouse):
    """Test tokens_between() with empty range."""
    content = "Test"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: tokens_between(5, 5) returns []
    pytest.skip("Implement after Step 3: Helper methods")


# ============================================================================
# text_between() Tests
# ============================================================================

def test_text_between_basic(create_warehouse):
    """Test text_between() extracts text between tokens."""
    content = "# Hello world"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected:
    # heading_open_idx = wh.by_type["heading_open"][0]
    # heading_close_idx = wh.find_close(heading_open_idx)
    # text = wh.text_between(heading_open_idx, heading_close_idx)
    # assert "Hello world" in text
    pytest.skip("Implement after Step 3: Helper methods")


def test_text_between_uses_line_offsets(create_warehouse):
    """Test text_between() uses _line_starts for efficiency."""
    content = "Line 1\nLine 2\nLine 3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: Uses _line_starts to calculate byte offsets
    pytest.skip("Implement after Step 3: Helper methods")


def test_text_between_preserves_whitespace(create_warehouse):
    """Test text_between() preserves whitespace."""
    content = "Text   with   spaces"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: Multiple spaces preserved
    pytest.skip("Implement after Step 3: Helper methods")


# ============================================================================
# get_line_range() Tests
# ============================================================================

def test_get_line_range_basic(create_warehouse):
    """Test get_line_range() returns lines in range."""
    content = "Line 1\nLine 2\nLine 3\nLine 4"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected:
    # lines = wh.get_line_range(1, 3)
    # assert len(lines) == 2
    # assert lines[0] == "Line 2"
    # assert lines[1] == "Line 3"
    pytest.skip("Implement after Step 3: Helper methods")


def test_get_line_range_uses_line_starts(create_warehouse):
    """Test get_line_range() uses _line_starts index."""
    content = "L1\nL2\nL3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: O(1) lookup using _line_starts
    pytest.skip("Implement after Step 3: Helper methods")


def test_get_line_range_edge_cases(create_warehouse):
    """Test get_line_range() edge cases."""
    content = "Line 1\nLine 2"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected:
    # get_line_range(0, 0) returns []
    # get_line_range(0, 1) returns ["Line 1"]
    # get_line_range(0, 10) handles overflow gracefully
    pytest.skip("Implement after Step 3: Helper methods")


# ============================================================================
# get_token_text() Tests
# ============================================================================

def test_get_token_text_basic(create_warehouse):
    """Test get_token_text() extracts text for token."""
    content = "# Title"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected:
    # heading_idx = wh.by_type["heading_open"][0]
    # text = wh.get_token_text(heading_idx)
    # assert "Title" in text
    pytest.skip("Implement after Step 3: Helper methods")


def test_get_token_text_uses_map(create_warehouse):
    """Test get_token_text() uses token.map for line range."""
    content = "Paragraph\nspanning\nmultiple lines"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: Uses token.map to get [start_line, end_line]
    pytest.skip("Implement after Step 3: Helper methods")


def test_get_token_text_no_map(create_warehouse):
    """Test get_token_text() handles tokens without map."""
    content = "Test"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: Returns empty string or token.content if no map
    pytest.skip("Implement after Step 3: Helper methods")


# ============================================================================
# Integration Tests
# ============================================================================

def test_helper_methods_together(create_warehouse):
    """Test helper methods work together correctly."""
    content = "# Title\n\n[link](url)\n\nParagraph"
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: Use find_close, text_between, etc. in combination
    # link_open_idx = wh.by_type["link_open"][0]
    # link_close_idx = wh.find_close(link_open_idx)
    # link_text = wh.text_between(link_open_idx, link_close_idx)
    # assert "link" in link_text
    pytest.skip("Implement after Step 3: Helper methods")


def test_helper_methods_performance(create_warehouse):
    """Test helper methods are O(1) or O(log N)."""
    content = "# Title\n\n" + "Line\n" * 1000
    wh = create_warehouse(content)

    # TODO: Implement after Step 3 completes
    # Expected: find_close, find_parent, find_children are O(1)
    # get_line_range is O(lines requested)
    pytest.skip("Implement after Step 3: Helper methods")
