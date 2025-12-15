---
ai_task_list:
  schema_version: "1.6"
  mode: "template"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# AI_TASK_LIST_TEMPLATE.md

**Version**: 6.0 (v1.6 spec)
**Scope**: Pydantic Schema Implementation for doxstrux parser output validation
**Modes**: Template mode (placeholders allowed) → Instantiated mode (placeholders forbidden)

---

## Non-negotiable Invariants

1. **Clean Table is a delivery gate** — Do not mark complete unless verified and stable.
2. **No silent errors** — Errors raise unconditionally.
3. **No weak tests** — Tests assert semantics, not existence/import/smoke.
4. **Single runner principle** — `uv` everywhere; no `.venv/bin/python`, `python -m`, or `pip install`.
5. **Evidence anchors required** — Claims require command output or file evidence.
6. **No synthetic reality** — Do not invent outputs, results, or versions.
7. **Import hygiene** — Absolute imports preferred; no multi-dot relative (`from ..`); no wildcards (`import *`).

---

## Placeholder Protocol

**Format**: `[[PH:NAME]]` where NAME is `[A-Z0-9_]+`

**Pre-flight** (must return zero — fails if placeholders found):
```bash
$ if rg '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md; then
>   echo "ERROR: Placeholders found"
>   exit 1
> fi
```

---

## Source of Truth Hierarchy

1. Executed tests + tool output (highest)
2. Repository state (commit hash)
3. Runtime code (`src/doxstrux/markdown/output_models.py` once created)
4. This task list
5. Design docs (`PYDANTIC_SCHEMA.md` — historical once execution begins)

**Drift rule**: Higher wins. Update lower source and log in Drift Ledger.

---

# Pydantic Schema Implementation — Task List

**Status**: Phase 0 — NOT STARTED

---

## Prose Coverage Mapping

| Prose Requirement | Source Section | Implemented by Task(s) |
|-------------------|----------------|------------------------|
| Phase 0: Shape Discovery Tool | Phase 0.1 | Task 0.1, 0.2 |
| Phase 0: Security Field Verification | Phase 0.1.1 | Task 0.3 |
| Milestone A: Add Pydantic Dependency | Task A.1 | Task 1.1 |
| Milestone A: Create Minimal Models | Task A.2 | Task 1.2 |
| Milestone A: Create Minimal Test | Task A.3 | Task 1.3 |
| Milestone A: RAG Safety Tests | Task A.3 (TestEarlyRAGSafety) | Task 1.4 |
| Milestone B1: Metadata/Security Models | Task B1.0 | Task 2.1 |
| Milestone B1: Schema Export Tool | Task B.1 | Task 2.2 |
| Milestone B1.5a: Content + Mappings | B1.5a | Task 3.1 |
| Milestone B1.5b: Sections/Headings/Paragraphs | B1.5b | Task 3.2 |
| Milestone B1.5c: Lists + Tasklists | B1.5c | Task 3.3 |
| Milestone B1.5d: Tables/CodeBlocks/Blockquotes | B1.5d | Task 3.4 |
| Milestone B1.5e: Links/Images/Math/Footnotes/HTML | B1.5e | Task 3.5 |
| Milestone B1.5f: DocumentIR Regression | B1.5f | Task 3.6 |
| Milestone B2: Curated Fixture Validation | Task B2.2 | Task 4.1 |
| Milestone B2: Fixture Regeneration | Task B2.3 | Task 4.2 |
| Milestone B2: Legacy Field Audit | B2.4, B2.5 | Task 4.3 |
| Milestone C: Full Validation Tool | Task C.1 | Task 5.1 |
| Milestone C: CI Integration Tests | Task C.2, C.3 | Task 5.2 |
| Milestone D: CI Gate | Task D.1, D.2 | Task 6.1 |
| CI Guard: DoxBaseModel extra=forbid | Branching Policy | Task 6.2 |

---

## Baseline Snapshot (capture before any work)

| Field | Value |
|-------|-------|
| Date | [[PH:DATE_YYYY_MM_DD]] |
| Repo | doxstrux |
| Branch | [[PH:GIT_BRANCH]] |
| Commit | [[PH:GIT_COMMIT]] |
| Runner | uv [[PH:UV_VERSION]] |
| Runtime | Python [[PH:PYTHON_VERSION]] |

