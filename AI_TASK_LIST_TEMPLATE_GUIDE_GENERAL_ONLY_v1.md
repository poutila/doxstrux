# AI_TASK_LIST_TEMPLATE — General-Only Guide

**Purpose**: Help you instantiate the general-only task list template without reintroducing drift.

---

## 1) What makes a task list “general-only”

A general-only template must contain:
- no project names
- no repo paths
- no project-specific environment variables
- no assumptions about language tooling beyond “single runner principle”

If you need a project-specific detail, it belongs in the instantiated `PROJECT_TASKS.md`, not the template.

---

## 2) Instantiation procedure (must follow)

1. Copy `AI_TASK_LIST_TEMPLATE_GENERAL_ONLY_v1.md` to `PROJECT_TASKS.md`.
2. Replace all `[[PH:...]]` placeholders with real values.
3. Run the placeholder scan; it must return zero:
   ```bash
   grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && exit 1 || true
   ```
4. Execute Phase 0 and paste outputs.
5. Only then write Phase 1+ tasks.

---

## 3) Runner selection (single runner principle)

Pick exactly one canonical runner and use it everywhere.

Examples:
- Python + uv: `RUNNER_PREFIX="uv run"` and tests use `uv run pytest ...`
- Python + poetry: `RUNNER_PREFIX="poetry run"`
- Node: `RUNNER_PREFIX="npm run"` or `pnpm` / `yarn`
- Go: runner is `go test ...` (no prefix)

Do not mix styles in the task list.

---

## 4) Evidence anchors (required)

Minimum viable evidence:
- tool versions (runner + runtime)
- baseline tests output
- grep/file excerpts for “exists/wired” claims

If evidence is missing, the claim does not exist in the task list.

---

## 5) Avoid common drift regressions

- Do not reintroduce bracket placeholders like `[PROJECT]`.
- Do not embed repo paths in the template.
- Do not include “skip if missing tool” in hard gates; if a tool is optional, state it as policy.

End of guide.
