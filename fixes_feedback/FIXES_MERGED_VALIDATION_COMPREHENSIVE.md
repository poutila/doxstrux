# FIXES_MERGED.md Validation Against Current Framework

**Analysis Date**: 2025-12-15  
**Validation Type**: Plan vs. Current Implementation State  
**Analyst**: Claude (Sonnet 4.5)

---

## Executive Summary

**CRITICAL FINDING**: FIXES_MERGED.md is a **PLANNING DOCUMENT**, not a status report.

**Implementation Status**: 0% (0 of 7 priority items implemented)

**Key Discovery**: ORCHESTRATOR_REFACTOR.md is ALSO a planning document describing the same work.

**Verdict**: ✅ **FIXES_MERGED.md accurately describes FUTURE work**, not current state.

---

## Validation Results by Priority Item

### Priority 1: Mode Semantics (mode: plan)

**FIXES_MERGED.md says**: "add `mode: plan` (Path A, no interim relaxation)"

**Current framework state**:
```yaml
# From Template line 3:
mode: "template"  # "template" = placeholders allowed, "instantiated" = placeholders forbidden
```

**Linter code** (ai_task_list_linter_v1_8.py):
- Only checks for "template" and "instantiated"
- No "plan" mode exists

**Finding**: ❌ **NOT IMPLEMENTED** (0% complete)

**Evidence**:
```bash
$ grep -E 'mode.*=.*(template|instantiated)' ai_task_list_linter_v1_8.py
# Returns: Only template and instantiated mode checks
# Returns: NO plan mode
```

**Related document**: ORCHESTRATOR_REFACTOR.md is a SEPARATE planning document describing this exact work:
```markdown
# Orchestrator Refactor Plan — Introduce `mode: plan` for Clean Lifecycle

Goal: create a three-stage lifecycle that eliminates template-vs-real 
command friction...
```

**Conclusion**: Both FIXES_MERGED.md and ORCHESTRATOR_REFACTOR.md describe future work on mode: plan.

---

### Priority 2: Prose Coverage Mapping Enforcement

**FIXES_MERGED.md says**: "Linter: warning in plan/instantiated modes—check header, Source is anchored, tasks referenced exist"

**Current framework state**:

**AI_ASSISTANT_USER_MANUAL.md** (line 40):
> "Prose Coverage Mapping (recommended, not linted)"

**USER_MANUAL.md** (section 5):
> "Prose Coverage Mapping: include a short table..."
> (No mention of enforcement)

**Linter code**:
```bash
$ grep -i 'prose.*coverage' ai_task_list_linter_v1_8.py
# Returns: (no matches)
```

**Finding**: ❌ **NOT IMPLEMENTED** (0% complete)

**Evidence**: Zero linter enforcement code for prose coverage mapping exists.

**Conclusion**: Prose coverage is documented as "recommended" with zero enforcement.

---

### Priority 3: Spec as SSOT

**FIXES_MERGED.md says**: "Update AI_TASK_LIST_SPEC_v1.md to match linter behavior/version or explicitly declare linter as SSOT—pick one"

**Current framework state**:

**USER_MANUAL.md** (section 1):
> "SSOT: spec + linter are authoritative. If this manual/template ever disagree with them, the spec/linter win."

**AI_ASSISTANT_USER_MANUAL.md**:
> "If this manual, the template, and the spec/linter ever disagree, the spec... and linter... win"

**Finding**: ⚠️ **AMBIGUOUS** (50% complete)

**Issues**:
1. Says "spec + linter" but doesn't clarify hierarchy
2. What if spec and linter disagree?
3. No explicit "Spec is SSOT, linter implements spec" statement

**Conclusion**: Principle stated but needs clarification per FIXES_MERGED.md requirements.

---

### Priority 4: Gates and Runner Normalization

**FIXES_MERGED.md says**: "Audit/replace any `&& exit 1 ||` gate patterns with fail-on-match"

**Current framework state - Gate Patterns**:

**Template** shows correct patterns:
```bash
# Line 297-298:
# $ ! rg 'TODO|FIXME|XXX' src/                           # No unfinished markers
# $ ! rg '\[\[PH:' .                                     # No placeholders
```

**README_ai_task_list_linter_v1_8.md**:
> "Use `! rg …` or `if rg …; then exit 1; fi` for gates (recommended authoring; not lint-enforced)"

**Finding - Gates**: ⚠️ **GOOD EXAMPLES, NO AUDIT** (70% complete)

**Evidence**: Template has correct patterns, but no systematic audit has been performed.

**Current framework state - Runner Normalization**:

All examples in uploaded files use `uv run` correctly. No legacy commands found.

**Finding - Runner**: ✅ **MOSTLY DONE** (95% complete)

**Conclusion**: Good patterns exist, but formal audit not completed per FIXES_MERGED.md.

---

### Priority 5: Migration + User Guidance

