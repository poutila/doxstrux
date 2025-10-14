# Chunking Strategies with MarkdownParserCore

## Overview

This document explains how to use `MarkdownParserCore` as an intermediary between markdown documents and RAG chunkers, with special focus on overlapping section strategies.

## Architecture: Parser → IR → Chunker

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Markdown   │      │ Document IR │      │   Chunker   │
│  Document   │ ───> │  (Universal │ ───> │  (RAG-     │
│             │      │  Format)    │      │  Optimized) │
└─────────────┘      └─────────────┘      └─────────────┘
```

### Why This Architecture?

1. **Separation of Concerns**: Parsing logic separate from chunking logic
2. **Source Agnostic**: IR works for Markdown, HTML, PDF, DOCX
3. **Stable Contract**: Chunker doesn't need to understand markdown syntax
4. **Security Aware**: Security metadata flows through the pipeline
5. **Optimized for RAG**: Includes spans, IDs, and link graphs

## Basic Usage Pattern

### 1. Parse Document to Structured Data

```python
from doxstrux.markdown_parser_core import MarkdownParserCore

# Parse markdown document
with open('CLAUDE.md', 'r') as f:
    content = f.read()

parser = MarkdownParserCore(content, security_profile='moderate')
result = parser.parse()

# Result contains:
# - result['structure']['sections']: Hierarchical sections
# - result['structure']['headings']: All headings with levels
# - result['structure']['paragraphs']: All paragraphs with line ranges
# - result['structure']['lists']: All lists (regular + task lists)
# - result['structure']['codeblocks']: All code blocks
# - result['structure']['tables']: All tables
# - result['structure']['links']: All links with validation
# - result['metadata']['security']: Security warnings and statistics
```

### 2. Transform to Document IR (Optional but Recommended)

```python
from doxstrux.markdown.ir import DocumentIR, DocNode

# Convert parser result to IR (simplified example)
def to_document_ir(parse_result: dict) -> DocumentIR:
    """Convert parser output to universal IR format."""

    # Build document tree from sections
    root = DocNode(
        id="root",
        type="section",
        text=None,
        children=[]
    )

    # Convert each section to DocNode
    for section in parse_result['structure']['sections']:
        section_node = DocNode(
            id=section['id'],
            type="section",
            text=section.get('title', ''),
            meta={'level': section['level']},
            line_span=(section['start_line'], section['end_line']),
            children=[]
        )

        # Add paragraphs, lists, code blocks as children
        # (Implementation depends on your needs)

        root.children.append(section_node)

    # Create IR
    doc_ir = DocumentIR(
        schema_version="md-ir@1.0.0",
        source_id="CLAUDE.md",
        source_type="markdown",
        security=parse_result['metadata']['security'],
        frontmatter=parse_result.get('frontmatter', {}),
        root=root,
        link_graph={}  # Build from links
    )

    return doc_ir
```

### 3. Chunk with Overlapping Strategies

Now you have multiple overlapping strategies available:

## Overlapping Strategies

### Strategy 1: **Section-Boundary Overlap**
*Best for: Documents with clear hierarchical structure*

```python
def chunk_with_section_overlap(
    parse_result: dict,
    target_tokens: int = 512,
    overlap_sections: int = 1  # Overlap with N previous sections
) -> list[dict]:
    """
    Chunk document with section-based overlap.

    Each chunk includes its section + N previous sections for context.

    Example with overlap_sections=1:
        Chunk 1: [Section A]
        Chunk 2: [Section A (overlap)] + [Section B]
        Chunk 3: [Section B (overlap)] + [Section C]
    """
    chunks = []
    sections = parse_result['structure']['sections']

    for i, section in enumerate(sections):
        chunk_sections = []

        # Add overlapping previous sections
        for j in range(max(0, i - overlap_sections), i + 1):
            chunk_sections.append(sections[j])

        # Extract text from sections
        chunk_text = _extract_section_text(chunk_sections, parse_result)

        chunks.append({
            'chunk_id': f"chunk_{i}",
            'section_path': [s['id'] for s in chunk_sections],
            'text': chunk_text,
            'overlap_context': chunk_sections[:-1],  # All but current
            'primary_section': section,
            'token_estimate': estimate_tokens(chunk_text)
        })

    return chunks
