#!/usr/bin/env python3
"""
Regex Inventory Tool for Zero-Regex Refactoring

Scans markdown_parser_core.py for all regex usage and generates a categorized
inventory for phased replacement.

Usage:
    python tools/create_regex_inventory.py
    python tools/create_regex_inventory.py --output regex_refactor_docs/steps_taken/REGEX_INVENTORY.md
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def extract_regex_patterns(file_path: Path) -> List[Dict[str, Any]]:
    """Extract all regex patterns from the source file."""
    patterns = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, start=1):
        line_stripped = line.strip()

        # Skip comments and empty lines
        if not line_stripped or line_stripped.startswith("#"):
            continue

        # Find re.compile() patterns
        compile_match = re.search(r're\.compile\s*\(\s*r?["\']([^"\']+)["\']', line)
        if compile_match:
            pattern = compile_match.group(1)
            patterns.append({
                "line": line_num,
                "pattern": pattern,
                "type": "re.compile",
                "code": line.strip(),
            })
            continue

        # Find re.match/search/sub/findall/finditer/split patterns
        for method in ["match", "search", "sub", "findall", "finditer", "split"]:
            method_match = re.search(rf're\.{method}\s*\(\s*r?["\']([^"\']+)["\']', line)
            if method_match:
                pattern = method_match.group(1)
                patterns.append({
                    "line": line_num,
                    "pattern": pattern,
                    "type": f"re.{method}",
                    "code": line.strip(),
                })
                break

    return patterns


def get_function_context(file_path: Path, line_num: int) -> str:
    """Get the function or method name containing the given line."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Search backwards for function/method definition
    for i in range(line_num - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith("def ") or line.startswith("async def "):
            func_match = re.match(r"(?:async\s+)?def\s+(\w+)", line)
            if func_match:
                return func_match.group(1)
        elif line.startswith("class "):
            class_match = re.match(r"class\s+(\w+)", line)
            if class_match:
                return f"{class_match.group(1)} (class)"

    return "module-level"


def categorize_pattern(pattern: str, context: str, code: str) -> Dict[str, str]:
    """Categorize a regex pattern by replacement phase and purpose."""

    # Phase 1: Fence patterns (code blocks)
    if any(p in pattern for p in ["```", "~~~", r"^\s{4}", r"^    "]):
        return {
            "phase": "1",
            "purpose": "Fence/indented code detection",
            "replacement": "Token-based: Check token.type == 'fence' or 'code_block'",
        }

    # Phase 2: Inline formatting (bold, italic, etc.)
    if any(p in pattern for p in [r"\*\*", r"\*", r"__", r"_", r"`"]):
        return {
            "phase": "2",
            "purpose": "Inline formatting (bold/italic/code)",
            "replacement": "Token-based: Check token.type == 'strong', 'em', 'code_inline'",
        }

    # Phase 3: Links and images
    if any(p in pattern for p in [r"\[", r"\]", r"\(", r"!\[", "href"]):
        return {
            "phase": "3",
            "purpose": "Link/image extraction",
            "replacement": "Token-based: Check token.type == 'link_open', 'image'",
        }

    # Phase 4: HTML tags and sanitization
    if any(p in pattern for p in ["<", ">", "script", "iframe", "object", "embed", r"\bon\w+", "javascript:"]):
        return {
            "phase": "4",
            "purpose": "HTML detection/sanitization",
            "replacement": "Token-based: Check token.type == 'html_block', 'html_inline'; use bleach",
        }

    # Phase 5: Table separators
    if any(p in pattern for p in [r"\|", r"-{3,}"]):
        return {
            "phase": "5",
            "purpose": "Table structure detection",
            "replacement": "Token-based: Check token.type == 'table_open', 'tr_open', 'td_open'",
        }

    # Phase 6: Security patterns (RETAINED)
    if any(p in pattern for p in ["data:", "[a-zA-Z][a-zA-Z0-9+.-]*:", r"[a-z]:[/\\]", r"[\u", "CSP", "X-Frame"]):
        return {
            "phase": "6 (RETAINED)",
            "purpose": "Security validation (schemes, control chars, data-URIs)",
            "replacement": "KEEP: Security-critical pattern validation",
        }

    # Slugification patterns (Phase 2-adjacent)
    if any(p in pattern for p in [r"[\s/]+", r"[^\w-]", r"-+", r"^#+\s+"]):
        return {
            "phase": "2",
            "purpose": "Slug generation/text normalization",
            "replacement": "Token-based: Use token.content directly, normalize with string ops",
        }

    # Default: Needs manual categorization
    return {
        "phase": "?",
        "purpose": "Needs manual categorization",
        "replacement": "TBD",
    }


def generate_inventory_markdown(patterns: List[Dict[str, Any]], file_path: Path) -> str:
    """Generate markdown inventory document."""

    # Get function context for each pattern
    for pattern in patterns:
        pattern["context"] = get_function_context(file_path, pattern["line"])
        categorization = categorize_pattern(pattern["pattern"], pattern["context"], pattern["code"])
        pattern.update(categorization)

    # Group by phase
    by_phase = defaultdict(list)
    for pattern in patterns:
        by_phase[pattern["phase"]].append(pattern)

    # Generate markdown
    md = "# Regex Inventory for Zero-Regex Refactoring\n\n"
    md += "**Generated**: 2025-10-12\n\n"
    md += "**Source**: `src/docpipe/markdown_parser_core.py`\n\n"
    md += f"**Total Patterns**: {len(patterns)}\n\n"
    md += "---\n\n"
    md += "## Summary by Phase\n\n"

    # Phase summary table
    phase_order = ["1", "2", "3", "4", "5", "6 (RETAINED)", "?"]
    md += "| Phase | Count | Description |\n"
    md += "|-------|-------|-------------|\n"
    for phase in phase_order:
        if phase in by_phase:
            count = len(by_phase[phase])
            desc = by_phase[phase][0]["purpose"].split()[0:3]
            desc_str = " ".join(desc) + "..."
            md += f"| {phase} | {count} | {desc_str} |\n"

    md += f"\n**Total**: {len(patterns)} patterns\n\n"
    md += "---\n\n"

    # Detailed inventory by phase
    for phase in phase_order:
        if phase not in by_phase:
            continue

        md += f"## Phase {phase}\n\n"
        md += f"**Count**: {len(by_phase[phase])}\n\n"

        if phase == "6 (RETAINED)":
            md += "**Note**: These patterns are security-critical and will be RETAINED (not replaced).\n\n"

        md += "| Line | Context | Pattern | Purpose | Replacement Strategy |\n"
        md += "|------|---------|---------|---------|---------------------|\n"

        for p in sorted(by_phase[phase], key=lambda x: x["line"]):
            # Escape pipe characters in pattern
            pattern_escaped = p["pattern"].replace("|", "\\|")
            # Truncate long patterns
            if len(pattern_escaped) > 50:
                pattern_escaped = pattern_escaped[:47] + "..."

            purpose_short = p["purpose"][:40]
            replacement_short = p["replacement"][:50]

            md += f"| {p['line']} | `{p['context']}` | `{pattern_escaped}` | {purpose_short} | {replacement_short} |\n"

        md += "\n"

    # Add detailed code snippets section
    md += "---\n\n"
    md += "## Detailed Code Snippets\n\n"
    md += "Full code context for each regex pattern:\n\n"

    for phase in phase_order:
        if phase not in by_phase:
            continue

        md += f"### Phase {phase} - Detailed Snippets\n\n"

        for p in sorted(by_phase[phase], key=lambda x: x["line"]):
            md += f"**Line {p['line']}** (`{p['context']}`)\n"
            md += "```python\n"
            md += p["code"] + "\n"
            md += "```\n\n"

    # Add replacement notes
    md += "---\n\n"
    md += "## Replacement Strategy Notes\n\n"
    md += "### Phase 1: Fence Patterns\n"
    md += "- Replace with token.type checks: `token.type == 'fence'`, `token.type == 'code_block'`\n"
    md += "- Use token.info for language detection\n\n"

    md += "### Phase 2: Inline Formatting\n"
    md += "- Replace with token.type checks: `token.type in ['strong', 'em', 'code_inline']`\n"
    md += "- Use token.content for text extraction\n\n"

    md += "### Phase 3: Links/Images\n"
    md += "- Replace with token.type checks: `token.type in ['link_open', 'image']`\n"
    md += "- Use token.attrGet() for href/src extraction\n\n"

    md += "### Phase 4: HTML Sanitization\n"
    md += "- Replace with token.type checks: `token.type in ['html_block', 'html_inline']`\n"
    md += "- Continue using bleach for sanitization (no regex replacement needed)\n\n"

    md += "### Phase 5: Tables\n"
    md += "- Replace with token.type checks: `token.type in ['table_open', 'tr_open', 'td_open']`\n"
    md += "- Use token.children for cell content\n\n"

    md += "### Phase 6: Security Patterns (RETAINED)\n"
    md += "- **DO NOT REPLACE**: These patterns are security-critical\n"
    md += "- Includes: scheme validation, control character detection, data-URI parsing\n"
    md += "- Must remain as regex for security boundary enforcement\n\n"

    return md


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate regex inventory for refactoring")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("regex_refactor_docs/steps_taken/REGEX_INVENTORY.md"),
        help="Output markdown file path",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("src/docpipe/markdown_parser_core.py"),
        help="Source file to scan",
    )

    args = parser.parse_args()

    # Ensure source exists
    if not args.source.exists():
        print(f"Error: Source file not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    # Extract patterns
    print(f"Scanning {args.source}...")
    patterns = extract_regex_patterns(args.source)
    print(f"Found {len(patterns)} regex patterns")

    # Generate markdown
    print("Generating inventory...")
    markdown = generate_inventory_markdown(patterns, args.source)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Inventory written to: {args.output}")
    print("\nSummary:")
    print(f"  Total patterns: {len(patterns)}")

    # Count by phase
    by_phase = defaultdict(int)
    for p in patterns:
        context = get_function_context(args.source, p["line"])
        categorization = categorize_pattern(p["pattern"], context, p["code"])
        by_phase[categorization["phase"]] += 1

    for phase in sorted(by_phase.keys()):
        print(f"  Phase {phase}: {by_phase[phase]} patterns")

    sys.exit(0)


if __name__ == "__main__":
    main()
