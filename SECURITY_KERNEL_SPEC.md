# SECURITY_KERNEL_SPEC.md

Version: 0.1.6  
Applies to: doxstrux >= 0.2.2 (target)  
Status: Draft / Implementation-guiding

This document defines the **security kernel** for the doxstrux markdown pipeline:
a minimal set of invariants, components, and behaviours that all security-relevant
logic MUST obey.

The goal is to make the security behaviour:

- Understandable  
- Testable  
- Non-drifting  
- Fail-closed

Everything in this spec is *normative* unless explicitly marked as “Implementation note”.

> Compatibility note (0.2.1 → 0.2.2)  
> As of version 0.2.1, some APIs and configuration shapes differ from this spec
> (e.g. `check_prompt_injection(text, timeout_seconds=0.1) -> bool`). Adopting
> this spec for 0.2.2 requires:  
> - introducing a new structured `check_prompt_injection(..., profile=...)` API, and  
> - adding `max_injection_scan_chars` to `SECURITY_PROFILES`.  
>  
> Version 0.2.2 MUST either:  
> - keep the old API as a thin shim (backwards-compatible deprecation), or  
> - document the breaking change clearly in the changelog and release notes.

---

## 1. Scope & Responsibilities

The security kernel governs:

1. **Path traversal protection**  
   Detecting filesystem/path traversal patterns in links and other text fragments.

2. **Prompt injection detection**  
   Detecting obvious prompt-injection style content in markdown (for LLM use).

3. **Budget limits**  
   Enforcing limits on dangerous content vectors such as:
   - Data URIs
   - Length of text scanned by injection detectors

4. **Error semantics for security checks**  
   Ensuring there are no silent failures in security code paths and that
   security checks fail-closed.

Out of scope for this spec:

- General markdown parsing correctness  
- Business-level policy around “block vs warn” decisions for documents found dangerous  
- Network-level or OS-level sandboxing

---

## 2. Terminology

- **Security profile**: Named configuration bundle controlling security behaviour.  
  Current profiles: `strict`, `moderate`, `permissive`.

- **Fail-closed**: If a security check cannot complete due to an *internal error*
  (e.g. runtime exception), the result MUST be treated as “suspicious” rather
  than “safe”.

- **Benign URL**: A normal HTTP(S) URL or similar (e.g. `mailto:`) that does not
  contain path traversal segments or obviously sensitive paths.

- **Path traversal**: Any path that attempts to escape an allowed directory via
  `..` segments or absolute paths into sensitive locations (e.g. `/etc/passwd`).

- **Prompt injection**: Patterns intended to override previous instructions, cause
  the LLM to exfiltrate data, or perform actions outside the intended task.

- **Budget**: A configurable numerical limit that caps a security-relevant resource
  (e.g. max data URI size, max characters inspected for injection).

---

## 3. Global Security Invariants

The security kernel MUST enforce the following invariants.

### INV-SEC-1 — No Silent Security Failures

Security checks MUST NOT use bare `except Exception: pass`, nor swallow exceptions
without recording them.

If a security component encounters an unexpected error:

- It MUST either:
  - Raise a well-defined domain exception; or
  - Return a structured result flagging the content as **suspicious** and include
    the error detail.

There MUST be **no** code path where security logic fails and the document is
still treated as “clean” without any signal.

---

### INV-SEC-2 — Fail-Closed Behaviour

If a security check cannot be confidently completed due to an internal error
(e.g. regex engine failure, config error, unsupported profile name):

- The document, link, or fragment under inspection MUST be treated as
  **potentially dangerous**, not clean.
- The reason MUST be recorded (log / warning / “reason” field).

Under no circumstances may an internal security error cause the result to default
to “safe”.

> Implementation note: budget-based truncation (e.g. only scanning the first N
> characters by design) is NOT considered an internal error and MAY result in
> `suspected=False` if no pattern is found in the scanned portion.

---

### INV-SEC-3 — No Global False Positives on Benign Content

The kernel MUST NOT flag **all** normal URLs as path traversal or prompt injection
by construction.

Specifically, the following examples MUST normally be treated as
**non-traversal** and **non-injection** (unless other patterns apply):

- `https://example.com`  
- `https://example.com/path`  
- `http://example.com/foo/bar`  
- `mailto:user@example.com`  
- `tel:+3581234567`

Patterns such as `//` MUST NOT be used as standalone indicators of path
traversal.