**Evidence** (paste outputs):
```bash
$ git rev-parse --abbrev-ref HEAD
[[PH:OUTPUT]]

$ git rev-parse HEAD
[[PH:OUTPUT]]

$ uv --version
[[PH:OUTPUT]]

$ uv run python --version
[[PH:OUTPUT]]
```

**Baseline tests**:
```bash
$ uv run pytest tests/ -q --tb=no
[[PH:OUTPUT]]
```

---

## Phase 0 — Baseline Reality

**Tests**: `uv run pytest tests/ -q` / `uv run pytest tests/`

### Task 0.1 — Instantiate + capture baseline

**Objective**: Create PROJECT_TASKS.md and capture baseline evidence.

**Paths**:
```bash
TASK_0_1_PATHS=(
  "PROJECT_TASKS.md"
)
```

**Steps**:
1. Copy template to PROJECT_TASKS.md
2. Replace all `[[PH:NAME]]` placeholders with real values
3. Run pre-flight (must be zero)
4. Run baseline commands, paste outputs
5. If failures: log in Drift Ledger, stop

**Verification**:
```bash
$ if rg '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md; then
>   echo "ERROR: Placeholders found"
>   exit 1
> fi
$ for p in "${TASK_0_1_PATHS[@]}"; do test -e "$p" || exit 1; done
```

- [ ] Placeholders zero
- [ ] Snapshot captured
- [ ] Tests captured
- [ ] Paths exist

**Status**: 📋 PLANNED

---

### Task 0.2 — Run shape discovery tool

**Objective**: Execute `tools/discover_parser_shape.py` to collect actual parser output structure.

**Paths**:
```bash
TASK_0_2_PATHS=(
  "tools/discover_parser_shape.py"
  "tools/discovery_output/all_keys.txt"
  "tools/discovery_output/sample_outputs.json"
)
```

**Steps**:
1. Create `tools/discover_parser_shape.py` as specified in PYDANTIC_SCHEMA.md Phase 0.1
2. Run tool with `uv run python tools/discover_parser_shape.py`
3. Review `all_keys.txt` for expected top-level keys
4. Verify `sample_outputs.json` has representative samples

**Verification**:
```bash
$ test -f tools/discovery_output/all_keys.txt && echo "PASS" || echo "FAIL"
$ rg '^metadata\.' tools/discovery_output/all_keys.txt | head -3
$ rg '^structure\.' tools/discovery_output/all_keys.txt | head -3
```

- [ ] Discovery tool created
- [ ] `all_keys.txt` generated
- [ ] Top-level keys (metadata, content, structure, mappings) present
- [ ] Sample outputs captured

**Status**: 📋 PLANNED

---

### Task 0.3 — Verify security field paths

**Objective**: Run Phase 0.1.1 security field verification to ensure RAG-critical paths exist.

**Paths**:
```bash
TASK_0_3_PATHS=(
  "tools/discovery_output/sample_outputs.json"
)
```

**Steps**:
1. Run security field verification script from PYDANTIC_SCHEMA.md Phase 0.1.1
2. Check that required security paths exist in >=80% of samples
3. If >20% missing: investigate and fix before proceeding

**Verification**:
```bash
$ uv run python -c "
import json
from pathlib import Path

samples = json.loads((Path('tools/discovery_output/sample_outputs.json')).read_text())

REQUIRED = [
    'metadata.security.statistics.has_script',
    'metadata.security.summary.has_dangerous_content',
    'metadata.security.warnings',
]

def check_path(obj, path):
    parts = path.split('.')
    current = obj
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True

total = len(samples)
for p in REQUIRED:
    found = sum(1 for s in samples if check_path(s['output'], p))
    pct = (found / total) * 100 if total else 0
    status = 'OK' if pct >= 80 else 'WARN'
    print(f'{status}: {p} - {pct:.0f}% ({found}/{total})')
"
```

- [ ] Security fields verified
- [ ] No critical path missing >20%
- [ ] Ready for Milestone A

**Status**: 📋 PLANNED

---

### Task 0.4 — Create phase unlock artifact

