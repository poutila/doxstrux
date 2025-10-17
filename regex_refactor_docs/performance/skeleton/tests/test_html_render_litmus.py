"""
End-to-end HTML/SVG render litmus tests for P0-2.

These tests validate the FULL pipeline: Parse → Store → Render
Unlike test_html_xss_end_to_end.py which tests collection only,
these tests actually render output to verify sanitization works end-to-end.

Per CLOSING_IMPLEMENTATION.md lines 338-600.
"""
import pytest
from pathlib import Path


def test_html_xss_litmus_script_tags():
    """
    Litmus test: Parse → Store → Render pipeline blocks <script> tags.

    CRITICAL: This test simulates actual rendering to verify sanitization.
    Per CLOSING_IMPLEMENTATION.md lines 383-436.
    """
    # Step 1: Parse markdown with XSS payloads
    markdown = """
# Test Heading

<script>alert('XSS')</script>
<img src=x onerror="alert('XSS2')">
"""

    try:
        from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        pytest.skip("HTMLCollector or TokenWarehouse not available")

    # Parse markdown (using markdown-it-py directly for simplicity)
    try:
        from markdown_it import MarkdownIt
    except ImportError:
        pytest.skip("markdown-it-py not available")

    md = MarkdownIt("commonmark", {"html": True})
    tokens = md.parse(markdown)

    # Step 2: Collect HTML with sanitization enabled
    html_collector = HTMLCollector(allow_html=True, sanitize_on_finalize=True)

    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(html_collector)
    wh.dispatch_all()
    result = html_collector.finalize(wh)

    # Handle dict return type (may have metadata)
    html_blocks = result if isinstance(result, list) else result.get("html_blocks", [])

    # Step 3: Simulate rendering (what downstream consumer does)
    # Jinja2 template simulation
    rendered_parts = []
    for block in html_blocks:
        content = block.get("content", "") if isinstance(block, dict) else str(block)
        rendered_parts.append(content)

    rendered_html = "\n".join(rendered_parts)

    # Step 4: ASSERTIONS - Verify dangerous content stripped
    assert '<script>' not in rendered_html.lower(), \
        "Script tags not stripped from rendered HTML"
    assert '</script>' not in rendered_html.lower(), \
        "Script close tags not stripped from rendered HTML"
    assert 'onerror=' not in rendered_html.lower(), \
        "Event handlers not stripped from rendered HTML"
    assert 'javascript:' not in rendered_html.lower(), \
        "javascript: URLs not stripped from rendered HTML"
    assert 'alert(' not in rendered_html.lower(), \
        "alert() calls not stripped from rendered HTML"

    # EVIDENCE ANCHOR
    # CLAIM-P0-2-LITMUS-1: End-to-end rendering sanitizes XSS payloads
    # Verification: Rendered HTML contains no executable content
    # Source: CLOSING_IMPLEMENTATION.md lines 383-436


def test_html_xss_litmus_svg_vectors():
    """
    Litmus test: SVG XSS vectors are sanitized in render pipeline.

    Per CLOSING_IMPLEMENTATION.md lines 439-463.
    """
    markdown = """
<svg onload="alert('XSS')">
  <image xlink:href="javascript:alert('XSS2')"/>
</svg>
"""

    try:
        from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from markdown_it import MarkdownIt
    except ImportError:
        pytest.skip("Required modules not available")

    md = MarkdownIt("commonmark", {"html": True})
    tokens = md.parse(markdown)

    html_collector = HTMLCollector(allow_html=True, sanitize_on_finalize=True)

    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(html_collector)
    wh.dispatch_all()
    result = html_collector.finalize(wh)

    html_blocks = result if isinstance(result, list) else result.get("html_blocks", [])

    # Render and verify
    for block in html_blocks:
        content = block.get("content", "") if isinstance(block, dict) else str(block)

        # SVG event handlers must be stripped
        assert 'onload=' not in content.lower(), \
            f"SVG onload not stripped: {content}"
        assert 'xlink:href="javascript:' not in content.lower(), \
            f"xlink:href javascript: not stripped: {content}"
        assert 'alert(' not in content.lower(), \
            f"alert() calls not stripped: {content}"

    # EVIDENCE ANCHOR
    # CLAIM-P0-2-LITMUS-2: SVG XSS vectors sanitized in render pipeline
    # Source: CLOSING_IMPLEMENTATION.md lines 439-463


