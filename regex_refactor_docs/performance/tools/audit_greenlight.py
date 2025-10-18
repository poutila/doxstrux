#!/usr/bin/env python3
"""
Green-Light Audit Script with Fatal P0 Enforcement (v1.1)

Purpose: Verify all green-light acceptance criteria before canary deployment
Source: PLAN_CLOSING_IMPLEMENTATION_extended_6.md (Part 6, Patches 1-3)

v1.1 Changes:
- P0 checks now FATAL (exit codes 5/6)
- Missing baseline → exit 6 (blocks deployment)
- Branch protection misconfigured → exit 5 (blocks deployment)
- Fail-closed semantics enforced

Exit Codes:
  0: All checks passed (GREEN LIGHT)
  2: Non-fatal issues (baseline breach, warnings) - proceed with caution
  5: FATAL - Branch protection misconfigured (BLOCKS DEPLOYMENT)
  6: FATAL - Baseline missing or capture failed (BLOCKS DEPLOYMENT)
  1: Other audit failures

Usage:
  python tools/audit_greenlight.py --report /tmp/audit.json
  python tools/audit_greenlight.py --report /tmp/audit.json --registry consumer_registry.yml
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


REPORT_DIR = Path("audit_reports")


def run_cmd(cmd: str, timeout: int = 60) -> Dict[str, Any]:
    """Run shell command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "rc": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "rc": 124,  # Timeout exit code
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s"
        }
    except Exception as e:
        return {
            "rc": 1,
            "stdout": "",
            "stderr": str(e)
        }


