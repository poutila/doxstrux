# COMPLETE_VALIDATION.md

> **Version**: 1.1
> **Purpose**: Define the complete input-to-output validation pipeline for the AI Task List Framework.
> **Implements**: GOAL.md §7 (Two-phase validation at both ends)

---

## Philosophy

**Strict input → Deterministic conversion → Validated output**

The framework eliminates drift by:
1. Controlling input structure strictly (no ambiguous prose)
2. Validating input in two phases (mechanical + semantic)
3. Converting deterministically (reformat, not interpret)
4. Validating output in two phases (mechanical + semantic)

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PHASE 0: DISCOVERY (OPTIONAL)                        │
│                                                                         │
│   Tool: PROMPT_PROSE_INPUT_DISCOVERY.md                                 │
│   Type: AI prompt (fact-gathering, no reasoning)                        │
│                                                                         │
│   Gathers from codebase:                                                │
│   • Project metadata (name, runner, search tool)                        │
│   • Directory structure                                                 │
│   • Existing files in target area                                       │
│   • Current dependencies                                                │
│   • Sample outputs (for schema work)                                    │
│   • CI/workflow configuration                                           │
│   • Key symbols to depend on                                            │
│                                                                         │
│   Output: Discovery report with facts to paste into template            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              INPUT                                       │
│                                                                         │
│   Author writes spec using PROSE_INPUT_TEMPLATE.md                      │
│   (Structured format that mirrors output structure)                      │
│   Uses facts from Phase 0 to fill in Sample Artifacts section           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     PHASE 1: DETERMINISTIC VALIDATION                    │
│                                                                         │
│   Tool: tools/prose_input_linter.py                                     │
│   Type: Script (deterministic, no AI)                                    │
│   Deps: pyyaml                                                          │
│                                                                         │
│   Validates:                                                            │
│   ✓ YAML front matter present and valid                                 │
│   ✓ Schema version matches                                              │
│   ✓ Required sections in correct order                                  │
│   ✓ No [[PLACEHOLDER]] tokens remain                                    │
│   ✓ No TBD/TODO/TBC/FIXME markers                                       │
│   ✓ No unanswered questions (lines ending with ?)                       │
│   ✓ No tentative language (maybe, might, could, consider)               │
│   ✓ No conditional logic (if we... then)                                │
│   ✓ No time estimates                                                   │
│   ✓ No pending decisions                                                │
│   ✓ Task structure complete (Objective, Paths, etc.)                    │
│   ✓ Decisions table has required columns                                │
│   ✓ File Manifest populated                                             │
│   ✓ Submission checklist fully checked                                  │
│                                                                         │
│   Exit codes:                                                           │
│     0 = PASS (proceed to Phase 2)                                       │
│     1 = FAIL (fix errors, re-run)                                       │
│     2 = Schema error                                                    │
│     3 = File error                                                      │
│                                                                         │
│   Command:                                                              │
│     uv run python tools/prose_input_linter.py SPEC.md                   │
│     uv run python tools/prose_input_linter.py --fix-hints SPEC.md       │
│     uv run python tools/prose_input_linter.py --json SPEC.md            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Exit 0
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     PHASE 2: SEMANTIC VALIDATION                         │
│                                                                         │
│   Tool: PROMPT_PROSE_INPUT_REVIEW.md                                    │
│   Type: AI reasoning (requires judgment)                                │
│   Deps: AI assistant capable of reasoning                               │
│                                                                         │
│   Validates:                                                            │
│   ✓ Objectives actually clear (not just present)                        │
│   ✓ Paths actually complete (all files covered)                         │
│   ✓ Preconditions actually valid (meaningful checks)                    │
│   ✓ Success criteria actually measurable (not subjective)               │
│   ✓ Test strategy actually tests behavior (not smoke tests)             │
│   ✓ Dependencies actually coherent (no cycles, valid refs)              │
│   ✓ Scope actually bounded (no "etc." or "as needed")                   │
│   ✓ Decisions actually complete (no implicit choices)                   │
│   ✓ Drift risks actually covered (realistic mitigations)                │
│   ✓ Document internally consistent (no contradictions)                  │
│                                                                         │
│   Output:                                                               │
│     VERDICT: PASS (proceed to conversion)                               │
│     VERDICT: FAIL (fix issues, return to Phase 1)                       │
│                                                                         │
│   Usage:                                                                │
│     1. Copy PROMPT_PROSE_INPUT_REVIEW.md into AI context                │
│     2. Provide the spec document that passed Phase 1                    │
│     3. AI produces review with explicit VERDICT                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ VERDICT: PASS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CONVERSION                                       │
│                                                                         │
│   Tool: PROMPT_AI_TASK_LIST_ORCHESTRATOR.md                             │
│   Type: Deterministic reformat (structure already defined)              │
│                                                                         │
│   Because input structure mirrors output structure:                     │
│   - No interpretation needed                                            │
│   - No guessing at requirements                                         │
│   - Just reformatting from template to template                         │
│                                                                         │
│   Output: AI Task List in plan mode                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                OUTPUT PHASE 1: DETERMINISTIC VALIDATION                  │
│                                                                         │
│   Tool: tools/ai_task_list_linter.py                                    │
│   Type: Script (deterministic)                                          │
│   Deps: pyyaml                                                          │
│                                                                         │
│   Validates:                                                            │
│   ✓ YAML front matter (schema_version, mode, runner, search_tool)       │
│   ✓ Required sections present                                           │
│   ✓ Phase structure valid                                               │
│   ✓ Task structure valid (TDD steps, STOP blocks, checklists)           │
│   ✓ Paths arrays valid                                                  │
│   ✓ Preconditions have symbol checks                                    │
│   ✓ Evidence blocks structured correctly                                │
│   ✓ Runner/uv enforcement                                               │
│   ✓ Search tool enforcement                                             │
│   ✓ Import hygiene (Python projects)                                    │
│   ✓ Prose Coverage Mapping (plan/instantiated modes)                    │
│                                                                         │
│   Command:                                                              │
│     uv run python tools/ai_task_list_linter.py PROJECT_TASKS.md         │
│     uv run python tools/ai_task_list_linter.py --json [...]             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Exit 0
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                OUTPUT PHASE 2: SEMANTIC VALIDATION                       │
│                                                                         │
│   Tool: PROMPT_AI_TASK_LIST_REVIEW.md                                   │
│   Type: AI reasoning (requires judgment)                                │
│   Deps: AI assistant capable of reasoning + original prose input        │
│                                                                         │
│   Validates:                                                            │
│   ✓ Conversion fidelity (task list matches prose input)                 │
│   ✓ Preconditions meaningful (not too broad, grounded in reality)       │
│   ✓ TDD/objective alignment (tests actually test stated objective)      │
│   ✓ Coverage mapping complete (no orphan tasks, no missing reqs)        │
│   ✓ Paths traceable (all paths in prose File Manifest)                  │
│   ✓ No AI invention (no new decisions, paths, symbols invented)         │
│   ✓ Governance preserved (TDD, checklists, STOP blocks intact)          │
│   ✓ Success criteria measurable (not subjective)                        │
│   ✓ Test case quality (no weak tests)                                   │
│   ✓ Internal consistency (no contradictions, forward deps only)         │
│                                                                         │
│   Output:                                                               │
│     VERDICT: PASS (proceed to execution)                                │
│     VERDICT: FAIL (fix issues, return to conversion)                    │
│                                                                         │
│   Usage:                                                                │
│     1. Copy PROMPT_AI_TASK_LIST_REVIEW.md into AI context               │
│     2. Provide the task list that passed Output Phase 1                 │
│     3. Provide the original prose input for comparison                  │
│     4. AI produces review with explicit VERDICT                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ VERDICT: PASS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION                                        │
│                                                                         │
│   Human implements tasks following the task list                        │
│   Evidence captured and pasted                                          │
│   Mode transitions: plan → instantiated                                 │
│   Phase gates enforced                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Reference

