"""
Doxstrux Security Package

Security validation and policy enforcement modules.

Modules:
- validators: Content validation functions (URL schemes, BiDi, confusables)
- policies: Security policy application (fail-closed approach)
- unicode: Unicode security (BiDi controls, confusable characters)

Security is layered throughout:
- Content size limits
- Recursion depth limits
- Link scheme validation
- HTML sanitization
- Script/event handler detection
- BiDi control detection
- Confusable character detection
"""
