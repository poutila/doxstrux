#!/usr/bin/env python3
"""
prose_input_linter.py

STRICT validator for Prose Input Template v1.0.

This linter validates that a prose input document conforms to the required
structure for deterministic conversion to an AI Task List.

Philosophy:
- Input structure mirrors output structure
- No ambiguity in input = no guessing in conversion
- Fail fast on any deviation from template

Exit codes:
    0 = Valid (ready for conversion)
    1 = Validation errors (do not convert)
    2 = Schema/parse error (malformed document)
    3 = Usage/file error

Dependencies:
    - pyyaml (for robust YAML parsing)

Usage:
    uv run python tools/prose_input_linter.py SPEC.md
    uv run python tools/prose_input_linter.py --json SPEC.md
    uv run python tools/prose_input_linter.py --fix-hints SPEC.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml


LINTER_VERSION = "1.1.0"
SCHEMA_VERSION = "1.0"


class Severity(Enum):
    """Error severity levels."""
    ERROR = "error"      # Must fix - blocks conversion
    WARNING = "warning"  # Should fix - may cause poor output


@dataclass
class LintError:
    """A single validation error."""
    rule_id: str
    line: int
    severity: Severity
    message: str
    fix_hint: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result."""
    file_path: str
    valid: bool
    schema_version: Optional[str]
    error_count: int
    warning_count: int
    errors: List[LintError]
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SCHEMA DEFINITION
# =============================================================================

REQUIRED_YAML_FIELDS = [
    ("schema_version", str, "prose_input.schema_version"),
    ("project_name", str, "prose_input.project_name"),
    ("runner", str, "prose_input.runner"),
    ("runner_prefix", str, "prose_input.runner_prefix"),  # Can be empty string
    ("search_tool", str, "prose_input.search_tool"),
]

VALID_RUNNERS = {"uv", "npm", "cargo", "go", "poetry", "pipenv"}
VALID_SEARCH_TOOLS = {"rg", "grep"}

# Required sections (must appear in this order)
REQUIRED_SECTIONS = [
    ("## SSOT Declaration", "PIN-001"),
    ("## Scope", "PIN-002"),
    ("### In Scope", "PIN-003"),
    ("### Out of Scope", "PIN-004"),
    ("## Decisions (Binding)", "PIN-005"),
    ("## External Dependencies", "PIN-006"),
    ("## File Manifest", "PIN-007"),
    ("## Test Strategy", "PIN-008"),
    ("## Phase 0", "PIN-009"),  # Partial match - Phase 0 required
]

# Required subsections within External Dependencies
REQUIRED_DEPENDENCY_SUBSECTIONS = [
    ("### Required Files/Modules", "PIN-010"),
    ("### Required Libraries", "PIN-011"),
    ("### Required Tools", "PIN-012"),
]

# Required task fields
REQUIRED_TASK_FIELDS = [
    "Objective",
    "Paths",
]

REQUIRED_TASK_FIELDS_NON_PHASE_0 = [
    "Objective",
    "Paths",
    "Precondition",  # Symbol check required
    "TDD Specification",
    "Success Criteria",
]

# Forbidden patterns (with rule IDs and messages)
FORBIDDEN_PATTERNS = [
    (
        "PIN-F01",
        re.compile(r"\b(TBD|TODO|TBC|FIXME|XXX)\b", re.IGNORECASE),
        "Unresolved marker '{match}' found. All items must be resolved before conversion.",
        "Replace with actual value or remove if not needed.",
    ),
    (
        "PIN-F02",
        re.compile(r"\[\[(?!PH:)[A-Z_]+\]\]"),  # [[PLACEHOLDER]] but not [[PH:...]]
        "Unfilled placeholder '{match}' found. All placeholders must be replaced.",
        "Replace [[PLACEHOLDER]] with actual value.",
    ),
    (
        "PIN-F03",
        re.compile(r"(?<!\?)\?\s*$", re.MULTILINE),  # Line ending with ? (but not ??)
        "Unanswered question found. All questions must be resolved.",
        "Answer the question or move to Out of Scope with reason.",
    ),
    (
        "PIN-F04",
        re.compile(r"\b(maybe|might|could|possibly|potentially|consider)\s+(we|you|add|use|implement|include)", re.IGNORECASE),
        "Tentative language '{match}' found. All statements must be definitive.",
        "Replace with definitive statement or move to Out of Scope.",
    ),
    (
        "PIN-F05",
        re.compile(r"\b(if\s+we|if\s+you|if\s+the)\s+.{5,50}\s+(then|,)", re.IGNORECASE),
        "Conditional logic '{match}' found. Conditions must be resolved to concrete decisions.",
        "Make the decision and state it in Decisions (Binding) table.",
    ),
    (
        "PIN-F06",
        re.compile(r"\b\d+[-–]\d+\s*(hours?|days?|weeks?|minutes?|mins?)\b", re.IGNORECASE),
        "Time estimate '{match}' found. Time estimates are not allowed.",
        "Remove time estimate. Use success criteria instead.",
    ),
    (
        "PIN-F07",
        re.compile(r"\bpending\b|\bto\s+be\s+decided\b|\bTBD\s+by\b", re.IGNORECASE),
        "Pending decision '{match}' found. All decisions must be final.",
        "Make the decision now or explicitly exclude from scope.",
    ),
]

