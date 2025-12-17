"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-YML-006
Check type: enum (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_enum_value


def enforce_pin_yml_006(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-YML-006: runner MUST be one of: uv, npm, cargo, go, poetry, pipenv"""
    # NOTE: field_pattern needs to be customized for your specific use case
    # This default extracts values after a colon on each line
    return check_enum_value(
        path, text,
        rule_id="PIN-YML-006",
        field_pattern=r":\s*(\w+)",
        allowed_values=["uv", "npm", "cargo", "go", "poetry", "pipenv"],
        case_sensitive=False
    )
