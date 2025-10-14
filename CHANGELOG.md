# Changelog

All notable changes to Doxstrux will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-10-13

**🏗️ Phase 7: Modular Architecture Complete**

### Changed
- **Core parser reduced by 33%**: From 2900 lines to 1944 lines
- Refactored monolithic parser into 11 specialized extractor modules
- All extractors now use clean dependency injection pattern
- Function-based extractors (no classes) for simplicity and testability

### Added
- **11 specialized extractor modules** in `src/doxstrux/markdown/extractors/`:
  - `lists.py` (305 lines): Regular lists and task lists with nested depth tracking
  - `codeblocks.py` (125 lines): Fenced and indented code blocks
  - `tables.py` (160 lines): GFM tables with alignment validation
  - `links.py` (180 lines): Links with security validation and embedded images
  - `sections.py`: Section and heading extraction
  - `paragraphs.py`: Paragraph extraction
  - `media.py`: Image extraction
  - `footnotes.py`: Footnote extraction
  - `blockquotes.py`: Blockquote extraction
  - `html.py`: HTML block extraction
- Complete extractor pattern documentation in CLAUDE.md
- Phase 7 completion artifact with detailed metrics

### Fixed
- List item structure now correctly uses `{text, children, blocks}` format
- Task checkbox detection fixed (proper parameter passing to `walk_tokens_iter`)
- Tasklist metrics now include `unchecked_count` and `has_mixed_task_items`
- All 542 baseline tests passing (100% byte-for-byte parity)

### Performance
- No performance degradation from modularization
- 14% improvement in median parse time
- Peak memory usage: 0.48MB

### Testing
- ✅ 95/95 pytest tests passing
- ✅ 542/542 baseline tests passing (100% parity)
- ✅ All CI gates passing (parity, performance, no-hybrids, canonical-pairs)
- Test coverage: 69% (new extractor modules need dedicated tests)

## [0.2.0] - 2025-10-12

**🎉 First PyPI Release!**

Available at: https://pypi.org/project/doxstrux/

### Changed
- **BREAKING**: Renamed package from `docpipe` to `doxstrux` for extensibility to PDF/HTML
- All imports changed from `from docpipe.X` to `from doxstrux.X`
- CLI command changed from `docpipe` to `doxstrux`
- Package description updated to emphasize document structure extraction

### Added
- **Published to PyPI**: `pip install doxstrux`
- MIT License file
- PyPI-ready README with badges, installation instructions, and quick start
- This CHANGELOG file
- Phase 7 modularization plan in documentation
- GitHub Actions workflows (CI, PyPI publishing)
- Community files (CONTRIBUTING.md, SECURITY.md)
- Issue and PR templates

### Fixed
- Dead code removed (regex timeout, bleach sanitization, unused methods)
- Test coverage improved to 70%
- Zero-regex architecture completed (Phase 6)

### Documentation
- Updated all documentation to reflect new package name
- Enhanced README with architecture details and security profiles
- Updated CLAUDE.md with current project state

## [0.1.0] - 2024-XX-XX

### Added
- Initial release as `docpipe`
- Markdown parser core with security profiles
- Token-based extraction (zero regex)
- Document IR for RAG chunking
- 63 pytest tests with 70% coverage
- 542 baseline regression tests
- Security-first design with three profiles

---

**Note**: Version 0.1.0 was never published to PyPI. Version 0.2.0 is the first PyPI release under the new name `doxstrux`.
