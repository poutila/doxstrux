"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-072
Check type: runner_conditional (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_runner_conditional


def enforce_r_atl_072(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-072: When runner=uv and instantiated, forbidden: .venv/bin/python, python -m, pip install"""
    return check_runner_conditional(
        path, text,
        rule_id="R-ATL-072",
        runner="uv",
        required_field="",
        required_value=None
    )
