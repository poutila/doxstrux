#!/usr/bin/env python3
"""Version normalization guardrail.

- Reads the canonical tuple from COMMON.md (§Version Metadata).
- Enforces schema_version in YAML front matter across markdown files (excluding archives/task_list_archive/work_folder/.git).
- Ensures version literals appear only in allowed files (COMMON.md, AI_TASK_LIST_SPEC_v1.md, ai_task_list_linter_v1_9.py) or allowed historical contexts.
- Enforces linter filename ↔ LINTER_VERSION major.minor match.
- Enforces ellipsis policy in SSOT docs.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterator, Tuple

import yaml

ROOT = Path(__file__).resolve().parent.parent
EXCLUDES = [
    "archive",
    "task_list_archive",
    "work_folder",
    ".git",
]
ALLOWED_VERSION_FILES = {
    ROOT / "COMMON.md",
    ROOT / "AI_TASK_LIST_SPEC_v1.md",
    ROOT / "tools" / "ai_task_list_linter_v1_9.py",
    ROOT / "AI_TASK_LIST_TEMPLATE_v6.md",
    ROOT / "CLEANING.md",
    ROOT / "MANUAL.md",
    # Input validation system files
    ROOT / "PROSE_INPUT_TEMPLATE_v1.md",
    ROOT / "PROSE_INPUT_DISCOVERY_PROMPT_v1.md",
    ROOT / "tools" / "prose_input_linter.py",
    ROOT / "PROSE_INPUT_REVIEW_PROMPT_v1.md",
    ROOT / "COMPLETE_VALIDATION.md",
}

HISTORICAL_RE = re.compile(
    r"(?i)(\b(previously|formerly|originally)\b.*\bv?\d+\.\d+\b|\bmigrated\s+from\b.*\bv?\d+\.\d+\b|\bwas\s+(version|v|schema_version)\s+\d+\.\d+\b)"
)

ELLIPSIS_ALLOWED_RE = re.compile(r"^(?:\$\s*)?(?:uv run|rg)\b.*\.\.\.")

VERSION_LINE_RE = re.compile(
    r"^-?\s*Spec:\s*v(\d+\.\d+)\s*(?:\(schema_version:\s*\"(\d+\.\d+)\"\))?\s*$"
    r"|^-?\s*schema_version:\s*\"(\d+\.\d+)\"\s*$"
    r"|^-?\s*Linter:\s*v(\d+\.\d+)\s*\(`?(?:tools/)?ai_task_list_linter_v(\d+)_(\d+)\.py`?\)\s*$"
    r"|^-?\s*Template:\s*v(\d+\.\d+)\s*$"
)

FRONTMATTER_RE = re.compile(r"^---\s*$")

LINTER_VERSION_RE = re.compile(r"LINTER_VERSION\s*=\s*['\"](\d+)\.(\d+)")


def fail(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    return any(exc in parts for exc in EXCLUDES)


def iter_md_files() -> Iterator[Path]:
    for p in ROOT.rglob("*.md"):
        if is_excluded(p):
            continue
        yield p


def parse_common_tuple() -> Tuple[str, str, str, str]:
    common = ROOT / "COMMON.md"
    if not common.exists():
        fail(f"COMMON.md not found at {common}")
    text = common.read_text(encoding="utf-8")
    m = re.search(r"^## \§Version Metadata\s*$", text, re.MULTILINE)
    if not m:
        fail("COMMON.md: heading '## §Version Metadata' not found")
    start = m.end()
    end = len(text)
    next_h = re.search(r"^## ", text[start:], re.MULTILINE)
    if next_h:
        end = start + next_h.start()
    block = text[start:end]
    spec = schema = linter = template = None
    for line in block.splitlines():
        vm = VERSION_LINE_RE.match(line.strip())
        if not vm:
            continue
        g = vm.groups()
        # Matches:
        # 0: spec from Spec line
        # 1: schema from Spec line
        # 2: schema standalone
        # 3: linter version (vX.Y)
        # 4: linter major
        # 5: linter minor
        # 6: template version
        if g[0]:
            spec = g[0]
        if g[1]:
            schema = g[1]
        if g[2]:
            schema = g[2]
        if g[3]:
            linter = g[3]
        if g[4] and g[5]:
            linter = f"{g[4]}.{g[5]}"
        if g[6]:
            template = g[6]
    if not all([spec, schema, linter, template]):
        fail("COMMON.md: could not parse full version tuple (spec/schema/linter/template)")
    return spec, schema, linter, template


def parse_frontmatter_metadata(p: Path) -> dict | None:
    """Parse full YAML front matter metadata."""
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not lines or not FRONTMATTER_RE.match(lines[0]):
        return None
    end_idx = None
    for i in range(1, len(lines)):
        if FRONTMATTER_RE.match(lines[i]):
            end_idx = i
            break
    if end_idx is None:
        return None
    yaml_content = "\n".join(lines[1:end_idx])
    try:
        metadata = yaml.safe_load(yaml_content)
        return metadata if metadata else None
    except yaml.YAMLError:
        return None


def parse_frontmatter_schema(p: Path) -> str | None:
    """Parse schema_version from YAML front matter using pyyaml."""
    metadata = parse_frontmatter_metadata(p)
    if metadata is None:
        return None
    # schema_version can be at top level or nested
    if "schema_version" in metadata:
        return str(metadata["schema_version"])
    # Check nested structures (e.g., prose_input.schema_version)
    for key, value in metadata.items():
        if isinstance(value, dict) and "schema_version" in value:
            return str(value["schema_version"])
    return None


def check_yaml_schema(schema_expected: str) -> None:
    for p in ROOT.rglob("*.md"):
        if is_excluded(p):
            continue
        metadata = parse_frontmatter_metadata(p)
        if metadata is None:
            continue
        # Skip prose input templates (they have their own validation system)
        if "prose_input" in metadata:
            continue
        schema = parse_frontmatter_schema(p)
        if schema and schema != schema_expected:
            fail(f"schema_version mismatch in {p}: {schema} != {schema_expected}")


def check_versions(spec_v: str, schema_v: str, linter_v: str) -> None:
    for p in iter_md_files():
        if "canonical_examples" in p.parts:
            continue
        if "validation" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if p in ALLOWED_VERSION_FILES:
            continue
        if p.name == "CHANGELOG.md":
            continue
        for m in re.finditer(r"v?\d+\.\d+", text):
            span = m.span()
            line_start = text.rfind("\n", 0, span[0]) + 1
            line_end = text.find("\n", span[1])
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]
            if "schema_version" in line:
                continue
            if HISTORICAL_RE.search(line):
                continue
            fail(f"Version literal in non-SSOT file {p}:{line_start}: {line.strip()}")
    linter_path = ROOT / "tools" / "ai_task_list_linter_v1_9.py"
    if not linter_path.exists():
        fail("Linter file tools/ai_task_list_linter_v1_9.py not found")
    linter_text = linter_path.read_text(encoding="utf-8", errors="ignore")
    mv = LINTER_VERSION_RE.search(linter_text)
    if not mv:
        fail("LINTER_VERSION not found in linter file")
    mv_tuple = f"{mv.group(1)}.{mv.group(2)}"
    if mv_tuple != linter_v:
        fail(f"LINTER_VERSION {mv_tuple} != expected {linter_v}")


def check_ellipsis() -> None:
    ssot_docs = [
        ROOT / "COMMON.md",
        ROOT / "AI_TASK_LIST_SPEC_v1.md",
        ROOT / "AI_TASK_LIST_TEMPLATE_v6.md",
        ROOT / "MANUAL.md",
    ]
    fence_re = re.compile(r"^```(?P<lang>\w+)?\s*$")
    for p in ssot_docs:
        text = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        in_fence = False
        lang = None
        for idx, line in enumerate(text, start=1):
            fm = fence_re.match(line)
            if fm:
                if not in_fence:
                    in_fence = True
                    lang = fm.group("lang")
                else:
                    in_fence = False
                    lang = None
                continue
            if "..." not in line:
                continue
            if not in_fence:
                fail(f"Ellipsis forbidden in prose: {p}:{idx}: {line.strip()}")
            if lang not in {"bash", "sh"}:
                fail(f"Ellipsis in non-bash fence: {p}:{idx}: {line.strip()}")
            if not ELLIPSIS_ALLOWED_RE.match(line.strip()):
                fail(f"Ellipsis violates allowed pattern: {p}:{idx}: {line.strip()}")


def main() -> None:
    spec_v, schema_v, linter_v, _ = parse_common_tuple()
    check_yaml_schema(schema_v)
    check_versions(spec_v, schema_v, linter_v)
    check_ellipsis()
    sys.exit(0)


if __name__ == "__main__":
    main()
