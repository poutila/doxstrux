# GOAL.md — AI Task List Framework Goal Definition

> **Version**: 1.0
> **Purpose**: Define what this framework exists to achieve and what success looks like.

---

## Goal Statement

**Produce an AI Task List from prose that:**

1. **Does not drift** — Output remains faithful to input; no interpretation creep
2. **Is as close to reality as possible** — Grounded in actual codebase state
3. **Can be validated against a specification with a linter** — Deterministic verification
4. **Has governance baked in** — TDD, no weak tests, uv enforcement, clean table, import rules, rg use
5. **Reduces iteration loops** — One well-prepared input yields usable output
6. **Minimizes AI guessing** — Explicit instructions, no ambiguity for executor
7. **Two-phase validation (input AND output)** — Deterministic linter + semantic AI review at both ends
8. **Maximally deterministic** — Heuristic parts receive facts; prompts prevent AI invention

---

## Sharpened Goal (Detailed)

### 1. Anchor to Single SSOT

- Every task list references `VERSION.yaml` for schema version
- Prose Coverage Mapping enforces traceability (task ↔ prose requirement)
- No orphan tasks; no undocumented requirements

### 2. Reality-First

- Precondition checks use real `rg` commands against actual codebase
- Evidence blocks contain captured output, not fabricated examples
- Sample Artifacts in prose input are pasted from running code, not guessed

### 3. Lintable

- Fixed `schema_version` in YAML front matter
- Deterministic linter rules with explicit rule IDs
- Exit codes: 0 = PASS, 1 = FAIL, 2 = schema error, 3 = file error
- JSON output mode for CI integration

### 4. Governance Baked In

| Governance Rule | Enforcement Mechanism |
|-----------------|----------------------|
| TDD | RED/GREEN/VERIFY steps required in each implementation task |
| No weak tests | Test Cases must have concrete assertions, not smoke checks |
| uv enforcement | `runner: uv` in front matter; linter rejects `pip`, `python -m pip` |
| Clean Table | No TODO/FIXME/TBC in final output; submission checklist enforced |
| Import rules | Absolute imports required; no `from ..x` patterns |
| rg use | Preconditions must use `rg` commands; `grep` rejected |

### 5. Reduced Iteration

- **Mode lifecycle**: `template` → `plan` → `instantiated`
- Template mode: placeholders allowed (scaffolding)
- Plan mode: real commands, placeholder evidence (ready to execute)
- Instantiated mode: no placeholders anywhere (execution complete)

### 6. Minimum Guessing

- Orchestrator prompt is unambiguous: reformat, don't interpret
- Manuals define every term; glossary in prose input
- File Manifest lists every file to be created/modified
- Decisions table captures all non-trivial choices with rationale

### 7. Two-Phase Validation (Input AND Output)

Both input and output are validated twice:

#### Input Validation (before conversion)

| Phase | Tool | Type | Catches |
|-------|------|------|---------|
| 1 | `tools/prose_input_linter.py` | Deterministic | Missing sections, placeholders, TBD markers, structural errors |
| 2 | `PROMPT_PROSE_INPUT_REVIEW.md` | Semantic (AI) | Vague objectives, subjective criteria, circular dependencies, missing negative tests |

#### Output Validation (after conversion)

| Phase | Tool | Type | Catches |
|-------|------|------|---------|
| 1 | `tools/ai_task_list_linter.py` | Deterministic | Missing YAML, invalid task IDs, missing TDD steps, runner violations |
| 2 | `PROMPT_AI_TASK_LIST_REVIEW.md` | Semantic (AI) | Drift from input, meaningless preconditions, lost tasks, TDD/objective mismatch |

**Why both phases are required at both ends:**

- Scripts cannot judge "Did conversion preserve intent?" — requires understanding
- AI cannot guarantee "Is task ID format valid?" — might miss edge cases
- Together: mechanical correctness AND semantic quality

**Validation flow:**

```
Prose Input → Input Ph1 → Input Ph2 → Conversion → Output Ph1 → Output Ph2
                 ↓            ↓                        ↓            ↓
             Exit 1:      VERDICT:                 Exit 1:      VERDICT:
             Fix struct   FAIL                     Fix struct   FAIL
```

### 8. Maximally Deterministic

The framework minimizes heuristic (AI-dependent) steps and feeds facts to those that remain.

**Determinism hierarchy:**

| Component | Type | Why |
|-----------|------|-----|
| Linters | Deterministic | Same input → same output, always |
| Templates | Deterministic | Structure fixed, only values change |
| Discovery | Heuristic + facts | AI runs commands, pastes actual output |
| Conversion | Heuristic + facts | AI reformats, doesn't interpret |
| Review | Heuristic + facts | AI judges against explicit criteria |

**Preventing AI invention:**

| Mechanism | Implementation |
|-----------|----------------|
| Facts before prompts | Discovery report pasted into prose input before AI sees it |
| Sample Artifacts section | Real `ls`, `rg`, JSON output pasted — AI cannot invent paths |
| Explicit decision tables | Choices already made — AI cannot choose differently |
| Bounded vocabulary | Glossary defines terms — AI cannot redefine |
| Precondition commands | Real `rg` patterns from codebase — AI cannot fabricate symbols |

**Prompt formatting rules:**

1. **Facts first** — Paste discovered facts before asking AI to act
2. **No open questions** — All `?` resolved before AI prompt
3. **Explicit constraints** — "You MUST use these paths" not "find appropriate paths"
4. **Output structure mandated** — Template shows exact format, AI fills values
5. **Rejection patterns** — Prompts list what AI must NOT do (invent, guess, assume)

