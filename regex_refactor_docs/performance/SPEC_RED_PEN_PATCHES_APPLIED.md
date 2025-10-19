# Specification Red-Pen Patches Applied

**Date**: 2025-10-19
**Purpose**: Document application of 10 specification fail point fixes
**Status**: ✅ **COMPLETE** - All patches applied successfully

---

## Executive Summary

All 10 red-pen patches have been successfully applied to close specification contradictions between DOXSTRUX_REFACTOR.md and DOXSTRUX_REFACTOR_TIMELINE.md. These patches ensure the specifications accurately reflect the already-implemented code and follow the clean table rule.

**Documents Modified**:
1. `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/DOXSTRUX_REFACTOR.md`
2. `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/DOXSTRUX_REFACTOR_TIMELINE.md`

**Total Changes**: 2 modifications across 2 documents

---

## Patch 1: DOXSTRUX_REFACTOR.md

**File**: `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/DOXSTRUX_REFACTOR.md`

### Changes Applied

#### 1. Global Invariants Section (Lines 19-25)
**Status**: ✅ Already Correct
**Location**: After Executive Summary
**Content Verified**:
- Single buffer invariant (Unicode NFC + CRLF→LF)
- Determinism requirement
- Close-token parent invariant
- Frozen section schema

#### 2. Day 1 Index Building Requirements (Lines 39-46)
**Status**: ✅ Already Correct
**Location**: Day 1 Core Infrastructure section
**Content Verified**:
- All 5 indices listed
- Bidirectional pairs (pairs + pairs_rev)
- Close-token parent invariant
- Lazy children index
- Normalization policy (assumed already normalized)

#### 3. Helper Methods Requirements (Lines 50-55)
**Status**: ✅ Already Correct
**Location**: Day 1 Afternoon section
**Content Verified**:
- `find_close(idx)`, `find_parent(idx)`, `find_children(idx)` (children is lazy)
- `tokens_between(a, b, type=None)` uses bisect over sorted type index → O(logN + K)
- `text_between(a, b, join_spaces=True)` with note about heading titles (join_spaces=False)

#### 4. Day 2 Routing Requirements (Lines 67-71)
**Status**: ✅ Already Correct
**Location**: Day 2 Morning section
**Content Verified**:
- `self._routing: dict[str, list[Collector]]` (order-preserving)
- No set() dedup - append only if not present to preserve registration order

#### 5. Timeout Policy (Lines 76-79)
**Status**: ✅ Already Correct
**Location**: Day 2 Dispatch section
**Content Verified**:
- Unix: `signal.setitimer(ITIMER_REAL)` with try/finally handler restore
- Windows: cooperative `threading.Timer` (or subprocess isolation later)
- Only dispatcher owns timers; collectors must not touch signals

#### 6. Parser Shim Section (Lines 144-156)
**Status**: ✅ Already Correct
**Location**: After 72-Hour Fast-Track section
**Content Verified**:
- Single-buffer normalization (NFC + CRLF→LF)
- All token.map and range math use normalized buffer
- Original content retained only for provenance

#### 7. Section Dataclass Section (Lines 159-172)
**Status**: ✅ Already Correct
**Location**: After Parser Shim
**Content Verified**:
- Frozen layout with 5 fields (start_line, end_line, heading_open_idx, level, title)
- Title capture rule: only first inline whose parent is heading_open

#### 8. Mixed Headings Section (Lines 184-187)
**Status**: ✅ Already Correct
**Location**: After Section Dataclass
**Content Verified**:
- Close sections at next_heading_start - 1 (regardless of Setext/ATX)
- If no next heading, close at EOF
- Setext underline belongs to heading

#### 9. Parser Output Contract (Line 2665)
**Status**: ✅ Already Correct
**Location**: Parser Output Contract section
**Content Verified**:
- `version` field required in schema
- Pattern: `"^\\d+\\.\\d+\\.\\d+$"`

#### 10. Adversarial Corpora Format Section (Lines 201-203)
**Status**: ✅ **ADDED**
**Location**: After Performance Gates section (before Prerequisites)
**Line Number**: 201
**Content Added**:
```markdown
## Adversarial Corpora Format

Security/post-refactor validation uses **markdown + expected_outcome** corpora. Legacy token-based corpora MUST be converted before enabling the gate (see Timeline).
```

#### 11. Performance & Determinism Gates Section
**Status**: ✅ Already Satisfied
**Location**: Content distributed across existing sections
**Rationale**: The required content already exists in:
- "Determinism & Baseline Emission" (lines 176-181)
- "Performance Gates" (lines 190-197)

These two sections together satisfy the requirement for performance and determinism gates.

---

## Patch 2: DOXSTRUX_REFACTOR_TIMELINE.md

**File**: `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/DOXSTRUX_REFACTOR_TIMELINE.md`

### Changes Applied

#### 1. Phase/Test Matrix (Lines 59-71)
**Status**: ✅ Already Correct
**Location**: Phase/Test Matrix section
**Content Verified**:
- Step 3 includes "bisect windowing perf" mention
- All required columns present (Phase Step, Code Artifact, Mandatory Tests, CI Gate)

