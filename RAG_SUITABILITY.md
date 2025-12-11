# RAG Pipeline Suitability Evaluation

This document evaluates doxstrux's suitability for Retrieval-Augmented Generation (RAG) pipelines. The evaluation is based on deep analysis of the codebase, not assumptions.

---

## Executive Summary

**Verdict: Highly Suitable for RAG Pipelines**

Doxstrux was explicitly designed for RAG use cases. The codebase contains 50+ explicit RAG-related code comments, a dedicated Document IR layer, security features specifically for embedding safety, and comprehensive structure extraction that preserves semantic boundaries.

| Criteria | Score | Notes |
|----------|-------|-------|
| Structure Preservation | 5/5 | Sections, paragraphs, code blocks with precise line spans |
| Chunking Support | 4/5 | IR layer exists, chunker not yet implemented |
| Security for RAG | 5/5 | `embedding_blocked`, `quarantine`, prompt injection detection |
| Metadata Richness | 5/5 | 20+ metadata fields per element |
| Content Classification | 5/5 | Line-level prose/code classification |
| Link Graph | 4/5 | Internal link adjacency list for retrieval expansion |
| Performance | 4/5 | ~1ms per file, 542 files in ~550ms |

---

## 1. RAG-Specific Design Evidence

### 1.1 Explicit RAG Intent in Code

The codebase explicitly mentions RAG in 50+ locations:

```python
# From ir.py
"""Document IR (Intermediate Representation) - Universal format for RAG chunking."""
"""RAG-optimized: Includes spans, IDs, and link graph for retrieval"""

# From markdown_parser_core.py
"""Convert parsed document to Document IR for RAG chunking."""
"""Build internal link adjacency list for retrieval expansion."""
"""RAG Safety: Comprehensive prompt injection detection"""
"""RAG Safety: Check footnotes for injection"""
```

### 1.2 Document IR Layer

Doxstrux provides a dedicated Intermediate Representation designed for RAG:

```python
from doxstrux.markdown.ir import DocumentIR, DocNode, ChunkPolicy, Chunk

# Key IR components:
# - DocumentIR: Container with security metadata, frontmatter, link graph
# - DocNode: Tree node with id, type, text, meta, span, line_span, children
# - ChunkPolicy: Configuration for chunking (mode, target_tokens, overlap, boundaries)
# - Chunk: Output with chunk_id, section_path, normalized_text, risk_flags
```

**Schema version**: `md-ir@1.0.0` (versioned for stability)

---

## 2. Structure Extraction Quality

### 2.1 Extracted Elements

| Element | Fields | RAG Relevance |
|---------|--------|---------------|
| **Sections** | id, level, title, slug, start_line, end_line, start_char, end_char, parent_id, child_ids, raw_content, text_content | **Critical** - Defines semantic boundaries for chunking |
| **Paragraphs** | id, text, start_line, end_line, section_id, word_count, has_links, has_emphasis, has_code | **High** - Primary content units |
| **Code Blocks** | id, type, language, content, start_line, end_line, section_id | **High** - Technical content preservation |
| **Lists** | id, type, items, items_count, section_id | **Medium** - Structured information |
| **Tables** | headers, rows, column_count, row_count, is_ragged, is_pure | **Medium** - Structured data |
| **Links** | text, url, scheme, allowed, line | **High** - Citations and references |
| **Headings** | id, level, text, slug, parent_heading_id | **Critical** - Hierarchy for retrieval |

### 2.2 Section Hierarchy Preservation

Sections maintain parent-child relationships critical for context:

```python
{
    "id": "section_introduction",
    "level": 1,
    "title": "Introduction",
    "parent_id": None,
    "child_ids": ["section_sub-section"],
    "start_line": 0,
    "end_line": 15,
    "start_char": 0,
    "end_char": 450,
    "text_content": "Full text without markdown syntax..."
}
```

**Why this matters for RAG**:
- Section boundaries define natural chunk points
- Parent-child relationships enable hierarchical retrieval
- Character offsets allow precise citation linking

### 2.3 Content Classification

Every line is classified as prose or code:

```python
result["mappings"] = {
    "line_to_type": {"0": "prose", "5": "code", "6": "code", ...},
    "prose_lines": [0, 1, 2, 3, 4, 10, 11, ...],
    "code_lines": [5, 6, 7, 8, 9],
    "code_blocks": [{"language": "python", "start_line": 5, "end_line": 9}]
}
```

