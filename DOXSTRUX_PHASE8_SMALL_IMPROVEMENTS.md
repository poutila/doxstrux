# DOXSTRUX_PHASE8_SMALL_IMPROVEMENTS.md
Version: 0.1.0
Status: Draft

Scope
=====
This document captures **only** the still-valuable ideas from the historical
`DOXSTRUX_REFACTOR.md` plan that are worth implementing on top of the current
Phase-7 modular architecture of `doxstrux`.

It does **not** reintroduce the old TokenWarehouse / `skeleton.doxstrux`
architecture. Instead, it defines three small, self-contained improvements
that can be implemented incrementally without changing the core parser design.

Authoritative SSOTs for the overall architecture remain:

- `CLAUDE.md`
- `regex_refactor_docs/REGEX_REFACTOR_POLICY_GATES.md`
- `SECURITY_KERNEL_SPEC.md`
- `NO_SILENTS_proposal.md`


Overview of Improvements
========================

This document defines three improvements:

1. **Canonical content normalization**  
   Normalize input text (Unicode + line endings) before parsing.

2. **Section lookup helper (`section_of_line`)**  
   Provide a fast, stable helper to map a 1-based line number to a section
   using the existing `sections` data produced by `extractors/sections.py`.

3. **Adversarial markdown corpora + CI gate extension**  
   Introduce a small set of adversarial Markdown fixtures and extend the
   existing performance/security gates to run against them, in addition to the
   normal baseline corpus.


Improvement 1 — Canonical Content Normalization
===============================================

Goal
----
Make `MarkdownParserCore` parse a **canonicalized** version of the input
content so that:

- Line/character spans are stable across platforms (LF vs CRLF).
- Unicode composition variants behave consistently for headings, slugs, and
  section boundaries.

Design
------

1. Introduce a private normalizer in `MarkdownParserCore`:

   - File: `src/doxstrux/markdown_parser_core.py`
   - Method (suggested name):

     ```python
     def _normalize_content(self, content: str) -> str:
         ...
     ```

2. The normalizer MUST perform at least:

   - Unicode normalization to NFC:

     ```python
     import unicodedata

     content = unicodedata.normalize("NFC", content)
     ```

   - Line-ending normalization:

     ```python
     # Convert CRLF -> LF
     content = content.replace("\r\n", "\n")
     # Optionally also convert bare CR -> LF if needed:
     content = content.replace("\r", "\n")
     ```

3. `MarkdownParserCore.__init__` MUST adopt the following invariants:

   - Preserve the raw input as `self.original_content` (unchanged).
   - Set `self.content` to the **normalized** result of `_normalize_content`.
   - Derive `self.lines` and all line/char span calculations from
     `self.content` (normalized), not from `original_content`.

4. Any downstream code that operates on text offsets or line numbers MUST
   treat `self.content` as the canonical source.

Non-Goals
---------

- No changes to the public API of `MarkdownParserCore`.
- No changes to baseline semantics except where line-ending / Unicode
  normalization exposes existing inconsistencies.

Tests
-----

Add tests under `tests/` (exact filenames are flexible). Suggested:

1. **CRLF vs LF parity**

   - Construct two markdown strings that differ only by line endings
     (LF vs CRLF).
   - Parse both via `MarkdownParserCore` and assert:

     - `structure["sections"]` is identical.
     - `structure["headings"]` and slugs are identical.
     - Any relevant span fields (e.g. `start_line`, `end_line`) match.

2. **Unicode NFC normalization**

   - Use two variants of the same heading text, one precomposed and one
     decomposed (e.g. `é` vs `e` + combining accent).
   - Assert that:

     - The resulting heading titles are identical.
     - The generated slug IDs match.
     - Sections derived from headings are identical.

Success Criteria
----------------

- `MarkdownParserCore` is the **only** place that normalizes content; there is
  no duplicated normalization logic.
- All existing tests and baselines pass after mechanically updating baseline
  files where line-ending / Unicode regularization caused benign differences.
- New normalization tests pass and clearly document the intended behaviour.


Improvement 2 — Section Lookup Helper (`section_of_line`)
=========================================================

Goal
----
Expose a fast, stable helper that maps a 1-based line number to the section
that contains it, using the existing `sections` structure produced by
`extractors/sections.py`. This is useful for external tools that want to
relate raw line numbers (e.g. from linters) back to document sections.

Design
------

Current state (Phase-7):
- `extractors/sections.py` already produces a list of section objects or
  dicts with at least: `start_line`, `end_line`, and an identifier.

The helper will sit **on top of** this data; no new indexing layer or
TokenWarehouse is introduced.

API Shape
---------

Two possible placements (choose one and document it):

1. **Utility function** in a new module, e.g.
   `doxstrux.markdown.utils.section_utils`:

   ```python
   def section_of_line(sections: list[dict], line: int) -> dict | None:
       """Return the section whose [start_line, end_line] contains `line`.

       Sections are expected to be sorted by start_line and non-overlapping.
       `line` is 1-based.
       """
   ```

2. **Method** on `DocumentIR` (if that is the preferred abstraction for
   external consumers):

   ```python
   class DocumentIR:
       ...

       def section_of_line(self, line: int) -> Section | None:
           ...
   ```

