"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-FBN-001
Check type: forbidden (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_forbidden_patterns


def enforce_pin_fbn_001(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-FBN-001: Document MUST NOT contain: TBD, TODO, TBC, FIXME, XXX (case-insensitive)"""
    return check_forbidden_patterns(
        path, text,
        rule_id="PIN-FBN-001",
        patterns=["TBD", "TODO", "TBC", "FIXME", "XXX (case-insensitive)"],
        case_insensitive=True
    )
