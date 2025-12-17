"""
AUTO-GENERATED DRIFT DETECTOR RUNNER — DO NOT EDIT BY HAND
Domain: ai_task_list
"""

from pathlib import Path
from typing import List

from .spec_vs_mapping import check_spec_vs_mapping
from .mapping_vs_enforcement import check_mapping_vs_enforcement
from .mapping_vs_tests import check_mapping_vs_tests


def run_all_drift_checks(base_dir: Path) -> List[str]:
    """
    Run all drift checks for the domain.

    Args:
        base_dir: Base directory containing mapping/, stubs/, tests/

    Returns:
        List of all drift messages. Empty list means no drift.
    """
    all_drift = []

    spec_path = base_dir.parent / "specs" / "AI_TASK_LIST_SPEC.md"
    mapping_path = base_dir / "mapping" / "mapping.yaml"
    stubs_dir = base_dir / "stubs"
    tests_dir = base_dir / "tests"

    # Check spec vs mapping
    if spec_path.exists() and mapping_path.exists():
        drift = check_spec_vs_mapping(spec_path, mapping_path)
        all_drift.extend(drift)
    else:
        if not spec_path.exists():
            all_drift.append(f"MISSING: Spec file {spec_path}")
        if not mapping_path.exists():
            all_drift.append(f"MISSING: Mapping file {mapping_path}")

    # Check mapping vs stubs
    if mapping_path.exists() and stubs_dir.exists():
        drift = check_mapping_vs_enforcement(mapping_path, stubs_dir)
        all_drift.extend(drift)

    # Check mapping vs tests
    if mapping_path.exists() and tests_dir.exists():
        drift = check_mapping_vs_tests(mapping_path, tests_dir)
        all_drift.extend(drift)

    return all_drift


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) != 2:
        print("Usage: run_all.py <base_dir>")
        sys.exit(2)

    base_dir = Path(sys.argv[1])
    drift = run_all_drift_checks(base_dir)

    if drift:
        print(f"DRIFT DETECTED ({len(drift)} total issues):")
        for msg in drift:
            print(f"  - {msg}")
        sys.exit(1)
    else:
        print("No drift detected. All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
