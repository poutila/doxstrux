# FIX_1.md Feedback — Executive Summary

**Overall Grade**: B+ (82/100)  
**Verdict**: ✅ **CONDITIONAL APPROVE** — Implement with required additions

---

## Quick Status

| Fix | Grade | Status | Notes |
|-----|-------|--------|-------|
| **#1: mode: plan** | A- | ⚠️ NEEDS ADDITIONS | Core solution is excellent; missing decision tree & migration guide |
| **#2: Gate patterns** | A | ✅ APPROVE | Straightforward correctness fix; no issues |
| **#3: Placeholder bridge** | B | ⚠️ NEEDS GUIDANCE | Need interim user guidance while plan mode ships |
| **#4: Prose coverage** | B | ⚠️ NEEDS DEFINITION | Must define "critical enumeration" concretely |
| **#5: Runner normalization** | B+ | ✅ APPROVE | Good for consistency; straightforward |
| **#6: Validation** | A- | ⚠️ NEEDS SPECS | Right approach; need detailed test specifications |

---

## Critical Missing Pieces (MUST ADD)

### 1. Mode Selection Decision Tree (Fix #1)

**Problem**: Users won't know when to use template vs. plan vs. instantiated

**Required addition to spec**:
```markdown
## Mode Selection Guide

### When to use `template`
- Creating generic, reusable template for framework library
- Commands must remain placeholders (no project details)
**Example**: AI_TASK_LIST_TEMPLATE_v6.md

### When to use `plan`  
- Planning work for specific project from prose
- Commands are project-specific but not yet executed
**Example**: PYDANTIC_SCHEMA_tasks_plan.md after generation

### When to use `instantiated`
- Work is being executed or completed
- Evidence blocks contain real command outputs
**Example**: Production task lists with CI integration

### Lifecycle Flow
Framework Template (mode: template)
  ↓ [Generate from prose]
Project Plan (mode: plan)
  ↓ [Execute + capture evidence]
Executed List (mode: instantiated)
```

---

### 2. Migration Guide (Fix #1)

**Problem**: Existing "template with real commands" docs need migration path

**Required addition**:
```markdown
## Migration: Template → Plan Mode

### Identify candidates
$ rg 'mode: "template"' --files-with-matches | \
  xargs grep -l '^\$ rg\|^\$ uv run' | \
  grep -v '\[\[PH:SYMBOL_CHECK_COMMAND\]\]'

### For each file
1. Review: Generic (framework) or project-specific?
   - Generic → Keep as template
   - Project-specific → Migrate to plan

2. Migrate:
   - Change mode: "template" → mode: "plan"
   - Remove [[PH:SYMBOL_CHECK_COMMAND]] lines
   - Keep concrete commands as-is
   - Keep output placeholders

3. Validate:
   $ uv run python linter.py <file>
```

---

### 3. Interim User Guidance (Fix #3)

**Problem**: What should users do RIGHT NOW before plan mode ships?

**Required addition to README/docs**:
```markdown
## Interim Guidance (Until Plan Mode Ships)

If you have mode: template with concrete commands:

**Option A - Keep as-is (accept violations)**:
- 20 violations expected
- Functionally correct
- Convert to plan mode when available

**Option B - Add placeholder lines (achieve compliance)**:
- Add [[PH:SYMBOL_CHECK_COMMAND]] lines
- Passes linter
- Extra work now, cleanup later

**Option C - Wait for plan mode (RECOMMENDED)**:
- Leave as-is
- Track fix plan progress
- Convert in one pass when plan mode available
```

---

### 4. Critical Enumeration Definition (Fix #4)

**Problem**: No concrete definition of what needs verbatim copying

**Required addition to spec**:
```markdown
## Critical Enumerations

A **critical enumeration** is a list where:
1. Completeness is essential (missing items = missing requirements)
2. Order may matter (sequence dependencies)
3. Each item is independently verifiable (no summarization)

**Examples**:
- Security field paths that MUST be checked
- Required schema fields with specific names
- Compliance checklist items with exact wording
- File paths that must exist

**Mark in prose**:
<!-- CRITICAL_ENUM: label -->
List items here
<!-- END_CRITICAL_ENUM -->

**Orchestrator instruction**:
"Copy critical enumerations VERBATIM. Do not summarize or truncate."
```

---

### 5. Validation Test Specifications (Fix #6)

**Problem**: No detailed test specs provided

**Required addition**:

```markdown
## Validation Test Suite

### Test 1: Template Scaffold
**Input**: AI_TASK_LIST_TEMPLATE_v6.md
**Expected**: Pass (exit 0) with mode: template
**Validates**: All placeholders, correct structure

### Test 2: Plan Artifact  
**Input**: PYDANTIC_SCHEMA_tasks_plan.md
**Expected**: Pass (exit 0) with mode: plan
**Validates**: Real commands, output placeholders only

### Test 3: Instantiated Sample
**Input**: example_instantiated.md
**Expected**: Pass with --require-captured-evidence
**Validates**: No placeholders, real evidence

### Test 4: Negative Cases
- Plan with command placeholders (should fail)
- Template with bad gates (should fail)

### Test 5: Mode Transitions
- Verify template→plan allows concrete commands
- Verify plan→instantiated requires evidence
```