**Objective**: Generate `.phase-0.complete.json` with real values.

**Paths**:
```bash
TASK_0_4_PATHS=(
  ".phase-0.complete.json"
)
```

**Steps**:
```bash
$ cat > .phase-0.complete.json << EOF
{
  "phase": 0,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "test_command": "uv run pytest tests/ -q",
  "result": "PASS"
}
EOF

$ if rg '\[\[PH:|YYYY-MM-DD|TBD' .phase-0.complete.json; then
>   echo "ERROR: Placeholder-like tokens found in artifact"
>   exit 1
> fi
```

- [ ] Artifact created with real timestamp
- [ ] Artifact has real commit hash
- [ ] No placeholders in artifact

**Status**: 📋 PLANNED

---

## Phase 1 — Minimal Schema + RAG Safety (Milestone A)

**Goal**: Create minimal Pydantic models with top-level validation and RAG safety tests.
**Tests**: `uv run pytest tests/test_output_models_minimal.py -v`

### Task 1.1 — Add Pydantic dependency

> **Naming rule**: Task ID `N.M` → Path array `TASK_N_M_PATHS` (dots become underscores)

**Objective**: Add Pydantic v2 to project dependencies.

**Paths**:
```bash
TASK_1_1_PATHS=(
  "pyproject.toml"
  "uv.lock"
)
```

**Scope**:
- In: Add `pydantic>=2,<3` to dependencies
- Out: No model implementation yet

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'pydantic' pyproject.toml || echo "pydantic not yet in deps"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from pydantic import BaseModel; print('pydantic available')"
# Expected: FAIL (ModuleNotFoundError) before adding dependency
```

### TDD Step 2 — Implement (minimal)

```bash
$ uv add "pydantic>=2,<3"
$ uv sync
```

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from pydantic import BaseModel; print('pydantic available')"
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 1.2 — Create minimal Pydantic models

**Objective**: Create `output_models.py` with ParserOutput and DoxBaseModel (extra="allow" for discovery).

**Paths**:
```bash
TASK_1_2_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: DoxBaseModel, ParserOutput with 4 top-level keys as `dict[str, Any]`, `empty()` method
- Out: Nested models (Milestone B)

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'class ParserOutput' src/doxstrux/markdown/ || echo "ParserOutput not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import ParserOutput; print(ParserOutput.empty())"
# Expected: FAIL (ImportError) before creating file
```

### TDD Step 2 — Implement (minimal)

Create `src/doxstrux/markdown/output_models.py` with:
- `DoxBaseModel` base class with `extra="allow"`
- `ParserOutput` with metadata, content, structure, mappings as `dict[str, Any]`
- `schema_version: str = "parser-output@1.0.0"`
- `empty()` classmethod returning minimal structure

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "
from doxstrux.markdown.output_models import ParserOutput
e = ParserOutput.empty()
assert e.schema_version == 'parser-output@1.0.0'
assert 'metadata' in e.model_dump()
print('ParserOutput.empty() OK')
"
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 1.3 — Create minimal schema validation tests

**Objective**: Create `tests/test_output_models_minimal.py` with TestMinimalSchemaValidation.

**Paths**:
```bash
TASK_1_3_PATHS=(
  "tests/test_output_models_minimal.py"
)
```

**Scope**:
- In: TestMinimalSchemaValidation class with 4 tests (empty constructs, four keys, real parser validates, discover extra)
- Out: RAG safety tests (Task 1.4), nested model tests

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'class TestMinimalSchemaValidation' tests/ || echo "TestMinimalSchemaValidation not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_minimal.py -v -k "TestMinimalSchemaValidation"
# Expected: FAIL (file not found or tests fail)
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_output_models_minimal.py` with:
- `test_empty_constructs` - verifies `ParserOutput.empty()` builds
- `test_empty_has_four_top_level_keys` - metadata, content, structure, mappings
- `test_real_parser_output_validates` - runs parser, validates with Pydantic
- `test_discover_extra_fields` - logs any extra fields for review

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_minimal.py -v -k "TestMinimalSchemaValidation"
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 1.4 — Create RAG safety tests

**Objective**: Create TestEarlyRAGSafety class with security behavior assertions.

