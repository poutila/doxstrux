# THREE_ADDITIONS Implementation Plan

**Based on**: THREE_ADDITIONS.md v2.7.0
**Created**: 2025-12-12
**Lifecycle**: Disposable execution guide. Will drift. Not part of formal SSOT.

This is a **procedural execution plan**, not a behavioral specification. For behavior, see `THREE_ADDITIONS.md`. This plan points to invariants by reference; it does not redefine them.

**Scope**: This plan will drift as tooling/paths change. Treat commands as examples for current environment, not permanent contracts.

**Version guard**: If `THREE_ADDITIONS.md` version ≠ 2.7.0, re-review this plan before executing. Invariant numbers/meanings may have changed.

---

## Current Environment Notes (will drift)

These are current as of plan creation. Adjust as needed:

```bash
# Preferred Python runner (use project's configured runner)
PYTHON=".venv/bin/python"  # or "uv run python" if using uv

# Test command
TEST_CMD="$PYTHON -m pytest"
```

---

## Pre-Implementation Checklist

- [ ] Read `CLAUDE.md` parser output section — confirm current parse result structure and line indexing convention
- [ ] Run existing baseline tests — all must pass
- [ ] Confirm CRLF test fixture exists (e.g., in `tools/test_mds/`)
- [ ] Create feature branch

---

## Phase 1 — Content Normalization

**Behavioral spec**: THREE_ADDITIONS.md INV-1.1 through INV-1.8

### Step 1.1: Write failing tests for INV-1.1, INV-1.2, INV-1.3

Create `TestLineEndingNormalization` with tests per THREE_ADDITIONS.md spec.

**Checkpoint**: Tests exist and FAIL (TDD red phase). Exact failure count depends on test granularity.

---

### Step 1.2: Write failing tests for INV-1.4

Create `TestUnicodeNormalization` with tests per spec.

**Checkpoint**: Tests exist and FAIL

---

### Step 1.3: Write failing tests for INV-1.5, INV-1.6

Create `TestNormalizationSecurity` with tests per spec.

**Prerequisite check**: Before writing these tests, verify that the security patterns you plan to test (e.g., `javascript:` scheme, confusables) are **already detected** by the current `metadata.security` implementation. If not, either:
- Expand security detection as part of this phase (document this scope expansion), or
- Choose patterns that are already detected

**Checkpoint**: Tests exist and FAIL (or pass if security already detects on raw input)

---

### Step 1.4: Write failing tests for INV-1.7

Create `TestNormalizationIdempotence` per spec.

**Checkpoint**: Tests exist and FAIL

---

### Step 1.5: Write failing tests for INV-1.8

Create `TestRawInputPreservation` per spec.

**Checkpoint**: Tests exist and FAIL

---

### Step 1.6: Implement normalization

Implement `_normalize_content()` method satisfying INV-1.1 through INV-1.4 and INV-1.7. See THREE_ADDITIONS.md "Implementation Guidance (Non-Normative)" for suggested approach.

**Checkpoint**: Method exists, not yet integrated

---

### Step 1.7: Integrate normalization into parser

Modify parser to:
1. Preserve raw input per INV-1.8
2. Run security checks on raw input per architectural guidance in spec
3. Normalize before parsing

**Verification**: Add or confirm a test that security detection works on raw CRLF input (e.g., pattern split across `\r\n`). This validates the check order.

**Checkpoint**: All Phase 1 tests pass

---

### Step 1.8: Expose `original_content` in parse result

Per INV-1.8.

**Checkpoint**: `TestRawInputPreservation` passes

---

### Step 1.9: Regenerate affected baselines

Normalization will change outputs for CRLF and potentially other fixtures. Regenerate baselines and **review all diffs**:
- Expected: CRLF fixtures show no trailing `\r` in lines
- Review any unexpected diffs in other fixtures (Unicode, old Mac `\r`)

**Checkpoint**: Diffs reviewed and accepted; baselines committed

---

### Step 1.10: Run full baseline test suite

**Checkpoint**: All baseline tests pass

---

### Step 1.11: Clean Table check for Phase 1

Per `.claude/rules/CLEAN_TABLE_PRINCIPLE.md` plus:
- [ ] All Phase 1 tests pass
- [ ] Baselines regenerated and verified

**Commit**: Phase 1 complete

---

## Phase 2 — Section Lookup Helper

**Behavioral spec**: THREE_ADDITIONS.md INV-2.1 through INV-2.6

### Step 2.1: Write failing tests for INV-2.1 through INV-2.5

Create `TestSectionOfLine` with synthetic fixtures per spec. Do not use hardcoded line numbers from specific files.

**Checkpoint**: Tests exist and FAIL

