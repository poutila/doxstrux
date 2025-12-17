"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-DEC-002
Check type: table (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_table_columns


def enforce_pin_dec_002(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-DEC-002: Decisions table MUST contain columns: ID, Decision, Rationale"""
    return check_table_columns(
        path, text,
        rule_id="PIN-DEC-002",
        required_columns=["ID", "Decision", "Rationale"],
        table_identifier=None
    )
