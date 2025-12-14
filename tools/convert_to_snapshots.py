#!/usr/bin/env python3
"""
Convert existing test JSON specs to full Parser Output Snapshots.
"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux import parse_markdown_file
from doxstrux.markdown.exceptions import MarkdownSecurityError, MarkdownSizeError

def get_compliant_result(md_file: Path, profile: str = "strict") -> dict:
    try:
        # Run parser
        result = parse_markdown_file(str(md_file), security_profile=profile)
        # Ensure 'content' exists (parser usually returns it, but let's be safe)
        if "content" not in result:
             result["content"] = {"raw": "", "lines": []}
        return result
        
    except (MarkdownSecurityError, MarkdownSizeError) as e:
        # Synthesize compliant result for blocked content
        msg = str(e)
        return {
            "metadata": {
                "security": {
                    "embedding_blocked": True,
                    "warnings": [{"type": "security_error", "message": msg}],
                    "statistics": {} # Empty stats if blocked early
                }
            },
            "content": {"raw": "", "lines": []}, # Required by schema
            "structure": {}, # Required by schema (empty)
            "mappings": {}, # Required by schema (empty)
            "exception_was_raised": True,
            "error_message": msg
        }
    except Exception as e:
        print(f"Error parsing {md_file}: {e}")
        return {}

from datetime import date, datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def convert_folder(target_dir: Path):
    files = sorted(target_dir.rglob("*.md"))
    print(f"Converting {len(files)} tests in {target_dir} to snapshots...")
    
    for md_file in files:
        json_file = md_file.with_suffix(".json")
        
        # Determine profile (heuristic matching run_security_tests logic)
        profile = "strict" 
        # Attempt to detect profile preference from existing json if matched
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    existing = json.load(f)
                    if "security_profile" in existing:
                        profile = existing["security_profile"]
                    elif "expected" in existing:
                        profile = "moderate" # Legacy default
            except:
                pass

        result = get_compliant_result(md_file, profile)
        
        if result:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=json_serial)
            # print(f"Updated {json_file.name}")

if __name__ == "__main__":
    target_dir = Path("tools/additional_test_mds")
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
        
    convert_folder(target_dir)
