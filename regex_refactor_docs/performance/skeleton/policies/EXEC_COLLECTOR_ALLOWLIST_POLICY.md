# Collector Allowlist & Package Signing Policy

**Version**: 1.0
**Date**: 2025-10-17
**Status**: YAGNI-gated (implements only if subprocess isolation deployed)
**Scope**: Subprocess-isolated collector instantiation security
**Source**: PLAN_CLOSING_IMPLEMENTATION_extended_2.md P1-2.5

---

## Threat Model

### Attack: Malicious Collector Injection via Subprocess Isolation

**Attack Vector**:
- Attacker provides crafted collector class name
- Subprocess imports and instantiates attacker-controlled code
- Arbitrary code execution in subprocess context

**Example Attack**:
```python
# Attacker provides malicious collector name
malicious_name = "os.system('rm -rf /')"  # Code injection attempt
subprocess_worker.instantiate_collector(malicious_name)
```

**Impact**: Remote Code Execution (RCE) if allowlist not enforced

---

## Mitigation: Allowlist Enforcement

### Pattern (in `tools/collector_worker.py`)

```python
# Hardcoded allowlist (not user-configurable)
ALLOWED_COLLECTORS = {
    "links": "doxstrux.markdown.collectors_phase8.links.LinksCollector",
    "images": "doxstrux.markdown.collectors_phase8.media.MediaCollector",
    "headings": "doxstrux.markdown.collectors_phase8.sections.SectionsCollector",
    "codeblocks": "doxstrux.markdown.collectors_phase8.codeblocks.CodeBlocksCollector",
    "tables": "doxstrux.markdown.collectors_phase8.tables.TablesCollector",
    "lists": "doxstrux.markdown.collectors_phase8.lists.ListsCollector",
}

def instantiate_collector(collector_name: str):
    """
    Instantiate collector from hardcoded allowlist only.

    Security: Prevents arbitrary code execution via malicious collector names.

    Args:
        collector_name: Collector name (must be in ALLOWED_COLLECTORS)

    Returns:
        Collector instance

    Raises:
        ValueError: If collector not in allowlist
    """
    if collector_name not in ALLOWED_COLLECTORS:
        raise ValueError(
            f"Collector '{collector_name}' not in allowlist. "
            f"Allowed: {list(ALLOWED_COLLECTORS.keys())}"
        )

    module_path, class_name = ALLOWED_COLLECTORS[collector_name].rsplit(".", 1)

    # Safe: module_path comes from hardcoded allowlist, not user input
    module = importlib.import_module(module_path)

    return getattr(module, class_name)()
```

### Security Properties

1. **Hardcoded Allowlist**: Not user-configurable (prevents runtime injection)
2. **No Dynamic Imports**: User input never passed to `importlib.import_module()`
3. **Explicit Validation**: Collector name validated before import
4. **Fail-Closed**: Unknown collectors rejected with clear error message

---

## Mitigation: Package Signing (Optional)

### When to Implement

**Only if**: Distributing as wheel/sdist and supply chain attacks are a concern

**Example Use Case**: PyPI package distribution

### Pattern

```python
import hashlib
import importlib.util

# At build time: Generate signatures
COLLECTOR_HASHES = {
    "links": "sha256:abc123...",
    "images": "sha256:def456...",
    "headings": "sha256:789xyz...",
    # ... etc
}

def verify_collector(collector_name: str):
    """
    Verify collector module has not been tampered with.

    Security: Detects supply chain attacks via hash verification.

    Args:
        collector_name: Collector name from allowlist

    Raises:
        SecurityError: If hash mismatch detected
    """
    module_path = ALLOWED_COLLECTORS[collector_name]
    module_file = importlib.util.find_spec(module_path.rsplit(".", 1)[0]).origin

    with open(module_file, 'rb') as f:
        actual_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"

    expected = COLLECTOR_HASHES[collector_name]
    if actual_hash != expected:
        raise SecurityError(
            f"Collector '{collector_name}' hash mismatch. "
            f"Expected: {expected}, Got: {actual_hash}. "
            f"Possible supply chain attack or corruption."
        )

def instantiate_collector_with_verification(collector_name: str):
    """Instantiate collector with hash verification."""
    verify_collector(collector_name)  # Verify first
    return instantiate_collector(collector_name)  # Then instantiate
```

### Build-Time Hash Generation

```bash
# tools/generate_collector_hashes.sh

#!/bin/bash
# Generate SHA256 hashes for all collectors

echo "COLLECTOR_HASHES = {"
for collector in links media sections codeblocks tables lists; do
    file="src/doxstrux/markdown/collectors_phase8/${collector}.py"
    hash=$(sha256sum "$file" | cut -d' ' -f1)
    echo "    \"${collector}\": \"sha256:${hash}\","
done
echo "}"
```

