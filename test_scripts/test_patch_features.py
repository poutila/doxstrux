#!/usr/bin/env python3
"""Test features from the patch files."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_scheme_policy_tel_and_stamp():
    """Test from test_scheme_policy.py"""
    doc = "Call [me](tel:+123) [web](https://e.x) [mail](mailto:a@b) [bad](javascript:alert(1))"
    p = MarkdownParserCore(doc, config={"security_profile": "strict"}).parse()
    links = p["structure"]["links"]
    tel = [l for l in links if l.get("scheme") == "tel"]
    assert tel and all(l.get("allowed") is True for l in tel), "Tel links should be allowed"
    sec = p["metadata"]["security"]
    assert sec["profile_used"] in ["strict", "moderate"], (
        f"Profile should be strict/moderate, got {sec['profile_used']}"
    )
    assert "tel" in sec["statistics"]["allowed_schemes"], "Tel should be in allowed_schemes"
    print("✅ Scheme policy test passed")


def test_frontmatter_bof_only_and_dots_not_allowed():
    """Test from test_frontmatter_bof_only.py"""
    # 1 blank line + BOM tolerated
    doc1 = "\ufeff\n---\nkey: v\n---\nBody"
    p1 = MarkdownParserCore(doc1).parse()
    assert p1["metadata"]["has_frontmatter"] is True, "BOM + blank + frontmatter should work"

    # mid-file fence must not be frontmatter
    doc2 = "Title\n\n---\nkey: v\n---\nBody"
    p2 = MarkdownParserCore(doc2).parse()
    assert p2["metadata"]["has_frontmatter"] is False, "Mid-file frontmatter should not be parsed"

    # dot closer not allowed
    doc3 = "---\nkey: v\n.\nBody"
    p3 = MarkdownParserCore(doc3).parse()
    assert p3["metadata"].get("frontmatter_error") == "unterminated", (
        "Single dot should cause unterminated error"
    )
    print("✅ Frontmatter BOF test passed")


def test_table_heuristics_and_summary():
    """Test from test_table_heuristics_flags.py"""
    doc = """| a | b |
|:--|--:|
| 1 |
| 2 | 3 |
"""
    parsed = MarkdownParserCore(doc).parse()
    tables = parsed["structure"]["tables"]
    assert (
        tables and "align_meta" in tables[0] and tables[0]["align_meta"].get("heuristic") is True
    ), "Should have align_meta heuristic"
    assert "is_ragged_meta" in tables[0] and tables[0]["is_ragged_meta"].get("heuristic") is True, (
        "Should have is_ragged_meta heuristic"
    )
    assert parsed["metadata"]["security"]["summary"]["ragged_tables_count"] >= 1, (
        "Should count ragged tables in summary"
    )
    print("✅ Table heuristics test passed")


def test_tel_link_classification():
    """Test from test_link_tel_scheme.py"""
    doc = "Call me: [phone](tel:+123456) and [site](https://ex.com) and [mail](mailto:a@b)"
    p = MarkdownParserCore(doc, config={}).parse()
    links = p["structure"]["links"]
    tel = next(
        (l for l in links if (l.get("scheme") == "tel") or l.get("url", "").startswith("tel:")),
        None,
    )
    assert tel is not None, "Should find tel link"
    assert tel.get("allowed") is True, "Tel link should be allowed"
    assert tel.get("type") in ("phone", "custom", "external"), (
        f"Tel link type should be phone/custom/external, got {tel.get('type')}"
    )
    print("✅ Tel link classification test passed")


def test_char_offsets_presence_and_order():
    """Test from test_char_offsets_skeleton.py"""
    doc = "# Title\n\nPara line.\n\n## Sub\ntext"
    p = MarkdownParserCore(doc, config={}).parse()
    parsed = p
    heads = parsed["structure"]["headings"]
    assert heads, "no headings parsed"
    for h in heads:
        assert "start_char" in h and "end_char" in h, "Headings should have char offsets"
        if h["start_char"] is not None and h["end_char"] is not None:
            assert h["start_char"] <= h["end_char"], "Start char should be <= end char"
    for s in parsed["structure"]["sections"]:
        assert "start_char" in s and "end_char" in s, "Sections should have char offsets"
        if s["start_char"] is not None and s["end_char"] is not None:
            assert s["start_char"] <= s["end_char"], "Start char should be <= end char"
    print("✅ Character offsets test passed")


if __name__ == "__main__":
    test_scheme_policy_tel_and_stamp()
    test_frontmatter_bof_only_and_dots_not_allowed()
    test_table_heuristics_and_summary()
    test_tel_link_classification()
    test_char_offsets_presence_and_order()

    print("\n✅ All patch feature tests passed!")
