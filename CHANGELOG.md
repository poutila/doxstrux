# Changelog

All notable changes to Doxstrux will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-10-12

### Changed
- **BREAKING**: Renamed package from `docpipe` to `doxstrux` for extensibility to PDF/HTML
- All imports changed from `from docpipe.X` to `from doxstrux.X`
- CLI command changed from `docpipe` to `doxstrux`
- Package description updated to emphasize document structure extraction

### Added
- MIT License file
- PyPI-ready README with badges, installation instructions, and quick start
- This CHANGELOG file
- Phase 7 modularization plan in documentation

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

**Note**: Version 0.1.0 was never published to PyPI. Version 0.2.0 will be the first PyPI release under the new name `doxstrux`.