**Why this matters for RAG**:
- Code blocks can be chunked separately with language context
- Prose density informs chunk quality
- Allows code-aware retrieval strategies

---

## 3. Security for RAG Embeddings

### 3.1 Embedding Safety Signals

Doxstrux provides explicit signals for RAG safety:

```python
result["metadata"] = {
    "embedding_blocked": True/False,      # Should this be embedded?
    "embedding_block_reason": "...",      # Why blocked
    "quarantined": True/False,            # Needs review before use
    "quarantine_reasons": ["..."],        # Specific concerns
}
```

### 3.2 Embedding Block Triggers

Content is blocked from embedding when:

| Trigger | Detection | Risk |
|---------|-----------|------|
| Script tags | `<script>` in HTML tokens | XSS in generated responses |
| Event handlers | `onclick`, `onerror`, etc. | Code execution |
| Dangerous schemes | `javascript:`, `vbscript:` | URL hijacking |
| Style injection | `url(javascript:)`, `expression()` | Scriptless XSS |
| Meta refresh | `<meta http-equiv=refresh>` | Redirect attacks |
| Frame elements | `<iframe>`, `<object>`, `<embed>` | Clickjacking |

### 3.3 Quarantine Signals

Documents are quarantined (flagged for review) when:

| Trigger | Reason | Action |
|---------|--------|--------|
| Ragged tables | Data may be corrupted | Review table structure |
| Long footnotes (>512 chars) | Potential payload hiding | Check footnote content |
| Prompt injection in footnotes | Hidden instructions | Strip or review |
| Prompt injection in content | Manipulation attempts | Review or reject |

### 3.4 Prompt Injection Detection

10 patterns detected, fail-closed on error:

```python
from doxstrux.markdown.security.validators import check_prompt_injection

result = check_prompt_injection(text, profile="strict")
# result.suspected: True if injection detected OR validator error
# result.reason: "pattern_match", "validator_error", "no_match"
# result.pattern: Matched pattern string
```

Detected patterns include:
- "ignore previous instructions"
- "disregard previous instructions"
- "system: you are a"
- "pretend you are"
- "act as if"
- "bypass your instructions"
- "override your instructions"

**Scan limits by profile**:
- Strict: 4096 chars (most thorough)
- Moderate: 2048 chars
- Permissive: 1024 chars

---

## 4. Chunking Support

### 4.1 ChunkPolicy Configuration

```python
@dataclass
class ChunkPolicy:
    mode: Literal["semantic", "fixed", "code_aware"] = "semantic"
    target_tokens: int = 600
    overlap_tokens: int = 60
    min_chunk_tokens: int = 100
    max_chunk_tokens: int = 1000
    respect_boundaries: bool = True          # Don't split across sections
    include_code: bool = True
    include_tables: bool = True
    normalize_whitespace: bool = True
    normalize_unicode: bool = True           # NFC normalization
    redact_urls: bool = False               # Strip query params
    token_estimator: Literal["bytes", "chars", "tiktoken"] = "bytes"
    base_url: str | None = None             # Resolve relative links
```

### 4.2 Chunk Output Structure

```python
@dataclass
class Chunk:
    chunk_id: str                           # Stable identifier
    section_path: list[str]                 # ["intro", "background"]
    text: str                               # Raw text
    normalized_text: str                    # Cleaned for embedding
    span: tuple[int, int] | None            # Character offsets
    line_span: tuple[int, int] | None       # Line numbers
    token_estimate: int                     # Token count
    chunk_hash: str                         # SHA256 for deduplication
    risk_flags: list[str]                   # Security warnings
    links: list[dict]                       # Links in chunk
    images: list[dict]                      # Images in chunk
    meta: dict                              # Additional metadata
```

### 4.3 Current Chunking Status

**Note**: The IR layer and data structures exist, but the actual chunker implementation is not yet complete. The architecture is ready:

```python
parser = MarkdownParserCore(content)
ir = parser.to_ir(source_id="docs/intro.md")

# Chunker interface (not yet implemented):
# chunks = chunker.chunk(ir, policy)
```

**What's available now**:
- Section boundaries with precise line/char spans
- Line-level prose/code classification
- Word counts per paragraph
- All raw content preserved

