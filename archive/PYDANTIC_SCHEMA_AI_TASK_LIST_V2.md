---
ai_task_list:
  schema_version: "1.6"
  mode: "instantiated"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# Pydantic Schema Implementation — Task List

**Version**: 2.0 (v1.6 spec compliant)
**Scope**: Implement Pydantic schema validation for MarkdownParserCore output
**Source**: PYDANTIC_SCHEMA.md (design document)

---

## Non-negotiable Invariants

1. **Clean Table is a delivery gate** — Do not mark complete unless verified and stable.
2. **No silent errors** — Errors raise unconditionally.
3. **No weak tests** — Tests assert semantics, not existence/import/smoke.
4. **Single runner principle** — One canonical runner (`uv run`) everywhere.
5. **Evidence anchors required** — Claims require command output or file evidence.
6. **No synthetic reality** — Do not invent outputs, results, or versions.
7. **Import hygiene** — Absolute imports preferred; no multi-dot relative (`from ..`); no wildcards (`import *`).

---

## Placeholder Protocol

**Format**: `[[PH:NAME]]` where NAME is `[A-Z0-9_]+`

**Pre-flight** (must return zero — fails if placeholders found):
```bash
$ rg '\[\[PH:[A-Z0-9_]+\]\]' PYDANTIC_SCHEMA_AI_TASK_LIST_V2.md && { echo "ERROR: Placeholders found"; exit 1; } || exit 0
```

---

## Source of Truth Hierarchy

1. Executed tests + tool output (highest)
2. Repository state (commit hash)
3. Runtime code (`src/doxstrux/markdown/output_models.py`)
4. This task list
5. Design docs (`PYDANTIC_SCHEMA.md` — historical once execution begins)

**Drift rule**: Higher wins. Update lower source and log in Drift Ledger.

---

## Baseline Snapshot (capture before any work)

| Field | Value |
|-------|-------|
| Date | 2024-XX-XX |
| Repo | doxstrux |
| Branch | feature/pydantic-schema |
| Commit | (capture at start) |
| Runner | uv 0.X.X |
| Runtime | Python 3.12.X |

**Evidence** (paste outputs):
```bash
$ git rev-parse --abbrev-ref HEAD
# OUTPUT HERE

$ git rev-parse HEAD
# OUTPUT HERE

$ uv --version
# OUTPUT HERE

$ uv run python --version
# OUTPUT HERE
```

**Baseline tests**:
```bash
$ uv run pytest -q tests/
# OUTPUT HERE
```

---

## Phase 0 — Discovery (Baseline Reality)

**Goal**: Verify parser output shape assumptions before implementing schema.
**Tests**: `uv run pytest -q` / `uv run pytest tests/`

### Task 0.1 — Instantiate task list + capture baseline

> **Naming rule**: Task ID `N.M` → Path array `TASK_N_M_PATHS` (dots become underscores)

**Objective**: Create this task list and capture baseline evidence.

**Paths**:
```bash
TASK_0_1_PATHS=(
  "PYDANTIC_SCHEMA_AI_TASK_LIST_V2.md"
)
```

**Scope**:
- In: Task list creation, baseline capture, pre-flight verification
- Out: Any code implementation

**Preconditions** (evidence required):
```bash
$ rg 'schema_version.*1\.6' PYDANTIC_SCHEMA_AI_TASK_LIST_V2.md
$ rg 'mode.*instantiated' PYDANTIC_SCHEMA_AI_TASK_LIST_V2.md
```

### TDD Step 1 — Write test (RED)

```bash
$ rg '\[\[PH:' PYDANTIC_SCHEMA_AI_TASK_LIST_V2.md
# Expected: FAIL (placeholders found in template sections)
```

### TDD Step 2 — Implement (minimal)

1. Copy template structure
2. Replace all placeholders with real values
3. Capture baseline outputs

### TDD Step 3 — Verify (GREEN)

```bash
$ rg '\[\[PH:' PYDANTIC_SCHEMA_AI_TASK_LIST_V2.md && exit 1 || echo "No placeholders"
$ uv run pytest -q tests/
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: rg '\[\[PH:' PYDANTIC_SCHEMA_AI_TASK_LIST_V2.md && exit 1 || echo "No placeholders"
# exit: 0
(paste output)

# cmd: uv run pytest -q tests/
# exit: 0
(paste output)
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

### Task 0.2 — Create shape discovery tool

**Objective**: Build tool to discover actual parser output structure from samples.

**Paths**:
```bash
TASK_0_2_PATHS=(
  "tools/discover_parser_shape.py"
  "tools/discovery_output/all_keys.txt"
  "tools/discovery_output/sample_outputs.json"
)
```

**Scope**:
- In: Shape discovery tool, key path extraction, sample output collection
- Out: Schema implementation, Pydantic models

**Preconditions** (evidence required):
```bash
$ rg 'MarkdownParserCore' src/doxstrux/markdown_parser_core.py
$ rg 'def parse' src/doxstrux/markdown_parser_core.py
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f tools/discover_parser_shape.py && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Create `tools/discover_parser_shape.py` with:
- `collect_all_keys()` function
- Sample collection from `tools/test_mds/`
- Output to `tools/discovery_output/`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/discover_parser_shape.py
$ test -f tools/discovery_output/all_keys.txt && echo "keys exist"
$ test -f tools/discovery_output/sample_outputs.json && echo "samples exist"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python tools/discover_parser_shape.py
# exit: 0
(paste output)

