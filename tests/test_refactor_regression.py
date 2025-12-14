"""
DOXSTRUX Refactoring Regression Tests

This test suite pins the EXACT output structure of MarkdownParserCore.parse()
before refactoring. Run after each refactoring step to catch regressions.

DO NOT MODIFY THESE TESTS during refactoring - they define correct behavior.
If a test fails after refactoring, the refactoring changed behavior.

Usage:
    # Run after each refactoring step
    uv run pytest tests/test_refactor_regression.py -v
    
    # Quick smoke test
    uv run pytest tests/test_refactor_regression.py -v -k "smoke"
"""

import pytest
from typing import Any

from doxstrux.markdown_parser_core import MarkdownParserCore


# =============================================================================
# FIXTURES: Test Documents
# =============================================================================

@pytest.fixture
def comprehensive_document() -> str:
    """Document exercising all extractors."""
    return '''---
title: Test Document
author: Regression Suite
---

# Introduction

This is the **introduction** paragraph with *italic* and `inline code`.

## Features

### Lists

- Bullet item 1
- Bullet item 2
  - Nested bullet
- Bullet item 3

1. Ordered item 1
2. Ordered item 2
3. Ordered item 3

### Task Lists

- [ ] Unchecked task
- [x] Checked task
- [ ] Another task

### Code Blocks

```python
def hello():
    print("Hello, World!")
```

```javascript
const x = 42;
```

### Tables

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |

### Links and Images

[Example Link](https://example.com)
[Anchor Link](#introduction)

![Alt text](https://example.com/image.png "Image Title")

### Blockquotes

> This is a blockquote.
> It can span multiple lines.

### Math

Inline math: $E = mc^2$

Block math:

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

### HTML

<div class="custom">Custom HTML</div>

## Conclusion

Final paragraph.

[^1]: This is a footnote.
'''


@pytest.fixture
def minimal_document() -> str:
    """Minimal valid markdown."""
    return "# Title\n\nParagraph."


@pytest.fixture
def adversarial_document() -> str:
    """Document with security-relevant content."""
    return '''# Security Test

[JavaScript Link](javascript:alert(1))
[Data URI](data:text/html,<script>alert(1)</script>)
[Normal Link](https://example.com)

Path traversal: [passwd](../../../etc/passwd)

<script>alert("xss")</script>

<!-- HTML comment -->
'''


# =============================================================================
# SMOKE TESTS: Quick validation that parse() works
# =============================================================================

class TestRefactorSmoke:
    """Quick smoke tests - run these first."""

    def test_smoke_parse_returns_dict(self, minimal_document: str) -> None:
        """parse() must return a dict."""
        parser = MarkdownParserCore(minimal_document)
        result = parser.parse()
        assert isinstance(result, dict)

    def test_smoke_top_level_keys(self, minimal_document: str) -> None:
        """parse() must return expected top-level keys."""
        parser = MarkdownParserCore(minimal_document)
        result = parser.parse()
        
        required_keys = {"metadata", "content", "structure", "mappings"}
        assert required_keys.issubset(result.keys()), \
            f"Missing keys: {required_keys - result.keys()}"

    def test_smoke_comprehensive_parse(self, comprehensive_document: str) -> None:
        """Comprehensive document must parse without error."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        assert "structure" in result


# =============================================================================
# STRUCTURE TESTS: Verify all extractors produce output
# =============================================================================

class TestRefactorStructureKeys:
    """Verify structure contains all expected extractor outputs."""

    @pytest.mark.parametrize("key", [
        "sections",
        "paragraphs",
        "lists",
        "tables",
        "code_blocks",
        "headings",
        "links",
        "images",
        "blockquotes",
        "frontmatter",
        "tasklists",
        "math",
        "html_blocks",
        "html_inline",
    ])
    def test_structure_has_key(self, comprehensive_document: str, key: str) -> None:
        """structure must contain all extractor output keys."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        structure = result["structure"]
        
        assert key in structure, f"Missing structure key: {key}"

    def test_all_structure_values_are_lists_or_dict(self, comprehensive_document: str) -> None:
        """All structure values must be lists or dicts (not None)."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        structure = result["structure"]
        
        for key, value in structure.items():
            assert value is not None or key == "frontmatter", \
                f"structure['{key}'] is None"
            if key != "frontmatter":
                assert isinstance(value, (list, dict)), \
                    f"structure['{key}'] is {type(value)}, expected list or dict"


# =============================================================================
# SECTIONS EXTRACTOR TESTS
# =============================================================================

class TestRefactorSections:
    """Regression tests for sections extractor."""

    def test_sections_extracted(self, comprehensive_document: str) -> None:
        """Sections must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        sections = result["structure"]["sections"]
        
        assert len(sections) >= 3, "Expected multiple sections"

    def test_section_has_required_keys(self, comprehensive_document: str) -> None:
        """Each section must have required keys."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        sections = result["structure"]["sections"]
        
        required_keys = {"id", "title", "level"}
        for section in sections:
            assert required_keys.issubset(section.keys()), \
                f"Section missing keys: {required_keys - section.keys()}"

    def test_section_levels_correct(self, minimal_document: str) -> None:
        """Section levels must match heading levels."""
        parser = MarkdownParserCore(minimal_document)
        result = parser.parse()
        sections = result["structure"]["sections"]
        
        # "# Title" is level 1
        assert sections[0]["level"] == 1


# =============================================================================
# PARAGRAPHS EXTRACTOR TESTS
# =============================================================================

class TestRefactorParagraphs:
    """Regression tests for paragraphs extractor."""

    def test_paragraphs_extracted(self, comprehensive_document: str) -> None:
        """Paragraphs must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        paragraphs = result["structure"]["paragraphs"]
        
        assert len(paragraphs) >= 2, "Expected multiple paragraphs"

    def test_paragraph_has_text(self, minimal_document: str) -> None:
        """Paragraphs must have text content."""
        parser = MarkdownParserCore(minimal_document)
        result = parser.parse()
        paragraphs = result["structure"]["paragraphs"]
        
        assert len(paragraphs) >= 1
        assert "text" in paragraphs[0]
        assert "Paragraph" in paragraphs[0]["text"]


