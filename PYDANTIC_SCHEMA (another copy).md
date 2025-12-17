---
prose_input:
  schema_version: "0.0.8"
  project_name: "doxstrux"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
  python_version: "3.12"
---

# Pydantic Schema Implementation Plan

> **STATUS: DESIGN DOCUMENT** - This describes a target state. None of the Pydantic
> models, tooling, or tests described below exist yet.

## SSOT Declaration

**Until `output_models.py` exists, this file is DESIGN ONLY.**

Once code exists:
- `src/doxstrux/markdown/output_models.py` is SSOT for schema shape
- `src/doxstrux/markdown/SCHEMA_CHANGELOG.md` is SSOT for version history
- This file becomes **historical reference only** - do not update it

**Do not treat any section of this file as "the truth" once implementation begins.**

---

## Scope

### In Scope

- [x] Pydantic models for parser output validation
- [x] Schema export tooling (JSON Schema generation)
- [x] Test fixture validation
- [x] RAG safety semantics testing
- [x] CI integration for schema enforcement

### Out of Scope

- Parser implementation changes — Deferred to: separate parser refactor
- Backwards compatibility with pre-schema consumers — Reason: schema defines correct behavior

---

## Decisions (Binding)

| ID | Decision | Rationale | Alternatives Rejected |
|----|----------|-----------|----------------------|
| D1 | Use Pydantic v2 for schema | Type safety, JSON Schema export, validation | dataclasses (no validation), attrs (less ecosystem) |
| D2 | Milestone-based incremental rollout | Reduces risk, allows early testing | Big bang release (too risky) |
| D3 | `extra="forbid"` as final state | Strict contract enforcement | `extra="allow"` (allows drift) |

---

## External Dependencies

### Required Files/Modules

| Path | Required Symbol(s) | Purpose |
|------|-------------------|---------|
| `src/doxstrux/markdown_parser_core.py` | `MarkdownParserCore` | Parser to validate against |
| `pyproject.toml` | — | Configuration file |

### Required Libraries

| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | `>=2,<3` | Schema validation and JSON Schema export |

### Required Tools

| Tool | Version | Verification Command |
|------|---------|---------------------|
| `uv` | `>=0.1` | `uv --version` |
| `rg` | `>=13` | `rg --version` |

---

## File Manifest

| Path | Action | Phase | Description |
|------|--------|-------|-------------|
| `src/doxstrux/markdown/output_models.py` | CREATE | A | Pydantic models for parser output |
| `tests/test_output_models_minimal.py` | CREATE | A | Minimal schema validation tests |
| `tests/test_output_models_security.py` | CREATE | A | RAG safety semantic tests |
| `tools/export_schema.py` | CREATE | B | JSON Schema export tool |
| `tools/validate_test_pairs.py` | CREATE | C | Fixture validation tool |

---

## Test Strategy

| Layer | Tool | Location | Trigger |
|-------|------|----------|---------|
| Unit tests | pytest | `tests/test_output_models_*.py` | Pre-commit, CI |
| Type checking | mypy | `src/doxstrux/` | Pre-commit, CI |
| Schema validation | Pydantic | `tests/` | CI |
| Linting | ruff | `src/`, `tests/` | Pre-commit |

---

## Phase 0

See detailed Phase 0 tasks in the implementation section below.

### Required Files/Modules

| Path | Required Symbol(s) | Purpose |
|------|-------------------|---------|
| `src/doxstrux/markdown_parser_core.py` | `MarkdownParserCore` | Parser under test |

### Required Libraries

| Package | Version | Purpose |
|---------|---------|---------|
| `markdown-it-py` | `>=3` | Parser dependency |

### Required Tools

| Tool | Version | Verification Command |
|------|---------|---------------------|
| `uv` | `>=0.1` | `uv --version` |

---

## Goal

Create a **single source of truth (SSOT) schema** for parser output using Pydantic models.

## Why We Need This

1. **Test pair validation**: We have `md` / `json` test pairs that must conform to the same schema as parser output
2. **Schema trust**: Current genson-inferred schema is incomplete (misses edge cases)
3. **Contract enforcement**: Parser output and test fixtures must share the exact same structure
4. **Documentation**: Pydantic models serve as living documentation of output format

---

## Current Reality (What Actually Exists)

### Codebase Inventory

| Item | Status | Location |
|------|--------|----------|
| Pydantic models | ❌ **Does not exist** | No `output_models.py` |
| Pydantic dependency | ❌ **Not in pyproject.toml** | `rg "pydantic" src` returns nothing |
| Schema tooling | ⚠️ genson-based only | `tools/generate_parser_schema.py` |
| JSON Schema | ⚠️ Inferred, not authoritative | `schemas/parser_output.schema.json` |
| `tools/export_schema.py` | ❌ **Does not exist** | Planned, not implemented |
| `tools/validate_test_pairs.py` | ❌ **Does not exist** | Planned, not implemented |
| `tools/regenerate_fixtures.py` | ❌ **Does not exist** | Planned, not implemented |
| `tests/test_output_models_empty.py` | ❌ **Does not exist** | Planned, not implemented |
| `tests/test_parser_output_schema_conformance.py` | ❌ **Does not exist** | Planned, not implemented |

### Expected Parser Output Shape (AUDIT ONLY)

> **⚠️ COARSE CHECKLIST ONLY**: This table is for Phase 0 spot-checks - just enough to know
> what areas to look at. Do NOT use this table to derive model shapes or detailed structure.
> Models and tests are the only contract. Let the schema speak for itself.

| Area | What to Check | Notes |
|------|---------------|-------|
| `structure.*` | Sections, lists, links exist | Shape determined at implementation time |
| `structure.footnotes` | Present under permissive | **ABSENT under strict profile** |
| `structure.math` | Present under permissive | May be empty |
| `metadata.*` | Security, embedding flags exist | Top-level location |
| `metadata.embedding_blocked` | Primary location | Set by `_apply_security_policy()` |
| `metadata.embedding_block_reason` | Primary location | Note: field name WITHOUT 'd' |
| `metadata.security.embedding_blocked` | **Also set for oversized data URIs** | Parser line 965 - NOT legacy |
| `metadata.security.embedding_blocked_reason` | Oversized URI reason | Note: field name WITH 'd' |

**Phase 0 usage:** Compare `all_keys.txt` against this list to spot obvious gaps.
This table is intentionally coarse. If discovery finds fields not listed here, that's expected -
add them to models if legitimate. Models are SSOT, not this table.

### Current Architecture

```
Parser (src/doxstrux/markdown_parser_core.py)
    │
    ▼
Plain dict output (no validation)
    │
    ▼
genson infers schema (incomplete, requires manual fixes)
    │
    ▼
schemas/parser_output.schema.json (descriptive, not authoritative)
```

---

## Target State (What This Plan Describes)

```
Pydantic Models (output_models.py)  ← SSOT
    │
    ├──▶ JSON Schema export (auto-generated, always accurate)
    │
    ├──▶ Parser output validation (CI gate)
    │
    └──▶ Test pair validation (md/json fixtures)
```

### Migration Required

Before implementing the models below:

1. ✅ **`embedding_blocked` location**: RESOLVED → model at BOTH levels (see Decisions below)
2. ✅ **`footnotes` presence**: RESOLVED → always present under permissive profile (see Decisions below)
3. **Add Pydantic dependency**: Update `pyproject.toml` with `pydantic>=2,<3`
4. **Implement tools**: `export_schema.py`, `validate_test_pairs.py`, `regenerate_fixtures.py`
5. **Implement tests**: `test_output_models_minimal.py`, `test_output_models_empty.py`

### Decisions (Binding for Implementation)

These decisions resolve the questions above. They are **binding** for implementation.

> **⚠️ Normative scope:** These decisions are binding **until `output_models.py` + `SCHEMA_CHANGELOG.md` exist**.
> After that, the code and its changelog are the only binding contract; this section becomes
> historical rationale only. See the SSOT Rule at the top of this document.

> **Scope:** These decisions apply to the **permissive** security profile, which is the schema
> baseline. Other profiles (strict, moderate) may legitimately disable plugins and produce
> different output structure. The Pydantic schema is designed for permissive profile output.

| Question | Decision | Rationale |
|----------|----------|-----------|
| Plugin policy | **All schema-required plugins enabled (permissive profile)** | Permissive profile guarantees full output; schema validates this baseline |
| `footnotes` presence | **Always present under permissive** (non-optional) | Permissive enables footnote plugin; empty if no footnotes in content |
| `math` presence | **Always present under permissive** (non-optional) | Permissive enables math plugin; empty if no math in content |
| `embedding_blocked` location | **Model at BOTH levels** | `metadata.embedding_blocked` = overall block flag; `metadata.security.embedding_blocked` = oversized URI block. Both are valid, non-legacy, and must continue to work. |
| `encoding` presence | **Optional** (`Encoding \| None`) | Only populated when parsing from bytes with decode step |
| `source_path` presence | **Optional** (`str \| None`) | Only populated by `parse_markdown_file()` |
| Extended security stats | **Optional with defaults** | Fields like `suspected_prompt_injection` are reserved; not yet implemented |

**Design principle:** Under permissive profile, parser emits full structure. Consumer decides what to use.
Other profiles may have reduced structure - schema validation targets permissive output only.

### ⚠️ Implementation Warnings (Verified Against Parser Code)

These issues were discovered during deep codebase analysis. Address them during implementation:

| Issue | Details | Resolution |
|-------|---------|------------|
| **Footnotes profile-dependent** | `structure.footnotes` is ABSENT under strict profile (footnote plugin disabled). Only present under permissive/moderate. | Schema tests MUST use `security_profile="permissive"` |
| **`embedding_blocked` dual location** | Set at BOTH `metadata.embedding_blocked` (by `_apply_security_policy()`) AND `metadata.security.embedding_blocked` (for oversized data URIs). | Model both locations; they serve different purposes |
| **Field naming inconsistency** | `metadata.embedding_block_reason` (without 'd') vs `metadata.security.embedding_blocked_reason` (with 'd'). Both exist. | Model each field exactly as parser emits it |
| **Profile scope for tests** | Plan assumes permissive profile output. Other profiles have legitimately different shapes. | Document profile scope in test docstrings |

