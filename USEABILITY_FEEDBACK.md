# USEABILITY_FEEDBACK.md

**Tester**: Claude (Opus 4.5)
**Date**: 2025-12-16
**Target prose document**: `PYDANTIC_SCHEMA.md` (~2000 lines)
**Framework evaluated**: `files (9)/` AI Task List Framework (Spec v1.9, Schema 1.7)

---

## Executive Summary

The AI Task List Framework is a well-engineered, rigorous system for converting prose into lintable task lists. However, applying it to `PYDANTIC_SCHEMA.md` reveals significant friction for complex, exploratory implementation plans. The framework excels at enforcement but struggles with the reality of iterative design documents.

**Verdict**: The framework provides value for **simple, well-defined implementation tasks** but introduces **significant overhead** for complex, multi-phase design documents like `PYDANTIC_SCHEMA.md`. Recommended for mature, stable plans; not recommended for exploratory or research-heavy phases.

---

## Goal Assessment

| Goal | Status | Assessment |
|------|--------|------------|
| 1. Does not drift | ⚠️ Partial | Strong structural enforcement, but prose→task mapping is manual and error-prone for large documents |
| 2. Is as close to reality as possible | ⚠️ Partial | Evidence requirements are good, but "plan mode" allows placeholders that may never be validated |
| 3. Can be validated against a specification with a linter | ✅ Achieved | The linter is comprehensive (1200+ lines), deterministic, and well-tested |
| 4. Has TDD, No Weak Tests, uv enforcement, Clean Table, import rules, rg use baked in | ✅ Achieved | All governance rules are enforced mechanically |
| 5. Reduces iteration loops for creating an AI task list | ❌ Not achieved | High overhead increases iteration loops, especially for complex prose |

---

## What Worked Well

### 1. Deterministic Linter (Excellent)

The linter (`ai_task_list_linter_v1_9.py`) is the standout component:
- **stdlib only**: No dependencies, portable
- **Clear error messages**: Rule IDs with actionable messages
- **Exit codes**: Well-defined (0=pass, 1=fail, 2=error)
- **JSON output**: Machine-readable for CI integration
- **1200+ lines of thorough validation**: Covers edge cases

**Example from testing**: Running the linter on canonical examples provides immediate, actionable feedback:
```
canonical_examples/negatives/plan_preconditions_placeholder.md:95:R-ATL-D2:Task 1.1 Preconditions must not use [[PH:SYMBOL_CHECK_COMMAND]] in plan mode. Use a real rg command.
```

### 2. Three-Mode Lifecycle (Good Concept)

The `template → plan → instantiated` lifecycle is conceptually sound:
- **Template**: Scaffolding with full placeholders
- **Plan**: Real commands, evidence placeholders allowed
- **Instantiated**: No placeholders, real evidence required

This allows incremental progress toward a fully-validated task list.

### 3. Governance Baked In (Excellent)

The framework mechanically enforces:
- TDD structure (RED/GREEN/VERIFY)
- No Weak Tests checklist (4 items)
- Clean Table checklist (5 items)
- Runner consistency (`uv run` everywhere)
- Import hygiene (`from ..` and `import *` checks)
- `rg` as search tool (no `grep`)

This eliminates "ceremony drift" where governance is stated but not verified.

### 4. Prose Coverage Mapping (Good Idea)

Requiring a mapping table from prose requirements to task IDs is valuable:
- Forces explicit coverage analysis
- Makes gaps visible
- Enables traceability

### 5. Canonical Examples (Helpful)

Having positive and negative examples in `canonical_examples/` is excellent for understanding the spec:
- `example_plan.md`: Shows valid plan-mode structure
- `example_instantiated.md`: Shows full evidence requirements
- `negatives/`: Shows what fails and why

---

## What Did NOT Work Well

### 1. Massive Overhead for Complex Documents

