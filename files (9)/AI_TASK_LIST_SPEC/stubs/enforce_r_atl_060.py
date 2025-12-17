# Auto-generated enforcement function for R-ATL-060
# Check type: section_include
# Spec: AI_TASK_LIST_SPEC v2.0.0

"""Section content check for R-ATL-060: `## Global Clean Table Scan` MUST include command and evidence paste slot"""

from __future__ import annotations

import re
from pathlib import Path

from speksi.core.interfaces.models import LintError


def enforce_r_atl_060(path: Path, text: str) -> list[LintError]:
    """Check that document includes required content.

    Rule: `## Global Clean Table Scan` MUST include command and evidence paste slot
    Required content: command and evidence paste slot
    """
    errors: list[LintError] = []

    required = "command and evidence paste slot"

    # Check if required content pattern exists
    if not re.search(re.escape(required), text, re.IGNORECASE):
        errors.append(
            LintError(
                line=1,
                code="R-ATL-060",
                message=f"Document must include: {required}",
            )
        )

    return errors
