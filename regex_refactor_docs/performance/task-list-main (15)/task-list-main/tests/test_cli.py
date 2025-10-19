import json
from pathlib import Path

import pytest
import yaml

from tasklist import (
    render_task_templates,
    sanitize_paths,
    validate_commands,
    validate_task_ids,
)


def test_render_and_validate(tmp_path):
    repo_yaml = Path("DETAILED_TASK_LIST_template.yaml")
    target_yaml = tmp_path / repo_yaml.name
    target_yaml.write_text(repo_yaml.read_text(encoding="utf-8"), encoding="utf-8")

    # Render into the temporary directory
    exit_code = render_task_templates.main(["--strict", "--allow-tbd", "--root", str(tmp_path)])
    assert exit_code == 0

    rendered_json = tmp_path / "DETAILED_TASK_LIST_template.json"
    assert rendered_json.exists()

    # Validate IDs using the generated JSON
    exit_code = validate_task_ids.main(["--root", str(tmp_path)])
    assert exit_code == 0

    exit_code = validate_commands.main(["--root", str(tmp_path)])
    assert exit_code == 0

    exit_code = sanitize_paths.main(["--root", str(tmp_path)])
    assert exit_code == 0


def test_render_fails_when_placeholders_remain(tmp_path):
    yaml_path = tmp_path / "plan.yaml"
    yaml_payload = {
        "schema_version": "2.0.0",
        "document": {
            "id": "demo-plan",
            "title": "Demo",
            "version": "1.0",
            "created": "2024-01-01",
            "owner": "QA",
            "audience": ["engineering"],
        },
        "metadata": {
            "project_full_name": "Demo",
            "project_goal": "Ship demo",
            "status": "Draft",
            "total_estimated_time_hours": 1,
            "total_phases": 1,
            "schema_version": "2.0.0",
        },
        "ci_gates": [
            {"id": "G1", "name": "schema", "command": "echo ok"},
        ],
        "phases": {
            "phase_template": {
                "phase_number": 0,
                "name": "Template",
                "goal": "Fill me in",
                "time_estimate_hours": 0,
                "status": "⏳ Not started",
                "prerequisites": "None",
                "tasks": [
                    {
                        "id": "T.T",
                        "name": "Template task",
                        "time_estimate_hours": 0,
                        "steps": ["Template"],
                        "acceptance_criteria": ["Template"],
                        "status": "⏳ Not started",
                    }
                ],
            },
            "phase_0": {
                "name": "Init",
                "goal": "Start",
                "time_estimate_hours": 1,
                "status": "⏳ Not started",
                "tasks": [
                    {
                        "id": "0.1",
                        "name": "Compile",
                        "time_estimate_hours": 0.5,
                        "steps": ["run build"],
                        "acceptance_criteria": ["build succeeds"],
                        "status": "⏳ Not started",
                        "files": "src/main.py",
                        "notes": "{{UNRESOLVED}}",
                    }
                ],
            }
        },
        "render_meta": {},
    }
    yaml_path.write_text(yaml.safe_dump(yaml_payload, sort_keys=False), encoding="utf-8")

    exit_code = render_task_templates.main(
        ["--root", str(tmp_path), "--source", str(yaml_path)]
    )

    assert exit_code == 1
    assert not (tmp_path / "DETAILED_TASK_LIST_template.json").exists()


def test_render_flags_tbd_without_allow(tmp_path):
    yaml_path = tmp_path / "plan.yaml"
    yaml_payload = {
        "schema_version": "2.0.0",
        "document": {
            "id": "demo-plan",
            "title": "Demo",
            "version": "1.0",
            "created": "2024-01-01",
            "owner": "QA",
            "audience": ["engineering"],
        },
        "metadata": {
            "project_full_name": "Demo",
            "project_goal": "Ship demo",
            "status": "Draft",
            "total_estimated_time_hours": 1,
            "total_phases": 1,
            "schema_version": "2.0.0",
        },
        "ci_gates": [
            {"id": "G1", "name": "schema", "command": "echo ok"},
        ],
        "phases": {
            "phase_template": {
                "phase_number": 0,
                "name": "Template",
                "goal": "Fill me in",
                "time_estimate_hours": 0,
                "status": "⏳ Not started",
                "prerequisites": "None",
                "tasks": [
                    {
                        "id": "T.T",
                        "name": "Template task",
                        "time_estimate_hours": 0,
                        "steps": ["Template"],
                        "acceptance_criteria": ["Template"],
                        "status": "⏳ Not started",
                    }
                ],
            },
            "phase_0": {
                "name": "Init",
                "goal": "Start",
                "time_estimate_hours": 1,
                "status": "⏳ Not started",
                "tasks": [
                    {
                        "id": "0.1",
                        "name": "Compile",
                        "time_estimate_hours": 0.5,
                        "steps": ["run build"],
                        "acceptance_criteria": ["build succeeds"],
                        "status": "⏳ Not started",
                        "files": "src/main.py",
                        "notes": "TBD_REPLACE_ME",
                    }
                ],
            }
        },
        "render_meta": {},
    }
    yaml_path.write_text(yaml.safe_dump(yaml_payload, sort_keys=False), encoding="utf-8")

    exit_code = render_task_templates.main(
        ["--strict", "--root", str(tmp_path), "--source", str(yaml_path)]
    )

    assert exit_code == 1


