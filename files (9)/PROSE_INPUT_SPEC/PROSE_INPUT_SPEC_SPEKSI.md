<!--
SPEC_KIND: linting_domain
SPEC_ID: PROSE_INPUT_SPEC
SPEC_VERSION: 2.0.0
STATUS: active
-->

# PROSE INPUT SPECIFICATION

## §0 META

- **Purpose**: Define normative contract for Prose Input Markdown documents used as input for AI Task List conversion
- **Scope**: Input validation, forbidden patterns, task structure, decisions table, file manifest
- **Tier**: Framework
- **Drift Budget**: 0 — Any violation MUST fail the linter

---

## §1 DEFINITIONS

### §1.1 Document Terms

| Term | Definition |
|------|------------|
| `Prose Input` | Structured Markdown document serving as input for AI Task List conversion |
| `Conversion` | Process of transforming Prose Input into AI Task List using orchestrator prompt |
| `Discovery` | Optional phase where facts are gathered from codebase before writing Prose Input |
| `Sample Artifacts` | Real output pasted from running commands, not fabricated examples |

### §1.2 Configuration Terms

| Term | Definition |
|------|------------|
| `schema_version` | Version string matching VERSION.yaml |
| `runner` | Toolchain used for commands: uv, npm, cargo, go, poetry, pipenv |
| `runner_prefix` | Prefix for runner-managed commands (may be empty) |
| `search_tool` | Text search command: rg or grep |

### §1.3 Required Sections

| Section | Rule ID |
|---------|---------|
| `## SSOT Declaration` | PIN-SEC-001 |
| `## Scope` | PIN-SEC-002 |
| `### In Scope` | PIN-SEC-003 |
| `### Out of Scope` | PIN-SEC-004 |
| `## Decisions (Binding)` | PIN-SEC-005 |
| `## External Dependencies` | PIN-SEC-006 |
| `## File Manifest` | PIN-SEC-007 |
| `## Test Strategy` | PIN-SEC-008 |
| `## Phase 0` | PIN-SEC-009 |
| `### Required Files/Modules` | PIN-SEC-010 |
| `### Required Libraries` | PIN-SEC-011 |
| `### Required Tools` | PIN-SEC-012 |

---

## §2 RULES

