"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-002
Check type: policy (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`

NOTE: This is a policy/declarative rule, not a document constraint.
It describes system behavior and always passes when applied to documents.
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_policy


def enforce_r_atl_002(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-002: Mode semantics: template allows placeholders; plan requires real commands; instantiated forbids all placeholders

    Note: Policy rules describe system behavior, not document constraints.
    This rule always passes on document validation.
    """
    return check_policy(
        path, text,
        rule_id="R-ATL-002",
        policy_description="Mode semantics: template allows placeholders; plan requires real commands; instantiated forbids all placeholders"
    )
