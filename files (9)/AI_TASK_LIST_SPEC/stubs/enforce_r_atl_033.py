# Auto-generated enforcement function for R-ATL-033
# Check type: section_include
# Spec: AI_TASK_LIST_SPEC v2.0.0

"""Section content check for R-ATL-033: Document MUST include naming rule linking Task ID N.M to array exactly once"""

from __future__ import annotations

import re
from pathlib import Path

from speksi.core.interfaces.models import LintError


def enforce_r_atl_033(path: Path, text: str) -> list[LintError]:
    """Check that document includes required content.

    Rule: Document MUST include naming rule linking Task ID N.M to array exactly once
    Required content: naming rule linking Task ID N
    """
    errors: list[LintError] = []

    required = "naming rule linking Task ID N"

    # Check if required content pattern exists
    if not re.search(re.escape(required), text, re.IGNORECASE):
        errors.append(
            LintError(
                line=1,
                code="R-ATL-033",
                message=f"Document must include: {required}",
            )
        )

    return errors
