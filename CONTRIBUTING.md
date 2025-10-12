# Contributing to Doxstrux

Thank you for your interest in contributing to Doxstrux! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, constructive, and professional in all interactions.

## Development Setup

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup Instructions

```bash
# Clone the repository
git clone https://github.com/doxstrux/doxstrux.git
cd doxstrux

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (with uv)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Testing Requirements

**All contributions must pass these checks:**

### 1. Pytest Suite (63 tests)
```bash
pytest
```

### 2. Baseline Regression Tests (542 tests)
If your changes affect parser behavior:
```bash
cd tools
python baseline_test_runner.py --test-dir test_mds --baseline-dir baseline_outputs
```

### 3. CI Gates (G1-G5)
If your changes affect parser behavior, run all CI gates:
```bash
cd tools/ci
python ci_gate_parity.py        # G1: Baseline parity
python ci_gate_canonical_pairs.py  # G2: Test pairs valid
python ci_gate_no_hybrids.py    # G3: No hybrid patterns
python ci_gate_evidence_hash.py # G4: Evidence integrity
python ci_gate_performance.py   # G5: Performance threshold
```

### 4. Type Checking
```bash
mypy src/doxstrux
```

### 5. Linting
```bash
ruff check src/ tests/
```

## Project Constraints

### Zero-Regex Architecture
- **Do not introduce regex patterns** in the parser
- Use token-based extraction from markdown-it-py AST
- Security patterns (BiDi, confusables) are exceptions

### Security-First Design
- All new features must consider security implications
- Maintain fail-closed approach (reject suspicious content)
- Document security trade-offs

### Test Coverage
- Minimum 80% code coverage required
- Add tests for all new functionality
- Update baseline tests if parser behavior changes

### Performance
- Changes must not regress performance >5%
- Run `ci_gate_performance.py` to verify

## Making Changes

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation only
- `refactor/description` - Code refactoring

### Commit Messages
Follow conventional commits:
```
type(scope): brief description

Longer description if needed.

- Detail 1
- Detail 2
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Pull Request Process

1. **Create a branch** from `main`
2. **Make your changes** with tests
3. **Run all checks** (tests, linting, type checking)
4. **Update documentation** if needed
5. **Update CHANGELOG.md** with your changes
6. **Submit PR** with description

**PR Checklist:**
- [ ] All tests pass
- [ ] Coverage maintained or improved
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Baseline tests pass (if parser changed)
- [ ] CI gates pass (if parser changed)

## Areas for Contribution

### High Priority
- **Test coverage improvements** (current: 70%, target: 80%)
- **Documentation examples** (more real-world use cases)
- **Performance optimizations** (profiling welcome)
- **Bug fixes** (see open issues)

### Medium Priority
- **CLI implementation** (`doxstrux` command)
- **Additional extractors** (more markdown features)
- **Enhanced Document IR** (chunking strategies)

### Future/Experimental
- **PDF support** (structure extraction from PDF)
- **HTML support** (parse HTML with same IR)
- **Semantic chunking** (AI-aware chunking)

## Code Style

### Python Style
- Follow PEP 8
- Line length: 100 characters (configured in ruff)
- Use type hints everywhere
- Docstrings for all public functions/classes

### Testing Style
```python
def test_feature_description():
    """Test that feature does X when Y."""
    # Arrange
    content = "# Test"
    parser = MarkdownParserCore(content)

    # Act
    result = parser.parse()

    # Assert
    assert result["structure"]["headings"][0]["text"] == "Test"
```

## Documentation

### Docstring Format
```python
def function_name(param: str) -> dict[str, Any]:
    """Brief description.

    Longer description if needed.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        SomeError: When condition occurs
    """
```

### README Updates
If adding new features, update:
- README.md (main features section)
- CHANGELOG.md (under "Unreleased")
- Relevant documentation in `CLAUDE.md`

## Release Process

(For maintainers only)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release date
3. Run all tests and CI gates
4. Build package: `python -m build`
5. Check with twine: `twine check dist/*`
6. Upload to TestPyPI first
7. Test installation from TestPyPI
8. Upload to PyPI: `twine upload dist/*`
9. Create GitHub release with tag
10. Update documentation

See `PYPI_RELEASE.md` for detailed steps.

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open an issue with bug report template
- **Features**: Open an issue with feature request template
- **Security**: See SECURITY.md (email security@doxstrux.example.com)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Doxstrux!** 🎉