**Run at build time**:
```bash
./tools/generate_collector_hashes.sh > src/doxstrux/collector_hashes_generated.py
```

---

## Policy Requirements

### Mandatory (if subprocess isolation deployed)

1. **✅ Hardcoded allowlist** (not configurable by users)
2. **✅ No dynamic imports** of user-provided collector names
3. **✅ Fail-closed validation** (reject unknown collectors)
4. **✅ Clear error messages** (security logging)

### Optional (if distributing as package)

5. **⚠️ Package signing** (hash verification)
6. **⚠️ Build-time hash generation** (automated in CI)
7. **⚠️ Supply chain monitoring** (dependency scanning)

---

## Implementation Status

**Current Status**: NOT IMPLEMENTED (YAGNI-gated)

**Dependency**: Requires subprocess isolation (P1-2) to be implemented first

**Decision Tree**:
```
Is subprocess isolation (P1-2) implemented?
├─ NO → This policy is moot (allowlist not needed)
└─ YES → Implement allowlist enforcement (mandatory)
         │
         └─ Are you distributing as wheel/sdist?
            ├─ NO → Skip package signing (optional)
            └─ YES → Implement package signing (recommended)
```

**If subprocess isolation never deployed**: This policy becomes unnecessary.

---

## Testing

### Test 1: Allowlist Enforcement

```python
def test_collector_allowlist_enforcement():
    """Verify only allowlisted collectors can be instantiated."""
    from tools.collector_worker import instantiate_collector

    # Valid collector (in allowlist)
    collector = instantiate_collector("links")
    assert collector is not None

    # Invalid collector (not in allowlist)
    with pytest.raises(ValueError, match="not in allowlist"):
        instantiate_collector("malicious_collector")

    # Code injection attempt (not in allowlist)
    with pytest.raises(ValueError, match="not in allowlist"):
        instantiate_collector("os.system('whoami')")
```

### Test 2: Package Signing Verification

```python
def test_collector_hash_verification():
    """Verify hash verification detects tampering."""
    from tools.collector_worker import verify_collector

    # Valid collector (hash matches)
    verify_collector("links")  # Should not raise

    # Simulate tampering (modify file, hash mismatch)
    # ... (test framework would need to mock file hash)
```

---

## Alternative: Code Review Only (No Runtime Checks)

### When Runtime Checks Not Needed

If ALL conditions met:
1. ✅ No subprocess isolation (in-process collectors only)
2. ✅ Collectors are part of main package (not plugins)
3. ✅ No user-provided collector names

**Then**: Code review is sufficient, runtime allowlist not needed.

**Rationale**: In-process collectors cannot be injected at runtime (hardcoded in source).

---

## Recommendations

### Recommendation 1: Deploy on Linux (Avoid Subprocess Overhead)

**Best Practice**: Use Linux deployment with SIGALRM timeout (no subprocess isolation needed)

**Benefits**:
- ✅ No subprocess overhead (faster)
- ✅ No allowlist complexity (simpler)
- ✅ No hash verification needed (fewer dependencies)

**See**: `EXEC_PLATFORM_SUPPORT_POLICY.md` (P0-4)

### Recommendation 2: If Windows Deployment Required

**If** Windows deployment confirmed:
1. Implement subprocess isolation (P1-2)
2. Implement allowlist enforcement (P1-2.5, mandatory)
3. Consider package signing (P1-2.5, optional)

### Recommendation 3: Package Signing Conditions

**Implement package signing ONLY if**:
- Distributing on PyPI or internal package index
- Supply chain attacks are a concern (high-value target)
- Tech Lead approves effort (build-time integration)

**Do NOT implement if**:
- Internal deployment only (not distributed)
- Low attack surface (trusted environment)
- No subprocess isolation (in-process collectors)

---

## References

- **P1-2**: Subprocess Isolation (dependency)
- **tools/collector_worker_YAGNI_PLACEHOLDER.py**: Worker script design
- **OWASP**: [Insecure Deserialization](https://owasp.org/www-project-top-ten/2017/A8_2017-Insecure_Deserialization)
- **Supply Chain Security**: [SLSA Framework](https://slsa.dev/)

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-P1-2.5-DOC | Collector allowlist policy documented | This file | ✅ Complete |
| CLAIM-P1-2.5-PATTERN | Allowlist enforcement pattern provided | Code examples above | ✅ Complete |
| CLAIM-P1-2.5-SIGNING | Package signing pattern provided | Code examples above | ✅ Complete |
| CLAIM-P1-2.5-DEPENDENCY | Policy linked to P1-2 dependency | Decision tree | ✅ Complete |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**YAGNI Status**: Gated by P1-2 (subprocess isolation)
**Approved By**: Pending Human Review
**Next Review**: If/when subprocess isolation implemented
