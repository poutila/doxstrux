## 🧪 TDD & Change Governance — Tests Drive Behavior (Project Rule)

This project treats tests as the primary executable description of behavior. New code, behavior changes, and bug fixes must be driven by tests, not added in isolation.

> **Hard rule:**  
> - No new behavior without corresponding tests.  
> - Every bug fix must start with a failing test that reproduces the bug.  
> - Refactors must keep the test suite green (no behavior changes without explicit tests).

---

### 1. Goals

- **Safety:** Prevent untested behavior from entering the codebase.
- **Clarity:** Make expected behavior visible and executable in tests.
- **Refactorability:** Allow internal changes as long as tests (contracts) keep passing.
- **Regression resistance:** Every bug fixed once, tested forever.

This rule complements other governance rules:

- **Clean Table Principle:** No half-finished or silently failing behavior is shipped.
- **No Weak Tests:** Tests must assert meaningful behavior, not just that “it runs”.

---

### 2. TDD-Inspired Workflow (Pragmatic Version)

We follow a lightweight, pragmatic form of Test-Driven Development:

1. **Red** — Start from a missing or failing test
   - For new features: write a test that describes the desired behavior and currently fails.
   - For bugs: write a regression test that reproduces the bug and currently fails.

2. **Green** — Implement or adjust code
   - Only write enough code to make the failing test(s) pass.
   - Do not add speculative behavior that is not covered by tests.

3. **Refactor** — Clean up while staying green
   - Improve structure, naming, and internal design.
   - Keep all tests passing; no behavior change without updated tests.

This loop is applied at the scale of small, incremental changes, not entire epics.

---

### 3. Rules for New Features

For any new feature or behavior change:

- **Requirement:** At least one new or updated test must demonstrate the new behavior.
- The test must **fail** before the feature implementation and **pass** after.
- The test must be **strong**, following the No Weak Tests rule:
  - It must assert actual outputs, side-effects, or state changes.
  - It must not only check “no exception raised” or “non-empty output”.

Example pattern:

```python
def test_new_discount_is_applied_for_vip_customers():
    basket = Basket(total=100, customer_tier="vip")

    # RED: initially fails
    total_after_discount = apply_discounts(basket)

    assert total_after_discount == 90  # 10% VIP discount
```

Then implement `apply_discounts()` to make this pass.

---

### 4. Rules for Bug Fixes

Every bug fix must be anchored by a regression test.

- Before changing the implementation, add a test that reproduces the bug.
- Confirm that the test **fails** against the current code.
- Apply the fix.
- Confirm that:
  - The new test passes.
  - Existing tests continue to pass.

Example pattern:

```python
def test_parsing_handles_trailing_comma_bug():
    # This input previously crashed or returned wrong result
    data = "a,b,c,"

    result = parse_csv_line(data)

    # Expected behavior after fix
    assert result == ["a", "b", "c", ""]
```

This ensures the bug cannot silently reappear.

---

### 5. Rules for Refactoring

Refactors change **structure**, not **observable behavior**.

- You may freely reorganize internals (functions, classes, modules) as long as all tests stay green.
- If behavior changes, you must update tests to reflect the new intended behavior.

Constraints:

- Do not “fix” tests to match broken behavior; tests describe the intended behavior.
- If behavior needs to change, make that explicit:
  - Update or add tests first.
  - Then adjust the implementation.

Example workflow:

1. Run tests → all green.
2. Refactor internals (e.g., extract helper functions, rename modules).
3. Run tests again → must still be green.
4. Only if behavior requirements change, add/update tests and then adjust code.

---

### 6. Enforcement & CI Expectations

To enforce this rule in practice:

- **Code review:**  
  - Reject changes that introduce new behavior without new or updated tests.
  - Reject bug fixes without a new regression test covering the bug.

- **CI / automation (optional but recommended):**
  - Require tests to be present for new modules or public APIs:
    - e.g., enforce minimum coverage thresholds on new/changed files.
  - Integrate static checks for “No Weak Tests” patterns (e.g., tests with no assertions).

The combination of:

- `pytest` (or another test runner),
- a coverage tool (e.g., `coverage.py`, `pytest-cov`),
- and governance rules (Clean Table, No Weak Tests)

gives teeth to this TDD governance rule.

---

### 7. Summary

- Tests are not an afterthought; they **drive** changes.
- New features and bug fixes always come with tests that would fail before the change.
- Refactors keep all tests passing; behavior changes must be reflected in tests.
- When the test suite is green:
  - You should be able to say: **“This is what the system is supposed to do, and it is doing it.”**
