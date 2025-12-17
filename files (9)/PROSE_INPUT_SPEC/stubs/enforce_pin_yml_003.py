"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-YML-003
Check type: yaml_field (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_yaml_field


def enforce_pin_yml_003(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-YML-003: prose_input block MUST contain: schema_version, project_name, runner, runner_prefix, search_tool"""
    return check_yaml_field(
        path, text,
        rule_id="PIN-YML-003",
        required_fields=["schema_version", "project_name", "runner", "runner_prefix", "search_tool"],
        block_marker="---"
    )
