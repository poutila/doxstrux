# Schema Changelog

All notable changes to task list schemas will be documented here.

**Format**: `[version] - YYYY-MM-DD`

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
- Added `--meta` flag to `render_task_templates.py` (Phase 9)
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
   nano schemas/detailed_task_list.schema.json
   # Add/modify fields
   ```

3. **Document in CHANGELOG**:
   ```bash
   nano schemas/CHANGELOG.md
   # Add entry under new version
   ```

4. **Regenerate all formats**:
   ```bash
   python tools/render_task_templates.py --strict
   ```

5. **Validate**:
   ```bash
   python -m jsonschema \
     -i DETAILED_TASK_LIST_template.json \
     schemas/detailed_task_list.schema.json
   ```

6. **Commit**:
   ```bash
   git add DETAILED_TASK_LIST_template.* schemas/
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
