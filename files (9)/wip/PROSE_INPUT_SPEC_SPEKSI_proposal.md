---
speksi:
  spec_id: PROSE_INPUT_SPEC
  version: 1.0.0
  status: DRAFT
  tier: STANDARD
  layers:
    META: "§M"
    ARCHITECTURE: "§A"
    DEFINITIONS: "§D"
    RULES: "§R"
    VALIDATION: "§V"
    CHANGELOG: "§C"
    GLOSSARY: "§G"
---

# Prose Input Specification (SPEKSI Format)

## §M META

### §M.1 Purpose and Scope

This document defines the normative contract for “Prose Input” Markdown documents used as input for AI Task List conversion.

Applies to:

- Prose input documents intended to be converted into an AI Task List artifact by an orchestrator prompt.

Does not apply to:

- This specification itself (it is not a prose input and is not intended to be linted by the prose input linter).

### §M.2 SSOT and Divergence Policy

PIN-SSOT-001: Spec is authoritative
Rule: This specification is the authoritative contract for prose input documents.

PIN-SSOT-002: Divergence resolution
Rule: If this specification and the linter diverge, update the linter to match the specification.

### §M.3 Design Intent (Informative)

The specification exists to ensure:

1. No ambiguity in input, minimizing AI guessing during conversion.
2. Input structure that mirrors the output structure (AI Task List).
3. All binding decisions are made before conversion.
4. Facts are provided as input (not discovered during conversion).
5. Deterministic validation occurs before semantic review.

## §A ARCHITECTURE

### §A.1 Conceptual Flow

A typical workflow is:

1) Author a Prose Input document that satisfies this specification.
2) Run a deterministic linter to validate the document.
3) After the linter passes, run semantic review (optional, separate process).
4) Convert the validated Prose Input into an AI Task List artifact.

### §A.2 Deterministic vs Semantic Checks

- Deterministic checks are enforced by a linter and include structural ordering, forbidden patterns, task field completeness, and metadata validity.
- Semantic review is an optional human/LLM review step performed after deterministic validation passes.

## §D DEFINITIONS

### §D.1 Terms

Prose Input
A structured Markdown document that serves as input for AI Task List conversion.

Conversion
The process of transforming Prose Input into an AI Task List using an orchestrator prompt.

Discovery
An optional phase where facts are gathered from the codebase before writing the Prose Input.

Sample Artifacts
Real output pasted from running commands, not fabricated examples.

Schema version
A version string expected to match the value declared in VERSION.yaml.

Runner
The toolchain used for commands (e.g., uv, npm, cargo).

Runner prefix
The prefix applied to runner-managed commands (may be empty).

Search tool
A text search command used in preconditions (rg or grep), declared in front matter.

### §D.2 Conventions and Interpretation Rules

- Headings and ordering rules refer to Markdown headings with exact text and case unless explicitly stated otherwise.
- “Forbidden patterns” apply to the full document text except where the rule explicitly allows comments.
- Questions are detected as lines ending with “?”; “??” may appear in code contexts and is not treated as a question marker for PIN-F03.

## §R RULES

### §R.1 YAML Front Matter

PIN-Y01: YAML front matter required
Rule: The document MUST start with YAML front matter delimited by a leading and trailing line containing exactly three hyphens (---).

PIN-Y02: prose_input block required
Rule: The YAML front matter MUST contain a top-level mapping key named “prose_input”.

PIN-Y03: Required fields
Rule: The “prose_input” block MUST contain the following fields:

- schema_version (string)
- project_name (string)
- runner (string)
- runner_prefix (string)
- search_tool (string)
- python_version (string, optional)

PIN-Y04: Field types
Rule: All required fields MUST be strings.

PIN-Y05: Schema version match
Rule: schema_version MUST exactly match the version declared in VERSION.yaml.

PIN-Y06: Valid runner
Rule: runner MUST be one of:
- uv, npm, cargo, go, poetry, pipenv

PIN-Y07: Valid search_tool
Rule: search_tool MUST be one of:
- rg, grep

