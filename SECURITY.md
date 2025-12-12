# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Security Features

Doxstrux is designed with security-first principles:

### Security Profiles

Three profiles with different trust levels:

| Profile | Max Size | Max Lines | Use Case |
|---------|----------|-----------|----------|
| **strict** | 100KB | 2K | Untrusted input from users |
| **moderate** | 1MB | 10K | Standard use (default) |
| **permissive** | 10MB | 50K | Trusted internal documents |

**Default behavior**:
- `MarkdownParserCore` defaults to `security_profile="moderate"` for content limits
- `check_prompt_injection()` defaults to `profile="strict"` for maximum safety
- Both can be overridden explicitly when needed

### Built-in Protections

- **Content size limits** - Prevents resource exhaustion
- **Recursion depth limits** - Prevents stack overflow attacks
- **Link scheme validation** - Blocks javascript:, data:, etc.
- **BiDi control detection** - Detects text direction manipulation
- **Confusable character detection** - Detects homograph attacks
- **HTML detection** - Detects dangerous HTML (see note below)
- **Script tag detection** - Warns about embedded scripts
- **Event handler detection** - Detects onclick, onerror, etc.

> **⚠️ HTML Sanitization Note**: Doxstrux **detects** dangerous HTML patterns and sets
> `embedding_blocked: True` when found, but it does **NOT** sanitize/strip HTML content.
> If you render parsed HTML content in a web UI, you MUST sanitize it downstream using
> a library like `bleach.clean()`. For untrusted input, use `security_profile='strict'`
> with `allows_html: False` to prevent HTML from being parsed entirely.

### Token-Based Parser Architecture

Phase 6 completed: **Zero regex patterns in the core parser**. All structure extraction is token-based from markdown-it-py AST. This eliminates:
- ReDoS (Regular Expression Denial of Service) vulnerabilities in parsing
- Regex complexity attacks on document structure
- Backtracking explosions from malformed markdown

**Security layer regex**: The security kernel uses ~15 vetted regex patterns for:
- Prompt injection detection (`PROMPT_INJECTION_PATTERNS`)
- BiDi/confusable character detection
- URL scheme classification
- Dangerous HTML pattern detection

These patterns operate on bounded input (truncated per security profile) and are not exposed to arbitrary document length.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### Reporting Process

1. **Email**: security@doxstrux.example.com (replace with actual email)
2. **Subject**: "Security Vulnerability in Doxstrux"
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: Within 7 days
  - High: Within 30 days
  - Medium: Within 60 days
  - Low: Next release

### Disclosure Policy

- We will coordinate disclosure with you
- Security advisories will be published after fix is released
- Credit will be given (if desired)

## Security Best Practices

### For Users

**1. Choose Appropriate Security Profile**
```python
# Untrusted user input
parser = MarkdownParserCore(content, security_profile='strict')

# Internal trusted docs
parser = MarkdownParserCore(content, security_profile='moderate')
```

**2. Validate Content Size Before Parsing**
```python
# Check size before parsing large content
if len(content) > 1_000_000:  # 1MB
    raise ValueError("Content too large")

parser = MarkdownParserCore(content)
```

**3. Check Security Metadata**
```python
result = parser.parse()
security = result['metadata']['security']

# Check for threats
if security['statistics']['has_script']:
    print("Warning: Script tags detected")

if security['statistics']['has_event_handlers']:
    print("Warning: Event handlers detected")
```

**4. Disable HTML for Untrusted Content**
```python
parser = MarkdownParserCore(
    content,
    config={'allows_html': False},
    security_profile='strict'
)
```

### For Developers

**1. Never Bypass Security Checks**
```python
# ❌ WRONG: Don't disable security
parser = MarkdownParserCore(content, security_profile=None)

# ✅ CORRECT: Use appropriate profile
parser = MarkdownParserCore(content, security_profile='moderate')
```

**2. Validate External Links**
```python
result = parser.parse()
for link in result['structure']['links']:
    scheme = urllib.parse.urlparse(link['href']).scheme
    if scheme not in ['http', 'https', 'mailto']:
        print(f"Warning: Unusual scheme: {scheme}")
```

**3. Monitor Security Warnings**
```python
result = parser.parse()
warnings = result['metadata']['security']['warnings']
for warning in warnings:
    logging.warning(f"Security: {warning['type']} - {warning['message']}")
```

## Known Limitations

### Not Protected Against

- **Markdown bombs** - Deeply nested structures (use recursion limits)
- **External resource exhaustion** - Image/link fetching (validate URLs before fetching)
- **Semantic attacks** - Misleading content (requires semantic analysis)
- **Novel prompt injections** - Pattern-based detection is a blocklist approach; new jailbreak
  techniques will bypass it. Treat `suspected_prompt_injection` as a signal, not a guarantee.
  Implement LLM-level guardrails for comprehensive protection.

### Protected Against

- ✅ ReDoS attacks (zero regex in parser)
- ✅ Script injection (detected, blocked if allows_html=False)
- ✅ Stack overflow (recursion limits)
- ✅ Memory exhaustion (size limits)
- ✅ Homograph attacks (confusable detection)
- ✅ BiDi manipulation (control character detection)

## Security Advisories

Security advisories will be published at:
- GitHub Security Advisories: https://github.com/doxstrux/doxstrux/security/advisories
- CHANGELOG.md with [SECURITY] prefix

## Dependencies

Current minimal dependencies (v0.2.1):
- `markdown-it-py>=3.0.0` - Parsing engine
- `mdit-py-plugins>=0.5.0` - Extended features
- `pyyaml>=6.0.2` - YAML frontmatter

All dependencies are from trusted sources with active security maintenance.

## Security Updates

Subscribe to security updates:
- Watch repository for releases
- Enable Dependabot alerts
- Follow GitHub Security Advisories

---

**Last Updated**: 2025-12-10
**Version**: 0.2.1
