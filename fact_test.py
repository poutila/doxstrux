"""Extract deterministic facts from SPEKSI core and serialize to FACTS.parquet.

Primary output: FACTS.parquet (columnar, compressed, lazy-loadable)
Sidecar output: FACTS.json (human-readable)
Legacy output: FACTS.yaml (deprecated, will be removed)
"""

from __future__ import annotations

import ast
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml
from golden_validator_hybrid.fact_extractor import get_all_facts
from golden_validator_hybrid.parquet_provider import write_facts, write_facts_json
from golden_validator_hybrid.rules_deterministic import RUBRIC_DESCRIPTIONS, RUBRIC_KEYS
from speksi.core.autogen.parsers.parse_engine_pipeline_spec import parse_engine_pipeline_spec
from speksi.core.autogen.spec_ast_v2 import SpecHeader
from speksi.core.autogen.spec_kind_registry import DEPENDENCIES, REGISTRY, SPEC_KIND_REGISTRY


def _dump(value: Any) -> str:
    """Serialize complex objects to JSON-friendly strings for FACTS."""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _extract_string(node: ast.AST) -> Optional[str]:
    """Return the literal string value stored in an AST node, if present."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Str):  # type: ignore[attr-defined]
        return node.s  # type: ignore[attr-defined]
    return None


def _collect_spec_header_keys(spec_dir: Path) -> Dict[str, List[str]]:
    """Gather header key names from SPEKSI spec files."""
    header_re = re.compile(r"\s*([^:]+):\s*(.+)")
    spec_headers: Dict[str, List[str]] = {}
    for spec_file in sorted(spec_dir.glob("*.md")):
        text = spec_file.read_text()
        keys: List[str] = []
        inside = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("<!--"):
                inside = True
                stripped = stripped[4:].strip()
                if stripped.endswith("-->"):
                    stripped = stripped[:-3].strip()
                    inside = False
            if inside and stripped.endswith("-->"):
                stripped = stripped[:-3].strip()
                inside = False
            if inside or stripped.startswith("<!--") or stripped.endswith("-->"):
                match = header_re.match(stripped)
                if match:
                    key = match.group(1).strip()
                    if key and key not in keys:
                        keys.append(key)
            if not inside and stripped.endswith("-->"):
                break
        if keys:
            spec_headers[spec_file.name] = keys
    return spec_headers


def _collect_generator_targets(generators_dir: Path) -> Dict[str, List[str]]:
    """Gather literal arguments passed to BaseGenerator.write_file calls."""
    targets: Dict[str, List[str]] = {}

    class _WriteCollector(ast.NodeVisitor):
        def __init__(self) -> None:
            self.targets: List[str] = []

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            attr_name = ""
            if isinstance(func, ast.Attribute):
                attr_name = func.attr
            if attr_name == "write_file" and node.args:
                try:
                    target = ast.unparse(node.args[0])
                except AttributeError:
                    target = ast.dump(node.args[0])
                self.targets.append(target)
            self.generic_visit(node)

    for generator_file in sorted(generators_dir.glob("*.py")):
        try:
            tree = ast.parse(generator_file.read_text(), filename=str(generator_file))
        except SyntaxError:
            continue
        collector = _WriteCollector()
        collector.visit(tree)
        if collector.targets:
            targets[generator_file.stem] = collector.targets
    return targets


def _collect_pipelines(specs_dir: Path) -> Dict[str, List[str]]:
    """Use the ENGINE_PIPELINE_SPEC parser to expose pipelines."""
    pipeline_spec = specs_dir / "ENGINE_PIPELINE_SPEC.md"
    if not pipeline_spec.exists():
        return {}
    text = pipeline_spec.read_text()
    header = SpecHeader(kind="engine_pipeline", spec_id="ENGINE_PIPELINE_SPEC", version="0.0.0")
    ast_root = parse_engine_pipeline_spec(text, pipeline_spec, header)
    pipelines: Dict[str, List[str]] = {}
    for entity in ast_root.entities:
        if entity.entity_type == "pipeline":
            spec_kind = entity.fields.get("spec_kind")
            if spec_kind:
                pipelines[spec_kind] = []
    for entity in ast_root.entities:
        if entity.entity_type == "generator":
            pipeline = entity.fields.get("pipeline")
            gen_id = entity.fields.get("id")
            if pipeline and gen_id and pipeline in pipelines:
                pipelines[pipeline].append(gen_id)
    return pipelines


def _collect_validator_contracts(validators_dir: Path) -> Dict[str, Dict[str, List[str]]]:
    """Extract the entity expectations and error messages from validators."""
    contracts: Dict[str, Dict[str, List[str]]] = {}
    for validator_file in sorted(validators_dir.glob("validate_*.py")):
        try:
            tree = ast.parse(validator_file.read_text(), filename=str(validator_file))
        except SyntaxError:
            continue
        contract: Dict[str, List[str]] = {}
        entity_types: List[str] = []
        errors: List[str] = []

        class _ValidatorVisitor(ast.NodeVisitor):
            def visit_Compare(self, node: ast.Compare) -> None:
                left = node.left
                if isinstance(left, ast.Attribute) and left.attr == "entity_type":
                    for comparator in node.comparators:
                        value = _extract_string(comparator)
                        if value and value not in entity_types:
                            entity_types.append(value)
                self.generic_visit(node)

            def visit_Raise(self, node: ast.Raise) -> None:
                exc = node.exc
                if isinstance(exc, ast.Call):
                    func = exc.func
                    target_name = ""
                    if isinstance(func, ast.Attribute):
                        target_name = func.attr
                    elif isinstance(func, ast.Name):
                        target_name = func.id
                    if target_name == "ValueError" and exc.args:
                        message = _extract_string(exc.args[0])
                        if message:
                            errors.append(message)
                self.generic_visit(node)

        _ValidatorVisitor().visit(tree)
        if entity_types:
            contract["entity_types"] = sorted(entity_types)
        if errors:
            contract["errors"] = errors
        if contract:
            contracts[validator_file.stem] = contract
    return contracts


def _collect_doc_metadata(base: Path) -> Dict[str, Dict[str, str]]:
    """Collect DOC_* metadata and bold field annotations from markdown docs."""
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


def _collect_spec_header_facts(base: Path) -> Dict[str, Any]:
    """Assemble facts derived from the SPEKSI specs directory headers."""
    specs_dir = base / "specs"
    spec_headers = _collect_spec_header_keys(specs_dir)
    if not spec_headers:
        return {}
    facts: Dict[str, Any] = {}
    all_keys = sorted({key for keys in spec_headers.values() for key in keys})
    facts["specs.header_keys"] = all_keys
    for spec_name, keys in spec_headers.items():
        facts[f"specs.{spec_name}.header_keys"] = keys

    counts = Counter(key for keys in spec_headers.values() for key in keys)
    required = sorted([key for key, count in counts.items() if count == len(spec_headers)])
    optional = sorted([key for key in all_keys if key not in required])
    facts["specs.header.required"] = required
    facts["specs.header.optional"] = optional

    usage: Dict[str, List[str]] = defaultdict(list)
    for spec_name, keys in spec_headers.items():
        for key in keys:
            usage[key].append(spec_name)
    facts["specs.header.usage"] = {key: sorted(names) for key, names in usage.items()}
    return facts


class _ParserRegexVisitor(ast.NodeVisitor):
    """AST visitor that captures top-level re.compile assignments."""

    def __init__(self) -> None:
        self.patterns: List[Dict[str, str]] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        regex = self._extract_regex(node.value)
        if regex:
            target_name = ""
            target = node.targets[0]
            if isinstance(target, ast.Name):
                target_name = target.id
            self.patterns.append({"name": target_name, "pattern": regex})
        self.generic_visit(node)

    def _extract_regex(self, node: ast.AST) -> Optional[str]:
        if not isinstance(node, ast.Call):
            return None
        if not node.args:
            return None
        pattern = _extract_string(node.args[0])
        if pattern is None:
            return None
        func = node.func
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id == "re":
                if func.attr == "compile":
                    return pattern
        elif isinstance(func, ast.Name) and func.id == "compile":
            return pattern
        return None


def _collect_parser_expectations(base: Path) -> Dict[str, Any]:
    """Document parser module expectations (docstrings + regexes)."""
    parsers_dir = base / "autogen" / "parsers"
    expectations: Dict[str, Any] = {}
    for parser_file in sorted(parsers_dir.glob("*.py")):
        try:
            tree = ast.parse(parser_file.read_text(), filename=str(parser_file))
        except SyntaxError:
            continue
        detail: Dict[str, Any] = {}
        doc = ast.get_docstring(tree)
        if doc:
            detail["doc"] = doc
        visitor = _ParserRegexVisitor()
        visitor.visit(tree)
        if visitor.patterns:
            detail["regexes"] = visitor.patterns
        if detail:
            expectations[parser_file.stem] = detail
    return {"parser.expectations": expectations} if expectations else {}


def _collect_generator_artifacts(base: Path) -> Dict[str, Any]:
    """Produce generator artifact targets from write_file calls."""
    generators_dir = base / "autogen" / "generators"
    targets = _collect_generator_targets(generators_dir)
    if not targets:
        return {}
    facts: Dict[str, Any] = {
        "artifacts.manifest": targets,
        "artifacts.generators": sorted(targets.keys()),
    }
    for generator_name, paths in targets.items():
        facts[f"generator.{generator_name}.write_targets"] = paths
    return facts


def _collect_pipeline_facts(base: Path) -> Dict[str, Any]:
    """Expose pipelines and dependency wiring driven by ENGINE_PIPELINE_SPEC.md."""
    specs_dir = base / "specs"
    pipelines = _collect_pipelines(specs_dir)
    facts: Dict[str, Any] = {}
    if pipelines:
        facts["pipelines.available"] = sorted(pipelines.keys())
        facts["pipelines.registrations"] = pipelines
        for spec_kind, gens in pipelines.items():
            facts[f"pipelines.{spec_kind}.generators"] = gens
    if DEPENDENCIES:
        sorted_deps = {k: sorted(v) for k, v in DEPENDENCIES.items() if v}
        if sorted_deps:
            facts["pipelines.dependencies"] = sorted_deps
            for generator_id, deps in sorted(sorted_deps.items()):
                facts[f"pipelines.dependencies.{generator_id}"] = deps
    return facts


def _collect_validator_facts(base: Path) -> Dict[str, Any]:
    """Gather validator contracts (entity expectations and errors)."""
    validators_dir = base / "autogen" / "validators"
    contracts = _collect_validator_contracts(validators_dir)
    if not contracts:
        return {}
    return {"validators.contracts": contracts}


def _collect_doc_facts(base: Path) -> Dict[str, Any]:
    """Capture document metadata written inside Markdown resources."""
    metadata = _collect_doc_metadata(base)
    if not metadata:
        return {}
    return {"docs.metadata": metadata}


def _collect_rubric_facts(_: Path) -> Dict[str, Any]:
    """Expose the GOLDEN_DOCS rubric keys/descriptions embedded in the validator."""
    return {
        "rubric.keys": RUBRIC_KEYS,
        "rubric.descriptions": RUBRIC_DESCRIPTIONS,
    }


def _collect_registry_facts(_: Path) -> Dict[str, Any]:
    """Publish spec/generator registry entries from SPEKSI core."""
    facts: Dict[str, Any] = {}
    spec_kinds = sorted(SPEC_KIND_REGISTRY.keys())
    if spec_kinds:
        facts["registry.spec_kinds"] = spec_kinds
    generator_ids = sorted(REGISTRY.keys())
    if generator_ids:
        facts["registry.generators"] = generator_ids
        facts["registry.generator_classes"] = {
            gen_id: type(gen).__name__ for gen_id, gen in REGISTRY.items()
        }
    return facts


Collector = Callable[[Path], Dict[str, Any]]

COLLECTORS: List[Collector] = [
    _collect_spec_header_facts,
    _collect_parser_expectations,
    _collect_generator_artifacts,
    _collect_pipeline_facts,
    _collect_validator_facts,
    _collect_doc_facts,
    _collect_rubric_facts,
    _collect_registry_facts,
]


def _collect_custom_facts(base: Path) -> Dict[str, Any]:
    """Run all SPEKSI-specific collectors and merge their facts."""
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

    facts = get_all_facts(base)
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
