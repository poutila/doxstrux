# SPEKSI Kernel Linter Specification

**Version**: 1.0.0
**Status**: DRAFT
**Tier**: FULL
**Kernel-Version**: 1.0
**Created**: 2025-11-29

> This specification defines the behavioral contract for kernel_linter.py,
> making the linter itself a first-class SPEKSI citizen subject to the
> governance it enforces.

---

## §0 META

### §0.1 Tier Declaration

This specification uses **FULL** tier (per R-STR-1).

### §0.2 Layer Mapping

| Section | Layer Type | Purpose |
|---------|------------|---------|
| §0 META | META | Governance for this spec |
| §1 DEFINITIONS | DEFINITIONS | Data structures and interfaces |
| §2 RULES | RULES | Linter behavioral constraints |
| §3 IMPLEMENTATION | IMPLEMENTATION | Validation phases |
| §4 TESTS | TESTS | Test specifications |
| §5 VALIDATION | VALIDATION | Verification checklists |
| §C CHANGELOG | CHANGELOG | Version history |
| §G GLOSSARY | GLOSSARY | Term definitions |

### §0.3 Frozen Layers

| Layer | Status | Unfreezing Requires |
|-------|--------|---------------------|
| §2 RULES | FROZEN | Major version bump + justification |
| §1 DEFINITIONS | FROZEN | Major version bump + justification |
| §0 META | OPEN | Minor version bump |
| §3-§5, §C, §G | OPEN | Patch version bump |

### §0.4 Linter Integration

This spec requires all three linters (per R-GOV-5):
- `spec_linter` → validates this spec's structure and governance (kernel + framework)
- `plan_linter` → validates any execution plan for this spec
- `consistency_linter` → validates spec↔plan alignment

**Implementation**: The kernel_linter.py (subject of this spec) implements the
Kernel portion of spec_linter. The framework_linter.py provides the Framework
portion plus plan_linter and consistency_linter modes.

---

## §1 DEFINITIONS

> Canonical data structures for the Kernel linter.

### §1.1 Input Schema

```python
@dataclass
class LintInput:
    """Input to kernel linter."""
    spec_path: Path
    # No mode parameter - kernel linter has single mode
```

### §1.2 Output Schema

```python
@dataclass
class LintError:
    """A single linting error."""
    line: int         # 1-based line number
    code: str         # Rule ID (e.g., "R-REF-1")
    message: str      # Human-readable description
    
    def format(self, path: Path) -> str:
        """Format for human consumption."""
        return f"{path}:{self.line}: [{self.code}] {self.message}"

@dataclass
class LintResult:
    """Output from kernel linter."""
    exit_code: int    # 0=pass, 1=fail, 2=usage error
    errors: List[LintError]
```

### §1.3 Section Schema

```python
@dataclass
class Section:
    """A parsed § section."""
    token: str              # e.g., "§1", "§2.3"
    title: str              # Full title after token
    level: int              # Heading level (# -> 1, ## -> 2, ...)
    start_line: int         # 1-based
    end_line: int           # 1-based, inclusive
    parent_idx: Optional[int]  # Index of parent section
    layer_type: Optional[str]  # Computed layer type
```

### §1.4 Pattern Constants

```python
# From SPEKSI Kernel §2 PATTERNS
RE_SECTION = re.compile(r"^(#+)\s+(§[0-9A-Z][0-9A-Z0-9.]*)(.*)$")
RE_RULE_ID = re.compile(r"\bR-([A-Z]+(?:-[A-Z]+)*)-(\d+)\b")
RE_INV_ID = re.compile(r"\bINV-([A-Za-z0-9_]+)\b")
RE_REF_SECTION = re.compile(r"→\s+(§[0-9A-Z][0-9A-Z0-9.]*)")
RE_REF_RULE = re.compile(r"\(per\s+(R-[A-Z]+(?:-[A-Z]+)*-\d+)\)")
RE_REF_INV = re.compile(r"\(see\s+(INV-[A-Za-z0-9_]+)\)")
RE_MUST_WORDS = re.compile(
    r"(?<![`\w-])\b(must|never|always|only)\b(?![\w-])", 
    re.IGNORECASE
)
RE_TIER_HEADER = re.compile(r"^Tier:\s*(\w+)", re.IGNORECASE)
RE_KERNEL_VERSION = re.compile(r"^\*?\*?Kernel-Version\*?\*?:\s*", re.IGNORECASE)

