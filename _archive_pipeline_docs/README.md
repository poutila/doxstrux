# Doxstrux Documentation

Restructured documentation for the doxstrux RAG pipeline toolkit.

---

## Document Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DOXSTRUX_REFERENCE.md                                 │
│                         (Master Document)                                    │
│                                                                              │
│  • Core philosophy          • Public API                                     │
│  • Output structure         • Security model                                 │
│  • Configuration            • Document IR                                    │
│  • Architecture             • Performance                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
       ┌────────────────┬───────────┴───────────┬────────────────┐
       │                │                       │                │
       ▼                ▼                       ▼                ▼
┌────────────┐  ┌────────────────┐  ┌───────────────────┐  ┌────────────┐
│CHUNKING.md │  │RAG_PIPELINES.md│  │RETRIEVAL_PIPELINES│  │DEVELOPMENT │
│            │  │  (doxstrux-rag)│  │    (doxstrux-rag) │  │    .md     │
│            │  │                │  │                   │  │            │
│• Chunking  │  │• Input adapters│  │• Query embedding  │  │• Critical  │
│  modes     │  │• Embedders     │  │• Security filter  │  │  rules     │
│• Algorithm │  │• Vector stores │  │• Link expansion   │  │• Testing   │
│• Policy    │  │• Indexing      │  │• Context assembly │  │• Workflow  │
│            │  │  pipeline      │  │• Prompt templates │  │            │
└────────────┘  └────────────────┘  └───────────────────┘  └────────────┘
```

---

## Package Boundaries

These docs describe components across multiple packages:

| Document | Package | Status |
|----------|---------|--------|
| DOXSTRUX_REFERENCE.md | `doxstrux` | Implemented |
| CHUNKING.md | `doxstrux` | Pending |
| RAG_PIPELINES.md | `doxstrux-rag` | Design |
| RETRIEVAL_PIPELINES.md | `doxstrux-rag` | Design |
| DEVELOPMENT.md | `doxstrux` | Implemented |

See `ARCHITECTURE_DECISION.md` for package separation rationale.

---

## Reading Order

**For users:** Start with `DOXSTRUX_REFERENCE.md` for API and output structure, then `RAG_PIPELINES.md` for integration.

**For implementers:** Read `CHUNKING.md` to understand chunker design, `RETRIEVAL_PIPELINES.md` for query-time operations.

**For AI assistants/developers:** Read `DEVELOPMENT.md` first for critical rules.

---

## What Changed

### Before: 7 Documents (~7,500 lines)

| Document | Lines | Issue |
|----------|-------|-------|
| AI_ASSISTANT_USER_MANUAL | 675 | Mixed concerns |
| RAG_SUITABILITY | 528 | Evaluation + duplicated content |
| CHUNKER_IMPLEMENTATION | 846 | Design + duplicated parser output |
| SCRAPING_PIPELINE | 1,171 | Full pipeline with overlap |
| WEB_CRAWLER_PIPELINE | 1,271 | Full pipeline with overlap |
| PDF_PIPELINE | 1,276 | Full pipeline with overlap |
| EMBEDDER_VECTORSTORE | 1,752 | Storage + duplicated chunker |

**Problems:**
- Security model described 4 times
- Parser output structure described 3 times
- Parser integration code nearly identical in 3 documents
- Same chunker usage pattern repeated everywhere
- ~40% content was duplicated

### After: 5 Documents (~2,200 lines)

| Document | Lines | Focus |
|----------|-------|-------|
| DOXSTRUX_REFERENCE | 413 | Single source for doxstrux core |
| CHUNKING | 345 | Chunker design only |
| RAG_PIPELINES | 608 | Indexing: adapters + embedders + stores |
| RETRIEVAL_PIPELINES | 509 | Retrieval: query + context + prompts |
| DEVELOPMENT | 359 | AI assistant rules + testing |

**Improvements:**
- ~77% reduction in total content (7,500 → 1,725 lines)
- Zero duplication of security model, output structure, or integration code
- Clear ownership: each concept has exactly one home
- Modular: update one place, effects propagate

---

## Cross-References

When information was consolidated, I preserved the relationships:

| Topic | Now Lives In | Referenced By |
|-------|--------------|---------------|
| Security profiles | DOXSTRUX_REFERENCE §4 | RAG_PIPELINES §6 |
| Parser output structure | DOXSTRUX_REFERENCE §3 | CHUNKING §— (uses) |
| Chunk output structure | CHUNKING §4 | RAG_PIPELINES §7 |
| Embedding safety checks | DOXSTRUX_REFERENCE §4.3 | RAG_PIPELINES §6.2 |
| Testing infrastructure | DEVELOPMENT §2 | — |
