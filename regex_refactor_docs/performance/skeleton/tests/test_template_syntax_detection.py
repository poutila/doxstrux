"""Tests for template syntax detection in collectors.

These tests verify that collectors flag potential SSTI (Server-Side Template
Injection) risks by detecting template syntax in user-provided content.
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "doxstrux" / "markdown"))

try:
    from utils.token_warehouse import TokenWarehouse
    from collectors_phase8.headings import HeadingsCollector
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("⚠️  Warning: Collectors not available")
    print("   Skipping template syntax detection tests")


def test_template_syntax_detection_jinja():
    """Verify collectors flag Jinja2 template syntax."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    # Simulate heading with Jinja2 syntax
    tokens = [
        {"type": "heading_open", "tag": "h1", "nesting": 1},
        {"type": "inline", "content": "Hello {{username}}", "nesting": 0},
        {"type": "heading_close", "tag": "h1", "nesting": -1},
    ]

    wh = TokenWarehouse(tokens, None)
    collector = HeadingsCollector()
    wh.register_collector(collector)
    wh.dispatch_all()

    result = collector.finalize(wh)

    assert len(result) == 1
    heading = result[0]

    assert heading["text"] == "Hello {{username}}"
    assert heading["contains_template_syntax"] is True
    assert heading["needs_escaping"] is True


def test_template_syntax_detection_erb():
    """Verify collectors flag ERB template syntax."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    tokens = [
        {"type": "heading_open", "tag": "h2", "nesting": 1},
        {"type": "inline", "content": "Welcome <%= user.name %>", "nesting": 0},
        {"type": "heading_close", "tag": "h2", "nesting": -1},
    ]

    wh = TokenWarehouse(tokens, None)
    collector = HeadingsCollector()
    wh.register_collector(collector)
    wh.dispatch_all()

    result = collector.finalize(wh)

    assert len(result) == 1
    assert result[0]["contains_template_syntax"] is True


def test_template_syntax_detection_php():
    """Verify collectors flag PHP template syntax."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    tokens = [
        {"type": "heading_open", "tag": "h3", "nesting": 1},
        {"type": "inline", "content": "<?php echo $var ?>", "nesting": 0},
        {"type": "heading_close", "tag": "h3", "nesting": -1},
    ]

    wh = TokenWarehouse(tokens, None)
    collector = HeadingsCollector()
    wh.register_collector(collector)
    wh.dispatch_all()

    result = collector.finalize(wh)

    assert len(result) == 1
    assert result[0]["contains_template_syntax"] is True


def test_template_syntax_detection_bash():
    """Verify collectors flag Bash variable syntax."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    tokens = [
        {"type": "heading_open", "tag": "h1", "nesting": 1},
        {"type": "inline", "content": "Path: ${HOME}/docs", "nesting": 0},
        {"type": "heading_close", "tag": "h1", "nesting": -1},
    ]

    wh = TokenWarehouse(tokens, None)
    collector = HeadingsCollector()
    wh.register_collector(collector)
    wh.dispatch_all()

    result = collector.finalize(wh)

    assert len(result) == 1
    assert result[0]["contains_template_syntax"] is True


def test_template_syntax_detection_ruby():
    """Verify collectors flag Ruby interpolation syntax."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    tokens = [
        {"type": "heading_open", "tag": "h1", "nesting": 1},
        {"type": "inline", "content": "Name: #{user.name}", "nesting": 0},
        {"type": "heading_close", "tag": "h1", "nesting": -1},
    ]

    wh = TokenWarehouse(tokens, None)
    collector = HeadingsCollector()
    wh.register_collector(collector)
    wh.dispatch_all()

    result = collector.finalize(wh)

    assert len(result) == 1
    assert result[0]["contains_template_syntax"] is True


def test_clean_heading_no_template():
    """Verify clean headings are not flagged."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    tokens = [
        {"type": "heading_open", "tag": "h1", "nesting": 1},
        {"type": "inline", "content": "Normal Heading", "nesting": 0},
        {"type": "heading_close", "tag": "h1", "nesting": -1},
    ]

    wh = TokenWarehouse(tokens, None)
    collector = HeadingsCollector()
    wh.register_collector(collector)
    wh.dispatch_all()

    result = collector.finalize(wh)

    assert len(result) == 1
    heading = result[0]

    assert heading["text"] == "Normal Heading"
    assert heading["contains_template_syntax"] is False
    assert heading["needs_escaping"] is False


def test_multiple_headings_mixed():
    """Test multiple headings with mixed template syntax."""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Skipped (imports not available)")
        return

    tokens = [
        # Heading 1: Clean
        {"type": "heading_open", "tag": "h1", "nesting": 1},
        {"type": "inline", "content": "Introduction", "nesting": 0},
        {"type": "heading_close", "tag": "h1", "nesting": -1},

        # Heading 2: Template
        {"type": "heading_open", "tag": "h2", "nesting": 1},
        {"type": "inline", "content": "User: {{name}}", "nesting": 0},
        {"type": "heading_close", "tag": "h2", "nesting": -1},

        # Heading 3: Clean
        {"type": "heading_open", "tag": "h2", "nesting": 1},
        {"type": "inline", "content": "Conclusion", "nesting": 0},
        {"type": "heading_close", "tag": "h2", "nesting": -1},
    ]

    wh = TokenWarehouse(tokens, None)
    collector = HeadingsCollector()
    wh.register_collector(collector)
    wh.dispatch_all()

    result = collector.finalize(wh)

    assert len(result) == 3

    # First heading: clean
    assert result[0]["contains_template_syntax"] is False

    # Second heading: template
    assert result[1]["contains_template_syntax"] is True
    assert result[1]["needs_escaping"] is True

    # Third heading: clean
    assert result[2]["contains_template_syntax"] is False


if __name__ == "__main__":
    # Run tests
    tests = [
        test_template_syntax_detection_jinja,
        test_template_syntax_detection_erb,
        test_template_syntax_detection_php,
        test_template_syntax_detection_bash,
        test_template_syntax_detection_ruby,
        test_clean_heading_no_template,
        test_multiple_headings_mixed,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
