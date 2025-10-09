#!/usr/bin/env python3
"""
Run the security test suite against MarkdownParserCore
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from docpipe.loaders.markdown_parser_core import (
    MarkdownParserCore,
    MarkdownSecurityError,
    MarkdownSizeError,
)


def run_security_test(test_id: str, content: str, expected: dict) -> dict:
    """Run a single security test case."""

    results = {"test_id": test_id, "passed": False, "errors": [], "warnings": []}

    security_profile = expected.get("security_profile", "moderate")

    try:
        # First try quick validation
        validation = MarkdownParserCore.validate_content(content, security_profile)

        # Check if it should be blocked during validation
        if expected.get("expected_security_blocked") and not validation["valid"]:
            results["passed"] = True
            results["warnings"].append(f"Content blocked during validation: {validation['issues']}")
            return results

        # Try full parsing
        parser = MarkdownParserCore(content, security_profile=security_profile)
        result = parser.parse()
        security = result["metadata"]["security"]

        # Check expectations
        checks = []

        # Check script detection
        if "expected_has_script" in expected:
            actual = security["statistics"].get("has_script", False)
            if actual != expected["expected_has_script"]:
                checks.append(
                    f"has_script: expected {expected['expected_has_script']}, got {actual}"
                )

        # Check event handlers
        if "expected_has_event_handlers" in expected:
            actual = security["statistics"].get("has_event_handlers", False)
            if actual != expected["expected_has_event_handlers"]:
                checks.append(
                    f"has_event_handlers: expected {expected['expected_has_event_handlers']}, got {actual}"
                )

        # Check prompt injection
        if "expected_suspected_prompt_injection" in expected:
            actual = security["statistics"].get("suspected_prompt_injection", False)
            if actual != expected["expected_suspected_prompt_injection"]:
                checks.append(
                    f"suspected_prompt_injection: expected {expected['expected_suspected_prompt_injection']}, got {actual}"
                )

        # Check Unicode issues
        if "expected_confusables_present" in expected:
            actual = security["statistics"].get("confusables_present", False)
            if actual != expected["expected_confusables_present"]:
                checks.append(
                    f"confusables_present: expected {expected['expected_confusables_present']}, got {actual}"
                )

        # Check Unicode risk score
        if "expected_unicode_risk_score" in expected:
            actual = security["statistics"].get("unicode_risk_score", 0)
            if actual < expected["expected_unicode_risk_score"]:
                checks.append(
                    f"unicode_risk_score: expected >= {expected['expected_unicode_risk_score']}, got {actual}"
                )

        # Check ragged tables
        if "expected_ragged_tables_count" in expected:
            actual = security["statistics"].get("ragged_tables_count", 0)
            if actual != expected["expected_ragged_tables_count"]:
                checks.append(
                    f"ragged_tables_count: expected {expected['expected_ragged_tables_count']}, got {actual}"
                )

        # Check link schemes
        if expected.get("expected_disallowed_link_schemes"):
            link_schemes = security["statistics"].get("link_schemes", {})
            disallowed = ["javascript", "file", "vbscript", "data"]
            has_disallowed = any(scheme in link_schemes for scheme in disallowed)
            if not has_disallowed:
                checks.append(f"expected disallowed link schemes, but none found in {link_schemes}")

        # Check path traversal
        if expected.get("expected_path_traversal_pattern"):
            actual = security["statistics"].get("path_traversal_pattern", False)
            if not actual:
                checks.append("expected path_traversal_pattern, but not detected")

        # Check warning count
        if "expected_warning_count_min" in expected:
            actual_count = len(security.get("warnings", []))
            if actual_count < expected["expected_warning_count_min"]:
                checks.append(
                    f"warning_count: expected >= {expected['expected_warning_count_min']}, got {actual_count}"
                )

        if checks:
            results["errors"] = checks
        else:
            results["passed"] = True

    except MarkdownSecurityError as e:
        # If it was supposed to be blocked, this is success
        if expected.get("expected_security_blocked"):
            results["passed"] = True
            results["warnings"].append(f"Content blocked as expected: {str(e)}")
        else:
            results["errors"].append(f"Unexpected security error: {str(e)}")

    except MarkdownSizeError as e:
        # Size errors are expected for size tests
        if expected.get("expected_size_exceeded") or expected.get("expected_lines_exceeded"):
            results["passed"] = True
            results["warnings"].append(f"Size limit enforced: {str(e)}")
        else:
            results["errors"].append(f"Unexpected size error: {str(e)}")

    except Exception as e:
        results["errors"].append(f"Unexpected error: {str(e)}")

    return results


def main():
    """Run all security tests."""

    print("=" * 60)
    print("Security Test Suite Runner")
    print("=" * 60 + "\n")

    # Generate test cases
    from src.docpipe.loaders.test_mds.security_test_suite import test_cases

    passed = 0
    failed = 0

    for test_id, content, expected, note in test_cases:
        print(f"\n[{test_id}] {note[:50]}...")

        results = run_security_test(test_id, content, expected)

        if results["passed"]:
            print("  ✅ PASSED")
            if results["warnings"]:
                for warning in results["warnings"]:
                    print(f"     ℹ️  {warning}")
            passed += 1
        else:
            print("  ❌ FAILED")
            for error in results["errors"]:
                print(f"     ❗ {error}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
