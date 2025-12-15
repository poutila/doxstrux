## 🧰 Environment & Dependencies — uv (Project Rule)

This project uses **uv** for all Python environment management, dependency resolution, and command execution.

> **Hard rule:**  
> - Never call `.venv/bin/python` (or any direct virtualenv Python path) in committed scripts, tests, or docs.  
> - **Never use `uv pip install` or any `uv pip` commands.** These bypass `pyproject.toml` and create drift.  
> - Always use `uv` commands: `uv sync`, `uv run`, `uv add`, `uv lock`.  
> Any direct venv Python usage or `uv pip` usage is **drift** and must be removed.

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

### 1.5 Project Layout (src/ layout)

This project follows the **src layout** for Python packages.

**Required structure:**
```
.
├── pyproject.toml
├── uv.lock
├── src/
│   └── package_name/
│       ├── __init__.py
│       └── modules...
├── tests/
└── tools/
```

**Why src/ layout:**
- **Import isolation:** Prevents accidental imports from the working directory during development
- **Proper testing:** Forces tests to run against the installed package, not loose files
- **Editable install clarity:** Makes `uv sync` behavior explicit and correct
- **Standard convention:** Recommended by PyPA and modern Python packaging guides

**❌ Forbidden (flat layout):**
```
.
├── pyproject.toml
├── package_name/          # Wrong: package at root
│   ├── __init__.py
│   └── module.py
```

**Configuration in pyproject.toml:**

Adjust the build backend configuration to find packages under `src/`:

```toml
# For setuptools:
[tool.setuptools.packages.find]
where = ["src"]

# For hatchling:
[tool.hatch.build.targets.wheel]
packages = ["src/package_name"]

# For poetry (if used):
[tool.poetry]
packages = [{include = "package_name", from = "src"}]
```

**Directory purposes:**
- `src/package_name/`: The package code itself
- `tests/`: All test code, mirroring `src/` structure if helpful
- `tools/`: Project-specific scripts, generators, validators, etc.

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

# Run project tools (direct script execution)
uv run tools/generate_report.py
uv run tools/check_style.py
uv run tools/validate_quality.py --strict

# Run a module instead of a script
uv run python -m your_package.main

# Run interactive Python
uv run python
```

**Pattern:**
- **Direct scripts:** `uv run script.py`
- **Module execution:** `uv run python -m module.name`
- **Installed commands:** `uv run pytest`, `uv run mypy`, etc.

Even inside an activated virtualenv, prefer:

```bash
uv run pytest
uv run tools/...
```

over direct `python` calls. `uv run` guarantees the correct interpreter, environment, and dependency set.

---

### 4. Dependency Organization

Python projects organize dependencies using two distinct mechanisms.

#### 4.1 Optional Dependencies (Extras)

Use `[project.optional-dependencies]` for features that end users might install optionally.

**When to use:**
- Your package will be published to PyPI
- End users need optional features: `pip install mypackage[viz]`
- Libraries that others will consume

**Install commands:**
```bash
uv sync --extra viz                    # Single extra
uv sync --extra viz --extra metrics    # Multiple extras
uv sync --all-extras                   # All extras
```

**Example:**
```toml
[project.optional-dependencies]
viz = ["plotly>=6.3.0", "shiny>=1.4.0"]
metrics = ["prometheus-client>=0.23.1"]
```

#### 4.2 Dependency Groups

Use `[dependency-groups]` for development-only tools that are not published.

**When to use:**
- Development tools (linting, testing, type checking)
- Internal tooling
- Application projects (not libraries)

**Install commands:**
```bash
uv sync --group dev                    # Single group
uv sync --group dev --group test       # Multiple groups
```

**Example:**
```toml
[dependency-groups]
dev = ["pytest>=8.0.0", "mypy>=1.17.0", "ruff>=0.12.0"]
test = ["pytest-playwright>=0.7.0", "httpx>=0.28.0"]
```

#### 4.3 Application vs Library Structure

**For applications (not published to PyPI):**
- Put all runtime dependencies in `[project.dependencies]`
- Use `[dependency-groups]` for dev/test tools only
- Don't create extras unless you have genuinely optional features

**For libraries (published to PyPI):**
- Keep `[project.dependencies]` minimal (core only)
- Use `[project.optional-dependencies]` for optional features users might want
- Use `[dependency-groups]` for development tools

---

### 5. Adding and Updating Dependencies

Use `uv add` and `uv lock` for all dependency changes.

**✓ CORRECT patterns:**
```bash
# Add a core dependency
uv add package-name

