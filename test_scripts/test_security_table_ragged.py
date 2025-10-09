#!/usr/bin/env python3
"""
Security test for table ragged detection vulnerabilities.
Tests that tables with mismatched column counts are properly detected.
"""

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_table_ragged_security():
    """Test table ragged detection for data integrity."""

    print("🔒 Testing Table Ragged Detection Security")
    print("=" * 60)

    tests = []

    # Test 1: Clean table (not ragged)
    test1 = {
        "name": "Clean table",
        "content": """| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |""",
        "expected_ragged": False,
        "description": "Well-formed table with consistent columns",
    }
    tests.append(test1)

    # Test 2: Ragged table - missing cells
    test2 = {
        "name": "Ragged table - missing cells",
        "content": """| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   |
| Cell 4   | Cell 5   | Cell 6   | Extra    |""",
        "expected_ragged": True,
        "description": "Table with inconsistent column counts",
    }
    tests.append(test2)

    # Test 3: Ragged table - header/body mismatch
    test3 = {
        "name": "Ragged table - header/body mismatch",
        "content": """| Header 1 | Header 2 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |""",
        "expected_ragged": True,
        "description": "Separator has 3 columns but header has 2",
    }
    tests.append(test3)

    # Test 4: Table with escaped pipes (tricky case)
    test4 = {
        "name": "Table with escaped pipes",
        "content": """| Command | Description |
|---------|-------------|
| `a\\|b`  | Pipe symbol |
| `grep`  | Search tool |""",
        "expected_ragged": False,
        "description": "Escaped pipes should not affect column count",
    }
    tests.append(test4)

    # Test 5: Injection via ragged table
    test5 = {
        "name": "Injection via ragged table",
        "content": """| User | Role |
|------|------|
| admin | root |
| hacker | admin | DROP TABLE users; |""",
        "expected_ragged": True,
        "description": "Extra columns could contain malicious content",
    }
    tests.append(test5)

    # Test 6: Empty cells (valid)
    test6 = {
        "name": "Empty cells",
        "content": """| A | B | C |
|---|---|---|
|   |   |   |
| 1 |   | 3 |""",
        "expected_ragged": False,
        "description": "Empty cells are valid, not ragged",
    }
    tests.append(test6)

    # Test 7: Complex ragged case
    test7 = {
        "name": "Complex ragged case",
        "content": """| Col1 | Col2 | Col3 |
|------|------|
| A    | B    | C    | D    | E |
| F    |""",
        "expected_ragged": True,
        "description": "Multiple ragged issues in one table",
    }
    tests.append(test7)

    # Run tests
    passed = 0
    failed = 0

    for test in tests:
        parser = MarkdownParserCore(test["content"])
        result = parser.parse()

        tables = result.get("structure", {}).get("tables", [])

        print(f"\n📋 Test: {test['name']}")
        print(f"   Description: {test['description']}")
        print(f"   Expected ragged: {test['expected_ragged']}")

        if not tables:
            print("   ❌ No table found in content")
            failed += 1
            continue

        table = tables[0]

        # Check for raggedness using parser's detection
        is_ragged = table.get("is_ragged", False)

        print(f"   Detected ragged: {is_ragged}")

        if is_ragged == test["expected_ragged"]:
            print("   ✅ PASS")
            passed += 1
        else:
            print("   ❌ FAIL")
            # Debug info
            print(f"      Headers: {len(table.get('headers', []))} columns")
            print(f"      Rows: {[len(row) for row in table.get('rows', [])]}")
            failed += 1

    # Summary
    print(f"\n{'=' * 60}")
    print("🎯 Table Ragged Detection Results:")
    print(f"   ✅ Passed: {passed}/{len(tests)}")
    print(f"   ❌ Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🔒 SUCCESS: All table ragged vulnerabilities detected!")
        print("   ✅ Ragged tables properly identified")
        print("   ✅ Clean tables not falsely flagged")
        print("   ✅ Data integrity protected")
    else:
        print("\n⚠️ TABLE RAGGED DETECTION ISSUES REMAIN!")
        print("   Review failed tests above")

    return failed == 0


def detect_table_ragged(table: dict) -> bool:
    """
    Detect if a table has ragged (mismatched) column counts.

    A table is considered ragged if:
    - Header column count doesn't match body column counts
    - Different rows have different column counts
    """
    headers = table.get("headers", [])
    rows = table.get("rows", [])

    if not headers and not rows:
        return False  # Empty table, not ragged

    # Determine expected column count
    header_cols = len(headers) if headers else 0

    # If we have rows, check their consistency
    if rows:
        row_counts = [len(row) for row in rows]

        # Check if all rows have same count
        if len(set(row_counts)) > 1:
            return True  # Different row lengths = ragged

        # If headers exist, check if they match row count
        if headers and row_counts and header_cols != row_counts[0]:
            return True  # Header/body mismatch = ragged

    return False


if __name__ == "__main__":
    test_table_ragged_security()
