# Server-Side Template Injection (SSTI) Prevention Policy

**Version**: 1.0
**Date**: 2025-10-17
**Status**: POLICY - REQUIRED COMPLIANCE
**Scope**: All consumer applications that render collected markdown metadata
**Source**: PLAN_CLOSING_IMPLEMENTATION.md P0-3.5 + External Security Analysis

---

## Executive Summary

**CRITICAL SECURITY REQUIREMENT**: Markdown metadata collected by doxstrux parsers MUST be treated as untrusted input and MUST NOT be evaluated by template engines.

**Attack Vector**: Template injection payloads embedded in markdown (e.g., `{{ 7 * 7 }}`, `<%= system('whoami') %>`) can achieve Remote Code Execution (RCE) if metadata is rendered without proper escaping.

**Severity**: 🔴 **CRITICAL** - RCE allows full server compromise

**Required Mitigation**: All consumer templates MUST use autoescape or explicit escaping for ALL collected metadata fields.

---

## SSTI Attack Vectors

### Common Template Injection Patterns

**Jinja2 (Python)**:
```jinja2
{{ 7 * 7 }}                          # Basic expression (evaluates to 49)
{{ ''.__class__.__mro__[1] }}       # Object traversal
{{ config.items() }}                 # Config access
{% for item in ().__class__.__bases__ %}  # Class hierarchy
```

**ERB (Ruby)**:
```erb
<%= 7 * 7 %>                         # Basic expression
<%= `whoami` %>                      # Command execution
<%= File.read('/etc/passwd') %>      # File access
```

**EJS (JavaScript)**:
```ejs
<%= 7 * 7 %>                         # Basic expression
<%= process.env %>                   # Environment variable access
<%= require('child_process').execSync('whoami') %>  # Command execution
```

**Handlebars (JavaScript)**:
```handlebars
{{7*7}}                              # Expression (may be disabled)
{{#each this}}{{@key}}{{/each}}     # Context access
```

### How Attackers Exploit SSTI

1. **Attacker embeds template payload** in markdown document:
   ```markdown
   # My Article

   Author: {{ config.SECRET_KEY }}
   ```

2. **Parser collects metadata**:
   ```json
   {
     "headings": [
       {"text": "My Article", "level": 1}
     ],
     "metadata": {
       "author": "{{ config.SECRET_KEY }}"
     }
   }
   ```

3. **Consumer renders template unsafely**:
   ```jinja2
   <h1>{{ metadata.author }}</h1>  <!-- VULNERABLE: evaluates template -->
   ```

4. **Result**: Secret key leaked to attacker (or RCE if more sophisticated payload)

---

## Safe vs. Unsafe Rendering Patterns

### ❌ UNSAFE PATTERN 1: Direct String Concatenation

**Code**:
```python
# ❌ CRITICAL VULNERABILITY
from jinja2 import Template

metadata = parser.parse(markdown)
template_string = f"<h1>{metadata['title']}</h1>"  # Direct interpolation
rendered = Template(template_string).render()
```

**Why Unsafe**: If `metadata['title']` contains `{{ 7 * 7 }}`, it becomes part of the template and gets evaluated.

---

### ❌ UNSAFE PATTERN 2: Template Without Autoescape

**Code**:
```python
# ❌ CRITICAL VULNERABILITY
from jinja2 import Environment

env = Environment(autoescape=False)  # Autoescape disabled!
template = env.from_string("<h1>{{ title }}</h1>")
rendered = template.render(title=metadata['title'])
```

**Why Unsafe**: Jinja2 evaluates `{{ title }}` as a template expression when autoescape is disabled.

---

### ✅ SAFE PATTERN 1: Autoescape Enabled (Recommended)

**Code**:
```python
# ✅ SAFE: Autoescape enabled by default
from jinja2 import Environment

env = Environment(autoescape=True)  # Autoescape ON
template = env.from_string("<h1>{{ title }}</h1>")
rendered = template.render(title=metadata['title'])
```

**Why Safe**: Autoescape treats `metadata['title']` as plain text. Template expressions like `{{ 7 * 7 }}` are escaped to `&lt;{{ 7 * 7 }}&gt;` and not evaluated.

**Verification**:
```python
# Expected output: <h1>&lt;{{ 7 * 7 }}&gt;</h1>
# NOT: <h1>49</h1>
```

---

### ✅ SAFE PATTERN 2: Explicit Escape Filter

