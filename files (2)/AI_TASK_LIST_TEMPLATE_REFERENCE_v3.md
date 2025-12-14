# AI_TASK_LIST_TEMPLATE — Reference Guide

**Version**: 3.0  
**Purpose**: Reference material for the minimal template. Consult when stuck, not during execution.  
**The template**: `AI_TASK_LIST_TEMPLATE_v3.md` (~200 lines, enforceable-only)

---

## How to Use This Guide

**Execute from the template**, not this guide. This guide is for:
- Understanding *why* a rule exists
- Looking up edge cases
- Training new team members
- Debugging when something goes wrong

If you're reading this during task execution, you're probably over-thinking it.

---

## The Six Invariants (explained)

The template lists six non-negotiable invariants. Here's the rationale:

| Invariant | Why It Exists | What Breaks Without It |
|-----------|---------------|------------------------|
| Clean Table delivery gate | Prevents "done but broken" | Debt accumulates silently |
| No silent errors | Makes failures visible | Bugs hide until production |
| No weak tests | Tests prove behavior | Stubs satisfy tests |
| Single runner principle | Consistent execution | "Works on my machine" |
| Evidence anchors | Claims are verifiable | AI invents facts |
| No synthetic reality | Baseline is real | Planning diverges from reality |

---

## The Four Drift Killers (explained)

1. **`[[PH:NAME]]` placeholders** — Single format, grep-able, no false positives
2. **Phase 0 baseline** — Can't plan without knowing current state
3. **Canonical path lists** — One list for header AND verification
4. **Single runner** — Same command everywhere

---

## Derived Governance (v3.0)

The template enforces rules from these governance categories:

| Category | What It Contributes |
|----------|---------------------|
| Clean Table | No placeholders, no TODOs, no deferrals, no silent errors |
| No Weak Tests | Semantic assertions, fixture-driven, fail-before/pass-after |
| Single Runner | One canonical runner, no mixing styles |
| Evidence Discipline | Evidence anchors, decision chains, stop rules |
| Code Quality | KISS/YAGNI/SOLID gates, real consumers required |

**Note**: Specific governance document names (e.g., `CLEAN_TABLE_PRINCIPLE.md`) belong in your instantiated project task list, not in the general template.

---

## The Four Drift Killers (v3.0)

1. **Single placeholder syntax `[[PH:NAME]]`** — Makes "no placeholders" enforceable and non-noisy
2. **Phase 0 baseline reality** — Forces capture of actual repo state before planning becomes fiction
3. **Canonical file lists per task** — Prevents "Files:" headers diverging from verification scripts
4. **Single runner principle** — One canonical runner used everywhere (no mixing)

---

## Runner Selection (Single Runner Principle)

Pick exactly one canonical runner and use it for ALL commands:

| Ecosystem | Runner | Example |
|-----------|--------|---------|
| Python + uv | `uv run` | `uv run pytest tests/` |
| Python + poetry | `poetry run` | `poetry run pytest tests/` |
| Python + pip | `python -m` | `python -m pytest tests/` |
| Node + npm | `npm run` | `npm run test` |
| Node + pnpm | `pnpm` | `pnpm test` |
| Rust | (implicit) | `cargo test` |
| Go | (implicit) | `go test ./...` |

**Do not mix styles** — if you declare `uv run`, never use `.venv/bin/python`.

---

## What "General-Only" Means (v3.0)

A general-only template must contain:
- **No project names** (e.g., no "DOXSTRUX", "MyProject")
- **No repo paths** (e.g., no "src/doxstrux/...")
- **No project-specific environment variables** (e.g., no "DOXSTRUX_UV_RUN")
- **No assumptions about specific language tooling** beyond "single runner principle"

If you need a project-specific detail, it belongs in the **instantiated** `PROJECT_TASKS.md`, not in the template.

---

## No Weak Tests (v3.0 Task Gate)

Every task has a "No Weak Tests Gate" checklist. A task's tests are **invalid** if any of these apply:

**Forbidden test patterns:**
- Import-only tests
- "Runs without crashing" smoke tests without semantic assertions
- Existence-only assertions ("file exists", "function exists")
- Line-count/length thresholds as primary proof
- Exit-code-only checks without output/content assertions

**Required properties:**
- A stub/no-op implementation must **FAIL** the test
- At least one negative case exists for critical behavior (errors/safety)
- Assertions prove semantics (structure/content), not just presence

**The checklist:**
```
No Weak Tests Gate (all must be YES):
- [ ] Would a stub/no-op implementation FAIL this test? → Must be YES
- [ ] Does test assert semantics (structure/content), not just presence? → Must be YES
- [ ] Is there at least one negative case for critical behavior? → Must be YES
- [ ] Is the test NOT any of: import-only, smoke, existence-only, line-count, exit-code-only? → Must be YES
```

---

**Single format**: `[[PH:PLACEHOLDER_NAME]]`

**Single format**: `[[PH:PLACEHOLDER_NAME]]`

This format:
- Does NOT collide with markdown links `[text](url)`
- Does NOT collide with checkboxes `[ ]` or `[x]`
- Is machine-detectable: `grep -RInE '\[\[PH:[A-Z0-9_]+\]\]'`
- Has zero false positives

**Pre-flight check** (must return zero matches):
```bash
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && exit 1 || true
```

---

## Minimalism Guidance (v3.0)

**Principle**: Smaller templates drift less.

- If a rule is not enforced by a command → it's guidance, not governance
- If a rule exists in both guide and template → keep only in template (single SSOT)
- If a mechanism isn't necessary to prevent drift → remove it

---

## What This Template Solves

| Problem | Solution in Template |
|---------|---------------------|
| AI drifts from task | ⛔ STOP checkpoints force re-verification |
| Tasks marked "done" but aren't | Clean Table gates block progress |
| Tests written as afterthought | TDD protocol: test first, always |
| Phase N+1 starts before N is stable | Phase unlock artifacts required |
| "I'll fix it later" debt | No proceeding with failing tests |
| **"It runs" tests capture nothing** | **Test Strength Rules forbid weak tests** |
| **Files listed but never created** | **File Manifest verification** |
| **Placeholders committed to repo** | **`[[PH:X]]` format + pre-flight check** |
| **Hard-coded paths break portability** | **Environment Portability Rules** |
| **Later phases relax TDD** | **Every phase requires test skeletons** |
| **Spec and code disagree** | **Source of Truth Hierarchy** |
| **Premature strict validation** | **Strictness Gate Protocol** |
| **Tests for non-existent features** | **Unimplemented Feature Protocol** |
| **Symbol names don't match code** | **Code-First Verification** |
| **Models defined from docs, not code** | **Discovery-First Protocol** |
| **Spec treated as implementation** | **Spec Interpretation Rules** |
| **Speculative "might need" code** | **YAGNI Decision Tree** |
| **Over-engineered solutions** | **KISS mandate (simplest viable)** |
| **God classes, tangled code** | **SOLID principles (SRP, etc.)** |
| **Swallowed exceptions hide bugs** | **No Silent Errors rule** |
| **"Temporary" fixes become permanent** | **No Hidden Debt rule** |
| **Import-only/smoke tests** | **Explicit weak test patterns forbidden** |
| **Tasks marked done without verification** | **Reflection Loop mandatory** |
| **Proceeding when uncertain** | **Stop on Ambiguity rule** |
| **Unclear reasoning for decisions** | **Thinking vs Execution separation** |
| **Claims without proof** | **Evidence anchors required (source:line + quote)** |
| **Assumptions confused with facts** | **Semantic types (Fact/Claim/Assumption/Risk)** |
| **Decisions without rationale** | **Decision chains + trace links** |
| **Unverified assumptions proceed** | **Must verify or flag as risk** |
| **Duplicate task IDs cause confusion** | **Task ID Uniqueness rule** |
| **Appendix doesn't track all tasks** | **File tracking completeness verification** |
| **Clean Table only checks some files** | **Global Clean Table enforcement** |
| **Defined patterns ignored in examples** | **Aspirational vs Actual alignment** |
| **Tests check existence not correctness** | **Semantic correctness tests required** |
| **Tests skip on missing pre-run** | **Pre-run dependency handling** |
| **Scope creep / unclear boundaries** | **Scope Decisions table** |
| **Exit code 0 or 1 both "pass"** | **Exit code tolerance explicitly forbidden** |
| **"Prints something" = passes** | **Plausible output tests forbidden** |
| **Heredoc literals committed** | **Placeholder detection in generated artifacts** |
| **Skip in docs, hard-fail in tests** | **Skip pattern consistency rule** |
| **CI tests check strings, not wiring** | **CI workflow tests must verify structure** |
| **Schema changes without history** | **Version changelog governance** |
| **Tools pass tests but do no work** | **No-Op Stub Tool detection** |
| **Early phases have weaker gates** | **Phase Gate Scope Alignment** |
| **Placeholder edit → forget re-test** | **Temporal Debt Window prevention** |
| **Weak test looks like oversight** | **Conscious Trade-off Documentation** |
| **Spec and task list drift** | **Cross-Document SSOT management** |
| **"Required" dep but tests skip** | **Required vs Optional dependency clarity** |
| **Package manager for setup only** | **Package Manager Consistency** |
| **CI and local use different commands** | **CI/Local Workflow Identity** |
| **Lockfile edited manually** | **Dependency SSOT Structure** |
| **Manifest committed without lockfile** | **Dependency SSOT Structure** |
| **Multiple tools manage environment** | **Environment Ownership** |
| **Direct calls in activated shell** | **"Even when activated" rule** |
| **Violations not clearly labeled** | **Drift Labeling** |
| **Ambiguous placeholder patterns** | **Machine-Detectable Placeholder Tokens** |
| **Strictness confused with error handling** | **Strictness vs Error Handling clarification** |
| **Shell syntax errors in docs** | **Shell Command Correctness** |
| **Grep fails on different platforms** | **Grep Portability** |
| **Scope rules create deadlocks** | **Procedural Deadlock Detection** |
| **Exclusions not tracked** | **Scope Delta Ledger** |
| **Test serves two conflicting purposes** | **Test Role Disambiguation** |
| **Evidence requirements too heavy** | **Evidence Anchor Scoping** |
| **Drift repairs not logged** | **Drift Repair Entry Format** |
| **File list in two places, can drift** | **Canonical FILE_LIST Block** |
| **Tests use >= N (fabricatable)** | **Exact Count Testing** |
| **Invalid fixtures only malformed JSON** | **Deliberate Schema-Invalid Fixtures** |
| **Env override bypasses "mandatory" tool** | **Override Escape Hatch Scoping** |
| **Rule sounds universal, only enforced later** | **Phased Enforcement Honesty** |
| **Tests assume dict, break on refactor** | **Structural vs Semantic Assumptions** |
| **Tests encode policy as hard invariant** | **Policy vs Safety Invariant Tests** |
| **Tests don't break when code evolves** | **Forced Refactor Tests** |
| **Claiming local discipline, relying on CI** | **CI as Last Safety Net** |
| **Bracket placeholders collide with markdown** | **[[PH:X]] format + pre-flight check** |
| **No baseline reality capture** | **Mandatory Baseline Snapshot** |
| **Two file lists (header vs verification)** | **Canonical FILE_LIST array** |
| **Template bloat reduces adoption** | **Minimalism guidance** |
| **Test strength is advisory** | **No Weak Tests as task gate** |
| **Rules seem arbitrary** | **Derived governance declaration** |

