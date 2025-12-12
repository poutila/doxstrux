"""RAG guard module - Policy layer for RAG pipeline security decisions.

This module provides a thin policy wrapper around doxstrux parser output,
translating raw security metadata into RAG-specific decisions:
- Should this document be embedded?
- Should this document be used in tool calls?
- What severity level applies?

The guard makes NO network calls, NO external lookups - it only interprets
the security metadata already produced by MarkdownParserCore.

Usage:
    from doxstrux import parse_markdown_file
    from doxstrux.rag_guard import guard_doxstrux_for_rag

    result = parse_markdown_file("untrusted.md", security_profile="strict")
    decision = guard_doxstrux_for_rag(result)

    if decision.must_block():
        log.warning(f"Document blocked: {decision.reasons}")
    if not decision.safe_for_tools:
        log.warning(f"Document unsafe for tools: {decision.reasons}")
"""

from dataclasses import dataclass, field
from typing import Any, Literal


DecisionSeverity = Literal["none", "low", "medium", "high", "critical"]


@dataclass
class GuardDecision:
    """RAG guard decision for a parsed document.

    Attributes:
        severity: Risk level (none, low, medium, high, critical)
        blocked: True if document should be completely rejected
        safe_for_embedding: True if document can be embedded in vector store
        safe_for_tools: True if document can be used in tool/function calls
        reasons: List of reasons for any blocking/unsafe decisions
        warnings: List of non-blocking warnings for logging
    """

    severity: DecisionSeverity = "none"
    blocked: bool = False
    safe_for_embedding: bool = True
    safe_for_tools: bool = True
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def must_block(self) -> bool:
        """Convenience: True if this document must not be used automatically."""
        return self.blocked or self.severity == "critical"


