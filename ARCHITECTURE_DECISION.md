# Architecture Decision: Package Boundaries

## The Question

Should we:
1. **Keep doxstrux focused** - Leave as markdown parser, develop others separately
2. **Extend doxstrux** - Add chunker, embedder, stores here
3. **Monorepo** - Everything in one place but separate packages

---

## Current State Analysis

### What doxstrux IS today:

```
doxstrux/
├── markdown_parser_core.py    # Core parser (1944 lines)
├── api.py                     # Public API
├── markdown/
│   ├── config.py              # Security profiles
│   ├── budgets.py             # Resource limits
│   ├── exceptions.py          # Custom exceptions
│   ├── ir.py                  # Document IR (for chunking)
│   ├── extractors/            # 11 element extractors
│   ├── security/              # Validators
│   └── utils/                 # Helpers
└── md_parser_testing/         # Test utilities
```

**Core competency**: Markdown structure extraction with security
**Dependencies**: markdown-it-py, mdit-py-plugins, pyyaml, charset-normalizer, polars

### What we've designed (in docs):

| Component | Dependencies | Coupling to doxstrux |
|-----------|--------------|---------------------|
| **Chunker** | None new | HIGH - uses parser output directly |
| **Embedder** | openai, sentence-transformers | NONE - generic text in, vectors out |
| **VectorStore** | chromadb, qdrant-client, pinecone, psycopg2 | NONE - generic vectors + metadata |
| **HTML Scraper** | beautifulsoup4, html2text | LOW - produces markdown for parser |
| **PDF Extractor** | pymupdf, marker-pdf | LOW - produces markdown for parser |
| **Web Crawler** | crawl4ai (playwright) | LOW - produces markdown for parser |

---

## Option Analysis

### Option 1: Keep doxstrux Focused (Recommended)

```
doxstrux/                    # Markdown parsing + security
├── parser
├── extractors
├── security
├── ir.py
└── chunker/                 # ADD: Tight coupling to parser output

doxstrux-rag/                # Separate package
├── embedders/
├── stores/
└── pipeline.py

doxstrux-scrapers/           # Separate package (or individual)
├── html_scraper.py
├── pdf_extractor.py
└── web_crawler.py
```

**Pros:**
- Clear boundaries, single responsibility
- Users install only what they need
- Independent versioning and release cycles
- Smaller dependency footprint per package
- Easier testing (isolated concerns)
- Follows Unix philosophy: do one thing well

**Cons:**
- Multiple packages to maintain
- Coordination overhead for breaking changes
- Users need to install multiple packages

**Dependency graph:**
```
doxstrux (core)
    ↑
    ├── doxstrux-rag (embedders + stores)
    │       ↑
    │       └── your-app
    │
    └── doxstrux-scrapers (optional)
            ↑
            └── your-app
```

### Option 2: Extend doxstrux (Everything Here)

```
doxstrux/
├── parser/                  # Core (existing)
├── chunker/                 # ADD
├── rag/                     # ADD
│   ├── embedders/
│   └── stores/
└── scrapers/                # ADD
    ├── html.py
    ├── pdf.py
    └── web.py
```

**Pros:**
- Single import, single install
- Unified versioning
- Easier for users (one package)
- Simpler documentation

**Cons:**
- **Dependency explosion**: openai, chromadb, qdrant-client, pinecone, sentence-transformers, playwright, pymupdf, beautifulsoup4...
- Users who just want parsing get 500MB+ of deps
- Harder to test (complex dep matrix)
- Slower CI/CD
- Conflicting dependency versions
- Package becomes "kitchen sink"

**pyproject.toml nightmare:**
```toml
dependencies = [
    # Core (current)
    "markdown-it-py>=4.0.0",
    "mdit-py-plugins>=0.5.0",
    # ...

    # Embedders
    "openai>=1.0.0",
    "sentence-transformers>=2.0.0",
    "torch>=2.0.0",  # 2GB+

    # Stores
    "chromadb>=0.4.0",
    "qdrant-client>=1.0.0",
    "pinecone-client>=2.0.0",
    "psycopg2-binary>=2.9.0",

    # Scrapers
    "beautifulsoup4>=4.12.0",
    "html2text>=2020.1.16",
    "pymupdf>=1.23.0",
    "marker-pdf>=0.2.0",
    "crawl4ai>=0.7.0",
    "playwright>=1.40.0",
]
# Total: 50+ transitive dependencies, 3GB+ installed size
```

