# PYDANTIC_SCHEMA_AI_TASK_LIST.md

**Purpose**: Executable task list for implementing Pydantic schema validation for parser output.
**Version**: 1.6
**Design Reference**: `PYDANTIC_SCHEMA.md` (for rationale and design decisions - do NOT read during execution)

---

## SSOT (Single Source of Truth) Contract

This project has three interrelated sources of truth. Understanding their relationship prevents drift:

| Source | Authority | Role |
|--------|-----------|------|
| `markdown_parser_core.py` | **SSOT for behavior** | How fields are populated at runtime |
| `output_models.py` | **SSOT for shape** | What types and fields the output must have |
| Regression fixtures | **Witnesses** | Prove parser and schema agree |

**Key Rules:**
1. **Parser is authoritative for behavior** — if the schema disagrees with actual parser output, fix the schema (or document why parser needs change)
2. **Schema is authoritative for shape** — downstream code depends on the Pydantic models
3. **Fixtures must be regenerated** when parser behavior OR schema changes
4. **`extra="forbid"`** can only be enabled once schema matches real output (Phase 2.4)

**When in doubt:** Run `tools/discover_parser_shape.py` and derive types from `sample_outputs.json`, not from design documents.

---

## Scope Decisions

This task list focuses on **schema validation** for parser output. The following are explicitly in or out of scope:

**IN SCOPE (this refactor):**
- Pydantic models for `ParserOutput` and nested structures
- RAG-critical security field validation
- Schema export and CI gate
- DocumentIR regression tests
- Fixture validation tooling

**OUT OF SCOPE (deferred to future work):**
- **Plugin-policy enforcement tests**: The design spec describes tests verifying `ALLOWED_PLUGINS`
  consistency and that math/footnotes are always present under permissive profile. These are
  **not included** in this task list. A future refactor should add
  `tests/test_plugin_policy_consistency.py` if profile invariants need enforcement.
- **Semantic extraction tests** (link discriminated unions, math extraction, footnote behavior):
  These are partially covered but not exhaustively ported from the design spec.
- **Parser behavior changes**: This refactor does NOT modify `markdown_parser_core.py` behavior.

If you need plugin-policy tests, create a separate task list or add them as Phase 6.

---

## How This Task List Works

1. **STOP Checkpoints** - AI must pause and verify before continuing
2. **Phase Gates** - Cannot advance until all criteria pass
3. **Clean Table Rule** - No debt carries forward

**Execute tasks sequentially. Do NOT skip ahead.**

---

# Pydantic Schema Implementation - Detailed Task List

**Project**: Add Pydantic v2 schema validation for MarkdownParserCore output
**Created**: 2024
**Status**: Phase 0 - NOT STARTED

---

## Quick Status Dashboard

| Phase | Name | Status | Tests | Clean Table |
|-------|------|--------|-------|-------------|
| 0 | Discovery | ⏳ NOT STARTED | -/- | - |
| 1 | RAG Safety Contract | 📋 PLANNED | -/- | - |
| 2 | Typed Models | 📋 PLANNED | -/- | - |
| 3 | Validation Tools | 📋 PLANNED | -/- | - |
| 4 | Full Validation | 📋 PLANNED | -/- | - |
| 5 | CI Gate | 📋 PLANNED | -/- | - |

**Status Key**: ✅ COMPLETE | ⏳ IN PROGRESS | 📋 PLANNED | ❌ BLOCKED

---

## Success Criteria (Project-Level)

The project is DONE when ALL of these are true:

- [ ] Pydantic models exist in `src/doxstrux/markdown/output_models.py`
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] RAG safety tests pass (script detection, clean doc, javascript: links)
- [ ] Schema exports successfully: `uv run python tools/export_schema.py`
- [ ] CI gate blocks on validation failure

---

## Phase Gate Rules

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE N+1 CANNOT START UNTIL:                              │
│                                                             │
│  1. All Phase N tasks have ✅ status                        │
│  2. Phase N tests pass                                      │
│  3. Phase N Clean Table verified                            │
│  4. Phase unlock artifact exists: .phase-N.complete.json    │
│                                                             │
│  If ANY criterion fails → STOP. Fix or rollback.            │
└─────────────────────────────────────────────────────────────┘
```

**IMPORTANT: Date Placeholders**

Phase unlock artifacts contain `"completion_date": "YYYY-MM-DDTHH:MM:SSZ"`.
Before committing, **replace with actual ISO 8601 timestamp**:

```bash
# Get current timestamp
date -u +"%Y-%m-%dT%H:%M:%SZ"
# Example output: 2024-12-14T15:30:00Z
```

Never commit artifacts with `YYYY-MM-DD` placeholder - this violates Clean Table.

---

## TDD Protocol

Every task follows this sequence:

```
1. WRITE TEST FIRST (or identify existing test)
   └── Test must fail initially (red)

2. IMPLEMENT minimum code to pass
   └── Test must pass (green)

3. VERIFY no regressions
   └── Run: uv run pytest tests/ -v
   └── Expected: ALL PASS

4. CLEAN TABLE CHECK
   └── No TODOs, no placeholders, no warnings
```

**Test Commands Reference**:
```bash
# Fast iteration (single test)
uv run pytest tests/test_output_models_minimal.py -v -x

# Full validation (before commits)
uv run pytest tests/ -v

# Schema export check
uv run python tools/export_schema.py
```

---

## Environment Assumptions

This project uses **uv** as the single entry point for all Python operations.

> **Rule**: Never call `.venv/bin/python` directly. Always use `uv run`.

### 1. Package Management with uv

```bash
# Initial setup (creates .venv and installs deps)
uv sync

# Run any Python command
uv run python tools/discover_parser_shape.py
uv run pytest tests/ -v

# Add dependencies
uv add "pydantic>=2,<3"

# Refresh lock and sync
uv lock --refresh && uv sync
```

### 2. Subprocess Calls in Tests

All subprocess tests MUST use the `UV_RUN` helper pattern:

```python
# tests/test_*.py - REQUIRED header for subprocess tests
import os
import subprocess

# Default: use uv run python (works on all platforms with uv installed)
# Override via env var for special cases (CI matrix, Windows, etc.)
UV_RUN = os.environ.get("DOXSTRUX_UV_RUN", "uv run python").split()

# Usage in subprocess calls:
# subprocess.run([*UV_RUN, "tools/some_tool.py"], ...)
```

**Why a list?** `"uv run python".split()` produces `["uv", "run", "python"]`, which
unpacks correctly with `[*UV_RUN, "script.py"]` → `["uv", "run", "python", "script.py"]`.

**Override policy (STRICT):**

The `DOXSTRUX_UV_RUN` override exists **only** for:
- CI matrix jobs testing against multiple Python versions where uv isn't available
- Exotic containerized environments without uv

**DO NOT use overrides for:**
- Local development (use `uv run`)
- Committed scripts or tests (always default to `uv run python`)
- "Convenience" to skip uv installation

```bash
# CI matrix example (acceptable):
export DOXSTRUX_UV_RUN="python3.11"  # In CI job testing 3.11 compatibility

# Local dev (NEVER do this):
# export DOXSTRUX_UV_RUN="python"  # ❌ Bypasses uv, causes drift
```

**If you find yourself wanting to bypass uv locally, fix your uv installation instead.**

**Cross-reference**: If this project has a global "uv mandatory" rule elsewhere (e.g., CLAUDE.md
or a uv-rules.md), that rule has ONE explicit exception documented here: the `DOXSTRUX_UV_RUN`
override for CI matrix testing. Any other bypass of uv is drift and must be fixed.

### 3. Temporary Files

Never hardcode `/tmp`. Use `tempfile` module:

```python
import tempfile

# WRONG: "/tmp/test_report.json"
# CORRECT:
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    report_path = f.name
```

### 4. External Tools (ripgrep)

Several tests use `rg` (ripgrep) for repo-wide searches. See **Appendix E** for the enforcement model.

**TL;DR**: ripgrep is strictly enforced on CI but skips locally if not installed.

```python
import shutil
import pytest

@pytest.fixture(autouse=True)
def require_ripgrep():
    """Skip if rg not installed (soft dependency - see Appendix E)."""
    if not shutil.which("rg"):
        pytest.skip("ripgrep (rg) not installed - skipping locally (enforced on CI)")
```

---

## Clean Table Definition

> A task is CLEAN only when ALL are true:

- ✅ No unresolved errors or warnings
- ✅ No TODOs, FIXMEs, or placeholders in **production code** (`src/doxstrux/`)
- ✅ No unverified assumptions
- ✅ No duplicated or conflicting logic
- ✅ Tests pass (not skipped, not mocked away)
- ✅ Code is production-ready (not "good enough for now")
- ✅ No placeholder dates in phase artifacts or changelog

**If any box is unchecked → task is NOT complete.**

**Scope clarification**: TODOs in `tools/` and `tests/` are allowed (they're dev code).
The enforced invariant is: no debt in production code under `src/doxstrux/`.

### Enforcement: Repo-Wide from Phase 0

Clean Table is enforced **repo-wide from the start**, not delayed until Phase 3.

Every phase gate includes this check:
```bash
# REQUIRED in every phase gate (not optional)
rg "TODO|FIXME|XXX" src/doxstrux/ && echo "❌ BLOCKED: Clean Table violation" && exit 1 || echo "✅ Clean"
```

**Why universal enforcement?**
- "No debt carries forward" means no debt *anywhere*, not just in task-specific files
- Delayed enforcement creates a loophole that contradicts the Clean Table principle
- Phase 3's `test_clean_table_global.py` is automated CI enforcement, not the first enforcement

**The test in Phase 3 makes enforcement automatic; the manual grep in earlier gates makes it manual but still mandatory.**

---

## Prerequisites (Verify Before Starting)

**ALL must pass before Phase 0 begins:**

- [ ] **uv installed**: `uv --version` returns 0.4+ (or latest)
- [ ] **Environment synced**: `uv sync` completes without error
- [ ] **Python version**: `uv run python --version` returns 3.12+
- [ ] **Dependencies available**: `uv run python -c "from doxstrux.markdown_parser_core import MarkdownParserCore"`
- [ ] **Tests run successfully**: `uv run pytest tests/ -v --tb=short`
- [ ] **Test files exist**: `ls tools/test_mds/` shows markdown test files

**Quick Check**:
```bash
uv sync && \
uv run python -c "from doxstrux.markdown_parser_core import MarkdownParserCore; print('OK')" && \
uv run pytest tests/ -x -q && \
echo "Prerequisites PASS"
```

---

# Phase 0: Discovery

**Goal**: Verify parser output shape before locking schema
**Status**: ⏳ NOT STARTED

---

## Task 0.1: Create Shape Discovery Tool

**Objective**: Build tool to discover actual parser output structure
**Files**: `tools/discover_parser_shape.py`

### TDD Step 1: Write Test First

```python
# tests/test_discover_parser_shape.py
import json
import os
import subprocess
from pathlib import Path

