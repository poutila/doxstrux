# Feedback on FIX_1.md — Template vs. Practical Commands Fix Plan

**Evaluator**: Claude (Sonnet 4.5)  
**Date**: 2025-12-15  
**Overall Grade**: B+ (Solid plan with room for improvement)

---

## Executive Summary

**Verdict**: ✅ **APPROVE WITH MODIFICATIONS**

The fix plan directly addresses the core tension (template purity vs. practical commands) identified in the task list evaluation. The proposed `mode: plan` is a thoughtful solution, but the plan needs stronger guidance on mode selection, migration paths, and validation.

**Key Concerns**:
1. Adds complexity (3 modes instead of 2)
2. Missing mode selection decision tree
3. Incomplete migration guidance for existing docs
4. "Critical enumeration" needs concrete definition
5. Validation pass specifics needed

---

## Detailed Analysis by Section

### Fix #1: Add `mode: plan`

**Grade**: A- (Good solution, needs refinement)

#### What It Solves ✅

Resolves the template purity vs. practical commands tension by creating a middle ground:
- `template` = Generic, reusable (for framework maintainers)
- `plan` = Project-specific, pre-execution (for project teams)
- `instantiated` = Executed with evidence (final state)

This directly addresses 19/20 linter violations from the PYDANTIC_SCHEMA task list.

#### Strengths ⭐⭐⭐⭐

1. **Semantically clear**: Three distinct purposes for three modes
2. **Solves the right problem**: Eliminates forced choice between compliance and usefulness
3. **Maintains governance**: Runner, import hygiene, search_tool rules still apply in plan mode
4. **Backward compatible**: Existing template mode unchanged

#### Weaknesses ⚠️

1. **Complexity increase**: 3 modes vs. 2 modes (50% increase in lifecycle states)
2. **Mode selection ambiguity**: When to use template vs. plan not defined clearly
3. **Migration burden**: Existing "template with concrete commands" docs need mode flips
4. **Lifecycle transitions**: template → plan → instantiated (2 transitions instead of 1)

#### Critical Missing Piece 🔴

**No mode selection guidance provided**. Users will ask:
- "I'm starting a new project from prose. Which mode?"
- "I have a template-mode doc with real commands. Should I change it?"
- "When do I transition from plan to instantiated?"

**Required Addition**: Add explicit decision tree to spec:

```markdown
## Mode Selection Guide

### When to use `template`
- Creating a generic, reusable template for the framework library
- Template will be instantiated for multiple projects
- Commands must remain placeholders (no project-specific details)

**Example**: AI_TASK_LIST_TEMPLATE_v6.md (framework's own template)

### When to use `plan`
- Planning work for a specific project from prose/requirements
- Commands are project-specific but not yet executed
- Evidence slots are placeholders (work hasn't started)

**Example**: PYDANTIC_SCHEMA_tasks_template.md after generation from prose

### When to use `instantiated`
- Work is being executed or completed
- Evidence blocks contain real command outputs
- All placeholders replaced with actual values

**Example**: Production task lists in real projects with CI integration

### Lifecycle Flow
```
Framework Template (AI_TASK_LIST_TEMPLATE_v6.md)
  mode: template
  ↓ [Orchestrator generates from prose]
Project Plan (PYDANTIC_SCHEMA_tasks_plan.md)
  mode: plan
  ↓ [Execute tasks, capture evidence]
Executed Task List (PYDANTIC_SCHEMA_tasks_COMPLETE.md)
  mode: instantiated
```
```

#### Proposed Spec Changes

**Excellent** that fix plan mentions:
- Spec: Define plan mode rules
- Linter: Accept plan, enforce plan-specific rules
- Template: Note plan mode
- Orchestrator: Default to plan
- Manuals: Update guidance

**Missing**:
- **Migration guide** for existing docs
- **Mode transition triggers** (what event causes template→plan vs. plan→instantiated?)
- **Validation rules** for each transition

#### Alternative Considered (But Rejected)

**Option**: Add `template_style: "concrete"` flag instead of new mode

**Why rejected**: Less semantically clear. Plan mode better communicates intent.

