# Prose Input Spec
<!-- See VERSION.yaml for framework version -->

**Schema version**: See `VERSION.yaml`
**Applies to**: Prose input documents used for AI Task List conversion
**SSOT**: The spec is the authoritative contract; the linter implements the spec. If spec and linter diverge, fix the linter.

**Primary goals**:
1. No ambiguity in input = no guessing in conversion
2. Input structure mirrors output structure
3. All decisions made before conversion
4. Facts provided, not discovered
5. Deterministic validation before semantic review

> This document is the normative contract for prose input documents. It is **not** a prose input
> and is **not** intended to be linted by `tools/prose_input_linter.py`.
> If this spec and the linter diverge, fix the linter to match the spec.

---

## 0. Definitions

| Term | Definition |
|------|------------|
| **Prose Input** | A structured markdown document that serves as input for AI Task List conversion |
| **Conversion** | The process of transforming prose input to AI Task List using the orchestrator prompt |
| **Discovery** | The optional phase where facts are gathered from codebase before writing prose input |
| **Sample Artifacts** | Real output pasted from running commands, not fabricated examples |

---

## 1. Required Document Header

### PIN-Y01: YAML front matter required

The document MUST start with YAML front matter delimited by `---`:

```yaml
---
prose_input:
  schema_version: "<VERSION.yaml version>"
  project_name: "<string>"
  runner: "<string>"
  runner_prefix: "<string>"
  search_tool: "rg" | "grep"
  python_version: "<string>"  # Optional
---
```

### PIN-Y02: prose_input block required

The YAML front matter MUST contain a `prose_input:` block.

### PIN-Y03: Required fields

The `prose_input:` block MUST contain these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | Yes | Must match VERSION.yaml |
| `project_name` | string | Yes | Project identifier |
| `runner` | string | Yes | Package runner tool |
| `runner_prefix` | string | Yes | Command prefix (may be empty string) |
| `search_tool` | string | Yes | Text search tool |
| `python_version` | string | No | Python version for Python projects |

### PIN-Y04: Field types

All required fields MUST be strings.

### PIN-Y05: Schema version match

`schema_version` MUST exactly match the version in `VERSION.yaml`.

### PIN-Y06: Valid runner

`runner` MUST be one of: `uv`, `npm`, `cargo`, `go`, `poetry`, `pipenv`.

### PIN-Y07: Valid search_tool

`search_tool` MUST be one of: `rg`, `grep`.

### PIN-Y08: No placeholders in YAML

YAML field values MUST NOT contain `[[` and `]]` placeholder tokens.

---

## 2. Required Top-Level Sections

### PIN-001 to PIN-009: Required sections

The document MUST contain these sections in this order:

| Rule ID | Section Heading | Purpose |
|---------|-----------------|---------|
| PIN-001 | `## SSOT Declaration` | What this document is authoritative for |
| PIN-002 | `## Scope` | Overall scope container |
| PIN-003 | `### In Scope` | Explicit list of what WILL be implemented |
| PIN-004 | `### Out of Scope` | Explicit list of what will NOT be implemented |
| PIN-005 | `## Decisions (Binding)` | All final decisions with rationale |
| PIN-006 | `## External Dependencies` | Pre-existing resources that must exist |
| PIN-007 | `## File Manifest` | All files to be created/modified |
| PIN-008 | `## Test Strategy` | How correctness will be verified |
| PIN-009 | `## Phase 0` | First phase (must exist, name may vary) |

### PIN-S01: Section ordering

Sections MUST appear in the order specified above. A section appearing before its predecessor is an error.

### PIN-010 to PIN-012: External Dependencies subsections

The `## External Dependencies` section MUST contain these subsections:

| Rule ID | Subsection Heading |
|---------|-------------------|
| PIN-010 | `### Required Files/Modules` |
| PIN-011 | `### Required Libraries` |
| PIN-012 | `### Required Tools` |

---

## 3. Forbidden Patterns

The following patterns are FORBIDDEN anywhere in the document (except comments):

### PIN-F01: No unresolved markers

The document MUST NOT contain: `TBD`, `TODO`, `TBC`, `FIXME`, `XXX` (case-insensitive).

**Rationale**: All items must be resolved before conversion. Unresolved markers indicate incomplete specification.

### PIN-F02: No unfilled placeholders

The document MUST NOT contain `[[PLACEHOLDER]]` tokens (except `[[PH:...]]` which is reserved for the output template).

**Rationale**: All placeholders from the template must be replaced with actual values.

### PIN-F03: No unanswered questions

Lines MUST NOT end with `?` (except `??` which may be used in code).

**Rationale**: All questions must be answered. Open questions indicate unresolved decisions.

### PIN-F04: No tentative language

The document MUST NOT contain tentative phrases like:
- "maybe we...", "might add...", "could use..."
- "possibly implement...", "potentially include..."
- "consider adding..."

**Rationale**: All statements must be definitive. Tentative language indicates unresolved decisions.

### PIN-F05: No conditional logic

The document MUST NOT contain conditional statements like:
- "if we... then..."
- "if you... then..."
- "if the... then..."

**Rationale**: Conditions must be resolved to concrete decisions before conversion.

### PIN-F06: No time estimates

The document MUST NOT contain time estimates like:
- "2-3 hours", "1-2 days", "3-4 weeks"

**Rationale**: Time estimates are not actionable. Use success criteria instead.

### PIN-F07: No pending decisions

