"""
Test TokenWarehouse index building (Step 1).

This test file is created BEFORE refactoring to provide
immediate verification as indices are implemented.

Tests cover:
- by_type index (all token types)
- pairs index (open→close mapping)
- pairs_rev index (close→open bidirectional mapping)
- children index (parent→children mapping)
- parents index (child→parent mapping)
- sections index (heading boundaries)
- Unicode NFC normalization
- CRLF→LF normalization
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
# by_type Index Tests
# ============================================================================

def test_by_type_index_populated(create_warehouse):
    """Test by_type index contains all token types."""
    content = "# Hello\n\nWorld [link](url)"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: by_type dict with keys like "heading_open", "paragraph_open", "link_open"
    # Each key maps to list of token indices
    pytest.skip("Implement after Step 1: Build indices")


def test_by_type_index_correct_indices(create_warehouse):
    """Test by_type index maps to correct token positions."""
    content = "# H1\n## H2\n### H3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: by_type["heading_open"] = [idx1, idx2, idx3] where wh.tokens[idx1].tag == "h1"
    pytest.skip("Implement after Step 1: Build indices")


# ============================================================================
# pairs Index Tests (open→close)
# ============================================================================

def test_pairs_index_populated(create_warehouse):
    """Test pairs index maps all opening tokens to closing tokens."""
    content = "# Hello"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: pairs[idx_heading_open] = idx_heading_close
    pytest.skip("Implement after Step 1: Build indices")


def test_pairs_index_nested_structures(create_warehouse):
    """Test pairs index handles nested structures correctly."""
    content = "- Item 1\n  - Nested item\n    - Deeply nested"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: All list_open→list_close pairs mapped correctly
    pytest.skip("Implement after Step 1: Build indices")


# ============================================================================
# pairs_rev Index Tests (close→open, bidirectional)
# ============================================================================

def test_pairs_bidirectional(create_warehouse):
    """Test bidirectional pairs (NEW - Step 1.7).

    Both pairs[open]=close AND pairs_rev[close]=open should exist.
    """
    content = "# Hello"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1.7 completes
    # Expected:
    # open_idx = wh.by_type["heading_open"][0]
    # close_idx = wh.pairs[open_idx]
    # assert wh.pairs_rev[close_idx] == open_idx
    pytest.skip("Implement after Step 1.7: Bidirectional pairs")


def test_pairs_rev_all_closing_tokens(create_warehouse):
    """Test pairs_rev contains all closing tokens."""
    content = "# H1\n\n**bold** [link](url)"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1.7 completes
    # Expected: Every *_close token has entry in pairs_rev
    pytest.skip("Implement after Step 1.7: Bidirectional pairs")


# ============================================================================
# children Index Tests (NEW - Step 1.8)
# ============================================================================

def test_children_index_populated(create_warehouse):
    """Test children index for nested structures (NEW - Step 1.8)."""
    content = "- Item 1\n  - Nested item"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1.8 completes
    # Expected:
    # list_open_idx = wh.by_type["bullet_list_open"][0]
    # assert list_open_idx in wh.children
    # assert len(wh.children[list_open_idx]) > 0
    pytest.skip("Implement after Step 1.8: Children index")


def test_children_index_nested_lists(create_warehouse):
    """Test children index handles deeply nested lists."""
    content = "- L1\n  - L2\n    - L3\n      - L4"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1.8 completes
    # Expected: Each list_open has children list with nested list indices
    pytest.skip("Implement after Step 1.8: Children index")


# ============================================================================
# parents Index Tests
# ============================================================================

def test_parents_index_populated(create_warehouse):
    """Test parents index maps all tokens to containing token."""
    content = "# Hello\n\nWorld"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: Every token (except root) has parent entry
    pytest.skip("Implement after Step 1: Build indices")


def test_parents_index_nested_content(create_warehouse):
    """Test parents index handles nested content correctly."""
    content = "> Blockquote\n> - List item"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: List item parent is blockquote
    pytest.skip("Implement after Step 1: Build indices")


# ============================================================================
# sections Index Tests
# ============================================================================

def test_sections_index_populated(create_warehouse):
    """Test sections index contains heading boundaries."""
    content = "# Title\n\nContent\n\n## Subtitle"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: sections = [(start_line, end_line, token_idx, level, title), ...]
    # assert len(wh.sections) == 2  # 2 headings
    pytest.skip("Implement after Step 1: Build indices")


def test_sections_index_structure(create_warehouse):
    """Test sections index has correct tuple structure."""
    content = "# Title\n\nContent"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: sect = wh.sections[0]
    # assert sect[3] == 1  # Level 1
    # assert sect[4] == "Title"  # Title extracted
    pytest.skip("Implement after Step 1: Build indices")


# ============================================================================
# Unicode Normalization Tests (NEW - Step 1.9)
# ============================================================================

def test_unicode_normalization(create_warehouse):
    """Test Unicode NFC normalization (NEW - Step 1.9).

    Composed vs decomposed characters should normalize to same form.
    """
    # Composed é (single code point U+00E9)
    content_composed = "café"

    # Decomposed é (e + combining acute accent U+0065 U+0301)
    content_decomposed = "café"  # NFD form

    # TODO: Implement after Step 1.9 completes
    # Expected:
    # wh1 = create_warehouse(content_composed)
    # wh2 = create_warehouse(content_decomposed)
    # assert wh1.text == wh2.text  # Both normalized to NFC
    pytest.skip("Implement after Step 1.9: Unicode normalization")


def test_unicode_normalization_consistency(create_warehouse):
    """Test Unicode normalization is applied consistently."""
    content = "naïve résumé"  # Mix of composed characters
    wh = create_warehouse(content)

    # TODO: Implement after Step 1.9 completes
    # Expected: All text normalized to NFC form
    # Verify with: unicodedata.is_normalized('NFC', wh.text)
    pytest.skip("Implement after Step 1.9: Unicode normalization")


# ============================================================================
# CRLF Normalization Tests (NEW - Step 1.10)
# ============================================================================

def test_crlf_normalization(create_warehouse):
    """Test CRLF→LF normalization (NEW - Step 1.10)."""
    content_crlf = "Line 1\r\nLine 2\r\n"
    content_lf = "Line 1\nLine 2\n"

    # TODO: Implement after Step 1.10 completes
    # Expected:
    # wh1 = create_warehouse(content_crlf)
    # wh2 = create_warehouse(content_lf)
    # assert wh1._line_starts == wh2._line_starts
    # assert wh1.text == wh2.text  # CRLF converted to LF
    pytest.skip("Implement after Step 1.10: CRLF normalization")


def test_crlf_normalization_mixed(create_warehouse):
    """Test CRLF normalization with mixed line endings."""
    content = "Line 1\r\nLine 2\nLine 3\r\n"  # Mix of CRLF and LF
    wh = create_warehouse(content)

    # TODO: Implement after Step 1.10 completes
    # Expected: All normalized to LF
    # assert "\r" not in wh.text
    pytest.skip("Implement after Step 1.10: CRLF normalization")


# ============================================================================
# _line_starts Index Tests
# ============================================================================

def test_line_starts_populated(create_warehouse):
    """Test _line_starts contains byte offsets for each line."""
    content = "Line 1\nLine 2\nLine 3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: _line_starts = [0, 7, 14] (byte offsets)
    pytest.skip("Implement after Step 1: Build indices")


def test_line_starts_accuracy(create_warehouse):
    """Test _line_starts byte offsets are accurate."""
    content = "# Title\n\nContent\nMore"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: Can reconstruct lines using offsets
    # line_text = wh.text[wh._line_starts[0]:wh._line_starts[1]]
    # assert line_text.strip() == "# Title"
    pytest.skip("Implement after Step 1: Build indices")


# ============================================================================
# Integration Tests
# ============================================================================

def test_all_indices_single_pass(create_warehouse):
    """Test all indices built in single pass over tokens."""
    content = "# Title\n\n- Item 1\n  - Nested\n\n[link](url)"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: All 7 indices populated (by_type, pairs, pairs_rev, children, parents, sections, _line_starts)
    # Verify: len(wh.by_type) > 0, len(wh.pairs) > 0, etc.
    pytest.skip("Implement after Step 1: Build indices")


def test_indices_consistency(create_warehouse):
    """Test indices are mutually consistent."""
    content = "# H1\n## H2\n### H3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 1 completes
    # Expected: Cross-validate indices
    # For each pair in wh.pairs: wh.pairs_rev[close] == open
    # For each child in wh.children[parent]: wh.parents[child] == parent
    pytest.skip("Implement after Step 1: Build indices")