Algorithm
---------

- Precondition: `sections` list is sorted by `start_line` and contains no
  overlapping ranges.
- Use binary search over `start_line` to achieve O(log N) lookup:

  1. Binary-search for the greatest `section.start_line` such that
     `start_line <= line`.
  2. If found, check whether `line <= section.end_line`:
     - If yes, return that section.
     - If no, return `None`.
  3. If no candidate found (line before first section), return `None`.

Tests
-----

Add tests such as:

- `test_section_of_line_basic_ranges`:
  - Simple case with 2–3 sections; test boundary lines and gaps.

- `test_section_of_line_outside_ranges`:
  - Line before first section and after last section returns `None`.

- `test_section_of_line_one_based_indices`:
  - Ensure 1-based indexing is used (line 1 is the first line).

- `test_section_of_line_large_n_performance` (optional):
  - Synthetic list of thousands of sections to assert that lookup completes
    within a small time bound and does not degrade to O(N) behaviour
    (e.g. via a simple timing guard).

Success Criteria
----------------

- The helper is implemented **once**, in a single module, and reused where
  needed.
- There is no direct dependency on a TokenWarehouse-like abstraction; the
  helper operates on the existing `sections` data.
- External tools can rely on a stable, documented way to resolve
  line-to-section without reimplementing the logic.


Improvement 3 — Adversarial Markdown Corpora + CI Gate
=======================================================

Goal
----
Augment the existing baseline and performance tests with a **small, focused
set of adversarial Markdown files** that exercise worst-case patterns for:

- Deep nesting
- Large tables/lists
- Unicode/Bidi edge cases
- Path traversal and prompt injection payloads at scale

These adversarial files are not about normal behaviour; they are about
ensuring the parser and security kernel behave correctly and within
performance budgets under stress.

Design
------

1. Introduce a new folder for adversarial fixtures, for example:

   - `tools/adversarial_mds/`

2. Populate it with a very small, curated set of `.md` files, e.g.:

   - `deep_nesting.md`  
     - Very deeply nested lists/blocks to stress recursion and stack depth.

   - `wide_tables.md`  
     - Extremely wide and/or tall tables to stress table extraction and
       token iteration.

   - `unicode_bidi.md`  
     - Contains bidi control characters and tricky Unicode sequences.

   - `path_traversal_saturation.md`  
     - Large document containing many URIs with and without traversal
       patterns, to stress the path traversal guard.

   - `prompt_injection_saturation.md`  
     - Large document containing many prompt-injection-like phrases at
       different positions, to stress `check_prompt_injection` and its
       truncation/budget logic.

3. Extend the existing baseline/performance tooling to be able to run against
   both:

   - Normal corpus: `tools/test_mds/`
   - Adversarial corpus: `tools/adversarial_mds/`

Tooling & CI Integration
------------------------

1. Extend `tools/baseline_test_runner.py` (or add a sibling script) to accept
   an optional `--adversarial-dir` argument:

   ```bash
   uv run python tools/baseline_test_runner.py        --test-dir tools/test_mds        --baseline-dir tools/baseline_outputs

   uv run python tools/baseline_test_runner.py        --test-dir tools/adversarial_mds        --baseline-dir tools/adversarial_baseline_outputs
   ```

2. Extend `tools/ci/ci_gate_performance.py` (or create
   `ci_gate_adversarial.py`) to:

   - Run the parser over `tools/adversarial_mds/`.
   - Enforce:

     - No crashes or unhandled exceptions.
     - Execution time and memory usage within a defined multiple of the
       baseline corpus (e.g. “adversarial p95 must be <= 3x normal p95”).

3. Optionally add a separate CI job, e.g. `adversarial-gate`, that runs only
   on `main` and/or nightly to avoid slowing down every PR.

Tests
-----

- Add at least one unit/integration test that validates the adversarial gate
  logic against a synthetic tiny adversarial set (e.g. 1–2 files) to ensure
  the CI gate is actually wired and fails closed.

Success Criteria
----------------

- The adversarial corpus remains **small and curated** (on the order of 5–10
  files), not a second baseline suite.
- CI clearly fails if:

  - Parser crashes on any adversarial file.
  - Performance characteristics exceed configured budgets.

- SECURITY_KERNEL_SPEC and NO_SILENTS remain the SSOT for semantic behaviour;
  adversarial corpora are a diagnostic layer, not a second spec.


Non-Goals & Out-of-Scope
========================

This document explicitly does **not** propose to:

- Reintroduce a parallel `skeleton.doxstrux` implementation.
- Introduce a monolithic TokenWarehouse that replaces the current modular
  extractor design.
- Change the public API surface of `MarkdownParserCore` beyond the internal
  normalization semantics described above.
- Replace or supersede `CLAUDE.md`, `regex_refactor_docs/*`,
  `SECURITY_KERNEL_SPEC.md`, or `NO_SILENTS_proposal.md`.

These improvements are intended to be **small, additive, and strictly
compatible** with the current Phase-7 architecture, aside from expected
normalization-induced baseline adjustments.
