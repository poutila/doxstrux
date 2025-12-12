#!/usr/bin/env python3
"""Test the refactored package."""

import sys
from pathlib import Path

from doxstrux.markdown_parser_core import MarkdownParserCore

from doxstrux.md_parser_testing.json_utils import write_json_file

# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print(f"\nsys.path: {sys.path}")
print(f"\n__name__: {__name__}")
print(f"\n__package__: {__package__}\n")


def test_imports():
    """Test basic imports."""
    try:
        from doxstrux.markdown_parser_core import MarkdownParserCore

        print("✅ Main import works")
    except ImportError as e:
        print(f"❌ Main import failed: {e}")
        return False

    return True

def mass_test_parser():
    """Test mass parser usage."""
    test_files = (Path(__file__).parent / "math_valid_set").rglob("*.md")
    counter = 0
    for md_file in test_files:
        # counter += 1
        # content = md_file.read_text(encoding="utf-8")
        # print(f"{counter}: {md_file.name}...")
        # # Here you would call your parser and check the output
        # # For example:
        # parser = MarkdownParserCore(content, config=config, security_profile='moderate')
        # result = parser.parse()
        # print(result)
        print(f"Testing {md_file}...")
         # Here you would call your parser and check the output
         # For example:
        test_basic_usage(md_file)

def test_basic_usage(path: Path = None):
    """Test basic parser usage."""

    # content = "# Test\n\nHello world!"
    # content = (Path(__file__).parent / "CLAUDEorig.md").read_text(encoding="utf-8")
    content = path.read_text(encoding="utf-8")
    config = {
    'allows_html': True,
    'plugins': ['table', 'strikethrough', 'tasklists','math'],
    'preset': 'gfm-like'}
    parser = MarkdownParserCore(content, config=config, security_profile='moderate')
    try:
        json_path = Path(path.parent) / path.stem / ".json"
        print(json_path)
        # print(parser.get_available_features())
        write_json_file(json_path, parser.parse(), compact=False)
        return True
    except Exception as e:
        print(f"❌ Parser failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing refactored package...")

    success = True
    success &= test_imports()
    # success &= test_basic_usage()
    mass_test_parser(

    )

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed.")