# Reserved Kernel namespaces
KERNEL_NAMESPACES = {"STR", "CNT", "REF", "CON", "PAT"}
```

### §1.5 Layer Type Recognition

Recognized layer types (per SPEKSI Kernel §1 LAYERS):

```python
LAYER_TYPES = {
    "META",
    "ARCHITECTURE", 
    "DEFINITIONS",
    "PRINCIPLES",
    "RULES",
    "INVARIANTS",  # Subsection of RULES
    "IMPLEMENTATION",
    "TESTS",
    "VALIDATION",
    "CHANGELOG",
    "GLOSSARY",
    "PATTERNS",
    "LAYERS",      # Kernel meta-section
    "TIERS",       # Framework
    "TEMPLATES",   # Framework
    "LINTERS",     # Framework
    "PLANS",       # Framework
    "GOVERNANCE",  # Framework
    "CONFIG",      # Framework
}
```

---

## §2 RULES

> Behavioral constraints for kernel linter operation.

### §2.1 Mandatory Section Checks

- MUST require `§5 FACTS-ONLY CONSTRAINTS` to exist (per Kernel §5).
- MUST fail if any governed section contains Markdown fences (facts-only, rules, invariants).
- MUST flag missing section numbering (per R-PAT-1).

### §2.2 Facts-Only Enforcement

- MUST parse §5 FACTS-ONLY CONSTRAINTS and flag:
  - Missing subsections (§5.1–§5.5).
  - Missing statements about no invention, anchoring, cross-references, and fence prohibition.
- MUST ensure any `must/never/always/only` in non-RULES layers are anchored (per R-CON-1).

### §2.3 Namespace Enforcement

- MUST reject new rule namespaces overlapping reserved Kernel namespaces (STR, CNT, REF, CON, PAT).
- MUST ensure all rule IDs are defined only in RULES/INVARIANTS (per R-CON-2).

### §2.4 Reference/Pattern Enforcement

- MUST ensure `→ §X.Y` references resolve (per R-REF-1).
- MUST ensure `(per R-XXX)` references resolve (per R-REF-2).
- MUST ensure numbering consistency (per R-PAT-1).

### §2.5 Fence-Free Constraint

- MUST fail if any fenced code block (``` or ```*) appears in governed sections (RULES, INVARIANTS, FACTS-ONLY).

### §2.6 Input Processing Rules

| Rule ID | Rule |
|---------|------|
| R-LINT-IN-1 | Linter must accept exactly one positional argument: path to spec file |
| R-LINT-IN-2 | Linter must validate file exists before processing |
| R-LINT-IN-3 | Linter must read file as UTF-8 text |

### §2.7 Parsing Rules

| Rule ID | Rule |
|---------|------|
| R-LINT-PARSE-1 | Linter must detect all § sections via `RE_SECTION` regex |
| R-LINT-PARSE-2 | Linter must compute section hierarchy based on heading level |
| R-LINT-PARSE-3 | Linter must infer layer types from section titles |
| R-LINT-PARSE-4 | Linter must inherit layer type from parent sections for subsections |
| R-LINT-PARSE-5 | Linter must detect Framework documents via `Kernel-Version:` header |

### §2.8 Rule Enforcement (Kernel Rules)

#### Structure Rules (R-STR-*)

| Rule ID | Rule | Implementation |
|---------|------|----------------|
| R-LINT-STR-1 | Linter must check tier declaration format via `check_tier_declared()` | If `Tier:` header found, value must be MINIMAL/STANDARD/FULL |
| R-LINT-STR-2 | Linter must not enforce tier-specific required layers | Framework territory |
| R-LINT-STR-3 | Linter must not enforce layer mapping | Framework territory |
| R-LINT-STR-4 | Linter must not enforce section numbering consistency | Not currently implemented |

#### Reference Rules (R-REF-*)

| Rule ID | Rule | Implementation |
|---------|------|----------------|
| R-LINT-REF-1 | Linter must check all `→ §X.Y` references resolve via `check_reference_integrity()` | Match against collected section tokens |
| R-LINT-REF-2 | Linter must check all rule `(per R-...)` and invariant `(see INV-...)` references resolve via `check_reference_integrity()` | Match against defined rule/invariant IDs |
| R-LINT-REF-3 | Linter must not flag circular references | Allowed per R-REF-3 |

#### Constraint Rules (R-CON-*)

| Rule ID | Rule | Implementation |
|---------|------|----------------|
| R-LINT-CON-1 | Linter must check normative language anchoring via `check_anchored_constraints()` | Detect `must/never/always/only` outside exempt layers |
| R-LINT-CON-2 | Linter must not enforce that rule IDs only appear in RULES layer | Content semantics beyond scope |

#### Pattern Rules (R-PAT-*)

| Rule ID | Rule | Implementation |
|---------|------|----------------|
| R-LINT-PAT-1 | Linter must not enforce section numbering consistency | Not implemented (should be R-STR-4) |
| R-LINT-PAT-2 | Linter must check rule ID uniqueness via `check_rule_and_invariant_ids()` | Detect duplicate R-* IDs within namespace |
| R-LINT-PAT-3 | Linter must check invariant ID uniqueness via `check_rule_and_invariant_ids()` | Detect duplicate INV-* IDs |
| R-LINT-PAT-4 | Linter must validate reference formats implicitly via regex patterns | RE_REF_SECTION, RE_REF_RULE, RE_REF_INV |

### §2.9 Exemption Rules

| Rule ID | Rule |
|---------|------|
| R-LINT-EX-1 | Linter must skip R-REF-1 validation for PATTERNS layer content | Pattern examples should not trigger false positives |
| R-LINT-EX-2 | Linter must skip R-REF-1 validation for references inside backticks | Code spans are examples |
| R-LINT-EX-3 | Linter must skip R-REF-2 validation for PATTERNS layer content | Rule ID examples should not require definitions |
| R-LINT-EX-4 | Linter must allow Framework documents to reference Kernel namespaces without local definitions | Kernel inheritance (per R-LINT-PARSE-5) |
| R-LINT-EX-5 | Linter must exempt normative language in RULES, PRINCIPLES, INVARIANTS layers from R-CON-1 | These layers define constraints |
| R-LINT-EX-6 | Linter must exempt normative language in GLOSSARY, DEFINITIONS, PATTERNS, LAYERS, TIERS, PLANS, LINTERS layers from R-CON-1 | Definitional/governance description layers |

### §2.10 Definition Detection Rules

| Rule ID | Rule |
|---------|------|
| R-LINT-DEF-1 | Linter must detect rule definitions from RULES-layer table rows matching `_is_table_definition_line_for_rule()` | Lines with `\| R-XXX-N \|` pattern |
| R-LINT-DEF-2 | Linter must detect invariant definitions from INVARIANTS subsection table rows | Lines with `\| INV-XXX \|` pattern |
| R-LINT-DEF-3 | Linter must treat all other R-*/INV-* occurrences as references | Non-definition occurrences |

### §2.11 Output Rules (per R-LNT-*)

| Rule ID | Rule |
|---------|------|
| R-LINT-OUT-1 | Linter must never crash; always return exit code (per R-LNT-1) | Catch exceptions, return exit code 2 |
| R-LINT-OUT-2 | Linter must provide human-readable diagnostics (per R-LNT-2) | `LintError.format()` for each error |
| R-LINT-OUT-3 | Linter must support `--json` for machine-readable output (per R-LNT-3) | Implemented via `--json` flag |
| R-LINT-OUT-4 | Linter must use exit codes: 0=pass, 1=fail, 2=usage error (per R-LNT-4) | Return from `lint_spec()` |

### §2.12 Performance Rules

| Rule ID | Rule |
|---------|------|
| R-LINT-PERF-1 | Linter must strip code blocks before most checks via `strip_code_blocks()` | Prevent false positives from code examples |
| R-LINT-PERF-2 | Linter must process specs in single pass where possible | Collect sections once, reuse |

---

## §3 IMPLEMENTATION

> Execution phases for kernel linter validation.

### §3.1 Phase 1: File Reading

**Spec References**: → §1.1 Input Schema, → §2.1 Input Processing Rules

**Tasks**:
- [ ] Read command-line argument via `sys.argv`
- [ ] Validate file path exists (per R-LINT-IN-2)
- [ ] Read file as UTF-8 text (per R-LINT-IN-3)
- [ ] Return exit code 2 if file not found

**Verification**:
```python
def test_file_reading():
    # Test file exists
    result = lint_spec(Path("test_spec.md"))
    assert result == 0 or result == 1  # Not usage error
    
    # Test file doesn't exist
    result = lint_spec(Path("nonexistent.md"))
    assert result == 2  # Usage error
