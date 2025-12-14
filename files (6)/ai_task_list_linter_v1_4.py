#!/usr/bin/env python3
"""
ai_task_list_linter_v1_4.py

Deterministic linter for AI Task Lists (Spec v1.2).

Version 1.4 changes (eliminates fake evidence loophole):
- NEW: --require-captured-evidence flag for evidence provenance validation
  - Requires # cmd: and # exit: headers in evidence blocks
  - STOP and Global Clean Table require exit: 0
- FIX: R-ATL-071 no longer false-positives on output lines (only checks $ command lines)
- FIX: R-ATL-033 now enforces "exactly once" not just "at least once"
- NEW: R-ATL-050 enforces Phase Unlock Artifact content (not just heading)

Version 1.3 features retained:
- R-ATL-023: Non-empty evidence required in instantiated mode
- D4: grep detection code-block-only
- D2: Preconditions symbol-check enforcement
- D3: Drift Ledger Evidence witness format

Base features:
- stdlib only
- deterministic (no network, no repo mutation)
- exit codes: 0=pass, 1=fail, 2=usage/internal error
- output:
  - default: path:line:rule_id:message
  - --json: machine report
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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
    if not lines or not RE_FM.match(lines[0]):
        return {}, LintError(1, "R-ATL-001", "Missing YAML front matter start '---' on line 1."), 0

    end_idx = None
    for i in range(1, len(lines)):
        if RE_FM.match(lines[i]):
            end_idx = i
            break
    if end_idx is None:
        return {}, LintError(1, "R-ATL-001", "Missing YAML front matter end '---'."), 0

    fm = lines[1:end_idx]
    meta: Dict[str, str] = {}

    try:
        root_i = next(i for i, ln in enumerate(fm) if ln.strip() == "ai_task_list:")
    except StopIteration:
        return {}, LintError(1, "R-ATL-001", "Front matter missing required 'ai_task_list:' block."), end_idx + 1

    for j in range(root_i + 1, len(fm)):
        ln = fm[j]
        if not ln.startswith("  "):
            break
        m = re.match(r"^\s{2}([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+?)\s*$", ln)
        if not m:
            continue
        key = m.group(1)
        val = m.group(2).strip()
        # Strip inline comments (# ...) before processing quotes
        if "#" in val:
            if val.startswith('"') and '"' in val[1:]:
                close_quote = val.index('"', 1)
                val = val[:close_quote + 1]
            elif val.startswith("'") and "'" in val[1:]:
                close_quote = val.index("'", 1)
                val = val[:close_quote + 1]
            else:
                val = val.split("#")[0].strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        meta[key] = val

    required = ["schema_version", "mode", "runner", "runner_prefix"]
    optional = ["search_tool"]  # Optional: "rg" or "grep"
    missing = [k for k in required if k not in meta or meta[k] == ""]
    if missing:
        return meta, LintError(1, "R-ATL-001", f"ai_task_list missing required keys or empty values: {', '.join(missing)}"), end_idx + 1

    # Validate search_tool if present
    if "search_tool" in meta and meta["search_tool"] not in ("rg", "grep", ""):
        return meta, LintError(1, "R-ATL-001", "search_tool must be 'rg' or 'grep'."), end_idx + 1

    if meta["mode"] not in ("template", "instantiated"):
        return meta, LintError(1, "R-ATL-002", "mode must be 'template' or 'instantiated'."), end_idx + 1

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


def _check_evidence_non_empty(block_lines: List[str], label: Optional[str] = None) -> bool:
    """
    Check if evidence block has non-empty content.
    If label is provided, check content after that label until next label or end.
    Otherwise check entire block for non-whitespace content.
    """
    if label:
        # Find label position
        label_idx = next((i for i, ln in enumerate(block_lines) if label in ln), None)
        if label_idx is None:
            return False
        # Check lines after label until next # label or end
        for i in range(label_idx + 1, len(block_lines)):
            ln = block_lines[i].strip()
            if ln.startswith("#") and not ln.startswith("##"):
                # Next label
                break
            if ln and ln != "```" and not ln.startswith("```"):
                return True
        return False
    else:
        # Check entire block
        for ln in block_lines:
            stripped = ln.strip()
            if stripped and stripped != "```" and not stripped.startswith("```"):
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
                if next_ln:
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
        
        # R-ATL-023: In instantiated mode, evidence must be non-empty
        if meta["mode"] == "instantiated":
            # Find Evidence fenced block
            ev_marker_idx = next((i for i, ln in enumerate(sec) if "Evidence" in ln), None)
            if ev_marker_idx is not None:
                fenced = _extract_fenced_code_block(sec, ev_marker_idx)
                if fenced:
                    f0, f1 = fenced
                    ev_block = sec[f0:f1 + 1]
                    # Check for $ command output pairs
                    missing_outputs = _check_command_output_pairs(ev_block)
                    if missing_outputs:
                        errors.append(LintError(content_start + 1 + b_start + f0, "R-ATL-023", 
                            "Baseline Snapshot evidence: command(s) missing output. Each $ command must have non-empty output."))
                    # Also check that there's at least some content
                    if not _check_evidence_non_empty(ev_block):
                        errors.append(LintError(content_start + 1 + b_start + f0, "R-ATL-023",
                            "Baseline Snapshot evidence block is empty in instantiated mode."))
                    # R-ATL-024: Captured evidence headers (optional, enabled by flag)
                    if require_captured_evidence:
                        header_err = _check_captured_header(ev_block, require_exit_zero=False)
                        if header_err:
                            errors.append(LintError(content_start + 1 + b_start + f0, "R-ATL-024",
                                f"Baseline Snapshot evidence {header_err}."))

    # Drift Ledger table columns + D3 evidence witness format for non-empty rows (instantiated)
    drift_heading = "## Drift Ledger (append-only)"
    d_bounds = _section_bounds(content, drift_heading)
    if d_bounds:
        d_start, d_end = d_bounds
        sec = content[d_start:d_end]
        table_rows = [ln for ln in sec if ln.strip().startswith("|")]
        header = table_rows[0] if table_rows else None
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
                    for row in table_rows[2:]:
                        parts = [c.strip() for c in row.strip().strip("|").split("|")]
                        # skip malformed rows (structure error is already caught elsewhere)
                        if len(parts) < len(cols):
                            continue
                        # allow fully empty template row
                        if all(p.strip() == "" for p in parts):
                            continue
                        evidence = parts[ev_idx].strip()
                        if RE_WITNESS_PATH_LINE.search(evidence) is None:
                            abs_line = content_start + 1 + d_start + sec.index(row)
                            errors.append(LintError(abs_line, "R-ATL-D3", "Drift Ledger Evidence must include a witness in path:line form (e.g., src/x.py:123)."))

    # R-ATL-050: Phase Unlock Artifact content enforcement
    p_heading = "## Phase Unlock Artifact"
    p_bounds = _section_bounds(content, p_heading)
    if p_bounds:
        p_start, p_end = p_bounds
        sec = content[p_start:p_end]
        sec_text = "\n".join(sec)
        # Must mention phase artifact file pattern
        has_artifact_pattern = (
            ".phase-" in sec_text.lower() or 
            "phase-" in sec_text.lower() and ".complete" in sec_text.lower() or
            "[[PH:" in sec_text  # Template mode placeholder is acceptable
        )
        # Must mention placeholder scan
        has_scan_mention = (
            "placeholder" in sec_text.lower() or
            "[[PH:" in sec_text.lower() or
            "rg" in sec_text or
            "scan" in sec_text.lower()
        )
        if meta["mode"] == "template":
            # Template mode: should have placeholders or describe the process
            if not has_artifact_pattern and not has_scan_mention:
                errors.append(LintError(content_start + 1 + p_start, "R-ATL-050",
                    "Phase Unlock Artifact section must describe artifact generation and placeholder scanning."))
        else:
            # Instantiated mode: must have concrete artifact reference
            if ".phase-" not in sec_text.lower() and "phase_" not in sec_text.lower():
                errors.append(LintError(content_start + 1 + p_start, "R-ATL-050",
                    "Phase Unlock Artifact must reference phase artifact file (e.g., .phase-N.complete.json)."))

    # Global Clean Table Scan hooks
    g_heading = "## Global Clean Table Scan"
    g_bounds = _section_bounds(content, g_heading)
    if g_bounds:
        g_start, g_end = g_bounds
        sec = content[g_start:g_end]
        if meta["mode"] == "template":
            if not any("[[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]]" in ln for ln in sec):
                errors.append(LintError(content_start + 1 + g_start, "R-ATL-060", "Missing [[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]] in template mode."))
            if not any("[[PH:PASTE_CLEAN_TABLE_OUTPUT]]" in ln for ln in sec):
                errors.append(LintError(content_start + 1 + g_start, "R-ATL-060", "Missing [[PH:PASTE_CLEAN_TABLE_OUTPUT]] in template mode."))
        else:
            if any("[[PH:PASTE_CLEAN_TABLE_OUTPUT]]" in ln for ln in sec):
                errors.append(LintError(content_start + 1 + g_start, "R-ATL-061", "Global Clean Table Scan output placeholder remains in instantiated mode."))
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

    # Phase/Task parse
    phases: Dict[str, int] = {}
    tasks: Dict[str, int] = {}
    task_indices: List[Tuple[str, int]] = []

    for i, ln in enumerate(content):
        mp = RE_PHASE.match(ln)
        if mp:
            phases[mp.group(1)] = content_start + 1 + i
        mt = RE_TASK.match(ln)
        if mt:
            tid = f"{int(mt.group(1))}.{int(mt.group(2))}"
            if tid in tasks:
                errors.append(LintError(content_start + 1 + i, "R-ATL-031", f"Duplicate Task ID {tid} (previous line {tasks[tid]})."))
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
                    
                    # R-ATL-023: STOP evidence must be non-empty in instantiated mode
                    # Find Evidence fenced block in stop_block
                    ev_marker_idx = next((k for k, ln in enumerate(stop_block) if "Evidence" in ln and "paste" in ln.lower()), None)
                    if ev_marker_idx is not None:
                        fenced = _extract_fenced_code_block(stop_block, ev_marker_idx)
                        if fenced:
                            f0, f1 = fenced
                            ev_block = stop_block[f0:f1 + 1]
                            # Check for labeled sections
                            has_test_output = _check_evidence_non_empty(ev_block, "# Test run output:")
                            has_precond_output = _check_evidence_non_empty(ev_block, "# Symbol/precondition check output:")
                            # Fallback: check entire block if no labels
                            if not has_test_output and not has_precond_output:
                                if not _check_evidence_non_empty(ev_block):
                                    errors.append(LintError(start_line + stop_i + f0, "R-ATL-023",
                                        f"Task {tid} STOP evidence block is empty in instantiated mode."))
                            
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
                    # template mode: require placeholder for symbol check
                    if meta["mode"] == "template":
                        if not any("[[PH:SYMBOL_CHECK_COMMAND]]" in ln for ln in code_lines):
                            errors.append(LintError(start_line + f0, "R-ATL-D2", f"Task {tid} Preconditions must include [[PH:SYMBOL_CHECK_COMMAND]] in template mode."))
                    else:
                        # instantiated: require rg or grep pattern in Preconditions commands
                        # Skip comment lines (starting with #)
                        cmd_lines = [ln for ln in code_lines if not ln.strip().startswith("#")]
                        search_tool = meta.get("search_tool", "")
                        if search_tool == "rg":
                            # Strict mode: only rg allowed
                            if not any(RE_SYMBOL_CMD_RG_ONLY.search(ln) for ln in cmd_lines):
                                errors.append(LintError(start_line + f0, "R-ATL-D2", f"Task {tid} Preconditions must include rg command (search_tool=rg)."))
                        else:
                            # Permissive mode: rg or grep allowed
                            if not any(RE_SYMBOL_CMD.search(ln) for ln in cmd_lines):
                                errors.append(LintError(start_line + f0, "R-ATL-D2", f"Task {tid} Preconditions must include a symbol-check command (rg/grep)."))

    # Runner enforcement
    if meta["mode"] == "instantiated":
        prefix = meta.get("runner_prefix", "")
        runner = meta.get("runner", "")
        
        if prefix:
            # R-ATL-071: Check ONLY $ command lines in code blocks (not output lines)
            # Commands that need runner_prefix: pytest, python, mypy, ruff, black, isort
            runner_commands = ["pytest", "python", "mypy", "ruff", "black", "isort"]
            
            code_blocks = _get_all_fenced_blocks(content)
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
            doc = "\n".join(content)
            for idx, ln in enumerate(content, start=content_start + 1):
                for forb in UV_FORBIDDEN:
                    if forb in ln:
                        errors.append(LintError(idx, "R-ATL-072", f"Forbidden under runner=uv: '{forb}'"))
            if "uv sync" not in doc:
                errors.append(LintError(content_start + 1, "R-ATL-072", "runner=uv requires at least one occurrence of 'uv sync'."))
            if "uv run" not in doc:
                errors.append(LintError(content_start + 1, "R-ATL-072", "runner=uv requires at least one occurrence of 'uv run'."))

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

    return meta, errors


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="ai_task_list_linter_v1_4.py")
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
