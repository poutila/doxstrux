"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-YML-008
Check type: forbidden (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_forbidden_patterns


def enforce_pin_yml_008(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-YML-008: YAML field values MUST NOT contain `[[` or `]]` placeholder tokens"""
    return check_forbidden_patterns(
        path, text,
        rule_id="PIN-YML-008",
        patterns=["[[` or `]]` placeholder tokens"],
        case_insensitive=True
    )
