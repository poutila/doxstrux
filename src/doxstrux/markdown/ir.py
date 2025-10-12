"""
Document IR (Intermediate Representation) - Universal format for RAG chunking.

This module defines a source-agnostic document structure that serves as the
boundary between parsers (Markdown, HTML, PDF) and the chunker.

Design Goals:
- Source-agnostic: Works for Markdown, HTML, PDF, DOCX, etc.
- Stable contract: Parsers emit IR; chunker consumes IR
- Versioned schema: Breaking changes increment version
- Security-aware: Carries security metadata from validation
- RAG-optimized: Includes spans, IDs, and link graph for retrieval

Schema Version: md-ir@1.0.0
"""

from __future__ import annotations
from typing import Literal, Any
from dataclasses import dataclass, field


@dataclass
class DocNode:
    """
    A node in the document tree.

    Represents a semantic unit: section, paragraph, list, code block, table, etc.
    Forms a tree structure via the `children` field.

    Attributes:
        id: Stable identifier within document (e.g., "section_intro-1", "para_5")
        type: Node type (section, para, list, code, table, image, link)
        text: Raw visible text content (None for containers)
        meta: Type-specific metadata (lang, fence, alt, url, table_dims, etc.)
        span: Character span in original source (start_char, end_char)
        line_span: Line span in original source (start_line, end_line)
        children: Child nodes (for sections, lists, etc.)
    """
    id: str
    type: Literal[
        "section", "para", "list", "list_item", "code", "table",
        "table_row", "image", "link", "blockquote", "hr"
    ]
    text: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    span: tuple[int, int] | None = None  # (start_char, end_char)
    line_span: tuple[int, int] | None = None  # (start_line, end_line)
    children: list[DocNode] = field(default_factory=list)


@dataclass
class DocumentIR:
    """
    Universal Document Intermediate Representation for RAG pipelines.

    This is the contract between parsers and chunkers:
    - Parsers (Markdown, HTML, PDF) emit DocumentIR
    - Chunkers consume DocumentIR to produce chunks

    Schema Version: md-ir@1.0.0

    Attributes:
        schema_version: IR schema version (e.g., "md-ir@1.0.0")
        source_id: Source identifier (file path, URL, hash)
        source_type: Source format (markdown, html, pdf, docx)
        content_hash: SHA256 of normalized content (for deduplication)
        allows_html: Whether HTML is allowed in content
        security: Security metadata from validation
        frontmatter: Document-level metadata (title, author, tags, etc.)
        root: Root node of document tree
        link_graph: Internal link adjacency list for retrieval expansion
    """
    schema_version: str = "md-ir@1.0.0"
    source_id: str = ""
    source_type: Literal["markdown", "html", "pdf", "docx", "text"] = "markdown"
    content_hash: str = ""  # SHA256 of normalized content
    allows_html: bool = False
    security: dict[str, Any] = field(default_factory=dict)
    frontmatter: dict[str, Any] = field(default_factory=dict)
    root: DocNode | None = None
    link_graph: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON export."""
        return {
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "content_hash": self.content_hash,
            "allows_html": self.allows_html,
            "security": self.security,
            "frontmatter": self.frontmatter,
            "root": self._node_to_dict(self.root) if self.root else None,
            "link_graph": self.link_graph,
        }

    @staticmethod
    def _node_to_dict(node: DocNode) -> dict[str, Any]:
        """Recursively serialize node tree."""
        return {
            "id": node.id,
            "type": node.type,
            "text": node.text,
            "meta": node.meta,
            "span": node.span,
            "line_span": node.line_span,
            "children": [DocumentIR._node_to_dict(c) for c in node.children],
        }


@dataclass
class ChunkPolicy:
    """
    Configuration for chunking strategy.

    Attributes:
        mode: Chunking strategy ("semantic", "fixed", "code_aware")
        target_tokens: Target tokens per chunk
        overlap_tokens: Overlap between chunks for context
        min_chunk_tokens: Minimum tokens to emit a chunk
        max_chunk_tokens: Hard maximum (split if exceeded)
        respect_boundaries: Don't split across sections/code/tables
        include_code: Include code blocks in chunks
        include_tables: Include tables in chunks
        normalize_whitespace: Collapse consecutive whitespace
        normalize_unicode: Normalize to NFC
        redact_urls: Remove query parameters from URLs
        token_estimator: How to estimate tokens ("bytes", "chars", "tiktoken")
        base_url: Base URL for resolving relative links
    """
    mode: Literal["semantic", "fixed", "code_aware"] = "semantic"
    target_tokens: int = 600
    overlap_tokens: int = 60
    min_chunk_tokens: int = 100
    max_chunk_tokens: int = 1000
    respect_boundaries: bool = True
    include_code: bool = True
    include_tables: bool = True
    normalize_whitespace: bool = True
    normalize_unicode: bool = True
    redact_urls: bool = False
    token_estimator: Literal["bytes", "chars", "tiktoken"] = "bytes"
    base_url: str | None = None


@dataclass
class Chunk:
    """
    A chunk suitable for embedding in RAG pipelines.

    Attributes:
        chunk_id: Unique identifier (stable across re-chunking)
        section_path: Breadcrumb of section IDs (["intro", "background"])
        text: Normalized text for embedding
        normalized_text: Cleaned text (whitespace, unicode, redactions)
        span: Character span in original source
        line_span: Line span in original source
        token_estimate: Estimated tokens (depends on estimator)
        chunk_hash: SHA256(section_path + normalized_text)
        risk_flags: Security warnings (["prompt_injection", "confusables"])
        links: Links present in chunk
        images: Images present in chunk
        meta: Additional metadata
    """
    chunk_id: str
    section_path: list[str]
    text: str
    normalized_text: str
    span: tuple[int, int] | None = None
    line_span: tuple[int, int] | None = None
    token_estimate: int = 0
    chunk_hash: str = ""
    risk_flags: list[str] = field(default_factory=list)
    links: list[dict[str, Any]] = field(default_factory=list)
    images: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkResult:
    """
    Result of chunking a document.

    Attributes:
        chunks: List of chunks
        link_graph: Internal link adjacency list
        stats: Statistics (total_chunks, avg_tokens, etc.)
        errors: Errors encountered during chunking
    """
    chunks: list[Chunk]
    link_graph: dict[str, list[str]] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


# Version history
__version__ = "1.0.0"
__schema_version__ = "md-ir@1.0.0"

"""
Schema Version History:

md-ir@1.0.0 (2025-10-12):
- Initial Document IR schema
- DocNode with type, text, meta, span, children
- DocumentIR with security, frontmatter, link_graph
- ChunkPolicy, Chunk, ChunkResult for chunker contract
"""