# cmd: test -f tools/discovery_output/all_keys.txt
# exit: 0
(paste output)
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

### Task 0.3 — Verify security field paths

**Objective**: Confirm RAG-critical security paths exist in parser output samples.

**Paths**:
```bash
TASK_0_3_PATHS=(
  "tools/verify_security_paths.py"
)
```

**Scope**:
- In: Security path verification against discovery output
- Out: Schema implementation

**Preconditions** (evidence required):
```bash
$ rg 'metadata.security' tools/discovery_output/all_keys.txt
$ rg 'statistics' tools/discovery_output/all_keys.txt
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python tools/verify_security_paths.py
# Expected: Script to verify required paths exist in 80%+ of samples
```

### TDD Step 2 — Implement (minimal)

Create verification script checking:
- `metadata.security.statistics.has_script`
- `metadata.security.statistics.has_event_handlers`
- `metadata.security.summary.has_dangerous_content`
- `metadata.security.warnings`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/verify_security_paths.py
# Expected: All required paths present in >=80% of samples
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python tools/verify_security_paths.py
# exit: 0
(paste output showing >=80% presence)
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

### Task 0.4 — Create phase unlock artifact

**Objective**: Generate `.phase-0.complete.json` to gate Phase 1.

**Paths**:
```bash
TASK_0_4_PATHS=(
  ".phase-0.complete.json"
)
```

**Scope**:
- In: Phase 0 completion artifact
- Out: Phase 1 work

**Preconditions** (evidence required):
```bash
$ rg 'all_keys.txt' tools/discovery_output/
$ rg 'sample_outputs.json' tools/discovery_output/
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f .phase-0.complete.json && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Generate artifact with real values.

### TDD Step 3 — Verify (GREEN)

```bash
$ cat .phase-0.complete.json
$ rg '\[\[PH:' .phase-0.complete.json && exit 1 || echo "No placeholders"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: cat .phase-0.complete.json
# exit: 0
(paste output)

# cmd: rg '\[\[PH:' .phase-0.complete.json && exit 1 || echo "No placeholders"
# exit: 0
No placeholders
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

## Phase 1 — RAG Safety Contract (Milestone A)

**Goal**: Lock in RAG-critical security semantics as executable tests.
**Tests**: `uv run pytest tests/test_output_models_minimal.py -v`

### Task 1.1 — Add Pydantic dependency

**Objective**: Add pydantic>=2,<3 to project dependencies.

**Paths**:
```bash
TASK_1_1_PATHS=(
  "pyproject.toml"
)
```

**Scope**:
- In: Dependency addition
- Out: Model implementation

**Preconditions** (evidence required):
```bash
$ rg 'pydantic' pyproject.toml || echo "not found"
$ test -f .phase-0.complete.json && echo "Phase 0 complete"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "import pydantic; print(pydantic.__version__)"
# Expected: FAIL (ModuleNotFoundError)
```

### TDD Step 2 — Implement (minimal)

```bash
$ uv add "pydantic>=2,<3"
```

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "import pydantic; print(pydantic.__version__)"
$ rg 'pydantic' pyproject.toml
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python -c "import pydantic; print(pydantic.__version__)"
# exit: 0
(paste version)

# cmd: rg 'pydantic' pyproject.toml
# exit: 0
(paste match)
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

**Objective**: Create ParserOutput with 4 top-level keys and extra="allow" for discovery.

