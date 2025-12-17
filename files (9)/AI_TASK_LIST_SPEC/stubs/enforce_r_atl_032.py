"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-032
Check type: block (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_block_exists


def enforce_r_atl_032(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-032: Every task MUST contain `**Paths**:` block with `TASK_<N>_<M>_PATHS=(<quoted paths>)`"""
    return check_block_exists(
        path, text,
        rule_id="R-ATL-032",
        block_name="**Paths**:",
        block_marker=None
    )
