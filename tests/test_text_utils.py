"""Unit tests for text_utils.py.

Tests for text extraction utilities extracted from markdown_parser_core.py
during Phase 7 modularization (Task 7.3).
"""

import pytest
from markdown_it import MarkdownIt
from doxstrux.markdown.utils import text_utils


@pytest.fixture
def md():
    """Markdown parser instance for testing."""
    return MarkdownIt("commonmark", {"html": False})


class TestCollectTextSegments:
    """Tests for collect_text_segments() function."""

    def test_simple_paragraph(self, md):
        """Should collect text from simple paragraph."""
        tokens = md.parse("Hello world")
        segments = text_utils.collect_text_segments(tokens)

        assert len(segments) == 1
        start, end, text = segments[0]
        assert text == "Hello world"
        assert start == 0

    def test_multiline_paragraph(self, md):
        """Should handle paragraph with line breaks."""
        tokens = md.parse("First line\nSecond line")
        segments = text_utils.collect_text_segments(tokens)

        assert len(segments) == 1
        start, end, text = segments[0]
        assert "First line" in text
        assert "Second line" in text

    def test_multiple_paragraphs(self, md):
        """Should collect multiple text segments."""
        tokens = md.parse("First paragraph\n\nSecond paragraph")
        segments = text_utils.collect_text_segments(tokens)

        assert len(segments) == 2
        assert segments[0][2] == "First paragraph"
        assert segments[1][2] == "Second paragraph"

    def test_inline_code(self, md):
        """Should include inline code in text."""
        tokens = md.parse("Text with `code` inline")
        segments = text_utils.collect_text_segments(tokens)

        assert len(segments) == 1
        text = segments[0][2]
        assert "Text with" in text
        assert "code" in text
        assert "inline" in text

    def test_empty_tokens(self):
        """Should return empty list for empty tokens."""
        segments = text_utils.collect_text_segments([])
        assert segments == []


class TestExtractTextFromInline:
    """Tests for extract_text_from_inline() function."""

    def test_simple_text(self, md):
        """Should extract text from inline token."""
        tokens = md.parse("Hello world")
        # Find the inline token
        inline_token = next(t for t in tokens if t.type == "inline")

        text = text_utils.extract_text_from_inline(inline_token)
        assert text == "Hello world"

    def test_formatted_text(self, md):
        """Should extract text from formatted content."""
        tokens = md.parse("**bold** and *italic*")
        inline_token = next(t for t in tokens if t.type == "inline")

        text = text_utils.extract_text_from_inline(inline_token)
        assert "bold" in text
        assert "italic" in text

    def test_inline_code(self, md):
        """Should extract inline code content."""
        tokens = md.parse("Text with `code` inline")
        inline_token = next(t for t in tokens if t.type == "inline")

        text = text_utils.extract_text_from_inline(inline_token)
        assert "code" in text

    def test_no_children(self, md):
        """Should return empty string if no children."""
        tokens = md.parse("# Heading")
        # heading_open has no children
        heading_token = next(t for t in tokens if t.type == "heading_open")

        text = text_utils.extract_text_from_inline(heading_token)
        assert text == ""

    def test_line_breaks(self, md):
        """Should handle softbreaks and hardbreaks."""
        tokens = md.parse("First line  \nSecond line")  # Two spaces for hard break
        inline_token = next(t for t in tokens if t.type == "inline")

        text = text_utils.extract_text_from_inline(inline_token)
        assert "\n" in text or "First" in text and "Second" in text


class TestHasChildType:
    """Tests for has_child_type() function."""

    def test_has_child_type_single(self, md):
        """Should detect child type in tree."""
        tokens = md.parse("```python\ncode\n```")
        tree = md.parse("```python\ncode\n```")

        # Parse to syntax tree
        from markdown_it.tree import SyntaxTreeNode
        root = SyntaxTreeNode(tokens)

        # Should find fence token
        assert text_utils.has_child_type(root, "fence")

    def test_no_child_type(self, md):
        """Should return False if type not found."""
        tokens = md.parse("Just text")
        from markdown_it.tree import SyntaxTreeNode
        root = SyntaxTreeNode(tokens)

        # Should not find fence token
        assert not text_utils.has_child_type(root, "fence")

    def test_multiple_types(self, md):
        """Should handle list of types."""
        tokens = md.parse("Text with **bold**")
        from markdown_it.tree import SyntaxTreeNode
        root = SyntaxTreeNode(tokens)

        # Should find text (always present in paragraphs)
        assert text_utils.has_child_type(root, ["text", "code_block"])

    def test_string_type_conversion(self, md):
        """Should convert string type to list."""
        tokens = md.parse("# Heading")
        from markdown_it.tree import SyntaxTreeNode
        root = SyntaxTreeNode(tokens)

        # Should find inline token (present in headings)
        assert text_utils.has_child_type(root, "inline")
