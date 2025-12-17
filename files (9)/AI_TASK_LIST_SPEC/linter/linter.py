# ----------------------------------------------------------
#   AUTOMATICALLY GENERATED FILE — DO NOT EDIT BY HAND
#   Domain: ai_task_list
#   Spec: AI_TASK_LIST_SPEC (v2.0.0)
#   Generated from: linter_template.py.j2
# ----------------------------------------------------------

import sys
from pathlib import Path
from typing import List, Optional

# Import shared types from interfaces (SSOT)
from speksi.core.interfaces.models import LintError, LintResult

# Enforcement functions
from ..stubs.enforce_r_atl_000 import enforce_r_atl_000
from ..stubs.enforce_r_atl_001 import enforce_r_atl_001
from ..stubs.enforce_r_atl_002 import enforce_r_atl_002
from ..stubs.enforce_r_atl_003 import enforce_r_atl_003
from ..stubs.enforce_r_atl_010 import enforce_r_atl_010
from ..stubs.enforce_r_atl_011 import enforce_r_atl_011
from ..stubs.enforce_r_atl_020 import enforce_r_atl_020
from ..stubs.enforce_r_atl_021 import enforce_r_atl_021
from ..stubs.enforce_r_atl_022 import enforce_r_atl_022
from ..stubs.enforce_r_atl_023 import enforce_r_atl_023
from ..stubs.enforce_r_atl_024 import enforce_r_atl_024
from ..stubs.enforce_r_atl_030 import enforce_r_atl_030
from ..stubs.enforce_r_atl_031 import enforce_r_atl_031
from ..stubs.enforce_r_atl_032 import enforce_r_atl_032
from ..stubs.enforce_r_atl_033 import enforce_r_atl_033
from ..stubs.enforce_r_atl_040 import enforce_r_atl_040
from ..stubs.enforce_r_atl_041 import enforce_r_atl_041
from ..stubs.enforce_r_atl_042 import enforce_r_atl_042
from ..stubs.enforce_r_atl_050 import enforce_r_atl_050
from ..stubs.enforce_r_atl_051 import enforce_r_atl_051
from ..stubs.enforce_r_atl_060 import enforce_r_atl_060
from ..stubs.enforce_r_atl_061 import enforce_r_atl_061
from ..stubs.enforce_r_atl_063 import enforce_r_atl_063
from ..stubs.enforce_r_atl_070 import enforce_r_atl_070
from ..stubs.enforce_r_atl_071 import enforce_r_atl_071
from ..stubs.enforce_r_atl_072 import enforce_r_atl_072
from ..stubs.enforce_r_atl_075 import enforce_r_atl_075
from ..stubs.enforce_r_atl_080 import enforce_r_atl_080
from ..stubs.enforce_r_atl_090 import enforce_r_atl_090
from ..stubs.enforce_r_atl_091 import enforce_r_atl_091
from ..stubs.enforce_r_lnt_001 import enforce_r_lnt_001
from ..stubs.enforce_r_lnt_002 import enforce_r_lnt_002
from ..stubs.enforce_r_lnt_003 import enforce_r_lnt_003
from ..stubs.enforce_inv_mode_a import enforce_inv_mode_a
from ..stubs.enforce_inv_ssot_a import enforce_inv_ssot_a
from ..stubs.enforce_inv_evidence_a import enforce_inv_evidence_a
from ..stubs.enforce_inv_tdd_a import enforce_inv_tdd_a
from ..stubs.enforce_inv_clean_a import enforce_inv_clean_a


# ---------------------------------------------------------------------
# Error Formatting Helper
# ---------------------------------------------------------------------
def fmt_error(err: LintError, file: Path) -> str:
    """Format a LintError for CLI output."""
    return f"{file}:{err.line}: [{err.code}] {err.message}"


# ---------------------------------------------------------------------
# Rule & Invariant Dispatch Tables
# ---------------------------------------------------------------------
RULE_DISPATCH = {
    "R-ATL-000": enforce_r_atl_000,
    "R-ATL-001": enforce_r_atl_001,
    "R-ATL-002": enforce_r_atl_002,
    "R-ATL-003": enforce_r_atl_003,
    "R-ATL-010": enforce_r_atl_010,
    "R-ATL-011": enforce_r_atl_011,
    "R-ATL-020": enforce_r_atl_020,
    "R-ATL-021": enforce_r_atl_021,
    "R-ATL-022": enforce_r_atl_022,
    "R-ATL-023": enforce_r_atl_023,
    "R-ATL-024": enforce_r_atl_024,
    "R-ATL-030": enforce_r_atl_030,
    "R-ATL-031": enforce_r_atl_031,
    "R-ATL-032": enforce_r_atl_032,
    "R-ATL-033": enforce_r_atl_033,
    "R-ATL-040": enforce_r_atl_040,
    "R-ATL-041": enforce_r_atl_041,
    "R-ATL-042": enforce_r_atl_042,
    "R-ATL-050": enforce_r_atl_050,
    "R-ATL-051": enforce_r_atl_051,
    "R-ATL-060": enforce_r_atl_060,
    "R-ATL-061": enforce_r_atl_061,
    "R-ATL-063": enforce_r_atl_063,
    "R-ATL-070": enforce_r_atl_070,
    "R-ATL-071": enforce_r_atl_071,
    "R-ATL-072": enforce_r_atl_072,
    "R-ATL-075": enforce_r_atl_075,
    "R-ATL-080": enforce_r_atl_080,
    "R-ATL-090": enforce_r_atl_090,
    "R-ATL-091": enforce_r_atl_091,
    "R-LNT-001": enforce_r_lnt_001,
    "R-LNT-002": enforce_r_lnt_002,
    "R-LNT-003": enforce_r_lnt_003,
}