### Option 3: Monorepo with Separate Packages

```
doxstrux-project/
├── packages/
│   ├── doxstrux/            # pip install doxstrux
│   ├── doxstrux-rag/        # pip install doxstrux-rag
│   └── doxstrux-scrapers/   # pip install doxstrux-scrapers
├── pyproject.toml           # Workspace config
└── docs/                    # Shared docs
```

**Pros:**
- Separate packages but shared repo
- Atomic commits across packages
- Shared CI/CD
- Easier refactoring

**Cons:**
- Complex tooling (uv workspaces, hatch, poetry)
- Still multiple packages to publish
- Overkill for this scope

---

## Recommendation: Option 1 with Twist

### Keep doxstrux focused, but add the chunker here.

**Why chunker belongs in doxstrux:**
1. **Tight coupling**: Chunker directly consumes parser's `ir.py` structures
2. **Same domain**: Both are about document structure
3. **No new dependencies**: Just tree walking + token estimation
4. **Natural API**: `parse() → chunk()` in one package
5. **Already have `ir.py`**: ChunkPolicy, Chunk dataclasses exist

**Why embedders/stores should be separate:**
1. **No coupling to parser**: Generic text → vector transformation
2. **Heavy dependencies**: torch, chromadb, etc.
3. **Different concerns**: Infrastructure vs document processing
4. **User choice**: Many won't need RAG, just parsing

**Why scrapers should be separate:**
1. **Independent**: They produce markdown, parser consumes it
2. **Heavy dependencies**: playwright, pymupdf
3. **Optional**: Most users have markdown already

### Proposed Structure

```
# Package 1: doxstrux (this repo)
# pip install doxstrux
doxstrux/
├── parser/                  # Existing
├── chunker/                 # ADD (no new deps)
├── ir.py                    # Existing (shared types)
└── security/                # Existing

# Package 2: doxstrux-rag (new repo)
# pip install doxstrux-rag
doxstrux-rag/
├── embedders/
│   ├── openai.py
│   ├── local.py
│   └── hybrid.py
├── stores/
│   ├── chroma.py
│   ├── qdrant.py
│   ├── pinecone.py
│   └── pgvector.py
├── models.py                # RAGChunk, EmbeddedChunk
└── pipeline.py              # Unified interface

# Package 3: doxstrux-ingest (new repo, optional)
# pip install doxstrux-ingest
doxstrux-ingest/
├── html.py                  # BeautifulSoup scraper
├── pdf.py                   # PyMuPDF/Marker
├── web.py                   # Crawl4AI wrapper
└── enhancers.py             # Markdown cleanup
```

### Dependency Flow

```
┌─────────────────────────────────────────────────────┐
│                    Your Application                  │
└─────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  doxstrux   │      │doxstrux-rag │      │doxstrux-ing │
│  (parser +  │◄─────│ (embedders  │      │   (scrapers │
│   chunker)  │      │  + stores)  │      │  + crawlers)│
└─────────────┘      └─────────────┘      └─────────────┘
      │                    │                    │
      │                    │                    │
markdown-it-py        openai             crawl4ai
pyyaml               chromadb            pymupdf
                     sentence-           playwright
                     transformers
```

### User Experience