```

**Use Cases:**
- Technical documentation where context from previous sections is critical
- Tutorials with sequential steps
- Policy documents with cumulative rules

**Pros:**
- Maintains logical flow
- Each chunk has built-in context
- Natural boundaries (sections)

**Cons:**
- Variable chunk sizes
- May exceed token limits for large sections

---

### Strategy 2: **Sliding Window with Token Overlap**
*Best for: Fixed-size chunks with guaranteed context*

```python
def chunk_with_sliding_window(
    parse_result: dict,
    target_tokens: int = 512,
    overlap_tokens: int = 50
) -> list[dict]:
    """
    Chunk document with sliding window overlap.

    Each chunk overlaps with previous by N tokens.

    Example with target=512, overlap=50:
        Chunk 1: tokens [0:512]
        Chunk 2: tokens [462:974]    # 50 token overlap
        Chunk 3: tokens [924:1436]   # 50 token overlap
    """
    chunks = []
    paragraphs = parse_result['structure']['paragraphs']

    # Flatten all text with token positions
    full_text = parse_result['content']['raw']
    tokens = tokenize(full_text)  # Use your tokenizer

    start = 0
    chunk_id = 0

    while start < len(tokens):
        end = min(start + target_tokens, len(tokens))

        # Extract chunk
        chunk_tokens = tokens[start:end]
        chunk_text = detokenize(chunk_tokens)

        # Find which sections/paragraphs this chunk spans
        chunk_sections = _find_overlapping_sections(
            start_token=start,
            end_token=end,
            sections=parse_result['structure']['sections']
        )

        chunks.append({
            'chunk_id': f"chunk_{chunk_id}",
            'text': chunk_text,
            'token_range': (start, end),
            'sections': chunk_sections,
            'token_estimate': len(chunk_tokens),
            'overlap_start': max(0, start - overlap_tokens),
            'overlap_end': end
        })

        # Slide window
        start = end - overlap_tokens
        chunk_id += 1

    return chunks
```

**Use Cases:**
- Uniform chunk sizes for embedding models
- Dense retrieval systems
- When section boundaries don't matter

**Pros:**
- Guaranteed token limits
- Consistent overlap
- No information loss at boundaries

**Cons:**
- May split mid-sentence
- No semantic boundaries
- Overlap may include incomplete context

---

### Strategy 3: **Hierarchical Overlap** (Recommended for Complex Docs)
*Best for: Multi-level documents with nested structure*

```python
def chunk_with_hierarchical_overlap(
    parse_result: dict,
    include_ancestors: bool = True,  # Include parent sections
    include_siblings: bool = False,  # Include sibling sections
    max_depth: int = 3  # Max heading levels to include
) -> list[dict]:
    """
    Chunk document with hierarchical context overlap.

    Each chunk includes:
    - Current section
    - All ancestor headings (for context path)
    - Optionally sibling sections

    Example structure:
        # Introduction (H1)
        ## Overview (H2)
        ### Key Concepts (H3)

        Chunk for "Key Concepts":
        - Includes: "Introduction" (H1) + "Overview" (H2) + "Key Concepts" (H3)
        - Context path: Introduction > Overview > Key Concepts
    """
    chunks = []
    sections = parse_result['structure']['sections']

    # Build section hierarchy
    hierarchy = _build_section_tree(sections)

    for section in sections:
        chunk_context = []

        # Add ancestor sections (for breadcrumb context)
        if include_ancestors:
            ancestors = _get_ancestors(section, hierarchy)
            chunk_context.extend(ancestors)

        # Add current section
        chunk_context.append(section)

        # Add sibling sections (if enabled)
        if include_siblings:
            siblings = _get_siblings(section, hierarchy)
            chunk_context.extend(siblings)

        # Build chunk text with hierarchy markers
        chunk_text = _build_hierarchical_text(
            chunk_context,
            parse_result,
            max_depth=max_depth
        )

        chunks.append({
            'chunk_id': section['id'],
            'section_path': [s['title'] for s in chunk_context if s.get('title')],
            'text': chunk_text,
            'context_sections': chunk_context[:-1],  # All but current
            'primary_section': section,
            'level': section['level'],
            'token_estimate': estimate_tokens(chunk_text)
        })

    return chunks
