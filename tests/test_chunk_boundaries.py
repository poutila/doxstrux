"""Tests for chunk boundary verification in RAG chunking.

These tests verify that actual chunk boundaries are correct on complex documents,
addressing the gap identified in the test review: "If chunking is a core value prop,
add tests that verify actual chunk boundaries on complex documents."
"""

import pytest

from doxstrux.markdown_parser_core import MarkdownParserCore


class TestChunkBoundariesBasic:
    """Test that chunk boundaries respect structural elements."""

    def test_sections_become_separate_nodes(self) -> None:
        """Each top-level section should become a separate IR node."""
        content = """# Introduction

This is the introduction paragraph.

# Methods

This describes the methods.

# Results

Here are the results.
"""
        parser = MarkdownParserCore(content)
        ir = parser.to_ir()

        # Root should contain section nodes
        assert ir.root is not None
        section_children = [c for c in ir.root.children if c.type == "section"]

        # Should have 3 top-level sections
        assert len(section_children) >= 3

        # Verify section titles
        titles = [c.meta.get("title", "") for c in section_children]
        assert "Introduction" in titles
        assert "Methods" in titles
        assert "Results" in titles

    def test_nested_sections_hierarchy(self) -> None:
        """Sections at different levels should be captured with correct level info."""
        content = """# Main Section

Overview paragraph.

## Subsection A

Content A.

### Sub-subsection A1

Deep content.

## Subsection B

Content B.
"""
        parser = MarkdownParserCore(content)
        ir = parser.to_ir()

        # IR flattens sections but preserves level info in meta
        all_sections = [c for c in ir.root.children if c.type == "section"]
        assert len(all_sections) >= 4  # Main, A, A1, B

        # Verify levels are preserved
        levels = [s.meta.get("level") for s in all_sections]
        assert 1 in levels  # Main Section
        assert 2 in levels  # Subsections A, B
        assert 3 in levels  # Sub-subsection A1

    def test_code_blocks_as_separate_nodes(self) -> None:
        """Code blocks should be identifiable as separate content units."""
        content = """# Example

Here's some explanation.

```python
def hello():
    print("Hello, World!")
```

More explanation after the code.

```javascript
console.log("Another block");
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        # Should extract 2 code blocks
        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 2

        # Verify language info preserved
        languages = [cb.get("language") for cb in code_blocks]
        assert "python" in languages
        assert "javascript" in languages

    def test_tables_as_separate_nodes(self) -> None:
        """Tables should be extractable as distinct units."""
        content = """# Data

| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |

Some analysis text.

| Category | Count |
|----------|-------|
| X        | 10    |
| Y        | 20    |
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        tables = result["structure"]["tables"]
        assert len(tables) == 2

        # Verify table structure preserved
        for table in tables:
            assert "headers" in table
            assert "rows" in table
            assert len(table["rows"]) >= 2


class TestChunkBoundaryLines:
    """Test that chunk boundaries align with correct line numbers."""

    def test_section_line_spans(self) -> None:
        """Section line spans should be accurate."""
        content = """# First Section

Line 3 content.
Line 4 content.

# Second Section

Line 8 content.
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        sections = result["structure"]["sections"]
        assert len(sections) >= 2

        # First section starts at line 0 (# First Section)
        first = sections[0]
        assert first["start_line"] == 0

        # Second section starts at line 5 (# Second Section - 0-indexed)
        second = sections[1]
        assert second["start_line"] == 5

    def test_code_block_line_spans(self) -> None:
        """Code block line spans should be accurate."""
        content = """# Test

