# DOXSTRUX_NEXT_STEPS.md - Parser/Warehouse/Collector/Registry Refactor Execution

**Status**: Phase 0.0 - 📋 PLANNED  
**Version**: 0.1  
**Last Updated**: 2025-12-12 04:00 UTC  
**Last Verified**: -  

**Related Documents**:
- DOXSTRUX_SPEC.md — Single source of truth for parser/warehouse/collector/registry wiring and contracts
- DOXSTRUX_SOLID_ANALYSIS.md — Pre-refactor diagnosis (archived, context only)

---

## Current Status

### Quick Status Dashboard

| Phase | Status | Tests | Files Changed | Clean Table |
|-------|--------|-------|---------------|-------------|
| 0.0 - Baseline Golden Tests (SPEC §8 Step 0) | 📋 PLANNED | 0/N | 0 | - |
| 1.0 - Infrastructure (interfaces, registry, warehouse) | 📋 PLANNED | 0/N | 0 | - |
| 2.0 - Parser Wiring (SPEC §8 Step 2) | 📋 PLANNED | 0/N | 0 | - |
| 3.0 - Collector Conformance (SPEC §8 Step 3) | 📋 PLANNED | 0/N | 0 | - |

> This document is an execution checklist. All normative behaviour and contracts come from **DOXSTRUX_SPEC.md** (especially §§2–6, 8).  

---

## Prerequisites

**ALL must be verified before starting Phase 0.0**:

- [ ] **Working virtual environment + uv**: You can run tests via `uv`.
  ```bash
  uv run python -c "import sys; print(sys.version)"
 doxstrux importable: Current package is installable and importable.

bash
Kopioi koodi
uv run python -c "import doxstrux; print(getattr(doxstrux, '__version__', 'no-version'))"
 Existing test suite green: Before refactor, all tests must pass.

bash
Kopioi koodi
uv run pytest
# Expected: all existing tests pass
Quick Verification:

bash
Kopioi koodi
uv run pytest
# Expected: test run completes successfully with no failures before refactor work starts
Phase 0.0 - Baseline Golden Tests (SPEC §8 Step 0)
Goal: Lock in current observable behaviour so regressions are caught.
Estimated Time: 2–4 hours
Clean Table Required: Yes
Spec Reference: DOXSTRUX_SPEC §8 “Execution Steps — Step 0”

Task 0.0.1: Per-Collector Golden Tests
 Design per-collector fixtures:

For each collector in collectors_phase8.* that will be returned by default_collectors() (per DOXSTRUX_SPEC §4), design at least one small markdown input that meaningfully exercises that collector’s behaviour (not just “non-empty” output).

Align with the examples / expectations described for collectors in DOXSTRUX_SPEC (e.g. headings include level, text, line).

 Implement per-collector tests:

Create or extend tests that:

Parse the markdown fixture through the current MarkdownParserCore (pre-refactor wiring).

Assert on structural properties of each collector’s output (e.g. for headings: exact levels/text/line triples for the sample input), in line with DOXSTRUX_SPEC §5–§7.

Keep these tests focused and deterministic.

Test Immediately:

bash
Kopioi koodi
uv run pytest -q
# Expected:
# - New golden tests run and pass against CURRENT implementation
# - No existing tests regress
Clean Table Check:

 Every collector that will be registered via default_collectors() has at least one golden test with structural assertions (per DOXSTRUX_SPEC §8 Step 0 “Per-collector”).

 Tests clearly document which collector(s) they are anchoring.

 No TODOs or “placeholder assertion” comments remain in these golden tests.

 Full test suite green (uv run pytest).

Task 0.0.2: Security Golden Test
 Select a security-sensitive document:

Choose a markdown input that triggers existing security flags in the current implementation (whatever the current security layer is doing today).

 Add a dedicated security baseline test:

Parse the document via MarkdownParserCore.parse() and capture the current security-related metadata output (keys and critical values).

Assert that, for this document, both keys and critical values (e.g. blocked=True, at least one issue code) match the current behaviour, as required by DOXSTRUX_SPEC §8 “Security” row.

Test Immediately:

bash
Kopioi koodi
uv run pytest -q -k "security"
# Expected: the new security baseline test passes and uses CURRENT behaviour as ground truth
Clean Table Check:

 At least one test exists that pins security metadata keys and critical values (as in DOXSTRUX_SPEC §8).

 The test name / comment clearly identifies it as a “pre-refactor baseline”.

 No test relies on internal details beyond what DOXSTRUX_SPEC considers observable metadata.

 uv run pytest still fully green.

Phase 0.0 Final Validation
0.0 Success Criteria:

 All collectors covered by at least one golden test with structural assertions (per DOXSTRUX_SPEC §8 Step 0).

 Security baseline test exists and passes.

 Entire test suite passes in the pre-refactor state.

Test Commands:

bash
Kopioi koodi
uv run pytest
Clean Table Check for Phase 0.0:

 No failing tests.

 No “TODO” / “fix later” markers left in new golden tests.

 DOXSTRUX_SPEC §8 Step 0 requirements demonstrably satisfied.

 Code and tests are in a coherent, production-ready state before structural changes start.

Phase 1.0 - Infrastructure (interfaces, registry, warehouse)
Goal: Add the new abstraction layer (interfaces, registry, warehouse wiring) with no behaviour change.
Estimated Time: 3–6 hours
Clean Table Required: Yes
Spec References: DOXSTRUX_SPEC §§3–5, §8 Step 1

Task 1.0.1: Implement interfaces.py (DOXSTRUX_SPEC §3)
 Create doxstrux/markdown/interfaces.py:

Implement DispatchContext, CollectorInterest, and Collector protocol exactly as described in DOXSTRUX_SPEC §3 (fields, semantics, and intentional weakness of the protocol).

 Update imports where needed:

Do not change behaviour; only introduce the new types and verify they import cleanly.

Test Immediately:

bash
Kopioi koodi
uv run python -c "from doxstrux.markdown.interfaces import DispatchContext, CollectorInterest, Collector; print('OK')"
# Expected: prints 'OK' with no ImportError
Clean Table Check:

 interfaces.py contents match DOXSTRUX_SPEC §3.

 No additional responsibilities or types added beyond those described in DOXSTRUX_SPEC.

 Existing tests still pass (uv run pytest).

 No TODOs or placeholders in interfaces.py.

Task 1.0.2: Implement collector_registry.py (DOXSTRUX_SPEC §4)
 Create doxstrux/markdown/collector_registry.py:

Implement default_collectors() and register_default_collectors(warehouse) as described in DOXSTRUX_SPEC §4.

Ensure imports of collector classes match the intended layout (per the spec) and only this module is tightly coupled to concrete collectors.

 Ensure no change in runtime behaviour yet:

Do not yet call these functions from the parser — that is Phase 2.0.

Test Immediately:

bash
Kopioi koodi
uv run python - << 'PY'
from doxstrux.markdown.collector_registry import default_collectors, register_default_collectors
class DummyWarehouse:
    def __init__(self):
        self.calls = []
    def register_collector(self, collector):
        self.calls.append(collector.name)

# This will fail until TokenWarehouse additions exist; for now just ensure default_collectors() instantiates collectors.
collectors = default_collectors()
print([c.name for c in collectors])
PY
# Expected: script runs and prints a list of collector names without ImportError
Clean Table Check:

 collector_registry.py matches DOXSTRUX_SPEC §4 (no extra responsibilities).

 No implicit behaviour changes: registry module exists but is not yet used by the parser.

 All tests still pass (uv run pytest).

Task 1.0.3: Add TokenWarehouse additions (DOXSTRUX_SPEC §5)
 Extend existing TokenWarehouse (location per current repo; follow DOXSTRUX_SPEC §5.2–§5.3):

Add _collectors and _routing attributes to __init__, as described in the spec (append-only additions; do not change constructor signature or existing fields).

Implement register_collector, _get_collectors_for, dispatch_all, and finalize_all exactly as described in DOXSTRUX_SPEC §5.3, including duplicate-key behaviour.

 Keep existing methods and semantics untouched:

Do not alter existing indexing/text/section helpers beyond what DOXSTRUX_SPEC explicitly allows.

Test Immediately:

bash
Kopioi koodi
uv run python - << 'PY'
from doxstrux.markdown.token_warehouse import TokenWarehouse

# Instantiate using existing constructor to ensure signature unchanged
try:
    tw = TokenWarehouse(...)  # replace with the current required args from existing code
except TypeError as e:
    raise SystemExit(f"Constructor signature changed unexpectedly: {e}")
print("TokenWarehouse instantiation OK (args unchanged)")
PY
# Expected: Constructor still accepts the existing argument pattern.
# (You may need to update the "..." to match the real signature in your codebase.)
Adjust the instantiation call to match your actual current constructor; the important part is: no signature change.

Clean Table Check:

 _collectors and _routing added exactly as an extension, not a rewrite, of __init__.

 New methods (register_collector, _get_collectors_for, dispatch_all, finalize_all) match DOXSTRUX_SPEC §5 in behaviour and signatures.

 All existing tests pass (no observable behaviour change yet).

 No new TODOs introduced in token_warehouse.py.

Phase 1.0 Final Validation
1.0 Success Criteria:

 interfaces.py and collector_registry.py exist and match DOXSTRUX_SPEC §§3–4.

 TokenWarehouse has new attributes and methods per DOXSTRUX_SPEC §5, with constructor signature unchanged.

 No code outside of TokenWarehouse/registry/interfaces yet depends on the new registry wiring (parser still uses old wiring).

 Full test suite passes.

Test Commands:

bash
Kopioi koodi
uv run pytest
Clean Table Check for Phase 1.0:

 All success criteria met.

 No failing tests or new warnings.

 No half-migrated wiring in the parser (either old wiring or the new registry-based wiring, not a mix).

 DOXSTRUX_SPEC §§3–5 are faithfully implemented without extra scope.

Phase 2.0 - Parser Wiring (SPEC §6, §8 Step 2)
Goal: Switch MarkdownParserCore to use collector_registry + TokenWarehouse.dispatch_all() without touching security/caching/metadata logic.
Estimated Time: 2–4 hours
Clean Table Required: Yes
Spec References: DOXSTRUX_SPEC §6, §8 Step 2

Task 2.0.1: Replace manual wiring with registry calls
 Update parser imports:

Import register_default_collectors from doxstrux.markdown.collector_registry as per DOXSTRUX_SPEC §6.

 Replace manual collector construction with:

python
Kopioi koodi
register_default_collectors(self.warehouse)
self.warehouse.dispatch_all()
metadata = self.warehouse.finalize_all()
exactly where DOXSTRUX_SPEC §6 indicates, preserving all surrounding logic.

 Do not touch:

Security prechecks,

Tokenization,

Security policy application,

Metadata assembly beyond swapping in metadata from finalize_all().

Test Immediately:

bash
Kopioi koodi
uv run pytest
# Expected:
# - All tests, including the golden tests from Phase 0.0, still pass.
Clean Table Check:

 Parser no longer imports concrete collectors directly (only collector_registry per DOXSTRUX_SPEC §6).

 Only the wiring lines are changed; security, caching, and metadata logic untouched.

 Golden collector tests from Phase 0.0 still pass, confirming collector outputs remain structurally identical.

 Security baseline test from Phase 0.0 still passes.

Phase 2.0 Final Validation
2.0 Success Criteria:

 Parser wiring matches DOXSTRUX_SPEC §6 (registry-based).

 All tests (including golden and security baselines) pass.

 No new imports of concrete collectors exist outside collector_registry.py.

Test Commands:

bash
Kopioi koodi
uv run pytest
Clean Table Check for Phase 2.0:

 All success criteria met.

 Code is stable and production-ready with new wiring.

 No TODO comments left in parser around collector wiring.

Phase 3.0 - Collector Conformance (SPEC §7, §8 Step 3)
Goal: Update each collector to implement Collector protocol (surface) without changing algorithms.
Estimated Time: 4–8 hours (depending on number/complexity of collectors)
Clean Table Required: Yes
Spec References: DOXSTRUX_SPEC collector expectations (e.g. §§5–7), §8 Step 3

Task 3.0.1: Update collectors to implement Collector protocol
 For each collector in collectors_phase8.* that will participate in default_collectors():

Add or confirm .name and .interest attributes per DOXSTRUX_SPEC (types/tags as appropriate).

Implement should_process, on_token, and finalize signatures matching Collector in interfaces.py.

Ensure that finalize() returns a dict whose keys do not collide with other collectors (as enforced by finalize_all() in DOXSTRUX_SPEC §5).

 No algorithmic changes:

Logic for what is collected and how is preserved; only the wiring and protocol surface are updated.

Test Immediately:

bash
Kopioi koodi
uv run pytest -q
# Expected:
# - All tests pass, including per-collector golden tests.
Clean Table Check:

 Each collector used by the registry conforms to the Collector protocol surface (name, interest, should_process, on_token, finalize).

 Phase 0.0 golden tests for each collector still pass without modification (or with purely mechanical updates to adapt to new interfaces).

 No collector introduces duplicate keys in finalize() that would break finalize_all().

Phase 3.0 Final Validation
3.0 Success Criteria:

 All registry-registered collectors conform to Collector as defined in DOXSTRUX_SPEC §3.

 All tests (including golden and security) green.

 No direct parser–collector coupling remains; all wiring flows through collector_registry and TokenWarehouse.

Test Commands:

bash
Kopioi koodi
uv run pytest
Clean Table Check for Phase 3.0:

 Success criteria met.

 No TODOs or placeholder comments in collectors.

 Code is production-ready with the new architecture.

File Changes Summary
File	Action	Phase
doxstrux/markdown/interfaces.py	CREATE	1.0
doxstrux/markdown/collector_registry.py	CREATE	1.0
doxstrux/markdown/token_warehouse.py	UPDATE (add attributes + methods per SPEC §5)	1.0
doxstrux/markdown/parser.py	UPDATE (wiring only, per SPEC §6)	2.0
doxstrux/markdown/collectors_phase8/*.py	UPDATE (protocol conformance only)	3.0
tests/...	UPDATE/CREATE (golden tests + security baseline per SPEC §8)	0.0–3.0

Exact test file paths are left to the implementation; this table captures which areas must change, not new specifications.

Success Criteria (Overall)
 DOXSTRUX_SPEC §§3–6 are fully implemented in code (interfaces, registry, warehouse additions, parser wiring).

 Execution Steps in DOXSTRUX_SPEC §8 (Steps 0–3) are satisfied: baselines, infrastructure, wiring, collector conformance.

 Public API of MarkdownParserCore remains compatible (DOXSTRUX_SPEC §9).

 All tests pass:

bash
Kopioi koodi
uv run pytest
 Clean Table achieved after Phase 3.0.

Clean Table Principle
A final answer is considered CLEAN only if ALL of the following are true:

✅ No unresolved errors, warnings, TODOs, placeholders

✅ No unverified assumptions

✅ No duplicated or conflicting logic

✅ Solution is canonical and production-ready

✅ No workarounds masking symptoms

Each checkbox must be fully complete before proceeding to next phase.

What's Next
After this document is complete (Phases 0.0–3.0 done and Clean Table achieved):

Consider whether any small SPEKSI-style spec is needed for long-term governance of this architecture (separate document, derived from DOXSTRUX_SPEC, not a replacement).

Revisit RAG-focused guards and integration (e.g. doxstrux_rag_guard.py) as a separate, higher-level concern — not part of the parser/warehouse/collector/registry refactor governed here.

End of DOXSTRUX_NEXT_STEPS.md