---

## Final Contract: ParserOutput v1.x (Design Target)

> **⚠️ INTENDED FINAL STATE** - This section defines the target schema shape. Once
> `output_models.py` exists, THE CODE IS SSOT, not this section.
>
> Milestones describe HOW to get here; this section defines WHERE we're aiming.
> Milestone code snippets show intermediate states; this shows the target.

### Final ParserOutput Structure

```python
class ParserOutput(DoxBaseModel):
    """Final schema - all fields typed, extra='forbid' everywhere."""
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "parser-output@1.0.0"  # Bump on shape changes only

    metadata: Metadata          # Fully typed (B1)
    content: Content            # Fully typed (B1.5)
    structure: Structure        # Fully typed (B1.5)
    mappings: Mappings          # Fully typed (B1.5)
```

### Final `empty()` Behavior

> **Implementation note:** `SecurityStatistics.empty()` is a helper method that returns
> a `SecurityStatistics` instance with all boolean flags `False`, all counts `0`, and
> empty collections. Define this helper in `output_models.py` when implementing B1.

```python
@classmethod
def empty(cls) -> "ParserOutput":
    """
    FINAL STATE: Returns fully typed nested models, not dicts.

    This is what empty() looks like AFTER all milestones complete.
    Milestone A uses dict placeholders; this is the target.
    """
    return cls(
        metadata=Metadata(
            total_lines=0,
            total_chars=0,
            has_sections=False,
            has_code=False,
            has_tables=False,
            has_lists=False,
            has_frontmatter=False,
            node_counts={},
            security=Security(
                warnings=[],
                statistics=SecurityStatistics.empty(),  # See model for fields
                summary=SecuritySummary(
                    ragged_tables_count=0,
                    total_warnings=0,
                    has_dangerous_content=False,
                    unicode_risk_score=0,
                ),
                # Security-level embedding fields (oversized URI case)
                embedding_blocked=None,  # Only set when oversized data URI detected
                embedding_blocked_reason=None,
            ),
            # Metadata-level embedding fields (set by _apply_security_policy)
            embedding_blocked=False,
            embedding_block_reason=None,  # Note: field name WITHOUT 'd'
            quarantined=False,
            quarantine_reasons=None,
        ),
        content=Content(raw="", lines=[]),
        structure=Structure(
            sections=[],
            paragraphs=[],
            lists=[],
            tables=[],
            code_blocks=[],
            headings=[],
            links=[],
            images=[],
            blockquotes=[],
            frontmatter=None,
            tasklists=[],
            math=Math(blocks=[], inline=[]),
            footnotes=Footnotes(definitions=[], references=[]),
            html_blocks=[],
            html_inline=[],
        ),
        mappings=Mappings(
            line_to_type={},
            line_to_section={},
            prose_lines=[],
            code_lines=[],
            code_blocks=[],
        ),
    )
```

### Final Security Semantics (RAG-Critical)

These behaviors MUST hold in the final implementation:

| Input | Required Output |
|-------|-----------------|
| `<script>alert('xss')</script>` | `metadata.security.statistics.has_script=True`, `summary.has_dangerous_content=True` |
| `[link](javascript:evil())` | Link flagged in warnings OR `disallowed_link_schemes` contains "javascript" |
| Safe markdown (no threats) | `metadata.embedding_blocked=False`, `summary.has_dangerous_content=False` |
| Oversized data URI | `metadata.embedding_blocked=True` with reason |

### Milestone → Final State Mapping

| Milestone | `empty()` returns | `extra=` | Notes |
|-----------|-------------------|----------|-------|
| A | Plain dicts | `"allow"` | Discovery phase |
| B1 | `Metadata` typed, others dict | `"forbid"` on Metadata | Partial typing |
| B1.5 | All typed models | `"forbid"` everywhere | **Matches Final Contract** |
| B2+ | All typed models | `"forbid"` everywhere | Matches Final Contract |

**Key point:** Code in Milestone A/B1 sections shows INTERMEDIATE states. The Final Contract
above shows the TARGET state. Do not confuse the two.

---

## Implementation Plan

> **RESTRUCTURED (v1.10)**: This plan now follows an incremental milestone approach
> instead of big-bang rollout. Each milestone has clear success criteria and can be
> verified independently.

---

### Phase 0: Discovery (REQUIRED FIRST)

**Goal:** Verify assumptions about parser output shape before locking schema.
**Estimated Time:** 2-4 hours
**Blocking:** All other phases depend on Phase 0 completion.

#### Phase 0.1: Shape Discovery Tool

**File:** `tools/discover_parser_shape.py`

```python
#!/usr/bin/env python3
"""
Discover actual parser output shape by parsing representative samples.

Dumps raw outputs for manual inspection and automated diffing against
expected schema. This tool MUST be run before implementing Pydantic models.
"""

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
    # Representative samples covering different feature areas
    test_mds = Path("tools/test_mds")
    samples = []

    # Collect ~50 diverse samples
    for subdir in sorted(test_mds.iterdir()):
        if subdir.is_dir():
            md_files = list(subdir.glob("*.md"))[:3]  # 3 per category
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

    # Write discovered shape
    output_dir = Path("tools/discovery_output")
    output_dir.mkdir(exist_ok=True)

    # All unique key paths
    (output_dir / "all_keys.txt").write_text(
        "\n".join(sorted(all_keys)) + "\n"
    )

    # Sample outputs for inspection
    (output_dir / "sample_outputs.json").write_text(
        json.dumps(outputs[:10], indent=2) + "\n"
    )

    print(f"Discovered {len(all_keys)} unique key paths from {len(outputs)} samples")
    print(f"Results written to {output_dir}/")
    print("\nNext: Compare all_keys.txt against PYDANTIC_SCHEMA.md expected fields")


if __name__ == "__main__":
    main()
```

**Execution:**
```bash
.venv/bin/python tools/discover_parser_shape.py
# Review: tools/discovery_output/all_keys.txt
# Review: tools/discovery_output/sample_outputs.json
```

**Success Criteria:**

> **Note:** This is sampling (~50 files), NOT a census. It provides sufficient confidence
> about parser shape but may miss edge-case fields. That's acceptable - Milestone A uses
> `extra="allow"` to catch any remaining unknowns.

- [x] `all_keys.txt` generated with field paths observed in sample outputs
- [x] Expected top-level keys (metadata, content, structure, mappings) are present
- [x] Any unexpected keys noted for investigation (not blocking)
- [x] **Security fields verified in `sample_outputs.json`** (see below)

#### Phase 0.1.1: Security Field Verification (REQUIRED)

**Why:** Milestone A tests assume specific security field paths exist. Verify them NOW:

```python
# Quick verification script (run after discover_parser_shape.py)
import json
from pathlib import Path

samples = json.loads((Path("tools/discovery_output/sample_outputs.json")).read_text())

REQUIRED_SECURITY_PATHS = [
    "metadata.security.statistics.has_script",
    "metadata.security.statistics.has_event_handlers",
    "metadata.security.statistics.has_data_uri_images",
    "metadata.security.summary.has_dangerous_content",
    "metadata.security.warnings",
]

def check_path(obj: dict, path: str) -> bool:
    """Check if a dotted path exists in nested dict."""
    parts = path.split(".")
    current = obj
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True

for sample in samples:
    output = sample["output"]
    missing = [p for p in REQUIRED_SECURITY_PATHS if not check_path(output, p)]
    if missing:
        print(f"WARN {sample['file']}: missing {missing}")
```

**Success criteria:** All required security paths exist in at least 80% of samples.
If paths are missing, investigate BEFORE Milestone A - the RAG safety tests will fail.

### Phase 0.1.1 Threshold Action Rule (BINDING)

**If Phase 0.1.1 reports ANY required path missing in >20% of samples, you MUST:**

| Missing Rate | Required Action |
|--------------|-----------------|
| 0-20% | **Proceed** - occasional gaps acceptable, tests will catch edge cases |
| 21-50% | **Investigate** - either (a) fix parser/extractor to emit field, or (b) downgrade Milestone A test to "best effort" with explicit `pytest.mark.xfail` |
| 51-100% | **STOP** - field is fundamentally missing; fix parser BEFORE continuing |

**Example actions:**

- `has_script` missing in 30% of samples → Investigate. Likely the test fixtures lack `<script>` tags. Add 2-3 fixtures with script tags, re-run.
- `summary.has_dangerous_content` missing in 60% of samples → STOP. The security extractor isn't emitting this field consistently. Fix the extractor first.

**This is a binding gate.** Do NOT proceed to Milestone A with >20% missing rate on any
required security path unless you've explicitly marked the corresponding test as `xfail`
with documented rationale.

#### Phase 0.2: Key Path Lister (DELETED)

> **DELETED:** This tool was demoted, then deleted. It cannot handle discriminated unions
> (`oneOf`/`anyOf`) so it always produces false positives. "Unknown field count = 0" is
> structurally impossible with our schema.
>
> If you need to debug why a field appears "extra", use `ParserOutput.model_json_schema()`
> directly and inspect the `$defs` for union branches.

#### Phase 0.3: Plugin Policy Verification (DEFERRED to Milestone B)

> **Note:** This phase is deferred. Plugin policy already exists in `config.py:ALLOWED_PLUGINS`.
> No new module needed - just verify the existing config is used consistently.

**Why deferred:** Creating a separate `plugin_policy.py` with its own `REQUIRED_PLUGINS` tuple
would be a parallel schema. The SSOT for plugins is `markdown/config.py:ALLOWED_PLUGINS`.

**Existing SSOT:** `src/doxstrux/markdown/config.py`

```python
# Already exists - DO NOT duplicate
ALLOWED_PLUGINS = {
    "strict": {"builtin": ["table"], "external": ["front_matter", "tasklists"]},
    "moderate": {"builtin": ["table", "strikethrough"], "external": ["front_matter", "tasklists", "footnote"]},
    "permissive": {"builtin": ["table", "strikethrough"], "external": ["front_matter", "tasklists", "footnote", "deflist"]},
}
```

**When to execute:** After Milestone A, as part of Milestone B validation.

**Test specification (for Milestone B):**

