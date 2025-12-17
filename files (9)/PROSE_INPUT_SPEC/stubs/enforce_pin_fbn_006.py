"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-FBN-006
Check type: forbidden (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_forbidden_patterns


def enforce_pin_fbn_006(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-FBN-006: Document MUST NOT contain time estimates: 2-3 hours, 1-2 days, etc."""
    return check_forbidden_patterns(
        path, text,
        rule_id="PIN-FBN-006",
        patterns=["time estimates: 2-3 hours", "1-2 days", "etc"],
        case_insensitive=True
    )
