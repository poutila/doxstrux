"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-003
Check type: placeholder (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_placeholder_tokens


def enforce_r_atl_003(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-003: Only `[[PH:NAME]]` placeholders recognized, NAME matching `[A-Z0-9_]+`"""
    return check_placeholder_tokens(
        path, text,
        rule_id="R-ATL-003",
        allowed_pattern="\[\[PH:([A-Z_]+)\]\]",
        forbidden_patterns=None
    )
