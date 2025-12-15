---
ai_task_list:
  schema_version: "1.6"
  mode: "instantiated"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# AI_TASK_LIST_TEMPLATE.md

**Version**: 6.0 (v1.6 spec — no comment compliance)  
**Scope**: Pydantic schema implementation for parser output (doxstrux)  
**Modes**: Template mode (placeholders allowed) → Instantiated mode (placeholders forbidden)

---

## Non-negotiable Invariants

1. **Clean Table is a delivery gate** — Do not mark complete unless verified and stable.
2. **No silent errors** — Errors raise unconditionally.
3. **No weak tests** — Tests assert semantics, not existence/import/smoke.
4. **Single runner principle** — One canonical runner everywhere (`uv run`).
5. **Evidence anchors required** — Claims require command output or file evidence.
6. **No synthetic reality** — Do not invent outputs, results, or versions.
7. **Import hygiene** — Absolute imports preferred; no multi-dot relative (`from ..`); no wildcards (`import *`).

---

## Placeholder Protocol

**Format** (template reference only): placeholder names use `PH_NAME` where NAME is `[A-Z0-9_]+` (none remain in this instantiated file).

**Pre-flight** (must return zero — fails if placeholders found):
```bash
$ rg '\\[\\[PH:' PYDANTIC_SCHEMA_TASKS.md && { echo "ERROR: Placeholders found"; exit 1; } || exit 0
```

---

## Source of Truth Hierarchy

1. Executed tests + tool output (highest)
2. Repository state (commit hash)
3. Runtime code
4. This task list
5. Design docs (lowest — historical once execution begins)

**Drift rule**: Higher wins. Update lower source and log in Drift Ledger.

---

# Pydantic Schema Implementation — Task List

**Status**: Phase 0 — NOT STARTED

---

## Baseline Snapshot (capture before any work)

| Field | Value |
|-------|-------|
| Date | 2025-12-15 |
| Repo | doxstrux |
| Branch | security |
| Commit | c44f5979e87be89a3d1deca016969953ac1141d0 |
| Runner | uv 0.9.17 |
| Runtime | Python 3.12.3 |

**Evidence** (paste outputs):
```bash
# cmd: git rev-parse --abbrev-ref HEAD
# exit: 0
$ git rev-parse --abbrev-ref HEAD
security

# cmd: git rev-parse HEAD
# exit: 0
$ git rev-parse HEAD
c44f5979e87be89a3d1deca016969953ac1141d0

# cmd: uv --version
# exit: 0
$ uv --version
uv 0.9.17 (2b5d65e61 2025-12-09)

# cmd: uv run python --version
# exit: 0
$ uv run python --version
Python 3.12.3

```