```

### §3.2 Phase 2: Section Parsing

**Spec References**: → §1.3 Section Schema, → §2.2 Parsing Rules

**Tasks**:
- [ ] Parse all § headings via `collect_sections()` (per R-LINT-PARSE-1)
- [ ] Compute section hierarchy (per R-LINT-PARSE-2)
- [ ] Infer layer types from titles (per R-LINT-PARSE-3)
- [ ] Inherit layer types from parents (per R-LINT-PARSE-4)
- [ ] Detect Framework documents (per R-LINT-PARSE-5)

**Verification**:
```python
def test_section_parsing():
    spec = """
    ## §1 DEFINITIONS
    ### §1.1 Models
    ## §2 RULES
    """
    sections = collect_sections(spec)
    assert len(sections) == 3
    assert sections[0].token == "§1"
    assert sections[0].layer_type == "DEFINITIONS"
    assert sections[1].token == "§1.1"
    assert sections[1].layer_type == "DEFINITIONS"  # Inherited
    assert sections[1].parent_idx == 0
```

### §3.3 Phase 3: Rule Enforcement

**Spec References**: → §2.3 Rule Enforcement

**Tasks**:
- [ ] Check tier declaration (per R-LINT-STR-1)
- [ ] Check section references (per R-LINT-REF-1)
- [ ] Check rule/invariant references (per R-LINT-REF-2)
- [ ] Check normative language anchoring (per R-LINT-CON-1)
- [ ] Check rule ID uniqueness (per R-LINT-PAT-2)
- [ ] Check invariant ID uniqueness (per R-LINT-PAT-3)
- [ ] Apply exemptions (per R-LINT-EX-1 through R-LINT-EX-6)

**Verification**:
```python
def test_rule_enforcement():
    # Test R-REF-1
    spec = """
    ## §1 TEST
    Reference → §2 should fail.
    """
    errors = lint_spec_text(spec)
    assert any(e.code == "R-REF-1" for e in errors)
    
    # Test R-CON-1
    spec = """
    ## §1 DEFINITIONS
    Models must be validated.
    """
    errors = lint_spec_text(spec)
    assert any(e.code == "R-CON-1" for e in errors)
    
    # Test R-CON-1 with anchoring
    spec = """
    ## §1 DEFINITIONS
    Models must be validated (per R-VAL-1).
    """
    errors = lint_spec_text(spec)
    assert not any(e.code == "R-CON-1" for e in errors)