**Paths**:
```bash
TASK_1_4_PATHS=(
  "tests/test_output_models_minimal.py"
)
```

**Scope**:
- In: TestEarlyRAGSafety with 3 tests (script_tag_detected, clean_document_not_blocked, javascript_link_detected)
- Out: Extended security semantics

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v -k "TestMinimalSchemaValidation"
$ rg 'class TestEarlyRAGSafety' tests/ || echo "TestEarlyRAGSafety not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_minimal.py -v -k "TestEarlyRAGSafety"
# Expected: FAIL (class not found or tests fail)
```

### TDD Step 2 — Implement (minimal)

Add to `tests/test_output_models_minimal.py`:
- `test_script_tag_detected_early` - `<script>` sets `has_script=True`, `has_dangerous_content=True`
- `test_clean_document_not_blocked` - clean markdown has `embedding_blocked=False`
- `test_javascript_link_detected_and_disallowed` - `javascript:` links flagged

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_minimal.py -v -k "TestEarlyRAGSafety"
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

## Phase 2 — Metadata + Security Models (Milestone B1)

**Goal**: Add typed nested models for Metadata and Security; switch to `extra="forbid"` on typed models.
**Tests**: `uv run pytest tests/test_output_models_minimal.py -v`

### Task 2.1 — Add Metadata and Security models

**Objective**: Expand `output_models.py` with Metadata, Security, SecurityStatistics, SecuritySummary, SecurityWarning, Encoding models.

**Paths**:
```bash
TASK_2_1_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Metadata, Security, SecurityStatistics, SecuritySummary, SecurityWarning, Encoding models with `extra="forbid"`
- Out: Structure/Mappings models (Phase 3)

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ rg 'class Metadata' src/doxstrux/markdown/output_models.py || echo "Metadata not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "
from doxstrux.markdown.output_models import Metadata, Security
print('Metadata and Security models available')
"
# Expected: FAIL (ImportError) before adding models
```

### TDD Step 2 — Implement (minimal)

Add to `output_models.py`:
- `Metadata` with typed fields: total_lines, total_chars, has_* booleans, node_counts, security, embedding_blocked, quarantined
- `Security` with warnings, statistics, summary, embedding_blocked, embedding_blocked_reason
- `SecurityStatistics` with all detection flags
- `SecuritySummary` with danger indicators
- `SecurityWarning` for security warnings list
- `Encoding` for optional encoding info
- All new models use `ConfigDict(extra="forbid")`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.output_models import ParserOutput

md = '# Hello\\n\\nWorld'
parser = MarkdownParserCore(md, security_profile='permissive')
raw = parser.parse()
validated = ParserOutput.model_validate(raw)
print(f'Metadata type: {type(validated.metadata)}')
assert hasattr(validated.metadata, 'total_lines')
print('Metadata model OK')
"
$ uv run pytest tests/test_output_models_minimal.py -v
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 2.2 — Create schema export tool

**Objective**: Create `tools/export_schema.py` to export JSON Schema from Pydantic models.

**Paths**:
```bash
TASK_2_2_PATHS=(
  "tools/export_schema.py"
  "schemas/parser_output.schema.json"
)
```

**Scope**:
- In: Export tool with deterministic output (sort_keys=True), schema verification
- Out: Full schema (Structure/Mappings still dict)

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ rg 'model_json_schema' tools/ || echo "export_schema.py not yet created"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python tools/export_schema.py
# Expected: FAIL (file not found)
```

### TDD Step 2 — Implement (minimal)

Create `tools/export_schema.py`:
- Import ParserOutput
- Call `model_json_schema()`
- Add metadata ($id, title, description)
- Write to `schemas/parser_output.schema.json` with `json.dumps(sort_keys=True)`
- Verify round-trip

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/export_schema.py
$ test -f schemas/parser_output.schema.json && echo "Schema exported"
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

## Phase 3 — Structure + Mappings Models (Milestone B1.5)

**Goal**: Add all remaining nested models; switch DoxBaseModel to `extra="forbid"`.
**Tests**: `uv run pytest tests/test_output_models_minimal.py tests/test_document_ir_regression.py -v`

