
import json
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux import parse_markdown_file
from doxstrux.markdown.exceptions import MarkdownSecurityError, MarkdownSizeError

def deep_compare(actual, expected, path="root"):
    """
    Recursively compare actual vs expected JSON.
    Returns list of mismatch strings.
    """
    failures = []
    
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
             return [f"{path}: Expected dict, got {type(actual).__name__}"]
             
        for k, v in expected.items():
            if k not in actual:
                 failures.append(f"{path}: Missing key '{k}'")
                 continue
            failures.extend(deep_compare(actual[k], v, f"{path}.{k}"))
            
    elif isinstance(expected, list):
        if not isinstance(actual, list):
             return [f"{path}: Expected list, got {type(actual).__name__}"]
             
        if len(expected) != len(actual):
             failures.append(f"{path}: Length mismatch (expected {len(expected)}, got {len(actual)})")
        
        # Zip compare up to min length
        for i, (exp_item, act_item) in enumerate(zip(expected, actual)):
             failures.extend(deep_compare(act_item, exp_item, f"{path}[{i}]"))
             
    else:
        if actual != expected:
             failures.append(f"{path}: Expected {expected!r}, got {actual!r}")
             
    return failures

def run_test_pair(md_file: Path, json_file: Path) -> tuple[bool, list[str]]:
    """
    Run a single test pair.
    """
    try:
        with open(json_file, "r") as f:
            snapshot = json.load(f)
    except Exception as e:
        return False, [f"Failed to load JSON: {e}"]
        
    # Check if this is a "valid" snapshot (must have metadata etc)
    # If using update_snapshots.py, it should be full output.
    
    # Determine Profile from Snapshot if present, else Default
    profile = "strict"
    # Legacy tests were updated with moderate + allows_html configuration.
    # While exact output is baked in, the parser configuration MATTERS for reproducing it.
    # We should detect if this test was generated with 'moderate'.
    # Our update_snapshots.py didn't explicitly save the config used to generate it 
    # BUT the output 'metadata.security.profile_used' might contain it if the parser saves it?
    # Current parser output schema: metadata.security does NOT seem to save profile name by default?
    # Wait, 'profile_used' key was proposed but relies on parser implementation.
    
    # Heuristic: The snapshots we Just generated used 'moderate'.
    # The 'additional_test_mds' (Claue tests) used 'strict'.
    # If we use strict for legacy tests (e.g. html_01.md), result will differ (HTML blocked).
    # We need to infer configuration or standardize.
    
    # If we assume ALL legacy tests in 'tools/test_mds' are Moderate+HTML, and 'tools/additional_test_mds' are Strict.
    # We can use file path?
    
    config = {}
    if "tools/test_mds" in str(md_file):
        profile = "moderate"
        config = {"allows_html": True}
    
    result = {}
    
    try:
        result = parse_markdown_file(
            md_file, 
            security_profile=profile,
            config=config
        )
    except (MarkdownSecurityError, MarkdownSizeError) as e:
        # If snapshot EXPECTED this error, it should be in there.
        # Construct error result format to match snapshot
        result = {
            "metadata": {
                "security": {
                    "embedding_blocked": True,
                    "warnings": [{"type": "security_error", "message": str(e)}],
                    "statistics": {}
                }
            },
            "exception_was_raised": True,
            "error_message": str(e),
            "structure": {},
            "content": {"raw": "", "lines": []}
         }
         
    # Serialize and Deserialize to normalize types (e.g. datetime -> str, tuples -> lists)
    # This matches what is stored in the JSON snapshot.
    import datetime
    
    class DateEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            return super().default(obj)
            
    try:
        json_str = json.dumps(result, cls=DateEncoder)
        result = json.loads(json_str)
    except Exception as e:
        return False, [f"Failed to normalize result JSON: {e}"]

    # Normalization for non-deterministic fields
    def normalize_structure(data):
        if isinstance(data, dict):
             # Sort tag_hints if present
             if "tag_hints" in data and isinstance(data["tag_hints"], list):
                 data["tag_hints"].sort()
             for k, v in data.items():
                 normalize_structure(v)
        elif isinstance(data, list):
             for item in data:
                 normalize_structure(item)
                 
    normalize_structure(result)
    normalize_structure(snapshot)

    # Compare
    # Note: Snapshot usually contains EXACTLY what parse_markdown_file returns.
    failures = deep_compare(result, snapshot)
    
    return len(failures) == 0, failures

def run_all_tests(test_dir: Path) -> dict:
    pairs = []
    # Recursively find .md files with sibling .json
    for md_file in test_dir.rglob("*.md"):
        if "node_modules" in str(md_file): continue
        json_path = md_file.with_suffix(".json")
        if json_path.exists():
            pairs.append((md_file, json_path))
            
    print(f"Found {len(pairs)} test pairs in {test_dir}")
    print("-" * 60)
    
    stats = {
        "total": len(pairs),
        "passed": 0,
        "failed": 0,
        "failures": []
    }
    
    for i, (md, json_path) in enumerate(pairs, 1):
        print(f"[{i}/{len(pairs)}] {md.name}...", end=" ", flush=True)
        passed, errors = run_test_pair(md, json_path)
        
        if passed:
            print("✅")
            stats["passed"] += 1
        else:
            print("❌")
            stats["failed"] += 1
            if len(errors) > 5:
                errors = errors[:5] + [f"... and {len(errors)-5} more"]
            stats["failures"].append({
                "file": md.name,
                "errors": errors
            })
            
    return stats


def main():
    parser = argparse.ArgumentParser(description="Run security regression tests (Snapshot Mode)")
    parser.add_argument("test_dir", type=Path, nargs="?", 
                      default=Path("tools/test_mds"),
                      help="Directory containing .md/.json test pairs")
    
    args = parser.parse_args()
    
    if not args.test_dir.exists():
        print(f"Error: Directory {args.test_dir} not found.")
        sys.exit(1)
        
    stats = run_all_tests(args.test_dir)
    
    print("-" * 60)
    print(f"Total: {stats['total']}, Passed: {stats['passed']}, Failed: {stats['failed']}")
    
    if stats["failures"]:
        print("\nFailures:")
        for f in stats["failures"]:
            print(f"\n{f['file']}:")
            for err in f["errors"]:
                print(f"  - {err}")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
