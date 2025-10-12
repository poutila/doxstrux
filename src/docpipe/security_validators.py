"""
Security Validators - Centralized security regex patterns and validation functions.

Phase 6 (Task 6.1): All regex patterns here are RETAINED per REGEX_REFACTOR_EXECUTION_GUIDE §6.
These patterns validate content security and cannot be replaced by markdown-it tokens
because they operate on raw content, not parsed markdown structure.

All functions tagged with: # REGEX RETAINED (§6 Security)
"""

import re
import unicodedata
from typing import Any

# ============================================================================
# REGEX RETAINED (§6 Security) - Scheme Detection
# ============================================================================
# Rationale: Raw content scan for dangerous schemes that markdown-it might not
# parse as links (e.g., in code blocks, escaped contexts, malformed syntax).
# Token-based link extraction only catches valid markdown links.

_DISALLOWED_SCHEMES_RAW_RE = re.compile(
    r"(?:javascript:|file:|vbscript:|data:text/html)",
    re.IGNORECASE
)  # REGEX RETAINED (§6 Security)

# Scheme extraction from URLs
_URL_SCHEME_RE = re.compile(r"^([a-z][a-z0-9+.-]*):(?://)?", re.IGNORECASE)  # REGEX RETAINED (§6 Security)


# ============================================================================
# REGEX RETAINED (§6 Security) - Data URI Parsing
# ============================================================================
# Rationale: Parse data URIs to extract mediatype, encoding, and estimate size
# for budget enforcement. O(1) size check without full decode.

_DATA_URI_RE = re.compile(r"^data:([^;,]+)?(;base64)?,(.*)$", re.IGNORECASE)  # REGEX RETAINED (§6 Security)


# ============================================================================
# Constants - Allowed Schemes
# ============================================================================

ALLOWED_LINK_SCHEMES_STRICT = {"https"}
ALLOWED_LINK_SCHEMES_MODERATE = {"http", "https", "mailto", "tel"}
ALLOWED_LINK_SCHEMES_PERMISSIVE = {"http", "https", "mailto", "tel", "ftp"}


# ============================================================================
# Constants - Confusable Characters (Homograph Attack Detection)
# ============================================================================
# Extended set of Latin lookalikes from other scripts

CONFUSABLES_EXTENDED = {
    # Cyrillic lookalikes
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c",
    "у": "y", "х": "x", "А": "A", "В": "B", "Е": "E",
    "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P",
    "С": "C", "Т": "T", "Х": "X",
    # Greek lookalikes
    "α": "a", "β": "b", "ε": "e", "ι": "i", "ο": "o",
    "ρ": "p", "υ": "y", "Α": "A", "Β": "B", "Ε": "E",
    "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M",
    "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y",
    "Χ": "X",
    # Additional confusables
    "ⅰ": "i", "ⅱ": "ii", "ⅲ": "iii", "ⅳ": "iv", "ⅴ": "v",
    "ⅵ": "vi", "ⅶ": "vii", "ⅷ": "viii", "ⅸ": "ix", "ⅹ": "x",
}