def guard_doxstrux_for_rag(result: dict[str, Any]) -> GuardDecision:
    """Apply RAG-specific security policy to parsed document result.

    This function interprets the security metadata from MarkdownParserCore.parse()
    and produces a RAG-focused decision. It does NOT re-analyze the document -
    it only interprets existing metadata.

    Policy (opinionated, RAG-focused):
    1. If doxstrux blocked embedding or quarantined the document:
       -> severity="critical", blocked=True.
    2. If any prompt-injection flag is set:
       -> severity="high", blocks embedding and tools.
    3. If path traversal is detected:
       -> severity="medium", tools must not follow links.
    4. If Unicode risk is high or scan limit exceeded:
       -> severity="medium", adds warning.
    5. All doxstrux security warnings are propagated.

    Args:
        result: The dict returned by MarkdownParserCore.parse()

    Returns:
        GuardDecision with severity, blocking, and safety assessments

    Raises:
        ValueError: If result is missing required metadata structure
    """
    decision = GuardDecision()
    metadata = result.get("metadata", {})

    # Validate required structure
    if "security" not in metadata:
        raise ValueError("Missing 'metadata.security' in parser result")

    security = metadata["security"]
    stats = security.get("statistics", {})

    # Collect doxstrux warnings
    raw_warnings = security.get("warnings", [])
    if isinstance(raw_warnings, list):
        for w in raw_warnings:
            if isinstance(w, dict):
                decision.warnings.append(w.get("message", str(w)))
            else:
                decision.warnings.append(str(w))

    # Check quarantine status (highest priority - document was flagged during parsing)
    if metadata.get("quarantined"):
        decision.severity = "critical"
        decision.blocked = True
        decision.safe_for_embedding = False
        decision.safe_for_tools = False
        quarantine_reason = metadata.get("quarantine_reason", "unknown")
        decision.reasons.append(f"Quarantined: {quarantine_reason}")
        # Also collect quarantine_reasons list if present
        quarantine_reasons = metadata.get("quarantine_reasons", [])
        if isinstance(quarantine_reasons, list):
            for r in quarantine_reasons:
                decision.reasons.append(f"quarantine_reason: {r}")
        return decision

    # Check embedding_blocked flag (set by dangerous scheme detection)
    if metadata.get("embedding_blocked"):
        decision.severity = _max_severity(decision.severity, "high")
        decision.blocked = False  # Not fully blocked, but unsafe for embedding
        decision.safe_for_embedding = False
        decision.safe_for_tools = False
        reason = metadata.get("embedding_block_reason", "embedding_blocked flag set")
        decision.reasons.append(reason)

    # Check prompt injection - both root level and statistics level
    # Root level keys
    if security.get("suspected_prompt_injection"):
        decision.severity = _max_severity(decision.severity, "high")
        decision.safe_for_embedding = False
        decision.safe_for_tools = False
        decision.reasons.append("Suspected prompt injection detected")

    if security.get("prompt_injection_in_content"):
        decision.severity = _max_severity(decision.severity, "high")
        decision.safe_for_embedding = False
        decision.safe_for_tools = False
        decision.reasons.append("Prompt injection detected in content")

    if security.get("prompt_injection_in_footnotes"):
        decision.severity = _max_severity(decision.severity, "high")
        decision.safe_for_embedding = False
        decision.safe_for_tools = False
        decision.reasons.append("Prompt injection detected in footnotes")

    # Statistics level injection keys
    injection_keys = [
        "prompt_injection_in_images",
        "prompt_injection_in_links",
        "prompt_injection_in_code",
        "prompt_injection_in_tables",
    ]
    for key in injection_keys:
        if stats.get(key):
            decision.severity = _max_severity(decision.severity, "high")
            decision.safe_for_embedding = False
            decision.safe_for_tools = False
            location = key.replace("prompt_injection_in_", "")
            decision.reasons.append(f"Prompt injection detected in {location}")

    # Check for dangerous HTML patterns
    if stats.get("has_script"):
        decision.severity = _max_severity(decision.severity, "high")
        decision.safe_for_embedding = False
        decision.safe_for_tools = False
        decision.reasons.append("Script tags detected")

    if stats.get("has_event_handlers"):
        decision.severity = _max_severity(decision.severity, "medium")
        decision.safe_for_tools = False
        decision.reasons.append("Event handlers detected (onclick, onerror, etc.)")

    # Check for disallowed link schemes
    if security.get("link_disallowed_schemes_raw"):
        decision.severity = _max_severity(decision.severity, "medium")
        decision.safe_for_tools = False
        decision.reasons.append("Disallowed link schemes detected (javascript:, data:, etc.)")

    # Check path traversal pattern
    if stats.get("path_traversal_pattern"):
        decision.severity = _max_severity(decision.severity, "medium")
        decision.safe_for_tools = False
        decision.reasons.append("Path traversal pattern detected in links")
        decision.warnings.append(
            "Links from this document must not be followed automatically"
        )

    # Check Unicode spoofing risk
    unicode_risk = stats.get("unicode_risk_score", 0)
    if isinstance(unicode_risk, (int, float)):
        if unicode_risk >= 2:
            decision.severity = _max_severity(decision.severity, "medium")
            decision.warnings.append(f"High unicode spoofing risk (score={unicode_risk})")
        elif unicode_risk >= 1:
            decision.severity = _max_severity(decision.severity, "low")
            decision.warnings.append(f"Moderate unicode spoofing risk (score={unicode_risk})")

    # Check if unicode scan was truncated (fail-closed signal)
    if stats.get("scan_limit_exceeded"):
        decision.severity = _max_severity(decision.severity, "medium")
        decision.warnings.append(
            "Unicode scan truncated due to size; treat spoofing risk as unknown/high"
        )

    # Check BiDi/confusable warnings (spoofing risk)
    # Parser uses both "has_bidi_controls" and "bidi_controls_present"
    if stats.get("has_bidi_controls") or stats.get("bidi_controls_present"):
        decision.severity = _max_severity(decision.severity, "low")
        decision.warnings.append("BiDi control characters detected")

    if stats.get("has_confusables") or stats.get("confusables_present"):
        decision.severity = _max_severity(decision.severity, "low")
        decision.warnings.append("Confusable characters detected (potential homograph)")

    # Check for external links (informational, not blocking)
    if stats.get("has_external_links"):
        decision.warnings.append("Document contains external links")

    # Check for iframes/frame-like elements
    if stats.get("has_iframe") or stats.get("has_frame_like"):
        decision.severity = _max_severity(decision.severity, "medium")
        decision.safe_for_tools = False
        decision.reasons.append("Iframe or frame-like element detected")

    # Check for meta refresh
    if stats.get("has_meta_refresh"):
        decision.severity = _max_severity(decision.severity, "medium")
        decision.safe_for_tools = False
        decision.reasons.append("Meta refresh tag detected")

    return decision


def _max_severity(current: DecisionSeverity, new: DecisionSeverity) -> DecisionSeverity:
    """Return the higher severity level.

    Severity order: none < low < medium < high < critical
    """
    order: dict[str, int] = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    return current if order.get(current, 0) >= order.get(new, 0) else new


__all__ = ["DecisionSeverity", "GuardDecision", "guard_doxstrux_for_rag"]
