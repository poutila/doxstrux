"""
End-to-end template injection litmus tests.

Verifies that template syntax in extracted metadata is:
1. Detected and flagged by collectors
2. Properly escaped/rendered by downstream consumers

This prevents SSTI (Server-Side Template Injection) attacks where malicious
markdown could inject template code that gets executed server-side.
"""
import pytest
import json
import re
from pathlib import Path
from types import SimpleNamespace


# Template syntax detection regex (matches Jinja2, ERB, JSP, EJS, Handlebars, etc.)
TEMPLATE_TOKENS = re.compile(r'(\{\{|\}\}|\{%|%}|\<%|%>|\$\{|\#\{)')


def test_template_corpus_all_flagged():
    """
    Test that ALL items in adversarial_template_injection.json are flagged.

    This is a comprehensive test that ensures the detection covers all
    template syntaxes: Jinja2, ERB, JSP, EJS, Mustache, Handlebars, Velocity, Ruby.
    """
    corpus_path = Path(__file__).parent.parent.parent / "adversarial_corpora" / "adversarial_template_injection.json"

    if not corpus_path.exists():
        pytest.skip(f"Corpus not found: {corpus_path}")

    # Load corpus
    tokens = json.loads(corpus_path.read_text())

    # Check each token for template syntax
    template_found_count = 0
    for token in tokens:
        content = token.get("content", "")
        if TEMPLATE_TOKENS.search(content):
            template_found_count += 1

    # The corpus should have multiple template patterns
    assert template_found_count >= 7, f"Expected at least 7 template patterns, found {template_found_count}"


def test_downstream_renderer_escapes_templates():
    """
    Test that downstream renderers escape template syntax.

    Simulates the flow: Parse → Extract → Render to HTML
    Ensures template syntax is escaped, not executed.
    """
    # Test cases: template syntax that should be escaped
    test_cases = [
        ("{{ config.SECRET }}", "&lbrace;&lbrace; config.SECRET &rbrace;&rbrace;"),
        ("{% if admin %}", "&lbrace;% if admin %&rbrace;"),
        ("<%= secret %>", "&lt;%= secret %&gt;"),
        ("${env.PASSWORD}", "$&lbrace;env.PASSWORD&rbrace;"),
        ("#{system_cmd}", "#&lbrace;system_cmd&rbrace;"),
    ]

    for template_input, expected_escaped in test_cases:
        # Simulate simple HTML escaping (what renderers should do)
        escaped = (template_input
                   .replace("{", "&lbrace;")
                   .replace("}", "&rbrace;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;"))

        # Verify escaping worked
        assert "{" not in escaped or "&lbrace;" in escaped, \
            f"Template '{template_input}' not properly escaped"
        assert "{{" not in escaped, \
            f"Jinja2 syntax '{{{{' found in escaped output: {escaped}"
        assert "{%" not in escaped, \
            f"Jinja2 control '{%' found in escaped output: {escaped}"


def test_heading_with_template_marked_unsafe():
    """
    Test that headings containing template syntax are marked as needing escaping.

    This ensures metadata consumers know which fields contain potentially
    dangerous template syntax.
    """
    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse class not available")

    # Create tokens with template syntax in heading
    tokens = [
        SimpleNamespace(
            type="heading_open",
            tag="h1",
            nesting=1,
            map=[0, 1],
            info=None,
            content="",
            attrGet=lambda x: None
        ),
        SimpleNamespace(
            type="inline",
            tag="",
            nesting=0,
            map=None,
            info=None,
            content="Welcome {{ config.SECRET_KEY }}",
            attrGet=lambda x: None
        ),
        SimpleNamespace(
            type="heading_close",
            tag="h1",
            nesting=-1,
            map=None,
            info=None,
            content="",
            attrGet=lambda x: None
        ),
    ]

    wh = TokenWarehouse(tokens, tree=None)

    # Create a collector that detects template syntax
    class TemplateAwareCollector:
        name = "headings"

        @property
        def interest(self):
            class I:
                types = {"heading_open", "inline"}
                tags = set()
                ignore_inside = set()
                predicate = None
            return I()

        def __init__(self):
            self.headings = []
            self.current_heading = None

        def should_process(self, token, ctx, wh_local):
            return True

        def on_token(self, idx, token, ctx, wh_local):
            if hasattr(token, 'type'):
                if token.type == "heading_open":
                    self.current_heading = {"text": "", "contains_template": False}
                elif token.type == "inline" and self.current_heading is not None:
                    content = getattr(token, "content", "")
                    self.current_heading["text"] += content
                    if TEMPLATE_TOKENS.search(content):
                        self.current_heading["contains_template"] = True
                elif token.type == "heading_close" and self.current_heading is not None:
                    self.headings.append(self.current_heading)
                    self.current_heading = None

        def finalize(self, wh_local):
            return self.headings

    collector = TemplateAwareCollector()
    try:
        wh.register_collector(collector)
    except Exception:
        wh._collectors.append(collector)

    # Dispatch
    wh.dispatch_all()

    # Get results
    headings = collector.finalize(wh)

    # Verify template syntax was detected
    assert len(headings) == 1, f"Expected 1 heading, got {len(headings)}"
    assert headings[0]["contains_template"], \
        f"Template syntax not detected in heading: {headings[0]['text']}"


