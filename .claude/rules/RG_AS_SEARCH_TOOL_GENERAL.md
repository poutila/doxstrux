## 🧰 Text Search & Clean Table — ripgrep (`rg`) (Project Rule)

This project uses **ripgrep** (`rg`) as the standard tool for all automated text searches used in project governance (Clean Table checks, legacy audits, drift detection, etc.).

> **Hard rule:** Never use `grep`, `egrep`, `ack`, or other ad-hoc search tools in committed scripts, tests, or CI for project governance.  
> Always use **ripgrep** (`rg`). Any use of other search tools for governance automation is **drift** and should be removed.

---

### 1. Prerequisites & Single Source of Truth

- **Search engine SSOT:**  
  - All automated text searches used for project governance (Clean Table, legacy field audits, schema drift checks) are defined in terms of `rg` invocations.
  - If a script or test needs to search the repository as part of governance, it MUST use `rg`.

- **Installation prerequisite:**  
  Before running project scripts or tests that rely on these checks, you must have **ripgrep** installed.  
  If `rg` is not found, install it first (e.g., via your OS package manager).

Typical installation commands:

```bash
# Debian / Ubuntu
sudo apt-get install ripgrep

# macOS (Homebrew)
brew install ripgrep

# Arch
sudo pacman -S ripgrep

# Windows (Chocolatey)
choco install ripgrep
```

---

### 2. Canonical Usage Pattern

All governance-related repo searches MUST follow the `rg` pattern.

Examples (adjust paths to your project):

```bash
# 1. Clean Table: forbid TODO/FIXME/XXX in production code
rg "TODO|FIXME|XXX" src/

# 2. Legacy field audit: find usages of deprecated identifiers
rg "legacy_field_name" src/ tools/ tests/

# 3. Schema drift check: ensure no direct access to removed fields
rg "removed_field_name" src/package_name/core_module.py
```

Guidelines:

- Always scope `rg` searches to **clear directories** (`src/`, `tools/`, `tests/`, etc.), not the entire repo root by default.
- Prefer explicit patterns and directory lists over `rg ... .` to avoid noise and unnecessary work.

---

### 3. Using `rg` in Python Tests and Tools

All Python tests/tools that perform governance-related searches should:

1. Check that `rg` is available.
2. Use `subprocess.run([RG_CMD, ...])` to perform the search.
3. Fail fast if `rg` is missing (this is a configuration error).

Recommended helper pattern:

```python
import os
import shutil
import subprocess

# Optional override; rename the env var to suit your project (e.g. MYPROJECT_RG)
RG_CMD = os.environ.get("PROJECT_RG", "rg")

def require_ripgrep() -> None:
    """Ensure ripgrep is available; if not, fail with a clear message."""
    if shutil.which(RG_CMD) is None:
        raise RuntimeError(
            f"ripgrep-compatible command '{RG_CMD}' not found. "
            "Install ripgrep or set PROJECT_RG to a valid rg binary."
        )

def run_rg(pattern: str, *paths: str) -> subprocess.CompletedProcess:
    """Run rg with the given pattern and paths."""
    require_ripgrep()
    cmd = [RG_CMD, pattern, *paths]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)
```

Usage in tests (example Clean Table check):

```python
def test_clean_table_src_has_no_todos():
    result = run_rg(r"TODO|FIXME|XXX", "src/")
    # rg returns 0 if matches found, 1 if none; both are valid exit codes here
    assert result.returncode in (0, 1)
    assert "TODO" not in result.stdout
    assert "FIXME" not in result.stdout
    assert "XXX" not in result.stdout
```

---

### 4. Clean Table & Legacy Audits — `rg` as the Enforcement Engine

**Clean Table checks** (no TODO/FIXME/XXX in production code) MUST use `rg`:

```bash
rg "TODO|FIXME|XXX" src/   && echo "❌ Clean Table violation in src/" && exit 1   || echo "✅ Clean Table: src/ has no TODO/FIXME/XXX"
```

**Legacy field audits** (e.g. preventing use of deprecated schema fields) MUST use `rg`:

```bash
# Example: block use of removed field `old_security_flag`
if rg "old_security_flag" src/; then
  echo "❌ Legacy field 'old_security_flag' used in src/"
  exit 1
fi
```

Rules:

- Do not re-implement wide regex scanning in Python when a single `rg` call suffices.
- Treat the `rg` patterns used in Clean Table / legacy scripts as part of the project’s governance contract.

---

### 5. Configuration & Environment Overrides

By default, scripts and tests must call `rg` via `RG_CMD`:

```python
cmd = [RG_CMD, pattern, *paths]
```

If you need an override (e.g. different binary name in CI images):

- Use a single, explicit environment variable (e.g. `PROJECT_RG`).
- That variable must contain **only** the executable name or full path (no arguments).

Constraints:

- The override must point to a binary that is CLI-compatible with ripgrep (`rg` flags and exit codes).
- Using `grep`/`egrep`/`ack` with this override is **not allowed**; that would be governance drift.

---

### 6. CI Alignment

CI must follow the same rules as local development:

1. Ensure `rg` is installed in the CI image (e.g., via apt, brew, or a pre-baked image).
2. Run all Clean Table and legacy audit checks via `rg`.
3. Treat “rg not found” as a misconfigured CI environment, not as a reason to degrade checks.

Example (GitHub Actions):

```yaml
- name: Install ripgrep
  run: |
    if ! command -v rg >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y ripgrep
    fi

- name: Clean Table (src)
  run: |
    rg "TODO|FIXME|XXX" src/       && { echo "❌ Clean Table violation in src/"; exit 1; }       || echo "✅ Clean Table: src/ has no TODO/FIXME/XXX"

- name: Legacy field audit
  run: |
    if rg "old_security_flag" src/; then
      echo "❌ Legacy field 'old_security_flag' used in src/"
      exit 1
    fi
```

Any CI step that uses `grep`/`egrep` for these governance checks, instead of `rg`, is considered **drift** and should be refactored.

---

### 7. Summary

- **ripgrep (`rg`) is the project-standard search tool for governance.**
- All automated checks that inspect source/text for policy (Clean Table, legacy audits, drift detection) must use `rg`, not `grep`.
- `rg` must be available in both local and CI environments; missing `rg` is a configuration error.
- Any introduction of `grep`/`egrep`/`ack` into scripts, tests, or CI for governance is treated as debt and must be removed.
