#!/usr/bin/env python3
"""Debug baseline differences."""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

test_file = "tools/test_mds/01_edge_cases/tasks_01.md"
baseline_file = "tools/baseline_outputs/01_edge_cases/tasks_01.baseline.json"

# Read content
with open(test_file, "r") as f:
    content = f.read()

# Parse with current parser
from src.doxstrux.markdown_parser_core import MarkdownParserCore
parser = MarkdownParserCore(content)
result = parser.parse()

# Read baseline
with open(baseline_file, "r") as f:
    baseline = json.load(f)

# Compare structure deeply
def compare_dicts(d1, d2, path=""):
    diffs = []
    all_keys = set(d1.keys()) | set(d2.keys())
    for key in sorted(all_keys):
        new_path = f"{path}.{key}" if path else key
        if key not in d1:
            diffs.append(f"Missing in current: {new_path}")
        elif key not in d2:
            diffs.append(f"Missing in baseline: {new_path}")
        elif type(d1[key]) != type(d2[key]):
            diffs.append(f"Type mismatch at {new_path}: {type(d1[key])} vs {type(d2[key])}")
        elif isinstance(d1[key], dict):
            diffs.extend(compare_dicts(d1[key], d2[key], new_path))
        elif isinstance(d1[key], list):
            if len(d1[key]) != len(d2[key]):
                diffs.append(f"List length mismatch at {new_path}: {len(d1[key])} vs {len(d2[key])}")
                # Show first few items
                print(f"\nCurrent {new_path} ({len(d1[key])} items):", d1[key][:3] if len(d1[key]) > 0 else "[]")
                print(f"Baseline {new_path} ({len(d2[key])} items):", d2[key][:3] if len(d2[key]) > 0 else "[]")
        elif d1[key] != d2[key]:
            diffs.append(f"Value mismatch at {new_path}: {repr(d1[key])[:100]} vs {repr(d2[key])[:100]}")
    return diffs

print("=== Comparing structure ===")
diffs = compare_dicts(result["structure"], baseline["structure"])
for diff in diffs[:30]:
    print(diff)

if not diffs:
    print("No differences found in structure!")

    # Check lists specifically
    print("\n=== Checking lists ===")
    if "lists" in result["structure"] and "lists" in baseline["structure"]:
        result_lists = result["structure"]["lists"]
        baseline_lists = baseline["structure"]["lists"]

        print(f"Result lists: {len(result_lists)}")
        print(f"Baseline lists: {len(baseline_lists)}")

        if result_lists and baseline_lists:
            print("\nResult list[0] keys:", list(result_lists[0].keys()))
            print("Baseline list[0] keys:", list(baseline_lists[0].keys()))

            if result_lists[0].get("items") and baseline_lists[0].get("items"):
                print("\nResult list[0] item[0] keys:", list(result_lists[0]["items"][0].keys()))
                print("Baseline list[0] item[0] keys:", list(baseline_lists[0]["items"][0].keys()))

                print("\nResult list[0] item[0]:")
                print(json.dumps(result_lists[0]["items"][0], indent=2)[:500])
                print("\nBaseline list[0] item[0]:")
                print(json.dumps(baseline_lists[0]["items"][0], indent=2)[:500])

    # Check tasklists specifically
    print("\n=== Checking tasklists ===")
    if "tasklists" in result["structure"] and "tasklists" in baseline["structure"]:
        result_tasklists = result["structure"]["tasklists"]
        baseline_tasklists = baseline["structure"]["tasklists"]

        print(f"Result tasklists: {len(result_tasklists)}")
        print(f"Baseline tasklists: {len(baseline_tasklists)}")

        if result_tasklists and baseline_tasklists:
            print("\nResult tasklist[0] keys:", list(result_tasklists[0].keys()))
            print("Baseline tasklist[0] keys:", list(baseline_tasklists[0].keys()))

            if result_tasklists[0].get("items") and baseline_tasklists[0].get("items"):
                print("\nResult tasklist[0] item[0] keys:", list(result_tasklists[0]["items"][0].keys()))
                print("Baseline tasklist[0] item[0] keys:", list(baseline_tasklists[0]["items"][0].keys()))

                print("\nResult tasklist[0] item[0]:")
                print(json.dumps(result_tasklists[0]["items"][0], indent=2)[:500])
                print("\nBaseline tasklist[0] item[0]:")
                print(json.dumps(baseline_tasklists[0]["items"][0], indent=2)[:500])