**Paths**:
```bash
TASK_1_2_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: DoxBaseModel, ParserOutput, ParserOutput.empty()
- Out: Nested models (Milestone B)

**Preconditions** (evidence required):
```bash
$ rg 'class.*BaseModel' src/doxstrux/markdown/ || echo "no models yet"
$ rg 'pydantic' pyproject.toml
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import ParserOutput"
# Expected: FAIL (ImportError)
```

### TDD Step 2 — Implement (minimal)

Create `output_models.py` with:
- `DoxBaseModel(BaseModel)` with `extra="allow"`
- `ParserOutput(DoxBaseModel)` with `metadata`, `content`, `structure`, `mappings`
- `ParserOutput.empty()` classmethod

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import ParserOutput; p = ParserOutput.empty(); print(p.schema_version)"
$ uv run pytest tests/test_output_models_minimal.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python -c "from doxstrux.markdown.output_models import ParserOutput; p = ParserOutput.empty(); print(p.schema_version)"
# exit: 0
parser-output@1.0.0

# cmd: uv run pytest tests/test_output_models_minimal.py -v
# exit: 0
(paste output)
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

### Task 1.3 — Create RAG safety tests

**Objective**: Implement tests for script detection, clean doc safety, javascript link detection.

**Paths**:
```bash
TASK_1_3_PATHS=(
  "tests/test_output_models_minimal.py"
)
```

**Scope**:
- In: TestMinimalSchemaValidation, TestEarlyRAGSafety test classes
- Out: Full schema validation (Milestone C)

**Preconditions** (evidence required):
```bash
$ rg 'class ParserOutput' src/doxstrux/markdown/output_models.py
$ rg 'def empty' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_minimal.py::TestEarlyRAGSafety -v
# Expected: Tests exist and run
```

### TDD Step 2 — Implement (minimal)

Create test file with:
- `TestMinimalSchemaValidation`: empty_constructs, four_top_level_keys, real_parser_validates
- `TestEarlyRAGSafety`: script_tag_detected, clean_document_not_blocked, javascript_link_detected

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest tests/test_output_models_minimal.py::TestEarlyRAGSafety::test_script_tag_detected_early -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run pytest tests/test_output_models_minimal.py -v
# exit: 0
(paste output showing all tests pass)

# cmd: uv run pytest tests/test_output_models_minimal.py::TestEarlyRAGSafety -v
# exit: 0
(paste output)
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

### Task 1.4 — Create phase unlock artifact

**Objective**: Generate `.phase-1.complete.json` to gate Phase 2.

**Paths**:
```bash
TASK_1_4_PATHS=(
  ".phase-1.complete.json"
)
```

**Scope**:
- In: Phase 1 completion artifact
- Out: Phase 2 work

**Preconditions** (evidence required):
```bash
$ rg 'TestEarlyRAGSafety' tests/test_output_models_minimal.py
$ uv run pytest tests/test_output_models_minimal.py -q
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f .phase-1.complete.json && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Generate artifact with real values.

### TDD Step 3 — Verify (GREEN)

```bash
$ cat .phase-1.complete.json
$ rg '\[\[PH:' .phase-1.complete.json && exit 1 || echo "No placeholders"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: cat .phase-1.complete.json
# exit: 0
(paste output)

# cmd: rg '\[\[PH:' .phase-1.complete.json && exit 1 || echo "No placeholders"
# exit: 0
No placeholders
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

**Goal**: Add nested models for Metadata and Security with extra="forbid".
**Tests**: `uv run pytest tests/test_output_models_minimal.py tests/test_metadata_models.py -v`

### Task 2.1 — Add Metadata and Security models

**Objective**: Expand output_models.py with typed Metadata, Security, SecurityStatistics, SecuritySummary, SecurityWarning, Encoding.

**Paths**:
```bash
TASK_2_1_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Metadata, Security, SecurityStatistics, SecuritySummary, SecurityWarning, Encoding models
- Out: Structure/Mappings models (B1.5)

**Preconditions** (evidence required):
```bash
$ rg 'class ParserOutput' src/doxstrux/markdown/output_models.py
$ test -f .phase-1.complete.json && echo "Phase 1 complete"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Metadata, Security"
# Expected: FAIL (ImportError)
```

### TDD Step 2 — Implement (minimal)

Add models with `ConfigDict(extra="forbid")` on typed models:
- `Metadata`, `Security`, `SecurityStatistics`, `SecuritySummary`, `SecurityWarning`, `Encoding`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Metadata, Security, SecurityStatistics; print('imports work')"
$ uv run pytest tests/test_output_models_minimal.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python -c "from doxstrux.markdown.output_models import Metadata, Security"
# exit: 0
(paste output)

# cmd: uv run pytest tests/test_output_models_minimal.py -v
# exit: 0
(paste output)
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

**Objective**: Build tools/export_schema.py to generate JSON Schema from Pydantic models.

**Paths**:
```bash
TASK_2_2_PATHS=(
  "tools/export_schema.py"
  "schemas/parser_output.schema.json"
)
```

**Scope**:
- In: Schema export tool, deterministic JSON output
- Out: Full schema (B1.5)

**Preconditions** (evidence required):
```bash
$ rg 'model_json_schema' src/doxstrux/markdown/output_models.py || echo "method available via pydantic"
$ rg 'class Metadata' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f tools/export_schema.py && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Create export tool with:
- `ParserOutput.model_json_schema()` call
- `sort_keys=True` for deterministic output
- Round-trip verification

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/export_schema.py
$ test -f schemas/parser_output.schema.json && echo "schema exists"
$ rg '"title"' schemas/parser_output.schema.json
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python tools/export_schema.py
# exit: 0
(paste output)

# cmd: test -f schemas/parser_output.schema.json
# exit: 0
schema exists
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

### Task 2.3 — Create phase unlock artifact

**Objective**: Generate `.phase-2.complete.json` to gate Phase 3.

**Paths**:
```bash
TASK_2_3_PATHS=(
  ".phase-2.complete.json"
)
```

**Scope**:
- In: Phase 2 completion artifact
- Out: Phase 3 work

**Preconditions** (evidence required):
```bash
$ rg 'class Metadata' src/doxstrux/markdown/output_models.py
$ test -f schemas/parser_output.schema.json
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f .phase-2.complete.json && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Generate artifact with real values.

