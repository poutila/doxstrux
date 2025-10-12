class MarkdownSecurityError(Exception):
    """Raised when content fails security validation."""

    def __init__(self, message: str, security_profile: str, content_info: dict = None):
        super().__init__(message)
        self.security_profile = security_profile
        self.content_info = content_info or {}


class MarkdownSizeError(MarkdownSecurityError):
    """Raised when content exceeds size limits."""

class MarkdownPluginError(MarkdownSecurityError):
    """Raised when plugins are not allowed."""