Local false positives MAY still occur on ambiguous sentences; the invariant is
that benign content is not systematically or globally treated as dangerous.

URLs whose path contains traversal segments (e.g. `https://example.com/../../etc/passwd`)
MUST be treated as **suspicious** and flagged by the path traversal guard.

---

### INV-SEC-4 — Single Source of Truth for Security Budgets

For each security profile, all budget-like values (e.g. `max_data_uri_size`,
`max_injection_scan_chars`) MUST be defined in a single canonical configuration
structure (e.g. `SECURITY_PROFILES` in `config.py`).

No other module may redefine these values in an independent dictionary.

Consumption of these budgets from other modules (e.g. `budgets.py`,
`validators.py`) MUST read from this central configuration.

---

### INV-SEC-5 — Deterministic, Structured Results

Security checks MUST return deterministic, structured results, such as:

- A boolean + reason code; or  
- A typed dataclass/struct with fields: `suspected`, `reason`, `pattern`,
  `error`, etc.

Loose string messages alone are NOT sufficient as the primary API. There MUST be
a machine-consumable structure that callers can assert on in tests.

> Implementation note: the `error` field is primarily for internal diagnostics
> and does not need to be serializable. For any user-facing or serialized
> representation, implementations SHOULD also expose an `error_message: Optional[str]`
> derived from the exception.

---

## 4. Module Layout

For the purposes of this spec, the **security kernel** is defined to live in:

- `doxstrux.markdown_parser_core`  
  Path traversal guard and security-related validations tied to parsing.

- `doxstrux.markdown.config`  
  Security profiles and budgets (via `SECURITY_PROFILES`).

- `doxstrux.markdown.budgets`  
  Helper accessors for budgets.

- `doxstrux.markdown.security.validators`  
  Prompt injection and related validators.

Any security-critical logic added later SHOULD be placed under these modules or
explicitly referenced from this spec.

> Implementation note: if you later re-export these symbols from
> `doxstrux.markdown` or move them into a dedicated `security` package, update
> this section and the tests accordingly.

---

## 5. Security Profiles

The kernel defines three profiles:

- `strict`  
- `moderate`  
- `permissive`

Each profile **MUST** be defined in a central configuration mapping, for example:

```python
SECURITY_PROFILES = {
    "strict": {
        "max_data_uri_size": <int>,
        "max_injection_scan_chars": <int>,
        # ... other strict-profile options
    },
    "moderate": {
        "max_data_uri_size": <int>,
        "max_injection_scan_chars": <int>,
        # ... other moderate-profile options
    },
    "permissive": {
        "max_data_uri_size": <int>,
        "max_injection_scan_chars": <int>,
        # ... other permissive-profile options
    },
}
```

### PROF-1 — Profile Resolution

- Any user-facing configuration that refers to a `security_profile` MUST validate
  that the profile name exists in `SECURITY_PROFILES`.
- Unknown profiles MUST cause a **hard failure** (exception) at configuration
  time or at the point of use (e.g. in validators).

### PROF-2 — Data URI Budgets

- `max_data_uri_size` is the maximum size (in bytes or characters, as defined)
  of data URI content that the parser will accept.
- If a data URI exceeds this budget:
  - The behaviour SHOULD be clearly defined per profile (e.g. reject vs warn).
  - The decision SHOULD be testable and consistent.

> Implementation note: For v0.2.2, data URI budget enforcement is deferred.
> The budget values exist in SECURITY_PROFILES for future use, but the
> "what happens when exceeded" behavior is not yet specified or tested.
> Priority is on prompt injection and path traversal invariants.

### PROF-3 — Injection Scan Budgets

- `max_injection_scan_chars` defines how many characters of a string are inspected
  by the prompt injection detector for that profile.
- Truncation MUST be implemented via this value—no hard-coded magic numbers in
  the validator.

> Recommended defaults (implementations MAY adjust):  
>
> | Profile       | max_injection_scan_chars |
> |--------------|---------------------------|
> | `strict`     | 4096                      |
> | `moderate`   | 2048                      |
> | `permissive` | 1024                      |

---

## 6. Path Traversal Protection

### 6.1 Interface

The path traversal guard MUST expose a stable internal API, for example:

```python
def check_path_traversal(target: str) -> bool:
    """
    Return True if `target` appears to contain a path traversal attempt,
    False otherwise.
    """
```