### TDD Step 3 — Verify (GREEN)

```bash
$ cat .phase-2.complete.json
$ rg '\[\[PH:' .phase-2.complete.json && exit 1 || echo "No placeholders"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: cat .phase-2.complete.json
# exit: 0
(paste output)

# cmd: rg '\[\[PH:' .phase-2.complete.json && exit 1 || echo "No placeholders"
# exit: 0
No placeholders
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

**Goal**: Add all remaining nested models and switch DoxBaseModel to extra="forbid".
**Tests**: `uv run pytest tests/ -v -k "output_models or schema"`

### Task 3.1 — Add Content and Mappings models (B1.5a)

**Objective**: Add Content, Mappings, MappingCodeBlock models.

**Paths**:
```bash
TASK_3_1_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Content, Mappings, MappingCodeBlock
- Out: Section/Heading/Paragraph models

**Preconditions** (evidence required):
```bash
$ rg 'class Metadata' src/doxstrux/markdown/output_models.py
$ test -f .phase-2.complete.json && echo "Phase 2 complete"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Content, Mappings"
# Expected: FAIL (ImportError)
```

### TDD Step 2 — Implement (minimal)

Add models: Content, Mappings, MappingCodeBlock

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Content, Mappings; print('imports work')"
$ uv run pytest tests/test_output_models_minimal.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python -c "from doxstrux.markdown.output_models import Content, Mappings"
# exit: 0
imports work

# cmd: uv run pytest tests/test_output_models_minimal.py -v
# exit: 0
(paste output)
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

### Task 3.2 — Add Section, Heading, Paragraph models (B1.5b)

**Objective**: Add Section, Heading, Paragraph models.

**Paths**:
```bash
TASK_3_2_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Section, Heading, Paragraph
- Out: List/Tasklist models

**Preconditions** (evidence required):
```bash
$ rg 'class Content' src/doxstrux/markdown/output_models.py
$ rg 'class Mappings' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Section, Heading, Paragraph"
# Expected: FAIL (ImportError)
```

### TDD Step 2 — Implement (minimal)

Add models: Section, Heading, Paragraph

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Section, Heading, Paragraph; print('imports work')"
$ uv run pytest tests/test_output_models_minimal.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python -c "from doxstrux.markdown.output_models import Section, Heading, Paragraph"
# exit: 0
imports work

# cmd: uv run pytest tests/test_output_models_minimal.py -v
# exit: 0
(paste output)
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

### Task 3.3 — Add List and Tasklist models (B1.5c)

**Objective**: Add List, ListItem, Tasklist, TasklistItem, BlockRef models with recursive children.

**Paths**:
```bash
TASK_3_3_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: List, ListItem, Tasklist, TasklistItem, BlockRef
- Out: Table/CodeBlock/Blockquote models

**Preconditions** (evidence required):
```bash
$ rg 'class Section' src/doxstrux/markdown/output_models.py
$ rg 'class Heading' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import List, ListItem, Tasklist"
# Expected: FAIL (ImportError)
```

### TDD Step 2 — Implement (minimal)

Add models with recursive children using `model_rebuild()`:
- List, ListItem, Tasklist, TasklistItem, BlockRef

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import List, ListItem, Tasklist; print('imports work')"
$ uv run pytest tests/test_output_models_minimal.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python -c "from doxstrux.markdown.output_models import List, ListItem, Tasklist"
# exit: 0
imports work

# cmd: uv run pytest tests/test_output_models_minimal.py -v
# exit: 0
(paste output)
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

### Task 3.4 — Add Table, CodeBlock, Blockquote models (B1.5d)

**Objective**: Add Table, CodeBlock, Blockquote, BlockquoteChildrenSummary models.

**Paths**:
```bash
TASK_3_4_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Table, CodeBlock, Blockquote, BlockquoteChildrenSummary
- Out: Link/Image/Math/Footnotes/HTML models

**Preconditions** (evidence required):
```bash
$ rg 'class List' src/doxstrux/markdown/output_models.py
$ rg 'class Tasklist' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Table, CodeBlock, Blockquote"
# Expected: FAIL (ImportError)
```

### TDD Step 2 — Implement (minimal)

Add models: Table, CodeBlock, Blockquote, BlockquoteChildrenSummary

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Table, CodeBlock, Blockquote; print('imports work')"
$ uv run pytest tests/test_output_models_minimal.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python -c "from doxstrux.markdown.output_models import Table, CodeBlock, Blockquote"
# exit: 0
imports work

# cmd: uv run pytest tests/test_output_models_minimal.py -v
# exit: 0
(paste output)
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

### Task 3.5 — Add Link, Image, Math, Footnotes, HTML models (B1.5e)

**Objective**: Add remaining models including discriminated union for Link.

**Paths**:
```bash
TASK_3_5_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Link (discriminated union), Image, Math, MathBlock, MathInline, Footnotes, FootnoteDefinition, FootnoteReference, HtmlBlock, HtmlInline
- Out: Validation tools (Phase 4)