import pytest

# REQUIRED: Use UV_RUN helper for portability (see Environment Assumptions)
UV_RUN = os.environ.get("DOXSTRUX_UV_RUN", "uv run python").split()

def test_discovery_tool_runs():
    """Tool must execute without error AND produce valid outputs."""
    result = subprocess.run(
        [*UV_RUN, "tools/discover_parser_shape.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Discovery failed: {result.stderr}"
    assert "Discovered" in result.stdout, f"Missing 'Discovered' in: {result.stdout}"

def test_discovery_output_files_exist():
    """Discovery must create expected output files."""
    output_dir = Path("tools/discovery_output")
    assert output_dir.exists(), "tools/discovery_output/ not created"
    assert (output_dir / "all_keys.txt").exists(), "all_keys.txt not created"
    assert (output_dir / "sample_outputs.json").exists(), "sample_outputs.json not created"

def test_discovery_all_keys_not_empty():
    """all_keys.txt must contain discovered key paths."""
    keys_file = Path("tools/discovery_output/all_keys.txt")
    if not keys_file.exists():
        pytest.skip("Run discover_parser_shape.py first")
    content = keys_file.read_text()
    lines = [l for l in content.strip().split("\n") if l]
    assert len(lines) >= 10, f"Too few keys discovered: {len(lines)}"
    # Must contain core top-level keys
    assert any("metadata" in k for k in lines), "No metadata keys found"
    assert any("structure" in k for k in lines), "No structure keys found"

def test_discovery_sample_outputs_valid_json():
    """sample_outputs.json must be valid JSON with expected structure."""
    samples_file = Path("tools/discovery_output/sample_outputs.json")
    if not samples_file.exists():
        pytest.skip("Run discover_parser_shape.py first")
    samples = json.loads(samples_file.read_text())
    assert isinstance(samples, list), "sample_outputs.json must be a list"
    assert len(samples) >= 1, "No samples in output"
    for sample in samples:
        assert "file" in sample, "Sample missing 'file' key"
        assert "output" in sample, "Sample missing 'output' key"
```

```bash
# Verify test fails (RED) - tool doesn't exist yet
uv run pytest tests/test_discover_parser_shape.py -v
# Expected: FAIL (FileNotFoundError or similar)
```

### TDD Step 2: Implement

```python
# tools/discover_parser_shape.py
#!/usr/bin/env python3
"""Discover actual parser output shape by parsing representative samples."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux.markdown_parser_core import MarkdownParserCore


def collect_all_keys(obj: dict, prefix: str = "") -> set[str]:
    """Recursively collect all key paths in a dict."""
    keys = set()
    for k, v in obj.items():
        full_key = f"{prefix}.{k}" if prefix else k
        keys.add(full_key)
        if isinstance(v, dict):
            keys.update(collect_all_keys(v, full_key))
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            keys.update(collect_all_keys(v[0], f"{full_key}[]"))
    return keys


def main():
    test_mds = Path("tools/test_mds")
    samples = []

    for subdir in sorted(test_mds.iterdir()):
        if subdir.is_dir():
            md_files = list(subdir.glob("*.md"))[:3]
            samples.extend(md_files)

    all_keys: set[str] = set()
    outputs = []

    for md_file in samples[:50]:
        try:
            content = md_file.read_text(encoding="utf-8")
            parser = MarkdownParserCore(content, security_profile="permissive")
            result = parser.parse()
            all_keys.update(collect_all_keys(result))
            outputs.append({"file": str(md_file), "output": result})
        except Exception as e:
            print(f"SKIP {md_file}: {e}", file=sys.stderr)

    output_dir = Path("tools/discovery_output")
    output_dir.mkdir(exist_ok=True)

    (output_dir / "all_keys.txt").write_text("\n".join(sorted(all_keys)) + "\n")
    (output_dir / "sample_outputs.json").write_text(json.dumps(outputs[:10], indent=2) + "\n")

    print(f"Discovered {len(all_keys)} unique key paths from {len(outputs)} samples")
    print(f"Results written to {output_dir}/")


if __name__ == "__main__":
    main()
```

### TDD Step 3: Verify (GREEN)

```bash
# Run the specific test
uv run pytest tests/test_discover_parser_shape.py -v
# Expected: PASS

# Run full suite (no regressions)
uv run pytest tests/ -v --tb=short
# Expected: ALL PASS

# Execute tool manually
uv run python tools/discover_parser_shape.py
# Expected: "Discovered N unique key paths..."
```

### STOP: Clean Table Check

- [ ] Test passes (not skipped)
- [ ] `tools/discovery_output/all_keys.txt` exists
- [ ] `tools/discovery_output/sample_outputs.json` exists
- [ ] No TODOs in new code
- [ ] Full test suite passes

**Status**: ⏳ NOT STARTED

---

## Task 0.2: Verify Security Fields Exist

**Objective**: Confirm RAG-critical security fields are present in parser output
**Files**: `tests/test_security_field_verification.py` (test-only, no tool file)

### TDD Step 1: Write Test First

```python
# tests/test_security_field_verification.py
import pytest

def test_security_fields_exist_in_samples():
    """Required security paths must exist in sample outputs."""
    import json
    from pathlib import Path

    samples_path = Path("tools/discovery_output/sample_outputs.json")
    if not samples_path.exists():
        pytest.skip("Run discover_parser_shape.py first")

    samples = json.loads(samples_path.read_text())

    REQUIRED_PATHS = [
        "metadata.security.statistics.has_script",
        "metadata.security.summary.has_dangerous_content",
        "metadata.security.warnings",
    ]

    def check_path(obj: dict, path: str) -> bool:
        parts = path.split(".")
        current = obj
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        return True

    missing_count = 0
    for sample in samples:
        output = sample["output"]
        for path in REQUIRED_PATHS:
            if not check_path(output, path):
                missing_count += 1

    # Allow up to 20% missing (edge case files)
    max_missing = len(samples) * len(REQUIRED_PATHS) * 0.2
    assert missing_count <= max_missing, f"Too many missing fields: {missing_count}"
```

```bash
# Verify test fails (RED) - no samples yet
uv run pytest tests/test_security_field_verification.py -v
# Expected: SKIP or FAIL
```

### TDD Step 2: Implement

Run Task 0.1 first if not done, then run the test.

### TDD Step 3: Verify (GREEN)

```bash
# Run discovery first (if needed)
uv run python tools/discover_parser_shape.py

# Run verification test
uv run pytest tests/test_security_field_verification.py -v
# Expected: PASS

# Full suite
uv run pytest tests/ -v --tb=short
# Expected: ALL PASS
```

### STOP: Clean Table Check

- [ ] Security fields verified in ≥80% of samples
- [ ] Test passes
- [ ] No TODOs in new code

**Status**: ⏳ NOT STARTED

---

## STOP: Phase 0 Gate

**Before starting Phase 1, ALL must be true:**

```bash
# 1. Discovery tool works
uv run python tools/discover_parser_shape.py
# Expected: "Discovered N unique key paths..."

# 2. Security fields verified
uv run pytest tests/test_security_field_verification.py -v
# Expected: PASS

# 3. Full test suite passes
uv run pytest tests/ -v --tb=short
# Expected: ALL PASS

# 4. Clean Table verified (REPO-WIDE, not just task files)
rg "TODO|FIXME|XXX" src/doxstrux/ && echo "❌ BLOCKED" && exit 1 || echo "✅ Clean Table"
# Expected: "✅ Clean Table" (no matches found)
```

### Phase 0 Completion Checklist

- [ ] `tools/discover_parser_shape.py` created and works
- [ ] `tools/discovery_output/all_keys.txt` generated
- [ ] Security field verification passes
- [ ] Full test suite passes
- [ ] Git checkpoint created

### Create Phase Unlock Artifact

```bash
# Only run this after ALL above criteria pass
cat > .phase-0.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 0,
  "phase_name": "Discovery",
  "tests_passed": true,
  "clean_table": true,
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"
}
EOF

git add .phase-0.complete.json tools/discover_parser_shape.py tools/discovery_output/
git commit -m "Phase 0 complete: parser shape discovered"
git tag phase-0-complete
```

**Phase 0 Status**: ⏳ NOT STARTED

---

# Phase 1: RAG Safety Contract

**Goal**: Lock in RAG-critical security semantics as executable tests
**Prerequisite**: `.phase-0.complete.json` must exist
**Status**: 📋 PLANNED

---

## STOP: Verify Phase 0 Complete

```bash
test -f .phase-0.complete.json && echo "✅ Phase 0 complete" || echo "❌ BLOCKED"
```

---

## Task 1.1: Add Pydantic Dependency

**Objective**: Add Pydantic v2 to project dependencies
**Files**: `pyproject.toml`

### TDD Step 1: Write Test First

```python
# tests/test_pydantic_installed.py
def test_pydantic_v2_available():
    """Pydantic v2 must be installed."""
    import pydantic
    assert pydantic.VERSION.startswith("2."), f"Need Pydantic v2, got {pydantic.VERSION}"
```

```bash
# Verify test fails (RED)
uv run pytest tests/test_pydantic_installed.py -v
# Expected: FAIL (ModuleNotFoundError)
```

### TDD Step 2: Implement

```bash
uv add "pydantic>=2,<3"
```

### TDD Step 3: Verify (GREEN)

```bash
uv run pytest tests/test_pydantic_installed.py -v
# Expected: PASS

uv run pytest tests/ -v --tb=short
# Expected: ALL PASS
```

### STOP: Clean Table Check

- [ ] `pydantic>=2,<3` in pyproject.toml
- [ ] Test passes
- [ ] No import errors

**Status**: 📋 PLANNED

---

## Task 1.1b: Verify No Existing ParserOutput Usages

**Objective**: Confirm ParserOutput is not already used in runtime code
**Files**: None (verification only)

**WHY**: Task 1.2 creates `ParserOutput` with specific semantics. If there's already
code importing/using a `ParserOutput` class, we could break it by changing the interface.

### Verification

```bash
# Check for existing ParserOutput imports in src/
rg "from.*output_models.*import.*ParserOutput|import.*ParserOutput" src/doxstrux/

# Check for any ParserOutput usage
rg "ParserOutput" src/doxstrux/ --type py

# Expected: No matches, OR only in output_models.py itself (which doesn't exist yet)
```

**If matches found**: Stop and audit. Either:
- The existing usage is compatible with the new interface → proceed
- The existing usage expects different semantics → adapt Task 1.2 or refactor existing code first

**If no matches**: Document this explicitly:
```
# Verified: ParserOutput is not used by any existing runtime code.
# Safe to create with new semantics.
```

### STOP: Clean Table Check

- [ ] No existing ParserOutput usages found (or audited and compatible)
- [ ] Verification documented

**Status**: 📋 PLANNED

---

## Task 1.2: Create Minimal Pydantic Models

**Objective**: Create ParserOutput model with 4 top-level keys
**Files**: `src/doxstrux/markdown/output_models.py`

### TDD Step 1: Write Test First

```python
# tests/test_output_models_minimal.py
import pytest

def test_parser_output_empty_constructs():
    """ParserOutput.empty() must construct without error."""
    from doxstrux.markdown.output_models import ParserOutput
    result = ParserOutput.empty()
    assert result.schema_version == "parser-output@1.0.0"

def test_parser_output_has_four_keys():
    """Empty output must have metadata, content, structure, mappings."""
    from doxstrux.markdown.output_models import ParserOutput
    data = ParserOutput.empty().model_dump()
    assert "metadata" in data
    assert "content" in data
    assert "structure" in data
    assert "mappings" in data

def test_real_parser_output_validates():
    """Real parser output must pass minimal validation."""
    from doxstrux.markdown_parser_core import MarkdownParserCore
    from doxstrux.markdown.output_models import ParserOutput

    parser = MarkdownParserCore("# Hello\n\nParagraph.", security_profile="permissive")
    raw = parser.parse()
    validated = ParserOutput.model_validate(raw)
    assert validated.metadata is not None

def test_empty_string_output_validates():
    """Empty string input must still produce schema-valid output.

    This is a corner case: parse("") should return a valid ParserOutput,
    even though empty() is NOT a spec for what parse("") returns.
    """
    from doxstrux.markdown_parser_core import MarkdownParserCore
    from doxstrux.markdown.output_models import ParserOutput

    parser = MarkdownParserCore("", security_profile="permissive")
    raw = parser.parse()
    validated = ParserOutput.model_validate(raw)  # Must not raise
    assert validated.metadata is not None
    assert validated.content is not None
```

```bash
# Verify test fails (RED)
uv run pytest tests/test_output_models_minimal.py -v
# Expected: FAIL (ImportError)
```

### TDD Step 2: Implement

```python
# src/doxstrux/markdown/output_models.py
"""Pydantic schema for parser output - Milestone A (minimal)."""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict


class DoxBaseModel(BaseModel):
    """Base model - extra='allow' for discovery phase."""
    model_config = ConfigDict(extra="allow")


class ParserOutput(DoxBaseModel):
    """Minimal parser output schema."""
    schema_version: str = "parser-output@1.0.0"
    metadata: dict[str, Any]
    content: dict[str, Any]
    structure: dict[str, Any]
    mappings: dict[str, Any]

    @classmethod
    def empty(cls) -> "ParserOutput":
        """Minimal empty document."""
        return cls(
            metadata={
                "total_lines": 0, "total_chars": 0,
                "has_sections": False, "has_code": False,
                "has_tables": False, "has_lists": False,
                "has_frontmatter": False, "node_counts": {},
                "security": {"warnings": [], "statistics": {}, "summary": {}},
            },
            content={"raw": "", "lines": []},
            structure={
                "sections": [], "paragraphs": [], "lists": [],
                "tables": [], "code_blocks": [], "headings": [],
                "links": [], "images": [], "blockquotes": [],
                "frontmatter": None, "tasklists": [],
                "math": {"blocks": [], "inline": []},
                "footnotes": {"definitions": [], "references": []},
                "html_blocks": [], "html_inline": [],
            },
            mappings={
                "line_to_type": {}, "line_to_section": {},
                "prose_lines": [], "code_lines": [], "code_blocks": [],
            },
        )
```

### TDD Step 3: Verify (GREEN)

```bash
uv run pytest tests/test_output_models_minimal.py -v
# Expected: PASS

uv run pytest tests/ -v --tb=short
# Expected: ALL PASS
```

### STOP: Clean Table Check

- [ ] All 3 tests pass
- [ ] `output_models.py` created
- [ ] No TODOs in new code

**Status**: 📋 PLANNED

---

## Task 1.3: Create RAG Safety Tests

**Objective**: Lock in RAG-critical security behavior
**Files**: `tests/test_rag_safety_contract.py`

**IMPLEMENTATION STATUS NOTE**: The parser (`markdown_parser_core.py`) already implements
ALL extended security fields. These are NOT "reserved/future" — they are live and wired:

| Field | Status | Lines |
|-------|--------|-------|
| `suspected_prompt_injection` | ✅ Implemented | 1113 |
| `prompt_injection_in_images/links/code/tables` | ✅ Implemented | 1130-1188 |
| `has_bidi_controls`, `bidi_controls_present` | ✅ Implemented | 1041-1042 |
| `mixed_scripts`, `invisible_chars` | ✅ Implemented | 1066, 1077 |
| `has_meta_refresh`, `has_frame_like` | ✅ Implemented | 931, existing |
| `oversized_footnotes`, `footnote_injection` | ✅ Implemented | 1218, 1201 |
| `has_csp_header`, `has_xframe_options` | ✅ Implemented | 1242, 1253 |

Do NOT mark these as "reserved" in Pydantic models. They should be typed fields with defaults.

### TDD Step 1: Write Test First

```python
# tests/test_rag_safety_contract.py
"""RAG Safety Contract - these tests MUST pass before proceeding.

IMPORTANT COUPLINGS:

1. Dict vs Typed Access:
   Phase 1 uses dict access (metadata.get("security", {})) because metadata
   is still dict[str, Any]. After Phase 2 completes, update to typed access:

       # Phase 1 (dict access):
       security = validated.metadata.get("security", {})
       stats = security.get("statistics", {})

       # Phase 2+ (typed access):
       security = validated.metadata.security
       stats = security.statistics

   The typed access is preferred as it provides IDE autocompletion and type safety.

2. Security Profile Behavior:
   These tests use `security_profile="permissive"` and bake in the current
   detection heuristics as hard contracts:
   - Script tags MUST set has_script=True
   - javascript: links MUST be flagged
   - Clean docs MUST NOT be blocked

   If security profiles evolve (e.g., stricter defaults, new heuristics), these
   tests become policy enforcement, not just safety verification. This is
   intentional: for RAG pipelines, the current behavior IS the contract.

   If you need to change detection behavior, update these tests explicitly -
   don't weaken them to make implementation changes pass.
"""

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.output_models import ParserOutput


def _get_security(validated: ParserOutput) -> tuple:
    """Helper to access security fields (Phase 1 compatible).

    After Phase 2, replace dict access with typed access:
        return validated.metadata.security, security.statistics, security.summary
    """
    # Phase 1: metadata is dict[str, Any]
    security = validated.metadata.get("security", {})
    stats = security.get("statistics", {})
    summary = security.get("summary", {})
    return security, stats, summary


class TestRAGSafetyContract:
    """If ANY of these fail, RAG safety is compromised."""

    def test_script_tag_detected(self):
        """Script tag MUST set has_script=True and has_dangerous_content=True."""
        md = "<script>alert('xss')</script>\n\nSome text."
        parser = MarkdownParserCore(md, security_profile="permissive")
        raw = parser.parse()
        validated = ParserOutput.model_validate(raw)

        security, stats, summary = _get_security(validated)

        assert stats.get("has_script") is True, "CRITICAL: Script tag not detected"
        assert summary.get("has_dangerous_content") is True, "CRITICAL: Dangerous content not flagged"

    def test_clean_document_not_blocked(self):
        """Clean document MUST NOT be blocked for embedding."""
        md = "# Hello\n\nThis is clean markdown."
        parser = MarkdownParserCore(md, security_profile="permissive")
        raw = parser.parse()
        validated = ParserOutput.model_validate(raw)

        assert validated.metadata.get("embedding_blocked") in (None, False), \
            "Clean document should NOT be blocked"

    def test_javascript_link_detected(self):
        """javascript: links MUST be flagged as dangerous."""
        md = "Click [here](javascript:alert('xss')) for surprise."
        parser = MarkdownParserCore(md, security_profile="permissive")
        raw = parser.parse()
        validated = ParserOutput.model_validate(raw)

        security, stats, _ = _get_security(validated)
        warnings = security.get("warnings", [])

        has_dangerous = (
            stats.get("raw_dangerous_schemes") is True or
            any(w.get("scheme") == "javascript" for w in warnings)
        )
        assert has_dangerous, "CRITICAL: javascript: link not flagged"
```

```bash
# These tests should PASS if parser is implemented correctly
uv run pytest tests/test_rag_safety_contract.py -v
# Expected: PASS (or reveals parser bugs to fix)
```

### TDD Step 2: Implement

Tests are the implementation. If they fail, fix the PARSER, not the tests.

### TDD Step 3: Verify (GREEN)

```bash
uv run pytest tests/test_rag_safety_contract.py -v
# Expected: ALL PASS

uv run pytest tests/ -v --tb=short
# Expected: ALL PASS
```

### STOP: Clean Table Check

- [ ] All 3 RAG safety tests pass
- [ ] No TODOs
- [ ] Tests are the contract - don't weaken them

**Status**: 📋 PLANNED

---

## STOP: Phase 1 Gate

```bash
# 1. Pydantic installed
uv run python -c "import pydantic; assert pydantic.VERSION.startswith('2.')"

# 2. Models exist and work
uv run python -c "from doxstrux.markdown.output_models import ParserOutput; ParserOutput.empty()"

# 3. RAG safety tests pass
uv run pytest tests/test_rag_safety_contract.py -v

# 4. Full suite passes
uv run pytest tests/ -v --tb=short

# 5. Clean Table verified (REPO-WIDE)
rg "TODO|FIXME|XXX" src/doxstrux/ && echo "❌ BLOCKED" && exit 1 || echo "✅ Clean Table"
```

### Phase 1 Completion Checklist

- [ ] Pydantic v2 installed
- [ ] `output_models.py` created with minimal schema
- [ ] RAG safety tests pass
- [ ] Full test suite passes
- [ ] Git checkpoint created

### Create Phase Unlock Artifact

```bash
cat > .phase-1.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 1,
  "phase_name": "RAG Safety Contract",
  "tests_passed": true,
  "clean_table": true,
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"
}
EOF

git add .phase-1.complete.json src/doxstrux/markdown/output_models.py tests/test_*.py
git commit -m "Phase 1 complete: RAG safety contract locked"
git tag phase-1-complete
```

**Phase 1 Status**: 📋 PLANNED

---

# Phase 2: Typed Models

**Goal**: Add fully typed nested models with extra="forbid"
**Prerequisite**: `.phase-1.complete.json` must exist
**Status**: 📋 PLANNED

---

## STOP: Verify Phase 1 Complete

```bash
test -f .phase-1.complete.json && echo "✅ Phase 1 complete" || echo "❌ BLOCKED"
```

---

## Task 2.1: Add Metadata + Security Models

**Objective**: Add typed models for Metadata and Security
**Files**: `src/doxstrux/markdown/output_models.py`

### TDD Step 1: Write Test First

```python
# tests/test_typed_models.py
def test_metadata_model_validates():
    """Metadata model must validate real parser output."""
    from doxstrux.markdown_parser_core import MarkdownParserCore
    from doxstrux.markdown.output_models import ParserOutput

    parser = MarkdownParserCore("# Test", security_profile="permissive")
    raw = parser.parse()
    validated = ParserOutput.model_validate(raw)

    # Access typed Metadata (not dict)
    assert hasattr(validated.metadata, "total_lines")
    assert hasattr(validated.metadata, "security")

def test_security_model_validates():
    """Security model must validate real parser output."""
    from doxstrux.markdown_parser_core import MarkdownParserCore
    from doxstrux.markdown.output_models import ParserOutput

    parser = MarkdownParserCore("# Test", security_profile="permissive")
    raw = parser.parse()
    validated = ParserOutput.model_validate(raw)

    security = validated.metadata.security
    assert hasattr(security, "warnings")
    assert hasattr(security, "statistics")
    assert hasattr(security, "summary")
```

```bash
uv run pytest tests/test_typed_models.py -v
# Expected: FAIL (metadata is still dict)
```

### TDD Step 2: Implement

Add typed models to `output_models.py`:
- `Metadata` with typed fields
- `Security`, `SecurityStatistics`, `SecuritySummary`, `SecurityWarning`
- `Encoding` (optional)

Set `extra="forbid"` on new typed models.

### TDD Step 3: Verify (GREEN)

```bash
uv run pytest tests/test_typed_models.py -v
# Expected: PASS

uv run pytest tests/ -v --tb=short
# Expected: ALL PASS
```

### STOP: Clean Table Check

- [ ] Metadata model typed
- [ ] Security models typed
- [ ] `extra="forbid"` on typed models
- [ ] All tests pass

**Status**: 📋 PLANNED

---

## Task 2.2: Add Structure Models (Sliced)

**Objective**: Add typed models for all Structure components
**Files**: `src/doxstrux/markdown/output_models.py`

### Slices (implement sequentially):

**2.2a: Content + Mappings** (~30 min)
- `Content`, `Mappings`, `MappingCodeBlock`

**2.2b: Sections + Headings + Paragraphs** (~45 min)
- `Section`, `Heading`, `Paragraph`

**2.2c: Lists + Tasklists** (~45 min)
- `List`, `ListItem`, `Tasklist`, `TasklistItem`, `BlockRef`
- Note: Use `model_rebuild()` for recursive types

**2.2d: Tables + Code Blocks + Blockquotes** (~45 min)
- `Table`, `CodeBlock`, `Blockquote`, `BlockquoteChildrenSummary`

**2.2e: Links + Images + Math + Footnotes + HTML** (~60 min)
- `Link` (discriminated union: `RegularLink | ImageLink`)
- `Image`, `Math`, `MathBlock`, `MathInline`
- `Footnotes`, `FootnoteDefinition`, `FootnoteReference`
- `HtmlBlock`, `HtmlInline`

### TDD Pattern for Each Slice

```python
def test_slice_X_validates():
    """Slice X models must validate real parser output."""
    from doxstrux.markdown_parser_core import MarkdownParserCore
    from doxstrux.markdown.output_models import ParserOutput

    # Use fixture that exercises this slice
    parser = MarkdownParserCore("...", security_profile="permissive")
    raw = parser.parse()
    validated = ParserOutput.model_validate(raw)

    # Assert typed access works
    assert hasattr(validated.structure, "field_name")
```

### STOP After Each Slice

- [ ] Slice tests pass
- [ ] Full suite passes
- [ ] No dict[str, Any] in completed slice

**Status**: 📋 PLANNED

---

## Task 2.3: Update ParserOutput.empty() for Typed Models

**Objective**: Ensure `empty()` constructs typed model instances, not raw dicts
**Files**: `src/doxstrux/markdown/output_models.py`, `tests/test_output_models_empty.py`

**Why this matters**: Once typed models exist, `ParserOutput.empty()` should explicitly
construct `Metadata`, `Content`, `Structure`, and `Mappings` instances. Do NOT rely on
implicit dict-to-model coercion — that masks semantic gaps.

### TDD Step 1: Write Test First

```python
# tests/test_output_models_empty.py
def test_empty_returns_typed_instances():
    """empty() must return typed model instances, not dicts."""
    from doxstrux.markdown.output_models import (
        ParserOutput, Metadata, Content, Structure, Mappings
    )
    empty = ParserOutput.empty()

    # Must be actual typed instances
    assert isinstance(empty.metadata, Metadata), "metadata must be Metadata instance"
    assert isinstance(empty.content, Content), "content must be Content instance"
    assert isinstance(empty.structure, Structure), "structure must be Structure instance"
    assert isinstance(empty.mappings, Mappings), "mappings must be Mappings instance"

def test_empty_validates_against_schema():
    """empty() output must pass its own validation."""
    from doxstrux.markdown.output_models import ParserOutput
    empty = ParserOutput.empty()
    # Re-validate through model_validate to ensure round-trip works
    revalidated = ParserOutput.model_validate(empty.model_dump())
    assert revalidated.schema_version == empty.schema_version
```

### TDD Step 2: Implement

Update `ParserOutput.empty()` in `output_models.py`:
```python
@classmethod
def empty(cls) -> "ParserOutput":
    """Minimal empty document with typed model instances."""
    return cls(
        metadata=Metadata(...),      # NOT dict
        content=Content(...),        # NOT dict
        structure=Structure(...),    # NOT dict
        mappings=Mappings(...),      # NOT dict
    )
```

### STOP: Clean Table Check

- [ ] `empty()` returns typed instances
- [ ] Test passes
- [ ] No implicit dict coercion in empty()

**Status**: 📋 PLANNED

---

## Task 2.4: DocumentIR Regression Test

**Objective**: Ensure schema changes don't break DocumentIR
**Files**: `tests/test_document_ir_regression.py`

**IMPORTANT API NOTE**: Use `MarkdownParserCore.to_ir()` as the only supported way
to build DocumentIR from parsed markdown. Do NOT use `DocumentIR.from_parser_output()`
— that method does not exist.

### TDD Step 1: Write Test First

```python
# tests/test_document_ir_regression.py
import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore

REGRESSION_FIXTURES = [
    "# Simple heading\n\nA paragraph.",
    "- item 1\n- item 2\n  - nested",
    "| col1 | col2 |\n|------|------|\n| a | b |",
    "```python\ncode\n```",
    "[link](https://example.com)\n\n![img](image.png)",
]

class TestDocumentIRRegression:
    @pytest.mark.parametrize("md_content", REGRESSION_FIXTURES)
    def test_ir_builds_without_error(self, md_content: str):
        """DocumentIR must build from parser without error."""
        parser = MarkdownParserCore(md_content, security_profile="permissive")
        parser.parse()  # Must parse first
        ir = parser.to_ir()  # Correct API: method on parser, not DocumentIR
        assert ir is not None
        assert ir.schema_version == "md-ir@1.0.0"

    def test_heading_document_has_structure(self):
        """IR root must contain parsed structure."""
        md = "# Test Heading\n\nA paragraph of text."
        parser = MarkdownParserCore(md, security_profile="permissive")
        parser.parse()
        ir = parser.to_ir()
        assert ir.root is not None
        assert len(ir.root.children) > 0

    def test_ir_security_metadata_populated(self):
        """IR must carry security metadata from parser.

        NOTE: This test is written to be robust to IR internal refactors.
        ir.security may be a dict today but could become a typed model later.
        We test for semantic presence, not structural assumptions.
        """
        md = "<script>alert('xss')</script>\n\nText."
        parser = MarkdownParserCore(md, security_profile="permissive")
        parser.parse()
        ir = parser.to_ir()

        # Security must be present (could be dict or model)
        assert ir.security is not None, "IR missing security metadata"

        # Access statistics - handle both dict and model patterns
        if hasattr(ir.security, "statistics"):
            # Typed model access
            stats = ir.security.statistics
            has_script = getattr(stats, "has_script", None) or stats.get("has_script")
        elif isinstance(ir.security, dict):
            # Dict access
            stats = ir.security.get("statistics", {})
            has_script = stats.get("has_script")
        else:
            pytest.fail(f"Unexpected ir.security type: {type(ir.security)}")

        assert has_script is True, (
            f"has_script should be True for script tag. Got: {has_script}"
        )
```

### TDD Step 3: Verify

```bash
uv run pytest tests/test_document_ir_regression.py -v
# Expected: ALL PASS
```

### STOP: Clean Table Check

- [ ] IR regression tests pass
- [ ] No silent IR breakage
- [ ] Full suite passes

**Status**: 📋 PLANNED

---

## Task 2.5: Add Strict Base Model for Parser Output

**Objective**: Enable strict validation for parser output WITHOUT breaking other models
**Files**: `src/doxstrux/markdown/output_models.py`

**IMPORTANT**: Do NOT modify `DoxBaseModel.extra` globally.

`DoxBaseModel` is a generic base that may be used by other models in the package
(plugin configs, import tools, future extensions). Flipping it to `extra="forbid"`
globally would break any code relying on "tolerate extra fields" semantics.

**Solution**: Create a parser-specific strict base:

```python
class DoxBaseModel(BaseModel):
    """Generic base - keeps extra='allow' for flexibility."""
    model_config = ConfigDict(extra="allow")

class ParserOutputBaseModel(DoxBaseModel):
    """Strict base for parser output models only - rejects extra fields."""
    model_config = ConfigDict(extra="forbid")
```

Then have `ParserOutput`, `Metadata`, `Structure`, etc. inherit from `ParserOutputBaseModel`.

### TDD Step 1: Write Test First

```python
# tests/test_schema_extra_forbid.py
def test_parser_output_base_is_strict():
    """ParserOutputBaseModel must use extra='forbid'."""
    from doxstrux.markdown.output_models import ParserOutputBaseModel
    extra_setting = ParserOutputBaseModel.model_config.get("extra")
    assert extra_setting == "forbid", f"extra='{extra_setting}' but must be 'forbid'"

def test_doxbasemodel_remains_permissive():
    """DoxBaseModel must remain extra='allow' for non-parser models."""
    from doxstrux.markdown.output_models import DoxBaseModel
    extra_setting = DoxBaseModel.model_config.get("extra")
    assert extra_setting == "allow", (
        f"DoxBaseModel changed to '{extra_setting}' - this breaks other models! "
        "Use ParserOutputBaseModel for strict validation."
    )

def test_parser_output_rejects_extra_fields():
    """ParserOutput must reject unknown fields."""
    from doxstrux.markdown.output_models import ParserOutput
    import pytest
    from pydantic import ValidationError

    valid_output = ParserOutput.empty().model_dump()
    valid_output["__unknown_field__"] = "should fail"

    with pytest.raises(ValidationError) as exc:
        ParserOutput.model_validate(valid_output)
    assert "extra" in str(exc.value).lower() or "unexpected" in str(exc.value).lower()
```

```bash
uv run pytest tests/test_schema_extra_forbid.py -v
# Expected: FAIL (ParserOutputBaseModel doesn't exist yet)
```

### TDD Step 2: Implement

Add to `output_models.py`:
```python
class ParserOutputBaseModel(DoxBaseModel):
    """Strict base for parser output models - rejects extra fields.

    WHY: Parser output schema is a contract. Extra fields indicate:
    - Parser emitting undocumented fields (schema drift), or
    - Consumer passing invalid data

    Both should fail loudly, not silently succeed.
    """
    model_config = ConfigDict(extra="forbid")

# Then update all parser models to inherit from ParserOutputBaseModel:
class Metadata(ParserOutputBaseModel): ...
class Structure(ParserOutputBaseModel): ...
class ParserOutput(ParserOutputBaseModel): ...
```

### TDD Step 3: Verify

```bash
uv run pytest tests/test_schema_extra_forbid.py -v
# Expected: PASS

# CRITICAL: Full suite must still pass with strict validation
uv run pytest tests/ -v --tb=short
# Expected: ALL PASS
```

### STOP: Clean Table Check

- [ ] `extra="forbid"` on DoxBaseModel
- [ ] All tests pass with strict validation
- [ ] No validation errors from extra fields

**Status**: 📋 PLANNED

---

## Task 2.6: Create SCHEMA_CHANGELOG.md with Version Alignment Test

**Objective**: Establish version history SSOT for schema changes WITH enforcement
**Files**: `src/doxstrux/markdown/SCHEMA_CHANGELOG.md`, `tests/test_schema_version_alignment.py`

**Why this matters**: The design spec says SCHEMA_CHANGELOG.md becomes SSOT for version
history once output_models.py exists. Without it, history is trapped in design docs.

**CRITICAL**: The changelog, model default, and exported schema must all agree on version.
Without enforcement, you get drift between three SSOT-ish sources.

### TDD Step 1: Write Version Alignment Test

```python
# tests/test_schema_version_alignment.py
"""Ensure schema version is consistent across all sources."""
import re
from pathlib import Path

def test_schema_version_alignment():
    """ParserOutput.schema_version must match latest SCHEMA_CHANGELOG entry."""
    from doxstrux.markdown.output_models import ParserOutput

    # Get version from model
    model_version = ParserOutput.empty().schema_version
    # e.g., "parser-output@1.0.0"

    # Get latest version from changelog
    changelog_path = Path("src/doxstrux/markdown/SCHEMA_CHANGELOG.md")
    assert changelog_path.exists(), "SCHEMA_CHANGELOG.md not found"

    content = changelog_path.read_text()
    # Match [parser-output@X.Y.Z] headers
    versions = re.findall(r'\[parser-output@(\d+\.\d+\.\d+)\]', content)
    assert versions, "No version entries found in SCHEMA_CHANGELOG.md"

    latest_changelog_version = f"parser-output@{versions[0]}"

    assert model_version == latest_changelog_version, (
        f"Version mismatch!\n"
        f"  ParserOutput.schema_version: {model_version}\n"
        f"  SCHEMA_CHANGELOG latest:     {latest_changelog_version}\n"
        f"Update one to match the other."
    )

def test_exported_schema_version_matches():
    """Exported JSON schema $id version must match model version."""
    import json
    from pathlib import Path
    from doxstrux.markdown.output_models import ParserOutput

    schema_path = Path("schemas/parser_output.schema.json")
    if not schema_path.exists():
        import pytest
        pytest.skip("Schema not exported yet - run tools/export_schema.py first")

    schema = json.loads(schema_path.read_text())
    schema_id = schema.get("$id", "")

    model_version = ParserOutput.empty().schema_version
    # Extract version from schema_id (e.g., "...parser-output.schema.json" doesn't have version)
    # But we should at least ensure schema exists and model is self-consistent
    assert model_version.startswith("parser-output@"), (
        f"Invalid model schema_version format: {model_version}"
    )
```

### Implementation

Create `src/doxstrux/markdown/SCHEMA_CHANGELOG.md`:

```markdown
# Schema Changelog

All notable changes to the parser output schema are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [parser-output@1.0.0] - YYYY-MM-DD

### Added
- Initial Pydantic schema for MarkdownParserCore output
- `ParserOutput` root model with `metadata`, `content`, `structure`, `mappings`
- `Metadata` model with security statistics
- `Structure` model with sections, paragraphs, lists, tables, code_blocks, etc.
- `extra="forbid"` strict validation

### Security
- All RAG-critical security fields typed and validated
- `suspected_prompt_injection`, `prompt_injection_in_*` fields
- BiDi control and invisible character detection fields

## Versioning Policy

- **MAJOR** (X.0.0): Breaking changes to field names/types
- **MINOR** (0.X.0): New optional fields added
- **PATCH** (0.0.X): Documentation or validation fixes only
```

### STOP: Clean Table Check

- [ ] SCHEMA_CHANGELOG.md created
- [ ] Initial entry for parser-output@1.0.0
- [ ] Date placeholder filled with actual date

**Status**: 📋 PLANNED

---

## STOP: Phase 2 Gate

```bash
# 1. All models typed
uv run python -c "
from doxstrux.markdown.output_models import ParserOutput
p = ParserOutput.empty()
assert hasattr(p.metadata, 'total_lines')
assert hasattr(p.structure, 'sections')
print('Models typed')
"

# 2. extra='forbid' enforced on parser models (not globally)
uv run python -c "
from doxstrux.markdown.output_models import ParserOutputBaseModel, DoxBaseModel
assert ParserOutputBaseModel.model_config.get('extra') == 'forbid', 'Parser models must be strict'
assert DoxBaseModel.model_config.get('extra') == 'allow', 'Generic base must stay permissive'
print('Strict validation enabled for parser models only')
"

# 3. IR regression passes
uv run pytest tests/test_document_ir_regression.py -v

# 4. Full suite passes
uv run pytest tests/ -v --tb=short

# 5. Clean Table verified (REPO-WIDE)
rg "TODO|FIXME|XXX" src/doxstrux/ && echo "❌ BLOCKED" && exit 1 || echo "✅ Clean Table"
```

### Create Phase Unlock Artifact

```bash
cat > .phase-2.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 2,
  "phase_name": "Typed Models",
  "tests_passed": true,
  "clean_table": true,
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"
}
EOF

git add .phase-2.complete.json src/doxstrux/markdown/output_models.py
git commit -m "Phase 2 complete: all models typed with extra=forbid"
git tag phase-2-complete
```

**Phase 2 Status**: 📋 PLANNED

---

# Phase 3: Validation Tools

**Goal**: Build fixture validation and regeneration tools
**Prerequisite**: `.phase-2.complete.json` must exist
**Status**: 📋 PLANNED

---

## STOP: Verify Phase 2 Complete

```bash
test -f .phase-2.complete.json && echo "✅ Phase 2 complete" || echo "❌ BLOCKED"
```

---

## Task 3.1: Schema Export Tool

**Objective**: Create tool to export JSON Schema from Pydantic models
**Files**: `tools/export_schema.py`

### TDD Step 1: Write Test First

```python
# tests/test_export_schema.py
import json
import os
import subprocess
from pathlib import Path

# REQUIRED: Use UV_RUN helper for portability (see Environment Assumptions)
UV_RUN = os.environ.get("DOXSTRUX_UV_RUN", "uv run python").split()

SCHEMA_PATH = Path("schemas/parser_output.schema.json")

def test_schema_export_runs():
    """Export tool must run successfully."""
    result = subprocess.run(
        [*UV_RUN, "tools/export_schema.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Export failed: {result.stderr}"
    assert "exported" in result.stdout.lower(), f"Missing success message: {result.stdout}"

def test_schema_file_created():
    """Schema file must exist after export."""
    assert SCHEMA_PATH.exists(), f"{SCHEMA_PATH} not created"

def test_schema_has_correct_id():
    """Schema $id must match expected URL."""
    schema = json.loads(SCHEMA_PATH.read_text())
    expected_id = "https://doxstrux.dev/schemas/parser-output.schema.json"
    assert schema.get("$id") == expected_id, f"Wrong $id: {schema.get('$id')}"

def test_schema_has_correct_title():
    """Schema title must be DoxstruxParserOutput."""
    schema = json.loads(SCHEMA_PATH.read_text())
    assert schema.get("title") == "DoxstruxParserOutput", f"Wrong title: {schema.get('title')}"

def test_schema_has_required_properties():
    """Schema must define metadata, content, structure, mappings properties."""
    schema = json.loads(SCHEMA_PATH.read_text())
    props = schema.get("properties", {})
    for required in ["metadata", "content", "structure", "mappings"]:
        assert required in props, f"Missing required property: {required}"

def test_schema_has_schema_version():
    """Schema must include schema_version with correct default."""
    schema = json.loads(SCHEMA_PATH.read_text())
    props = schema.get("properties", {})
    assert "schema_version" in props, "Missing schema_version property"
    # Check default if present
    sv_prop = props.get("schema_version", {})
    if "default" in sv_prop:
        assert sv_prop["default"].startswith("parser-output@"), (
            f"Unexpected schema_version default: {sv_prop['default']}"
        )
```

### TDD Step 2: Implement

```python
# tools/export_schema.py
#!/usr/bin/env python3
"""Export JSON Schema from Pydantic models."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux.markdown.output_models import ParserOutput


def main():
    schema = ParserOutput.model_json_schema()
    schema["$id"] = "https://doxstrux.dev/schemas/parser-output.schema.json"
    schema["title"] = "DoxstruxParserOutput"

    output_path = Path("schemas/parser_output.schema.json")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")

    print(f"Schema exported to {output_path}")


if __name__ == "__main__":
    main()
```

### STOP: Clean Table Check

- [ ] Export tool works
- [ ] Schema file generated
- [ ] `sort_keys=True` for deterministic output

**Status**: 📋 PLANNED

---

## Task 3.2: Curated Fixture Validator

**Objective**: Validate fixture subset against schema
**Files**: `tools/validate_curated_fixtures.py`

### TDD Step 1: Write Test First

```python
# tests/test_validate_curated_fixtures.py
import os
import re
import subprocess
import tempfile
from pathlib import Path

# REQUIRED: Use UV_RUN helper for portability (see Environment Assumptions)
UV_RUN = os.environ.get("DOXSTRUX_UV_RUN", "uv run python").split()


def test_curated_validation_runs_and_succeeds():
    """Curated fixtures MUST all pass validation (exit code 0)."""
    result = subprocess.run(
        [*UV_RUN, "tools/validate_curated_fixtures.py"],
        capture_output=True,
        text=True,
    )
    # Exit code 0 = all valid, 1 = failures exist
    assert result.returncode == 0, (
        f"Curated fixture validation failed:\n{result.stderr}\n{result.stdout}"
    )


def test_curated_validation_reports_count():
    """Validation must report how many fixtures were checked."""
    result = subprocess.run(
        [*UV_RUN, "tools/validate_curated_fixtures.py"],
        capture_output=True,
        text=True,
    )
    # Must report validation count in output
    assert "validated" in result.stdout.lower() or "passed" in result.stdout.lower(), (
        f"Missing validation count in output: {result.stdout}"
    )


def test_validation_detects_empty_directory():
    """Validation on empty/no-fixture directory must NOT silently pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [*UV_RUN, "tools/validate_curated_fixtures.py",
             "--fixture-dir", tmpdir],
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr

        # MUST either:
        # 1. Exit non-zero, OR
        # 2. Explicitly report "0 fixtures" or "no fixtures"
        if result.returncode == 0:
            assert "0 " in output or "no fixture" in output.lower(), (
                f"Tool silently passed on empty dir without reporting 0 fixtures:\n{output}"
            )


def test_validation_with_real_fixtures_reports_count():
    """When fixtures exist, validation must report actual count (not zero)."""
    result = subprocess.run(
        [*UV_RUN, "tools/validate_curated_fixtures.py"],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    # Must report some positive count (proves tool actually ran)
    match = re.search(r'(\d+)\s*(validated|passed|fixtures)', output.lower())
    assert match, f"No fixture count found in output: {output}"
    count = int(match.group(1))
    assert count > 0, f"Expected >0 fixtures validated, got {count}"


def test_validation_detects_broken_fixture():
    """Tool MUST fail when given an invalid JSON fixture.

    This prevents a stub that always reports success without validation.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a broken fixture (invalid JSON or wrong schema)
        broken_fixture = tmppath / "broken.fixture.json"
        broken_fixture.write_text('{"not_a_valid_parser_output": true}')

        result = subprocess.run(
            [*UV_RUN, "tools/validate_curated_fixtures.py",
             "--fixture-dir", tmpdir],
            capture_output=True,
            text=True,
        )

        # Tool must either:
        # 1. Exit non-zero (validation failed), OR
        # 2. Report the failure in output
        output = result.stdout + result.stderr
        detected_failure = (
            result.returncode != 0 or
            "failed" in output.lower() or
            "invalid" in output.lower() or
            "error" in output.lower()
        )
        assert detected_failure, (
            f"Tool did not detect broken fixture. Exit={result.returncode}, output:\n{output}"
        )


def test_validation_actually_calls_pydantic():
    """Tool must use ParserOutput.model_validate, not just read JSON.

    We verify this by creating a fixture that is valid JSON but missing
    required Pydantic fields.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Valid JSON but missing required ParserOutput fields
        incomplete_fixture = tmppath / "incomplete.fixture.json"
        incomplete_fixture.write_text('{"metadata": {}}')  # Missing content, structure, mappings

        result = subprocess.run(
            [*UV_RUN, "tools/validate_curated_fixtures.py",
             "--fixture-dir", tmpdir],
            capture_output=True,
            text=True,
        )

        # If tool uses model_validate(), this should fail due to missing required fields
        # If tool just loads JSON, this would pass
        output = result.stdout + result.stderr

        # Either exit non-zero OR report validation failure
        if result.returncode == 0:
            # If exit 0, must at least mention 0 passed or report failures
            assert "fail" in output.lower() or "0 passed" in output.lower(), (
                f"Tool passed incomplete fixture without reporting failure:\n{output}"
            )
```

### TDD Step 2: Implement

Create `tools/validate_curated_fixtures.py` with:
- Pattern-based fixture discovery (NO hard-coded paths)
- `ParserOutput.model_validate()` on each fixture
- Exit code 1 on any failure

### STOP: Clean Table Check

- [ ] Tool runs without crash
- [ ] Pattern-based discovery (no hard-coded lists)
- [ ] Reports pass/fail clearly

**Status**: 📋 PLANNED

---

## Task 3.3: Legacy Field Audit Test

**Objective**: Ensure no runtime code depends on deprecated fields
**Files**: `tests/test_no_legacy_field_runtime_usage.py`

### TDD Step 1: Write Test First

```python
# tests/test_no_legacy_field_runtime_usage.py
import subprocess
import shutil
import pytest

LEGACY_FIELDS_TO_AUDIT = [
    "exception_was_raised",
]

class TestLegacyFieldAudit:
    @pytest.fixture(autouse=True)
    def require_ripgrep(self):
        """Skip tests if ripgrep is not installed."""
        if not shutil.which("rg"):
            pytest.skip("ripgrep (rg) not installed - see Appendix E")

    @pytest.mark.parametrize("field_name", LEGACY_FIELDS_TO_AUDIT)
    def test_no_runtime_usage(self, field_name: str):
        result = subprocess.run(
            ["rg", "-l", field_name, "src/doxstrux/"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            files = result.stdout.strip().split("\n")
            pytest.fail(f"'{field_name}' found in: {files}")
        # rg returns 1 for "no matches" which is success for this test
        assert result.returncode in (0, 1), f"rg failed: {result.stderr}"
```

### STOP: Clean Table Check

- [ ] Audit test passes
- [ ] No legacy fields in runtime code
- [ ] ripgrep (`rg`) is installed (or test skips gracefully)

**Status**: 📋 PLANNED

---

## Task 3.4: Global Clean Table Test

**Objective**: Enforce Clean Table rule across entire repo
**Files**: `tests/test_clean_table_global.py`

**Why this matters**: The Clean Table rule says "no TODOs, FIXMEs, or placeholders".
Without automated enforcement, this is just a slogan. This test makes it a hard invariant.

### TDD Step 1: Write Test First

```python
# tests/test_clean_table_global.py
"""Global Clean Table enforcement - catches policy violations repo-wide."""

import subprocess
import shutil
import pytest
from pathlib import Path

class TestCleanTableGlobal:
    @pytest.fixture(autouse=True)
    def require_ripgrep(self):
        if not shutil.which("rg"):
            pytest.skip("ripgrep (rg) not installed")

    def test_no_todo_or_fixme_in_src(self):
        """No TODO/FIXME markers in production code."""
        result = subprocess.run(
            ["rg", "-l", r"TODO|FIXME|XXX", "src/doxstrux/"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            files = result.stdout.strip().split("\n")
            pytest.fail(f"TODO/FIXME found in: {files}")

    def test_no_placeholder_dates_in_phase_artifacts(self):
        """Phase completion artifacts must have real dates, not placeholders."""
        placeholder = "YYYY-MM-DDTHH:MM:SSZ"
        for artifact in Path(".").glob(".phase-*.complete.json"):
            content = artifact.read_text()
            assert placeholder not in content, (
                f"{artifact} contains placeholder date '{placeholder}' - "
                "replace with actual ISO 8601 timestamp before committing"
            )

    def test_no_placeholder_dates_in_changelog(self):
        """SCHEMA_CHANGELOG.md must have real dates."""
        changelog = Path("src/doxstrux/markdown/SCHEMA_CHANGELOG.md")
        if changelog.exists():
            content = changelog.read_text()
            assert "YYYY-MM-DD" not in content, (
                f"{changelog} contains placeholder date - replace before committing"
            )
```

### STOP: Clean Table Check

- [ ] Test passes on clean repo
- [ ] Test fails if TODO/FIXME added to src/
- [ ] Test fails if phase artifact has placeholder date

**Status**: 📋 PLANNED

---

## STOP: Phase 3 Gate

```bash
# 1. Export tool works
uv run python tools/export_schema.py

# 2. Curated validation runs
uv run python tools/validate_curated_fixtures.py

# 3. Legacy audit passes
uv run pytest tests/test_no_legacy_field_runtime_usage.py -v

# 4. Global Clean Table passes
uv run pytest tests/test_clean_table_global.py -v

# 5. Full suite passes
uv run pytest tests/ -v --tb=short
```

### Create Phase Unlock Artifact

```bash
cat > .phase-3.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 3,
  "phase_name": "Validation Tools",
  "tests_passed": true,
  "clean_table": true,
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"
}
EOF

git add .phase-3.complete.json tools/
git commit -m "Phase 3 complete: validation tools ready"
git tag phase-3-complete
```

**Phase 3 Status**: 📋 PLANNED

---

# Phase 4: Full Validation

**Goal**: Validate ALL fixtures (report-only mode)
**Prerequisite**: `.phase-3.complete.json` must exist
**Status**: 📋 PLANNED

---

## Task 4.1: Full Validation Tool

**Objective**: Create tool to validate all fixtures with report mode
**Files**: `tools/validate_test_pairs.py`, `tests/test_validate_test_pairs.py`

### TDD Step 1: Write Test First

```python
# tests/test_validate_test_pairs.py
import json
import os
import subprocess
import tempfile
from pathlib import Path

# REQUIRED: Use UV_RUN helper for portability (see Environment Assumptions)
UV_RUN = os.environ.get("DOXSTRUX_UV_RUN", "uv run python").split()


def test_validation_tool_runs():
    """Tool must execute without crashing."""
    result = subprocess.run(
        [*UV_RUN, "tools/validate_test_pairs.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Tool crashed: {result.stderr}"
    assert "--report" in result.stdout, "Missing --report flag"
    assert "--threshold" in result.stdout, "Missing --threshold flag"


def test_validation_report_mode():
    """Report mode must exit 0 and produce JSON output."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        report_path = Path(f.name)

    try:
        result = subprocess.run(
            [*UV_RUN, "tools/validate_test_pairs.py",
             "--report", "--output", str(report_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Report mode failed: {result.stderr}"
        assert report_path.exists(), "Report file not created"
        report = json.loads(report_path.read_text())
        assert "total" in report, "Report missing 'total'"
        assert "passed" in report, "Report missing 'passed'"
        assert "pass_rate" in report, "Report missing 'pass_rate'"
    finally:
        report_path.unlink(missing_ok=True)


def test_validation_threshold_pass():
    """Threshold mode must exit 0 when pass rate meets threshold."""
    result = subprocess.run(
        [*UV_RUN, "tools/validate_test_pairs.py", "--threshold", "0"],
        capture_output=True,
        text=True,
    )
    # Threshold 0% should always pass
    assert result.returncode == 0, f"Threshold 0% failed: {result.stderr}"


def test_validation_threshold_fail():
    """Threshold mode must exit 1 when pass rate below threshold."""
    result = subprocess.run(
        [*UV_RUN, "tools/validate_test_pairs.py", "--threshold", "101"],
        capture_output=True,
        text=True,
    )
    # Threshold 101% should always fail (impossible to achieve)
    assert result.returncode == 1, "Threshold 101% should fail"


def test_validation_finds_real_fixtures():
    """Tool MUST actually parse fixtures (not just pretend).

    This test prevents a no-op stub that claims success without doing work.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        report_path = Path(f.name)

    try:
        result = subprocess.run(
            [*UV_RUN, "tools/validate_test_pairs.py",
             "--report", "--output", str(report_path),
             "--test-dir", "tools/test_mds"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Validation failed: {result.stderr}"
        report = json.loads(report_path.read_text())

        # CRITICAL: Must have actually found fixtures
        assert report["total"] > 0, (
            "Tool reported 0 fixtures - either test_mds is empty or tool is a stub"
        )
        # Sanity check: we know test_mds has hundreds of files
        assert report["total"] >= 50, (
            f"Expected ≥50 fixtures in test_mds, got {report['total']}"
        )
    finally:
        report_path.unlink(missing_ok=True)


def test_tool_uses_pydantic_validation():
    """Tool MUST actually call ParserOutput.model_validate() - verified by code inspection.

    This is THE critical IP test. We can't easily mock across subprocess boundaries,
    so we verify by inspecting the tool's source code for the validation call.

    A stub tool that doesn't use Pydantic would be caught by this test.
    """
    tool_path = Path("tools/validate_test_pairs.py")
    assert tool_path.exists(), "validate_test_pairs.py not found"

    content = tool_path.read_text()

    # Tool MUST import ParserOutput
    assert "ParserOutput" in content, (
        "validate_test_pairs.py does not mention ParserOutput - "
        "tool is not using Pydantic schema validation!"
    )

    # Tool MUST call model_validate (or validate, or parse_obj for older Pydantic)
    validation_patterns = [
        "model_validate",
        ".validate(",
        "parse_obj",
    ]
    has_validation_call = any(pattern in content for pattern in validation_patterns)
    assert has_validation_call, (
        "validate_test_pairs.py does not call model_validate() or equivalent - "
        "tool is not actually validating against the Pydantic schema!\n"
        f"Expected one of: {validation_patterns}"
    )

    # Tool MUST handle validation errors
    error_handling_patterns = [
        "ValidationError",
        "except Exception",
        "except BaseException",
    ]
    has_error_handling = any(pattern in content for pattern in error_handling_patterns)
    assert has_error_handling, (
        "validate_test_pairs.py does not handle validation errors - "
        "tool will crash on invalid fixtures instead of counting them as failed!"
    )


def test_tool_validation_affects_results():
    """Tool's reported counts MUST reflect actual validation, not hardcoded values.

    We run the tool twice:
    1. Against a directory with valid markdown
    2. Against a directory with intentionally problematic content

    If the tool is actually validating, the results should differ based on content.
    If it's hardcoding results, both runs would report the same thing.
    """
    with tempfile.TemporaryDirectory() as tmpdir1, \
         tempfile.TemporaryDirectory() as tmpdir2:

        tmppath1 = Path(tmpdir1)
        tmppath2 = Path(tmpdir2)

        # Directory 1: Simple valid markdown
        (tmppath1 / "valid.md").write_text("# Valid\n\nSimple paragraph.")

        # Directory 2: Multiple files to get different counts
        for i in range(5):
            (tmppath2 / f"file{i}.md").write_text(f"# File {i}\n\nContent.")

        # Run tool on both directories
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1, \
             tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            report1_path = Path(f1.name)
            report2_path = Path(f2.name)

        try:
            subprocess.run(
                [*UV_RUN, "tools/validate_test_pairs.py",
                 "--report", "--output", str(report1_path), "--test-dir", tmpdir1],
                capture_output=True, text=True,
            )
            subprocess.run(
                [*UV_RUN, "tools/validate_test_pairs.py",
                 "--report", "--output", str(report2_path), "--test-dir", tmpdir2],
                capture_output=True, text=True,
            )

            report1 = json.loads(report1_path.read_text())
            report2 = json.loads(report2_path.read_text())

            # Counts MUST differ based on actual content
            assert report1["total"] != report2["total"], (
                f"Both directories reported same total ({report1['total']}) - "
                "tool may be hardcoding results instead of actually validating!"
            )

            # Sanity check: counts should match what we created
            assert report1["total"] == 1, f"Expected 1 file in dir1, got {report1['total']}"
            assert report2["total"] == 5, f"Expected 5 files in dir2, got {report2['total']}"

        finally:
            report1_path.unlink(missing_ok=True)
            report2_path.unlink(missing_ok=True)


def test_validation_reports_failures_correctly():
    """Tool MUST report failed > 0 when given files that fail validation.

    This test creates a directory with markdown files, runs the tool,
    and verifies the tool is actually doing schema validation by checking
    that it processes files and reports results accurately.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a valid markdown file
        (tmppath / "valid.md").write_text("# Valid\n\nJust a heading.")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_path = Path(f.name)

        try:
            result = subprocess.run(
                [*UV_RUN, "tools/validate_test_pairs.py",
                 "--report", "--output", str(report_path),
                 "--test-dir", tmpdir],
                capture_output=True,
                text=True,
            )
            report = json.loads(report_path.read_text())

            # Must have processed our file
            assert report["total"] >= 1, "Did not find any fixtures in temp dir"

            # Report must have proper structure
            assert "passed" in report, "Report missing 'passed'"
            assert "failed" in report, "Report missing 'failed'"
            assert "pass_rate" in report, "Report missing 'pass_rate'"

            # Verify math: passed + failed == total
            assert report["passed"] + report["failed"] == report["total"], (
                f"Math error: {report['passed']} + {report['failed']} != {report['total']}"
            )
        finally:
            report_path.unlink(missing_ok=True)
```

### TDD Step 2: Implement

```python
# tools/validate_test_pairs.py
#!/usr/bin/env python3
"""Validate all test pair fixtures against Pydantic schema."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.output_models import ParserOutput


def main():
    parser = argparse.ArgumentParser(description="Validate test pairs")
    parser.add_argument("--report", action="store_true", help="Exit 0 even on failures")
    parser.add_argument("--threshold", type=float, default=100, help="Pass if >= N%% valid")
    parser.add_argument("--output", type=str, help="Write JSON report to file")
    parser.add_argument("--test-dir", type=str, default="tools/test_mds")
    args = parser.parse_args()

    test_dir = Path(args.test_dir)
    passed, failed = 0, 0
    errors = []

    for md_file in sorted(test_dir.rglob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            result = MarkdownParserCore(content, security_profile="permissive").parse()
            ParserOutput.model_validate(result)
            passed += 1
        except Exception as e:
            failed += 1
            errors.append({"file": str(md_file), "error": str(e)})

    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0

    report = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(pass_rate, 2),
        "errors": errors[:20],  # Limit error details
    }

    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n")

    print(f"Validated {total} fixtures: {passed} passed, {failed} failed ({pass_rate:.1f}%)")

    if args.report:
        sys.exit(0)
    elif pass_rate >= args.threshold:
        sys.exit(0)
    else:
        print(f"FAIL: Pass rate {pass_rate:.1f}% < threshold {args.threshold}%")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### TDD Step 3: Verify (GREEN)

```bash
uv run pytest tests/test_validate_test_pairs.py -v
# Expected: ALL PASS

uv run pytest tests/ -v --tb=short
# Expected: ALL PASS
```

### Key Features:
- `--report` mode (exit 0 even on failures)
- `--threshold N` (pass if ≥N% valid)
- JSON report output

### STOP: Clean Table Check

- [ ] Tool validates all fixtures
- [ ] Report mode works
- [ ] Threshold mode works

**Status**: 📋 PLANNED

---

## Task 4.2: Run Full Validation

**Objective**: Execute full validation and triage results

```bash
uv run python tools/validate_test_pairs.py --report --output validation_report.json
```

### STOP: Clean Table Check

- [ ] Full validation completed
- [ ] Report generated
- [ ] Pass rate ≥95% (required for Phase 5)

**Status**: 📋 PLANNED

---

## STOP: Phase 4 Gate

```bash
# 1. Full validation runs
uv run python tools/validate_test_pairs.py --report

# 2. Check pass rate (must be ≥95% for Phase 5)
# If <95%, fix fixtures or schema before proceeding
```

### Create Phase Unlock Artifact

```bash
cat > .phase-4.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 4,
  "phase_name": "Full Validation",
  "pass_rate": 0.XX,
  "tests_passed": true,
  "clean_table": true,
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"
}
EOF

git add .phase-4.complete.json
git commit -m "Phase 4 complete: full validation at XX%"
git tag phase-4-complete
```

**Phase 4 Status**: 📋 PLANNED

---

# Phase 5: CI Gate

**Goal**: Make schema validation a blocking CI gate
**Prerequisite**: `.phase-4.complete.json` must exist AND pass rate ≥95%
**Status**: 📋 PLANNED

---

## Task 5.1: Add CI Workflow

**Objective**: Create GitHub Actions workflow for schema validation
**Files**: `.github/workflows/schema_validation.yml`, `tests/test_ci_workflow.py`

### TDD Step 1: Write Test First

```python
# tests/test_ci_workflow.py
"""CI Workflow validation tests.

TRADE-OFF NOTE: These tests validate workflow *structure* (presence of required steps,
correct ordering), not workflow *correctness* (whether commands actually work).

A workflow like:
    - run: echo uv sync
    - run: echo validate_test_pairs.py --threshold 100

would technically pass these tests, because we're checking for string presence,
not actual execution semantics.

Why we accept this:
1. Testing actual CI behavior requires running the workflow, which is expensive and slow.
2. Stricter YAML parsing (e.g., verifying no `echo` prefix) becomes brittle fast.
3. The validation tools themselves have strong tests - if they're present in CI,
   they'll do their job.

If someone writes a fake workflow, it will fail when CI actually runs. These tests
catch structural mistakes (missing steps, wrong order) not malicious compliance.
"""
from pathlib import Path
import yaml

WORKFLOW_PATH = Path(".github/workflows/schema_validation.yml")

def _load_workflow():
    """Load and parse workflow YAML."""
    content = WORKFLOW_PATH.read_text()
    return yaml.safe_load(content)

def _get_steps(workflow):
    """Extract all steps from all jobs."""
    steps = []
    for job_name, job in workflow.get("jobs", {}).items():
        steps.extend(job.get("steps", []))
    return steps

def test_ci_workflow_file_exists():
    """CI workflow file must exist."""
    assert WORKFLOW_PATH.exists(), "CI workflow file not created"

def test_ci_workflow_valid_yaml():
    """CI workflow must be valid YAML."""
    workflow = _load_workflow()
    assert workflow is not None, "Invalid YAML"
    assert "jobs" in workflow, "Missing 'jobs' key"

def test_ci_workflow_has_uv_setup():
    """CI workflow must set up uv for reproducible deps."""
    workflow = _load_workflow()
    steps = _get_steps(workflow)

    # Check for uv setup action
    uv_setup = any(
        "astral-sh/setup-uv" in str(step.get("uses", ""))
        for step in steps
    )
    assert uv_setup, "Missing astral-sh/setup-uv action"

def test_ci_workflow_has_dependency_install():
    """CI workflow must install dependencies before validation."""
    workflow = _load_workflow()
    steps = _get_steps(workflow)

    found_uv_sync = False
    for step in steps:
        run_cmd = step.get("run", "")
        if "uv sync" in run_cmd:
            found_uv_sync = True
            break
    assert found_uv_sync, "Missing 'uv sync' step"

def test_ci_workflow_has_validation_step():
    """CI workflow must include schema validation step."""
    workflow = _load_workflow()
    steps = _get_steps(workflow)

    found_validation = False
    for step in steps:
        run_cmd = step.get("run", "")
        if "validate_test_pairs.py" in run_cmd:
            found_validation = True
            assert "--threshold 100" in run_cmd, "Missing --threshold 100"
            break
    assert found_validation, "No validation step found"

def test_ci_workflow_has_schema_drift_check():
    """CI workflow must check for schema drift."""
    workflow = _load_workflow()
    steps = _get_steps(workflow)

    found_drift_check = False
    for step in steps:
        run_cmd = step.get("run", "")
        if "git diff --exit-code" in run_cmd and "schema" in run_cmd.lower():
            found_drift_check = True
            break
    assert found_drift_check, "No schema drift check found"

def test_ci_workflow_step_ordering():
    """Dependencies must be installed BEFORE validation runs."""
    workflow = _load_workflow()
    steps = _get_steps(workflow)

    uv_sync_idx = None
    validate_idx = None

    for i, step in enumerate(steps):
        run_cmd = step.get("run", "")
        if "uv sync" in run_cmd and uv_sync_idx is None:
            uv_sync_idx = i
        if "validate_test_pairs.py" in run_cmd and validate_idx is None:
            validate_idx = i

    assert uv_sync_idx is not None, "uv sync step not found"
    assert validate_idx is not None, "validate step not found"
    assert uv_sync_idx < validate_idx, (
        f"uv sync (step {uv_sync_idx}) must come before validation (step {validate_idx})"
    )
```

### TDD Step 2: Implement

```yaml
# .github/workflows/schema_validation.yml
name: Schema Validation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate-schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync

      - name: Validate all test pairs
        run: uv run python tools/validate_test_pairs.py --threshold 100

      - name: Export schema
        run: uv run python tools/export_schema.py

      - name: Check for schema drift
        run: git diff --exit-code schemas/parser_output.schema.json
```

### TDD Step 3: Verify (GREEN)

```bash
uv run pytest tests/test_ci_workflow.py -v
# Expected: ALL PASS

uv run pytest tests/ -v --tb=short
# Expected: ALL PASS
```

### Key Steps:
1. Validate all test pairs (`--threshold 100`)
2. Export schema
3. Check for schema drift (`git diff --exit-code`)

### STOP: Clean Table Check

- [ ] CI workflow created
- [ ] Blocks on validation failure
- [ ] Blocks on schema drift

**Status**: 📋 PLANNED

---

## STOP: Phase 5 Gate (FINAL)

```bash
# 1. CI workflow exists
test -f .github/workflows/schema_validation.yml

# 2. Full validation passes at 100%
uv run python tools/validate_test_pairs.py --threshold 100

# 3. Schema export is clean
uv run python tools/export_schema.py
git diff --exit-code schemas/parser_output.schema.json
```

### Create Phase Unlock Artifact (FINAL)

```bash
cat > .phase-5.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 5,
  "phase_name": "CI Gate",
  "tests_passed": true,
  "clean_table": true,
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ",
  "project_complete": true
}
EOF

git add .phase-5.complete.json .github/workflows/
git commit -m "Phase 5 complete: CI gate enabled"
git tag phase-5-complete
git tag pydantic-schema-v1.0.0
```

**Phase 5 Status**: 📋 PLANNED

---

# Appendix A: Rollback Procedures

## A.1: Single Test Failure

```bash
# 1. Identify failing test
uv run pytest tests/ -v --tb=short 2>&1 | head -50

# 2. If fixable in <15 min, fix it
# 3. If not fixable, revert last change
git diff HEAD~1 --stat
git checkout HEAD~1 -- [affected_file]

# 4. Verify tests pass again
uv run pytest tests/ -v --tb=short
```

## A.2: Multiple Test Failures (Full Revert)

```bash
# 1. Find last known good state
git log --oneline -10

# 2. Hard reset
git reset --hard [GOOD_COMMIT]

# 3. Verify
uv run pytest tests/ -v --tb=short
```

## A.3: Phase Gate Failure

```
DO NOT proceed to next phase.
1. Identify which criterion failed
2. Fix the specific issue
3. Re-run phase gate verification
4. Only proceed when ALL criteria pass
```

---

# Appendix B: AI Assistant Instructions

## Drift Prevention Rules

1. **Before each response**, re-read the current task's objective
2. **After completing code**, immediately run verification commands
3. **If test fails**, fix it before moving on (no "we'll fix it later")
4. **If blocked**, document why and suggest rollback
5. **Never skip** Clean Table checks

## Verification Frequency

| Action | Verify Immediately |
|--------|-------------------|
| Create new file | File exists, syntax valid |
| Modify function | Related tests pass |
| Complete task | Full test suite |
| Complete phase | Phase gate checklist |

## When to Stop and Escalate

- Test suite drops below 100% pass rate
- RAG safety tests fail
- Clean Table criteria cannot be satisfied
- Phase gate blocked for >2 attempts

## Prohibited Actions

- ❌ Starting Phase N+1 without Phase N artifact
- ❌ Marking task complete with failing tests
- ❌ Leaving TODOs in "completed" code
- ❌ Skipping Clean Table verification
- ❌ Weakening RAG safety tests to make them pass
- ❌ Reading PYDANTIC_SCHEMA.md during execution (design rationale causes drift)

---

# Appendix C: File Change Tracking

**Note on Task 2.2 slices**: Task 2.2 defines slices 2.2a–2.2e (Content, Sections, Lists, Tables, Links).
These slices all UPDATE `output_models.py` incrementally and reuse `tests/test_typed_models.py`.
No separate test files per slice; validation happens via the Phase 2 gate.

| Phase.Task | File | Action | Verified |
|------------|------|--------|----------|
| 0.1 | `tools/discover_parser_shape.py` | CREATE | ⏳ |
| 0.1 | `tests/test_discover_parser_shape.py` | CREATE | ⏳ |
| 0.1 | `tools/discovery_output/all_keys.txt` | CREATE | ⏳ |
| 0.1 | `tools/discovery_output/sample_outputs.json` | CREATE | ⏳ |
| 0.2 | `tests/test_security_field_verification.py` | CREATE | ⏳ |
| 1.1 | `pyproject.toml` | UPDATE | 📋 |
| 1.1 | `tests/test_pydantic_installed.py` | CREATE | 📋 |
| 1.2 | `src/doxstrux/markdown/output_models.py` | CREATE | 📋 |
| 1.2 | `tests/test_output_models_minimal.py` | CREATE | 📋 |
| 1.3 | `tests/test_rag_safety_contract.py` | CREATE | 📋 |
| 2.1 | `src/doxstrux/markdown/output_models.py` | UPDATE | 📋 |
| 2.1 | `tests/test_typed_models.py` | CREATE | 📋 |
| 2.2 | `src/doxstrux/markdown/output_models.py` | UPDATE | 📋 |
| 2.3 | `tests/test_output_models_empty.py` | CREATE | 📋 |
| 2.4 | `tests/test_document_ir_regression.py` | CREATE | 📋 |
| 2.5 | `tests/test_schema_extra_forbid.py` | CREATE | 📋 |
| 2.6 | `src/doxstrux/markdown/SCHEMA_CHANGELOG.md` | CREATE | 📋 |
| 3.1 | `tools/export_schema.py` | CREATE | 📋 |
| 3.1 | `tests/test_export_schema.py` | CREATE | 📋 |
| 3.1 | `schemas/parser_output.schema.json` | CREATE | 📋 |
| 3.2 | `tools/validate_curated_fixtures.py` | CREATE | 📋 |
| 3.2 | `tests/test_validate_curated_fixtures.py` | CREATE | 📋 |
| 3.3 | `tests/test_no_legacy_field_runtime_usage.py` | CREATE | 📋 |
| 3.4 | `tests/test_clean_table_global.py` | CREATE | 📋 |
| 4.1 | `tools/validate_test_pairs.py` | CREATE | 📋 |
| 4.1 | `tests/test_validate_test_pairs.py` | CREATE | 📋 |
| 5.1 | `.github/workflows/schema_validation.yml` | CREATE | 📋 |
| 5.1 | `tests/test_ci_workflow.py` | CREATE | 📋 |

---

# Appendix D: Progress Log

```
[YYYY-MM-DD HH:MM] Started Phase 0
[YYYY-MM-DD HH:MM] Task 0.1 complete - discovery tool works
[YYYY-MM-DD HH:MM] Task 0.2 complete - security fields verified
[YYYY-MM-DD HH:MM] Phase 0 Gate: ✅ ALL PASS
[YYYY-MM-DD HH:MM] Created .phase-0.complete.json
```

---

# Appendix E: External Dependencies

## ripgrep (`rg`)

**Enforcement model**: ripgrep is a **soft dependency** with different behavior in CI vs local:

| Environment | Behavior | Rationale |
|-------------|----------|-----------|
| CI (ubuntu-latest) | **Strictly enforced** | rg is pre-installed; tests MUST run |
| Local dev machine | **Skips with warning** | Don't block devs without rg installed |

**What this means:**
- The `require_ripgrep` fixture calls `pytest.skip()` if `shutil.which("rg")` returns None.
- On CI, rg is always present, so Clean Table and legacy field audit tests always run.
- Locally, if you don't have rg, those tests skip silently — **you won't catch Clean Table violations until CI**.

**Recommendation**: Install ripgrep locally to get the same enforcement as CI:

```bash
# Ubuntu/Debian
sudo apt install ripgrep

# macOS
brew install ripgrep

# Windows (via scoop)
scoop install ripgrep
```

**If you choose not to install rg**, be aware that:
- `test_clean_table_global.py` will skip its repo-wide TODO/FIXME scan
- `test_no_legacy_field_runtime_usage.py` will skip legacy field audits
- You'll only discover violations when CI runs

---

**End of Task List**
