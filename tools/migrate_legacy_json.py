import json
from pathlib import Path

def migrate_file(json_path: Path):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {json_path}: {e}")
        return

    if "expected" not in data:
        # Already migrated or different format
        return

    expected = data["expected"]
    
    # sparse snapshot structure
    # We RETAIN existing keys (expected, category) to allow legacy runner logic to work
    # while adding 'metadata' to satisfy new schema compliance (partially).
    
    snapshot = data.copy()
    if "metadata" not in snapshot:
         snapshot["metadata"] = {
            "security": {
                "statistics": {},
                "warnings": [],
                "embedding_blocked": False
            }
        }
    
    stats = snapshot["metadata"]["security"]["statistics"]

    # Mappings
    if "ragged" in expected:
        stats["ragged_tables_count"] = 1 if expected["ragged"] else 0
        
    if "align_mismatch" in expected:
        stats["table_align_mismatches"] = 1 if expected["align_mismatch"] else 0
        
    if "confusables_present" in expected:
        stats["confusables_present"] = expected["confusables_present"]
        
    if "expected_security_blocked" in data:
        snapshot["metadata"]["security"]["embedding_blocked"] = data["expected_security_blocked"]
        
    if "expected_warnings" in data:
        # Transform list of strings to list of objects with 'type' matching string
        snapshot["metadata"]["security"]["warnings"] = [{"type": w} for w in data["expected_warnings"]]

    # Write sparse snapshot containing BOTH legacy and new structure
    with open(json_path, 'w') as f:
        json.dump(snapshot, f, indent=2)
    print(f"Migrated {json_path}")

def main():
    root = Path("tools/test_mds")
    for f in root.rglob("*.json"):
        migrate_file(f)

if __name__ == "__main__":
    main()
