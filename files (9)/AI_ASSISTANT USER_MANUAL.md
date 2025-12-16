# AI Assistant Manual — Converting Prose to a Spec-Compliant AI Task List

Mental model: “I am making a manual for myself. I need to use this opportunity 100%.” Do not assume; verify. Use the spec, template, and linter as your guardrails.

**SSOT hierarchy**: If this manual, the template, and the spec/linter ever disagree, the spec (`AI_TASK_LIST_SPEC_v1.md` — Spec v1.9, schema_version 1.7) wins; the linter implements the spec (fix linter if they diverge). Copy patterns from spec/template; only adapt paths/commands. <!-- See COMMON.md §SSOT Hierarchy -->
**Shared definitions**: `COMMON.md` holds canonical version metadata, modes, runner/import/gate/placeholder/evidence rules. Always match it.

## 1) Inputs and Prep
- Source: the prose/design file you’re converting (e.g., the current project’s design/spec doc).
- Framework: spec `AI_TASK_LIST_SPEC_v1.md`, template `AI_TASK_LIST_TEMPLATE_v6.md`, linter `ai_task_list_linter_v1_9.py`.
- Run env: use the declared runner (e.g., `uv run`) for lint/test commands.
- Goal reminder: produce an instantiated task list that passes the linter and anchors to reality with real commands/evidence.
- Mode decision:
  - `mode: "template"`: scaffold with command/evidence placeholders for generic reuse.
  - `mode: "plan"`: project-specific planning; commands must be real; evidence/output placeholders allowed.
  - `mode: "instantiated"`: no placeholders; required evidence carries real output.
- Prose coverage: list each major requirement from the prose and map it to task(s). If a requirement has no mapped task, either add one or explicitly mark it out-of-scope.

## 2) Read and Extract Work Items
- Skim the prose once end-to-end; list candidate phases and tasks.
- Identify deliverables (files to create/modify), key commands/tests, and acceptance criteria.
- Note risky areas (missing deps, ambiguous scope, external constraints).
- Decide phase grouping: Phase 0 = baseline/bootstrap; Phase 1+ = feature work.

## 3) Instantiate the Template (Structure First)
- Copy `AI_TASK_LIST_TEMPLATE_v6.md` to a new file (e.g., `PROJECT_TASKS.md`).
- Fill YAML front matter: `schema_version: "1.7"`, `mode: "plan"` for project planning; flip to `mode: "instantiated"` only when evidence is real; set `runner`, `runner_prefix`, `search_tool`.
- Keep required headings intact (per spec anchors).
- Set status for each task (one of: 📋 PLANNED, ⏳ IN PROGRESS, ✅ COMPLETE, ❌ BLOCKED).

## 4) Baseline Snapshot (Reality First)
- Fill Date, Repo, Branch, Commit, Runner, Runtime with real values.
- Run baseline commands and paste outputs with `# cmd`/`# exit` headers:
  - `git rev-parse --abbrev-ref HEAD`
  - `git rev-parse HEAD`
  - Runner/runtime versions (e.g., `uv --version`, `uv run python --version`).
- Run baseline tests (e.g., `uv run pytest -q`); paste full output.
- Run lint/tests via the declared runner (e.g., `uv run python ai_task_list_linter_v1_9.py …`), not system python.
- Instantiated mode means no pseudo-placeholders either (e.g., no `XX-XX`, `(capture at start)`, or `# OUTPUT HERE`); use real values or leave the field blank and mark status ≠ COMPLETE.

## 5) Define Phases and Tasks
- Phase 0: bootstrap/instantiation and phase-0 unlock artifact.
- For each feature/task from the prose:
  - Create `### Task N.M — <name>` with `TASK_N_M_PATHS` array (quoted paths). Task IDs must be unique (no duplicate `Task N.M` headings).
  - Preconditions: add `$ rg`/`$ grep` symbol checks relevant to the task (required by search_tool).
  - TDD steps: commands for RED/GREEN aligned to the real test entrypoints. Keep the three TDD headings. If true RED (failing behavior test) isn’t possible, use Step 1 to add a characterization/contract test (or explicit rationale) under the RED heading rather than dropping the headings.
  - STOP: include No Weak Tests + Clean Table checklists; plan to paste evidence labeled with `# Test run output:` and `# Symbol/precondition check output:`.
