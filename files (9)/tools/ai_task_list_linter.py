#!/usr/bin/env python3
"""
ai_task_list_linter.py

Deterministic linter for AI Task Lists.
Spec is SSOT; this linter implements the spec. If linter and spec diverge, fix the linter.

Features:
- R-ATL-001: schema_version validation (reads from VERSION.yaml)
- R-ATL-042: Clean Table checklist enforcement
- R-ATL-063: Import hygiene enforcement (Python/uv)
- R-ATL-071/072/075: Runner/UV/$ enforcement
- pyyaml for robust YAML parsing
- deterministic (no network, no repo mutation)
- exit codes: 0=pass, 1=fail, 2=usage/internal error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


def _load_framework_version() -> str:
    """Load framework version from VERSION.yaml (SSOT)."""
    version_file = Path(__file__).parent.parent / "VERSION.yaml"
    if not version_file.exists():
        raise RuntimeError(f"VERSION.yaml not found at {version_file}")
    data = yaml.safe_load(version_file.read_text(encoding="utf-8"))
    return data["version"]


FRAMEWORK_VERSION = _load_framework_version()


RE_FM = re.compile(r"^---\s*$")
RE_ALLOWED_PH = re.compile(r"\[\[PH:[A-Z0-9_]+\]\]")

RE_PHASE = re.compile(r"^##\s+Phase\s+(\d+)\s*[—-]\s*(.+)\s*$")
RE_TASK = re.compile(r"^###\s+Task\s+(\d+)\.(\d+)\s*[—-]\s*(.+)\s*$")

RE_ARRAY_END = re.compile(r"^\)\s*$")
RE_QUOTED_PATH = re.compile(r'^\s*"[^"]+"\s*$')

REQ_TDD_1 = "### TDD Step 1 — Write test (RED)"
REQ_TDD_2 = "### TDD Step 2 — Implement (minimal)"
REQ_TDD_3 = "### TDD Step 3 — Verify (GREEN)"
REQ_STOP = "### STOP — Clean Table"

# R-ATL-010: Required headings (includes Phase Gate per R-ATL-051)
REQUIRED_HEADINGS = [
    "## Non-negotiable Invariants",
    "## Placeholder Protocol",
    "## Source of Truth Hierarchy",
    "## Baseline Snapshot (capture before any work)",
    "## Phase 0 — Baseline Reality",
    "## Drift Ledger (append-only)",
    "## Phase Unlock Artifact",
    "## Global Clean Table Scan",
    "## STOP — Phase Gate",
]

BASELINE_ROW_LABELS = ["Date", "Repo", "Branch", "Commit", "Runner", "Runtime"]
DRIFT_LEDGER_COLUMNS = ["Date", "Higher", "Lower", "Mismatch", "Resolution", "Evidence"]

NO_WEAK_TESTS_PROMPTS = [
    "Stub/no-op would FAIL this test?",
    "Asserts semantics, not just presence?",
    "Has negative case for critical behavior?",
    "Is NOT import-only/smoke/existence-only/exit-code-only?",
]

CLEAN_TABLE_PROMPTS = [
    "Tests pass (not skipped)",
    "Full suite passes",
    "No placeholders remain",
    "Paths exist",
    "Drift ledger updated",
]

ALLOWED_STATUS_VALUES = [
    "📋 PLANNED",
    "⏳ IN PROGRESS",
    "✅ COMPLETE",
    "❌ BLOCKED",
]

STRICT_FORBIDDEN_TOKENS = [
    "[[PH:OUTPUT]]",
    "[[PH:PASTE_TEST_OUTPUT]]",
    "[[PH:PASTE_PRECONDITION_OUTPUT]]",
    "[[PH:PASTE_CLEAN_TABLE_OUTPUT]]",
]

UV_FORBIDDEN = [
    ".venv/bin/python",
    "python -m",
    "pip install",
]

# D3 witness: prefer filename-ish or path-ish with :line
RE_WITNESS_PATH_LINE = re.compile(
    r"(?:(?:[A-Za-z0-9_.\-]+/)+[A-Za-z0-9_.\-]+|[A-Za-z0-9_.\-]+\.[A-Za-z0-9_.\-]+):\d+\b"
)

# D2 symbol-check command patterns
RE_SYMBOL_CMD = re.compile(r"(^|\s)(rg\s+-n|rg\s+|grep\s+-R|grep\s+-n|grep\s+-Rn|grep\s+-RIn|grep\s+-RInE)\b")
RE_SYMBOL_CMD_RG_ONLY = re.compile(r"(^|\s)(rg\s+-n|rg\s+)\b")
RE_GREP_USAGE = re.compile(r"\bgrep\b")

# R-ATL-024: Captured evidence header patterns
RE_HDR_CMD = re.compile(r"^\s*#\s*cmd\s*:\s*\S+")
RE_HDR_EXIT = re.compile(r"^\s*#\s*exit\s*:\s*(\d+)\s*$")


@dataclass(frozen=True)
class LintError:
    line: int
    rule_id: str
    message: str


def _json_report(path: Path, meta: Dict[str, str], errors: List[LintError]) -> Dict[str, object]:
    return {
        "file": str(path),
        "passed": len(errors) == 0,
        "error_count": len(errors),
        "schema_version": meta.get("schema_version", ""),
        "mode": meta.get("mode", ""),
        "runner": meta.get("runner", ""),
        "runner_prefix": meta.get("runner_prefix", ""),
        "search_tool": meta.get("search_tool", ""),
        "errors": [{"line": e.line, "rule_id": e.rule_id, "message": e.message} for e in errors],
    }


def _read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _parse_front_matter(lines: List[str]) -> Tuple[Dict[str, str], Optional[LintError], int]:
    """Parse YAML front matter using pyyaml for robustness.

    Skips leading HTML comments (<!-- ... -->) before the YAML front matter.
    """
    if not lines:
        return {}, LintError(1, "R-ATL-001", "Empty file."), 0

    # Skip leading HTML comments
    start_idx = 0
    in_comment = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("<!--") and "-->" in stripped:
            # Single-line comment, skip it
            continue
        elif stripped.startswith("<!--"):
            in_comment = True
            continue
        elif in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        else:
            start_idx = i
            break

    if start_idx >= len(lines) or not RE_FM.match(lines[start_idx]):
        return {}, LintError(start_idx + 1, "R-ATL-001", f"Missing YAML front matter start '---' (found at line {start_idx + 1})."), 0

    end_idx = None
    for i in range(start_idx + 1, len(lines)):
        if RE_FM.match(lines[i]):
            end_idx = i
            break
    if end_idx is None:
        return {}, LintError(start_idx + 1, "R-ATL-001", "Missing YAML front matter end '---'."), 0

    yaml_content = "\n".join(lines[start_idx + 1:end_idx])
    try:
        parsed = yaml.safe_load(yaml_content)
        if parsed is None:
            parsed = {}
    except yaml.YAMLError as e:
        return {}, LintError(1, "R-ATL-001", f"Invalid YAML in front matter: {e}"), end_idx + 1

    if not isinstance(parsed, dict) or "ai_task_list" not in parsed:
        return {}, LintError(1, "R-ATL-001", "Front matter missing required 'ai_task_list:' block."), end_idx + 1

    ai_task_list = parsed.get("ai_task_list", {})
    if not isinstance(ai_task_list, dict):
        return {}, LintError(1, "R-ATL-001", "ai_task_list must be a mapping."), end_idx + 1

    # Convert all values to strings for consistency
    meta: Dict[str, str] = {k: str(v) if v is not None else "" for k, v in ai_task_list.items()}

    # R-ATL-001: Front matter required; R-ATL-070: Runner metadata required
    required = ["schema_version", "mode", "runner", "runner_prefix", "search_tool"]
    missing = [k for k in required if k not in meta]
    if missing:
        return meta, LintError(1, "R-ATL-001", f"ai_task_list missing required keys: {', '.join(missing)}"), end_idx + 1

    # Allow runner_prefix to be empty by design (e.g., go/cargo); other fields must be non-empty
    empties = [k for k in ["schema_version", "mode", "runner", "search_tool"] if meta.get(k, "") == ""]
    if empties:
        return meta, LintError(1, "R-ATL-001", f"ai_task_list missing required values: {', '.join(empties)}"), end_idx + 1

    # Enforce schema_version matches VERSION.yaml
    if meta["schema_version"] != FRAMEWORK_VERSION:
        return meta, LintError(1, "R-ATL-001", f"schema_version must be '{FRAMEWORK_VERSION}' (found '{meta['schema_version']}')."), end_idx + 1

    # Fix F: Validate search_tool (now required)
    if meta["search_tool"] not in ("rg", "grep"):
        return meta, LintError(1, "R-ATL-001", "search_tool must be 'rg' or 'grep'."), end_idx + 1

    if meta["mode"] not in ("template", "plan", "instantiated"):
        return meta, LintError(1, "R-ATL-002", "mode must be 'template', 'plan', or 'instantiated'."), end_idx + 1

    return meta, None, end_idx + 1


def _section_bounds(content: List[str], heading: str) -> Optional[Tuple[int, int]]:
    start = next((i for i, ln in enumerate(content) if ln == heading), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(content)) if content[i].startswith("## ")), len(content))
    return start, end


def _extract_fenced_code_block(block: List[str], start_idx: int) -> Optional[Tuple[int, int]]:
    """
    Return (fence_start_idx, fence_end_idx) within `block`, inclusive boundaries,
    for the first fenced code block starting at/after start_idx. Supports ```bash / ```.

    fence_end_idx points to the closing fence line.
    """
    fence_start = next((i for i in range(start_idx, len(block)) if block[i].strip().startswith("```")), None)
    if fence_start is None:
        return None
    fence_end = next((i for i in range(fence_start + 1, len(block)) if block[i].strip() == "```"), None)
    if fence_end is None:
        return None
    return fence_start, fence_end


def _get_all_fenced_blocks(content: List[str]) -> List[Tuple[int, int]]:
    """
    Return list of (start, end) line indices for all fenced code blocks in content.
    Both indices are inclusive (start is ```, end is closing ```).
    """
    blocks = []
    i = 0
    while i < len(content):
        if content[i].strip().startswith("```"):
            start = i
            # Find closing fence
            for j in range(i + 1, len(content)):
                if content[j].strip() == "```":
                    blocks.append((start, j))
                    i = j
                    break
            else:
                # Unclosed fence, skip to end
                break
        i += 1
    return blocks


def _is_inside_code_block(line_idx: int, code_blocks: List[Tuple[int, int]]) -> bool:
    """Check if line_idx is inside any fenced code block (inclusive of fences)."""
    for start, end in code_blocks:
        if start <= line_idx <= end:
            return True
    return False

def _is_inside_any_block(idx: int, blocks: List[Tuple[int, int]]) -> bool:
    return any(start <= idx <= end for start, end in blocks)


def _is_captured_header_line(stripped: str) -> bool:
    """Check if a line is a captured evidence header metadata line."""
    low = stripped.lower()
    return (
        low.startswith("# cmd:")
        or low.startswith("# exit:")
        or low.startswith("# ts_utc:")
        or low.startswith("# cwd:")
    )


def _is_stop_label_line(stripped: str) -> bool:
    """Check if a line is a STOP evidence section label."""
    return stripped in ("# Test run output:", "# Symbol/precondition check output:")


def _parse_coverage_entry(entry: str) -> List[str]:
    """
    Parse a coverage entry string into a list of task IDs.
    Allowed forms: single 'N.M', list 'N.M, X.Y', range 'N.M-P.Q' (same prefix).
    """
    refs: List[str] = []
    items = [itm.strip() for itm in entry.split(",") if itm.strip()]
    for itm in items:
        if "-" in itm:
            parts = itm.split("-")
            if len(parts) != 2:
                raise ValueError(f"invalid range '{itm}'")
            start, end = parts
            m1 = re.match(r"^(\d+)\.(\d+)$", start)
            m2 = re.match(r"^(\d+)\.(\d+)$", end)
            if not (m1 and m2):
                raise ValueError(f"invalid range endpoints in '{itm}'")
            p1, s1 = m1.group(1), int(m1.group(2))
            p2, s2 = m2.group(1), int(m2.group(2))
            if p1 != p2:
                raise ValueError(f"range '{itm}' crosses prefixes")
            if s1 > s2:
                raise ValueError(f"range '{itm}' is backward")
            refs.extend([f"{p1}.{k}" for k in range(s1, s2 + 1)])
        else:
            if not re.match(r"^\d+\.\d+$", itm):
                raise ValueError(f"invalid task id '{itm}'")
            refs.append(itm)
    return refs


def _check_evidence_non_empty(block_lines: List[str], label: Optional[str] = None) -> bool:
    """
    Check if evidence block has non-empty *output* content.
    
    - Ignores fenced markers (``` / ```lang)
    - Ignores captured-evidence header metadata lines (# cmd:, # exit:, # ts_utc:, # cwd:)
    - Ignores STOP section labels
    - If `label` is provided, checks lines after that label until the next labeled section
      or end of block.
    """
    if label:
        # Find label position
        label_idx = next((i for i, ln in enumerate(block_lines) if label in ln), None)
        if label_idx is None:
            return False
        # Check lines after label until next labeled section or end
        for i in range(label_idx + 1, len(block_lines)):
            ln = block_lines[i].strip()
            # Next labeled section (but not captured header metadata)
            if ln.startswith("#") and ":" in ln and not _is_captured_header_line(ln):
                break
            # Skip empty, fences, captured headers
            if not ln or ln == "```" or ln.startswith("```") or _is_captured_header_line(ln):
                continue
            # Found real output line
            return True
        return False
    else:
        # Check entire block (ignore fences, captured headers, and STOP labels)
        for ln in block_lines:
            stripped = ln.strip()
            if (
                stripped
                and stripped != "```"
                and not stripped.startswith("```")
                and not _is_captured_header_line(stripped)
                and not _is_stop_label_line(stripped)
            ):
                return True
        return False



def _check_command_output_pairs(block_lines: List[str]) -> List[int]:
    """
    Check that each $ command line has at least one non-empty output line after it.
    Returns list of line indices (relative to block) where output is missing.
    """
    missing = []
    i = 0
    while i < len(block_lines):
        ln = block_lines[i].strip()
        if ln.startswith("$"):
            # Found a command, check for output
            has_output = False
            for j in range(i + 1, len(block_lines)):
                next_ln = block_lines[j].strip()
                if next_ln.startswith("$"):
                    # Next command, no output found
                    break
                if next_ln == "```" or next_ln.startswith("```"):
                    # End of block
                    break
                # Captured header metadata does not count as output
                if next_ln and not _is_captured_header_line(next_ln):
                    has_output = True
                    break
            if not has_output:
                missing.append(i)
        i += 1
    return missing


def _check_captured_header(block_lines: List[str], require_exit_zero: bool = False) -> Optional[str]:
    """
    Check if evidence block contains captured evidence headers (# cmd: and # exit:).
    
    Args:
        block_lines: Lines of the evidence block
        require_exit_zero: If True, exit code must be 0
        
    Returns:
        None if valid, error message string if invalid
    """
    has_cmd = False
    has_exit = False
    exit_value = None
    
    for ln in block_lines:
        if RE_HDR_CMD.match(ln):
            has_cmd = True
        match = RE_HDR_EXIT.match(ln)
        if match:
            has_exit = True
            exit_value = int(match.group(1))
    
    if not has_cmd:
        return "missing '# cmd:' header"
    if not has_exit:
        return "missing '# exit:' header"
    if require_exit_zero and exit_value != 0:
        return f"exit must be 0 (found exit: {exit_value})"
    
    return None


def _check_captured_header_in_section(
    block_lines: List[str], 
    label: str, 
    require_exit_zero: bool = False
) -> Optional[str]:
    """
    Check captured evidence headers within a labeled section of an evidence block.
    
    Args:
        block_lines: Lines of the evidence block
        label: Section label to find (e.g., "# Test run output:")
        require_exit_zero: If True, exit code must be 0
        
    Returns:
        None if valid, error message string if invalid
    """
    # Find label position
    label_idx = next((i for i, ln in enumerate(block_lines) if label in ln), None)
    if label_idx is None:
        return f"section '{label}' not found"
    
    # Find section end (next # label or end of block)
    section_end = len(block_lines)
    for i in range(label_idx + 1, len(block_lines)):
        ln = block_lines[i].strip()
        if ln.startswith("#") and ":" in ln and not ln.startswith("# cmd") and not ln.startswith("# exit"):
            section_end = i
            break
    
    section_lines = block_lines[label_idx:section_end]
    return _check_captured_header(section_lines, require_exit_zero)


def lint(path: Path, require_captured_evidence: bool = False) -> Tuple[Dict[str, str], List[LintError]]:
    if not path.exists():
        return {}, [LintError(0, "R-LNT-002", f"File not found: {path}")]

    lines = _read_lines(path)
    meta, fm_err, content_start = _parse_front_matter(lines)
    if fm_err:
        return meta, [fm_err]

    content = lines[content_start:]
    errors: List[LintError] = []

    # Required headings
    found = {h: None for h in REQUIRED_HEADINGS}
    for idx, ln in enumerate(content, start=content_start + 1):
        if ln in found and found[ln] is None:
            found[ln] = idx
    missing = [h for h, lnno in found.items() if lnno is None]
    if missing:
        errors.append(LintError(content_start + 1, "R-ATL-010", f"Missing required heading(s): {', '.join(missing)}"))

    # R-ATL-033: Naming rule must be stated EXACTLY once
    # Look for the naming convention statement (not placeholder usage)
    # The naming rule pattern is prose like "Naming rule: Task ID N.M → TASK_N_M_PATHS"
    naming_rule_patterns = [
        r"Naming rule.*TASK_N_M_PATHS",
        r"Task\s+ID.*N\.M.*→.*TASK_N_M_PATHS",
    ]
    naming_rule_count = 0
    naming_rule_lines = []
    for idx, ln in enumerate(content):
        for pattern in naming_rule_patterns:
            if re.search(pattern, ln, re.IGNORECASE):
                naming_rule_count += 1
                naming_rule_lines.append(content_start + 1 + idx)
                break
    if naming_rule_count == 0:
        errors.append(LintError(content_start + 1, "R-ATL-033", 
            "Missing naming rule statement. Document must state: Task ID N.M → TASK_N_M_PATHS"))
    elif naming_rule_count > 1:
        errors.append(LintError(naming_rule_lines[1], "R-ATL-033", 
            f"Naming rule stated {naming_rule_count} times (must be exactly once). Lines: {naming_rule_lines}"))

    # Placeholder token validity
    for idx, ln in enumerate(content, start=content_start + 1):
        for m in re.finditer(r"\[\[PH:([^\]]+)\]\]", ln):
            token = m.group(0)
            if not RE_ALLOWED_PH.fullmatch(token):
                errors.append(LintError(idx, "R-ATL-003", f"Invalid placeholder token '{token}'. Allowed: [[PH:[A-Z0-9_]+]]."))

    # Instantiated mode: no placeholders
    if meta["mode"] == "instantiated":
        for idx, ln in enumerate(content, start=content_start + 1):
            if RE_ALLOWED_PH.search(ln):
                errors.append(LintError(idx, "R-ATL-002", "Placeholders are forbidden in instantiated mode (found [[PH:...]])."))
            for tok in STRICT_FORBIDDEN_TOKENS:
                if tok in ln:
                    errors.append(LintError(idx, "R-ATL-022", f"Evidence placeholder '{tok}' must not remain in instantiated mode."))

    # Baseline Snapshot checks
    baseline_heading = "## Baseline Snapshot (capture before any work)"
    b_bounds = _section_bounds(content, baseline_heading)
    if b_bounds:
        b_start, b_end = b_bounds
        sec = content[b_start:b_end]
        for label in BASELINE_ROW_LABELS:
            if not any(re.match(rf"^\|\s*{re.escape(label)}\s*\|", ln) for ln in sec):
                errors.append(LintError(content_start + 1 + b_start, "R-ATL-020", f"Baseline Snapshot missing table row label: '{label}'"))
        if not any("Evidence" in ln for ln in sec):
            errors.append(LintError(content_start + 1 + b_start, "R-ATL-021", "Baseline Snapshot missing 'Evidence' marker."))
        
        ev_marker_idx = next((i for i, ln in enumerate(sec) if "Evidence" in ln), None)
        if meta["mode"] in ("template", "plan", "instantiated") and ev_marker_idx is not None:
            fenced = _extract_fenced_code_block(sec, ev_marker_idx)
            if not fenced:
                errors.append(LintError(content_start + 1 + b_start + ev_marker_idx, "R-ATL-021", "Baseline Snapshot Evidence missing fenced code block."))
            else:
                f0, f1 = fenced
                ev_block = sec[f0:f1 + 1]
                if meta["mode"] == "template":
                    if not any("[[PH:OUTPUT]]" in ln for ln in ev_block):
                        errors.append(LintError(content_start + 1 + b_start + f0, "R-ATL-021", "Baseline Snapshot Evidence in template mode must include [[PH:OUTPUT]]."))
                if meta["mode"] == "instantiated":
                    missing_outputs = _check_command_output_pairs(ev_block)
                    if missing_outputs:
                        errors.append(LintError(content_start + 1 + b_start + f0, "R-ATL-023", 
                            "Baseline Snapshot evidence: command(s) missing output. Each $ command must have non-empty output."))
                    if not _check_evidence_non_empty(ev_block):
                        errors.append(LintError(content_start + 1 + b_start + f0, "R-ATL-023",
                            "Baseline Snapshot evidence block is empty in instantiated mode."))
                    if require_captured_evidence:
                        header_err = _check_captured_header(ev_block, require_exit_zero=False)
                        if header_err:
                            errors.append(LintError(content_start + 1 + b_start + f0, "R-ATL-024",
                                f"Baseline Snapshot evidence {header_err}."))
        # Baseline tests block required in all modes; stricter in plan/instantiated
        baseline_tests_idx = next((i for i, ln in enumerate(sec) if "Baseline tests" in ln), None)
        if baseline_tests_idx is None:
            errors.append(LintError(content_start + 1 + b_start, "R-ATL-021B",
                "Baseline Snapshot missing **Baseline tests** fenced block."))
        else:
            bt_fenced = _extract_fenced_code_block(sec, baseline_tests_idx)
            if not bt_fenced:
                errors.append(LintError(content_start + 1 + b_start + baseline_tests_idx, "R-ATL-021B",
                    "Baseline tests missing fenced code block."))
            else:
                bf0, bf1 = bt_fenced
                bt_block = sec[bf0:bf1 + 1]
                if meta["mode"] == "template":
                    if not any("[[PH:OUTPUT]]" in ln for ln in bt_block):
                        errors.append(LintError(content_start + 1 + b_start + bf0, "R-ATL-021B",
                            "Baseline tests in template mode must include [[PH:OUTPUT]] placeholder."))
                else:
                    if not any(ln.strip().startswith("$") for ln in bt_block):
                        errors.append(LintError(content_start + 1 + b_start + bf0, "R-ATL-021B",
                            "Baseline tests must include at least one $ command line."))
                    missing_bt_outputs = _check_command_output_pairs(bt_block)
                    if missing_bt_outputs:
                        errors.append(LintError(content_start + 1 + b_start + bf0, "R-ATL-021B",
                            "Baseline tests: command(s) missing output. Each $ command must have non-empty output."))
                    if not _check_evidence_non_empty(bt_block):
                        errors.append(LintError(content_start + 1 + b_start + bf0, "R-ATL-021B",
                            "Baseline tests evidence block is empty in instantiated mode."))

    # Phase Gate content enforcement (checklist items)
    stop_bounds = _section_bounds(content, "## STOP — Phase Gate")
    if stop_bounds:
        s_start, s_end = stop_bounds
        stop_sec = content[s_start:s_end]
        required_checks = [
            (".phase-N.complete.json", ".phase-N.complete.json exists"),
            ("Global Clean Table scan passes", "Global Clean Table scan passes"),
            ("Phase N tests pass", "Phase N tests pass"),
            ("Drift ledger current", "Drift ledger current"),
        ]
        for token, desc in required_checks:
            if not any(token in ln for ln in stop_sec):
                errors.append(LintError(content_start + 1 + s_start, "R-ATL-051",
                    f"STOP — Phase Gate missing checklist item: {desc}."))

    # Drift Ledger table columns + D3 evidence witness format for non-empty rows (instantiated)
    drift_heading = "## Drift Ledger (append-only)"
    d_bounds = _section_bounds(content, drift_heading)
    if d_bounds:
        d_start, d_end = d_bounds
        sec = content[d_start:d_end]
        table_rows = [(idx, ln) for idx, ln in enumerate(sec) if ln.strip().startswith("|")]
        header = table_rows[0][1] if table_rows else None
        if header is None:
            errors.append(LintError(content_start + 1 + d_start, "R-ATL-080", "Drift Ledger missing markdown table header row."))
        else:
            cols = [c.strip() for c in header.strip().strip("|").split("|")]
            miss = [c for c in DRIFT_LEDGER_COLUMNS if c not in cols]
            if miss:
                errors.append(LintError(content_start + 1 + d_start, "R-ATL-080", f"Drift Ledger missing column(s): {', '.join(miss)}"))
            else:
                if meta["mode"] == "instantiated":
                    ev_idx = cols.index("Evidence")
                    # iterate data rows after header + separator
                    for row_idx, row in table_rows[2:]:
                        parts = [c.strip() for c in row.strip().strip("|").split("|")]
                        # skip malformed rows (structure error is already caught elsewhere)
                        if len(parts) < len(cols):
                            continue
                        # allow fully empty template row
                        if all(p.strip() == "" for p in parts):
                            continue
                        evidence = parts[ev_idx].strip()
                        if RE_WITNESS_PATH_LINE.search(evidence) is None:
                            abs_line = content_start + 1 + d_start + row_idx
                            errors.append(LintError(abs_line, "R-ATL-D3", "Drift Ledger Evidence must include a witness in path:line form (e.g., src/x.py:123)."))

    # R-ATL-050: Phase Unlock Artifact content enforcement (v1.8: require $ command lines)
    p_heading = "## Phase Unlock Artifact"
    p_bounds = _section_bounds(content, p_heading)
    if p_bounds:
        p_start, p_end = p_bounds
        sec = content[p_start:p_end]
        sec_text = "\n".join(sec)
        
        # Check for fenced code block with artifact commands
        has_fenced_block = any(ln.strip().startswith("```") for ln in sec)
        
        # v1.8 FIX: Extract $ command lines from fenced code blocks
        dollar_cmd_lines = []
        for fenced in _get_all_fenced_blocks(sec):
            f_start, f_end = fenced
            for rel_idx in range(f_start + 1, f_end):
                if rel_idx < len(sec):
                    ln = sec[rel_idx].strip()
                    if ln.startswith("$"):
                        dollar_cmd_lines.append(ln)
        
        # Check for placeholder rejection scan as actual $ command line
        has_placeholder_scan_cmd = any(
            "rg" in cmd and ("[[PH:" in cmd or "\\[\\[PH" in cmd or "[PH:" in cmd)
            for cmd in dollar_cmd_lines
        )
        
        if meta["mode"] == "template":
            # Template mode: should have placeholders OR show the artifact generation process
            if not has_fenced_block:
                errors.append(LintError(content_start + 1 + p_start, "R-ATL-050",
                    "Phase Unlock Artifact section must include a fenced code block in template mode."))
            # Must show artifact file pattern
            artifact_pattern = re.search(r"\.phase-[N0-9]+\.complete\.json", sec_text, re.IGNORECASE)
            if not artifact_pattern:
                errors.append(LintError(content_start + 1 + p_start, "R-ATL-050",
                    "Phase Unlock Artifact must show artifact file pattern (e.g., .phase-N.complete.json)."))
        else:
            # Instantiated mode: must have actual artifact creation command
            # Require: cat > .phase-N.complete.json pattern (not just echo or mention)
            # v1.8: Check for $ cat > pattern in command lines
            has_cat_artifact = any(
                re.search(r"cat\s*>\s*\.phase-\d+\.complete\.json", cmd)
                for cmd in dollar_cmd_lines
            )
            if not has_cat_artifact:
                errors.append(LintError(content_start + 1 + p_start, "R-ATL-050",
                    "Phase Unlock Artifact must have '$ cat > .phase-N.complete.json' command (not comment or prose)."))
            # Should have a fenced code block with actual commands
            if not has_fenced_block:
                errors.append(LintError(content_start + 1 + p_start, "R-ATL-050",
                    "Phase Unlock Artifact should include a fenced code block with artifact generation commands."))
            # v1.8 FIX: Placeholder rejection scan must be actual $ rg command
            if not has_placeholder_scan_cmd:
                errors.append(LintError(content_start + 1 + p_start, "R-ATL-050",
                    "Phase Unlock Artifact must have '$ rg' command for placeholder rejection (not comment)."))

    # Global Clean Table Scan hooks
    g_heading = "## Global Clean Table Scan"
    g_bounds = _section_bounds(content, g_heading)
    if g_bounds:
        g_start, g_end = g_bounds
        sec = content[g_start:g_end]
        sec_text = "\n".join(sec)
        if meta["mode"] == "template":
            if not any("[[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]]" in ln for ln in sec):
                errors.append(LintError(content_start + 1 + g_start, "R-ATL-060", "Missing [[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]] in template mode."))
            if not any("[[PH:PASTE_CLEAN_TABLE_OUTPUT]]" in ln for ln in sec):
                errors.append(LintError(content_start + 1 + g_start, "R-ATL-060", "Missing [[PH:PASTE_CLEAN_TABLE_OUTPUT]] in template mode."))
        else:
            if meta["mode"] == "instantiated" and any("[[PH:PASTE_CLEAN_TABLE_OUTPUT]]" in ln for ln in sec):
                errors.append(LintError(content_start + 1 + g_start, "R-ATL-061", "Global Clean Table Scan output placeholder remains in instantiated mode."))
            
            # R-ATL-063: Import hygiene enforcement for Python projects (runner=uv)
            # v1.8 FIX: Must be actual $ command lines, not comments
            runner = meta.get("runner", "")
            if runner == "uv":
                # Extract $ command lines from fenced code blocks in this section
                dollar_cmd_lines = []
                for fenced in _get_all_fenced_blocks(sec):
                    f_start, f_end = fenced
                    for rel_idx in range(f_start + 1, f_end):
                        if rel_idx < len(sec):
                            ln = sec[rel_idx].strip()
                            if ln.startswith("$"):
                                dollar_cmd_lines.append(ln)
                
                # Check for multi-dot relative import pattern in $ command lines
                has_multidot_check = any(
                    re.search(r"rg\s+['\"]?from\s*\\*\.\\*\.", cmd) or 
                    re.search(r"rg\s+.*from\s*\.\.", cmd)
                    for cmd in dollar_cmd_lines
                )
                # Check for wildcard import pattern in $ command lines
                has_wildcard_check = any(
                    re.search(r"rg\s+['\"]?import\s*\\*\*", cmd) or
                    re.search(r"rg\s+.*import\s*\*", cmd)
                    for cmd in dollar_cmd_lines
                )
                
                if not has_multidot_check:
                    errors.append(LintError(content_start + 1 + g_start, "R-ATL-063",
                        "Python project (runner=uv) missing $ command line: rg 'from \\.\\.' for multi-dot relative imports."))
                if not has_wildcard_check:
                    errors.append(LintError(content_start + 1 + g_start, "R-ATL-063",
                        "Python project (runner=uv) missing $ command line: rg 'import \\*' for wildcard imports."))
            
            # R-ATL-023: Global Clean Table evidence must be non-empty
            ev_marker_idx = next((i for i, ln in enumerate(sec) if "Evidence" in ln), None)
            if ev_marker_idx is not None:
                fenced = _extract_fenced_code_block(sec, ev_marker_idx)
                if fenced:
                    f0, f1 = fenced
                    ev_block = sec[f0:f1 + 1]
                    if not _check_evidence_non_empty(ev_block):
                        errors.append(LintError(content_start + 1 + g_start + f0, "R-ATL-023",
                            "Global Clean Table evidence block is empty in instantiated mode."))
                    # R-ATL-024: Captured evidence headers (optional, enabled by flag)
                    # Global Clean Table requires exit: 0
                    if require_captured_evidence:
                        header_err = _check_captured_header(ev_block, require_exit_zero=True)
                        if header_err:
                            errors.append(LintError(content_start + 1 + g_start + f0, "R-ATL-024",
                                f"Global Clean Table evidence {header_err}."))
    else:
        if meta.get("mode") in ("plan", "instantiated"):
            errors.append(LintError(1, "R-ATL-NEW-03", "Global Clean Table Scan section missing (required for plan/instantiated modes)."))

    # Phase/Task parse
    phases: Dict[str, int] = {}
    tasks: Dict[str, int] = {}
    task_indices: List[Tuple[str, int]] = []

    code_blocks_all = _get_all_fenced_blocks(content)

    for i, ln in enumerate(content):
        if _is_inside_any_block(i, code_blocks_all):
            continue
        mp = RE_PHASE.match(ln)
        if mp:
            phases[mp.group(1)] = content_start + 1 + i
        mt = RE_TASK.match(ln)
        if mt:
            tid = f"{int(mt.group(1))}.{int(mt.group(2))}"
            if tid in tasks:
                errors.append(LintError(content_start + 1 + i, "R-ATL-NEW-01", f"Duplicate Task ID {tid} (previous line {tasks[tid]})."))
            tasks[tid] = content_start + 1 + i
            task_indices.append((tid, i))

    if "0" not in phases:
        errors.append(LintError(content_start + 1, "R-ATL-030", "Missing Phase 0 heading '## Phase 0 — Baseline Reality'."))

    # Task blocks
    task_blocks: Dict[str, Tuple[int, int]] = {}
    for idx, (tid, start_i) in enumerate(task_indices):
        end_i = len(content)
        if idx + 1 < len(task_indices):
            end_i = min(end_i, task_indices[idx + 1][1])
        for j in range(start_i + 1, len(content)):
            if content[j].startswith("## Phase "):
                end_i = min(end_i, j)
                break
        task_blocks[tid] = (start_i, end_i)

    for tid, (start_i, end_i) in task_blocks.items():
        block = content[start_i:end_i]
        start_line = content_start + 1 + start_i

        n_str, m_str = tid.split(".")
        expected = f"TASK_{n_str}_{m_str}_PATHS=("
        arr_rel = next((k for k, ln in enumerate(block) if ln.strip() == expected), None)
        if arr_rel is None:
            errors.append(LintError(start_line, "R-ATL-032", f"Task {tid} missing canonical paths array line: '{expected}'"))
        else:
            quoted = False
            closed = False
            for rel_k in range(arr_rel + 1, len(block)):
                ln = block[rel_k].strip()
                if RE_ARRAY_END.match(ln):
                    closed = True
                    break
                if RE_QUOTED_PATH.match(ln):
                    quoted = True
            if not closed:
                errors.append(LintError(start_line + arr_rel, "R-ATL-032", f"Task {tid} paths array not closed with ')'"))
            if not quoted:
                errors.append(LintError(start_line + arr_rel, "R-ATL-032", f"Task {tid} paths array contains no quoted paths."))

        # Status line enforcement (single value)
        status_value: Optional[str] = None
        status_rel_idx = next((k for k, ln in enumerate(block) if ln.strip().startswith("**Status**")), None)
        if status_rel_idx is not None:
            status_line = block[status_rel_idx].strip()
            m_status = re.match(r"^\*\*Status\*\*\s*:\s*(.+)$", status_line)
            if not m_status:
                errors.append(LintError(start_line + status_rel_idx, "R-ATL-090", "Status line must use '**Status**: <value>' format."))
            else:
                status_value = " ".join(m_status.group(1).split())
                if status_value not in ALLOWED_STATUS_VALUES:
                    errors.append(LintError(start_line + status_rel_idx, "R-ATL-090",
                        f"Status must be one of: {', '.join(ALLOWED_STATUS_VALUES)}."))
        else:
            errors.append(LintError(start_line, "R-ATL-090", "Task missing Status line ('**Status**: <status>')."))
        status_is_complete = status_value == "✅ COMPLETE"

        # Phase 0 tasks (bootstrap) are exempt from TDD/STOP requirements
        is_phase_0 = n_str == "0"

        if not is_phase_0:
            for h in (REQ_TDD_1, REQ_TDD_2, REQ_TDD_3):
                if h not in block:
                    errors.append(LintError(start_line, "R-ATL-040", f"Task {tid} missing heading: '{h}'"))

            if REQ_STOP not in block:
                errors.append(LintError(start_line, "R-ATL-041", f"Task {tid} missing STOP heading: '{REQ_STOP}'"))
            else:
                stop_i = block.index(REQ_STOP)
                stop_block = block[stop_i:]
                norm_lines = [" ".join(ln.strip().split()) for ln in stop_block]

                for prompt in NO_WEAK_TESTS_PROMPTS:
                    p = " ".join(prompt.split())
                    if not any(p in ln for ln in norm_lines):
                        errors.append(LintError(start_line + stop_i, "R-ATL-041", f"Task {tid} STOP missing No Weak Tests prompt: '{prompt}'"))

                # R-ATL-042: Clean Table checklist enforcement
                for prompt in CLEAN_TABLE_PROMPTS:
                    p = " ".join(prompt.split())
                    if not any(p in ln for ln in norm_lines):
                        errors.append(LintError(start_line + stop_i, "R-ATL-042", f"Task {tid} STOP missing Clean Table prompt: '{prompt}'"))

                # If task is marked complete, require checklists to be checked
                if status_is_complete and meta["mode"] == "instantiated":
                    for prompt in NO_WEAK_TESTS_PROMPTS + CLEAN_TABLE_PROMPTS:
                        p = " ".join(prompt.split())
                        rel_idx_prompt = next((i for i, ln in enumerate(stop_block) if p in " ".join(ln.strip().split())), None)
                        if rel_idx_prompt is None:
                            continue
                        if "[x]" not in stop_block[rel_idx_prompt].lower():
                            errors.append(LintError(start_line + stop_i + rel_idx_prompt, "R-ATL-091",
                                f"Task {tid} marked COMPLETE must check checkbox for: '{prompt}'"))

                # Evidence placeholders enforcement (existing v1 behavior)
                if meta["mode"] == "template":
                    if not any("[[PH:PASTE_TEST_OUTPUT]]" in ln for ln in stop_block):
                        errors.append(LintError(start_line + stop_i, "R-ATL-041", f"Task {tid} STOP missing [[PH:PASTE_TEST_OUTPUT]] in template mode."))
                    if not any("[[PH:PASTE_PRECONDITION_OUTPUT]]" in ln for ln in stop_block):
                        errors.append(LintError(start_line + stop_i, "R-ATL-041", f"Task {tid} STOP missing [[PH:PASTE_PRECONDITION_OUTPUT]] in template mode."))
                else:
                    for rel_k, ln in enumerate(stop_block):
                        if "[[PH:PASTE_TEST_OUTPUT]]" in ln or "[[PH:PASTE_PRECONDITION_OUTPUT]]" in ln:
                            errors.append(LintError(start_line + stop_i + rel_k, "R-ATL-022", f"Task {tid} STOP contains forbidden evidence placeholder in instantiated mode."))
                    
                    # R-ATL-023: STOP evidence must have both labels with real output in instantiated mode
                    # Find Evidence fenced block in stop_block
                    ev_marker_idx = next((k for k, ln in enumerate(stop_block) if "Evidence" in ln and "paste" in ln.lower()), None)
                    if ev_marker_idx is None:
                        # If marker is missing, still require a fenced evidence block from the top of STOP
                        ev_marker_idx = 0
                    if ev_marker_idx is not None:
                        fenced = _extract_fenced_code_block(stop_block, ev_marker_idx)
                        if fenced:
                            f0, f1 = fenced
                            ev_block = stop_block[f0:f1 + 1]
                            
                            # Gap A fix: Require both labeled sections always
                            test_label = "# Test run output:"
                            pre_label = "# Symbol/precondition check output:"
                            test_idx = next((i for i, ln in enumerate(ev_block) if test_label in ln), None)
                            pre_idx = next((i for i, ln in enumerate(ev_block) if pre_label in ln), None)
                            
                            missing_labels: List[str] = []
                            if test_idx is None:
                                missing_labels.append(test_label)
                            if pre_idx is None:
                                missing_labels.append(pre_label)
                            
                            if missing_labels:
                                errors.append(LintError(start_line + stop_i + f0, "R-ATL-023",
                                    f"Task {tid} STOP evidence missing required section label(s): {', '.join(missing_labels)}"))
                            else:
                                # Gap B fix: Check for real output (not just headers) under each label
                                if not _check_evidence_non_empty(ev_block, test_label):
                                    errors.append(LintError(start_line + stop_i + f0, "R-ATL-023",
                                        f"Task {tid} STOP Test run output is empty (must include real output lines, not only headers)."))
                                if not _check_evidence_non_empty(ev_block, pre_label):
                                    errors.append(LintError(start_line + stop_i + f0, "R-ATL-023",
                                        f"Task {tid} STOP Symbol/precondition check output is empty (must include real output lines, not only headers)."))
                            
                            # R-ATL-024: Captured evidence headers (optional, enabled by flag)
                            # STOP evidence requires exit: 0
                            if require_captured_evidence:
                                # Check Test run output section
                                test_header_err = _check_captured_header_in_section(ev_block, "# Test run output:", require_exit_zero=True)
                                if test_header_err:
                                    errors.append(LintError(start_line + stop_i + f0, "R-ATL-024",
                                        f"Task {tid} STOP Test run output {test_header_err}."))
                                # Check Symbol/precondition check output section
                                precond_header_err = _check_captured_header_in_section(ev_block, "# Symbol/precondition check output:", require_exit_zero=True)
                                if precond_header_err:
                                    errors.append(LintError(start_line + stop_i + f0, "R-ATL-024",
                                        f"Task {tid} STOP Symbol/precondition check output {precond_header_err}."))
                        else:
                            errors.append(LintError(start_line + stop_i, "R-ATL-023",
                                f"Task {tid} STOP evidence missing fenced code block."))

        # D2: Preconditions symbol-check command enforcement for non-Phase-0 tasks
        if not is_phase_0:
            pre_i = next((k for k, ln in enumerate(block) if "Preconditions" in ln), None)
            if pre_i is None:
                errors.append(LintError(start_line, "R-ATL-D2", f"Task {tid} missing Preconditions block (symbol check required)."))
            else:
                fenced = _extract_fenced_code_block(block, pre_i)
                if fenced is None:
                    errors.append(LintError(start_line + pre_i, "R-ATL-D2", f"Task {tid} Preconditions missing fenced code block with commands."))
                else:
                    f0, f1 = fenced
                    code_lines = block[f0:f1 + 1]
                    search_tool = meta.get("search_tool", "")
                    # template mode: require placeholder for symbol check
                    if meta["mode"] == "template":
                        if not any("[[PH:SYMBOL_CHECK_COMMAND]]" in ln for ln in code_lines):
                            errors.append(LintError(start_line + f0, "R-ATL-D2", f"Task {tid} Preconditions must include [[PH:SYMBOL_CHECK_COMMAND]] in template mode."))
                    else:
                        # plan/instantiated: require rg or grep pattern in Preconditions commands; no placeholders
                        if meta["mode"] == "plan" and any("[[PH:SYMBOL_CHECK_COMMAND]]" in ln for ln in code_lines):
                            tool_hint = search_tool or "rg/grep"
                            errors.append(LintError(start_line + f0, "R-ATL-D2", f"Task {tid} Preconditions must not use [[PH:SYMBOL_CHECK_COMMAND]] in plan mode. Use a real {tool_hint} command."))
                        # Skip comment lines (starting with #)
                        cmd_lines = []
                        for ln in code_lines:
                            stripped = ln.strip()
                            if stripped.startswith("#") or stripped.startswith("```"):
                                continue
                            if stripped.startswith("$"):
                                stripped = stripped[1:].strip()
                            cmd_lines.append(stripped)
                        if search_tool == "rg":
                            # Strict mode: only rg allowed
                            if not any(RE_SYMBOL_CMD_RG_ONLY.search(ln) for ln in cmd_lines):
                                errors.append(LintError(start_line + f0, "R-ATL-D2", f"Task {tid} Preconditions must include rg command (search_tool=rg)."))
                        else:
                            # Permissive mode: rg or grep allowed
                            if not any(RE_SYMBOL_CMD.search(ln) for ln in cmd_lines):
                                errors.append(LintError(start_line + f0, "R-ATL-D2", f"Task {tid} Preconditions must include a symbol-check command (rg/grep)."))

    # Runner enforcement
    if meta["mode"] in ("plan", "instantiated"):
        prefix = meta.get("runner_prefix", "")
        runner = meta.get("runner", "")
        
        # R-ATL-075: $ prefix mandatory for command lines in instantiated mode
        # This prevents bypassing runner enforcement by omitting $
        # Sections that MUST use $ for commands: Preconditions, TDD Verify, Phase Unlock, Global Scan
        code_blocks = _get_all_fenced_blocks(content)
        
        # Helper to check if a fenced block has command-like content without $
        def _check_dollar_prefix_in_section(sec_lines: List[str], section_name: str, sec_start: int):
            """Check that command-like lines in a section use $ prefix."""
            # Commands that indicate executable lines
            command_indicators = ["rg ", "grep ", "cat ", "echo ", "pytest", "python", "mypy", 
                                  "ruff", "black", "isort", "uv ", "git ", "cd ", "ls ", "mkdir ",
                                  "touch ", "rm ", "cp ", "mv ", "test ", "exit "]
            
            for fenced in _get_all_fenced_blocks(sec_lines):
                f_start, f_end = fenced
                for rel_idx in range(f_start + 1, f_end):
                    if rel_idx >= len(sec_lines):
                        break
                    ln = sec_lines[rel_idx].strip()
                    # Skip empty, fence markers, comments, pure output
                    if not ln or ln.startswith("```") or ln.startswith("#"):
                        continue
                    # Skip lines that look like output (no command indicators)
                    is_command_like = any(ln.startswith(cmd) or f" {cmd}" in ln for cmd in command_indicators)
                    if is_command_like and not ln.startswith("$"):
                        # This looks like a command but has no $ prefix
                        errors.append(LintError(sec_start + rel_idx + 1, "R-ATL-075",
                            f"{section_name}: command lines must start with '$' in instantiated mode."))
                        break  # One error per section is enough
        
        # Check Preconditions in each task
        for tid, t_idx in task_indices:
            n_str = tid.split(".")[0]
            if n_str == "0":
                continue  # Phase 0 exempt
            
            end_idx_task = next((j for j in range(t_idx + 1, len(content)) if RE_TASK.match(content[j]) or RE_PHASE.match(content[j])), len(content))
            task_block = content[t_idx:end_idx_task]
            
            pre_i = next((k for k, ln in enumerate(task_block) if "Preconditions" in ln), None)
            if pre_i is not None:
                # Find next section heading after Preconditions
                pre_end = next((k for k in range(pre_i + 1, len(task_block)) if task_block[k].startswith("###") or task_block[k].startswith("**")), len(task_block))
                _check_dollar_prefix_in_section(task_block[pre_i:pre_end], f"Task {tid} Preconditions", content_start + t_idx + pre_i)
            
            # Check TDD Step 3 — Verify
            verify_i = next((k for k, ln in enumerate(task_block) if "TDD Step 3" in ln), None)
            if verify_i is not None:
                stop_i = next((k for k, ln in enumerate(task_block) if "### STOP" in ln), len(task_block))
                verify_block = task_block[verify_i:stop_i]
                _check_dollar_prefix_in_section(verify_block, f"Task {tid} TDD Verify", content_start + t_idx + verify_i)
        
        # Check Phase Unlock Artifact
        p_bounds = _section_bounds(content, "## Phase Unlock Artifact")
        if p_bounds:
            p_start, p_end = p_bounds
            _check_dollar_prefix_in_section(content[p_start:p_end], "Phase Unlock Artifact", content_start + p_start)
        
        # Check Baseline Snapshot commands
        b_bounds_inst = _section_bounds(content, "## Baseline Snapshot (capture before any work)")
        if b_bounds_inst:
            b_start_inst, b_end_inst = b_bounds_inst
            _check_dollar_prefix_in_section(content[b_start_inst:b_end_inst], "Baseline Snapshot", content_start + b_start_inst)

        # Check Global Clean Table Scan
        g_bounds = _section_bounds(content, "## Global Clean Table Scan")
        if g_bounds:
            g_start, g_end = g_bounds
            _check_dollar_prefix_in_section(content[g_start:g_end], "Global Clean Table Scan", content_start + g_start)
        
        if prefix:
            # R-ATL-071: Check ONLY $ command lines in code blocks (not output lines)
            # Commands that need runner_prefix: pytest, python, mypy, ruff, black, isort
            runner_commands = ["pytest", "python", "mypy", "ruff", "black", "isort"]
            
            for idx, ln in enumerate(content):
                if not _is_inside_code_block(idx, code_blocks):
                    continue
                stripped = ln.strip()
                # Skip fence markers, comments, empty lines
                if stripped.startswith("```") or stripped.startswith("#") or not stripped:
                    continue
                # ONLY check lines that start with $ (command prompts)
                # Output lines (without $) are NOT checked - this prevents false positives
                if not stripped.startswith("$"):
                    continue
                # Extract the actual command after $
                cmd_line = stripped[1:].strip()
                # Check if line contains a runner command without prefix
                for cmd in runner_commands:
                    if cmd in cmd_line:
                        # Check if prefix is present in the command
                        if prefix not in cmd_line:
                            # Check if the command appears at start or after common shell operators
                            cmd_pattern = rf'(^|\s|&&|\|\||;)\s*{cmd}\b'
                            if re.search(cmd_pattern, cmd_line):
                                errors.append(LintError(content_start + 1 + idx, "R-ATL-071", 
                                    f"Command '{cmd}' must use runner_prefix '{prefix}'."))
                                break

        if runner == "uv":
            uv_cmd_lines: List[Tuple[int, str]] = []
            # Gap C fix: UV_FORBIDDEN only checked on $ command lines, not pasted output
            for idx, ln in enumerate(content):
                stripped = ln.strip()
                # Only check $ command lines inside code blocks
                if _is_inside_code_block(idx, code_blocks) and stripped.startswith("$"):
                    cmd_line = stripped[1:].strip()
                    uv_cmd_lines.append((idx, cmd_line))
                    for forb in UV_FORBIDDEN:
                        if forb in cmd_line:
                            errors.append(LintError(content_start + 1 + idx, "R-ATL-072", f"Forbidden under runner=uv: '{forb}'"))
            if not any("uv sync" in cmd for _, cmd in uv_cmd_lines):
                errors.append(LintError(content_start + 1, "R-ATL-072", "runner=uv requires '$ uv sync' command line in code blocks."))
            if not any("uv run" in cmd for _, cmd in uv_cmd_lines):
                errors.append(LintError(content_start + 1, "R-ATL-072", "runner=uv requires '$ uv run ...' command line in code blocks."))

        # D4: search_tool enforcement - grep forbidden when search_tool=rg
        # Only check inside fenced code blocks to avoid false positives on prose
        if meta.get("search_tool", "") == "rg":
            code_blocks = _get_all_fenced_blocks(content)
            for idx, ln in enumerate(content):
                # Only check lines inside code blocks
                if not _is_inside_code_block(idx, code_blocks):
                    continue
                # Skip fence markers and comment lines
                stripped = ln.strip()
                if stripped.startswith("```") or stripped.startswith("#"):
                    continue
                # Check for grep usage
                if RE_GREP_USAGE.search(ln):
                    # Avoid false positive on "ripgrep"
                    if "ripgrep" not in ln.lower():
                        errors.append(LintError(content_start + 1 + idx, "R-ATL-D4", 
                            f"grep is forbidden when search_tool=rg. Use ripgrep (rg) instead."))

    # Coverage Mapping integrity (R-ATL-NEW-02)
    if meta.get("mode") in ("plan", "instantiated"):
        pcm_bounds = _section_bounds(content, "## Prose Coverage Mapping")
        if not pcm_bounds:
            errors.append(LintError(1, "R-ATL-NEW-02", "Prose Coverage Mapping section required for plan/instantiated modes (missing)."))
        else:
            pcm_start, pcm_end = pcm_bounds
            pcm_sec = content[pcm_start:pcm_end]
            # Find first markdown table after the heading
            table_start = None
            pcm_body = pcm_sec[1:]  # skip heading line
            for idx, ln in enumerate(pcm_body):
                if ln.strip().startswith("|"):
                    table_start = idx
                    break
                # stop if we hit another heading
                if ln.startswith("#"):
                    break
            if table_start is None:
                errors.append(LintError(content_start + 1 + pcm_start, "R-ATL-NEW-02", "Prose Coverage Mapping table is empty or malformed (required in plan/instantiated)."))
            else:
                # Collect contiguous table lines
                table_lines: List[str] = []
                for j in range(table_start, len(pcm_body)):
                    ln = pcm_body[j]
                    if not ln.strip():
                        break
                    if ln.startswith("#"):
                        break
                    if ln.strip().startswith("|"):
                        table_lines.append(ln)
                    else:
                        break
                if len(table_lines) < 2:
                    errors.append(LintError(content_start + 1 + pcm_start + 1 + table_start, "R-ATL-NEW-02", "Prose Coverage Mapping table requires header and at least one data row."))
                else:
                    header = table_lines[0].strip().strip("|")
                    headers = [h.strip() for h in header.split("|")]
                    accepted = ["Implemented by Task(s)", "Implemented by Tasks", "Tasks", "Task IDs"]
                    col_idx = None
                    for idx, name in enumerate(headers):
                        if name in accepted:
                            if name == "Implemented by Task(s)":
                                col_idx = idx
                                break
                            if col_idx is None:
                                col_idx = idx
                    if col_idx is None:
                        errors.append(LintError(content_start + 1 + pcm_start + 1 + table_start, "R-ATL-NEW-02", "Prose Coverage Mapping missing Implemented-by column."))
                    else:
                        # Parse data rows
                        data_rows = table_lines[1:]
                        # Drop separator row if present
                        if data_rows and data_rows[0].strip().startswith("|-"):
                            data_rows = data_rows[1:]
                        for rel_row, row in enumerate(data_rows, start=1):
                            cells = [c.strip() for c in row.strip().strip("|").split("|")]
                            if col_idx >= len(cells):
                                errors.append(LintError(content_start + 1 + pcm_start + 1 + table_start + rel_row, "R-ATL-NEW-02", "Coverage table row missing Implemented-by cell."))
                                continue
                            cell = cells[col_idx]
                            try:
                                refs = _parse_coverage_entry(cell)
                            except ValueError as e:
                                errors.append(LintError(content_start + 1 + pcm_start + 1 + table_start + rel_row, "R-ATL-NEW-02", f"Coverage parse error: {e}"))
                                continue
                            for ref in refs:
                                count = list(tasks.keys()).count(ref)
                                if count == 0:
                                    errors.append(LintError(content_start + 1 + pcm_start + 1 + table_start + rel_row, "R-ATL-NEW-02", f"Coverage references task '{ref}' which does not exist."))
                                elif count > 1:
                                    errors.append(LintError(content_start + 1 + pcm_start + 1 + table_start + rel_row, "R-ATL-NEW-02", f"Task '{ref}' appears {count} times (ambiguous)."))

    return meta, errors


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="ai_task_list_linter.py")
    parser.add_argument("--version", action="version", version=f"%(prog)s {FRAMEWORK_VERSION}")
    parser.add_argument("path", help="Path to task list markdown file")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--require-captured-evidence", action="store_true",
                       help="Require captured evidence headers (# cmd:, # exit:) in evidence blocks")
    args = parser.parse_args(argv)

    try:
        meta, errors = lint(Path(args.path), require_captured_evidence=args.require_captured_evidence)
    except Exception as e:
        if args.json:
            print(json.dumps({"passed": False, "error_count": 1, "errors": [{"line": 0, "rule_id": "R-LNT-001", "message": f"Unhandled exception: {e}"}]}, indent=2))
        else:
            print(f"{args.path}:0:R-LNT-001:Unhandled exception: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(_json_report(Path(args.path), meta, errors), indent=2, sort_keys=True))
    else:
        for e in errors:
            print(f"{args.path}:{e.line}:{e.rule_id}:{e.message}", file=sys.stderr)

    return 0 if len(errors) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