**Preconditions** (evidence required):
```bash
$ rg 'class Table' src/doxstrux/markdown/output_models.py
$ rg 'class CodeBlock' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Link, Image, Math, Footnotes"
# Expected: FAIL (ImportError)
```

### TDD Step 2 — Implement (minimal)

Add models:
- Link (discriminated union: RegularLink | ImageLink)
- Image, Math, MathBlock, MathInline
- Footnotes, FootnoteDefinition, FootnoteReference
- HtmlBlock, HtmlInline

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python -c "from doxstrux.markdown.output_models import Link, Image, Math, Footnotes; print('imports work')"
$ uv run pytest tests/test_output_models_minimal.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python -c "from doxstrux.markdown.output_models import Link, Image, Math, Footnotes"
# exit: 0
imports work

# cmd: uv run pytest tests/test_output_models_minimal.py -v
# exit: 0
(paste output)
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

### Task 3.6 — Switch DoxBaseModel to extra="forbid"

**Objective**: Change DoxBaseModel from extra="allow" to extra="forbid" for enforcement.

**Paths**:
```bash
TASK_3_6_PATHS=(
  "src/doxstrux/markdown/output_models.py"
  "tests/test_schema_extra_forbid.py"
)
```

**Scope**:
- In: DoxBaseModel config change, CI guard test
- Out: Phase 4 work

**Preconditions** (evidence required):
```bash
$ rg 'extra.*allow' src/doxstrux/markdown/output_models.py
$ rg 'class DoxBaseModel' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_schema_extra_forbid.py -v
# Expected: FAIL (test doesn't exist yet OR extra="allow")
```

### TDD Step 2 — Implement (minimal)

1. Create `tests/test_schema_extra_forbid.py` with `test_doxbasemodel_extra_is_forbid`
2. Change DoxBaseModel to `extra="forbid"`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_schema_extra_forbid.py -v
$ rg 'extra.*forbid' src/doxstrux/markdown/output_models.py
$ uv run pytest tests/test_output_models_minimal.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run pytest tests/test_schema_extra_forbid.py -v
# exit: 0
(paste output)

# cmd: rg 'extra.*forbid' src/doxstrux/markdown/output_models.py
# exit: 0
(paste match showing extra="forbid")
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

### Task 3.7 — Add DocumentIR regression test

**Objective**: Ensure ParserOutput schema changes don't break DocumentIR construction.

**Paths**:
```bash
TASK_3_7_PATHS=(
  "tests/test_document_ir_regression.py"
)
```

**Scope**:
- In: DocumentIR regression test
- Out: Phase 4 work

**Preconditions** (evidence required):
```bash
$ rg 'class DocumentIR' src/doxstrux/markdown/ir.py
$ rg 'from_parser_output\|to_ir' src/doxstrux/markdown/ir.py src/doxstrux/markdown_parser_core.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_document_ir_regression.py -v
# Expected: Test file doesn't exist
```

### TDD Step 2 — Implement (minimal)

Create test file with:
- `test_ir_builds_without_error` parametrized on 5 fixtures
- `test_heading_document_has_structure`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_document_ir_regression.py -v
$ uv run pytest tests/ -v -k "ir_regression"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run pytest tests/test_document_ir_regression.py -v
# exit: 0
(paste output)
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

### Task 3.8 — Create phase unlock artifact

**Objective**: Generate `.phase-3.complete.json` to gate Phase 4.

**Paths**:
```bash
TASK_3_8_PATHS=(
  ".phase-3.complete.json"
)
```

**Scope**:
- In: Phase 3 completion artifact
- Out: Phase 4 work

**Preconditions** (evidence required):
```bash
$ rg 'extra.*forbid' src/doxstrux/markdown/output_models.py
$ uv run pytest tests/test_document_ir_regression.py -q
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f .phase-3.complete.json && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Generate artifact with real values.

### TDD Step 3 — Verify (GREEN)

```bash
$ cat .phase-3.complete.json
$ rg '\[\[PH:' .phase-3.complete.json && exit 1 || echo "No placeholders"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: cat .phase-3.complete.json
# exit: 0
(paste output)

# cmd: rg '\[\[PH:' .phase-3.complete.json && exit 1 || echo "No placeholders"
# exit: 0
No placeholders
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
**Tests**: `uv run pytest tests/ -v`

### Task 4.1 — Create curated fixture validation tool

**Objective**: Build tools/validate_curated_fixtures.py with pattern-based discovery.

**Paths**:
```bash
TASK_4_1_PATHS=(
  "tools/validate_curated_fixtures.py"
)
```