### Task 3.1 — Add Content and Mappings models

**Objective**: Add Content, Mappings, MappingCodeBlock models.

**Paths**:
```bash
TASK_3_1_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Content (raw, lines), Mappings (line_to_type, line_to_section, prose_lines, code_lines, code_blocks), MappingCodeBlock
- Out: Structure models

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ rg 'class Content' src/doxstrux/markdown/output_models.py || echo "Content not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "
from doxstrux.markdown.output_models import Content, Mappings
print('Content and Mappings models available')
"
# Expected: FAIL before adding models
```

### TDD Step 2 — Implement (minimal)

Add models: Content, Mappings, MappingCodeBlock with typed fields.

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.output_models import ParserOutput

md = '\`\`\`python\\ncode\\n\`\`\`'
parser = MarkdownParserCore(md, security_profile='permissive')
validated = ParserOutput.model_validate(parser.parse())
assert hasattr(validated.content, 'raw')
assert hasattr(validated.mappings, 'code_blocks')
print('Content + Mappings OK')
"
$ uv run pytest tests/test_output_models_minimal.py -v
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 3.2 — Add Section, Heading, Paragraph models

**Objective**: Add structure models for sections, headings, paragraphs.

**Paths**:
```bash
TASK_3_2_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Section, Heading, Paragraph models
- Out: Lists, tables, code blocks

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ rg 'class Section' src/doxstrux/markdown/output_models.py || echo "Section not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "
from doxstrux.markdown.output_models import Section, Heading, Paragraph
print('Section, Heading, Paragraph models available')
"
# Expected: FAIL before adding models
```

### TDD Step 2 — Implement (minimal)

Add Section, Heading, Paragraph models with typed fields (id, level, title, start_line, end_line, etc.).

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.output_models import ParserOutput

md = '# Title\\n\\nParagraph text.'
parser = MarkdownParserCore(md, security_profile='permissive')
validated = ParserOutput.model_validate(parser.parse())
print(f'Sections: {len(validated.structure.sections)}')
print(f'Headings: {len(validated.structure.headings)}')
print(f'Paragraphs: {len(validated.structure.paragraphs)}')
print('Section/Heading/Paragraph OK')
"
$ uv run pytest tests/test_output_models_minimal.py -v
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 3.3 — Add List and Tasklist models

**Objective**: Add List, ListItem, Tasklist, TasklistItem, BlockRef models with recursive children.

**Paths**:
```bash
TASK_3_3_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: List, ListItem, Tasklist, TasklistItem, BlockRef with recursive children (use model_rebuild)
- Out: Tables, code blocks

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ rg 'class List\b' src/doxstrux/markdown/output_models.py || echo "List not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "
from doxstrux.markdown.output_models import List, ListItem, Tasklist, TasklistItem
print('List models available')
"
# Expected: FAIL before adding models
```

### TDD Step 2 — Implement (minimal)

Add List, ListItem, Tasklist, TasklistItem, BlockRef models.
Use `model_rebuild()` for recursive ListItem.children.

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.output_models import ParserOutput

md = '- item 1\\n  - nested\\n- item 2'
parser = MarkdownParserCore(md, security_profile='permissive')
validated = ParserOutput.model_validate(parser.parse())
print(f'Lists: {len(validated.structure.lists)}')
print('List models OK')
"
$ uv run pytest tests/test_output_models_minimal.py -v
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 3.4 — Add Table, CodeBlock, Blockquote models

**Objective**: Add Table, CodeBlock, Blockquote, BlockquoteChildrenSummary models.

**Paths**:
```bash
TASK_3_4_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Table, CodeBlock, Blockquote models
- Out: Links, images, math, footnotes, HTML

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ rg 'class Table\b' src/doxstrux/markdown/output_models.py || echo "Table not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "
from doxstrux.markdown.output_models import Table, CodeBlock, Blockquote
print('Table, CodeBlock, Blockquote models available')
"
# Expected: FAIL before adding models
```

### TDD Step 2 — Implement (minimal)

Add Table, CodeBlock, Blockquote, BlockquoteChildrenSummary models.

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.output_models import ParserOutput

