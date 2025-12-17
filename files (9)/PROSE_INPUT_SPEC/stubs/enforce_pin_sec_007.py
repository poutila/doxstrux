"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-SEC-007
Check type: heading (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_heading_exists


def enforce_pin_sec_007(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-SEC-007: Document MUST contain `## File Manifest` section"""
    return check_heading_exists(
        path, text,
        rule_id="PIN-SEC-007",
        heading="## File Manifest",
        exact_match=False
    )