# Patterns that should NOT appear in certain contexts
CONTEXT_FORBIDDEN = [
    # In Success Criteria, subjective terms are forbidden
    (
        "PIN-C01",
        "Success Criteria",
        re.compile(r"\b(good|nice|clean|proper|appropriate|reasonable|adequate)\b", re.IGNORECASE),
        "Subjective term '{match}' in Success Criteria. Criteria must be measurable.",
        "Replace with specific, measurable criterion (e.g., 'coverage > 80%').",
    ),
]


# =============================================================================
# PARSING HELPERS
# =============================================================================

def parse_yaml_front_matter(lines: List[str]) -> Tuple[Dict[str, Any], Optional[LintError], int]:
    """Parse YAML front matter and return metadata dict."""
    if not lines or lines[0].strip() != "---":
        return {}, LintError("PIN-Y01", 1, Severity.ERROR,
            "Missing YAML front matter. Document must start with '---'."), 0

    # Find closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, LintError("PIN-Y01", 1, Severity.ERROR,
            "Unclosed YAML front matter. Missing closing '---'."), 0

    # Parse YAML using PyYAML
    yaml_content = "\n".join(lines[1:end_idx])
    try:
        metadata = yaml.safe_load(yaml_content)
        if metadata is None:
            metadata = {}
    except yaml.YAMLError as e:
        return {}, LintError("PIN-Y01", 1, Severity.ERROR,
            f"Invalid YAML in front matter: {e}"), 0

    return metadata, None, end_idx + 1


def find_sections(lines: List[str], start_idx: int) -> Dict[str, Tuple[int, int]]:
    """Find all markdown sections and their line ranges."""
    sections: Dict[str, Tuple[int, int]] = {}
    current_section: Optional[str] = None
    current_start: int = start_idx

    for i in range(start_idx, len(lines)):
        line = lines[i]
        # Match ## or ### headings
        match = re.match(r"^(#{1,4})\s+(.+)$", line)
        if match:
            # Close previous section
            if current_section:
                sections[current_section] = (current_start, i)
            current_section = line.strip()
            current_start = i

    # Close last section
    if current_section:
        sections[current_section] = (current_start, len(lines))

    return sections


def find_tasks(lines: List[str], start_idx: int) -> List[Tuple[str, int, int]]:
    """Find all task definitions and their line ranges."""
    tasks: List[Tuple[str, int, int]] = []  # (task_id, start, end)
    task_pattern = re.compile(r"^####\s+Task\s+(\d+\.\d+)\s*[-—]\s*(.+)$")

    current_task: Optional[str] = None
    current_start: int = start_idx

    for i in range(start_idx, len(lines)):
        line = lines[i]
        match = task_pattern.match(line)
        if match:
            # Close previous task
            if current_task:
                tasks.append((current_task, current_start, i))
            current_task = match.group(1)
            current_start = i
        # New phase or section closes task
        elif current_task and re.match(r"^#{1,3}\s+", line):
            tasks.append((current_task, current_start, i))
            current_task = None

    # Close last task
    if current_task:
        tasks.append((current_task, current_start, len(lines)))

    return tasks


