#!/usr/bin/env python3
"""
Test critical fixes for MarkdownParserCore.
Tests dependency management, security profile consistency, and error handling.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_security_profile_consistency():
    """Test that security profiles are consistently applied."""
    print("\n=== Testing Security Profile Consistency ===")

    from docpipe.loaders.markdown_parser_core import MarkdownParserCore

    # Test that schemes are consistent between validation and policy
    doc = """
[FTP Link](ftp://files.example.com/file.zip)
[Tel Link](tel:+1234567890)
[HTTP Link](http://example.com)
"""

    # Test strict profile
    parser = MarkdownParserCore(doc, security_profile="strict")
    result = parser.parse()

    # Check that allowed schemes are set correctly
    assert hasattr(parser, "_effective_allowed_schemes"), "Should have effective allowed schemes"

    # Verify links are validated according to profile
    links = result["structure"]["links"]
    for link in links:
        scheme = link.get("scheme")
        if scheme:
            allowed = link.get("allowed")
            expected_allowed = scheme in parser._effective_allowed_schemes
            assert allowed == expected_allowed, (
                f"Scheme {scheme} allowance mismatch: got {allowed}, expected {expected_allowed}"
            )

    print("   Strict profile: schemes validated consistently")

    # Test permissive profile
    parser_perm = MarkdownParserCore(doc, security_profile="permissive")
    result_perm = parser_perm.parse()

    links_perm = result_perm["structure"]["links"]
    # Permissive should allow ftp and tel
    ftp_link = next((l for l in links_perm if l.get("scheme") == "ftp"), None)
    tel_link = next((l for l in links_perm if l.get("scheme") == "tel"), None)

    assert ftp_link and ftp_link.get("allowed"), "Permissive should allow FTP"
    assert tel_link and tel_link.get("allowed"), "Permissive should allow Tel"

    print("   Permissive profile: schemes validated consistently")


def test_missing_yaml_handling():
    """Test graceful handling when PyYAML is not installed."""
    print("\n=== Testing Missing YAML Handling ===")

    # Temporarily mock missing YAML
    import docpipe.loaders.markdown_parser_core as mdcore

    # Save original state
    original_has_yaml = mdcore.HAS_YAML
    original_yaml = mdcore.yaml

    try:
        # Simulate missing YAML
        mdcore.HAS_YAML = False
        mdcore.yaml = None

        from docpipe.loaders.markdown_parser_core import MarkdownParserCore

        doc = """---
title: Test Document
author: Test Author
---

# Content

This is the main content."""

        parser = MarkdownParserCore(doc)
        result = parser.parse()

        # Should parse without crashing
        assert result is not None, "Should parse even without YAML"

        # Check for appropriate error
        assert parser.frontmatter is None, "Should not parse frontmatter without YAML"
        assert hasattr(parser, "frontmatter_error"), "Should have frontmatter error"
        assert "yaml_library_not_available" in parser.frontmatter_error, (
            f"Should indicate YAML not available, got: {parser.frontmatter_error}"
        )

        # Content should be intact
        assert "# Content" in result["content"]["raw"], "Content should be preserved"

        print("   Handles missing YAML library gracefully")

    finally:
        # Restore original state
        mdcore.HAS_YAML = original_has_yaml
        mdcore.yaml = original_yaml


def test_plugin_validation():
    """Test that plugin validation works correctly."""
    print("\n=== Testing Plugin Validation ===")

    from docpipe.loaders.markdown_parser_core import MarkdownParserCore

    # Request mix of valid and invalid plugins
    config = {
        "plugins": ["table", "strikethrough", "invalid_plugin"],
        "external_plugins": ["footnote", "tasklists", "fake_plugin"],
    }

    parser = MarkdownParserCore("# Test", config=config)

    # Check what was actually enabled
    assert hasattr(parser, "enabled_plugins"), "Should track enabled plugins"
    assert hasattr(parser, "unavailable_plugins"), "Should track unavailable plugins"

    # Table and strikethrough should be enabled (built-in)
    assert "table" in parser.enabled_plugins, "Table should be enabled"
    assert "strikethrough" in parser.enabled_plugins, "Strikethrough should be enabled"

    # Invalid plugins should be tracked
    assert "invalid_plugin" in parser.unavailable_plugins, "Should track invalid built-in plugin"
    assert "fake_plugin" in parser.unavailable_plugins, "Should track invalid external plugin"

    print(f"   Enabled plugins: {parser.enabled_plugins}")
    print(f"   Unavailable plugins: {parser.unavailable_plugins}")


def test_available_features():
    """Test feature detection."""
    print("\n=== Testing Feature Detection ===")

    from docpipe.loaders.markdown_parser_core import MarkdownParserCore

    features = MarkdownParserCore.get_available_features()

    assert isinstance(features, dict), "Should return feature dict"

    # Check expected keys
    expected_keys = {"bleach", "yaml", "footnotes", "tasklists", "content_context"}
    assert expected_keys.issubset(features.keys()), (
        f"Missing expected feature keys. Got: {features.keys()}"
    )

    # All values should be boolean
    for key, value in features.items():
        assert isinstance(value, bool), f"Feature {key} should be boolean, got {type(value)}"

    print("  Available features:")
    for feature, available in features.items():
        status = "" if available else ""
        print(f"    {status} {feature}")


def test_yaml_error_handling():
    """Test proper YAML error handling with detailed messages."""
    print("\n=== Testing YAML Error Handling ===")

    import docpipe.loaders.markdown_parser_core as mdcore
    from docpipe.loaders.markdown_parser_core import MarkdownParserCore

    # Only test if YAML is available
    if not mdcore.HAS_YAML:
        print("  �  YAML not available, skipping error handling test")
        return

    # Test malformed YAML
    doc_bad_yaml = """---
title: Test
invalid_yaml: [unclosed
---

# Content"""

    parser = MarkdownParserCore(doc_bad_yaml)
    result = parser.parse()

    # Should handle the error gracefully
    assert result is not None, "Should parse even with bad YAML"
    assert parser.frontmatter is None, "Should not parse bad YAML"

    if hasattr(parser, "frontmatter_error"):
        assert "yaml_parse_error" in parser.frontmatter_error, (
            f"Should indicate YAML parse error, got: {parser.frontmatter_error}"
        )
        print(f"   YAML error captured: {parser.frontmatter_error[:50]}...")

    # Test unterminated frontmatter
    doc_unterminated = """---
title: Test
.
# Content"""

    parser2 = MarkdownParserCore(doc_unterminated)
    result2 = parser2.parse()

    assert hasattr(parser2, "frontmatter_error"), "Should detect unterminated frontmatter"
    assert "unterminated" in parser2.frontmatter_error, (
        f"Should indicate unterminated, got: {parser2.frontmatter_error}"
    )

    print("   Unterminated frontmatter detected")


if __name__ == "__main__":
    print("=' Critical Fixes Test Suite")
    print("=" * 50)

    test_security_profile_consistency()
    test_missing_yaml_handling()
    test_plugin_validation()
    test_available_features()
    test_yaml_error_handling()

    print("\n" + "=" * 50)
    print(" All critical fixes tested successfully!")
