# AI_TASK_LIST_TEMPLATE.md

**Purpose**: Unified task execution template for AI assistants. Prevents drift, enforces completion, bakes in TDD and Clean Table.

**Version**: 2.0
**Based On**: v1.0 + drift prevention hardening

---

## How This Template Works

This template has **sixteen** enforcement mechanisms:

1. **STOP Checkpoints** — AI must pause and verify before continuing
2. **Phase Gates** — Cannot advance until all criteria pass
3. **Clean Table Rule** — No debt carries forward
4. **Test Strength Rules** — "It runs" tests are explicitly forbidden
5. **File Manifest Verification** — Every listed file must exist
6. **Source of Truth Hierarchy** — Code wins over docs
7. **Strictness Gates** — Loose must pass before strict
8. **Unimplemented Feature Protocol** — Don't test what doesn't exist
9. **Discovery-First Protocol** — Discover structure before defining models
10. **Code Quality Gates (SOLID/KISS/YAGNI)** — No speculative code
11. **No Silent Errors** — All exceptions raise unconditionally
12. **Reflection Loop** — Mandatory self-assessment before proceeding
13. **Task ID Uniqueness** — No duplicate IDs, all tracked in Appendix
14. **Global Clean Table Enforcement** — Check entire repo, not selective files
15. **Aspirational vs Actual Alignment** — Defined patterns must be used in examples
16. **Scope Decisions Table** — Explicit in/out of scope declarations

**The AI assistant should copy this template, fill in project-specific details, and follow it sequentially.**

---

# [PROJECT_NAME] - Detailed Task List

**Project**: [One-line description]
**Created**: [YYYY-MM-DD]
**Status**: Phase 0 - NOT STARTED

---

## Quick Status Dashboard

| Phase | Name | Status | Tests | Clean Table |
|-------|------|--------|-------|-------------|
| 0 | Setup & Infrastructure | ⏳ NOT STARTED | -/- | - |
| 1 | [Name] | 📋 PLANNED | -/- | - |
| 2 | [Name] | 📋 PLANNED | -/- | - |

**Status Key**: ✅ COMPLETE | ⏳ IN PROGRESS | 📋 PLANNED | ❌ BLOCKED

---

## Success Criteria (Project-Level)

The project is DONE when ALL of these are true:

- [ ] [Primary objective achieved]
- [ ] [All tests pass: `[command]`]
- [ ] [Performance requirement met]
- [ ] [No regressions introduced]

---

## ⛔ PHASE GATE RULES

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE N+1 CANNOT START UNTIL:                              │
│                                                             │
│  1. All Phase N tasks have ✅ status                        │
│  2. Phase N tests pass: [test_command] → PASS               │
│  3. Phase N Clean Table verified                            │
│  4. Phase unlock artifact exists: .phase-N.complete.json    │
│  5. File manifest verified: all listed files exist          │
│  6. Strictness gates passed (if applicable)                 │
│                                                             │
│  If ANY criterion fails → STOP. Fix or rollback.            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📜 SOURCE OF TRUTH HIERARCHY

```
┌─────────────────────────────────────────────────────────────┐
│  When spec/docs and code disagree, resolve in this order:   │
│                                                             │
│  1. RUNNING CODE OUTPUT (highest authority)                 │
│     └── What the system actually produces                   │
│                                                             │
│  2. GENERATED SAMPLES / SNAPSHOTS                           │
│     └── Captured from real runs, not hand-written           │
│                                                             │
│  3. IMPLEMENTATION CODE                                     │
│     └── The source files that produce (1)                   │
│                                                             │
│  4. THIS TASK LIST                                          │
│     └── Execution plan, derived from above                  │
│                                                             │
│  5. DESIGN SPECS / ARCHITECTURE DOCS (lowest authority)     │
│     └── Aspirational; historical once code exists           │
│                                                             │
│  CONFLICT RULE:                                             │
│  If higher-authority source differs from lower →            │
│  UPDATE THE LOWER SOURCE, not the higher.                   │
│                                                             │
│  NEVER change working code to match a design doc.           │
│  Instead, update the design doc to match reality.           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 STRICTNESS GATE PROTOCOL

```
┌─────────────────────────────────────────────────────────────┐
│  STRICTNESS GATES: Prevent premature tightening             │
│                                                             │
│  Many projects have "loose → strict" transitions:           │
│  - Validation: permissive → strict                          │
│  - Types: Any → specific                                    │
│  - Checks: warnings → errors                                │
│  - Constraints: optional → required                         │
│                                                             │
│  RULE: Cannot tighten until loose version passes:           │
│                                                             │
│  1. Implement with loose/permissive settings                │
│  2. Run against N representative real-world inputs          │
│  3. ALL must pass without error                             │
│  4. Only then tighten constraints                           │
│  5. Re-run same inputs; failures indicate model bug         │
│                                                             │
│  If tightening causes failures → FIX THE MODEL/CODE         │
│  Do NOT synthesize fake data to satisfy strict checks       │
└─────────────────────────────────────────────────────────────┘
```

### Strictness Gate Template

```bash
# Before tightening [CONSTRAINT_NAME]:
# 1. Run loose version against real inputs
[LOOSE_VALIDATION_COMMAND]
# Expected: PASS on N≥[MINIMUM] inputs

# 2. Only after (1) passes, tighten
[TIGHTEN_COMMAND]

# 3. Re-run same inputs
[STRICT_VALIDATION_COMMAND]
# Expected: PASS on same inputs

# If (3) fails but (1) passed → Model/code is wrong, not inputs
```

---

## 🚫 UNIMPLEMENTED FEATURE PROTOCOL

```
┌─────────────────────────────────────────────────────────────┐
│  DO NOT TEST FEATURES THAT DON'T EXIST YET                  │
│                                                             │
│  Design docs often describe future features.                │
│  Task lists may reference planned capabilities.             │
│                                                             │
│  BEFORE writing a test for ANY feature:                     │
│                                                             │
│  1. VERIFY it exists in running code                        │
│     └── grep, import, or execute to confirm                 │
│                                                             │
│  2. VERIFY it produces the expected output                  │
│     └── Run it, capture output, inspect                     │
│                                                             │
│  3. Only then write assertions about it                     │
│                                                             │
│  FOR RESERVED/PLANNED FEATURES:                             │
│  - Define with safe defaults (Optional, None, empty)        │
│  - DO NOT assert specific values                            │
│  - DO NOT synthesize fake data to satisfy tests             │
│  - Mark clearly as "reserved" or "not yet implemented"      │
└─────────────────────────────────────────────────────────────┘
```

### Feature Verification Checklist

Before testing `[FEATURE]`:

- [ ] Feature exists in code: `grep -rn "[FEATURE]" src/`
- [ ] Feature is callable/accessible (not just defined)
- [ ] Feature produces output matching test expectations
- [ ] Feature is NOT marked "reserved", "planned", "TODO"

```bash
# Verification command template
grep -rn "[FEATURE_NAME]" src/ && echo "✅ Found" || echo "❌ NOT FOUND - do not test"
```

---

## 🔍 CODE-FIRST VERIFICATION

```
┌─────────────────────────────────────────────────────────────┐
│  VERIFY BEFORE ASSUMING                                     │
│                                                             │
│  Design docs may reference:                                 │
│  - Class names that don't exist                             │
│  - Method signatures that differ                            │
│  - Constants with wrong values                              │
│  - APIs that were renamed or removed                        │
│                                                             │
│  BEFORE writing code/tests that depend on a symbol:         │
│                                                             │
│  1. grep for the exact symbol name                          │
│  2. Verify signature/parameters match expectations          │
│  3. If mismatch: UPDATE TASK LIST, not code                 │
│                                                             │
│  This prevents:                                             │
│  - Tests that fail due to typos in design docs              │
│  - Renaming stable code to match outdated specs             │
│  - Importing modules that don't exist                       │
└─────────────────────────────────────────────────────────────┘
```

### Symbol Verification Template

```bash
# Before using [SYMBOL] from design doc:

# 1. Verify class/function/type exists
grep -rn "class [CLASS_NAME]" src/           # Python
grep -rn "function [FUNC_NAME]" src/         # JavaScript
grep -rn "struct [STRUCT_NAME]" src/         # Rust/Go/C
grep -rn "interface [IFACE_NAME]" src/       # TypeScript/Java

# 2. Verify signature (if applicable)
grep -A5 "[FUNCTION_NAME]" src/

# 3. Verify constants/values
grep -rn "[CONSTANT_NAME]" src/

# If ANY verification fails:
# → Update task list to match actual code
# → DO NOT rename code to match task list
```

---

## 🧪 TDD Protocol

Every task follows this sequence:

```
1. WRITE TEST FIRST (or identify existing test)
   └── Test must fail initially (red)
   └── Test must assert SPECIFIC BEHAVIOR (see Test Strength Rules)

2. IMPLEMENT minimum code to pass
   └── Test must pass (green)

3. VERIFY no regressions
   └── Run: [full_test_command]
   └── Expected: N/N PASS

4. CLEAN TABLE CHECK
   └── No TODOs, no placeholders, no warnings

5. FILE MANIFEST CHECK
   └── Every file in "Files:" header exists
```

**Test Commands Reference**:
```bash
# Fast iteration (after each small change)
[FAST_TEST_COMMAND]

# Full validation (before commits)
[FULL_TEST_COMMAND]