def extract_task_fields(lines: List[str], start: int, end: int) -> Dict[str, Tuple[int, str]]:
    """Extract field values from a task block."""
    fields: Dict[str, Tuple[int, str]] = {}

    for i in range(start, end):
        line = lines[i]
        # Match **Field**: value or **Field**:
        match = re.match(r"^\*\*([A-Za-z][A-Za-z\s]+)\*\*\s*[:|]\s*(.*)$", line.strip())
        if match:
            field_name = match.group(1).strip()
            field_value = match.group(2).strip()
            fields[field_name] = (i + 1, field_value)

        # Match | **Field** | value | (table format)
        table_match = re.match(r"^\|\s*\*\*([A-Za-z][A-Za-z\s]+)\*\*\s*\|\s*(.+)\s*\|", line.strip())
        if table_match:
            field_name = table_match.group(1).strip()
            field_value = table_match.group(2).strip()
            fields[field_name] = (i + 1, field_value)

    return fields


def get_phase_number(task_id: str) -> int:
    """Extract phase number from task ID like '1.2' -> 1."""
    return int(task_id.split(".")[0])


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_yaml_metadata(metadata: Dict[str, Any], errors: List[LintError]) -> Dict[str, str]:
    """Validate YAML front matter fields."""
    flat_meta: Dict[str, str] = {}

    prose_input = metadata.get("prose_input", {})
    if not prose_input:
        errors.append(LintError("PIN-Y02", 1, Severity.ERROR,
            "Missing 'prose_input:' block in front matter."))
        return flat_meta

    # Check required fields
    for field_name, field_type, full_path in REQUIRED_YAML_FIELDS:
        value = prose_input.get(field_name)
        if value is None:
            errors.append(LintError("PIN-Y03", 1, Severity.ERROR,
                f"Missing required field: {full_path}"))
        elif not isinstance(value, str):
            errors.append(LintError("PIN-Y04", 1, Severity.ERROR,
                f"Field {full_path} must be a string."))
        else:
            flat_meta[field_name] = value

    # Validate specific fields
    if "schema_version" in flat_meta and flat_meta["schema_version"] != SCHEMA_VERSION:
        errors.append(LintError("PIN-Y05", 1, Severity.ERROR,
            f"schema_version must be '{SCHEMA_VERSION}' (found '{flat_meta['schema_version']}')."))

    if "runner" in flat_meta and flat_meta["runner"] not in VALID_RUNNERS:
        errors.append(LintError("PIN-Y06", 1, Severity.ERROR,
            f"Invalid runner '{flat_meta['runner']}'. Must be one of: {', '.join(sorted(VALID_RUNNERS))}"))

    if "search_tool" in flat_meta and flat_meta["search_tool"] not in VALID_SEARCH_TOOLS:
        errors.append(LintError("PIN-Y07", 1, Severity.ERROR,
            f"Invalid search_tool '{flat_meta['search_tool']}'. Must be one of: {', '.join(sorted(VALID_SEARCH_TOOLS))}"))

    # Check for unfilled placeholders in values
    for key, value in flat_meta.items():
        if "[[" in value and "]]" in value:
            errors.append(LintError("PIN-Y08", 1, Severity.ERROR,
                f"Unfilled placeholder in {key}: '{value}'"))

    return flat_meta


def validate_required_sections(
    sections: Dict[str, Tuple[int, int]],
    lines: List[str],
    errors: List[LintError]
) -> None:
    """Validate that all required sections exist in order."""
    found_order: List[Tuple[str, int]] = []

    for section_pattern, rule_id in REQUIRED_SECTIONS:
        found = False
        for section_name, (start, _) in sections.items():
            if section_name.startswith(section_pattern) or section_pattern in section_name:
                found = True
                found_order.append((section_pattern, start))
                break

        if not found:
            errors.append(LintError(rule_id, 1, Severity.ERROR,
                f"Missing required section: '{section_pattern}'",
                f"Add '{section_pattern}' section to document."))

    # Check ordering
    for i in range(1, len(found_order)):
        prev_name, prev_line = found_order[i-1]
        curr_name, curr_line = found_order[i]
        if curr_line < prev_line:
            errors.append(LintError("PIN-S01", curr_line, Severity.ERROR,
                f"Section '{curr_name}' appears before '{prev_name}'. Sections must be in order.",
                "Reorder sections to match template structure."))

    # Validate External Dependencies subsections
    validate_dependency_subsections(sections, lines, errors)


