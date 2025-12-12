# DOXSTRUX_REFACTOR

Canonical plan for the doxstrux markdown parser refactor.

---

## 1. Problem

`MarkdownParserCore` is a 2075-line God Object with 49 methods handling 8 responsibilities. Key violations:

| Principle | Issue |
|-----------|-------|
| SRP | 8 responsibilities in one class |
| OCP | Extractors hardcoded, no registry |
| DIP | Parser imports 11 concrete modules |

**Goal:** Split the God Object. Parser orchestrates; warehouse owns tokens and dispatch; collectors extract features; registry wires them together.

---

## 2. Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Parser (MarkdownParserCore)                            │
│  Orchestrates: markdown-it → warehouse → collectors     │
├─────────────────────────────────────────────────────────┤
│  Registry (collector_registry.py)                       │
│  Knows which collectors to register. Single edit point. │
├─────────────────────────────────────────────────────────┤
│  Warehouse (TokenWarehouse)                             │
│  Owns tokens, topology, text slicing, dispatch loop.    │
├─────────────────────────────────────────────────────────┤
│  Collectors (collectors_phase8.*)                       │
│  12 single-purpose extractors. Implement Collector.     │
└─────────────────────────────────────────────────────────┘
```

**New modules:**
- `interfaces.py` — `DispatchContext`, `CollectorInterest`, `Collector` protocol
- `collector_registry.py` — `default_collectors()`, `register_default_collectors()`

**Unchanged:** Security code paths, plugin configuration, parser API signature.

**Current API (must remain compatible):**
```python
MarkdownParserCore(content: str, *, config: dict | None = None, security_profile: str | None = None)
parse(self) -> dict
```

See **DOXSTRUX_ARCHITECTURE_SPEC.md** for type definitions.

---

## 3. Phases

### Phase 0 — Baseline

| Task | Output |
|------|--------|
| Lock behaviour | Golden tests for representative markdown |
| Anchor examples | 5-10 inputs + expected IR snippets |
| CI green | Unit tests, type checks (Linux), smoke (Windows) |

**Exit:** All tests pass. Anchors documented.

### Phase 1 — Architecture Split

| Step | Change |
|------|--------|
| 1.1 | Add `interfaces.py` (DispatchContext, CollectorInterest, Collector) |
| 1.2 | Add `collector_registry.py` (default_collectors, register_default_collectors) |
| 1.3 | Update TokenWarehouse: add register_collector, dispatch_all, finalize_all |
| 1.4 | Update parser: call `register_default_collectors(warehouse)` instead of manual wiring |
| 1.5 | Conform collectors to Collector protocol |

**Exit:** Parser no longer imports concrete collectors. Registry is single edit point. Existing tests pass.

### Mandatory Tests (Phase 1)

Three high-signal tests:

1. **`test_parser_registry_wiring`** — Verify default collectors are registered and used (via monkeypatch or by checking known collector output in result).
2. **`test_parser_api_compatible`** — `MarkdownParserCore(content, ...)` and `parse() -> dict` signatures unchanged.
3. **`test_anchor_examples_preserved`** — Golden IR tests still pass.

---

## 4. Future Work

Not part of this refactor. Revisit only when concrete need arises:

- **SecurityValidator protocol** — If multiple security profiles needed
- **PluginManager protocol** — If plugin strategies diverge
- **Warehouse protocol** — If alternate implementations emerge
- **RAG guard** — Separate integration layer

---

## 5. Scope

**In scope:** Parser, warehouse, collectors, registry. Library-level only.

**Out of scope:** Service rollout, observability, cross-repo integration, RAG pipelines.

---

## 6. References

| Document | Purpose |
|----------|---------|
| DOXSTRUX_ARCHITECTURE_SPEC.md | Type definitions, concrete specs |
| DOXSTRUX_SOLID_ANALYSIS.md | Pre-refactor diagnosis (archived) |
