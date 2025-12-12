# THREE_ADDITIONS.md - Behavioral Specification

**Status**: IMPLEMENTED
**Version**: 2.7.0
**Last Updated**: 2025-12-12

**Revision History**:
- v2.7.0: Added visibility note for future field constraint (INV-1.1), clarified INV-1.2 is about data not API surface, downgraded security order to SHOULD, scoped INV-1.5/1.6 MUSTs explicitly to tested patterns, acknowledged INV-2.6 verification is best-effort, removed timeout upper bound and clamping (was internally inconsistent), added explicit CLAUDE.md dependency note in header
- v2.6.0: Closed parse result field set with future-field clause (INV-1.1), added TestRawInputPreservation for INV-1.8, downgraded caller normalization to SHOULD, clarified security invariant enforcement is test-bound (INV-1.5/1.6), removed internal helper names from spec, added explicit line numbering SSOT note, relaxed debug mechanism to implementer choice, bound parse result type to CLAUDE.md (INV-3.4), added timeout clamping test requirement (INV-3.2), acknowledged phase completion is soft, added supersedes clause for proposal, marked all file headings as examples inline
- v2.5.0: Defined structural parse result fields explicitly (INV-1.1), bounded security ruleset scope (INV-1.5/1.6), stated normalization ownership and processing order, demoted `build_line_to_section_index` to internal, added line indexing test requirement, canonicalized parse result type (INV-3.4), added timeout upper bound (INV-3.2), consolidated Clean Table gate, marked file paths as examples, added upstream contradiction clause, defined phase completion state
- v2.4.0: Resolved INV-1.1/1.8 contradiction (structural vs raw), clarified idempotence as sole enforceable contract, relaxed SectionIndex to allow lazy build, added 0-indexed cross-doc ref, clarified security authority in tests, tightened parse result type, clarified adversarial non-goal, softened file name coupling
- v2.3.0: Added explicit test classes for all invariants, INV-1.8 (raw input preservation), flexible debug hook for INV-2.6, coverage rules for adversarial corpus, security detection severity semantics, enforcement cross-links
- v2.2.0: Replaced migration prediction with idempotence invariant, behavioral preconditions, test hooks for INV-2.6, concrete parse result fields for INV-3.3/3.4, CI gate conditions, test lifecycle bridging
- v2.1.0: Removed drifting constants, narrowed security invariants to no-regression scope, consolidated Clean Table refs
- v2.0.0: Refactored to behavioral specification (invariants, not implementation)

**Related Documents**:
- Source proposal: `DOXSTRUX_PHASE8_SMALL_IMPROVEMENTS.md` (this spec **supersedes** the proposal as the binding contract)
- Architecture SSOT: `CLAUDE.md` (**this spec inherits definitions from CLAUDE.md**; parse result type and line indexing are defined there)
- Clean Table rules: `.claude/rules/CLEAN_TABLE_PRINCIPLE.md`

**Note**: This spec is not self-contained. Key definitions (parse result structure, line indexing convention) are inherited from `CLAUDE.md`. When `CLAUDE.md` changes, this spec's meaning changes accordingly.

---

## Overview

Three improvements to implement on top of Phase 7 modular architecture:

1. **Content normalization** — NFC + CRLF→LF before parsing
2. **`section_of_line()` helper** — O(log N) line-to-section lookup
3. **Adversarial corpus** — Stress test files + CI gate

---

## Implementation Order

**Order: 1 → 2 → 3**

| Priority | Improvement | Rationale |
|----------|-------------|-----------|
| **1st** | Content normalization | Foundation — affects all line/char spans |
| **2nd** | `section_of_line()` | Depends on stable section output |
| **3rd** | Adversarial corpus | Uses both above; tests the whole system |

**Why this order:**
- Normalization changes content and line boundaries — must be first
- Section lookup needs stable line numbers — wait for normalization
- Adversarial tests validate everything — run last

---

## Phase 1 — Content Normalization

### Behavioral Invariants

These invariants define the contract. Implementation must satisfy all of them.

**INV-1.1: Line ending equivalence**
> CRLF-encoded and LF-encoded versions of the same logical document MUST produce identical parse results for all top-level keys except `original_content`. Any future top-level keys added to the parse result are also subject to this invariant unless explicitly exempted here. Currently: `structure`, `mappings`, `metadata`, `content` MUST be byte-for-byte identical. Only `original_content` is allowed to differ (governed by INV-1.8). **Visibility**: Contributors adding new parse result fields should be aware of this constraint; consider adding a reference in `CLAUDE.md` parser output docs.

**INV-1.2: No trailing CR in lines**
> After parsing, no line in the normalized content MUST end with `\r`. This applies to `parse_result["content"]["lines"]` if exposed, or equivalently to any internal `parser.lines` array. The invariant is about the data, not the specific API surface.