**Code**:
```python
# ✅ SAFE: Explicit |e filter
from jinja2 import Environment

env = Environment(autoescape=False)  # Even if autoescape off
template = env.from_string("<h1>{{ title|e }}</h1>")  # |e = escape
rendered = template.render(title=metadata['title'])
```

**Why Safe**: `|e` filter explicitly escapes HTML entities and prevents template evaluation.

---

### ✅ SAFE PATTERN 3: Pre-Sanitization

**Code**:
```python
# ✅ SAFE: Sanitize before passing to template
import bleach

metadata = parser.parse(markdown)
safe_title = bleach.clean(metadata['title'], tags=[], strip=True)  # Strip ALL tags
rendered = template.render(title=safe_title)
```

**Why Safe**: Bleach strips all HTML and template-like syntax before rendering.

**Note**: This approach is defense-in-depth. Still use autoescape=True as primary defense.

---

## Consumer Requirements

### Requirement 1: Template Engine Configuration

**All consumer applications MUST configure their template engine with autoescape enabled**:

**Jinja2 (Python)**:
```python
from jinja2 import Environment, select_autoescape

env = Environment(
    autoescape=select_autoescape(['html', 'xml']),  # Enable for HTML/XML
    # OR
    autoescape=True  # Enable for all templates
)
```

**Django (Python)**:
```python
# Django templates have autoescape ON by default - do NOT disable
# settings.py:
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'autoescape': True,  # Ensure this is True (default)
        },
    },
]
```

**EJS (Node.js)**:
```javascript
// app.js:
app.set('view engine', 'ejs');
// Use <%- ... %> for escaped output (default)
// NEVER use <%= ... %> for untrusted input
```

**ERB (Ruby)**:
```ruby
# Use <%= ... %> for escaped output (default)
# NEVER use <%== ... %> for untrusted input
```

---

### Requirement 2: Variable Escaping

**All metadata variables MUST be escaped when rendered**:

**Jinja2**:
```jinja2
<!-- ✅ SAFE: Autoescape enabled -->
<h1>{{ metadata.title }}</h1>

<!-- ✅ SAFE: Explicit escape filter -->
<h1>{{ metadata.title|e }}</h1>

<!-- ❌ UNSAFE: |safe disables escaping -->
<h1>{{ metadata.title|safe }}</h1>
```

**Django**:
```django
<!-- ✅ SAFE: Autoescape enabled (default) -->
<h1>{{ metadata.title }}</h1>

<!-- ✅ SAFE: Explicit escape filter -->
<h1>{{ metadata.title|escape }}</h1>

<!-- ❌ UNSAFE: |safe disables escaping -->
<h1>{{ metadata.title|safe }}</h1>
```

---

### Requirement 3: Litmus Testing

**All consumer applications MUST implement SSTI litmus tests**:

**Test File**: `tests/test_consumer_ssti_litmus.py` (copy from skeleton)

**Test Coverage**:
1. ✅ Template expressions NOT evaluated (e.g., `{{ 7 * 7 }}` → `{{ 7 * 7 }}`, not `49`)
2. ✅ Autoescape enabled by default
3. ✅ Explicit `|e` filter prevents evaluation
4. ✅ All metadata fields tested (title, author, description, custom fields)

**Verification Command**:
```bash
pytest tests/test_consumer_ssti_litmus.py -v
```

**CI Integration**: Add to required checks in `.github/workflows/`

---

## Forbidden Patterns (Require Waiver)

The following patterns **REQUIRE Tech Lead approval + documented waiver**:

### ❌ FORBIDDEN 1: Disabling Autoescape

**Code**:
```python
# ❌ REQUIRES WAIVER
env = Environment(autoescape=False)
```

**Waiver Requirements**:
- Ticket ID: __________
- Tech Lead approval: __________
- Security review: __________
- Mitigation plan: __________ (e.g., pre-sanitization with Bleach)

---

### ❌ FORBIDDEN 2: Using |safe Filter on Untrusted Input

**Code**:
```jinja2
<!-- ❌ REQUIRES WAIVER -->
<div>{{ metadata.content|safe }}</div>
```

**Waiver Requirements**:
- Ticket ID: __________
- Tech Lead approval: __________
- Enhanced sanitization: Bleach/DOMPurify configured
- Litmus tests: Additional XSS tests passing

---

### ❌ FORBIDDEN 3: Rendering User-Controlled Template Strings

**Code**:
```python
# ❌ REQUIRES WAIVER (never recommended)
template_string = f"<h1>{user_input}</h1>"  # user_input from metadata
template = Template(template_string)
rendered = template.render()
```

