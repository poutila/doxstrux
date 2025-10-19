"""Minimal build backend to install the tasklist package without external build deps."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import textwrap
import zipfile
from pathlib import Path
from typing import Iterable, Mapping

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    import tomli as tomllib  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"


def _load_project() -> Mapping[str, object]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict):  # pragma: no cover - defensive
        raise RuntimeError("pyproject.toml missing [project] table")
    return project


def _normalize(name: str) -> str:
    return name.replace("-", "_")


def _metadata_text(project: Mapping[str, object]) -> str:
    name = project.get("name", "")
    version = project.get("version", "0")
    summary = project.get("description", "")
    requires_python = project.get("requires-python")
    dependencies = project.get("dependencies", [])
    authors = project.get("authors", [])

    lines = [
        "Metadata-Version: 2.1",
        f"Name: {name}",
        f"Version: {version}",
    ]
    if summary:
        lines.append(f"Summary: {summary}")
    if requires_python:
        lines.append(f"Requires-Python: {requires_python}")
    for author in authors:
        if isinstance(author, dict) and author.get("name"):
            lines.append(f"Author: {author['name']}")
    for dep in dependencies or []:
        lines.append(f"Requires-Dist: {dep}")
    lines.append("")
    return "\n".join(lines)


def _wheel_text(generator: str = "tasklist-build-backend") -> str:
    return textwrap.dedent(
        f"""
        Wheel-Version: 1.0
        Generator: {generator}
        Root-Is-Purelib: true
        Tag: py3-none-any
        """
    ).lstrip()


def _entry_points(project: Mapping[str, object]) -> str:
    scripts = project.get("scripts", {})
    if not isinstance(scripts, dict) or not scripts:
        return ""

    lines = ["[console_scripts]"]
    for name, target in scripts.items():
        lines.append(f"{name} = {target}")
    lines.append("")
    return "\n".join(lines)


def _package_files() -> Iterable[tuple[Path, str]]:
    package_root = SRC_DIR / "tasklist"
    for file_path in package_root.rglob("*"):
        if file_path.is_file():
            relative = file_path.relative_to(SRC_DIR)
            yield file_path, relative.as_posix()


def _encode_record(path: str, data: bytes) -> tuple[str, str, str]:
    digest = hashlib.sha256(data).digest()
    b64 = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return path, f"sha256={b64}", str(len(data))


def _build_wheel(wheel_directory: Path, editable: bool = False) -> str:
    project = _load_project()
    dist_name = str(project.get("name", "tasklist-tools"))
    norm_name = _normalize(dist_name)
    version = str(project.get("version", "0"))

    dist_info = f"{norm_name}-{version}.dist-info"
    wheel_name = f"{norm_name}-{version}-py3-none-any.whl"
    wheel_path = wheel_directory / wheel_name

    records: list[tuple[str, str, str]] = []

    with zipfile.ZipFile(wheel_path, "w") as zf:
        if not editable:
            for src, arc in _package_files():
                data = src.read_bytes()
                zf.writestr(arc, data)
                records.append(_encode_record(arc, data))
        else:
            pth_content = (SRC_DIR.resolve().as_posix() + "\n").encode("utf-8")
            pth_name = f"{norm_name}.pth"
            zf.writestr(pth_name, pth_content)
            records.append(_encode_record(pth_name, pth_content))

        meta_text = _metadata_text(project).encode("utf-8")
        meta_path = f"{dist_info}/METADATA"
        zf.writestr(meta_path, meta_text)
        records.append(_encode_record(meta_path, meta_text))

        wheel_text = _wheel_text().encode("utf-8")
        wheel_file = f"{dist_info}/WHEEL"
        zf.writestr(wheel_file, wheel_text)
        records.append(_encode_record(wheel_file, wheel_text))

        entry_points = _entry_points(project)
        if entry_points:
            ep_bytes = entry_points.encode("utf-8")
            ep_path = f"{dist_info}/entry_points.txt"
            zf.writestr(ep_path, ep_bytes)
            records.append(_encode_record(ep_path, ep_bytes))

        direct_url = {
            "url": ROOT.resolve().as_uri(),
            "dir_info": {"editable": editable},
        }
        direct_bytes = json.dumps(direct_url, indent=2).encode("utf-8")
        direct_path = f"{dist_info}/direct_url.json"
        zf.writestr(direct_path, direct_bytes)
        records.append(_encode_record(direct_path, direct_bytes))

        record_path = f"{dist_info}/RECORD"
        record_lines = "\n".join(
            f"{path},{hash_value},{size}" for path, hash_value, size in records
        ) + f"\n{record_path},,\n"
        zf.writestr(record_path, record_lines.encode("utf-8"))

    return wheel_path.name


def build_wheel(
    wheel_directory: str, config_settings: Mapping[str, object] | None = None, metadata_directory: str | None = None
) -> str:
    return _build_wheel(Path(wheel_directory), editable=False)


def build_editable(
    wheel_directory: str, config_settings: Mapping[str, object] | None = None, metadata_directory: str | None = None
) -> str:
    return _build_wheel(Path(wheel_directory), editable=True)


def _prepare_metadata(metadata_directory: Path) -> str:
    project = _load_project()
    dist_name = str(project.get("name", "tasklist-tools"))
    norm_name = _normalize(dist_name)
    version = str(project.get("version", "0"))

    dist_info = metadata_directory / f"{norm_name}-{version}.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)

    dist_info.joinpath("METADATA").write_text(_metadata_text(project), encoding="utf-8")
    dist_info.joinpath("WHEEL").write_text(_wheel_text(), encoding="utf-8")
    entry_points = _entry_points(project)
    if entry_points:
        dist_info.joinpath("entry_points.txt").write_text(entry_points, encoding="utf-8")
    return dist_info.name


def prepare_metadata_for_build_wheel(
    metadata_directory: str, config_settings: Mapping[str, object] | None = None
) -> str:
    return _prepare_metadata(Path(metadata_directory))


def get_requires_for_build_wheel(config_settings: Mapping[str, object] | None = None) -> list[str]:
    return []


def get_requires_for_build_editable(config_settings: Mapping[str, object] | None = None) -> list[str]:
    return []


def prepare_metadata_for_build_editable(
    metadata_directory: str, config_settings: Mapping[str, object] | None = None
) -> str:
    return _prepare_metadata(Path(metadata_directory))


def build_sdist(sdist_directory: str, config_settings: Mapping[str, object] | None = None) -> str:
    project = _load_project()
    dist_name = str(project.get("name", "tasklist-tools"))
    version = str(project.get("version", "0"))
    archive_name = f"{dist_name}-{version}.tar.gz"
    sdist_path = Path(sdist_directory) / archive_name

    import tarfile

    with tarfile.open(sdist_path, "w:gz") as tar:
        for path in ROOT.iterdir():
            if path.name in {".git", "__pycache__", "build", "dist", ".venv"}:
                continue
            tar.add(path, arcname=f"{dist_name}-{version}/{path.name}")
    return archive_name