The exact name and placement MAY differ (e.g. a private method
`MarkdownParserCore._check_path_traversal(self, target: str) -> bool`), but
callers MUST be able to obtain an equivalent function:

```python
def path_traversal_guard(target: str) -> bool:
    ...
```

that implements this behaviour.

Path traversal detection MUST be **profile-independent**: whether a path is
considered traversal MUST NOT depend on `security_profile` or other runtime
configuration.

### 6.2 Behaviour

The guard MUST:

1. Parse URLs using a standard URL parser where appropriate (e.g. `urlparse`).
2. For benign schemes (`http`, `https`, `mailto`, `tel`):
   - Only inspect the **path** component, not the full raw string (scheme, host,
     fragment are irrelevant for traversal).
   - Query string inspection is OPTIONAL; implementations MAY choose to inspect
     query parameters for traversal patterns but this is not required.
3. Normalize slashes (`\` to `/`) before inspection.
4. Flag traversal when:
   - The normalized path segments contain `..` (e.g. `../` or `/../`); or
   - The string matches a Windows absolute path pattern (`C:\...`); or
   - The string matches a Windows UNC path (e.g. `\\server\share\...`).

> Implementation note: Detecting "absolute sensitive paths" (e.g. `/etc/passwd`
> without `..`) is NOT required by this spec. Such detection is prone to false
> positives and platform-specific. Implementations MAY add this as an optional
> strictness level but it is not part of the core invariants.

Implementations SHOULD also decode typical URL-encoded traversal segments
(e.g. `%2e%2e` for `..`). If the decoded path contains traversal segments, it
MUST be treated as suspicious.

**Fail-closed on internal error**: If the guard encounters an internal error
(e.g. URL parser failure, encoding exception), implementations MUST either
raise a domain error or treat the value as suspicious (return `True`).
Returning `False` (safe) in this scenario is forbidden by INV-SEC-2.

### 6.3 Non-Goals

The guard MUST NOT:

- Treat `https://` or `http://` as path traversal by itself.  
- Treat `//` as sufficient evidence of traversal.  
- Attempt to fully normalize arbitrary file systems (this is a heuristic, not a
  complete VFS).

### 6.4 Test Obligations

There MUST be tests asserting that:

- Normal URLs are not flagged as traversal.  
- Obvious traversal patterns (`../../etc/passwd`, `/../../etc/shadow`,
  Windows absolute paths, UNC paths, etc.) are flagged.  
- URLs with traversal segments in the path (e.g. `https://example.com/../../etc/passwd`)
  are treated as **suspicious** and flagged as traversal.  
- URL-encoded traversal segments (e.g. `https://example.com/%2e%2e/%2e%2e/etc/passwd`)
  are flagged as traversal.

---

## 7. Prompt Injection Detection

### 7.1 Interface

The prompt injection detector MUST expose a structured result, for example:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class PromptInjectionCheck:
    suspected: bool           # True if injection-like content or error
    reason: str               # 'pattern_match', 'no_match', 'validator_error', 'truncated', ...
    pattern: Optional[str]    # The regex pattern that matched (if any)
    error: Optional[Exception] = None
```

and a function:

```python
def check_prompt_injection(text: str, profile: str = "strict") -> PromptInjectionCheck:
    ...
```

Calling `check_prompt_injection(text)` with no `profile` argument MUST behave
identically to `check_prompt_injection(text, profile="strict")`.

> Compatibility note: previously `check_prompt_injection(text, timeout_seconds=0.1) -> bool`
> existed. Implementations MAY keep that as a thin wrapper around the new API for
> backwards compatibility.

### 7.2 Behaviour

Given `text` and `profile`:

1. Resolve `profile` via `SECURITY_PROFILES[profile]`.  
   - Unknown profiles MUST result in a hard failure (exception).
2. Determine `max_len = SECURITY_PROFILES[profile]["max_injection_scan_chars"]`.  
3. Compute `check_text = text[:max_len]`.  
4. For each pattern in `PROMPT_INJECTION_PATTERNS`:
   - If the pattern matches `check_text`, return:

     ```python
     PromptInjectionCheck(
         suspected=True,
         reason="pattern_match",
         pattern=<pattern.pattern>,
         error=None,
     )
     ```

5. If no patterns match, return:

   ```python
   PromptInjectionCheck(
       suspected=False,
       reason="no_match",
       pattern=None,
       error=None,
   )
   ```

6. If any unexpected error occurs during pattern evaluation:
   - Catch the error and return:

     ```python
     PromptInjectionCheck(
         suspected=True,
         reason="validator_error",
         pattern=None,
         error=<exc>,
     )
     ```

   - This satisfies **fail-closed** behaviour.

### 7.3 Truncation Semantics

- Truncation is **mandatory** and must be derived from
  `max_injection_scan_chars`.  
- For `strict`, `moderate`, `permissive`, the values MAY differ but MUST be
  explicitly documented in the config.  
- If an injection-like pattern would appear **only after** the truncation point
  (i.e. beyond `max_injection_scan_chars`), the detector MUST NOT claim it was
  detected. In that case, the result MUST be:

  ```python
  PromptInjectionCheck(
      suspected=False,
      reason="no_match",
      pattern=None,
      error=None,
  )
  ```

### 7.4 Test Obligations

There MUST be tests asserting that:

- Normal text (no injection-like phrasing) yields `suspected=False`,
  `reason="no_match"`.  
- Representative injection-like text yields `suspected=True`,
  `reason="pattern_match"`, and a **non-empty** `pattern` string.  
- Synthetic failures (e.g. forcing a pattern's `search` method to throw) yield
  `suspected=True`, `reason="validator_error"`, and the error is present.  
- Passing an unknown profile name to `check_prompt_injection` raises a clear
  exception (e.g. `ValueError` or domain error).  
- Patterns placed entirely beyond `max_injection_scan_chars` are not detected
  and yield `suspected=False`, `reason="no_match"`.

---

## 8. Budget & Config Integration

### 8.1 Canonical Config

All security budgets MUST be defined in a single canonical mapping, such as
`SECURITY_PROFILES` in `config.py`.

Values include (at minimum):

- `max_data_uri_size`  
- `max_injection_scan_chars`

### 8.2 Accessors

Other modules (e.g. `budgets.py`, `validators.py`) MUST NOT re-declare their
own copies of these maps.

Instead, they MUST access budgets via thin helpers that delegate to
`SECURITY_PROFILES`, for example:

```python
def get_max_data_uri_size(profile: str) -> int:
    ...

def get_max_injection_scan_chars(profile: str) -> int:
    ...
```

These helpers MUST raise a clear error on unknown profile.

### 8.3 Test Obligations

There MUST be tests verifying that:

- Each helper returns the same value as the underlying `SECURITY_PROFILES`.  
- Unknown profiles raise a well-defined exception.

---

## 9. Error Handling & Observability

### 9.1 No Bare Exception Swallowing

Within the security kernel:

- Bare `except Exception:` with `pass` is forbidden.  
- Any exception handler MUST either:
  - Re-raise as a domain error, or  
  - Return a structured “error” result (e.g. `PromptInjectionCheck` with
    `reason="validator_error"`).

### 9.2 Diagnostics

Security components SHOULD record structured diagnostics, including:

- Component name (`"path_traversal"`, `"prompt_injection"`, etc.)
- Reason (`"pattern_match"`, `"validator_error"`, `"truncated"`, etc.)
- Pattern (if applicable)
- Error representation (if applicable)

How these diagnostics are surfaced (logs, warnings array, etc.) is an
implementation detail and SHOULD be unit-testable where practical.

> Implementation note: For v0.2.2, diagnostics are considered a SHOULD, not a
> gate. The core invariants (fail-closed, no silent failures, structured results)
> take priority. Diagnostics infrastructure may be added in a future release.

---

## 10. Test Coverage & Evidence

The security kernel MUST be covered by automated tests that:

1. Exercise:
   - All profiles (`strict`, `moderate`, `permissive`)  
   - Success paths (benign content)  
   - Detection paths (malicious content)  
   - Error paths (forced internal failures)

2. Assert:
   - No silent failures  
   - Fail-closed behaviour  
   - No global false positives on benign URLs

3. Are run as part of the standard CI pipeline (e.g. `pytest`).

Optional but recommended:

- A small “security regression” suite that feeds known-bad payloads and verifies
  stable detection behaviour across versions.

---

## 11. Drift Detection

Any future change to:

- `SECURITY_PROFILES`  
- Path traversal detection logic  
- Prompt injection patterns or budgets

MUST update:

- This spec (if behaviour changes), and  
- The corresponding tests

The presence of:

- New hard-coded budget numbers, or  
- New `except Exception: pass`

in security-related modules MUST be treated as a **drift** from this spec and
blocked at review/CI.
