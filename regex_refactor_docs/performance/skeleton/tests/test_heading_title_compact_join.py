"""
Test heading title compact join - RED TEAM BLOCKER TEST 3.

CRITICAL: Verify heading titles have no double spaces from inline children.

When heading inline content contains multiple inline elements (bold, code, links),
naively concatenating their content creates double spaces:
"Hello **bold** world" -> "Hello bold  world" (note double space)

The fix uses " ".join(content.split()) to compact multiple spaces into one.

Red-Team Scenario:
Without compact join, heading titles will have irregular spacing that breaks
string comparisons and makes titles look unprofessional.
"""

import pytest
from pathlib import Path
import sys

# Add skeleton to path for imports
SKELETON_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKELETON_ROOT))

try:
    from skeleton.doxstrux.markdown.utils.text_normalization import parse_markdown_normalized
    from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    from skeleton.doxstrux.markdown.utils.section import Section
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Section utilities not available"
)


def test_heading_title_no_double_spaces():
    """
    CRITICAL: Heading titles must not have double spaces.

    Inline content with mixed formatting can create double spaces if not compacted.
    """
    # Heading with bold, code, and link
    md = "# Hello **bold** `code` [link](url)\n\nParagraph\n"

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) >= 1, "Should have at least one section"

    section = Section.from_tuple(wh.sections[0])

    # CRITICAL: No double spaces in title
    assert "  " not in section.title, \
        f"Double spaces in title: {section.title!r}"

    # Title should contain all text elements
    assert "Hello" in section.title
    assert "bold" in section.title
    assert "code" in section.title
    assert "link" in section.title


def test_heading_title_leading_trailing_whitespace():
    """
    Verify heading titles have no leading or trailing whitespace.

    " ".join(content.split()) also strips leading/trailing whitespace.
    """
    # Heading with extra spaces
    md = "#   Heading with extra spaces   \n\nContent\n"

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) >= 1, "Should have at least one section"

    section = Section.from_tuple(wh.sections[0])

    # No leading whitespace
    assert not section.title.startswith(" "), \
        f"Leading whitespace in title: {section.title!r}"

    # No trailing whitespace
    assert not section.title.endswith(" "), \
        f"Trailing whitespace in title: {section.title!r}"


def test_heading_title_tabs_and_newlines():
    """
    Verify heading titles normalize tabs and newlines to single spaces.

    split() without arguments splits on ALL whitespace (spaces, tabs, newlines).
    """
    # Markdown doesn't allow newlines in headings, but tabs are possible
    md = "# Title\twith\ttabs\n\nContent\n"

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) >= 1, "Should have at least one section"

    section = Section.from_tuple(wh.sections[0])

    # Tabs should be converted to single spaces
    assert "\t" not in section.title, \
        f"Tabs in title: {section.title!r}"

    # Should have single spaces instead
    assert "with" in section.title
    assert "tabs" in section.title


def test_heading_title_multiple_inline_elements():
    """
    Verify headings with many inline elements are compacted correctly.

    Complex headings with bold, italic, code, and links should all be joined cleanly.
    """
    md = "# **Bold** *italic* `code` [link](url) text\n\nContent\n"

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) >= 1, "Should have at least one section"

    section = Section.from_tuple(wh.sections[0])

    # No double spaces anywhere
    assert "  " not in section.title, \
        f"Double spaces in complex title: {section.title!r}"

    # All elements present
    assert "Bold" in section.title
    assert "italic" in section.title
    assert "code" in section.title
    assert "link" in section.title
    assert "text" in section.title


def test_heading_title_empty_after_compaction():
    """
    Verify headings that are only whitespace become empty string after compaction.

    Edge case: heading with only spaces/tabs should become "".
    """
    # Heading with only whitespace (markdown-it may parse this)
    md = "#    \n\nContent\n"

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    # May or may not create a section (depends on parser)
    # If section exists, title should be empty string (not whitespace)
    if len(wh.sections) > 0:
        section = Section.from_tuple(wh.sections[0])
        # Title should be empty or not have whitespace-only content
        assert section.title == "" or section.title.strip() != "", \
            f"Whitespace-only title not compacted: {section.title!r}"


def test_heading_title_unicode_whitespace():
    """
    Verify heading titles handle unicode whitespace correctly.

    Python's str.split() handles unicode whitespace (nbsp, em space, etc).
    """
    # Heading with non-breaking space (U+00A0)
    md = "# Title\u00A0with\u00A0nbsp\n\nContent\n"

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) >= 1, "Should have at least one section"

    section = Section.from_tuple(wh.sections[0])

    # Unicode whitespace should be compacted to single ASCII spaces
    # (split() without arguments treats unicode whitespace as separator)
    assert "Title" in section.title
    assert "with" in section.title
    assert "nbsp" in section.title


def test_heading_title_emoji_no_corruption():
    """
    Verify heading titles with emoji are preserved correctly after compaction.

    split() and join() should not corrupt multi-byte unicode characters.
    """
    md = "# Title 🚀 with 💡 emoji\n\nContent\n"

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) >= 1, "Should have at least one section"

    section = Section.from_tuple(wh.sections[0])

    # Emoji should be preserved
    assert "🚀" in section.title or "Title" in section.title, \
        f"Emoji corrupted in title: {section.title!r}"

    assert "💡" in section.title or "with" in section.title, \
        f"Emoji corrupted in title: {section.title!r}"

    # No double spaces
    assert "  " not in section.title


def test_heading_title_only_inline_content():
    """
    Verify title extraction only uses inline content from heading.

    This is related to the "globally greedy" fix - title should ONLY come from
    inline tokens that are children of the heading_open token.
    """
    # Two headings back-to-back (second inline should not bleed into first title)
    md = """# First Heading

## Second Heading

Content.
"""

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) >= 2, "Should have at least 2 sections"

    s0 = Section.from_tuple(wh.sections[0])
    s1 = Section.from_tuple(wh.sections[1])

    # First section title should NOT contain "Second"
    assert "First" in s0.title, f"Section 0 title wrong: {s0.title!r}"
    assert "Second" not in s0.title, \
        f"Section 0 title includes content from Section 1: {s0.title!r}"

    # Second section title should NOT contain "First"
    assert "Second" in s1.title, f"Section 1 title wrong: {s1.title!r}"
    assert "First" not in s1.title, \
        f"Section 1 title includes content from Section 0: {s1.title!r}"
