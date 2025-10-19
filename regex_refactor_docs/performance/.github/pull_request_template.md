# Pull Request

## Description
<!-- Brief description of changes -->

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Security hardening

## Checklist

### Required for All PRs
- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] Code follows project style guidelines
- [ ] Documentation updated (if applicable)
- [ ] No new warnings introduced

### Feature/Design Changes (Required)
- [ ] **Decision artifact attached** (use `.github/DECISION_ARTIFACT_TEMPLATE.md`)
  - If this PR introduces a new feature or significant design change, you MUST include a decision artifact
  - Generate using: `python tools/generate_decision_artifact.py --interactive`
  - Attach the completed decision artifact to this PR description
  - All Q1-Q4 questions must be answered with rationale

### Security Changes
- [ ] Security impact assessed
- [ ] Adversarial corpus tests pass (if applicable)
- [ ] No sensitive data exposed

### Performance Changes
- [ ] Benchmarks run and documented
- [ ] Performance metrics within acceptable thresholds (parse_p99_ms <= baseline * 1.5)
- [ ] No regression in critical paths

## Related Issues
<!-- Link to related issues using #issue_number -->

## Testing
<!-- Describe testing performed -->

## Additional Notes
<!-- Any additional context or notes for reviewers -->