def validate_dependency_subsections(
    sections: Dict[str, Tuple[int, int]],
    lines: List[str],
    errors: List[LintError]
) -> None:
    """Validate required subsections within External Dependencies."""
    # Find External Dependencies section start
    ext_deps_start = None
    for section_name, (start, _) in sections.items():
        if "External Dependencies" in section_name:
            ext_deps_start = start
            break

    if ext_deps_start is None:
        return  # Already reported by required sections check

    # Find next ## section after External Dependencies to determine true bounds
    ext_deps_end = len(lines)
    for section_name, (start, _) in sections.items():
        if section_name.startswith("## ") and start > ext_deps_start:
            if start < ext_deps_end:
                ext_deps_end = start

    # Check for required subsections within External Dependencies
    for subsection_pattern, rule_id in REQUIRED_DEPENDENCY_SUBSECTIONS:
        found = False
        for section_name, (start, _) in sections.items():
            if subsection_pattern in section_name:
                # Verify subsection is within External Dependencies bounds
                if ext_deps_start < start < ext_deps_end:
                    found = True
                    break

        if not found:
            errors.append(LintError(rule_id, ext_deps_start, Severity.ERROR,
                f"Missing required subsection in External Dependencies: '{subsection_pattern}'",
                f"Add '{subsection_pattern}' subsection to External Dependencies."))


def validate_forbidden_patterns(
    lines: List[str],
    start_idx: int,
    errors: List[LintError]
) -> None:
    """Check for forbidden patterns throughout document."""
    for i in range(start_idx, len(lines)):
        line = lines[i]
        line_num = i + 1

        # Skip comment lines
        if line.strip().startswith("<!--") or line.strip().startswith("#"):
            continue

        for rule_id, pattern, message_template, fix_hint in FORBIDDEN_PATTERNS:
            matches = pattern.findall(line)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Get first group
                message = message_template.format(match=match)
                errors.append(LintError(rule_id, line_num, Severity.ERROR, message, fix_hint))


def validate_tasks(
    lines: List[str],
    tasks: List[Tuple[str, int, int]],
    metadata: Dict[str, str],
    errors: List[LintError]
) -> None:
    """Validate task structure and required fields."""
    seen_task_ids: Set[str] = set()
    search_tool = metadata.get("search_tool", "rg")

    for task_id, start, end in tasks:
        line_num = start + 1

        # Check for duplicate task IDs
        if task_id in seen_task_ids:
            errors.append(LintError("PIN-T01", line_num, Severity.ERROR,
                f"Duplicate task ID: {task_id}"))
        seen_task_ids.add(task_id)

        # Extract fields
        fields = extract_task_fields(lines, start, end)
        phase_num = get_phase_number(task_id)

        # Determine required fields based on phase
        required = REQUIRED_TASK_FIELDS if phase_num == 0 else REQUIRED_TASK_FIELDS_NON_PHASE_0

        for field_name in required:
            if field_name not in fields:
                errors.append(LintError("PIN-T02", line_num, Severity.ERROR,
                    f"Task {task_id} missing required field: '{field_name}'",
                    f"Add '**{field_name}**: value' to task."))

        # Validate Paths field (must be comma-separated file paths)
        if "Paths" in fields:
            _, paths_value = fields["Paths"]
            if paths_value and not re.search(r"`[^`]+`", paths_value):
                errors.append(LintError("PIN-T03", fields["Paths"][0], Severity.WARNING,
                    f"Task {task_id} Paths should use backticks: `path/to/file.py`"))

        # Validate Precondition uses correct search tool
        if "Precondition" in fields and phase_num > 0:
            precond_start = fields["Precondition"][0]
            # Look for code block after Precondition
            for j in range(precond_start, min(precond_start + 10, end)):
                if j < len(lines):
                    check_line = lines[j]
                    if "grep" in check_line and search_tool == "rg":
                        errors.append(LintError("PIN-T04", j + 1, Severity.ERROR,
                            f"Task {task_id} Precondition uses 'grep' but search_tool is 'rg'.",
                            "Replace 'grep' with 'rg'."))

        # Validate Success Criteria are present and measurable
        task_block = "\n".join(lines[start:end])
        if "Success Criteria" in task_block:
            # Check for checkboxes
            criteria_count = len(re.findall(r"- \[ \]", task_block))
            if criteria_count == 0:
                errors.append(LintError("PIN-T05", line_num, Severity.WARNING,
                    f"Task {task_id} Success Criteria has no checkboxes.",
                    "Add '- [ ] criterion' items."))


