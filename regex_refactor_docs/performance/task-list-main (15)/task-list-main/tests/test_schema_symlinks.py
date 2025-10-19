from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "filename",
    [
        "detailed_task_list.schema.json",
        "phase_complete.schema.json",
        "task_result.schema.json",
    ],
)
def test_repository_schema_aliases_are_synced(filename: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    canonical = repo_root / "src" / "tasklist" / "schemas" / filename
    alias = repo_root / "tasklist" / "schemas" / filename

    assert canonical.exists(), f"Missing canonical schema: {canonical}"  # sanity check
    assert alias.exists(), f"Missing repository schema alias: {alias}"

    canonical_bytes = canonical.read_bytes()
    alias_bytes = alias.read_bytes()
    assert (
        canonical_bytes == alias_bytes
    ), f"Schema alias {alias} is out of sync with canonical {canonical}"
