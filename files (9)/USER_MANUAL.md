# AI Task List Framework — User Manual

This framework pairs a strict specification, a template, and a deterministic linter to produce AI task lists that are lintable, drift-resistant, and runnable. Files:
- `AI_TASK_LIST_SPEC_v1.md` — the contract (Spec v1.7; schema_version 1.6; includes plan mode).
- `AI_TASK_LIST_TEMPLATE_v6.md` — starting point for new task lists.
- `ai_task_list_linter_v1_8.py` — the linter implementing the spec (v1.9 code; filename unchanged).
- `README_ai_task_list_linter_v1_8.md` — release notes and highlights.
- Orchestrator prompts:
  - `PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md` — runtime prompt for converting prose → AI task list (plan mode output).

## 1) Core Concepts
- SSOT: spec is authoritative; the linter implements the spec. If spec and linter diverge, fix the linter. If this manual/template ever disagree with them, the spec wins.
- Modes: `template` allows placeholders; `plan` uses real commands and evidence placeholders; `instantiated` forbids placeholders.
- Runner metadata: `runner` and `runner_prefix` declared in YAML front matter.
- Search tool: `search_tool` must be `rg` or `grep` (required).
- Evidence: real command output required in instantiated mode; with `--require-captured-evidence`, `# cmd:` and `# exit:` headers are also required.
- Status: each task has exactly one status (`📋 PLANNED`, `⏳ IN PROGRESS`, `✅ COMPLETE`, `❌ BLOCKED`). `✅ COMPLETE` in instantiated mode requires all STOP checkboxes checked.
- Baseline tests: Baseline Snapshot must include a Baseline tests fenced block with `$` commands and real output in instantiated mode.
- Mode decision: use `mode: template` for generic scaffolds with placeholders; use `mode: plan` for project-specific plans (real commands, evidence placeholders); switch to `mode: instantiated` only when evidence will be real.

## 1.5) How to start a new task list (prose → task list)
1) Select the prose source (e.g., a design/spec doc for the current project).
2) Start a fresh AI session.
3) Paste the entire `PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md`.
4) Paste the full prose document.
5) Let the AI generate a task list in `mode: "plan"`:
  - Includes required headings/sections, TASK_N_M_PATHS arrays, Prose Coverage Mapping, STOP/Global/Drift structure, real commands with evidence placeholders.
6) Save the output in the repo (e.g., `work_folder/<label>_TASKS_v1_plan.md`).
7) Run the linter (via runner) and fix structural issues.
8) Review Prose Coverage Mapping: ensure each major requirement is mapped or explicitly out-of-scope.
9) Later human+CI pass will move to `mode: "instantiated"` once evidence is real. Do not fabricate evidence to satisfy instantiated mode.

## 2) Quickstart (New Project)
1. Copy `AI_TASK_LIST_TEMPLATE_v6.md` to your repo as `PROJECT_TASKS.md`.
2. Fill YAML front matter: `schema_version: "1.6"`, `mode: "template"` for generic scaffolds or `mode: "plan"` for project plans (real commands, evidence placeholders); switch to `mode: "instantiated"` only when evidence is real; set `runner`, `runner_prefix`, `search_tool`.
3. Map prose to tasks: list each major requirement from the source prose and map to task(s); mark out-of-scope items explicitly.
4. Replace placeholders and flip to `mode: "instantiated"` only when evidence will be real.
5. Run baseline commands (git branch/commit, runner/runtime versions, baseline tests); paste outputs with `# cmd/# exit`.
6. For each task: set status, fill paths, add Preconditions commands (use `{search_tool}`), TDD/STOP sections, and evidence when executed.
7. Generate phase unlock artifact with `$ cat > .phase-N.complete.json` and `$ rg` placeholder scan.
8. Run the linter via runner (see below) until it passes.

## 3) Running the Linter
```bash
# Standard lint
uv run python ai_task_list_linter_v1_8.py PROJECT_TASKS.md

# Enforce captured headers in evidence blocks
uv run python ai_task_list_linter_v1_8.py --require-captured-evidence PROJECT_TASKS.md

# JSON output
uv run python ai_task_list_linter_v1_8.py --json PROJECT_TASKS.md
```
Exit codes: 0 = pass, 1 = lint violations, 2 = usage/error.

