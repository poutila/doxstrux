# Chunker Implementation Strategy

This document describes how to implement a world-class chunker using the rich output from `MarkdownParserCore`. Based on deep analysis of what the parser provides, not assumptions.

---

## Table of Contents

1. [What We Have](#1-what-we-have)
2. [Chunking Philosophy](#2-chunking-philosophy)
3. [Implementation Strategy](#3-implementation-strategy)
4. [Core Algorithm](#4-core-algorithm)
5. [Token Estimation](#5-token-estimation)
6. [Chunk Types](#6-chunk-types)
7. [API Design](#7-api-design)
8. [Edge Cases](#8-edge-cases)
9. [Implementation Plan](#9-implementation-plan)

---

## 1. What We Have

The parser provides **everything needed** for intelligent chunking. Here's the complete inventory:

### 1.1 Sections (The Gold)

```python
{
    "id": "section_methodology",
    "level": 3,
    "title": "Methodology",
    "slug": "methodology",
    "start_line": 15,
    "end_line": 33,
    "start_char": 286,
    "end_char": 562,
    "parent_id": "section_background",
    "child_ids": [],
    "raw_content": "### Methodology\n\n- Item one\n...",
    "text_content": "Item one. Item two. Item three..."  # NO markdown syntax
}
```

**Chunking value**:
- `text_content` is pre-cleaned prose ready for embedding
- `start_char`/`end_char` enable precise citation linking
- `parent_id`/`child_ids` enable hierarchical context
- `level` enables depth-based splitting decisions

### 1.2 Paragraphs (Atomic Units)

```python
{
    "id": "para_0",
    "text": "This is the introduction paragraph...",
    "start_line": 7,
    "end_line": 8,
    "section_id": "section_introduction",
    "word_count": 10,
    "has_links": False,
    "has_emphasis": True,
    "has_code": False
}
```

**Chunking value**:
- `word_count` enables token estimation without re-parsing
- `section_id` links to parent section for context
- `has_*` flags enable content-aware decisions

### 1.3 Code Blocks (Special Handling)

```python
{
    "id": "code_0",
    "type": "fenced",
    "language": "python",
    "content": "def hello():\n    return 'world'",
    "start_line": 21,
    "end_line": 26,
    "section_id": "section_methodology"
}
```

**Chunking value**:
- `language` enables language-specific embedding models
- `content` is the raw code, preserving whitespace
- Should often be chunked separately from prose

### 1.4 Line Mappings (Classification)

```python
{
    "line_to_type": {"0": "prose", "5": "code", "6": "code"},
    "prose_lines": [0, 1, 2, 3, 4, 10, 11],
    "code_lines": [5, 6, 7, 8, 9],
    "code_blocks": [{"language": "python", "start_line": 5, "end_line": 9}]
}
```

**Chunking value**:
- Enables code-aware chunking strategies
- Can skip or include code based on policy

### 1.5 Raw Content Access

```python
{
    "content": {
        "raw": "# Introduction\n\nThis is...",
        "lines": ["# Introduction", "", "This is..."]
    }
}
```

**Chunking value**:
- Direct line slicing: `lines[start_line:end_line]`
- Character slicing: `raw[start_char:end_char]`

### 1.6 Tables

```python
{
    "id": "table_0",
    "headers": ["Col1", "Col2"],
    "rows": [["a", "b"], ["c", "d"]],
    "start_line": 30,
    "end_line": 34,
    "column_count": 2,
    "row_count": 2,
    "is_ragged": False,
    "is_pure": True
}
```

**Chunking value**:
- Can serialize to text or keep structured
- Row count enables size-based splitting

### 1.7 Security Signals

```python
{
    "embedding_blocked": False,
    "quarantined": False,
    "quarantine_reasons": [],
    "prompt_injection_in_content": False
}
```

**Chunking value**:
- Pre-flight safety check before any chunking
- Per-chunk risk flagging possible

---

## 2. Chunking Philosophy

### 2.1 The Fundamental Insight

**Sections are the natural chunking boundary.**

The parser already did the hard work:
- Sections have `text_content` (cleaned prose)
- Sections have character spans (citation linking)
- Sections have hierarchy (context expansion)
- Sections have known boundaries (never split mid-sentence)

The chunker's job is NOT to re-parse. It's to:
1. Walk the section tree
2. Decide when to split (too big) or merge (too small)
3. Add metadata for retrieval

### 2.2 Core Principles

1. **Never split mid-paragraph** - Paragraphs are atomic
2. **Respect code blocks** - Never split mid-function
3. **Preserve context** - Include section path in every chunk
4. **Stable IDs** - Same input = same chunk IDs (deterministic)
5. **Fail-closed** - Inherit security signals, propagate risk flags

### 2.3 Three Chunking Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **semantic** | Follow section boundaries, merge small sections | Documentation, articles |
| **fixed** | Split at token count, overlap for context | Large homogeneous text |
| **code_aware** | Separate code and prose chunks | Technical documentation |

---

## 3. Implementation Strategy

### 3.1 The Key Realization

We don't need to re-tokenize or re-parse. The parser gives us:

```
Section A (500 chars)
├── Paragraph 1 (word_count=50)
├── Paragraph 2 (word_count=30)
├── Code Block (python, 200 chars)
└── Paragraph 3 (word_count=40)
```

We can estimate tokens from word counts:
- Prose: ~1.3 tokens per word (English average)
- Code: ~0.25 tokens per character (more tokens due to symbols)

### 3.2 The Algorithm Shape

```
1. Pre-flight security check (embedding_blocked?)
2. Build section tree from flat list
3. Walk tree depth-first
4. For each section:
   a. Estimate token count
   b. If under target: consider merging with siblings
   c. If over max: split into sub-chunks
   d. Emit chunk with metadata
5. Post-process: add overlap, compute hashes
```

### 3.3 What We DON'T Need

- No re-parsing of markdown
- No regex for splitting
- No sentence boundary detection (paragraphs are atomic)
- No special handling for lists (already in text_content)

---

## 4. Core Algorithm

### 4.1 Section Tree Builder

The parser gives us flat sections with `parent_id`. Convert to tree:

```python
def build_section_tree(sections: list[dict]) -> dict:
    """Build tree from flat sections with parent_id."""
    by_id = {s["id"]: {**s, "children": []} for s in sections}
    root = {"id": "root", "children": [], "level": 0}

    for section in sections:
        parent_id = section.get("parent_id")
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(by_id[section["id"]])
        else:
            root["children"].append(by_id[section["id"]])

    return root
```

### 4.2 Token Estimation

```python
def estimate_tokens(section: dict, code_blocks: list[dict]) -> int:
    """Estimate token count without re-tokenizing."""
    text_content = section.get("text_content", "")

    # Prose: ~1.3 tokens per word
    word_count = len(text_content.split())
    prose_tokens = int(word_count * 1.3)

    # Code blocks in this section
    code_tokens = 0
    for block in code_blocks:
        if block.get("section_id") == section["id"]:
            # Code: ~0.25 tokens per char (more dense)
            code_tokens += int(len(block.get("content", "")) * 0.25)

    return prose_tokens + code_tokens
```

### 4.3 Chunk Emission

```python
@dataclass
class ChunkBuilder:
    policy: ChunkPolicy
    sections: list[dict]
    code_blocks: list[dict]
    paragraphs: list[dict]
    content_lines: list[str]
    security: dict

    def chunk(self) -> list[Chunk]:
        chunks = []
        tree = build_section_tree(self.sections)

        # Walk tree and emit chunks
        self._walk(tree, [], chunks)

        # Add overlaps if configured
        if self.policy.overlap_tokens > 0:
            chunks = self._add_overlaps(chunks)

        return chunks

    def _walk(self, node: dict, path: list[str], chunks: list[Chunk]):
        """Depth-first walk, emit chunks at boundaries."""
        if node["id"] != "root":
            path = path + [node["id"]]

        # Estimate size
        tokens = estimate_tokens(node, self.code_blocks)

        if tokens <= self.policy.max_chunk_tokens:
            # Fits in one chunk - emit
            self._emit_chunk(node, path, chunks)
        else:
            # Too big - recurse into children or split
            if node.get("children"):
                for child in node["children"]:
                    self._walk(child, path, chunks)
            else:
                # Leaf section too big - split by paragraphs
                self._split_section(node, path, chunks)

    def _emit_chunk(self, section: dict, path: list[str], chunks: list[Chunk]):
        """Emit a chunk for this section."""
        text = section.get("text_content", "")
        if not text.strip():
            return

        # Gather code blocks in this section
        section_code = [
            b for b in self.code_blocks
            if b.get("section_id") == section["id"]
        ]

        # Build chunk
        chunk = Chunk(
            chunk_id=self._make_id(section, path),
            section_path=path,
            text=text,
            normalized_text=self._normalize(text),
            span=(section.get("start_char"), section.get("end_char")),
            line_span=(section.get("start_line"), section.get("end_line")),
            token_estimate=estimate_tokens(section, self.code_blocks),
            chunk_hash=self._hash(path, text),
            risk_flags=self._get_risk_flags(section),
            links=self._get_links_in_range(section),
            images=self._get_images_in_range(section),
            meta={
                "title": section.get("title"),
                "level": section.get("level"),
                "code_blocks": len(section_code),
                "languages": list(set(b.get("language") for b in section_code if b.get("language"))),
            }
        )
        chunks.append(chunk)
```

### 4.4 Splitting Oversized Sections

When a section is too large, split by paragraphs:

```python
def _split_section(self, section: dict, path: list[str], chunks: list[Chunk]):
    """Split a large section into multiple chunks by paragraph."""
    # Get paragraphs in this section
    section_paras = [
        p for p in self.paragraphs
        if p.get("section_id") == section["id"]
    ]

    if not section_paras:
        # No paragraphs - emit as-is (shouldn't happen)
        self._emit_chunk(section, path, chunks)
        return

    # Group paragraphs into chunks
    current_paras = []
    current_tokens = 0
    chunk_index = 0

    for para in section_paras:
        para_tokens = int(para.get("word_count", 0) * 1.3)

        if current_tokens + para_tokens > self.policy.target_tokens and current_paras:
            # Emit current group
            self._emit_para_chunk(section, path, current_paras, chunk_index, chunks)
            chunk_index += 1
            current_paras = []
            current_tokens = 0

        current_paras.append(para)
        current_tokens += para_tokens

    # Emit final group
    if current_paras:
        self._emit_para_chunk(section, path, current_paras, chunk_index, chunks)
```

---

## 5. Token Estimation

### 5.1 Without tiktoken

We can estimate tokens reasonably well without tiktoken:

| Content Type | Ratio | Notes |
|--------------|-------|-------|
| English prose | 1.3 tokens/word | Average for GPT tokenizers |
| Code | 0.25 tokens/char | More tokens due to punctuation |
| Technical prose | 1.5 tokens/word | More specialized terms |
| CJK text | 2.0 tokens/char | Each character often = 1 token |

```python
def estimate_tokens_fast(text: str, is_code: bool = False) -> int:
    """Fast token estimation without tiktoken."""
    if is_code:
        return int(len(text) * 0.25)
    else:
        return int(len(text.split()) * 1.3)
```

### 5.2 With tiktoken (Optional)

For exact counts when needed:

```python
def estimate_tokens_exact(text: str, model: str = "gpt-4") -> int:
    """Exact token count using tiktoken."""
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except ImportError:
        # Fallback to fast estimation
        return estimate_tokens_fast(text)
```

### 5.3 Using Parser's Word Counts

The parser already provides `word_count` for paragraphs:

```python
def section_tokens_from_paragraphs(section_id: str, paragraphs: list[dict]) -> int:
    """Use pre-computed word counts from parser."""
    section_paras = [p for p in paragraphs if p.get("section_id") == section_id]
    total_words = sum(p.get("word_count", 0) for p in section_paras)
    return int(total_words * 1.3)
```

---

## 6. Chunk Types

### 6.1 Prose Chunks

Standard text chunks from sections:

```python
Chunk(
    chunk_id="doc123_section_intro_0",
    section_path=["section_introduction"],
    text="The introduction provides context...",
    normalized_text="the introduction provides context...",
    token_estimate=150,
    meta={"type": "prose", "title": "Introduction"}
)
```

### 6.2 Code Chunks (code_aware mode)

Separate chunks for code blocks:

```python
Chunk(
    chunk_id="doc123_code_0",
    section_path=["section_methodology"],
    text="def hello():\n    return 'world'",
    normalized_text="def hello():\n    return 'world'",
    token_estimate=25,
    meta={
        "type": "code",
        "language": "python",
        "in_section": "Methodology"
    }
)
```

### 6.3 Table Chunks

Tables as structured or text:

```python
# As text
Chunk(
    chunk_id="doc123_table_0",
    text="Header1 | Header2\na | b\nc | d",
    meta={"type": "table", "rows": 2, "cols": 2}
)

# As structured (for specialized retrieval)
Chunk(
    chunk_id="doc123_table_0",
    text="",  # Empty - use meta
    meta={
        "type": "table_structured",
        "headers": ["Header1", "Header2"],
        "rows": [["a", "b"], ["c", "d"]]
    }
)
```

### 6.4 Mixed Chunks

When a section has prose + code, options:

**Option A: Combined** (default)
```python
Chunk(
    text="The function works as follows:\n\ndef hello():\n    return 'world'\n\nThis returns a greeting.",
    meta={"type": "mixed", "has_code": True, "languages": ["python"]}
)
```

**Option B: Split** (code_aware mode)
```python
# Prose chunk
Chunk(text="The function works as follows:", meta={"type": "prose"})
# Code chunk
Chunk(text="def hello():\n    return 'world'", meta={"type": "code"})
# Prose chunk
Chunk(text="This returns a greeting.", meta={"type": "prose"})
```

---

## 7. API Design

### 7.1 Main Entry Point

```python
from doxstrux import parse_markdown_file
from doxstrux.chunker import chunk_document, ChunkPolicy

# Parse
result = parse_markdown_file("doc.md", security_profile="strict")

# Configure chunking
policy = ChunkPolicy(
    mode="semantic",
    target_tokens=500,
    max_chunk_tokens=1000,
    overlap_tokens=50,
    respect_boundaries=True,
    include_code=True,
)

# Chunk
chunks = chunk_document(result, policy)

for chunk in chunks:
    print(f"{chunk.chunk_id}: {chunk.token_estimate} tokens")
    print(f"  Path: {chunk.section_path}")
    print(f"  Risk: {chunk.risk_flags}")
```

### 7.2 Function Signature

```python
def chunk_document(
    parse_result: dict,
    policy: ChunkPolicy | None = None,
    source_id: str = "",
) -> ChunkResult:
    """
    Chunk a parsed markdown document.

    Args:
        parse_result: Output from parse_markdown_file()
        policy: Chunking configuration (defaults to semantic mode)
        source_id: Optional source identifier for chunk IDs

    Returns:
        ChunkResult with chunks, link_graph, stats, errors

    Raises:
        ValueError: If parse_result is missing required fields
        SecurityError: If embedding_blocked and policy doesn't allow
    """
```

### 7.3 Policy Presets

```python
# For documentation
POLICY_DOCS = ChunkPolicy(
    mode="semantic",
    target_tokens=600,
    max_chunk_tokens=1000,
    overlap_tokens=60,
    respect_boundaries=True,
)

# For code-heavy content
POLICY_CODE = ChunkPolicy(
    mode="code_aware",
    target_tokens=400,
    max_chunk_tokens=800,
    include_code=True,
)

# For large homogeneous text
POLICY_FIXED = ChunkPolicy(
    mode="fixed",
    target_tokens=500,
    max_chunk_tokens=600,
    overlap_tokens=100,
)
```

---

## 8. Edge Cases

### 8.1 Empty Sections

```python
# Section with only whitespace
if not section.get("text_content", "").strip():
    continue  # Skip, don't emit empty chunk
```

### 8.2 Single Huge Paragraph

A paragraph larger than `max_chunk_tokens`:

```python
# Option 1: Emit as-is with warning
chunk.risk_flags.append("oversized_paragraph")

# Option 2: Split at sentence boundaries (requires sentence tokenizer)
# NOT recommended - adds dependency and complexity
```

**Recommendation**: Emit as-is with warning. Oversized paragraphs are rare and often intentional (e.g., legal text). Let the embedding model handle truncation.

### 8.3 Code Block Larger Than Max

```python
# Don't split code blocks - they lose meaning
# Emit as-is with warning
if code_tokens > policy.max_chunk_tokens:
    chunk.risk_flags.append("oversized_code_block")
```

### 8.4 Deeply Nested Sections

Document with many nesting levels:

```python
# section_path grows: ["intro", "background", "methodology", "details", "specifics"]
# This is fine - path is metadata, not chunk content
```

### 8.5 Security-Blocked Documents

```python
if parse_result["metadata"].get("embedding_blocked"):
    if policy.allow_blocked:
        # User explicitly allows - emit with risk flags
        for chunk in chunks:
            chunk.risk_flags.append("document_blocked")
    else:
        raise SecurityError("Document is blocked from embedding")
```

### 8.6 Tables Spanning Sections

Tables are always associated with a section via `section_id`. No special handling needed.

### 8.7 Footnotes

Footnotes have content that should be chunked:

```python
# Option 1: Include footnote content in the section where referenced
# Option 2: Emit footnotes as separate chunks
# Recommendation: Option 2 - keeps chunks focused

for footnote in result["structure"]["footnotes"]["definitions"]:
    chunk = Chunk(
        chunk_id=f"{source_id}_footnote_{footnote['label']}",
        text=footnote["content"],
        meta={"type": "footnote", "label": footnote["label"]}
    )
```

---

## 9. Implementation Plan

### 9.1 Phase 1: Core Chunker (MVP)

**Goal**: Semantic chunking that respects section boundaries

**Files**:
- `src/doxstrux/chunker/__init__.py`
- `src/doxstrux/chunker/core.py`
- `src/doxstrux/chunker/estimators.py`

**Implementation**:
```python
# core.py
def chunk_document(parse_result: dict, policy: ChunkPolicy | None = None) -> ChunkResult:
    """Main entry point."""
    policy = policy or ChunkPolicy()

    # Pre-flight
    _check_security(parse_result, policy)

    # Build
    builder = ChunkBuilder(
        policy=policy,
        sections=parse_result["structure"]["sections"],
        paragraphs=parse_result["structure"]["paragraphs"],
        code_blocks=parse_result["structure"]["code_blocks"],
        content_lines=parse_result["content"]["lines"],
        security=parse_result["metadata"]["security"],
    )

    # Chunk
    chunks = builder.chunk()

    # Build result
    return ChunkResult(
        chunks=chunks,
        link_graph=_build_link_graph(chunks, parse_result),
        stats=_compute_stats(chunks),
        errors=[],
    )
```

**Tests**:
- Empty document
- Single section
- Nested sections
- Oversized section
- Code blocks
- Tables

### 9.2 Phase 2: Code-Aware Mode

**Goal**: Separate code and prose chunks

**Implementation**:
- Add `mode="code_aware"` handling in `_walk()`
- Emit code blocks as separate chunks
- Link code chunks to their section context

### 9.3 Phase 3: Overlap & Deduplication

**Goal**: Add overlap for context, deduplicate

**Implementation**:
```python
def _add_overlaps(self, chunks: list[Chunk]) -> list[Chunk]:
    """Add overlap text from previous chunk."""
    if not self.policy.overlap_tokens:
        return chunks

    result = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            prev_text = chunks[i-1].normalized_text
            overlap = self._get_last_n_tokens(prev_text, self.policy.overlap_tokens)
            chunk.text = overlap + "\n\n" + chunk.text
            chunk.meta["has_overlap"] = True
        result.append(chunk)

    return result
```

### 9.4 Phase 4: tiktoken Integration (Optional)

**Goal**: Exact token counts

**Implementation**:
```python
# estimators.py
class TokenEstimator:
    def __init__(self, method: str = "bytes", model: str = "gpt-4"):
        self.method = method
        self.model = model
        self._tiktoken = None

        if method == "tiktoken":
            import tiktoken
            self._tiktoken = tiktoken.encoding_for_model(model)

    def estimate(self, text: str, is_code: bool = False) -> int:
        if self.method == "tiktoken" and self._tiktoken:
            return len(self._tiktoken.encode(text))
        elif self.method == "chars":
            return len(text)
        else:  # bytes
            if is_code:
                return int(len(text) * 0.25)
            return int(len(text.split()) * 1.3)
```

---

## 10. Summary

### 10.1 The Key Insight

**The parser already did the hard work.** Sections have:
- Clean text content (no markdown)
- Precise character/line spans
- Hierarchical relationships
- Word counts for estimation

The chunker's job is simple:
1. Walk the section tree
2. Estimate sizes
3. Emit chunks that respect boundaries
4. Add metadata for retrieval

### 10.2 What Makes This "Dream Chunker"

1. **No re-parsing** - Uses parser's rich output directly
2. **Semantic boundaries** - Never splits mid-paragraph or mid-code
3. **Hierarchical context** - Section path in every chunk
4. **Security-aware** - Inherits and propagates risk flags
5. **Precise citations** - Character spans enable exact linking
6. **Fast estimation** - Token counts without tiktoken
7. **Deterministic** - Same input = same chunks (stable IDs)
8. **Minimal dependencies** - Just the parser output

### 10.3 Implementation Priority

1. Core chunker with semantic mode
2. Code-aware mode + tests
3. Overlap + deduplication
4. tiktoken integration (optional)

The architecture is ready. The data is there. The chunker is just a tree walk with size checks.
