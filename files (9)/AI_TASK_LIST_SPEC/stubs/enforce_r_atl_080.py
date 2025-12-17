"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-080
Check type: table (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_table_columns


def enforce_r_atl_080(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-080: Drift Ledger MUST contain table with Date, Higher, Lower, Mismatch, Resolution, Evidence columns"""
    return check_table_columns(
        path, text,
        rule_id="R-ATL-080",
        required_columns=["Date", "Higher", "Lower", "Mismatch", "Resolution", "Evidence columns"],
        table_identifier=None
    )
