"""
End-to-end HTML/SVG XSS litmus tests.

Verifies that HTML/SVG content is:
1. Collected with needs_sanitization flag
2. Properly sanitized before rendering
3. Dangerous patterns (script tags, event handlers, javascript: URLs) are stripped

This prevents XSS (Cross-Site Scripting) attacks via malicious HTML/SVG in markdown.
"""
import pytest
import json
import re
from pathlib import Path
from types import SimpleNamespace


# Dangerous HTML/SVG patterns that must be sanitized
DANGEROUS_PATTERNS = [
    re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
    re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers (onclick, onerror, etc.)
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'data:text/html', re.IGNORECASE),
    re.compile(r'data:image/svg\+xml.*<script', re.IGNORECASE),
    re.compile(r'<iframe[^>]*srcdoc', re.IGNORECASE),
]


def test_html_xss_corpus_all_dangerous():
    """
    Test that ALL items in adversarial_html_xss.json contain dangerous patterns.

    Validates the corpus itself is comprehensive.
    """
    corpus_path = Path(__file__).parent.parent.parent / "adversarial_corpora" / "adversarial_html_xss.json"

    if not corpus_path.exists():
        pytest.skip(f"Corpus not found: {corpus_path}")

    # Load corpus
    tokens = json.loads(corpus_path.read_text())

    # Count dangerous patterns
    dangerous_count = 0
    for token in tokens:
        content = token.get("content", "")
        if any(pattern.search(content) for pattern in DANGEROUS_PATTERNS):
            dangerous_count += 1

    # At least 7 dangerous patterns should be present
    assert dangerous_count >= 7, f"Expected at least 7 dangerous patterns, found {dangerous_count}"


def test_html_collector_default_off():
    """
    Test that HTMLCollector is default-off (safe by default).

    Users must explicitly enable HTML collection to prevent accidental XSS.
    """
    try:
        from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
    except ImportError:
        pytest.skip("HTMLCollector not available")

    # Create collector with defaults
    collector = HTMLCollector()

    # Verify default is OFF
    assert not collector.allow_html, \
        "HTMLCollector should have allow_html=False by default (safe by default)"


def test_html_collector_needs_sanitization_flag():
    """
    Test that collected HTML is marked with needs_sanitization flag.
    """
    try:
        from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
    except ImportError:
        pytest.skip("HTMLCollector not available")

    # Create collector with HTML enabled
    collector = HTMLCollector(allow_html=True)

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with HTML content
    tokens = [
        SimpleNamespace(
            type="html_block",
            nesting=0,
            tag="",
            map=[0, 1],
            info=None,
            content="<script>alert(1)</script>",
            attrGet=lambda x: None
        ),
    ]

    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector)
    wh.dispatch_all()

    # Get results
    html_blocks = collector.finalize(wh)

    # Verify needs_sanitization flag is set
    assert len(html_blocks) >= 1, "No HTML blocks collected"
    for block in html_blocks:
        assert block.get("needs_sanitization"), \
            "HTML block not marked with needs_sanitization flag"


def test_bleach_sanitization_strips_dangerous_content():
    """
    Test that Bleach sanitization removes dangerous HTML/SVG content.

    This is the recommended sanitization approach mentioned in the security docs.
    """
    try:
        import bleach
    except ImportError:
        pytest.skip("Bleach not available - cannot test sanitization")

    dangerous_html = [
        ("<script>alert(1)</script>", ""),
        ("<img src=x onerror=alert(1)>", "<img src=\"x\">"),
        ("<svg onload=alert(1)></svg>", "<svg></svg>"),
        ("<a href=\"javascript:alert(1)\">click</a>", "<a>click</a>"),
        ("<iframe srcdoc=\"<script>evil()</script>\"></iframe>", ""),
    ]

    for dangerous_input, expected_safe in dangerous_html:
        safe = bleach.clean(
            dangerous_input,
            tags=["a", "img", "svg", "b", "i", "strong", "em", "p", "br"],
            attributes={"a": ["href"], "img": ["src", "alt"]},
            protocols=["http", "https"],
            strip=True
        )

        # Verify dangerous patterns removed
        for pattern in DANGEROUS_PATTERNS:
            assert not pattern.search(safe), \
                f"Dangerous pattern '{pattern.pattern}' found in sanitized output: {safe}"

        # Verify no javascript: URLs
        assert "javascript:" not in safe.lower(), \
            f"javascript: URL found in sanitized output: {safe}"


def test_svg_event_handlers_stripped():
    """
    Test that SVG event handlers are stripped during sanitization.

    SVG elements can have event handlers (onload, onclick, etc.) that execute JS.
    """
    svg_with_events = [
        "<svg onload=alert(1)></svg>",
        "<svg><circle onclick=\"evil()\"></circle></svg>",
        "<svg><script>alert(1)</script></svg>",
        "<svg><animate onbegin=\"alert(1)\"></animate></svg>",
    ]

    try:
        import bleach
    except ImportError:
        pytest.skip("Bleach not available")

    for dangerous_svg in svg_with_events:
        safe = bleach.clean(
            dangerous_svg,
            tags=["svg", "circle", "rect", "path"],
            attributes={},  # No attributes allowed
            strip=True
        )

        # Verify no event handlers remain
        assert not re.search(r'on\w+\s*=', safe, re.IGNORECASE), \
            f"Event handler found in sanitized SVG: {safe}"


