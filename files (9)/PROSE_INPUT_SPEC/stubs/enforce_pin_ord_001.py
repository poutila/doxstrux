"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-ORD-001
Check type: ordering (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_section_order


def enforce_pin_ord_001(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-ORD-001: Sections MUST appear in order PIN-SEC-001 to PIN-SEC-009; preceding section before succeeding"""
    return check_section_order(
        path, text,
        rule_id="PIN-ORD-001",
        required_order=[],
        heading_level=2
    )
