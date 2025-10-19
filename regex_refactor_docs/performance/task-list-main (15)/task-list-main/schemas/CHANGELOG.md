# Schema Changelog

All notable changes to task list schemas will be documented here.

**Format**: `[version] - YYYY-MM-DD`


## [2.1.0] - 2025-10-19 (Type-safe v2 refresh)

### Added
- `src/tasklist/schemas/phase_complete.schema.json` to validate `.phase-N.complete.json` artifacts with numeric counters and ISO 8601 completion timestamps.

### Changed
- Tightened `src/tasklist/schemas/detailed_task_list.schema.json` so hours, counts, and duration fields are numeric instead of strings.
- Promoted `metadata.schema_version` and embedded phase artifact versions to `"2.0.0"` to remove lingering v1 identifiers.
- Updated task and phase definitions to use `time_estimate_hours` numeric values.

### Validation
- Regenerated JSON/Markdown artifacts via `tasklist-render --strict` to sync drift and refresh `render_meta` hashes.

---

## [2.0.0] - 2025-10-19 (Document-centric schema alignment)

### Changed
- Updated `src/tasklist/schemas/detailed_task_list.schema.json` to advertise `model_version` 2.0.0 and keep metadata in lockstep with the
  document-centric layout.
- Set `metadata.schema_version` in all templates to `"2.0.0"` so YAML, JSON, and Markdown renders share the same schema identifier.

### Validation
- Re-rendered artifacts to refresh `render_meta` hashes and timestamps after the schema alignment.

---

## [1.1.0] - 2025-10-19 (100% Coverage Enhancements)

### Added
- **`render_meta` block** in JSON output (Phase 1)
  - `source_file`: Path to YAML source
  - `schema_version`: Version from YAML
  - `sha256_of_yaml`: SHA256 hash of source YAML
  - `rendered_utc`: ISO 8601 timestamp of render

- **`task_result.schema.json`** (Phase 2)
  - New schema for task execution results
  - Fields: task_id, status, stdout, stderr, return_code, duration_sec, timestamp, artifacts, meta

- **`post_rollback_criteria`** field in tasks (Phase 3)
  - Array of verification steps after rollback
  - Example: "Repository state matches HEAD~1", "All tests still pass"

- **Evidence directory structure** (Phase 4)
  - `evidence/logs/` - Execution logs
  - `evidence/results/` - Task result JSON files
  - `evidence/hashes/` - SHA256 verification hashes
  - `evidence/artifacts/` - Build outputs

### Changed
- **Markdown rendering** now includes YAML front matter (Phase 6)
  - Fields: phase, title, author, schema_version, rendered_utc, source_sha256
- **Markdown footer** includes render metadata (Phase 1)

### Tools
- Added `--meta` flag to `src/tasklist/render_task_templates.py` (Phase 9)
- Added `emit_task_result.py` for standardized result emission
- Auto-generate SHA256 hashes to `evidence/hashes/` on every render

---

## [1.0.0] - 2025-10-18

### Added
- Initial schema with meta, ai, tasks, gates
- `no_placeholders_string` validation pattern
- Strict `additionalProperties: false` enforcement

### Schema Fields
- **meta**: phase, title, summary, author, created_utc, updated_utc
- **ai**: role, objectives, constraints, stop_conditions, interaction_policy, runbook
- **tasks[]**: id, name, kind, impact, files, inputs, outputs, command_sequence, acceptance_criteria, blockers_if_missing, rollback
- **gates[]**: id, name, description, command, fix_on_failure

### Validation
- All required fields enforced
- Enum types for kind (code_change, test_change, doc_change, ops)
- Enum types for impact (P0, P1, P2)
- Enum types for status (success, failed, skipped)

---

## Versioning Policy

### Semantic Versioning
- **Major** (X.0.0): Breaking changes (require YAML rewrite)
- **Minor** (1.X.0): Additive changes (backward compatible)
- **Patch** (1.0.X): Clarifications, bug fixes, documentation

### When to Bump Version

**Bump MAJOR (X.0.0) when**:
- Removing required fields
- Changing field types incompatibly
- Renaming fields
- Changing enum values

**Bump MINOR (1.X.0) when**:
- Adding optional fields
- Adding new enum values
- Adding new schema files

**Bump PATCH (1.0.X) when**:
- Fixing documentation
- Clarifying descriptions
- Fixing typos in schema

### Update Procedure

1. **Edit YAML template**:
   ```bash
   nano DETAILED_TASK_LIST_template.yaml
   # Update schema_version field
   ```

2. **Update schema file**:
   ```bash
   nano src/tasklist/schemas/detailed_task_list.schema.json
   # Add/modify fields
   ```

3. **Document in CHANGELOG**:
   ```bash
   nano schemas/CHANGELOG.md
   # Add entry under new version
   ```

4. **Regenerate all formats**:
   ```bash
   tasklist-render --strict
   ```

5. **Validate**:
   ```bash
   python -m jsonschema \
     -i DETAILED_TASK_LIST_template.json \
     src/tasklist/schemas/detailed_task_list.schema.json
   ```

6. **Commit**:
   ```bash
   git add DETAILED_TASK_LIST_template.* src/tasklist/schemas/
   git commit -m "chore: bump schema version to X.Y.Z"
   ```

---

## Backward Compatibility

- **Renderer supports**: Up to 2 major versions back
- **Older JSON** with `schema_version < current` may trigger warnings
- **Always use latest** schema for new work
- **Breaking changes** require migration guide in this CHANGELOG

---

## Migration Guides

### 1.1.0 → 2.0.0

**Changes**: Replaced legacy `meta/ai/tasks/gates` layout with document-centric
`document/metadata/ci_gates/phases` model, enforced `render_meta` at the schema
level, and normalized task artifacts to POSIX-relative paths.

**Action required**:

- Promote YAML templates to `schema_version: "2.0.0"` before rendering.
- Ensure renderers write the new `render_meta` block and update
  `metadata.template_metadata.last_rendered_utc`.
- Flatten any remaining legacy `tasks` arrays into the appropriate phase
  entries.

**Benefits**:

- Single source of truth for project metadata improves automation ergonomics.
- CI gates and phase tasks now validate under the same schema, reducing drift.
- Render metadata is mandatory, enabling reliable SHA synchronization checks.

### 1.0.0 → 1.1.0

**Changes**: Added `render_meta` block, `post_rollback_criteria` field

**Action required**: None (backward compatible)

**Benefits**:
- SHA synchronization prevents stale renders
- Post-rollback verification improves safety
- Metadata visibility in all formats

**Optional**: Add `post_rollback_criteria` to tasks that have rollback steps.

---

**Last Updated**: 2025-10-19
**Maintained by**: Doxstrux Refactor Team
