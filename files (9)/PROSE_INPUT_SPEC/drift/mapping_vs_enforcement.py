"""
AUTO-GENERATED DRIFT DETECTOR — DO NOT EDIT BY HAND
Mapping vs Enforcement Drift Detection

Domain: prose_input
Spec: PROSE_INPUT_SPEC (v2.0.0)
"""

import ast
from pathlib import Path
from typing import List, Set

import yaml


def load_mapping(mapping_path: Path) -> Set[str]:
    """Extract expected enforcement function names from mapping."""
    mapping = yaml.safe_load(mapping_path.read_text())
    functions = set()

    for rule in mapping.get("rules", []):
        functions.add(rule["enforcement"])

    for inv in mapping.get("invariants", []):
        functions.add(inv["enforcement"])

    return functions


def extract_enforcement_functions(enforcement_dir: Path) -> Set[str]:
    """Extract all enforcement function names from the enforcement directory."""
    functions = set()

    for py_file in enforcement_dir.glob("enforce_*.py"):
        try:
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith("enforce_"):
                        functions.add(node.name)
        except SyntaxError:
            continue

    return functions


def check_mapping_vs_enforcement(mapping_path: Path, enforcement_dir: Path) -> List[str]:
    """
    Check for drift between mapping and enforcement functions.

    Returns list of drift messages. Empty list means no drift.
    """
    drift_messages = []

    # Load expected from mapping
    try:
        expected = load_mapping(mapping_path)
    except Exception as e:
        return [f"Failed to load mapping: {e}"]

    # Get actual functions
    actual = extract_enforcement_functions(enforcement_dir)

    # Check for missing functions
    missing = expected - actual
    for fn in sorted(missing):
        drift_messages.append(f"MISSING: '{fn}' in mapping but not implemented")

    # Check for orphaned functions
    orphaned = actual - expected
    for fn in sorted(orphaned):
        drift_messages.append(f"ORPHANED: '{fn}' implemented but not in mapping")

    return drift_messages


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) != 3:
        print("Usage: mapping_vs_enforcement.py <mapping.yaml> <enforcement_dir>")
        sys.exit(2)

    mapping_path = Path(sys.argv[1])
    enforcement_dir = Path(sys.argv[2])

    drift = check_mapping_vs_enforcement(mapping_path, enforcement_dir)

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
