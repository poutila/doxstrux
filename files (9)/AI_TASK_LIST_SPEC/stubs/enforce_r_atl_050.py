"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-050
Check type: task_structure (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_task_structure


def enforce_r_atl_050(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-050: Task list MUST include `## Phase Unlock Artifact` section with .phase-N.complete.json generation"""
    return check_task_structure(
        path, text,
        rule_id="R-ATL-050",
        required_fields=None,
        task_pattern=None
    )