**Verdict on Fix #1**: ✅ **APPROVE** but **REQUIRE** decision tree, migration guide, and transition rules

---

### Fix #2: Gate patterns

**Grade**: A (Straightforward correctness fix)

#### What It Fixes ✅

Ensures gates actually fail when matches are found, not always pass.

**Current problem**:
```bash
# BAD (always succeeds):
$ rg 'TODO' src/ && exit 1 || echo "clean"  # If no match, echo runs, exit 0

# GOOD (fails on match):
$ ! rg 'TODO' src/  # Exit 1 if matches found
$ if rg 'TODO' src/; then exit 1; fi  # Explicit fail on match
```

#### Strengths ⭐⭐⭐⭐⭐

1. **Critical correctness issue**: Gates that don't gate are dangerous
2. **Clear fix**: Replace all `&& exit 1 || true/echo` with `! rg` or explicit `if`
3. **Easy to verify**: Search for bad patterns, replace with good patterns

#### Weaknesses

None identified. This is a pure bug fix.

#### Missing Details

**Which files need updates?**
- ✅ Template: Mentioned
- ✅ Orchestrator: Mentioned
- ✅ Manuals: Mentioned
- ⚠️ **Spec examples**: Not explicitly mentioned (verify they use correct patterns)
- ⚠️ **Existing task lists**: Migration note needed

**Recommended addition**:
```bash
# Verification command to find bad patterns:
$ rg '&&\s*exit\s+1\s*\|\|' *.md  # Find all bad gate patterns
```

**Verdict on Fix #2**: ✅ **APPROVE** - straightforward and critical

---

### Fix #3: Placeholder vs. real commands (bridge)

**Grade**: B (Acceptable interim, needs clarity)

#### What It Does

Acknowledges tension until plan mode ships; notes that template currently requires placeholders.

#### Concerns ⚠️

1. **Timeline unclear**: When does plan mode ship? How long is "interim"?
2. **User guidance**: What should users do RIGHT NOW with existing docs?
3. **Transition plan**: What happens to "template with real commands" docs when plan mode is live?

#### Required Additions

**Immediate guidance for users**:
```markdown
## Interim Guidance (Until Plan Mode Ships)

If you have a task list in `mode: template` with concrete commands:

**Option A - Keep as template (accept violations)**:
- 20 violations expected
- Functionally correct
- Will convert to plan mode when available

**Option B - Add placeholder lines (achieve compliance)**:
- Add `[[PH:SYMBOL_CHECK_COMMAND]]` lines
- Passes linter
- Extra work now, needs cleanup later

**Option C - Wait for plan mode (recommended)**:
- Leave as-is
- Track fix plan progress
- Convert to plan mode in one pass when available

Choose Option C unless you need immediate linter pass for CI.
```

**Migration guidance when plan mode ships**:
```markdown
## Migration: Template → Plan Mode

1. Identify candidates:
   $ rg 'mode: "template"' --files-with-matches | xargs grep '$ rg' | grep -v '\[\[PH:'
   
2. For each file with concrete commands:
   - Change `mode: "template"` → `mode: "plan"`
   - Remove `[[PH:SYMBOL_CHECK_COMMAND]]` if added for compliance
   - Run linter with plan mode rules
   
3. Verify:
   $ uv run python linter.py --mode=plan <file>
```

**Verdict on Fix #3**: ⚠️ **APPROVE** but **REQUIRE** interim guidance and migration plan

---

### Fix #4: Prose Coverage and critical enumerations

**Grade**: B (Good principle, needs concrete definition)

#### What It Addresses

Risk that important lists (security paths, required rules, etc.) get truncated or summarized when generating task lists.

#### Strengths ⭐⭐⭐

1. **Identifies real risk**: AI might shorten critical lists
2. **Proposes solution**: Mark them for verbatim copying
3. **Right scope**: Highlights this in orchestrator/manuals

#### Critical Missing Piece 🔴

**No definition of "critical enumeration"**

Without concrete criteria, users won't know what to mark or orchestrator won't know what to preserve verbatim.

#### Required Additions