`PYDANTIC_SCHEMA.md` has:
- **7 major phases** (0, A, B1, B1.5, B2, C, D)
- **~25 distinct tasks** implied across milestones
- **~50 code examples** (Python snippets, bash commands)
- **~15 decision tables**
- **Complex inter-phase dependencies**

Converting this to the framework requires:
- Creating 25+ `### Task N.M` sections
- Each with: Paths array, Preconditions, TDD Steps 1-3, STOP block
- Each STOP block with 9 checklist items
- Each task with evidence placeholders

**Estimated output size**: Converting PYDANTIC_SCHEMA.md would produce a 3000+ line task list.

### 2. Framework Assumes "Action" Tasks, Not "Discovery" Tasks

`PYDANTIC_SCHEMA.md` Phase 0 says:

> **Goal:** Verify assumptions about parser output shape before locking schema.
> **Estimated Time:** 2-4 hours

This is exploratory work. The framework structure doesn't fit:
- What are the TDD steps for "run a discovery script and review output"?
- How do you write a RED test for "verify assumptions"?
- What is the "minimal implementation" for an investigative task?

The TDD structure (`RED → IMPLEMENT → GREEN`) assumes you know what to build. Discovery phases don't have this property.

### 3. Placeholder Syntax is Verbose and Error-Prone

Every placeholder must match `[[PH:[A-Z0-9_]+]]`. For a large document:
- Manual placeholder creation is tedious
- Typos are easy (`[[PH:OUPUT]]` vs `[[PH:OUTPUT]]`)
- AI-generated placeholders may drift from template names

### 4. STOP Block Structure is Repetitive

Every non-Phase-0 task requires:
```markdown
### STOP — Clean Table
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated
```

For 25 tasks, this is 225 checklist items to manage. In practice, this becomes "check all boxes" ceremony rather than genuine verification.

### 5. Prose Coverage Mapping is Manual and Fragile

For `PYDANTIC_SCHEMA.md`, I would need to:
1. Identify ~50 prose requirements
2. Map each to task IDs
3. Ensure task IDs exist and are unique
4. Update mapping when tasks change

The linter validates that referenced tasks exist, but cannot validate that the mapping is **complete** or **correct**. This is a significant gap for the "no drift" goal.

### 6. Evidence Capture is Manual and Unverifiable

The framework requires pasting command output:
```bash
# cmd: uv run pytest -q
# exit: 0
5 passed in 0.42s
```

But as the spec admits:
> Linting cannot cryptographically prove provenance; it enforces structure and presence of output

This means evidence can be:
- Copy-pasted from old runs
- Fabricated entirely
- Outdated (code changed after evidence capture)

For `PYDANTIC_SCHEMA.md`, which spans weeks of work, evidence staleness is a real concern.

### 7. Path Array Naming Convention is Awkward

```bash
TASK_1_2_PATHS=(
  "src/doxstrux/markdown/output_models.py"
)
```

For a task like "Add Metadata + Security models" affecting 5+ files, this becomes:
```bash
TASK_B1_0_PATHS=(
  "src/doxstrux/markdown/output_models.py"
  "tests/test_output_models_minimal.py"
  "tests/test_output_models_empty.py"
  "tests/test_parser_output_schema_conformance.py"
  "tools/export_schema.py"
)
```

The naming (`TASK_B1_0_PATHS`) is invalid because task IDs must be `N.M` (numeric). The framework doesn't support semantic phase names like "B1".

### 8. No Support for Conditional/Optional Tasks

`PYDANTIC_SCHEMA.md` has:
> **Phase 0.2: Key Path Lister (DELETED)**
> **Phase 0.3: Plugin Policy Verification (DEFERRED to Milestone B)**

The framework has no mechanism for:
- Deleted tasks
- Deferred tasks
- Conditional tasks (run only if X)
- Optional tasks

---

## Applying the Framework to PYDANTIC_SCHEMA.md (Simulation)

I mentally simulated using the framework to convert PYDANTIC_SCHEMA.md. Here's what would happen:

### Step 1: Run the Orchestrator Prompt

