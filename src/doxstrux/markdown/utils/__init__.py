"""
Doxstrux Utilities Package

Utility modules for common operations.

Modules:
- token_utils: Token traversal and manipulation (walk_tokens_iter, TokenAdapter)
- line_utils: Line slicing and manipulation
- text_utils: Text extraction from tokens
- encoding: Robust encoding detection (detect_and_decode, read_file_robust)

All utilities are stateless functions with clear interfaces.
No dependencies on parser internals.
"""

from .encoding import DecodeResult, detect_and_decode, read_file_robust

__all__ = ["DecodeResult", "detect_and_decode", "read_file_robust"]