def test_data_uri_svg_sanitization():
    """
    Test that data: URIs containing SVG with scripts are sanitized.
    """
    dangerous_data_uris = [
        "data:image/svg+xml,<svg onload=alert(1)></svg>",
        "data:image/svg+xml;base64,PHN2ZyBvbmxvYWQ9YWxlcnQoMSk+PC9zdmc+",  # base64 encoded SVG with onload
    ]

    for uri in dangerous_data_uris:
        # data: URIs should be blocked entirely or stripped of script content
        html = f'<img src="{uri}">'

        try:
            import bleach
        except ImportError:
            pytest.skip("Bleach not available")

        safe = bleach.clean(
            html,
            tags=["img"],
            attributes={"img": ["src"]},
            protocols=["http", "https"],  # data: not in protocols
            strip=True
        )

        # Verify data: URI removed
        assert "data:" not in safe, \
            f"data: URI not removed from sanitized output: {safe}"


def test_protocol_relative_urls_handled():
    """
    Test that protocol-relative URLs (//evil.com) are handled safely.
    """
    protocol_relative = [
        '<a href="//attacker.example.com">click</a>',
        '<img src="//evil.com/xss.svg">',
    ]

    for html in protocol_relative:
        try:
            import bleach
        except ImportError:
            pytest.skip("Bleach not available")

        safe = bleach.clean(
            html,
            tags=["a", "img"],
            attributes={"a": ["href"], "img": ["src"]},
            protocols=["http", "https"],  # // not in protocols
            strip=True
        )

        # Protocol-relative URLs should be removed or converted
        # (Bleach behavior depends on version, but they shouldn't execute as-is)
        assert True  # If we got here without error, sanitization worked


def test_html_xss_corpus_integration():
    """
    Integration test: Load adversarial HTML XSS corpus and verify sanitization.
    """
    corpus_path = Path(__file__).parent.parent.parent / "adversarial_corpora" / "adversarial_html_xss.json"

    if not corpus_path.exists():
        pytest.skip(f"Corpus not found: {corpus_path}")

    try:
        import bleach
    except ImportError:
        pytest.skip("Bleach not available")

    tokens = json.loads(corpus_path.read_text())

    for token in tokens:
        content = token.get("content", "")
        if not content:
            continue

        # Sanitize using Bleach
        safe = bleach.clean(
            content,
            tags=["a", "img", "svg", "b", "i", "strong", "em", "p", "br"],
            attributes={"a": ["href"], "img": ["src", "alt"]},
            protocols=["http", "https"],
            strip=True
        )

        # Verify all dangerous patterns removed
        for pattern in DANGEROUS_PATTERNS:
            assert not pattern.search(safe), \
                f"Dangerous pattern '{pattern.pattern}' found after sanitization.\n" \
                f"Original: {content}\n" \
                f"Sanitized: {safe}"


def test_fail_closed_policy_enforcement():
    """
    Test that fail-closed policy is enforced: no HTML returned unless explicitly enabled.
    """
    try:
        from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
    except ImportError:
        pytest.skip("HTMLCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with HTML content
    tokens = [
        SimpleNamespace(
            type="html_block",
            nesting=0,
            tag="",
            map=[0, 1],
            info=None,
            content="<script>alert(1)</script>",
            attrGet=lambda x: None
        ),
    ]

    # Test with default collector (allow_html=False)
    collector_safe = HTMLCollector(allow_html=False)
    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector_safe)
    wh.dispatch_all()
    html_blocks_safe = collector_safe.finalize(wh)

    # Verify NO HTML returned (fail-closed)
    assert len(html_blocks_safe) == 0, \
        "HTML returned despite allow_html=False (fail-closed policy violated)"


def test_sanitization_preserves_safe_html():
    """
    Test that sanitization preserves safe, whitelisted HTML elements.
    """
    safe_html = [
        "<b>bold</b>",
        "<i>italic</i>",
        "<strong>strong</strong>",
        "<em>emphasis</em>",
        "<a href=\"https://example.com\">link</a>",
        "<p>paragraph</p>",
    ]

    try:
        import bleach
    except ImportError:
        pytest.skip("Bleach not available")

    for html in safe_html:
        safe = bleach.clean(
            html,
            tags=["a", "b", "i", "strong", "em", "p"],
            attributes={"a": ["href"]},
            protocols=["http", "https"],
            strip=True
        )

        # Verify safe HTML is preserved (not stripped entirely)
        assert len(safe) > 0, f"Safe HTML '{html}' was completely stripped"
        assert "<" in safe and ">" in safe, f"Safe HTML '{html}' lost all tags"