I would paste `PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md` and the entire `PYDANTIC_SCHEMA.md` into Claude.

**Problem**: PYDANTIC_SCHEMA.md is ~2000 lines. The orchestrator prompt is ~200 lines. Combined with context, this approaches context limits.

### Step 2: AI Generates Initial Plan

The AI would produce a task list with:
- Phase 0 tasks for discovery
- Phase A tasks for minimal schema
- Phase B1, B1.5, B2 tasks for expansion
- Phase C, D tasks for validation/CI

**Problem**: Task IDs would be numeric (1.1, 1.2...) but the prose uses letters (A, B1, B1.5). This creates a mapping challenge.

### Step 3: Prose Coverage Mapping

I would need to create:
```markdown
| Prose requirement | Source | Implemented by Task(s) |
|-------------------|--------|------------------------|
| Discover parser shape | PYDANTIC_SCHEMA.md Phase 0.1 | 1.1 |
| Security field verification | PYDANTIC_SCHEMA.md Phase 0.1.1 | 1.2 |
| Add Pydantic dependency | Milestone A Task A.1 | 2.1 |
| Create minimal models | Milestone A Task A.2 | 2.2, 2.3 |
... (50+ rows)
```

**Problem**: This is substantial manual work with no automation. The framework provides no tooling to extract requirements from prose.

### Step 4: Linter Validation

Running `uv run python ai_task_list_linter_v1_9.py PYDANTIC_SCHEMA_TASKS_plan.md` would likely produce 10-20 errors on first attempt:
- Missing TDD headings
- Missing STOP blocks
- Missing Preconditions
- Placeholder format issues

**Problem**: Each error requires manual fix, then re-lint. High iteration count.

### Step 5: Evidence Instantiation

Converting from plan → instantiated mode requires running commands and pasting output.

**Problem**: `PYDANTIC_SCHEMA.md` tasks involve:
- Creating Python files
- Running pytest
- Checking schema exports
- Validating 620+ fixtures

This is **days of work** to instantiate, not a quick pass.

---

## Suggestions for Improvement

### 1. Add "Research/Discovery" Task Type

Create a variant task structure for exploratory phases:
```markdown
### Task 0.1 — Discover parser shape (RESEARCH)

**Objective**: Verify assumptions about parser output shape.

**Artifacts**:
- `tools/discovery_output/all_keys.txt`
- `tools/discovery_output/sample_outputs.json`

**Completion criteria**:
- [ ] Discovery script ran without error
- [ ] Output files exist and are non-empty
- [ ] Key gaps documented in Drift Ledger

**Evidence**:
```bash
$ uv run python tools/discover_parser_shape.py
...
```
```

This removes the TDD structure for tasks where it doesn't apply.

### 2. Support Semantic Phase Names

Allow task IDs like `A.1`, `B1.1`, `B1.5.1` instead of only numeric `N.M`:
```yaml
task_id_format: "semantic"  # or "numeric" (default)
```

### 3. Provide a Prose Extractor Tool

Add `tools/extract_requirements.py` that uses heuristics to identify requirements from prose:
- Lines starting with "MUST"
- Items in tables with "Required" column
- Checklist items
- Phase/Milestone headings

Output a draft coverage mapping that can be manually refined.

### 4. Support Task State Beyond Status

Add explicit support for:
```markdown
**State**: DEFERRED to Phase B  # or DELETED, OPTIONAL, CONDITIONAL
```

### 5. Reduce STOP Block Verbosity

Allow a "checklist profile" to reduce repetition:
```yaml
ai_task_list:
  checklist_profile: "python_tdd"  # includes standard No Weak Tests + Clean Table
```

Then tasks can reference the profile instead of repeating 9 items.

### 6. Add Evidence Freshness Metadata

Include timestamp requirements:
```bash
# cmd: uv run pytest -q
# exit: 0
# ts_utc: 2025-12-16T10:30:00Z
# commit: abc123
5 passed
```

The linter could warn if evidence is older than N days.