**Baseline tests**:
```bash
# cmd: uv sync
# exit: 0
$ uv sync
Resolved 147 packages in 1ms
Audited 57 packages in 0.96ms

# cmd: uv run pytest -q
# exit: 0
$ uv run pytest -q
........................................................................ [ 12%]
........................................................................ [ 24%]
........................................................................ [ 37%]
........................................................................ [ 49%]
........................................................................ [ 61%]
........................................................................ [ 74%]
........................................................................ [ 86%]
........................................................................ [ 98%]
.......                                                                  [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________

Name                                              Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------------
src/doxstrux/__init__.py                              6      0   100%
src/doxstrux/api.py                                  11      0   100%
src/doxstrux/markdown/__init__.py                     1      0   100%
src/doxstrux/markdown/budgets.py                     61      0   100%
src/doxstrux/markdown/config.py                      56      8    86%   47-52, 66, 70
src/doxstrux/markdown/exceptions.py                   7      0   100%
src/doxstrux/markdown/extractors/__init__.py          0      0   100%
src/doxstrux/markdown/extractors/blockquotes.py      21      0   100%
src/doxstrux/markdown/extractors/codeblocks.py       44      0   100%
src/doxstrux/markdown/extractors/footnotes.py        40      3    92%   82, 99-100
src/doxstrux/markdown/extractors/html.py             47      0   100%
src/doxstrux/markdown/extractors/links.py            52     11    79%   85-102, 127-128
src/doxstrux/markdown/extractors/lists.py            92     14    85%   153, 164, 186, 247, 268-297
src/doxstrux/markdown/extractors/math.py             17      4    76%   60-61, 85-86
src/doxstrux/markdown/extractors/media.py            58      1    98%   99
src/doxstrux/markdown/extractors/paragraphs.py       16      0   100%
src/doxstrux/markdown/extractors/sections.py        108      7    94%   65-66, 133-134, 192, 200-201
src/doxstrux/markdown/extractors/tables.py          124     15    88%   70-74, 158-162, 180-183, 187, 190-193, 229
src/doxstrux/markdown/ir.py                          66      0   100%
src/doxstrux/markdown/security/__init__.py            0      0   100%
src/doxstrux/markdown/security/validators.py        128     17    87%   90, 93, 106, 114, 125, 247, 263-264, 312, 339-342, 348-350, 390, 429, 442
src/doxstrux/markdown/utils/__init__.py               3      0   100%
src/doxstrux/markdown/utils/encoding.py              58      6    90%   98-99, 128-133
src/doxstrux/markdown/utils/line_utils.py            21      0   100%
src/doxstrux/markdown/utils/section_utils.py         55      8    85%   75, 79-81, 170, 181-182, 191
src/doxstrux/markdown/utils/text_utils.py            50      1    98%   108
src/doxstrux/markdown/utils/token_utils.py          101     32    68%   97, 99-101, 103, 108, 189, 191, 240-256, 280-281, 283-288
src/doxstrux/markdown_parser_core.py                749     88    88%   65, 84-134, 265-267, 325, 340, 416-418, 426, 457, 461, 488, 540-545, 597-601, 656, 676-677, 687, 764, 766, 863-864, 920-921, 1035, 1037, 1161-1169, 1176-1184, 1188-1196, 1201-1204, 1218-1226, 1242-1243, 1253-1254, 1707, 1711, 1759, 1880, 1889, 1934, 1936, 2054, 2058
src/doxstrux/rag_guard.py                           118      0   100%
-------------------------------------------------------------------------------
TOTAL                                              2110    215    90%
Coverage HTML written to dir htmlcov
Required test coverage of 80% reached. Total coverage: 89.81%
583 passed in 13.62s
```

---

## Phase 0 — Baseline Reality

**Tests**: `uv run pytest -q` / `uv run pytest`

### Task 0.1 — Instantiate + capture baseline

**Objective**: Copy template, set metadata, capture repo baseline, and validate empty schema state.

**Paths**:
```bash
TASK_0_1_PATHS=(
  "PYDANTIC_SCHEMA_TASKS.md"
)
```

**Steps**:
1. Copy template to `PYDANTIC_SCHEMA_TASKS.md`.
2. Replace all placeholder tokens with real values (completed in this version).
3. Run pre-flight placeholder scan on this task list.
4. Run baseline commands, paste outputs.
5. If failures: log in Drift Ledger, stop.

**Verification**:
```bash
if rg '\[\[PH:[A-Z0-9_]+\]\]' PYDANTIC_SCHEMA_TASKS.md; then
  echo "ERROR: Placeholders found"
  exit 1
fi
for p in "${TASK_0_1_PATHS[@]}"; do test -e "$p" || exit 1; done
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
cat > .phase-0.complete.json << EOF
{
  "phase": 0,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "test_command": "uv run pytest -q",
  "result": "PASS"
}
EOF

# Verify no placeholders in artifact
if rg '\[\[PH:|YYYY-MM-DD|TBD' .phase-0.complete.json; then
  echo "ERROR: Placeholder-like tokens found in artifact"
  exit 1
fi
```

- [ ] Artifact created with real timestamp
- [ ] Artifact has real commit hash
- [ ] No placeholders in artifact

**Status**: 📋 PLANNED

---

## Phase 1 — Pydantic schema foundations

**Goal**: Establish Pydantic models for parser output and lock contract with tests + changelog.
**Tests**: `uv run pytest tests/markdown -q` / `uv run pytest tests/markdown`

### Task 1.1 — Add Pydantic dependency and scaffolding

