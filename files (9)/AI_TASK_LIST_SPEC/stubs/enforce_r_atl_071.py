"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-071
Check type: conditional (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_conditional


def enforce_r_atl_071(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-071: In instantiated mode with non-empty runner_prefix, tool invocations MUST include prefix"""
    return check_conditional(
        path, text,
        rule_id="R-ATL-071",
        mode="instantiated",
        condition="with non-empty runner_prefix, tool invocations MUST include prefix",
        check_fn=None
    )
