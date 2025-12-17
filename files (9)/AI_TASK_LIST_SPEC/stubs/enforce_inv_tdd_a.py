"""
AUTO-GENERATED ENFORCEMENT STUB — DO NOT EDIT BY HAND
Generated from: AI_TASK_LIST_SPEC (v2.0.0)
Domain: ai_task_list
Invariant: INV-TDD-A

Implement the enforcement logic below.
"""

from pathlib import Path
from typing import List

from speksi.core.config import find_project_root, load_config
from speksi.core.interfaces.models import LintError


def enforce_inv_tdd_a(path: Path, text: str) -> List[LintError]:
    """
    Enforce INV-TDD-A: Non-Phase-0 tasks MUST follow RED-GREEN-REFACTOR structure

    Args:
        path: Path to the file being linted
        text: Content of the file

    Returns:
        List of LintError objects for any violations found
    """
    errors: List[LintError] = []

    # Load project config
    project_root = find_project_root(path)
    config = load_config(project_root) if project_root else None

    # TODO: Implement enforcement logic for INV-TDD-A
    # Available: project_root, config.spec_folder_name, config.package_name, etc.
    # Example:
    # if config and not (config.project_root / "pyproject.toml").exists():
    #     errors.append(LintError(
    #         line=1,
    #         code="INV-TDD-A",
    #         message="pyproject.toml not found"
    #     ))

    return errors
