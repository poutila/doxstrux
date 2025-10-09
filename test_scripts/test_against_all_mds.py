#!/usr/bin/env python3
"""Test MarkdownParserCore against JSON ground truth files."""

import json
import sys
from pathlib import Path

# Import parser directly, avoiding the problematic __init__.py
sys.path.insert(0, str(Path(__file__).parent))
from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def main():
    """Run tests against all markdown/JSON pairs."""

    # Setup test directory
    test_dir = Path("src/docpipe/loaders/test_mds/md_stress_mega")
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        sys.exit(1)

    # Find test pairs
    pairs = []
    for md_file in sorted(test_dir.glob("*.md")):
        json_file = md_file.with_suffix(".json")
        if json_file.exists():
            pairs.append((md_file, json_file))

    print(f"Found {len(pairs)} test pairs")
    print("=" * 70)

    passed = 0
    failed = 0

    for i, (md_file, json_file) in enumerate(pairs, 1):
        # Progress
        if i % 50 == 0:
            print(f"Progress: {i}/{len(pairs)}")

        try:
            # Load expected counts
            with open(json_file) as f:
                expected = json.load(f).get("feature_counts", {})

            # Parse markdown
            content = md_file.read_text()
            parser = MarkdownParserCore(content)
            result = parser.parse()

            # Extract actual counts (simplified)
            structure = result.get("structure", {})
            actual = {
                "headings": len(structure.get("headings", [])),
                "blockquotes": len(structure.get("blockquotes", [])),
                "tables": len(structure.get("tables", [])),
                "links": len([l for l in structure.get("links", []) if l.get("type") != "image"]),
                "images": len(structure.get("images", [])),
                "code_fences": len(
                    [c for c in structure.get("code_blocks", []) if c.get("type") == "fenced"]
                ),
                "footnotes": len(structure.get("footnotes", {}).get("definitions", [])),
            }

            # Compare (only critical features)
            critical_features = ["headings", "tables", "code_fences"]
            mismatches = []
            for feature in critical_features:
                if feature in expected:
                    if expected[feature] != actual.get(feature, 0):
                        mismatches.append(
                            f"{feature}: expected {expected[feature]}, got {actual.get(feature, 0)}"
                        )

            if not mismatches:
                passed += 1
            else:
                failed += 1
                if failed <= 3:  # Show first 3 failures
                    print(f"❌ {md_file.name}: {mismatches[0]}")

        except Exception as e:
            failed += 1
            if failed <= 3:
                print(f"❌ {md_file.name}: {str(e)[:100]}")

    # Results
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{len(pairs)} passed")
    if passed == len(pairs):
        print("✅ All tests passed")
    else:
        print(f"❌ {failed} tests failed")

    sys.exit(0 if passed == len(pairs) else 1)


if __name__ == "__main__":
    main()