**Define in spec**:
```markdown
## Critical Enumerations

A **critical enumeration** is a list where:
1. Completeness is essential (missing items = missing requirements)
2. Order may matter (sequence dependencies)
3. Each item is independently verifiable (no summarization possible)

**Examples**:
- Security field paths that MUST be checked
- Required schema fields with specific names
- Compliance checklist items with exact wording
- File paths that must exist

**Mark in prose with**:
```markdown
<!-- CRITICAL_ENUM: security_paths -->
**Required security fields** (check each in test fixtures):
1. metadata.security.statistics.has_script
2. metadata.security.summary.has_dangerous_content
3. metadata.security.warnings
<!-- END_CRITICAL_ENUM -->
```

**Orchestrator instruction**:
"When encountering `<!-- CRITICAL_ENUM:label -->`, copy the enclosed list VERBATIM. Do not summarize, reorder, or truncate. Each item is independently required."
```

#### Missing Enforcement

**How to verify?**
- Orchestrator self-check should count critical enum items in prose vs. task list
- Linter could optionally validate if markers are preserved

**Verdict on Fix #4**: ⚠️ **APPROVE** but **REQUIRE** concrete definition with markers

---

### Fix #5: Runner normalization

**Grade**: B+ (Good for consistency)

#### What It Does

Ensures all framework examples use compliant commands (uv, rg).

#### Analysis

This is more of a **documentation consistency** issue than a functional issue. If examples show non-compliant patterns, users might copy them.

#### Recommended Approach

1. **Audit current examples**:
   ```bash
   $ rg '^\$ ' AI_TASK_LIST_*.md | grep -E '(python -m|pip install|\.venv|grep)' 
   ```

2. **Replace patterns**:
   - `python -m` → `uv run python -m` (if needed) or `uv run <tool>`
   - `pip install` → `uv add`
   - `.venv/bin/python` → `uv run python`
   - `grep` → `rg` (when search_tool is rg)

3. **Verify no legacy commands in examples**

#### Concern

**What about prose documents that users provide?**

