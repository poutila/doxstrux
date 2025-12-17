# Auto-generated enforcement function for PIN-TSK-004
# Check type: search_tool_conditional
# Spec: PROSE_INPUT_SPEC v2.0.0

"""Search tool conditional check for PIN-TSK-004: Precondition commands MUST use search_tool declared in YAML; if rg, grep forbidden"""

from __future__ import annotations

import re
from pathlib import Path

from speksi.core.interfaces.models import LintError


def enforce_pin_tsk_004(path: Path, text: str) -> list[LintError]:
    """Check search tool consistency.

    Rule: Precondition commands MUST use search_tool declared in YAML; if rg, grep forbidden
    Field: search_tool
    Conditional: if rg, grep forbidden
    """
    errors: list[LintError] = []

    # Extract search_tool from YAML front matter
    yaml_match = re.search(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not yaml_match:
        return errors

    yaml_content = yaml_match.group(1)
    search_tool_match = re.search(r'search_tool:\s*["\']?(\w+)["\']?', yaml_content)
    if not search_tool_match:
        return errors

    search_tool = search_tool_match.group(1).lower()

    # If search_tool is rg, grep is forbidden in code blocks
    if search_tool == 'rg':
        # Find code blocks
        code_blocks = re.findall(r'```[^\n]*\n(.*?)```', text, re.DOTALL)
        for i, block in enumerate(code_blocks):
            for j, line in enumerate(block.splitlines()):
                if re.search(r'\bgrep\b', line):
                    errors.append(
                        LintError(
                            line=0,  # Line number would need more context
                            code="PIN-TSK-004",
                            message=f"grep command found but search_tool is rg",
                        )
                    )

    return errors
