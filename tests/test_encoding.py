"""Tests for robust encoding detection utilities."""

import codecs
import tempfile
from pathlib import Path

import pytest
from doxstrux.markdown.utils.encoding import (
    DecodeResult,
    detect_and_decode,
    read_file_robust,
    _looks_reasonable,
)


class TestLooksReasonable:
    """Tests for _looks_reasonable() sanity check."""

    def test_empty_text_is_reasonable(self):
        """Empty text should pass."""
        assert _looks_reasonable("") is True

    def test_normal_text_is_reasonable(self):
        """Normal text should pass."""
        assert _looks_reasonable("Hello, world!") is True
        assert _looks_reasonable("Line 1\nLine 2\nLine 3") is True
        assert _looks_reasonable("Tab\there\tand\tthere") is True

    def test_unicode_text_is_reasonable(self):
        """Unicode text should pass."""
        assert _looks_reasonable("Héllo wörld") is True
        assert _looks_reasonable("日本語テキスト") is True
        assert _looks_reasonable("Emoji: 🎉🚀") is True

    def test_too_many_replacement_chars_fails(self):
        """Text with >1% replacement characters should fail."""
        # 100 chars with 2 replacement chars = 2% > 1%
        text = "a" * 98 + "\ufffd\ufffd"
        assert _looks_reasonable(text) is False

    def test_few_replacement_chars_passes(self):
        """Text with <1% replacement characters should pass."""
        # 200 chars with 1 replacement char = 0.5% < 1%
        text = "a" * 199 + "\ufffd"
        assert _looks_reasonable(text) is True

    def test_too_many_control_chars_fails(self):
        """Text with >2% control characters should fail."""
        # 100 chars with 3 control chars = 3% > 2%
        text = "a" * 97 + "\x00\x01\x02"
        assert _looks_reasonable(text) is False

    def test_allowed_control_chars_pass(self):
        """Tab, newline, carriage return should not count as control chars."""
        text = "Line1\n\tIndented\r\nLine3"
        assert _looks_reasonable(text) is True


class TestDetectAndDecode:
    """Tests for detect_and_decode() function."""

    def test_utf8_without_bom(self):
        """UTF-8 without BOM should be detected."""
        data = "Hello, world!".encode("utf-8")
        result = detect_and_decode(data)
        assert result.text == "Hello, world!"
        assert result.confidence > 0

    def test_utf8_with_bom(self):
        """UTF-8 with BOM should be detected with confidence 1.0."""
        data = codecs.BOM_UTF8 + "Hello, world!".encode("utf-8")
        result = detect_and_decode(data)
        # utf-8-sig strips the BOM during decoding
        assert result.text == "Hello, world!"
        assert result.encoding == "utf-8-sig"
        assert result.confidence == 1.0

    def test_utf16_le_with_bom(self):
        """UTF-16 LE with BOM should be detected."""
        text = "Hello"
        data = codecs.BOM_UTF16_LE + text.encode("utf-16-le")
        result = detect_and_decode(data)
        assert "Hello" in result.text
        assert result.encoding == "utf-16-le"
        assert result.confidence == 1.0

    def test_utf16_be_with_bom(self):
        """UTF-16 BE with BOM should be detected."""
        text = "Hello"
        data = codecs.BOM_UTF16_BE + text.encode("utf-16-be")
        result = detect_and_decode(data)
        assert "Hello" in result.text
        assert result.encoding == "utf-16-be"
        assert result.confidence == 1.0

    def test_latin1_text(self):
        """Latin-1 specific characters should be handled."""
        # café encoded in latin-1
        data = b"caf\xe9"
        result = detect_and_decode(data)
        assert "caf" in result.text
        # Should decode successfully (either as latin-1 or cp1252)
        assert result.confidence >= 0

    def test_empty_bytes(self):
        """Empty bytes should return empty string."""
        result = detect_and_decode(b"")
        assert result.text == ""

    def test_pure_ascii(self):
        """Pure ASCII should be detected as UTF-8 compatible."""
        data = b"Just ASCII text 12345"
        result = detect_and_decode(data)
        assert result.text == "Just ASCII text 12345"

    def test_confidence_threshold_respected(self):
        """Low confidence results should fall through to UTF-8 trial."""
        # Simple ASCII will have high confidence anyway
        data = b"test"
        result = detect_and_decode(data, confidence_threshold=0.99)
        assert result.text == "test"

    def test_returns_decode_result_namedtuple(self):
        """Result should be a DecodeResult namedtuple."""
        result = detect_and_decode(b"test")
        assert isinstance(result, DecodeResult)
        assert hasattr(result, "text")
        assert hasattr(result, "encoding")
        assert hasattr(result, "confidence")


class TestReadFileRobust:
    """Tests for read_file_robust() function."""

    def test_read_utf8_file(self):
        """Should read UTF-8 file correctly."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".md", delete=False) as f:
            f.write("# Hello\n\nWorld".encode("utf-8"))
            path = f.name

        try:
            result = read_file_robust(path)
            assert result.text == "# Hello\n\nWorld"
            assert result.confidence > 0
        finally:
            Path(path).unlink()

    def test_read_utf8_bom_file(self):
        """Should read UTF-8 BOM file correctly."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".md", delete=False) as f:
            f.write(codecs.BOM_UTF8 + "Content".encode("utf-8"))
            path = f.name

        try:
            result = read_file_robust(path)
            assert "Content" in result.text
            assert result.encoding == "utf-8-sig"
            assert result.confidence == 1.0
        finally:
            Path(path).unlink()

    def test_read_nonexistent_file_raises(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            read_file_robust("/nonexistent/path/file.md")

    def test_accepts_path_object(self):
        """Should accept Path objects."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".md", delete=False) as f:
            f.write(b"test")
            path = Path(f.name)

        try:
            result = read_file_robust(path)
            assert result.text == "test"
        finally:
            path.unlink()

    def test_accepts_string_path(self):
        """Should accept string paths."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".md", delete=False) as f:
            f.write(b"test")
            path = f.name

        try:
            result = read_file_robust(path)
            assert result.text == "test"
        finally:
            Path(path).unlink()


class TestIntegrationWithRealFiles:
    """Integration tests with actual test files."""

    def test_mixed_encoding_files(self):
        """Test against mixed encoding test files if they exist."""
        test_dir = Path("tools/test_mds/04_stress_encoding")
        if not test_dir.exists():
            pytest.skip("Test directory not found")

        # Just verify we can read all files without error
        for md_file in test_dir.glob("*.md"):
            result = read_file_robust(md_file)
            assert isinstance(result.text, str)
            assert result.encoding is not None
            assert 0 <= result.confidence <= 1.0
