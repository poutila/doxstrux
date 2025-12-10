"""Configuration constants and security profiles.

This module contains all configuration constants, security patterns, and
security profiles for the markdown parser. Single source of truth for
security policies and resource limits.

Constants:
    SECURITY_PROFILES: Security profile configurations (strict/moderate/permissive)
    SECURITY_LIMITS: Content size and recursion limits by profile
    ALLOWED_PLUGINS: Allowed markdown-it plugins by profile

Security Patterns (regex, retained for §6 Security):
    _STYLE_JS_PAT: CSS injection pattern (javascript: in style)
    _META_REFRESH_PAT: Meta refresh redirect detection
    _FRAMELIKE_PAT: Frame-like tags (iframe/object/embed)
    _BIDI_CONTROLS: BiDi control characters for text direction manipulation
"""

import re
from doxstrux.markdown.security import validators as security_validators


# ============================================================================
# Security Patterns (REGEX RETAINED - §6 Security)
# ============================================================================

# Phase 6 Task 6.1: These regex patterns validate content security and cannot
# be replaced by markdown-it tokens because they operate on raw content.

_STYLE_JS_PAT = re.compile(
    r'style\s*=\s*["\'][^"\']*(url\s*\(\s*javascript:|expression\s*\()', re.I
)  # REGEX RETAINED (§6 Security)

_META_REFRESH_PAT = re.compile(
    r'<meta[^>]+http-equiv\s*=\s*["\']refresh["\'][^>]*>', re.I
)  # REGEX RETAINED (§6 Security)

_FRAMELIKE_PAT = re.compile(
    r"<(iframe|object|embed)[^>]*>", re.I
)  # REGEX RETAINED (§6 Security)


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
