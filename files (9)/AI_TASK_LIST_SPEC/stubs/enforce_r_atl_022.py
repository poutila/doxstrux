"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-022
Check type: conditional (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_conditional


def enforce_r_atl_022(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-022: In instantiated mode, linter MUST fail if any `[[PH:...]]` tokens remain"""
    return check_conditional(
        path, text,
        rule_id="R-ATL-022",
        mode="instantiated",
        condition="linter MUST fail if any `[[PH:...]]` tokens remain",
        check_fn=None
    )
