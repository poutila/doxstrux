"""Robust encoding detection and decoding utilities.

This module provides encoding detection using charset-normalizer with
BOM detection, confidence thresholds, and sanity checks.

Functions:
    detect_and_decode: Detect encoding and decode bytes to string
    read_file_robust: Read a file with automatic encoding detection
"""

import codecs
import unicodedata
from pathlib import Path
from typing import NamedTuple

from charset_normalizer import from_bytes


class DecodeResult(NamedTuple):
    """Result of encoding detection and decoding."""

    text: str
    encoding: str
    confidence: float


# BOM signatures and their encodings
_BOM_ENCODINGS = [
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16-le"),
    (codecs.BOM_UTF16_BE, "utf-16-be"),
    (codecs.BOM_UTF32_LE, "utf-32-le"),
    (codecs.BOM_UTF32_BE, "utf-32-be"),
]

# Preferred encodings for fallback (in order of preference)
PREFERRED_ENCODINGS = ["utf-8", "cp1252", "latin-1"]


def _looks_reasonable(text: str, max_replacement_ratio: float = 0.01) -> bool:
    """Check if decoded text looks reasonable (not garbled).

    Args:
        text: Decoded text to validate
        max_replacement_ratio: Maximum allowed ratio of replacement characters

    Returns:
        True if text passes sanity checks
    """
    if not text:
        return True

    # Check for too many replacement characters (U+FFFD)
    repl_count = text.count("\ufffd")
    if repl_count / len(text) > max_replacement_ratio:
        return False

    # Check for too many control characters (excluding tab, newline, carriage return)
    control_chars = sum(
        1
        for ch in text
        if unicodedata.category(ch) in ("Cc", "Cs") and ch not in "\t\n\r"
    )
    if control_chars > len(text) * 0.02:
        return False

    return True


def detect_and_decode(
    data: bytes,
    default: str = "utf-8",
    confidence_threshold: float = 0.2,
) -> DecodeResult:
    """Detect encoding from bytes and decode to string.

    Detection order:
    1. BOM (Byte Order Mark) - highest confidence
    2. charset-normalizer auto-detection
    3. UTF-8 trial decode
    4. Fallback to latin-1 (never fails)

    Args:
        data: Raw bytes to decode
        default: Default encoding if detection fails
        confidence_threshold: Minimum confidence to trust detection

    Returns:
        DecodeResult with text, detected encoding, and confidence score
    """
    # 1. Check for BOM first (highest confidence)
    for bom, encoding in _BOM_ENCODINGS:
        if data.startswith(bom):
            try:
                text = data.decode(encoding)
                if _looks_reasonable(text):
                    return DecodeResult(text, encoding, 1.0)
            except UnicodeDecodeError:
                pass

    # 2. Use charset-normalizer for auto-detection
    result = from_bytes(data)
    best = result.best()

    if best is not None:
        encoding = best.encoding
        confidence = best.coherence  # coherence score 0-1

        if confidence >= confidence_threshold:
            text = str(best)
            if _looks_reasonable(text):
                return DecodeResult(text, encoding, confidence)

    # 3. Try UTF-8 explicitly (most common modern encoding)
    try:
        text = data.decode("utf-8")
        if _looks_reasonable(text):
            return DecodeResult(text, "utf-8", 0.9)
    except UnicodeDecodeError:
        pass

    # 4. Try other preferred encodings
    for encoding in PREFERRED_ENCODINGS[1:]:  # Skip utf-8, already tried
        try:
            text = data.decode(encoding)
            if _looks_reasonable(text):
                return DecodeResult(text, encoding, 0.5)
        except UnicodeDecodeError:
            pass

    # 5. Last resort: latin-1 never fails (1:1 byte mapping)
    text = data.decode("latin-1")
    return DecodeResult(text, "latin-1", 0.0)


def read_file_robust(
    path: Path | str,
    default: str = "utf-8",
    confidence_threshold: float = 0.2,
) -> DecodeResult:
    """Read a file with automatic encoding detection.

    Args:
        path: Path to the file
        default: Default encoding if detection fails
        confidence_threshold: Minimum confidence to trust detection

    Returns:
        DecodeResult with file content, detected encoding, and confidence

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    path = Path(path)
    data = path.read_bytes()
    return detect_and_decode(data, default, confidence_threshold)
