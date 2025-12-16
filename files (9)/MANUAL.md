# AI Task List Framework — Manual

This framework pairs a strict specification, a template, and a deterministic linter to produce AI task lists that are lintable, drift-resistant, and runnable.

**SSOT hierarchy**: Spec is authoritative; the linter implements the spec. If they diverge, fix the linter. This manual is derivative; the spec wins on conflicts. <!-- See COMMON.md §SSOT Hierarchy -->

**Files**:
- `AI_TASK_LIST_SPEC.md` — the authoritative contract (see VERSION.yaml for version)
- `AI_TASK_LIST_TEMPLATE.md` — starting point for new task lists
- `tools/ai_task_list_linter.py` — the linter implementing the spec
- `PROMPT_AI_TASK_LIST_ORCHESTRATOR.md` — runtime prompt for prose → task list conversion

---

## 1. Overview

**Modes** (see COMMON.md §Mode Definitions):
- `template`: placeholders allowed (commands and evidence); generic scaffolds
- `plan`: real commands required; evidence placeholders allowed
- `instantiated`: no placeholders anywhere; real evidence required
- Lifecycle: template → plan → instantiated

**Key concepts**:
- Runner metadata: `runner` and `runner_prefix` declared in YAML front matter
- Search tool: `search_tool` must be `rg` or `grep` (required)
- Evidence: real command output required in instantiated mode
- Status: each task has exactly one status (`📋 PLANNED`, `⏳ IN PROGRESS`, `✅ COMPLETE`, `❌ BLOCKED`)

---

## 2. Creating a Task List

### 2.1 From Prose (AI-assisted)

1. Select the prose source (e.g., a design/spec doc for the current project)
2. Start a fresh AI session
3. Paste the entire `PROMPT_AI_TASK_LIST_ORCHESTRATOR.md`
4. Paste the full prose document
5. Let the AI generate a task list in `mode: "plan"`:
   - Includes required headings, TASK_N_M_PATHS arrays, Prose Coverage Mapping, STOP/Global/Drift structure
   - Commands are real; evidence placeholders allowed
6. Save output (e.g., `work_folder/<label>_TASKS_plan.md`)
7. Run the linter and fix structural issues
8. Review Prose Coverage Mapping: ensure each major requirement is mapped or explicitly out-of-scope
9. Later human+CI pass moves to `mode: "instantiated"` once evidence is real

**Prose Coverage Mapping** (required in plan/instantiated):
- Include a markdown table under `## Prose Coverage Mapping` with an Implemented-by column
- Accepted headers: Implemented by Task(s), Implemented by Tasks, Tasks, Task IDs
- Map each major requirement to task(s); if not mapped, explicitly mark out-of-scope
- Missing/empty table is an error in plan/instantiated modes

### 2.2 From Template (Manual)

1. Copy `AI_TASK_LIST_TEMPLATE.md` to your repo as `PROJECT_TASKS.md`
2. Fill YAML front matter:
   - `schema_version`: see COMMON.md §Version Metadata
   - `mode`: "template" for scaffolds, "plan" for projects, "instantiated" when evidence is real
   - `runner`, `runner_prefix`, `search_tool`
3. Replace placeholders; flip mode only when evidence is ready
4. Run baseline commands and paste outputs with `# cmd`/`# exit` headers
5. For each task: set status, fill paths, add Preconditions, TDD/STOP sections

---

## 3. Task List Structure

### Baseline Snapshot

- Fill Date, Repo, Branch, Commit, Runner, Runtime with real values
- Run baseline commands and paste outputs:
  - `git rev-parse --abbrev-ref HEAD`
  - `git rev-parse HEAD`
  - Runner/runtime versions (e.g., `uv --version`, `uv run python --version`)
- Run baseline tests (e.g., `uv run pytest -q`); paste full output
- Instantiated mode: no pseudo-placeholders (no `XX-XX`, `(capture at start)`)

### Phases and Tasks

- Phase 0: bootstrap/instantiation and phase-0 unlock artifact
- For each task:
  - Create `### Task N.M — <name>` with `TASK_N_M_PATHS` array (quoted paths)
  - Task IDs must be unique
  - Preconditions: add `$ rg`/`$ grep` symbol checks (per search_tool)
  - TDD steps: commands for RED/GREEN; keep the three TDD headings

### STOP Blocks

- Include No Weak Tests + Clean Table checklists
- Paste evidence labeled with `# Test run output:` and `# Symbol/precondition check output:`
- Include `# cmd:`/`# exit:` headers when using `--require-captured-evidence`

---

## 4. Running the Linter

```bash
# Standard lint
uv run python tools/ai_task_list_linter.py PROJECT_TASKS.md

# Enforce captured headers in evidence blocks
uv run python tools/ai_task_list_linter.py --require-captured-evidence PROJECT_TASKS.md

# JSON output
uv run python tools/ai_task_list_linter.py --json PROJECT_TASKS.md
```

Exit codes: 0 = pass, 1 = lint violations, 2 = usage/error.

---

## 5. Enforcement Rules (Reference)