---

### Step 2.2: Write failing tests for INV-2.6

Create `TestSectionIndex` per spec. Verification of "no per-call rebuild" is best-effort per INV-2.6; choose a verification method (debug stats, timing, or other) that works for your implementation.

**Checkpoint**: Tests exist and FAIL

---

### Step 2.3: Write integration tests

Create:
- `TestSectionOfLineIntegration` — uses real parser output
- `TestParserSectionInvariants` — verifies sections are sorted, non-overlapping, 0-indexed per `CLAUDE.md`

For zero-indexing test: use a simple fixture with heading on first line (no frontmatter, no leading blanks) to verify `start_line=0`.

**Checkpoint**: Tests exist and FAIL

---

### Step 2.4: Implement `section_of_line()` function

Implement to satisfy INV-2.1 through INV-2.5.

**Checkpoint**: `TestSectionOfLine` passes

---

### Step 2.5: Implement `SectionIndex` class

Implement to satisfy INV-2.6. Build strategy (lazy vs eager) is implementation choice per spec; document which you chose.

**Checkpoint**: `TestSectionIndex` passes

---

### Step 2.6: Run all Phase 2 tests

**Checkpoint**: All pass

---

### Step 2.7: Clean Table check for Phase 2

Per `.claude/rules/CLEAN_TABLE_PRINCIPLE.md` plus:
- [ ] All Phase 2 tests pass

**Commit**: Phase 2 complete

---

## Phase 3 — Adversarial Corpus

**Behavioral spec**: THREE_ADDITIONS.md INV-3.1 through INV-3.4

### Step 3.1: Create adversarial corpus directory

Location per spec (example path; adjust if needed).

---

### Step 3.2: Generate/create adversarial files

Create ≥1 file per category defined in THREE_ADDITIONS.md. Each file must actually stress the category:

| Category | Minimum stress level |
|----------|---------------------|
| Deep nesting | ≥50 levels (lists) or ≥30 levels (quotes) |
| Wide structures | ≥100x100 table or ≥1000 links |
| Long content | ≥100K chars in single line |
| Unicode edge cases | Contains actual BiDi controls or confusables |
| Security patterns | Contains patterns that trigger detection |
| Binary edge cases | Contains null bytes or mixed encoding |

**Checkpoint**: Files exist and tests (Step 3.3) can assert minimum stress levels

---

### Step 3.3: Write tests for INV-3.1, INV-3.2, INV-3.4

Create test classes per spec. Each test:
1. Loads corpus file
2. Parses with `security_profile="strict"`
3. Asserts no exception (INV-3.1)
4. Asserts completes within timeout (INV-3.2) — timeout is environment-dependent per spec
5. Asserts parse result is not None with `metadata.security` populated (INV-3.4)

**Checkpoint**: Tests exist

---

### Step 3.4: Write tests for INV-3.3

Create `TestSecurityPatterns` per spec. The expected warnings/blocks are defined by these tests, not by this plan.

**Checkpoint**: Tests exist

---

### Step 3.5: Create shared adversarial runner module

**Important**: Implement core adversarial parsing logic in ONE module. Both pytest tests and CI gate should import and use this shared implementation to avoid drift.

```
adversarial_runner.py  # Core logic
├── used by: tests/test_adversarial.py
└── used by: tools/ci/ci_gate_adversarial.py
```

**Checkpoint**: Single source of truth for adversarial execution

---

### Step 3.6: Run adversarial tests, fix any crashes

If crashes occur, fix parser to return result with warnings per INV-3.4.

**Checkpoint**: All adversarial tests pass

---

### Step 3.7: Create CI gate

Wrapper that calls shared runner and returns appropriate exit code.

**Checkpoint**: CI gate works

---

### Step 3.8: Clean Table check for Phase 3

Per `.claude/rules/CLEAN_TABLE_PRINCIPLE.md` plus:
- [ ] All Phase 3 tests pass
- [ ] CI gate passes
- [ ] Corpus covers all categories with minimum stress levels

**Commit**: Phase 3 complete

---

## Post-Implementation

### Final verification

Run all test suites (unit, baseline, adversarial, CI gate).

### Update THREE_ADDITIONS.md Status

Change Status from `PROPOSED` to `IMPLEMENTED (all phases)`.

**Note**: This is a manual update per spec; it can drift if CI later regresses.

### Final commit

---

## Step Summary

| Phase | Steps |
|-------|-------|
| Phase 1 | 11 |
| Phase 2 | 7 |
| Phase 3 | 8 |
| **Total** | **26** |

Test counts depend on implementation granularity; see spec for required coverage.

---

**End of Implementation Plan**
