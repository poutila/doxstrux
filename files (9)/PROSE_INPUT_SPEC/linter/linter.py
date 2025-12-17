# ----------------------------------------------------------
#   AUTOMATICALLY GENERATED FILE — DO NOT EDIT BY HAND
#   Domain: prose_input
#   Spec: PROSE_INPUT_SPEC (v2.0.0)
#   Generated from: linter_template.py.j2
# ----------------------------------------------------------

import sys
from pathlib import Path
from typing import List, Optional

# Import shared types from interfaces (SSOT)
from speksi.core.interfaces.models import LintError, LintResult

# Enforcement functions
from ..stubs.enforce_pin_ssot_001 import enforce_pin_ssot_001
from ..stubs.enforce_pin_ssot_002 import enforce_pin_ssot_002
from ..stubs.enforce_pin_yml_001 import enforce_pin_yml_001
from ..stubs.enforce_pin_yml_002 import enforce_pin_yml_002
from ..stubs.enforce_pin_yml_003 import enforce_pin_yml_003
from ..stubs.enforce_pin_yml_004 import enforce_pin_yml_004
from ..stubs.enforce_pin_yml_005 import enforce_pin_yml_005
from ..stubs.enforce_pin_yml_006 import enforce_pin_yml_006
from ..stubs.enforce_pin_yml_007 import enforce_pin_yml_007
from ..stubs.enforce_pin_yml_008 import enforce_pin_yml_008
from ..stubs.enforce_pin_sec_001 import enforce_pin_sec_001
from ..stubs.enforce_pin_sec_002 import enforce_pin_sec_002
from ..stubs.enforce_pin_sec_003 import enforce_pin_sec_003
from ..stubs.enforce_pin_sec_004 import enforce_pin_sec_004
from ..stubs.enforce_pin_sec_005 import enforce_pin_sec_005
from ..stubs.enforce_pin_sec_006 import enforce_pin_sec_006
from ..stubs.enforce_pin_sec_007 import enforce_pin_sec_007
from ..stubs.enforce_pin_sec_008 import enforce_pin_sec_008
from ..stubs.enforce_pin_sec_009 import enforce_pin_sec_009
from ..stubs.enforce_pin_sec_010 import enforce_pin_sec_010
from ..stubs.enforce_pin_sec_011 import enforce_pin_sec_011
from ..stubs.enforce_pin_sec_012 import enforce_pin_sec_012
from ..stubs.enforce_pin_ord_001 import enforce_pin_ord_001
from ..stubs.enforce_pin_fbn_001 import enforce_pin_fbn_001
from ..stubs.enforce_pin_fbn_002 import enforce_pin_fbn_002
from ..stubs.enforce_pin_fbn_003 import enforce_pin_fbn_003
from ..stubs.enforce_pin_fbn_004 import enforce_pin_fbn_004
from ..stubs.enforce_pin_fbn_005 import enforce_pin_fbn_005
from ..stubs.enforce_pin_fbn_006 import enforce_pin_fbn_006
from ..stubs.enforce_pin_fbn_007 import enforce_pin_fbn_007
from ..stubs.enforce_pin_ctx_001 import enforce_pin_ctx_001
from ..stubs.enforce_pin_tsk_001 import enforce_pin_tsk_001
from ..stubs.enforce_pin_tsk_002 import enforce_pin_tsk_002
from ..stubs.enforce_pin_tsk_003 import enforce_pin_tsk_003
from ..stubs.enforce_pin_tsk_004 import enforce_pin_tsk_004
from ..stubs.enforce_pin_dec_001 import enforce_pin_dec_001
from ..stubs.enforce_pin_dec_002 import enforce_pin_dec_002
from ..stubs.enforce_pin_man_001 import enforce_pin_man_001
from ..stubs.enforce_pin_chk_001 import enforce_pin_chk_001
from ..stubs.enforce_pin_chk_002 import enforce_pin_chk_002
from ..stubs.enforce_pin_lnt_001 import enforce_pin_lnt_001
from ..stubs.enforce_pin_lnt_002 import enforce_pin_lnt_002
from ..stubs.enforce_pin_lnt_003 import enforce_pin_lnt_003
from ..stubs.enforce_pin_lnt_004 import enforce_pin_lnt_004
from ..stubs.enforce_pin_sev_001 import enforce_pin_sev_001
from ..stubs.enforce_inv_ssot_a import enforce_inv_ssot_a
from ..stubs.enforce_inv_complete_a import enforce_inv_complete_a
from ..stubs.enforce_inv_decision_a import enforce_inv_decision_a
from ..stubs.enforce_inv_facts_a import enforce_inv_facts_a
from ..stubs.enforce_inv_determinism_a import enforce_inv_determinism_a


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
    "PIN-SSOT-001": enforce_pin_ssot_001,
    "PIN-SSOT-002": enforce_pin_ssot_002,
    "PIN-YML-001": enforce_pin_yml_001,
    "PIN-YML-002": enforce_pin_yml_002,
    "PIN-YML-003": enforce_pin_yml_003,
    "PIN-YML-004": enforce_pin_yml_004,
    "PIN-YML-005": enforce_pin_yml_005,
    "PIN-YML-006": enforce_pin_yml_006,
    "PIN-YML-007": enforce_pin_yml_007,
    "PIN-YML-008": enforce_pin_yml_008,
    "PIN-SEC-001": enforce_pin_sec_001,
    "PIN-SEC-002": enforce_pin_sec_002,
    "PIN-SEC-003": enforce_pin_sec_003,
    "PIN-SEC-004": enforce_pin_sec_004,
    "PIN-SEC-005": enforce_pin_sec_005,
    "PIN-SEC-006": enforce_pin_sec_006,
    "PIN-SEC-007": enforce_pin_sec_007,
    "PIN-SEC-008": enforce_pin_sec_008,
    "PIN-SEC-009": enforce_pin_sec_009,
    "PIN-SEC-010": enforce_pin_sec_010,
    "PIN-SEC-011": enforce_pin_sec_011,
    "PIN-SEC-012": enforce_pin_sec_012,
    "PIN-ORD-001": enforce_pin_ord_001,
    "PIN-FBN-001": enforce_pin_fbn_001,
    "PIN-FBN-002": enforce_pin_fbn_002,
    "PIN-FBN-003": enforce_pin_fbn_003,
    "PIN-FBN-004": enforce_pin_fbn_004,
    "PIN-FBN-005": enforce_pin_fbn_005,
    "PIN-FBN-006": enforce_pin_fbn_006,
    "PIN-FBN-007": enforce_pin_fbn_007,
    "PIN-CTX-001": enforce_pin_ctx_001,
    "PIN-TSK-001": enforce_pin_tsk_001,
    "PIN-TSK-002": enforce_pin_tsk_002,
    "PIN-TSK-003": enforce_pin_tsk_003,
    "PIN-TSK-004": enforce_pin_tsk_004,
    "PIN-DEC-001": enforce_pin_dec_001,
    "PIN-DEC-002": enforce_pin_dec_002,
    "PIN-MAN-001": enforce_pin_man_001,
    "PIN-CHK-001": enforce_pin_chk_001,
    "PIN-CHK-002": enforce_pin_chk_002,
    "PIN-LNT-001": enforce_pin_lnt_001,
    "PIN-LNT-002": enforce_pin_lnt_002,
    "PIN-LNT-003": enforce_pin_lnt_003,
    "PIN-LNT-004": enforce_pin_lnt_004,
    "PIN-SEV-001": enforce_pin_sev_001,
}