# Performance check (before phase completion)
[PERF_TEST_COMMAND]
```

---

## ⛔ TEST STRENGTH RULES (MANDATORY)

```
┌─────────────────────────────────────────────────────────────┐
│  FORBIDDEN TEST PATTERNS - DO NOT USE:                      │
│                                                             │
│  ❌ assert result.returncode == 0  (only proves it runs)    │
│  ❌ assert result.returncode in (0, 1)  (useless)           │
│  ❌ assert "something" in output   (too vague)              │
│  ❌ Tests with no assertions                                │
│  ❌ Tests that pass with empty/stub implementation          │
│                                                             │
│  ❌ EXIT CODE TOLERANCE:                                    │
│     assert result.returncode in (0, 1)  # Accepts BOTH!     │
│     # Tool could be unimplemented, just sys.exit(0)         │
│                                                             │
│  ❌ "PRINTS SOMETHING PLAUSIBLE":                           │
│     assert "exported" in result.stdout.lower()              │
│     assert "Discovered" in output                           │
│     # Stub that prints "exported" passes!                   │
│                                                             │
│  ❌ IMPORT-ONLY tests:                                      │
│     test_module(): import mymodule  # proves nothing        │
│                                                             │
│  ❌ EXISTENCE-ONLY tests:                                   │
│     assert file.exists()  # no content verification         │
│     assert length(output) > 0  # just "not empty"           │
│                                                             │
│  ❌ SMOKE tests (just runs without crash):                  │
│     result = run_tool()  # no assertion on behavior         │
│     assert result != null  # trivially true                 │
│                                                             │
│  ❌ LINE-COUNT tests:                                       │
│     assert length(lines) > 10  # arbitrary threshold        │
│                                                             │
│  ❌ CI/WORKFLOW tests that only check strings:              │
│     assert "validate_tool.py" in workflow_yaml              │
│     # Doesn't verify correct wiring, just presence          │
│                                                             │
│  REQUIRED TEST PATTERNS - MUST USE:                         │
│                                                             │
│  ✅ Assert specific output values or structures             │
│  ✅ Assert count/quantity of results (== expected, not >0)  │
│  ✅ Assert file contents, not just file existence           │
│  ✅ Assert behavior differences between valid/invalid input │
│  ✅ Tests that FAIL with stub implementation                │
│  ✅ Fixture-driven deterministic outcomes                   │
│  ✅ Each error code/rule has test that triggers it          │
│  ✅ Exit code 0 means SUCCESS, exit code 1 means FAILURE    │
│     (never accept both as "passing")                        │
└─────────────────────────────────────────────────────────────┘
```

### Test Strength Checklist (Apply to EVERY Test)

Before accepting a test as valid:

- [ ] **Stub test**: Would this pass if implementation just returned `None` or `[]`? → If YES, test is too weak
- [ ] **Behavior captured**: Does test verify the actual business logic, not just "code ran"?
- [ ] **Failure modes**: Does test distinguish success from failure cases?
- [ ] **Output verification**: Does test check actual output content, not just presence?
- [ ] **Deterministic**: Does test use fixtures for reproducible outcomes?
- [ ] **Rule coverage**: If code emits error codes/rules, does each have a triggering test?
- [ ] **Existence vs Correctness**: Does test check semantic correctness, not just "file exists"?

### Existence vs Correctness Tests

```
┌─────────────────────────────────────────────────────────────┐
│  EXISTENCE TESTS ARE NOT CORRECTNESS TESTS                  │
│                                                             │
│  ❌ EXISTENCE-ONLY (weak):                                  │
│     assert file("output.json").exists()                     │
│     assert length(content) > 0                              │
│     assert "exported" in stdout                             │
│                                                             │
│  These pass with a stub that writes "{}" or "exported\n"    │
│                                                             │
│  ✅ CORRECTNESS (strong):                                   │
│     data = parse(file("output.json"))                       │
│     assert data["$id"] == "expected-schema-url"             │
│     assert "metadata" in data["properties"]                 │
│     assert data["required"] contains ["content", "metadata"]│
│                                                             │
│  These fail unless the output is semantically correct       │
└─────────────────────────────────────────────────────────────┘
```

Example - Schema Export Test:
```
# ❌ WEAK: Only checks existence
test_export_schema():
    run(["./export_schema"])
    assert file("schema.json").exists()
    assert "exported" in stdout

# ✅ STRONG: Checks semantic correctness
test_export_schema():
    run(["./export_schema"])
    schema = json.load(file("schema.json"))
    assert schema["$id"] == "https://example.com/parser-output.schema.json"
    assert "metadata" in schema["properties"]
    assert "content" in schema["properties"]
    assert schema["properties"]["metadata"]["type"] == "object"
```

---

## 🎭 NO-OP STUB TOOL DETECTION

```
┌─────────────────────────────────────────────────────────────┐
│  TOOLS CAN SATISFY TESTS WITHOUT DOING REAL WORK            │
│                                                             │
│  PROBLEM: Tests check tool outputs but not tool behavior    │
│                                                             │
│  Example - Validation Tool Tests:                           │
│  ✓ --help exits 0 and mentions --report                     │
│  ✓ --report writes JSON with {total, passed, pass_rate}     │
│  ✓ --threshold 0 exits 0                                    │
│  ✓ --threshold 101 exits 1                                  │
│                                                             │
│  NO-OP STUB THAT PASSES ALL TESTS:                          │
│  def main():                                                │
│      if "--help" in sys.argv:                               │
│          print("--report --threshold"); sys.exit(0)         │
│      report = {"total": 0, "passed": 0, "pass_rate": 0.0}   │
│      write_json(report)  # Never validated anything!        │
│      threshold = get_threshold()                            │
│      sys.exit(0 if threshold <= 0 else 1)                   │
│                                                             │
│  This stub:                                                 │
│  ❌ Never reads actual fixture files                        │
│  ❌ Never calls schema validation                           │
│  ❌ Never parses real data                                  │
│  ✓ Passes all tests!                                        │
│                                                             │
│  REQUIRED TESTS TO PREVENT NO-OP STUBS:                     │
│                                                             │
│  ✅ Test with KNOWN-GOOD input: total > 0, passed > 0       │
│  ✅ Test with KNOWN-BAD input: failed > 0, specific error   │
│  ✅ Test that tool actually calls the validation function   │
│     (mock/spy if needed)                                    │
│  ✅ Test exit code matches actual results, not canned       │
└─────────────────────────────────────────────────────────────┘
```

### No-Op Stub Prevention Tests

```
# For any tool that validates/processes data:

test_tool_processes_real_good_input():
    # Run against known-good fixtures directory
    result = run_tool(["--input", "fixtures/valid/"])
    report = parse_output(result)
    assert report["total"] > 0, "Must process at least 1 fixture"
    assert report["passed"] > 0, "Known-good fixtures must pass"

test_tool_detects_real_bad_input():
    # Run against known-bad fixture
    result = run_tool(["--input", "fixtures/invalid/malformed.json"])
    report = parse_output(result)
    assert report["failed"] > 0, "Must detect invalid fixture"
    assert "validation error" in report["errors"][0].lower()

test_tool_exit_code_reflects_results():
    # With threshold 100%, known-bad input must fail
    result = run_tool(["--input", "fixtures/invalid/", "--threshold", "100"])
    assert result.exitCode != 0, "Must fail when threshold not met"
```

---

## 📝 CONSCIOUS TRADE-OFF DOCUMENTATION

```
┌─────────────────────────────────────────────────────────────┐
│  SOME TESTS ARE INTENTIONALLY WEAK - DOCUMENT WHY           │
│                                                             │
│  Not all tests can or should be bulletproof. But:           │
│  - Weak tests that LOOK strong create false confidence      │
│  - Undocumented trade-offs become forgotten oversights      │
│                                                             │
│  PATTERN: Mark intentional weaknesses explicitly            │
│                                                             │
│  # TRADE-OFF: This test only verifies command presence,     │
│  # not correct wiring. Full CI testing would be brittle     │
│  # and duplicate what CI itself validates. Accepted risk:   │
│  # someone could write plausible-looking but broken CI.     │
│  def test_ci_workflow_commands_present():                   │
│      ...                                                    │
│                                                             │
│  REQUIRED FOR INTENTIONALLY WEAK TESTS:                     │
│                                                             │
│  ✅ Comment explaining WHY test is limited                  │
│  ✅ What risk is accepted                                   │
│  ✅ What would break if assumption is wrong                 │
│  ✅ Whether stronger test is possible but rejected          │
│                                                             │
│  FORBIDDEN:                                                 │
│  ❌ Weak test with no explanation (looks like oversight)    │
│  ❌ "This is good enough" without stating trade-off         │
│  ❌ Assuming readers know why test is limited               │
└─────────────────────────────────────────────────────────────┘
```

### Trade-off Documentation Template

```
# CONSCIOUS TRADE-OFF: [Test Name]
# 
# LIMITATION: [What this test doesn't verify]
# 
# REASON: [Why stronger test was rejected]
#   - [Specific reason 1]
#   - [Specific reason 2]
# 
# ACCEPTED RISK: [What could go wrong]
# 
# MITIGATION: [How the risk is handled elsewhere, if at all]
# 
# REVISIT IF: [Conditions under which to strengthen this test]
```

### Forbidden vs Required Examples

> **Note**: Examples below use Python syntax, but the **patterns apply to any language**.
> The key concepts are: (1) don't just check exit codes, (2) verify actual output content,
> (3) test both success and failure paths distinctly.

```
# ❌ FORBIDDEN: "It runs" test
test_discover_shape():
    result = run(["./tools/discover"])
    assert result.exitCode == 0  # USELESS - stub passes this

# ✅ REQUIRED: Behavior test
test_discover_shape():
    result = run(["./tools/discover"], captureOutput=true)
    assert result.exitCode == 0
    
    # Verify actual output exists and has content
    output = file("all_keys.txt")
    assert output.exists(), "Output file must be created"
    
    lines = output.read().split("\n")
    assert length(lines) >= 10, "Expected ≥10 keys discovered"
    
    # Verify specific expected keys appear
    assert any("metadata" in line for line in lines), "Must discover metadata keys"
```

```
# ❌ FORBIDDEN: Exit code tolerance
test_validator():
    result = run(["./tools/validate"])
    assert result.exitCode in (0, 1)  # USELESS - any behavior passes

# ✅ REQUIRED: Distinct behavior verification
test_validator_valid_input():
    result = run(["./tools/validate", "valid.json"], captureOutput=true)
    assert result.exitCode == 0
    assert "PASS" in result.stdout
    assert "errors: 0" in result.stdout

test_validator_invalid_input():
    result = run(["./tools/validate", "invalid.json"], captureOutput=true)
    assert result.exitCode == 1  # Must fail for invalid
    assert "FAIL" in result.stdout
    assert "errors:" in result.stdout