**Example — Discovery before conversion:**

```markdown
<!-- GOOD: Facts provided -->
## Sample Artifacts
### Existing Files
$ ls src/doxstrux/models/
__init__.py
section.py
paragraph.py

<!-- AI now knows exactly what exists — cannot invent "utils.py" -->
```

```markdown
<!-- BAD: No facts -->
## Sample Artifacts
(To be discovered by AI assistant)

<!-- AI will guess/invent file structure -->
```

---

## What Ideal Output Looks Like

Given a well-formed prose input (e.g., `PYDANTIC_SCHEMA.md`), the AI Task List should exhibit:

### Structure

| Element | Expectation |
|---------|-------------|
| Phases | 1:1 mapping to prose milestones (Phase 0 = Discovery, Phase 1 = Milestone A, etc.) |
| Tasks | Every prose requirement appears as a task; no orphans, no gaps |
| IDs | Sequential within phase (0.1, 0.2, 1.1, 1.2, etc.) |
| STOP blocks | Present at every phase gate; require human approval |

### Preconditions

```bash
# GOOD: Real check against actual codebase
$ rg -n 'class MarkdownParserCore' src/doxstrux/markdown_parser_core.py

# BAD: Placeholder or fictional path
$ rg -n '[[SYMBOL]]' [[FILE]]
```

### TDD Specification

| Step | Requirement |
|------|-------------|
| RED | Specific test name: `test_pydantic_model_validates_section_structure` |
| GREEN | Specific implementation: "Create `Section` model in `src/doxstrux/models/section.py`" |
| VERIFY | Actual command: `uv run pytest tests/test_section.py -v` |

### Test Cases

```python
# GOOD: Concrete assertion
def test_section_rejects_negative_line_number():
    """Section.start_line must be >= 1."""
    with pytest.raises(ValidationError):
        Section(id="sec_1", level=1, title="Test", start_line=-1)

# BAD: Smoke test
def test_section_works():
    """It should work."""
    s = Section(...)
    assert s is not None
```

### Success Criteria

```markdown
# GOOD: Measurable
- [ ] `uv run pytest tests/test_section.py -v` passes
- [ ] `uv run mypy src/doxstrux/models/section.py` returns 0 errors
- [ ] `rg 'class Section' src/doxstrux/models/section.py` returns match

# BAD: Subjective
- [ ] Code is clean and well-organized
- [ ] Implementation is complete
```

### Decisions Table

| ID | Decision | Rationale | Alternatives Rejected |
|----|----------|-----------|----------------------|
| D1 | Use Pydantic v2 BaseModel | Native validation, JSON schema export | dataclasses (no validation), attrs (extra dep) |
| D2 | Strict mode for all models | Catch typos in field names | Permissive mode (silent failures) |

### Evidence Blocks

```markdown
<!-- GOOD: Captured output -->
**Evidence (captured)**:
```
$ uv run pytest tests/test_section.py -v
============================= test session starts ==============================
tests/test_section.py::test_section_validates_id PASSED
tests/test_section.py::test_section_rejects_negative_line PASSED
============================= 2 passed in 0.03s ================================
```

<!-- BAD: Placeholder -->
**Evidence**:
```
[[PASTE_TEST_OUTPUT_HERE]]
```
```

---

## What Would Disappoint

If the AI Task List output exhibits any of these, the framework has failed:

| Anti-Pattern | Example |
|--------------|---------|
| Vague objectives | "Implement the schema" instead of "Create Section Pydantic model with id, level, title, start_line fields" |
| Placeholder preconditions | `rg '[[SYMBOL]]' [[FILE]]` |
| Smoke tests only | `assert model is not None` |
| Subjective criteria | "Code should be clean" |
| Missing decisions | Major choices made implicitly without documentation |
| No phase gates | Tasks flow without STOP blocks for human review |
| Fictional evidence | Test output that wasn't actually run |
| Orphan tasks | Tasks not traceable to prose requirements |
| Missing negative tests | Only happy path covered |
| Invented paths/symbols | `src/utils/helpers.py` that doesn't exist in discovery facts |
| AI-chosen alternatives | Decision made by AI when Decisions table was empty |

---

## Success Metric

The framework succeeds when:

1. **Input validated (both phases)** — `prose_input_linter.py` exits 0, `PROMPT_PROSE_INPUT_REVIEW.md` returns VERDICT: PASS
2. **Output validated (both phases)** — `ai_task_list_linter.py` exits 0, `PROMPT_AI_TASK_LIST_REVIEW.md` returns VERDICT: PASS
3. **Coverage complete** — Prose Coverage Mapping shows 100% requirement coverage
4. **Executor can start immediately** — No clarifying questions needed
5. **Evidence is authentic** — All captured output is reproducible
6. **Governance is visible** — TDD steps, uv commands, rg checks present throughout
7. **No AI invention** — All paths, symbols, commands traceable to discovery facts or prose input

---

## Non-Goals

What this framework explicitly does NOT attempt:

| Non-Goal | Reason |
|----------|--------|
| Guarantee technical correctness | Spec might describe wrong solution |
| Ensure feasibility | Tasks might be impossible |
| Complete requirements | Source prose might be incomplete |
| Prevent evidence fabrication | Can only raise cost of faking |
| Replace human judgment | Semantic review still needed |

---

**End of Document**
