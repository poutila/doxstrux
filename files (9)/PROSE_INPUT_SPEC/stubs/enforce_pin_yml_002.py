"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-YML-002
Check type: block (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError
from speksi.core.enforcement.check_functions import check_block_exists


def enforce_pin_yml_002(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-YML-002: YAML front matter MUST contain `prose_input:` block"""
    return check_block_exists(
        path, text,
        rule_id="PIN-YML-002",
        block_name="prose_input:",
        block_marker=None
    )