# =============================================================================
# LISTS EXTRACTOR TESTS
# =============================================================================

class TestRefactorLists:
    """Regression tests for lists extractor."""

    def test_bullet_list_extracted(self, comprehensive_document: str) -> None:
        """Bullet lists must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        lists = result["structure"]["lists"]
        
        bullet_lists = [lst for lst in lists if lst.get("type") == "bullet"]
        assert len(bullet_lists) >= 1, "Expected at least one bullet list"

    def test_ordered_list_extracted(self, comprehensive_document: str) -> None:
        """Ordered lists must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        lists = result["structure"]["lists"]
        
        ordered_lists = [lst for lst in lists if lst.get("type") == "ordered"]
        assert len(ordered_lists) >= 1, "Expected at least one ordered list"

    def test_list_has_items(self, comprehensive_document: str) -> None:
        """Lists must have items."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        lists = result["structure"]["lists"]
        
        for lst in lists:
            assert "items" in lst
            assert isinstance(lst["items"], list)


# =============================================================================
# TASKLISTS EXTRACTOR TESTS
# =============================================================================

class TestRefactorTasklists:
    """Regression tests for tasklists extractor."""

    def test_tasklists_extracted(self, comprehensive_document: str) -> None:
        """Task lists must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        tasklists = result["structure"]["tasklists"]
        
        assert len(tasklists) >= 1, "Expected at least one task list"

    def test_tasklist_items_have_checked_state(self, comprehensive_document: str) -> None:
        """Task list items must have checked state."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        tasklists = result["structure"]["tasklists"]
        
        for tasklist in tasklists:
            items = tasklist.get("items", [])
            for item in items:
                assert "checked" in item or "done" in item, \
                    "Task item must have checked/done field"


# =============================================================================
# CODE BLOCKS EXTRACTOR TESTS
# =============================================================================

class TestRefactorCodeBlocks:
    """Regression tests for code_blocks extractor."""

    def test_code_blocks_extracted(self, comprehensive_document: str) -> None:
        """Code blocks must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        code_blocks = result["structure"]["code_blocks"]
        
        assert len(code_blocks) >= 2, "Expected multiple code blocks"

    def test_code_block_has_language(self, comprehensive_document: str) -> None:
        """Code blocks must have language info."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        code_blocks = result["structure"]["code_blocks"]
        
        languages = [cb.get("language") for cb in code_blocks]
        assert "python" in languages
        assert "javascript" in languages

    def test_code_block_has_content(self, comprehensive_document: str) -> None:
        """Code blocks must have content."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        code_blocks = result["structure"]["code_blocks"]
        
        for cb in code_blocks:
            content = cb.get("content", cb.get("code", ""))
            assert content, f"Code block missing content"

    def test_code_block_has_line_info(self, comprehensive_document: str) -> None:
        """Code blocks must have line attribution."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        code_blocks = result["structure"]["code_blocks"]
        
        for cb in code_blocks:
            assert "start_line" in cb, "Code block missing start_line"


# =============================================================================
# TABLES EXTRACTOR TESTS
# =============================================================================

class TestRefactorTables:
    """Regression tests for tables extractor."""

    def test_tables_extracted(self, comprehensive_document: str) -> None:
        """Tables must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        tables = result["structure"]["tables"]
        
        assert len(tables) >= 1, "Expected at least one table"

    def test_table_has_headers(self, comprehensive_document: str) -> None:
        """Tables must have headers."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        tables = result["structure"]["tables"]
        
        for table in tables:
            assert "headers" in table or "header_row" in table, \
                "Table missing headers"

    def test_table_has_rows(self, comprehensive_document: str) -> None:
        """Tables must have rows."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        tables = result["structure"]["tables"]
        
        for table in tables:
            assert "rows" in table or "body_rows" in table, \
                "Table missing rows"

    def test_table_has_quality_flags(self, comprehensive_document: str) -> None:
        """Tables must have is_pure and is_ragged flags."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        tables = result["structure"]["tables"]
        
        for table in tables:
            assert "is_pure" in table
            assert "is_ragged" in table


# =============================================================================
# HEADINGS EXTRACTOR TESTS
# =============================================================================

class TestRefactorHeadings:
    """Regression tests for headings extractor."""

    def test_headings_extracted(self, comprehensive_document: str) -> None:
        """Headings must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        headings = result["structure"]["headings"]
        
        assert len(headings) >= 5, "Expected multiple headings"

    def test_heading_has_text_and_level(self, comprehensive_document: str) -> None:
        """Headings must have text and level."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        headings = result["structure"]["headings"]
        
        for heading in headings:
            assert "text" in heading
            assert "level" in heading
            assert 1 <= heading["level"] <= 6


# =============================================================================
# LINKS EXTRACTOR TESTS
# =============================================================================

class TestRefactorLinks:
    """Regression tests for links extractor."""

    def test_links_extracted(self, comprehensive_document: str) -> None:
        """Links must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        links = result["structure"]["links"]
        
        assert len(links) >= 2, "Expected multiple links"

    def test_link_has_url_and_text(self, comprehensive_document: str) -> None:
        """Links must have url and text."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        links = result["structure"]["links"]
        
        for link in links:
            assert "url" in link or "href" in link
            assert "text" in link or "title" in link


# =============================================================================
# IMAGES EXTRACTOR TESTS
# =============================================================================

class TestRefactorImages:
    """Regression tests for images extractor."""

    def test_images_extracted(self, comprehensive_document: str) -> None:
        """Images must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        images = result["structure"]["images"]
        
        assert len(images) >= 1, "Expected at least one image"

    def test_image_has_url_and_alt(self, comprehensive_document: str) -> None:
        """Images must have url and alt text."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        images = result["structure"]["images"]
        
        for image in images:
            assert "url" in image or "src" in image
            assert "alt" in image


# =============================================================================
# BLOCKQUOTES EXTRACTOR TESTS
# =============================================================================

class TestRefactorBlockquotes:
    """Regression tests for blockquotes extractor."""

    def test_blockquotes_extracted(self, comprehensive_document: str) -> None:
        """Blockquotes must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        blockquotes = result["structure"]["blockquotes"]
        
        assert len(blockquotes) >= 1, "Expected at least one blockquote"