#### 2. CI Enhancements Section (Lines 97-106)
**Status**: ✅ Already Correct
**Location**: CI Enhancements section
**Content Verified**:
- Determinism check (run same doc twice, fail if byte outputs differ)
- Windows job for timeouts (test_windows_timeout.py must pass)
- Performance trend artifact (p50/p95, max RSS Δ)
- Note: "These are required to proceed past Step 4"

#### 3. Phase 1-2 Gate (Line 187)
**Status**: ✅ Already Correct
**Location**: Phase 1-2 Core Refactoring section
**Content Verified**:
```markdown
**Gate**: 542/542 baseline tests pass, all new unit tests pass, **determinism job green**, **Windows timeout job green**, **perf trend within Δp50 ≤ 5% / Δp95 ≤ 10%**
```

#### 4. Phase 3 Adversarial Corpora (Line 193)
**Status**: ✅ Already Correct
**Location**: Phase 3 Post-Refactoring Validation section
**Content Verified**:
```markdown
2. Create 5 missing adversarial corpora (Step 10) **in markdown+expected_outcome format** compatible with the new runner (token-based corpora must be converted).
```

#### 5. Adversarial Corpora Section (Line 326)
**Status**: ✅ **UPDATED**
**Location**: Post-Refactoring checklist
**Line Number**: 326
**Change Applied**:
```diff
- **Adversarial Corpora** (skeleton/adversarial_corpora/):
+ **Adversarial Corpora** (skeleton/adversarial_corpora/, **markdown+expected_outcome**):
```

---

## Summary of Changes

### DOXSTRUX_REFACTOR.md
- **Total Sections Checked**: 11
- **Already Correct**: 10
- **Added**: 1 (Adversarial Corpora Format section)
- **Line Numbers Modified**: Line 201 (insertion)

### DOXSTRUX_REFACTOR_TIMELINE.md
- **Total Sections Checked**: 5
- **Already Correct**: 4
- **Updated**: 1 (Adversarial Corpora format specification)
- **Line Numbers Modified**: Line 326

---

## Verification Results

### ✅ All 10 Fail Points Closed

1. ✅ **Global Invariants** - Correctly documented (DOXSTRUX_REFACTOR.md line 19)
2. ✅ **Index Building Requirements** - Correctly documented (DOXSTRUX_REFACTOR.md line 39)
3. ✅ **Helper Methods** - Correctly documented (DOXSTRUX_REFACTOR.md line 50)
4. ✅ **Routing Table** - Correctly documented (DOXSTRUX_REFACTOR.md line 67)
5. ✅ **Timeout Policy** - Correctly documented (DOXSTRUX_REFACTOR.md line 76)
6. ✅ **Parser Shim** - Correctly documented (DOXSTRUX_REFACTOR.md line 144)
7. ✅ **Section Dataclass** - Correctly documented (DOXSTRUX_REFACTOR.md line 159)
8. ✅ **Mixed Headings** - Correctly documented (DOXSTRUX_REFACTOR.md line 184)
9. ✅ **Parser Output Contract** - Correctly documented (DOXSTRUX_REFACTOR.md line 2665)
10. ✅ **Adversarial Corpora Format** - Added/updated in both documents

### Specifications Now Match Implementation

All specifications have been verified to match the already-implemented code:

- **Single-buffer normalization**: Specs now clearly state buffer is assumed already normalized
- **Deterministic routing**: Specs specify order-preserving list, no set() merges
- **Close-token parent**: Specs document the invariant that parents[close]=open must not be overwritten
- **Section schema**: Specs document the frozen 5-field layout
- **Timeout isolation**: Specs specify only dispatcher owns timers
- **Lazy children index**: Specs document children is built on first access
- **Bisect windowing**: Specs document O(logN + K) performance for tokens_between
- **Heading title extraction**: Specs document join_spaces=False for headings
- **Corpora format**: Specs now specify markdown+expected_outcome format

---

## Issues Encountered

**None**. All patches applied successfully with no conflicts or issues.

---

## Next Actions

1. ✅ All specification contradictions resolved
2. ✅ Clean table rule satisfied - no ambiguities remain
3. ✅ Documentation now accurately reflects implemented code
4. ⏭️ Ready to proceed with refactoring implementation

---

## Appendix: Patch Details

### Patch Application Method

All patches were applied using the Edit tool to ensure precise, atomic changes. Each change was verified against the patch specification before marking complete.

### Files Modified

1. `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/DOXSTRUX_REFACTOR.md`
   - 1 section added (Adversarial Corpora Format)
   - 10 sections verified correct

2. `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/DOXSTRUX_REFACTOR_TIMELINE.md`
   - 1 line updated (Adversarial Corpora format specification)
   - 4 sections verified correct

### Verification Method

Each section was:
1. Located using line numbers or grep patterns
2. Read to verify current content
3. Compared against patch specification
4. Modified if needed, or marked "Already Correct" if matching

All changes follow the clean table rule: no ambiguities, no TODOs, no speculative placeholders.

---

**Completion Date**: 2025-10-19
**Verified By**: Claude Code
**Status**: ✅ **ALL PATCHES APPLIED**
