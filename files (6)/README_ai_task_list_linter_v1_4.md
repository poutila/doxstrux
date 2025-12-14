# AI Task List Linter v1.4

Deterministic linter for AI Task Lists (Spec v1.2).

## Run

```bash
# Standard lint
uv run python ai_task_list_linter_v1_4.py PROJECT_TASKS.md

# With captured evidence header enforcement (opt-in)
uv run python ai_task_list_linter_v1_4.py --require-captured-evidence PROJECT_TASKS.md

# JSON output
uv run python ai_task_list_linter_v1_4.py --json PROJECT_TASKS.md
```

Exit codes:
- 0 = pass
- 1 = lint violations
- 2 = usage/internal error

## What's New in v1.4 (Spec v1.2)

### R-ATL-024: Captured Evidence Headers (opt-in)

When `--require-captured-evidence` is enabled, evidence blocks must include:

```bash
# cmd: uv run pytest tests/
# exit: 0
===== test session starts =====
...
```

**Enforcement**:
- Baseline Snapshot: `# cmd:` + `# exit:` required (exit can be non-zero)
- STOP evidence: `# cmd:` + `# exit: 0` required (must pass)
- Global Clean Table: `# cmd:` + `# exit: 0` required (must pass)

This eliminates the "fake evidence" loophole where fabricated outputs pass lint.

### R-ATL-071: Fixed False Positives

Runner prefix enforcement now **only checks `$` command lines**:
- ✅ `$ uv run pytest tests/` — checked
- ✅ `python version ok` (output) — NOT checked

This prevents false positives on output that mentions `python`, `pytest`, etc.

### R-ATL-033: Exactly Once Enforcement

Naming rule must be stated **exactly once**, not just "at least once".

### R-ATL-050: Phase Unlock Artifact Content

In instantiated mode, Phase Unlock Artifact section must reference phase artifact file (e.g., `.phase-0.complete.json`).

## Rules Enforced

| Rule | Description |
|------|-------------|
| R-ATL-001 | YAML front matter with `ai_task_list` block |
| R-ATL-002 | Mode semantics (template vs instantiated) |
| R-ATL-003 | Placeholder syntax `[[PH:NAME]]` |
| R-ATL-010 | Required headings (9 total) |
| R-ATL-020 | Baseline Snapshot table rows |
| R-ATL-021 | Baseline Evidence marker |
| R-ATL-022 | No evidence placeholders in instantiated mode |
| R-ATL-023 | Non-empty evidence in instantiated mode |
| **R-ATL-024** | **Captured evidence headers (opt-in, NEW)** |
| R-ATL-030 | Phase 0 required |
| R-ATL-031 | Task ID uniqueness |
| R-ATL-032 | Canonical `TASK_N_M_PATHS` array |
| **R-ATL-033** | **Naming rule stated exactly once (FIXED)** |
| R-ATL-040 | TDD headings (Phase 1+ only) |
| R-ATL-041 | STOP block + No Weak Tests (Phase 1+ only) |
| **R-ATL-050** | **Phase Unlock Artifact content (NEW)** |
| R-ATL-060 | Global Clean Table Scan hooks |
| R-ATL-061 | Global scan evidence in instantiated mode |
| **R-ATL-071** | **Runner prefix on $ command lines only (FIXED)** |
| R-ATL-072 | UV-specific enforcement |
| R-ATL-080 | Drift Ledger table columns |
| R-ATL-D2 | Preconditions symbol-check command |
| R-ATL-D3 | Drift Ledger Evidence witness format |
| R-ATL-D4 | search_tool=rg forbids grep in code blocks only |

## Design Notes

- **stdlib only** — no external dependencies
- **deterministic** — no network, no repo mutation
- **opt-in provenance** — `--require-captured-evidence` for strict evidence validation
- **no false positives** — R-ATL-071 only checks `$` prefixed lines
- **Phase 0 exempt** — bootstrap tasks don't require TDD/STOP blocks

## Test Coverage

```bash
# Template passes
python ai_task_list_linter_v1_4.py template.md  # ✅ PASS

# R-ATL-071 no false positive on output
python ai_task_list_linter_v1_4.py doc_with_python_in_output.md  # ✅ PASS

# Fake evidence without flag (passes baseline)
python ai_task_list_linter_v1_4.py fake_evidence.md  # ✅ PASS

# Fake evidence with flag (FAILS R-ATL-024)
python ai_task_list_linter_v1_4.py --require-captured-evidence fake_evidence.md  # ❌ R-ATL-024

# Valid captured evidence
python ai_task_list_linter_v1_4.py --require-captured-evidence valid_evidence.md  # ✅ PASS

# Non-zero exit in gate (FAILS)
python ai_task_list_linter_v1_4.py --require-captured-evidence exit_1.md  # ❌ R-ATL-024: exit must be 0
```

## Example Output

Human-readable:
```
PROJECT_TASKS.md:30:R-ATL-024:Baseline Snapshot evidence missing '# cmd:' header.
PROJECT_TASKS.md:64:R-ATL-024:Global Clean Table evidence exit must be 0 (found exit: 1).
PROJECT_TASKS.md:52:R-ATL-050:Phase Unlock Artifact must reference phase artifact file.
```

## Migration from v1.3

1. Ensure Phase Unlock Artifact references `.phase-N.complete.json`
2. If using `--require-captured-evidence`:
   - Add `# cmd:` and `# exit:` headers to all evidence blocks
   - Ensure STOP and Global Clean Table have `exit: 0`
3. Remove duplicate naming rule statements (if any)
4. No changes needed for R-ATL-071 (fix is backward compatible)
