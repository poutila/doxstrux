"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-YML-004
Check type: yaml_type (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_yaml_type


def enforce_pin_yml_004(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-YML-004: All required YAML fields MUST be strings"""
    return check_yaml_type(
        path, text,
        rule_id="PIN-YML-004",
        field_name="",
        expected_type="strings",
        block_marker="---"
    )