> **Naming rule**: Task ID `N.M` → Path array `TASK_N_M_PATHS` (dots become underscores)

**Objective**: Add Pydantic to the project and create the output models module scaffold.

**Paths**:
```bash
# Example: Task 1.1 → TASK_1_1_PATHS
TASK_1_1_PATHS=(
  "pyproject.toml"
  "src/doxstrux/markdown/output_models.py"
)
```

**Scope**:
- In: Declare dependency, create module file with stubs, ensure import hygiene.
- Out: Full field definitions (covered in Task 1.2).

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ rg pydantic pyproject.toml src || true
$ rg -n pydantic pyproject.toml || true
$ rg 'from \.\.' src/doxstrux || true
$ rg 'import \*' src/doxstrux || true
$ rg output_models tests || true
$ rg parser_output tests || true
$ rg BaseModel src/doxstrux/markdown || true
$ rg pydantic tests || true
$ rg BaseModel tests || true
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/markdown/test_output_models.py::test_placeholder  # stub test expected to fail
```

### TDD Step 2 — Implement (minimal)

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/markdown/test_output_models.py::test_placeholder
$ uv run pytest tests/markdown -q
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
# cmd: echo "not run"
# exit: 0
NOT RUN — task planned

# Symbol/precondition check output:
# cmd: echo "not run"
# exit: 0
NOT RUN — task planned
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

### Task 1.2 — Define output models and schema changelog

**Objective**: Implement Pydantic models for parser output and document schema changes.

**Paths**:
```bash
TASK_1_2_PATHS=(
  "src/doxstrux/markdown/output_models.py"
  "src/doxstrux/markdown/SCHEMA_CHANGELOG.md"
)
```

**Scope**:
- In: Field definitions for parser output, validation rules, version bump entry in changelog.
- Out: Parser integration (wiring), covered in later phase.

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ rg 'class .*BaseModel' src/doxstrux/markdown/output_models.py || true
$ rg -n BaseModel src/doxstrux/markdown/output_models.py || true
$ rg SCHEMA_CHANGELOG src/doxstrux/markdown || true
$ rg 'from \.\.' src/doxstrux || true
$ rg 'import \*' src/doxstrux || true
$ rg output_models tests || true
$ rg parser_output tests || true
$ rg BaseModel src/doxstrux/markdown || true
$ rg pydantic tests || true
$ rg BaseModel tests || true
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/markdown/test_output_models.py::test_required_fields  # expected to fail initially
```

### TDD Step 2 — Implement (minimal)

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/markdown/test_output_models.py
$ uv run pytest tests/markdown -q
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
# cmd: echo "not run"
# exit: 0
NOT RUN — task planned

# Symbol/precondition check output:
# cmd: echo "not run"
# exit: 0
NOT RUN — task planned
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

Generate with real values (no placeholders — commands must use $ prefix when instantiated):
```bash
$ cat > .phase-1.complete.json << EOF
{
  "phase": 1,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "result": "PASS"
}
EOF

# Verify no placeholders
$ rg '\[\[PH:|YYYY-MM-DD|TBD' .phase-1.complete.json || true
```

---

## Global Clean Table Scan

Run before each phase gate (commands must use $ prefix when instantiated):

```bash
$ rg --stats 'TODO|FIXME|XXX' src/
$ rg 'from \.\.' src/doxstrux || true
$ rg 'import \*' src/doxstrux || true
```

**Evidence** (paste output):
```
# cmd: rg --stats 'TODO|FIXME|XXX' src/ || true; rg 'from \.\.' src/doxstrux || true; rg --stats 'import \*' src/doxstrux || true
# exit: 0
0 matches
0 matched lines
0 files contained matches
30 files searched
0 bytes printed
238654 bytes searched
0.000136 seconds spent searching
0.003240 seconds

src/doxstrux/markdown/security/validators.py:    from ..config import SECURITY_PROFILES

0 matches
0 matched lines
0 files contained matches
30 files searched
0 bytes printed
238654 bytes searched
0.000143 seconds spent searching
0.003370 seconds
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

**End of Template**