All enforcement rules are defined in `AI_TASK_LIST_SPEC.md`. Key rule IDs:

| Rule ID | One-line Summary |
|---------|-----------------|
| R-ATL-003 | Placeholder format and mode restrictions |
| R-ATL-021 | Baseline evidence requirements |
| R-ATL-023 | STOP evidence block required |
| R-ATL-024 | Evidence labeled sections and headers |
| R-ATL-050 | Phase unlock commands and scan |
| R-ATL-060 | Global Clean Table scan commands |
| R-ATL-063 | Import hygiene (runner=uv) |
| R-ATL-070 | Runner/runner_prefix required |
| R-ATL-071 | Runner consistency enforcement |
| R-ATL-072 | Runner-specific forbidden patterns |
| R-ATL-090 | Status values and state transitions |

For detailed rule text and requirements, see the spec.

---

## 6. Evidence and Commands

### $ Prefix Requirements

- All executable lines in required sections (Baseline, STOP, Global, Phase Unlock) must start with `$`
- Use real commands; avoid placeholders in instantiated mode
- Comments containing required patterns do NOT satisfy requirements

### Runner/Search Tool Rules

- `search_tool: "rg"`: use `rg` in code blocks; grep forbidden
- `runner: "uv"` with `runner_prefix: "uv run"`:
  - Include `$ uv sync` and `$ uv run <command>`
  - Never emit `$ .venv/bin/python`, `$ python -m`, or `$ pip install` in `$` lines

### Import Hygiene (runner=uv)

Include as actual `$` command lines (not comments):
```bash
$ rg 'from \.\.' src/
$ rg 'import \*' src/
```

### Phase Unlock

Must show `$ cat > .phase-N.complete.json` and a `$ rg` placeholder scan:
```bash
$ cat > .phase-0.complete.json << EOF
{"phase": 0}
EOF

$ if rg '\[\[PH:' .phase-0.complete.json; then
>   echo "ERROR: placeholders found"
>   exit 1
> fi
```

### Gates Must Gate

Do NOT use `rg <pattern> && exit 1 || true` in gates. Use failing patterns:
```bash
$ ! rg 'TODO|FIXME|XXX' src/
# or
$ if rg 'pattern' path/; then
>   echo "ERROR: pattern found"
>   exit 1
> fi
```

---

## 7. Common Mistakes and Fixes

| Error | Fix |
|-------|-----|
| `schema_version must match COMMON.md` | Fix YAML front matter to value in COMMON.md |
| `Placeholders are forbidden in instantiated mode` | Remove remaining `[[PH:]]` |
| `command lines must start with '$'` | Add `$` to commands in required sections |
| `runner=uv requires '$ uv sync' command line` | Add `$ uv sync` in a fenced block |
| `Baseline evidence: command(s) missing output` | Paste real output after each baseline command |
| `STOP evidence missing fenced code block` | Add evidence fenced block with labeled sections |
| `Preconditions must include rg command` | Add `$ rg <pattern>` line to each non-Phase-0 task |
| `search_tool=rg: grep forbidden` | Replace `grep` with `rg` in code blocks |

---

## 8. Checklists

### 8.1 Plan Mode Checklist

- [ ] YAML front matter filled; mode = plan
- [ ] Required headings present (unchanged from template)
- [ ] Baseline/STOP/Global sections structurally present (evidence placeholders allowed)
- [ ] Tasks have paths arrays, Preconditions with `$ {search_tool} <pattern>`
- [ ] Prose Coverage Mapping table present with Implemented-by column
- [ ] All major requirements mapped or explicitly out-of-scope
- [ ] Drift ledger started if any mismatches are known

### 8.2 Instantiated Mode Checklist

- [ ] YAML front matter filled; mode = instantiated
- [ ] Required headings present; naming rule stated once
- [ ] Baseline snapshot + tests have real outputs with `# cmd`/`# exit` headers
- [ ] Tasks have paths arrays, Preconditions `$ {search_tool} <pattern>`, TDD/STOP sections
- [ ] At least one behavior-level test (name + behavior) referenced per behavior-changing task
- [ ] STOP evidence blocks present with labeled sections and real output
- [ ] Phase unlock artifact commands `$ cat > .phase-N.complete.json` + `$ rg` scan
- [ ] Global scan commands present; import hygiene commands included (runner=uv)
- [ ] No placeholders or pseudo-placeholders remain
- [ ] Drift ledger updated with any known mismatches
- [ ] Linter passes with `--require-captured-evidence`

---

## 9. CI Integration

Run in CI for instantiated lists (recommended as mandatory):
```bash
uv run python tools/ai_task_list_linter.py --require-captured-evidence PROJECT_TASKS.md
```

- Fail CI on any lint error
- Keep the task list updated alongside code changes to avoid drift

---

## 10. Limitations

- Linting cannot cryptographically prove provenance; it enforces structure and presence of output
- True "reality verification" requires execution/evidence-capture tooling
- The spec acknowledges headers as "not cryptographically verifiable"
- Pair with execution logs or automated capture if available
