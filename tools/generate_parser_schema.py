#!/usr/bin/env python3
"""
Generate JSON Schema for MarkdownParserCore output.

Uses genson to infer schema from parsing diverse markdown samples.
The resulting schema can be used for:
- Validating parser outputs
- Building markdown-JSON test pairs
- Documentation

Usage:
    .venv/bin/python tools/generate_parser_schema.py
    .venv/bin/python tools/generate_parser_schema.py --output schemas/parser_output.schema.json
    .venv/bin/python tools/generate_parser_schema.py --samples 100
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from genson import SchemaBuilder

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux.markdown_parser_core import MarkdownParserCore


def collect_markdown_files(test_dir: Path, max_files: int = 50) -> list[Path]:
    """Collect diverse markdown files for schema inference."""
    files = list(test_dir.rglob("*.md"))
    # Sort by name for reproducibility, then take subset
    files.sort(key=lambda p: p.name)
    return files[:max_files]


def generate_schema(
    test_dir: Path,
    max_samples: int = 50,
    verbose: bool = False,
) -> dict:
    """
    Generate JSON Schema by parsing markdown samples.

    Args:
        test_dir: Directory containing markdown test files
        max_samples: Maximum number of files to parse
        verbose: Print progress

    Returns:
        JSON Schema dict
    """
    builder = SchemaBuilder()
    builder.add_schema({"type": "object"})

    # Collect from primary test_dir
    files = collect_markdown_files(test_dir, max_samples)
    
    # Also collect from additional_test_mds if it exists and wasn't passed as test_dir
    add_dir = test_dir.parent / "additional_test_mds"
    if add_dir.exists() and add_dir != test_dir:
        files.extend(collect_markdown_files(add_dir, max_samples))
        
    # Also try the 'claude_tests' subdir specifically if we are pointing at tools/test_mds
    claude_dir = add_dir / "claude_tests"
    if claude_dir.exists():
         files.extend(collect_markdown_files(claude_dir, max_samples))

    if verbose:
        print(f"Found {len(files)} markdown files from {test_dir} and neighbors")

    parsed_count = 0
    errors = []

    for md_file in files:
        try:
            content = md_file.read_text(encoding="utf-8")
            parser = MarkdownParserCore(content, security_profile="permissive")
            result = parser.parse()

            # Remove raw content to keep schema focused on structure
            # (raw content is always str, lines is always list[str])
            if "content" in result:
                result["content"] = {"raw": "", "lines": []}

            builder.add_object(result)
            parsed_count += 1

            if verbose and parsed_count % 10 == 0:
                print(f"  Parsed {parsed_count}/{len(files)} files...")

        except Exception as e:
            errors.append((md_file.name, str(e)))
            if verbose:
                print(f"  SKIP {md_file.name}: {e}")

    if verbose:
        print(f"Successfully parsed {parsed_count} files")
        if errors:
            print(f"Skipped {len(errors)} files with errors")

    schema = builder.to_schema()

    # Add metadata
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    schema["$id"] = "https://doxstrux.dev/schemas/parser-output.schema.json"
    schema["title"] = "DoxstruxParserOutput"
    schema["description"] = (
        "JSON Schema for MarkdownParserCore.parse() output. "
        f"Generated from {parsed_count} sample documents."
    )

    # Fix dynamic key objects (line_to_type, line_to_section have line numbers as keys)
    schema = _fix_dynamic_key_schemas(schema)

    return schema


def _fix_dynamic_key_schemas(schema: dict) -> dict:
    """
    Fix objects with dynamic keys (like line_to_type, line_to_section).

    Genson infers these as objects with specific numeric keys, but they should
    use additionalProperties since keys are dynamic line numbers.
    """
    mappings = schema.get("properties", {}).get("mappings", {}).get("properties", {})

    # line_to_type: {0: "prose", 1: "code", ...} -> additionalProperties: {type: string}
    if "line_to_type" in mappings:
        mappings["line_to_type"] = {
            "type": "object",
            "description": "Map of line number to content type (prose, code, etc.)",
            "additionalProperties": {"type": "string"},
        }

    # line_to_section: {0: "section_0", ...} -> additionalProperties: {type: string}
    if "line_to_section" in mappings:
        mappings["line_to_section"] = {
            "type": "object",
            "description": "Map of line number to section ID",
            "additionalProperties": {"type": "string"},
        }

    # node_counts also has dynamic keys (node type names)
    node_counts = (
        schema.get("properties", {})
        .get("metadata", {})
        .get("properties", {})
        .get("node_counts", {})
    )
    if node_counts:
        schema["properties"]["metadata"]["properties"]["node_counts"] = {
            "type": "object",
            "description": "Count of each AST node type",
            "additionalProperties": {"type": "integer"},
        }

    # link_schemes in security.statistics
    security_stats = (
        schema.get("properties", {})
        .get("metadata", {})
        .get("properties", {})
        .get("security", {})
        .get("properties", {})
        .get("statistics", {})
        .get("properties", {})
    )
    if security_stats and "link_schemes" in security_stats:
        security_stats["link_schemes"] = {
            "type": "object",
            "description": "Count of links by scheme (https, mailto, relative, etc.)",
            "additionalProperties": {"type": "integer"},
        }

    # Remove 'required' requirements from top-level and structure objects
    # to handle partial outputs or dynamic content omission.
    def make_optional(s):
        if isinstance(s, dict):
            if "required" in s:
                del s["required"]
            for v in s.values():
                make_optional(v)

    make_optional(schema)

    # Fix nullable fields that genson may have incorrectly typed as only null
    # when training data lacked examples with non-null values
    _fix_nullable_fields(schema)

    return schema


def _fix_nullable_fields(schema: dict) -> None:
    """
    Fix fields that can be null OR another type.

    Genson infers type from observed values. If it only sees nulls,
    it types the field as {type: null}, but we need {type: [null, string]}.
    """
    structure = schema.get("properties", {}).get("structure", {}).get("properties", {})

    # images[].scheme can be null or string
    images_items = structure.get("images", {}).get("items", {}).get("properties", {})
    if images_items:
        if "scheme" in images_items:
            images_items["scheme"] = {"type": ["null", "string"]}
        if "alt" in images_items:
            images_items["alt"] = {"type": ["null", "string"]}
        if "title" in images_items:
            images_items["title"] = {"type": ["null", "string"]}

    # links[].scheme can be null or string
    links_items = structure.get("links", {}).get("items", {}).get("properties", {})
    if links_items and "scheme" in links_items:
        links_items["scheme"] = {"type": ["null", "string"]}

    # tasklists items checked can be null or boolean
    _fix_tasklist_checked(structure.get("tasklists", {}))

    # lists items can have various nullable fields
    _fix_list_items(structure.get("lists", {}))

    # blockquotes section_id can be null or string
    bq_items = structure.get("blockquotes", {}).get("items", {}).get("properties", {})
    if bq_items and "section_id" in bq_items:
        bq_items["section_id"] = {"type": ["null", "string"]}

    # code_blocks section_id can be null or string
    cb_items = structure.get("code_blocks", {}).get("items", {}).get("properties", {})
    if cb_items and "section_id" in cb_items:
        cb_items["section_id"] = {"type": ["null", "string"]}

    # paragraphs section_id can be null or string
    para_items = structure.get("paragraphs", {}).get("items", {}).get("properties", {})
    if para_items and "section_id" in para_items:
        para_items["section_id"] = {"type": ["null", "string"]}

    # sections parent_id can be null or string
    sec_items = structure.get("sections", {}).get("items", {}).get("properties", {})
    if sec_items and "parent_id" in sec_items:
        sec_items["parent_id"] = {"type": ["null", "string"]}

    # headings parent_heading_id can be null or string
    hdg_items = structure.get("headings", {}).get("items", {}).get("properties", {})
    if hdg_items and "parent_heading_id" in hdg_items:
        hdg_items["parent_heading_id"] = {"type": ["null", "string"]}

    # tables section_id can be null or string
    tbl_items = structure.get("tables", {}).get("items", {}).get("properties", {})
    if tbl_items and "section_id" in tbl_items:
        tbl_items["section_id"] = {"type": ["null", "string"]}

    # footnotes references[].id can be string or integer
    fn_refs = (
        structure.get("footnotes", {})
        .get("properties", {})
        .get("references", {})
        .get("items", {})
        .get("properties", {})
    )
    if fn_refs and "id" in fn_refs:
        fn_refs["id"] = {"type": ["string", "integer"]}

    # footnotes definitions[].id can be string or integer
    fn_defs = (
        structure.get("footnotes", {})
        .get("properties", {})
        .get("definitions", {})
        .get("items", {})
        .get("properties", {})
    )
    if fn_defs and "id" in fn_defs:
        fn_defs["id"] = {"type": ["string", "integer"]}


def _fix_tasklist_checked(tasklists_schema: dict) -> None:
    """Recursively fix checked field in tasklist items to allow null or boolean."""
    def fix_items(items_schema: dict) -> None:
        if not items_schema:
            return
        props = items_schema.get("properties", {})
        if "checked" in props:
            props["checked"] = {"type": ["null", "boolean"]}
        # Recurse into children
        children = props.get("children", {}).get("items", {})
        if children:
            fix_items(children)

    items = tasklists_schema.get("items", {}).get("properties", {}).get("items", {})
    if items and "items" in items:
        for item in [items.get("items", {})]:
            fix_items(item)


def _fix_list_items(lists_schema: dict) -> None:
    """Fix list item schemas to handle nullable text fields."""
    def fix_items(items_schema: dict) -> None:
        if not items_schema:
            return
        props = items_schema.get("properties", {})
        if "text" in props:
            props["text"] = {"type": ["null", "string"]}
        # Recurse into children
        children = props.get("children", {}).get("items", {})
        if children:
            fix_items(children)

    items = lists_schema.get("items", {}).get("properties", {}).get("items", {})
    if items and "items" in items:
        fix_items(items.get("items", {}))


def main():
    parser = argparse.ArgumentParser(
        description="Generate JSON Schema for parser output"
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path(__file__).parent / "test_mds",
        help="Directory containing markdown test files",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(__file__).parent.parent / "schemas" / "parser_output.schema.json",
        help="Output schema file path",
    )
    parser.add_argument(
        "--samples",
        "-n",
        type=int,
        default=50,
        help="Maximum number of samples to parse",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print progress",
    )

    args = parser.parse_args()

    if not args.test_dir.exists():
        print(f"Error: Test directory not found: {args.test_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Generating schema from {args.test_dir}...")
    schema = generate_schema(args.test_dir, args.samples, args.verbose)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write schema
    args.output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Schema written to {args.output}")

    # Print summary
    props = schema.get("properties", {})
    print(f"\nTop-level properties: {list(props.keys())}")

    if "structure" in props:
        struct_props = props["structure"].get("properties", {})
        print(f"Structure keys: {list(struct_props.keys())}")


if __name__ == "__main__":
    main()