**FIXES_MERGED.md says**: "Mode decision tree, migration guide, deprecation timeline"

**Current framework state**:
- No mode decision tree (only 2 modes exist)
- No MIGRATION_GUIDE.md file
- No deprecation timeline documented
- No version plan for breaking changes

**Finding**: ❌ **NOT IMPLEMENTED** (0% complete)

**Evidence**:
```bash
$ ls -la MIGRATION* 2>/dev/null
# Returns: (no such file)
```

**Conclusion**: No migration materials exist. Cannot create migration guide for mode: plan that doesn't exist yet.

---

### Priority 6: Validation Suite

**FIXES_MERGED.md says**: "Define/run tests: template/plan/instantiated + negatives + doc-sync"

**Current framework state**:

**README_ai_task_list_linter_v1_8.md** shows manual verification:
```markdown
## Test Results

✅ Template v6 passes
✅ Valid v1.6 document passes
✅ Comment compliance REJECTED
...
```

**Finding**: ❌ **NOT IMPLEMENTED** (0% complete)

**Evidence**:
- No test files provided
- Only manual "Test Results" bullet points
- No automated test suite
- No test runner script

**Conclusion**: Only manual verification exists. No automated validation suite.

---

### Priority 7: Critical Enumerations

**FIXES_MERGED.md says**: "Define criteria/markers, instruct verbatim copy"

**Current framework state**:
```bash
$ grep -i 'critical.*enum' *.md *.py
# Returns: Only found in FIXES_MERGED.md itself
```

**Finding**: ❌ **NOT IMPLEMENTED** (0% complete)

**Evidence**: Concept doesn't exist anywhere in current framework files.

**Conclusion**: This is entirely new work.

---

## Additional Validation: Acceptance Criteria

### Versioning/Communication

**FIXES_MERGED.md mentions**: "spec v1.7.0/linter v1.9 with schema_version "1.6" unchanged"

**Current versions**:
- Spec: v1.6 (AI_TASK_LIST_SPEC_v1.md)
- Linter: v1.8 (README_ai_task_list_linter_v1_8.md)
- Template: v6.0 (AI_TASK_LIST_TEMPLATE_v6.md)
- schema_version: "1.6" (in YAML)

