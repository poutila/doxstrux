#!/usr/bin/env python3
"""
Comprehensive data loss validation for all markdown files in test suite.

This script performs deep validation of every markdown file to ensure no data
is lost during processing. It checks:
- Sections and headings
- Code blocks with languages
- Lists and nesting levels
- Requirements (MUST/SHOULD/MAY)
- Tables
- Links (internal, external, anchors)
- Checklists/task lists
- Special markdown features

Usage:
    uv run scripts/validate_comprehensive_data_loss.py [--verbose] [--limit N]
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


def make_json_serializable(obj: Any) -> Any:
    """Recursively convert Path objects to strings for JSON serialization."""
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(make_json_serializable(item) for item in obj)
    return obj


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher


class ComprehensiveValidator:
    """Validate markdown processing for data loss."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = []
        self.total_issues = 0
        self.files_with_issues = 0

    def analyze_raw_markdown(self, file_path: Path) -> dict[str, Any]:
        """Manually analyze raw markdown to establish ground truth."""
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        analysis = {
            "file": file_path.name,
            "path": str(file_path),
            "size_bytes": len(content),
            "line_count": len(lines),
            "headings": self._count_headings(lines),
            "code_blocks": self._count_code_blocks(content),
            "lists": self._analyze_lists(lines),
            "links": self._extract_links(content),
            "tables": self._count_tables(lines),
            "requirements": self._extract_requirements(content),
            "task_lists": self._count_task_lists(lines),
            "blockquotes": self._count_blockquotes(lines),
            "emphasis": self._count_emphasis(content),
        }

        return analysis

    def _count_headings(self, lines: list[str]) -> dict[str, int]:
        """Count headings at each level."""
        headings = {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0, "total": 0}

        for line in lines:
            if line.startswith("#"):
                # Count the number of # characters
                level = 0
                for char in line:
                    if char == "#":
                        level += 1
                    else:
                        break

                if 1 <= level <= 6:
                    headings[f"h{level}"] += 1
                    headings["total"] += 1

        return headings

    def _count_code_blocks(self, content: str) -> dict[str, Any]:
        """Count code blocks and identify languages."""
        # Match code blocks with ``` or ~~~
        pattern = r"```(\w*)|~~~(\w*)"
        matches = re.findall(pattern, content)

        languages = {}
        total_blocks = len(matches) // 2  # Opening and closing markers

        for match in matches:
            lang = match[0] or match[1]
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        # Also check for indented code blocks (4 spaces or tab)
        indented_blocks = 0
        in_code = False
        for line in content.split("\n"):
            if line.startswith("    ") or line.startswith("\t"):
                if not in_code:
                    indented_blocks += 1
                    in_code = True
            else:
                in_code = False

        return {
            "fenced": total_blocks,
            "indented": indented_blocks,
            "total": total_blocks + indented_blocks,
            "languages": languages,
        }

    def _analyze_lists(self, lines: list[str]) -> dict[str, Any]:
        """Analyze list structures and nesting."""
        lists = {"bullet_lists": 0, "ordered_lists": 0, "max_nesting": 0, "total_items": 0}

        current_nesting = 0
        for line in lines:
            # Bullet lists (-, *, +)
            if re.match(r"^[ \t]*[-*+] ", line):
                lists["total_items"] += 1
                if not lists["bullet_lists"]:
                    lists["bullet_lists"] += 1

                # Calculate nesting level
                indent = len(line) - len(line.lstrip())
                nesting = indent // 2  # Approximate nesting
                lists["max_nesting"] = max(lists["max_nesting"], nesting)

            # Ordered lists
            elif re.match(r"^[ \t]*\d+\. ", line):
                lists["total_items"] += 1
                if not lists["ordered_lists"]:
                    lists["ordered_lists"] += 1

                indent = len(line) - len(line.lstrip())
                nesting = indent // 2
                lists["max_nesting"] = max(lists["max_nesting"], nesting)

        return lists

    def _extract_links(self, content: str) -> dict[str, Any]:
        """Extract all types of links."""
        links = {
            "markdown_links": [],  # [text](url)
            "reference_links": [],  # [text][ref]
            "auto_links": [],  # <url>
            "raw_urls": [],  # http://...
            "internal_links": [],  # Links to local files
            "external_links": [],  # Links to external sites
            "anchor_links": [],  # Links with #anchor
            "total": 0,
        }

        # Markdown links [text](url)
        md_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
        for match in re.finditer(md_pattern, content):
            text, url = match.groups()
            links["markdown_links"].append({"text": text, "url": url})

            # Classify the link
            if url.startswith("#"):
                links["anchor_links"].append(url)
            elif url.startswith("http://") or url.startswith("https://"):
                links["external_links"].append(url)
            elif not url.startswith("mailto:"):
                links["internal_links"].append(url)

        # Reference links [text][ref]
        ref_pattern = r"\[([^\]]+)\]\[([^\]]+)\]"
        for match in re.finditer(ref_pattern, content):
            links["reference_links"].append(match.groups())

        # Auto links <url>
        auto_pattern = r"<(https?://[^>]+)>"
        for match in re.finditer(auto_pattern, content):
            links["auto_links"].append(match.group(1))
            links["external_links"].append(match.group(1))

        # Raw URLs
        url_pattern = r"(?<!\()https?://[^\s\)]+"
        for match in re.finditer(url_pattern, content):
            url = match.group(0)
            if url not in links["external_links"]:
                links["raw_urls"].append(url)
                links["external_links"].append(url)

        links["total"] = (
            len(links["markdown_links"])
            + len(links["reference_links"])
            + len(links["auto_links"])
            + len(links["raw_urls"])
        )

        return links

    def _count_tables(self, lines: list[str]) -> dict[str, int]:
        """Count markdown tables."""
        tables = {"pipe_tables": 0, "html_tables": 0, "total": 0}

        in_table = False
        for i, line in enumerate(lines):
            # Pipe tables
            if "|" in line:
                # Check if next line is separator
                if i + 1 < len(lines) and re.match(r"^[\s\|:\-]+$", lines[i + 1]):
                    if not in_table:
                        tables["pipe_tables"] += 1
                        in_table = True
            else:
                in_table = False

            # HTML tables
            if "<table" in line.lower():
                tables["html_tables"] += 1

        tables["total"] = tables["pipe_tables"] + tables["html_tables"]
        return tables

    def _extract_requirements(self, content: str) -> dict[str, list[str]]:
        """Extract requirement patterns."""
        requirements = {
            "MUST": [],
            "SHOULD": [],
            "MAY": [],
            "MUST_NOT": [],
            "SHOULD_NOT": [],
            "total": 0,
        }

        patterns = {
            "MUST": r"\bMUST\s+[A-Z\w]",
            "SHOULD": r"\bSHOULD\s+[A-Z\w]",
            "MAY": r"\bMAY\s+[A-Z\w]",
            "MUST_NOT": r"\bMUST\s+NOT\s+[A-Z\w]",
            "SHOULD_NOT": r"\bSHOULD\s+NOT\s+[A-Z\w]",
        }

        for req_type, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Extract the sentence containing the requirement
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 100)
                context = content[start:end].replace("\n", " ").strip()
                requirements[req_type].append(context)

        requirements["total"] = sum(len(v) for v in requirements.values() if isinstance(v, list))
        return requirements

    def _count_task_lists(self, lines: list[str]) -> dict[str, int]:
        """Count task list items."""
        tasks = {"checked": 0, "unchecked": 0, "total": 0}

        for line in lines:
            if re.match(r"^[ \t]*[-*+] \[x\]", line, re.IGNORECASE):
                tasks["checked"] += 1
            elif re.match(r"^[ \t]*[-*+] \[ \]", line):
                tasks["unchecked"] += 1

        tasks["total"] = tasks["checked"] + tasks["unchecked"]
        return tasks

    def _count_blockquotes(self, lines: list[str]) -> int:
        """Count blockquote lines."""
        return sum(1 for line in lines if line.strip().startswith(">"))

    def _count_emphasis(self, content: str) -> dict[str, int]:
        """Count emphasis markers."""
        return {
            "bold": len(re.findall(r"\*\*[^*]+\*\*|__[^_]+__", content)),
            "italic": len(re.findall(r"(?<!\*)\*[^*]+\*(?!\*)|(?<!_)_[^_]+_(?!_)", content)),
            "code": len(re.findall(r"`[^`]+`", content)),
            "strikethrough": len(re.findall(r"~~[^~]+~~", content)),
        }

    def process_with_framework(self, file_path: Path) -> dict[str, Any]:
        """Process file with docpipe framework."""
        try:
            enricher = MarkdownDocEnricher(file_path)
            doc = enricher.extract_rich_doc()

            # Extract framework results
            # Use aggregated links from all sections
            all_links = doc.all_section_links

            framework_results = {
                "sections": len(doc.sections),
                "headings": {
                    "total": len(doc.sections),
                    "h1": sum(1 for s in doc.sections if s.level == 1),
                    "h2": sum(1 for s in doc.sections if s.level == 2),
                    "h3": sum(1 for s in doc.sections if s.level == 3),
                    "h4": sum(1 for s in doc.sections if s.level == 4),
                    "h5": sum(1 for s in doc.sections if s.level == 5),
                    "h6": sum(1 for s in doc.sections if s.level == 6),
                },
                "code_blocks": {"total": len(doc.code_blocks), "languages": {}},
                "requirements": {
                    "MUST": len([r for r in doc.requirements if r.type == "MUST"]),
                    "SHOULD": len([r for r in doc.requirements if r.type == "SHOULD"]),
                    "MAY": len([r for r in doc.requirements if r.type == "MAY"]),
                    "MUST_NOT": len([r for r in doc.requirements if r.type == "MUST NOT"]),
                    "total": len(doc.requirements),
                },
                "links": {
                    "total": sum(len(v) if isinstance(v, list) else 0 for v in all_links.values()),
                    "valid_file": len(all_links.get("valid_file", [])),
                    "invalid_file": len(all_links.get("invalid_file", [])),
                    "invalid_anchor": len(all_links.get("invalid_anchor", [])),
                    "external": len(all_links.get("external", [])),
                    "raw_urls": len(all_links.get("raw_urls", [])),
                    "raw_links": all_links,
                    "all_section_links": {
                        f"section_{i}": section.links for i, section in enumerate(doc.sections)
                    },
                },
                "lists": {"total": len(doc.lists), "max_nesting": 0, "total_items": 0},
                "tables": len(doc.tables) if hasattr(doc, "tables") else 0,
                "task_lists": len(doc.checklist_items),
                "heading_valid": doc.heading_structure_valid,
            }

            # Get language distribution
            for cb in doc.code_blocks:
                lang = cb.language or "none"
                framework_results["code_blocks"]["languages"][lang] = (
                    framework_results["code_blocks"]["languages"].get(lang, 0) + 1
                )

            # Calculate max nesting and total items for lists
            for section in doc.sections:
                if section.lists:
                    for lst in section.lists:
                        framework_results["lists"]["total_items"] += len(lst.items)
                        for item in lst.items:
                            framework_results["lists"]["max_nesting"] = max(
                                framework_results["lists"]["max_nesting"], item.level
                            )

            return {"success": True, "data": framework_results}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def compare_results(self, manual: dict, framework: dict) -> dict[str, Any]:
        """Compare manual analysis with framework results."""
        issues = []

        # Compare headings
        if manual["headings"]["total"] != framework["headings"]["total"]:
            issues.append(
                {
                    "type": "heading_count",
                    "manual": manual["headings"]["total"],
                    "framework": framework["headings"]["total"],
                    "difference": manual["headings"]["total"] - framework["headings"]["total"],
                }
            )

        # Compare code blocks
        if manual["code_blocks"]["total"] != framework["code_blocks"]["total"]:
            issues.append(
                {
                    "type": "code_block_count",
                    "manual": manual["code_blocks"]["total"],
                    "framework": framework["code_blocks"]["total"],
                    "difference": manual["code_blocks"]["total"]
                    - framework["code_blocks"]["total"],
                }
            )

        # Compare requirements
        if manual["requirements"]["total"] != framework["requirements"]["total"]:
            issues.append(
                {
                    "type": "requirements_count",
                    "manual": manual["requirements"]["total"],
                    "framework": framework["requirements"]["total"],
                    "difference": manual["requirements"]["total"]
                    - framework["requirements"]["total"],
                    "details": {
                        "MUST": f"{manual['requirements']['MUST']} vs {framework['requirements']['MUST']}",
                        "SHOULD": f"{manual['requirements']['SHOULD']} vs {framework['requirements']['SHOULD']}",
                        "MAY": f"{manual['requirements']['MAY']} vs {framework['requirements']['MAY']}",
                    },
                }
            )

        # Compare links
        if manual["links"]["total"] != framework["links"]["total"]:
            issues.append(
                {
                    "type": "links_count",
                    "manual": manual["links"]["total"],
                    "framework": framework["links"]["total"],
                    "difference": manual["links"]["total"] - framework["links"]["total"],
                    "details": {
                        "internal": len(manual["links"]["internal_links"]),
                        "external": len(manual["links"]["external_links"]),
                        "anchors": len(manual["links"]["anchor_links"]),
                    },
                }
            )

        # Compare lists
        if manual["lists"]["total_items"] != framework["lists"]["total_items"]:
            issues.append(
                {
                    "type": "list_items",
                    "manual": manual["lists"]["total_items"],
                    "framework": framework["lists"]["total_items"],
                    "difference": manual["lists"]["total_items"]
                    - framework["lists"]["total_items"],
                }
            )

        # Compare tables
        if manual["tables"]["total"] != framework["tables"]:
            issues.append(
                {
                    "type": "tables_count",
                    "manual": manual["tables"]["total"],
                    "framework": framework["tables"],
                    "difference": manual["tables"]["total"] - framework["tables"],
                }
            )

        # Compare task lists
        if manual["task_lists"]["total"] != framework["task_lists"]:
            issues.append(
                {
                    "type": "task_lists",
                    "manual": manual["task_lists"]["total"],
                    "framework": framework["task_lists"],
                    "difference": manual["task_lists"]["total"] - framework["task_lists"],
                }
            )

        return {"has_issues": len(issues) > 0, "issue_count": len(issues), "issues": issues}

    def validate_file(self, file_path: Path) -> dict[str, Any]:
        """Validate a single file for data loss."""
        if self.verbose:
            print(f"\n{'=' * 60}")
            print(f"Validating: {file_path.name}")
            print(f"Path: {file_path}")

        # Manual analysis
        manual = self.analyze_raw_markdown(file_path)

        # Framework processing
        framework_result = self.process_with_framework(file_path)

        if not framework_result["success"]:
            return {
                "file": file_path.name,
                "path": str(file_path),
                "error": framework_result["error"],
                "status": "error",
            }

        # Compare results
        comparison = self.compare_results(manual, framework_result["data"])

        result = {
            "file": file_path.name,
            "path": str(file_path),
            "size_bytes": manual["size_bytes"],
            "line_count": manual["line_count"],
            "status": "issues" if comparison["has_issues"] else "ok",
            "issue_count": comparison["issue_count"],
            "issues": comparison["issues"],
            "manual_analysis": manual,
            "framework_analysis": framework_result["data"],
        }

        if comparison["has_issues"]:
            self.files_with_issues += 1
            self.total_issues += comparison["issue_count"]

            if self.verbose:
                print(f"  ⚠️  Found {comparison['issue_count']} issues:")
                for issue in comparison["issues"]:
                    print(
                        f"    - {issue['type']}: manual={issue['manual']}, framework={issue['framework']}"
                    )
        elif self.verbose:
            print("  ✅ No data loss detected")

        return result

    def validate_all(self, directory: Path, limit: int | None = None) -> None:
        """Validate all markdown files in directory."""
        md_files = sorted(directory.glob("**/*.md"))

        if limit:
            md_files = md_files[:limit]

        print("\n🔍 Comprehensive Data Loss Validation")
        print(f"{'=' * 60}")
        print(f"Found {len(md_files)} markdown files to validate")

        start_time = time.time()

        for i, file_path in enumerate(md_files, 1):
            if not self.verbose:
                print(f"[{i}/{len(md_files)}] {file_path.name}...", end=" ")

            result = self.validate_file(file_path)
            self.results.append(result)

            if not self.verbose:
                if result["status"] == "error":
                    print(f"❌ Error: {result['error']}")
                elif result["status"] == "issues":
                    print(f"⚠️  {result['issue_count']} issues")
                else:
                    print("✅")

        elapsed = time.time() - start_time

        # Print summary
        print(f"\n{'=' * 60}")
        print("📊 VALIDATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total files validated: {len(self.results)}")
        print(f"Files with issues: {self.files_with_issues}")
        print(f"Total issues found: {self.total_issues}")
        print(f"Time taken: {elapsed:.2f}s")

        # Show breakdown by issue type
        if self.total_issues > 0:
            issue_types = {}
            for result in self.results:
                if result["status"] == "issues":
                    for issue in result["issues"]:
                        issue_type = issue["type"]
                        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

            print("\n📋 Issues by Type:")
            for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {issue_type}: {count}")

        # Save detailed report (convert Path objects to strings for JSON serialization)
        report_file = Path("data_loss_validation_report.json")

        # Convert all Path objects to strings recursively
        json_safe_results = make_json_serializable(self.results)

        with open(report_file, "w") as f:
            json.dump(
                {
                    "summary": {
                        "total_files": len(self.results),
                        "files_with_issues": self.files_with_issues,
                        "total_issues": self.total_issues,
                        "success_rate": f"{((len(self.results) - self.files_with_issues) / len(self.results)) * 100:.1f}%",
                        "time_taken": elapsed,
                    },
                    "files": json_safe_results,
                },
                f,
                indent=2,
            )

        print(f"\n📝 Detailed report saved to {report_file}")

        # Exit code based on results
        if self.files_with_issues > 0:
            print(f"\n⚠️  Data loss detected in {self.files_with_issues} files")
            sys.exit(1)
        else:
            print("\n✅ No data loss detected in any files!")
            sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive data loss validation for markdown files"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output for each file"
    )
    parser.add_argument(
        "--limit", "-l", type=int, help="Limit number of files to validate (for testing)"
    )
    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default="src/docpipe/loaders/test_mds",
        help="Directory to validate (default: src/docpipe/loaders/test_mds)",
    )

    args = parser.parse_args()

    # Create validator and run
    validator = ComprehensiveValidator(verbose=args.verbose)
    test_dir = Path(args.directory)

    if not test_dir.exists():
        print(f"❌ Directory not found: {test_dir}")
        sys.exit(1)

    validator.validate_all(test_dir, limit=args.limit)


if __name__ == "__main__":
    main()
