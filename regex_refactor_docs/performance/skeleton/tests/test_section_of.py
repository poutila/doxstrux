"""
Test section_of() binary search implementation (Step 2).

This test file is created BEFORE refactoring to provide
immediate verification as section_of() is implemented.

Tests cover:
- O(log N) complexity verification
- Accuracy of line → section mapping
- Edge cases (line 0, EOF, between sections)
- Performance benchmarking
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
# Basic Functionality Tests
# ============================================================================

def test_section_of_returns_section_tuple(create_warehouse):
    """Test section_of() returns correct tuple structure."""
    content = "# Title\n\nContent line 1\nContent line 2"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: section_of(line) returns (start_line, end_line, token_idx, level, title)
    # sect = wh.section_of(2)  # Line with "Content line 1"
    # assert isinstance(sect, tuple)
    # assert len(sect) == 5
    # assert sect[4] == "Title"  # Title field
    pytest.skip("Implement after Step 2: section_of() binary search")


def test_section_of_none_when_no_sections(create_warehouse):
    """Test section_of() returns None when no headings exist."""
    content = "Just a paragraph\nNo headings here"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: section_of(0) returns None (no sections)
    pytest.skip("Implement after Step 2: section_of() binary search")


# ============================================================================
# Accuracy Tests
# ============================================================================

def test_section_of_accuracy_single_section(create_warehouse):
    """Test section_of() correctly maps lines to single section."""
    content = "# Title\n\nLine 2\nLine 3\nLine 4"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: All lines map to "Title" section
    # for line in range(5):
    #     sect = wh.section_of(line)
    #     assert sect[4] == "Title"
    pytest.skip("Implement after Step 2: section_of() binary search")


def test_section_of_accuracy_multiple_sections(create_warehouse):
    """Test section_of() correctly maps lines to different sections."""
    content = "# Section 1\n\nContent 1\n\n# Section 2\n\nContent 2"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected:
    # sect = wh.section_of(2)  # "Content 1"
    # assert sect[4] == "Section 1"
    # sect = wh.section_of(6)  # "Content 2"
    # assert sect[4] == "Section 2"
    pytest.skip("Implement after Step 2: section_of() binary search")


def test_section_of_accuracy_nested_headings(create_warehouse):
    """Test section_of() with nested heading levels."""
    content = "# H1\n\n## H2\n\nContent under H2\n\n### H3\n\nContent under H3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: Each line maps to closest preceding heading
    # sect = wh.section_of(4)  # "Content under H2"
    # assert sect[3] == 2  # Level 2
    # assert sect[4] == "H2"
    # sect = wh.section_of(8)  # "Content under H3"
    # assert sect[3] == 3  # Level 3
    # assert sect[4] == "H3"
    pytest.skip("Implement after Step 2: section_of() binary search")


# ============================================================================
# Edge Case Tests
# ============================================================================

def test_section_of_line_zero(create_warehouse):
    """Test section_of() handles line 0 correctly."""
    content = "# Title\n\nContent"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: section_of(0) returns section starting at line 0
    pytest.skip("Implement after Step 2: section_of() binary search")


def test_section_of_eof(create_warehouse):
    """Test section_of() handles EOF line correctly."""
    content = "# Title\n\nContent\nLast line"
    wh = create_warehouse(content)
    num_lines = content.count('\n') + 1

    # TODO: Implement after Step 2 completes
    # Expected: section_of(num_lines - 1) returns last section
    pytest.skip("Implement after Step 2: section_of() binary search")


def test_section_of_between_sections(create_warehouse):
    """Test section_of() for blank lines between sections."""
    content = "# Section 1\n\nContent 1\n\n\n\n# Section 2"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: Blank lines (4, 5) map to Section 1 (not Section 2)
    # sect = wh.section_of(4)
    # assert sect[4] == "Section 1"
    pytest.skip("Implement after Step 2: section_of() binary search")


def test_section_of_invalid_line_number(create_warehouse):
    """Test section_of() handles invalid line numbers gracefully."""
    content = "# Title\n\nContent"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: section_of(-1) returns None or raises ValueError
    # Expected: section_of(1000) returns None or last section
    pytest.skip("Implement after Step 2: section_of() binary search")


# ============================================================================
# Binary Search Complexity Tests
# ============================================================================

def test_section_of_binary_search_complexity(create_warehouse):
    """Test section_of() uses binary search (O(log N))."""
    # Create document with many sections
    sections = [f"# Section {i}\n\nContent {i}\n\n" for i in range(1000)]
    content = "".join(sections)
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: Measure lookup time, verify O(log N)
    # Time 10 sections: t1
    # Time 1000 sections: t2
    # assert t2 / t1 < 3  # log(1000)/log(10) ≈ 3
    pytest.skip("Implement after Step 2: section_of() binary search")


def test_section_of_performance_benchmark(create_warehouse):
    """Test section_of() lookup is fast (<1ms for 10K lines)."""
    # Create large document
    content = "# Title\n\n" + "Line\n" * 10000
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: 1000 lookups complete in <1 second
    # start = time.perf_counter()
    # for i in range(1000):
    #     wh.section_of(i * 10)
    # elapsed = time.perf_counter() - start
    # assert elapsed < 1.0  # <1ms per lookup
    pytest.skip("Implement after Step 2: section_of() binary search")


# ============================================================================
# Caching Tests
# ============================================================================

def test_section_of_uses_cache(create_warehouse):
    """Test section_of() caches sorted section list."""
    content = "# S1\n\n# S2\n\n# S3"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: _section_starts_sorted is built once and reused
    # First call builds cache
    # wh.section_of(0)
    # assert hasattr(wh, '_section_starts_sorted')
    # Second call reuses cache (verify by checking id())
    pytest.skip("Implement after Step 2: section_of() binary search")


def test_section_of_cache_not_rebuilt(create_warehouse):
    """Test section_of() doesn't rebuild cache on repeated calls."""
    content = "# Title\n\nContent"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: Cache built once, not on every call
    # wh.section_of(0)
    # cache_id = id(wh._section_starts_sorted)
    # wh.section_of(1)
    # assert id(wh._section_starts_sorted) == cache_id  # Same object
    pytest.skip("Implement after Step 2: section_of() binary search")


