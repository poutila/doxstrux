# DOXSTRUX_REFACTOR_TIMELINE_CORE

Core, reusable parts extracted from the original `DOXSTRUX_REFACTOR_TIMELINE.md`.
This file is intended to stay small, stable, and focused on *how* to run a
disciplined refactor for the markdown/parser stack, without historical noise
or service‑level rollout details.

---

## 1. Purpose

This document defines **how** we plan and control the doxstrux refactor:

- Keep changes **incremental**, with clear phase boundaries.
- Keep tests and CI as the **primary gate** for progress.
- Make every phase **reversible**: at any checkpoint, we can ship or roll back
  without half‑migrated APIs.
- Separate **library refactor** concerns from production rollout details.

It is *not* a history log; it should always describe the **current agreed plan**
for refactoring the parser/warehouse/collector stack.

---

## 2. Phase structure (library only)

We keep three main phases for the *library* refactor itself.

### Phase 0 — Baseline and control

Goal: be sure we understand the current behaviour and can detect regressions.

Core tasks:

- Lock down **current behaviour** with:
  - Golden tests for representative markdown samples.
  - Baseline performance measurements (tokens/s, docs/s) on a fixed corpus.
- Ensure CI has, at minimum:
  - Unit tests (Linux).
  - Type checks (mypy, optional).
  - A smoke test job on Windows (to catch obvious incompatibilities).

Exit criteria:

- All tests passing on main branch.
- A small list of **anchor examples** (markdown inputs + expected IR snippets)
  that we will preserve through the refactor.

### Phase 1 — Internal architecture refactor

Goal: introduce the new architecture while keeping the *external* API stable.

Core steps (library level):

1. Introduce **TokenWarehouse** (already done in the skeleton plan).
2. Introduce **collector model** (single‑pass dispatcher, per‑feature collectors).
3. Introduce the **minimal abstraction layer**:
   - `interfaces.py`: `WarehouseView`, `Collector`, `SecurityValidator`, `PluginManager`.
   - `collector_registry.py`: `default_collectors()` and `register_default_collectors()`.
4. Update the parser shim (`MarkdownParserCore`) to:
   - Depend on `WarehouseView` and `Collector`, not concrete warehouse internals.
   - Call `register_default_collectors(self.warehouse)` instead of wiring each
     collector manually.
   - Accept optional `security_validator` and `plugin_manager` for future
     dependency injection.

Invariants:

- Public API of `MarkdownParserCore` stays compatible (constructor + `parse()`).
- Existing tests for security and IR structure continue to pass.
- New interfaces/registry have their own focused tests.

### Phase 2 — Behaviour tightening & extensions

Goal: make full use of the new abstractions and harden behaviour.

Examples of work that belong here:

- Splitting wide responsibilities into small services:
  - Move security logic behind a concrete `SecurityValidator` that implements
    the protocol.
  - Move markdown‑it plugin wiring into a concrete `PluginManager`.
- Adding new collectors without touching the parser:
  - E.g. a dedicated collector for footnote metadata, or additional structural
    metrics.
- Adding RAG‑specific helpers (e.g. `doxstrux_rag_guard.py`) that consume the
  parser’s metadata and enforce a clear, testable policy.

Exit criteria:

- The new abstractions are actually used (not just present as dead code).
- We can demonstrate adding/removing a collector by editing the registry only.
- RAG guard tests encode the policy: if they pass, the guard behaves as agreed.

---

## 3. Phase/test matrix (core version)

This is a *lightweight* version of the original matrix, focusing only on the
library and the new abstraction layer.

### 3.1 Matrix

| Step | Area                      | Code artifacts                                        | Mandatory tests                                      |
|-----:|---------------------------|-------------------------------------------------------|------------------------------------------------------|
| 0    | Baseline                  | existing parser, tests, CI                            | smoke tests, golden IR tests, basic perf sample      |
| 1    | Warehouse + collectors    | `markdown/utils/token_warehouse.py`, collectors      | `test_token_warehouse_basic`, per‑collector unit     |
| 2    | Interfaces layer          | `markdown/interfaces.py`                              | `test_interfaces_protocols`                          |
| 3    | Collector registry        | `markdown/collector_registry.py`                      | `test_collector_registry_registers_all`             |
| 4    | Parser wiring             | `markdown/parser.py`                                  | `test_parser_uses_registry`, `test_parser_api_compat` |
| 5    | Security integration      | concrete `SecurityValidator` implementation           | `test_security_validator_called`, existing security tests |
| 6    | RAG guard (if used here)  | `doxstrux_rag_guard.py`                               | `test_rag_guard_decisions`                           |

Notes:

- Steps 2–4 are the **minimal additional layer** that fixes most SOLID issues
  (OCP/DIP/ISP) with low risk.
- Step 6 is optional in the library itself; it can live in a separate package
  that imports doxstrux.

---

## 4. CI expectations (library scope)

For this refactor timeline, CI requirements are strictly **library‑level**:

- Linux:
  - Unit tests.
  - Type checks (if enabled).
- Windows:
  - At least a smoke test for running the main test suite or selected
    high‑value tests.
- Optionally, a small performance regression check on a fixed corpus:
  - Parse N markdown files.
  - Compare runtime to baseline with a generous threshold (e.g. within 10–20%).

Production canary rollout, fleet‑wide metrics, and feature flags belong in a
**service‑level** document, not here.

---

## 5. Test design patterns worth preserving

From the original timeline and surrounding work, these patterns are worth
keeping as norms:

1. **Anchor tests before refactor**  
   - Add small, high‑signal tests *before* refactoring, so you can detect
     regressions even if the internals change drastically.

2. **Precise, behaviour‑based assertions**  
   - Avoid “just runs without error” tests wherever possible.
   - Assert on IR structure, security flags, and specific edge‑case behaviour.

3. **Introduce empty tests as TODOs (with `pytest.skip`)**  
   - For planned areas (e.g. new collectors), add tests that explicitly skip
     with a message:
     - “Implement after Step 3 (registry) is complete”.
   - This keeps the test plan visible without failing CI prematurely.

4. **Guard tests for new abstractions**  
   - For `interfaces.py` and `collector_registry.py`, tests should prove that:
     - Concrete collectors satisfy the runtime protocol.
     - The parser actually uses the registry.
     - Removing a collector from the registry changes behaviour in a controlled,
       test‑visible way.

---

## 6. Out of scope for this file

The following topics are intentionally **excluded** from this trimmed timeline
and should live in separate documents:

- Service‑level **canary rollout** strategies (traffic % stages, latency/error
  SLOs, automatic rollback).
- Production **observability** details (Prometheus/Grafana dashboards,
  alerting rules, on‑call runbooks).
- Cross‑repo integration plans (how doxstrux is wired into crawl pipelines,
  web UIs, etc.).

This file is strictly about **library‑level refactor planning and control** for
the markdown/parser stack.
