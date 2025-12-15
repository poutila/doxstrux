# AI Task List Framework — What It Is For

This folder contains a small, deterministic framework for writing and validating AI task lists so they are strict, repeatable, and runnable:

- **Specification**: `AI_TASK_LIST_SPEC_v1.md` defines the contract (v1.7; schema_version 1.6; adds plan mode) for task lists, including required headings, evidence rules, runner/import hygiene, Clean Table, and TDD/STOP gates.
- **Template**: `AI_TASK_LIST_TEMPLATE_v6.md` is the starting point for new task lists, with placeholders and required sections laid out.
- **Linter**: `ai_task_list_linter_v1_8.py` (v1.9 code) enforces the spec deterministically (no network, no mutation). It catches placeholder leaks, missing gates, runner/uv violations, weak evidence, and format bypasses.
- **Release Notes**: `README_ai_task_list_linter_v1_8.md` summarizes changes and usage.
- **User Manual**: `USER_MANUAL.md` explains how to author, lint, and operate with minimal iteration.

The goal is to produce AI task lists that:
1. **Don’t drift**: Required anchors, path arrays, and drift ledger rules keep structure honest.
2. **Stay close to reality**: Real command outputs are required in instantiated mode; `$` enforcement and uv/import hygiene reduce “comment compliance.”
3. **Are lintable**: One deterministic linter validates against the spec with clear exit codes.
4. **Bake in governance**: TDD steps, No Weak Tests, Clean Table, runner/uv enforcement, import hygiene, and `rg`/`grep` rules are first-class.
5. **Reduce iteration loops**: Strict structure and evidence requirements surface issues early; CI can run the linter (optionally with `--require-captured-evidence`) to block regressions.
