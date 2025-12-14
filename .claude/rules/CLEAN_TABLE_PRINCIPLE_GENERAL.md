# Clean Table Principle (Project Rule)

The Clean Table Principle is a non-negotiable gate: only ship or present work when it is fully correct, verified, and stable. Anything less stays on the workbench.

## Definition of "Clean"

- No unresolved errors, warnings, TODOs, placeholders, or speculative comments.
- No unverified assumptions; facts are checked or removed.
- No duplicated, conflicting, or workaround logic; the solution is canonical and stable.
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
- "Good enough for now" branches that are never tracked as explicit debt.

## No Silent Errors

All errors must fail loudly and predictably. There is no "strict mode" toggle that changes whether errors are raised.

**FORBIDDEN patterns (examples):**

```python
# BAD: conditional raise based on a strict flag
except Exception as e:
    if strict:
        raise ResourceLoadError(resource_path, e) from e
    errors.append((resource_path, e))
    continue

# BAD: swallowed exception with warning
except Exception as e:
    print(f"Warning: {e}")
    continue

# BAD: strict mode parameter controlling whether errors are raised
def load_resources(path: Path, strict: bool = True) -> list[Resource]:
    ...

# BAD: environment variable to enable strict mode
if os.environ.get("PROJECT_STRICT"):
    raise RuntimeError("Strict mode error handling enabled")
```

**REQUIRED pattern (examples):**

```python
# GOOD: unconditional raise, no conditional strictness
except Exception as e:
    raise ResourceLoadError(resource_path, e) from e
```

The codebase must not contain a configuration, parameter, or environment variable that turns error handling on or off. There must be no code path that continues execution after an unexpected error instead of failing fast.

## Quick Checklist Before Delivery

- [ ] All tests, linters, and type checks pass, or are intentionally updated with clear justification.
- [ ] No TODO/FIXME placeholders in code, docs, or prompts.
- [ ] No silent exceptions: errors are not merely logged or printed and then ignored.
- [ ] All exceptions that indicate a failure are "loud": execution stops or propagates a clear error.
- [ ] No conflicting or duplicated logic; a single canonical path remains for each behavior.
- [ ] Assumptions are verified and documented where necessary.
- [ ] The resulting solution is production-ready as-is (no "we'll clean this later" hidden in the code).
