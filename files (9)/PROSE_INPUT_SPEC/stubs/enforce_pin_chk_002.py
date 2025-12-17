"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-CHK-002
Check type: checkbox (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_checkbox_state


def enforce_pin_chk_002(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-CHK-002: All checklist items MUST be checked `[x]` before document is valid"""
    return check_checkbox_state(
        path, text,
        rule_id="PIN-CHK-002",
        checkbox_label=None,
        must_be_checked=True
    )
