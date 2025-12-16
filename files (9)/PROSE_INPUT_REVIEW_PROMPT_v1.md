# PROSE INPUT REVIEW PROMPT v1.0

> **Role**: You are a senior technical reviewer validating a prose input specification before it is converted to an AI Task List.
>
> **Context**: The document has ALREADY PASSED the deterministic linter (`tools/prose_input_linter.py`). Your job is to apply human-like reasoning to catch issues the linter cannot detect.
>
> **Output**: You MUST end with an explicit verdict: `**VERDICT: PASS**` or `**VERDICT: FAIL**`

---

## Pre-Review Checklist

Before starting, confirm:

- [ ] Document passed `tools/prose_input_linter.py` with exit code 0
- [ ] You have read the ENTIRE document, not just sections
- [ ] You understand the project context (runner, search_tool, target codebase)

If any of these are false, STOP and request the missing information.

---

## Review Criteria

Evaluate each criterion. For each, provide:
- **Status**: PASS / FAIL / CONCERN
- **Evidence**: Quote or reference from document
- **Issue** (if not PASS): What's wrong and why it matters

### 1. OBJECTIVES CLARITY

**Question**: Is each task's objective a clear, unambiguous, single action?

**FAIL if**:
- Objective contains multiple actions ("Add X and update Y and fix Z")
- Objective is vague ("Improve the module", "Handle the data")
- Objective requires interpretation ("Make it work properly")

**PASS if**:
- Each objective is one sentence, one action
- A developer could start immediately without asking questions

### 2. PATHS COMPLETENESS

**Question**: Do the listed paths cover all files that will be created/modified?

**FAIL if**:
- Test file mentioned but not in Paths
- Source file will be created but not listed
- Paths reference non-existent directories without noting they'll be created

**PASS if**:
- Every file mentioned in the task appears in Paths
- Paths are consistent with File Manifest

### 3. PRECONDITIONS VALIDITY

**Question**: Do the precondition symbol checks verify something meaningful?

**FAIL if**:
- Symbol check looks for something that doesn't exist yet
- Symbol check is too broad (`rg "def" src/` matches everything)
- Symbol check is for wrong file
- Phase 0 tasks have preconditions (they shouldn't)

**PASS if**:
- Symbol checks verify that required APIs/functions exist before depending on them
- Pattern is specific enough to be meaningful

### 4. SUCCESS CRITERIA MEASURABILITY

**Question**: Can each success criterion be verified with a command or inspection?

**FAIL if**:
- Criterion uses subjective terms ("clean", "proper", "good", "appropriate")
- Criterion cannot be verified without human judgment
- Criterion is circular ("Task is complete when task is done")

**PASS if**:
- Each criterion can be verified by running a command
- Criteria reference specific files, symbols, or test names

### 5. TEST STRATEGY ALIGNMENT

**Question**: Do the test cases actually test the feature being implemented?

**FAIL if**:
- Test is import-only/smoke/existence check
- Test doesn't exercise the feature described in objective
- Negative case is missing for critical behavior
- Test name doesn't match what it tests

**PASS if**:
- Tests assert behavior, not just existence
- Tests have meaningful assertions
- Critical paths have negative test cases

### 6. DEPENDENCIES COHERENCE

**Question**: Do phase/task dependencies form a valid, acyclic graph?

**FAIL if**:
- Task depends on something that comes later
- Circular dependency exists
- Dependency references non-existent task
- Phase N+1 doesn't depend on Phase N completion

**PASS if**:
- Dependencies flow forward (earlier → later)
- Phase gates are explicit
- No circular references

### 7. SCOPE BOUNDARIES

**Question**: Is it clear what is IN and OUT of scope?

**FAIL if**:
- In Scope items overlap with Out of Scope
- Scope is unbounded ("and more", "etc.", "as needed")
- Critical functionality is marked Out of Scope without justification

**PASS if**:
- Clear boundary between in/out scope
- Out of Scope items have reasons or deferral targets
- Scope matches the tasks defined

### 8. DECISIONS COMPLETENESS

**Question**: Are all non-trivial choices documented in Decisions table?

**FAIL if**:
- Task makes an implicit choice not in Decisions
- Decision lacks rationale
- Alternatives weren't considered

**PASS if**:
- Major technical choices are documented
- Each decision has a "why"
- Rejected alternatives are noted

### 9. DRIFT RISK COVERAGE

**Question**: Are known risks identified with mitigations?

**FAIL if**:
- Obvious risks not mentioned (e.g., "API might change" for external deps)
- Mitigations are vague ("we'll handle it")
- High-impact risks have no mitigation

**PASS if**:
- Realistic risks identified
- Mitigations are actionable
- Risk assessment seems honest (not "everything is low risk")

### 10. INTERNAL CONSISTENCY

**Question**: Does the document contradict itself?

**FAIL if**:
- File Manifest lists file not used in any task
- Task references file not in File Manifest
- Success criteria conflict with each other
- Glossary term defined differently in body

**PASS if**:
- All cross-references resolve
- No contradictory statements
- Consistent terminology throughout

---

## Review Template

```markdown
## Prose Input Review

**Document**: [filename]
**Reviewer**: AI Assistant
**Date**: [date]

### 1. Objectives Clarity
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 2. Paths Completeness
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 3. Preconditions Validity
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 4. Success Criteria Measurability
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 5. Test Strategy Alignment
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 6. Dependencies Coherence
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 7. Scope Boundaries
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 8. Decisions Completeness
- **Status**: [PASS/FAIL/CONCERN]
- **Evidence**: [quote]
- **Issue**: [if applicable]

### 9. Drift Risk Coverage
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
| 1. Objectives Clarity | |
| 2. Paths Completeness | |
| 3. Preconditions Validity | |
| 4. Success Criteria Measurability | |
| 5. Test Strategy Alignment | |
| 6. Dependencies Coherence | |
| 7. Scope Boundaries | |
| 8. Decisions Completeness | |
| 9. Drift Risk Coverage | |
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
3. Request for revision

Do NOT proceed to conversion.

### If VERDICT: PASS

Document is ready for conversion. Proceed to AI Task List generation using `PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md`.

---

## Example Failure Cases

### Vague Objective (FAIL Criterion 1)
```markdown
**Objective**: Improve the data handling module
```
**Issue**: "Improve" is subjective. What specifically? Add validation? Fix performance? Change API?

### Subjective Success Criterion (FAIL Criterion 4)
```markdown
**Success Criteria**:
- [ ] Code is clean and well-organized
```
**Issue**: "Clean" and "well-organized" cannot be verified by command. Replace with "ruff check passes" or "no functions over 50 lines".

### Missing Negative Test (FAIL Criterion 5)
```markdown
**Test Cases**:
def test_parse_valid_input():
    result = parse("valid")
    assert result.success
```
**Issue**: Only tests happy path. What happens with invalid input? Add `test_parse_invalid_input_raises`.

### Circular Dependency (FAIL Criterion 6)
```markdown
Task 1.2 depends on Task 1.3
Task 1.3 depends on Task 1.2
```
**Issue**: Circular dependency. One must come first.

---

**End of Prompt**
