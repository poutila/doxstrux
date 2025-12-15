---
ai_task_list:
  schema_version: "1.6"
  mode: "plan"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# PYDANTIC_SCHEMA — Task List

**Version**: 1.0
**Scope**: Implement Pydantic-based schema validation for parser output per PYDANTIC_SCHEMA.md design.
**Modes**: Plan mode (real commands, evidence placeholders allowed)

---

## Non-negotiable Invariants

1. **Clean Table is a delivery gate** — Do not mark complete unless verified and stable.
2. **No silent errors** — Errors raise unconditionally.
3. **No weak tests** — Tests assert semantics, not existence/import/smoke.
4. **Single runner principle** — `uv run` everywhere.
5. **Evidence anchors required** — Claims require command output or file evidence.
6. **No synthetic reality** — Do not invent outputs, results, or versions.
7. **Import hygiene** — Absolute imports preferred; no multi-dot relative (`from ..`); no wildcards (`import *`).
8. **Permissive profile for schema** — Schema tests MUST use `security_profile="permissive"`.
9. **`empty()` is a helper, not a spec** — Do NOT require `parse("") == empty()`.

---

## Placeholder Protocol

**Format**: `[[PH:NAME]]` where NAME is `[A-Z0-9_]+`

**Pre-flight** (must return zero — fails if placeholders found):
```bash
$ if rg '\[\[PH:[A-Z0-9_]+\]\]' PYDANTIC_SCHEMA_tasks_template.md; then
>   echo "ERROR: Placeholders found"
>   exit 1
> fi
```

---

## Source of Truth Hierarchy

1. Executed tests + tool output (highest)
2. Repository state (commit hash)
3. Runtime code (`output_models.py` once it exists)
4. This task list
5. Design docs (`PYDANTIC_SCHEMA.md` — historical once implementation begins)

**Drift rule**: Higher wins. Update lower source and log in Drift Ledger.

---

## Prose Coverage Mapping

| Prose Requirement | Source Location | Implemented by Task(s) |
|-------------------|-----------------|------------------------|
| Add Pydantic dependency | Milestone A / Task A.1 | 1.1 |
| Create minimal ParserOutput model | Milestone A / Task A.2 | 1.2 |
| Create minimal schema test | Milestone A / Task A.3 | 1.3 |
| RAG safety tests (script, clean doc, javascript:) | Milestone A / Task A.3 (TestEarlyRAGSafety) | 1.3 |
| Phase 0 shape discovery | Phase 0 / Phase 0.1 | 0.3 |
| Security field verification | Phase 0 / Phase 0.1.1 | 0.4 |
| Metadata + Security models | Milestone B1 / Task B1.0 | 2.1 |
| Schema export tool | Milestone B1 / Task B.1 | 2.2 |
| Content + Mappings models | Milestone B1.5a | 3.1 |
| Sections + Headings + Paragraphs | Milestone B1.5b | 3.2 |
| Lists + Tasklists models | Milestone B1.5c | 3.3 |
| Tables + Code Blocks + Blockquotes | Milestone B1.5d | 3.4 |
| Links + Images + Math + Footnotes + HTML | Milestone B1.5e | 3.5 |
| DocumentIR regression test | Milestone B1.5f | 3.6 |
| DoxBaseModel extra="forbid" enforcement | Milestone B1.5 completion | 3.7 |
| Curated fixture validation tool | Milestone B2 / Task B2.2 | 4.1 |
| Fixture regeneration tool | Milestone B2 / Task B2.3 | 4.2 |
| Legacy field audit test | Milestone B2 / B2.5 | 4.3 |
| Full validation tool (report-only) | Milestone C / Task C.1 | 5.1 |
| Empty baseline tests | Milestone C / Task C.2 | 5.2 |
| Schema conformance tests | Milestone C / Task C.3 | 5.3 |
| CI workflow for schema validation | Milestone D / Task D.1 | 6.1 |
| Schema version tests | Milestone D / Task D.2 | 6.2 |
| CI guard for extra="forbid" on main | Branching Policy / CI Guard | 6.3 |
| Plugin policy tests (deferred 0.3) | Phase 0.3 (deferred to B) | 2.3 |
| Embedding invariant tests (deferred 0.4) | Phase 0.4 (deferred to B) | 2.4 |

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
$ uv run pytest -q
[[PH:OUTPUT]]
```

---

## Phase 0 — Baseline Reality

**Tests**: `uv run pytest -q` / `uv run pytest`

### Task 0.1 — Instantiate + capture baseline

**Objective**: Create PROJECT_TASKS.md and capture baseline evidence.

**Paths**:
```bash
TASK_0_1_PATHS=(
  "files (9)/work_folder/PYDANTIC_SCHEMA_tasks_template.md"
)
```

**Steps**:
1. Copy template to work_folder
2. Replace YAML placeholders with real values
3. Run pre-flight (must be zero)
4. Run baseline commands, paste outputs
5. If failures: log in Drift Ledger, stop

**Verification**:
```bash
$ if rg '\[\[PH:[A-Z0-9_]+\]\]' "files (9)/work_folder/PYDANTIC_SCHEMA_tasks_template.md"; then
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