| Rule ID | Description | Enforcement |
|---------|-------------|-------------|
| PIN-SSOT-001 | This specification is the authoritative contract for prose input documents | enforce_pin_ssot_001 |
| PIN-SSOT-002 | If spec and linter diverge, linter MUST be updated to match spec | enforce_pin_ssot_002 |
| PIN-YML-001 | Document MUST start with YAML front matter delimited by `---` | enforce_pin_yml_001 |
| PIN-YML-002 | YAML front matter MUST contain `prose_input:` block | enforce_pin_yml_002 |
| PIN-YML-003 | prose_input block MUST contain: schema_version, project_name, runner, runner_prefix, search_tool | enforce_pin_yml_003 |
| PIN-YML-004 | All required YAML fields MUST be strings | enforce_pin_yml_004 |
| PIN-YML-005 | schema_version MUST exactly match VERSION.yaml | enforce_pin_yml_005 |
| PIN-YML-006 | runner MUST be one of: uv, npm, cargo, go, poetry, pipenv | enforce_pin_yml_006 |
| PIN-YML-007 | search_tool MUST be one of: rg, grep | enforce_pin_yml_007 |
| PIN-YML-008 | YAML field values MUST NOT contain `[[` or `]]` placeholder tokens | enforce_pin_yml_008 |
| PIN-SEC-001 | Document MUST contain `## SSOT Declaration` section | enforce_pin_sec_001 |
| PIN-SEC-002 | Document MUST contain `## Scope` section | enforce_pin_sec_002 |
| PIN-SEC-003 | Document MUST contain `### In Scope` subsection | enforce_pin_sec_003 |
| PIN-SEC-004 | Document MUST contain `### Out of Scope` subsection | enforce_pin_sec_004 |
| PIN-SEC-005 | Document MUST contain `## Decisions (Binding)` section | enforce_pin_sec_005 |
| PIN-SEC-006 | Document MUST contain `## External Dependencies` section | enforce_pin_sec_006 |
| PIN-SEC-007 | Document MUST contain `## File Manifest` section | enforce_pin_sec_007 |
| PIN-SEC-008 | Document MUST contain `## Test Strategy` section | enforce_pin_sec_008 |
| PIN-SEC-009 | Document MUST contain `## Phase 0` section | enforce_pin_sec_009 |
| PIN-SEC-010 | External Dependencies MUST contain `### Required Files/Modules` | enforce_pin_sec_010 |
| PIN-SEC-011 | External Dependencies MUST contain `### Required Libraries` | enforce_pin_sec_011 |
| PIN-SEC-012 | External Dependencies MUST contain `### Required Tools` | enforce_pin_sec_012 |
| PIN-ORD-001 | Sections MUST appear in order PIN-SEC-001 to PIN-SEC-009; preceding section before succeeding | enforce_pin_ord_001 |
| PIN-FBN-001 | Document MUST NOT contain: TBD, TODO, TBC, FIXME, XXX (case-insensitive) | enforce_pin_fbn_001 |
| PIN-FBN-002 | Document MUST NOT contain `[[PLACEHOLDER]]` tokens (except `[[PH:...]]` reserved format) | enforce_pin_fbn_002 |
| PIN-FBN-003 | Lines MUST NOT end with single `?` (except `??` in code) | enforce_pin_fbn_003 |
| PIN-FBN-004 | Document MUST NOT contain tentative phrases: maybe, might, could, possibly, potentially, consider | enforce_pin_fbn_004 |
| PIN-FBN-005 | Document MUST NOT contain conditional statements: if we... then, if you... then | enforce_pin_fbn_005 |
| PIN-FBN-006 | Document MUST NOT contain time estimates: 2-3 hours, 1-2 days, etc. | enforce_pin_fbn_006 |
| PIN-FBN-007 | Document MUST NOT contain pending decision phrases: pending, to be decided, TBD by | enforce_pin_fbn_007 |
| PIN-CTX-001 | Success Criteria MUST NOT contain subjective terms: good, nice, clean, proper, appropriate, reasonable, adequate | enforce_pin_ctx_001 |
| PIN-TSK-001 | Document MUST contain at least one task matching `#### Task N.M — Name` | enforce_pin_tsk_001 |
| PIN-TSK-002 | Task IDs (N.M format) MUST be unique across document | enforce_pin_tsk_002 |
| PIN-TSK-003 | Phase 0 tasks MUST contain Objective, Paths; non-Phase-0 tasks MUST also contain Precondition, TDD Specification, Success Criteria | enforce_pin_tsk_003 |
| PIN-TSK-004 | Precondition commands MUST use search_tool declared in YAML; if rg, grep forbidden | enforce_pin_tsk_004 |
| PIN-DEC-001 | Decisions table MUST have at least one decision row (not just header/separator) | enforce_pin_dec_001 |
| PIN-DEC-002 | Decisions table MUST contain columns: ID, Decision, Rationale | enforce_pin_dec_002 |
| PIN-MAN-001 | File Manifest table MUST have at least one file entry | enforce_pin_man_001 |
| PIN-CHK-001 | Document MUST contain `## Checklist Before Submission` section | enforce_pin_chk_001 |
| PIN-CHK-002 | All checklist items MUST be checked `[x]` before document is valid | enforce_pin_chk_002 |
| PIN-LNT-001 | Linter exit codes: 0=valid, 1=validation errors, 2=schema/parse error, 3=usage/file error | enforce_pin_lnt_001 |
| PIN-LNT-002 | Default diagnostics format: `Line N: [RULE_ID] message` | enforce_pin_lnt_002 |
| PIN-LNT-003 | With --json, emit JSON with: file, valid, schema_version, error_count, warning_count, metadata, errors | enforce_pin_lnt_003 |
| PIN-LNT-004 | With --fix-hints, show suggested fixes for each error | enforce_pin_lnt_004 |
| PIN-SEV-001 | ERROR severity blocks conversion (exit 1); WARNING does not block but may cause poor output | enforce_pin_sev_001 |

---

## §3 INVARIANTS

| Invariant ID | Description | Enforcement |
|--------------|-------------|-------------|
| INV-SSOT-A | Spec is authoritative; linter implements spec | enforce_inv_ssot_a |
| INV-COMPLETE-A | All placeholders MUST be replaced before conversion | enforce_inv_complete_a |
| INV-DECISION-A | All decisions MUST be final before conversion | enforce_inv_decision_a |
| INV-FACTS-A | Facts are provided in input, not discovered during conversion | enforce_inv_facts_a |
| INV-DETERMINISM-A | Validation is deterministic and repeatable | enforce_inv_determinism_a |

