# COMMON.md — Shared Framework Definitions

## §Version Metadata
- Spec: v1.9 (schema_version: "1.7")
- Linter: v1.9 (`ai_task_list_linter_v1_9.py`)
- Template: v6.0

## §SSOT Hierarchy
1) Spec (authoritative contract)
2) Linter (implements the spec; if spec and linter diverge, fix the linter)
3) Template, manuals, orchestrator
4) Prose (lowest; must not contradict 1–3)

## §Mode Definitions
- `template`: placeholders allowed (commands and evidence); used for generic scaffolds.
- `plan`: real commands required; evidence/output placeholders allowed; runner/search_tool/import-hygiene rules apply.
- `instantiated`: no placeholders anywhere; real evidence required.
- Lifecycle: template → plan → instantiated.

## §Runner Rules (uv)
- Required: `$ uv sync` and `$ uv run ...` as command lines in code blocks.
- Forbidden on `$` lines: `.venv/bin/python`, `python -m ...`, `pip install ...`.
- Runner prefix: enforce `runner_prefix` on runner-managed tools (`pytest`, `python`, `mypy`, `ruff`, `black`, `isort`).

## §Import Hygiene (Python/uv)
- Required checks (as `$` commands):
  - `$ if rg 'from \.\.' src/; then exit 1; fi` (no multi-dot relative imports)
  - `$ if rg 'import \*' src/; then exit 1; fi` (no wildcard imports)

## §Gate Patterns
- Recommended: fail on match (`! rg 'pattern' ...` or `if rg 'pattern' ...; then exit 1; fi`).
- Anti-patterns: `rg ... && exit 1 || echo/true` (always passes).

## §Placeholder Protocol
- Format: `[[PH:NAME]]`, NAME = `[A-Z0-9_]+`.
- Pre-flight regex: `rg '\[\[PH:[A-Z0-9_]+\]\]' <file>`.

## §Status Values
- Allowed: 📋 PLANNED | ⏳ IN PROGRESS | ✅ COMPLETE | ❌ BLOCKED.
- `✅ COMPLETE` (instantiated) requires STOP checkboxes checked.

## §Evidence Requirements
- Required sections: Baseline Evidence, Baseline tests, STOP evidence, Global Clean Table evidence (template/plan: placeholders allowed; instantiated: real output).
- Evidence blocks must be fenced; command lines start with `$` (plan and instantiated).
- Non-empty output required after `$` commands; captured headers optional via `--require-captured-evidence` (# cmd/# exit).

## §Prose Coverage Mapping
- Required in `plan` and `instantiated` modes: include a `## Prose Coverage Mapping` section with a markdown table (header + at least one data row) mapping prose requirements to tasks or marking them out-of-scope.
- `template` mode: recommended only.