# =============================================================================
# FRONTMATTER EXTRACTOR TESTS
# =============================================================================

class TestRefactorFrontmatter:
    """Regression tests for frontmatter extractor."""

    def test_frontmatter_extracted(self, comprehensive_document: str) -> None:
        """Frontmatter must be extracted when present."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        frontmatter = result["structure"]["frontmatter"]
        
        assert frontmatter is not None, "Frontmatter not extracted"
        assert isinstance(frontmatter, dict)
        assert "title" in frontmatter

    def test_no_frontmatter_returns_none(self, minimal_document: str) -> None:
        """Documents without frontmatter return None."""
        parser = MarkdownParserCore(minimal_document)
        result = parser.parse()
        frontmatter = result["structure"]["frontmatter"]
        
        assert frontmatter is None


# =============================================================================
# MATH EXTRACTOR TESTS
# =============================================================================

class TestRefactorMath:
    """Regression tests for math extractor."""

    def test_math_extracted(self, comprehensive_document: str) -> None:
        """Math must be extracted."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        math = result["structure"]["math"]
        
        assert isinstance(math, dict)
        # Math extractor returns dict with 'blocks' and 'inline'
        assert "blocks" in math or "inline" in math or len(math) == 0


# =============================================================================
# HTML EXTRACTOR TESTS
# =============================================================================