---

## §4 PHASES

### Phase 1: YAML Validation
Validate front matter structure and field values.
Run PIN-YML-001, PIN-YML-002, PIN-YML-003, PIN-YML-004, PIN-YML-005, PIN-YML-006, PIN-YML-007, PIN-YML-008.

### Phase 2: Section Validation
Validate required sections exist in correct order.
Run PIN-SEC-001 to PIN-SEC-012, PIN-ORD-001.

### Phase 3: Forbidden Pattern Scan
Scan for forbidden patterns globally.
Run PIN-FBN-001, PIN-FBN-002, PIN-FBN-003, PIN-FBN-004, PIN-FBN-005, PIN-FBN-006, PIN-FBN-007.

### Phase 4: Context-Specific Validation
Validate context-specific rules.
Run PIN-CTX-001, PIN-TSK-001, PIN-TSK-002, PIN-TSK-003, PIN-TSK-004.

### Phase 5: Table Validation
Validate required tables.
Run PIN-DEC-001, PIN-DEC-002, PIN-MAN-001.

### Phase 6: Checklist Validation
Validate submission checklist.
Run PIN-CHK-001, PIN-CHK-002.

### Phase 7: Output Generation
Generate linter output.
Run PIN-LNT-001, PIN-LNT-002, PIN-LNT-003, PIN-LNT-004, PIN-SEV-001.

---

## §5 SCHEMAS

### §5.1 YAML Front Matter

```yaml
---
prose_input:
  schema_version: "<VERSION.yaml version>"
  project_name: "<string>"
  runner: "uv" | "npm" | "cargo" | "go" | "poetry" | "pipenv"
  runner_prefix: "<string>"
  search_tool: "rg" | "grep"
  python_version: "<string>"  # Optional
---
```

### §5.2 Task Structure

```markdown
#### Task N.M — <Name>

**Objective**: <single clear action>

**Paths**: `path/to/file.py`

**Precondition**: (non-Phase-0 only)
$ rg "symbol" path/

**TDD Specification**: (non-Phase-0 only)
- Test: test_function_name
- Behavior: <what it tests>

**Success Criteria**: (non-Phase-0 only)
- [ ] criterion 1
- [ ] criterion 2
```

### §5.3 Decisions Table

```markdown
| ID | Decision | Rationale | Alternatives Rejected |
|----|----------|-----------|----------------------|
| D1 | Use X | Because Y | A, B considered |
```

### §5.4 Linter JSON Output

```json
{
  "file": "path/to/file.md",
  "valid": true,
  "schema_version": "1.0.0",
  "error_count": 0,
  "warning_count": 0,
  "metadata": {},
  "errors": []
}
```

---

## §6 CLI COMMANDS

### §6.1 `prose_input_linter.py <file.md>`

**Purpose**: Validate Prose Input document against this specification.

**Flags**:
- `--json`: Output JSON instead of human-readable diagnostics
- `--fix-hints`: Show suggested fixes for each error

**Exit codes**:
- 0: Valid (ready for conversion)
- 1: Validation errors (do not convert)
- 2: Schema/parse error (malformed document)
- 3: Usage/file error

---

## §7 APPENDICES

### A. Rule ID Namespaces

| Prefix | Domain |
|--------|--------|
| `PIN-SSOT-` | SSOT policy |
| `PIN-YML-` | YAML front matter |
| `PIN-SEC-` | Required sections |
| `PIN-ORD-` | Section ordering |
| `PIN-FBN-` | Forbidden patterns |
| `PIN-CTX-` | Context-specific forbidden patterns |
| `PIN-TSK-` | Task structure |
| `PIN-DEC-` | Decisions table |
| `PIN-MAN-` | File Manifest |
| `PIN-CHK-` | Submission checklist |
| `PIN-LNT-` | Linter behavior |
| `PIN-SEV-` | Severity levels |
| `INV-` | Invariants |

### B. Forbidden Patterns (SSOT)

**Unresolved markers**: TBD, TODO, TBC, FIXME, XXX

**Tentative phrases**: maybe we, might add, could use, possibly implement, potentially include, consider adding

**Conditional statements**: if we... then, if you... then, if the... then

**Pending decisions**: pending, to be decided, TBD by

**Subjective terms (in Success Criteria)**: good, nice, clean, proper, appropriate, reasonable, adequate

### C. Valid Runners

- uv
- npm
- cargo
- go
- poetry
- pipenv

---

**END OF SPEC**
