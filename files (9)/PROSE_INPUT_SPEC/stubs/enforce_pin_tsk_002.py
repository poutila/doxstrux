"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-TSK-002
Check type: unique (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_unique


def enforce_pin_tsk_002(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-TSK-002: Task IDs (N.M format) MUST be unique across document"""
    # NOTE: extraction_pattern needs to be customized for your specific use case
    # This default extracts IDs in format "ID: XXX" or "id: XXX"
    return check_unique(
        path, text,
        rule_id="PIN-TSK-002",
        extraction_pattern=r"[Ii][Dd]:\s*(\S+)",
        item_name="ID"
    )
