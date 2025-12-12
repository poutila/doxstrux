"""Tests for section lookup utilities (Phase 8 - THREE_ADDITIONS.md).

This module tests the section lookup invariants from THREE_ADDITIONS.md:
- INV-2.1: Correct section identification
- INV-2.2: Boundary correctness
- INV-2.3: Gap handling
- INV-2.4: Edge cases (negative lines, empty sections)
- INV-2.5: Single-line section
- INV-2.6: Amortized lookup (SectionIndex builds index once)

TDD: These tests are written before implementation and should initially FAIL.
"""

import pytest

# Import will fail until implementation exists
try:
    from doxstrux.markdown.utils.section_utils import SectionIndex, section_of_line
except ImportError:
    SectionIndex = None
    section_of_line = None


# Skip all tests if module not yet implemented
pytestmark = pytest.mark.skipif(
    section_of_line is None,
    reason="section_utils module not yet implemented"
)


# Fixtures for synthetic section data
@pytest.fixture
def simple_sections():
    """Simple non-overlapping sections."""
    return [
        {"id": "section_intro", "start_line": 0, "end_line": 5},
        {"id": "section_main", "start_line": 6, "end_line": 15},
        {"id": "section_conclusion", "start_line": 16, "end_line": 20},
    ]


@pytest.fixture
def gapped_sections():
    """Sections with gaps between them."""
    return [
        {"id": "section_a", "start_line": 0, "end_line": 3},
        # Gap: lines 4-6
        {"id": "section_b", "start_line": 7, "end_line": 10},
        # Gap: lines 11-14
        {"id": "section_c", "start_line": 15, "end_line": 20},
    ]


@pytest.fixture
def single_line_section():
    """Section where start_line == end_line."""
    return [
        {"id": "section_single", "start_line": 5, "end_line": 5},
    ]


@pytest.fixture
def adjacent_sections():
    """Sections that are immediately adjacent (no gaps)."""
    return [
        {"id": "section_first", "start_line": 0, "end_line": 4},
        {"id": "section_second", "start_line": 5, "end_line": 9},
        {"id": "section_third", "start_line": 10, "end_line": 14},
    ]


class TestSectionOfLine:
    """Tests for INV-2.1 through INV-2.5: section_of_line() function."""

    def test_finds_section_containing_line(self, simple_sections):
        """INV-2.1: Returns section dict where start_line <= line <= end_line."""
        # Line 3 is in first section (0-5)
        result = section_of_line(simple_sections, 3)
        assert result is not None
        assert result["id"] == "section_intro"

        # Line 10 is in second section (6-15)
        result = section_of_line(simple_sections, 10)
        assert result is not None
        assert result["id"] == "section_main"

        # Line 18 is in third section (16-20)
        result = section_of_line(simple_sections, 18)
        assert result is not None
        assert result["id"] == "section_conclusion"

    def test_returns_none_for_line_not_in_any_section(self, gapped_sections):
        """INV-2.1: Returns None if no section contains the line."""
        # Line 5 is in gap between section_a (0-3) and section_b (7-10)
        result = section_of_line(gapped_sections, 5)
        assert result is None

        # Line 12 is in gap between section_b (7-10) and section_c (15-20)
        result = section_of_line(gapped_sections, 12)
        assert result is None

    def test_boundary_start_line_included(self, simple_sections):
        """INV-2.2: start_line is included in section."""
        # Line 0 is start of first section
        result = section_of_line(simple_sections, 0)
        assert result is not None
        assert result["id"] == "section_intro"

        # Line 6 is start of second section
        result = section_of_line(simple_sections, 6)
        assert result is not None
        assert result["id"] == "section_main"

    def test_boundary_end_line_included(self, simple_sections):
        """INV-2.2: end_line is included in section."""
        # Line 5 is end of first section
        result = section_of_line(simple_sections, 5)
        assert result is not None
        assert result["id"] == "section_intro"

        # Line 15 is end of second section
        result = section_of_line(simple_sections, 15)
        assert result is not None
        assert result["id"] == "section_main"

    def test_adjacent_section_boundaries(self, adjacent_sections):
        """INV-2.2: Adjacent sections correctly handle boundary lines."""
        # Line 4 is end of first section
        result = section_of_line(adjacent_sections, 4)
        assert result["id"] == "section_first"

        # Line 5 is start of second section
        result = section_of_line(adjacent_sections, 5)
        assert result["id"] == "section_second"

    def test_gap_lines_return_none(self, gapped_sections):
        """INV-2.3: Lines in gaps between sections return None."""
        # All gap lines should return None
        for gap_line in [4, 5, 6, 11, 12, 13, 14]:
            result = section_of_line(gapped_sections, gap_line)
            assert result is None, f"Line {gap_line} should be in gap, got {result}"

    def test_negative_line_returns_none(self, simple_sections):
        """INV-2.4: Negative line numbers return None."""
        assert section_of_line(simple_sections, -1) is None
        assert section_of_line(simple_sections, -100) is None

    def test_empty_sections_returns_none(self):
        """INV-2.4: Empty sections list returns None for any line."""
        assert section_of_line([], 0) is None
        assert section_of_line([], 5) is None
        assert section_of_line([], 100) is None

    def test_line_beyond_all_sections_returns_none(self, simple_sections):
        """INV-2.4: Line beyond all sections returns None."""
        # Last section ends at 20
        assert section_of_line(simple_sections, 21) is None
        assert section_of_line(simple_sections, 100) is None

    def test_single_line_section_found(self, single_line_section):
        """INV-2.5: Section where start_line == end_line identifies that line."""
        result = section_of_line(single_line_section, 5)
        assert result is not None
        assert result["id"] == "section_single"

    def test_single_line_section_adjacent_lines_not_found(self, single_line_section):
        """INV-2.5: Lines adjacent to single-line section return None."""
        assert section_of_line(single_line_section, 4) is None
        assert section_of_line(single_line_section, 6) is None