```

---

## 🧹 Clean Table Definition

> A task is CLEAN only when ALL are true:

**Completeness**:
- ✅ No unresolved errors or warnings
- ✅ No TODOs, FIXMEs, or placeholders in changed code
- ✅ No unverified assumptions; facts are checked or removed
- ✅ No duplicated, conflicting, or workaround logic
- ✅ Tests pass (not skipped, not mocked away)
- ✅ Code is production-ready (not "good enough for now")

**No Hidden Debt**:
- ✅ No "temporary" fixes or band-aids masking root causes
- ✅ No deferred follow-ups ("adjust later", "check this later")
- ✅ No speculative comments ("you may need to", "might require")
- ✅ Solution is canonical and stable, not a workaround

**No Silent Errors**:
- ✅ All errors raise unconditionally (no swallowed exceptions)
- ✅ No "strict mode" toggles or conditional error handling
- ✅ No environment variables that disable error checking
- ✅ Execution stops on error; no "continue on failure" paths

**File & Symbol Integrity**:
- ✅ All files listed in task "Files:" header actually exist
- ✅ No literal placeholders in artifacts (e.g., `YYYY-MM-DD` must be replaced)
- ✅ No tests for unimplemented features
- ✅ No assumptions about code that weren't verified

**Code Quality (SOLID/KISS/YAGNI)**:
- ✅ **YAGNI**: All new code has immediate consumer (passed decision tree)
- ✅ **KISS**: Simpler alternative was considered and rejected with reason
- ✅ **SRP**: Each new module/class has single clear purpose
- ✅ No unused parameters, hooks, flags, or abstractions
- ✅ Generalizations have ≥2 real consumers (not speculative)

**If any box is unchecked → task is NOT complete.**

---

## 🔇 NO SILENT ERRORS

```
┌─────────────────────────────────────────────────────────────┐
│  ALL ERRORS MUST RAISE UNCONDITIONALLY                      │
│                                                             │
│  There is no "strict mode" toggle. Errors are always fatal. │
│                                                             │
│  FORBIDDEN PATTERNS:                                        │
│                                                             │
│  ❌ Conditional raise based on flag:                        │
│     except Exception as e:                                  │
│         if strict:                                          │
│             raise                                           │
│         errors.append(e)  # swallowed!                      │
│         continue                                            │
│                                                             │
│  ❌ Swallowed exception with warning:                       │
│     except Exception as e:                                  │
│         print(f"Warning: {e}")                              │
│         continue                                            │
│                                                             │
│  ❌ Strict mode parameter:                                  │
│     def process(data, strict: bool = True): ...             │
│                                                             │
│  ❌ Environment variable for strict mode:                   │
│     if os.environ.get("STRICT_MODE"):                       │
│         raise SomeError(...)                                │
│                                                             │
│  REQUIRED PATTERN:                                          │
│                                                             │
│  ✅ Unconditional raise, no conditions:                     │
│     except Exception as e:                                  │
│         raise ProcessingError(context, e) from e            │
│                                                             │
│  There must be NO possibility to choose "run without        │
│  error handling". Errors are never optional.                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📖 SPEC INTERPRETATION RULES

```
┌─────────────────────────────────────────────────────────────┐
│  NORMATIVE vs ASPIRATIONAL CONTENT                          │
│                                                             │
│  NORMATIVE (must follow exactly):                           │
│  - Phase gates and their criteria                           │
│  - TDD protocol steps                                       │
│  - Clean Table rules                                        │
│  - Test strength rules                                      │
│  - Source of truth hierarchy                                │
│  - Rollback procedures                                      │
│                                                             │
│  ASPIRATIONAL (derive from code, don't enforce):            │
│  - "Final state" / "target architecture" sections           │
│  - Example schemas or data structures                       │
│  - Field/API tables in design documents                     │
│  - Diagrams showing future state                            │
│                                                             │
│  RULE: When you see a complete schema/structure labeled     │
│  "final" or "target" → treat as "where we want to end up"   │
│  NOT as "what must be implemented exactly as written"       │
│                                                             │
│  Derive actual names/structures from RUNNING CODE.          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 DISCOVERY-FIRST PROTOCOL

```
┌─────────────────────────────────────────────────────────────┐
│  DISCOVER BEFORE DEFINING                                   │
│                                                             │
│  When building models/schemas/types for existing code:      │
│                                                             │
│  1. RUN the existing code with representative inputs        │
│  2. CAPTURE actual outputs (JSON, logs, return values)      │
│  3. ANALYZE captured outputs for structure/patterns         │
│  4. DERIVE models from actual outputs                       │
│  5. VALIDATE models against captured outputs                │
│  6. Only then write tests that assert specific structures   │
│                                                             │
│  DO NOT:                                                    │
│  ❌ Define models from design docs alone                    │
│  ❌ Assume field names match documentation                  │
│  ❌ Write tests before discovery phase completes            │
│  ❌ Change existing code to match your models               │
│                                                             │
│  Discovery artifacts should include:                        │
│  - sample_outputs/ directory with real outputs              │
│  - all_keys.txt or similar listing all observed fields      │
│  - type_analysis.json showing inferred types                │
└─────────────────────────────────────────────────────────────┘
```

### Discovery Phase Template

```bash
# 1. Generate sample outputs from real code
[RUN_COMMAND] > sample_outputs/sample_001.[EXT]
[RUN_COMMAND] > sample_outputs/sample_002.[EXT]
# ... repeat for N≥10 representative inputs

