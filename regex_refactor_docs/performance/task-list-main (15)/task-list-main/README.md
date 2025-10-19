# Detailed Task List Template

This repository packages the version 2.0.0 task-list template together with renderers, validators, and JSON schemas. The YAML template is the **single source of truth**. JSON and Markdown outputs are generated artifacts that must stay in sync with the YAML and should never be edited directly. For the full contract, field glossary, and authoring guidance, read [USER_MANUAL.md](USER_MANUAL.md).

## Quick start

```bash
# 0. Install the CLI tools
pip install -e .

# 1. Render YAML → JSON + Markdown with all validators enabled
tasklist-render --strict

# 2. Validate the rendered JSON against the packaged schema (redundant safety net)
python -m jsonschema \
  -i DETAILED_TASK_LIST_template.json \
  src/tasklist/schemas/detailed_task_list.schema.json

# 3. Confirm generated artifacts are committed
git diff --exit-code DETAILED_TASK_LIST_template.json DETAILED_TASK_LIST_template.md

# 4. (Optional) Inspect metadata and hashes
tasklist-render --meta

# 5. (Optional) Extract placeholders or bootstrap from prose
tasklist-render-template -t DETAILED_TASK_LIST_template.yaml --list-placeholders
tasklist-prose2yaml docs/refactor_brief.md -o drafts/DETAILED_TASK_LIST_auto.yaml
```

### Draft vs. release profiles

- **Draft profile:** placeholder strings beginning with `TBD_` are permitted while collecting requirements. Always run `tasklist-render --strict` locally to ensure no `{{…}}` tokens remain.
- **Release profile:** CI fails if any `TBD_` value survives in required fields. Replace every placeholder with concrete values before merging.

## Validation pipeline at a glance

Running `tasklist-render --strict` performs the same checks that execute in CI:

1. Loads optional `.env` files so sensitive values can be provided without touching the template.
2. Renders JSON and Markdown from the YAML source and records render metadata (hashes, timestamps, schema version).
3. Fails if any template placeholders remain unresolved.
4. Enforces task ID monotonicity, gate uniqueness, command safety, and POSIX-relative path hygiene.
5. Writes SHA-256 digests for drift detection and runs JSON-schema validation.

The GitHub Actions workflow re-renders the artifacts, validates the JSON schema, checks hash alignment, rejects unsafe shell commands, and ensures the working tree remains clean. It also validates any `.phase-*.complete.json` artifacts against `src/tasklist/schemas/phase_complete.schema.json`.

## Additional resources

- [USER_MANUAL.md](USER_MANUAL.md) — authoritative field-by-field documentation for schema version 2.0.0.
- [`src/tasklist/schemas`](src/tasklist/schemas) — packaged JSON schemas (`detailed_task_list.schema.json`, `phase_complete.schema.json`).
- [`src/tasklist/render_task_templates.py`](src/tasklist/render_task_templates.py) — reference renderer used by `tasklist-render`.

For detailed troubleshooting steps, release checklists, and evidence requirements consult the manual.
