
import json
import argparse
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux import parse_markdown_file
from doxstrux.markdown.exceptions import MarkdownSecurityError, MarkdownSizeError

def update_snapshots(test_dir: Path):
    """
    Iterate through all .md files in test_dir (recursive).
    Parse them with configuration mimicking legacy expectation (allows_html=True, profile=moderate).
    Overwrite the corresponding .json file with the FULL parser output.
    """
    if not test_dir.exists():
        print(f"Error: Directory {test_dir} not found.")
        sys.exit(1)

    pairs = []
    # Find all .md files and check for corresponding .json
    for md_file in test_dir.rglob("*.md"):
        json_file = md_file.with_suffix(".json")
        if json_file.exists():
            pairs.append((md_file, json_file))

    print(f"Found {len(pairs)} test pairs to update.")
    
    updated_count = 0
    error_count = 0

    for md_file, json_file in pairs:
        try:
            # Parse with Moderate Profile + HTML Allowed (Legacy Standard)
            # This ensures we don't break existing tests that relied on HTML parsing
            result = parse_markdown_file(
                md_file, 
                security_profile="moderate",
                config={"allows_html": True}
            )
            
            # Write full snapshot
            import datetime
            
            class DateEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, (datetime.date, datetime.datetime)):
                        return obj.isoformat()
                    return super().default(obj)

            with open(json_file, "w") as f:
                json.dump(result, f, indent=2, cls=DateEncoder)
            
            updated_count += 1
            print(f"Updated: {json_file.name}")
            
        except Exception as e:
            print(f"FAILED: {md_file.name} - {e}")
            error_count += 1
            # If parsing fails (e.g. security block), we can't generate a "clean" snapshot easily 
            # unless we catch the error and dump the exception state.
            # Doxstrux raises exceptions for blocking.
            
            # Handle Security Blocking as valid output state? 
            # If the parser raises MarkdownSecurityError, we should dump that state?
            if isinstance(e, (MarkdownSecurityError, MarkdownSizeError)):
                 # Construct valid error snapshot
                 error_snapshot = {
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
                 with open(json_file, "w") as f:
                    json.dump(error_snapshot, f, indent=2)
                 updated_count += 1
                 print(f"Updated (Security Blocked): {json_file.name}")

    print("-" * 40)
    print(f"Total Updated: {updated_count}")
    print(f"Errors: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update test snapshots to full parser output.")
    parser.add_argument("test_dir", type=Path, help="Directory containing .md/.json pairs")
    args = parser.parse_args()
    
    update_snapshots(args.test_dir)
