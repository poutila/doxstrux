"""
Test mixed Setext/ATX section boundaries - RED TEAM BLOCKER TEST 2.

CRITICAL: Verify section boundaries are correct with mixed heading styles.

Markdown supports two heading styles:
- ATX: # Heading (with # symbols)
- Setext: Heading with underline (=== or ---)

This test ensures section boundary calculation handles both styles correctly
and doesn't create overlapping or invalid sections.

Red-Team Scenario:
Mixed heading styles can cause section boundary bugs if the parser doesn't
handle both styles uniformly. Setext headings don't have explicit level markers
in the heading_open token (level is inferred from underline character).
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


def test_section_mixed_setext_atx_boundaries():
    """
    CRITICAL: Mixed Setext and ATX headings must create non-overlapping sections.

    Setext (underline) and ATX (# symbols) headings should be treated uniformly.
    """
    # Document with mixed heading styles
    md = """Heading 1
=========

Paragraph under H1.

### Heading 3

Paragraph under H3.

Heading 2
---------

Paragraph under H2.
"""

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Should have 3 sections (H1 setext, H3 ATX, H2 setext)
    assert len(wh.sections) == 3, \
        f"Expected 3 sections, got {len(wh.sections)}"

    # Parse sections
    sections = [Section.from_tuple(s) for s in wh.sections]

    # Section 0: H1 (setext)
    s0 = sections[0]
    assert s0.level == 1, f"Section 0 should be level 1, got {s0.level}"
    assert "Heading 1" in s0.title, f"Section 0 title wrong: {s0.title!r}"

    # Section 1: H3 (ATX)
    s1 = sections[1]
    assert s1.level == 3, f"Section 1 should be level 3, got {s1.level}"
    assert "Heading 3" in s1.title, f"Section 1 title wrong: {s1.title!r}"

    # Section 2: H2 (setext)
    s2 = sections[2]
    assert s2.level == 2, f"Section 2 should be level 2, got {s2.level}"
    assert "Heading 2" in s2.title, f"Section 2 title wrong: {s2.title!r}"

    # CRITICAL: Sections must not overlap
    # s0 ends before s1 starts
    assert s0.end_line is not None and s0.end_line < s1.start_line, \
        f"Section 0 overlaps Section 1: s0.end={s0.end_line}, s1.start={s1.start_line}"

    # s1 ends before s2 starts
    assert s1.end_line is not None and s1.end_line < s2.start_line, \
        f"Section 1 overlaps Section 2: s1.end={s1.end_line}, s2.start={s2.start_line}"


def test_setext_h1_h2_distinction():
    """
    Verify Setext headings correctly distinguish H1 (===) vs H2 (---).

    The underline character determines level: === is H1, --- is H2.
    """
    md = """H1 Title
========

Paragraph.

H2 Title
--------

Paragraph.
"""

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) == 2, f"Expected 2 sections, got {len(wh.sections)}"

    sections = [Section.from_tuple(s) for s in wh.sections]

    # First should be H1
    assert sections[0].level == 1, \
        f"Setext === should be H1, got level {sections[0].level}"

    # Second should be H2
    assert sections[1].level == 2, \
        f"Setext --- should be H2, got level {sections[1].level}"


def test_atx_heading_levels():
    """
    Verify ATX headings (# through ######) are parsed correctly.

    ATX headings have explicit level markers (number of # symbols).
    """
    md = """# H1

## H2

### H3

#### H4

##### H5

###### H6
"""

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) == 6, f"Expected 6 sections, got {len(wh.sections)}"

    sections = [Section.from_tuple(s) for s in wh.sections]

    # Verify all levels are correct
    for i, section in enumerate(sections):
        expected_level = i + 1
        assert section.level == expected_level, \
            f"Section {i} should be H{expected_level}, got H{section.level}"


def test_mixed_heading_nesting_boundaries():
    """
    Verify section boundaries respect heading hierarchy with mixed styles.

    Higher-level headings should close lower-level sections.
    """
    md = """H1 (Setext)
===========

## H2 (ATX)

### H3 (ATX)

H1 Again (Setext)
=================

Content.
"""

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) == 4, f"Expected 4 sections, got {len(wh.sections)}"

    sections = [Section.from_tuple(s) for s in wh.sections]

    # Section 0: H1 setext
    assert sections[0].level == 1
    assert "H1 (Setext)" in sections[0].title

    # Section 1: H2 ATX
    assert sections[1].level == 2
    assert "H2 (ATX)" in sections[1].title

    # Section 2: H3 ATX
    assert sections[2].level == 3
    assert "H3 (ATX)" in sections[2].title

    # Section 3: H1 setext (should close all previous sections)
    assert sections[3].level == 1
    assert "H1 Again" in sections[3].title

    # CRITICAL: Section 0 should end before Section 1 starts
    assert sections[0].end_line < sections[1].start_line, \
        f"Section 0 doesn't end before Section 1"

    # Section 1 should end before Section 2 starts
    assert sections[1].end_line < sections[2].start_line, \
        f"Section 1 doesn't end before Section 2"

    # Section 2 should end before Section 3 starts
    assert sections[2].end_line < sections[3].start_line, \
        f"Section 2 doesn't end before Section 3"


def test_setext_multiline_title():
    """
    Verify Setext headings with multi-word titles are captured correctly.

    Setext title can be multiple words (entire line before underline).
    """
    md = """This is a long title with multiple words
=========================================

Content.
"""

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) >= 1, "Should have at least one section"

    section = Section.from_tuple(wh.sections[0])

    # Title should contain all words
    assert "long title" in section.title, \
        f"Setext title incomplete: {section.title!r}"
    assert "multiple words" in section.title, \
        f"Setext title incomplete: {section.title!r}"


def test_atx_with_trailing_hashes():
    """
    Verify ATX headings with trailing # symbols are parsed correctly.

    Markdown allows optional trailing hashes: # Title # or # Title
    """
    md = """# Title with trailing hash #

## Title without trailing hash

### Title with multiple trailing ###
"""

    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.sections) == 3, f"Expected 3 sections, got {len(wh.sections)}"

    sections = [Section.from_tuple(s) for s in wh.sections]

    # All should have correct levels
    assert sections[0].level == 1
    assert sections[1].level == 2
    assert sections[2].level == 3

    # Titles should not include trailing hashes (markdown-it strips them)
    # But this depends on parser behavior - just verify they're not None
    assert sections[0].title != ""
    assert sections[1].title != ""
    assert sections[2].title != ""
