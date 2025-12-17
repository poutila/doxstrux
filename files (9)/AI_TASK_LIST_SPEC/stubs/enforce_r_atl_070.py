"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-070
Check type: yaml_type (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_yaml_type


def enforce_r_atl_070(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-070: runner and runner_prefix MUST be non-empty strings (or runner_prefix explicitly empty)"""
    return check_yaml_type(
        path, text,
        rule_id="R-ATL-070",
        field_name="",
        expected_type="non-empty",
        block_marker="---"
    )
