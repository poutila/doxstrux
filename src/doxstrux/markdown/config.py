"""Configuration constants and security profiles.

This module contains all configuration constants, security patterns, and
security profiles for the markdown parser. Single source of truth for
security policies and resource limits.

Constants:
    SECURITY_PROFILES: Security profile configurations (strict/moderate/permissive)
    SECURITY_LIMITS: Content size and recursion limits by profile
    ALLOWED_PLUGINS: Allowed markdown-it plugins by profile

Security Detection Functions (zero-regex):
    has_style_js_injection: CSS injection detection (javascript: in style)
    has_meta_refresh: Meta refresh redirect detection
    has_framelike_tag: Frame-like tags (iframe/object/embed)
    _BIDI_CONTROLS: BiDi control characters for text direction manipulation
"""

from doxstrux.markdown.security import validators as security_validators


# ============================================================================
# Security Detection Functions (ZERO-REGEX)
# ============================================================================

# Phase 8: Replaced regex with string-based detection


def has_style_js_injection(content: str) -> bool:
    """Detect style-based JavaScript injection (url(javascript:) or expression()).

    Checks for CSS-based script injection patterns in style attributes.
    """
    lower = content.lower()
    # Look for style= followed by dangerous patterns
    idx = 0
    while True:
        style_pos = lower.find("style", idx)
        if style_pos == -1:
            return False
        # Find the attribute value after style=
        eq_pos = lower.find("=", style_pos + 5)
        if eq_pos == -1 or eq_pos > style_pos + 10:  # style and = should be close
            idx = style_pos + 5
            continue
        # Check content after = for dangerous patterns
        check_region = lower[eq_pos:eq_pos + 200]  # Check reasonable window
        if "url" in check_region and "javascript:" in check_region:
            return True
        if "expression(" in check_region:
            return True
        idx = style_pos + 5


def has_meta_refresh(content: str) -> bool:
    """Detect <meta http-equiv='refresh'> tags."""
    lower = content.lower()
    idx = 0
    while True:
        meta_pos = lower.find("<meta", idx)
        if meta_pos == -1:
            return False
        # Find end of tag
        end_pos = lower.find(">", meta_pos)
        if end_pos == -1:
            return False
        tag_content = lower[meta_pos:end_pos + 1]
        if "http-equiv" in tag_content and "refresh" in tag_content:
            return True
        idx = meta_pos + 5


def has_framelike_tag(content: str) -> bool:
    """Detect frame-like tags: <iframe>, <object>, <embed>."""
    lower = content.lower()
    for tag in ("<iframe", "<object", "<embed"):
        pos = lower.find(tag)
        if pos != -1:
            # Verify it's a tag (followed by space or >)
            next_char_pos = pos + len(tag)
            if next_char_pos < len(lower):
                next_char = lower[next_char_pos]
                if next_char in (" ", ">", "\t", "\n", "/"):
                    return True
    return False


# Legacy pattern objects for backward compatibility (wrap functions)
class _PatternWrapper:
    """Wrapper to provide .search() interface for string-based detection."""
    def __init__(self, func: callable):
        self._func = func

    def search(self, content: str) -> bool:
        return self._func(content)


_STYLE_JS_PAT = _PatternWrapper(has_style_js_injection)
_META_REFRESH_PAT = _PatternWrapper(has_meta_refresh)
_FRAMELIKE_PAT = _PatternWrapper(has_framelike_tag)


# ============================================================================
# BiDi Control Characters
# ============================================================================

# BiDi control characters for detecting text direction manipulation attacks
_BIDI_CONTROLS = [
    "\u202a",  # Left-to-Right Embedding
    "\u202b",  # Right-to-Left Embedding
    "\u202c",  # Pop Directional Formatting
    "\u202d",  # Left-to-Right Override
    "\u202e",  # Right-to-Left Override
    "\u2066",  # Left-to-Right Isolate
    "\u2067",  # Right-to-Left Isolate
    "\u2068",  # First Strong Isolate
    "\u2069",  # Pop Directional Isolate
    "\u200e",  # Left-to-Right Mark
    "\u200f",  # Right-to-Left Mark
]


