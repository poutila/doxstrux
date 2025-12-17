"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-YML-007
Check type: enum (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_enum_value


def enforce_pin_yml_007(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-YML-007: search_tool MUST be one of: rg, grep"""
    # NOTE: field_pattern needs to be customized for your specific use case
    # This default extracts values after a colon on each line
    return check_enum_value(
        path, text,
        rule_id="PIN-YML-007",
        field_pattern=r":\s*(\w+)",
        allowed_values=["rg", "grep"],
        case_sensitive=False
    )
