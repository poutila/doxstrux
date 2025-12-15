# AI Task List Linter v1.9 (code file name unchanged)

Deterministic linter for AI Task Lists (Spec v1.7; schema_version remains "1.6", adds `mode: plan`). Code filename unchanged (`ai_task_list_linter_v1_8.py`). <!-- See COMMON.md §Version Metadata -->

## What this framework is for
- **Specification**: `AI_TASK_LIST_SPEC_v1.md` (v1.7; schema_version 1.6; plan mode) — contract for headings, evidence, runner/import hygiene, Clean Table, TDD/STOP gates.
- **Template**: `AI_TASK_LIST_TEMPLATE_v6.md` — starting point with required sections/placeholders.
- **Linter**: `ai_task_list_linter_v1_8.py` (v1.9 code) — stdlib-only, deterministic enforcement (no network/mutation).
- **Manuals/Docs**: `USER_MANUAL.md`, `AI_ASSISTANT USER_MANUAL.md`, `COMMON.md` for shared rules, plus `INDEX.md` for orientation (planning docs in `task_list_archive/`).
- **Goal**: produce task lists that (1) don’t drift, (2) stay close to reality, (3) are lintable, (4) bake in governance (TDD, No Weak Tests, Clean Table, runner/import/search rules), and (5) reduce iteration loops.

## What's Fixed in v1.9

**Plan mode added (Spec v1.7; schema_version 1.6 unchanged):**
- Accepts `mode: plan` (real commands, evidence placeholders).
- Template/plan Baseline: fenced Evidence with `[[PH:OUTPUT]]`, Baseline tests fenced block required.
- Instantiated Baseline: $-prefix enforced; existing non-empty/output checks retained.
- STOP — Phase Gate: required checklist items enforced.
- Prose Coverage Mapping: presence/structure check in plan/instantiated modes (loud errors when missing/malformed).

**UV/import hygiene/comment compliance (carried forward):**
- Import hygiene (R-ATL-063): **$ command line required** (no comments).
- Phase Unlock scan (R-ATL-050): **$ rg command line required**; `.phase-N.complete.json` suffix enforced.
- Runner/search_tool: **$ uv sync / $ uv run** required in code blocks; grep forbidden when `search_tool=rg`.
- Checklist/status tightening: single status required; COMPLETE needs checked boxes.
- Gate patterns: recommended fail-on-match (`! rg …` or `if rg …; then exit 1; fi`); linter enforces presence, not shell flow.

## Key Changes

**R-ATL-050: Phase Unlock Artifact (UPDATED)**

Must have actual `$` command lines, not comments:
```bash
$ cat > .phase-0.complete.json << EOF
{"phase": 0}
EOF

$ if rg '\[\[PH:' .phase-0.complete.json; then
>   echo "ERROR: placeholders found in artifact"
>   exit 1
> fi
```

Comments like `# rg '\[\[PH:' ...` do NOT satisfy the requirement.

**Migration**
- If you have a project-specific task list with real commands and `mode: "template"`, flip to `mode: "plan"` and keep evidence placeholders.
- Keep `mode: "template"` only for generic scaffolds (command placeholders intact).
- Executed lists use `mode: "instantiated"` with real evidence and no placeholders.

**Validation suite (examples)**
- `canonical_examples/example_template.md` (template) — lint passes.
- `canonical_examples/example_plan.md` (plan) — lint passes.
- `canonical_examples/example_instantiated.md` (instantiated) — lint passes with `--require-captured-evidence`.

See `VALIDATION_SUITE.md` for full test list (including negatives, doc-sync check, perf/backcompat notes).

**Status + completion tightening (plan mode accepted)**

- Each task must use a single status value (`📋 PLANNED`, `⏳ IN PROGRESS`, `✅ COMPLETE`, `❌ BLOCKED`).
- If status is `✅ COMPLETE` in instantiated mode, all No Weak Tests + Clean Table checkboxes must be checked.
- STOP evidence blocks are required even if the “Evidence/paste” marker is removed; missing fenced block fails lint.
- Phase unlock commands must target `.phase-N.complete.json` (suffix enforced).
- For runner=uv, `$ uv sync` and `$ uv run ...` must appear as command lines inside fenced code blocks (prose mentions no longer count).

**R-ATL-063: Import hygiene (UPDATED)**

Must have actual `$` command lines, not comments:
```bash
$ if rg 'from \.\.' src/; then
>   echo "ERROR: multi-dot relative import found"
>   exit 1
> fi
$ if rg 'import \*' src/; then
>   echo "ERROR: wildcard import found"
>   exit 1
> fi
```

Comments like `# rg 'from \.\.' ...` do NOT satisfy the requirement.

**R-ATL-D4: search_tool (FIXED)**

Spec now consistently says `search_tool` is REQUIRED (removed "MAY include" language).

## Run

```bash
# Standard lint
uv run python ai_task_list_linter_v1_8.py PROJECT_TASKS.md

# With captured evidence header enforcement
uv run python ai_task_list_linter_v1_8.py --require-captured-evidence PROJECT_TASKS.md

# Recommended for CI (instantiated lists)
uv run python ai_task_list_linter_v1_8.py --require-captured-evidence PROJECT_TASKS.md
```

Exit codes: 0 = pass, 1 = lint violations, 2 = usage/internal error

## Required YAML Front Matter

```yaml
ai_task_list:
  schema_version: "1.6"    # Must be exactly "1.6"
  mode: "plan"             # or "template" / "instantiated"
  runner: "uv"
  runner_prefix: "uv run"  # REQUIRED; used for runner enforcement
  search_tool: "rg"        # REQUIRED; rg vs grep enforcement
```

## Test Results

```
✅ Template v6 passes (template mode)
✅ Plan example passes
✅ Instantiated example passes (--require-captured-evidence)
✅ Comment compliance REJECTED (import hygiene patterns in comments)
✅ Comment compliance REJECTED (Phase Unlock scan in comments)
✅ Old schema versions rejected (e.g., 1.5 rejected; requires 1.6)
✅ Spec search_tool consistency (MUST include, not MAY)
```

## Migration to v1.9 (plan mode)

1. For project-specific task lists with real commands: set `mode: "plan"`; keep evidence placeholders.
2. For generic scaffolds: keep `mode: "template"` with command placeholders.
3. For executed lists: use `mode: "instantiated"` with real evidence; no placeholders.
4. Ensure import hygiene and Phase Unlock scans are actual `$` command lines (not comments).
5. Add `## Prose Coverage Mapping` (plan/instantiated): missing/empty table is an error.

## Design Philosophy

v1.8 closes the "comment compliance" loophole identified by strict validation:

> "Some enforcement can be satisfied via comments/prose because the linter checks for string presence in section text rather than requiring them as $ command lines."

Now the linter verifies that required patterns appear in actual `$` command lines inside fenced code blocks, not just anywhere in the section text.

## Remaining Reality Limitations

As noted in external validation:
- A deterministic linter cannot prove outputs were actually produced
- True "reality verification" requires execution/evidence-capture tooling
- The spec acknowledges headers as "not cryptographically verifiable"

The recommended operational practice is to make `--require-captured-evidence` mandatory in CI for instantiated task lists.
