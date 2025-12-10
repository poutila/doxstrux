"""Extract deterministic facts from a Python codebase and serialize to multiple formats.

This is a generic fact extraction tool using golden_validator_hybrid.
It contains NO project-specific code - only generic Python analysis.

Primary output: FACTS.parquet (columnar, compressed, lazy-loadable)
Sidecar output: FACTS.json (human-readable)
Legacy output: FACTS.yaml (deprecated, will be removed)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List

import yaml
from golden_validator_hybrid.fact_extractor import get_all_facts
from golden_validator_hybrid.parquet_provider import write_facts, write_facts_json
from golden_validator_hybrid.rules_deterministic import RUBRIC_DESCRIPTIONS, RUBRIC_KEYS


def _dump(value: Any) -> str:
    """Serialize complex objects to JSON-friendly strings for FACTS."""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _collect_doc_metadata(base: Path) -> Dict[str, Dict[str, str]]:
    """Collect DOC_* metadata and bold field annotations from markdown docs.

    This is a generic collector that extracts structured metadata from
    markdown files in the base directory. It looks for:
    - **Key**: Value patterns (bold field annotations)
    - DOC_KEY: Value patterns (document metadata)
    """
    doc_meta: Dict[str, Dict[str, str]] = {}
    pattern_bold = re.compile(r"^\*\*(.+?)\*\*:\s*(.+)")
    pattern_doc = re.compile(r"^(DOC_[A-Z_]+):\s*(.+)")
    for doc_file in sorted(base.glob("*.md")):
        metadata: Dict[str, str] = {}
        lines = doc_file.read_text().splitlines()
        for line in lines[:40]:
            for pattern in (pattern_bold, pattern_doc):
                match = pattern.match(line.strip())
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    metadata[key] = value
        if metadata:
            doc_meta[doc_file.name] = metadata
    return doc_meta


def _collect_doc_facts(base: Path) -> Dict[str, Any]:
    """Capture document metadata written inside Markdown resources."""
    metadata = _collect_doc_metadata(base)
    if not metadata:
        return {}
    return {"docs.metadata": metadata}


def _collect_rubric_facts(_: Path) -> Dict[str, Any]:
    """Expose the GOLDEN_DOCS rubric keys/descriptions from golden_validator_hybrid."""
    return {
        "rubric.keys": RUBRIC_KEYS,
        "rubric.descriptions": RUBRIC_DESCRIPTIONS,
    }


Collector = Callable[[Path], Dict[str, Any]]

# Generic collectors that work on any Python codebase
COLLECTORS: List[Collector] = [
    _collect_doc_facts,
    _collect_rubric_facts,
]


def _collect_custom_facts(base: Path) -> Dict[str, Any]:
    """Run all generic collectors and merge their facts."""
    aggregated: Dict[str, Any] = {}
    for collector in COLLECTORS:
        aggregated.update(collector(base))
    return aggregated


def main() -> None:
    """Extract facts and write them to FACTS.parquet (primary), FACTS.json, and FACTS.yaml."""
    base = Path(__file__).parent
    parquet_path = base / "FACTS.parquet"
    json_path = base / "FACTS.json"
    yaml_path = base / "FACTS.yaml"  # Legacy, deprecated

    # Core fact extraction via golden_validator_hybrid
    facts = get_all_facts(base)

    # Add generic custom facts
    custom_facts = _collect_custom_facts(base)
    for key, value in custom_facts.items():
        facts[key] = _dump(value)

    # Primary output: Parquet (columnar, compressed, lazy-loadable)
    write_facts(facts, parquet_path)
    print(f"Generated: {parquet_path} ({parquet_path.stat().st_size / 1024:.1f} KB)")

    # Sidecar: JSON (human-readable)
    write_facts_json(facts, json_path)
    print(f"Generated: {json_path} ({json_path.stat().st_size / 1024:.1f} KB)")

    # Legacy: YAML (deprecated, will be removed)
    content = yaml.dump(facts, default_flow_style=False, sort_keys=False, allow_unicode=True)
    yaml_path.write_text(content, encoding="utf-8")
    print(f"Generated: {yaml_path} ({yaml_path.stat().st_size / 1024:.1f} KB) [DEPRECATED]")


if __name__ == "__main__":
    main()