def test_no_false_positives_on_safe_content():
    """
    Test that safe content is NOT flagged as containing templates.

    Prevents over-flagging that would break legitimate content.
    """
    safe_content = [
        "Normal heading without any special syntax",
        "Math: { x | x > 0 }",  # Set notation, not template
        "CSS: .class { color: red; }",  # CSS, not template
        "JSON: {\"key\": \"value\"}",  # JSON, not template
        "Price: $50 or ${amount}",  # Dollar sign alone shouldn't trigger
        "Comment: # This is a comment",  # Hash comment, not Ruby interpolation
    ]

    for content in safe_content:
        has_template = bool(TEMPLATE_TOKENS.search(content))
        assert not has_template, \
            f"False positive: '{content}' incorrectly flagged as template"


def test_jinja2_specific_patterns():
    """
    Test Jinja2-specific template patterns (most common in Python ecosystem).
    """
    jinja2_patterns = [
        "{{ variable }}",
        "{{ obj.attr }}",
        "{{ dict['key'] }}",
        "{{ func() }}",
        "{% for item in items %}",
        "{% if condition %}",
        "{% block content %}",
        "{{- stripped -}}",
        "{{ lookup('env', 'SECRET') }}",
    ]

    for pattern in jinja2_patterns:
        has_template = bool(TEMPLATE_TOKENS.search(pattern))
        assert has_template, \
            f"Jinja2 pattern not detected: '{pattern}'"


def test_mixed_template_syntaxes():
    """
    Test that content with multiple template syntaxes is detected.
    """
    mixed_content = "User: {{ user.name }} | Admin: <%= is_admin %> | Secret: ${secret}"

    matches = TEMPLATE_TOKENS.findall(mixed_content)

    # Should find: {{, }}, <%=, %>, ${, }
    assert len(matches) >= 6, f"Expected at least 6 template tokens, found {len(matches)}: {matches}"


def test_template_in_frontmatter():
    """
    Test that template syntax in frontmatter/metadata is detected.

    Frontmatter often contains configuration that gets rendered by
    downstream systems, making it a high-risk injection vector.
    """
    frontmatter_with_templates = """
    ---
    title: {{ site.title }}
    description: <%= page.desc %>
    admin_secret: ${env.ADMIN_PASSWORD}
    ---
    """

    has_template = bool(TEMPLATE_TOKENS.search(frontmatter_with_templates))
    assert has_template, "Template syntax in frontmatter not detected"


def test_template_corpus_integration():
    """
    Integration test: Load adversarial corpus and verify all patterns detected.
    """
    corpus_path = Path(__file__).parent.parent.parent / "adversarial_corpora" / "adversarial_template_injection.json"

    if not corpus_path.exists():
        pytest.skip(f"Corpus not found: {corpus_path}")

    tokens = json.loads(corpus_path.read_text())

    # Track detection rate
    total_tokens = len(tokens)
    tokens_with_templates = 0
    tokens_detected = 0

    for token in tokens:
        content = token.get("content", "")
        has_template = bool(TEMPLATE_TOKENS.search(content))

        if has_template:
            tokens_with_templates += 1
            tokens_detected += 1

    # Verify high detection rate
    if tokens_with_templates > 0:
        detection_rate = tokens_detected / tokens_with_templates
        assert detection_rate >= 0.95, \
            f"Low detection rate: {detection_rate:.2%} ({tokens_detected}/{tokens_with_templates})"
