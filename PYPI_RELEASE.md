# PyPI Release Instructions for Doxstrux

**Version**: 0.2.0
**Status**: ✅ Ready for PyPI Upload
**Date**: 2025-10-12

---

## Pre-Release Checklist

### ✅ Completed

- [x] Package renamed from `docpipe` to `doxstrux`
- [x] Dependencies cleaned (removed ptool, openai, anthropic, etc.)
- [x] Core dependencies: `markdown-it-py`, `mdit-py-plugins`, `pyyaml` only
- [x] LICENSE file created (MIT)
- [x] README.md PyPI-ready (badges, installation, quick start)
- [x] CHANGELOG.md created
- [x] pyproject.toml configured for PyPI
- [x] CLI entry point commented out (not implemented yet)
- [x] All tests passing (63/63 pytest, 542/542 baselines)
- [x] All CI gates passing (G1-G5)
- [x] Package builds successfully
- [x] Twine check passes
- [x] Test installation in clean venv works

---

## Build Status

### Package Build
```bash
✓ Built: doxstrux-0.2.0-py3-none-any.whl (44KB)
✓ Built: doxstrux-0.2.0.tar.gz (52KB)
✓ Twine check: PASSED (both wheel and sdist)
✓ Test install: PASSED (imports work, parser works)
```

### Dependencies Installed
```
✓ markdown-it-py-4.0.0
✓ mdit-py-plugins-0.5.0
✓ pyyaml-6.0.3
✓ mdurl-0.1.2 (transitive)
```

---

## PyPI Upload Instructions

### 1. Setup PyPI Account

**First time only:**

1. Create account at https://pypi.org/account/register/
2. Verify email address
3. Enable 2FA (required for new uploads)
4. Create API token at https://pypi.org/manage/account/token/
   - Token name: `doxstrux-upload`
   - Scope: Select "Entire account" or create after first upload
5. Save token to `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-AgENdGVzdC...  # Your token here
```

**Permissions:**
```bash
chmod 600 ~/.pypirc
```

### 2. Test Upload (TestPyPI - RECOMMENDED)

**Upload to TestPyPI first:**

```bash
# Build fresh packages
rm -rf dist/
uv run python -m build

# Upload to TestPyPI
uv run twine upload --repository testpypi dist/*
```

**Test installation from TestPyPI:**

```bash
# Create clean test environment
python3 -m venv /tmp/test_testpypi
source /tmp/test_testpypi/bin/activate

# Install from TestPyPI (with deps from real PyPI)
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    doxstrux

# Test it works
python -c "from doxstrux.markdown_parser_core import MarkdownParserCore; \
    parser = MarkdownParserCore('# Test'); \
    print('✓ TestPyPI install works')"

deactivate
```

### 3. Production Upload (Real PyPI)

**When TestPyPI looks good:**

```bash
# Upload to real PyPI
uv run twine upload dist/*
```

**Expected output:**
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading doxstrux-0.2.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.2/45.2 kB • 00:00
Uploading doxstrux-0.2.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 52.4/52.4 kB • 00:00

View at:
https://pypi.org/project/doxstrux/0.2.0/
```

### 4. Verify Upload

**Check PyPI page:**
- https://pypi.org/project/doxstrux/

**Test installation:**

```bash
# Create clean environment
python3 -m venv /tmp/test_real_pypi
source /tmp/test_real_pypi/bin/activate

# Install from PyPI
pip install doxstrux

# Test it works
python -c "from doxstrux.markdown_parser_core import MarkdownParserCore; \
    parser = MarkdownParserCore('# Hello\n\nWorld **bold**'); \
    result = parser.parse(); \
    print(f'✓ PyPI install works: {len(result[\"structure\"][\"headings\"])} headings')"

deactivate
```

---

## Post-Release Steps

### 5. Tag and Push Git

```bash
# Tag the release
git tag -a v0.2.0 -m "Release v0.2.0: First PyPI release as doxstrux"

# Push to remote
git push origin main
git push origin v0.2.0
```

### 6. Create GitHub Release

1. Go to https://github.com/doxstrux/doxstrux/releases/new
2. Choose tag: `v0.2.0`
3. Release title: `v0.2.0 - First PyPI Release`
4. Description:

```markdown
# Doxstrux v0.2.0 🎉

First PyPI release! Package renamed from `docpipe` to `doxstrux` for extensibility to PDF and HTML.

## Installation

```bash
pip install doxstrux
```

## What's New

- **Package renamed** from `docpipe` to `doxstrux`
- **Zero-regex architecture** completed (Phase 6)
- **Minimal dependencies**: Only markdown-it-py, mdit-py-plugins, pyyaml
- **Security-first design**: Three security profiles (strict/moderate/permissive)
- **Document IR**: Clean intermediate representation for RAG chunking
- **63 tests** passing with 70% coverage
- **542 baseline tests** maintaining byte-for-byte parity

## Quick Start

```python
from doxstrux.markdown_parser_core import MarkdownParserCore

parser = MarkdownParserCore("# Hello\n\nWorld!")
result = parser.parse()
print(result['structure']['headings'])
```

See [README.md](https://github.com/doxstrux/doxstrux/blob/main/README.md) for complete documentation.
```

5. Attach `dist/` files (optional)
6. Publish release

### 7. Update Documentation

- Update README.md badges if needed
- Announce on relevant channels
- Update any external documentation

---

## Troubleshooting

### Build Issues

**Error: "No module named build"**
```bash
uv add --dev build
```

**Error: "ptool not found"**
- Fixed in pyproject.toml (commented out)
- Rebuild: `rm -rf dist/ && uv run python -m build`

### Upload Issues

**Error: "403 Forbidden"**
- Check API token is correct in `~/.pypirc`
- Ensure 2FA is enabled on PyPI account

**Error: "400 Bad Request: Invalid distribution"**
- Run `uv run twine check dist/*` first
- Check metadata in pyproject.toml

**Error: "File already exists"**
- Cannot re-upload same version
- Bump version in pyproject.toml
- Rebuild and upload

### Installation Issues

**Import errors after install**
- Check dependencies installed: `pip list`
- Verify Python version >= 3.12

---

## Version Bumping

**For future releases:**

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.3.0"  # or whatever
   ```

2. Update `CHANGELOG.md` with changes

3. Rebuild:
   ```bash
   rm -rf dist/ build/ src/*.egg-info
   uv run python -m build
   ```

4. Follow upload steps above

---

## Commands Quick Reference

```bash
# Build package
rm -rf dist/ && uv run python -m build

# Check with twine
uv run twine check dist/*

# Upload to TestPyPI
uv run twine upload --repository testpypi dist/*

# Upload to PyPI
uv run twine upload dist/*

# Test install
pip install doxstrux

# Test import
python -c "from doxstrux.markdown_parser_core import MarkdownParserCore; print('✓')"
```

---

## Current Status

**Ready for upload**: ✅ YES

**Pre-upload verification:**
- ✅ All tests pass (63/63 pytest, 542/542 baselines)
- ✅ All CI gates pass (G1-G5)
- ✅ Twine check passes
- ✅ Test installation works
- ✅ Dependencies minimal and correct
- ✅ Documentation complete

**Next step**: Upload to TestPyPI first, verify, then upload to real PyPI.

---

**Last Updated**: 2025-10-12
**Maintainer**: Doxstrux Team