- Scope: in/out bullets if needed for clarity.
- Canonical examples: use `canonical_examples/example_plan.md` (plan) and `canonical_examples/example_template.md` (template) as structural guides; see `canonical_examples/negatives/` for expected-fail patterns.

## 1.5) Prose Coverage Mapping (required in plan/instantiated)
- Required in plan/instantiated: include a markdown table under `## Prose Coverage Mapping` with an Implemented-by column (accepted headers: Implemented by Task(s), Implemented by Tasks, Tasks, Task IDs). References must point to existing unique Task IDs; ranges must be forward and same prefix.
- For each major requirement in the source prose, map it to task(s). If a requirement has no mapped task, either add one or explicitly mark it out-of-scope. Plan/instantiated modes error on missing/empty coverage tables.
- Suggested table:

| Prose requirement (label) | Location (file/section) | Implemented by task(s) |
|---------------------------|--------------------------|------------------------|
|                           |                          |                        |

## 1.6) Orchestrator entry point (prose → task list)
- Runtime prompt: `PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md`.
- How to use:
  1. Start a fresh AI session.
  2. Paste the entire orchestrator prompt.
  3. Paste the full prose document.
  4. Expect a `mode: "plan"` task list with required headings, TASK_N_M_PATHS arrays, Prose Coverage Mapping, STOP/Global/Drift structure, real commands and evidence placeholders.
  - Role split:
    - Orchestrator: the runtime prompt used in chat to generate the task list.
    - Manual/spec/template/linter: background rules that must be respected.
    - Design-time output: plan mode; commands real, evidence placeholders allowed; no fabricated evidence.
    - Execution/human+CI: later pass switches to instantiated mode with real evidence.

## 6) Evidence and Commands (No Comment Compliance)
- All executable lines in required sections must start with `$`.
- Use real commands; avoid placeholders in instantiated mode.
- For uv projects: include `$ uv sync`, `$ uv run …` commands somewhere in code blocks.
- Import hygiene (runner=uv): include `$ rg 'from \.\.' …` and `$ rg 'import \*' …` as commands (not comments).
- Phase Unlock: must show `$ cat > .phase-N.complete.json` and a `$ rg` placeholder scan.
- Global Clean Table: include `$ rg` checks for TODO/FIXME/XXX and placeholders; include import hygiene checks when uv.
- Preconditions: each non-Phase-0 task must include at least one `$ rg …` (or `$ grep …` if search_tool=grep) in its Preconditions block.
- STOP evidence: each STOP block must have labeled sections (`# Test run output:`, `# Symbol/precondition check output:`) with `# cmd:`/`# exit:` headers and real output when COMPLETE.
- Discovery-only checks (non-gating): can use `$ rg ... || true` when you only want to find references (not fail).
- Gates must actually gate: do NOT use `rg … && exit 1 || true/echo` in gates. Use `! rg 'pattern' …` or:
  ```bash
  $ if rg 'pattern' path/; then
  >   echo "ERROR: pattern found"
  >   exit 1
  > fi
  ```
- TDD semantics: RED should be a real failing behavior test, not just file/existence checks. Keep the TDD headings; if a failing test isn’t possible, use RED to add a characterization/contract test or explicit rationale under that heading.
- No Weak Tests: don’t claim non-weak tests if you only check existence/imports; strengthen tests or adjust the STOP checklist expectations for wiring-only tasks. For behavior-changing tasks, include at least one behavior-level test (beyond import/existence) in TDD/STOP and reference a concrete test name + behavior. Ensure STOP checkboxes reflect this honestly.
- Runner/search_tool rules:
  - `search_tool: "rg"`: use `rg` in code blocks; grep forbidden in code blocks (prose mention OK).
  - `runner: "uv"` with `runner_prefix: "uv run"`: include `$ uv sync` and `$ uv run …`; use `$ uv run pytest/python/...` for managed tools; never emit `$ .venv/bin/python`, `$ python -m`, or `$ pip install` in `$` lines.