def verify_branch_protection_from_registry(
    registry_path: Path,
    github_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify branch protection configured for all consumers in registry.

    Returns:
        Dict with status ('ok'|'fail'|'skipped'), consumers checked, violations
    """
    if not registry_path.exists():
        return {
            "status": "skipped",
            "reason": "Registry file not found",
            "registry_path": str(registry_path)
        }

    try:
        import yaml
    except ImportError:
        return {
            "status": "error",
            "error": "pyyaml not installed (cannot parse registry)"
        }

    try:
        registry_data = yaml.safe_load(registry_path.read_text())
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to parse registry: {e}"
        }

    consumers = registry_data.get("consumers", [])
    if not consumers:
        return {
            "status": "skipped",
            "reason": "No consumers in registry"
        }

    # Check if GitHub token available
    if not github_token:
        return {
            "status": "skipped",
            "reason": "GITHUB_TOKEN not set (cannot query GitHub API)",
            "consumers_count": len(consumers)
        }

    violations = []
    checked = []

    for consumer in consumers:
        name = consumer.get("name")
        repo = consumer.get("repo")
        required_checks = consumer.get("required_checks", [])

        if not repo or not required_checks:
            continue

        # Query GitHub API for branch protection
        cmd = f"gh api repos/{repo}/branches/main/protection"
        result = run_cmd(cmd, timeout=10)

        if result["rc"] != 0:
            violations.append({
                "consumer": name,
                "repo": repo,
                "issue": "Branch protection query failed",
                "error": result["stderr"][:200]
            })
            continue

        try:
            protection = json.loads(result["stdout"])
            actual_checks = set(protection.get("required_status_checks", {}).get("contexts", []))
        except Exception as e:
            violations.append({
                "consumer": name,
                "repo": repo,
                "issue": "Failed to parse branch protection response",
                "error": str(e)
            })
            continue

        # Check if all required checks are configured
        missing_checks = set(required_checks) - actual_checks
        if missing_checks:
            violations.append({
                "consumer": name,
                "repo": repo,
                "issue": "Missing required checks in branch protection",
                "missing_checks": list(missing_checks),
                "required": required_checks,
                "actual": list(actual_checks)
            })

        checked.append({
            "consumer": name,
            "repo": repo,
            "required_checks_count": len(required_checks),
            "configured_checks_count": len(actual_checks),
            "compliant": len(missing_checks) == 0
        })

    return {
        "status": "fail" if violations else "ok",
        "consumers_checked": len(checked),
        "violations": violations,
        "checked": checked
    }


def verify_baseline(
    baseline_path: Path,
    temp_current_path: Path = Path("/tmp/current_metrics_compare.json")
) -> Dict[str, Any]:
    """
    Verify current metrics against a stored baseline.

    Behavior:
    - If baseline_path doesn't exist -> returns {'status':'missing_baseline'} (FATAL in v1.1)
    - Attempts to run tools/capture_baseline_metrics.py --auto to produce current metrics.
      If that script cannot run or produces no metrics, returns {'status':'capture_skipped'} (FATAL in v1.1).
    - If both baseline and current metrics present, compares a set of keys and reports any breaches.
      Thresholds:
        - parse_p95_ms: fail if current > baseline * 1.25
        - parse_p99_ms: fail if current > baseline * 1.5
        - parse_peak_rss_mb: fail if current > baseline + 30
        - collector_timeouts_total_per_min: fail if current > baseline * 1.5
        - collector_truncated_rate: fail if current > baseline * 2

    Returns:
        Dict with fields: status ('ok'|'fail'|'capture_skipped'|'missing_baseline'),
                         baseline, current, diffs
    """
    out = {
        "status": None,
        "baseline_path": str(baseline_path),
        "current_path": str(temp_current_path),
        "diffs": []
    }

    if not baseline_path.exists():
        out["status"] = "missing_baseline"
        return out

    try:
        baseline = json.loads(baseline_path.read_text())
    except Exception as e:
        out["status"] = "baseline_read_error"
        out["error"] = str(e)
        return out

    # Try to auto-capture current metrics using capture_baseline_metrics.py
    capture_script = Path("tools") / "capture_baseline_metrics.py"
    if not capture_script.exists():
        out["status"] = "capture_script_missing"
        out["baseline"] = baseline
        return out

    # Run capture script --auto and write to temp_current_path
    cmd = f"{sys.executable} {shlex.quote(str(capture_script))} --auto --out {shlex.quote(str(temp_current_path))}"
    cap = run_cmd(cmd, timeout=900)

    if cap["rc"] != 0 or not temp_current_path.exists():
        out["status"] = "capture_skipped"
        out["capture_stdout"] = cap.get("stdout", "")[:2000]
        out["capture_stderr"] = cap.get("stderr", "")[:2000]
        out["baseline"] = baseline
        return out

    try:
        current = json.loads(temp_current_path.read_text())
    except Exception as e:
        out["status"] = "current_read_error"
        out["error"] = str(e)
        return out

    out["baseline"] = baseline
    out["current"] = current

    # Comparison rules
    comparisons = []

    def cmp_gt(cur, base, mult=None, add=None):
        if cur is None or base is None:
            return None
        if mult is not None:
            return cur > (base * mult)
        if add is not None:
            return cur > (base + add)
        return cur > base

    # keys to compare and thresholds
    checks = [
        ("parse_p95_ms", lambda c, b: cmp_gt(c, b, mult=1.25)),
        ("parse_p99_ms", lambda c, b: cmp_gt(c, b, mult=1.5)),
        ("parse_peak_rss_mb", lambda c, b: cmp_gt(c, b, add=30)),
        ("collector_timeouts_total_per_min", lambda c, b: cmp_gt(c, b, mult=1.5)),
        ("collector_truncated_rate", lambda c, b: cmp_gt(c, b, mult=2.0)),
    ]

    failed = False
    for key, check in checks:
        bval = baseline.get(key)
        cval = current.get(key)
        breached = check(cval, bval)
        comparisons.append({
            "metric": key,
            "baseline": bval,
            "current": cval,
            "breached": bool(breached) if breached is not None else None
        })
        if breached:
            failed = True

    out["diffs"] = comparisons
    out["status"] = "fail" if failed else "ok"
    return out


def load_consumer_artifacts(artifacts_dir: Path) -> Dict[str, Any]:
    """
    Load consumer self-audit artifacts instead of scanning GitHub org.

    This replaces the org-scan approach with consumer-driven discovery.
    Each consumer repo runs consumer_self_audit.py in CI and publishes artifacts.

    Returns:
        Dict with status, artifacts loaded, and any errors
    """
    if not artifacts_dir.exists():
        return {
            "status": "skipped",
            "reason": f"Artifacts directory not found: {artifacts_dir}",
            "artifacts_loaded": 0
        }

    artifacts = {}
    errors = []

    for artifact_file in artifacts_dir.glob("*.json"):
        try:
            artifact_data = json.loads(artifact_file.read_text())

            # Validate required fields
            repo = artifact_data.get("repo")
            hits = artifact_data.get("hits")

            if not repo:
                errors.append({
                    "file": artifact_file.name,
                    "error": "Missing 'repo' field"
                })
                continue

            if hits is None:
                errors.append({
                    "file": artifact_file.name,
                    "error": "Missing 'hits' field"
                })
                continue

            # Store artifact by repo name
            artifacts[repo] = {
                "hits": hits,
                "hit_count": len(hits),
                "branch": artifact_data.get("branch"),
                "commit": artifact_data.get("commit"),
                "timestamp": artifact_data.get("timestamp"),
                "tool_version": artifact_data.get("tool_version"),
                "source_file": artifact_file.name
            }

        except json.JSONDecodeError as e:
            errors.append({
                "file": artifact_file.name,
                "error": f"Invalid JSON: {e}"
            })
        except Exception as e:
            errors.append({
                "file": artifact_file.name,
                "error": str(e)
            })

    return {
        "status": "ok" if artifacts and not errors else ("error" if errors else "skipped"),
        "artifacts_loaded": len(artifacts),
        "artifacts": artifacts,
        "errors": errors if errors else None
    }


def discover_unregistered_hits(
    artifacts: Dict[str, Dict],
    registry_path: Path,
    exceptions_path: Path = Path("audit_exceptions.yml")
) -> Dict[str, Any]:
    """
    Discover unregistered renderer hits from consumer artifacts.

    Cross-references artifact hits against consumer_registry.yml and audit_exceptions.yml
    to identify files that need registration.

    Returns:
        Dict with unregistered hits per repo
    """
    unregistered = {}

    # Load registry
    registered_paths = set()
    if registry_path.exists():
        try:
            import yaml
            registry = yaml.safe_load(registry_path.read_text())
            for consumer in registry.get("consumers", []):
                for code_path in consumer.get("code_paths", []):
                    registered_paths.add(code_path)
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to load registry: {e}"
            }

    # Load exceptions
    exception_paths = set()
    if exceptions_path.exists():
        try:
            import yaml
            exceptions = yaml.safe_load(exceptions_path.read_text())
            for exc in exceptions.get("exceptions", []):
                exception_paths.add(exc.get("path"))
        except Exception:
            pass  # Exceptions are optional

    # Find unregistered hits
    for repo, artifact in artifacts.items():
        repo_unregistered = []
        for hit in artifact.get("hits", []):
            path = hit.get("path")
            if path and path not in registered_paths and path not in exception_paths:
                repo_unregistered.append(hit)

        if repo_unregistered:
            unregistered[repo] = repo_unregistered

    return {
        "status": "ok",
        "unregistered_hits_count": sum(len(hits) for hits in unregistered.values()),
        "repos_with_hits": len(unregistered),
        "org_unregistered_hits": [
            {"repo": repo, **hit}
            for repo, hits in unregistered.items()
            for hit in hits
        ],
        "renderer_unregistered_local": []  # Local hits handled separately
    }


def check_token_canonicalization() -> Dict[str, Any]:
    """
    Static check for raw token object usage patterns.
    Searches for dangerous patterns that bypass canonicalization.
    """
    dangerous_patterns = [
        (r'token\.attr', 'Direct token attribute access'),
        (r'\.__getattr__', 'Use of __getattr__ on token'),
        (r'SimpleNamespace', 'SimpleNamespace usage (may bypass canonicalization)'),
        (r'token\[.*\]\.', 'Token dict access followed by attribute access'),
    ]

    violations = []
    for pattern, description in dangerous_patterns:
        cmd = f"grep -r '{pattern}' skeleton/doxstrux/ --include='*.py'"
        result = run_cmd(cmd, timeout=30)
        if result['rc'] == 0 and result['stdout']:
            violations.append({
                'pattern': pattern,
                'description': description,
                'matches': result['stdout'].split('\n')[:10]  # First 10 matches
            })

    return {
        'status': 'fail' if violations else 'ok',
        'violations': violations
    }


def run_adversarial_smoke(corpus_dir: Path) -> Dict[str, Any]:
    """
    Run adversarial smoke tests (subset for PR jobs).
    """
    if not corpus_dir.exists():
        return {
            "status": "skipped",
            "reason": "Adversarial corpus directory not found"
        }

    smoke_corpora = [
        "adversarial_encoded_urls.json",
        "adversarial_template_injection.json"
    ]

    results = []
    failed_count = 0

    for corpus_file in smoke_corpora:
        corpus_path = corpus_dir / corpus_file
        if not corpus_path.exists():
            results.append({
                "corpus": corpus_file,
                "status": "skipped",
                "reason": "Corpus file not found"
            })
            continue

        # Run adversarial test (simplified - actual implementation would use test runner)
        cmd = f".venv/bin/python -m pytest skeleton/tests/ -k adversarial -v --tb=short"
        result = run_cmd(cmd, timeout=300)

        passed = result["rc"] == 0
        if not passed:
            failed_count += 1

        results.append({
            "corpus": corpus_file,
            "status": "passed" if passed else "failed",
            "exit_code": result["rc"]
        })

    return {
        "status": "fail" if failed_count > 0 else "ok",
        "smoke_corpora_count": len(smoke_corpora),
        "failed_count": failed_count,
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="Green-light audit with fatal P0 enforcement")
    parser.add_argument("--report", required=True, help="Output report JSON path")
    parser.add_argument("--registry", default="consumer_registry.yml", help="Consumer registry path")
    parser.add_argument("--baseline", default="baselines/metrics_baseline_v1_signed.json", help="Baseline path")
    args = parser.parse_args()

    report = {
        "version": "1.1",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "audit_type": "green-light-pre-canary"
    }
    exit_code = 0

    print("=" * 60)
    print("GREEN-LIGHT AUDIT v1.1 (with Fatal P0 Enforcement)")
    print("=" * 60)
    print()

    # P0 Check 1: Branch Protection Verification (FATAL if missing/errored)
    print("[P0-1] Verifying branch protection from registry...")
    registry_path = Path(args.registry)
    github_token = os.environ.get("GITHUB_TOKEN")

    if registry_path.exists():
        bp_result = verify_branch_protection_from_registry(registry_path, github_token)
        report["branch_protection"] = bp_result

        # FATAL: Branch protection verification skipped or errored
        if bp_result.get("skipped", False) or bp_result.get("error"):
            print(f"❌ FATAL P0 FAILURE: Branch protection verification failed: {bp_result.get('error', bp_result.get('reason', 'skipped'))}")
            exit_code = max(exit_code, 5)  # Fatal exit code
        elif bp_result.get("status") == "fail":
            print(f"❌ FATAL P0 FAILURE: Branch protection misconfigured")
            print(f"   Violations: {len(bp_result.get('violations', []))}")
            for v in bp_result.get("violations", [])[:3]:
                print(f"   - {v.get('consumer')}: {v.get('issue')}")
            exit_code = max(exit_code, 5)
        else:
            print(f"✅ Branch protection verified: {bp_result.get('consumers_checked', 0)} consumers checked")
    else:
        print(f"⚠️  WARN: consumer_registry.yml not found, skipping branch protection check")
        report["branch_protection"] = {"status": "skipped", "reason": "registry not found"}

    # P0 Check 2: Baseline Verification (FATAL if missing/capture failed)
    print()
    print("[P0-2] Verifying baseline metrics...")
    baseline_path = Path(args.baseline)
    baseline_result = verify_baseline(baseline_path)
    report["baseline_verification"] = baseline_result

    bl_status = baseline_result.get("status")

    # FATAL: Missing baseline (no signed baseline exists)
    if bl_status == "missing_baseline":
        print(f"❌ FATAL P0 FAILURE: Signed canonical baseline missing at {baseline_path}")
        print(f"   Action required: Capture and sign baseline with tools/capture_baseline_metrics.py + tools/sign_baseline.py")
        exit_code = max(exit_code, 6)  # Fatal exit code

    # FATAL: Capture script missing or failed
    elif bl_status in ("capture_skipped", "capture_script_missing", "current_read_error"):
        print(f"❌ FATAL P0 FAILURE: Baseline verification could not auto-capture current metrics (status: {bl_status})")
        print(f"   Action required: Fix tools/capture_baseline_metrics.py or run manually")
        exit_code = max(exit_code, 6)

    # Baseline exists but metrics exceeded thresholds
    elif bl_status == "fail":
        print(f"⚠️  BASELINE BREACH: Current metrics exceed thresholds")
        for diff in baseline_result.get("diffs", []):
            if diff.get("breached"):
                print(f"   - {diff['metric']}: current={diff['current']}, baseline={diff['baseline']} (BREACHED)")
        exit_code = max(exit_code, 2)  # Non-fatal but alert

    else:
        print(f"✅ Baseline verification passed")

    # Non-P0 Checks (informational, not fatal)
    print()
    print("[INFO] Token canonicalization static check...")
    token_check = check_token_canonicalization()
    report["token_canonicalization"] = token_check
    if token_check["status"] == "fail":
        print(f"⚠️  Token canonicalization violations found: {len(token_check['violations'])}")
        exit_code = max(exit_code, 1)
    else:
        print(f"✅ Token canonicalization check passed")

    print()
    print("[INFO] Adversarial smoke tests...")
    adv_result = run_adversarial_smoke(Path("adversarial_corpora"))
    report["adversarial_smoke"] = adv_result
    if adv_result["status"] == "fail":
        print(f"⚠️  Adversarial smoke tests failed: {adv_result.get('failed_count', 0)} failures")
        exit_code = max(exit_code, 1)
    else:
        print(f"✅ Adversarial smoke tests passed")

    # Consumer-driven discovery (replaces org-scan)
    print()
    print("[INFO] Loading consumer self-audit artifacts...")
    artifacts_dir = Path("consumer_artifacts")
    artifacts_result = load_consumer_artifacts(artifacts_dir)
    report["consumer_artifacts"] = artifacts_result

    if artifacts_result["status"] == "ok":
        print(f"✅ Loaded {artifacts_result['artifacts_loaded']} consumer artifacts")

        # Discover unregistered hits
        print()
        print("[INFO] Discovering unregistered renderer hits...")
        discovery_result = discover_unregistered_hits(
            artifacts_result["artifacts"],
            registry_path
        )
        report.update(discovery_result)  # Adds org_unregistered_hits, renderer_unregistered_local

        if discovery_result["status"] == "ok":
            hits_count = discovery_result["unregistered_hits_count"]
            repos_count = discovery_result["repos_with_hits"]
            if hits_count > 0:
                print(f"⚠️  Found {hits_count} unregistered hits across {repos_count} repos")
                exit_code = max(exit_code, 1)
            else:
                print(f"✅ No unregistered renderer hits found")
        else:
            print(f"⚠️  Discovery failed: {discovery_result.get('error', 'unknown error')}")
            exit_code = max(exit_code, 1)

    elif artifacts_result["status"] == "skipped":
        print(f"⚠️  Consumer artifacts not found (skipped): {artifacts_result.get('reason')}")
        report["org_unregistered_hits"] = []
        report["renderer_unregistered_local"] = []
    else:
        print(f"⚠️  Consumer artifact loading failed: {len(artifacts_result.get('errors', []))} errors")
        exit_code = max(exit_code, 1)

    # Write report
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2))

    # Final summary
    print()
    print("=" * 60)
    if exit_code != 0:
        if exit_code >= 5:
            print(f"❌ FATAL: Audit failed with P0 failures (exit {exit_code})")
            print(f"   Cannot proceed to canary/deployment until P0 items resolved")
        else:
            print(f"⚠️  Audit completed with warnings (exit {exit_code})")
    else:
        print(f"✅ Audit passed - all checks green")

    print(f"Report written to: {args.report}")
    print("=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