**Scope**:
- In: Pattern-based fixture discovery, validation via ParserOutput.model_validate
- Out: Full validation (Phase 5)

**Preconditions** (evidence required):
```bash
$ rg 'class ParserOutput' src/doxstrux/markdown/output_models.py
$ test -f .phase-3.complete.json && echo "Phase 3 complete"
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f tools/validate_curated_fixtures.py && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Create tool with:
- `CURATED_PATTERNS` glob patterns
- `discover_curated_fixtures()` function
- `validate_fixture()` function
- MAX_CURATED = 50 cap

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/validate_curated_fixtures.py
$ uv run python tools/validate_curated_fixtures.py --help || echo "no help yet"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python tools/validate_curated_fixtures.py
# exit: 0
(paste output)
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

**Objective**: Build tools/regenerate_fixtures.py with bucket-aware classification.

**Paths**:
```bash
TASK_4_2_PATHS=(
  "tools/regenerate_fixtures.py"
)
```

**Scope**:
- In: Bucket classification (structural/security/legacy), --review flag
- Out: Full validation (Phase 5)

**Preconditions** (evidence required):
```bash
$ rg 'discover_curated_fixtures' tools/validate_curated_fixtures.py
$ rg 'CURATED_PATTERNS' tools/validate_curated_fixtures.py
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f tools/regenerate_fixtures.py && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Create tool with:
- `classify_fixture()` function (structural/security/legacy)
- `needs_manual_review()` content-based safety check
- `--bucket`, `--review`, `--dry-run` flags

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/regenerate_fixtures.py --dry-run --bucket structural
$ uv run python tools/regenerate_fixtures.py --help || echo "no help yet"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python tools/regenerate_fixtures.py --dry-run --bucket structural
# exit: 0
(paste output)
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

**Objective**: Add tests/test_no_legacy_field_runtime_usage.py to enforce audit.

**Paths**:
```bash
TASK_4_3_PATHS=(
  "tests/test_no_legacy_field_runtime_usage.py"
)
```

**Scope**:
- In: Legacy field audit via rg, LEGACY_FIELDS_TO_AUDIT list
- Out: Phase 5 work

**Preconditions** (evidence required):
```bash
$ which rg && echo "ripgrep installed"
$ rg 'exception_was_raised' src/doxstrux/ || echo "not found in src"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_no_legacy_field_runtime_usage.py -v
# Expected: Test file doesn't exist
```

### TDD Step 2 — Implement (minimal)

Create test with:
- `LEGACY_FIELDS_TO_AUDIT` list
- `test_no_runtime_usage_of_legacy_field` parametrized test
- Subprocess call to `rg`

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_no_legacy_field_runtime_usage.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run pytest tests/test_no_legacy_field_runtime_usage.py -v
# exit: 0
(paste output)
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

### Task 4.4 — Add validation tool tests

**Objective**: Create tests that verify validation tools use Pydantic validation and affect results.

**Paths**:
```bash
TASK_4_4_PATHS=(
  "tests/test_validation_tools.py"
)
```

**Scope**:
- In: Tests for validate_curated_fixtures.py, regenerate_fixtures.py
- Out: Phase 5 work

**Preconditions** (evidence required):
```bash
$ rg 'model_validate' tools/validate_curated_fixtures.py
$ rg 'ParserOutput' tools/validate_curated_fixtures.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_validation_tools.py -v
# Expected: Test file doesn't exist
```

### TDD Step 2 — Implement (minimal)

Create tests:
- `test_tool_uses_pydantic_validation` - verify model_validate is called
- `test_tool_validation_affects_results` - verify validation failures are reported

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_validation_tools.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run pytest tests/test_validation_tools.py -v
# exit: 0
(paste output)
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

### Task 4.5 — Create phase unlock artifact

**Objective**: Generate `.phase-4.complete.json` to gate Phase 5.

**Paths**:
```bash
TASK_4_5_PATHS=(
  ".phase-4.complete.json"
)
```

**Scope**:
- In: Phase 4 completion artifact
- Out: Phase 5 work

**Preconditions** (evidence required):
```bash
$ uv run python tools/validate_curated_fixtures.py
$ uv run pytest tests/test_validation_tools.py -q
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f .phase-4.complete.json && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Generate artifact with real values.

### TDD Step 3 — Verify (GREEN)

```bash
$ cat .phase-4.complete.json
$ rg '\[\[PH:' .phase-4.complete.json && exit 1 || echo "No placeholders"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: cat .phase-4.complete.json
# exit: 0
(paste output)

# cmd: rg '\[\[PH:' .phase-4.complete.json && exit 1 || echo "No placeholders"
# exit: 0
No placeholders
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

**Goal**: Validate ALL fixtures (620+) in report-only mode.
**Tests**: `uv run pytest tests/ -v`

### Task 5.1 — Create full validation tool

**Objective**: Build tools/validate_test_pairs.py with --report and --threshold modes.

**Paths**:
```bash
TASK_5_1_PATHS=(
  "tools/validate_test_pairs.py"
)
```

