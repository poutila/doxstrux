"""Unit tests for line_utils.py.

Tests for line slicing and manipulation utilities extracted from markdown_parser_core.py
during Phase 7 modularization (Task 7.3).
"""

import pytest
from doxstrux.markdown.utils import line_utils


class TestSliceLines:
    """Tests for slice_lines() function."""

    def test_basic_slicing(self):
        """Should slice lines using markdown-it convention."""
        lines = ["line0", "line1", "line2", "line3", "line4"]
        result = line_utils.slice_lines(lines, 1, 3)
        assert result == ["line1", "line2"]

    def test_single_line(self):
        """Should handle single-line slice."""
        lines = ["line0", "line1", "line2"]
        result = line_utils.slice_lines(lines, 1, 2)
        assert result == ["line1"]

    def test_none_start(self):
        """Should return empty list if start_line is None."""
        lines = ["line0", "line1"]
        result = line_utils.slice_lines(lines, None, 1)
        assert result == []

    def test_none_end(self):
        """Should return empty list if end_line is None."""
        lines = ["line0", "line1"]
        result = line_utils.slice_lines(lines, 0, None)
        assert result == []

    def test_out_of_bounds_start(self):
        """Should return empty list if start_line is out of bounds."""
        lines = ["line0", "line1"]
        result = line_utils.slice_lines(lines, 5, 10)
        assert result == []

    def test_negative_start(self):
        """Should return empty list if start_line is negative."""
        lines = ["line0", "line1"]
        result = line_utils.slice_lines(lines, -1, 1)
        assert result == []

    def test_end_before_start(self):
        """Should return empty list if end <= start."""
        lines = ["line0", "line1", "line2"]
        result = line_utils.slice_lines(lines, 2, 2)
        assert result == []

    def test_end_before_start_reversed(self):
        """Should return empty list if end < start."""
        lines = ["line0", "line1", "line2"]
        result = line_utils.slice_lines(lines, 2, 1)
        assert result == []


class TestSliceLinesRaw:
    """Tests for slice_lines_raw() function."""

    def test_basic_raw_slicing(self):
        """Should return joined string with newlines."""
        lines = ["first", "second", "third"]
        result = line_utils.slice_lines_raw(lines, 0, 2)
        assert result == "first\nsecond"

    def test_single_line_raw(self):
        """Should return single line without trailing newline."""
        lines = ["first", "second", "third"]
        result = line_utils.slice_lines_raw(lines, 1, 2)
        assert result == "second"

    def test_empty_result_raw(self):
        """Should return empty string if slice is empty."""
        lines = ["first", "second"]
        result = line_utils.slice_lines_raw(lines, None, 1)
        assert result == ""

    def test_all_lines_raw(self):
        """Should handle slicing all lines."""
        lines = ["a", "b", "c"]
        result = line_utils.slice_lines_raw(lines, 0, 3)
        assert result == "a\nb\nc"


class TestBuildLineOffsets:
    """Tests for build_line_offsets() function."""

    def test_basic_offsets(self):
        """Should calculate correct offsets for simple lines."""
        lines = ["abc", "def", "ghi"]
        offsets, total = line_utils.build_line_offsets(lines)
        assert offsets == [0, 4, 8]  # 'abc\n' = 4, 'abc\ndef\n' = 8
        assert total == 11  # 'abc\ndef\nghi' = 11

    def test_empty_lines(self):
        """Should handle empty input."""
        lines = []
        offsets, total = line_utils.build_line_offsets(lines)
        assert offsets == [0]
        assert total == 0

    def test_single_line(self):
        """Should handle single line."""
        lines = ["hello"]
        offsets, total = line_utils.build_line_offsets(lines)
        assert offsets == [0]
        assert total == 5

    def test_empty_string_lines(self):
        """Should handle lines containing empty strings."""
        lines = ["", "a", ""]
        offsets, total = line_utils.build_line_offsets(lines)
        assert offsets == [0, 1, 3]  # '\n' = 1, '\na\n' = 3
        assert total == 3  # '\na\n' = 3

    def test_varying_lengths(self):
        """Should handle lines of varying lengths."""
        lines = ["x", "yyy", "zz"]
        offsets, total = line_utils.build_line_offsets(lines)
        assert offsets == [0, 2, 6]  # 'x\n' = 2, 'x\nyyy\n' = 6
        assert total == 8  # 'x\nyyy\nzz' = 8

    def test_unicode_characters(self):
        """Should handle Unicode characters correctly."""
        lines = ["α", "β", "γ"]  # Greek letters
        offsets, total = line_utils.build_line_offsets(lines)
        # Each Greek letter is 2 bytes in UTF-8, but len() counts characters
        assert offsets == [0, 2, 4]  # Character counts, not byte counts
        assert total == 5
