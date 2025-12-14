## 🧪 Testing Governance — No Weak Tests (Project Rule)

This project enforces a **No Weak Tests** rule: tests must assert meaningful, domain-relevant behavior — not just that “the code runs without crashing”.

> **Hard rule:** Any test that only checks imports, exit code 0, or “no exception raised” without asserting behavior is considered **weak** and must be refactored or removed.

---

### 1. Purpose

Weak tests give a false sense of safety. They often:

- Only import a module or call a function once.
- Only assert that a command exits with code 0.
- Only check that output is “non-empty” without verifying semantics.
- Only check that “no exception was raised” without caring about what the code actually did.

This governance rule requires that:

- Tests encode **contracts** and **invariants**, not just smoke checks.
- If tests pass, maintainers can say “the important behavior works as specified”, not “it didn’t crash this time”.

---

### 2. What Counts as a Weak Test?

A test is **weak** if it primarily asserts:

- “Can import module” (no behavioral assertions).
- “Tool exits with 0” without checking outputs or side-effects.
- “Output length > 0” or “file exists” without verifying content.
- “No exception thrown” while ignoring what the function returned or changed.

Examples of weak tests:

```python
def test_tool_runs():
    # ❌ Weak: only checks that the tool does not crash
    result = subprocess.run(["my_tool", "--help"])
    assert result.returncode == 0
```

```python
def test_function_does_not_crash():
    # ❌ Weak: ignores outputs and side effects
    do_something_complex()
```

These must be refactored into behavior-asserting tests.

---

### 3. Strong Tests — Expectations by Category

#### 3.1 Library / Pure Functions

For pure or mostly pure functions:

- Assert **exact outputs** given known inputs.
- Assert error cases: invalid input → specific exception or error result.
- Assert invariants (e.g., sorted output, idempotence, monotonic properties).

Example:

```python
def test_normalize_usernames_trims_and_lowercases():
    users = [" Alice ", "BOB", "charlie "]
    result = normalize_usernames(users)
    assert result == ["alice", "bob", "charlie"]
```

#### 3.2 CLI Tools and Scripts

For command-line tools:

- Assert exit code **and** stdout/stderr content or generated artifacts.
- Use fixtures as input (files or directories) and assert expected transformations.

Example:

```python
def test_report_tool_emits_expected_json(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "data.txt").write_text("example")

    result = subprocess.run(
        ["my_tool", "build-report", str(input_dir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["files_processed"] == 1
    assert report["errors"] == []
```

#### 3.3 Linters, Validators, and Checkers

For linters / validators:

- Use fixtures that **deliberately violate** specific rules.
- Assert that the expected rule IDs, messages, and exit codes are emitted.
- Ensure that “clean” fixtures produce no errors/warnings.

Example:

```python
def test_linter_flags_todo_comment(tmp_path):
    src = tmp_path / "example.py"
    src.write_text("# TODO: remove
x = 1
")

    result = subprocess.run(
        ["my_linter", str(src)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "LINT001" in result.stdout  # example rule ID
    assert "TODO comment not allowed" in result.stdout
```

#### 3.4 Orchestrators / Pipelines

For orchestration code (pipelines, task runners, generators):

- Use small, controlled configurations (fixtures).
- Assert which outputs are created, in which locations.
- Assert behavior on failure: partial outputs, error logs, or rollback semantics.

Example:

```python
def test_pipeline_generates_expected_files(tmp_path):
    cfg = {"input_dir": str(tmp_path), "output_dir": str(tmp_path / "out")}
    (tmp_path / "input.md").write_text("# Title\n\nBody")

    result = run_pipeline(cfg)

    assert result.success is True
    output_dir = tmp_path / "out"
    assert (output_dir / "index.html").exists()
    html = (output_dir / "index.html").read_text()
    assert "<h1>Title</h1>" in html
```

---

### 4. Governance Checklist for Refactoring Weak Tests

To apply this rule in any project:

1. **Identify Weak Tests**
   - Search for tests named `test_*runs`, `test_*imports`, or tests that only use `subprocess.run` with `returncode == 0`.
   - Look for tests with no assertions or only `assert result is not None` / `assert True`.

2. **Attach Tests to Contracts**
   - For each module, CLI, linter, or pipeline, define the **expected behavior** (input → output, or error conditions).
   - Write tests that assert **those contracts**, not just execution.

3. **Use Fixtures Aggressively**
   - Create small, representative input fixtures (files, configs, JSON, etc.).
   - For each significant branch / rule / error path, create at least one fixture that hits it.

4. **Map Rules/IDs to Tests**
   - For systems that emit rule IDs, error codes, or status flags:
     - Maintain a list of all IDs / codes.
     - Ensure at least one test exercises each code and asserts its presence.

5. **Coverage Gate (Optional but Recommended)**
   - Enforce a coverage threshold (e.g. via `pytest --cov`).
   - Use it only after tests assert real behavior; do **not** inflate coverage with more weak tests.

---

### 5. Summary

- Weak tests (import-only, crash-only, length-only, “no exception” only) are **not allowed** as final tests.
- Every significant behavior (success and failure) must have at least one test that asserts **what** happens, not just **that** something happened.
- Linters, CLI tools, and orchestrators must be tested with realistic fixtures and **expected outputs** (codes, messages, artifacts).
- If tests pass, the team should be comfortable saying:  
  **“The system’s critical contracts hold,” not merely “it didn’t crash.”**
