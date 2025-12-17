"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-TSK-001
Check type: min_count (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_min_count


def enforce_pin_tsk_001(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-TSK-001: Document MUST contain at least one task matching `#### Task N.M — Name`"""
    # NOTE: extraction_pattern needs to be customized for your specific use case
    # This default counts lines matching a simple pattern
    return check_min_count(
        path, text,
        rule_id="PIN-TSK-001",
        extraction_pattern=r"^\s*[-*]\s+",  # Bullet points
        min_count=1,
        item_name="item"
    )