# ============================================================================
# Security Limits
# ============================================================================

# Content size and resource limits by security profile
SECURITY_LIMITS = {
    "strict": {
        "max_content_size": 100 * 1024,  # 100KB
        "max_line_count": 2000,  # 2K lines
        "max_token_count": 50000,  # 50K tokens
        "max_recursion_depth": 50,  # Reduced recursion
    },
    "moderate": {
        "max_content_size": 1024 * 1024,  # 1MB
        "max_line_count": 10000,  # 10K lines
        "max_token_count": 200000,  # 200K tokens
        "max_recursion_depth": 100,  # Standard recursion
    },
    "permissive": {
        "max_content_size": 10 * 1024 * 1024,  # 10MB
        "max_line_count": 50000,  # 50K lines
        "max_token_count": 1000000,  # 1M tokens
        "max_recursion_depth": 150,  # Higher recursion
    },
}


# ============================================================================
# Allowed Plugins by Profile
# ============================================================================

ALLOWED_PLUGINS = {
    "strict": {
        "builtin": ["table"],  # Only basic table support
        "external": ["front_matter", "tasklists"],  # Frontmatter plugin allowed (read-only extraction)
    },
    "moderate": {
        "builtin": ["table", "strikethrough"],
        "external": ["front_matter", "tasklists", "footnote"],
    },
    "permissive": {
        "builtin": ["table", "strikethrough"],
        "external": ["front_matter", "tasklists", "footnote", "deflist"],
    },
}


# ============================================================================
# Security Profiles
# ============================================================================

# Security profiles define policies for different trust levels
#
# SECURITY_PROFILES semantics (per SECURITY_KERNEL_SPEC.md §5):
#
# Most limits: strict < moderate < permissive (smaller = stricter)
#   - max_content_size: 100KB < 1MB < 10MB
#   - max_data_uri_size: 0 < 10KB < 100KB
#
# Exception - max_injection_scan_chars: strict > moderate > permissive
#   - Scanning MORE chars = more thorough = stricter security
#   - 4096 > 2048 > 1024 chars scanned
#   - Recommended defaults per SECURITY_KERNEL_SPEC.md §5 PROF-3
#
SECURITY_PROFILES = {
    "strict": {
        "allows_html": False,
        "allows_scripts": False,
        "allows_data_uri": False,
        "max_data_uri_size": 0,
        "max_injection_scan_chars": 4096,  # Strict scans more chars
        "allowed_schemes": security_validators.ALLOWED_LINK_SCHEMES_STRICT,
        "max_link_count": 50,
        "max_image_count": 20,
        "max_footnote_size": 256,
        "max_heading_depth": 4,
        "quarantine_on_injection": True,
        "strip_all_html": True,
    },
    "moderate": {
        "allows_html": True,
        "allows_scripts": False,
        "allows_data_uri": True,
        "max_data_uri_size": 10240,  # 10KB
        "max_injection_scan_chars": 2048,
        "allowed_schemes": security_validators.ALLOWED_LINK_SCHEMES_MODERATE,
        "max_link_count": 200,
        "max_image_count": 100,
        "max_footnote_size": 512,
        "max_heading_depth": 6,
        "quarantine_on_injection": False,
        "strip_all_html": False,
    },
    "permissive": {
        "allows_html": True,
        "allows_scripts": False,  # Never allow scripts in RAG
        "allows_data_uri": True,
        "max_data_uri_size": 102400,  # 100KB
        "max_injection_scan_chars": 1024,  # Permissive scans fewer chars
        "allowed_schemes": security_validators.ALLOWED_LINK_SCHEMES_PERMISSIVE,
        "max_link_count": 1000,
        "max_image_count": 500,
        "max_footnote_size": 2048,
        "max_heading_depth": 6,
        "quarantine_on_injection": False,
        "strip_all_html": False,
    },
}


# ============================================================================
# Safety Constants
# ============================================================================

# Maximum recursion depth to prevent stack overflow
# This is a global safety limit; per-profile limits are in SECURITY_LIMITS
MAX_RECURSION_DEPTH = 100