# 2. Extract all unique keys/fields (method depends on output format)
# For JSON:
cat sample_outputs/*.json | jq -r 'paths | join(".")' | sort -u > all_keys.txt
# For XML:
grep -ohE '<[^/][^>]+>' sample_outputs/*.xml | sort -u > all_keys.txt
# For structured text:
[CUSTOM_EXTRACTION_COMMAND] > all_keys.txt

# 3. Verify discovery completeness
wc -l all_keys.txt
# Expected: ≥[MINIMUM_KEYS] unique paths/fields

# 4. Only proceed to model definition after discovery
test $(wc -l < all_keys.txt) -ge [MINIMUM_KEYS] && echo "✅ Discovery complete" || echo "❌ Insufficient discovery"
```

---

## 🏗️ CODE QUALITY PRINCIPLES

```
┌─────────────────────────────────────────────────────────────┐
│  MANDATORY DESIGN PRINCIPLES                                │
│                                                             │
│  SOLID (for maintainable design):                           │
│  ├── Single Responsibility: One module, one purpose         │
│  ├── Open/Closed: Open for extension, closed for changes    │
│  ├── Liskov Substitution: Subtypes must be substitutable    │
│  ├── Interface Segregation: Small, focused interfaces       │
│  └── Dependency Inversion: Depend on abstractions           │
│                                                             │
│  KISS (simplicity mandate):                                 │
│  └── Choose simplest solution that solves the problem       │
│      Simpler = easier to understand, maintain, debug        │
│                                                             │
│  YAGNI (feature discipline):                                │
│  └── Implement features only when currently needed          │
│      No speculative code, no "might need later"             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚦 YAGNI DECISION TREE

Before implementing ANY new feature, function, or abstraction:

```
┌─────────────────────────────────────────────────────────────┐
│  Q1: Is there a CURRENT requirement for this?               │
│      (Not "might need" or "could be useful")                │
│                                                             │
│      NO  → STOP. Do not implement. (YAGNI triggered)        │
│      YES → Continue to Q2                                   │
├─────────────────────────────────────────────────────────────┤
│  Q2: Will it be used IMMEDIATELY after it's built?          │
│      (By known code path, not hypothetical consumer)        │
│                                                             │
│      NO  → STOP. Do not implement. (YAGNI triggered)        │
│      YES → Continue to Q3                                   │
├─────────────────────────────────────────────────────────────┤
│  Q3: Is it backed by stakeholder request or concrete data?  │
│      (Not speculation or "good practice")                   │
│                                                             │
│      NO  → STOP. Do not implement. (YAGNI triggered)        │
│      YES → Continue to Q4                                   │
├─────────────────────────────────────────────────────────────┤
│  Q4: Can it be added LATER without massive rework?          │
│                                                             │
│      YES → WAIT until actually needed. (YAGNI triggered)    │
│      NO  → Implement now (confirmed unavoidable)            │
└─────────────────────────────────────────────────────────────┘

OUTCOME: implement_now = Q1_yes AND Q2_yes AND Q3_yes AND Q4_no
```

### YAGNI Violations to Avoid

| ❌ Violation | Why It's Wrong | ✅ Instead |
|-------------|----------------|-----------|
| Unused parameters | API surface with no consumer | Remove until needed |
| Speculative flags | `enable_feature_x=False` for "someday" | Add when feature exists |
| Premature abstraction | Interface with 1 implementation | Concrete until 2+ consumers |
| Unused hooks | `pre_hook`, `post_hook` with no callers | Plain function |
| Future-proofing | "We might need this later" | Build what's needed now |

---

## ✅ CODE QUALITY CHECKLIST

Add to task completion verification:

```
BEFORE marking any task complete, verify:

□ YAGNI: All new code has immediate consumer (no speculative features)
□ KISS: Simpler alternative was considered
□ SRP: Each new module/class has single clear purpose
□ No unused parameters, hooks, or abstractions added
□ Generalizations have ≥2 real consumers today
□ Tests prove current necessity (fail-before, pass-after)
```

---

## 🔄 REFLECTION LOOP (MANDATORY)

```
┌─────────────────────────────────────────────────────────────┐
│  BEFORE COMPLETING ANY TASK OR PHASE:                       │
│                                                             │
│  1. PAUSE - Do not proceed to next task                     │
│                                                             │
│  2. REFLECT - Answer these questions:                       │
│     □ Did I achieve the stated objective?                   │
│     □ Can I provide evidence for each claim I made?         │
│     □ Did I verify assumptions or just assume?              │
│     □ Are there risks I identified but didn't mitigate?     │
│     □ Is there anything I'm uncertain about?                │
│                                                             │
│  3. VALIDATE - Check against success criteria:              │
│     □ All tests pass (verified by running them)             │
│     □ Clean Table checklist complete                        │
│     □ No items deferred or skipped                          │
│     □ Every claim has evidence anchor (source + quote)      │
│                                                             │
│  4. DECIDE:                                                 │
│     - All checks pass → Proceed to next task                │
│     - Any uncertainty → STOP and clarify                    │
│     - Any failure → Fix before proceeding                   │
└─────────────────────────────────────────────────────────────┘
```

### Semantic Type Distinctions

When reflecting, distinguish between:

| Type | Definition | Requirement |
|------|------------|-------------|
| **FACT** | Verified true statement | Must have evidence anchor |
| **CLAIM** | Assertion being made | Must have supporting evidence |
| **ASSUMPTION** | Unverified belief | Must state + attempt to verify |
| **RISK** | Potential problem | Must have mitigation or acceptance |
| **HYPOTHESIS** | Testable proposition | Must have test + result |

```
❌ BAD: "The function returns a list" (unstated assumption)
✅ GOOD: "ASSUMPTION: The function returns a list
         VERIFICATION: grep -A5 'def process' src/module.py
         RESULT: Returns List[str] - CONFIRMED"
```

### Evidence Anchor Requirements

Every significant claim must have:

```
CLAIM: [What you're asserting]
SOURCE: [file:line or command output]
QUOTE: "[Exact text that supports claim]"
```

Example:
```
CLAIM: Parser handles nested structures
SOURCE: tests/test_parser.py:45
QUOTE: "def test_nested_dict(): assert parse({'a': {'b': 1}}) == expected"
```

### Reflection Template

After each task, explicitly state:

```
REFLECTION: Task [X.Y]
├── Objective achieved: [YES/NO + evidence anchor]
├── Claims made:
│   ├── CLAIM: [statement] → SOURCE: [file:line]
│   └── CLAIM: [statement] → SOURCE: [file:line]
├── Assumptions:
│   ├── ASSUMPTION: [statement] → VERIFIED: [YES/NO + how]
│   └── ASSUMPTION: [statement] → VERIFIED: [YES/NO + how]
├── Risks:
│   ├── RISK: [description] → MITIGATION: [action taken]
│   └── RISK: [description] → MITIGATION: [action taken]
├── Uncertainties: [list any that remain]
├── Confidence: [0-100%] (if <80% → STOP)
└── Decision: [PROCEED / STOP + reason]
```

### Trace Links (Decision → Evidence → Impact)

For significant decisions, create trace links:

```
TRACE LINK:
├── DECISION: [What action was taken]
├── EVIDENCE:
│   ├── CLAIM: [Supporting assertion]
│   │   └── SOURCE: [file:line], QUOTE: "[text]"
│   └── CLAIM: [Another assertion]
│       └── SOURCE: [file:line], QUOTE: "[text]"
├── IMPACT: [Consequence of this decision]
└── RELATED:
    ├── Assumptions: [list]
    ├── Risks: [list]
    └── Mitigations: [list]
```

---

## 🛑 STOP ON AMBIGUITY

```
┌─────────────────────────────────────────────────────────────┐
│  WHEN TO STOP AND CLARIFY:                                  │
│                                                             │
│  STOP if ANY of these are true:                             │
│                                                             │
│  □ Confidence in approach < 80%                             │
│  □ Missing information required to proceed                  │
│  □ Conflicting requirements detected                        │
│  □ Assumption cannot be verified                            │
│  □ Success criteria unclear or unmeasurable                 │
│  □ Multiple valid interpretations exist                     │
│                                                             │
│  DO NOT:                                                    │
│  ❌ Guess and proceed                                       │
│  ❌ Make assumptions without stating them                   │
│  ❌ Pick arbitrary interpretation                           │
│  ❌ Defer clarification to later                            │
│                                                             │
│  INSTEAD:                                                   │
│  ✅ State what is blocking                                  │
│  ✅ State what information is needed                        │
│  ✅ State what will be done once clarified                  │
└─────────────────────────────────────────────────────────────┘
```

### Stop Block Template

When stopping for clarification, use this format:

```
⛔ STOP: CLARIFICATION REQUIRED

BLOCKING: [What element is missing or ambiguous]
REASON: [Why we cannot proceed without this]
NEEDED: [Minimal information required to continue]
NEXT STEP: [What will be executed once provided]

Awaiting clarification before proceeding.
```

---

## 🧠 THINKING vs EXECUTION BOUNDARIES

```
┌─────────────────────────────────────────────────────────────┐
│  SEPARATE REASONING FROM ACTION                             │
│                                                             │
│  --- THINKING ---                                           │
│  • Assumptions being made                                   │
│  • Risks being considered                                   │
│  • Trade-offs being evaluated                               │
│  • Alternative approaches considered                        │
│  • Why chosen approach is best                              │
│                                                             │
│  --- EXECUTION ---                                          │
│  • Exact command/code to run                                │
│  • Expected output/result                                   │
│  • How to validate success                                  │
│                                                             │
│  This separation ensures:                                   │
│  • Reasoning is explicit and reviewable                     │
│  • Actions are concrete and verifiable                      │
│  • Mistakes in logic vs execution are distinguishable       │
└─────────────────────────────────────────────────────────────┘
```

### Decision Chain Template

For significant decisions, document:

```
DECISION: [What action to take]
├── WHY: [Evidence-based reason]
│   └── EVIDENCE: [source:line] "[quote]"
├── WHY NOT alternatives:
│   ├── [Alternative 1]: Rejected because [reason]
│   └── [Alternative 2]: Rejected because [reason]
├── IMPACT: [Expected consequence]
├── ASSUMPTIONS: [What we're assuming is true]
│   └── VERIFICATION: [How verified, or "UNVERIFIED - RISK"]
├── RISKS: [What could go wrong]
│   └── MITIGATION: [Action taken, or "ACCEPTED because [reason]"]
└── VALIDATION: [How we'll verify this was correct]
```

Example:
```
DECISION: Use polling instead of webhooks for data sync
├── WHY: Target API doesn't support webhooks
│   └── EVIDENCE: docs/api.md:45 "Events API: Coming Q3 2025"
├── WHY NOT alternatives:
│   ├── Webhooks: Rejected because not yet available
│   └── WebSockets: Rejected because API doesn't support
├── IMPACT: 30-second delay in data freshness
├── ASSUMPTIONS: API rate limits allow 2 req/min
│   └── VERIFICATION: docs/api.md:12 "Rate limit: 100 req/min" - VERIFIED
├── RISKS: Rate limiting during high-traffic periods
│   └── MITIGATION: Exponential backoff implemented in sync.py:89
└── VALIDATION: Integration test covers rate limit scenario
```

---

## 📋 TASK COMPLETION VALIDATION PIPELINE

Before marking any task complete, execute this pipeline in order:

```
┌─────────────────────────────────────────────────────────────┐
│  VALIDATION PIPELINE (Execute in order, stop on failure)    │
│                                                             │
│  1. BUILD decision chains                                   │
│     └── Document what/why/why_not for significant choices   │
│                                                             │
│  2. ATTACH evidence anchors                                 │
│     └── Every claim has: source + quote                     │
│     └── Missing evidence → STOP                             │
│                                                             │
│  3. CREATE trace links                                      │
│     └── Decision → Evidence → Impact connected              │
│                                                             │
│  4. ASSESS confidence                                       │
│     └── If < 80% certain on any element → STOP              │
│                                                             │
│  5. SEPARATE thinking from execution                        │
│     └── Reasoning documented, actions concrete              │
│                                                             │
│  6. REFLECT                                                 │
│     └── Evidence + decisions satisfy success criteria?      │
│     └── If not → STOP                                       │
│                                                             │
│  7. CROSS-REFERENCE                                         │
│     └── No conflicts between claims and results             │
│     └── All assumptions verified or flagged                 │
│     └── All risks mitigated or accepted with reason         │
│                                                             │
│  If ANY step fails → Do not complete task. Fix or STOP.     │
└─────────────────────────────────────────────────────────────┘
```

### Quick Validation Checklist

```
□ Decision chains documented (what/why/why_not/impact)
□ Evidence anchors present (claim → source:line → quote)
□ Trace links created for significant decisions
□ Confidence ≥ 80% on all elements
□ Thinking separated from execution
□ Reflection complete with semantic types distinguished
□ Cross-reference: no conflicts, assumptions verified, risks handled
□ Clean Table checklist passes
□ Tests pass (actually run, not assumed)
```

---

## 📁 File Manifest Rules

```
┌─────────────────────────────────────────────────────────────┐
│  FILE MANIFEST ENFORCEMENT:                                 │
│                                                             │
│  Every task has a "Files:" header listing affected files.   │
│                                                             │
│  RULE: If a file is listed, it MUST:                        │
│  1. Be created/modified by a step in that task              │
│  2. Exist after task completion                             │
│  3. Be verifiable via: test -f <filename>                   │
│                                                             │
│  If a file is listed but not created → TASK INCOMPLETE      │
│  If a file is created but not listed → Add it to Files:     │
│                                                             │
│  GHOST FILES ARE FORBIDDEN                                  │
└─────────────────────────────────────────────────────────────┘
```

### File Manifest Verification Command

```bash
# Run after each task to verify all listed files exist
# Replace FILE_LIST with actual files from task header
for f in FILE_LIST; do
    test -f "$f" && echo "✅ $f" || echo "❌ MISSING: $f"
done
```

---

## 🔢 TASK ID UNIQUENESS

```
┌─────────────────────────────────────────────────────────────┐
│  TASK IDs MUST BE UNIQUE AND 1:1 WITH TASKS                 │
│                                                             │
│  FORBIDDEN:                                                 │
│  ❌ Reusing same ID for different tasks                     │
│     Task 2.2a: Structure Models                             │
│     Task 2.2a: Update Empty Method  ← CONFLICT!             │
│                                                             │
│  ❌ Slices/sub-tasks without tracked IDs                    │
│     Task 2.2 mentions "slices 2.2a-e" but Appendix          │
│     only tracks 2.2a                                        │
│                                                             │
│  REQUIRED:                                                  │
│  ✅ Every task has unique ID (X.Y or X.Y.Z)                 │
│  ✅ Every slice mentioned in narrative has ID               │
│  ✅ Appendix/tracking table covers ALL IDs                  │
│  ✅ ID → Task is bijective (one-to-one mapping)             │
│                                                             │
│  WHY: Ambiguous IDs break file tracking, progress logs,     │
│  and allow "which 2.2a?" confusion during execution.        │
└─────────────────────────────────────────────────────────────┘
```

### Task ID Verification

Before finalizing task list:
```bash
# Extract all task IDs mentioned in document
grep -oE "Task [0-9]+\.[0-9]+[a-z]?" PROJECT_TASKS.md | sort | uniq -d
# Expected: NO OUTPUT (no duplicates)

# Verify Appendix covers all IDs
grep -oE "[0-9]+\.[0-9]+[a-z]?" PROJECT_TASKS.md | sort -u > /tmp/task_ids.txt
grep -oE "^[|] *[0-9]+\.[0-9]+[a-z]?" PROJECT_TASKS.md | sort -u > /tmp/tracked_ids.txt
comm -23 /tmp/task_ids.txt /tmp/tracked_ids.txt
# Expected: NO OUTPUT (all tasks tracked in Appendix)
```

---

## 🔍 SCOPE DECISIONS TABLE

```
┌─────────────────────────────────────────────────────────────┐
│  EXPLICITLY DECLARE WHAT'S IN AND OUT OF SCOPE              │
│                                                             │
│  At the top of your task list, include a scope table:       │
│                                                             │
│  | Item                    | Status      | Rationale       │
│  |-------------------------|-------------|-----------------|
│  | Core feature X          | IN SCOPE    | Primary goal    │
│  | Edge case Y             | IN SCOPE    | Critical path   │
│  | Nice-to-have Z          | OUT OF SCOPE| Defer to v2     │
│  | Legacy cleanup W        | OUT OF SCOPE| Separate effort │
│                                                             │
│  WHY: Prevents scope creep and makes exclusions explicit.   │
│  Anyone reading knows what WON'T be done, not just what     │
│  will be done.                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌐 GLOBAL CLEAN TABLE ENFORCEMENT

```
┌─────────────────────────────────────────────────────────────┐
│  CLEAN TABLE CHECKS MUST BE GLOBAL, NOT SELECTIVE           │
│                                                             │
│  FORBIDDEN:                                                 │
│  ❌ Ad-hoc greps on only some files:                        │
│     grep "TODO" file1.py file2.py  # Misses file3.py!       │
│                                                             │
│  ❌ Phase gates that only check changed files:              │
│     # Doesn't catch pre-existing debt                       │
│                                                             │
│  REQUIRED:                                                  │
│  ✅ Single global check across entire repo:                 │
│     grep -rn "TODO\|FIXME\|XXX" src/ tests/ tools/          │
│                                                             │
│  ✅ Phase artifacts checked for placeholders:               │
│     grep -E "YYYY|MM-DD|placeholder|\[.*\]" .phase-*.json   │
│                                                             │
│  ✅ Ideally: automated test that fails on any violation     │
└─────────────────────────────────────────────────────────────┘
```

### Heredoc/Template Placeholder Detection

```
┌─────────────────────────────────────────────────────────────┐
│  HEREDOCS AND TEMPLATES OFTEN CONTAIN LITERAL PLACEHOLDERS  │
│                                                             │
│  PROBLEM: Task list shows:                                  │
│     cat > .phase-0.complete.json << 'EOF'                   │
│     {                                                       │
│       "completion_date": "YYYY-MM-DDTHH:MM:SSZ"  ← LITERAL! │
│     }                                                       │
│     EOF                                                     │
│                                                             │
│  If executed literally, the artifact contains a placeholder │
│  which violates Clean Table but no check catches it.        │
│                                                             │
│  REQUIRED:                                                  │
│  ✅ Either: Use shell variable substitution:                │
│     "completion_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"     │
│                                                             │
│  ✅ Or: Explicit instruction to replace before commit:      │
│     "Replace YYYY-MM-DDTHH:MM:SSZ with actual timestamp"    │
│                                                             │
│  ✅ And: Global check for common placeholder patterns:      │
│     grep -rE "YYYY|XXXX|\[INSERT|\[TODO\]|placeholder"      │
│                                                             │
│  COMMON PLACEHOLDER PATTERNS TO DETECT:                     │
│  • YYYY-MM-DD, YYYY/MM/DD (date placeholders)               │
│  • [INSERT X], [TODO], [PLACEHOLDER]                        │
│  • YOUR_*, MY_*, EXAMPLE_* (template variables)             │
│  • <description>, <your-value> (XML-style placeholders)     │
│  • __REPLACE__, %%VARIABLE%% (template markers)             │
└─────────────────────────────────────────────────────────────┘
```

### Global Clean Table Test Template

```
# tests/test_clean_table_global.[ext]
# This test runs on every CI build and fails if debt found

test_no_todos_in_codebase():
    result = run(["grep", "-rn", "TODO|FIXME|XXX", "src/", "tests/", "tools/"])
    assert result.exitCode == 1, "Found TODOs in codebase"  # grep returns 1 if no match

test_no_placeholders_in_artifacts():
    result = run(["grep", "-rE", "YYYY-MM-DD|placeholder|\\[INSERT", "."])
    assert result.exitCode == 1, "Found placeholders in repo"

test_no_template_literals_in_generated_files():
    # Check phase completion artifacts
    for artifact in glob(".phase-*.json"):
        content = read(artifact)
        assert "YYYY" not in content, f"Placeholder in {artifact}"
        assert "XXXX" not in content, f"Placeholder in {artifact}"
        assert "[INSERT" not in content, f"Placeholder in {artifact}"
```

---

## 🎯 PHASE GATE SCOPE ALIGNMENT

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE GATES MUST ENFORCE THE SAME SCOPE AS GLOBAL RULES    │
│                                                             │
│  PROBLEM:                                                   │
│  Global rule: "Clean Table applies to entire repo"          │
│  Phase 0 gate: grep TODO file1.py file2.py  # Only 2 files! │
│                                                             │
│  RESULT:                                                    │
│  - TODOs can exist in src/ during Phase 0-2                 │
│  - Only Phase 3+ catches them (when global test added)      │
│  - Early phases have weaker enforcement than later phases   │
│                                                             │
│  REQUIRED:                                                  │
│  ✅ If rule is global, ALL phase gates enforce it globally  │
│  ✅ Or: Global test exists from Phase 0 (not introduced     │
│     later)                                                  │
│  ✅ Phase gates should reference the global test, not       │
│     duplicate logic with narrower scope                     │
│                                                             │
│  PATTERN:                                                   │
│  Phase 0 Gate:                                              │
│    - Run: [FAST_TEST_COMMAND] tests/test_clean_table.py     │
│    - NOT: grep TODO only-these-two-files.py                 │
└─────────────────────────────────────────────────────────────┘
```

---

## ⏱️ TEMPORAL DEBT WINDOW

```
┌─────────────────────────────────────────────────────────────┐
│  AVOID WORKFLOWS THAT CREATE TEMPORARY DEBT IN TRACKED FILES│
│                                                             │
│  PROBLEM WORKFLOW:                                          │
│  1. Create .phase-0.complete.json with placeholder date     │
│  2. Run tests → pass (placeholder not yet committed)        │
│  3. Edit file to replace placeholder with real date         │
│  4. Forget to re-run tests                                  │
│  5. Commit via GUI → placeholder could slip through         │
│                                                             │
│  The "debt window" is step 1→3 where invalid content exists │
│  in a tracked file but hasn't been caught yet.              │
│                                                             │
│  SOLUTIONS:                                                 │
│                                                             │
│  Option A: Never create placeholders                        │
│     Use shell substitution: $(date -u +%Y-%m-%dT%H:%M:%SZ)  │
│     File is correct from creation                           │
│                                                             │
│  Option B: Pre-commit hook                                  │
│     Hook runs placeholder check before every commit         │
│     Cannot accidentally commit debt                         │
│                                                             │
│  Option C: CI as safety net (current approach)              │
│     Global test catches placeholders                        │
│     But requires discipline to run tests after edits        │
│                                                             │
│  DOCUMENT which option you're using and its trade-offs      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Environment Portability Rules

```
┌─────────────────────────────────────────────────────────────┐
│  FORBIDDEN PATTERNS (examples from various languages):      │
│                                                             │
│  ❌ Hard-coded paths:                                       │
│     .venv/bin/python, /usr/bin/node, C:\Ruby\bin\ruby      │
│  ❌ System-specific paths:                                  │
│     /usr/local/bin/*, /opt/homebrew/bin/*                  │
│  ❌ Version-pinned executables in paths:                    │
│     python3.11, node18, ruby3.2                            │
│                                                             │
│  REQUIRED PATTERNS:                                         │
│                                                             │
│  ✅ Use runtime's self-reference where available:           │
│     Python: sys.executable                                  │
│     Node: process.execPath                                  │
│     Ruby: RbConfig.ruby                                     │
│  ✅ Use package manager invocation:                         │
│     python -m module, npx command, bundle exec              │
│  ✅ Use shell lookup:                                       │
│     $(which python), $(which node), $(which ruby)          │
│                                                             │
│  For tool dependencies (rg, jq, etc.):                      │
│  - Document in Prerequisites section                        │
│  - Add existence check in verification commands             │
│  - Provide installation instructions                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📐 ASPIRATIONAL VS ACTUAL ALIGNMENT

```
┌─────────────────────────────────────────────────────────────┐
│  IF YOU DEFINE A PATTERN, USE IT EVERYWHERE                 │
│                                                             │
│  FORBIDDEN:                                                 │
│  ❌ Define helper but don't use it in examples:             │
│     "Use PYTHON env var for portability"                    │
│     ...later in same doc...                                 │
│     subprocess.run([".venv/bin/python", ...])  # Ignores!   │
│                                                             │
│  ❌ Document skip pattern but test doesn't use it:          │
│     "Skip gracefully if rg not installed"                   │
│     ...test code...                                         │
│     result = run(["rg", ...])  # Hard fails if missing!     │
│                                                             │
│  REQUIRED:                                                  │
│  ✅ Every pattern/helper defined MUST appear in all         │
│     relevant examples in the same document                  │
│  ✅ If you show "the right way", never show "the wrong way" │
│     in executable code blocks                               │
│  ✅ Audit: search for pattern violations in your own doc    │
│                                                             │
│  WHY: Readers copy-paste examples. If examples contradict   │
│  your guidelines, guidelines are effectively dead.          │
└─────────────────────────────────────────────────────────────┘
```

### Aspirational vs Actual Audit

Before finalizing task list:
```bash
# If you defined PYTHON helper, verify all subprocess calls use it
grep -n "PYTHON\s*=" PROJECT_TASKS.md  # Find definition
grep -n "\.venv/bin/python\|/usr/bin/python" PROJECT_TASKS.md
# Expected: No hard-coded paths after helper is defined

# If you defined skip pattern for tool X, verify tests use it
grep -n "pytest.skip.*X not" PROJECT_TASKS.md  # Find pattern
grep -n "subprocess.*\[\"X\"" PROJECT_TASKS.md  # Find usages
# Expected: All usages either have skip guard or are in "wrong" examples
```

---

## ⚠️ PRE-RUN DEPENDENCIES IN TESTS

```
┌─────────────────────────────────────────────────────────────┐
│  TESTS THAT REQUIRE MANUAL PRE-RUN ARE FRAGILE              │
│                                                             │
│  PATTERN:                                                   │
│  test_output_file_valid():                                  │
│      if not file("output.json").exists():                   │
│          pytest.skip("Run tool first")  # FRAGILE!          │
│      ...                                                    │
│                                                             │
│  PROBLEMS:                                                  │
│  - On clean checkout, tests skip silently                   │
│  - CI might pass with 0 tests run                           │
│  - Pre-run step can be forgotten                            │
│                                                             │
│  SOLUTIONS:                                                 │
│                                                             │
│  Option A: Gate ensures pre-run before tests                │
│     Phase gate runs tool THEN tests (documented in order)   │
│                                                             │
│  Option B: Test runs the tool itself (integration test)     │
│     test runs tool → checks output → cleans up              │
│                                                             │
│  Option C: Fixture generates required files                 │
│     @pytest.fixture creates file, test uses it              │
│                                                             │
│  REQUIRED: Document which option you're using and why       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 VERSION CHANGELOG GOVERNANCE

```
┌─────────────────────────────────────────────────────────────┐
│  SCHEMA/API CHANGES MUST UPDATE CHANGELOG                   │
│                                                             │
│  If your project has versioned schemas, models, or APIs:    │
│                                                             │
│  REQUIRED:                                                  │
│  ✅ CHANGELOG file exists (e.g., SCHEMA_CHANGELOG.md)       │
│  ✅ Every schema change adds changelog entry                │
│  ✅ Version numbers follow semantic versioning              │
│  ✅ CI can enforce: "if schema changed, changelog changed"  │
│                                                             │
│  CHANGELOG ENTRY FORMAT:                                    │
│  ## [version] - YYYY-MM-DD                                  │
│  ### Added / Changed / Deprecated / Removed / Fixed         │
│  - Description of change                                    │
│  - Migration notes if breaking                              │
│                                                             │
│  ENFORCEMENT (optional CI check):                           │
│  if git diff --name-only | grep "schema\|models"; then      │
│    git diff --name-only | grep "CHANGELOG" || exit 1        │
│  fi                                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 PACKAGE MANAGER CONSISTENCY

```
┌─────────────────────────────────────────────────────────────┐
│  IF YOU DECLARE A PACKAGE MANAGER, USE IT EVERYWHERE        │
│                                                             │
│  PROBLEM:                                                   │
│  Project says: "We use uv for package management"           │
│  But examples show: .venv/bin/python tools/script.py        │
│                                                             │
│  RESULT: Partial integration                                │
│  - Tool used for: setup (uv add, uv sync)                   │
│  - Tool NOT used for: running tests, tools, commands        │
│  - Developer workflow ignores the declared tool             │
│                                                             │
│  REQUIRED:                                                  │
│  ✅ If package manager declared, ALL commands use it:       │
│     uv run pytest                                           │
│     uv run python tools/script.py                           │
│     NOT: .venv/bin/python tools/script.py                   │
│                                                             │
│  ✅ "Never call X directly" rule documented:                │
│     "Never call .venv/bin/python directly.                  │
│      Always use uv run python ..."                          │
│                                                             │
│  ✅ Examples in docs match the declared tool                │
│                                                             │
│  FORBIDDEN:                                                 │
│  ❌ Tool for setup, raw paths for execution                 │
│  ❌ CI uses tool, local dev uses raw paths                  │
│  ❌ "We use X" but examples show direct venv access         │
└─────────────────────────────────────────────────────────────┘
```

### Package Manager Examples (Language-Agnostic)

| Language | Declared Tool | Wrong | Right |
|----------|---------------|-------|-------|
| Python (uv) | uv | `.venv/bin/python script.py` | `uv run python script.py` |
| Python (poetry) | poetry | `.venv/bin/pytest` | `poetry run pytest` |
| Node (npm) | npm | `node script.js` | `npm run script` |
| Node (pnpm) | pnpm | `./node_modules/.bin/cmd` | `pnpm exec cmd` |
| Ruby | bundler | `ruby script.rb` | `bundle exec ruby script.rb` |
| Rust | cargo | `./target/debug/tool` | `cargo run --bin tool` |

---

## 🔄 CI/LOCAL WORKFLOW IDENTITY

```
┌─────────────────────────────────────────────────────────────┐
│  LOCAL COMMANDS SHOULD MATCH CI COMMANDS EXACTLY            │
│                                                             │
│  PROBLEM:                                                   │
│  CI workflow:     uv run pytest tests/                      │
│  Local docs:      .venv/bin/python -m pytest tests/         │
│                                                             │
│  RESULT:                                                    │
│  - "Works on my machine" but fails in CI (or vice versa)    │
│  - Debugging CI requires translating commands               │
│  - Two mental models for same action                        │
│                                                             │
│  REQUIRED:                                                  │
│  ✅ Same command works locally AND in CI                    │
│  ✅ Documentation shows the CI-identical command            │
│  ✅ Phase gates use CI-identical commands                   │
│  ✅ Test snippets use CI-identical invocation               │
│                                                             │
│  PATTERN:                                                   │
│  CI:    uv run pytest tests/                                │
│  Local: uv run pytest tests/   # IDENTICAL                  │
│  Docs:  "Run tests: uv run pytest tests/"                   │
│  Gate:  uv run pytest tests/ && echo "PASS"                 │
│                                                             │
│  BENEFITS:                                                  │
│  - Copy-paste from CI to local (and vice versa)             │
│  - No translation needed when debugging                     │
│  - Single source of truth for "how to run X"                │
└─────────────────────────────────────────────────────────────┘
```

### CI/Local Alignment Checklist

Before finalizing task list:
```bash
# Extract all commands from CI workflow
grep -E "run:|uv |pytest|python" .github/workflows/*.yml

# Extract all commands from task list/docs  
grep -E "\.venv/|python |pytest" PROJECT_TASKS.md

# These should use the same invocation pattern
# If CI uses "uv run pytest", docs should NOT use ".venv/bin/pytest"
```

---

## 🔀 SKIP PATTERN CONSISTENCY

```
┌─────────────────────────────────────────────────────────────┐
│  IF YOU DEFINE A SKIP PATTERN, USE IT EVERYWHERE            │
│                                                             │
│  PROBLEM:                                                   │
│  Guidelines say:                                            │
│     "Skip gracefully if rg not installed"                   │
│     if not shutil.which("rg"):                              │
│         pytest.skip("ripgrep not installed")                │
│                                                             │
│  But actual test does:                                      │
│     result = subprocess.run(["rg", ...])                    │
│     assert result.returncode in (0, 1)  # Hard fails if 127!│
│                                                             │
│  RESULT: Half-committed. Either:                            │
│  - Tool is REQUIRED (hard fail, no skip pattern needed)     │
│  - Tool is OPTIONAL (skip pattern used consistently)        │
│                                                             │
│  REQUIRED: Make explicit decision and apply consistently:   │
│                                                             │
│  Option A: REQUIRED dependency                              │
│  - Document in Prerequisites                                │
│  - CI installs it                                           │
│  - Tests hard-fail if missing (no skip)                     │
│  - Remove any skip suggestions from guidelines              │
│                                                             │
│  Option B: OPTIONAL dependency                              │
│  - Document in Prerequisites with install instructions      │
│  - ALL tests that use it have skip guard                    │
│  - Guidelines and tests are consistent                      │
│                                                             │
│  FORBIDDEN:                                                 │
│  ❌ Skip pattern in guidelines, hard-fail in tests          │
│  ❌ Some tests skip, other tests hard-fail for same tool    │
│  ❌ "Should skip if missing" without actual skip code       │
└─────────────────────────────────────────────────────────────┘
```

### Required vs Optional Dependency Documentation

When documenting dependencies, be explicit:

```
## Prerequisites

### REQUIRED (CI and local must have)
- Python 3.10+
- uv package manager

### REQUIRED FOR CI, OPTIONAL LOCAL (tests skip if missing)
- ripgrep (rg): Tests skip locally, but CI must have it
  - Local: `brew install ripgrep` or tests will skip
  - CI: Pre-installed on GitHub runners

### FULLY OPTIONAL (tests skip if missing)
- graphviz: Only needed for diagram generation
```

**Anti-pattern**: Saying "REQUIRED" but tests skip when missing. This creates:
- False sense of enforcement locally
- Different behavior between CI and dev machines
- Confusion about actual contract

---

## 📄 CROSS-DOCUMENT SSOT

```
┌─────────────────────────────────────────────────────────────┐
│  WHEN SPEC AND TASK LIST COEXIST, PREVENT DRIFT             │
│                                                             │
│  COMMON SITUATION:                                          │
│  - SPEC.md: Design document with rich detail                │
│  - TASK_LIST.md: Executable plan with subset of spec        │
│                                                             │
│  RISK:                                                      │
│  - Spec describes tests X, Y, Z                             │
│  - Task list only implements X, Y (Z out of scope)          │
│  - Future reader of spec expects Z to exist                 │
│  - Soft double-SSOT: two documents, different "truth"       │
│                                                             │
│  REQUIRED:                                                  │
│                                                             │
│  ✅ Mark spec as HISTORICAL once task list exists:          │
│     "For active work, see TASK_LIST.md. This document       │
│      is design history only."                               │
│                                                             │
│  ✅ Or: Task list references spec with explicit scope:      │
│     "Implements sections 1-3 of SPEC.md. Sections 4-5       │
│      are OUT OF SCOPE for this refactor."                   │
│                                                             │
│  ✅ If spec is still active, sync changes both ways:        │
│     Task list change → update spec (or vice versa)          │
│                                                             │
│  FORBIDDEN:                                                 │
│  ❌ Two documents with overlapping scope, no cross-ref      │
│  ❌ Spec promises tests that task list doesn't implement    │
│  ❌ "The spec says X but we're doing Y" without updating    │
│     either document                                         │
└─────────────────────────────────────────────────────────────┘
```

### Cross-Document Reference Pattern

At top of task list:
```markdown
## Document Relationship

| Document | Status | Role |
|----------|--------|------|
| SPEC.md | HISTORICAL | Design rationale, not executable |
| TASK_LIST.md | ACTIVE | Executable plan, SSOT for this work |
| output_models.py | ACTIVE | SSOT for schema once created |

For discrepancies: TASK_LIST.md wins over SPEC.md.
After completion: output_models.py wins over both.
```

At top of spec (once task list exists):
```markdown
## ⚠️ HISTORICAL DOCUMENT

This document is design history. For active implementation:
- See: TASK_LIST.md (executable plan)
- See: output_models.py (schema SSOT once created)

Do NOT use this document as source of truth for current work.
```

---

## Prerequisites (Verify Before Starting)

**ALL must pass before Phase 0 begins:**

- [ ] **Environment ready**: [verification command]
- [ ] **Dependencies installed**: [verification command]
- [ ] **Tests run successfully**: [verification command]
- [ ] **No blocking issues**: [verification command]
- [ ] **Required tools available**: [list tools with `which` checks]

**Quick Check**:
```bash
# Single command to verify all prerequisites
[PREREQ_CHECK_COMMAND]

# Tool availability (customize per project/language)
# Python:  which python && which pytest || echo "Missing"
# Node:    which node && which npm || echo "Missing"
# Rust:    which cargo || echo "Missing"
# Go:      which go || echo "Missing"
```

---

# Phase 0: Setup & Infrastructure

**Goal**: Establish testing infrastructure and baseline
**Time Estimate**: [X-Y hours]
**Status**: ⏳ NOT STARTED

---

## Task 0.1: [Task Name]

**Objective**: [One sentence]
**Files**: `[file1]`, `[file2]`

### TDD Step 1: Write Test First

```
# Language-specific test file (examples below)
# Adapt syntax to your project's language/framework

# Python (pytest):
# tests/test_[name].py
def test_[feature]():
    """[What this test verifies]"""
    # Arrange / Act / Assert
    # Arrange
    [setup]
    
    # Act
    result = [function_call]
    
    # Assert - MUST be specific, not "it runs"
    assert result == [expected_specific_value]
    assert len(result.items) >= [minimum_expected]
    # Add assertions that would FAIL with stub implementation
```

```bash
# Verify test fails (RED)
[TEST_COMMAND]
# Expected: FAIL (test exists but implementation missing)
```

### ⛔ Test Strength Self-Check

Before proceeding to implementation:
- [ ] Would this test pass with empty/null return? → If yes, strengthen it
- [ ] Does test verify specific output content? → Must be yes
- [ ] Does test have minimum count/value assertions? → Must be yes

### TDD Step 2: Implement

```
# [file]
# Implementation in your language

function [name]():
    """[Docstring/documentation]"""
    [implementation]
```

### TDD Step 3: Verify (GREEN)

```bash
# Run the specific test
[TEST_COMMAND]
# Expected: PASS

# Run full suite (no regressions)
[FULL_TEST_COMMAND]
# Expected: N/N PASS
```

### ⛔ STOP: Clean Table Check

Before marking this task complete, verify:

- [ ] Test passes (not skipped)
- [ ] **Test is strong** (fails with stub implementation)
- [ ] Full test suite passes: `[FULL_TEST_COMMAND]` → N/N PASS
- [ ] No TODOs or placeholders in new code
- [ ] No new warnings introduced
- [ ] Code is documented
- [ ] **All files in "Files:" header exist**: `test -f [each_file]`

**Status**: ⏳ NOT STARTED

---

## Task 0.2: [Next Task]

[Same structure as Task 0.1]

---

## ⛔ STOP: Phase 0 Gate

**Before starting Phase 1, ALL must be true:**

```bash
# 1. All tests pass
[FULL_TEST_COMMAND]
# Expected: N/N PASS

# 2. No regressions
[REGRESSION_CHECK]
# Expected: 0 failures

# 3. Clean Table verified
grep -r "TODO\|FIXME\|XXX" src/
# Expected: No results (or only pre-existing)

# 4. File manifest verified
for f in [ALL_PHASE_0_FILES]; do test -f "$f" || echo "MISSING: $f"; done
# Expected: No output (all files exist)
```

### Phase 0 Completion Checklist

- [ ] All Task 0.x items have ✅ status
- [ ] Full test suite passes
- [ ] **All tests are strong** (not "it runs" tests)
- [ ] No new TODOs introduced
- [ ] Infrastructure documented
- [ ] **All listed files exist**
- [ ] Git checkpoint created

### Create Phase Unlock Artifact

```bash
# Only run this after ALL above criteria pass
# NOTE: Replace placeholders with ACTUAL values before running

PHASE_NUM=0
PHASE_NAME="Setup & Infrastructure"
# Get test count (adapt command to your test framework)
# Python/pytest: pytest --collect-only -q 2>/dev/null | tail -1 | grep -oP '\d+(?= test)'
# Node/jest:     npm test -- --listTests 2>/dev/null | wc -l
# Go:            go test -list '.*' ./... 2>/dev/null | wc -l
TESTS_PASSED=[YOUR_TEST_COUNT_COMMAND]
GIT_COMMIT=$(git rev-parse --short HEAD)
COMPLETION_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > .phase-${PHASE_NUM}.complete.json << EOF
{
  "schema_version": "1.0",
  "phase": ${PHASE_NUM},
  "phase_name": "${PHASE_NAME}",
  "tests_passed": ${TESTS_PASSED:-0},
  "tests_total": ${TESTS_PASSED:-0},
  "clean_table": true,
  "git_commit": "${GIT_COMMIT}",
  "completion_date": "${COMPLETION_DATE}"
}
EOF

# Verify no placeholders remain
grep -E "YYYY|placeholder|\[.*\]" .phase-${PHASE_NUM}.complete.json && \
    echo "❌ ERROR: Placeholders found in artifact" && exit 1

git add .phase-${PHASE_NUM}.complete.json
git commit -m "Phase ${PHASE_NUM} complete: ${PHASE_NAME}"
git tag phase-${PHASE_NUM}-complete
```

**Phase 0 Status**: ⏳ NOT STARTED

---

# Phase 1: [Phase Name]

**Goal**: [One sentence]
**Time Estimate**: [X-Y hours]
**Prerequisite**: `.phase-0.complete.json` must exist
**Status**: 📋 PLANNED

---

## ⛔ STOP: Verify Phase 0 Complete

```bash
# This MUST pass before starting Phase 1
test -f .phase-0.complete.json && echo "✅ Phase 0 complete" || echo "❌ BLOCKED"
```

---

## Task 1.1: [Task Name]

**Objective**: [One sentence]
**Files**: `[files]`

### TDD Step 1: Write Test First

[Test code with verification command]

**⛔ Test Strength Self-Check** (mandatory):
- [ ] Test fails with stub implementation
- [ ] Test verifies specific output values
- [ ] Test has boundary/count assertions

### TDD Step 2: Implement

[Implementation guidance]

### TDD Step 3: Verify

```bash
[TEST_COMMAND]
# Expected: PASS
```

### ⛔ STOP: Clean Table Check

- [ ] Test passes
- [ ] **Test is strong**
- [ ] Full suite passes
- [ ] No new debt
- [ ] **All "Files:" exist**

**Status**: 📋 PLANNED

---

## Task 1.2: [Next Task]

[Same structure]

---

## ⛔ STOP: Phase 1 Gate

[Same structure as Phase 0 Gate, including file manifest verification]

---

# Appendix A: Rollback Procedures

## A.1: Single Test Failure

```bash
# 1. Identify failing test
[TEST_COMMAND] 2>&1 | head -50

# 2. If fixable in <15 min, fix it
# 3. If not fixable, revert last change
git diff HEAD~1 --stat
git checkout HEAD~1 -- [affected_file]

# 4. Verify tests pass again
[FULL_TEST_COMMAND]
```

## A.2: Multiple Test Failures (Full Revert)

```bash
# 1. Identify last known good state
git log --oneline -10

# 2. Hard reset to good commit
git reset --hard [GOOD_COMMIT]

# 3. Verify
[FULL_TEST_COMMAND]

# 4. Document what went wrong
echo "[DATE]: Reverted due to [REASON]" >> ISSUES.md
```

## A.3: Phase Gate Failure

```bash
# DO NOT proceed to next phase
# 1. Identify which criterion failed
# 2. Fix the specific issue
# 3. Re-run phase gate verification
# 4. Only proceed when ALL criteria pass
```

## A.4: Weak Test Discovered

```bash
# If a test is discovered to be an "it runs" test:
# 1. DO NOT proceed with current task
# 2. Strengthen the test first
# 3. Verify strengthened test fails with stub
# 4. Only then continue implementation
```

---

# Appendix B: AI Assistant Instructions

## Drift Prevention Rules

1. **Before each response**, re-read the current task's objective
2. **After completing code**, immediately run verification commands
3. **If test fails**, fix it before moving on (no "we'll fix it later")
4. **If blocked**, document why and suggest rollback
5. **Never skip** Clean Table checks
6. **Never write** "it runs" tests (see Test Strength Rules)
7. **Never list** files that won't be created
8. **Never test** features that don't exist yet
9. **Never assume** code matches design docs—verify first
10. **Never tighten** constraints until loose version passes

## Authority Resolution

When design doc says X but code does Y:
1. **Verify** code behavior is intentional (not a bug)
2. **If intentional** → Update design doc and task list to match code
3. **If bug** → Fix code, but through proper TDD cycle
4. **Never** rename/restructure working code just to match docs

## Verification Frequency

| Action | Verify Immediately |
|--------|-------------------|
| Create new file | File exists, syntax valid |
| Modify function | Related tests pass |
| Write test | **Test fails with stub** |
| Reference symbol from spec | **Symbol exists in code** |
| Complete task | Full test suite + file manifest |
| Complete phase | Phase gate checklist |
| Tighten constraints | **Loose version passes first** |

## When to Stop and Escalate

- Test suite drops below 100% pass rate
- Performance degrades beyond threshold
- Clean Table criteria cannot be satisfied
- Phase gate blocked for >2 attempts
- **Test discovered to be "it runs" pattern**
- **File listed but not created**
- **Spec and code disagree on symbol names**
- **Tightening constraints breaks previously passing tests**
- **Feature referenced in spec doesn't exist in code**

## Prohibited Actions

- ❌ Starting Phase N+1 without Phase N artifact
- ❌ Marking task complete with failing tests
- ❌ Leaving TODOs in "completed" code
- ❌ Skipping Clean Table verification
- ❌ Proceeding after rollback without re-verification
- ❌ **Writing tests that only check exit code**
- ❌ **Writing tests that pass with stub implementation**
- ❌ **Listing files in "Files:" that aren't created**
- ❌ **Leaving literal placeholders in artifacts**
- ❌ **Using hard-coded interpreter paths** (use runtime self-reference)
- ❌ **Testing features marked "reserved" or "planned"**
- ❌ **Assuming symbol names without grep verification**
- ❌ **Changing working code to match design docs**
- ❌ **Tightening constraints before loose version passes**
- ❌ **Defining models without discovery phase**
- ❌ **Treating "final state" diagrams as implementation specs**

**YAGNI Violations (Code Quality)**:
- ❌ **Adding features without current requirement** (YAGNI Q1)
- ❌ **Building for hypothetical future consumers** (YAGNI Q2)
- ❌ **Speculative flags, hooks, or parameters** (unused API surface)
- ❌ **Premature abstractions** (interface with only 1 implementation)
- ❌ **"Might need later" code** (if addable later, defer)
- ❌ **Generalizations without ≥2 real consumers today**
- ❌ **Complex solution when simpler one works** (KISS violation)

**Silent Error Violations**:
- ❌ **Swallowed exceptions** (catch and continue without raise)
- ❌ **Conditional error handling** (if strict: raise)
- ❌ **Strict mode parameters** (strict: bool = True)
- ❌ **Environment variables for strictness** (STRICT_MODE env var)
- ❌ **Warning instead of error** (print warning and continue)
- ❌ **Error collection without raise** (errors.append() then continue)

**Hidden Debt Violations**:
- ❌ **"Temporary" fixes** that mask root causes
- ❌ **"Adjust later" comments** without immediate resolution
- ❌ **"You may need to" speculative comments**
- ❌ **Workaround logic** instead of proper fix
- ❌ **Deferred follow-ups** in completed code

**Reflection Violations**:
- ❌ **Skipping reflection** before task completion
- ❌ **Proceeding with uncertainty** (confidence < 80%)
- ❌ **Unstated assumptions** (assuming without documenting)
- ❌ **Guessing when ambiguous** (should STOP and clarify)
- ❌ **Mixing thinking and execution** (must separate reasoning from action)
- ❌ **Claims without evidence anchors** (no source:line + quote)
- ❌ **Assumptions treated as facts** (must distinguish semantic types)
- ❌ **Undocumented decisions** (must have decision chain)
- ❌ **Missing trace links** (decision → evidence → impact)
- ❌ **Unverified assumptions proceeding** (must verify or flag as risk)

**Governance Violations**:
- ❌ **Duplicate task IDs** (same ID for different tasks)
- ❌ **Untracked tasks in Appendix** (all IDs must appear in file tracking)
- ❌ **Selective Clean Table checks** (must be global, entire repo)
- ❌ **Aspirational helpers not used** (defined pattern ignored in examples)
- ❌ **Existence-only tests** (must check content correctness, not just presence)
- ❌ **Unhandled pre-run dependencies** (tests that skip without explicit strategy)
- ❌ **Missing scope decisions** (must declare what's in/out of scope)
- ❌ **Exit code tolerance** (`returncode in (0, 1)` accepts both success and failure)
- ❌ **Plausible output tests** (`"exported" in stdout` doesn't verify behavior)
- ❌ **Heredoc placeholders** (literal `YYYY-MM-DD` committed to artifacts)
- ❌ **Inconsistent skip patterns** (guidelines say skip, tests hard-fail)
- ❌ **CI string-only tests** (checking YAML contains string, not correct wiring)
- ❌ **Schema changes without changelog** (versioned artifacts need history)
- ❌ **No-op stub tools** (tool passes tests but never processes real data)
- ❌ **Phase gate scope mismatch** (global rules enforced locally in early phases)
- ❌ **Temporal debt window** (create placeholder → edit → forget to re-test)
- ❌ **Undocumented weak tests** (intentionally limited tests without TRADE-OFF comment)
- ❌ **Cross-document drift** (spec and task list overlap without cross-reference)
- ❌ **"Required" but skips** (dependency called REQUIRED but tests skip when missing)
- ❌ **Package manager partial use** ("We use X" but examples show direct venv access)
- ❌ **CI/Local command mismatch** (CI uses tool runner, local uses raw paths)

## Discovery-First Checklist

Before defining models/schemas/types for existing code:

- [ ] Ran existing code with ≥10 representative inputs
- [ ] Captured actual outputs to sample_outputs/
- [ ] Extracted all unique keys/fields
- [ ] Derived model structure from actual outputs
- [ ] Validated model against captured outputs
- [ ] Only then: wrote tests asserting specific structures

## Strictness Transition Checklist

Before tightening any constraint (validation, types, checks):

- [ ] Loose/permissive version implemented
- [ ] Loose version passes on ≥N real-world inputs
- [ ] Tightened constraint applied
- [ ] Same inputs still pass (if not → fix model, not inputs)
- [ ] No fake data synthesized to satisfy strict checks

## YAGNI Checklist (Before Adding ANY New Code)

For every new function, class, parameter, or abstraction:

- [ ] **Q1**: Current requirement exists (ticket/issue ID)?
- [ ] **Q2**: Will be used immediately by known consumer?
- [ ] **Q3**: Backed by stakeholder request or data (not speculation)?
- [ ] **Q4**: Cannot be added later without massive rework?
- [ ] **KISS**: Simpler alternative considered and rejected?
- [ ] **SRP**: Single clear purpose for this code?
- [ ] No unused parameters, hooks, or flags added?
- [ ] Generalizations have ≥2 real consumers today?

**If any Q1-Q3 is NO → Do not implement**
**If Q4 is YES → Defer until actually needed**

---

# Appendix C: File Change Tracking

Track all file changes for audit trail:

| Phase.Task | File | Action | Verified |
|------------|------|--------|----------|
| 0.1 | `src/module.[ext]` | CREATE | ⏳ |
| 0.1 | `tests/test_module.[ext]` | CREATE | ⏳ |
| 1.1 | `src/module.[ext]` | UPDATE | 📋 |

**File Manifest Audit**:
```bash
# After each phase, verify all tracked files exist
cat << 'EOF' | while read line; do
    file=$(echo "$line" | awk '{print $3}')
    test -f "$file" && echo "✅ $file" || echo "❌ $file"
done
[PASTE_TABLE_HERE]
EOF
```

---

# Appendix D: Progress Log

## Session Log

```
[YYYY-MM-DD HH:MM] Started Phase 0
[YYYY-MM-DD HH:MM] Task 0.1 complete - tests: 5/5 PASS (strong tests verified)
[YYYY-MM-DD HH:MM] Task 0.2 complete - tests: 8/8 PASS
[YYYY-MM-DD HH:MM] Phase 0 Gate: ✅ ALL PASS
[YYYY-MM-DD HH:MM] File manifest: ✅ ALL FILES EXIST
[YYYY-MM-DD HH:MM] Created .phase-0.complete.json (no placeholders)
```

## Time Tracking

| Phase | Task | Estimated | Actual | Notes |
|-------|------|-----------|--------|-------|
| 0 | 0.1 | 1h | - | - |
| 0 | 0.2 | 2h | - | - |

---

# Appendix E: Test Strength Audit

Run this audit after writing tests to catch weak patterns:

```bash
# Find potential "it runs" tests (adapt patterns to your language)
# Look for exit code checks without content verification
grep -rn "exitCode == 0\|returncode == 0\|exit_code == 0" tests/
grep -rn "exitCode in\|returncode in" tests/

# Find assertions that only check presence, not content
grep -rn "assert.*exists\|expect.*exist\|toBeDefined" tests/

# Find empty or near-empty test functions
# Python:
grep -l "def test_" tests/ | xargs grep -A10 "def test_" | grep -B5 "^$"
# JavaScript:
grep -l "it(" tests/ | xargs grep -A10 "it(" | grep -B5 "^$"

# Manual review checklist:
# - Does each test have specific value assertions?
# - Would a stub implementation pass this test?
# - Are both success and failure paths tested?
```

If any weak patterns found, strengthen before proceeding.

---

# Template Customization Checklist

Before using this template, replace:

- [ ] `[PROJECT_NAME]` → Your project name
- [ ] `[FAST_TEST_COMMAND]` → Quick test command for your language/framework
  - Python: `pytest tests/ -x -q`
  - Node: `npm test -- --bail`
  - Rust: `cargo test --quiet`
  - Go: `go test ./... -short`
- [ ] `[FULL_TEST_COMMAND]` → Complete test suite command
  - Python: `pytest tests/ -v`
  - Node: `npm test`
  - Rust: `cargo test`
  - Go: `go test ./... -v`
- [ ] `[PERF_TEST_COMMAND]` → Performance/benchmark command (if applicable)
- [ ] `[TEST_COMMAND]` → Single test file/case command
- [ ] Phase names and task breakdowns
- [ ] Success criteria for your project
- [ ] **All "Files:" headers with actual files**
- [ ] **Tool dependencies in Prerequisites**
- [ ] **Language-specific syntax in examples** (adapt to your stack)

**Final verification**: `grep -E "\[.*\]" PROJECT_TASKS.md` should return only intentional placeholders.

---

**End of Template**