```

### §3.4 Phase 4: Output Generation

**Spec References**: → §1.2 Output Schema, → §2.6 Output Rules

**Tasks**:
- [ ] Collect all errors from checks
- [ ] Format errors for human consumption (per R-LINT-OUT-2)
- [ ] Return exit code 0/1/2 (per R-LINT-OUT-4)
- [ ] Never crash (per R-LINT-OUT-1)

**Verification**:
```python
def test_output_generation():
    spec = """
    ## §1 TEST
    Reference → §999 is broken.
    """
    # Should not crash
    exit_code = lint_spec_text(spec)
    assert exit_code == 1  # Fail, not crash
    
    # Valid spec should return 0
    spec = """
    ## §1 RULES
    | R-TEST-1 | Must do something |
    """
    exit_code = lint_spec_text(spec)
    assert exit_code == 0
```

---

## §4 TESTS

> Test specifications for kernel linter validation.

### §4.1 Regression Test Suite

| Test ID | Description | Expected Behavior |
|---------|-------------|-------------------|
| T-REF-1 | Broken section reference | Exit 1, error code R-REF-1 |
| T-REF-2 | Broken rule reference | Exit 1, error code R-REF-2 |
| T-REF-3 | Valid references | Exit 0, no errors |
| T-CON-1 | Unanchored normative language | Exit 1, error code R-CON-1 |
| T-CON-2 | Anchored normative language | Exit 0, no errors |
| T-CON-3 | Normative language in RULES | Exit 0, no errors |
| T-PAT-1 | Duplicate rule ID | Exit 1, error code R-PAT-2 |
| T-PAT-2 | Duplicate invariant ID | Exit 1, error code R-PAT-3 |
| T-EX-1 | Pattern examples in PATTERNS | Exit 0, no false positives |
| T-EX-2 | Code examples in backticks | Exit 0, no false positives |

### §4.2 Property-Based Tests

Optional (recommended). Hypothesis is not bundled with the package; if used, add it to dev
dependencies. These examples illustrate desired coverage patterns rather than a mandatory suite.

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_never_crashes(spec_text: str):
    """Linter must never crash on arbitrary input (per R-LINT-OUT-1)."""
    try:
        exit_code = lint_spec_text(spec_text)
        assert exit_code in {0, 1, 2}
    except Exception as e:
        pytest.fail(f"Linter crashed: {e}")

@given(st.lists(st.text(alphabet="§0123456789.", min_size=1, max_size=5)))
def test_section_references(section_tokens: List[str]):
    """Generated section tokens should validate correctly."""
    # Create spec with sections
    spec = "\n".join(f"## {token} TEST" for token in section_tokens)
    # Add references
    spec += "\n\n" + "\n".join(f"→ {token}" for token in section_tokens)
    
    errors = lint_spec_text(spec)
    # Should have no R-REF-1 errors (all refs resolve)
    assert not any(e.code == "R-REF-1" for e in errors)
```

