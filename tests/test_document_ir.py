"""
Tests for Document IR (Intermediate Representation) for RAG chunking.

Phase 6 Task 6.2: Document IR as contract between parsers and chunkers.
"""

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.ir import DocumentIR, DocNode, ChunkPolicy, Chunk, ChunkResult


class TestDocumentIR:
    """Test Document IR generation and serialization."""

    def test_basic_ir_generation(self):
        """Test basic IR generation from markdown."""
        content = """# Introduction

This is a paragraph with a [link](#section).

## Section

Content here.
"""
        parser = MarkdownParserCore(content)
        ir = parser.to_ir(source_id="test_doc")

        assert ir.schema_version == "md-ir@1.0.0"
        assert ir.source_id == "test_doc"
        assert ir.source_type == "markdown"
        assert len(ir.content_hash) == 64  # SHA256 hash
        assert ir.allows_html is False
        assert isinstance(ir.security, dict)
        assert isinstance(ir.frontmatter, dict)
        assert ir.root is not None
        assert ir.root.type == "section"
        assert len(ir.root.children) > 0

    def test_ir_with_frontmatter(self):
        """Test IR generation with frontmatter."""
        content = """---
title: Test Document
author: Claude
tags: [test, markdown]
---

# Content

Body text.
"""
        parser = MarkdownParserCore(content)
        ir = parser.to_ir(source_id="frontmatter_test")

        assert ir.frontmatter.get("title") == "Test Document"
        assert ir.frontmatter.get("author") == "Claude"
        assert ir.frontmatter.get("tags") == ["test", "markdown"]

    def test_ir_link_graph(self):
        """Test link graph generation for internal links."""
        content = """# Introduction

See [background](#background).

## Background

Read the [introduction](#introduction).

## Conclusion

No links here.
"""
        parser = MarkdownParserCore(content)
        ir = parser.to_ir()

        # Should have links between sections
        assert isinstance(ir.link_graph, dict)
        # Introduction should link to background
        intro_links = None
        background_links = None
        for section_id, targets in ir.link_graph.items():
            if "introduction" in section_id.lower():
                intro_links = targets
            elif "background" in section_id.lower():
                background_links = targets

        # At least one section should have links
        assert intro_links or background_links

    def test_ir_security_metadata(self):
        """Test security metadata propagation to IR."""
        content = """# Test

<script>alert('xss')</script>

[javascript link](javascript:void(0))
"""
        parser = MarkdownParserCore(content, config={"allows_html": True})
        ir = parser.to_ir()

        assert "security" in ir.to_dict()
        security = ir.security
        assert "statistics" in security
        # Should detect dangerous content
        stats = security["statistics"]
        assert stats.get("has_script") or stats.get("has_html_block")

    def test_ir_json_serialization(self):
        """Test IR serialization to JSON-compatible dict."""
        content = """# Test

Paragraph with **bold** and *italic*.

- List item 1
- List item 2

```python
code = "block"
```
"""
        parser = MarkdownParserCore(content)
        ir = parser.to_ir()

        # Should serialize to dict
        ir_dict = ir.to_dict()
        assert isinstance(ir_dict, dict)
        assert ir_dict["schema_version"] == "md-ir@1.0.0"
        assert "root" in ir_dict
        assert ir_dict["root"]["type"] == "section"
        assert "children" in ir_dict["root"]

    def test_ir_without_source_id(self):
        """Test IR generation without explicit source_id."""
        content = "# Test\n\nContent."
        parser = MarkdownParserCore(content)
        ir = parser.to_ir()

        # Should use content hash prefix as source_id
        assert len(ir.source_id) == 16
        assert ir.source_id == ir.content_hash[:16]

    def test_ir_node_structure(self):
        """Test DocNode tree structure."""
        content = """# Main

## Sub1

Content 1.

## Sub2

Content 2.
"""
        parser = MarkdownParserCore(content)
        ir = parser.to_ir()

        # Root should have section children
        assert ir.root is not None
        assert len(ir.root.children) > 0

        # Each section should have metadata
        for section_node in ir.root.children:
            assert section_node.type == "section"
            assert section_node.id.startswith("section_")
            assert "title" in section_node.meta
            assert "level" in section_node.meta
            assert "slug" in section_node.meta


class TestChunkPolicy:
    """Test ChunkPolicy dataclass."""

    def test_default_policy(self):
        """Test default chunking policy."""
        policy = ChunkPolicy()
        assert policy.mode == "semantic"
        assert policy.target_tokens == 600
        assert policy.overlap_tokens == 60
        assert policy.min_chunk_tokens == 100
        assert policy.max_chunk_tokens == 1000
        assert policy.respect_boundaries is True
        assert policy.include_code is True
        assert policy.include_tables is True
        assert policy.token_estimator == "bytes"

    def test_custom_policy(self):
        """Test custom chunking policy."""
        policy = ChunkPolicy(
            mode="fixed",
            target_tokens=1000,
            overlap_tokens=100,
            token_estimator="tiktoken"
        )
        assert policy.mode == "fixed"
        assert policy.target_tokens == 1000
        assert policy.overlap_tokens == 100
        assert policy.token_estimator == "tiktoken"


class TestChunk:
    """Test Chunk dataclass."""

    def test_chunk_creation(self):
        """Test chunk creation."""
        chunk = Chunk(
            chunk_id="chunk_0",
            section_path=["intro", "background"],
            text="Original text",
            normalized_text="Normalized text",
            span=(0, 100),
            line_span=(0, 5),
            token_estimate=50,
            chunk_hash="abc123"
        )
        assert chunk.chunk_id == "chunk_0"
        assert chunk.section_path == ["intro", "background"]
        assert chunk.text == "Original text"
        assert chunk.normalized_text == "Normalized text"
        assert chunk.token_estimate == 50


class TestChunkResult:
    """Test ChunkResult dataclass."""

    def test_chunk_result_creation(self):
        """Test chunk result creation."""
        chunk = Chunk(
            chunk_id="chunk_0",
            section_path=["intro"],
            text="Text",
            normalized_text="Text"
        )
        result = ChunkResult(
            chunks=[chunk],
            link_graph={"intro": ["background"]},
            stats={"total_chunks": 1},
            errors=[]
        )
        assert len(result.chunks) == 1
        assert result.link_graph["intro"] == ["background"]
        assert result.stats["total_chunks"] == 1
        assert len(result.errors) == 0