| File | Type | Purpose |
|------|------|---------|
| `GOAL.md` | Spec | Framework goal definition (authoritative) |
| `PROMPT_PROSE_INPUT_DISCOVERY.md` | Prompt | Discovery: Gather project facts before writing spec |
| `PROSE_INPUT_SPEC.md` | Spec | Authoritative rules for prose input |
| `PROSE_INPUT_TEMPLATE.md` | Template | Mandatory input structure for new specs |
| `tools/prose_input_linter.py` | Script | Input Phase 1: Deterministic validation |
| `PROMPT_PROSE_INPUT_REVIEW.md` | Prompt | Input Phase 2: AI semantic review |
| `PROMPT_AI_TASK_LIST_ORCHESTRATOR.md` | Prompt | Conversion: Prose → Task List |
| `AI_TASK_LIST_SPEC.md` | Spec | Authoritative rules for task lists |
| `AI_TASK_LIST_TEMPLATE.md` | Template | Task list structure |
| `tools/ai_task_list_linter.py` | Script | Output Phase 1: Deterministic validation |
| `PROMPT_AI_TASK_LIST_REVIEW.md` | Prompt | Output Phase 2: AI semantic review |

---

## Division of Labor

### What Scripts Check (Deterministic)

| Check | Tool | Why Script |
|-------|------|------------|
| YAML syntax valid | `tools/prose_input_linter.py` | Parse error = objective |
| Section exists | `tools/prose_input_linter.py` | String match = objective |
| Placeholder absent | `tools/prose_input_linter.py` | Regex match = objective |
| TBD marker absent | `tools/prose_input_linter.py` | Regex match = objective |
| Checkbox checked | `tools/prose_input_linter.py` | String match = objective |
| Task ID format | `tools/ai_task_list_linter.py` | Regex match = objective |
| Evidence block present | `tools/ai_task_list_linter.py` | Structure match = objective |

