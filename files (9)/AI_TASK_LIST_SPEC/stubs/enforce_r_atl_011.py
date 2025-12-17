# Auto-generated enforcement function for R-ATL-011
# Check type: mode_conditional
# Spec: AI_TASK_LIST_SPEC v2.0.0

"""Mode-conditional check for R-ATL-011: If mode is plan or instantiated, MUST include `## Prose Coverage Mapping` section with table"""

from __future__ import annotations

import re
from pathlib import Path

from speksi.core.interfaces.models import LintError


def enforce_r_atl_011(path: Path, text: str) -> list[LintError]:
    """Check condition when mode matches.

    Rule: If mode is plan or instantiated, MUST include `## Prose Coverage Mapping` section with table
    Modes: ['plan', 'instantiated']
    Condition: MUST include `## Prose Coverage Mapping` section with table
    """
    errors: list[LintError] = []

    # Extract mode from YAML front matter
    yaml_match = re.search(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not yaml_match:
        return errors

    yaml_content = yaml_match.group(1)
    mode_match = re.search(r'mode:\s*["\']?(\w+)["\']?', yaml_content)
    if not mode_match:
        return errors

    mode = mode_match.group(1).lower()

    # Check if mode matches any of the target modes
    target_modes = ["plan", "instantiated"]
    if mode not in [m.lower() for m in target_modes]:
        return errors  # Mode doesn't match, rule doesn't apply

    # TODO: Implement mode-specific condition check
    # Condition: MUST include `## Prose Coverage Mapping` section with table

    return errors
