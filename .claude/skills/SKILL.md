---
name: skills
description: Master index of all available code quality and analysis skills. Use to discover specialized skills for governance, security, performance, testing, and code quality checks.
allowed-tools: Bash, Read
---

# Skills Directory

This directory contains 26 specialized skills for code quality analysis, governance enforcement, security auditing, and refactoring validation.

## Available Skills

### Governance & Quality

For **governance-check**, see [governance-check](./governance-check/SKILL.md).

For **governance-report**, see [governance-report](./governance-report/SKILL.md).

For **doc-quality-validator**, see [doc-quality-validator](./doc-quality-validator/SKILL.md).

For **naming-validator**, see [naming-validator](./naming-validator/SKILL.md).

For **type-coverage-enforcer**, see [type-coverage-enforcer](./type-coverage-enforcer/SKILL.md).

### Security

For **security-audit**, see [security-audit](./security-audit/SKILL.md).

For **hardcoding-detector**, see [hardcoding-detector](./hardcoding-detector/SKILL.md).

### Performance

For **performance-hotspots**, see [performance-hotspots](./performance-hotspots/SKILL.md).

### Testing

For **test-gap-analysis**, see [test-gap-analysis](./test-gap-analysis/SKILL.md).

For **weak-test-detector**, see [weak-test-detector](./weak-test-detector/SKILL.md).

### Architecture & Design

For **architecture-map**, see [architecture-map](./architecture-map/SKILL.md).

For **blast-radius**, see [blast-radius](./blast-radius/SKILL.md).

For **drift-detector**, see [drift-detector](./drift-detector/SKILL.md).

For **evaluate-refactor-plan**, see [evaluate-refactor-plan](./evaluate-refactor-plan/SKILL.md).

For **module-purity-check**, see [module-purity-check](./module-purity-check/SKILL.md).

### SOLID Principles

For **solid-lsp-validator**, see [solid-lsp-validator](./solid-lsp-validator/SKILL.md).

For **solid-srp-validator**, see [solid-srp-validator](./solid-srp-validator/SKILL.md).

### Code Patterns

For **error-pattern-audit**, see [error-pattern-audit](./error-pattern-audit/SKILL.md).

For **import-audit**, see [import-audit](./import-audit/SKILL.md).

For **logging-audit**, see [logging-audit](./logging-audit/SKILL.md).

For **magic-number-detector**, see [magic-number-detector](./magic-number-detector/SKILL.md).

For **modern-syntax-validator**, see [modern-syntax-validator](./modern-syntax-validator/SKILL.md).

For **mutable-defaults-detector**, see [mutable-defaults-detector](./mutable-defaults-detector/SKILL.md).

### Fact System

For **magic-power**, see [magic-power](./magic-power/SKILL.md).

For **fact-query**, see [fact-query](./fact-query/SKILL.md).

For **query-pack**, see [query-pack](./query-pack/SKILL.md).

## How to Use

Each skill provides:
- **When to Use This** - Specific scenarios for proactive/reactive usage
- **What It Detects** - Detailed list of checks performed
- **Instructions** - How to invoke the skill
- **Examples** - Concrete usage examples
- **Related Skills** - Cross-references to complementary skills

## Quick Start

1. Choose a skill based on your current task
2. Read the skill's individual documentation
3. Invoke via agent or fact-file-query-tool command
4. Review violations and apply fixes

## Categories

- **Pre-commit Quality Gates**: governance-check, security-audit, performance-hotspots
- **Code Review Tools**: blast-radius, architecture-map, drift-detector
- **Refactoring & Planning**: evaluate-refactor-plan
- **Security Analysis**: security-audit, hardcoding-detector
- **Test Analysis**: test-gap-analysis, weak-test-detector
- **SOLID Compliance**: solid-lsp-validator, solid-srp-validator
- **Pattern Detection**: All detector skills (mutable-defaults, magic-number, etc.)