```python
line1 = 1
line2 = 2
line3 = 3
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

        cb = code_blocks[0]
        assert cb["start_line"] == 2  # ```python line
        assert cb["end_line"] == 7    # line after closing ```

    def test_paragraph_line_attribution(self) -> None:
        """Paragraphs should have correct line attribution."""
        content = """# Test

First paragraph here.

Second paragraph here.

Third paragraph here.
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        paragraphs = result["structure"]["paragraphs"]
        assert len(paragraphs) >= 3

        # Each paragraph should have line info
        for para in paragraphs:
            assert "start_line" in para or "line" in para


class TestChunkBoundaryComplex:
    """Test chunk boundaries on complex mixed-content documents."""

    def test_mixed_content_document(self) -> None:
        """Complex document with all element types."""
        content = """---
title: Complex Document
---

# Overview

This document has many elements.

## Code Example

```python
def example():
    return 42
```

## Data Table

| Col1 | Col2 |
|------|------|
| A    | B    |

## List Section

- Item 1
- Item 2
  - Nested item

## Blockquote

> This is a quote
> with multiple lines

## Final Notes

Conclusion text.
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()
        ir = parser.to_ir()

        # Verify all elements extracted
        assert result["structure"]["frontmatter"] is not None
        assert len(result["structure"]["sections"]) >= 5
        assert len(result["structure"]["code_blocks"]) >= 1
        assert len(result["structure"]["tables"]) >= 1
        assert len(result["structure"]["lists"]) >= 1
        assert len(result["structure"]["blockquotes"]) >= 1

        # IR should have structured nodes
        assert ir.root is not None
        assert len(ir.root.children) > 0

    def test_deeply_nested_structure(self) -> None:
        """Deeply nested sections should preserve hierarchy."""
        content = """# Level 1

## Level 2

### Level 3

#### Level 4

##### Level 5

###### Level 6

Back to higher level.

## Another Level 2

Different branch.
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        sections = result["structure"]["sections"]

        # Should have multiple sections at different levels
        levels = [s["level"] for s in sections]
        assert 1 in levels
        assert 2 in levels
        assert 3 in levels

    def test_adjacent_code_blocks(self) -> None:
        """Adjacent code blocks should be separate chunks."""
        content = """# Code Examples

```python
# Python
print("Hello")
```

```javascript
// JavaScript
console.log("Hello");
```

```rust
// Rust
fn main() {}
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 3

        # Each should have distinct line ranges
        line_ranges = [(cb["start_line"], cb["end_line"]) for cb in code_blocks]
        # No overlapping ranges
        for i, (s1, e1) in enumerate(line_ranges):
            for j, (s2, e2) in enumerate(line_ranges):
                if i != j:
                    assert e1 <= s2 or e2 <= s1, "Code blocks should not overlap"


class TestChunkBoundaryEdgeCases:
    """Edge cases for chunk boundary detection."""

    def test_empty_sections(self) -> None:
        """Sections with no content should still be detected."""
        content = """# Section 1

# Section 2

# Section 3
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        sections = result["structure"]["sections"]
        assert len(sections) >= 3

    def test_section_with_only_code(self) -> None:
        """Section containing only a code block."""
        content = """# Code Only Section

```python
# This section has only code
x = 1
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        sections = result["structure"]["sections"]
        code_blocks = result["structure"]["code_blocks"]

        assert len(sections) >= 1
        assert len(code_blocks) >= 1

    def test_inline_code_not_separate_chunk(self) -> None:
        """Inline code should not create separate chunks."""
        content = """# Test

This has `inline code` in a paragraph.

And more `code` here.
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        # Should have paragraphs but code_blocks should be empty
        # (inline code is part of paragraph, not code_block)
        paragraphs = result["structure"]["paragraphs"]
        code_blocks = result["structure"]["code_blocks"]

        assert len(paragraphs) >= 1
        assert len(code_blocks) == 0

    def test_list_following_paragraph(self) -> None:
        """List immediately after paragraph should be separate."""
        content = """# Test

Here is a paragraph.
- List item 1
- List item 2
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        paragraphs = result["structure"]["paragraphs"]
        lists = result["structure"]["lists"]

        assert len(paragraphs) >= 1
        assert len(lists) >= 1
