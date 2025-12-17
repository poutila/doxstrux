"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-SEV-001
Check type: policy (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`

NOTE: This is a policy/declarative rule, not a document constraint.
It describes system behavior and always passes when applied to documents.
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_policy


def enforce_pin_sev_001(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-SEV-001: ERROR severity blocks conversion (exit 1); WARNING does not block but may cause poor output

    Note: Policy rules describe system behavior, not document constraints.
    This rule always passes on document validation.
    """
    return check_policy(
        path, text,
        rule_id="PIN-SEV-001",
        policy_description="ERROR severity blocks conversion (exit 1); WARNING does not block but may cause poor output"
    )
