import pytest

from tasklist.sanitize_paths import (
    sanitize_artifact_path,
    validate_task_file_paths,
    validate_task_inputs,
)


def test_sanitize_artifact_path_allows_evidence_only():
    assert sanitize_artifact_path("evidence/logs/output.txt").as_posix() == "evidence/logs/output.txt"

    with pytest.raises(ValueError):
        sanitize_artifact_path("logs/output.txt")

    with pytest.raises(ValueError):
        sanitize_artifact_path("evidence\\bad.txt")


def test_validate_task_file_paths_detects_violations():
    data = {
        "phases": {
            "phase_0": {
                "tasks": [
                    {
                        "id": "1",
                        "files": ["/abs/path", "src\\main.py", "../escape"],
                    }
                ]
            }
        }
    }

    errors = validate_task_file_paths(data)
    assert any("absolute" in err.lower() for err in errors)
    assert any("backslash" in err.lower() for err in errors)
    assert any("traverses upward" in err.lower() for err in errors)


def test_validate_task_file_paths_allows_normalized_list():
    data = {
        "phases": {
            "phase_0": {
                "tasks": [
                    {
                        "id": "2",
                        "files": "src/app.py, src/utils/helpers.py\nREADME.md",
                    }
                ]
            }
        }
    }

    errors = validate_task_file_paths(data)
    assert not errors


def test_validate_task_inputs_detects_invalid_paths():
    data = {
        "phases": {
            "phase_0": {
                "tasks": [
                    {"id": "3", "inputs": ["../secrets.txt", "src\\bad.py"]}
                ]
            }
        }
    }

    errors = validate_task_inputs(data)
    assert len(errors) == 2
