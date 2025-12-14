## 🧰 Text Search & Clean Table — ripgrep (`rg`) (Project Rule)

This project uses **ripgrep** (`rg`) as the standard tool for all automated text searches (Clean Table checks, legacy audits, schema drift checks, etc.).

> **Hard rule:** Never use `grep`, `egrep`, `ack`, or other ad-hoc search tools in committed scripts, tests, or docs.  
> Always use **ripgrep** (`rg`). Any use of other search tools for project automation is **drift** and should be removed.

---

### 1. Prerequisites & Single Source of Truth

- **Search engine SSOT:**  
  - All automated text searches in this project (e.g. Clean Table gates, legacy field audits, schema drift checks) are defined in terms of `rg` invocations.
  - If a script or test needs to search the repository, it MUST use `rg`.

- **Installation prerequisite:**  
  Before running project scripts or tests that rely on search, you must have **ripgrep** installed.  
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

All repo-wide searches MUST follow the `rg` pattern.

Examples:

```bash
# 1. Clean Table: forbid TODO/FIXME/XXX in production code
rg "TODO|FIXME|XXX" src/doxstrux/

# 2. Legacy field audit: find usages of deprecated keys
rg "legacy_field_name" src/doxstrux/ tools/ tests/

# 3. Schema drift check: ensure no direct access to removed fields
rg "removed_field_name" src/doxstrux/markdown_parser_core.py
```

Guidelines:

- Always scope `rg` searches to **clear directories** (`src/doxstrux/`, `tools/`, `tests/`) instead of running on the entire repo without thinking.
- Prefer explicit patterns and directory lists over `rg ... .` to avoid noisy or slow searches.

---

### 3. Using `rg` in Python Tests and Tools

All Python tests/tools that need to search files should:

1. Check that `rg` is available.
2. Use `subprocess.run(["rg", ...])` to perform the search.
3. Fail or skip based on project policy.

Recommended helper pattern:

```python
import shutil
import subprocess

def require_ripgrep() -> None:
    """Ensure ripgrep is available; if not, fail with a clear message."""
    if shutil.which("rg") is None:
        raise RuntimeError(
            "ripgrep (rg) is required for this test/tool. "
            "Install it via your OS package manager."
        )

def run_rg(pattern: str, *paths: str) -> subprocess.CompletedProcess:
    """Run rg with the given pattern and paths."""
    require_ripgrep()
    cmd = ["rg", pattern, *paths]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)
```

Usage in tests:

```python
def test_clean_table_src_has_no_todos():
    result = run_rg(r"TODO|FIXME|XXX", "src/doxstrux/")
    # We expect no matches: rg returns 1 if nothing found, 0 if matches
    assert result.returncode in (0, 1)
    assert "TODO" not in result.stdout
    assert "FIXME" not in result.stdout
    assert "XXX" not in result.stdout
```

---

### 4. Clean Table & Legacy Audits — `rg` as the Enforcement Engine

**Clean Table checks** (no TODO/FIXME/XXX in production code) MUST use `rg`:

```bash
rg "TODO|FIXME|XXX" src/doxstrux/   && echo "❌ Clean Table violation in src/doxstrux/" && exit 1   || echo "✅ Clean Table: src/doxstrux/ has no TODO/FIXME/XXX"
```

**Legacy field audits** (e.g. preventing use of deprecated schema fields) MUST use `rg`:

```bash
# Example: block use of removed field `old_security_flag`
if rg "old_security_flag" src/doxstrux/; then
  echo "❌ Legacy field 'old_security_flag' used in src/doxstrux/"
  exit 1
fi
```

Rules:

- Do not re-implement regex scanning in Python when a simple `rg` call would do.
- Treat the `rg` patterns used in Clean Table / legacy scripts as part of the project’s governance contract.

---

### 5. Configuration & Environment Overrides

By default, scripts and tests must call `rg` directly:

```python
cmd = ["rg", pattern, *paths]
```

If you need an override (e.g. different binary name in CI images), use a single, explicit environment variable:

```python
import os
import shutil

RG_CMD = os.environ.get("DOXSTRUX_RG", "rg")

def require_ripgrep() -> None:
    if shutil.which(RG_CMD) is None:
        raise RuntimeError(
            f"ripgrep-compatible command '{RG_CMD}' not found. "
            "Install ripgrep or set DOXSTRUX_RG correctly."
        )
```

Constraints:

- `DOXSTRUX_RG` is intended only for CI or exotic environments (e.g., `rg.exe`, container-local path).
- `DOXSTRUX_RG` **must** point to a binary that is CLI-compatible with ripgrep (`rg` flags and exit codes).
- Using `grep`/`egrep` with `DOXSTRUX_RG` is **not allowed**; that would be drift.

---

### 6. CI Alignment

CI must follow the same rules as local development:

1. Ensure `rg` is installed in the CI image (e.g. via apt, brew, or a pre-baked image).
2. Run all Clean Table and legacy audit checks via `rg`.
3. Treat “rg not found” as a misconfigured CI environment.

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
    rg "TODO|FIXME|XXX" src/doxstrux/       && { echo "❌ Clean Table violation in src/doxstrux/"; exit 1; }       || echo "✅ Clean Table: src/doxstrux/ has no TODO/FIXME/XXX"

- name: Legacy field audit
  run: |
    if rg "old_security_flag" src/doxstrux/; then
      echo "❌ Legacy field 'old_security_flag' used in src/doxstrux/"
      exit 1
    fi
```

Any CI step that uses `grep`/`egrep` for these governance checks, instead of `rg`, is considered **drift** and should be refactored.

---

### 7. Summary

- **ripgrep (`rg`) is the project-standard search tool.**
- All automated checks that inspect source/text (Clean Table, legacy audits, drift detection) must use `rg`, not `grep`.
- `rg` must be available in both local and CI environments; missing `rg` is a configuration error, not a reason to degrade checks.
- Any introduction of `grep`/`egrep`/`ack` into scripts, tests, or CI for project governance is treated as debt and must be removed.