md = '| a | b |\\n|---|---|\\n| 1 | 2 |\\n\\n\`\`\`python\\ncode\\n\`\`\`\\n\\n> quote'
parser = MarkdownParserCore(md, security_profile='permissive')
validated = ParserOutput.model_validate(parser.parse())
print(f'Tables: {len(validated.structure.tables)}')
print(f'CodeBlocks: {len(validated.structure.code_blocks)}')
print(f'Blockquotes: {len(validated.structure.blockquotes)}')
print('Table/CodeBlock/Blockquote OK')
"
$ uv run pytest tests/test_output_models_minimal.py -v
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 3.5 — Add Link, Image, Math, Footnotes, HTML models

**Objective**: Add remaining structure models including Link discriminated union.

**Paths**:
```bash
TASK_3_5_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Link (discriminated union: RegularLink | ImageLink), Image, Math, MathBlock, MathInline, Footnotes, FootnoteDefinition, FootnoteReference, HtmlBlock, HtmlInline
- Out: DoxBaseModel extra="forbid" switch

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ rg 'class Link\b' src/doxstrux/markdown/output_models.py || echo "Link not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "
from doxstrux.markdown.output_models import Link, Image, Math, Footnotes, HtmlBlock
print('Link, Image, Math, Footnotes, HtmlBlock models available')
"
# Expected: FAIL before adding models
```

### TDD Step 2 — Implement (minimal)

Add all remaining models:
- Link as discriminated union (RegularLink | ImageLink)
- Image, Math, MathBlock, MathInline
- Footnotes, FootnoteDefinition, FootnoteReference
- HtmlBlock, HtmlInline

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.output_models import ParserOutput

md = '[link](https://example.com)\\n\\n![img](pic.png)\\n\\n\$x^2\$\\n\\n[^1]: note\\n\\n<div>html</div>'
parser = MarkdownParserCore(md, security_profile='permissive')
validated = ParserOutput.model_validate(parser.parse())
print(f'Links: {len(validated.structure.links)}')
print(f'Images: {len(validated.structure.images)}')
print('All structure models OK')
"
$ uv run pytest tests/test_output_models_minimal.py -v
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 3.6 — Create DocumentIR regression test and switch to extra="forbid"

**Objective**: Add DocumentIR regression test; switch DoxBaseModel to `extra="forbid"`.

**Paths**:
```bash
TASK_3_6_PATHS=(
  "tests/test_document_ir_regression.py"
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: DocumentIR regression test, DoxBaseModel extra="forbid"
- Out: Feature branch merge to main

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ rg "extra.*=.*allow" src/doxstrux/markdown/output_models.py && echo "Still allow mode"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_document_ir_regression.py -v
# Expected: FAIL (file not found or tests fail)
```

### TDD Step 2 — Implement (minimal)

1. Create `tests/test_document_ir_regression.py` with TestDocumentIRRegression
2. Modify `output_models.py`: change DoxBaseModel `extra="allow"` to `extra="forbid"`
3. Run full validation to ensure no regressions

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_document_ir_regression.py -v
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run python -c "
from doxstrux.markdown.output_models import DoxBaseModel
assert DoxBaseModel.model_config.get('extra') == 'forbid', 'Must be forbid'
print('DoxBaseModel extra=forbid OK')
"
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

## Phase 4 — Validation Tools (Milestone B2)

**Goal**: Build curated fixture validation and regeneration tools.
**Tests**: `uv run pytest tests/ -q`

### Task 4.1 — Create curated fixture validation tool

**Objective**: Create `tools/validate_curated_fixtures.py` with pattern-based discovery.

**Paths**:
```bash
TASK_4_1_PATHS=(
  "tools/validate_curated_fixtures.py"
)
```