**INV-1.3: Bare CR handling**
> Bare CR (old Mac style `\r` without following `\n`) MUST be treated as line separator.

**INV-1.4: Unicode composition equivalence**
> Precomposed (NFC) and decomposed (NFD) forms of the same logical text MUST produce identical slugs and heading text.

**INV-1.5: Line-ending normalization does not weaken security (for tested patterns)**
> For each security pattern with a test in `TestNormalizationSecurity` or `TestSecurityPatterns`, detection MUST NOT be weakened by line-ending normalization. CRLF vs LF MUST NOT be usable to bypass those tested checks. Patterns without tests are aspirationally covered but not mechanically enforced.

**INV-1.6: Unicode normalization does not weaken security (for tested patterns)**
> For each security pattern with a test, NFC normalization MUST NOT weaken detection. Same enforcement scope as INV-1.5: only tested patterns are guaranteed.

**INV-1.7: Idempotence**
> Normalization MUST be idempotent: normalizing already-normalized content MUST NOT change it. This is the enforceable contract; whether normalization happens once or multiple times is an implementation detail as long as idempotence holds.

**INV-1.8: Raw input preservation**
> If the parser exposes `original_content` (or equivalent), it MUST preserve the raw input prior to normalization for auditing and security debugging. Normalization only affects internal parsing buffers and derived fields.

### Normalization Ownership

Normalization is owned by the parser, not the caller. Callers SHOULD NOT pre-normalize content before passing to the parser; the parser is the canonical place for normalization. (This is architectural guidance, not a testable invariant — callers may pre-normalize if they accept responsibility for security implications.) The parser is responsible for:
1. Preserving raw input (INV-1.8)
2. Running security checks on raw input (before normalization)
3. Normalizing for internal parsing (after security checks)

**Processing order**: raw input → security checks → normalization → parsing. This order ensures INV-1.5/1.6 hold.

### Preconditions to Verify

**Current-state notes** (non-normative):
- Current implementation assumes LF-only line endings and performs no parse-time Unicode normalization

**Architectural guidance** (not strictly required for invariants):
- Security checks SHOULD see raw input before normalization. INV-1.5/1.6 can technically be satisfied even if checks run post-normalization, but running on raw input is the intended design. If this order changes, revisit INV-1.5/1.6 tests to ensure they still pass.

If any precondition is not satisfied, this specification MUST be updated (or invariants relaxed) before implementation proceeds.

### Tests to Create

**Example file**: `tests/test_content_normalization.py` (path is illustrative; see Non-Goals)

Test classes:
- `TestLineEndingNormalization` — tests for INV-1.1, INV-1.2, INV-1.3
- `TestUnicodeNormalization` — tests for INV-1.4
- `TestNormalizationSecurity` — tests for INV-1.5, INV-1.6 (constructs inputs where security checks trigger, asserts detection still works after normalization; e.g., `javascript:` split across CRLF)
- `TestNormalizationIdempotence` — tests for INV-1.7 (calls normalize twice, asserts equality)
- `TestRawInputPreservation` — tests for INV-1.8: asserts `parse_result["original_content"] == raw_input` for any input; asserts `original_content` differs between CRLF/LF variants while `content` is identical

Each test should:
1. Be written BEFORE implementation (TDD red phase)
2. Initially FAIL
3. PASS after implementation (TDD green phase)

**Note**: INV-1.5 and INV-1.6 are also exercised by `TestSecurityPatterns` in Phase 3, which provides end-to-end coverage.

### Implementation Guidance (Non-Normative)

The following steps are non-normative guidance; the only normative requirements are the invariants above.

- Add `_normalize_content(content: str) -> str` method
- Apply `unicodedata.normalize("NFC", content)`
- Apply `content.replace("\r\n", "\n").replace("\r", "\n")`
- Call normalization in `__init__` before `split("\n")`
- Parsing SHOULD operate on normalized content, not a mix of raw and partially-normalized buffers

### Baseline Impact

Normalization is expected to change baseline outputs for CRLF fixtures. After implementation:
- Run baseline tests to identify DIFFs
- Baselines MUST be regenerated and re-verified
- Verify all baseline tests pass (no regressions)

---

## Phase 2 — Section Lookup Helper

### Behavioral Invariants

**INV-2.1: Correct section identification**
> `section_of_line(sections, line)` returns the section dict where `start_line <= line <= end_line`, or `None` if no such section exists.

**INV-2.2: Boundary correctness**
> Lines at exact section boundaries (start_line, end_line) are included in that section.

**INV-2.3: Gap handling**
> Lines in gaps between sections return `None`.

**INV-2.4: Edge cases**
> Negative line numbers return `None`. Empty sections list returns `None`.