PIN-Y08: No placeholders in YAML
Rule: YAML field values MUST NOT contain placeholder token delimiters “[[" or “]]”.

Non-normative example structure (for illustration only; not a rule):

    ---
    prose_input:
      schema_version: "<VERSION.yaml version>"
      project_name: "<string>"
      runner: "<string>"
      runner_prefix: "<string>"
      search_tool: "rg" | "grep"
      python_version: "<string>"  # Optional
    ---

### §R.2 Required Top-Level Sections

PIN-001 to PIN-009: Required sections and order
Rule: The document MUST contain the following sections in this order:

- PIN-001: ## SSOT Declaration
- PIN-002: ## Scope
- PIN-003: ### In Scope
- PIN-004: ### Out of Scope
- PIN-005: ## Decisions (Binding)
- PIN-006: ## External Dependencies
- PIN-007: ## File Manifest
- PIN-008: ## Test Strategy
- PIN-009: ## Phase 0

PIN-S01: Section ordering
Rule: Sections MUST appear in the order specified by PIN-001 to PIN-009. A section appearing before its predecessor is an error.

PIN-010 to PIN-012: External Dependencies subsections required
Rule: The “## External Dependencies” section MUST contain these subsections:

- PIN-010: ### Required Files/Modules
- PIN-011: ### Required Libraries
- PIN-012: ### Required Tools

### §R.3 Forbidden Patterns (Global)

PIN-F01: No unresolved markers
Rule: The document MUST NOT contain these markers anywhere (case-insensitive):
- TBD, TODO, TBC, FIXME, XXX
Exception: comments (as defined by the linter) may be excluded from this scan.

PIN-F02: No unfilled placeholders
Rule: The document MUST NOT contain [[PLACEHOLDER]]-style tokens.
Exception: [[PH:...]] is reserved for the output template and may appear only where explicitly permitted by other documents; it is not a valid unresolved placeholder format for prose input.

PIN-F03: No unanswered questions
Rule: Lines MUST NOT end with a single “?”.
Exception: “??” may be used in code contexts.

PIN-F04: No tentative language
Rule: The document MUST NOT contain tentative phrases such as:
- “maybe we…”, “might add…”, “could use…”, “possibly implement…”, “potentially include…”, “consider adding…”

PIN-F05: No conditional logic
Rule: The document MUST NOT contain conditional statements such as:
- “if we… then…”, “if you… then…”, “if the… then…”

PIN-F06: No time estimates
Rule: The document MUST NOT contain time estimates such as:
- “2-3 hours”, “1-2 days”, “3-4 weeks”

PIN-F07: No pending decisions
Rule: The document MUST NOT contain phrases indicating unresolved decision state, such as:
- “pending”, “to be decided”, “TBD by…”

### §R.4 Context-Specific Forbidden Patterns

PIN-C01: No subjective terms in Success Criteria
Rule: Within Success Criteria sections, the following subjective terms are forbidden:
- good, nice, clean, proper, appropriate, reasonable, adequate

Rationale (informative): success criteria must be measurable and verifiable.

### §R.5 Task Structure

PIN-T00: Tasks required
Rule: The document MUST contain at least one task heading matching the pattern:
- #### Task N.M — Name

PIN-T01: Unique task IDs
Rule: Task IDs in N.M format MUST be unique across the document.

PIN-T02: Required task fields
Rule: Tasks MUST contain required fields depending on phase:

- Phase 0 tasks MUST contain:
  - **Objective**
  - **Paths**

- Non-Phase-0 tasks MUST contain:
  - **Objective**
  - **Paths**
  - **Precondition** (including a symbol check command)
  - **TDD Specification**
  - **Success Criteria**

PIN-T03: Paths format (recommended)
Guideline: Paths SHOULD use backticks, e.g., `src/path/file.py`.

PIN-T04: Search tool consistency
Rule: Precondition commands MUST use the search_tool declared in YAML front matter.
- If search_tool is rg, preconditions MUST NOT use grep.

PIN-T05: Success criteria checkboxes (recommended)
Guideline: Success Criteria SHOULD contain checkbox items of the form:
- [ ] criterion

### §R.6 Decisions Table

PIN-D01: Decisions table populated
Rule: The Decisions table MUST have at least one decision row (beyond header and separator).

PIN-D02: Decisions table columns
Rule: The Decisions table MUST contain these columns:
- ID
- Decision
- Rationale

Guideline: A column “Alternatives Rejected” is recommended.

### §R.7 File Manifest

PIN-M01: File Manifest populated
Rule: The File Manifest table MUST have at least one file entry.

PIN-M02: File paths format (recommended)
Guideline: File paths in the manifest SHOULD use backticks, e.g., `src/path/file.py`.

### §R.8 Submission Checklist

PIN-CL01: Checklist section required
Rule: The document MUST contain a section titled:
- ## Checklist Before Submission

PIN-CL02: All items checked
Rule: All checklist items MUST be checked ([x]) before the document is valid for conversion.

### §R.9 Linter Behavior Contract

PIN-LNT-001: Exit codes
Rule: The linter MUST use these exit codes:
- 0: valid (ready for conversion)
- 1: validation errors (do not convert)
- 2: schema/parse error (malformed document)
- 3: usage/file error

PIN-LNT-002: Diagnostics format
Rule: Default (human-readable) diagnostics MUST be formatted as:
- Line N: [RULE_ID] message

PIN-LNT-003: JSON output
Rule: With a --json flag, the linter MUST emit a JSON object containing at minimum:
- file (string)
- valid (bool)
- schema_version (string)
- error_count (int)
- warning_count (int)
- metadata (object)
- errors (array)

PIN-LNT-004: Fix hints
Rule: With a --fix-hints flag, the linter MUST show suggested fixes for each error.

### §R.10 Severity Levels

PIN-SEV-001: Error vs Warning semantics
Rule: The linter MUST support severities with these meanings:

- ERROR: must fix; blocks conversion (exit code 1)
- WARNING: should fix; does not block conversion, but may cause poor output

### §R.11 Minimal Compliance Summary (Informative)

A document is compliant if all of the following hold:

1) YAML front matter present with prose_input block (PIN-Y01, PIN-Y02)
2) Required YAML fields present and valid (PIN-Y03 to PIN-Y08)
3) schema_version matches VERSION.yaml (PIN-Y05)
4) Required sections present in order (PIN-001 to PIN-012, PIN-S01)
5) No forbidden patterns (PIN-F01 to PIN-F07)
6) No subjective terms in Success Criteria (PIN-C01)
7) At least one task present (PIN-T00)
8) Task IDs unique (PIN-T01)
9) Task fields complete per phase (PIN-T02)
10) Search tool consistent in preconditions (PIN-T04)
11) Decisions table populated (PIN-D01, PIN-D02)
12) File Manifest populated (PIN-M01)
13) Submission checklist present and fully checked (PIN-CL01, PIN-CL02)

