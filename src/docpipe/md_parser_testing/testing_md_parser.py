#!/usr/bin/env python3
"""Test the refactored package."""

import sys
from pathlib import Path

from docpipe.markdown_parser_core import MarkdownParserCore

from json_utils import write_json_file

# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print(f"\nsys.path: {sys.path}")
print(f"\n__name__: {__name__}")
print(f"\n__package__: {__package__}\n")


def test_imports():
    """Test basic imports."""
    try:
        from docpipe.markdown_parser_core import MarkdownParserCore

        print("✅ Main import works")
    except ImportError as e:
        print(f"❌ Main import failed: {e}")
        return False

    return True


def test_basic_usage():
    """Test basic parser usage."""

    # content = "# Test\n\nHello world!"
    content = (Path(__file__).parent / "CLAUDEorig.md").read_text(encoding="utf-8")
    config = {
    'allows_html': True,
    'plugins': ['table', 'strikethrough', 'tasklists'],
    'preset': 'gfm-like'}
    parser = MarkdownParserCore(content, config=config, security_profile='moderate')
    try:
        json_path = Path(__file__).parent / "test_output.json"
        # print(parser.parse())
        print(parser.get_available_features())
        write_json_file(json_path, parser.parse())
        return True
    except Exception as e:
        print(f"❌ Parser failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing refactored package...")

    success = True
    success &= test_imports()
    success &= test_basic_usage()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed.")
