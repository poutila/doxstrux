"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-TSK-003
Check type: task_structure (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_task_structure


def enforce_pin_tsk_003(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-TSK-003: Phase 0 tasks MUST contain Objective, Paths; non-Phase-0 tasks MUST also contain Precondition, TDD Specification, Success Criteria"""
    return check_task_structure(
        path, text,
        rule_id="PIN-TSK-003",
        required_fields=None,
        task_pattern=None
    )
