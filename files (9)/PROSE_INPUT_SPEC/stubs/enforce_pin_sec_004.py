"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-SEC-004
Check type: heading (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_heading_exists


def enforce_pin_sec_004(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-SEC-004: Document MUST contain `### Out of Scope` subsection"""
    return check_heading_exists(
        path, text,
        rule_id="PIN-SEC-004",
        heading="### Out of Scope",
        exact_match=False
    )
