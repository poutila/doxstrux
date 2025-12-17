"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-LNT-003
Check type: policy (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`

NOTE: This is a policy/declarative rule, not a document constraint.
It describes system behavior and always passes when applied to documents.
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_policy


def enforce_r_lnt_003(path: Path, text: str) -> List[LintError]:
    """Enforce R-LNT-003: With --json flag, emit JSON object with passed, error_count, errors, mode, runner, schema_version

    Note: Policy rules describe system behavior, not document constraints.
    This rule always passes on document validation.
    """
    return check_policy(
        path, text,
        rule_id="R-LNT-003",
        policy_description="With --json flag, emit JSON object with passed, error_count, errors, mode, runner, schema_version"
    )