INV_DISPATCH = {
    "INV-SSOT-A": enforce_inv_ssot_a,
    "INV-COMPLETE-A": enforce_inv_complete_a,
    "INV-DECISION-A": enforce_inv_decision_a,
    "INV-FACTS-A": enforce_inv_facts_a,
    "INV-DETERMINISM-A": enforce_inv_determinism_a,
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
        "name": "Document Terms",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "Configuration Terms",
        "rules": [],
        "invariants": [],
    },
    {
        "name": "Required Sections",
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
        "name": "1: YAML Validation",
        "rules": ["PIN-YML-001", "PIN-YML-002", "PIN-YML-003", "PIN-YML-004", "PIN-YML-005", "PIN-YML-006", "PIN-YML-007", "PIN-YML-008"],
        "invariants": [],
    },
    {
        "name": "2: Section Validation",
        "rules": ["PIN-SEC-001", "PIN-SEC-002", "PIN-SEC-003", "PIN-SEC-004", "PIN-SEC-005", "PIN-SEC-006", "PIN-SEC-007", "PIN-SEC-008", "PIN-SEC-009", "PIN-SEC-010", "PIN-SEC-011", "PIN-SEC-012", "PIN-ORD-001"],
        "invariants": [],
    },
    {
        "name": "3: Forbidden Pattern Scan",
        "rules": ["PIN-FBN-001", "PIN-FBN-002", "PIN-FBN-003", "PIN-FBN-004", "PIN-FBN-005", "PIN-FBN-006", "PIN-FBN-007"],
        "invariants": [],
    },
    {
        "name": "4: Context-Specific Validation",
        "rules": ["PIN-CTX-001", "PIN-TSK-001", "PIN-TSK-002", "PIN-TSK-003", "PIN-TSK-004"],
        "invariants": [],
    },
    {
        "name": "5: Table Validation",
        "rules": ["PIN-DEC-001", "PIN-DEC-002", "PIN-MAN-001"],
        "invariants": [],
    },
    {
        "name": "6: Checklist Validation",
        "rules": ["PIN-CHK-001", "PIN-CHK-002"],
        "invariants": [],
    },
    {
        "name": "7: Output Generation",
        "rules": ["PIN-LNT-001", "PIN-LNT-002", "PIN-LNT-003", "PIN-LNT-004", "PIN-SEV-001"],
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
        "name": "Decisions Table",
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
        "name": "`prose_input_linter.py <file.md>`",
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
        print("Usage: prose_input_linter <file>")
        return 2

    path = Path(sys.argv[1])
    result = lint(path)

    for e in result.errors:
        print(fmt_error(e, path))

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
