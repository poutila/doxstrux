"""Security validators for URLs, HTML, and content.

DEPRECATED: URL normalization has been moved to utils/url_utils.py

This module is kept for backward compatibility but all normalize_url
functionality is now in the canonical location:

    from ..utils.url_utils import normalize_url

Per CLOSING_IMPLEMENTATION.md P0-1: Single source of truth for URL normalization.
"""

# Import canonical implementation
from ..utils.url_utils import normalize_url, ALLOWED_SCHEMES

# Re-export for backward compatibility
__all__ = ['normalize_url', 'ALLOWED_SCHEMES']

# Note: security/validators.py previously contained a different signature:
# normalize_url(url) -> Tuple[Optional[str], bool]
#
# The new canonical signature in utils/url_utils.py is:
# normalize_url(url) -> Optional[str]
#
# This returns the normalized URL directly (or None if rejected).
# This is simpler and follows KISS principle.
