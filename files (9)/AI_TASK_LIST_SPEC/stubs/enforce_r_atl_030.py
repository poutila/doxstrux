"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-030
Check type: regex (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_regex_match


def enforce_r_atl_030(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-030: Phase headings MUST match `^## Phase (\d+) — (.+)$`; Phase 0 MUST exist"""
    # NOTE: field_pattern needs to be customized for your specific use case
    # This default extracts the whole line content
    return check_regex_match(
        path, text,
        rule_id="R-ATL-030",
        field_pattern=r"^(.+)$",
        required_pattern=r"^## Phase (\d+) — (.+)$",
        field_name="value"
    )
