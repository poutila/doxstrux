"""Tests for polars-based GFM table detection.

Tests parse_gfm_table_line() and table classification (ragged, pure, malformed).
"""

import pytest
from doxstrux.markdown.extractors.tables import parse_gfm_table_line
from doxstrux.markdown_parser_core import MarkdownParserCore


class TestParseGfmTableLine:
    """Tests for parse_gfm_table_line() function."""

    @pytest.mark.parametrize("line,expected_cols,expected_cells", [
        # Basic valid lines
        ("| a | b | c |", 3, ["a", "b", "c"]),
        ("| single |", 1, ["single"]),
        ("| a | b |", 2, ["a", "b"]),
        # Empty cells
        ("| | |", 2, ["", ""]),
        ("| a | | c |", 3, ["a", "", "c"]),
        ("|||", 2, ["", ""]),
        # Whitespace handling
        ("|  spaced  |  out  |", 2, ["spaced", "out"]),
        ("| a|b |", 2, ["a", "b"]),
        # Escaped pipes
        (r"| a \| b | c |", 2, ["a | b", "c"]),
        (r"| \| | \| |", 2, ["|", "|"]),
    ])
    def test_valid_lines(self, line, expected_cols, expected_cells):
        """Valid GFM table lines must return correct column count and cells."""
        result = parse_gfm_table_line(line)
        assert result is not None, f"Line should be valid: {line}"
        col_count, cells = result
        assert col_count == expected_cols, f"Expected {expected_cols} columns, got {col_count}"
        assert cells == expected_cells, f"Expected cells {expected_cells}, got {cells}"

    @pytest.mark.parametrize("line", [
        # Missing leading pipe
        "a | b | c |",
        "no leading pipe |",
        # Missing trailing pipe
        "| a | b | c",
        "| no trailing pipe",
        # Both missing
        "a | b | c",
        "no pipes at all",
        # Empty/whitespace only
        "",
        "   ",
        "\t",
    ])
    def test_invalid_lines(self, line):
        """Invalid lines must return None."""
        result = parse_gfm_table_line(line)
        assert result is None, f"Line should be invalid: {line!r}"

    @pytest.mark.parametrize("line,expected_cols", [
        # Edge cases: valid format but 0 columns
        ("|", 0),
        ("||", 0),
    ])
    def test_edge_case_zero_columns(self, line, expected_cols):
        """Lines with |...| format but no content return 0 columns."""
        result = parse_gfm_table_line(line)
        assert result is not None, f"Line has valid format: {line!r}"
        col_count, cells = result
        assert col_count == expected_cols
        assert cells == []

    def test_blockquote_prefix_stripped(self):
        """Blockquote markers (>) should be stripped before parsing."""
        result = parse_gfm_table_line("> | a | b |")
        assert result is not None
        col_count, cells = result
        assert col_count == 2
        assert cells == ["a", "b"]

        # Nested blockquotes
        result = parse_gfm_table_line(">> | x | y | z |")
        assert result is not None
        col_count, cells = result
        assert col_count == 3

    def test_list_marker_stripped(self):
        """List markers (- *) should be stripped before parsing."""
        result = parse_gfm_table_line("- | a | b |")
        assert result is not None
        col_count, cells = result
        assert col_count == 2

        result = parse_gfm_table_line("* | x |")
        assert result is not None
        col_count, cells = result
        assert col_count == 1


