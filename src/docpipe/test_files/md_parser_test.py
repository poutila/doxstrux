#!/usr/bin/env python3
"""Test the refactored package."""

import sys
from json import loads
from pathlib import Path

from docpipe.loaders.markdown_parser_core import MarkdownParserCore

from .json_utils import write_json_file

# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print(f"\nsys.path: {sys.path}")
print(f"\n__name__: {__name__}")
print(f"\n__package__: {__package__}\n")
def split_claude_gen_test_file():
    """Split the CLAUDE generation test file into smaller parts."""
    content = (Path(__file__).parent / "claude_generated_tests.txt").read_text(encoding="utf-8")
    parts = [x.strip() for x in content.split("============================================================\n")]
    for i, part in enumerate(parts):
        print(f"\n-- Part {i + 1} --")
        # print(f"Part {i + 1}:\n{part[:250]}")
        item_counter = 0
        for item in part.split("=== ")[1:]:
            item_counter += 1
            rows = [x.strip() for x in item.split("\n")]
            file_name = rows[0].split(" ")[0].strip()
            # print(file_name)
            Path.mkdir(Path(__file__).parent / "claude tests/", exist_ok=True)
            out_file = Path(__file__).parent / ("claude tests/" + str(file_name))
            if ".json" in file_name:
                json = loads("\n".join(rows[1:]))
                print(f"JSON item: {json}")
                write_json_file(out_file, json, compact=False)
            elif ".md" in file_name:
                out_file.write_text("\n".join(rows[1:]), encoding="utf-8")
                print(f"Markdown item: {rows[1:]}")
            print(f"Item {item_counter}: {item[:50]}")
        print("-- end --\n")
        # print(part.split("=== "))
        # part_path = Path(__file__).parent / f"claude_generated_test_part_{i + 1}.md"
        # part_path.write_text(part, encoding="utf-8")

def mass_test_parser():
    """Test mass parser usage."""
    test_files = (Path(__file__).parent / "test_mds").rglob("*.md")
    counter = 0
    for md_file in test_files:
        counter += 1
        content = md_file.read_text(encoding="utf-8")
        print(f"{counter}: {md_file.name}...")
        # Here you would call your parser and check the output
        # For example:
        # parser = MarkdownParserCore(content, config=config, security_profile='moderate')
        # result = parser.parse()
        # print(result)

def test_basic_usage():
    """Test basic parser usage."""

    # content = "# Test\n\nHello world!"
    content = Path("CLAUDEorig.md").read_text(encoding="utf-8")
    config = {
    'allows_html': True,
    'plugins': ['table', 'strikethrough'],
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
    # mass_test_parser()
    split_claude_gen_test_file()