**Waiver Requirements**:
- Ticket ID: __________
- Tech Lead approval: __________
- Security audit: External review required
- Sandboxing: Restricted Jinja2 environment configured

---

## Integration Guide for Consumer Repos

### Step 1: Install Dependencies

```bash
# Python (Jinja2)
pip install jinja2

# Python (Bleach for additional sanitization)
pip install bleach

# Node.js (EJS)
npm install ejs

# Ruby (ERB - built-in)
# No installation needed
```

---

### Step 2: Configure Template Engine

**Jinja2 Example** (`app.py`):
```python
from flask import Flask, render_template
from jinja2 import Environment, select_autoescape

app = Flask(__name__)
app.jinja_env.autoescape = select_autoescape(['html', 'xml'])

@app.route('/article/<id>')
def article(id):
    # Parse markdown
    from doxstrux.markdown_parser_core import MarkdownParserCore
    parser = MarkdownParserCore(markdown_content)
    metadata = parser.parse()

    # Render template (autoescape handles escaping)
    return render_template('article.html', metadata=metadata)
```

**Template** (`templates/article.html`):
```jinja2
<!DOCTYPE html>
<html>
<head>
    <title>{{ metadata.title }}</title>  <!-- Autoescape ON -->
</head>
<body>
    <h1>{{ metadata.title }}</h1>
    <p>Author: {{ metadata.author }}</p>
</body>
</html>
```

---

### Step 3: Copy SSTI Litmus Test

```bash
# Copy reference test from skeleton
cp skeleton/tests/test_consumer_ssti_litmus.py <consumer_repo>/tests/

# Install test dependencies
pip install pytest jinja2

# Run tests
pytest tests/test_consumer_ssti_litmus.py -v
```

---

### Step 4: Add to CI Pipeline

**`.github/workflows/test.yml`**:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run SSTI litmus tests
        run: pytest tests/test_consumer_ssti_litmus.py -v
        continue-on-error: false  # HARD FAIL - blocks PR merge
```

---

## Monitoring & Detection

### Production Monitoring

**Log suspicious patterns** in rendered output:

```python
import logging
import re

SSTI_PATTERNS = [
    r'\{\{.*\}\}',           # Jinja2/Handlebars
    r'\{%.*%\}',             # Jinja2 blocks
    r'<%=.*%>',              # ERB/EJS
    r'<%-.*%>',              # ERB
]

def detect_ssti_in_output(rendered_html):
    """Alert if template expressions leak into output."""
    for pattern in SSTI_PATTERNS:
        if re.search(pattern, rendered_html):
            logging.critical(
                f"SSTI_DETECTED: Template expression in output: {pattern}",
                extra={'html': rendered_html[:200]}
            )
            # Alert ops team
```

**Grafana Alerts**:
```yaml
alerts:
  - alert: SSTI_Template_Leak
    expr: rate(ssti_detected_total[1m]) > 0
    for: 1m
    labels:
      severity: P0
    annotations:
      summary: "Template expressions detected in rendered output"
```

---

## Security Audit Checklist

Before deploying consumer application to production:

- [ ] Template engine configured with autoescape=True
- [ ] All metadata variables use `{{ var }}` (escaped) or `{{ var|e }}` (explicit escape)
- [ ] No use of `|safe` filter on metadata fields
- [ ] `test_consumer_ssti_litmus.py` passing
- [ ] SSTI litmus tests added to required CI checks
- [ ] Monitoring configured for template expression detection
- [ ] Security team sign-off obtained

---

## References

- **PLAN_CLOSING_IMPLEMENTATION.md**: P0-3.5 specification
- **External Security Analysis**: Adversary-minded threat assessment (SSTI section)
- **skeleton/tests/test_consumer_ssti_litmus.py**: Reference litmus tests
- **OWASP**: [Server-Side Template Injection](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server-side_Template_Injection)
- **PortSwigger**: [Server-Side Template Injection Guide](https://portswigger.net/web-security/server-side-template-injection)

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-SSTI-POLICY | SSTI prevention policy documented | This document | ✅ Complete |
| CLAIM-SSTI-AUTOESCAPE | Autoescape requirement enforced | Integration guide Section 2 | ✅ Documented |
| CLAIM-SSTI-LITMUS | Consumer litmus tests provided | skeleton/tests/test_consumer_ssti_litmus.py | ✅ Available |
| CLAIM-SSTI-CI | CI enforcement documented | Integration guide Section 4 | ✅ Documented |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Next Review**: After first consumer integration
