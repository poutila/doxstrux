# Auto-generated enforcement function for R-ATL-051
# Check type: section_include
# Spec: AI_TASK_LIST_SPEC v2.0.0

"""Section content check for R-ATL-051: `## STOP — Phase Gate` MUST include checklist referencing unlock artifacts"""

from __future__ import annotations

import re
from pathlib import Path

from speksi.core.interfaces.models import LintError


def enforce_r_atl_051(path: Path, text: str) -> list[LintError]:
    """Check that document includes required content.

    Rule: `## STOP — Phase Gate` MUST include checklist referencing unlock artifacts
    Required content: checklist referencing unlock artifacts
    """
    errors: list[LintError] = []

    required = "checklist referencing unlock artifacts"

    # Check if required content pattern exists
    if not re.search(re.escape(required), text, re.IGNORECASE):
        errors.append(
            LintError(
                line=1,
                code="R-ATL-051",
                message=f"Document must include: {required}",
            )
        )

    return errors
