# Doxstrux Documentation

## Document Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOXSTRUX.md                                     │
│                         doxstrux package                                     │
│                                                                              │
│  Parser: API, output structure, security model                               │
│  Chunker: policy, algorithm, API                                             │
│  Document IR, architecture, performance                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           │                                                 │
           ▼                                                 ▼
┌─────────────────────────────┐               ┌─────────────────────────────┐
│      DOXSTRUX_RAG.md        │               │      DEVELOPMENT.md         │
│     doxstrux-rag package    │               │     Contributing rules      │
│                             │               │                             │
│ Embedders, vector stores    │               │ Python env, testing         │
│ Indexing pipeline           │               │ Workflow, pitfalls          │
│ Retrieval pipeline          │               │                             │
│ Prompt templates            │               │                             │
└─────────────────────────────┘               └─────────────────────────────┘
```

---

## Packages

| Package | Install | Purpose |
|---------|---------|---------|
| `doxstrux` | `pip install doxstrux` | Parse markdown, chunk for RAG |
| `doxstrux-rag` | `pip install doxstrux-rag[openai,chroma]` | Embed, store, retrieve |

---

## Reading Order

**Users:** `DOXSTRUX.md` → `DOXSTRUX_RAG.md`

**Contributors:** `DEVELOPMENT.md` first

---

## What Changed

### Before: 7 Documents (~7,500 lines)

| Document | Issue |
|----------|-------|
| AI_ASSISTANT_USER_MANUAL | Mixed concerns |
| RAG_SUITABILITY | Duplicated content |
| CHUNKER_IMPLEMENTATION | Separated from parser |
| SCRAPING_PIPELINE | Overlap with other pipelines |
| WEB_CRAWLER_PIPELINE | Overlap with other pipelines |
| PDF_PIPELINE | Overlap with other pipelines |
| EMBEDDER_VECTORSTORE | Duplicated chunker content |

### After: 3 Documents (1,278 lines)

| Document | Lines | Focus |
|----------|-------|-------|
| DOXSTRUX.md | 488 | Parser + Chunker (one package) |
| DOXSTRUX_RAG.md | 545 | Indexing + Retrieval (one package) |
| DEVELOPMENT.md | 245 | Contributing rules |

**Result:** 82% reduction (7,500 → 1,278), zero duplication, package-aligned.

---

## Key Decisions

1. **One doc per package** — Clear ownership, no cross-referencing
2. **Chunker with parser** — Tightly coupled, version together
3. **Indexing with retrieval** — Same system, same users
4. **Input adapters not packaged** — Use existing libs, just patterns in docs