## 4) Enforcement Highlights (what will fail lint)
- Front matter must have exact `schema_version: "1.6"`, `mode`, `runner`, `runner_prefix`, `search_tool`.
- Required headings (9 anchors) must be present exactly.
- No placeholders allowed anywhere in instantiated mode.
- Task naming rule must appear exactly once.
- Paths array per task: `TASK_N_M_PATHS=(...)` with quoted paths and closing `)`.
- Status line required and must be one allowed value.
- Preconditions (non-Phase-0) must include `$ rg`/`$ grep` per `search_tool`.
- TDD Step 3/Phase Unlock/Global Scan command lines must start with `$`.
- Runner prefix enforcement on `$ pytest/python/mypy/ruff/black/isort`.
- Runner `uv`: forbids `.venv/bin/python`, `python -m`, `pip install` in `$` lines; requires `$ uv sync` and `$ uv run ...` as `$` commands in fenced blocks.
- Import hygiene (runner=uv): `$ rg 'from \.\.'` and `$ rg 'import \*'` must appear as `$` commands in Global Clean Table.
- Phase Unlock: must include `$ cat > .phase-N.complete.json` and `$ rg` placeholder scan as `$` commands (comments don’t count); `.json` suffix enforced.
- STOP evidence: fenced block required even if labels are renamed; both labeled sections must contain real output (headers alone don’t count).
- Baseline evidence: each `$` command must have real (non-header) output lines following.
- Baseline tests: fenced block required with `$` command(s) and real output.
- Drift Ledger: table structure with witness `path:line` in instantiated rows.
- search_tool=rg: `grep` forbidden in fenced code blocks.

## 5) Authoring Guidance (reduce iteration loops)
- Always add `$` before commands in fenced blocks; omit `$` for pasted output.
- Paste real outputs immediately after each `$` command; avoid leaving headers-only evidence.
- For uv projects, ensure all test/tool commands use the declared `runner_prefix` (e.g., `uv run pytest ...`).
- When marking a task `✅ COMPLETE`, check all No Weak Tests and Clean Table boxes.
- Keep a consistent evidence pattern: `# cmd: ...`, `# exit: ...`, then raw output.
- Gates must gate: for Clean Table/unlock, use failing patterns (`! rg ...` or `if rg ...; then exit 1; fi`), not `rg ... || true`.
- If you can’t craft a failing behavior test, label steps Precondition/Implement/Verify rather than pretending TDD.
- For behavior-changing tasks, reference at least one behavior-level test (name + behavior) in TDD/STOP.
- Drift Ledger: if you detect or mention mismatches (prose vs tasks, invariants vs repo), add a ledger row with path:line witness; don’t leave it empty when drift is known.
- Prose Coverage Mapping: include a short table mapping prose requirements to tasks or mark them out-of-scope. Missing or empty coverage is an error in plan/instantiated modes.

## 6) Typical Linter Failures and Fixes
- `schema_version must be '1.6'`: fix YAML front matter.
- `Placeholders are forbidden in instantiated mode`: remove remaining `[[PH:...]]`.
- `command lines must start with '$'`: add `$` to commands in required sections.
- `runner=uv requires '$ uv sync' command line`: add `$ uv sync` in a fenced block.
- `Baseline Snapshot evidence: command(s) missing output`: paste real output after each baseline command (headers alone don’t count).
- `STOP evidence missing fenced code block`: add the evidence fenced block under STOP with labeled sections and real output.
- `Preconditions must include rg command`: ensure each non-Phase-0 task has at least one `$ {search_tool} ...` line.
- `runner=uv requires '$ uv sync' command line`: add `$ uv sync` in a fenced block.

## 7) Recommended CI Usage
- Run `uv run python ai_task_list_linter_v1_8.py --require-captured-evidence PROJECT_TASKS.md` in CI for instantiated lists (recommended as mandatory).
- Fail CI on any lint error; keep the task list updated alongside code changes to avoid drift.

## 8) Known Limitations
- Linting cannot cryptographically prove provenance; it enforces structure and presence of output. Pair with execution logs or automated capture if available.

## 9) Quick Checklists
- Design/AI output (no real evidence yet):
  - [ ] YAML front matter filled; mode = template.
  - [ ] Required headings present (unchanged from template).
  - [ ] Baseline/STOP/Global sections structurally present (may carry placeholders).
  - [ ] Tasks have paths arrays, Preconditions `$ {search_tool} …`, TDD/STOP sections.
  - [ ] Prose Coverage Mapping table present; all major requirements mapped or explicitly out-of-scope.
  - [ ] Drift ledger started if any mismatches are known.
- Executed/human+CI artifact (real evidence):
  - [ ] YAML front matter filled; mode = instantiated.
  - [ ] Required headings present; naming rule stated once (per spec).
  - [ ] Baseline snapshot + tests have real outputs with headers.
  - [ ] Tasks have paths arrays, Preconditions `$ {search_tool} …`, TDD/STOP sections.
  - [ ] At least one behavior-level test (with test name + behavior) referenced for each behavior-changing task.
  - [ ] STOP evidence blocks present with labeled sections, `# cmd/# exit`, real output; checkboxes set if status is COMPLETE.
  - [ ] Phase unlock artifact commands `$ cat …` + `$ rg` scan, `$`-prefixed.
  - [ ] Global scan commands present; uv import hygiene commands included.
  - [ ] No placeholders or pseudo-placeholders remain.
  - [ ] Drift ledger updated with any known mismatches.
  - [ ] Linter passes with `--require-captured-evidence`.
