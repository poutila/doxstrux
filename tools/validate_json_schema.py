#!/usr/bin/env python3
"""
Validate JSON files against the Parser Output Schema.
"""
import argparse
import json
import sys
from pathlib import Path
try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("Error: jsonschema library not found. Please install it (e.g. 'pip install jsonschema').")
    sys.exit(1)

def validate_files(schema_path: Path, target_dir: Path):
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        sys.exit(1)
        
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
        
    files = sorted(target_dir.rglob("*.json"))
    print(f"Validating {len(files)} files in {target_dir} against schema...")
    
    passed = 0
    failures = []
    
    for json_file in files:
        # Skip unrelated JSONs if any (e.g. VSCode configs? No, strictly in target_dir)
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            validate(instance=data, schema=schema)
            passed += 1
            # print(f"✅ {json_file.name}")
            
        except ValidationError as e:
            failures.append((json_file.name, e.message))
            # print(f"❌ {json_file.name}: {e.message}")
        except Exception as e:
            failures.append((json_file.name, f"Error: {e}"))
            
    print(f"\nSummary: {passed}/{len(files)} passed.")
    if failures:
        print("\nFailures:")
        for name, err in failures[:20]: # Show first 20 failure reasons
            print(f"❌ {name}: {err[:100]}...") # Truncate error
        if len(failures) > 20:
            print(f"... and {len(failures) - 20} more.")
            
    return len(failures) == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, default=Path("schemas/parser_output.schema.json"))
    parser.add_argument("--dir", type=Path, default=Path("tools/additional_test_mds"))
    args = parser.parse_args()
    
    success = validate_files(args.schema, args.dir)
    sys.exit(0 if success else 1)