### 7. Support Hierarchical Dependencies

Allow explicit inter-phase dependencies:
```yaml
phases:
  A:
    depends_on: ["0"]
  B1:
    depends_on: ["A"]
  B1.5:
    depends_on: ["B1"]
```

### 8. Provide a "Dry Run" Mode for Large Documents

Add `--dry-run` to the orchestrator that produces:
- Estimated task count
- Estimated output size
- Identified requirements (no full generation)

This helps assess effort before committing.

---

## Overall Value Assessment

### Value for PYDANTIC_SCHEMA.md Specifically

| Aspect | Score | Notes |
|--------|-------|-------|
| Time to produce plan-mode task list | 2/5 | 4-8 hours of manual work |
| Time to produce instantiated list | 1/5 | Days, requiring actual implementation |
| Drift prevention | 3/5 | Structural drift prevented; semantic drift still possible |
| Confidence in completeness | 2/5 | Manual mapping doesn't guarantee coverage |
| CI integration value | 4/5 | Once instantiated, excellent for regression |
| Developer experience | 2/5 | High ceremony, repetitive structure |

### Value for Simpler Projects

For a straightforward feature with 3-5 tasks, the framework would score higher:
- Clear structure forces good planning
- TDD enforcement catches test gaps
- Evidence requirements prevent "it works on my machine"

### Recommendation

**For PYDANTIC_SCHEMA.md**: Do not use the framework as-is. The overhead exceeds the benefit. Instead:
1. Use the governance principles (TDD, No Weak Tests, Clean Table) directly
2. Maintain a simpler checklist document
3. Use pytest markers and coverage tools for verification

**For future projects**: Consider the framework for:
- Feature implementations with well-defined scope
- Bug fix campaigns with regression tests
- Refactoring efforts with behavior preservation requirements

Avoid the framework for:
- Exploratory/research phases
- Large design documents with many unknowns
- Projects where the task structure may change significantly

---

## Detailed Findings Log

### Finding 1: Linter handles edge cases well

The linter correctly handles:
- Task 0.x exempt from TDD requirements (Phase 0 bootstrap)
- Comments in code blocks not counted as commands
- Captured evidence headers in labeled sections
- Multiple fenced code blocks per section

### Finding 2: Template is comprehensive but intimidating

The template (`AI_TASK_LIST_TEMPLATE_v6.md`) is 330 lines. For a new user, this is overwhelming. A "minimal template" option would help.

### Finding 3: Orchestrator prompt is well-designed but untested at scale

The `PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md` includes self-check steps:
- Spec compliance sweep
- Governance sweep
- Prose coverage sweep
- No synthetic reality check

However, for a 2000-line input like `PYDANTIC_SCHEMA.md`, the orchestrator may not complete all sweeps before output.

### Finding 4: Version metadata management is solid

The `COMMON.md` file centralizing version metadata prevents drift between spec/linter/template versions. This is a good pattern.

### Finding 5: Negative test fixtures are valuable but incomplete

The `canonical_examples/negatives/` folder has 3 fixtures. More edge cases would improve confidence:
- Instantiated with remaining placeholders
- Invalid status value
- Duplicate task ID
- Malformed path array

---

## Conclusion

The AI Task List Framework is a serious, well-engineered attempt to solve a real problem: AI-assisted task generation often produces plans that drift from reality and cannot be validated. The framework addresses this with a deterministic linter and strict structural requirements.

However, for complex, multi-phase design documents like `PYDANTIC_SCHEMA.md`, the framework's rigidity becomes a liability. The overhead of converting prose to compliant task lists may exceed the effort of simply implementing the work directly.

The framework would benefit from:
1. Flexible task types (implementation vs. research)
2. Reduced boilerplate for common patterns
3. Better tooling for prose extraction
4. Support for semantic phase names

Until these improvements are made, the framework is best suited for smaller, well-scoped implementation tasks where the structure provides discipline without overwhelming overhead.

---

**End of Feedback**
