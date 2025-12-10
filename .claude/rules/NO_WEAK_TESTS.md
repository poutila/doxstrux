# No Weak Tests Plan

## Goal
Refactor test suite to assert meaningful behavior (not just existence/import/smoke), reducing guesswork and increasing coverage confidence.

## Priorities
- Includes & prompts: assert functional rendering and spec alignment, not just file presence/length.
- Tools: assert outputs match spec/SSOT, not just that commands run.
- Linters: assert emitted codes/messages for known fixtures, not just imports.
- Orchestration: assert generated templates and workflows handle inputs/failures predictably.

## Refactors
1) Includes/Prompts
   - Render each thin prompt with minimal valid configs; assert no unresolved placeholders, required sections present, and include content matches spec-derived expectations.
   - Align include drift tests to spec sections (namespaces, tiers, constraints/failure/version/plan templates once codified).

2) Tools
   - `namespace_inventory.py`: assert CLI JSON matches spec-derived sets (already done).
   - `include_drift_checker.py`: add tests that feed known mismatches and expect failures.
   - `spec_section_extractor.py`: test extraction on sample text (headings, nested levels).
   - `tools_speksi_ai.py`: assert template paths resolve and contents include expected placeholders.

3) Linters
   - For framework/kernel linters, use fixtures that trigger specific codes/messages; assert exact outputs and exit codes, not just that they run.
   - Ensure all emitted rule IDs are covered by tests that expect those codes.

4) Orchestration
   - `speksi_prompt_builder`: render prompts with sample configs; assert output contains injected values and required includes; fail on missing required inputs.
   - `yaml_provider`: cover all kinds with real files/folders and failure cases.
   - `tools_aiassistant_linter`: add fixtures to assert AI-specific checks (TODO/FENCE/COMMENTARY) and subprocess delegation behavior.

5) Coverage Gate
   - Run full suite; avoid partial runs hitting fail-under. If needed, tweak per-test coverage expectations only after meaningful assertions are in place.

## Execution Steps
- Identify weak tests (existence/line-count/import-only) and replace with behavior assertions per above.
- Add fixtures (sample specs/plans/prompts) to drive deterministic outcomes.
- Update CI to run full pytest to satisfy coverage.
- Track rule/code coverage: ensure each emitted rule code has a test that triggers it.
