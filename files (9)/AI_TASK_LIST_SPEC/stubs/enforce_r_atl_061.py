"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-061
Check type: conditional (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_conditional


def enforce_r_atl_061(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-061: In instantiated mode, `[[PH:PASTE_CLEAN_TABLE_OUTPUT]]` MUST NOT remain"""
    return check_conditional(
        path, text,
        rule_id="R-ATL-061",
        mode="instantiated",
        condition="`[[PH:PASTE_CLEAN_TABLE_OUTPUT]]` MUST NOT remain",
        check_fn=None
    )