### What AI Checks (Reasoning)

**Input Semantic Review:**

| Check | Tool | Why AI |
|-------|------|--------|
| Objective is clear | `PROMPT_PROSE_INPUT_REVIEW.md` | Requires understanding intent |
| Success criteria measurable | `PROMPT_PROSE_INPUT_REVIEW.md` | "Clean" vs "ruff passes" |
| Test covers behavior | `PROMPT_PROSE_INPUT_REVIEW.md` | Requires understanding code |
| Dependencies coherent | `PROMPT_PROSE_INPUT_REVIEW.md` | Requires logical reasoning |
| Scope bounded | `PROMPT_PROSE_INPUT_REVIEW.md` | "etc." detection in context |
| Risks realistic | `PROMPT_PROSE_INPUT_REVIEW.md` | Domain knowledge needed |

**Output Semantic Review:**

| Check | Tool | Why AI |
|-------|------|--------|
| Conversion fidelity | `PROMPT_AI_TASK_LIST_REVIEW.md` | Requires comparing prose to task list |
| Preconditions meaningful | `PROMPT_AI_TASK_LIST_REVIEW.md` | "rg def" too broad vs specific symbol |
| TDD/objective alignment | `PROMPT_AI_TASK_LIST_REVIEW.md` | Test must match stated objective |
| No AI invention | `PROMPT_AI_TASK_LIST_REVIEW.md` | Paths/symbols must trace to prose |
| Coverage complete | `PROMPT_AI_TASK_LIST_REVIEW.md` | No orphan tasks, no missing reqs |
| Test quality | `PROMPT_AI_TASK_LIST_REVIEW.md` | Weak tests detection in context |

---

## Validation Outcomes

### Phase 1 Outcomes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Structure valid | Proceed to Phase 2 |
| 1 | Validation errors | Fix errors, re-run Phase 1 |
| 2 | Schema/parse error | Fix YAML, re-run Phase 1 |
| 3 | File not found | Check path |

### Phase 2 Outcomes

| Verdict | Meaning | Action |
|---------|---------|--------|
| PASS | Content valid | Proceed to conversion |
| PASS + CONCERNS | Valid with notes | Proceed, author aware of concerns |
| FAIL | Content invalid | Fix issues, return to Phase 1 |

### Output Phase 1 Outcomes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Structure valid | Proceed to Output Phase 2 |
| 1 | Lint violations | Fix violations, re-run |
| 2 | Usage error | Check command |

### Output Phase 2 Outcomes

| Verdict | Meaning | Action |
|---------|---------|--------|
| PASS | Conversion valid | Ready for execution |
| PASS + CONCERNS | Valid with notes | Proceed, author aware of concerns |
| FAIL | Conversion invalid | Fix issues, re-convert or correct manually |

---

## Quick Start

### For New Specifications

```bash
# 0. (Optional) Run discovery to gather project facts
# In AI chat: paste PROMPT_PROSE_INPUT_DISCOVERY.md
# AI gathers facts from codebase → produces discovery report

# 1. Copy the input template
cp PROSE_INPUT_TEMPLATE.md my_spec.md

# 2. Fill in all sections (replace all [[PLACEHOLDER]] tokens)
# Use discovery report to fill Sample Artifacts section
# Edit my_spec.md...

# 3. Phase 1: Run deterministic linter
uv run python tools/prose_input_linter.py my_spec.md

# 4. Fix any errors, repeat step 3 until exit 0

# 5. Phase 2: AI review (in AI chat)
# Paste PROMPT_PROSE_INPUT_REVIEW.md
# Paste my_spec.md
# Wait for VERDICT: PASS

# 6. Convert to task list (in AI chat)
# Paste PROMPT_AI_TASK_LIST_ORCHESTRATOR.md
# Paste my_spec.md
# AI produces task list

# 7. Output Phase 1: Validate structure
uv run python tools/ai_task_list_linter.py my_tasks.md

# 8. Output Phase 2: AI review (in AI chat)
# Paste PROMPT_AI_TASK_LIST_REVIEW.md
# Paste my_tasks.md AND my_spec.md (for comparison)
# Wait for VERDICT: PASS

# 9. Execute tasks
```