INV_DISPATCH = {
    "INV-MODE-A": enforce_inv_mode_a,
    "INV-SSOT-A": enforce_inv_ssot_a,
    "INV-EVIDENCE-A": enforce_inv_evidence_a,
    "INV-TDD-A": enforce_inv_tdd_a,
    "INV-CLEAN-A": enforce_inv_clean_a,
}

# ---------------------------------------------------------------------
# Phase Definitions
# ---------------------------------------------------------------------
PHASES = [
    {
        "name": "META",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "DEFINITIONS",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "Mode Variables",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "Structural Terms",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "Required Headings",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "RULES",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "INVARIANTS",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "PHASES",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "1: Front Matter Validation",
        "rules": ["R-ATL-001", "R-ATL-002", "R-ATL-003", "R-ATL-070"],
        "invariants": [],
    },
    {
        "name": "2: Structure Validation",
        "rules": ["R-ATL-010", "R-ATL-011", "R-ATL-020", "R-ATL-030", "R-ATL-050", "R-ATL-051", "R-ATL-060", "R-ATL-080"],
        "invariants": [],
    },
    {
        "name": "3: Task Validation",
        "rules": ["R-ATL-031", "R-ATL-032", "R-ATL-033", "R-ATL-040", "R-ATL-041", "R-ATL-042", "R-ATL-090"],
        "invariants": [],
    },
    {
        "name": "4: Mode-Specific Validation",
        "rules": ["R-ATL-021", "R-ATL-021", "R-ATL-022", "R-ATL-023", "R-ATL-061", "R-ATL-063", "R-ATL-071", "R-ATL-072", "R-ATL-075", "R-ATL-091"],
        "invariants": [],
    },
    {
        "name": "5: Output Generation",
        "rules": ["R-LNT-001", "R-LNT-002", "R-LNT-003"],
        "invariants": [],
    },
    {
        "name": "SCHEMAS",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "YAML Front Matter",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "Task Structure",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "Linter JSON Output",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "CLI COMMANDS",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "`ai_task_list_linter.py <file.md>`",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "APPENDICES",
        "rules": [],
        "invariants": [],
    },
]

# ---------------------------------------------------------------------
# Linter Implementation
# ---------------------------------------------------------------------
def lint(file_path: Path) -> LintResult:
    """Run all phases defined in the spec."""
    try:
        text = file_path.read_text()
    except FileNotFoundError:
        return LintResult(
            exit_code=2,
            errors=[LintError(0, "FILE-NOT-FOUND", f"Cannot open {file_path}")],
        )

    errors: List[LintError] = []

    for phase in PHASES:
        phase_name = phase["name"]

        # Run rules
        for rule_id in phase["rules"]:
            fn = RULE_DISPATCH.get(rule_id)
            if fn is None:
                errors.append(LintError(0, "INTERNAL", f"Missing enforcement function for {rule_id}"))
                continue

            try:
                phase_errors = fn(file_path, text)
            except Exception as e:
                errors.append(LintError(0, rule_id, f"Crash in enforcement: {e}"))
                continue

            errors.extend(phase_errors or [])

        # Run invariants
        for inv_id in phase["invariants"]:
            fn = INV_DISPATCH.get(inv_id)
            if fn is None:
                errors.append(LintError(0, "INTERNAL", f"Missing invariant enforcement for {inv_id}"))
                continue

            try:
                phase_errors = fn(file_path, text)
            except Exception as e:
                errors.append(LintError(0, inv_id, f"Crash in invariant: {e}"))
                continue

            errors.extend(phase_errors or [])

    exit_code = 0 if not errors else 1
    return LintResult(exit_code=exit_code, errors=errors)


# ---------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------
def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: ai_task_list_linter <file>")
        return 2

    path = Path(sys.argv[1])
    result = lint(path)

    for e in result.errors:
        print(fmt_error(e, path))

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