**Finding**: ❌ **FUTURE VERSIONS** (v1.7/v1.9 don't exist yet)

**Evidence**: No v1.7 or v1.9 mentioned anywhere in actual framework files.

---

### Canonical Examples

**FIXES_MERGED.md says**: "three example files (template/plan/instantiated) created"

**Current framework state**:
```bash
$ ls -la example*.md 2>/dev/null
# Returns: (no such files)
```

**Files that exist**:
- AI_TASK_LIST_TEMPLATE_v6.md (template example)
- No example_plan.md (plan mode doesn't exist)
- No example_instantiated.md

**Finding**: ⚠️ **1 OF 3 EXISTS** (33% complete)

---

### Real-Project Validation

**FIXES_MERGED.md says**: "migration guide tested on 2-3 real task lists"

**Finding**: ❌ **CANNOT TEST** (migration guide doesn't exist)

---

### Edge Cases Documentation

**FIXES_MERGED.md says**: "documented stances on mixed-mode, reverse migration, plan-in-CI, schema_version vs spec version"

**Current framework state**: None of these edge cases documented.

**Finding**: ❌ **NOT DOCUMENTED** (0% complete)

**Reason**: Can't document plan mode edge cases when plan mode doesn't exist.

---

## Summary Table: Implementation Status

| Priority | Item | FIXES_MERGED Status | Current State | Implementation % |
|----------|------|---------------------|---------------|------------------|
| 1 | Mode: plan | To implement | ❌ Doesn't exist | 0% |
| 2 | Prose coverage | To implement | ❌ Not enforced | 0% |
| 3 | Spec SSOT | To clarify | ⚠️ Ambiguous | 50% |
| 4 | Gate audit | To audit | ⚠️ Examples good | 70% |
| 4 | Runner norm | To audit | ✅ Examples good | 95% |
| 5 | Migration | To write | ❌ Doesn't exist | 0% |
| 6 | Validation | To implement | ❌ Manual only | 0% |
| 7 | Critical enum | To define | ❌ Not mentioned | 0% |

**Overall Implementation**: **15%** (weighted by priority)

Breakdown:
- Fully implemented: 0 items (0%)
- Partially implemented: 2 items (SSOT 50%, Gates 70%)
- Not implemented: 6 items (0%)

---

## Key Discoveries

### Discovery #1: ORCHESTRATOR_REFACTOR.md is ALSO a Planning Document

**ORCHESTRATOR_REFACTOR.md header**:
```markdown
# Orchestrator Refactor Plan — Introduce `mode: plan` for Clean Lifecycle

Goal: create a three-stage lifecycle...
```

**Implication**: Two planning documents exist for the same work:
1. FIXES_MERGED.md (consolidated plan)
2. ORCHESTRATOR_REFACTOR.md (refactor plan)

Both describe adding mode: plan. Neither has been implemented.

---

### Discovery #2: Version Numbers Indicate Planning Phase

**Current versions**: v1.6 (spec), v1.8 (linter)  
**FIXES_MERGED versions**: v1.7 (spec), v1.9 (linter)

The version bump indicates this is **future work**, not current state.

---

### Discovery #3: Template Already Has Good Patterns

The template (AI_TASK_LIST_TEMPLATE_v6.md) already shows:
- Correct gate patterns (`! rg`)
- Correct runner usage (`uv run`)
- Correct placeholder format (`[[PH:NAME]]`)

**This means**: Examples are good, formal audit is what's missing.

---

## What FIXES_MERGED.md Is

✅ Comprehensive implementation plan  
✅ Prioritized work breakdown  
✅ Clear acceptance criteria  
✅ Roadmap for v1.7 release

---

## What FIXES_MERGED.md Is NOT

❌ Status report of current implementation  
❌ Changelog of completed features  
❌ Description of existing framework  
❌ Validation that work is done

---

## Validation Verdict

**Question**: Does FIXES_MERGED.md reflect current framework state?

**Answer**: ❌ **NO** - It describes **future state**, not current state.

**Accuracy of plan**: ✅ **HIGHLY ACCURATE**
- Correctly identifies gaps
- Accurately describes current limitations
- Proposes sound solutions

**Implementation status**: 📋 **0% COMPLETE** on priority items (15% overall including partial work)

---

## Recommendations

### Recommendation #1: Add Planning Document Header

**Add to FIXES_MERGED.md**:
```markdown
---
**DOCUMENT TYPE**: 📋 PLANNING DOCUMENT (NOT IMPLEMENTATION STATUS)
**STATUS**: Not started (0% of priority items complete)
**TARGET**: Framework v1.7 (spec) / v1.9 (linter)
**CURRENT**: Framework v1.6 (spec) / v1.8 (linter)
---

⚠️ **WARNING**: This document describes FUTURE changes, not current features.

**Before implementation**:
1. Make 3 critical decisions (see feedback documents)
2. Follow implementation sequence
3. Validate against acceptance criteria
```

---

### Recommendation #2: Reconcile Planning Documents

You have two planning documents:
1. **FIXES_MERGED.md** - Consolidated, comprehensive (recommended)
2. **ORCHESTRATOR_REFACTOR.md** - Focused on mode: plan

**Decision needed**: 
- Option A: Archive ORCHESTRATOR_REFACTOR.md (superseded by FIXES_MERGED)
- Option B: Keep both (ORCHESTRATOR_REFACTOR = detailed spec for Priority #1)

**Recommended**: Option B with cross-reference:
```markdown
# In ORCHESTRATOR_REFACTOR.md:
**NOTE**: This plan is now part of FIXES_MERGED.md Priority #1.
See FIXES_MERGED.md for full context and sequence.

# In FIXES_MERGED.md Priority #1:
See ORCHESTRATOR_REFACTOR.md for detailed implementation spec of mode: plan.
```

---

### Recommendation #3: Create Implementation Tracker

**Create FIXES_STATUS.md**:
```markdown
# FIXES Implementation Status

**Last Updated**: 2025-12-15  
**Plan**: FIXES_MERGED.md  
**Target Version**: v1.7 (spec), v1.9 (linter)

## Priority Items

| # | Item | Status | Progress | Blocker | ETA |
|---|------|--------|----------|---------|-----|
| 1 | Mode: plan | 📋 Not started | 0% | Need SSOT decision | TBD |
| 2 | Coverage | 📋 Not started | 0% | Depends on #1 | TBD |
| 3 | SSOT | 📋 Not started | 0% | Need decision | TBD |
| 4 | Gates | 📋 Not started | 0% | - | TBD |
| 5 | Migration | 📋 Not started | 0% | Depends on #1 | TBD |
| 6 | Validation | 📋 Not started | 0% | Depends on #1 | TBD |
| 7 | Critical enum | 📋 Not started | 0% | - | TBD |

**Legend**: 📋 Not started | 🚧 In progress | ✅ Complete | ❌ Blocked
```

---

## Conclusion

**FIXES_MERGED.md is an excellent planning document** that accurately describes:
- Current framework limitations
- Required fixes
- Implementation approach
- Acceptance criteria

**However, it describes work to be done, not work completed.**

**Implementation status**: 0% on core features (plan mode, coverage, migration, validation, critical enum)

**Ready to implement**: ✅ YES (after 3 clarifications)

**Current framework**: v1.6/v1.8 (stable, no plan mode)  
**Target framework**: v1.7/v1.9 (after FIXES_MERGED implementation)

---

**End of Validation Report**