class TestTableClassification:
    """Tests for table classification (is_pure, is_ragged, malformed_lines)."""

    def test_pure_table(self):
        """Pure table: all rows start/end with |, consistent columns."""
        md = """\
| Col1 | Col2 | Col3 |
|------|------|------|
| a    | b    | c    |
| d    | e    | f    |
"""
        parser = MarkdownParserCore(md)
        result = parser.parse()
        tables = result["structure"]["tables"]

        assert len(tables) == 1
        t = tables[0]
        assert t["is_pure"] is True
        assert t["is_ragged"] is False
        assert t["malformed_lines"] == []
        assert t["table_valid_md"] is True

    def test_ragged_table_different_column_counts(self):
        """Ragged table: rows have different column counts."""
        md = """\
| Col1 | Col2 |
|------|------|
| a    | b    |
| c    | d    | e    |
| f    |
"""
        parser = MarkdownParserCore(md)
        result = parser.parse()
        tables = result["structure"]["tables"]

        assert len(tables) == 1
        t = tables[0]
        assert t["is_ragged"] is True
        assert t["is_pure"] is False
        assert "source_col_counts" in t.get("is_ragged_meta", {})
        # Should have multiple unique column counts
        counts = t["is_ragged_meta"]["source_col_counts"]
        assert len(counts) > 1

    def test_malformed_table_missing_trailing_pipe(self):
        """Malformed: lines with pipes but not following |...| format."""
        md = """\
| Col1 | Col2 |
|------|------|
| a    | b    |
| c    | d
| e    | f    |
"""
        parser = MarkdownParserCore(md)
        result = parser.parse()
        tables = result["structure"]["tables"]

        assert len(tables) == 1
        t = tables[0]
        assert t["is_pure"] is False
        assert len(t["malformed_lines"]) > 0
        # Line 3 (0-indexed) should be malformed (missing trailing pipe)
        assert 3 in t["malformed_lines"]

    def test_malformed_table_missing_leading_pipe(self):
        """Malformed: lines missing leading pipe."""
        md = """\
| Col1 | Col2 |
|------|------|
| a    | b    |
c    | d    |
| e    | f    |
"""
        parser = MarkdownParserCore(md)
        result = parser.parse()
        tables = result["structure"]["tables"]

        assert len(tables) == 1
        t = tables[0]
        assert t["is_pure"] is False
        assert len(t["malformed_lines"]) > 0

    def test_table_with_escaped_pipes_is_pure(self):
        """Tables with escaped pipes should still be detected as pure."""
        md = r"""
| Command | Description |
|---------|-------------|
| a \| b  | pipe in cell |
| c       | normal       |
"""
        parser = MarkdownParserCore(md)
        result = parser.parse()
        tables = result["structure"]["tables"]

        assert len(tables) == 1
        t = tables[0]
        assert t["is_pure"] is True
        assert t["is_ragged"] is False

    def test_empty_cells_not_ragged(self):
        """Empty cells should not cause ragged detection."""
        md = """\
| Col1 | Col2 |
|------|------|
|      | b    |
| a    |      |
|      |      |
"""
        parser = MarkdownParserCore(md)
        result = parser.parse()
        tables = result["structure"]["tables"]

        assert len(tables) == 1
        t = tables[0]
        assert t["is_ragged"] is False
        assert t["is_pure"] is True

    def test_brutal_tables_file(self):
        """Integration test against md_brutal_tables.md known results."""
        from doxstrux import parse_markdown_file

        result = parse_markdown_file("tools/test_mds/14_tables/md_brutal_tables.md")
        tables = result["structure"]["tables"]

        assert len(tables) == 10

        # Table 8 (lines 176-180) should be pure
        t8 = tables[8]
        assert t8["start_line"] == 176
        assert t8["is_pure"] is True
        assert t8["is_ragged"] is False
        assert t8["malformed_lines"] == []

        # Table 9 (lines 186-191) should be pure
        t9 = tables[9]
        assert t9["start_line"] == 186
        assert t9["is_pure"] is True
        assert t9["is_ragged"] is False
        assert t9["malformed_lines"] == []

        # Table 2 (lines 68-88) should be ragged
        t2 = tables[2]
        assert t2["start_line"] == 68
        assert t2["is_ragged"] is True
        assert t2["is_pure"] is False
        assert set(t2["is_ragged_meta"]["source_col_counts"]) == {1, 2, 4}

        # Table 7 (lines 158-166) should be ragged
        t7 = tables[7]
        assert t7["start_line"] == 158
        assert t7["is_ragged"] is True
        assert t7["is_pure"] is False
        assert set(t7["is_ragged_meta"]["source_col_counts"]) == {3, 4}

        # Tables 0-6 should have malformed lines (continuation lines)
        for i in range(7):
            t = tables[i]
            assert t["is_pure"] is False, f"Table {i} should not be pure"

    def test_separator_line_not_counted(self):
        """Separator line (|---|---|) should not affect column counting."""
        md = """\
| A | B |
|---|---|
| 1 | 2 |
"""
        parser = MarkdownParserCore(md)
        result = parser.parse()
        tables = result["structure"]["tables"]

        assert len(tables) == 1
        t = tables[0]
        # Should be pure - separator line skipped in column count
        assert t["is_pure"] is True
        assert t["is_ragged"] is False
