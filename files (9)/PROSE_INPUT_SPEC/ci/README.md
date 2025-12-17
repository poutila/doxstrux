# CI Configuration for prose_input

Generated from: PROSE_INPUT_SPEC (v2.0.0)

## Workflows

### lint.yml
Runs the prose_input linter on all Markdown and Python files.

**Triggers:**
- Push to any branch (when .md or .py files change)
- Pull requests (when .md or .py files change)

### drift.yml
Checks for drift between the specification and generated code.

**Triggers:**
- Push to any branch (when spec, mapping, or stubs change)
- Pull requests (when spec, mapping, or stubs change)
- Daily at midnight UTC (scheduled)

## Usage

Copy these files to your repository's `.github/workflows/` directory:

```bash
cp ci/*.yml .github/workflows/
```

## Customization

These files are regenerated when running `speksi re-generate`.
To customize without losing changes:

1. Copy to `.github/workflows/` (outside generated/)
2. Modify as needed
3. The original files in `ci/` serve as reference

## Requirements

- Python 3.11+
- Package must be installable (`pip install -e .`)
- PyYAML for drift detection
