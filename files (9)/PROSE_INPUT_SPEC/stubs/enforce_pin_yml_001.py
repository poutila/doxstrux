"""
AUTO-GENERATED ENFORCEMENT — PROSE_INPUT_SPEC v2.0.0
Rule: PIN-YML-001
Check type: prefix (auto-classified, confidence=1.0)

DO NOT EDIT — regenerate via `speksi generate`
"""

from pathlib import Path
from typing import List

from speksi.core.interfaces.models import LintError


def enforce_pin_yml_001(path: Path, text: str) -> List[LintError]:
    """Enforce PIN-YML-001: Document MUST start with YAML front matter delimited by `---`"""
    errors: List[LintError] = []

    # Check that document starts with required prefix
    prefix = "YAML front matter delimited by `---"
    if not text.lstrip().startswith(prefix):
        errors.append(LintError(
            line=1,
            code="PIN-YML-001",
            message=f"Document must start with: {prefix}"
        ))

    return errors