---

## Strengths of Fix Plan ⭐⭐⭐⭐

1. **Correctly identifies core problem**: Template purity vs. practical commands
2. **Proposes sound solution**: Three-mode lifecycle makes semantic sense
3. **Addresses gate pattern bug**: Critical correctness issue
4. **Maintains governance**: Runner/import hygiene still enforced in plan mode
5. **Backward compatible**: Existing template mode unchanged

---

## Weaknesses / Gaps ⚠️

1. **Complexity increase**: 3 modes vs. 2 (50% more lifecycle states)
2. **Missing decision tree**: Users won't know which mode to use
3. **No migration guide**: Existing docs left in limbo
4. **Undefined critical enums**: "Copy verbatim" has no concrete criteria
5. **Incomplete validation**: Test approach right, but specs missing
6. **Documentation proliferation**: 9 files to update consistently

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| User confusion (3 modes) | 🟡 MODERATE | Decision tree, clear examples |
| Migration burden | 🟡 MODERATE | Migration guide, helper script |
| Linter complexity | 🟡 MODERATE | Comprehensive tests, refactor |
| Doc sync issues | 🟡 MODERATE | Single source of truth, validation |
| Breaking changes | 🟠 HIGH | Deprecation period, clear comms |

**Overall**: 🟡 MODERATE (manageable with mitigations)

---

## Implementation Priority

### MUST HAVE (before shipping)
1. ✅ Mode selection decision tree → Spec
2. ✅ Migration guide with examples → Docs
3. ✅ Critical enum definition with markers → Spec
4. ✅ Validation test specifications → Test suite
5. ✅ Interim user guidance → README

### SHOULD HAVE (strongly recommended)
6. ⚠️ Enhanced linter error messages (suggest correct mode)
7. ⚠️ Migration helper script (automate template→plan)
8. ⚠️ Canonical example for each mode
9. ⚠️ Deprecation timeline for strict template enforcement

### NICE TO HAVE (optional improvements)
10. Linter refactor (mode-specific rule objects)
11. Doc sync validation in CI
12. Backward compatibility period (v1.6.1 → v1.7)

---

## Implementation Estimate

**Core work**: 2-3 days
- Spec updates: 0.5 day
- Linter changes: 1 day
- Doc updates (9 files): 1 day
- Testing: 0.5 day

**With required additions**: 4-6 days
- Decision tree: 0.5 day
- Migration guide: 0.5 day
- Critical enum definition: 0.5 day
- Test specifications: 0.5 day
- Integration testing: 1 day

---

## Approval Status

**✅ CONDITIONAL APPROVE**

**Conditions**:
1. Add mode selection decision tree (REQUIRED)
2. Add migration guide (REQUIRED)
3. Define critical enumerations (REQUIRED)
4. Specify validation test suite (REQUIRED)
5. Provide interim user guidance (REQUIRED)

**Once conditions met**: Full approval to implement

---

## Key Quote from Detailed Feedback

> "The fix plan directly addresses the core tension (template purity vs. practical commands) identified in the task list evaluation. The proposed `mode: plan` is a thoughtful solution, but the plan needs stronger guidance on mode selection, migration paths, and validation."

---

## What You Should Do Next

### Immediate (Before Implementation)

1. **Read full feedback**: FIX_PLAN_FEEDBACK.md (20+ pages, comprehensive)
2. **Add required pieces**: Decision tree, migration guide, definitions
3. **Create test specs**: Detailed acceptance criteria per validation pass
4. **Plan backward compatibility**: Deprecation timeline, communication strategy

### During Implementation

5. **Update spec first**: Single source of truth for mode rules
6. **Implement linter changes**: With comprehensive tests
7. **Update all 9 docs consistently**: Use checklist to avoid gaps
8. **Create example files**: Canonical template, plan, instantiated

### After Implementation

9. **Run validation suite**: All tests must pass
10. **Test migration path**: Template→plan with real file
11. **Update CHANGELOG**: Clear breaking change communication
12. **Ship with confidence**: Framework will be stronger for it

---

## Bottom Line

**Good plan** that solves the right problems. Needs **5 concrete additions** before implementation to avoid user confusion and ensure smooth adoption.

**Effort**: +2-3 days for additions  
**Benefit**: Eliminates 95% of "template with real commands" violations  
**Risk**: Moderate, manageable with proposed mitigations

**Recommendation**: ✅ **Add required pieces, then implement**

---

**See FIX_PLAN_FEEDBACK.md for exhaustive analysis (includes all missing details, risk mitigation strategies, and implementation guidance)**
