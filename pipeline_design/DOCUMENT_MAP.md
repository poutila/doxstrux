# Document Map

**Cross-document link graph and validation for documentation corpora.**

**Status:** Design only — not implemented

---

## 1. Overview

Document Map builds a validated dependency graph from a collection of markdown documents by analyzing internal links.

```
docs/
├── index.md       → [getting-started.md, api.md]
├── getting-started.md → [api.md, #installation]
├── api.md         → [examples.md, ../changelog.md]
└── examples.md    → [api.md]

↓ make_document_map()

DocumentMap:
  nodes: 4 documents
  edges: 6 links
  broken: 1 (../changelog.md not found)
  orphans: 0
```

**Core Use Cases:**

1. **Broken link detection** — Find links to non-existent files/anchors
2. **Orphan detection** — Find documents with no incoming links
3. **Dependency analysis** — Understand document relationships
4. **RAG link expansion** — Feed graph to retrieval pipeline

---

## 2. Relationship to Existing Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         doxstrux (core)                         │
│                                                                 │
│  parse_markdown_file() → result["structure"]["links"]           │
│  DocumentIR.link_graph → per-document section links             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOCUMENT MAP (this)                        │
│                                                                 │
│  make_document_map(paths) → cross-document link graph           │
│  Validates: file exists, anchor exists, no cycles               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        doxstrux-rag                             │
│                                                                 │
│  pipeline.get_link_graph() → uses document map for expansion    │
│  RetrievalPipeline(link_graph=...) → retrieval with expansion   │
└─────────────────────────────────────────────────────────────────┘
```

**Design Decision:** Document Map is a standalone utility that can be used:
- Without RAG (just link validation)
- With RAG (feed graph to retrieval pipeline)

---

## 3. API Design

### 3.1 Main Entry Point

```python
from doxstrux import make_document_map

# From file list
doc_map = make_document_map(
    paths=["docs/index.md", "docs/api.md"],
    check_targets=True,      # Validate internal links resolve
    check_anchors=False,     # Validate #anchor targets exist
    include_external=False,  # Include external URLs in graph
)

# From directory
doc_map = make_document_map(
    paths=Path("docs/"),
    pattern="**/*.md",       # Glob pattern for directory
)
```

### 3.2 DocumentMap Output

```python
@dataclass
class DocumentMap:
    # Graph structure
    nodes: dict[str, DocumentNode]      # path → node
    edges: list[DocumentEdge]           # all links

    # Validation results
    broken_links: list[BrokenLink]      # target not found
    orphan_documents: list[str]         # no incoming links
    circular_refs: list[list[str]]      # cycles (A→B→C→A)

    # Statistics
    stats: MapStats

    def to_adjacency_list(self) -> dict[str, list[str]]:
        """For RAG link expansion."""

    def to_dot(self) -> str:
        """Graphviz DOT format."""

    def to_mermaid(self) -> str:
        """Mermaid diagram format."""
```

### 3.3 Supporting Types

```python
@dataclass
class DocumentNode:
    path: str                           # Normalized path
    title: str | None                   # First H1 or filename
    anchors: set[str]                   # Available #anchors
    outgoing: list[str]                 # Links from this doc
    incoming: list[str]                 # Links to this doc

@dataclass
class DocumentEdge:
    source: str                         # Source document path
    target: str                         # Target (path or path#anchor)
    line: int | None                    # Line number in source
    link_type: str                      # "internal", "anchor", "external"
    valid: bool                         # Target exists

@dataclass
class BrokenLink:
    source: str
    target: str
    line: int | None
    reason: str                         # "file_not_found", "anchor_not_found"

@dataclass
class MapStats:
    document_count: int
    link_count: int
    broken_count: int
    orphan_count: int
    external_count: int
```

---

## 4. Link Resolution Rules

### 4.1 Internal Links

| Link Format | Resolution |
|-------------|------------|
| `./file.md` | Relative to current file |
| `../file.md` | Parent directory |
| `file.md` | Same directory |
| `/docs/file.md` | Absolute from root |
| `#anchor` | Same file anchor |
| `file.md#anchor` | File + anchor |

### 4.2 External Links (Optional)

When `include_external=True`:

| Link Format | Handling |
|-------------|----------|
| `https://...` | Stored in graph, not validated |
| `http://...` | Stored in graph, not validated |
| `mailto:...` | Ignored |

### 4.3 Anchor Extraction

When `check_anchors=True`, anchors are extracted from:

1. Heading slugs: `## My Section` → `#my-section`
2. Explicit IDs: `{#custom-id}`
3. HTML anchors: `<a id="anchor">`

---

## 5. Use Cases

### 5.1 CI Link Validation

```python
doc_map = make_document_map(Path("docs/"), check_targets=True, check_anchors=True)

if doc_map.broken_links:
    for link in doc_map.broken_links:
        print(f"{link.source}:{link.line}: broken link to {link.target}")
    sys.exit(1)
```

### 5.2 Documentation Health Report

