# Clean Table Principle

The Clean Table Principle is a non-negotiable gate: only ship or present work when it is fully correct, verified, and stable. Anything less stays on the workbench.

## Definition of "Clean"
- No unresolved errors, warnings, TODOs, placeholders, or speculative comments.
- No unverified assumptions; facts are checked or removed.
- No duplicated, conflicting, or workaround logic; solution is canonical and stable.
- No hidden debt: no "temporary" fixes, deferred follow-ups, or "adjust later" notes.

## Enforcement Loop
1. Assess the work product. If any impurity remains, do not ship.
2. Enumerate every impurity (error, assumption, mismatch, conflict, workaround).
3. Resolve immediately—rewrite, verify, delete, or replace with the correct approach.
4. Re-evaluate from step 1 until the table is clean; only then deliver.

## What to Avoid
- "This needs to be checked later" or similar deferrals.
- "You may need to adjust this" without doing the adjustment.
- Temporary band-aids that mask root causes.

## No silent errors

All errors must raise unconditionally. There is no "strict mode" toggle.

**FORBIDDEN patterns:**

```python
# BAD: conditional raise based on strict flag
except Exception as e:
    if strict:
        raise SpecLoadError(spec_path, e) from e
    errors.append((spec_path, e))
    continue

# BAD: swallowed exception with warning
except Exception as e:
    print(f"Warning: {e}")
    continue

# BAD: strict mode parameter
def load_specs(path: Path, strict: bool = True) -> List[Spec]:
    ...

# BAD: environment variable for strict mode
if os.environ.get("SPEKSI_STRICT"):
    raise SomeError(...)
```

**REQUIRED pattern:**

```python
# GOOD: unconditional raise, no conditions
except Exception as e:
    raise SpecLoadError(spec_path, e) from e
```

There must be no possibility to choose "run without error handling".


## Quick Checklist Before Delivery
- [ ] All tests/lints/type checks pass or are intentionally updated.
- [ ] No TODO/FIXME placeholders in code, docs, or prompts.
- [ ] No silent exceptions.
- [ ] All exceptions are loud i.e. execution stops unconditionally.
- [ ] No conflicting or duplicated logic; a single canonical path remains.
- [ ] Assumptions are verified and documented where necessary.
- [ ] The resulting solution is production-ready as-is.