The document MUST NOT contain:
- "pending", "to be decided", "TBD by..."

**Rationale**: All decisions must be final before conversion.

---

## 4. Context-Specific Forbidden Patterns

### PIN-C01: No subjective terms in Success Criteria

Within Success Criteria sections, the following terms are FORBIDDEN:
- "good", "nice", "clean", "proper"
- "appropriate", "reasonable", "adequate"

**Rationale**: Success criteria must be measurable, not subjective. Replace with specific, verifiable criteria.

---

## 5. Task Structure

### PIN-T00: Tasks required

The document MUST contain at least one task matching the pattern:
```
#### Task N.M — Name
```

### PIN-T01: Unique task IDs

Task IDs (N.M format) MUST be unique across the document.

### PIN-T02: Required task fields

**Phase 0 tasks** MUST contain:
- `**Objective**`
- `**Paths**`

**Non-Phase-0 tasks** MUST contain:
- `**Objective**`
- `**Paths**`
- `**Precondition**` (with symbol check)
- `**TDD Specification**`
- `**Success Criteria**`

### PIN-T03: Paths format

Paths SHOULD use backticks: `` `path/to/file.py` ``

### PIN-T04: Search tool consistency

Precondition commands MUST use the `search_tool` declared in YAML front matter.
- If `search_tool: rg`, preconditions MUST NOT use `grep`.

### PIN-T05: Success criteria checkboxes

Success Criteria SHOULD contain checkbox items: `- [ ] criterion`

---

## 6. Decisions Table

### PIN-D01: Decisions table populated

The Decisions table MUST have at least one decision row (not just header and separator).

### PIN-D02: Decisions table columns

The Decisions table MUST contain these columns:
- `ID`
- `Decision`
- `Rationale`

Recommended additional column: `Alternatives Rejected`

---

## 7. File Manifest

### PIN-M01: File Manifest populated

The File Manifest table MUST have at least one file entry.

### PIN-M02: File Manifest paths format

File paths in the manifest SHOULD use backticks: `` `src/path/file.py` ``

---

## 8. Submission Checklist

### PIN-CL01: Checklist section required

The document MUST contain a `## Checklist Before Submission` section.

### PIN-CL02: All items checked

All checklist items MUST be checked (`[x]`) before the document is valid for conversion.

---

## 9. Linter Behavior Contract

### PIN-LNT-001: Exit codes

| Code | Meaning |
|------|---------|
| 0 | Valid (ready for conversion) |
| 1 | Validation errors (do not convert) |
| 2 | Schema/parse error (malformed document) |
| 3 | Usage/file error |

### PIN-LNT-002: Diagnostics format

Default output (human-readable):
```
Line N: [RULE_ID] message
```

### PIN-LNT-003: JSON output

`--json` flag emits structured output:
```json
{
  "file": "path/to/file.md",
  "valid": true,
  "schema_version": "0.0.8",
  "error_count": 0,
  "warning_count": 0,
  "metadata": {...},
  "errors": [...]
}
```

### PIN-LNT-004: Fix hints

`--fix-hints` flag shows suggested fixes for each error.

---

## 10. Severity Levels

### PIN-SEV-001: Error vs Warning

| Severity | Meaning | Effect |
|----------|---------|--------|
| ERROR | Must fix | Blocks conversion (exit code 1) |
| WARNING | Should fix | Does not block, but may cause poor output |

---

## 11. Minimal Compliance Summary

A document is **Prose Input Spec compliant** if:

1. ✅ YAML front matter present with `prose_input:` block (PIN-Y01, PIN-Y02)
2. ✅ All required YAML fields present and valid (PIN-Y03 to PIN-Y08)
3. ✅ Schema version matches VERSION.yaml (PIN-Y05)
4. ✅ All required sections present in order (PIN-001 to PIN-012, PIN-S01)
5. ✅ No forbidden patterns anywhere (PIN-F01 to PIN-F07)
6. ✅ No subjective terms in Success Criteria (PIN-C01)
7. ✅ At least one task present (PIN-T00)
8. ✅ Task IDs unique (PIN-T01)
9. ✅ Task fields complete per phase (PIN-T02)
10. ✅ Search tool consistent in preconditions (PIN-T04)
11. ✅ Decisions table populated with required columns (PIN-D01, PIN-D02)
12. ✅ File Manifest populated (PIN-M01)
13. ✅ Submission checklist present and fully checked (PIN-CL01, PIN-CL02)

---

## 12. Rule ID Namespaces

| Prefix | Domain |
|--------|--------|
| `PIN-Y` | YAML front matter rules |
| `PIN-` (numeric) | Required sections |
| `PIN-S` | Section ordering |
| `PIN-F` | Forbidden patterns |
| `PIN-C` | Context-specific forbidden patterns |
| `PIN-T` | Task structure |
| `PIN-D` | Decisions table |
| `PIN-M` | File Manifest |
| `PIN-CL` | Submission checklist |
| `PIN-LNT` | Linter behavior |
| `PIN-SEV` | Severity levels |

---

## 13. Relationship to Other Documents

| Document | Relationship |
|----------|--------------|
| `PROSE_INPUT_TEMPLATE.md` | Template that implements this spec |
| `tools/prose_input_linter.py` | Linter that enforces this spec |
| `PROMPT_PROSE_INPUT_REVIEW.md` | Semantic review after linter passes |
| `AI_TASK_LIST_SPEC.md` | Spec for the output format |

---

**End of Spec**