**Scope**:
- In: Full fixture validation, --report, --threshold, --output flags
- Out: CI gate (Phase 6)

**Preconditions** (evidence required):
```bash
$ rg 'model_validate' tools/validate_curated_fixtures.py
$ test -f .phase-4.complete.json && echo "Phase 4 complete"
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f tools/validate_test_pairs.py && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Create tool with:
- `validate_directory()` function
- `--report` mode (always exit 0)
- `--threshold` mode (pass if >=N% valid)
- `--output` JSON report

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python tools/validate_test_pairs.py --report
$ uv run python tools/validate_test_pairs.py --threshold 90
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run python tools/validate_test_pairs.py --report
# exit: 0
(paste output)
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

**Objective**: Add tests/test_output_models_empty.py for ParserOutput.empty() validation.

**Paths**:
```bash
TASK_5_2_PATHS=(
  "tests/test_output_models_empty.py"
)
```

**Scope**:
- In: TestEmptyBaseline test class with 10 tests
- Out: CI gate (Phase 6)

**Preconditions** (evidence required):
```bash
$ rg 'def empty' src/doxstrux/markdown/output_models.py
$ rg 'class ParserOutput' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_empty.py -v
# Expected: Test file doesn't exist
```

### TDD Step 2 — Implement (minimal)

Create test file with TestEmptyBaseline class containing:
- test_empty_returns_parser_output_instance
- test_empty_has_all_top_level_keys
- test_empty_content_is_empty
- test_empty_metadata_has_zero_counts
- test_empty_has_no_security_warnings
- test_empty_has_no_dangerous_flags
- test_empty_embedding_not_blocked
- test_empty_not_quarantined
- test_empty_structure_is_empty
- test_empty_mappings_is_empty

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_empty.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run pytest tests/test_output_models_empty.py -v
# exit: 0
(paste output)
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

**Objective**: Add tests/test_parser_output_schema_conformance.py for full validation.

**Paths**:
```bash
TASK_5_3_PATHS=(
  "tests/test_parser_output_schema_conformance.py"
)
```

**Scope**:
- In: TestParserOutputSchemaConformance, TestSecuritySemantics, TestLinkDiscriminatedUnion, TestMathExtraction, TestFootnoteExtraction
- Out: CI gate (Phase 6)

**Preconditions** (evidence required):
```bash
$ rg 'class ParserOutput' src/doxstrux/markdown/output_models.py
$ rg 'model_validate' src/doxstrux/markdown/output_models.py || echo "method from pydantic"
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_parser_output_schema_conformance.py -v
# Expected: Test file doesn't exist
```

### TDD Step 2 — Implement (minimal)

Create test file with 5 test classes:
- TestParserOutputSchemaConformance
- TestSecuritySemantics
- TestLinkDiscriminatedUnion
- TestMathExtraction
- TestFootnoteExtraction

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_parser_output_schema_conformance.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run pytest tests/test_parser_output_schema_conformance.py -v
# exit: 0
(paste output)
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

### Task 5.4 — Create phase unlock artifact

**Objective**: Generate `.phase-5.complete.json` to gate Phase 6.

**Paths**:
```bash
TASK_5_4_PATHS=(
  ".phase-5.complete.json"
)
```

**Scope**:
- In: Phase 5 completion artifact
- Out: Phase 6 work

**Preconditions** (evidence required):
```bash
$ uv run python tools/validate_test_pairs.py --report
$ uv run pytest tests/test_parser_output_schema_conformance.py -q
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f .phase-5.complete.json && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Generate artifact with real values.

### TDD Step 3 — Verify (GREEN)

```bash
$ cat .phase-5.complete.json
$ rg '\[\[PH:' .phase-5.complete.json && exit 1 || echo "No placeholders"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: cat .phase-5.complete.json
# exit: 0
(paste output)

# cmd: rg '\[\[PH:' .phase-5.complete.json && exit 1 || echo "No placeholders"
# exit: 0
No placeholders
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
**Tests**: `uv run pytest tests/ -v`

### Task 6.1 — Create CI workflow

**Objective**: Add .github/workflows/schema_validation.yml for blocking validation.

**Paths**:
```bash
TASK_6_1_PATHS=(
  ".github/workflows/schema_validation.yml"
)
```

**Scope**:
- In: CI workflow with schema version check, fixture validation, schema drift detection
- Out: Production deployment

**Preconditions** (evidence required):
```bash
$ test -d .github/workflows && echo "workflows dir exists" || echo "create it"
$ test -f .phase-5.complete.json && echo "Phase 5 complete"
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f .github/workflows/schema_validation.yml && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Create workflow with:
- Schema version check
- `validate_test_pairs.py --threshold 100`
- Schema drift detection via git diff

### TDD Step 3 — Verify (GREEN)

