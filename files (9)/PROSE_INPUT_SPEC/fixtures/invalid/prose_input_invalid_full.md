# INTENTIONALLY INVALID DOCUMENT

# VIOLATION 1: Missing header block
# The required HTML comment header is omitted

# Invalid Document for prose_input

This document intentionally violates multiple rules.

## wrong section name

This section has wrong naming convention.

## §2 RULES

| Rule ID | Description |
|---------|

# VIOLATION 2: Malformed rule table above

## §3 MISSING INVARIANTS TABLE

# VIOLATION 3: Invariants table is missing

# VIOLATION 4: Section order is wrong (§4 before §3)

# Expected violations:

# - PIN-SSOT-001: This specification is the authoritative ...
# - PIN-SSOT-002: If spec and linter diverge, linter MUST ...
# - PIN-YML-001: Document MUST start with YAML front matt...
# - PIN-YML-002: YAML front matter MUST contain `prose_in...
# - PIN-YML-003: prose_input block MUST contain: schema_v...

---

INVALID_DOCUMENT = True