# ============================================================================
# Integration Tests
# ============================================================================

def test_section_of_with_real_content(create_warehouse):
    """Test section_of() with realistic markdown document."""
    content = """# Introduction

This is the introduction section with multiple paragraphs.

More content here.

## Background

Subsection content.

# Methods

## Experimental Setup

Details here.

## Results

Data and analysis.

# Conclusion

Final thoughts.
"""
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: Verify section mapping for various lines
    # Line with "More content" → "Introduction"
    # Line with "Details here" → "Experimental Setup"
    # Line with "Final thoughts" → "Conclusion"
    pytest.skip("Implement after Step 2: section_of() binary search")


def test_section_of_empty_sections(create_warehouse):
    """Test section_of() with empty sections (heading followed by heading)."""
    content = "# Section 1\n# Section 2\n\nContent"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: Empty Section 1 still has valid range
    # sect = wh.section_of(0)
    # assert sect[4] == "Section 1"
    # sect = wh.section_of(1)
    # assert sect[4] == "Section 2"
    pytest.skip("Implement after Step 2: section_of() binary search")


# ============================================================================
# Regression Tests
# ============================================================================

def test_section_of_matches_existing_implementation(create_warehouse):
    """Test section_of() matches behavior of existing section_utils.py."""
    content = "# H1\n\n## H2\n\nContent\n\n### H3\n\nMore"
    wh = create_warehouse(content)

    # TODO: Implement after Step 2 completes
    # Expected: Compare output with skeleton/doxstrux/markdown/utils/section_utils.py
    # If section_utils.section_of_with_binary_search exists, verify identical output
    pytest.skip("Implement after Step 2: section_of() binary search")