### Task 0.2 — Create phase unlock artifact

**Objective**: Generate `.phase-0.complete.json` with real values.

**Paths**:
```bash
TASK_0_2_PATHS=(
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
  "test_command": "uv run pytest",
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

### Task 0.3 — Run shape discovery tool

**Objective**: Execute `tools/discover_parser_shape.py` to verify parser output shape assumptions.

**Paths**:
```bash
TASK_0_3_PATHS=(
  "tools/discover_parser_shape.py"
  "tools/discovery_output/all_keys.txt"
  "tools/discovery_output/sample_outputs.json"
)
```

**Steps**:
1. Create `tools/discover_parser_shape.py` per PYDANTIC_SCHEMA.md Phase 0.1
2. Run the script to generate discovery outputs
3. Spot-check `all_keys.txt` for expected top-level keys (metadata, content, structure, mappings)

**Verification**:
```bash
$ uv run python tools/discover_parser_shape.py
$ rg '^metadata\.' tools/discovery_output/all_keys.txt
$ rg '^content\.' tools/discovery_output/all_keys.txt
$ rg '^structure\.' tools/discovery_output/all_keys.txt
$ rg '^mappings\.' tools/discovery_output/all_keys.txt
```

- [ ] Discovery script runs without error
- [ ] `all_keys.txt` contains metadata, content, structure, mappings paths
- [ ] No unexpected top-level keys

**Status**: 📋 PLANNED

---

### Task 0.4 — Verify security fields in samples

**Objective**: Confirm required security field paths exist in sample outputs per Phase 0.1.1.

**Paths**:
```bash
TASK_0_4_PATHS=(
  "tools/discovery_output/sample_outputs.json"
)
```

**Steps**:
1. Run security field verification script against sample outputs
2. Verify <20% missing rate on required security paths
3. If >20% missing, investigate before proceeding to Phase 1

**Verification**:
```bash
$ uv run python -c "
import json
from pathlib import Path

samples = json.loads(Path('tools/discovery_output/sample_outputs.json').read_text())