```python
"""Tests that parser uses config.py plugin policy consistently."""

import pytest
from doxstrux.markdown.config import ALLOWED_PLUGINS
from doxstrux.markdown_parser_core import MarkdownParserCore


class TestPluginPolicyConsistency:
    """Verify parser uses ALLOWED_PLUGINS from config.py."""

    def test_permissive_profile_has_all_plugins(self):
        """Permissive profile must include all schema-required plugins."""
        permissive = ALLOWED_PLUGINS["permissive"]
        all_plugins = set(permissive["builtin"]) | set(permissive["external"])
        # These plugins affect output structure and must be present
        required_for_schema = {"table", "footnote", "tasklists", "front_matter"}
        assert required_for_schema <= all_plugins

    def test_math_always_present_in_output(self):
        """Math structure must always be present (plugin or fallback)."""
        parser = MarkdownParserCore("No math here.", security_profile="permissive")
        result = parser.parse()
        assert "math" in result.get("structure", {}), "math must always be present"

    def test_footnotes_always_present_in_output(self):
        """Footnotes structure must always be present with permissive profile."""
        parser = MarkdownParserCore("No footnotes.", security_profile="permissive")
        result = parser.parse()
        assert "footnotes" in result.get("structure", {}), "footnotes must always be present"
```

**Success Criteria (for Milestone B):**
- [x] Tests verify `ALLOWED_PLUGINS["permissive"]` includes all schema-required plugins
- [x] NO new plugin list created - use `config.py:ALLOWED_PLUGINS` as SSOT
- [x] Parser output includes `math` and `footnotes` with permissive profile

#### Phase 0.4: Embedding Invariant Tests (DEFERRED to Milestone B)

> **Note:** This phase is deferred. Embedding invariants require understanding the actual
> parser output first. Run after Milestone A validates basic schema shape.

**Why deferred:** Writing invariant tests before knowing the actual parser behavior is
speculative. First validate that the schema matches reality (Milestone A), then add
behavioral invariants (Milestone B).

**Test specification (for Milestone B):**

```python
"""Tests for embedding_blocked field invariants - add after Milestone A."""

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore


class TestEmbeddingInvariants:
    """
    Tests that embedding_blocked fields maintain consistency.

    Invariant: If security.embedding_blocked is True, then
    metadata.embedding_blocked must also be True.
    """

    def test_embedding_blocked_consistency(self):
        """embedding_blocked at security level implies metadata level."""
        md = '![img](data:image/png;base64,' + 'A' * 100000 + ')'
        parser = MarkdownParserCore(md, security_profile="moderate")
        result = parser.parse()

        meta_blocked = result.get("metadata", {}).get("embedding_blocked", False)
        sec_blocked = result.get("metadata", {}).get("security", {}).get("embedding_blocked", False)

        if sec_blocked:
            assert meta_blocked, (
                "INVARIANT VIOLATION: security.embedding_blocked=True "
                "but metadata.embedding_blocked=False"
            )

    def test_safe_document_not_blocked(self):
        """Safe document must not have embedding blocked."""
        md = "# Hello\n\nClean markdown."
        parser = MarkdownParserCore(md, security_profile="permissive")
        result = parser.parse()

        assert not result.get("metadata", {}).get("embedding_blocked"), \
            "Safe document should not be blocked"
```

**Success Criteria (for Milestone B):**
- [x] Invariant tests pass against real parser output
- [x] Tests run AFTER Milestone A schema is validated

#### Phase 0 Completion Checklist

**Phase 0 is now minimal:** Only shape discovery (0.1) and security field verification (0.1.1)
run before Milestone A. Phase 0.2 (Key Path Lister) was deleted. Phases 0.3, 0.4 are deferred to Milestone B.

**Sampling disclaimer:** Phase 0 provides _sufficient confidence_, not certainty.
We sample ~50 files to identify obvious shape issues. Milestone A's `extra="allow"`
catches anything missed. Do NOT block on "complete coverage" - that's impossible
without running every fixture, which defeats the purpose of sampling.

Before proceeding to Milestone A:

- [x] `tools/discover_parser_shape.py` executed successfully
- [x] `all_keys.txt` generated - spot-check for obvious gaps (not exhaustive review)
- [x] **Security field verification passed** (Phase 0.1.1 script shows no critical missing paths)
- [x] NO requirement for "0 unknown fields" yet (that's Milestone B)
- [x] Proceed to Milestone A to create minimal schema

---

### Milestone A: RAG Safety Contract (NOT Minimal)

**Goal:** Lock in RAG-critical security semantics as executable tests.
**Scope:** 4 top-level keys + `ParserOutput.empty()` + security field tests.
**Reality Check:** This is a SECURITY milestone, not a "quick schema check".

> **What gets locked in:**
> - Script tag detection (`has_script`, `has_dangerous_content`)
> - Safe document safety (`embedding_blocked`)
> - Dangerous link scheme detection (`javascript:` links)
>
> **Implication:** If parser output uses different field names than these tests expect,
> you WILL need to modify security extractors. RAG safety is the IP worth protecting.
>
> **⚠️ DELIBERATE BEHAVIOR CHANGE:** If these tests fail, the plan requires changing parser
> behavior to match. This is intentional - we're defining what "correct" RAG safety means.
> If current parser behavior differs, fixing it IS a breaking change for consumers who
> depended on the old behavior. This trade-off is accepted: RAG safety correctness > backwards
> compatibility for security fields.

#### Task A.1: Add Pydantic Dependency

```bash
uv add "pydantic>=2,<3"
```

#### Task A.2: Create MINIMAL Pydantic Models

**File:** `src/doxstrux/markdown/output_models.py`

```python
"""
Minimal Pydantic schema - Milestone A.

SCOPE: Top-level structure only. Nested models added in Milestone B.

This file will grow incrementally:
- Milestone A: ParserOutput with 4 top-level keys (dict placeholders)
- Milestone B: Add nested models (Section, Paragraph, List, Table)
- Milestone C: Full validation
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class DoxBaseModel(BaseModel):
    """
    Base model for schema validation.

    MILESTONE A (feature branch): extra="allow" - discover unexpected fields without failing.
    MILESTONE B1 (feature branch): DoxBaseModel stays "allow"; typed models (Metadata, Security)
        get their own ConfigDict(extra="forbid").
    MILESTONE B1.5 (enforcement branch): Switch DoxBaseModel itself to extra="forbid".
    MAIN BRANCH: DoxBaseModel MUST be extra="forbid" (enforced by test_doxbasemodel_extra_is_forbid).
    """
    model_config = ConfigDict(extra="allow")  # Will become "forbid" when merged to main


class ParserOutput(DoxBaseModel):
    """
    Minimal parser output schema - Milestone A.

    Only validates presence of 4 top-level keys.
    Nested structure is Any until Milestone B.
    """
    schema_version: str = "parser-output@1.0.0"  # First implementation version

    # Top-level keys only - nested structure is Any for now
    metadata: dict[str, Any]
    content: dict[str, Any]
    structure: dict[str, Any]
    mappings: dict[str, Any]

    @classmethod
    def empty(cls) -> "ParserOutput":
        """
        Minimal empty document - Milestone A.

        Only defines top-level structure. Nested defaults added in Milestone B.
        """
        return cls(
            metadata={
                "total_lines": 0,
                "total_chars": 0,
                "has_sections": False,
                "has_code": False,
                "has_tables": False,
                "has_lists": False,
                "has_frontmatter": False,
                "node_counts": {},
                "security": {"warnings": [], "statistics": {}, "summary": {}},
            },
            content={"raw": "", "lines": []},
            structure={
                "sections": [],
                "paragraphs": [],
                "lists": [],
                "tables": [],
                "code_blocks": [],
                "headings": [],
                "links": [],
                "images": [],
                "blockquotes": [],
                "frontmatter": None,
                "tasklists": [],
                "math": {"blocks": [], "inline": []},
                "footnotes": {"definitions": [], "references": []},
                "html_blocks": [],
                "html_inline": [],
            },
            mappings={
                "line_to_type": {},
                "line_to_section": {},
                "prose_lines": [],
                "code_lines": [],
                "code_blocks": [],
            },
        )
```

**Key points:**
- `extra="allow"` for discovery (will become `"forbid"` in Milestone B)
- Nested structure is `dict[str, Any]` - no nested models yet
- `empty()` uses plain dicts, not nested Pydantic models

> **⚠️ `empty()` IS A HELPER, NOT A BEHAVIORAL SPEC**
>
> `ParserOutput.empty()` is a **convenience factory** for tests and tools that need a valid
> empty document structure. It is **NOT** a requirement for parser behavior.
>
> **Binding rule:** We do NOT require `parse("")` to equal `ParserOutput.empty()`.
>
> - `empty()` provides a syntactically valid baseline with all required fields present
> - Tests may use `empty()` as a starting point, but must NOT assert `parse("") == empty()`
> - If `parse("")` produces different output, that is fine - the parser's behavior is authoritative
> - Do NOT change parser behavior just to make `parse("")` match `empty()`
>
> **Rationale:** The parser's actual behavior for empty input may include profile-specific
> defaults, metadata fields, or other legitimate variations. Forcing equality would require
> parser changes that break existing consumers.

#### Task A.3: Create Minimal Test

**File**: `tests/test_output_models_minimal.py`

```python
"""
Milestone A: Minimal schema validation test.

This test validates ONLY that:
1. ParserOutput can be constructed from real parser output
2. Top-level keys exist
3. extra="allow" captures any unexpected fields (for review)

NO nested model validation. That's Milestone B.
"""

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.output_models import ParserOutput


class TestMinimalSchemaValidation:
    """Milestone A: Top-level structure only."""

    def test_empty_constructs(self):
        """ParserOutput.empty() must construct without error."""
        result = ParserOutput.empty()
        assert result.schema_version == "parser-output@1.0.0"

    def test_empty_has_four_top_level_keys(self):
        """Empty output must have metadata, content, structure, mappings."""
        result = ParserOutput.empty()
        data = result.model_dump()
        assert "metadata" in data
        assert "content" in data
        assert "structure" in data
        assert "mappings" in data

    def test_real_parser_output_validates(self):
        """Real parser output must pass minimal validation."""
        md = "# Hello\n\nSome paragraph."
        parser = MarkdownParserCore(md, security_profile="permissive")
        raw = parser.parse()

        # This should NOT raise with extra="allow"
        validated = ParserOutput.model_validate(raw)
        assert validated.metadata is not None
        assert validated.content is not None
        assert validated.structure is not None
        assert validated.mappings is not None

    def test_discover_extra_fields(self):
        """
        Log any extra fields for review (not a failure).

        With extra="allow", Pydantic captures unexpected fields.
        This test logs them for manual review before Milestone B.
        """
        md = "# Test\n\n- item 1\n- item 2"
        parser = MarkdownParserCore(md, security_profile="permissive")
        raw = parser.parse()

        validated = ParserOutput.model_validate(raw)

        # With extra="allow", check if any extra fields were captured
        # (This is informational, not a failure)
        extra = validated.model_extra or {}
        if extra:
            print(f"EXTRA FIELDS DISCOVERED: {list(extra.keys())}")


class TestEarlyRAGSafety:
    """
    Milestone A: Early RAG-critical behavioral test.

    Even with dict[str, Any] nested types, we can validate RAG safety signals
    via dict access. This gives meaningful behavioral coverage BEFORE building
    full nested models or tooling.
    """

    def test_script_tag_detected_early(self):
        """
        Script tag MUST set has_script=True and has_dangerous_content=True.

        This is the most RAG-critical security signal. If this fails,
        something fundamental is broken - don't proceed to Milestone B.
        """
        md = "<script>alert('xss')</script>\n\nSome text."
        parser = MarkdownParserCore(md, security_profile="permissive")
        raw = parser.parse()

        # Validate via Pydantic (top-level only)
        validated = ParserOutput.model_validate(raw)

        # Access security via dict (nested models not yet typed)
        security = validated.metadata.get("security", {})
        stats = security.get("statistics", {})
        summary = security.get("summary", {})

        assert stats.get("has_script") is True, \
            "CRITICAL: Script tag not detected - RAG safety compromised"
        assert summary.get("has_dangerous_content") is True, \
            "CRITICAL: Dangerous content not flagged - RAG safety compromised"

    def test_safe_document_not_blocked(self):
        """
        Safe document MUST NOT be blocked for embedding.

        False positives here would block legitimate RAG content.
        """
        md = "# Hello\n\nThis is safe markdown with no dangerous content."
        parser = MarkdownParserCore(md, security_profile="permissive")
        raw = parser.parse()

        validated = ParserOutput.model_validate(raw)

        # Access embedding_blocked via dict (top-level metadata field)
        assert validated.metadata.get("embedding_blocked") in (None, False), \
            "Safe document should NOT be blocked for embedding"

    def test_javascript_link_detected_and_disallowed(self):
        """
        javascript: links MUST be detected and marked disallowed.

        This is a classic XSS vector that must not reach RAG embeddings.
        """
        md = "Click [here](javascript:alert('xss')) for surprise."
        parser = MarkdownParserCore(md, security_profile="permissive")
        raw = parser.parse()

        validated = ParserOutput.model_validate(raw)

        # Access security stats via dict
        security = validated.metadata.get("security", {})
        stats = security.get("statistics", {})

        # javascript: should be in disallowed schemes or trigger warning
        link_schemes = stats.get("link_schemes", {})
        disallowed = security.get("disallowed_link_schemes", stats.get("disallowed_link_schemes", {}))

        # Either javascript is in disallowed schemes, or raw_dangerous_schemes is True
        has_dangerous = (
            "javascript" in disallowed or
            stats.get("raw_dangerous_schemes") is True or
            any(w.get("scheme") == "javascript" for w in security.get("warnings", []))
        )
        assert has_dangerous, \
            "CRITICAL: javascript: link not flagged - RAG safety compromised"
```

#### Milestone A Completion Checklist

- [x] `uv add "pydantic>=2,<3"` executed
- [x] `src/doxstrux/markdown/output_models.py` created with minimal schema
- [x] `tests/test_output_models_minimal.py` passes (both classes)
- [x] `ParserOutput.model_validate(parser.parse())` works on at least 5 sample files
- [x] **RAG safety tests pass**: `test_script_tag_detected_early`, `test_safe_document_not_blocked`, `test_javascript_link_detected_and_disallowed`
- [x] Any extra fields logged for review (will be addressed in Milestone B)

**EXIT CRITERIA:** Proceed to Milestone B when tests pass. Do NOT add nested models yet.

---

> ## 🛑 STOP HERE - Milestone A First
>
> **Do NOT read or implement Milestones B, C, D until Milestone A is complete and verified.**
>
> The content below describes future milestones. Implementing them prematurely will:
> - Create unnecessary complexity before validating basic shape
> - Risk building on unverified assumptions
> - Waste effort if Milestone A reveals schema issues
>
> **Complete Milestone A. Verify tests pass. Then proceed.**

---

### Milestone B1: Metadata + Security Models (Incremental)

**Goal:** Add nested models for Metadata and Security ONLY. Leave Structure/Mappings as `dict[str, Any]`.
**Scope:**
- Add models: `Metadata`, `Security`, `SecurityStatistics`, `SecuritySummary`, `SecurityWarning`, `Encoding`
- Set `extra="forbid"` on NEW typed models (NOT on DoxBaseModel - that stays "allow" until B1.5)
- Schema export tool (partial schema)
- Spot-check validation on 5 files
**Blocking:** Milestone A must be complete.
**Estimated effort:** 1 focused session

> **Why incremental:** Typing all 25+ models in one milestone is too big. Start with Metadata
> and Security because RAG safety tests depend on these fields. Structure/Mappings can remain
> `dict[str, Any]` until B1.5.
>
> **B1 is Metadata/Security focused.** Structure comes in B1.5. Tooling comes in B2.

#### Task B1.0: Add Metadata + Security Models

Expand `output_models.py` to include nested models for Metadata and Security only:

**B1 models (must add):**
- `Metadata` (typed fields: `total_lines`, `total_chars`, `has_*` booleans, `node_counts`, `security`)
- `Security`, `SecurityStatistics`, `SecuritySummary`, `SecurityWarning`
- `Encoding` (optional field in Metadata)

**B1 unchanged (remain dict[str, Any]):**
- `content: dict[str, Any]` - still untyped
- `structure: dict[str, Any]` - still untyped
- `mappings: dict[str, Any]` - still untyped

**Important:** Switch to `extra="forbid"` for the NEW typed models:
```python
class Metadata(DoxBaseModel):
    model_config = ConfigDict(extra="forbid")  # Enforce strict on typed models
    ...

# ParserOutput keeps Structure/Mappings as dict for now
class ParserOutput(DoxBaseModel):
    metadata: Metadata  # NOW typed
    content: dict[str, Any]  # Still untyped - B1.5
    structure: dict[str, Any]  # Still untyped - B1.5
    mappings: dict[str, Any]  # Still untyped - B1.5
```

---

### Milestone B1.5: Structure + Mappings Models (Domain Slices)

**Goal:** Add remaining nested models for Structure and Mappings in **incremental domain slices**.
**Blocking:** Milestone B1 must be complete.

> **Why slices?** The original B1.5 was too big ("1-2 focused sessions" but 15+ models). Breaking
> into domain slices ensures each is achievable in ~30-60 minutes with clear tests.

---

#### B1.5a: Content + Mappings (Simple Models)

**Models:** `Content`, `Mappings`, `MappingCodeBlock`
**Estimated effort:** 30 minutes

```python
class Content(DoxBaseModel):
    raw: str
    lines: list[str]

class MappingCodeBlock(DoxBaseModel):
    start_line: int
    end_line: int
    language: str | None = None

class Mappings(DoxBaseModel):
    line_to_type: dict[str, str]
    line_to_section: dict[str, str]
    prose_lines: list[int]
    code_lines: list[int]
    code_blocks: list[MappingCodeBlock]
```

**Tests:** Validate on 3 fixtures with code blocks.
**Done when:** `ParserOutput.model_validate()` passes with typed `content` and `mappings`.

---

#### B1.5b: Sections + Headings + Paragraphs

**Models:** `Section`, `Heading`, `Paragraph`
**Estimated effort:** 45 minutes

**Tests:** Validate on 3 fixtures with headings and sections.
**Done when:** Structure has typed `sections`, `headings`, `paragraphs`.

---

#### B1.5c: Lists + Tasklists

**Models:** `List`, `ListItem`, `Tasklist`, `TasklistItem`, `BlockRef`
**Estimated effort:** 45 minutes

**Note:** `ListItem` and `TasklistItem` have recursive `children` - use `model_rebuild()`.

**Tests:** Validate on 3 fixtures with nested lists.
**Done when:** Structure has typed `lists`, `tasklists`.

---

#### B1.5d: Tables + Code Blocks + Blockquotes

**Models:** `Table`, `CodeBlock`, `Blockquote`, `BlockquoteChildrenSummary`
**Estimated effort:** 45 minutes

**Tests:** Validate on 3 fixtures with tables and code.
**Done when:** Structure has typed `tables`, `code_blocks`, `blockquotes`.

---

#### B1.5e: Links + Images + Math + Footnotes + HTML

**Models:**
- `Link` (discriminated union: `RegularLink | ImageLink`)
- `Image`
- `Math`, `MathBlock`, `MathInline`
- `Footnotes`, `FootnoteDefinition`, `FootnoteReference`
- `HtmlBlock`, `HtmlInline`

**Estimated effort:** 60 minutes (most complex slice)

**Note:** `Link` uses discriminated union - test with both link types.

**Tests:** Validate on 5 fixtures covering links, images, math, footnotes, HTML.
**Done when:** All Structure fields typed; `extra="forbid"` everywhere including DoxBaseModel.

---

#### B1.5 Completion Checklist

- [x] B1.5a: `Content`, `Mappings` typed and validated
- [x] B1.5b: `Section`, `Heading`, `Paragraph` typed and validated
- [x] B1.5c: `List`, `Tasklist` with recursive items typed and validated
- [x] B1.5d: `Table`, `CodeBlock`, `Blockquote` typed and validated
- [x] B1.5e: `Link`, `Image`, `Math`, `Footnotes`, `HTML` typed and validated
- [x] **DoxBaseModel switched to `extra="forbid"`** (enforcement branch ready for main)
- [x] `extra="forbid"` on ALL models (no more `dict[str, Any]`)
- [x] Full schema export works
- [x] **DocumentIR regression test passes** (see below)

#### B1.5f: DocumentIR Regression Test (REQUIRED)

**Purpose:** Ensure ParserOutput schema changes don't silently break DocumentIR construction.

**File:** `tests/test_document_ir_regression.py`

```python
"""
DocumentIR regression test - ensures ParserOutput → DocumentIR conversion still works.

This test MUST run after any ParserOutput schema change. If it fails, either:
1. The schema change broke ir.py's assumptions about ParserOutput structure
2. ir.py needs to be updated to handle the new schema

Do NOT suppress this test - fix the root cause.
"""

import pytest
from pathlib import Path

from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.ir import DocumentIR


# Representative fixtures covering different structure types
REGRESSION_FIXTURES = [
    "# Simple heading\n\nA paragraph.",
    "- item 1\n- item 2\n  - nested",
    "| col1 | col2 |\n|------|------|\n| a | b |",
    "```python\ncode\n```",
    "[link](https://example.com)\n\n![img](image.png)",
]


class TestDocumentIRRegression:
    """Verify DocumentIR still builds from ParserOutput."""

    @pytest.mark.parametrize("md_content", REGRESSION_FIXTURES)
    def test_ir_builds_without_error(self, md_content: str):
        """DocumentIR construction must not raise for valid parser output."""
        parser = MarkdownParserCore(md_content, security_profile="permissive")
        result = parser.parse()

        # This is the critical assertion - if this raises, schema broke IR
        ir = DocumentIR.from_parser_output(result)

        # Basic sanity checks
        assert ir is not None
        assert ir.schema_version == "md-ir@1.0.0"

    def test_heading_document_has_structure(self):
        """
        Semantic assertion: heading document must produce non-empty IR.

        This catches "IR builds but is silently empty" regressions.
        """
        md = "# Test Heading\n\nA paragraph of text."
        parser = MarkdownParserCore(md, security_profile="permissive")
        result = parser.parse()
        ir = DocumentIR.from_parser_output(result)

        # IR must have a root node with children (not silently empty)
        assert ir.root is not None, "IR root must not be None for non-empty document"
        assert len(ir.root.children) > 0, "IR must contain nodes for heading + paragraph"
```

**Success criteria:** All 5 fixtures build DocumentIR without exceptions; heading document has non-empty structure.

**EXIT CRITERIA:** All B1.5 slices complete. Proceed to B2.

> **⚠️ ARCHIVED:** `PYDANTIC_SCHEMA_proposal.md` is historical context only. Do NOT use it as
> normative input for model shapes. Models derive from code + fixtures; this plan + models are SSOT.

#### Task B.1: Schema Export Tool

**File**: `tools/export_schema.py`

```python
#!/usr/bin/env python3
"""Export JSON Schema from Pydantic models."""

import tools._bootstrap  # noqa: F401 - sets up sys.path

import json
from pathlib import Path

from doxstrux.markdown.output_models import ParserOutput


def main():
    schema = ParserOutput.model_json_schema()

    # Add metadata
    schema["$id"] = "https://doxstrux.dev/schemas/parser-output.schema.json"
    schema["title"] = "DoxstruxParserOutput"
    schema["description"] = "JSON Schema for MarkdownParserCore.parse() output"

    output_path = Path("schemas/parser_output.schema.json")
    output_path.parent.mkdir(exist_ok=True)
    # sort_keys=True required for deterministic output (CI git diff)
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")

    print(f"Schema exported to {output_path}")

    # Verify round-trip
    generated = ParserOutput.model_json_schema()
    assert schema.get("properties") == generated.get("properties"), "Schema drift detected!"
    print("Schema verification passed")


if __name__ == "__main__":
    main()
```

#### Milestone B1 Completion Checklist

- [x] `Metadata`, `Security`, `SecurityStatistics`, `SecuritySummary`, `SecurityWarning`, `Encoding` models added
- [x] `extra="forbid"` on Metadata and Security models
- [x] `tools/export_schema.py` created (partial schema - Structure/Mappings still dict)
- [x] Spot-check: `ParserOutput.model_validate()` passes on 5 diverse fixture files
- [x] RAG safety tests still pass (script detection, safe doc, javascript: links)

**EXIT CRITERIA:** Metadata/Security typed and validated. Proceed to B1.5.

---

#### Milestone B1.5 Completion Checklist

- [x] All remaining models added (`Content`, `Structure`, `Mappings`, and sub-models)
- [x] `extra="forbid"` on ALL models (no more `dict[str, Any]` at top level)
- [x] Schema export now covers full structure
- [x] Spot-check: `ParserOutput.model_validate()` passes on 10+ diverse fixture files
- [x] **DocumentIR regression test passes** (B1.5f)

**EXIT CRITERIA:** Full schema typed and validated. Proceed to B2.

---

### Milestone B2: Validation Tools

**Goal:** Build curated fixture validation and regeneration tools.
**Scope:** Two tools only - `validate_curated_fixtures.py` and `regenerate_fixtures.py`
**Blocking:** Milestone B1 must be complete.

> **B2 is tool-only.** Deferred Phase 0.3/0.4 checks run automatically in pytest - they don't need a separate milestone.

#### Task B2.1: Curated Fixture Discovery (Pattern-Based)

> **SSOT Principle:** Do NOT maintain a hand-coded list of fixture paths.
> Use patterns to discover fixtures at runtime.

**Strategy:** Discover fixtures using glob patterns. This ensures the curated list
stays in sync with the filesystem automatically.

**Curated patterns (not paths):**

```python
# Fixture discovery patterns - NO hard-coded paths
CURATED_PATTERNS = [
    # One representative from each major directory
    "tools/test_mds/**/*basic*.md",      # All "basic" fixtures
    "tools/test_mds/**/*simple*.md",     # All "simple" fixtures
    "tools/test_mds/**/empty*.md",       # All "empty" fixtures
    # Add patterns as needed - they auto-discover new fixtures
]
```

#### Task B2.2: Curated Validation Tool (Pattern-Based)

**File**: `tools/validate_curated_fixtures.py`

**Purpose:** Validate curated fixture subset against Pydantic schema using glob patterns.

**Key functions:**
```python
def discover_curated_fixtures() -> list[Path]: ...
def validate_fixture(json_path: Path) -> tuple[bool, str]: ...
def main(): ...
```

**Key invariants:**
- Uses `CURATED_PATTERNS` glob patterns (NO hand-maintained path lists)
- Caps at `MAX_CURATED = 50` for fast validation
- Validates via `ParserOutput.model_validate(data)`
- Exit code 1 on any failure

> **Implementation:** Create `tools/validate_curated_fixtures.py` when implementing B2.

#### Task B2.3: Fixture Regeneration (Bucket-Aware)

**File**: `tools/regenerate_fixtures.py`

**Purpose:** Regenerate fixtures with bucket-aware classification and optional human review.

**Usage:**
```bash
.venv/bin/python tools/regenerate_fixtures.py --bucket structural
.venv/bin/python tools/regenerate_fixtures.py --bucket security --review
.venv/bin/python tools/regenerate_fixtures.py --curated
```

**Key functions:**
```python
def classify_fixture(path: Path) -> str: ...      # Returns "structural" | "security" | "legacy"
def discover_curated_fixtures() -> list[Path]: ...
def regenerate_fixture(md_path, json_path, bucket, review) -> bool: ...
```

**Bucket classification rules:**
- `security`: path contains "security", "injection", "xss", "script_tag", or `_sec_`/`sec_` prefix
- `legacy`: path contains "additional_test_mds" or "claude_tests"
- `structural`: everything else (default)

**Key invariants:**
- Uses same `CURATED_PATTERNS` as `validate_curated_fixtures.py`
- Security bucket with `--review` requires human confirmation
- Validates via `ParserOutput.model_validate()` before writing

> **Implementation:** Create `tools/regenerate_fixtures.py` when implementing B2.

#### Milestone B2 Completion Checklist

- [x] `tools/validate_curated_fixtures.py` passes (pattern-based discovery)
- [x] `tools/regenerate_fixtures.py` created with bucket-aware classification
- [x] NO hand-maintained fixture lists (patterns only)
- [x] **Legacy field audit completed** (B2.4)
- [x] **Legacy field audit test passes** (B2.5 - enforced by code)

#### B2.4: Legacy Field Audit (REQUIRED before fixture regeneration)

**Purpose:** Ensure no runtime code depends on fields being removed.

**Audit procedure:**
```bash
# For each legacy field identified during regeneration:
rg "exception_was_raised" src/  # Adjust field name as needed

# Expected result: Only matches in tests/ or fixtures/
# If matches in src/doxstrux/: DO NOT remove field, deprecate instead
```

**Legacy fields to audit:**
- `exception_was_raised` - should not exist in parser output
- Any field flagged during fixture regeneration that causes validation failure

**If runtime usage found:**
1. Do NOT drop the field immediately
2. Add deprecation warning to parser output
3. Create tracking issue for removal in next major version
4. Proceed with Milestone B2 using the legacy field (don't block)

#### B2.5: Legacy Field Audit Test (ENFORCED)

**Purpose:** Make the audit enforceable by code, not just prose.

**File:** `tests/test_no_legacy_field_runtime_usage.py`

```python
"""
Enforces legacy field audit - fails if runtime code uses deprecated fields.

This test ensures we don't accidentally drop fields that runtime code depends on.
If this test fails, DO NOT delete the field - deprecate it instead.
"""

import subprocess
import pytest

# Fields scheduled for removal - add here before dropping from schema
LEGACY_FIELDS_TO_AUDIT = [
    "exception_was_raised",
    # Add more as identified during fixture regeneration
]


class TestLegacyFieldAudit:
    """Enforce legacy field audit via code, not just prose."""

    @pytest.mark.parametrize("field_name", LEGACY_FIELDS_TO_AUDIT)
    def test_no_runtime_usage_of_legacy_field(self, field_name: str):
        """
        Legacy field must not be used in runtime code (src/doxstrux/).

        If this fails:
        1. DO NOT remove the field from schema
        2. Deprecate with warning instead
        3. Create tracking issue for future removal
        """
        result = subprocess.run(
            ["rg", "-l", field_name, "src/doxstrux/"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:  # Matches found
            files = result.stdout.strip().split("\n")
            pytest.fail(
                f"AUDIT FAILURE: '{field_name}' found in runtime code:\n"
                f"  {chr(10).join(files)}\n\n"
                f"DO NOT drop this field. Deprecate it instead."
            )
        # returncode == 1 means no matches (safe to drop)
        # returncode == 2 means rg error (test should fail for investigation)
        assert result.returncode in (0, 1), f"rg failed: {result.stderr}"
```

**How it works:**
- Add field names to `LEGACY_FIELDS_TO_AUDIT` before dropping them
- Test runs `rg` and fails if field is found in `src/doxstrux/`
- Test passes only when field has no runtime usage (safe to drop)

**EXIT CRITERIA:** Curated fixtures validate. Proceed to Milestone C.

---

### Milestone C: Full Validation (Report-Only)

**Goal:** Validate ALL fixtures (620+) without failing CI.
**Scope:** Full validation with report-only mode for monitoring.
**Blocking:** Milestone B must be complete.

#### Task C.1: Full Validation Tool (Report-Only Mode)

**File**: `tools/validate_test_pairs.py`

**Purpose:** Validate ALL test pair JSON files against Pydantic schema with configurable exit modes.

**Usage:**
```bash
.venv/bin/python tools/validate_test_pairs.py              # Fail on errors
.venv/bin/python tools/validate_test_pairs.py --report     # Report only (exit 0)
.venv/bin/python tools/validate_test_pairs.py --threshold 95  # Pass if >=95% valid
```

**Key functions:**
```python
def validate_directory(dir_path: Path) -> tuple[int, list[tuple[str, str]]]: ...
def main(): ...  # --report, --threshold, --output args
```

**Key invariants:**
- Validates via `ParserOutput.model_validate(data)`
- `--report` mode always exits 0 (for monitoring)
- `--threshold` enables gradual rollout (default: 100%)
- `--output` writes JSON report with failures

> **Implementation:** Create `tools/validate_test_pairs.py` when implementing C.

#### Task C.2: CI Integration Tests (Non-Blocking)

**IMPORTANT:** During Milestone C, schema validation tests run but DO NOT block CI.
Use pytest markers to control this.

**File**: `tests/test_output_models_empty.py`

**Purpose:** Test `ParserOutput.empty()` baseline - the canonical empty document shape.

**Test class:** `TestEmptyBaseline`

**Tests to implement:**
- `test_empty_returns_parser_output_instance` - validates instance type
- `test_empty_has_all_top_level_keys` - {metadata, content, structure, mappings, schema_version}
- `test_empty_content_is_empty` - raw="", lines=[]
- `test_empty_metadata_has_zero_counts` - all counts 0, all has_* False
- `test_empty_has_no_security_warnings` - warnings=[], has_dangerous_content=False
- `test_empty_has_no_dangerous_flags` - has_script, has_html_*, has_event_handlers all False
- `test_empty_embedding_not_blocked` - embedding_blocked=False
- `test_empty_not_quarantined` - quarantined=False
- `test_empty_structure_is_empty` - all lists empty
- `test_empty_mappings_is_empty` - all dicts/lists empty

> **NOTE:** These tests validate `ParserOutput.empty()` as a helper factory, NOT as a behavioral
> spec for parser output. Do NOT add `test_parse_empty_string_equals_empty()` - see the
> `empty()` IS A HELPER binding rule in Task A.2.

> **Implementation:** Create `tests/test_output_models_empty.py` when implementing C.

#### Task C.3: Schema Conformance Tests (Report-Only)

**File**: `tests/test_parser_output_schema_conformance.py`

**Purpose:** CONTRACT tests - validate parser output conforms to Pydantic schema.

**Test classes to implement:**

1. **`TestParserOutputSchemaConformance`** - validates against all sample files
   - `test_parser_output_conforms_to_schema(all_sample_files)` - validates ALL fixtures
   - `test_schema_has_expected_top_level_properties` - metadata, content, structure, mappings

2. **`TestSecuritySemantics`** - behavioral security tests
   - `test_script_tag_detected` - `<script>` → `has_script=True`
   - `test_safe_document_is_safe` - safe markdown → no warnings
   - `test_event_handler_detected` - `onclick` → `has_event_handlers=True`
   - `test_data_uri_image_detected` - `data:` URI → `has_data_uri_images=True`

3. **`TestLinkDiscriminatedUnion`** - tests RegularLink | ImageLink union
   - `test_regular_link_validates` - hyperlink → type in (relative, absolute)
   - `test_image_link_validates` - image → type='image', has src/alt
   - `test_mixed_links_validate` - both types coexist

4. **`TestMathExtraction`** - MathBlock/MathInline
   - `test_inline_math_validates` - `$...$` → MathInline
   - `test_block_math_validates` - `$$...$$` → MathBlock
   - `test_math_always_present` - math structure never None

5. **`TestFootnoteExtraction`** - FootnoteDefinition/FootnoteReference (PERMISSIVE ONLY)
   - `test_footnote_definition_validates` - `[^1]:` → definition with label
   - `test_footnote_reference_validates` - `[^note]` → reference with label
   - `test_footnotes_present_under_permissive` - footnotes key exists (permissive profile)
   - **NOTE**: `structure.footnotes` is ABSENT under strict profile (footnote plugin disabled)

> **Implementation:** Create `tests/test_parser_output_schema_conformance.py` when implementing C.

#### Milestone C Completion Checklist

- [x] `tools/validate_test_pairs.py` created with `--report` mode
- [x] All fixtures run through validation in report-only mode
- [x] JSON report generated with failure inventory
- [x] Known failures triaged into: schema fix, parser fix, or legacy
- [x] Report-only CI job runs on every PR (informational)

---

### Milestone D: CI Gate

**Goal:** Make schema validation a blocking CI gate.
**Scope:** Schema violations fail the build. No exceptions.
**Blocking:** Milestone C must show ≥95% pass rate before enabling.

#### Task D.1: Version-Bump CI Check

**File**: `.github/workflows/schema_validation.yml` (or add to existing CI)

```yaml
name: Schema Validation

on: [push, pull_request]

jobs:
  schema-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync

      # Validate schema version matches expectations
      - name: Check schema version
        run: |
          .venv/bin/python -c "
          from doxstrux.markdown.output_models import ParserOutput
          version = ParserOutput.model_fields['schema_version'].default
          expected = 'parser-output@1.0.0'
          assert version == expected, f'Schema version {version} != {expected}'
          print(f'✓ Schema version: {version}')
          "

      # Validate all fixtures (blocking)
      - name: Validate fixtures
        run: .venv/bin/python tools/validate_test_pairs.py --threshold 100

      # Export schema and verify no drift
      # NOTE: export_schema.py MUST use json.dumps(sort_keys=True) for deterministic output
      - name: Export and verify schema
        run: |
          .venv/bin/python tools/export_schema.py
          git diff --exit-code schemas/parser_output.schema.json || \
            (echo "Schema drift detected! Regenerate with: .venv/bin/python tools/export_schema.py" && exit 1)
```

#### Task D.2: Version Bump Enforcement

**File**: `tests/test_schema_version.py`

```python
"""
Test that schema version is properly maintained.

This test ensures:
1. Schema version exists and is well-formed
2. Version matches expected format
3. Version is incremented when schema changes
"""

import re

import pytest
from doxstrux.markdown.output_models import ParserOutput


class TestSchemaVersion:
    """Schema version enforcement tests."""

    def test_schema_version_exists(self):
        """ParserOutput must have schema_version field."""
        assert hasattr(ParserOutput, "model_fields")
        assert "schema_version" in ParserOutput.model_fields

    def test_schema_version_format(self):
        """Schema version must match expected format."""
        version = ParserOutput.model_fields["schema_version"].default
        # Format: parser-output@X.Y.Z
        pattern = r"^parser-output@\d+\.\d+\.\d+$"
        assert re.match(pattern, version), f"Invalid version format: {version}"

    def test_schema_version_not_dev(self):
        """Schema version must not contain dev/alpha/beta markers in main."""
        version = ParserOutput.model_fields["schema_version"].default
        assert "-dev" not in version
        assert "-alpha" not in version
        assert "-beta" not in version

    def test_empty_has_same_version(self):
        """ParserOutput.empty() must have same schema_version."""
        empty = ParserOutput.empty()
        expected = ParserOutput.model_fields["schema_version"].default
        assert empty.schema_version == expected
```

#### Task D.3: Pre-Commit Hook (Optional)

**File**: `.pre-commit-config.yaml` (add to existing)

```yaml
repos:
  - repo: local
    hooks:
      - id: schema-validation
        name: Validate Parser Schema
        entry: .venv/bin/python tools/validate_curated_fixtures.py
        language: system
        pass_filenames: false
        files: ^src/doxstrux/markdown/.*\.py$|^tools/test_mds/.*\.json$
```

#### Milestone D Completion Checklist

- [x] CI job created with 100% threshold (blocking)
- [x] Schema version test passes
- [x] Schema drift detection works (git diff check)
- [x] Pre-commit hook installed (optional but recommended)
- [x] All existing fixtures pass validation

---

### Milestone Summary

| Milestone | Goal | Blocking? | Pass Rate |
|-----------|------|-----------|-----------|
| A | Minimal schema + RAG safety semantics | No | N/A |
| B1 | Metadata + Security models | No | Spot-check |
| B1.5 | Structure + Mappings models | No | Spot-check |
| B2 | Curated fixture validation | No | 100% of curated |
| C | Full validation (report-only) | No | Informational |
| D | CI Gate | **Yes** | **100%** |

**Progression:**
1. Complete milestones in order (A → B1 → B1.5 → B2 → C → D)
2. Do not enable CI blocking (D) until C shows ≥95% pass rate
3. Each milestone has independent success criteria

---

## Test Coverage Matrix

> **⚠️ DIAGNOSTIC ONLY**: This is a coarse snapshot for planning. Consult `tests/test_*.py`
> for ground truth. Do NOT rely on this table being current.

| Category | Schema | Behavior | Notes |
|----------|--------|----------|-------|
| **Structure (core)** | ✅ | ❌ | Sections, paragraphs, lists, tables, code, headings, images, blockquotes, HTML |
| **Structure (plugin)** | ✅ | ✅ | Math, footnotes - always present under permissive; behavioral tests exist |
| **Links** | ✅ | ✅ | Discriminated union (RegularLink/ImageLink) tested |
| **Security (core)** | ✅ | ✅ | XSS, onclick, data URI, javascript: link detection tested |
| **Security (extended)** | ✅ | ❌ | Prompt injection, BiDi - **reserved, not behaviorally tested** |
| **Empty baseline** | ✅ | ✅ | `ParserOutput.empty()` shape and defaults |

**Legend:** ✅ = Tested | ❌ = Shape only (not behavior)

**Important:** Extended security fields (prompt injection, BiDi controls, confusable chars) are **reserved**
and **not behaviorally tested**. Do not build downstream logic on them until tests exist.

---

## Execution Summary

Follow the milestones in order: **Phase 0 → A → B1 → B1.5 → B2 → C → D**

### Quick Reference

| Phase/Milestone | Action | Command |
|-----------------|--------|---------|
| Phase 0 | Discover actual parser shape | `.venv/bin/python tools/discover_parser_shape.py` |
| Milestone A | Create minimal Pydantic models + RAG tests | `uv add "pydantic>=2,<3"` then create `output_models.py` |
| Milestone B1 | Add Metadata/Security models | Add models to `output_models.py`, run spot-checks |
| Milestone B1.5 | Add Structure/Mappings models | Add remaining models, `.venv/bin/python tools/export_schema.py` |
| Milestone B2 | Curated fixture validation + tools | `.venv/bin/python tools/validate_curated_fixtures.py` |
| Milestone C | Full validation (report) | `.venv/bin/python tools/validate_test_pairs.py --report` |
| Milestone D | Enable CI gate | Add to `.github/workflows/` |

### Alignment Strategy (BINDING)

**Two-phase approach:**

| Phase | `extra=` | Purpose |
|-------|----------|---------|
| **Milestone A** | `"allow"` | Discovery: capture unexpected fields without failing |
| **Milestone B+** | `"forbid"` | Enforcement: unknown fields cause immediate failure |

**Milestone A (Discovery):**
- `extra="allow"` lets Pydantic capture unexpected fields in `model_extra`
- Run validation on sample files; log any extra fields discovered
- This is NOT production-ready - it's a diagnostic phase

**Milestone B+ (Enforcement):**
- Switch to `extra="forbid"` - unknown fields cause validation error
- This is the production target

**Alignment workflow** (when `extra="forbid"` fails):

1. Do NOT regress to `extra="allow"` - that's Milestone A only
2. Instead: identify the unexpected field, then either:
   - Add it to the schema (if it's a legitimate parser output), OR
   - Fix the parser to not emit it (if it's a bug)
3. Iterate until validation passes with `extra="forbid"`

The schema conforms to documented parser output. If validation fails, the cause is either:
- A schema bug (fix the schema)
- A parser bug (fix the parser)
- A fixture bug (regenerate the fixture)

### Branching Policy

| Branch | DoxBaseModel `extra=` | Milestones | Notes |
|--------|----------------------|------------|-------|
| `feature/pydantic-schema` | `"allow"` | Phase 0, A | Discovery branch - never merged to main |
| `feature/pydantic-schema-enforce` | `"allow"` → `"forbid"` | B1, B1.5, B2 | B1: typed models get "forbid", DoxBaseModel stays "allow"; B1.5: DoxBaseModel switches to "forbid" |
| `main` | `"forbid"` | C, D | Production - only `extra="forbid"` allowed |

**Branching workflow:**

1. **Milestone A** is implemented on a feature branch (`feature/pydantic-schema`)
2. Once Milestone A passes, create a new branch (`feature/pydantic-schema-enforce`)
3. **B1**: Add typed models with `extra="forbid"` (DoxBaseModel stays "allow")
4. **B1.5**: Switch DoxBaseModel itself to `extra="forbid"`
5. Complete B2 on the enforcement branch
6. **Only merge to main** when `extra="forbid"` is stable and passing
7. Milestones C and D run on main

**Main branch rule:** `extra="forbid"` only. The `extra="allow"` mode is strictly for
Milestone A discovery; it must not reach main.

### CI Guard for Branching Policy (REQUIRED on main)

> **Don't trust prose - enforce with code.** Add this test to prevent accidental merge
> of `extra="allow"` to main.

**File:** `tests/test_schema_extra_forbid.py`

```python
"""
CI guard: Ensure DoxBaseModel.extra == "forbid" on main branch.

This test MUST run on main and fail if extra="allow" is accidentally merged.
"""

import os
import pytest

# Only enforce on main/master branches or CI
ENFORCE_BRANCHES = {"main", "master", "refs/heads/main", "refs/heads/master"}


def get_current_branch() -> str:
    """Get current git branch or CI ref."""
    # GitHub Actions
    if ref := os.environ.get("GITHUB_REF"):
        return ref
    # GitLab CI
    if branch := os.environ.get("CI_COMMIT_BRANCH"):
        return branch
    # Local git
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


@pytest.mark.skipif(
    get_current_branch() not in ENFORCE_BRANCHES and "CI" not in os.environ,
    reason="Only enforced on main branch or in CI"
)
def test_doxbasemodel_extra_is_forbid():
    """
    CRITICAL: DoxBaseModel must use extra='forbid' on main.

    If this fails, someone merged Milestone A (discovery mode) to main.
    Revert and complete Milestone B first.
    """
    from doxstrux.markdown.output_models import DoxBaseModel

    extra_setting = DoxBaseModel.model_config.get("extra")
    assert extra_setting == "forbid", (
        f"CRITICAL: DoxBaseModel.extra = '{extra_setting}' but must be 'forbid' on main. "
        "Did Milestone A (discovery mode) get merged prematurely? "
        "Revert and complete Milestone B1+ before merging to main."
    )
```

**Why code, not policy:** A paragraph in a doc is easily forgotten. A failing CI test is not.

---

## Fixture Classification Policy

**Do NOT regenerate all 620+ fixtures blindly.** Classify using mechanical rules below.

### Mechanical Bucketing Rules (Path-Based)

Bucket assignment is determined by file path - no tribal knowledge required.

> **Canonical implementation:** See `classify_fixture()` in Task B2.3 (`tools/regenerate_fixtures.py`).
> The function classifies fixtures into three buckets based on path patterns:
> - **security**: Path contains `security`, `injection`, `xss`, `script_tag`, or filename has `_sec_`/`sec_` prefix
> - **legacy**: Path contains `additional_test_mds` or `claude_tests`
> - **structural**: Everything else (default)

### Content-Based Safety Heuristic (Secondary Check)

**Problem:** Path-based bucketing can miss security-sensitive fixtures in "structural" directories.
A file named `basic_paragraph.md` in `01_edge_cases/` can contain `<script>` tags as edge case content.

**Solution:** After path-based classification, run a content-based safety check on structural fixtures:

```python
DANGEROUS_CONTENT_PATTERNS = [
    "<script",       # Script tags
    "javascript:",   # javascript: URLs
    "data:image",    # Data URIs (may be oversized)
    "onload=",       # Event handlers
    "onclick=",      # Event handlers
    "onerror=",      # Event handlers
]

def needs_manual_review(md_path: Path, bucket: str) -> bool:
    """Check if a structural fixture contains security-sensitive content."""
    if bucket != "structural":
        return False  # Security bucket already requires review

    content = md_path.read_text(encoding="utf-8").lower()
    for pattern in DANGEROUS_CONTENT_PATTERNS:
        if pattern in content:
            return True  # Structural fixture with dangerous content = review
    return False
```

**Usage:** If `needs_manual_review()` returns True for a structural fixture, treat it as
security bucket (require diff review). This catches edge-case test files that test
security features but aren't in security directories.

### Bucket 1: Structural (Default)

**Rule:** Any fixture NOT matching security or legacy patterns, AND not flagged by content heuristic.

**Location:** `tools/test_mds/01_edge_cases/`, `tools/test_mds/02_*/`, and similar numbered directories.

**Strategy:**
- Regenerate wholesale using current parser + schema
- Run content-based safety check; if flagged, treat as security bucket
- Command: `tools/regenerate_fixtures.py --bucket structural`

### Bucket 2: Security

**Rule:** Path contains `security`, `injection`, `xss`, `script_tag`, or filename contains `_sec_` or starts with `sec_`.

**Location:** Files matching security patterns anywhere in `tools/test_mds/`

**Strategy:**
- Regenerate to get new canonical output
- **Manually review diffs** - did semantics change?
- Add/update behavioral tests for each
- Only commit after review + test coverage

### Bucket 3: Legacy

**Rule:** Path contains `additional_test_mds` or `claude_tests`.

**Location:** `tools/additional_test_mds/`, `tools/additional_test_mds/claude_tests/`

**Strategy:**
- Triage: is this part of the core contract?
- If yes: move to `tools/test_mds/` (structural or security), regenerate, add tests
- If no: either mark as non-blocking or remove from enforced test suite
- Don't let legacy fixtures block CI without conscious adoption

### Fixture Regeneration Command

> **Canonical implementation:** See Task B2.3 (`tools/regenerate_fixtures.py`) for the full
> implementation with bucket-aware classification, `--review` flag, and `--dry-run` support.
> Do NOT duplicate the implementation here - B2.3 is the SSOT.

## File Structure After All Milestones (B–D)

> **Note:** This shows the final state after completing all milestones. During Milestone A,
> tests live in `tests/test_output_models_minimal.py` (top-level validation only).
> The full test files below replace/extend that file in later milestones.

```
src/doxstrux/
├── markdown_parser_core.py          # Returns plain dicts (unchanged)
├── markdown/
│   ├── output_models.py             # NEW: Pydantic models (SSOT)
│   ├── extractors/                  # Unchanged
│   └── ...

schemas/
└── parser_output.schema.json        # Auto-generated from Pydantic (Milestone B+)

tools/
├── export_schema.py                 # NEW: Schema export tool (Milestone B)
├── validate_test_pairs.py           # NEW: Test pair validation (Milestone C)
├── regenerate_fixtures.py           # NEW: Fixture regeneration (Milestone B)
├── generate_parser_schema.py        # DEPRECATED (keep for reference)
└── ...

tests/
├── test_output_models_minimal.py    # Milestone A: Top-level + RAG safety tests
├── test_output_models_empty.py      # Milestone C: Full nested baseline tests
└── test_parser_output_schema_conformance.py  # Milestone C: CI schema + semantics tests
```

## Success Criteria

### Primary Success Metrics

1. **100% validation**: All parser outputs validate against Pydantic models
2. **100% test pairs valid**: All 620+ JSON test files pass validation
3. **CI gate**: Schema violations fail the build (Milestone D)
4. **Single source of truth**: Pydantic models define the contract, JSON Schema is derived
5. **Security semantics tested**: Script tags, event handlers, and dangerous URLs are correctly detected

### Escape Paths (When Things Go Wrong)

| Problem | Escape Path | NOT Allowed |
|---------|-------------|-------------|
| Unknown field in parser output | Add field to schema OR fix parser | Regress to `extra="allow"` |
| Fixture fails validation | Regenerate fixture OR fix schema | Skip fixture silently |
| CI blocking too early | Use `--threshold 95` temporarily | Disable CI job entirely |
| Schema version mismatch | Bump version in schema AND tests | Leave version unchanged |
| Legacy fixture incompatible | Move to legacy bucket, triage later | Delete without review |

### Rollback Criteria

If Milestone D (CI Gate) is enabled and causes problems:

1. **Immediate rollback**: Set `--threshold 95` instead of 100
2. **Investigation**: Generate JSON report with `--output report.json`
3. **Triage**: Classify failures into buckets (schema, parser, legacy)
4. **Fix forward**: Address root causes, don't weaken the gate
5. **Re-enable 100%**: Only after all failures resolved

### "Done" Definition Per Milestone

| Milestone | Done When |
|-----------|-----------|
| Phase 0 | `discover_parser_shape.py` runs; `all_keys.txt` reviewed; security fields verified in samples |
| A | `ParserOutput.empty()` constructs; 3 RAG safety tests pass; basic validation on 5+ files |
| B1 | Metadata/Security models added; `extra="forbid"` on those; `export_schema.py` works |
| B1.5 | All models added; `extra="forbid"` everywhere; full schema exports |
| B2 | `validate_curated_fixtures.py` 100% pass; deferred Phase 0.3-0.4 checks (plugin policy, embedding invariants) pass via Milestone B tests |
| C | `validate_test_pairs.py --report` runs without crash; pass rate logged |
| D | CI job blocks on validation failure + schema drift |

**Note:** Phase 0.2 (Key Path Lister) was deleted - it cannot handle discriminated unions.
Strict shape enforcement comes from `extra="forbid"` (Milestone B1+), not from counting unknown fields.

## Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing
    "pydantic>=2,<3",  # Pydantic v2 required for discriminated unions and model_config
]
```

**Version Policy**: `>=2,<3` ensures we get Pydantic v2 features (discriminated unions, ConfigDict) while avoiding breaking changes from a hypothetical Pydantic v3.

### External Tool Dependency (Tests)

**ripgrep (`rg`) is REQUIRED** for the legacy field audit test (`test_no_legacy_field_runtime_usage.py`).

```bash
# Ubuntu/Debian
sudo apt install ripgrep

# macOS
brew install ripgrep

# CI (GitHub Actions)
# ripgrep is pre-installed on ubuntu-latest runners
```

If `rg` is not installed, the test will fail with "rg failed" rather than silently passing.

## Known Opaque Types (Historical Notes - Move to Code)

> **⚠️ NON-NORMATIVE / HISTORICAL**: This section will be DELETED after Milestone B1.5.
> It exists only for planning reference. Once `output_models.py` exists, opaque types
> should be documented as comments in the model code, not here.
>
> **Do NOT treat this as SSOT.** The actual model definitions in code are SSOT.

**Intentionally opaque fields** (document as comments in models):
- `align_meta`, `is_ragged_meta` in `Table` - plugin-dependent metadata
- `frontmatter` in `Structure`/`Metadata` - user-defined YAML, inherently dynamic

**Historical design notes** (v1.1-v1.9 design evolution - for archive only):
- These details are now obsolete; models are derived from code, not this list
- Consult `output_models.py` for current field definitions

## Notes

- Parser core remains dict-based (no performance impact)
- Pydantic validation is opt-in (for tests and consumers who want it)
- JSON Schema is always in sync with models (auto-generated)
- Test pairs and parser output share the exact same schema
- Security failures = exceptions, NOT output fields like `exception_was_raised`
  - **Legacy note:** Any existing fixtures containing `exception_was_raised` are legacy and must be migrated or dropped during fixture regeneration (Milestone B2)
  - **⚠️ AUDIT REQUIRED:** Before dropping any legacy field, search for its usage in the repo:
    ```bash
    rg "exception_was_raised" src/  # Check runtime code, not just tests/fixtures
    ```
    If runtime code uses the field, deprecate with a transition period instead of instant removal.
    Only drop immediately if usage is confined to test fixtures.

## Module Relationships

This section documents how `ParserOutput` relates to other modules in `src/doxstrux/markdown/`.

### Not Part of ParserOutput Schema

| Module | Purpose | Why Not in Schema |
|--------|---------|-------------------|
| `budgets.py` | `NodeBudget`, `CellBudget`, `URIBudget` | Enforcement mechanisms - raise `MarkdownSizeError`, not output fields |
| `config.py` | `SECURITY_PROFILES`, `SECURITY_LIMITS`, `ALLOWED_PLUGINS` | Configuration constants - `profile_used` field references these |
| `exceptions.py` | `MarkdownSecurityError`, `MarkdownSizeError` | Exceptions are raised, not returned in output |
| `ir.py` | `DocumentIR`, `DocNode`, `Chunk`, `ChunkResult` | **Separate contract** for RAG chunking pipeline (schema: `md-ir@1.0.0`) |

### Utilities That Map to Schema Fields

| Utility | Schema Field | Notes |
|---------|--------------|-------|
| `utils/encoding.py:DecodeResult` | `Metadata.encoding: Encoding` | NamedTuple → Pydantic model |
| `utils/section_utils.py:SectionIndex` | `Structure.sections` | Lookup utility for sections list |
| `utils/line_utils.py` | `mappings.line_to_type`, `mappings.line_to_section` | Line slicing for mappings |

### DocumentIR vs ParserOutput

The codebase has **two distinct output schemas**:

1. **ParserOutput** (this document) - Direct parser output for validation and test pairs
   - Schema version: `parser-output@1.0.0` (via `schema_version` field)
   - Consumer: Test fixtures, validation, direct analysis

2. **DocumentIR** (`ir.py`) - Universal format for RAG chunking
   - Schema version: `md-ir@1.0.0`
   - Consumer: Chunker → Embedding pipelines
   - Converts `ParserOutput` → `DocumentIR` → `ChunkResult`

These are **separate contracts**. `DocumentIR` is not covered by this schema.

## Schema Change Log

> **⚠️ DESIGN HISTORY**: These entries describe the **design evolution** of this specification,
> NOT deployed schema migrations. Actual schema versioning only starts once `output_models.py`
> exists in the codebase.

### Two Version Numbers (Don't Confuse Them)

| Version Type | Format | What It Tracks | Where It Lives |
|--------------|--------|----------------|----------------|
| **Doc revision** | `v1.15` | This document's text edits, process changes, clarifications | This file's changelog |
| **Schema version** | `parser-output@1.0.0` | Actual JSON output shape changes | `ParserOutput.schema_version` field |

**Rules:**

1. **Doc revision** bumps on ANY edit to this file (process, clarification, wording)
2. **Schema version** bumps ONLY when the JSON output shape changes (new field, type change, removal)
3. These are INDEPENDENT - a doc edit does NOT require a schema version bump
4. Example: "Doc rev v1.15 – added branching CI guard (no schema_version change, still parser-output@1.0.0)"

### Changelog Cutover Rule

**Once `output_models.py` exists with `schema_version >= "parser-output@1.0.0"`:**

1. **Freeze this changelog** - no new entries here after cutover
2. Create `src/doxstrux/markdown/SCHEMA_CHANGELOG.md` for schema version changes
3. This file (`PYDANTIC_SCHEMA.md`) becomes historical/planning reference only
4. CI should verify that `schema_version` in code matches the latest code-adjacent changelog entry

**Why:** A spec file can drift from implementation. The only trustworthy changelog is
one that lives next to the schema code and is updated atomically with schema changes.

---

### Design History (Archived)

> **Full changelog archived.** Detailed entries for v1.0 through v1.15 (14 iterations)
> are preserved in git history. This document evolved through:
>
> - v1.0–v1.3: Initial schema, module alignment, link polymorphism
> - v1.4–v1.7: Alignment strategy, fixture policy, strict pass fixes
> - v1.8–v1.10: Full output policy, proposal alignment, milestone restructure
> - v1.11–v1.13: Strict pass fixes, SSOT cleanup, execution cleanup
> - v1.14–v1.15: Ultra-strict fixes, structural refactoring, code trimming
>
> **Key design decisions made:**
> - `extra="allow"` in Milestone A, `extra="forbid"` in Milestone B
> - Pattern-based fixture discovery (no hand-maintained path lists)
> - RAG safety tests locked in before schema expansion
> - Changelog cutover to `SCHEMA_CHANGELOG.md` after implementation
>
> See git history for full design rationale on any specific change.

---

## Checklist Before Submission

- [x] All placeholder tokens replaced with real values
- [x] No incomplete markers remain
- [x] No questions remain
- [x] All decisions in Decisions table are final
- [x] External Dependencies section lists all prerequisites
- [x] Required libraries match pyproject.toml requirements
- [x] Required tools have verification commands
- [x] All paths in File Manifest are specified
- [x] All test cases have concrete assertions
- [x] All success criteria are measurable
- [x] Dependencies between phases are explicit
- [x] Glossary defines project-specific terms

---

**End of Specification**