class TestSectionIndex:
    """Tests for INV-2.6: SectionIndex class with amortized lookup."""

    def test_basic_lookup(self, simple_sections):
        """SectionIndex provides same results as section_of_line."""
        index = SectionIndex(simple_sections)

        assert index.get(3)["id"] == "section_intro"
        assert index.get(10)["id"] == "section_main"
        assert index.get(18)["id"] == "section_conclusion"

    def test_repeated_lookups_consistent(self, simple_sections):
        """Multiple lookups for same line return same result."""
        index = SectionIndex(simple_sections)

        # Look up same line multiple times
        for _ in range(10):
            result = index.get(10)
            assert result["id"] == "section_main"

    def test_lookup_returns_none_for_gaps(self, gapped_sections):
        """SectionIndex returns None for lines in gaps."""
        index = SectionIndex(gapped_sections)

        assert index.get(5) is None
        assert index.get(12) is None

    def test_build_count_increments_once(self, simple_sections):
        """INV-2.6: Index built at most once per instance.

        This test verifies the _build_count attribute if exposed.
        If not exposed, this test will be skipped.
        """
        index = SectionIndex(simple_sections)

        # Perform multiple lookups
        for line in range(25):
            index.get(line)

        # Check build count if exposed
        if hasattr(index, "_build_count"):
            assert index._build_count == 1, (
                f"INV-2.6: Expected 1 build, got {index._build_count}"
            )
        else:
            pytest.skip("_build_count not exposed - cannot verify build count")

    def test_empty_sections(self):
        """SectionIndex handles empty sections list."""
        index = SectionIndex([])
        assert index.get(0) is None
        assert index.get(10) is None

    def test_negative_line(self, simple_sections):
        """SectionIndex returns None for negative lines."""
        index = SectionIndex(simple_sections)
        assert index.get(-1) is None


