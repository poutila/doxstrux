"""Schema version validator for phase unlock artifacts.

Validates phase unlock artifacts before allowing Phase N+1 to start.
"""
import json
import sys
from pathlib import Path


class SecurityError(RuntimeError):
    pass


REQUIRED_SCHEMA = {
    "schema_version": "1.0",
    "min_schema_version": "1.0"
}


def validate_artifact(artifact_path: Path) -> dict:
    """Validate phase unlock artifact schema.

    Args:
        artifact_path: Path to .phase-N.complete.json

    Returns:
        Validated artifact dict

    Raises:
        SecurityError: On validation failure
    """
    if not artifact_path.exists():
        raise SecurityError(f"Artifact not found: {artifact_path}")

    data = json.loads(artifact_path.read_text(encoding="utf-8"))

    # Schema version check
    for key, expected_value in REQUIRED_SCHEMA.items():
        actual_value = data.get(key)
        if actual_value != expected_value:
            raise SecurityError(
                f"{key} mismatch: {actual_value} != {expected_value}"
            )

    # Required keys
    required_keys = [
        "phase", "baseline_pass_count", "ci_gates_passed",
        "git_commit", "schema_version", "min_schema_version"
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise SecurityError(f"Missing required keys: {missing}")

    return data


if __name__ == "__main__":
    try:
        artifact = validate_artifact(Path(sys.argv[1]))
        print(json.dumps({"status": "OK", "phase": artifact["phase"]}))
        sys.exit(0)
    except SecurityError as e:
        print(json.dumps({"status": "FAIL", "reason": str(e)}))
        sys.exit(1)