**Scope**:
- In: Pattern-based fixture discovery, ParserOutput.model_validate validation, MAX_CURATED=50
- Out: Full validation tool (Milestone C)

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'CURATED_PATTERNS' tools/ || echo "validate_curated_fixtures.py not yet created"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python tools/validate_curated_fixtures.py
# Expected: FAIL (file not found)
```

### TDD Step 2 — Implement (minimal)

Create `tools/validate_curated_fixtures.py`:
- CURATED_PATTERNS for glob-based discovery
- MAX_CURATED = 50
- validate_fixture() using ParserOutput.model_validate()
- Exit code 1 on any failure

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/validate_curated_fixtures.py
$ echo "Exit code: $?"
$ uv run pytest tests/ -q --tb=no
# Expected: PASS (exit 0 if fixtures valid)
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 4.2 — Create fixture regeneration tool

**Objective**: Create `tools/regenerate_fixtures.py` with bucket-aware classification.

**Paths**:
```bash
TASK_4_2_PATHS=(
  "tools/regenerate_fixtures.py"
)
```

**Scope**:
- In: classify_fixture (structural/security/legacy), --bucket arg, --review flag, --dry-run
- Out: Full regeneration pipeline

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'classify_fixture' tools/ || echo "regenerate_fixtures.py not yet created"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python tools/regenerate_fixtures.py --help
# Expected: FAIL (file not found)
```

### TDD Step 2 — Implement (minimal)

Create `tools/regenerate_fixtures.py`:
- classify_fixture() based on path patterns (security, legacy, structural)
- --bucket argument (structural, security, legacy)
- --review flag for security bucket
- --dry-run for preview
- ParserOutput.model_validate() before writing

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/regenerate_fixtures.py --help
$ uv run python tools/regenerate_fixtures.py --bucket structural --dry-run | head -10
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 4.3 — Create legacy field audit test

**Objective**: Create `tests/test_no_legacy_field_runtime_usage.py` to enforce legacy field audit.

**Paths**:
```bash
TASK_4_3_PATHS=(
  "tests/test_no_legacy_field_runtime_usage.py"
)
```

**Scope**:
- In: LEGACY_FIELDS_TO_AUDIT list, rg-based search of src/, pytest parametrized test
- Out: Full CI integration

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'LEGACY_FIELDS_TO_AUDIT' tests/ || echo "test_no_legacy_field_runtime_usage.py not yet created"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_no_legacy_field_runtime_usage.py -v
# Expected: FAIL (file not found)
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_no_legacy_field_runtime_usage.py`:
- LEGACY_FIELDS_TO_AUDIT = ["exception_was_raised"]
- test_no_runtime_usage_of_legacy_field() using rg to search src/

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_no_legacy_field_runtime_usage.py -v
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

## Phase 5 — Full Validation (Milestone C)

**Goal**: Validate ALL fixtures in report-only mode.
**Tests**: `uv run pytest tests/ -q`

### Task 5.1 — Create full validation tool

**Objective**: Create `tools/validate_test_pairs.py` with --report mode and --threshold option.

**Paths**:
```bash
TASK_5_1_PATHS=(
  "tools/validate_test_pairs.py"
)
```

**Scope**:
- In: Validate ALL test pairs, --report (exit 0), --threshold N, --output JSON report
- Out: CI blocking (Milestone D)

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'validate_directory' tools/ || echo "validate_test_pairs.py not yet created"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python tools/validate_test_pairs.py --report
# Expected: FAIL (file not found)
```

### TDD Step 2 — Implement (minimal)

Create `tools/validate_test_pairs.py`:
- validate_directory() returns (count, failures)
- --report mode (always exit 0)
- --threshold N (pass if >= N% valid)
- --output JSON report with failures

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/validate_test_pairs.py --report
$ uv run python tools/validate_test_pairs.py --threshold 95
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 5.2 — Create comprehensive schema tests

**Objective**: Create `tests/test_output_models_empty.py` and `tests/test_parser_output_schema_conformance.py`.

**Paths**:
```bash
TASK_5_2_PATHS=(
  "tests/test_output_models_empty.py"
  "tests/test_parser_output_schema_conformance.py"
)
```

