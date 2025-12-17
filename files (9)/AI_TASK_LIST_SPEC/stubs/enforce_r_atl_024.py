"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-024
Check type: evidence (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_evidence_block


def enforce_r_atl_024(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-024: With `--require-captured-evidence`, evidence blocks MUST include cmd and exit headers"""
    return check_evidence_block(
        path, text,
        rule_id="R-ATL-024",
        required_fields=None,
        evidence_marker="## Evidence"
    )