def validate_decisions_table(
    lines: List[str],
    sections: Dict[str, Tuple[int, int]],
    errors: List[LintError]
) -> None:
    """Validate the Decisions (Binding) table."""
    decisions_section = None
    for name, bounds in sections.items():
        if "Decisions" in name and "Binding" in name:
            decisions_section = bounds
            break

    if not decisions_section:
        return  # Already caught by required sections check

    start, end = decisions_section
    table_lines = [lines[i] for i in range(start, end) if lines[i].strip().startswith("|")]

    if len(table_lines) < 3:  # Header + separator + at least 1 row
        errors.append(LintError("PIN-D01", start + 1, Severity.ERROR,
            "Decisions table must have at least one decision row.",
            "Add decisions to the table."))
        return

    # Check header columns
    header = table_lines[0]
    required_cols = ["ID", "Decision", "Rationale"]
    for col in required_cols:
        if col not in header:
            errors.append(LintError("PIN-D02", start + 1, Severity.ERROR,
                f"Decisions table missing column: '{col}'"))


def validate_file_manifest(
    lines: List[str],
    sections: Dict[str, Tuple[int, int]],
    errors: List[LintError]
) -> None:
    """Validate the File Manifest table."""
    manifest_section = None
    for name, bounds in sections.items():
        if "File Manifest" in name:
            manifest_section = bounds
            break

    if not manifest_section:
        return

    start, end = manifest_section
    table_lines = [lines[i] for i in range(start, end) if lines[i].strip().startswith("|")]

    if len(table_lines) < 3:
        errors.append(LintError("PIN-M01", start + 1, Severity.ERROR,
            "File Manifest must have at least one file entry.",
            "Add file entries to the manifest."))
        return

    # Check for backtick-quoted paths
    for i, table_line in enumerate(table_lines[2:], start=3):  # Skip header and separator
        if "`" not in table_line:
            errors.append(LintError("PIN-M02", start + i, Severity.WARNING,
                "File Manifest paths should use backticks: `src/path/file.py`"))
            break  # Only warn once


def validate_submission_checklist(
    lines: List[str],
    errors: List[LintError]
) -> None:
    """Validate that submission checklist exists and is checked."""
    checklist_start = None
    for i, line in enumerate(lines):
        if "Checklist Before Submission" in line:
            checklist_start = i
            break

    if checklist_start is None:
        errors.append(LintError("PIN-CL01", 1, Severity.ERROR,
            "Missing 'Checklist Before Submission' section.",
            "Add the submission checklist from the template."))
        return

    # Count unchecked items
    unchecked = 0
    for i in range(checklist_start, len(lines)):
        line = lines[i]
        if "- [ ]" in line:
            unchecked += 1

    if unchecked > 0:
        errors.append(LintError("PIN-CL02", checklist_start + 1, Severity.ERROR,
            f"Submission checklist has {unchecked} unchecked items. All must be checked.",
            "Review and check all checklist items before submission."))


# =============================================================================
# MAIN LINT FUNCTION
# =============================================================================

