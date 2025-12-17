"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-023
Check type: conditional (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_conditional


def enforce_r_atl_023(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-023: In instantiated mode, required evidence slots MUST contain real output lines"""
    return check_conditional(
        path, text,
        rule_id="R-ATL-023",
        mode="instantiated",
        condition="required evidence slots MUST contain real output lines",
        check_fn=None
    )
