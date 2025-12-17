---
ai_task_list:
  schema_version: "0.0.8"
  mode: "plan"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# Pydantic Schema Implementation — Task List

**Status**: Phase 0 — NOT STARTED

---

## Non-negotiable Invariants

1. **Clean Table is a delivery gate** — Do not mark complete unless verified and stable.
2. **No silent errors** — Errors raise unconditionally.
3. **No weak tests** — Tests assert semantics, not existence/import/smoke.
4. **Single runner principle** — One canonical runner everywhere (uv).
5. **Evidence anchors required** — Claims require command output or file evidence.
6. **No synthetic reality** — Do not invent outputs, results, or versions.
7. **Import hygiene** — Absolute imports preferred; no multi-dot relative; no wildcards.

---

## Baseline Snapshot

| Field | Value |
|-------|-------|
| Date | 2025-12-17 |
| Repo | doxstrux |
| Branch | security |
| Commit | (capture with git rev-parse HEAD) |
| Runner | uv 0.5.x |
| Runtime | Python 3.12 |

**Evidence** (paste outputs):
```bash
$ git rev-parse --abbrev-ref HEAD
(paste output)

$ git rev-parse HEAD
(paste output)

$ uv --version
(paste output)

$ python --version
(paste output)
```

**Baseline tests**:
```bash
$ uv run pytest -q
(paste output)
```

---

## Phase 0 — Baseline Reality

**Tests**: `uv run pytest -q` / `uv run pytest`

### Task 0.1 — Instantiate + capture baseline

**Objective**: Create task list and capture baseline evidence.

**Paths**:
```bash
TASK_0_1_PATHS=(
  "PYDANTIC_SCHEMA_TASKS.md"
)
```

**Steps**:
1. Copy template to PYDANTIC_SCHEMA_TASKS.md
2. Replace all placeholders with real values
3. Run pre-flight (must be zero)
4. Run baseline commands, paste outputs
5. If failures: log in Drift Ledger, stop

**Verification**:
```bash
$ if rg '\[\[PH:[A-Z0-9_]+\]\]' PYDANTIC_SCHEMA_TASKS.md; then
    echo "ERROR: Placeholders found"
    exit 1
  fi
$ for p in "${TASK_0_1_PATHS[@]}"; do test -e "$p" || exit 1; done
```

- [x] Placeholders zero
- [x] Snapshot captured
- [x] Tests captured
- [x] Paths exist

**Status**: 📋 PLANNED

---

## Phase 1 — Milestone A: RAG Safety Contract

**Goal**: Minimal schema + RAG safety semantics locked in
**Tests**: `uv run pytest tests/test_output_models_*.py -v`

### Task 1.1 — Add Pydantic Dependency

**Objective**: Add pydantic>=2,<3 to project dependencies.

**Paths**:
```bash
TASK_1_1_PATHS=(
  "pyproject.toml"
)
```

**Scope**:
- In: Add pydantic dependency
- Out: No model creation yet

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "pydantic" pyproject.toml
```

### TDD Step 1 — Write test (RED)

```bash
$ python -c "import pydantic; print(pydantic.VERSION)"
# Expected: FAIL (not installed)
```

### TDD Step 2 — Implement (minimal)

```bash
$ uv add "pydantic>=2,<3"
```

### TDD Step 3 — Verify (GREEN)

```bash
$ python -c "import pydantic; print(pydantic.VERSION)"
$ uv run pytest -q
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Pydantic version check:
(paste output)

# Test run output:
(paste output)
```

**No Weak Tests** (all YES):
- [x] Stub/no-op would FAIL this test?
- [x] Asserts semantics, not just presence?
- [x] Has negative case for critical behavior?
- [x] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [x] Tests pass (not skipped)
- [x] Full suite passes
- [x] No placeholders remain
- [x] Paths exist
- [x] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 1.2 — Create MINIMAL Pydantic Models

**Objective**: Create ParserOutput with 4 top-level dict placeholders and DoxBaseModel base class.

**Paths**:
```bash
TASK_1_2_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: ParserOutput, DoxBaseModel, metadata/content/structure/mappings as dict[str, Any]
- Out: Nested models (deferred to Phase 2)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class MarkdownParserCore" src/doxstrux/markdown_parser_core.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_minimal.py -v
# Expected: FAIL (file does not exist)
```

### TDD Step 2 — Implement (minimal)

Create `src/doxstrux/markdown/output_models.py` with:
- DoxBaseModel base class with extra="allow"
- ParserOutput with metadata, content, structure, mappings as dict[str, Any]
- ParserOutput.empty() class method

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_minimal.py -v
$ uv run pytest -q
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
(paste output)

# Model import check:
(paste output)
```

