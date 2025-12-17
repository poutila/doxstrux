"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-091
Check type: checkbox (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_checkbox_state


def enforce_r_atl_091(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-091: If task is COMPLETE and instantiated, all checklist items in STOP block MUST be checked"""
    return check_checkbox_state(
        path, text,
        rule_id="R-ATL-091",
        checkbox_label=None,
        must_be_checked=True
    )
