"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-SEC-001
Check type: heading (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_heading_exists


def enforce_pin_sec_001(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-SEC-001: Document MUST contain `## SSOT Declaration` section"""
    return check_heading_exists(
        path, text,
        rule_id="PIN-SEC-001",
        heading="## SSOT Declaration",
        exact_match=False
    )
