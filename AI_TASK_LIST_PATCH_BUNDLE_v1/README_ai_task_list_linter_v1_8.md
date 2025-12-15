# AI Task List Linter v1.8

Deterministic linter for AI Task Lists (Spec v1.6).

## What's Fixed in v1.8

**Comment compliance loophole CLOSED:**

| Issue | Before v1.8 | After v1.8 |
|-------|-------------|------------|
| Import hygiene (R-ATL-063) | Comment with pattern passed | **$ command line required** |
| Phase Unlock scan (R-ATL-050) | Comment with `rg` passed | **$ rg command line required** |
| Spec search_tool (R-ATL-D4) | Said "MAY include" | **Fixed: MUST include** |
| STOP evidence marker deletion | Marker removal bypassed evidence checks | **Fenced evidence block required even if marker removed** |
| Phase unlock artifact suffix | `.phase-N.complete` accepted | **Requires `.phase-N.complete.json`** |
| Checklist completion status | Status not validated | **Single status required; COMPLETE needs checked boxes** |
| UV commands | Prose mention sufficed | **$ uv sync / $ uv run required in code blocks** |
| Baseline tests evidence | Not enforced | **Baseline tests block must have $ commands + output** |
| Gate patterns | Could succeed even on matches | **Use `! rg …` or `if rg …; then exit 1; fi` for gates** |

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

**Status + completion tightening**

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
  mode: "instantiated"     # or "template"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"        # REQUIRED (not optional)
```

## Test Results

```
✅ Template v6 passes
✅ Valid v1.6 document passes
✅ Comment compliance REJECTED (import hygiene patterns in comments)
✅ Comment compliance REJECTED (Phase Unlock scan in comments)
✅ Schema version 1.5 rejected (requires 1.6)
✅ Spec search_tool consistency (MUST include, not MAY)
```

## Migration from v1.7

1. Update `schema_version` to `"1.6"`
2. Ensure import hygiene patterns are actual `$` command lines (not comments)
3. Ensure Phase Unlock placeholder scan is actual `$ rg` command line (not comment)

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