- Validation suite: after writing the task list, run positives/negatives from `VALIDATION_SUITE.md` (canonical_examples plus negatives in `canonical_examples/negatives/`) to catch regressions early.

## 7) Evidence Blocks (Captured and Non-Empty)
- Baseline, STOP, and Global Clean Table evidence blocks must have:
  - `# cmd:` and `# exit:` headers (with `--require-captured-evidence`).
  - Real output lines; headers alone do not count.
- For tasks marked ✅ COMPLETE, ensure STOP checkboxes are `[x]`.
- “Not run” evidence is acceptable only while status is not COMPLETE; replace with real outputs before marking COMPLETE.

## 8) Clean-Up and Alignment
- Remove any remaining placeholders; run `rg '\[\[PH:'` to confirm zero.
- Ensure status lines use a single value (no menus).
- Phase unlock artifact commands and scans must be `$`-prefixed.
- Preconditions must contain at least one `$ rg …` line per task.
- Drift Ledger: log real mismatches (e.g., known import hygiene violations vs. invariant); don’t leave it empty if you’ve observed drift. If you mention or detect a mismatch between the task list and prose/spec, or between invariants and repo state, add a ledger entry with higher/lower sources, short mismatch, and a path:line witness—do not silently correct without logging.
- Prose Coverage Mapping: table present in plan/instantiated; Implemented-by column present (accepted headers in §1.5); entries reference real task IDs (no missing/duplicate IDs; ranges forward/same prefix).
- Clean Table: write commands so they fail on matches (e.g., `! rg 'TODO|FIXME|XXX' src/...`) instead of “always succeed” patterns.

## 9) Validate with the Linter
- Run via runner: `uv run python ai_task_list_linter_v1_9.py PROJECT_TASKS.md --require-captured-evidence`.
- Fix reported violations; rerun until exit code 0.

### Common linter failures to avoid
- Missing `$` on command lines in Baseline/STOP/Global sections.
- Missing `# cmd:` / `# exit:` headers in evidence blocks.
- No `$ {search_tool} …` line in Preconditions for a task.
- Using `grep` in code blocks when `search_tool=rg`.
- Using `.venv/bin/python`, bare `python`, or `pip install` in `$` lines when `runner=uv`.

## 10) Reality Check (Beyond Lint)
- Prefer real executions over stubs; avoid “NOT RUN” except where truly planned.
- If execution is impossible, clearly mark blocking reasons and leave status ≠ COMPLETE.
- Keep outputs truthful; do not fabricate.

## 11) Quick Checklist Before Delivering
- For design/AI output (plan, no real evidence yet):
  - [ ] YAML front matter filled; mode = plan.
  - [ ] Required headings present (unchanged from template).
  - [ ] Baseline/STOP/Global sections structurally present (evidence placeholders allowed).
  - [ ] Tasks have paths arrays, Preconditions with real `$ {search_tool} …` commands, TDD/STOP sections.
  - [ ] Prose Coverage Mapping table present (required in plan/instantiated) with major requirements mapped or explicitly out-of-scope; Implemented-by column present.
  - [ ] Drift ledger started if any mismatches are known.
- For executed/human+CI artifact (real evidence):
  - [ ] YAML front matter filled; mode = instantiated.
  - [ ] Required headings present; naming rule stated once (per spec).
  - [ ] Baseline snapshot + tests have real outputs with headers and $-prefixed commands.
  - [ ] Tasks have paths arrays, Preconditions `$ {search_tool} …`, TDD/STOP sections.
  - [ ] At least one behavior-level test (with test name + behavior) referenced for each behavior-changing task.
  - [ ] STOP evidence blocks present with labeled sections, `# cmd/# exit`, real output; checkboxes set if status is COMPLETE.
  - [ ] Phase unlock artifact commands `$ cat …` + `$ rg` scan, `$`-prefixed.
  - [ ] Global scan commands present; uv import hygiene commands included.
  - [ ] No placeholders or pseudo-placeholders remain.
  - [ ] Prose Coverage Mapping passes lint: Implemented-by column present; all referenced task IDs exist and are unique.
  - [ ] Drift ledger updated with any known mismatches.
  - [ ] Linter passes with `--require-captured-evidence`.