```bash
$ cat .github/workflows/schema_validation.yml
$ rg 'validate_test_pairs' .github/workflows/schema_validation.yml
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: cat .github/workflows/schema_validation.yml
# exit: 0
(paste output)

# cmd: rg 'validate_test_pairs' .github/workflows/schema_validation.yml
# exit: 0
(paste match)
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

### Task 6.2 — Create schema version test

**Objective**: Add tests/test_schema_version.py to enforce version format and consistency.

**Paths**:
```bash
TASK_6_2_PATHS=(
  "tests/test_schema_version.py"
)
```

**Scope**:
- In: Version format test, no-dev test, empty has same version test
- Out: Production deployment

**Preconditions** (evidence required):
```bash
$ rg 'schema_version' src/doxstrux/markdown/output_models.py
$ rg 'parser-output@' src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_schema_version.py -v
# Expected: Test file doesn't exist
```

### TDD Step 2 — Implement (minimal)

Create test file with:
- test_schema_version_exists
- test_schema_version_format
- test_schema_version_not_dev
- test_empty_has_same_version

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_schema_version.py -v
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: uv run pytest tests/test_schema_version.py -v
# exit: 0
(paste output)
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

### Task 6.3 — Create schema changelog

**Objective**: Create src/doxstrux/markdown/SCHEMA_CHANGELOG.md for version history.

**Paths**:
```bash
TASK_6_3_PATHS=(
  "src/doxstrux/markdown/SCHEMA_CHANGELOG.md"
)
```

**Scope**:
- In: Schema changelog with version history
- Out: Production deployment

**Preconditions** (evidence required):
```bash
$ rg 'parser-output@1.0.0' src/doxstrux/markdown/output_models.py
$ test -f src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f src/doxstrux/markdown/SCHEMA_CHANGELOG.md && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Create changelog with:
- Version `parser-output@1.0.0` entry
- Initial release notes

### TDD Step 3 — Verify (GREEN)

```bash
$ cat src/doxstrux/markdown/SCHEMA_CHANGELOG.md
$ rg 'parser-output@1.0.0' src/doxstrux/markdown/SCHEMA_CHANGELOG.md
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: cat src/doxstrux/markdown/SCHEMA_CHANGELOG.md
# exit: 0
(paste output)

# cmd: rg 'parser-output@1.0.0' src/doxstrux/markdown/SCHEMA_CHANGELOG.md
# exit: 0
(paste match)
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

### Task 6.4 — Create final phase unlock artifact

**Objective**: Generate `.phase-6.complete.json` marking implementation complete.

**Paths**:
```bash
TASK_6_4_PATHS=(
  ".phase-6.complete.json"
)
```

**Scope**:
- In: Phase 6 completion artifact
- Out: Implementation complete

**Preconditions** (evidence required):
```bash
$ test -f .github/workflows/schema_validation.yml
$ uv run pytest tests/test_schema_version.py -q
$ test -f src/doxstrux/markdown/SCHEMA_CHANGELOG.md
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f .phase-6.complete.json && echo "exists" || echo "missing"
# Expected: missing
```

### TDD Step 2 — Implement (minimal)

Generate artifact with real values.

### TDD Step 3 — Verify (GREEN)

```bash
$ cat .phase-6.complete.json
$ rg '\[\[PH:' .phase-6.complete.json && exit 1 || echo "No placeholders"
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# cmd: cat .phase-6.complete.json
# exit: 0
(paste output)

# cmd: rg '\[\[PH:' .phase-6.complete.json && exit 1 || echo "No placeholders"
# exit: 0
No placeholders
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
  "test_command": "uv run pytest tests/ -v",
  "result": "PASS"
}
EOF

$ rg '\[\[PH:' .phase-N.complete.json && exit 1 || echo "No placeholders"
```

---

## Global Clean Table Scan

Run before each phase gate:

```bash
$ rg 'TODO|FIXME|XXX' src/doxstrux/markdown/output_models.py && exit 1 || echo "No unfinished markers"
$ rg '\[\[PH:' . --type md && exit 1 || echo "No placeholders"

$ rg 'from \.\.' src/doxstrux/ && exit 1 || echo "No multi-dot relative imports"
$ rg 'import \*' src/doxstrux/ && exit 1 || echo "No wildcard imports"
```

**Evidence** (paste output):
```
# cmd: rg 'TODO|FIXME|XXX' src/doxstrux/markdown/output_models.py && exit 1 || echo "No unfinished markers"
# exit: 0
(paste output)

# cmd: rg 'from \.\.' src/doxstrux/ && exit 1 || echo "No multi-dot relative imports"
# exit: 0
(paste output)

# cmd: rg 'import \*' src/doxstrux/ && exit 1 || echo "No wildcard imports"
# exit: 0
(paste output)
```

---

## STOP — Phase Gate

Requirements for next phase:

- [ ] All current phase tasks COMPLETE
- [ ] Phase tests pass
- [ ] Global Clean Table scan passes (output pasted above)
- [ ] `.phase-N.complete.json` exists
- [ ] All paths exist
- [ ] Drift ledger current

---

**End of Task List**