**INV-2.5: Single-line section**
> A section where `start_line == end_line` correctly identifies that single line.

**INV-2.6: Amortized lookup**
> `SectionIndex` MUST build its internal index at most once per instance and reuse it for all subsequent lookups (no rebuild per call). Whether indexing is eager (in `__init__`) or lazy (on first lookup) is an implementation choice. Tests SHOULD verify no per-call rebuilding occurs; verification is best-effort (timing-based tests are inherently flaky, debug hooks couple to internals). A recommended approach: expose `_build_count` or similar, but this is not required.

### Preconditions

The following must be true for section lookup to work correctly:
- Sections are sorted by `start_line` (ascending)
- Sections have `start_line` and `end_line` fields (0-indexed)
- Sections are non-overlapping — each line belongs to at most one section

**SSOT for line numbering**: `CLAUDE.md` is the authoritative source for line indexing convention. This spec inherits 0-based indexing from there. If `CLAUDE.md` changes to 1-based lines, this spec MUST be updated to match — `CLAUDE.md` takes precedence.

These preconditions are enforced by `TestParserSectionInvariants` (see Tests to Create). If the core parser changes line numbering semantics (e.g., to 1-based), this spec and helpers MUST be updated together.

If any precondition is not satisfied, this specification MUST be updated (or invariants relaxed) before implementation proceeds.

### Tests to Create

**Example file**: `tests/test_section_utils.py` (path is illustrative; see Non-Goals)

Test classes:
- `TestSectionOfLine` — tests for INV-2.1 through INV-2.5
- `TestSectionIndex` — tests for repeated lookup consistency and verifies no per-call rebuilding (INV-2.6)
- `TestSectionOfLineIntegration` — tests with real parser output
- `TestParserSectionInvariants` — asserts sections from real parser output are sorted, non-overlapping, and use 0-indexed line numbers

Each test should use synthetic section data fixtures, not hardcoded line numbers from specific files.

**Line indexing test**: At least one test MUST explicitly verify that `start_line=0` corresponds to the first line of the document, confirming 0-indexed convention alignment with `CLAUDE.md`.

### Implementation Location

**Example file**: `src/doxstrux/markdown/utils/section_utils.py` (path is illustrative; see Non-Goals)

**Public API**:
- `section_of_line(sections, line)` — single lookup function (convenience wrapper)
- `SectionIndex` — class for repeated lookups (primary API)

**Note**: `SectionIndex` is the canonical public interface. Any internal helpers (index builders, caches) are implementation details and MAY change without notice. This spec does not name or constrain internal helpers.

---

## Phase 3 — Adversarial Corpus

### Behavioral Invariants

**INV-3.1: No crashes**
> Parser MUST NOT crash (exception, segfault) on any adversarial input.

**INV-3.2: Bounded time**
> Each adversarial file MUST complete parsing within configurable timeout (default: 5 seconds). Timeout is controlled via environment variable `DOXSTRUX_ADVERSARIAL_TIMEOUT_MS`. There is no enforced upper bound; CI environments with slow runners MAY use longer timeouts as needed. The 5s default is a target for typical hardware, not a hard constraint. **Test guidance**: Tests SHOULD verify that parsing completes within a reasonable timeout, but specific bounds are environment-dependent.

**INV-3.3: Security detection**
> `TestSecurityPatterns` tests MUST assert expected `metadata.security.embedding_blocked` and `metadata.security.warnings` values. The authoritative mapping of patterns → severity is encoded in those tests, not in this spec.

**INV-3.4: Graceful degradation**
> Malformed input MUST yield a non-None parse result (as defined in `CLAUDE.md`; currently the `dict` returned by `MarkdownParserCore.parse()`) with a populated `metadata.security` section. No uncaught exceptions are allowed. Warnings MUST be encoded in `metadata.security.warnings`, not only in logs. If the parse result type changes in `CLAUDE.md`, this invariant inherits that change.

**Enforcement**: These invariants are enforced at unit-test level (`tests/test_adversarial.py`) and via the CI gate (`tools/ci/ci_gate_adversarial.py`).

### Adversarial Categories

The corpus covers these stress categories:

| Category | Purpose | Examples |
|----------|---------|----------|
| **Deep nesting** | Stack overflow prevention | 50+ level lists, 30+ level quotes |
| **Wide structures** | O(N²) detection | 100x100 tables, 1000+ links |
| **Long content** | Memory/timeout | 100K+ char single lines |
| **Unicode edge cases** | BiDi, confusables | RTL override, homoglyphs |
| **Security patterns** | Detection validation | Prompt injection, path traversal |
| **Binary edge cases** | Robustness | Null bytes, mixed encodings |

### Tests to Create