REQUIRED_SECURITY_PATHS = [
    'metadata.security.statistics.has_script',
    'metadata.security.statistics.has_event_handlers',
    'metadata.security.statistics.has_data_uri_images',
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
for path in REQUIRED_SECURITY_PATHS:
    found = sum(1 for s in samples if check_path(s['output'], path))
    pct = (found / total) * 100 if total else 0
    status = 'OK' if pct >= 80 else 'WARN'
    print(f'{status}: {path} found in {found}/{total} ({pct:.0f}%)')
"
```

- [ ] All required security paths have >=80% presence
- [ ] No critical gaps identified (or documented in Drift Ledger)

**Status**: 📋 PLANNED

---

## Phase 1 — Milestone A (RAG Safety Contract)

**Goal**: Lock in RAG-critical security semantics as executable tests.
**Tests**: `uv run pytest tests/test_output_models_minimal.py -v`

### Task 1.1 — Add Pydantic dependency

> **Naming rule**: Task ID `N.M` → Path array `TASK_N_M_PATHS` (dots become underscores)

**Objective**: Add Pydantic v2 to project dependencies.

**Paths**:
```bash
TASK_1_1_PATHS=(
  "pyproject.toml"
)
```

**Scope**:
- In: Add `pydantic>=2,<3` to dependencies
- Out: No code changes yet

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "pydantic" pyproject.toml
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from pydantic import BaseModel; print('pydantic available')"
# Expected: ModuleNotFoundError (pydantic not yet installed)
```

### TDD Step 2 — Implement (minimal)

```bash
$ uv add "pydantic>=2,<3"
$ uv sync
```

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from pydantic import BaseModel; print('pydantic available')"
$ uv run pytest -q
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

**Objective**: Create `output_models.py` with `DoxBaseModel`, `ParserOutput`, and `empty()` factory.

**Paths**:
```bash
TASK_1_2_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: `DoxBaseModel` with `extra="allow"`, `ParserOutput` with 4 top-level keys, `schema_version`, `empty()` method
- Out: Nested models (Milestone B)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class ParserOutput" src/doxstrux/
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import ParserOutput; print(ParserOutput.empty())"
# Expected: ImportError (module does not exist)
```

### TDD Step 2 — Implement (minimal)

Create `src/doxstrux/markdown/output_models.py` per PYDANTIC_SCHEMA.md Task A.2:
- `DoxBaseModel` with `ConfigDict(extra="allow")`
- `ParserOutput` with `metadata`, `content`, `structure`, `mappings` as `dict[str, Any]`
- `schema_version: str = "parser-output@1.0.0"`
- `empty()` classmethod returning minimal valid structure

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import ParserOutput; p = ParserOutput.empty(); print(p.schema_version)"
$ uv run pytest -q
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

### Task 1.3 — Create minimal test with RAG safety

**Objective**: Create `test_output_models_minimal.py` with top-level validation AND RAG safety tests.

**Paths**:
```bash
TASK_1_3_PATHS=(
  "tests/test_output_models_minimal.py"
)
```

**Scope**:
- In: `TestMinimalSchemaValidation` (4 tests), `TestEarlyRAGSafety` (3 tests)
- Out: Full conformance tests (Milestone C)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class TestMinimalSchemaValidation" tests/
$ rg "class TestEarlyRAGSafety" tests/
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_minimal.py -v
# Expected: File not found or tests fail
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_output_models_minimal.py` per PYDANTIC_SCHEMA.md Task A.3:
- `test_empty_constructs` — `ParserOutput.empty()` works
- `test_empty_has_four_top_level_keys` — metadata, content, structure, mappings present
- `test_real_parser_output_validates` — Real parser output passes validation
- `test_discover_extra_fields` — Log any extra fields (informational)
- `test_script_tag_detected_early` — `<script>` triggers `has_script=True`, `has_dangerous_content=True`
- `test_clean_document_not_blocked` — Clean markdown not blocked for embedding
- `test_javascript_link_detected_and_disallowed` — `javascript:` links flagged

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest -q
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

## Phase 2 — Milestone B1 (Metadata + Security Models)

**Goal**: Add typed Metadata and Security models with `extra="forbid"` on those models.
**Tests**: `uv run pytest tests/test_output_models_minimal.py -v`

### Task 2.1 — Add Metadata and Security models

**Objective**: Expand `output_models.py` with typed `Metadata`, `Security`, `SecurityStatistics`, `SecuritySummary`, `SecurityWarning`, `Encoding` models.

**Paths**:
```bash
TASK_2_1_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Nested models for Metadata and Security with `extra="forbid"`
- Out: Structure and Mappings models (B1.5)

**Preconditions** (evidence required):
```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ rg "class Metadata" src/doxstrux/markdown/output_models.py
$ rg "class Security" src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Metadata, Security; print('typed models available')"
# Expected: ImportError (classes do not exist yet)
```

### TDD Step 2 — Implement (minimal)

Add to `output_models.py`:
- `Metadata(DoxBaseModel)` with `model_config = ConfigDict(extra="forbid")`
- `Security`, `SecurityStatistics`, `SecuritySummary`, `SecurityWarning` models
- `Encoding` model (optional field in Metadata)
- Update `ParserOutput.metadata` type from `dict[str, Any]` to `Metadata`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Metadata, Security; print('typed models available')"
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest -q
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

**Objective**: Create `tools/export_schema.py` to generate JSON Schema from Pydantic models.

**Paths**:
```bash
TASK_2_2_PATHS=(
  "tools/export_schema.py"
  "schemas/parser_output.schema.json"
)
```

**Scope**:
- In: Export tool with `sort_keys=True` for deterministic output
- Out: Full schema (deferred until B1.5)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "def main" tools/export_schema.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python tools/export_schema.py
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tools/export_schema.py` per PYDANTIC_SCHEMA.md Task B.1:
- Import `ParserOutput` from `output_models`
- Call `model_json_schema()`
- Add `$id`, `title`, `description` metadata
- Write to `schemas/parser_output.schema.json` with `sort_keys=True`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/export_schema.py
$ rg "ParserOutput" schemas/parser_output.schema.json
$ uv run pytest -q
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

### Task 2.3 — Plugin policy tests (deferred Phase 0.3)

**Objective**: Verify parser uses `config.py:ALLOWED_PLUGINS` consistently.

**Paths**:
```bash
TASK_2_3_PATHS=(
  "tests/test_plugin_policy_consistency.py"
)
```

**Scope**:
- In: 3 tests per PYDANTIC_SCHEMA.md Phase 0.3
- Out: Plugin SSOT changes (use existing config.py)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "ALLOWED_PLUGINS" src/doxstrux/markdown/config.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_plugin_policy_consistency.py -v
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_plugin_policy_consistency.py`:
- `test_permissive_profile_has_all_plugins` — Required plugins in permissive
- `test_math_always_present_in_output` — Math structure always present
- `test_footnotes_always_present_in_output` — Footnotes present under permissive

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_plugin_policy_consistency.py -v
$ uv run pytest -q
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

### Task 2.4 — Embedding invariant tests (deferred Phase 0.4)

**Objective**: Test embedding_blocked field consistency invariants.

**Paths**:
```bash
TASK_2_4_PATHS=(
  "tests/test_embedding_invariants.py"
)
```

**Scope**:
- In: 2 tests per PYDANTIC_SCHEMA.md Phase 0.4
- Out: Parser behavior changes

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "embedding_blocked" src/doxstrux/markdown_parser_core.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_embedding_invariants.py -v
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_embedding_invariants.py`:
- `test_embedding_blocked_consistency` — security.embedding_blocked implies metadata.embedding_blocked
- `test_clean_document_not_blocked` — Clean doc not blocked

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_embedding_invariants.py -v
$ uv run pytest -q
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

## Phase 3 — Milestone B1.5 (Structure + Mappings Models)

**Goal**: Add remaining nested models for Structure and Mappings in incremental domain slices.
**Tests**: `uv run pytest tests/test_output_models_minimal.py -v`

### Task 3.1 — Content + Mappings models (B1.5a)

**Objective**: Add `Content`, `Mappings`, `MappingCodeBlock` models.

**Paths**:
```bash
TASK_3_1_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: `Content(raw, lines)`, `Mappings(line_to_type, line_to_section, prose_lines, code_lines, code_blocks)`, `MappingCodeBlock`
- Out: Structure models

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class Content" src/doxstrux/markdown/output_models.py
$ rg "class Mappings" src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Content, Mappings; print('models available')"
# Expected: ImportError
```

### TDD Step 2 — Implement (minimal)

Add to `output_models.py`:
- `Content(DoxBaseModel)` with `raw: str`, `lines: list[str]`
- `MappingCodeBlock(DoxBaseModel)` with `start_line`, `end_line`, `language`
- `Mappings(DoxBaseModel)` with typed fields
- Update `ParserOutput.content` and `ParserOutput.mappings` types

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Content, Mappings; print('models available')"
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest -q
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

### Task 3.2 — Sections + Headings + Paragraphs models (B1.5b)

**Objective**: Add `Section`, `Heading`, `Paragraph` models.

**Paths**:
```bash
TASK_3_2_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: `Section`, `Heading`, `Paragraph` with appropriate fields
- Out: Lists models

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class Section" src/doxstrux/markdown/output_models.py
$ rg "class Heading" src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Section, Heading, Paragraph; print('models available')"
# Expected: ImportError
```

### TDD Step 2 — Implement (minimal)

Add `Section`, `Heading`, `Paragraph` models to `output_models.py`.

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Section, Heading, Paragraph; print('models available')"
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest -q
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

### Task 3.3 — Lists + Tasklists models (B1.5c)

**Objective**: Add `List`, `ListItem`, `Tasklist`, `TasklistItem`, `BlockRef` models with recursive children.

**Paths**:
```bash
TASK_3_3_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: List-related models with `model_rebuild()` for recursive types
- Out: Tables models

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class List" src/doxstrux/markdown/output_models.py
$ rg "class Tasklist" src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import List, Tasklist; print('models available')"
# Expected: ImportError
```

### TDD Step 2 — Implement (minimal)

Add list models with recursive children support using `model_rebuild()`.

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import List, Tasklist; print('models available')"
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest -q
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

### Task 3.4 — Tables + Code Blocks + Blockquotes models (B1.5d)

**Objective**: Add `Table`, `CodeBlock`, `Blockquote`, `BlockquoteChildrenSummary` models.

**Paths**:
```bash
TASK_3_4_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Table, code block, blockquote models
- Out: Links/Media models

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class Table" src/doxstrux/markdown/output_models.py
$ rg "class CodeBlock" src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Table, CodeBlock, Blockquote; print('models available')"
# Expected: ImportError
```

### TDD Step 2 — Implement (minimal)

Add `Table`, `CodeBlock`, `Blockquote`, `BlockquoteChildrenSummary` models.

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Table, CodeBlock, Blockquote; print('models available')"
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest -q
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

### Task 3.5 — Links + Images + Math + Footnotes + HTML models (B1.5e)

**Objective**: Add `Link` (discriminated union), `Image`, `Math`, `MathBlock`, `MathInline`, `Footnotes`, `FootnoteDefinition`, `FootnoteReference`, `HtmlBlock`, `HtmlInline` models.

**Paths**:
```bash
TASK_3_5_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: All remaining Structure models including discriminated union for Link
- Out: Structure model complete

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class Link" src/doxstrux/markdown/output_models.py
$ rg "class Math" src/doxstrux/markdown/output_models.py
$ rg "class Footnotes" src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Link, Image, Math, Footnotes; print('models available')"
# Expected: ImportError
```

### TDD Step 2 — Implement (minimal)

Add all remaining models:
- `Link` as discriminated union (`RegularLink | ImageLink`)
- `Image`, `Math`, `MathBlock`, `MathInline`
- `Footnotes`, `FootnoteDefinition`, `FootnoteReference`
- `HtmlBlock`, `HtmlInline`
- Update `Structure` model with typed fields

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Link, Image, Math, Footnotes; print('models available')"
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest -q
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

### Task 3.6 — DocumentIR regression test (B1.5f)

**Objective**: Ensure ParserOutput schema changes don't break DocumentIR construction.

**Paths**:
```bash
TASK_3_6_PATHS=(
  "tests/test_document_ir_regression.py"
)
```

**Scope**:
- In: 5 fixture parametrized tests + 1 semantic assertion test
- Out: DocumentIR changes

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class DocumentIR" src/doxstrux/markdown/ir.py
$ rg "from_parser_output" src/doxstrux/markdown/ir.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_document_ir_regression.py -v
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_document_ir_regression.py` per PYDANTIC_SCHEMA.md B1.5f:
- `test_ir_builds_without_error` — Parametrized with 5 fixtures
- `test_heading_document_has_structure` — Non-empty IR for heading doc

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_document_ir_regression.py -v
$ uv run pytest -q
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

### Task 3.7 — Switch DoxBaseModel to extra="forbid"

**Objective**: Enforce strict schema by switching `DoxBaseModel.extra` from `"allow"` to `"forbid"`.

**Paths**:
```bash
TASK_3_7_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Change `DoxBaseModel.model_config = ConfigDict(extra="forbid")`
- Out: Milestone B1.5 complete

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg 'extra.*=.*"allow"' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "
from doxstrux.markdown.output_models import DoxBaseModel
assert DoxBaseModel.model_config.get('extra') == 'forbid', 'Still allow'
"
# Expected: AssertionError (still "allow")
```

### TDD Step 2 — Implement (minimal)

Change `DoxBaseModel.model_config = ConfigDict(extra="forbid")`.

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "
from doxstrux.markdown.output_models import DoxBaseModel
assert DoxBaseModel.model_config.get('extra') == 'forbid', 'Still allow'
print('extra=forbid confirmed')
"
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest -q
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

## Phase 4 — Milestone B2 (Validation Tools)

**Goal**: Build curated fixture validation and regeneration tools.
**Tests**: `uv run pytest -q`

### Task 4.1 — Create curated fixture validation tool

**Objective**: Create `tools/validate_curated_fixtures.py` with pattern-based discovery.

**Paths**:
```bash
TASK_4_1_PATHS=(
  "tools/validate_curated_fixtures.py"
)
```

**Scope**:
- In: Glob pattern discovery, validation via `ParserOutput.model_validate()`, max 50 fixtures
- Out: Full validation (Milestone C)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "def validate_fixture" tools/validate_curated_fixtures.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python tools/validate_curated_fixtures.py
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tools/validate_curated_fixtures.py` per PYDANTIC_SCHEMA.md Task B2.2:
- `CURATED_PATTERNS` for glob-based discovery
- `discover_curated_fixtures()` function
- `validate_fixture()` function using `ParserOutput.model_validate()`
- Exit code 1 on any failure

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/validate_curated_fixtures.py
$ uv run pytest -q
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
- In: Bucket classification (structural/security/legacy), `--review` flag, `--dry-run` support
- Out: Mass regeneration

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "def classify_fixture" tools/regenerate_fixtures.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python tools/regenerate_fixtures.py --help
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tools/regenerate_fixtures.py` per PYDANTIC_SCHEMA.md Task B2.3:
- `classify_fixture()` with path-based bucketing
- `needs_manual_review()` for content-based safety check
- `regenerate_fixture()` with validation before write
- CLI with `--bucket`, `--review`, `--dry-run`, `--curated` flags

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/regenerate_fixtures.py --help
$ uv run python tools/regenerate_fixtures.py --dry-run --curated
$ uv run pytest -q
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

### Task 4.3 — Legacy field audit test

**Objective**: Create `tests/test_no_legacy_field_runtime_usage.py` to enforce legacy field audit via code.

**Paths**:
```bash
TASK_4_3_PATHS=(
  "tests/test_no_legacy_field_runtime_usage.py"
)
```

**Scope**:
- In: Parametrized test using `rg` to find legacy field usage in `src/doxstrux/`
- Out: Actual field removal (requires audit pass first)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "LEGACY_FIELDS_TO_AUDIT" tests/test_no_legacy_field_runtime_usage.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_no_legacy_field_runtime_usage.py -v
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_no_legacy_field_runtime_usage.py` per PYDANTIC_SCHEMA.md B2.5:
- `LEGACY_FIELDS_TO_AUDIT` list (starting with `exception_was_raised`)
- Parametrized test using `subprocess.run(["rg", "-l", field_name, "src/doxstrux/"])`
- Fail if matches found in runtime code

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_no_legacy_field_runtime_usage.py -v
$ uv run pytest -q
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

## Phase 5 — Milestone C (Full Validation)

**Goal**: Validate ALL fixtures (620+) in report-only mode.
**Tests**: `uv run pytest -q`

### Task 5.1 — Create full validation tool with report-only mode

**Objective**: Create `tools/validate_test_pairs.py` with `--report` and `--threshold` options.

**Paths**:
```bash
TASK_5_1_PATHS=(
  "tools/validate_test_pairs.py"
)
```

**Scope**:
- In: Full directory validation, `--report` mode (exit 0), `--threshold` for gradual rollout, `--output` for JSON report
- Out: CI blocking (Milestone D)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "def validate_directory" tools/validate_test_pairs.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python tools/validate_test_pairs.py --help
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tools/validate_test_pairs.py` per PYDANTIC_SCHEMA.md Task C.1:
- `validate_directory()` function
- `--report` mode (always exit 0)
- `--threshold` option (default 100%)
- `--output` for JSON failure report

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/validate_test_pairs.py --report
$ uv run pytest -q
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

### Task 5.2 — Create empty baseline tests

**Objective**: Create `tests/test_output_models_empty.py` testing `ParserOutput.empty()` thoroughly.

**Paths**:
```bash
TASK_5_2_PATHS=(
  "tests/test_output_models_empty.py"
)
```

**Scope**:
- In: 10 tests covering empty baseline shape and security defaults
- Out: N/A

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class TestEmptyBaseline" tests/test_output_models_empty.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_empty.py -v
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_output_models_empty.py` per PYDANTIC_SCHEMA.md Task C.2:
- `test_empty_returns_parser_output_instance`
- `test_empty_has_all_top_level_keys`
- `test_empty_content_is_empty`
- `test_empty_metadata_has_zero_counts`
- `test_empty_has_no_security_warnings`
- `test_empty_has_no_dangerous_flags`
- `test_empty_embedding_not_blocked`
- `test_empty_not_quarantined`
- `test_empty_structure_is_empty`
- `test_empty_mappings_is_empty`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_empty.py -v
$ uv run pytest -q
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

### Task 5.3 — Create schema conformance tests

**Objective**: Create `tests/test_parser_output_schema_conformance.py` with CONTRACT tests for parser output.

**Paths**:
```bash
TASK_5_3_PATHS=(
  "tests/test_parser_output_schema_conformance.py"
)
```

**Scope**:
- In: 5 test classes per PYDANTIC_SCHEMA.md Task C.3
- Out: N/A

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class TestParserOutputSchemaConformance" tests/test_parser_output_schema_conformance.py
$ rg "class TestSecuritySemantics" tests/test_parser_output_schema_conformance.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_parser_output_schema_conformance.py -v
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_parser_output_schema_conformance.py`:
- `TestParserOutputSchemaConformance` — validates against sample files
- `TestSecuritySemantics` — script, clean doc, event handler, data URI tests
- `TestLinkDiscriminatedUnion` — regular vs image links
- `TestMathExtraction` — inline and block math
- `TestFootnoteExtraction` — footnote definitions and references (permissive only)

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_parser_output_schema_conformance.py -v
$ uv run pytest -q
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

## Phase 6 — Milestone D (CI Gate)

**Goal**: Make schema validation a blocking CI gate.
**Tests**: `uv run pytest -q`

### Task 6.1 — Create CI workflow for schema validation

**Objective**: Create `.github/workflows/schema_validation.yml` with blocking validation.

**Paths**:
```bash
TASK_6_1_PATHS=(
  ".github/workflows/schema_validation.yml"
)
```

**Scope**:
- In: Schema version check, fixture validation with 100% threshold, schema drift detection
- Out: Pre-commit hooks (optional)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "schema-validation" .github/workflows/schema_validation.yml
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f .github/workflows/schema_validation.yml && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Create `.github/workflows/schema_validation.yml` per PYDANTIC_SCHEMA.md Task D.1:
- Check schema version matches expected
- Run `validate_test_pairs.py --threshold 100`
- Export schema and verify no git diff

### TDD Step 3 — Verify (GREEN)

```bash
$ test -f .github/workflows/schema_validation.yml && echo "exists"
$ rg "threshold 100" .github/workflows/schema_validation.yml
$ uv run pytest -q
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

### Task 6.2 — Create schema version tests

**Objective**: Create `tests/test_schema_version.py` to enforce schema version maintenance.

**Paths**:
```bash
TASK_6_2_PATHS=(
  "tests/test_schema_version.py"
)
```

**Scope**:
- In: 4 tests per PYDANTIC_SCHEMA.md Task D.2
- Out: N/A

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class TestSchemaVersion" tests/test_schema_version.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_schema_version.py -v
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_schema_version.py`:
- `test_schema_version_exists`
- `test_schema_version_format` — `parser-output@X.Y.Z` pattern
- `test_schema_version_not_dev` — no -dev/-alpha/-beta
- `test_empty_has_same_version`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_schema_version.py -v
$ uv run pytest -q
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

### Task 6.3 — Create CI guard for extra="forbid" on main

**Objective**: Create `tests/test_schema_extra_forbid.py` to prevent accidental merge of `extra="allow"` to main.

**Paths**:
```bash
TASK_6_3_PATHS=(
  "tests/test_schema_extra_forbid.py"
)
```

**Scope**:
- In: CI guard test per PYDANTIC_SCHEMA.md Branching Policy
- Out: N/A

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "test_doxbasemodel_extra_is_forbid" tests/test_schema_extra_forbid.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_schema_extra_forbid.py -v
# Expected: File not found
```

### TDD Step 2 — Implement (minimal)

Create `tests/test_schema_extra_forbid.py` per PYDANTIC_SCHEMA.md CI Guard:
- `get_current_branch()` helper
- `test_doxbasemodel_extra_is_forbid` with skipif for non-main branches

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_schema_extra_forbid.py -v
$ uv run pytest -q
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

Generate with real values (no placeholders):
```bash
$ cat > .phase-N.complete.json << EOF
{
  "phase": N,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "test_command": "uv run pytest",
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

Run before each phase gate:

```bash
# Standard patterns (gates must fail on matches):
$ if rg 'TODO|FIXME|XXX' src/doxstrux/; then
>   echo "ERROR: Unfinished markers found"
>   exit 1
> fi

$ if rg '\[\[PH:' .; then
>   echo "ERROR: Placeholders found"
>   exit 1
> fi

# Python import hygiene (REQUIRED when runner=uv):
$ if rg 'from \.\.' src/doxstrux/; then
>   echo "ERROR: Multi-dot relative import found"
>   exit 1
> fi

$ if rg 'import \*' src/doxstrux/; then
>   echo "ERROR: Wildcard import found"
>   exit 1
> fi

# uv sync and run verification:
$ uv sync
$ uv run pytest -q
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
