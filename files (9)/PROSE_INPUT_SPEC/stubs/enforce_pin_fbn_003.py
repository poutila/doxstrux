"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-FBN-003
Check type: line_ending (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_line_ending


def enforce_pin_fbn_003(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-FBN-003: Lines MUST NOT end with single `?` (except `??` in code)"""
    return check_line_ending(
        path, text,
        rule_id="PIN-FBN-003",
        forbidden_suffix="single `?` (except `??` in code)",
        required_suffix=None,
        line_pattern=None
    )