If user's prose contains `python -m pytest`, should orchestrator:
- **Option A**: Convert to `uv run pytest` (enforce normalization)
- **Option B**: Preserve as-is (respect user's environment)
- **Option C**: Flag and ask user

**Recommendation**: Option A (normalize to runner), but document this behavior.

**Verdict on Fix #5**: ✅ **APPROVE** - straightforward consistency improvement

---

### Fix #6: Validation passes

**Grade**: A- (Critical, needs test specifications)

#### What It Proposes

After changes, validate with multiple scenarios:
- (a) Template scaffold
- (b) Plan artifact (e.g., PYDANTIC_SCHEMA after mode flip)
- (c) Instantiated sample

#### Strengths ⭐⭐⭐⭐⭐

1. **Test suite approach**: Prevents regressions
2. **Multiple scenarios**: Covers all modes
3. **Enforces governance**: Verifies gates/checks still work

#### Critical Missing Details 🔴

**No test specifications provided**

For each validation pass, need:
1. **Input**: Specific file or scenario
2. **Expected outcome**: Pass/fail with specific violations
3. **Acceptance criteria**: What makes the test pass?

#### Required Additions

**Validation Test Suite**:

```markdown
## Validation Pass Suite

### Test 1: Template Scaffold (AI_TASK_LIST_TEMPLATE_v6.md)

**Input**: Framework's generic template file  
**Expected**: Pass (exit 0) with mode: template  
**Validates**:
- All required headings present
- YAML correct with placeholders
- Command placeholders in Preconditions
- Output placeholders in evidence

**Command**:
```bash
$ uv run python ai_task_list_linter_v1_8.py AI_TASK_LIST_TEMPLATE_v6.md
# Expected: Exit 0, zero violations
```

### Test 2: Plan Artifact (PYDANTIC_SCHEMA_tasks_plan.md)

**Input**: Generated task list with mode: plan  
**Expected**: Pass (exit 0) with mode: plan  
**Validates**:
- Real commands in Preconditions (no command placeholders)
- Output placeholders in evidence
- Runner/import hygiene enforced
- Gate patterns use fail-on-match

**Command**:
```bash
$ uv run python ai_task_list_linter_v1_8.py PYDANTIC_SCHEMA_tasks_plan.md
# Expected: Exit 0, zero violations
```

### Test 3: Instantiated Sample (example_instantiated.md)

**Input**: Task list with real evidence  
**Expected**: Pass (exit 0) with mode: instantiated  
**Validates**:
- No placeholders anywhere
- Real evidence in STOP sections
- Captured headers present (if --require-captured-evidence)
- Status values valid

**Command**:
```bash
$ uv run python ai_task_list_linter_v1_8.py --require-captured-evidence example_instantiated.md
# Expected: Exit 0, zero violations
```

### Test 4: Negative Cases

**Test 4a: Plan mode with command placeholders (should fail)**
```bash
# Create plan_with_placeholders.md with [[PH:SYMBOL_CHECK_COMMAND]]
$ uv run python ai_task_list_linter_v1_8.py plan_with_placeholders.md
# Expected: Exit 1, R-ATL-D2 violations
```

**Test 4b: Template with bad gate patterns (should fail)**
```bash
# Template with `rg 'TODO' && exit 1 || echo "clean"`
$ uv run python ai_task_list_linter_v1_8.py template_bad_gates.md
# Expected: Exit 1 or warning (gate pattern check)
```

### Test 5: Mode Transition Validation

**Test 5a: Template → Plan transition**
```bash
# Verify concrete commands allowed after mode flip
$ sed 's/mode: "template"/mode: "plan"/' template.md > plan.md
$ uv run python ai_task_list_linter_v1_8.py plan.md
# Expected: Exit 0 if commands are concrete
```
```

**Create test runner script**:
```bash
#!/bin/bash
# validate_framework.sh

FAILED=0

echo "=== Framework Validation Suite ==="

echo "Test 1: Template scaffold..."
if ! uv run python ai_task_list_linter_v1_8.py AI_TASK_LIST_TEMPLATE_v6.md; then
  echo "FAIL: Template scaffold"
  FAILED=$((FAILED + 1))
fi

echo "Test 2: Plan artifact..."
if ! uv run python ai_task_list_linter_v1_8.py PYDANTIC_SCHEMA_tasks_plan.md; then
  echo "FAIL: Plan artifact"
  FAILED=$((FAILED + 1))
fi

# ... more tests

if [ $FAILED -eq 0 ]; then
  echo "✅ All validation passes succeeded"
  exit 0
else
  echo "❌ $FAILED validation passes failed"
  exit 1
fi
```

**Verdict on Fix #6**: ⚠️ **APPROVE** but **REQUIRE** detailed test specifications

---

## Cross-Cutting Concerns

### Concern #1: Documentation Proliferation

**Issue**: Multiple docs need updates (spec, linter, template, orchestrator, 2 manuals, readme, description, index)

**Risk**: Inconsistency if one doc is missed or updated incorrectly

**Mitigation**:
1. Create **single source of truth** for mode definitions (spec)
2. Other docs **reference** spec rather than redefining
3. Add **doc sync validation** to test suite:
   ```bash
   $ rg 'mode: "plan"' *.md | wc -l
   # Should find expected count in all relevant docs
   ```

---

### Concern #2: Linter Complexity Increase

**Issue**: Linter now needs to handle 3 modes with different rule sets

**Current**:
```python
if mode == "template":
    # Allow placeholders
elif mode == "instantiated":
    # Forbid placeholders, require evidence
```

**After fix**:
```python
if mode == "template":
    # Allow all placeholders (commands + output)
elif mode == "plan":
    # Forbid command placeholders, allow output placeholders
    # Enforce real commands in Preconditions/Global
elif mode == "instantiated":
    # Forbid all placeholders, require real evidence
```

**Risk**: More branching = more potential bugs

**Mitigation**:
1. **Comprehensive linter tests** (per Fix #6)
2. **Clear rule matrix** in linter comments
3. **Refactor linter** to use mode-specific rule objects:
   ```python
   class ModeRules:
       def allows_command_placeholders(self) -> bool: ...
       def allows_output_placeholders(self) -> bool: ...
       def requires_real_evidence(self) -> bool: ...
   
   TEMPLATE_RULES = ModeRules(cmd_ph=True, out_ph=True, evidence=False)
   PLAN_RULES = ModeRules(cmd_ph=False, out_ph=True, evidence=False)
   INSTANTIATED_RULES = ModeRules(cmd_ph=False, out_ph=False, evidence=True)
   ```

---

### Concern #3: User Confusion About Modes

**Issue**: 3 modes is inherently more complex than 2

**Mitigation strategies**:

1. **Clear naming**: "template" vs. "plan" vs. "instantiated" are intuitive
2. **Decision tree**: Provided in spec (required addition)
3. **Error messages**: Linter should suggest correct mode when violations detected
   ```
   Error: Concrete commands found in template mode
   Suggestion: Use mode: "plan" for project-specific task lists with real commands
   ```

4. **Examples**: Each mode should have a canonical example file in framework

---

### Concern #4: Backward Compatibility

**Issue**: Existing template-mode docs with concrete commands

**Impact**: 
- Breaking change if we suddenly reject them
- Migration burden on users

**Recommended approach**:

1. **Deprecation period**: 
   - v1.6.1: Add plan mode, keep template mode relaxed (warn but don't fail)
   - v1.7: Enforce strict template mode (fail on concrete commands)

2. **Migration helper**:
   ```bash
   $ uv run python migrate_to_plan.py <file>
   # Automatically converts mode, removes placeholder lines
   ```

3. **Clear communication**:
   - Changelog entry explaining breaking change
   - Migration guide in docs
   - Example migration in release notes

---

## Missing from Fix Plan

### Missing #1: Orchestrator Default Behavior

**Question**: Should orchestrator ALWAYS output mode: plan, or sometimes template?

**Answer needed**: 
- If prose is generic (no project specifics) → template
- If prose has project specifics → plan

**Recommendation**: Default to plan (safer choice), but add flag:
```bash
# Generate generic template
$ use orchestrator with --template-mode flag

# Generate project plan (default)
$ use orchestrator normally
```

---

### Missing #2: Phase Unlock Commands in Template Mode

**Question**: Should Phase Unlock artifact generation use placeholders in template mode?

**Current template**:
```bash
$ cat > .phase-N.complete.json << EOF
{
  "phase": N,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  ...
}
EOF
```

**Is this a command placeholder or concrete command?**
- It's a concrete pattern (cat + here-doc)
- But phase number is placeholder (N)

**Recommendation**: Clarify in spec:
- Template mode: `$ [[PH:PHASE_UNLOCK_COMMAND]]`
- Plan/instantiated mode: Concrete cat command

---

### Missing #3: Evidence Slot Placeholders Definition

**Question**: What counts as an "output placeholder"?

**Examples**:
```bash
[[PH:OUTPUT]]                    # Clear placeholder
[[PH:PASTE_TEST_OUTPUT]]        # Clear placeholder
(paste output here)             # Is this a placeholder?
# OUTPUT HERE                   # Is this a placeholder?
```

**Recommendation**: Define precisely in spec:
```markdown
**Output placeholders** (allowed in plan mode):
- `[[PH:OUTPUT]]`
- `[[PH:PASTE_*]]` (any PASTE_ variant)

**Not placeholders** (forbidden in all modes):
- Comments like `# OUTPUT HERE`
- Prose like `(paste output here)`

Rationale: Only `[[PH:...]]` format is machine-detectable.
```

---

### Missing #4: Prose Coverage Mapping Validation

**Question**: Should linter validate Prose Coverage Mapping table exists and is populated?

**Proposal**:
```python
# In linter for plan/instantiated modes
if mode in ("plan", "instantiated"):
    if not find_section("## Prose Coverage Mapping"):
        warnings.append("Prose Coverage Mapping recommended but missing")
    elif count_mapping_rows() < 1:
        warnings.append("Prose Coverage Mapping is empty")
```

**Verdict**: Add as optional warning (not hard error) in plan mode

---

## Recommended Additions to Fix Plan

### Addition #1: Mode Selection Decision Tree

Add to spec (shown earlier in Fix #1 analysis)

### Addition #2: Migration Guide

```markdown
## Migration Guide: Existing Templates → Plan Mode

### Identify candidates
Templates with concrete commands (not generic placeholders):
$ rg 'mode: "template"' --files-with-matches | \
  xargs grep -l '^\$ rg\|^\$ uv run pytest' | \
  grep -v '\[\[PH:SYMBOL_CHECK_COMMAND\]\]'

### For each candidate
1. Review: Is this generic (for framework) or project-specific?
   - Generic → Keep as template
   - Project-specific → Migrate to plan

2. Migrate:
   - Change `mode: "template"` → `mode: "plan"`
   - Remove any `[[PH:SYMBOL_CHECK_COMMAND]]` lines added for compliance
   - Keep concrete commands as-is
   - Keep output placeholders in evidence blocks

3. Validate:
   $ uv run python linter.py <file>
   # Should now pass with mode: plan

### Example migration
**Before** (template with violations):
```yaml
mode: "template"
```
```bash
**Preconditions**:
```bash
$ uv run pytest tests/ -q
$ [[PH:SYMBOL_CHECK_COMMAND]]  # Added for compliance
$ rg 'pydantic' pyproject.toml
```
```

**After** (plan mode, clean):
```yaml
mode: "plan"
```
```bash
**Preconditions**:
```bash
$ uv run pytest tests/ -q
$ rg 'pydantic' pyproject.toml  # Concrete command OK in plan mode
```
```
```

### Addition #3: Critical Enumeration Markers

Add to spec and orchestrator (shown in Fix #4 analysis)

### Addition #4: Validation Test Specifications

Add to spec and create test runner (shown in Fix #6 analysis)

### Addition #5: Linter Mode-Specific Error Messages

Enhance linter error messages:

```python
# Current
"Task 1.1 Preconditions must include [[PH:SYMBOL_CHECK_COMMAND]] in template mode."

# Enhanced
"Task 1.1 Preconditions must include [[PH:SYMBOL_CHECK_COMMAND]] in template mode.
Hint: If this is a project-specific task list with real commands, use mode: 'plan' instead."
```

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Mode proliferation** | 🟡 MODERATE | Clear decision tree, examples, error messages |
| **Migration burden** | 🟡 MODERATE | Migration guide, helper script, deprecation period |
| **Linter complexity** | 🟡 MODERATE | Comprehensive tests, refactored rule objects |
| **User confusion** | 🟡 MODERATE | Decision tree, clear naming, examples |
| **Documentation sync** | 🟡 MODERATE | Single source of truth, sync validation |
| **Backward incompatibility** | 🟠 HIGH | Deprecation period, clear communication |

**Overall risk**: 🟡 MODERATE (manageable with proposed mitigations)

---

## Approval Checklist

Before implementing, ensure:

- [ ] Mode selection decision tree added to spec
- [ ] Migration guide written with examples
- [ ] Critical enumeration markers defined
- [ ] Validation test suite specified with acceptance criteria
- [ ] Linter error messages enhanced with mode hints
- [ ] Backward compatibility plan documented
- [ ] Deprecation timeline defined
- [ ] Example files created for each mode
- [ ] Documentation sync validation added
- [ ] All 9 framework docs updated consistently

---

## Final Verdict

**Grade: B+ (82/100)**

**Breakdown**:
- **Problem identification**: A (Correctly identifies core issues)
- **Solution design**: B+ (Good solution, needs refinement)
- **Implementation plan**: B (Solid but incomplete)
- **Risk mitigation**: C+ (Acknowledged but under-specified)
- **Validation strategy**: B (Right idea, needs detail)

**Recommendation**: ✅ **APPROVE FOR IMPLEMENTATION** with required additions

**Required before shipping**:
1. Add mode selection decision tree
2. Write migration guide
3. Define critical enumeration markers
4. Specify validation test suite
5. Plan backward compatibility strategy

**Optional but recommended**:
6. Create migration helper script
7. Add enhanced linter error messages
8. Create canonical example for each mode

**Timeline estimate**:
- Core implementation: 2-3 days
- Documentation: 1-2 days
- Testing: 1 day
- **Total**: 4-6 days

---

**Approval status**: ✅ **CONDITIONAL APPROVE**

Fix plan addresses real problems and proposes sound solutions. With the required additions specified above, this will be a strong improvement to the framework.

**End of Feedback**
