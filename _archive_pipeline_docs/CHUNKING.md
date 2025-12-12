# Chunking

This document describes the semantic chunker for doxstrux, designed to create optimal chunks for RAG embedding.

**Status:** Architecture complete, implementation pending

---

## 1. Philosophy

### 1.1 The Key Insight

**The parser already did the hard work.** Sections have:
- Clean `text_content` (markdown syntax stripped)
- Precise character/line spans
- Hierarchical parent-child relationships
- Word counts per paragraph

The chunker's job is simple: walk the section tree, estimate sizes, and emit chunks that respect semantic boundaries.

### 1.2 Core Principles

1. **Never split mid-paragraph** — Paragraphs are atomic
2. **Never split mid-code-block** — Functions lose meaning when split
3. **Respect section boundaries** — Sections define semantic units
4. **Preserve context** — Include section path in every chunk
5. **Stable IDs** — Same input = same chunk IDs (deterministic)
6. **Fail-closed** — Inherit security signals, propagate risk flags

---

## 2. Chunking Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **semantic** | Follow section boundaries, merge small sections | Documentation, articles |
| **fixed** | Split at token count with overlap | Large homogeneous text |
| **code_aware** | Separate code and prose chunks | Technical documentation |

---

## 3. ChunkPolicy Configuration

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
    redact_urls: bool = False                # Strip query params
    token_estimator: Literal["bytes", "chars", "tiktoken"] = "bytes"
    base_url: str | None = None              # Resolve relative links
```

### 3.1 Policy Presets

```python
# For documentation
POLICY_DOCS = ChunkPolicy(
    mode="semantic",
    target_tokens=600,
    max_chunk_tokens=1000,
    overlap_tokens=60,
)

# For code-heavy content
POLICY_CODE = ChunkPolicy(
    mode="code_aware",
    target_tokens=400,
    max_chunk_tokens=800,
)

# For large homogeneous text
POLICY_FIXED = ChunkPolicy(
    mode="fixed",
    target_tokens=500,
    max_chunk_tokens=600,
    overlap_tokens=100,
)

# For PDFs (higher overlap due to context loss)
POLICY_PDF = ChunkPolicy(
    mode="semantic",
    target_tokens=500,
    overlap_tokens=75,
)
```

---

## 4. Chunk Output Structure

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

---

## 5. Algorithm

### 5.1 Overview

```
1. Pre-flight security check (embedding_blocked?)
2. Build section tree from flat list
3. Walk tree depth-first
4. For each section:
   a. Estimate token count
   b. If under target: consider merging with siblings
   c. If over max: split at paragraph boundaries
   d. Emit chunk with metadata
5. Post-process: add overlap, compute hashes
```

### 5.2 Section Tree Builder

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

### 5.3 Token Estimation

```python
def estimate_tokens(section: dict, code_blocks: list[dict]) -> int:
    """Estimate token count without re-tokenizing."""
    text_content = section.get("text_content", "")

    # Prose: ~1.3 tokens per word
    word_count = len(text_content.split())
    prose_tokens = int(word_count * 1.3)

    # Code blocks in this section: ~0.25 tokens per char
    code_tokens = 0
    for block in code_blocks:
        if block.get("section_id") == section["id"]:
            code_tokens += int(len(block.get("content", "")) * 0.25)

    return prose_tokens + code_tokens
```

### 5.4 Tree Walk and Emission

```python
def _walk(node: dict, path: list[str], chunks: list[Chunk], policy: ChunkPolicy):
    """Depth-first walk, emit chunks at boundaries."""
    if node["id"] != "root":
        path = path + [node["id"]]

    tokens = estimate_tokens(node, code_blocks)

    if tokens <= policy.max_chunk_tokens:
        # Fits in one chunk — emit
        chunks.append(create_chunk(node, path, tokens))
    elif node["children"]:
        # Too big but has children — recurse
        for child in node["children"]:
            _walk(child, path, chunks, policy)
    else:
        # Too big, no children — split at paragraph boundaries
        chunks.extend(split_at_paragraphs(node, path, policy))
```

---

## 6. Edge Cases

### 6.1 Empty Sections

```python
if not section.get("text_content", "").strip():
    continue  # Skip, don't emit empty chunk
```

### 6.2 Single Huge Paragraph

A paragraph larger than `max_chunk_tokens`:

```python
# Emit as-is with warning — oversized paragraphs are rare
chunk.risk_flags.append("oversized_paragraph")
```

Don't split at sentence boundaries (adds complexity and dependencies).

### 6.3 Code Block Larger Than Max

```python
# Don't split code blocks — they lose meaning
if code_tokens > policy.max_chunk_tokens:
    chunk.risk_flags.append("oversized_code_block")
```

### 6.4 Security-Blocked Documents

```python
if parse_result["metadata"]["security"]["embedding_blocked"]:
    if policy.allow_blocked:
        # User explicitly allows — emit with risk flags
        for chunk in chunks:
            chunk.risk_flags.append("document_blocked")
    else:
        raise SecurityError("Document is blocked from embedding")
```

### 6.5 Footnotes

Emit footnotes as separate chunks:

```python
for footnote in result["structure"]["footnotes"]["definitions"]:
    chunks.append(Chunk(
        chunk_id=f"{source_id}_footnote_{footnote['label']}",
        text=footnote["content"],
        meta={"type": "footnote", "label": footnote["label"]}
    ))
```

---

## 7. API

### 7.1 Main Entry Point

```python
from doxstrux import parse_markdown_file
from doxstrux.chunker import chunk_document, ChunkPolicy

# Parse
result = parse_markdown_file("doc.md", security_profile="strict")

# Chunk
policy = ChunkPolicy(mode="semantic", target_tokens=500)
chunk_result = chunk_document(result, policy)

for chunk in chunk_result.chunks:
    print(f"{chunk.chunk_id}: {chunk.token_estimate} tokens")
    print(f"  Path: {chunk.section_path}")
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

### 7.3 ChunkResult

```python
@dataclass
class ChunkResult:
    chunks: list[Chunk]
    link_graph: dict[str, list[str]]  # chunk_id → linked chunk_ids
    stats: dict                        # Processing statistics
    errors: list[str]                  # Non-fatal errors
```

---

## 8. Token Estimators

```python
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

## 9. What Makes This Design Effective

1. **No re-parsing** — Uses parser's rich output directly
2. **Semantic boundaries** — Never splits mid-paragraph or mid-code
3. **Hierarchical context** — Section path in every chunk
4. **Security-aware** — Inherits and propagates risk flags
5. **Precise citations** — Character spans enable exact linking
6. **Fast estimation** — Token counts without tiktoken dependency
7. **Deterministic** — Same input = same chunks (stable IDs)
8. **Minimal dependencies** — Just the parser output
