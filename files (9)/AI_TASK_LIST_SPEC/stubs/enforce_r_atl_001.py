"""
AUTO-GENERATED ENFORCEMENT — AI_TASK_LIST_SPEC v2.0.0
Rule: R-ATL-001
Check type: yaml_front_matter (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_yaml_field, check_block_exists


def enforce_r_atl_001(path: Path, text: str) -> List[LintError]:
    """Enforce R-ATL-001: Task list MUST start with YAML front matter containing ai_task_list block with schema_version, mode, runner, runner_prefix, search_tool"""
    errors: List[LintError] = []

    # Check 1: Document starts with YAML front matter (---)
    if not text.lstrip().startswith("---"):
        errors.append(LintError(
            line=1,
            code="R-ATL-001",
            message="Document must start with YAML front matter (---)"
        ))
        return errors  # Can't check further without YAML front matter

    # Check 2: YAML contains the required block
    block_name = "ai_task_list"
    if block_name:
        block_errors = check_block_exists(
            path, text,
            rule_id="R-ATL-001",
            block_name=block_name + ":",
            block_marker=None
        )
        errors.extend(block_errors)

    # Check 3: Block contains required fields
    required_fields = ["schema_version", "mode", "runner", "runner_prefix", "search_tool"]
    if required_fields:
        field_errors = check_yaml_field(
            path, text,
            rule_id="R-ATL-001",
            required_fields=required_fields,
            block_marker="---"
        )
        errors.extend(field_errors)

    return errors