---

## 5. Link Graph for Retrieval Expansion

### 5.1 Internal Link Adjacency

The `link_graph` maps sections to their linked targets:

```python
ir.link_graph = {
    "section_introduction": ["section_background", "section_methods"],
    "section_methods": ["section_results"],
    ...
}
```

**Why this matters for RAG**:
- When retrieving a chunk, also retrieve linked chunks
- Improves context coverage
- Supports graph-based retrieval algorithms

### 5.2 Link Metadata

Each link includes:
```python
{
    "text": "click here",
    "url": "https://example.com/page",
    "line": 42,
    "type": "link",
    "scheme": "https",
    "allowed": True  # RAG safety flag
}
```

---

## 6. Performance Characteristics

### 6.1 Benchmarks

| Metric | Value | Notes |
|--------|-------|-------|
| Parse time (avg) | ~1.02 ms/file | 542 test files |
| Total suite time | ~550 ms | Full 542-file parity test |
| Memory overhead | Minimal | Plain dict outputs, no heavy models |
| Startup time | ~200 ms | Plugin loading |

### 6.2 Scalability

- No recursion in parser (stack-safe for deeply nested documents)
- Configurable recursion depth limits (50-150 by profile)
- Resource budgets prevent DoS:
  - Max nodes: 10K-200K
  - Max table cells: 1K-50K
  - Max content size: 100KB-10MB

---

## 7. Comparison with Alternatives

### 7.1 vs. LangChain MarkdownLoader

| Feature | Doxstrux | LangChain |
|---------|----------|-----------|
| Structure extraction | Full hierarchy | Flat text |
| Section boundaries | Precise spans | Basic splits |
| Security validation | Comprehensive | None |
| Prompt injection detection | Yes | No |
| Embedding safety flags | Yes | No |
| Code block language | Preserved | Lost |
| Table structure | Full | Lost |

### 7.2 vs. Unstructured.io

| Feature | Doxstrux | Unstructured |
|---------|----------|--------------|
| Markdown-specific | Optimized | Generic |
| Token-based parsing | Yes (markdown-it) | Regex-based |
| RAG-specific IR | Yes | No |
| Security profiles | 3 levels | None |
| Performance | ~1ms/file | Slower |
| Dependencies | Minimal | Heavy |

### 7.3 vs. Raw markdown-it-py

| Feature | Doxstrux | Raw markdown-it |
|---------|----------|-----------------|
| Structure extraction | Ready-to-use | DIY |
| Section hierarchy | Built-in | Manual |
| Security layer | Comprehensive | None |
| Chunking support | IR + Policy | None |
| Link graph | Built-in | Manual |

---

## 8. Integration Example

### 8.1 Basic RAG Pipeline Integration

```python
from doxstrux import parse_markdown_file
from your_embedder import embed_text
from your_vectordb import VectorStore

def ingest_document(path: str, store: VectorStore):
    # Parse with security
    result = parse_markdown_file(path, security_profile="strict")

    # Check RAG safety
    if result["metadata"].get("embedding_blocked"):
        reason = result["metadata"].get("embedding_block_reason")
        raise ValueError(f"Document blocked: {reason}")

    if result["metadata"].get("quarantined"):
        reasons = result["metadata"].get("quarantine_reasons", [])
        # Log for review, or skip
        print(f"Quarantined: {reasons}")

    # Extract chunks (manual until chunker implemented)
    for section in result["structure"]["sections"]:
        chunk_text = section["text_content"]
        if not chunk_text:
            continue

        # Create chunk metadata
        metadata = {
            "source": path,
            "section_id": section["id"],
            "section_title": section["title"],
            "level": section["level"],
            "line_start": section["start_line"],
            "line_end": section["end_line"],
        }

        # Embed and store
        embedding = embed_text(chunk_text)
        store.add(embedding, chunk_text, metadata)
```

### 8.2 Using Line Classifications

```python
def get_code_chunks(result):
    """Extract code blocks as separate chunks."""
    for block in result["mappings"]["code_blocks"]:
        yield {
            "text": result["content"]["lines"][block["start_line"]:block["end_line"]],
            "language": block["language"],
            "type": "code"
        }

def get_prose_chunks(result):
    """Extract prose paragraphs."""
    for para in result["structure"]["paragraphs"]:
        yield {
            "text": para["text"],
            "section_id": para["section_id"],
            "word_count": para["word_count"],
            "type": "prose"
        }
```