---

## Core Concepts

### 1. STOP Checkpoints

Every task ends with:
```markdown
### ⛔ STOP: Clean Table Check
- [ ] Test passes
- [ ] **Test is strong** (fails with stub)
- [ ] Full suite passes
- [ ] No new debt
- [ ] **All "Files:" exist**
```

**Rule**: AI must verify ALL boxes before moving on.

### 2. Phase Gates

```
Phase 0 ──► .phase-0.complete.json ──► Phase 1 ──► ...
```

Cannot start Phase N+1 until:
- All Phase N tasks complete
- Phase N tests pass
- Clean Table verified
- `.phase-N.complete.json` artifact created
- **File manifest verified**
- **No placeholders in artifact**

### 3. TDD Protocol (Every Task)

```
1. Write test (RED)    ← Test fails because code doesn't exist
2. Implement (GREEN)   ← Minimal code to pass
3. Verify (CLEAN)      ← Full suite, no regressions
```

### 4. Clean Table Definition

A task is **NOT COMPLETE** if any of these exist:
- Failing tests
- TODOs/FIXMEs in new code
- Unverified assumptions
- "We'll fix it later" items
- **Files listed but not created**
- **Tests that pass with stub implementations**
- **Literal placeholders in committed files**

---

## NEW in v2+: Anti-Drift Mechanisms

### 5. Test Strength Rules

**The core problem**: Tests like `assert returncode == 0` don't verify behavior. A stub implementation that does nothing passes these tests.

**The solution**: Every test must have assertions that would **fail** with a stub implementation.

> Examples use Python, but patterns apply to any language: check output content, not just exit codes.

```python
# ❌ FORBIDDEN - passes with empty implementation
def test_discover():
    result = subprocess.run(["./tools/discover"])
    assert result.returncode == 0

# ✅ REQUIRED - fails with empty implementation
def test_discover():
    result = subprocess.run(["./tools/discover"])
    assert result.returncode == 0
    
    # These assertions FAIL if tool does nothing:
    output = Path("output.txt")
    assert output.exists()
    lines = output.read_text().strip().split("\n")
    assert len(lines) >= 10  # Must produce real output
    assert "expected_key" in lines  # Must have specific content
```

**Self-check question**: "Would this test pass if the function returned `None` or empty?"
- If YES → Test is too weak, strengthen it
- If NO → Test is acceptable

### 6. File Manifest Verification

**The core problem**: Task headers list files that are never actually created ("ghost files"). This creates confusion and drift.

**The solution**: Every file listed in a task's `Files:` header must:
1. Have a creation/modification step in that task
2. Actually exist after task completion
3. Be verifiable via `test -f`

### 7. Placeholder Prevention

**The core problem**: Phase artifacts with literal `YYYY-MM-DD` or `[PLACEHOLDER]` get committed.

**The solution**: Artifact generation uses shell variables that expand at runtime.

### 8. Environment Portability

**The core problem**: Hard-coded paths break on different systems.

**The solution**: Use portable patterns (runtime self-reference, package manager invocation, shell lookup).

### 9. Source of Truth Hierarchy

**The core problem**: Design docs and code disagree. Which wins?

**The solution**: Explicit authority hierarchy:

```
1. Running code output      (highest - always wins)
2. Generated samples        
3. Implementation code      
4. Task list               
5. Design specs            (lowest - aspirational only)
```

**Rule**: When higher-authority source differs from lower → update the lower source, never the higher.

### 10. Strictness Gates

**The core problem**: Someone jumps straight to strict validation without verifying loose version works.

**The solution**: Cannot tighten constraints until loose version passes on N real inputs.

```
Loose mode passes on 10+ test inputs → OK to tighten
Strict mode fails → Fix model/code, NOT the inputs
```

### 11. Unimplemented Feature Protocol

**The core problem**: Design docs describe future features. Tests get written for things that don't exist.

**The solution**: Before testing ANY feature:
1. Verify it exists in code (grep)
2. Verify it produces expected output (run it)
3. Only then write assertions

For reserved/planned features:
- Define with safe defaults (Optional, None)
- DO NOT assert specific values
- Mark clearly as "reserved"

### 12. Code-First Verification

**The core problem**: Design docs reference class names, methods, constants that don't exist or have different names.

**The solution**: Before using ANY symbol from design doc:
1. grep for exact symbol name
2. Verify signature matches
3. If mismatch → update task list, NOT code

### 13. Discovery-First Protocol

**The core problem**: Models defined from design docs don't match actual code output.

**The solution**: When building models for existing code:
1. RUN existing code with representative inputs
2. CAPTURE actual outputs
3. ANALYZE outputs for structure
4. DERIVE models from actual outputs
5. VALIDATE models against outputs
6. Only then write tests

Never define models from design docs alone.

### 14. Code Quality Gates (SOLID/KISS/YAGNI)

**The core problem**: Speculative code, over-engineering, and "might need later" features create maintenance burden and drift.

**The solution**: Three mandatory principles enforced at task completion:

**SOLID** (design quality):
- Single Responsibility: One module, one purpose
- Open/Closed: Extend without modifying
- Liskov Substitution: Subtypes must be substitutable
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: Depend on abstractions

**KISS** (simplicity):
- Always choose simplest solution that works
- Document why complex solution was needed (if ever)

**YAGNI** (feature discipline):
- Decision tree must pass before implementing any new code
- Q1: Current requirement exists?
- Q2: Immediate consumer exists?
- Q3: Backed by data/stakeholder (not speculation)?
- Q4: Cannot be added later?
- If any Q1-Q3 is NO → don't implement
- If Q4 is YES → defer until needed

### 15. No Silent Errors

**The core problem**: Swallowed exceptions, conditional error handling, and "strict mode" toggles hide bugs and create unpredictable behavior.

**The solution**: All errors must raise unconditionally. There is no strict mode.

**Forbidden patterns**:
- `if strict: raise` (conditional)
- `except: print(warning); continue` (swallowed)
- `def func(strict=True)` (toggle parameter)
- `if os.environ.get("STRICT")` (env var toggle)
- `errors.append(e); continue` (collected but not raised)

**Required pattern**:
- `except Exception as e: raise SpecificError(context, e) from e`

### 16. No Hidden Debt

**The core problem**: "Temporary" fixes, "adjust later" comments, and workarounds become permanent technical debt.

**The solution**: Clean Table requires no deferred work in completed tasks:
- No "temporary" fixes masking root causes
- No "you may need to adjust" comments
- No workaround logic instead of proper fixes
- Solution must be canonical and stable

### 17. Reflection Loop

**The core problem**: Tasks get marked complete without verifying objectives were achieved, assumptions were valid, or uncertainties were addressed.

**The solution**: Mandatory reflection before completing any task:

1. **PAUSE** - Don't rush to next task
2. **REFLECT** - Answer key questions:
   - Did I achieve the objective?
   - Can I provide evidence for claims?
   - Did I verify assumptions?
   - Are there unmitigated risks?
   - Am I uncertain about anything?
3. **VALIDATE** - Check success criteria + evidence anchors
4. **DECIDE** - Proceed, fix, or STOP

**Semantic Type Distinctions**: When reflecting, categorize statements:
- **FACT**: Verified true (must have evidence anchor)
- **CLAIM**: Assertion (must have supporting evidence)
- **ASSUMPTION**: Unverified belief (must verify or flag as risk)
- **RISK**: Potential problem (must mitigate or explicitly accept)
- **HYPOTHESIS**: Testable proposition (must test and record result)

**Evidence Anchors**: Every significant claim must have:
```
CLAIM: [assertion]
SOURCE: [file:line]
QUOTE: "[exact supporting text]"
```

**Trace Links**: Connect decisions to evidence:
```
DECISION → EVIDENCE (source:line) → IMPACT
```

### 18. Stop on Ambiguity

**The core problem**: Proceeding with uncertainty leads to wrong implementations that need rework.

**The solution**: Explicit STOP conditions:
- Confidence < 80%
- Missing required information
- Conflicting requirements
- Unverifiable assumptions
- Unclear success criteria
- Multiple valid interpretations

When stopping, use the Stop Block Template:
```
⛔ STOP: CLARIFICATION REQUIRED
BLOCKING: [what's missing]
REASON: [why can't proceed]
NEEDED: [what info required]
NEXT STEP: [what happens after]
```

### 19. Thinking vs Execution Boundaries

**The core problem**: Mixing reasoning with action makes it hard to review logic and identify where things went wrong.

**The solution**: Explicitly separate:

**THINKING** (reasoning):
- Assumptions, risks, trade-offs
- Alternative approaches
- Why chosen approach is best

**EXECUTION** (action):
- Exact command/code
- Expected output
- How to validate

This makes mistakes distinguishable (logic error vs implementation error).

### 20. Task ID Uniqueness

**The core problem**: Same task ID used for different tasks causes confusion and breaks file tracking.

**The solution**:
- Every task has unique ID (X.Y or X.Y.Z)
- Every slice mentioned has explicit ID
- Appendix/tracking covers ALL IDs
- Audit for duplicates before execution

### 21. Global Clean Table Enforcement

**The core problem**: Ad-hoc greps only check some files, missing debt in others.

**The solution**:
- Single global check across entire repo
- Phase artifacts checked for placeholders
- Ideally: automated test that fails on any violation
- Never selective/partial checks

### 22. Aspirational vs Actual Alignment

**The core problem**: Document defines helper/pattern but examples ignore it.

**The solution**:
- If you define a pattern, use it in ALL examples
- Never show "wrong way" in executable code blocks
- Audit: search for pattern violations in your own doc
- Readers copy-paste examples; make them correct

### 23. Existence vs Correctness Tests

**The core problem**: Tests check "file exists" but not "file is correct".

**The solution**:
- Existence tests are not sufficient
- Parse output and verify expected fields/values
- Check semantic correctness, not just presence
- Stub that writes "{}" should fail

### 24. Pre-Run Dependency Handling

**The core problem**: Tests skip if required files don't exist; CI passes with 0 tests.

**The solution** (choose and document):
- Option A: Gate ensures pre-run before tests
- Option B: Test runs tool itself (integration)
- Option C: Fixture generates required files

### 25. Scope Decisions Table

**The core problem**: Unclear what's in/out of scope causes scope creep and confusion.

**The solution**:
- Explicit table at top of task list
- IN SCOPE items with rationale
- OUT OF SCOPE items with rationale
- Anyone reading knows what WON'T be done

### 26. Version Changelog Governance

**The core problem**: Schema/API changes happen without history, making it impossible to track what changed when.

**The solution**:
- CHANGELOG file exists for versioned artifacts
- Every schema change adds changelog entry
- CI can enforce: "if schema changed, changelog changed"
- Version numbers follow semantic versioning

### 27. Skip Pattern Consistency

**The core problem**: Guidelines say "skip if tool missing" but tests hard-fail. Half-committed.

**The solution**:
- Decide: REQUIRED (hard-fail) or OPTIONAL (skip)
- Apply consistently across all tests
- Remove conflicting guidance
- Either all tests skip, or no tests skip

### 28. Heredoc Placeholder Detection

**The core problem**: Task list heredocs contain literal placeholders like `YYYY-MM-DD` that get committed.

**The solution**:
- Use shell variable substitution: `$(date -u +%Y-%m-%dT%H:%M:%SZ)`
- Or explicit "replace before commit" instruction
- Global check for common placeholder patterns
- Test that generated artifacts contain no placeholders

### 29. CI/Workflow Test Strength

**The core problem**: CI tests that just check "string X appears in YAML" pass with dummy workflows.

**The solution**:
- Check correct wiring, not just string presence
- Verify step order (install before test)
- Verify actual commands, not echo statements
- Check dependency installation steps exist

### 30. No-Op Stub Tool Detection

**The core problem**: Tools can satisfy all tests by returning canned data without touching real inputs.

**The solution**:
- Test with KNOWN-GOOD input: `total > 0, passed > 0`
- Test with KNOWN-BAD input: `failed > 0`, specific error message
- Assert tool actually calls validation function (mock/spy if needed)
- Exit code must match actual results, not canned values

### 31. Phase Gate Scope Alignment

**The core problem**: Global rules enforced locally in early phases, globally only in later phases.

**The solution**:
- If rule is global, ALL phase gates enforce it globally
- Or: Global test exists from Phase 0 (not introduced later)
- Phase gates reference global test, don't duplicate with narrower scope

### 32. Temporal Debt Window Prevention

**The core problem**: Create placeholder → tests pass → edit → forget to re-test → commit debt.

**The solution** (choose one):
- **Option A**: Never create placeholders (shell substitution)
- **Option B**: Pre-commit hook catches placeholders
- **Option C**: CI as safety net (current approach)
- Document which option and its trade-offs

### 33. Conscious Trade-off Documentation

**The core problem**: Weak tests look like oversights; readers don't know if intentional.

**The solution**:
- Comment explaining WHY test is limited
- What risk is accepted
- What would break if assumption is wrong
- Whether stronger test was considered and rejected

### 34. Cross-Document SSOT Management

**The core problem**: Spec and task list can drift; two documents, two "truths".

**The solution**:
- Mark spec as HISTORICAL once task list exists
- Or: Task list references spec with explicit scope delta
- If spec is active, sync changes both ways
- Never have overlapping scope without cross-reference

### 35. Required vs Optional Dependency Clarity

**The core problem**: "REQUIRED" in docs, but tests skip when missing. False sense of enforcement.

**The solution**:
- **REQUIRED**: CI and local must have; tests hard-fail
- **REQUIRED FOR CI, OPTIONAL LOCAL**: Tests skip locally; document this
- **FULLY OPTIONAL**: Tests always skip if missing
- Never say "REQUIRED" if tests skip

### 36. Package Manager Consistency

**The core problem**: Project declares a package manager but examples use raw paths.

**The solution**:
- If package manager declared, ALL commands use it
- "Never call X directly" rule documented
- Examples match declared tool
- No partial integration (setup only)

Examples:
- Python (uv): `uv run python script.py` not `.venv/bin/python script.py`
- Python (poetry): `poetry run pytest` not `.venv/bin/pytest`
- Node (npm): `npm run script` not `node script.js`

### 37. CI/Local Workflow Identity

**The core problem**: CI uses one command style, local docs show another.

**The solution**:
- Same command works locally AND in CI
- Documentation shows CI-identical command
- Phase gates use CI-identical commands
- Copy-paste works both directions

Benefits:
- No translation when debugging CI failures
- Single source of truth for "how to run X"
- Reduces "works on my machine" issues

### 38. Dependency SSOT Structure

**The core problem**: Dependencies declared in one place, locked in another, edited inconsistently.

**The solution**:
- Two files: manifest (what you want) + lockfile (exact versions)
- NEVER edit lockfile manually
- ALWAYS commit both together after changes
- CI installs from lockfile for reproducibility

### 39. Environment Ownership

**The core problem**: Multiple tools creating/managing the same environment.

**The solution**:
- Only the declared tool creates .venv/
- No manual pip installs when using uv/poetry
- If corrupted: delete and re-sync
- Even when activated, prefer tool commands

### 40. Drift Labeling

**The core problem**: Violations exist but aren't clearly marked as wrong.

**The solution**:
- Explicitly label violations as "drift"
- Make drift searchable: `grep -rn "\.venv/bin/python"`
- Document that drift should be removed
- Hard rule format: "Any X usage is **drift** and should be removed"

### 41. Machine-Detectable Placeholder Tokens

**The core problem**: `grep "\[.*\]"` matches normal markdown, creating noise.