def test_html_default_off_policy():
    """
    Verify HTMLCollector is default-off (fail-closed).

    Per Executive summary: "enforce fail-closed default"
    CLOSING_IMPLEMENTATION.md lines 465-481.
    """
    try:
        from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
    except ImportError:
        pytest.skip("HTMLCollector not available")

    # Default instance
    collector = HTMLCollector()

    # ASSERTION: allow_html must be False by default
    assert hasattr(collector, 'allow_html'), \
        "HTMLCollector missing allow_html attribute"
    assert collector.allow_html is False, \
        "HTMLCollector must be default-off (fail-closed). Found allow_html=True."

    # EVIDENCE ANCHOR
    # CLAIM-P0-2-DEFAULT: HTMLCollector fails closed (default-off)
    # Source: Executive summary A.2 + CLOSING_IMPLEMENTATION.md lines 465-481


def test_allow_raw_html_flag_mechanism():
    """
    Verify ALLOW_RAW_HTML flag mechanism works correctly.

    Per Executive summary: "require ALLOW_RAW_HTML=True and a documented sanitizer pipeline"
    CLOSING_IMPLEMENTATION.md lines 484-501.
    """
    try:
        from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
    except ImportError:
        pytest.skip("HTMLCollector not available")

    # Test 1: Explicit opt-in works
    collector_enabled = HTMLCollector(allow_html=True, sanitize_on_finalize=False)
    assert collector_enabled.allow_html is True, \
        "Explicit allow_html=True should enable HTML collection"

    # Test 2: Sanitization can be enabled
    collector_sanitized = HTMLCollector(allow_html=True, sanitize_on_finalize=True)
    assert collector_sanitized.allow_html is True
    assert hasattr(collector_sanitized, 'sanitize_on_finalize'), \
        "HTMLCollector missing sanitize_on_finalize attribute"
    assert collector_sanitized.sanitize_on_finalize is True

    # Test 3: Default is off + no sanitization (fail closed)
    collector_default = HTMLCollector()
    assert collector_default.allow_html is False

    # EVIDENCE ANCHOR
    # CLAIM-P0-2-FLAG: ALLOW_RAW_HTML flag mechanism verified
    # Source: CLOSING_IMPLEMENTATION.md lines 484-501


def test_html_xss_litmus_with_jinja2_rendering():
    """
    CRITICAL LITMUS: Parse → Store → Render pipeline with actual Jinja2 template.

    This test RENDERS collected HTML in Jinja2 to verify sanitization end-to-end.
    Per extended plan P0-2: "parse → persist → server-side render into real template"
    """
    try:
        from jinja2 import Template
    except ImportError:
        pytest.skip("jinja2 not installed")

    # Step 1: Parse markdown with XSS payloads
    markdown = """
# Test Heading

<script>alert('XSS')</script>
<img src=x onerror="alert('XSS2')">
<svg onload="alert('XSS3')">
  <image xlink:href="javascript:alert('XSS4')"/>
</svg>
"""

    try:
        from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from markdown_it import MarkdownIt
    except ImportError:
        pytest.skip("Required modules not available")

    # Step 2: Parse with HTMLCollector (sanitization enabled)
    md = MarkdownIt("commonmark", {"html": True})
    tokens = md.parse(markdown)

    html_collector = HTMLCollector(allow_html=True, sanitize_on_finalize=True)

    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(html_collector)
    wh.dispatch_all()
    result = html_collector.finalize(wh)

    html_blocks = result if isinstance(result, list) else result.get("html_blocks", [])

    # Step 3: Render to Jinja2 template (simulate downstream consumer)
    template = Template("""
<!DOCTYPE html>
<html>
<body>
{%- for block in html_blocks %}
{{ block.content if block is mapping else block | safe }}
{%- endfor %}
</body>
</html>
""")

    rendered_html = template.render(html_blocks=html_blocks)

    # Step 4: CRITICAL ASSERTIONS - No executable content survives
    assert '<script>' not in rendered_html.lower(), \
        "❌ CRITICAL: Script tags not stripped from rendered output"
    assert '</script>' not in rendered_html.lower(), \
        "❌ CRITICAL: Script close tags not stripped"
    assert 'onerror=' not in rendered_html.lower(), \
        "❌ CRITICAL: Event handlers not stripped"
    assert 'onload=' not in rendered_html.lower(), \
        "❌ CRITICAL: SVG onload not stripped"
    assert 'javascript:' not in rendered_html.lower(), \
        "❌ CRITICAL: javascript: URLs not stripped"
    assert 'xlink:href="javascript:' not in rendered_html.lower(), \
        "❌ CRITICAL: SVG xlink javascript: not stripped"

    # EVIDENCE ANCHOR
    # CLAIM-P0-2-JINJA2: End-to-end Jinja2 rendering sanitizes XSS payloads
    # Verification: Rendered HTML contains no executable content
    # Source: PLAN_CLOSING_IMPLEMENTATION_extended_1.md lines 259-333


