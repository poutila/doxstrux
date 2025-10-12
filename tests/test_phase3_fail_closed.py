"""
Phase 3 Tests - Fail-Closed Validation

Tests for the fail-closed approach to link/image validation:
- parse() never mutates source text
- Disallowed content triggers embedding_blocked
- sanitize() is deprecated and non-mutating
"""

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux import security_validators


def test_parse_does_not_mutate_source():
    """Verify fail-closed: parse() never modifies content."""
    text = "Click [here](javascript:alert(1)) ok"
    p = MarkdownParserCore(text, {"security_profile": "strict"})
    result = p.parse()

    # Raw content must be unchanged (fail-closed, no mutation in parse)
    assert result["content"]["raw"] == text


def test_disallowed_links_blocked():
    """Verify policy enforcement: disallowed schemes trigger block."""
    text = "Click [here](javascript:alert(1)) ok"
    p = MarkdownParserCore(text, {"security_profile": "strict"})
    result = p.parse()

    # Links with disallowed scheme should be filtered out of structure
    assert all(l.get("allowed", True) for l in result["structure"]["links"])

    # Embedding should be blocked by policy
    assert result["metadata"].get("embedding_blocked") is True
    assert "disallowed link schemes" in result["metadata"].get("embedding_block_reason", "").lower()


def test_data_uri_images_dropped():
    """Verify data-URI images are dropped by policy."""
    text = "![tiny](data:image/png;base64,AAAA)"
    p = MarkdownParserCore(text, {"security_profile": "strict"})
    result = p.parse()

    # Images with data URIs should be dropped from structure
    # (data: scheme is not in allowed schemes)
    data_images = [img for img in result["structure"]["images"] if img.get("src", "").startswith("data:")]
    assert len(data_images) == 0


def test_sanitize_deprecation():
    """Verify sanitize() returns unchanged text with deprecation warning."""
    text = "A [bad](javascript:void(0)) link"
    p = MarkdownParserCore(text)

    with pytest.warns(DeprecationWarning, match="sanitize.*deprecated"):
        s = p.sanitize()

    # Text must be unchanged
    assert s["sanitized_text"] == text
    # Must return blocked status
    assert isinstance(s["blocked"], bool)
    # Must return reasons list
    assert isinstance(s["reasons"], list)


def test_sanitize_uses_parse_results():
    """Verify sanitize() reuses parse() results (no second mutation)."""
    text = "Click [here](javascript:alert(1))"
    p = MarkdownParserCore(text, {"security_profile": "strict"})

    with pytest.warns(DeprecationWarning):
        s = p.sanitize()

    # Should be blocked due to disallowed scheme
    assert s["blocked"] is True
    # Should have reasons from parse() metadata
    assert len(s["reasons"]) > 0


def test_parse_with_allowed_links():
    """Verify allowed links are preserved."""
    text = "Visit [example](https://example.com) and [local](#section)"
    p = MarkdownParserCore(text, {"security_profile": "strict"})
    result = p.parse()

    # Should NOT be blocked
    assert result["metadata"].get("embedding_blocked") is not True
    # Links should be present in structure
    assert len(result["structure"]["links"]) == 2
    # All links should be marked as allowed
    assert all(l.get("allowed", True) for l in result["structure"]["links"])


def test_parse_with_allowed_images():
    """Verify allowed images are preserved."""
    text = "![alt](https://example.com/image.png)"
    p = MarkdownParserCore(text, {"security_profile": "strict"})
    result = p.parse()

    # Should NOT be blocked
    assert result["metadata"].get("embedding_blocked") is not True
    # Image should be present in structure
    assert len(result["structure"]["images"]) == 1
    # Image should have https scheme
    assert result["structure"]["images"][0].get("scheme") == "https"


def test_multiple_policy_violations():
    """Verify multiple violations are all captured in reasons."""
    text = """
    [bad1](javascript:alert(1))
    [bad2](data:text/html,<script>alert(2)</script>)
    <script>alert(3)</script>
    """
    p = MarkdownParserCore(text, {"security_profile": "strict"})

    with pytest.warns(DeprecationWarning):
        s = p.sanitize()

    # Should be blocked
    assert s["blocked"] is True
    # Should have multiple reasons
    assert len(s["reasons"]) >= 1
    # Text should be unchanged
    assert s["sanitized_text"] == text


def test_sanitize_with_security_profile():
    """Verify sanitize() respects security_profile parameter."""
    text = "![test](data:image/png;base64,AAAA)"
    p = MarkdownParserCore(text)

    # Strict profile should block data URIs
    with pytest.warns(DeprecationWarning):
        s_strict = p.sanitize(security_profile="strict")

    # Should block in strict mode (data: not allowed)
    assert s_strict["blocked"] is True or len(s_strict["reasons"]) > 0

    # Text unchanged
    assert s_strict["sanitized_text"] == text


def test_parse_immutability_with_mixed_content():
    """Verify parse() immutability with various content types."""
    text = """
# Header

Regular text with **bold** and *italic*.

[Good link](https://example.com)
[Bad link](javascript:void(0))

![Good image](https://example.com/img.png)
![Bad image](data:image/png;base64,AAAA)

```python
code = "block"
```

<script>alert('xss')</script>
"""
    p = MarkdownParserCore(text, {"security_profile": "moderate"})
    result = p.parse()

    # Raw content must be byte-identical
    assert result["content"]["raw"] == text
    # Should have security flags set
    assert "embedding_blocked" in result["metadata"] or "quarantined" in result["metadata"]


def test_raw_scheme_detection_compiled_regex():
    """Verify centralized security validator catches dangerous schemes in raw content.

    Phase 6 Task 6.1: Updated to use security_validators.scan_raw_for_disallowed_schemes()
    """
    # Positive cases - should match
    assert security_validators.scan_raw_for_disallowed_schemes("prefix javascript:alert(1) suffix")["found"]
    assert security_validators.scan_raw_for_disallowed_schemes("FILE://host/path")["found"]  # case insensitive
    assert security_validators.scan_raw_for_disallowed_schemes("data:text/html,<script>")["found"]
    assert security_validators.scan_raw_for_disallowed_schemes("[link](javascript:alert)")["found"]
    assert security_validators.scan_raw_for_disallowed_schemes("vbscript:msgbox")["found"]

    # Negative cases - should NOT match
    assert not security_validators.scan_raw_for_disallowed_schemes("https://example.com")["found"]
    assert not security_validators.scan_raw_for_disallowed_schemes("mailto:user@example.com")["found"]
    assert not security_validators.scan_raw_for_disallowed_schemes("data:image/png;base64,ABC")["found"]  # data:image is OK
    assert not security_validators.scan_raw_for_disallowed_schemes("normal text with javascript word")["found"]