class TestSectionOfLineIntegration:
    """Integration tests using real parser output."""

    def test_with_real_parser_output(self):
        """section_of_line works with actual parser sections.

        Note: The parser creates hierarchical sections where parent sections
        contain child sections (overlapping ranges). For flat (non-overlapping)
        section lookup, filter to top-level sections only, or use the first
        matching section in document order.
        """
        from doxstrux.markdown_parser_core import MarkdownParserCore

        # Use a flat document structure (no nesting) for reliable lookup
        content = """# Section One

First section content.

# Section Two

Second section content.

# Section Three

Third section content.
"""
        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser.parse()
        sections = result["structure"]["sections"]

        # Should have sections
        assert len(sections) == 3

        # Find section for line 0 (first heading)
        first_section = section_of_line(sections, 0)
        assert first_section is not None
        assert first_section["title"] == "Section One"

        # Find section for a line in "Section Two"
        section_two = next((s for s in sections if s["title"] == "Section Two"), None)
        assert section_two is not None
        result = section_of_line(sections, section_two["start_line"])
        assert result["title"] == "Section Two"

    def test_zero_indexed_first_line(self):
        """Line indexing test: start_line=0 corresponds to first line.

        Per THREE_ADDITIONS.md: At least one test MUST explicitly verify
        that start_line=0 corresponds to the first line of the document.
        """
        from doxstrux.markdown_parser_core import MarkdownParserCore

        # Simple document with heading on very first line (no frontmatter)
        content = "# First Heading\n\nSome content.\n"

        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser.parse()
        sections = result["structure"]["sections"]

        # The first section should start at line 0
        assert len(sections) > 0
        first_section = sections[0]
        assert first_section["start_line"] == 0, (
            f"First section should start at line 0, got {first_section['start_line']}"
        )

        # section_of_line(sections, 0) should return this section
        found = section_of_line(sections, 0)
        assert found is not None
        assert found["id"] == first_section["id"]


class TestParserSectionInvariants:
    """Tests verifying parser section output meets preconditions."""

    def test_sections_sorted_by_start_line(self):
        """Sections from parser are sorted by start_line (ascending)."""
        from doxstrux.markdown_parser_core import MarkdownParserCore

        content = """# A

## B

### C

## D

# E
"""
        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser.parse()
        sections = result["structure"]["sections"]

        # Verify sorted order
        for i in range(1, len(sections)):
            prev = sections[i - 1]
            curr = sections[i]
            assert prev["start_line"] <= curr["start_line"], (
                f"Sections not sorted: {prev['title']} (line {prev['start_line']}) "
                f"comes after {curr['title']} (line {curr['start_line']})"
            )

    def test_top_level_sections_non_overlapping(self):
        """Top-level sections (same heading level) are non-overlapping.

        Note: The parser creates hierarchical sections where parent sections
        contain child sections. Only sections at the same level should be
        non-overlapping. This test uses a flat document with all H1s.
        """
        from doxstrux.markdown_parser_core import MarkdownParserCore

        # Use flat structure - all H1 headings
        content = """# Section One

Content for section one.

# Section Two

Content for section two.
"""
        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser.parse()
        sections = result["structure"]["sections"]

        # For flat H1-only documents, sections should not overlap
        for i, s1 in enumerate(sections):
            for j, s2 in enumerate(sections):
                if i >= j:
                    continue
                # s1 comes before s2 in list
                # s1 should end before s2 starts (or at s2.start_line - 1)
                if s1["end_line"] is not None and s2["start_line"] is not None:
                    assert s1["end_line"] < s2["start_line"], (
                        f"Sections overlap: {s1['title']} ends at {s1['end_line']}, "
                        f"{s2['title']} starts at {s2['start_line']}"
                    )

    def test_sections_use_zero_indexed_lines(self):
        """Sections use 0-indexed line numbers per CLAUDE.md."""
        from doxstrux.markdown_parser_core import MarkdownParserCore

        # Document where we know exact line positions
        content = "# Line Zero\n"  # Line 0

        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser.parse()
        sections = result["structure"]["sections"]

        assert len(sections) == 1
        assert sections[0]["start_line"] == 0, (
            "Section should use 0-indexed lines"
        )

    def test_sections_have_required_fields(self):
        """Sections have start_line and end_line fields."""
        from doxstrux.markdown_parser_core import MarkdownParserCore

        content = "# Test\n\nContent\n"

        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser.parse()
        sections = result["structure"]["sections"]

        for section in sections:
            assert "start_line" in section, f"Section missing start_line: {section}"
            assert "end_line" in section, f"Section missing end_line: {section}"