### 8.3 Using Security Signals

```python
def should_embed(result) -> tuple[bool, str]:
    """Determine if document is safe for embedding."""
    meta = result["metadata"]

    if meta.get("embedding_blocked"):
        return False, meta.get("embedding_block_reason", "blocked")

    if meta.get("quarantined"):
        reasons = meta.get("quarantine_reasons", [])
        # Optional: allow some quarantine reasons
        dangerous = ["prompt_injection_content", "prompt_injection_footnotes"]
        if any(r in str(reasons) for r in dangerous):
            return False, f"quarantined: {reasons}"

    security = meta.get("security", {})
    stats = security.get("statistics", {})

    # Custom thresholds
    if stats.get("has_script"):
        return False, "contains scripts"
    if stats.get("unicode_risk_score", 0) > 2:
        return False, "high unicode risk"

    return True, "safe"
```

---

## 9. Gaps and Limitations

### 9.1 Current Limitations

| Gap | Impact | Workaround |
|-----|--------|------------|
| Chunker not implemented | Manual chunking required | Use section boundaries |
| No tiktoken integration | Token estimates only | Use bytes/chars estimator |
| No PDF/HTML support yet | Markdown only | Convert to markdown first |
| IR tree is flat | No nested children beyond section | Use section hierarchy |

### 9.2 Future Enhancements (Roadmap)

- **Semantic chunker**: Respect boundaries, target token counts
- **tiktoken integration**: Accurate token estimation
- **PDF support**: Extract structure from PDF
- **HTML support**: Parse HTML to same IR
- **Graph retrieval**: Use link graph for expansion

---

## 10. Conclusion

### 10.1 Strengths for RAG

1. **Purpose-built**: Explicit RAG design intent throughout codebase
2. **Security-first**: Embedding safety signals, prompt injection detection
3. **Structure preservation**: Sections, paragraphs, code blocks with precise spans
4. **Metadata richness**: 20+ fields per element enable smart chunking
5. **Content classification**: Line-level prose/code for specialized handling
6. **Link graph**: Built-in retrieval expansion support
7. **Performance**: ~1ms per file, suitable for batch ingestion

### 10.2 Recommended Use Cases

| Use Case | Suitability | Notes |
|----------|-------------|-------|
| Documentation RAG | Excellent | Section hierarchy, code blocks |
| Knowledge base ingestion | Excellent | Security, metadata |
| Code documentation | Excellent | Language-aware code blocks |
| User-submitted content | Excellent | Strict profile, embedding safety |
| Batch document processing | Good | Fast parsing, resource limits |
| Real-time parsing | Good | ~1ms latency |

### 10.3 Final Verdict

**Doxstrux is highly suitable for RAG pipelines.** It was designed specifically for this purpose, provides comprehensive security for embedding safety, extracts rich structure with precise boundaries, and includes an IR layer ready for chunking integration.

The main gap is the unimplemented chunker, but the architecture and data structures are ready. Manual chunking using section boundaries is straightforward until the semantic chunker is complete.

---

## Appendix: Quick Reference

### Parse and Check Safety
```python
from doxstrux import parse_markdown_file

result = parse_markdown_file("doc.md", security_profile="strict")

# Safety check
safe = not result["metadata"].get("embedding_blocked")
quarantined = result["metadata"].get("quarantined")
```

### Access Structure
```python
sections = result["structure"]["sections"]
paragraphs = result["structure"]["paragraphs"]
code_blocks = result["structure"]["code_blocks"]
links = result["structure"]["links"]
```

### Access Mappings
```python
line_types = result["mappings"]["line_to_type"]  # {"0": "prose", "5": "code"}
prose_lines = result["mappings"]["prose_lines"]   # [0, 1, 2, ...]
code_lines = result["mappings"]["code_lines"]     # [5, 6, 7, ...]
```

### Convert to IR
```python
from doxstrux.markdown_parser_core import MarkdownParserCore

parser = MarkdownParserCore(content)
ir = parser.to_ir(source_id="doc.md")
# ir.root, ir.link_graph, ir.security, ir.frontmatter
```