**The solution**:
- Use explicit format: `[[PH:PLACEHOLDER_NAME]]`
- Detector: `grep '\[\[PH:'` - noise-free
- Self-documenting (name says what's needed)
- Easy to find and replace

### 42. Strictness vs Error Handling Disambiguation

**The core problem**: "Strictness gates" and "no silent errors" sound contradictory.

**The solution**:
- Strictness = validation constraint progression (what triggers error)
- Error handling = always unconditional (whether errors raise)
- These are orthogonal: errors raise at every strictness level
- Add clarifying sentence: "Strictness refers to validation constraints, not error-handling behavior"

### 43. Shell Command Correctness

**The core problem**: Shell snippets have syntax errors that become copy-paste traps.

**The solution**:
- Use correct command substitution: `VAR="$(cmd)"` not `VAR=[cmd]`
- Quote variables: `"${ARRAY[@]}"` not `$ARRAY`
- Add error handling: `|| { echo "Failed"; exit 1; }`
- Every snippet must be syntactically correct

### 44. Grep Portability

**The core problem**: Grep behaves differently on GNU vs BSD (macOS).

**The solution**:
- Use portable form: `grep -RInE '(TODO|FIXME|XXX)'`
- Or document "GNU grep required"
- Or use cross-platform tools (ripgrep, Python)

### 45. Procedural Deadlock Detection

**The core problem**: Two "cannot change X" rules with no escape path = stuck.

**The solution**:
- For each constraint, ask "what if Y depends on X?"
- Every scope constraint needs an escape path:
  - Option A: Exception category
  - Option B: xfail with rationale
  - Option C: Escalation path

### 46. Scope Delta Ledger

**The core problem**: Prose exclusions are forgotten; no audit trail.

**The solution**:
- Maintain explicit table: Excluded Item | Why | Consequence | Follow-on
- Track what invariants are NOT guaranteed
- Track where/when excluded items will be addressed

### 47. Test Role Disambiguation

**The core problem**: Same test trying to be milestone-driver AND branch-guard.

**The solution**:
- Milestone driver: Must run and fail until goal achieved
- Branch guard: Skips on feature branches, runs on main
- If you need both: write two tests
- Never have "Expected: FAIL" in a test that sometimes skips

### 48. Evidence Anchor Scoping

**The core problem**: Unbounded evidence requirements create "evidence theater".

**The solution**:
- Mandatory for: API changes, safety claims, performance claims, architectural decisions
- Optional for: Small refactors, doc updates, trivial facts
- Focus effort on high-risk claims

### 49. Drift Repair Entry Format

**The core problem**: No record of drift repairs; can't distinguish "fixed" from "never noticed".

**The solution**:
- Log: Date | Higher Source | Lower Source | Mismatch | Resolution
- Enables audit and pattern detection
- Required when SSOT mismatch discovered

### 50. Canonical FILE_LIST Block

**The core problem**: "Files:" header and verification use separate lists that can drift.

**The solution**:
- Define single `TASK_X_FILES=()` array per task
- Use for both header and verification
- One list, two uses, cannot drift

### 51. Exact Count Testing

**The core problem**: `total >= N` tests are fabricatable; stub can hardcode any number.

**The solution**:
- Create fixture directories with known exact counts
- Test with `== N`, not `>= N`
- Different directories have different counts to prevent single hardcoded value

### 52. Deliberate Schema-Invalid Fixtures

**The core problem**: "Invalid" fixtures that are just malformed JSON test parsing, not validation.

**The solution**:
- Distinguish malformed (bad JSON) from schema-invalid (valid JSON, wrong schema)
- Schema-invalid fixtures force actual model_validate() call
- Must have at least one test asserting `failed > 0` against schema-invalid fixture

### 53. Override Escape Hatch Scoping

**The core problem**: Env overrides that bypass "mandatory" tools undercut the rule.

**The solution**:
- Document when override is valid (CI-only, throwaway experiments)
- State explicitly: "Using override outside these contexts is drift"
- Override existence doesn't mean rule is optional

### 54. Phased Enforcement Honesty

**The core problem**: Rule sounds universal but mechanics only enforce it in later phases.

**The solution**:
- Document enforcement timeline explicitly (Phase 0-2 vs Phase 3+)
- Either make it truly universal (add checks to all phases)
- Or document the gap honestly ("strictly enforced from Phase 3 onward")

### 55. Structural vs Semantic Test Assumptions

**The core problem**: Tests assume dict access, break on legitimate refactors to typed models.

**The solution**:
- Use type-agnostic accessors, or
- Explicitly tie test to type contract with assertion, or
- Test semantic behavior, not structural access

### 56. Policy vs Safety Invariant Tests

**The core problem**: Tests encode current policy behavior as hard invariants.

**The solution**:
- Label tests by category: SAFETY INVARIANT vs POLICY TEST
- Safety: "script tags detected" (should never change)
- Policy: "clean doc not blocked" (may change with profiles)
- Know which tests to update vs which failures indicate bugs

### 57. Forced Refactor Tests

**The core problem**: Tests don't break when underlying code evolves, so updates are forgotten.

**The solution**:
- Add evolution assertions that intentionally break: `assert isinstance(x, dict), "Update for typed!"`
- Or use feature flags to switch test behavior
- Tests that break remind you to update them

### 58. CI as Last Safety Net

**The core problem**: Relying on CI to catch things but claiming local discipline enforces them.

**The solution**:
- Document which checks are "CI will catch" vs "must run locally"
- Create explicit safety net table: Check | Local | CI
- Set expectations correctly so CI failures aren't surprising

### 59. Machine-Safe Placeholder Format

**The core problem**: `[X]` placeholders collide with markdown syntax.

**The solution**:
- Use `[[PH:NAME]]` format exclusively
- Pre-flight check: `grep -RInE '\[\[PH:[A-Z0-9_]+\]\]'`
- Zero false positives from markdown links or checkboxes

### 60. Mandatory Baseline Snapshot

**The core problem**: AI can "comply" while inventing facts (never ran tests, guessed versions).

**The solution**:
- Required section at top of task list
- Must contain pasted command output, not filled from memory
- Includes: commit hash, branch, runtime version, test status

### 61. Canonical File List as Single Source

**The core problem**: Header file list and verification script use different lists.

**The solution**:
- Define bash array per task: `TASK_X_FILES=(...)`
- Use for BOTH the header AND the verification loop
- One list, two uses, cannot drift

### 62. Minimalism Principle

**The core problem**: Large templates are harder to maintain and adopt.

**The solution**:
- If rule not enforced by command → consider removing
- If rule in both guide and template → keep only in template
- Smaller templates drift less

### 63. No Weak Tests as Task Gate

**The core problem**: "Test strength" is advisory, not enforced.

**The solution**:
- Explicit checklist in every task's STOP gate
- Four yes/no questions that must all be YES
- Tests invalid if any answer is NO

### 64. Derived Governance Declaration

**The core problem**: Template rules seem arbitrary without source.

**The solution**:
- List source governance documents at top of template
- Each rule traces to a specific document
- Teams can update table if using different governance docs

---

## Quick Start

### Step 1: Copy Template

```bash
cp AI_TASK_LIST_TEMPLATE_v3.md PROJECT_TASKS.md
```

### Step 2: Fill Project-Specific Values

Required replacements (all use `[[PH:NAME]]` format):
- `[[PH:PROJECT_NAME]]` → Your project
- `[[PH:FAST_TEST_COMMAND]]` → Fully-qualified quick test (e.g., `uv run pytest -q`)
- `[[PH:FULL_TEST_COMMAND]]` → Fully-qualified full test (e.g., `uv run pytest -v`)
- `[[PH:TEST_COMMAND]]` → Fully-qualified single test command
- Phase/task breakdown for your work
- **All path arrays with real paths**

### Step 3: Verify No Placeholders Remain

```bash
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && exit 1 || echo "OK"
# Must return zero matches
```

### Step 4: Work Sequentially

```
Task 0.1 → Clean Table → Task 0.2 → Phase 0 Gate → Phase 1...
```

---

## For AI Assistants: Execution Rules

### Before Starting Any Task

1. Read task objective
2. Identify test command
3. Verify prerequisites pass
4. **Note all files listed in `Files:` header**

### After Writing Any Test

1. **Run stub check**: Would test pass with `return None`?
2. If yes → Strengthen test before proceeding
3. If no → Proceed to implementation

### After Completing Any Code

1. Run specified test immediately
2. Check for warnings/errors
3. Run full suite
4. Verify Clean Table
5. **Verify all `Files:` exist**

### When Tests Fail

```
IF fixable in <15 minutes:
    Fix it now
ELSE:
    Rollback (see Appendix A)
    Document in ISSUES.md
    Re-attempt with different approach
```

### Prohibited Shortcuts

- ❌ "Tests are probably fine" (run them)
- ❌ "I'll add tests later" (TDD means now)
- ❌ "This TODO is minor" (no TODOs in "done" code)
- ❌ "Phase gate is just ceremony" (it's enforcement)
- ❌ **"Exit code 0 means it works"** (test actual behavior)
- ❌ **"I'll create that file later"** (if listed, create now)
- ❌ **"The placeholder is obvious"** (no placeholders in artifacts)

---

## Test Strength Patterns

> Patterns shown in Python-like pseudocode. Concepts apply to any testing framework.

### Pattern 1: Output File Verification

```
# ❌ Weak
assert file("output.txt").exists()

# ✅ Strong
output = file("output.txt")
assert output.exists()
content = output.read()
assert length(content) > 0
assert "expected_header" in content
lines = content.split("\n")
assert length(lines) >= 5
```

### Pattern 2: Tool Invocation

```
# ❌ Weak
result = run(["tool"])
assert result.exitCode == 0

# ✅ Strong
result = run(["tool", "--input", "test.json"], captureOutput=true)
assert result.exitCode == 0
stdout = result.stdout
assert "processed: 10" in stdout  # Specific expected output
assert "errors: 0" in stdout
```

### Pattern 3: Validation Tools

```
# ❌ Weak - accepts any outcome
result = run(["validate"])
assert result.exitCode in (0, 1)

# ✅ Strong - tests both paths
test validator_accepts_valid:
    result = run(["validate", "valid.json"], captureOutput=true)
    assert result.exitCode == 0
    assert "PASS" in result.stdout

test validator_rejects_invalid:
    result = run(["validate", "invalid.json"], captureOutput=true)
    assert result.exitCode == 1
    assert "FAIL" in result.stdout
    assert "line 5" in result.stderr  # Specific error location
```

### Pattern 4: Data Processing

```
# ❌ Weak
result = process(data)
assert result != null

# ✅ Strong
result = process(data)
assert result is list
assert length(result) == 3
assert result[0]["key"] == "expected_value"
assert all(item has "required_field" for item in result)
```

---

## Verification Commands (Customize Per Project)

```bash
# Fast check (after each change) - adapt to your language
# Python:     pytest tests/test_current.py -x -q
# Node:       npm test -- --testPathPattern=current
# Rust:       cargo test current
# Go:         go test ./... -run Current

# Full validation (before task completion)
# Python:     pytest tests/ -v --tb=short
# Node:       npm test
# Rust:       cargo test --verbose
# Go:         go test ./... -v

# Clean Table check (language-agnostic)
grep -rn "TODO\|FIXME\|XXX" src/
# Expected: no new results

# Phase gate
test -f .phase-N.complete.json && echo "OK" || echo "BLOCKED"

# Test strength audit (adapt pattern to your language)
grep -rn "returncode == 0" tests/ | grep -v "# strong"
grep -rn "returncode in" tests/
# Expected: no results (or all marked as verified strong)

# File manifest check
for f in FILE1 FILE2 FILE3; do test -f "$f" || echo "MISSING: $f"; done

# Placeholder check (must return zero)
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]|YYYY-MM-DD|TBD' .phase-*.complete.json && exit 1 || true
```

---

## When Things Go Wrong

### Test Failure
→ Fix immediately or rollback

### Phase Gate Blocked
→ Do NOT proceed; resolve failing criterion

### Multiple Failures
→ Full revert to last known good commit

### Lost Progress
→ Check `git reflog` for recovery

### Weak Test Discovered
→ Stop current work, strengthen test, verify it fails with stub, then continue

### Ghost File Found
→ Either create the file or remove from `Files:` header

### Placeholder in Artifact
→ Regenerate artifact with proper shell variable expansion

---

## Template Structure Summary

```
PROJECT_TASKS.md
├── Quick Status Dashboard      ← Current state at a glance
├── Scope Decisions Table       ← NEW: Explicit in/out of scope
├── Success Criteria            ← Project-level "done"
├── Phase Gate Rules            ← Enforcement mechanism
├── Source of Truth Hierarchy   ← What wins when docs conflict
├── Strictness Gate Protocol    ← Loose before strict
├── Unimplemented Feature Protocol ← Don't test what doesn't exist
├── Code-First Verification     ← Verify symbols before using
├── TDD Protocol                ← Every task follows this
├── Test Strength Rules         ← Forbids weak tests (expanded)
├── Existence vs Correctness    ← NEW: Check content, not just presence
├── Clean Table Definition      ← What "complete" means (expanded)
├── No Silent Errors            ← All exceptions raise
├── Reflection Loop             ← Evidence anchors + semantic types
├── Stop on Ambiguity           ← Confidence threshold
├── Thinking vs Execution       ← Separate reasoning from action
├── Discovery-First Protocol    ← Discover before defining
├── Code Quality Principles     ← SOLID/KISS/YAGNI
├── YAGNI Decision Tree         ← Feature gate
├── Code Quality Checklist      ← Task completion verification
├── Validation Pipeline         ← 7-step verification
├── File Manifest Rules         ← No ghost files
├── Task ID Uniqueness          ← NEW: No duplicate IDs
├── Global Clean Table          ← NEW: Check entire repo
├── Aspirational vs Actual      ← NEW: Use defined patterns
├── Pre-Run Dependencies        ← NEW: Handle test prerequisites
├── Environment Portability     ← No hard-coded paths
├── Prerequisites               ← Before Phase 0
│
├── Phase 0                     ← Setup & Infrastructure
│   ├── Task 0.1               ← TDD structure
│   │   ├── Write Test
│   │   ├── Test Strength Check
│   │   ├── Implement
│   │   ├── Verify
│   │   └── ⛔ STOP: Clean Table + Reflection
│   ├── Task 0.2
│   └── ⛔ STOP: Phase 0 Gate
│
├── Phase 1...N                 ← Same structure (ALL phases need tests)
│
├── Appendix A: Rollback        ← When things fail
├── Appendix B: AI Instructions ← Behavioral rules (expanded)
├── Appendix C: File Tracking   ← Audit trail (must cover all task IDs)
├── Appendix D: Progress Log    ← Time/session tracking
└── Appendix E: Test Audit      ← Catch weak tests
```

---

## Key Differences from v1.0

| v1.0 | v2.0 |
|------|------|
| "It runs" tests allowed implicitly | Test Strength Rules forbid them |
| Files in header could be ghosts | File Manifest verification required |
| Placeholder artifacts possible | Shell variable expansion + verification |
| Hard-coded paths common | Environment Portability Rules |
| Later phases could be prose-only | All phases require test skeletons |
| 3 enforcement mechanisms | **16 enforcement mechanisms** |
| No authority hierarchy | Source of Truth Hierarchy defined |
| Strict mode any time | Strictness Gates require loose-first |
| Test anything in spec | Unimplemented Feature Protocol |
| Trust symbol names in docs | Code-First Verification required |
| Models from design docs | Discovery-First Protocol |
| Spec is normative | Spec Interpretation Rules (aspirational) |
| No design principle enforcement | **SOLID/KISS/YAGNI baked in** |
| Speculative code allowed | **YAGNI Decision Tree gates features** |
| Complex solutions accepted | **KISS mandate requires simplicity** |
| Swallowed exceptions allowed | **No Silent Errors rule** |
| "Temporary" fixes allowed | **No Hidden Debt rule** |
| Import/smoke tests allowed | **Weak test patterns explicitly forbidden** |
| No mandatory reflection | **Reflection Loop with evidence anchors** |
| Assumptions unstated | **Semantic types distinguish Fact/Claim/Assumption** |
| Decisions undocumented | **Decision chains + trace links required** |
| Duplicate task IDs possible | **Task ID Uniqueness enforced** |
| Selective Clean Table checks | **Global enforcement across entire repo** |
| Patterns defined but unused | **Aspirational vs Actual alignment** |
| Existence tests sufficient | **Correctness tests required** |
| Scope implicit | **Scope Decisions table required** |
| Exit code 0 or 1 both pass | **Exit code tolerance forbidden** |
| "Prints something" passes | **Plausible output tests forbidden** |
| Heredoc placeholders committed | **Placeholder detection enforced** |
| Skip in docs, fail in tests | **Skip pattern consistency required** |
| CI tests check strings | **CI workflow wiring verification** |
| Schema changes untracked | **Version changelog governance** |
| No-op stub tools pass | **Real data processing required** |
| Phase gates vary in scope | **Phase Gate Scope Alignment** |
| Temporal debt window ignored | **Placeholder workflow documented** |
| Weak tests undocumented | **Conscious Trade-off Documentation** |
| Spec and task list drift | **Cross-Document SSOT management** |
| "Required" but skips | **Required vs Optional clarity** |
| Package manager for setup only | **Package Manager Consistency** |
| CI/Local use different commands | **CI/Local Workflow Identity** |
| Lockfile edited manually | **Dependency SSOT Structure** |
| Manifest without lockfile | **Dependency SSOT Structure** |
| Multiple env tools | **Environment Ownership** |
| Direct calls when activated | **"Even when activated" rule** |
| Violations unlabeled | **Drift Labeling** |
| Ambiguous placeholders | **Machine-Detectable Tokens** |
| Strictness confused with errors | **Strictness vs Error clarification** |
| Shell syntax errors in docs | **Shell Command Correctness** |
| Grep platform-specific | **Grep Portability** |
| Scope deadlocks possible | **Procedural Deadlock Detection** |
| Exclusions untracked | **Scope Delta Ledger** |
| Dual-purpose tests | **Test Role Disambiguation** |
| Evidence requirements unbounded | **Evidence Anchor Scoping** |
| Drift repairs unlogged | **Drift Repair Entry Format** |
| File list in two places | **Canonical FILE_LIST Block** |
| Tests use >= N (fabricatable) | **Exact Count Testing** |
| Invalid = malformed JSON only | **Schema-Invalid Fixtures** |
| Override bypasses mandatory | **Override Escape Hatch Scoping** |
| Universal rule, phased enforcement | **Phased Enforcement Honesty** |
| Dict access breaks on refactor | **Structural vs Semantic Assumptions** |
| Policy encoded as invariant | **Policy vs Safety Tests** |
| Tests don't break on evolution | **Forced Refactor Tests** |
| Local claim, CI reality | **CI as Last Safety Net** |
| Bracket placeholders | **[[PH:X]] format** |
| No baseline capture | **Mandatory Baseline Snapshot** |
| Two file lists | **Canonical FILE_LIST array** |
| Template bloat | **Minimalism principle** | |

---

## Customization Points

**Must customize:**
- Test commands (project-specific)
- Phase/task breakdown
- Success criteria
- **All `Files:` headers**

**Can keep as-is:**
- STOP checkpoint structure
- Clean Table definition
- Test Strength Rules
- File Manifest Rules
- Rollback procedures
- AI instruction appendix

---

## Common Anti-Patterns to Avoid

> Examples use Python syntax for illustration, but these patterns occur in **any language**.

### Anti-Pattern 1: The Ceremonial Test
```
# Looks like a test but verifies nothing
test_module_exists:
    import mymodule  # Passes even if module is empty
    assert True      # Or: expect(true).toBe(true)
```
**Fix**: Test actual behavior of the module.

### Anti-Pattern 2: The Optimistic Validator
```
# Accepts both success and failure as "passing"
assert result.exitCode in (0, 1)  # Or: expect([0,1]).toContain(code)
```
**Fix**: Test success and failure paths separately.

### Anti-Pattern 3: The Ghost File
```markdown
**Files**: `tools/verify`, `tools/analyze`

### Implementation
[Only creates verify, analyze mentioned but never created]
```
**Fix**: Either create all listed files or remove from header.

### Anti-Pattern 4: The Immortal Placeholder
```json
{
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"
}
```
**Fix**: Use shell variable expansion when generating artifacts.

### Anti-Pattern 5: The Prose Phase
```markdown
## Phase 4: Integration

### Task 4.1: Full Integration

Just run everything together and make sure it works.
Use your judgment to verify correctness.
```
**Fix**: Define concrete test skeletons with specific assertions.

### Anti-Pattern 6: The Spec-First Model
```
# Defined from design doc without running actual code
OutputSchema:
    field_name: string  # Doc says "fieldName" but code outputs "field_name"
    
# Or in any schema language:
# { "fieldName": "string" }  # Doc says this
# { "field_name": "string" }  # Code actually produces this
```
**Fix**: Run discovery phase first, derive schema from actual outputs.

### Anti-Pattern 7: The Premature Strictness
```
# Jumping straight to strict validation
config = { strict_mode: true }  # Without verifying permissive mode works

# Or: enabling "fail on unknown fields" before mapping all fields
# Or: enabling "required" before confirming field always exists
```
**Fix**: Implement loose version, validate on real inputs, then tighten.

### Anti-Pattern 8: The Phantom Feature Test
```
# Testing a feature that only exists in design docs
test_future_capability:
    result = module.planned_feature()  # Doesn't exist yet
    assert result.new_field == "expected"
```
**Fix**: Verify feature exists in code before writing test.

### Anti-Pattern 9: The Trusted Spec
```
# Assuming design doc is correct without verification
import ClassName from module  # Error: no such export
# Doc said "ClassName" but code has "class_name"
```
**Fix**: grep for symbol before using it; update task list if different.

### Anti-Pattern 10: The Inverted Authority
```
# Changing working code to match design doc
# Old (working): function process_data(input)
# New (broken):  function processData(input)  # "Fixed" to match spec
```
**Fix**: Update spec to match code, never vice versa.

### Anti-Pattern 11: The Speculative Parameter (YAGNI)
```
# Adding parameters for hypothetical future use
function export(data, format="pdf", compress=false, encrypt=false, watermark=null):
    # Only format is used today, others are "for later"
    ...
```
**Fix**: Only add parameters when they have immediate consumers.

### Anti-Pattern 12: The Premature Abstraction (YAGNI)
```
# Interface with only one implementation
interface DataProcessor:
    process(data)

class ConcreteProcessor implements DataProcessor:
    process(data): ...

# No other implementations exist or are planned
```
**Fix**: Use concrete class until ≥2 implementations actually needed.

### Anti-Pattern 13: The Future Hook (YAGNI)
```
# Extension points with no consumers
function process(data, pre_hook=null, post_hook=null, validators=[]):
    if pre_hook: pre_hook(data)
    # actual work
    if post_hook: post_hook(data)
    
# pre_hook, post_hook, validators never used anywhere
```
**Fix**: Remove hooks until actual consumers exist.

### Anti-Pattern 14: The Complex Solution (KISS)
```
# Over-engineered when simple solution works
class DataProcessorFactory:
    class Builder:
        class Config:
            ...
    
# When this would suffice:
function process_data(input): ...
```
**Fix**: Start with simplest solution; add complexity only when proven necessary.

### Anti-Pattern 15: The Silent Swallower
```
# Swallowed exception hides bugs
try:
    result = process(data)
except Exception as e:
    print(f"Warning: {e}")  # Silent failure!
    continue
```
**Fix**: Always raise; never swallow exceptions.

### Anti-Pattern 16: The Strict Mode Toggle
```
# Conditional error handling
function process(data, strict=true):
    try:
        validate(data)
    except Error as e:
        if strict:
            raise
        else:
            log.warning(e)  # Bug hiding!
```
**Fix**: Remove strict parameter; errors always raise.

### Anti-Pattern 17: The Temporary Fix
```
# "Temporary" workaround that becomes permanent
# TODO: Fix this properly later
result = data.replace("broken", "")  # Band-aid!
# This "temporary" fix shipped 2 years ago
```
**Fix**: Fix root cause now or don't ship.

### Anti-Pattern 18: The Deferred Adjustment
```
# Speculative comment creating hidden debt
# You may need to adjust this for edge cases
# Check if this works with large files
function process(data):
    ...
```
**Fix**: Either verify now and document, or remove the comment.

### Anti-Pattern 19: The Unsupported Claim
```
# Claim without evidence
"The parser handles all edge cases"  # Says who? Where's the proof?

# No source, no quote, no verification
```
**Fix**: Every claim needs evidence anchor: `SOURCE: file:line, QUOTE: "text"`

### Anti-Pattern 20: The Assumption-As-Fact
```
# Treating assumption as verified fact
"The API returns JSON"  # Did you check? Or assume?

# No distinction between what's verified and what's assumed
```
**Fix**: Use semantic types - label as ASSUMPTION, then VERIFY or flag as RISK.

### Anti-Pattern 21: The Undocumented Decision
```
# Significant choice with no reasoning trail
# Uses approach X instead of Y... but why?

# Six months later: "Why did we do it this way?"
```
**Fix**: Decision chain: WHAT + WHY + WHY_NOT alternatives + IMPACT.

### Anti-Pattern 22: The Skipped Reflection
```
# Task marked complete without reflection
"Done! Moving to next task..."

# No pause to verify objective achieved
# No evidence that claims are supported
# No check for unresolved uncertainties
```
**Fix**: Mandatory reflection template before any task completion.

### Anti-Pattern 23: The Duplicate Task ID
```
# Same ID used for different tasks
Task 2.2a: Structure Models
Task 2.2a: Update Empty Method  # CONFLICT!

# Appendix only tracks one of them
# "Which 2.2a did you mean?"
```
**Fix**: Every task ID must be unique. Audit for duplicates before execution.

### Anti-Pattern 24: The Selective Clean Table
```
# Clean Table check only covers some files
grep "TODO" file1.py file2.py  # Misses file3.py!

# Phase gate passes, but debt exists in unchecked files
```
**Fix**: Global Clean Table test that scans entire repo, not ad-hoc greps.

### Anti-Pattern 25: The Aspirational Helper
```
# Document defines helper
"Use PYTHON env var: PYTHON = os.environ.get('PYTHON', sys.executable)"

# But all examples ignore it
subprocess.run([".venv/bin/python", ...])  # Hard-coded!
```
**Fix**: If you define a pattern, use it in ALL examples. Audit for violations.

### Anti-Pattern 26: The Existence Test
```
# Checks file exists but not content
test_export():
    run(["./export"])
    assert file("output.json").exists()  # WEAK
    assert "exported" in stdout  # WEAK

# Stub that writes "{}" and prints "exported" passes
```
**Fix**: Check semantic correctness - parse output and verify expected fields/values.

### Anti-Pattern 27: The Pre-Run Dependency
```
# Test skips if file doesn't exist
test_output_valid():
    if not file("output.json").exists():
        pytest.skip("Run tool first")  # FRAGILE!
    
# On clean checkout: 0 tests run, CI passes
```
**Fix**: Either gate ensures pre-run, test runs tool itself, or fixture generates file.

### Anti-Pattern 28: The Exit Code Tolerator
```
# Accepts both success AND failure as "passing"
result = subprocess.run(["./tool"])
assert result.returncode in (0, 1)  # USELESS!

# Tool could be unimplemented, just sys.exit(0)
# Tool could fail on all inputs, sys.exit(1)
# Both pass this test!
```
**Fix**: Exit code 0 means SUCCESS, 1 means FAILURE. Test both paths separately.

### Anti-Pattern 29: The Plausible Printer
```
# Checks output contains expected-ish string
result = subprocess.run(["./export_tool"], capture_output=True)
assert "exported" in result.stdout.lower()  # WEAK!

# Stub: print("Schema exported!"); sys.exit(0)
# Passes test, does nothing useful
```
**Fix**: Check actual output content/structure, not just presence of keywords.

### Anti-Pattern 30: The Heredoc Placeholder
```
# Task list shows literal placeholder in heredoc
cat > .phase-0.complete.json << 'EOF'
{
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"  # LITERAL!
}
EOF

# If executed as-is, artifact contains placeholder
# Violates Clean Table but nothing catches it
```
**Fix**: Use shell substitution `$(date -u +%Y-%m-%dT%H:%M:%SZ)` or explicit "replace before commit" instruction.

### Anti-Pattern 31: The Inconsistent Skip
```
# Guidelines say:
"Skip gracefully if rg not installed"
if not shutil.which("rg"):
    pytest.skip("ripgrep not installed")

# But actual test does:
result = subprocess.run(["rg", ...])
assert result.returncode in (0, 1)  # No skip! Fails with 127!

# Half-committed: guidelines say optional, tests say required
```
**Fix**: Decide: REQUIRED (hard-fail, no skip) or OPTIONAL (skip everywhere). Be consistent.

### Anti-Pattern 32: The CI String Checker
```
# CI workflow test only checks strings present
workflow = yaml.load("ci.yml")
assert "validate_tool.py" in str(workflow)
assert "--threshold 100" in str(workflow)

# Workflow could have:
#   run: "echo validate_tool.py --threshold 100"
# Test passes, CI does nothing useful
```
**Fix**: Check correct wiring: step order, actual commands, dependency installation present.

### Anti-Pattern 33: The No-Op Stub Tool
```
# Tool satisfies all tests but does no real work
def main():
    if "--help" in sys.argv:
        print("--report --threshold"); sys.exit(0)
    report = {"total": 0, "passed": 0, "pass_rate": 0.0}
    write_json(report)  # Never validated anything!
    sys.exit(0 if threshold <= 0 else 1)

# Passes: help test, report format test, threshold tests
# Fails: nothing, because no test requires actual validation
```
**Fix**: Test with known-good AND known-bad inputs; assert tool actually processes data.

### Anti-Pattern 34: The Phase Gate Scope Mismatch
```
# Global rule says: "Clean Table applies to entire repo"
# Phase 0 gate checks: grep TODO file1.py file2.py  # Only 2 files!

# Result: TODOs can exist in src/ during Phase 0-2
# Only Phase 3+ catches them (when global test added)
```
**Fix**: If rule is global, phase gates must enforce globally from Phase 0.

### Anti-Pattern 35: The Temporal Debt Window
```
# 1. Create .phase-0.complete.json with "YYYY-MM-DD" placeholder
# 2. Run tests → pass (file not yet committed)
# 3. Edit file to add real date
# 4. Forget to re-run tests
# 5. Commit via GUI → placeholder could slip through

# The "debt window" is steps 1→3 where invalid content exists
```
**Fix**: Use shell substitution (no placeholder), or pre-commit hook, or document the risk.

### Anti-Pattern 36: The Undocumented Weak Test
```
# Test is intentionally limited, but no explanation
def test_ci_workflow():
    assert "validate_tool.py" in workflow_yaml
    # Why not check actual wiring? Reader doesn't know.
    # Is this an oversight or conscious trade-off?
```
**Fix**: Add TRADE-OFF comment explaining limitation, reason, accepted risk, mitigation.

### Anti-Pattern 37: The Cross-Document Drift
```
# SPEC.md says: "Test plugin invariants, semantic extraction"
# TASK_LIST.md says: "OUT OF SCOPE: plugin tests, semantic tests"
# Neither document references the other

# Future reader of spec expects tests that don't exist
# Two documents, two "truths"
```
**Fix**: Mark spec as HISTORICAL, or task list explicitly references spec with scope delta.

### Anti-Pattern 38: The Partial Package Manager
```
# Project declares: "We use uv for package management"
# Setup commands: uv add, uv sync ✓
# But all examples show: .venv/bin/python tools/script.py ✗

# uv is for setup only; developer workflow ignores it
```
**Fix**: If you declare a tool, use it everywhere. `uv run python tools/script.py`

### Anti-Pattern 39: The CI/Local Split
```
# CI workflow: uv run pytest tests/
# Local docs:  .venv/bin/python -m pytest tests/

# Works on my machine, fails in CI (or vice versa)
# Two mental models for same action
```
**Fix**: Same command locally and in CI. Copy-paste should work both directions.

### Anti-Pattern 40: The Manual Lockfile Edit
```
# Developer edits uv.lock / package-lock.json by hand
# "Just need to pin this one version..."

# Lockfile now inconsistent with manifest
# Next sync may overwrite or conflict
```
**Fix**: Never edit lockfiles manually. Change manifest, run lock command, commit both.

### Anti-Pattern 41: The Orphaned Manifest
```
# Commit pyproject.toml with new dependency
# Forget to commit uv.lock

# CI fails: "dependency not found"
# Or worse: CI resolves different versions than local
```
**Fix**: Always commit manifest AND lockfile together. CI should fail if they're out of sync.

### Anti-Pattern 42: The Rogue Environment
```
# Project uses uv, but developer runs:
python -m venv .venv  # Wrong! Should use uv sync
pip install package   # Wrong! Should use uv add

# Environment now differs from lockfile
# "Works on my machine" begins
```
**Fix**: Only the declared tool creates/manages the environment. Delete rogue envs.

### Anti-Pattern 43: The Activated Shortcut
```
# In activated venv, developer runs:
pytest tests/           # Direct call
python tools/script.py  # Direct call

# Might use wrong interpreter or stale deps
# Not reproducible if venv is corrupted
```
**Fix**: Even when activated, prefer `uv run pytest`. Guarantees correct environment.

### Anti-Pattern 44: The Ambiguous Placeholder
```
# Placeholder detector: grep -E "\[.*\]" doc.md
# Matches:
#   [link text](url)  ← false positive
#   [ ] checkbox      ← false positive
#   [actual placeholder]  ← true positive

# Too noisy → gets ignored → placeholders slip through
```
**Fix**: Use explicit tokens like `[[PH:NAME]]`. Detector: `grep '\[\[PH:'`

### Anti-Pattern 45: The Shell Syntax Error
```
# Task list shows:
TESTS_PASSED=[YOUR_TEST_COUNT_COMMAND]

# This assigns literal string "[YOUR_TEST_COUNT_COMMAND]"
# Not command substitution! Copy-paste creates bugs.
```
**Fix**: `TESTS_PASSED="$(your_command)"` - correct command substitution.

### Anti-Pattern 46: The GNU/BSD Surprise
```
# Works on Linux, fails on macOS:
grep -r "TODO\|FIXME" src/

# BSD grep requires -E for alternation
# Different -r/-R semantics for symlinks
```
**Fix**: Use portable form: `grep -RInE '(TODO|FIXME)' src/`

### Anti-Pattern 47: The Procedural Deadlock
```
# Rule 1: "Parser changes are OUT OF SCOPE"
# Rule 2: "Do NOT weaken safety tests"
# Situation: Safety test fails due to parser behavior

# Cannot change parser (Rule 1)
# Cannot change test (Rule 2)
# = STUCK
```
**Fix**: Every scope constraint needs an escape path or exception category.

### Anti-Pattern 48: The Dual-Purpose Test
```
# Test tries to be both:
# - Milestone driver (must fail until goal achieved)
# - Branch guard (skips except on main)

# During development: skips → no feedback
# On main: expected to fail → confusing
```
**Fix**: Write two tests if you need both behaviors.

### Anti-Pattern 49: The Evidence Theater
```
# Every claim requires full evidence anchor
# Even: "Renamed variable from x to y"
# Result: Team writes fake/minimal evidence to satisfy rule
# Or: Team ignores rule entirely because it's burdensome
```
**Fix**: Scope evidence requirements - mandatory for high-risk claims, optional for trivial.

### Anti-Pattern 50: The Greater-Than Test
```
# Test checks:
assert report["total"] >= 50

# Stub can hardcode:
report = {"total": 100, "passed": 100, "failed": 0}
# Never touches filesystem, passes test!
```
**Fix**: Use exact counts with known-count fixture directories: `assert report["total"] == 3`

### Anti-Pattern 51: The Malformed-Only Invalid
```
# "Invalid" fixture is just bad JSON:
fixtures/invalid/bad.json: "{not valid json"

# This tests JSON parsing, not schema validation!
# Stub can catch this without calling model_validate()
```
**Fix**: Include schema-invalid fixtures (valid JSON, wrong schema): extra fields, wrong types, missing required.

### Anti-Pattern 52: The Lagging Test
```
# Phase 1: ir.security is dict
stats = ir.security.get("statistics", {})

# Phase 2: ir.security becomes SecurityInfo model
# But test still passes because __getitem__ works!
# Test never forces update to typed access
```
**Fix**: Add evolution assertions: `assert isinstance(ir.security, dict), "Update for typed model!"`

### Anti-Pattern 53: The Bracket Placeholder
```
# Template uses:
[TEST_COMMAND]
[PROJECT_NAME]

# Problem: grep "\[.*\]" matches:
# - [link text](url)   ← false positive
# - [ ] checkbox       ← false positive
# - [TEST_COMMAND]     ← true positive

# Too noisy → pre-flight check gets ignored
```
**Fix**: Use `[[PH:NAME]]` format exclusively. Grep: `'\[\[PH:[A-Z0-9_]+\]\]'`

### Anti-Pattern 54: The Missing Baseline
```
# Task list starts with tasks, no baseline capture
# AI can "comply" while inventing facts:
# - "Tests pass" (never ran them)
# - "On branch main" (never checked)
# - "Python 3.11" (guessed)
```
**Fix**: Mandatory baseline snapshot with pasted command output before any work.

### Anti-Pattern 55: The Dual File List
```
# Header says:
Files: `src/foo.py`, `tests/test_foo.py`

# Verification uses:
for f in src/foo.py tests/test_bar.py; do  # Different list!
```
**Fix**: Single canonical bash array used for BOTH header AND verification.

### Anti-Pattern 56: The Bloated Template
```
# Template is 3000+ lines
# Team doesn't read it
# Rules get ignored because too many to track
# Drift happens despite "having a template"
```
**Fix**: Strip to essentials (6 invariants + 4 drift killers). Add depth only when needed.

---

## Checklist for AI Agents

Before marking ANY task complete:

```
□ Test exists and is written FIRST
□ Test FAILS with stub implementation (verified)
□ Implementation makes test pass
□ Full test suite passes
□ No TODOs/FIXMEs in new code
□ All files in "Files:" header exist
□ No warnings introduced
□ Code is production-ready
□ No tests for unimplemented features
□ All symbol references verified via grep
□ No assumptions about code structure without verification

Code Quality (SOLID/KISS/YAGNI):
□ YAGNI Q1: Current requirement exists for all new code?
□ YAGNI Q2: Immediate consumer exists for all new code?
□ YAGNI Q3: Backed by data/stakeholder (not speculation)?
□ KISS: Simpler alternative considered?
□ SRP: Each new module has single purpose?
□ No unused parameters, hooks, or abstractions?
□ Generalizations have ≥2 real consumers?

No Silent Errors:
□ All exceptions raise unconditionally?
□ No "strict mode" parameters or toggles?
□ No swallowed exceptions (catch and continue)?
□ No environment variables for error strictness?

No Hidden Debt:
□ No "temporary" fixes or band-aids?
□ No "adjust later" or "check this later" comments?
□ No speculative "you may need to" comments?
□ No workaround logic (proper fix implemented)?

Test Strength:
□ No import-only tests?
□ No existence-only tests (file.exists() without content check)?
□ No smoke tests (just runs without assertions)?
□ Each error code/rule has triggering test?
□ Tests use fixtures for deterministic outcomes?
□ Existence tests upgraded to correctness tests (check content, not just presence)?
□ Pre-run dependencies handled (gate, integration test, or fixture)?
□ No exit code tolerance (returncode in (0,1) is FORBIDDEN)?
□ No "prints something plausible" tests (check actual content, not keywords)?
□ CI/workflow tests check wiring, not just string presence?

Task List Governance:
□ All task IDs are unique (no duplicates)?
□ Appendix/file tracking covers ALL task IDs?
□ Scope decisions table present (in/out of scope explicit)?
□ All defined patterns/helpers used in examples (no aspirational-only)?
□ Clean Table checks are global (entire repo), not selective?
□ Skip patterns consistent (either all skip or all hard-fail)?
□ Version changelog updated for schema/API changes?

Artifact Generation:
□ No literal placeholders in heredocs (YYYY-MM-DD, [INSERT], etc.)?
□ Shell variable substitution used for dynamic values?
□ Generated artifacts checked for placeholder patterns?
□ Phase completion files have actual timestamps?
□ Temporal debt window handled (shell substitution, pre-commit, or documented CI safety net)?

Tool Tests:
□ No-op stub would fail tests (tests require real data processing)?
□ Known-good input tested (total > 0, passed > 0)?
□ Known-bad input tested (failed > 0, specific error)?
□ Exit codes reflect actual results, not canned values?

Phase Gate Alignment:
□ Global rules enforced globally from Phase 0 (not just later phases)?
□ Phase gates reference global tests, not duplicate with narrower scope?

Documentation Integrity:
□ Intentionally weak tests have TRADE-OFF comments?
□ Cross-document references explicit (spec marked historical or scope delta documented)?
□ "REQUIRED" dependencies actually hard-fail (not skip)?
□ Required vs Optional vs "Required for CI only" clearly distinguished?
□ Package manager used consistently (not just for setup)?
□ CI and local commands are identical?
□ No raw venv paths when package manager declared?

Dependency Management:
□ Lockfile never edited manually?
□ Manifest and lockfile committed together?
□ Only declared tool creates/manages environment?
□ No rogue pip/npm installs when using managed tool?
□ Even activated shell uses tool commands (uv run, poetry run)?
□ Violations explicitly labeled as "drift"?

Shell & Portability:
□ Shell snippets syntactically correct (command substitution, quoting)?
□ Grep commands use portable form (-RInE)?
□ Placeholders use machine-detectable format ([[PH:NAME]])?
□ Platform requirements documented (GNU grep, etc.)?

Scope & Governance:
□ Scope Delta Ledger present for excluded items?
□ No procedural deadlocks (conflicting "cannot change" rules)?
□ Escape paths defined for each scope constraint?
□ Drift repairs logged (date, mismatch, resolution)?

Test Organization:
□ Tests don't serve dual purposes (milestone-driver vs branch-guard)?
□ Evidence anchors scoped (mandatory for high-risk, optional for trivial)?
□ FILE_LIST is canonical (used for both header and verification)?
□ Count tests use exact values (== N), not minimums (>= N)?
□ Invalid fixtures include schema violations, not just malformed JSON?
□ Tests labeled as SAFETY INVARIANT vs POLICY TEST?

Code Evolution:
□ Tests have evolution assertions that break on type changes?
□ Structural assumptions documented (e.g., "assumes dict, update when typed")?
□ Feature flags for test behavior when underlying code evolves?

Enforcement Honesty:
□ Override escape hatches have documented valid-use scope?
□ Phased enforcement documented (which rules apply when)?
□ Safety net table shows what's local vs CI enforcement?
□ No claims of "universal" for rules only enforced in later phases?

Placeholder & Baseline (v3.0):
□ All placeholders use [[PH:NAME]] format (not [NAME])?
□ Pre-flight check returns zero placeholder matches?
□ Baseline snapshot populated from executed commands (not memory)?
□ Git commit, branch, runtime versions captured with evidence?
□ Canonical FILE_LIST array used for both header and verification?

Reflection & Evidence (NEW):
□ Reflection template completed for this task?
□ All claims have evidence anchors (source:line + quote)?
□ Assumptions distinguished from facts?
□ Each assumption verified or flagged as risk?
□ Risks identified with mitigations?
□ Decision chains documented (what/why/why_not/impact)?
□ Trace links created for significant decisions?
□ Confidence ≥ 80% on all elements?
□ No unresolved uncertainties?

Before marking ANY phase complete:

□ All tasks complete (above checklist for each)
□ Phase gate verification passes
□ .phase-N.complete.json created
□ NO PLACEHOLDERS in artifact (verified with grep)
□ Git tag created
□ Strictness gates passed (if applicable)
□ Discovery artifacts current (if applicable)
□ Phase-level reflection completed

Before tightening ANY constraint:

□ Loose version implemented and passing
□ Tested on ≥N representative real inputs
□ Tightened version applied
□ Same inputs still pass
□ No fake data synthesized to satisfy constraints

Before using ANY symbol from design doc:

□ grep confirms symbol exists in code
□ Signature/parameters match expectations
□ If mismatch: updated task list (not code)

Before testing ANY feature:

□ Feature exists in code (grep verified)
□ Feature is callable/accessible
□ Feature produces expected output type
□ Feature is NOT marked reserved/planned

Before adding ANY new code (YAGNI gate):

□ Q1: Current requirement? (NO → don't add)
□ Q2: Immediate consumer? (NO → don't add)
□ Q3: Data/stakeholder backed? (NO → don't add)
□ Q4: Can't add later? (YES → defer)
□ Simpler alternative rejected with reason?

Validation Pipeline (execute in order):

□ 1. Decision chains built
□ 2. Evidence anchors attached (claim → source → quote)
□ 3. Trace links created
□ 4. Confidence assessed (≥80%)
□ 5. Thinking separated from execution
□ 6. Reflection completed
□ 7. Cross-reference validated (no conflicts)
```

---

**End of Usage Guide**
