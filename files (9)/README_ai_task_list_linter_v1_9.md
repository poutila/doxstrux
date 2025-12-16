# AI Task List Linter

Deterministic linter for AI Task Lists (modes: template/plan/instantiated). Code filename: `ai_task_list_linter_v1_9.py`. Versions/schema: see COMMON.md §Version Metadata. <!-- See COMMON.md §Version Metadata -->

## What this framework is for
- **Specification**: `AI_TASK_LIST_SPEC_v1.md` (see COMMON.md for versions/schema) — contract for headings, evidence, runner/import hygiene, Clean Table, TDD/STOP gates.
- **Template**: `AI_TASK_LIST_TEMPLATE_v6.md` — starting point with required sections/placeholders.
- **Linter**: `ai_task_list_linter_v1_9.py` — stdlib-only, deterministic enforcement (no network/mutation).
- **Manuals/Docs**: `USER_MANUAL.md`, `AI_ASSISTANT USER_MANUAL.md`, `COMMON.md` for shared rules, plus `INDEX.md` for orientation (planning docs in `task_list_archive/`).
- **Goal**: produce task lists that (1) don’t drift, (2) stay close to reality, (3) are lintable, (4) bake in governance (TDD, No Weak Tests, Clean Table, runner/import/search rules), and (5) reduce iteration loops.

## Enforcement Features

**Three modes** (see COMMON.md §Mode Definitions):
- `mode: template` — placeholders allowed (commands and evidence); generic scaffolds.
- `mode: plan` — real commands required; evidence placeholders allowed.
- `mode: instantiated` — no placeholders anywhere; real evidence required.

**Baseline enforcement**:
- Template/plan: fenced Evidence with `[[PH:OUTPUT]]`, Baseline tests fenced block required.
- Instantiated: $-prefix enforced; non-empty output required after each command.
- STOP — Phase Gate: required checklist items enforced.
- Prose Coverage Mapping: table with Implemented-by column required in plan/instantiated.

**Command line enforcement** (actual `$` lines required, not comments):
- Import hygiene (R-ATL-063): `$ rg 'from \.\.'` and `$ rg 'import \*'` command lines.
- Phase Unlock scan (R-ATL-050): `$ cat > .phase-N.complete.json` and `$ rg` command lines.
- Runner/search_tool: `$ uv sync` / `$ uv run` required in code blocks; grep forbidden when `search_tool=rg`.

**Status and checklist enforcement**:
- Single status value required per task (`📋 PLANNED`, `⏳ IN PROGRESS`, `✅ COMPLETE`, `❌ BLOCKED`).
- `✅ COMPLETE` in instantiated mode requires all No Weak Tests + Clean Table checkboxes checked.
- STOP evidence blocks required; missing fenced block fails lint.
- Phase unlock commands must target `.phase-N.complete.json` (suffix enforced).

**Validation suite**:
- `canonical_examples/example_template.md` (template) — lint passes.
- `canonical_examples/example_plan.md` (plan) — lint passes.
- `canonical_examples/example_instantiated.md` (instantiated) — lint passes with `--require-captured-evidence`.
- See `VALIDATION_SUITE.md` for full test list.

## Usage Examples

**Phase Unlock Artifact** (must be actual `$` command lines):
```bash
$ cat > .phase-0.complete.json << EOF
{"phase": 0}
EOF

$ if rg '\[\[PH:' .phase-0.complete.json; then
>   echo "ERROR: placeholders found in artifact"
>   exit 1
> fi
```

**Import hygiene** (must be actual `$` command lines):
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

Comments containing these patterns do NOT satisfy the requirement.

## Run

```bash
# Standard lint
uv run python ai_task_list_linter_v1_9.py PROJECT_TASKS.md

# With captured evidence header enforcement
uv run python ai_task_list_linter_v1_9.py --require-captured-evidence PROJECT_TASKS.md

# Recommended for CI (instantiated lists)
uv run python ai_task_list_linter_v1_9.py --require-captured-evidence PROJECT_TASKS.md
```

Exit codes: 0 = pass, 1 = lint violations, 2 = usage/internal error

## Required YAML Front Matter

```yaml
ai_task_list:
  schema_version: "<see COMMON.md §Version Metadata>"    # Do not hard-code; use the value from COMMON.md
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
✅ schema_version enforcement: must match COMMON.md tuple; mismatches fail
✅ Spec search_tool consistency (MUST include, not MAY)
```

## Mode usage

1. Project-specific task lists with real commands: set `mode: "plan"`; keep evidence placeholders.
2. Generic scaffolds: keep `mode: "template"` with command placeholders.
3. Executed lists: use `mode: "instantiated"` with real evidence; no placeholders.
4. Ensure import hygiene and Phase Unlock scans are actual `$` command lines (not comments).
5. Add `## Prose Coverage Mapping` (plan/instantiated): missing/empty table is an error.

## Design Philosophy

The linter verifies that required patterns appear in actual `$` command lines inside fenced code blocks, not just anywhere in the section text. This prevents comment/prose-only compliance.

## Remaining Reality Limitations

As noted in external validation:
- A deterministic linter cannot prove outputs were actually produced
- True "reality verification" requires execution/evidence-capture tooling
- The spec acknowledges headers as "not cryptographically verifiable"

The recommended operational practice is to make `--require-captured-evidence` mandatory in CI for instantiated task lists.