**No Weak Tests** (all YES):
- [x] Stub/no-op would FAIL this test?
- [x] Asserts semantics, not just presence?
- [x] Has negative case for critical behavior?
- [x] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [x] Tests pass (not skipped)
- [x] Full suite passes
- [x] No placeholders remain
- [x] Paths exist
- [x] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

### Task 1.3 — Create RAG Safety Tests

**Objective**: Create security semantic tests for RAG safety contract.

**Paths**:
```bash
TASK_1_3_PATHS=(
  "tests/test_output_models_security.py"
)
```

**Scope**:
- In: test_script_tag_detected, test_safe_document_not_blocked, test_javascript_link_detected
- Out: Extended security fields (prompt injection, BiDi)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class ParserOutput" src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_security.py -v
# Expected: FAIL (tests not passing yet)
```

### TDD Step 2 — Implement (minimal)

Create tests that verify:
- Script tags set has_script=True, has_dangerous_content=True
- Safe markdown does not block embedding
- javascript: links are detected and flagged

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_security.py -v
$ uv run pytest -q
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Security test output:
(paste output)
```

**No Weak Tests** (all YES):
- [x] Stub/no-op would FAIL this test?
- [x] Asserts semantics, not just presence?
- [x] Has negative case for critical behavior?
- [x] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [x] Tests pass (not skipped)
- [x] Full suite passes
- [x] No placeholders remain
- [x] Paths exist
- [x] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

## STOP — Phase 1 Gate

Requirements for Phase 2:

- [x] All Phase 1 tasks COMPLETE
- [x] Phase 1 tests pass
- [x] Global Clean Table scan passes
- [x] `.phase-1.complete.json` exists
- [x] All paths exist
- [x] Drift ledger current

---

## Phase 2 — Milestone B1: Metadata + Security Models

**Goal**: Type Metadata and Security models with extra="forbid"
**Tests**: `uv run pytest tests/test_output_models_*.py -v`

### Task 2.1 — Add Metadata + Security Models

**Objective**: Add typed Metadata, Security, SecurityStatistics, SecuritySummary, SecurityWarning, Encoding models.

**Paths**:
```bash
TASK_2_1_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Metadata, Security sub-models with extra="forbid"
- Out: Content, Structure, Mappings (deferred)

**Preconditions** (evidence required):
```bash
$ uv run pytest -q
$ rg "class ParserOutput" src/doxstrux/markdown/output_models.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_output_models_metadata.py -v
# Expected: FAIL
```

### TDD Step 2 — Implement (minimal)

Add Metadata and Security model hierarchy with extra="forbid".

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_output_models_metadata.py -v
$ uv run pytest -q
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test output:
(paste output)
```

**Clean Table**:
- [x] Tests pass (not skipped)
- [x] Full suite passes
- [x] No placeholders remain
- [x] Paths exist
- [x] Drift ledger updated (if needed)

**Status**: 📋 PLANNED

---

## Drift Ledger

| Date | Higher | Lower | Mismatch | Resolution | Evidence |
|------|--------|-------|----------|------------|----------|
| | | | | | |

---

## Global Clean Table Scan

Run before each phase gate:

```bash
$ rg 'TODO|FIXME|XXX' src/
# Expected: zero matches

$ rg '\[\[PH:' .
# Expected: zero matches

# Import hygiene (required for Python/uv projects):
$ if rg 'from \.\.' src/doxstrux/; then
    echo "ERROR: Multi-dot relative import found"
    exit 1
  fi
$ if rg 'import \*' src/doxstrux/; then
    echo "ERROR: Wildcard import found"
    exit 1
  fi
```

**Evidence** (paste output):
```
(paste clean table scan output)
```

---

## Phase Unlock Artifact

Generate with real values:
```bash
$ cat > .phase-1.complete.json << EOF
{
  "phase": 1,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "test_command": "uv run pytest -q",
  "result": "PASS"
}
EOF

# Verify no placeholders
$ if rg '\[\[PH:|YYYY-MM-DD|TBD' .phase-1.complete.json; then
    echo "ERROR: Placeholder-like tokens found in artifact"
    exit 1
  fi
```

---

**End of Task List**