# Add with version constraint
uv add "pydantic>=2,<3"

# Add to an optional extra
uv add --optional viz plotly

# Add to a dependency group
uv add --group dev pytest mypy

# Refresh all locked dependencies and re-sync
uv lock --refresh
uv sync
```

**❌ FORBIDDEN patterns:**
```bash
# These bypass pyproject.toml and create drift
uv pip install pandas
uv pip install -r requirements.txt
pip install pandas

# These are also wrong
.venv/bin/python -m pip install pandas
.venv/bin/pip install pandas
```

Guidelines:

- Do **not** edit `uv.lock` manually; let `uv` manage it.
- After any change to dependencies, commit both `pyproject.toml` and `uv.lock` together to keep environment reproducible.
- Never use `uv pip` commands; they break the SSOT contract.

---

### 6. Common Mistakes to Avoid

#### 6.1 Self-referential dependencies

**❌ WRONG:**
```toml
[dependency-groups]
dev = [
  "my-package-name",  # Don't reference your own package!
  "pytest>=8.0.0",
]
```

**✓ CORRECT:**
```toml
[dependency-groups]
dev = ["pytest>=8.0.0"]  # uv sync installs your package automatically
```

#### 6.2 Unnecessary workspace configuration

**❌ WRONG (single package):**
```toml
[tool.uv.workspace]
members = ["."]  # Don't use workspace for single packages
```

**✓ CORRECT (single package) — remove workspace entirely, or:**
```toml
[tool.uv.sources]
my-package-name = { path = ".", editable = true }
```

**Note:** `[tool.uv.workspace]` is only needed for monorepos with multiple packages in subdirectories. Most projects are single packages and should NOT use workspace.

#### 6.3 Wrong install command for dependency type

**Problem:** Using `--extra` for groups or `--group` for extras

**Solution:** Match the command to the configuration:
- `[project.optional-dependencies]` → `uv sync --extra NAME`
- `[dependency-groups]` → `uv sync --group NAME`

---

### 7. Optional: Manual Activation (Rarely Needed)

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
uv run tools/...
```

Direct `python` invocations are allowed only for **truly local, throwaway experiments** — never in committed scripts, tests, or docs.

---

### 8. CI Alignment

CI must follow the same rules as local development:

1. Install uv (e.g. via `astral-sh/setup-uv` or equivalent).
2. Run `uv sync` to create/update `.venv` and install dependencies.
3. Run all checks via `uv run`.

Example (GitHub Actions):

```yaml
- uses: astral-sh/setup-uv@v4

- name: Sync dependencies
  run: uv sync --all-extras --group dev --group test

- name: Run tests and tools
  run: |
    uv run pytest
    uv run mypy src/
    uv run tools/validate_quality.py --strict
```

Any CI step that uses `.venv/bin/python` directly or `uv pip install` is considered **drift** and must be refactored to `uv run` and `uv add`.

---

### 9. Summary

- **uv** is the single entry point for Python in this project.
- `pyproject.toml` + `uv.lock` are the single sources of truth for dependencies.
- **src/ layout** is required; package code lives under `src/package_name/`.
- `.venv/` is managed only by `uv`; no manual activation is required for normal workflows.
- Never use `uv pip install` or any `uv pip` commands; they bypass `pyproject.toml`.
- Use `[project.optional-dependencies]` for user-facing features; use `[dependency-groups]` for dev tools.
- All tests, tools, and CI jobs run via `uv run`, ensuring consistent, reproducible environments everywhere.
