"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-FBN-007
Check type: forbidden (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_forbidden_patterns


def enforce_pin_fbn_007(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-FBN-007: Document MUST NOT contain pending decision phrases: pending, to be decided, TBD by"""
    return check_forbidden_patterns(
        path, text,
        rule_id="PIN-FBN-007",
        patterns=["pending decision phrases: pending", "to be decided", "TBD by"],
        case_insensitive=True
    )
