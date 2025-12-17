# INTENTIONALLY INVALID DOCUMENT

# VIOLATION 1: Missing header block
# The required HTML comment header is omitted

# Invalid Document for ai_task_list

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

# - R-ATL-000: If spec and linter diverge, linter MUST ...
# - R-ATL-001: Task list MUST start with YAML front mat...
# - R-ATL-002: Mode semantics: template allows placehol...
# - R-ATL-003: Only `[[PH:NAME]]` placeholders recogniz...
# - R-ATL-010: Task list MUST contain all required head...

---

INVALID_DOCUMENT = True
