"""
AUTO-GENERATED DRIFT DETECTOR — DO NOT EDIT BY HAND
Spec vs Mapping Drift Detection

Domain: ai_task_list
Spec: AI_TASK_LIST_SPEC (v2.0.0)
"""

import re
from pathlib import Path
from typing import List, Tuple, Set

import yaml


def extract_spec_rules(spec_path: Path) -> Tuple[Set[str], str]:
    """
    Extract rule/invariant IDs and version from specification.
    Returns (set of IDs, spec_version).
    """
    text = spec_path.read_text()
    ids = set()
    version = "0.0.0"

    # Extract version from header
    version_match = re.search(r"SPEC_VERSION:\s*(\S+)", text)
    if version_match:
        version = version_match.group(1)

    # Extract rule IDs (pattern: R-XXX-NNN or INV-XXX)
    rule_pattern = re.compile(r"\b(R-[A-Z]+-\d+|INV-[A-Z]+-[A-Z0-9]+)\b")
    for match in rule_pattern.finditer(text):
        ids.add(match.group(1))

    return ids, version


def load_mapping(mapping_path: Path) -> Tuple[Set[str], str]:
    """
    Extract rule/invariant IDs and version from mapping.
    Returns (set of IDs, spec_version).
    """
    mapping = yaml.safe_load(mapping_path.read_text())
    ids = set()

    for rule in mapping.get("rules", []):
        ids.add(rule["id"])

    for inv in mapping.get("invariants", []):
        ids.add(inv["id"])

    version = mapping.get("spec_version", "0.0.0")

    return ids, version


def check_spec_vs_mapping(spec_path: Path, mapping_path: Path) -> List[str]:
    """
    Check for drift between specification and mapping.

    Returns list of drift messages. Empty list means no drift.
    """
    drift_messages = []

    # Extract from spec
    try:
        spec_ids, spec_version = extract_spec_rules(spec_path)
    except Exception as e:
        return [f"Failed to parse spec: {e}"]

    # Extract from mapping
    try:
        mapping_ids, mapping_version = load_mapping(mapping_path)
    except Exception as e:
        return [f"Failed to load mapping: {e}"]

    # Check version match
    if spec_version != mapping_version:
        drift_messages.append(
            f"VERSION MISMATCH: Spec is v{spec_version}, mapping is v{mapping_version}"
        )

    # Check for rules in spec but not in mapping
    missing_in_mapping = spec_ids - mapping_ids
    for rule_id in sorted(missing_in_mapping):
        drift_messages.append(f"MISSING IN MAPPING: '{rule_id}' in spec but not in mapping")

    # Check for rules in mapping but not in spec
    extra_in_mapping = mapping_ids - spec_ids
    for rule_id in sorted(extra_in_mapping):
        drift_messages.append(f"EXTRA IN MAPPING: '{rule_id}' in mapping but not in spec")

    return drift_messages


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) != 3:
        print("Usage: spec_vs_mapping.py <spec.md> <mapping.yaml>")
        sys.exit(2)

    spec_path = Path(sys.argv[1])
    mapping_path = Path(sys.argv[2])

    drift = check_spec_vs_mapping(spec_path, mapping_path)

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