**Example file**: `tests/test_adversarial.py` (path is illustrative; see Non-Goals)

Test classes organized by category:
- `TestDeepNesting` — synthetic deep structures
- `TestLargeStructures` — wide tables, many links
- `TestSecurityPatterns` — prompt injection, BiDi detection
- `TestEdgeCases` — null bytes, empty sections

Initially these tests serve as **specification tests** and MAY fail. Once implementation satisfies INV-3.1 through INV-3.4, they become **regression tests** and MUST remain green.

### Corpus Location

**Example directory**: `tools/adversarial_mds/` (path is illustrative; see Non-Goals)

Files are generated by scripts in `tools/`:
- Static files for patterns that need exact content
- Generated files for large structures (tables, links)

**Coverage rule**:
- The corpus MUST contain ≥1 `.md` file per category listed above
- Each test class in `tests/test_adversarial.py` MUST exercise at least one corpus file from `tools/adversarial_mds/` for its category (synthetic inline fixtures are allowed in addition, not instead)

### CI Integration

**Example file**: `tools/run_adversarial_tests.py` (path is illustrative; see Non-Goals)

- Iterates adversarial corpus directory
- Parses each with `security_profile="strict"`
- Validates INV-3.1 (no crash) and INV-3.2 (timeout)
- Reports pass/fail per file

**CI Gate**: `tools/ci/ci_gate_adversarial.py` integrates adversarial runner.

CI gate MUST fail if:
- Any adversarial file crashes (uncaught exception)
- Any adversarial file times out
- The runner fails to produce a parse result
- Required security flags are missing for `TestSecurityPatterns` cases

---

## Clean Table Gate

Before closing **any** phase, all conditions in `.claude/rules/CLEAN_TABLE_PRINCIPLE.md` MUST hold. Phase-specific additions:

| Phase | Additional requirements |
|-------|------------------------|
| 1 | Normalization tests pass, affected CRLF baselines regenerated |
| 2 | Section utils tests pass |
| 3 | Adversarial unit tests pass, corpus runner passes, CI gate passes |

---

## Success Criteria

### Phase 1 Complete When:
- INV-1.1 through INV-1.8 verified by passing tests
- CRLF baselines regenerated
- All baseline tests pass (no regressions)

### Phase 2 Complete When:
- INV-2.1 through INV-2.6 verified by passing tests
- `TestParserSectionInvariants` confirms sorted/non-overlapping sections
- Integration tests with real parser output pass

### Phase 3 Complete When:
- INV-3.1 through INV-3.4 verified by passing tests
- Adversarial corpus covers all categories
- CI gate passes

### All Phases Complete When:
- All invariants satisfied
- All tests pass (unit + baseline + adversarial)
- Clean git state (no uncommitted changes, no failing CI)

**Phase completion state**: A phase is "complete" when its success criteria are met AND its tests are committed to the repository as regression tests (no longer marked `xfail`). Completion is recorded by updating `Status` at the top of this document from `PROPOSED` to `IMPLEMENTED (Phase N)` or `IMPLEMENTED (all)`. Note: this is a manual process and can drift from reality if CI later regresses. The `Status` field is informational, not a live gate.

---

## Non-Goals

This specification does **not** propose:

- Changing the public API of `MarkdownParserCore`
- Changing parser output structure (except CRLF → LF normalization)
- Adding new security profiles
- Adding `section_of_line()` to DocumentIR (kept as standalone util)
- Creating golden-output baselines for adversarial files; only behavior is tested (no crash, within timeout, correct security flags)
- Freezing line counts or paths of existing code (these drift)

**File path convention**: Paths in this spec (e.g., `tests/test_section_utils.py`, `tools/adversarial_mds/`) are **examples**, not mandates. Renaming is allowed if tests/CI are updated accordingly.

---

## Implementation Notes

**Test lifecycle**: Until a phase is marked complete, tests added for that phase MAY legitimately fail. CI configuration MUST accommodate this (e.g., mark as `xfail` or exclude) until implementation catches up. Once a phase is complete, its tests become regression tests and MUST remain green.

When implementing:

1. **Write tests first** (TDD). Tests should fail before implementation, pass after.

2. **Verify preconditions** against actual codebase, not this document's assumptions.

3. **Check Clean Table** after each task per `.claude/rules/CLEAN_TABLE_PRINCIPLE.md`.

4. **Commit after each phase** with clear message.

5. **If invariants conflict with codebase reality**, update this spec before proceeding.

6. **Upstream contradiction handling**: If `CLAUDE.md` or `.claude/rules/CLEAN_TABLE_PRINCIPLE.md` contradicts this spec, those documents take precedence. Update this spec to align, do not override upstream.

---

**End of THREE_ADDITIONS.md**
