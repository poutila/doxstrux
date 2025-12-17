"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-FBN-002
Check type: forbidden (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_forbidden_patterns


def enforce_pin_fbn_002(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-FBN-002: Document MUST NOT contain `[[PLACEHOLDER]]` tokens (except `[[PH:...]]` reserved format)"""
    return check_forbidden_patterns(
        path, text,
        rule_id="PIN-FBN-002",
        patterns=["[[PLACEHOLDER]]` tokens (except `[[PH:"],
        case_insensitive=True
    )