```python
doc_map = make_document_map(Path("docs/"))

print(f"Documents: {doc_map.stats.document_count}")
print(f"Links: {doc_map.stats.link_count}")
print(f"Broken: {doc_map.stats.broken_count}")
print(f"Orphans: {len(doc_map.orphan_documents)}")

for orphan in doc_map.orphan_documents:
    print(f"  - {orphan} (no incoming links)")
```

### 5.3 RAG Link Expansion

```python
from doxstrux import make_document_map
from doxstrux_rag import RetrievalPipeline, ExpansionPolicy

# Build map during indexing
doc_map = make_document_map(Path("docs/"))

# Use for retrieval expansion
retrieval = RetrievalPipeline(
    ...,
    link_graph=doc_map.to_adjacency_list(),
    expansion_policy=ExpansionPolicy(enabled=True),
)
```

### 5.4 Visualization

```python
doc_map = make_document_map(Path("docs/"))

# Mermaid (for GitHub/GitLab)
print(doc_map.to_mermaid())
# graph LR
#   index.md --> getting-started.md
#   index.md --> api.md
#   getting-started.md --> api.md

# Graphviz DOT
with open("docs.dot", "w") as f:
    f.write(doc_map.to_dot())
# dot -Tpng docs.dot -o docs.png
```

---

## 6. CLI Interface

```bash
# Validate links
doxstrux map docs/ --check-anchors
# docs/api.md:45: broken link to ../changelog.md (file not found)
# docs/guide.md:12: broken link to #instalation (anchor not found, did you mean #installation?)

# Generate report
doxstrux map docs/ --format json > map.json

# Generate diagram
doxstrux map docs/ --format mermaid > docs.mmd
doxstrux map docs/ --format dot | dot -Tpng -o docs.png

# Find orphans
doxstrux map docs/ --orphans-only
# docs/old-api.md (no incoming links)
```

---

## 7. Implementation Notes

### 7.1 Algorithm

```
1. Collect all .md files from paths
2. For each file:
   a. Parse with doxstrux (extract links, headings)
   b. Extract available anchors from headings
   c. Normalize all link targets to absolute paths
3. Build adjacency graph
4. Validate:
   a. For each internal link, check target file exists
   b. For each anchor link, check anchor exists in target
5. Find orphans (nodes with in-degree 0, excluding index/root)
6. Find cycles (optional, via DFS)
```

### 7.2 Performance Considerations

- Lazy parsing: only parse files when needed for anchor validation
- Caching: cache parsed results for repeated access
- Streaming: for large corpora, don't load all into memory

### 7.3 Edge Cases

| Case | Handling |
|------|----------|
| Circular references | Detected, reported, not an error |
| Self-links (`#anchor`) | Valid if anchor exists |
| Case sensitivity | Platform-aware (Linux sensitive, macOS/Windows not) |
| URL-encoded paths | Decode before resolution |
| Non-markdown targets | Valid (e.g., `schema.json`) if file exists |

---

## 8. Package Placement Decision

**Options:**

| Location | Pros | Cons |
|----------|------|------|
| `doxstrux` (core) | No extra dependency, natural fit | Adds multi-file scope to single-file parser |
| `doxstrux-rag` | Already handles multi-doc | Overkill if you just want link validation |
| `doxstrux-map` (new) | Clean separation | Another package to maintain |

**Recommendation:** Add to `doxstrux` core as `doxstrux.map` submodule.

Rationale:
- Link extraction already in core
- No new dependencies required
- Natural progression: parse one → map many
- RAG can import and extend

---

## 9. Future Extensions

### 9.1 Anchor Suggestion

```python
# When anchor not found, suggest closest match
BrokenLink(
    target="api.md#authenication",
    reason="anchor_not_found",
    suggestion="authentication"  # Levenshtein distance
)
```

### 9.2 Link Health Over Time

```python
# Track link health across commits
doxstrux map docs/ --compare-to HEAD~10
# +2 new broken links since abc123
# -1 broken link fixed
```

### 9.3 External Link Validation

```python
doc_map = make_document_map(
    paths,
    validate_external=True,  # HTTP HEAD requests
    external_timeout=5.0,
)
```

---

## 10. Non-Goals

Explicitly out of scope:

1. **Content analysis** — Map is structural, not semantic
2. **Link rewriting** — Detection only, no auto-fix
3. **External validation** — No HTTP requests by default
4. **Real-time watching** — Batch operation only
5. **Cross-format** — Markdown only (no RST, AsciiDoc)

---

## 11. Summary

Document Map provides:

| Feature | Description |
|---------|-------------|
| `make_document_map()` | Build validated link graph from docs |
| Broken link detection | Find links to non-existent targets |
| Orphan detection | Find unreferenced documents |
| Anchor validation | Verify #anchor targets exist |
| RAG integration | Feed graph to retrieval expansion |
| Visualization | DOT, Mermaid output formats |
| CLI | `doxstrux map docs/` |

**Implementation status:** Design complete, not implemented.