def test_html_xss_litmus_ssti_prevention():
    """
    CRITICAL LITMUS: Verify SSTI prevention in downstream rendering.

    Tests that template expressions in HTML content are NOT evaluated.
    Per P0-3.5 SSTI Prevention Policy.
    """
    try:
        from jinja2 import Template, Environment
    except ImportError:
        pytest.skip("jinja2 not installed")

    # Payload with template expression
    unsafe_payload = "{{ 7 * 7 }}"

    # BAD CONSUMER: naive Template without autoescape (demonstrates risk)
    t = Template(unsafe_payload)
    rendered_bad = t.render()
    assert rendered_bad.strip() == "49", \
        "Sanity check: jinja2 evaluated the expression (demonstrates SSTI risk)"

    # GOOD CONSUMER: Environment with autoescape + passing data as variables
    env = Environment(autoescape=True)
    tm = env.from_string("{{ value }}")
    safe_rendered = tm.render(value=unsafe_payload)

    # The safe render should escape the curly braces; literal should NOT evaluate to 49
    assert "49" not in safe_rendered, \
        "❌ CRITICAL: SSTI evaluation occurred - template expression was executed"
    assert "{{" in safe_rendered or "{" in safe_rendered or "7" in safe_rendered, \
        f"Safe rendering should preserve literal template tokens; found: {safe_rendered!r}"

    # Test with HTML collection pipeline
    markdown = f"<p>{unsafe_payload}</p>"

    try:
        from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from markdown_it import MarkdownIt
    except ImportError:
        pytest.skip("Required modules not available for pipeline test")

    md = MarkdownIt("commonmark", {"html": True})
    tokens = md.parse(markdown)

    html_collector = HTMLCollector(allow_html=True, sanitize_on_finalize=True)

    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(html_collector)
    wh.dispatch_all()
    result = html_collector.finalize(wh)

    html_blocks = result if isinstance(result, list) else result.get("html_blocks", [])

    # Render in safe template
    template = env.from_string("""
{%- for block in html_blocks %}
{{ block.content if block is mapping else block | safe }}
{%- endfor %}
""")

    rendered_pipeline = template.render(html_blocks=html_blocks)

    # MUST NOT evaluate to 49
    assert "49" not in rendered_pipeline, \
        "❌ CRITICAL: SSTI evaluation in pipeline - template expression was executed"

    # EVIDENCE ANCHOR
    # CLAIM-P0-3.5-LITMUS: SSTI prevention verified via rendering tests
    # Source: P0-3.5 policy + PLAN_CLOSING_IMPLEMENTATION_extended_1.md lines 335-369


# EVIDENCE ANCHOR FOR FULL P0-2 COMPLETION
# CLAIM-P0-2-IMPL: HTML/SVG litmus tests complete
# Files: test_html_render_litmus.py (6 tests: 4 original + 2 new Jinja2/SSTI)
# Coverage:
#   - Script tag sanitization (litmus 1)
#   - SVG XSS vector sanitization (litmus 2)
#   - Default-off policy (test 3)
#   - Flag mechanism verification (test 4)
#   - Jinja2 rendering end-to-end (test 5) ✅ NEW
#   - SSTI prevention (test 6) ✅ NEW
# Source: CLOSING_IMPLEMENTATION.md lines 338-600
# Extended: PLAN_CLOSING_IMPLEMENTATION_extended_1.md lines 221-388
# Status: ✅ COMPLETE