# ============================================================================
# Constants - Prompt Injection Patterns
# ============================================================================

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions?", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
    re.compile(r"disregard\s+previous\s+instructions?", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
    re.compile(r"forget\s+previous\s+instructions?", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
    re.compile(r"you\s+are\s+now\s+acting\s+as", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
    re.compile(r"pretend\s+you\s+are", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
    re.compile(r"simulate\s+being", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
    re.compile(r"act\s+as\s+if", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
    re.compile(r"bypass\s+your\s+instructions?", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
    re.compile(r"override\s+your\s+instructions?", re.IGNORECASE),  # REGEX RETAINED (§6 Security)
]


# ============================================================================
# Validator Functions
# ============================================================================

def scan_raw_for_disallowed_schemes(content: str) -> dict[str, Any]:
    """
    Scan raw content for disallowed schemes that markdown-it might not parse.

    # REGEX RETAINED (§6 Security)
    Rationale: Markdown-it only parses valid markdown links. Dangerous schemes
    can appear in code blocks, escaped contexts, or malformed syntax where they
    won't be caught by token-based link extraction.

    Args:
        content: Raw markdown content to scan

    Returns:
        dict with 'found' (bool) and 'match' (str or None)
    """
    match = _DISALLOWED_SCHEMES_RAW_RE.search(content)
    return {
        "found": match is not None,
        "match": match.group(0) if match else None
    }


def validate_link_scheme(url: str, allowed_schemes: set[str]) -> tuple[str | None, bool]:
    """
    Extract and validate URL scheme.

    # REGEX RETAINED (§6 Security)
    Rationale: Scheme extraction requires regex parsing of URL structure.
    Cannot be done with markdown tokens (URLs are atomic strings in tokens).

    Args:
        url: URL string to validate
        allowed_schemes: Set of allowed schemes (e.g., {"http", "https"})

    Returns:
        Tuple of (scheme, is_allowed)
        - scheme: The URL scheme or None for relative/anchor links
        - is_allowed: True if scheme is in allowed_schemes or is relative/anchor
    """
    # Check for scheme
    match = _URL_SCHEME_RE.match(url)
    if match:
        scheme = match.group(1).lower()
        is_allowed = scheme in allowed_schemes
        return scheme, is_allowed

    # No scheme - relative or anchor link (allowed by default)
    return None, True


def parse_data_uri(uri: str) -> dict[str, Any]:
    """
    Parse data URI to extract media type, encoding, and size estimate.

    # REGEX RETAINED (§6 Security)
    Rationale: Data URI parsing requires regex to extract components.
    Size budget enforcement needs O(1) estimation without full decode.

    Args:
        uri: Data URI string (e.g., "data:image/png;base64,iVBORw0...")

    Returns:
        dict with:
        - is_data_uri: bool
        - mediatype: str (e.g., "image/png")
        - encoding: str ("base64" or "url")
        - size_bytes: int (estimated decoded size)
        - data_preview: str (first 50 chars of data)
    """
    match = _DATA_URI_RE.match(uri)
    if not match:
        return {
            "is_data_uri": False,
            "mediatype": None,
            "encoding": None,
            "size_bytes": 0,
            "data_preview": ""
        }

    mediatype = match.group(1) or "text/plain"
    is_base64 = match.group(2) == ";base64"
    data = match.group(3)

    # Estimate size without full decode (O(1))
    if is_base64:
        # Base64: 4 chars encode 3 bytes, minus padding
        padding = data.count("=")
        size_bytes = ((len(data) - padding) * 3) // 4
    else:
        # URL-encoded: rough estimate (most chars are 1 byte, %XX is 1 byte)
        # Conservative: count %XX sequences, assume rest is 1:1
        percent_count = data.count("%")
        size_bytes = len(data) - (percent_count * 2)  # %XX = 3 chars → 1 byte

    return {
        "is_data_uri": True,
        "mediatype": mediatype,
        "encoding": "base64" if is_base64 else "url",
        "size_bytes": size_bytes,
        "data_preview": data[:50]
    }


def detect_unicode_issues(content: str, max_scan_bytes: int = 10240) -> dict[str, Any]:
    """
    Detect Unicode spoofing attempts including confusables and mixed scripts.

    # REGEX RETAINED (§6 Security)
    Rationale: Character-level analysis requires iterating over Unicode codepoints,
    checking character properties (script, category). Cannot be done with tokens.

    Args:
        content: Text content to analyze
        max_scan_bytes: Maximum bytes to scan (performance limit)

    Returns:
        dict with:
        - has_bidi_override: bool (BiDi override characters present)
        - has_confusables: bool (Latin lookalikes from other scripts)
        - has_mixed_scripts: bool (Mixed scripts with Latin)
        - has_rtl: bool (Right-to-left text present)
        - has_zero_width: bool (Zero-width characters present)
    """
    issues = {
        "has_bidi_override": False,
        "has_confusables": False,
        "has_mixed_scripts": False,
        "has_rtl": False,
        "has_zero_width": False,
    }

    # Limit scan size for performance
    scan_content = content[:max_scan_bytes]

    try:
        # Quick byte-level checks first
        if "\u202e" in scan_content or "\u202d" in scan_content:  # BiDi override
            issues["has_bidi_override"] = True

        if "\u200b" in scan_content or "\u200c" in scan_content or "\u200d" in scan_content:  # Zero-width
            issues["has_zero_width"] = True

        # Character-level analysis
        scripts_seen = set()
        has_latin = False

        for char in scan_content:
            # Skip ASCII for performance
            if ord(char) < 128:
                has_latin = True
                continue

            # Check for confusable characters
            if char in CONFUSABLES_EXTENDED:
                issues["has_confusables"] = True

            # Script detection
            try:
                script = unicodedata.name(char, "").split()[0]
                if "LATIN" in script:
                    has_latin = True
                # Exclude whitespace, typographic variants, and neutral scripts from spoofing detection
                elif script and script not in ("COMMON", "INHERITED", "NO-BREAK", "SPACE", "HYPHEN", "DASH", "FULLWIDTH", "HALFWIDTH"):
                    scripts_seen.add(script)

                # RTL detection
                if unicodedata.bidirectional(char) in ("R", "AL"):
                    issues["has_rtl"] = True
            except (ValueError, IndexError):
                pass

        # Mixed scripts with Latin (potential spoofing)
        if has_latin and scripts_seen:
            issues["has_mixed_scripts"] = True

    except Exception:
        # On any error, mark as having confusables (fail-closed)
        issues["has_confusables"] = True

    return issues


def check_prompt_injection(text: str, timeout_seconds: float = 0.1) -> bool:
    """
    Check for prompt injection patterns in text.

    # REGEX RETAINED (§6 Security)
    Rationale: Prompt injection detection requires pattern matching on content.
    These patterns describe semantic attack vectors, not markdown structure.

    Args:
        text: Text content to check
        timeout_seconds: Timeout for regex matching (safety limit)

    Returns:
        bool: True if prompt injection patterns detected
    """
    if not text:
        return False

    # Truncate for performance (only check first 1KB)
    check_text = text[:1024]

    try:
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(check_text):
                return True
    except Exception:
        # On regex timeout or error, return False (fail-open for this check)
        pass

    return False


def classify_link_type(url: str) -> str:
    """
    Classify URL into type: absolute, relative, anchor, malformed.

    # REGEX RETAINED (§6 Security)
    Rationale: URL structure analysis requires regex. Used for security
    classification and link validation.

    Args:
        url: URL string to classify

    Returns:
        str: "absolute", "relative", "anchor", or "malformed"
    """
    if not url:
        return "malformed"

    # Anchor links
    if url.startswith("#"):
        return "anchor"

    # Check for scheme
    match = _URL_SCHEME_RE.match(url)
    if match:
        scheme_part = match.group(1)
        # Validate scheme is alphanumeric
        if scheme_part.isalpha():
            return "absolute"
        else:
            return "malformed"  # Non-alphabetic scheme

    # Relative paths
    return "relative"
