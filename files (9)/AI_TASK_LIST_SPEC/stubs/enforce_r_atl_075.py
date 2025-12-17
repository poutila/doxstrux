"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-075
Check type: prefix (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError


def enforce_r_atl_075(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-075: In plan/instantiated mode, command lines in gated sections MUST start with `$`"""
    errors: List[LintError] = []

    # Check that document starts with required prefix
    prefix = "$"
    if not text.lstrip().startswith(prefix):
        errors.append(LintError(
            line=1,
            code="R-ATL-075",
            message=f"Document must start with: {prefix}"
        ))

    return errors