```

**Use Cases:**
- Large documentation with deep nesting
- Knowledge bases with hierarchical organization
- When section context is critical (e.g., "Security Standards" → "Input Validation" → "SQL Injection Prevention")

**Pros:**
- Preserves document structure
- Natural semantic boundaries
- Context-aware retrieval

**Cons:**
- More complex implementation
- Variable chunk sizes
- Potential token overflow for deep hierarchies

---

### Strategy 4: **Semantic Boundary Overlap**
*Best for: Natural language understanding*

```python
def chunk_with_semantic_overlap(
    parse_result: dict,
    target_tokens: int = 512,
    overlap_strategy: str = "sentence"  # "sentence", "paragraph", "section"
) -> list[dict]:
    """
    Chunk document respecting semantic boundaries with overlap.

    Ensures:
    - Never split mid-sentence
    - Paragraphs stay together when possible
    - Code blocks never split
    - Tables never split

    Overlap based on semantic units (sentences/paragraphs).
    """
    chunks = []

    # Extract all semantic units
    units = []
    for para in parse_result['structure']['paragraphs']:
        units.append({
            'type': 'paragraph',
            'text': _extract_text(para, parse_result),
            'line_span': (para['start_line'], para['end_line']),
            'section_id': para['section_id']
        })

    for code in parse_result['structure']['codeblocks']:
        units.append({
            'type': 'code',
            'text': code['content'],
            'language': code.get('language', ''),
            'line_span': (code['start_line'], code['end_line']),
            'section_id': code['section_id']
        })

    # Sort by line position
    units.sort(key=lambda u: u['line_span'][0])

    # Build chunks respecting boundaries
    current_chunk = []
    current_tokens = 0
    overlap_units = []  # Units to include in next chunk

    for unit in units:
        unit_tokens = estimate_tokens(unit['text'])

        # Check if adding this unit exceeds limit
        if current_tokens + unit_tokens > target_tokens and current_chunk:
            # Emit chunk
            chunks.append({
                'chunk_id': f"chunk_{len(chunks)}",
                'units': current_chunk.copy(),
                'text': _join_units(current_chunk),
                'token_estimate': current_tokens,
                'overlap_units': overlap_units.copy()
            })

            # Prepare overlap for next chunk
            if overlap_strategy == "sentence":
                overlap_units = _get_last_n_sentences(current_chunk, n=2)
            elif overlap_strategy == "paragraph":
                overlap_units = [current_chunk[-1]]  # Last paragraph
            elif overlap_strategy == "section":
                overlap_units = _get_section_start(current_chunk)

            # Start new chunk with overlap
            current_chunk = overlap_units.copy()
            current_tokens = sum(estimate_tokens(u['text']) for u in overlap_units)

        # Add unit to current chunk
        current_chunk.append(unit)
        current_tokens += unit_tokens

    # Emit final chunk
    if current_chunk:
        chunks.append({
            'chunk_id': f"chunk_{len(chunks)}",
            'units': current_chunk,
            'text': _join_units(current_chunk),
            'token_estimate': current_tokens,
            'overlap_units': []
        })

    return chunks
```

**Use Cases:**
- Natural language documents (articles, blogs, documentation)
- When embedding models benefit from complete sentences
- Mixed content (text + code + tables)

**Pros:**
- Never splits sentences or code blocks
- Natural semantic units
- Context-aware overlap

**Cons:**
- Variable chunk sizes
- Complex implementation
- Requires sentence boundary detection

---

## Advanced: Hybrid Overlapping Strategy

Combine multiple strategies for optimal results:

```python
def chunk_with_hybrid_overlap(
    parse_result: dict,
    target_tokens: int = 512,
    overlap_tokens: int = 50,
    respect_sections: bool = True,
    include_ancestors: bool = True
) -> list[dict]:
    """
    Hybrid strategy combining:
    1. Section-boundary respect
    2. Token-based overlap
    3. Hierarchical context
    4. Semantic unit preservation
    """
    chunks = []
    sections = parse_result['structure']['sections']

    for section in sections:
        # Get section hierarchy for context
        ancestors = _get_ancestors(section, sections) if include_ancestors else []
        context_text = _build_context_header(ancestors)

        # Extract section content as semantic units
        units = _extract_semantic_units(section, parse_result)

        # Chunk within section using sliding window
        section_chunks = _chunk_units_with_overlap(
            units=units,
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens
        )

        # Add section context to each chunk
        for i, chunk in enumerate(section_chunks):
            chunks.append({
                'chunk_id': f"{section['id']}_chunk_{i}",
                'context_header': context_text,  # Hierarchical context
                'text': chunk['text'],
                'section_path': [s['title'] for s in ancestors] + [section.get('title', '')],
                'token_estimate': chunk['token_estimate'],
                'overlap_prev': chunk.get('overlap_tokens', 0)
            })

    return chunks