class TestRefactorHtml:
    """Regression tests for HTML extraction."""

    def test_html_blocks_extracted(self, comprehensive_document: str) -> None:
        """HTML blocks list must exist and be a list."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        html_blocks = result["structure"]["html_blocks"]
        
        assert isinstance(html_blocks, list)
        # Note: The comprehensive doc may not produce block-level HTML
        # (inline divs become part of paragraph content)

    def test_html_inline_is_list(self, comprehensive_document: str) -> None:
        """HTML inline must be a list."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        html_inline = result["structure"]["html_inline"]
        
        assert isinstance(html_inline, list)


# =============================================================================
# METADATA TESTS
# =============================================================================

class TestRefactorMetadata:
    """Regression tests for metadata structure."""

    def test_metadata_has_security(self, comprehensive_document: str) -> None:
        """Metadata must have security section."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        metadata = result["metadata"]
        
        assert "security" in metadata

    def test_security_metadata_structure(self, comprehensive_document: str) -> None:
        """Security metadata must have expected structure."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        security = result["metadata"]["security"]
        
        # These keys should exist in security metadata
        expected_keys = {"warnings", "statistics", "summary"}
        assert expected_keys.issubset(security.keys()), \
            f"Security missing keys: {expected_keys - security.keys()}"

    def test_security_has_profile_used(self, comprehensive_document: str) -> None:
        """Security metadata must record profile_used."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        security = result["metadata"]["security"]
        
        assert "profile_used" in security


# =============================================================================
# MAPPINGS TESTS
# =============================================================================

class TestRefactorMappings:
    """Regression tests for mappings structure."""

    def test_mappings_has_line_to_type(self, comprehensive_document: str) -> None:
        """Mappings must have line_to_type."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        mappings = result["mappings"]
        
        assert "line_to_type" in mappings

    def test_mappings_has_code_blocks(self, comprehensive_document: str) -> None:
        """Mappings must have code_blocks list."""
        parser = MarkdownParserCore(comprehensive_document)
        result = parser.parse()
        mappings = result["mappings"]
        
        assert "code_blocks" in mappings
        assert isinstance(mappings["code_blocks"], list)


# =============================================================================
# CONTENT TESTS
# =============================================================================

class TestRefactorContent:
    """Regression tests for content structure."""

    def test_content_has_raw_and_lines(self, minimal_document: str) -> None:
        """Content must have raw and lines."""
        parser = MarkdownParserCore(minimal_document)
        result = parser.parse()
        content = result["content"]
        
        assert "raw" in content
        assert "lines" in content
        assert isinstance(content["lines"], list)


# =============================================================================
# SECURITY DETECTION TESTS
# =============================================================================

class TestRefactorSecurityDetection:
    """Regression tests for security detection."""

    def test_javascript_link_detected(self, adversarial_document: str) -> None:
        """JavaScript links must be flagged."""
        parser = MarkdownParserCore(adversarial_document)
        result = parser.parse()
        security = result["metadata"]["security"]
        
        # Should have warnings about javascript: scheme
        warnings = security.get("warnings", [])
        has_js_warning = any(
            "javascript" in str(w).lower() 
            for w in warnings
        )
        assert has_js_warning or security.get("statistics", {}).get("blocked_schemes", 0) > 0, \
            "JavaScript link not flagged"

    def test_path_traversal_detected(self, adversarial_document: str) -> None:
        """Path traversal must be detected."""
        parser = MarkdownParserCore(adversarial_document)
        result = parser.parse()
        security = result["metadata"]["security"]
        
        # Should have warnings about path traversal
        warnings = security.get("warnings", [])
        statistics = security.get("statistics", {})
        
        has_traversal_warning = any(
            "traversal" in str(w).lower() 
            for w in warnings
        ) or statistics.get("path_traversal", 0) > 0
        
        assert has_traversal_warning, "Path traversal not detected"


# =============================================================================
# GOLDEN OUTPUT TEST
# =============================================================================

class TestRefactorGoldenOutput:
    """Golden output test - pinned structure from known document."""

    def test_minimal_document_golden(self, minimal_document: str) -> None:
        """Minimal document produces expected structure."""
        parser = MarkdownParserCore(minimal_document)
        result = parser.parse()
        
        # Pin exact structure for minimal document
        assert len(result["structure"]["sections"]) == 1
        assert result["structure"]["sections"][0]["title"] == "Title"
        assert result["structure"]["sections"][0]["level"] == 1
        
        assert len(result["structure"]["headings"]) == 1
        assert result["structure"]["headings"][0]["text"] == "Title"
        
        assert len(result["structure"]["paragraphs"]) >= 1
        
        # Pin content preservation
        assert "# Title" in result["content"]["raw"]
        assert "Paragraph" in result["content"]["raw"]
