"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-CTX-001
Check type: forbidden (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_forbidden_patterns


def enforce_pin_ctx_001(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-CTX-001: Success Criteria MUST NOT contain subjective terms: good, nice, clean, proper, appropriate, reasonable, adequate"""
    return check_forbidden_patterns(
        path, text,
        rule_id="PIN-CTX-001",
        patterns=["subjective terms: good", "nice", "clean", "proper", "appropriate", "reasonable", "adequate"],
        case_insensitive=True
    )
