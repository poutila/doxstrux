#!/usr/bin/env python3
"""
Mini SPEKSI spec_linter (Kernel-only)

Enforces a subset of SPEKSI Kernel rules (v1.0):

- R-STR-1  (tier declaration, for tier-classified specs)
- R-REF-1  (all → §X.Y references resolve, except pattern examples)
- R-REF-2  (all rule/invariant references resolve)
- R-CON-1  (must/never/always/only outside RULES/PRINCIPLES must be anchored)
- R-PAT-2  (rule IDs unique within namespace, based on definitions)
- R-PAT-3  (invariant IDs unique, based on definitions)
- R-PAT-4  (cross-references use recognized format)

Definition vs reference:
- Rule *definitions* are detected in RULES-layer tables: lines like "| R-STR-1 | ... |"
- Invariant *definitions* are detected in INVARIANTS subsection tables only
- All other occurrences of R-*/INV-* are treated as references only

Layer inheritance:
- Subsections inherit layer type from parent sections (§2.4 inherits PATTERNS from §2)

Framework compatibility:
- Documents with "Kernel-Version:" can reference Kernel namespaces (STR/CNT/REF/CON/PAT)
  without local definitions

This linter intentionally ignores all Framework-level rules (GOV/PLN/LNT/etc)
and any project-specific conventions.

Usage:
    python kernel_linter.py path/to/spec.md
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# --- Regexes derived from Kernel patterns ------------------------------------
RE_SECTION = re.compile(r"^(#+)\s+(§[0-9A-Z][0-9A-Z0-9.]*)(.*)$")
# Rule ID pattern - supports both R-NS-# and R-NS-SUB-# formats
RE_RULE_ID = re.compile(r"\bR-([A-Z]+(?:-[A-Z]+)*)-(\d+)\b")
RE_INV_ID = re.compile(r"\bINV-([A-Za-z0-9_]+)\b")
RE_REF_SECTION = re.compile(r"→\s+(§[0-9A-Z][0-9A-Z0-9.]*)")
RE_REF_RULE = re.compile(r"\(per\s+(R-[A-Z]+(?:-[A-Z]+)*-\d+)\)")
RE_REF_INV = re.compile(r"\(see\s+(INV-[A-Za-z0-9_]+)\)")
# More precise normative word detection - avoid matching in code/patterns
RE_MUST_WORDS = re.compile(r"(?<![`\w-])\b(must|never|always|only)\b(?![\w-])", re.IGNORECASE)
RE_TIER_HEADER = re.compile(r"^Tier:\s*(\w+)", re.IGNORECASE)
RE_KERNEL_VERSION = re.compile(r"^\*?\*?Kernel-Version\*?\*?:\s*", re.IGNORECASE)

# Reserved Kernel namespaces
KERNEL_NAMESPACES = {"STR", "CNT", "REF", "CON", "PAT"}

# Framework namespaces (can be referenced by Framework docs)
FRAMEWORK_NAMESPACES = {"GOV", "PLN", "LNT", "EXT"}


@dataclass
class Section:
    token: str         # e.g. '§1', '§2.3'
    title: str         # full title after token
    level: int         # heading level (# -> 1, ## -> 2, ...)
    start_line: int    # 1-based
    end_line: int      # 1-based, inclusive
    parent_idx: Optional[int] = None  # index of parent section
    layer_type: Optional[str] = None  # computed layer type


@dataclass
class LintError:
    line: int
    code: str
    message: str

    def format(self, path: Path) -> str:
        return f"{path}:{self.line}: [{self.code}] {self.message}"

    def to_dict(self, path: Path) -> dict:
        return {"file": str(path), "line": self.line, "code": self.code, "message": self.message}


# --- Parsing helpers ---------------------------------------------------------


def read_text(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"[ERROR] Spec file not found: {path}")
    return path.read_text(encoding="utf-8")


def collect_sections(text: str) -> List[Section]:
    """
    Parse markdown headings into sections identified by § tokens.
    Track parent relationships based on heading level.
    """
    lines = text.splitlines()
    raw: List[Tuple[int, str, str, str]] = []  # (lineno, hashes, token, rest)

    for lineno, line in enumerate(lines, start=1):
        m = RE_SECTION.match(line)
        if not m:
            continue
        hashes, token, rest = m.groups()
        raw.append((lineno, hashes, token.strip(), rest.strip()))

    sections: List[Section] = []
    level_stack: List[Tuple[int, int]] = []  # (level, section_index)

    for idx, (lineno, hashes, token, rest) in enumerate(raw):
        level = len(hashes)
        start_line = lineno
        if idx + 1 < len(raw):
            next_lineno = raw[idx + 1][0]
            end_line = next_lineno - 1
        else:
            end_line = len(lines)

        # Find parent: walk stack backwards to find first section with smaller level
        parent_idx = None
        while level_stack and level_stack[-1][0] >= level:
            level_stack.pop()
        if level_stack:
            parent_idx = level_stack[-1][1]

        sections.append(
            Section(
                token=token,
                title=rest,
                level=level,
                start_line=start_line,
                end_line=end_line,
                parent_idx=parent_idx,
            )
        )
        level_stack.append((level, len(sections) - 1))

    # Compute layer types with inheritance
    _compute_layer_types(sections)

    return sections


def _infer_layer_type_from_title(title: str) -> Optional[str]:
    """Infer layer type from section title."""
    if not title:
        return None
    title_upper = title.upper()
    for layer in [
        "META",
        "ARCHITECTURE",
        "DEFINITIONS",
        "PRINCIPLES",
        "RULES",
        "INVARIANTS",  # subsection of RULES
        "IMPLEMENTATION",
        "TESTS",
        "VALIDATION",
        "CHANGELOG",
        "GLOSSARY",
        "PATTERNS",
        "LAYERS",  # Kernel meta-section defining layer types
        "TIERS",  # Framework-specific
        "TEMPLATES",
        "LINTERS",
        "PLANS",
        "GOVERNANCE",
        "CONFIG",
    ]:
        if layer in title_upper:
            return layer
    return None


def _compute_layer_types(sections: List[Section]) -> None:
    """Compute layer types for all sections, inheriting from parents if needed."""
    for idx, sec in enumerate(sections):
        # First try to infer from this section's title
        layer = _infer_layer_type_from_title(sec.title)
        if layer:
            sec.layer_type = layer
            continue

        # Walk up parent chain to inherit
        parent_idx = sec.parent_idx
        while parent_idx is not None:
            parent = sections[parent_idx]
            if parent.layer_type:
                sec.layer_type = parent.layer_type
                break
            parent_idx = parent.parent_idx


def get_section_by_line(sections: List[Section], line_no: int) -> Optional[Section]:
    """Find the most specific (deepest) section containing this line."""
    best: Optional[Section] = None
    for sec in sections:
        if sec.start_line <= line_no <= sec.end_line:
            if best is None or sec.level > best.level:
                best = sec
    return best


def is_framework_document(text: str) -> bool:
    """Check if document declares Kernel inheritance."""
    for line in text.splitlines()[:50]:  # Check header area
        if RE_KERNEL_VERSION.match(line.strip()):
            return True
    return False


# --- Kernel rule checks ------------------------------------------------------


def check_tier_declared(text: str) -> List[LintError]:
    """
    R-STR-1 (Kernel-aware interpretation):

    For tier-classified specifications, Tier: must be present in the header.
    This mini linter treats Tier as optional overall, but if any 'Tier:' line
    exists, it must be well-formed.
    """
    errors: List[LintError] = []
    lines = text.splitlines()

    for lineno, line in enumerate(lines, start=1):
        m = RE_TIER_HEADER.match(line)
        if m:
            tier = m.group(1).strip()
            if tier.upper() not in {"MINIMAL", "STANDARD", "FULL"}:
                errors.append(
                    LintError(
                        line=lineno,
                        code="R-STR-1",
                        message=f"Unrecognized tier '{tier}'. Expected MINIMAL/STANDARD/FULL.",
                    )
                )
    return errors


def _is_table_definition_line_for_rule(line: str) -> Optional[str]:
    """
    Detect rule definition in table row and return the defined rule ID.

    A rule definition looks like:
        | R-STR-1 | A tier-classified ... |

    Returns the rule ID from the FIRST cell only, or None if not a definition.

    This ensures that rule IDs mentioned in description columns (e.g.,
    "must skip R-REF-1 validation") are not treated as definitions.
    """
    stripped = line.lstrip()
    if not stripped.startswith("|"):
        return None

    # Extract first cell content: | CONTENT | ...
    match = re.match(r"\|\s*([^|]+?)\s*\|", stripped)
    if not match:
        return None

    first_cell = match.group(1).strip()

    # Check if first cell IS a rule ID (not contains, IS)
    rule_match = re.fullmatch(r"R-[A-Z]+(?:-[A-Z]+)*-\d+", first_cell)
    if rule_match:
        return first_cell
    return None


def _is_invariant_definition_context(section: Section) -> bool:
    """
    Check if section is specifically for invariant definitions.
    Only count definitions in sections titled "INVARIANTS" within RULES layer.
    """
    if not section:
        return False
    title_upper = section.title.upper()
    # Must be in INVARIANTS subsection (not just any RULES section)
    if "INVARIANTS" in title_upper:
        return True
    # Also allow parent being RULES and this being a sub-subsection
    return False


def _is_table_definition_line_for_invariant(line: str, section: Section) -> bool:
    """
    Heuristic: an invariant definition in a table row looks like:

        | INV-SSOT | Each concept has ... |

    Only count as definition if in INVARIANTS subsection.
    """
    if not _is_invariant_definition_context(section):
        return False
    stripped = line.lstrip()
    if not stripped.startswith("|"):
        return False
    return bool(re.search(r"\|\s*INV-[A-Za-z0-9_]+\s*\|", line))


def check_rule_and_invariant_ids(
    text: str, sections: List[Section]
) -> Tuple[List[LintError], Dict[str, int], Dict[str, int]]:
    """
    Enforce:
    - R-PAT-2: rule IDs unique within namespace (based on definitions)
    - R-PAT-3: invariant IDs unique (based on definitions)

    Definitions:
      - Rules: table rows in RULES layer with "| R-XXX-# |"
      - Invariants: table rows in INVARIANTS subsection with "| INV-XXX |"
    """
    errors: List[LintError] = []
    rule_defs: Dict[str, int] = {}
    inv_defs: Dict[str, int] = {}

    lines = text.splitlines()

    for lineno, line in enumerate(lines, start=1):
        sec = get_section_by_line(sections, line_no=lineno)
        layer = sec.layer_type if sec else None

        # Rule definitions only in RULES-layer tables
        # Only the FIRST cell's rule ID is a definition, not mentions in descriptions
        if layer == "RULES":
            rid = _is_table_definition_line_for_rule(line)
            if rid:
                if rid in rule_defs:
                    prev = rule_defs[rid]
                    errors.append(
                        LintError(
                            line=lineno,
                            code="R-PAT-2",
                            message=f"Rule ID {rid} defined more than once "
                                    f"(previous definition around line {prev}).",
                        )
                    )
                else:
                    rule_defs[rid] = lineno

        # Invariant definitions only in INVARIANTS subsection tables
        if sec and _is_table_definition_line_for_invariant(line, sec):
            for m in RE_INV_ID.finditer(line):
                iid = m.group(0)
                if iid in inv_defs:
                    prev = inv_defs[iid]
                    errors.append(
                        LintError(
                            line=lineno,
                            code="R-PAT-3",
                            message=f"Invariant ID {iid} defined more than once "
                                    f"(previous definition around line {prev}).",
                        )
                    )
                else:
                    inv_defs[iid] = lineno

    return errors, rule_defs, inv_defs


def check_reference_integrity(
    text: str,
    sections: List[Section],
    rule_defs: Dict[str, int],
    inv_defs: Dict[str, int],
    is_framework: bool,
) -> List[LintError]:
    """
    Enforce:
    - R-REF-1: all → §X.Y references resolve (except PATTERNS examples)
    - R-REF-2: rule/invariant references resolve
    - R-PAT-4: references use recognized formats (implicit via regex)

    Framework documents can reference Kernel namespaces without local defs.
    """
    errors: List[LintError] = []
    lines = text.splitlines()

    # Section tokens set
    section_tokens = {sec.token for sec in sections}

    for lineno, line in enumerate(lines, start=1):
        sec = get_section_by_line(sections, line_no=lineno)
        layer = sec.layer_type if sec else None

        # Section references
        for m in RE_REF_SECTION.finditer(line):
            token = m.group(1)
            if token not in section_tokens:
                # Allow unresolved refs inside PATTERNS as pattern examples
                if layer == "PATTERNS":
                    continue
                # Skip if reference is inside backticks (code span pattern example)
                ref_text = m.group(0)  # e.g., "→ §X.Y"
                if f"`{ref_text}`" in line or f"`→ {token}`" in line:
                    continue
                errors.append(
                    LintError(
                        line=lineno,
                        code="R-REF-1",
                        message=f"Reference to section {token} does not resolve.",
                    )
                )

        # Rule references
        for m in RE_REF_RULE.finditer(line):
            rid = m.group(1)
            if rid not in rule_defs:
                # Allow pattern examples in PATTERNS layer
                if layer == "PATTERNS":
                    continue
                # Framework can reference Kernel and Framework namespaces
                ns_match = RE_RULE_ID.match(rid)
                if ns_match:
                    ns = ns_match.group(1)
                    if is_framework and ns in (KERNEL_NAMESPACES | FRAMEWORK_NAMESPACES):
                        continue  # Valid reference to inherited rule
                errors.append(
                    LintError(
                        line=lineno,
                        code="R-REF-2",
                        message=f"Reference {rid} does not resolve to a defined rule.",
                    )
                )

        # Invariant references
        for m in RE_REF_INV.finditer(line):
            iid = m.group(1)
            if iid not in inv_defs:
                # Allow pattern examples in PATTERNS layer
                if layer == "PATTERNS":
                    continue
                # Framework inherits Kernel invariants
                if is_framework and iid in {"INV-SSOT", "INV-LAYER", "INV-REF", "INV-ANCHOR"}:
                    continue
                errors.append(
                    LintError(
                        line=lineno,
                        code="R-REF-2",
                        message=f"Reference {iid} does not resolve to a defined invariant.",
                    )
                )

    return errors


def strip_code_blocks(text: str) -> Tuple[str, List[Tuple[int, int]]]:
    """
    Remove fenced code blocks (``` ... ```), returning stripped text and a list
    of (start_line, end_line) ranges for blocks.
    """
    lines = text.splitlines()
    in_block = False
    block_ranges: List[Tuple[int, int]] = []
    out_lines: List[str] = []

    block_start = 0
    for lineno, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            if not in_block:
                in_block = True
                block_start = lineno
            else:
                in_block = False
                block_ranges.append((block_start, lineno))
            out_lines.append("")
        elif in_block:
            out_lines.append("")
        else:
            out_lines.append(line)

    return "\n".join(out_lines), block_ranges


def _line_has_normative_language(line: str) -> bool:
    """
    Check if line contains normative language that needs anchoring.
    Skip lines that are clearly patterns/code (contain backticks around the word).
    """
    # Skip table cells that look like pattern/regex examples
    if "`must" in line or "`never" in line or "`always" in line or "`only" in line:
        return False
    # Skip lines where the word is inside backticks
    if re.search(r"`[^`]*\b(must|never|always|only)\b[^`]*`", line, re.IGNORECASE):
        return False
    return bool(RE_MUST_WORDS.search(line))


def check_anchored_constraints(
    text: str, sections: List[Section]
) -> List[LintError]:
    """
    Enforce R-CON-1: must/never/always/only outside RULES layer must reference
    a rule ID somewhere on the same line.

    Exceptions:
    - PRINCIPLES layer is axiomatic
    - RULES layer can have unanchored normative text
    - INVARIANTS subsection (part of RULES)
    - Pattern examples in backticks
    """
    errors: List[LintError] = []
    lines = text.splitlines()

    for lineno, line in enumerate(lines, start=1):
        if not _line_has_normative_language(line):
            continue

        sec = get_section_by_line(sections, line_no=lineno)
        layer = sec.layer_type if sec else None

        # Layers that can have unanchored normative text:
        # - RULES, INVARIANTS: define constraints
        # - PRINCIPLES: define axioms
        # - GLOSSARY, DEFINITIONS: define terms (not behavioral claims)
        # - PATTERNS: define syntax patterns
        # - LAYERS: Kernel meta-section defining layer types
        # - TIERS, PLANS, LINTERS: Framework meta-sections (per §3.4 Conceptual Layer Exemptions)
        if layer in {"RULES", "PRINCIPLES", "INVARIANTS", "GLOSSARY", "DEFINITIONS", "PATTERNS", "LAYERS", "TIERS", "PLANS", "LINTERS"}:
            continue

        # Outside these layers: require rule ID reference on same line
        if not RE_RULE_ID.search(line):
            errors.append(
                LintError(
                    line=lineno,
                    code="R-CON-1",
                    message=(
                        "Normative language ('must/never/always/only') outside "
                        "RULES/PRINCIPLES layers must be anchored to a rule ID."
                    ),
                )
            )
    return errors


# --- Lint entrypoint ---------------------------------------------------------


def lint_spec(path: Path, *, json_mode: bool = False) -> int:
    raw_text = read_text(path)

    # Check if this is a Framework document
    is_framework = is_framework_document(raw_text)

    # Strip code blocks for most checks so examples don't trigger false positives
    stripped_text, _ = strip_code_blocks(raw_text)

    sections = collect_sections(stripped_text)
    if not sections:
        print(f"[WARN] No §-sections found in {path} — is this a SPEKSI spec?")

    errors: List[LintError] = []

    # 1) Tier declaration (minimal interpretation of R-STR-1)
    errors.extend(check_tier_declared(stripped_text))

    # 2) Rule + invariant definitions (R-PAT-2, R-PAT-3)
    id_errors, rule_defs, inv_defs = check_rule_and_invariant_ids(
        stripped_text, sections
    )
    errors.extend(id_errors)

    # 3) Reference integrity (R-REF-1, R-REF-2, R-PAT-4)
    errors.extend(
        check_reference_integrity(stripped_text, sections, rule_defs, inv_defs, is_framework)
    )

    # 4) Anchored constraints (R-CON-1)
    errors.extend(check_anchored_constraints(stripped_text, sections))

    if errors:
        if json_mode:
            print(json.dumps({
                "file": str(path),
                "errors": [err.to_dict(path) for err in errors],
            }, indent=2))
        else:
            print(f"Kernel spec_linter found {len(errors)} issue(s) in {path}:")
            for err in errors:
                print("  " + err.format(path))
        return 1

    if json_mode:
        print(json.dumps({"file": str(path), "errors": []}, indent=2))
    else:
        print(f"Kernel spec_linter OK for {path}")
    return 0


def main(argv: List[str]) -> int:
    json_mode = False
    args = [a for a in argv[1:] if a]

    if args and args[0] == "--json":
        json_mode = True
        args = args[1:]

    if len(args) != 1:
        print("Usage: kernel_linter.py [--json] <spec.md>", file=sys.stderr)
        return 2

    spec_path = Path(args[0])
    return lint_spec(spec_path, json_mode=json_mode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