### §4.3 Integration Tests

```python
def test_validate_speksi_kernel():
    """Linter must validate SPEKSI Kernel spec."""
    result = lint_spec(Path("SPEKSI_KERNEL.md"))
    assert result == 0, "SPEKSI Kernel must be valid"

def test_validate_self():
    """Linter must validate its own specification (bootstrap)."""
    result = lint_spec(Path("KERNEL_LINTER_SPEC.md"))
    assert result == 0, "Kernel linter spec must be valid"
```

---

## §5 VALIDATION

> Verification checklists for kernel linter correctness.

### §5.1 Code-Spec Alignment Checklist

- [ ] Every rule in §2 RULES has corresponding implementation
- [ ] Every `check_*()` function corresponds to a rule in §2
- [ ] All regex patterns in code match §1.4 Pattern Constants
- [ ] All layer types in code match §1.5 Layer Type Recognition
- [ ] Exit codes match §2.6 Output Rules

### §5.2 Test Coverage Checklist

- [ ] All rules in §2.3 have at least one test in §4
- [ ] All exemptions in §2.4 have tests verifying they work
- [ ] Property-based tests validate R-LINT-OUT-1 (never crash)
- [ ] Integration tests validate self-application

### §5.3 Documentation Consistency Checklist

- [ ] `kernel_linter_description.md` matches this spec
- [ ] `USING_LINTERS.md` documents all features in this spec
- [ ] Code comments reference rule IDs from this spec

---

## §C CHANGELOG

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2025-11-29 | Initial specification extracted from kernel_linter.py implementation |

---

## §G GLOSSARY

| Term | Definition |
|------|------------|
| **Kernel linter** | Tool that enforces SPEKSI Kernel rules (R-STR-*, R-CNT-*, R-REF-*, R-CON-*, R-PAT-*) |
| **Framework linter** | Tool that enforces SPEKSI Framework rules (R-GOV-*, R-PLN-*) |
| **Section token** | The § identifier for a section (e.g., "§1", "§2.3") |
| **Layer type** | The classification of a layer's purpose (META, RULES, etc.) |
| **Rule definition** | The canonical statement of a rule in a RULES-layer table |
| **Rule reference** | A mention of a rule ID outside its definition (per R-XXX) |
| **Anchoring** | Tying normative language to a specific rule ID (per R-CON-1) |
| **Exemption** | A context where a rule does not apply (e.g., PATTERNS layer) |
| **Framework document** | A spec that declares Kernel-Version and inherits Kernel rules |

---

**End of Kernel Linter Specification v1.0.0**