def test_render_fails_on_invalid_phase_completion_artifact(tmp_path):
    repo_yaml = Path("DETAILED_TASK_LIST_template.yaml")
    target_yaml = tmp_path / repo_yaml.name
    target_yaml.write_text(repo_yaml.read_text(encoding="utf-8"), encoding="utf-8")

    bad_completion = tmp_path / ".phase-0.complete.json"
    bad_completion.write_text(json.dumps({"not": "valid"}), encoding="utf-8")

    exit_code = render_task_templates.main(["--strict", "--allow-tbd", "--root", str(tmp_path)])
    assert exit_code == 1


def test_render_fails_for_schema_version_mismatch(tmp_path, capsys):
    repo_yaml = Path("DETAILED_TASK_LIST_template.yaml")
    payload = yaml.safe_load(repo_yaml.read_text(encoding="utf-8"))
    payload["schema_version"] = "9.9.9"
    if isinstance(payload.get("metadata"), dict):
        payload["metadata"]["schema_version"] = "9.9.9"

    yaml_path = tmp_path / "plan.yaml"
    yaml_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        render_task_templates.main(
            [
                "--strict",
                "--allow-tbd",
                "--root",
                str(tmp_path),
                "--source",
                str(yaml_path),
            ]
        )

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "schema_version" in captured.err


def test_schema_packaged_accessible():
    from importlib import resources

    schema_resource = resources.files("tasklist.schemas").joinpath("detailed_task_list.schema.json")
    with resources.as_file(schema_resource) as path:
        assert path.exists()


def test_render_preserves_timestamps_when_yaml_unchanged(tmp_path, monkeypatch):
    repo_yaml = Path("DETAILED_TASK_LIST_template.yaml")
    target_yaml = tmp_path / repo_yaml.name
    target_yaml.write_text(repo_yaml.read_text(encoding="utf-8"), encoding="utf-8")

    first_timestamp = "2000-01-01T00:00:00Z"
    second_timestamp = "2001-02-03T04:05:06Z"

    monkeypatch.setattr(render_task_templates, "_utc_now", lambda: first_timestamp)
    exit_code = render_task_templates.main(["--strict", "--allow-tbd", "--root", str(tmp_path)])
    assert exit_code == 0

    json_path = tmp_path / "DETAILED_TASK_LIST_template.json"
    md_path = tmp_path / "DETAILED_TASK_LIST_template.md"

    initial_json = json.loads(json_path.read_text(encoding="utf-8"))
    assert initial_json["render_meta"]["rendered_utc"] == first_timestamp
    assert initial_json["metadata"]["template_metadata"]["last_rendered_utc"] == first_timestamp

    monkeypatch.setattr(render_task_templates, "_utc_now", lambda: second_timestamp)
    exit_code = render_task_templates.main(["--strict", "--allow-tbd", "--root", str(tmp_path)])
    assert exit_code == 0

    rerendered_json = json.loads(json_path.read_text(encoding="utf-8"))
    assert rerendered_json["render_meta"]["rendered_utc"] == first_timestamp
    assert rerendered_json["metadata"]["template_metadata"]["last_rendered_utc"] == first_timestamp

    markdown_lines = md_path.read_text(encoding="utf-8").splitlines()
    generated_line = next(line for line in markdown_lines if line.startswith("Generated:"))
    assert first_timestamp in generated_line


def test_render_updates_timestamps_when_yaml_changes(tmp_path, monkeypatch):
    repo_yaml = Path("DETAILED_TASK_LIST_template.yaml")
    target_yaml = tmp_path / repo_yaml.name
    target_yaml.write_text(repo_yaml.read_text(encoding="utf-8"), encoding="utf-8")

    baseline_timestamp = "2010-01-01T00:00:00Z"
    updated_timestamp = "2011-12-13T14:15:16Z"

    monkeypatch.setattr(render_task_templates, "_utc_now", lambda: baseline_timestamp)
    exit_code = render_task_templates.main(["--strict", "--allow-tbd", "--root", str(tmp_path)])
    assert exit_code == 0

    payload = yaml.safe_load(target_yaml.read_text(encoding="utf-8"))
    payload["metadata"]["project_goal"] = "Ship updated goal"
    target_yaml.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    monkeypatch.setattr(render_task_templates, "_utc_now", lambda: updated_timestamp)
    exit_code = render_task_templates.main(["--strict", "--allow-tbd", "--root", str(tmp_path)])
    assert exit_code == 0

    json_path = tmp_path / "DETAILED_TASK_LIST_template.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["render_meta"]["rendered_utc"] == updated_timestamp
    assert data["metadata"]["template_metadata"]["last_rendered_utc"] == updated_timestamp

    md_path = tmp_path / "DETAILED_TASK_LIST_template.md"
    markdown_lines = md_path.read_text(encoding="utf-8").splitlines()
    generated_line = next(line for line in markdown_lines if line.startswith("Generated:"))
    assert updated_timestamp in generated_line
