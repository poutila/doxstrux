## 🧰 Environment & Dependencies — uv (Project Rule)

This project uses **uv** for all Python environment management, dependency resolution, and command execution.

> **Hard rule:** Never call `.venv/bin/python` (or any direct virtualenv Python path) in committed scripts, tests, or docs.  
> Always use `uv` (`uv sync`, `uv run`, `uv add`, `uv lock`). Any direct venv Python usage is **drift** and must be removed.

---

### 1. Prerequisites & Single Source of Truth

- **Python version:**  
  Use the version declared in `pyproject.toml` (and enforced by `uv`).

- **Dependencies SSOT:**  
  - Declared dependencies: `pyproject.toml`  
  - Locked dependencies: `uv.lock`

- **Environment:**  
  - `.venv/` is created and managed **only** by `uv`.  
  - Do **not** edit `.venv/` by hand or create parallel virtualenvs for this project.

Before running project commands, you must have **uv** installed (see official uv installation docs).  
If `uv` is not found, install it first.

---

### 2. Initial Setup

On a fresh clone or after dependency changes:

```bash
# Create or update the virtual environment and install all dependencies
uv sync
```

Notes:

- `uv sync` will create `.venv/` if it does not exist and install the exact versions from `uv.lock` (or resolve and lock if no lock exists yet).
- You do **not** need to activate the virtual environment manually when using `uv run`.

Optional explicit venv creation (seldom needed):

```bash
uv venv        # optional: explicitly create .venv
uv sync        # install / update dependencies
```

---

### 3. Running Commands (Always via `uv run`)

All project commands are run via `uv run`. This applies to tests, tools, and ad-hoc scripts.

Examples (adapt paths/names to your project):

```bash
# Run the full test suite
uv run pytest

# Run a single test file
uv run pytest tests/test_example.py

# Run project tools
uv run python tools/generate_report.py
uv run python tools/check_style.py
uv run python tools/validate_fixtures.py --report --threshold 100

# Run a module instead of a script
uv run python -m your_package.main
```

Even inside an activated virtualenv, prefer:

```bash
uv run pytest
uv run python tools/...
```

over direct `python` calls. `uv run` guarantees the correct interpreter, environment, and dependency set.

---

### 4. Adding and Updating Dependencies

Use `uv add` and `uv lock` for all dependency changes.

```bash
# Add a new dependency
uv add package-name

# Example: add Pydantic v2
uv add "pydantic>=2,<3"

# Refresh all locked dependencies and re-sync the environment
uv lock --refresh
uv sync
```

Guidelines:

- Do **not** edit `uv.lock` manually; let `uv` manage it.
- After any change to dependencies, commit both `pyproject.toml` and `uv.lock` together to keep environment reproducible.

---

### 5. Optional: Manual Activation (Rarely Needed)

You usually do **not** need to activate the venv when using `uv run`.  
If you still want an activated shell for interactive work:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

Even in an activated shell, the canonical pattern remains:

```bash
uv run pytest
uv run python tools/...
```

Direct `python` invocations are allowed only for **truly local, throwaway experiments** — never in committed scripts, tests, or docs.

---

### 6. CI Alignment

CI must follow the same rules as local development:

1. Install uv (e.g. via `astral-sh/setup-uv` or equivalent).
2. Run `uv sync` to create/update `.venv` and install dependencies.
3. Run all checks via `uv run`.

Example (GitHub Actions):

```yaml
- uses: astral-sh/setup-uv@v4

- name: Sync dependencies
  run: uv sync

- name: Run tests and validators
  run: |
    uv run pytest
    uv run python tools/validate_fixtures.py --threshold 100
```

Any CI step that uses `.venv/bin/python` directly is considered **drift** and must be refactored to `uv run`.

---

### 7. Summary

- **uv** is the single entry point for Python in this project.
- `pyproject.toml` + `uv.lock` are the single sources of truth for dependencies.
- `.venv/` is managed only by `uv`; no manual activation is required for normal workflows.
- All tests, tools, and CI jobs run via `uv run`, ensuring consistent, reproducible environments everywhere.