---

## Why Two Phases at Both Ends?

### Problem with Single-Phase Validation

A script cannot check:
- "Is this objective actually clear?" (requires understanding)
- "Does this test actually test the behavior?" (requires reasoning)
- "Did conversion preserve intent?" (requires comparing two documents)
- "Are paths invented or traceable?" (requires codebase knowledge)

An AI alone cannot guarantee:
- "Is this YAML syntactically valid?" (might miss edge cases)
- "Does this match the required format exactly?" (pattern drift)
- "Are all forbidden tokens absent?" (might overlook)

### Solution: Complementary Validation at Both Ends

| Phase | Strength | Weakness |
|-------|----------|----------|
| Script | Consistent, fast, no false negatives on format | Cannot reason about meaning |
| AI | Understands context, catches semantic issues | May drift, slower, less consistent |

**Input validation**: Script catches structural issues; AI catches semantic issues in the prose spec.

**Output validation**: Script catches format violations; AI catches conversion drift and AI invention.

Together: **Mechanical correctness AND semantic quality at both ends**.

---

## Error Recovery

### Phase 1 Failure

```
$ uv run python tools/prose_input_linter.py my_spec.md
Line 45: [PIN-F02] Unfilled placeholder '[[PATH]]' found.
Line 89: [PIN-F01] Unresolved marker 'TBD' found.
```

**Action**: Edit `my_spec.md`, replace placeholders, resolve TBDs, re-run.

### Phase 2 Failure

```
## Verdict
**VERDICT: FAIL**

Blocking issues:
1. Task 1.2 Objective is vague: "Improve the handling"
2. Task 2.1 Success Criteria uses subjective term "clean code"
3. Circular dependency: Task 1.3 ↔ Task 1.4
```

**Action**: Edit spec to address issues, return to Phase 1 (re-validate structure after edits).

### Output Phase 1 Failure

```
$ uv run python tools/ai_task_list_linter.py my_tasks.md
my_tasks.md:145:R-ATL-D2:Task 1.2 Preconditions must include rg command.
```

**Action**: Fix task list structure, re-run linter.

### Output Phase 2 Failure

```
## Verdict
**VERDICT: FAIL**

Blocking issues:
1. Task 1.3 path `src/utils/helpers.py` not in prose File Manifest (AI invention)
2. Task 2.1 precondition `rg 'def' src/` too broad (matches everything)
3. Coverage gap: prose requirement "Add caching" has no corresponding task
```

**Action**: Re-convert or manually correct task list, return to Output Phase 1.

---

## Guarantees

When a document passes the complete pipeline (all 4 gates):

| Guarantee | Source |
|-----------|--------|
| Input structure matches spec | `tools/prose_input_linter.py` |
| No unresolved placeholders | `tools/prose_input_linter.py` |
| No ambiguous markers | `tools/prose_input_linter.py` |
| Objectives are clear | `PROMPT_PROSE_INPUT_REVIEW.md` |
| Success criteria measurable | `PROMPT_PROSE_INPUT_REVIEW.md` |
| Tests cover behavior | `PROMPT_PROSE_INPUT_REVIEW.md` |
| Dependencies valid | `PROMPT_PROSE_INPUT_REVIEW.md` |
| Task list format valid | `tools/ai_task_list_linter.py` |
| Governance baked in | `tools/ai_task_list_linter.py` |
| Conversion faithful to prose | `PROMPT_AI_TASK_LIST_REVIEW.md` |
| No AI invention | `PROMPT_AI_TASK_LIST_REVIEW.md` |
| Coverage complete | `PROMPT_AI_TASK_LIST_REVIEW.md` |
| Preconditions meaningful | `PROMPT_AI_TASK_LIST_REVIEW.md` |
| TDD aligned with objectives | `PROMPT_AI_TASK_LIST_REVIEW.md` |

---

## Limitations

### What This Cannot Guarantee

1. **Technical correctness** - The spec might describe the wrong solution
2. **Feasibility** - Tasks might be impossible to implement
3. **Completeness** - Requirements might be missing from the source
4. **Evidence authenticity** - Captured evidence can still be faked

### Mitigations

| Limitation | Mitigation |
|------------|------------|
| Wrong solution | Phase 0 discovery before committing |
| Impossible tasks | Precondition checks catch missing APIs |
| Missing requirements | Prose Coverage Mapping enforces tracing |
| Fake evidence | `--require-captured-evidence` raises cost of faking |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-16 | Initial complete validation pipeline |
| 1.1 | 2025-12-16 | Added two-phase output validation (implements GOAL.md §7) |

---

**End of Document**