def lint(path: Path) -> ValidationResult:
    """Run all validation checks on the input document."""
    errors: List[LintError] = []

    # Read file
    if not path.exists():
        return ValidationResult(
            file_path=str(path),
            valid=False,
            schema_version=None,
            error_count=1,
            warning_count=0,
            errors=[LintError("PIN-F00", 0, Severity.ERROR, f"File not found: {path}")],
        )

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
    except Exception as e:
        return ValidationResult(
            file_path=str(path),
            valid=False,
            schema_version=None,
            error_count=1,
            warning_count=0,
            errors=[LintError("PIN-F00", 0, Severity.ERROR, f"Error reading file: {e}")],
        )

    # Parse YAML front matter
    metadata, yaml_error, content_start = parse_yaml_front_matter(lines)
    if yaml_error:
        errors.append(yaml_error)
        return ValidationResult(
            file_path=str(path),
            valid=False,
            schema_version=None,
            error_count=1,
            warning_count=0,
            errors=errors,
        )

    # Validate YAML metadata
    flat_meta = validate_yaml_metadata(metadata, errors)
    schema_version = flat_meta.get("schema_version")

    # Find sections
    sections = find_sections(lines, content_start)

    # Validate required sections
    validate_required_sections(sections, lines, errors)

    # Validate forbidden patterns
    validate_forbidden_patterns(lines, content_start, errors)

    # Find and validate tasks
    tasks = find_tasks(lines, content_start)
    if not tasks:
        errors.append(LintError("PIN-T00", content_start, Severity.ERROR,
            "No tasks found. Document must have at least one '#### Task N.M — Name'."))
    else:
        validate_tasks(lines, tasks, flat_meta, errors)

    # Validate specific sections
    validate_decisions_table(lines, sections, errors)
    validate_file_manifest(lines, sections, errors)
    validate_submission_checklist(lines, errors)

    # Count by severity
    error_count = sum(1 for e in errors if e.severity == Severity.ERROR)
    warning_count = sum(1 for e in errors if e.severity == Severity.WARNING)

    return ValidationResult(
        file_path=str(path),
        valid=error_count == 0,
        schema_version=schema_version,
        error_count=error_count,
        warning_count=warning_count,
        errors=errors,
        metadata=flat_meta,
    )


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def format_human_output(result: ValidationResult, show_hints: bool = False) -> str:
    """Format result for human-readable output."""
    lines: List[str] = []

    lines.append("=" * 70)
    lines.append(f"PROSE INPUT VALIDATION: {result.file_path}")
    lines.append("=" * 70)
    lines.append("")

    status = "VALID" if result.valid else "INVALID"
    icon = "✅" if result.valid else "❌"
    lines.append(f"Status: {icon} {status}")
    lines.append(f"  Errors:   {result.error_count}")
    lines.append(f"  Warnings: {result.warning_count}")
    if result.schema_version:
        lines.append(f"  Schema:   {result.schema_version}")
    lines.append("")

    if result.errors:
        # Group by severity
        errs = [e for e in result.errors if e.severity == Severity.ERROR]
        warns = [e for e in result.errors if e.severity == Severity.WARNING]

        if errs:
            lines.append("-" * 70)
            lines.append("ERRORS (must fix)")
            lines.append("-" * 70)
            for e in errs:
                lines.append(f"  Line {e.line}: [{e.rule_id}] {e.message}")
                if show_hints and e.fix_hint:
                    lines.append(f"           💡 {e.fix_hint}")
            lines.append("")

        if warns:
            lines.append("-" * 70)
            lines.append("WARNINGS (should fix)")
            lines.append("-" * 70)
            for e in warns:
                lines.append(f"  Line {e.line}: [{e.rule_id}] {e.message}")
                if show_hints and e.fix_hint:
                    lines.append(f"           💡 {e.fix_hint}")
            lines.append("")

    lines.append("=" * 70)
    if result.valid:
        lines.append("READY FOR CONVERSION: uv run python ai_task_list_orchestrator.py " + result.file_path)
    else:
        lines.append("NOT READY: Fix all errors before conversion.")
    lines.append("=" * 70)

    return "\n".join(lines)


def format_json_output(result: ValidationResult) -> str:
    """Format result as JSON."""
    return json.dumps({
        "file": result.file_path,
        "valid": result.valid,
        "schema_version": result.schema_version,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "metadata": result.metadata,
        "errors": [
            {
                "rule_id": e.rule_id,
                "line": e.line,
                "severity": e.severity.value,
                "message": e.message,
                "fix_hint": e.fix_hint,
            }
            for e in result.errors
        ],
    }, indent=2)


# =============================================================================
# MAIN
# =============================================================================

def main(argv: List[str]) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="prose_input_linter.py",
        description="Strict validator for Prose Input Template v1.0.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0  Valid (ready for conversion)
  1  Validation errors (do not convert)
  2  Schema/parse error
  3  Usage/file error

Examples:
  uv run python tools/prose_input_linter.py SPEC.md
  uv run python tools/prose_input_linter.py --json SPEC.md
  uv run python tools/prose_input_linter.py --fix-hints SPEC.md
""",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {LINTER_VERSION}")
    parser.add_argument("path", help="Path to prose input document")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--fix-hints", action="store_true", help="Show fix hints for errors")
    args = parser.parse_args(argv)

    result = lint(Path(args.path))

    if args.json:
        print(format_json_output(result))
    else:
        print(format_human_output(result, show_hints=args.fix_hints))

    if result.error_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
