# PROMPT: AI TASK LIST REVIEW (see VERSION.yaml for framework version)

> **Role**: You are a senior technical reviewer validating an AI Task List after conversion from prose input.
>
> **Context**: The document has ALREADY PASSED the deterministic linter (`tools/ai_task_list_linter.py`). Your job is to apply human-like reasoning to catch issues the linter cannot detect.
>
> **Output**: You MUST end with an explicit verdict: `**VERDICT: PASS**` or `**VERDICT: FAIL**`

---

## Pre-Review Checklist

Before starting, confirm:

- [ ] Document passed `tools/ai_task_list_linter.py` with exit code 0
- [ ] You have access to the original prose input document
- [ ] You have read the ENTIRE task list, not just sections
- [ ] You understand the project context (runner, search_tool, target codebase)

If any of these are false, STOP and request the missing information.

---

## Review Criteria

Evaluate each criterion. For each, provide:
- **Status**: PASS / FAIL / CONCERN
- **Evidence**: Quote or reference from document
- **Issue** (if not PASS): What's wrong and why it matters

### 1. CONVERSION FIDELITY

**Question**: Does the task list faithfully represent the prose input?

**FAIL if**:
- Task objective differs semantically from prose requirement
- Phase structure doesn't match prose milestones
- Scope items from prose are missing from tasks
- Decisions table content altered or invented

**PASS if**:
- 1:1 mapping between prose requirements and tasks
- Phase names match prose milestone names
- All in-scope items appear as tasks

### 2. PRECONDITION VALIDITY

**Question**: Are precondition checks meaningful and grounded in reality?

**FAIL if**:
- `rg` pattern is too generic (`rg "def" src/` matches everything)
- Symbol being checked doesn't exist in the codebase
- File path in precondition doesn't match Sample Artifacts
- Precondition checks for something created in a later task

**PASS if**:
- Patterns are specific enough to be meaningful
- Symbols/paths traceable to prose input's Sample Artifacts or File Manifest
- Dependencies flow forward (earlier → later)

### 3. TDD/OBJECTIVE ALIGNMENT

**Question**: Do TDD steps actually test the stated objective?

**FAIL if**:
- RED step test name doesn't relate to objective
- GREEN step implementation doesn't fulfill RED step
- VERIFY step runs unrelated tests
- Test asserts something different from what objective states

**PASS if**:
- Test name reflects objective action
- Implementation directly addresses test
- Verification command tests the specific feature

### 4. COVERAGE MAPPING COMPLETENESS

**Question**: Does Prose Coverage Mapping account for all requirements?

**FAIL if**:
- Prose requirement has no corresponding task
- Task has no corresponding prose requirement (orphan)
- Mapping table has empty cells in plan/instantiated mode

**PASS if**:
- Every prose requirement maps to at least one task
- Every task maps to at least one prose requirement
- No orphans in either direction

### 5. PATHS TRACEABILITY

**Question**: Are all file paths traceable to prose input facts?

**FAIL if**:
- Path in TASK_N_M_PATHS not in prose File Manifest
- Path invented (not in Sample Artifacts or File Manifest)
- Directory structure assumed but not verified in discovery

**PASS if**:
- All paths appear in prose input's File Manifest
- New files marked as CREATE in File Manifest
- Existing files confirmed in Sample Artifacts

### 6. NO AI INVENTION

**Question**: Did conversion introduce content not in prose input?

**FAIL if**:
- New decisions made (not in prose Decisions table)
- New dependencies added (not in prose External Dependencies)
- Alternative approaches chosen (prose had a different decision)
- Symbols/classes invented (not in prose or Sample Artifacts)

**PASS if**:
- All content traceable to prose input sections
- No new technical choices made during conversion
- Glossary terms match prose definitions exactly

### 7. GOVERNANCE PRESERVATION

**Question**: Are governance rules properly baked into task structure?

**FAIL if**:
- TDD steps missing for implementation task
- No Weak Tests checklist incomplete
- Clean Table checklist incomplete
- STOP blocks missing at phase gates
- Evidence placeholders not properly formatted

**PASS if**:
- Every implementation task has TDD structure
- All checklists have required items
- Phase gates have STOP blocks
- Evidence format matches spec

