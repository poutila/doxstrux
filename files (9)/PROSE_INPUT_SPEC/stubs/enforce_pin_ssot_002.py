"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-SSOT-002
Check type: policy (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`

NOTE: This is a policy/declarative rule, not a document constraint.
It describes system behavior and always passes when applied to documents.
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_policy


def enforce_pin_ssot_002(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-SSOT-002: If spec and linter diverge, linter MUST be updated to match spec

    Note: Policy rules describe system behavior, not document constraints.
    This rule always passes on document validation.
    """
    return check_policy(
        path, text,
        rule_id="PIN-SSOT-002",
        policy_description="If spec and linter diverge, linter MUST be updated to match spec"
    )