```python
# Minimal: Just parsing
pip install doxstrux

from doxstrux import parse_markdown_file
result = parse_markdown_file("doc.md")

# With chunking (same package)
from doxstrux.chunker import chunk_document, ChunkPolicy
chunks = chunk_document(result, ChunkPolicy())

# Full RAG pipeline
pip install doxstrux doxstrux-rag

from doxstrux import parse_markdown_file
from doxstrux.chunker import chunk_document
from doxstrux_rag import create_pipeline

pipeline = create_pipeline(embedder="openai", store="chroma")
result = parse_markdown_file("doc.md")
chunks = chunk_document(result)
pipeline.embed_and_store(chunks)

# With web scraping
pip install doxstrux doxstrux-rag doxstrux-ingest

from doxstrux_ingest import WebCrawler
from doxstrux import parse_markdown_string
from doxstrux.chunker import chunk_document
from doxstrux_rag import create_pipeline

crawler = WebCrawler()
markdown = crawler.crawl("https://docs.example.com")
result = parse_markdown_string(markdown)
# ...
```

---

## Action Plan

### Phase 1: Add Chunker to doxstrux (This Repo)

```
src/doxstrux/
├── chunker/
│   ├── __init__.py
│   ├── policy.py          # ChunkPolicy config
│   ├── estimators.py      # Token estimation
│   ├── semantic.py        # Semantic chunking
│   ├── fixed.py           # Fixed-size chunking
│   └── code_aware.py      # Code-aware chunking
```

**No new dependencies. Uses existing `ir.py` types.**

### Phase 2: Create doxstrux-rag (New Repo)

```
doxstrux-rag/
├── src/doxstrux_rag/
│   ├── __init__.py
│   ├── models.py
│   ├── embedders/
│   └── stores/
├── pyproject.toml
└── tests/
```

**Dependencies:**
```toml
dependencies = [
    "doxstrux>=0.3.0",  # For RAGChunk compatibility
]

[project.optional-dependencies]
openai = ["openai>=1.0.0"]
local = ["sentence-transformers>=2.0.0"]
chroma = ["chromadb>=0.4.0"]
qdrant = ["qdrant-client>=1.0.0"]
pinecone = ["pinecone-client>=3.0.0"]
pgvector = ["psycopg2-binary>=2.9.0", "sqlalchemy>=2.0.0"]
all = ["doxstrux-rag[openai,local,chroma,qdrant,pinecone,pgvector]"]
```

### Phase 3: Create doxstrux-ingest (New Repo, Optional)

```
doxstrux-ingest/
├── src/doxstrux_ingest/
│   ├── __init__.py
│   ├── html.py
│   ├── pdf.py
│   └── web.py
├── pyproject.toml
└── tests/
```

**Dependencies:**
```toml
[project.optional-dependencies]
html = ["beautifulsoup4>=4.12.0", "html2text>=2020.1.16"]
pdf-fast = ["pymupdf>=1.23.0", "pymupdf4llm>=0.0.5"]
pdf-accurate = ["marker-pdf>=0.2.0"]
web = ["crawl4ai>=0.7.0"]
all = ["doxstrux-ingest[html,pdf-fast,web]"]
```

---

## Summary

| Component | Package | Reason |
|-----------|---------|--------|
| Parser | `doxstrux` | Core competency |
| Extractors | `doxstrux` | Core competency |
| Security | `doxstrux` | Core competency |
| IR types | `doxstrux` | Shared foundation |
| **Chunker** | **`doxstrux`** | **Tight coupling, no deps** |
| Embedders | `doxstrux-rag` | Heavy deps, generic |
| Vector Stores | `doxstrux-rag` | Heavy deps, infrastructure |
| HTML Scraper | `doxstrux-ingest` | Optional, different concern |
| PDF Extractor | `doxstrux-ingest` | Optional, heavy deps |
| Web Crawler | `doxstrux-ingest` | Optional, heavy deps |

### Final Answer

**Add chunker here. Everything else in separate packages.**

The chunker is the natural extension of the parser - it's just "what do I do with the parsed structure?" without adding any dependencies. The embedders, stores, and scrapers are infrastructure that many users won't need.

This follows the principle: **Make the common case easy, make the complex case possible.**

```python
# Common case: parse + chunk (one package)
from doxstrux import parse_markdown_file
from doxstrux.chunker import chunk_document

# Complex case: full RAG pipeline (opt-in)
from doxstrux_rag import create_pipeline
from doxstrux_ingest import WebCrawler
```