### 8. SUCCESS CRITERIA MEASURABILITY

**Question**: Can success criteria be verified with commands?

**FAIL if**:
- Criterion uses subjective terms ("clean", "proper", "good")
- Criterion cannot be verified by running a command
- Criterion contradicts preconditions or TDD steps

**PASS if**:
- Each criterion references specific command, file, or symbol
- Verification command provided for each criterion
- Criteria align with TDD VERIFY step

### 9. TEST CASE QUALITY

**Question**: Do test cases meet No Weak Tests requirements?

**FAIL if**:
- Test is import-only/smoke/existence check
- Test lacks meaningful assertion
- Negative case missing for critical behavior
- Test name doesn't describe what it tests

**PASS if**:
- Tests assert behavior, not just existence
- Tests have specific assertions
- Critical paths have negative test cases
- Test names are descriptive

### 10. INTERNAL CONSISTENCY

**Question**: Is the task list internally consistent?

**FAIL if**:
- Task depends on something that comes later
- Same file appears with conflicting actions
- Phase N+1 doesn't depend on Phase N
- Glossary term used differently in tasks

**PASS if**:
- Dependencies flow forward only
- No circular references
- Consistent terminology throughout
- File actions are coherent (CREATE before MODIFY)

---

## Review Template

```markdown
## AI Task List Review

**Task List**: [filename]
**Prose Input**: [source prose filename]
**Reviewer**: AI Assistant
**Date**: [date]

### 1. Conversion Fidelity
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 2. Precondition Validity
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 3. TDD/Objective Alignment
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 4. Coverage Mapping Completeness
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 5. Paths Traceability
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 6. No AI Invention
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 7. Governance Preservation
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 8. Success Criteria Measurability
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 9. Test Case Quality
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 10. Internal Consistency
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

---

## Summary

| Criterion | Status |
|-----------|--------|
| 1. Conversion Fidelity | |
| 2. Precondition Validity | |
| 3. TDD/Objective Alignment | |
| 4. Coverage Mapping Completeness | |
| 5. Paths Traceability | |
| 6. No AI Invention | |
| 7. Governance Preservation | |
| 8. Success Criteria Measurability | |
| 9. Test Case Quality | |
| 10. Internal Consistency | |

**FAIL Count**: [N]
**CONCERN Count**: [N]

---

## Verdict

**VERDICT: [PASS/FAIL]**

[If FAIL: List the blocking issues that must be fixed]
[If PASS with CONCERNS: List concerns for author awareness]
```

---

## Verdict Rules

- **Any FAIL** → `VERDICT: FAIL`
- **All PASS, no CONCERN** → `VERDICT: PASS`
- **All PASS, some CONCERN** → `VERDICT: PASS` (with concerns noted)

---

## Post-Review Actions

### If VERDICT: FAIL

Return the review to the author with:
1. List of failing criteria
2. Specific issues to fix
3. Request for re-conversion or manual correction

Do NOT proceed to execution.

### If VERDICT: PASS

Task list is ready for execution. Human may proceed with Phase 0.

---

## Example Failure Cases

### AI Invention (FAIL Criterion 6)
```markdown
**Paths**: `src/utils/helpers.py`
```
**Issue**: `helpers.py` not in prose File Manifest or Sample Artifacts. AI invented this path.

### Weak Precondition (FAIL Criterion 2)
```bash
$ rg 'def' src/
```
**Issue**: Pattern too broad. Every function definition matches. Use specific symbol name.

### TDD/Objective Mismatch (FAIL Criterion 3)
```markdown
**Objective**: Add validation for user email
**TDD RED**: `test_user_model_exists`
```
**Issue**: Test checks model existence, not email validation. Test should be `test_user_email_validates_format`.

### Missing Coverage (FAIL Criterion 4)
```markdown
Prose: "Implement caching for API responses"
Tasks: [no task for caching]
```
**Issue**: In-scope requirement from prose has no corresponding task.

### Invented Decision (FAIL Criterion 6)
```markdown
Prose Decisions: [empty table]
Task List: "Use Redis for caching (D1)"
```
**Issue**: Decision D1 was made during conversion. Decisions must come from prose input.

---

**End of Prompt**