### §R.12 Rule ID Namespaces (Informative)

| Prefix | Domain |
|--------|--------|
| PIN-Y | YAML front matter |
| PIN- (numeric) | Required sections |
| PIN-S | Section ordering |
| PIN-F | Forbidden patterns |
| PIN-C | Context-specific forbidden patterns |
| PIN-T | Task structure |
| PIN-D | Decisions table |
| PIN-M | File Manifest |
| PIN-CL | Submission checklist |
| PIN-LNT | Linter behavior |
| PIN-SEV | Severity levels |

### §R.13 Relationship to Other Documents (Informative)

| Document | Relationship |
|----------|--------------|
| PROSE_INPUT_TEMPLATE.md | Template that implements this spec |
| tools/prose_input_linter.py | Linter that enforces this spec |
| PROMPT_PROSE_INPUT_REVIEW.md | Semantic review after linter passes |
| AI_TASK_LIST_SPEC.md | Spec for the output format |

## §V VALIDATION

### §V.1 Rule-Anchored Validation Checklist

- [ ] YAML front matter present and valid (PIN-Y01 to PIN-Y08)
- [ ] Required sections present and in correct order (PIN-001 to PIN-012, PIN-S01)
- [ ] Forbidden patterns absent (PIN-F01 to PIN-F07)
- [ ] Context-specific forbidden patterns absent in Success Criteria (PIN-C01)
- [ ] At least one task present and uniquely identified (PIN-T00, PIN-T01)
- [ ] Task field completeness per phase (PIN-T02)
- [ ] Search tool consistency (PIN-T04)
- [ ] Decisions table populated and has required columns (PIN-D01, PIN-D02)
- [ ] File Manifest populated (PIN-M01)
- [ ] Submission checklist present and fully checked (PIN-CL01, PIN-CL02)
- [ ] Linter behavior contract implemented (PIN-LNT-001 to PIN-LNT-004)
- [ ] Severity semantics implemented (PIN-SEV-001)

## §C CHANGELOG

- 1.0.0 (2025-12-16): Converted PROSE_INPUT_SPEC.md into SPEKSI layer structure (META/ARCHITECTURE/DEFINITIONS/RULES/VALIDATION/CHANGELOG/GLOSSARY) without intended semantic changes to the existing PIN-* rule set; removed Markdown fences to satisfy Kernel constraints.

## §G GLOSSARY

Prose Input Specification
A normative contract defining the required structure and forbidden patterns for prose input documents used for AI Task List conversion.

Prose Input
A structured Markdown document that serves as input for AI Task List conversion.

Conversion
Transformation of Prose Input into an AI Task List artifact using an orchestrator prompt.

Deterministic validation
Repeatable validation enforced by a linter that checks structure, ordering, and forbidden patterns.

Semantic review
A non-deterministic review step (human or LLM) performed after deterministic validation passes.

End of Document
