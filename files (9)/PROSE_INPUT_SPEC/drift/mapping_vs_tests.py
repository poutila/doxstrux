"""
AUTO-GENERATED DRIFT DETECTOR — DO NOT EDIT BY HAND
Mapping vs Tests Drift Detection

Domain: prose_input
Spec: PROSE_INPUT_SPEC (v2.0.0)
"""

import re
from pathlib import Path
from typing import List, Set

import yaml


def load_mapping_ids(mapping_path: Path) -> Set[str]:
    """Extract rule/invariant IDs from mapping."""
    mapping = yaml.safe_load(mapping_path.read_text())
    ids = set()

    for rule in mapping.get("rules", []):
        ids.add(rule["id"])

    for inv in mapping.get("invariants", []):
        ids.add(inv["id"])

    return ids


def extract_test_coverage(tests_dir: Path) -> Set[str]:
    """Extract rule/invariant IDs covered by test files."""
    covered = set()

    # Pattern to match test file names like test_r_doc_hdr_1.py
    file_pattern = re.compile(r"test_([a-z_0-9]+)\.py")

    for py_file in tests_dir.glob("test_*.py"):
        if py_file.name in ("test_integration.py", "test_conftest.py"):
            continue

        match = file_pattern.match(py_file.name)
        if match:
            # Convert normalized name back to ID
            normalized = match.group(1)
            # This is approximate - actual ID recovery may need adjustment
            rule_id = normalized.upper().replace("_", "-")
            covered.add(rule_id)

    return covered


def check_mapping_vs_tests(mapping_path: Path, tests_dir: Path) -> List[str]:
    """
    Check for drift between mapping and test coverage.

    Returns list of drift messages. Empty list means no drift.
    """
    drift_messages = []

    # Load mapping IDs
    try:
        expected = load_mapping_ids(mapping_path)
    except Exception as e:
        return [f"Failed to load mapping: {e}"]

    # Get test coverage
    covered = extract_test_coverage(tests_dir)

    # Check for missing tests (normalize IDs for comparison)
    def normalize(s):
        return s.lower().replace("-", "_")

    expected_normalized = {normalize(i): i for i in expected}
    covered_normalized = {normalize(i): i for i in covered}

    missing = set(expected_normalized.keys()) - set(covered_normalized.keys())
    for norm_id in sorted(missing):
        original_id = expected_normalized[norm_id]
        drift_messages.append(f"MISSING TEST: No test for '{original_id}'")

    # Check for orphaned tests
    orphaned = set(covered_normalized.keys()) - set(expected_normalized.keys())
    for norm_id in sorted(orphaned):
        original_id = covered_normalized[norm_id]
        drift_messages.append(f"ORPHANED TEST: Test for '{original_id}' but rule not in mapping")

    return drift_messages


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) != 3:
        print("Usage: mapping_vs_tests.py <mapping.yaml> <tests_dir>")
        sys.exit(2)

    mapping_path = Path(sys.argv[1])
    tests_dir = Path(sys.argv[2])

    drift = check_mapping_vs_tests(mapping_path, tests_dir)

    if drift:
        print(f"DRIFT DETECTED ({len(drift)} issues):")
        for msg in drift:
            print(f"  - {msg}")
        sys.exit(1)
    else:
        print("No drift detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
