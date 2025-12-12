"""Tests for runtime robustness - Preventing TypeError/AttributeError crashes.

These tests verify that the parser handles edge cases like None content
in tokens, malformed heading tags, and empty math blocks without crashing.
"""

import pytest

from doxstrux.markdown.extractors import math as math_module
from doxstrux.markdown.utils import token_utils
from doxstrux.markdown_parser_core import MarkdownParserCore


class TestNoneContentHandling:
    """Tests for handling None content in tokens."""

    def test_parser_rejects_none_content(self) -> None:
        """Parser should raise TypeError for None content."""
        with pytest.raises(TypeError, match="content must be str, not None"):
            MarkdownParserCore(None)  # type: ignore[arg-type]

    def test_empty_string_content_allowed(self) -> None:
        """Empty string content should be allowed."""
        parser = MarkdownParserCore("")
        result = parser.parse()
        assert result is not None
        assert "metadata" in result

    def test_whitespace_only_content(self) -> None:
        """Whitespace-only content should be handled."""
        parser = MarkdownParserCore("   \n\n   \t   ")
        result = parser.parse()
        assert result is not None


class TestHeadingLevelExtraction:
    """Tests for safe heading level extraction."""

    def test_normal_headings(self) -> None:
        """Normal h1-h6 headings should work correctly."""
        content = """# H1
## H2
### H3
#### H4
##### H5
###### H6
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()
        sections = result["structure"]["sections"]

        # Verify we got all 6 headings
        assert len(sections) >= 6

    def test_heading_extraction_via_parser(self) -> None:
        """Headings should be safely extracted."""
        content = "# Test Heading\n\nSome text"
        parser = MarkdownParserCore(content)
        result = parser.parse()

        headings = result["structure"]["headings"]
        assert len(headings) >= 1
        assert headings[0]["level"] == 1


class TestMathBlockHandling:
    """Tests for math block extraction with edge cases."""

    def test_extract_math_with_empty_tokens(self) -> None:
        """Extract math should handle empty token list."""
        result = math_module.extract_math([])
        assert result == {"blocks": [], "inline": []}

    def test_fenced_math_block(self) -> None:
        """Fenced math blocks should be extracted."""
        content = """```math
E = mc^2
```"""
        parser = MarkdownParserCore(content)
        # Math extraction happens during parsing
        result = parser.parse()
        assert result is not None


class TestLinkExtraction:
    """Tests for link extraction with edge cases."""

    def test_link_with_empty_text(self) -> None:
        """Links with empty text should not crash."""
        content = "[](http://example.com)"
        parser = MarkdownParserCore(content)
        result = parser.parse()
        links = result["structure"]["links"]
        assert len(links) == 1
        assert links[0]["url"] == "http://example.com"

    def test_image_with_empty_alt(self) -> None:
        """Images with empty alt text should not crash."""
        content = "![](image.png)"
        parser = MarkdownParserCore(content)
        result = parser.parse()
        images = result["structure"]["images"]
        assert len(images) == 1


class TestTableExtraction:
    """Tests for table extraction with edge cases."""

    def test_table_with_empty_cells(self) -> None:
        """Tables with empty cells should not crash."""
        content = """| A | B |
|---|---|
|   |   |
| x |   |
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()
        tables = result["structure"]["tables"]
        assert len(tables) == 1
        # Empty cells should be empty strings, not None
        for row in tables[0]["rows"]:
            for cell in row:
                assert cell is not None


class TestTokenUtilsRobustness:
    """Tests for token_utils edge cases."""

    def test_extract_links_and_images_empty(self) -> None:
        """Extract links/images from empty content."""
        links, images = token_utils.extract_links_and_images("")
        assert links == []
        assert images == []

    def test_extract_links_and_images_text_only(self) -> None:
        """Extract links/images from text without links."""
        links, images = token_utils.extract_links_and_images("Just plain text")
        assert links == []
        assert images == []


class TestEdgeCaseDocuments:
    """Tests for edge case documents that might crash naive implementations."""

    def test_deeply_nested_lists(self) -> None:
        """Deeply nested lists should not cause stack overflow."""
        # Create a deeply nested list
        content = "- Level 1\n"
        for i in range(2, 20):
            content += "  " * (i - 1) + f"- Level {i}\n"

        parser = MarkdownParserCore(content)
        result = parser.parse()
        assert result is not None

    def test_many_code_blocks(self) -> None:
        """Many code blocks should be handled efficiently."""
        content = "\n".join([f"```\ncode block {i}\n```" for i in range(50)])
        parser = MarkdownParserCore(content)
        result = parser.parse()
        assert len(result["structure"]["code_blocks"]) == 50

    def test_mixed_content_stress(self) -> None:
        """Mixed content with many element types."""
        content = """# Heading

Paragraph with **bold** and *italic* and `code`.

- List item 1
- List item 2

| Header |
|--------|
| Cell   |

```python
print("hello")
```

> Blockquote

[Link](http://example.com)

![Image](img.png)
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()
        structure = result["structure"]

        # Verify all element types were extracted
        assert len(structure["sections"]) >= 1
        assert len(structure["paragraphs"]) >= 1
        assert len(structure["lists"]) >= 1
        assert len(structure["tables"]) >= 1
        assert len(structure["code_blocks"]) >= 1
        assert len(structure["blockquotes"]) >= 1
        assert len(structure["links"]) >= 1
        assert len(structure["images"]) >= 1