```

## Practical Example: Chunking Your CLAUDE.md

```python
from doxstrux.markdown_parser_core import MarkdownParserCore

# Parse CLAUDE.md
with open('src/doxstrux/md_parser_testing/CLAUDEorig.md', 'r') as f:
    content = f.read()

parser = MarkdownParserCore(content)
result = parser.parse()

# Analyze document structure
print(f"Total sections: {len(result['structure']['sections'])}")
print(f"Total headings: {len(result['structure']['headings'])}")
print(f"Total paragraphs: {len(result['structure']['paragraphs'])}")
print(f"Total code blocks: {len(result['structure']['codeblocks'])}")

# Strategy 1: Section-based with hierarchical context
chunks_hierarchical = chunk_with_hierarchical_overlap(
    result,
    include_ancestors=True,
    include_siblings=False
)

print(f"\\nHierarchical chunks: {len(chunks_hierarchical)}")
for chunk in chunks_hierarchical[:3]:
    print(f"  {chunk['section_path']}")
    print(f"  Tokens: {chunk['token_estimate']}")

# Strategy 2: Fixed-size with overlap
chunks_fixed = chunk_with_sliding_window(
    result,
    target_tokens=512,
    overlap_tokens=50
)

print(f"\\nFixed-size chunks: {len(chunks_fixed)}")
for chunk in chunks_fixed[:3]:
    print(f"  Tokens: {chunk['token_estimate']}")
    print(f"  Sections: {[s['id'] for s in chunk['sections']]}")
```

## Key Insights from Your test_output.json

Based on your parsed CLAUDE.md:

```json
{
    "total_lines": 1060,
    "total_chars": 43607,
    "has_sections": true,
    "headings": 108,
    "paragraphs": 416,
    "bullet_lists": 88,
    "code_blocks": 31,
    "tables": 1
}
```

**Recommended Strategy:**
```python
# For CLAUDE.md, use hierarchical overlap due to:
# 1. Deep nesting (108 headings)
# 2. Many lists (88) and code blocks (31)
# 3. Hierarchical structure is critical for context

chunks = chunk_with_hybrid_overlap(
    result,
    target_tokens=512,
    overlap_tokens=50,
    respect_sections=True,
    include_ancestors=True
)
```

This will produce chunks like:
```
Chunk 1: "CLAUDE.md > Mandatory Startup Checklist"
  Context: [Project overview] + [Checklist items]
  Overlap: None (first chunk)

Chunk 2: "CLAUDE.md > Mandatory Startup Checklist > Encoding"
  Context: [Project overview] + [Checklist] + [Encoding section]
  Overlap: Last 50 tokens from Chunk 1

Chunk 3: "CLAUDE.md > Core Principle > Definition of Fact"
  Context: [Project overview] + [Core Principle] + [Fact definition]
  Overlap: Last 50 tokens from Chunk 2
```

## Conclusion

**MarkdownParserCore provides:**
1. **Structured data**: Sections, headings, paragraphs, lists, code blocks
2. **Line/span information**: Exact positions for overlap calculations
3. **Hierarchy**: Section nesting for context-aware chunking
4. **Security metadata**: Warnings and validation for safe chunking

**Chunking strategies enable:**
- **Section overlap**: Context from previous sections
- **Token overlap**: Fixed-size sliding windows
- **Hierarchical overlap**: Ancestor context for nested docs
- **Semantic overlap**: Sentence/paragraph-aware boundaries
- **Hybrid**: Combine multiple strategies for optimal results

The key is choosing the right strategy for your use case and document structure!