**Scope**:
- In: TestEmptyBaseline (10 tests), TestParserOutputSchemaConformance, TestSecuritySemantics, TestLinkDiscriminatedUnion, TestMathExtraction, TestFootnoteExtraction
- Out: CI gate tests

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'class TestEmptyBaseline' tests/ || echo "TestEmptyBaseline not yet defined"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_empty.py tests/test_parser_output_schema_conformance.py -v
# Expected: FAIL (files not found or tests fail)
```

### TDD Step 2 — Implement (minimal)

Create both test files with full test coverage as specified in PYDANTIC_SCHEMA.md Task C.2 and C.3.

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_empty.py -v
$ uv run pytest tests/test_parser_output_schema_conformance.py -v
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

## Phase 6 — CI Gate (Milestone D)

**Goal**: Make schema validation a blocking CI gate.
**Tests**: `uv run pytest tests/ -q`

### Task 6.1 — Create CI workflow and schema version test

**Objective**: Create `.github/workflows/schema_validation.yml` and `tests/test_schema_version.py`.

**Paths**:
```bash
TASK_6_1_PATHS=(
  ".github/workflows/schema_validation.yml"
  "tests/test_schema_version.py"
)
```

**Scope**:
- In: CI job with 100% threshold, schema version format test, schema drift detection
- Out: Production deployment

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'schema-validation' .github/workflows/ || echo "schema_validation.yml not yet created"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_schema_version.py -v
# Expected: FAIL (file not found)
```

### TDD Step 2 — Implement (minimal)

1. Create `tests/test_schema_version.py` with TestSchemaVersion class
2. Create `.github/workflows/schema_validation.yml` with:
   - Schema version check
   - validate_test_pairs.py --threshold 100
   - export_schema.py + git diff check

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_schema_version.py -v
$ uv run python tools/validate_test_pairs.py --threshold 100
$ uv run pytest tests/ -q --tb=no
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 6.2 — Create DoxBaseModel extra=forbid CI guard

**Objective**: Create `tests/test_schema_extra_forbid.py` to prevent accidental merge of extra="allow".

**Paths**:
```bash
TASK_6_2_PATHS=(
  "tests/test_schema_extra_forbid.py"
)
```

**Scope**:
- In: CI guard test that fails if DoxBaseModel.extra != "forbid" on main branch
- Out: None (final task)

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/ -q --tb=no
$ rg 'test_doxbasemodel_extra_is_forbid' tests/ || echo "test_schema_extra_forbid.py not yet created"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_schema_extra_forbid.py -v
# Expected: FAIL (file not found or test fails if extra="allow")
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_schema_extra_forbid.py`:
- get_current_branch() helper
- ENFORCE_BRANCHES = {"main", "master", ...}
- test_doxbasemodel_extra_is_forbid() with skipif for non-main branches

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_schema_extra_forbid.py -v
$ uv run pytest tests/ -q --tb=no
# Expected: PASS (or skip on non-main branch)
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

## Drift Ledger (append-only)

| Date | Higher | Lower | Mismatch | Resolution | Evidence |
|------|--------|-------|----------|------------|----------|
| | | | | | |

---

## Phase Unlock Artifact

Generate with real values (commands must use $ prefix when instantiated):
```bash
$ cat > .phase-N.complete.json << EOF
{
  "phase": N,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "test_command": "uv run pytest tests/ -q",
  "result": "PASS"
}
EOF

$ if rg '\[\[PH:|YYYY-MM-DD|TBD' .phase-N.complete.json; then
>   echo "ERROR: Placeholder-like tokens found in artifact"
>   exit 1
> fi
```

---

## Global Clean Table Scan

Run before each phase gate (commands must use $ prefix when instantiated):

```bash
# Standard patterns:
$ rg 'TODO|FIXME|XXX' src/ && exit 1 || echo "No unfinished markers"
$ rg '\[\[PH:' . && exit 1 || echo "No placeholders"

# Python import hygiene (REQUIRED for runner=uv):
$ if rg 'from \.\.' src/; then
>   echo "ERROR: Multi-dot relative import found"
>   exit 1
> fi
$ if rg 'import \*' src/; then
>   echo "ERROR: Wildcard import found"
>   exit 1
> fi
```

**Evidence** (paste output):
```
[[PH:PASTE_CLEAN_TABLE_OUTPUT]]
```

---

## STOP — Phase Gate

Requirements for Phase N+1:

- [ ] All Phase N tasks ✅ COMPLETE
- [ ] Phase N tests pass
- [ ] Global Clean Table scan passes (output pasted above)
- [ ] `.phase-N.complete.json` exists
- [ ] All paths exist
- [ ] Drift ledger current

---

**End of Task List**
