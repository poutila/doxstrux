"""
Markdown Parser Core - Clean, efficient markdown structure extraction.

This is the foundation for all markdown processing tools.
No backward compatibility burden - fresh architecture.
"""

import hashlib
import posixpath
import re
import urllib.parse
import warnings
from collections.abc import Callable
from typing import Any
import yaml
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from doxstrux.markdown.security import validators as security_validators
from doxstrux.markdown.ir import DocumentIR, DocNode
from doxstrux.markdown.utils.token_utils import walk_tokens_iter
from doxstrux.markdown.utils import line_utils, text_utils
from doxstrux.markdown.exceptions import MarkdownSecurityError, MarkdownSizeError
from doxstrux.markdown import config

class MarkdownParserCore:
    """
    Core markdown parser with universal recursion engine.

    Principles:
    - Single parse of document
    - Universal recursion pattern
    - Extract everything, analyze nothing
    - Preserve original formatting
    - No file I/O (takes content string)
    - No Pydantic models (plain dicts)
    """

    @classmethod
    def get_available_features(cls) -> dict[str, bool]:
        """Return dict of available features (all required now).

        Phase 6: content_context removed - pure token-based classification.
        """
        # Phase 6: All features are required dependencies, no optional packages
        return {
            "yaml": True,
            "footnotes": True,
            "tasklists": True,
        }

    @classmethod
    def validate_content(cls, content: str, security_profile: str = "moderate") -> dict[str, Any]:
        """Quick validation without full parsing - for CLI --validate-only mode.

        Returns:
            Dict with 'valid' bool and 'issues' list
        """
        issues = []
        limits = cls.SECURITY_LIMITS.get(security_profile, cls.SECURITY_LIMITS["moderate"])

        # Size check
        content_size = len(content.encode("utf-8"))
        if content_size > limits["max_content_size"]:
            issues.append(f"Content size {content_size} exceeds {limits['max_content_size']} limit")

        # Line count check
        line_count = content.count("\n") + 1
        if line_count > limits["max_line_count"]:
            issues.append(f"Line count {line_count} exceeds {limits['max_line_count']} limit")

        # Quick malicious pattern scan
        malicious_patterns = [
            (r"<script[^>]*>", "script tag"),
            (r"javascript:", "javascript protocol"),
            (r"data:text/html", "HTML data URI"),
            (r"vbscript:", "vbscript protocol"),
            (r"on\w+\s*=", "event handler"),
        ]

        for pattern, description in malicious_patterns:
            if re.search(pattern, content[:10000], re.IGNORECASE):  # Check first 10KB
                issues.append(f"Suspicious pattern detected: {description}")
                if security_profile == "strict":
                    break  # Stop on first issue in strict mode

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "security_profile": security_profile,
            "content_size": content_size,
            "line_count": line_count,
        }

    # Phase 7 Task 7.4: Configuration moved to markdown/config.py
    # Use config.SECURITY_PROFILES, config.SECURITY_LIMITS, config.ALLOWED_PLUGINS
    # Use config._STYLE_JS_PAT, config._META_REFRESH_PAT, config._FRAMELIKE_PAT
    # Use config._BIDI_CONTROLS

    # Safety: Maximum recursion depth to prevent stack overflow
    MAX_RECURSION_DEPTH = config.MAX_RECURSION_DEPTH

    # Security: Content size limits (reference config module)
    SECURITY_LIMITS = config.SECURITY_LIMITS

    # Security: Allowed plugins (reference config module)
    ALLOWED_PLUGINS = config.ALLOWED_PLUGINS

    # Security patterns (reference config module)
    _STYLE_JS_PAT = config._STYLE_JS_PAT
    _META_REFRESH_PAT = config._META_REFRESH_PAT
    _FRAMELIKE_PAT = config._FRAMELIKE_PAT
    _BIDI_CONTROLS = config._BIDI_CONTROLS

    # Security profiles (reference config module)
    SECURITY_PROFILES = config.SECURITY_PROFILES

    def __init__(
        self,
        content: str,
        config: dict[str, Any] | None = None,
        security_profile: str | None = None,
    ):
        """
        Initialize parser with markdown content.

        Args:
            content: Raw markdown content as string
            config: Optional configuration dict with keys:
                - 'plugins': list of markdown-it plugins to enable
                - 'allows_html': bool, whether HTML blocks are allowed
                - 'preset': str, markdown-it preset ('commonmark', 'gfm', etc.)
            security_profile: Optional security profile ('strict', 'moderate', 'permissive')
        """
        # Validate security profile if provided
        valid_profiles = {"strict", "moderate", "permissive"}
        if security_profile and security_profile not in valid_profiles:
            raise ValueError(
                f"Unknown security profile: {security_profile}. Available: {sorted(valid_profiles)}"
            )

        self.original_content = content
        self.config = config or {}
        self.security_profile = security_profile or "moderate"  # Default to moderate

        # Validate content size limits BEFORE any processing
        self._validate_content_security(content)

        # Set effective allowed schemes based on security profile
        profile = self.SECURITY_PROFILES.get(
            self.security_profile, self.SECURITY_PROFILES["moderate"]
        )
        # Phase 6 Task 6.1: Use centralized security_validators constants
        self._effective_allowed_schemes = profile.get("allowed_schemes", security_validators.ALLOWED_LINK_SCHEMES_MODERATE)

        # Store limits for later validation
        limits = self.SECURITY_LIMITS[self.security_profile]
        self._max_token_count = limits["max_token_count"]
        self.MAX_RECURSION_DEPTH = limits["max_recursion_depth"]

        # Use original content (frontmatter will be extracted by plugin after parsing)
        self.content = content
        self.lines = self.content.split("\n")

        # Build character offset map for RAG chunking
        self._build_line_offsets()

        # Initialize markdown parser with configurable features
        # Always enable HTML parsing to get tokens (policy enforces allows_html)
        preset = self.config.get("preset", "commonmark")
        self.md = MarkdownIt(preset, options_update={"html": True})

        # Enable built-in plugins and external plugins
        # Use profile-appropriate defaults when not specified
        default_builtin = self.ALLOWED_PLUGINS[self.security_profile]["builtin"]
        default_external = self.ALLOWED_PLUGINS[self.security_profile]["external"]

        plugins = self.config.get("plugins", default_builtin)
        external_plugins = self.config.get("external_plugins", default_external)

        # Validate plugins against security profile
        allowed_builtin, allowed_external, rejected = self._validate_plugins(
            plugins, external_plugins
        )

        # Store rejected plugins for reporting
        self.rejected_plugins = rejected

        # Track what we actually enabled
        self.enabled_plugins = set()

        # Enable allowed built-in plugins
        if allowed_builtin:
            self.md.enable(allowed_builtin)
            self.enabled_plugins.update(allowed_builtin)

        # Apply allowed external plugins with availability check
        for plugin_config in allowed_external:
            if plugin_config == "footnote":
                self.md.use(footnote_plugin)
                self.enabled_plugins.add("footnote")
            elif plugin_config == "tasklists":
                self.md.use(tasklists_plugin)
                self.enabled_plugins.add("tasklists")
            elif plugin_config == "front_matter":
                self.md.use(front_matter_plugin)
                self.enabled_plugins.add("front_matter")

        # Track enabled features for extraction logic
        self.allows_html = self.config.get("allows_html", False)

        # Initialize env dict for plugins (front_matter plugin stores data here)
        self.md.env = {}

        # Parse once and create tree (frontmatter extracted by plugin to env)
        self.tokens = self.md.parse(self.content, self.md.env)
        self.tree = SyntaxTreeNode(self.tokens)

        # Phase 6: ContentContext removed - use pure token-based classification
        # Prose/code distinction now derived entirely from AST code blocks

        # Pre-collect text segments for faster plain text extraction
        self._text_segments = []
        self._collect_text_segments()

        # Track sections for cross-referencing
        self._sections = []

        # Initialize extraction caches to avoid redundant work
        self._cache = {
            "code_blocks": None,  # Cache for code blocks
            "sections": None,  # Cache for sections
            "headings": None,  # Cache for headings
            "tables": None,  # Cache for tables
            "lists": None,  # Cache for lists
            "paragraphs": None,  # Cache for paragraphs
            "links": None,  # Cache for links
            "images": None,  # Cache for images
            "blockquotes": None,  # Cache for blockquotes
            "footnotes": None,  # Cache for footnotes
            "html_blocks": None,  # Cache for HTML blocks
        }

    def _validate_content_security(self, content: str) -> None:
        """Comprehensive content security validation.

        Performs size validation and malicious pattern detection based on security profile.
        """
        limits = self.SECURITY_LIMITS[self.security_profile]

        # Size validation
        content_size = len(content.encode("utf-8"))
        if content_size > limits["max_content_size"]:
            raise MarkdownSizeError(
                f"Content size {content_size} bytes exceeds limit",
                self.security_profile,
                {"size": content_size, "limit": limits["max_content_size"]},
            )

        # Line count validation
        line_count = content.count("\n") + 1
        if line_count > limits["max_line_count"]:
            raise MarkdownSizeError(
                f"Line count {line_count} exceeds limit",
                self.security_profile,
                {"lines": line_count, "limit": limits["max_line_count"]},
            )

        # Quick scan for obviously malicious patterns
        malicious_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"data:text/html",
            r"vbscript:",
            r"on\w+\s*=",  # Event handlers
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, content[:10000], re.IGNORECASE):  # Check first 10KB
                if self.security_profile == "strict":
                    raise MarkdownSecurityError(
                        f"Malicious pattern detected: {pattern}",
                        self.security_profile,
                        {"pattern": pattern},
                    )
                # In moderate/permissive, we'll catch it in detailed analysis
                break

    def _validate_plugins(
        self, plugins: list[str], external_plugins: list[str]
    ) -> tuple[list[str], list[str], list[str]]:
        """Validate plugins against security profile.

        Args:
            plugins: Builtin plugins to validate
            external_plugins: External plugins to validate

        Returns:
            Tuple of (allowed_builtin, allowed_external, rejected)
        """
        profile_config = self.ALLOWED_PLUGINS[self.security_profile]
        allowed_builtin = []
        allowed_external = []
        rejected = []

        # Check builtin plugins
        for plugin in plugins:
            if plugin in ["table", "strikethrough", "linkify"]:
                if plugin in profile_config["builtin"]:
                    allowed_builtin.append(plugin)
                else:
                    rejected.append(f"builtin:{plugin}")
            else:
                rejected.append(f"unknown:{plugin}")

        # Check external plugins
        for plugin in external_plugins:
            if plugin in ["footnote", "tasklists", "front_matter"]:
                if plugin in profile_config["external"]:
                    allowed_external.append(plugin)
                else:
                    rejected.append(f"external:{plugin}")
            else:
                rejected.append(f"unknown:{plugin}")

        # In strict mode, silently filter out disallowed plugins
        # The rejected list is still tracked for reporting

        return allowed_builtin, allowed_external, rejected

    def process_tree(
        self,
        node: SyntaxTreeNode,
        processor: Callable,
        context: Any | None = None,
        level: int = 0,
    ) -> Any:
        """
        Universal tree processor with pluggable logic.

        This is the heart of the parser - one recursion pattern for all needs.

        Args:
            node: Current node to process
            processor: Function(node, context, level) -> bool (should recurse)
            context: Mutable context object to collect results
            level: Current depth in tree

        Returns:
            The context object with accumulated results
        """
        if context is None:
            context = {}

        # Safety: Prevent stack overflow from deeply nested structures
        if level > self.MAX_RECURSION_DEPTH:
            return context  # Bail out gracefully

        # Process current node - processor decides if we should recurse
        should_recurse = processor(node, context, level)

        # Recurse into children if needed
        if should_recurse and node.children:
            for child in node.children:
                self.process_tree(child, processor, context, level + 1)

        return context

    def parse(self) -> dict[str, Any]:
        """
        Parse document and extract all structure with enhanced security validation.

        Returns:
            Dictionary with all extracted information

        Raises:
            MarkdownSizeError: If token count exceeds limit
            MarkdownSecurityError: If parsing fails due to security issues
        """
        try:
            # Post-processing security validation - check token count
            token_count = len(self.tokens)
            if token_count > self._max_token_count:
                raise MarkdownSizeError(
                    f"Token count {token_count} exceeds limit",
                    self.security_profile,
                    {"tokens": token_count, "limit": self._max_token_count},
                )

            structure = {
                "sections": self._extract_sections(),
                "paragraphs": self._extract_paragraphs(),
                "lists": self._extract_lists(),
                "tables": self._extract_tables(),
                "code_blocks": self._extract_code_blocks(),
                "headings": self._extract_headings(),
                "links": self._extract_links(),
                "images": self._extract_images(),
                "blockquotes": self._extract_blockquotes(),
                "frontmatter": self._extract_frontmatter(),
                "tasklists": self._extract_tasklists(),
            }



            # Add conditional extractions based on enabled features
            if "footnote" in self.enabled_plugins:
                structure["footnotes"] = self._extract_footnotes()

            # Always extract HTML for security scanning (RAG safety)
            # Include 'allowed' flag based on allows_html config
            html_data = self._extract_html()
            structure["html_blocks"] = html_data["blocks"]
            structure["html_inline"] = html_data["inline"]

            result = {
                "metadata": self._extract_metadata(structure),
                "content": {"raw": self.content, "lines": self.lines},
                "structure": structure,
                "mappings": self._build_mappings(),
            }

            # Apply security policy enforcement
            result = self._apply_security_policy(result)

            # Record security profile used
            result["metadata"]["security"]["profile_used"] = self.security_profile

            # Record any rejected plugins
            if hasattr(self, "rejected_plugins") and self.rejected_plugins:
                result["metadata"]["security"]["rejected_plugins"] = self.rejected_plugins

            return result

        except MarkdownSecurityError:
            # Re-raise security errors as-is
            raise
        except Exception as e:
            # Wrap other errors with security context
            raise MarkdownSecurityError(
                f"Parsing failed: {str(e)}",
                self.security_profile,
                {"original_error": str(e), "error_type": type(e).__name__},
            ) from e

    def _apply_security_policy(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Apply security policy enforcement based on metadata signals.

        This method enforces security policies by:
        1. Blocking embedding if has_script or disallowed link schemes
        2. Stripping HTML blocks when allows_html=False
        3. Dropping unsafe links/images
        4. Quarantining documents with risky features

        Args:
            result: The parsed result dictionary

        Returns:
            Modified result with policy enforcement applied
        """
        security = result["metadata"]["security"]
        structure = result["structure"]

        # Policy flags
        policy_applied = []
        quarantine_reasons = []

        # 1. Block embedding if has_script or disallowed link schemes
        if security["statistics"].get("has_script"):
            result["metadata"]["embedding_blocked"] = True
            result["metadata"]["embedding_block_reason"] = "Document contains script tags"
            policy_applied.append("embedding_blocked_script")

        if security["statistics"].get("disallowed_link_schemes"):
            result["metadata"]["embedding_blocked"] = True
            result["metadata"]["embedding_block_reason"] = (
                "Document contains disallowed link schemes"
            )
            policy_applied.append("embedding_blocked_schemes")

        # Check raw content for disallowed schemes
        if security.get("link_disallowed_schemes_raw"):
            result["metadata"]["embedding_blocked"] = True
            result["metadata"]["embedding_block_reason"] = (
                "Raw content contains disallowed link schemes"
            )
            policy_applied.append("embedding_blocked_schemes_raw")

        # Block embedding for scriptless attack vectors
        if security["statistics"].get("has_style_scriptless"):
            result["metadata"]["embedding_blocked"] = True
            result["metadata"]["embedding_block_reason"] = (
                "Document contains style-based JavaScript injection"
            )
            policy_applied.append("embedding_blocked_style_js")

        if security["statistics"].get("has_meta_refresh"):
            result["metadata"]["embedding_blocked"] = True
            result["metadata"]["embedding_block_reason"] = "Document contains meta refresh redirect"
            policy_applied.append("embedding_blocked_meta_refresh")

        if security["statistics"].get("has_frame_like"):
            result["metadata"]["embedding_blocked"] = True
            result["metadata"]["embedding_block_reason"] = (
                "Document contains frame-like elements (iframe/object/embed)"
            )
            policy_applied.append("embedding_blocked_frame")

        # 2. Strip HTML blocks when allows_html=False
        if not self.allows_html:
            # Strip HTML blocks
            if structure.get("html_blocks"):
                original_count = len(structure["html_blocks"])
                structure["html_blocks"] = []
                policy_applied.append(f"stripped_{original_count}_html_blocks")

            # Strip HTML inline
            if structure.get("html_inline"):
                original_count = len(structure["html_inline"])
                structure["html_inline"] = []
                policy_applied.append(f"stripped_{original_count}_html_inline")

        # 3. Drop unsafe links/images
        # Filter links - remove those with disallowed schemes
        if structure.get("links"):
            safe_links = []
            dropped_count = 0
            for link in structure["links"]:
                if link.get("allowed", True):
                    safe_links.append(link)
                else:
                    dropped_count += 1
            if dropped_count > 0:
                structure["links"] = safe_links
                policy_applied.append(f"dropped_{dropped_count}_unsafe_links")

        # Filter images - remove those with disallowed schemes or data URIs
        if structure.get("images"):
            safe_images = []
            dropped_count = 0
            for img in structure["images"]:
                url = img.get("src", "")  # Images use 'src' not 'url'
                # Check for data URIs or other unsafe schemes
                if url.startswith("data:") or url.startswith("javascript:"):
                    dropped_count += 1
                else:
                    # Validate scheme
                    scheme = img.get("scheme")
                    if scheme and scheme not in self._effective_allowed_schemes:
                        dropped_count += 1
                    else:
                        safe_images.append(img)
            if dropped_count > 0:
                structure["images"] = safe_images
                policy_applied.append(f"dropped_{dropped_count}_unsafe_images")

        # 4. Quarantine documents with risky features
        # Check for ragged tables
        if security["statistics"].get("ragged_tables_count", 0) > 0:
            quarantine_reasons.append(
                f"ragged_tables:{security['statistics']['ragged_tables_count']}"
            )

        # Check for long footnote definitions (potential payload hiding)
        if structure.get("footnotes"):
            definitions = structure["footnotes"].get("definitions", [])
            for footnote in definitions:
                content = footnote.get("content", "")
                if len(content) > 512:
                    quarantine_reasons.append(f"long_footnote:{footnote.get('label', 'unknown')}")
                    break

        # Check for prompt injection in footnotes
        if security.get("prompt_injection_in_footnotes"):
            quarantine_reasons.append("prompt_injection_footnotes")

        # Check for prompt injection in content
        if security.get("prompt_injection_in_content"):
            quarantine_reasons.append("prompt_injection_content")

        # Set quarantine status if needed
        if quarantine_reasons:
            result["metadata"]["quarantined"] = True
            result["metadata"]["quarantine_reasons"] = quarantine_reasons
            # User can whitelist by checking quarantine_reasons

        # Record what policies were applied
        if policy_applied:
            result["metadata"]["security_policies_applied"] = policy_applied

        return result

    def sanitize(
        self, policy: dict[str, Any] | None = None, security_profile: str | None = None
    ) -> dict[str, Any]:
        """
        DEPRECATED (Phase 3): Non-mutating wrapper. Use parse() results instead.

        This method no longer modifies the source text. It emits:
          - sanitized_text: the original, unmodified content
          - blocked: whether embedding should be blocked
          - reasons: high-level reasons derived from parse() metadata

        Rationale:
          - Align with fail-closed policy and single-source-of-truth security enforcement
          - Avoid hybrid regex + token approaches inside validation
          - Eliminate heavy second parse (performance improvement)

        Args:
            policy: Optional policy dict (ignored, for API compatibility)
            security_profile: Optional security profile name ('strict', 'moderate', 'permissive')

        Returns:
            Dictionary with:
            - sanitized_text: The original content (UNCHANGED)
            - blocked: Whether document should be blocked
            - reasons: List of validation issues/warnings
        """
        warnings.warn(
            "sanitize() is deprecated: it no longer mutates text. "
            "Use parse() and inspect result['metadata'] for policy decisions.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Keep profile override consistent with parse() behavior
        if security_profile and security_profile in self.SECURITY_PROFILES:
            # Create a temporary parser with the requested profile, but do not change text
            temp_config = {**self.config}
            temp_config["security_profile"] = security_profile
            tmp = MarkdownParserCore(self.content, temp_config)
            parsed = tmp.parse()
        else:
            parsed = self.parse()

        md = parsed.get("metadata", {})
        sec = md.get("security", {})
        stats = sec.get("statistics", {}) or {}

        blocked = bool(
            md.get("embedding_blocked")
            or md.get("quarantined")
        )

        # Build human-facing reasons from applied policies and security stats
        reasons: list[str] = []
        if md.get("embedding_block_reason"):
            reasons.append(md["embedding_block_reason"])
        reasons.extend(md.get("quarantine_reasons", []) or [])
        for k in ("has_script", "has_style_scriptless", "has_meta_refresh", "has_frame_like"):
            if stats.get(k):
                reasons.append(k)
        if stats.get("disallowed_link_schemes"):
            reasons.append("disallowed_link_schemes")
        if sec.get("warnings"):
            # Append unique warning types for visibility
            reasons.extend({w.get("type", "warning") for w in sec["warnings"]})
        reasons = list(dict.fromkeys(reasons))

        return {
            "sanitized_text": self.content,  # unchanged
            "blocked": blocked,
            "reasons": reasons,
        }

    def _extract_metadata(self, structure: dict[str, Any]) -> dict[str, Any]:
        """Extract document-level metadata with single-pass node type counting and security summary."""
        # Single pass to count all node types
        type_counts = {}
        for node in self.tree.walk():
            node_type = getattr(node, "type", "")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        metadata = {
            "total_lines": len(self.lines),
            "total_chars": len(self.content),
            "has_sections": type_counts.get("heading", 0) > 0,
            "has_code": (type_counts.get("fence", 0) + type_counts.get("code_block", 0)) > 0,
            "has_tables": type_counts.get("table", 0) > 0,
            "has_lists": (type_counts.get("bullet_list", 0) + type_counts.get("ordered_list", 0))
            > 0,
            "node_counts": type_counts,  # Bonus: expose raw counts for debugging/analytics
        }

        # Add frontmatter if present (from structure, not self.frontmatter)
        frontmatter = structure.get("frontmatter")
        if frontmatter:
            metadata["frontmatter"] = frontmatter
            metadata["has_frontmatter"] = True
        else:
            metadata["has_frontmatter"] = False

        # Add security metadata
        metadata["security"] = self._generate_security_metadata(structure)

        # Add frontmatter error if present
        if hasattr(self, "frontmatter_error"):
            metadata["frontmatter_error"] = self.frontmatter_error

        return metadata

    def _generate_security_metadata(self, structure: dict[str, Any]) -> dict[str, Any]:
        """Generate security metadata summarizing potential issues found.

        Returns:
            Dictionary with security warnings and statistics
        """
        import re

        security = {
            "warnings": [],
            "statistics": {
                "frontmatter_at_bof": False,
                "ragged_tables_count": 0,
                "allowed_schemes": sorted(list(self._effective_allowed_schemes)),  # Phase 6 Task 6.1: Use effective schemes from profile
                "table_align_mismatches": 0,
                "nested_headings_blocked": 0,
                "has_html_block": False,
                "has_html_inline": False,
                "has_script": False,
                "has_event_handlers": False,
                "has_data_uri_images": False,
                "confusables_present": False,
                "nbsp_present": False,
                "zwsp_present": False,
                "path_traversal_pattern": False,
                "link_schemes": {},
            },
        }

        # Check frontmatter location (from structure)
        frontmatter = structure.get("frontmatter")
        if frontmatter:
            security["statistics"]["frontmatter_at_bof"] = True
            # We know it's at BOF because plugin only extracts it from there

        # Count ragged tables and alignment mismatches
        tables = self._get_cached("tables", self._extract_tables)
        ragged_count = 0
        align_mismatch_count = 0
        for table in tables:
            if table.get("is_ragged", False):
                ragged_count += 1
                security["warnings"].append(
                    {
                        "type": "ragged_table",
                        "line": table.get("start_line"),
                        "message": "Table has inconsistent column counts",
                    }
                )
            if table.get("align_mismatch", False):
                align_mismatch_count += 1
                security["warnings"].append(
                    {
                        "type": "table_align_mismatch",
                        "line": table.get("start_line"),
                        "message": "Table alignment specification does not match column count",
                    }
                )
        security["statistics"]["ragged_tables_count"] = ragged_count
        security["statistics"]["table_align_mismatches"] = align_mismatch_count

        # HTML detection (Phase 4: pure token-based, zero regex)
        # Extract HTML from structure (already parsed via tokens in _extract_html)
        html_blocks = structure.get("html_blocks", [])
        html_inline = structure.get("html_inline", [])

        # Keep raw_content for non-HTML patterns (style JS, etc.)
        raw_content = self.original_content

        # Token-based detection (always works now since html=True in parser init)
        if html_blocks:
            security["statistics"]["has_html_block"] = True
        if html_inline:
            security["statistics"]["has_html_inline"] = True

        # Script detection (pure token-based)
        html_items = html_blocks + html_inline
        for html_item in html_items:
            content = html_item.get("content", "").lower()
            if "<script" in content:
                security["statistics"]["has_script"] = True
                security["warnings"].append(
                    {
                        "type": "script_tag",
                        "line": html_item.get("line") or html_item.get("start_line"),
                        "message": "Document contains <script> tags"
                    }
                )
                break

        # Event handler detection (pure token-based)
        event_handlers = ["onload", "onerror", "onclick", "onmouse", "onkey", "onfocus", "onblur", "onchange", "onsubmit"]
        for html_item in html_items:
            content = html_item.get("content", "").lower()
            if any(handler in content for handler in event_handlers):
                security["statistics"]["has_event_handlers"] = True
                security["warnings"].append(
                    {
                        "type": "event_handlers",
                        "line": html_item.get("line") or html_item.get("start_line"),
                        "message": "Document contains HTML event handler attributes",
                    }
                )
                break

        # Style-based JavaScript injection detection
        if self._STYLE_JS_PAT.search(raw_content):
            security["statistics"]["has_style_scriptless"] = True
            security["warnings"].append(
                {
                    "type": "style_scriptless",
                    "line": None,
                    "message": "style=url(javascript:...) or expression() detected",
                }
            )

        # Meta refresh detection (can be used for redirects)
        if self._META_REFRESH_PAT.search(raw_content):
            security["statistics"]["has_meta_refresh"] = True
            security["warnings"].append(
                {
                    "type": "meta_refresh",
                    "line": None,
                    "message": "<meta http-equiv=refresh> present",
                }
            )

        # Frame-like element detection (iframe, object, embed)
        if self._FRAMELIKE_PAT.search(raw_content):
            security["statistics"]["has_frame_like"] = True
            security["warnings"].append(
                {
                    "type": "frame_like",
                    "line": None,
                    "message": "<iframe|object|embed src|data> present",
                }
            )

        # Check images for data URIs
        images = self._get_cached("images", self._extract_images)
        for img in images:
            if img.get("src", "").startswith("data:"):  # Images use 'src' not 'url'
                security["statistics"]["has_data_uri_images"] = True
                security["warnings"].append(
                    {
                        "type": "data_uri_image",
                        "line": img.get("line"),
                        "message": "Image uses data: URI scheme",
                    }
                )
                break

        # Link scheme analysis with RAG safety validation
        links = self._get_cached("links", self._extract_links)
        link_schemes = {}
        disallowed_schemes = {}
        for link in links:
            scheme = link.get("scheme")
            allowed = link.get("allowed", True)
            url = link.get("url", "")

            # Track scheme counts
            if scheme:
                link_schemes[scheme] = link_schemes.get(scheme, 0) + 1
                if not allowed:
                    disallowed_schemes[scheme] = disallowed_schemes.get(scheme, 0) + 1
            elif url:
                # Track schemeless links
                if url.startswith("#"):
                    link_schemes["anchor"] = link_schemes.get("anchor", 0) + 1
                else:
                    link_schemes["relative"] = link_schemes.get("relative", 0) + 1

            # Check for path traversal with comprehensive detection
            if self._check_path_traversal(url):
                security["statistics"]["path_traversal_pattern"] = True
                security["warnings"].append(
                    {
                        "type": "path_traversal",
                        "line": link.get("line"),
                        "message": "Link contains path traversal pattern",
                        "url": url[:100],  # Truncate for safety
                    }
                )

        security["statistics"]["link_schemes"] = link_schemes
        if disallowed_schemes:
            security["statistics"]["disallowed_link_schemes"] = disallowed_schemes
            security["warnings"].append(
                {
                    "type": "disallowed_link_schemes",
                    "schemes": list(disallowed_schemes.keys()),
                    "message": f"Links with disallowed schemes detected: {', '.join(disallowed_schemes.keys())}",
                }
            )

        # Comprehensive Unicode security checks
        unicode_issues = self._check_unicode_spoofing(raw_content)

        # Basic Unicode checks
        if "\xa0" in raw_content or "\u00a0" in raw_content:
            security["statistics"]["nbsp_present"] = True
        if "\u200b" in raw_content or "\u200c" in raw_content or "\u200d" in raw_content:
            security["statistics"]["zwsp_present"] = True

        # BiDi control detection
        if unicode_issues["has_bidi"]:
            security["statistics"]["has_bidi_controls"] = True
            security["statistics"]["bidi_controls_present"] = True
            security["warnings"].append(
                {
                    "type": "bidi_controls",
                    "line": None,
                    "message": "Document contains BiDi control characters (potential text direction manipulation)",
                }
            )

        # Confusable character detection
        if unicode_issues["has_confusables"]:
            security["statistics"]["has_confusables"] = True
        if unicode_issues["has_confusables"]:
            security["statistics"]["confusables_present"] = True
            security["warnings"].append(
                {
                    "type": "confusable_characters",
                    "line": None,
                    "message": "Document contains confusable Unicode characters (potential homograph attack)",
                }
            )

        # Mixed script detection
        if unicode_issues["has_mixed_scripts"]:
            security["statistics"]["mixed_scripts"] = True
            security["warnings"].append(
                {
                    "type": "mixed_scripts",
                    "line": None,
                    "message": "Document mixes multiple scripts with Latin (potential spoofing)",
                }
            )

        # Invisible character detection
        if unicode_issues["has_invisible_chars"]:
            security["statistics"]["invisible_chars"] = True
            security["warnings"].append(
                {
                    "type": "invisible_characters",
                    "line": None,
                    "message": "Document contains invisible/zero-width characters",
                }
            )

        # Calculate unicode risk score (0-4 based on detected issues)
        unicode_risk_score = sum(
            [
                unicode_issues.get("has_bidi", False),
                unicode_issues.get("has_confusables", False),
                unicode_issues.get("has_mixed_scripts", False),
                unicode_issues.get("has_invisible_chars", False),
            ]
        )
        security["statistics"]["unicode_risk_score"] = unicode_risk_score

        # Scan raw content for disallowed link schemes that markdown-it might not parse (Phase 6 Task 6.1)
        scheme_scan = security_validators.scan_raw_for_disallowed_schemes(raw_content)
        if scheme_scan["found"]:
            security["link_disallowed_schemes_raw"] = True
            security["warnings"].append(
                {
                    "type": "disallowed_schemes_raw",
                    "message": f"Raw content contains potentially dangerous scheme: {scheme_scan['match']}",
                }
            )

        # RAG Safety: Comprehensive prompt injection detection

        # Check main content (Phase 6 Task 6.1)
        if security_validators.check_prompt_injection(raw_content):
            security["statistics"]["suspected_prompt_injection"] = True
            security["warnings"].append(
                {
                    "type": "prompt_injection",
                    "line": None,
                    "message": "Suspected prompt injection patterns detected in content",
                }
            )

        # Check all image alt/title text
        for img in images:
            alt_text = img.get("alt", "")
            title = img.get("title", "")
            if security_validators.check_prompt_injection(alt_text) or security_validators.check_prompt_injection(title):
                security["statistics"]["prompt_injection_in_images"] = True
                security["warnings"].append(
                    {
                        "type": "prompt_injection_image",
                        "line": img.get("line"),
                        "message": "Prompt injection in image alt/title text",
                    }
                )
                break

        # Check all link titles
        for link in links:
            title = link.get("title", "")
            text = link.get("text", "")
            if security_validators.check_prompt_injection(title) or security_validators.check_prompt_injection(text):
                security["statistics"]["prompt_injection_in_links"] = True
                security["warnings"].append(
                    {
                        "type": "prompt_injection_link",
                        "line": link.get("line"),
                        "message": "Prompt injection in link text/title",
                    }
                )
                break

        # Check code block content (even though not rendered, could be copied)
        code_blocks = self._get_cached("code_blocks", self._extract_code_blocks)
        for block in code_blocks:
            code = block.get("code", "")
            if security_validators.check_prompt_injection(code):
                security["statistics"]["prompt_injection_in_code"] = True
                security["warnings"].append(
                    {
                        "type": "prompt_injection_code",
                        "line": block.get("start_line"),
                        "message": "Prompt injection patterns in code block",
                    }
                )
                break

        # Check table cell content
        for table in tables:
            # Check headers
            for header in table.get("headers", []):
                if security_validators.check_prompt_injection(header):
                    security["statistics"]["prompt_injection_in_tables"] = True
                    security["warnings"].append(
                        {
                            "type": "prompt_injection_table",
                            "line": table.get("start_line"),
                            "message": "Prompt injection in table content",
                        }
                    )
                    break
            # Check rows
            for row in table.get("rows", []):
                if any(security_validators.check_prompt_injection(cell) for cell in row):
                    security["statistics"]["prompt_injection_in_tables"] = True
                    security["warnings"].append(
                        {
                            "type": "prompt_injection_table",
                            "line": table.get("start_line"),
                            "message": "Prompt injection in table content",
                        }
                    )
                    break

        # RAG Safety: Check footnotes for injection
        footnotes = structure.get("footnotes", {})
        if self._check_footnote_injection(footnotes):
            security["statistics"]["footnote_injection"] = True
            security["warnings"].append(
                {
                    "type": "footnote_injection",
                    "line": None,
                    "message": "Prompt injection detected in footnote definitions",
                }
            )

        # RAG Safety: Check for oversized footnotes (potential payload hiding)
        if footnotes and isinstance(footnotes, dict):
            definitions = footnotes.get("definitions", [])
            for footnote in definitions:
                content = footnote.get("content", "")
                if len(content) > 512:
                    security["statistics"]["oversized_footnotes"] = True
                    security["warnings"].append(
                        {
                            "type": "oversized_footnote",
                            "line": footnote.get("start_line"),
                            "message": f"Footnote definition exceeds 512 chars ({len(content)} chars)",
                        }
                    )
                    break

        # RAG Safety: Check for HTML when not allowed
        html_blocks = structure.get("html_blocks", [])
        html_inline = structure.get("html_inline", [])
        disallowed_html_blocks = [b for b in html_blocks if not b.get("allowed", True)]
        disallowed_html_inline = [i for i in html_inline if not i.get("allowed", True)]

        # Check for CSP headers in HTML blocks
        for block in html_blocks:
            content = block.get("content", "") if isinstance(block, dict) else str(block)
            # Check for Content Security Policy in meta tags
            csp_pattern = r'<meta[^>]*http-equiv=["\']Content-Security-Policy["\'][^>]*>'
            if re.search(csp_pattern, content, re.IGNORECASE):
                security["statistics"]["has_csp_header"] = True
                security["warnings"].append(
                    {
                        "type": "csp_header_detected",
                        "line": block.get("line") if isinstance(block, dict) else None,
                        "message": "Content Security Policy header detected in HTML",
                    }
                )

            # Check for X-Frame-Options
            xfo_pattern = r'<meta[^>]*http-equiv=["\']X-Frame-Options["\'][^>]*>'
            if re.search(xfo_pattern, content, re.IGNORECASE):
                security["statistics"]["has_xframe_options"] = True
                security["warnings"].append(
                    {
                        "type": "xframe_options_detected",
                        "line": block.get("line") if isinstance(block, dict) else None,
                        "message": "X-Frame-Options header detected in HTML",
                    }
                )

        if disallowed_html_blocks or disallowed_html_inline:
            security["statistics"]["html_disallowed"] = True
            security["warnings"].append(
                {
                    "type": "html_disallowed",
                    "blocks": len(disallowed_html_blocks),
                    "inline": len(disallowed_html_inline),
                    "message": "HTML present but not allowed by configuration",
                }
            )

        # RAG Safety: Raw scan for dangerous patterns that might bypass tokenizer
        dangerous_schemes = ["javascript:", "vbscript:", "data:text/html", "file:"]
        for scheme in dangerous_schemes:
            if scheme in raw_content.lower():
                security["statistics"]["raw_dangerous_schemes"] = True
                security["warnings"].append(
                    {
                        "type": "raw_dangerous_scheme",
                        "scheme": scheme.rstrip(":"),
                        "message": f'Dangerous scheme "{scheme}" found in raw content',
                    }
                )

        # Add summary section with key metrics
        security["summary"] = {
            "ragged_tables_count": security["statistics"].get("ragged_tables_count", 0),
            "total_warnings": len(security["warnings"]),
            "has_dangerous_content": bool(security["warnings"]),
            "unicode_risk_score": security["statistics"].get("unicode_risk_score", 0),
        }

        return security

    def _get_cached(self, key: str, extractor: Callable) -> Any:
        """Get cached result or extract and cache."""
        if self._cache[key] is None:
            self._cache[key] = extractor()
        return self._cache[key]

    def _slice_lines_inclusive(self, start_line: int | None, end_line: int | None) -> list[str]:
        """
        Centralized line slicing with end-inclusive convention.

        This method enforces the codebase standard: markdown-it's node.map[1] represents
        the line AFTER the content, so we use end-inclusive slicing (end_line+1) to
        capture all content lines.

        Args:
            start_line: Start line number (inclusive, 0-based)
            end_line: End line number (markdown-it convention: first line AFTER content)

        Returns:
            List of lines from start_line to end_line (inclusive of actual content)

        Examples:
            # node.map = [5, 8] means lines 5, 6, 7 contain content
            _slice_lines_inclusive(5, 8) -> self.lines[5:8] -> lines 5, 6, 7
        """
        return line_utils.slice_lines(self.lines, start_line, end_line)

    def _slice_lines_raw(self, start_line: int | None, end_line: int | None) -> str:
        """
        Get raw content string from line range using consistent slicing convention.

        Args:
            start_line: Start line number (inclusive, 0-based)
            end_line: End line number (markdown-it convention: first line AFTER content)

        Returns:
            Joined string content with newlines preserved
        """
        return line_utils.slice_lines_raw(self.lines, start_line, end_line)

    def _extract_frontmatter(self) -> dict | None:
        """
        Extract YAML frontmatter from tokens (Phase 5: plugin-based).

        The front_matter plugin creates a 'front_matter' token with YAML content.
        We parse the YAML content from the token.

        Returns:
            Frontmatter dict or None if not present
        """
        # Find front_matter token (plugin creates this)
        for token in self.tokens:
            if hasattr(token, 'type') and token.type == 'front_matter':
                # Token content is the raw YAML string
                yaml_content = token.content
                if yaml_content:
                    try:
                        parsed_yaml = yaml.safe_load(yaml_content)
                        # Return parsed YAML if it's a dict or list
                        if isinstance(parsed_yaml, (dict, list)):
                            return parsed_yaml
                    except yaml.YAMLError:
                        # Invalid YAML - return None
                        pass
                break
        return None

    # Phase 6 Task 6.1: Removed get_total_hrule_count() - broken after frontmatter plugin migration
    # Frontmatter line numbers not needed for RAG use cases (metadata extracted, sections start after frontmatter)

    def _extract_sections(self) -> list[dict]:
        """
        Extract document sections with preserved content.

        Sections are defined by headings and contain all content
        until the next heading of equal or higher level.
        """
        # Return cached result if available
        if self._cache["sections"] is not None:
            return self._cache["sections"]

        sections = []
        section_stack = []  # Track hierarchy
        slug_counts = {}  # Track slug usage for stable IDs

        def section_processor(node, ctx, level):
            if node.type == "heading":
                # Extract heading info
                heading_level = self._heading_level(node)
                heading_text = self._get_text(node)
                base_slug = self._slugify_base(heading_text)

                # Generate stable ID with running count
                if base_slug in slug_counts:
                    slug_counts[base_slug] += 1
                    stable_slug = f"{base_slug}-{slug_counts[base_slug]}"
                else:
                    slug_counts[base_slug] = 1
                    stable_slug = base_slug

                stable_id = f"section_{stable_slug}"

                # Create new section
                start_line = node.map[0] if node.map else None
                start_char, _ = (
                    self._span_from_lines(start_line, start_line)
                    if start_line is not None
                    else (None, None)
                )

                section = {
                    "id": stable_id,
                    "level": heading_level,
                    "title": heading_text,
                    "slug": stable_slug,
                    "start_line": start_line,
                    "end_line": None,  # Set when next section starts
                    "start_char": start_char,
                    "end_char": None,  # Set when section content is finalized
                    "parent_id": None,
                    "child_ids": [],
                }

                # Set end line of previous section at same or higher level
                while ctx["stack"] and ctx["stack"][-1]["level"] >= heading_level:
                    prev = ctx["stack"].pop()
                    if prev["end_line"] is None:
                        prev["end_line"] = section["start_line"] - 1

                # Set parent relationship
                if ctx["stack"]:
                    parent = ctx["stack"][-1]
                    section["parent_id"] = parent["id"]
                    parent["child_ids"].append(section["id"])

                # Add to stack and results
                ctx["stack"].append(section)
                ctx["sections"].append(section)

            return True  # Always continue traversing

        context = {"sections": [], "stack": []}
        self.process_tree(self.tree, section_processor, context)

        # Set end lines for remaining sections
        for section in context["stack"]:
            if section["end_line"] is None:
                section["end_line"] = len(self.lines) - 1

        # Fill in section content from original lines
        for section in context["sections"]:
            if section["start_line"] is not None and section["end_line"] is not None:
                start = section["start_line"]
                end = section["end_line"] + 1
                # Use centralized slicing utility for consistency
                section["raw_content"] = self._slice_lines_raw(start, end)
                section["text_content"] = self._plain_text_in_range(start, end - 1)
                # Update end_char for completed section
                _, section["end_char"] = self._span_from_lines(
                    section["start_line"], section["end_line"]
                )
            else:
                section["raw_content"] = ""
                section["text_content"] = ""

        self._sections = context["sections"]
        # Cache the result
        self._cache["sections"] = context["sections"]
        return context["sections"]

    def _extract_paragraphs(self) -> list[dict]:
        """Extract all paragraphs with metadata."""
        paragraphs = []

        def paragraph_processor(node, ctx, level):
            if node.type == "paragraph":
                # Skip if inside a list or blockquote (they handle their own paragraphs)
                parent = getattr(node, "parent", None)
                while parent:
                    if parent.type in ["list_item", "blockquote"]:
                        return False
                    parent = getattr(parent, "parent", None)

                para = {
                    "id": f"para_{len(ctx)}",
                    "text": self._get_text(node),
                    "start_line": node.map[0] if node.map else None,
                    "end_line": node.map[1] if node.map else None,
                    "section_id": self._find_section_id(node.map[0] if node.map else 0),
                    "word_count": len(self._get_text(node).split()),
                    "has_links": self._has_child_type(node, "link"),
                    "has_emphasis": self._has_child_type(node, ["em", "strong"]),
                    "has_code": self._has_child_type(node, "code_inline"),
                }
                ctx.append(para)
                return False  # Don't recurse, we extracted everything

            return True

        self.process_tree(self.tree, paragraph_processor, paragraphs)
        return paragraphs

    def _extract_lists(self) -> list[dict]:
        """Extract regular lists (excludes task lists - those are in _extract_tasklists)."""
        lists = []

        def list_processor(node, ctx, level):
            if node.type in ["bullet_list", "ordered_list"]:
                # Check if this is a task list (skip if it is)
                class_attr = ""
                if hasattr(node, 'attrs') and node.attrs:
                    class_attr = node.attrs.get('class', '')

                if 'contains-task-list' in class_attr:
                    # Skip task lists (handled by _extract_tasklists)
                    return True

                # Extract regular list structure
                items = self._extract_list_items(node)

                list_data = {
                    "id": f"list_{len(ctx)}",
                    "type": "bullet" if node.type == "bullet_list" else "ordered",
                    "start_line": node.map[0] if node.map else None,
                    "end_line": node.map[1] if node.map else None,
                    "section_id": self._find_section_id(node.map[0] if node.map else 0),
                    "items": items,
                    "items_count": len(items),
                }

                ctx.append(list_data)
                return False  # Don't recurse, we handled the entire list

            return True

        self.process_tree(self.tree, list_processor, lists)
        return lists

    def _extract_tasklists(self) -> list[dict]:
        """Extract task lists (GFM extension with checkbox items)."""
        tasklists = []

        def tasklist_processor(node, ctx, level):
            if node.type in ["bullet_list", "ordered_list"]:
                # Check if this is a task list (plugin marks it with class)
                class_attr = ""
                if hasattr(node, 'attrs') and node.attrs:
                    class_attr = node.attrs.get('class', '')

                if 'contains-task-list' not in class_attr:
                    # Skip regular lists (handled by _extract_lists)
                    return True

                # Extract task list structure
                start_line = node.map[0] if node.map else None
                end_line = node.map[1] if node.map else None

                tasklist = {
                    "id": f"tasklist_{len(ctx)}",
                    "type": "bullet" if node.type == "bullet_list" else "ordered",
                    "start_line": start_line,
                    "end_line": end_line,
                    "section_id": self._find_section_id(start_line if start_line is not None else 0),
                    "items": [],
                }

                # Extract task list items
                tasklist["items"] = self._extract_tasklist_items(node)

                # Calculate metrics
                items_count = len(tasklist["items"])
                checked_count = sum(1 for item in tasklist["items"] if item.get("checked") is True)
                unchecked_count = sum(1 for item in tasklist["items"] if item.get("checked") is False)

                tasklist["items_count"] = items_count
                tasklist["checked_count"] = checked_count
                tasklist["unchecked_count"] = unchecked_count
                tasklist["has_mixed_task_items"] = any(
                    item.get("checked") is None for item in tasklist["items"]
                )

                ctx.append(tasklist)
                return False  # Don't recurse, we handled the entire task list

            return True

        self.process_tree(self.tree, tasklist_processor, tasklists)
        return tasklists

    def _detect_task_checkbox(self, paragraph_node) -> tuple[bool, bool]:
        """Detect task list checkbox from tasklists plugin.

        The plugin injects html_inline tokens with class="task-list-item-checkbox"
        and checked="checked" for checked items.

        Returns:
            (has_checkbox, is_checked) tuple
        """
        if not hasattr(paragraph_node, "children"):
            return False, False

        # Walk inline tokens looking for checkbox HTML
        for token in walk_tokens_iter([paragraph_node]):
            if token.type == "html_inline":
                content = getattr(token, "content", "")
                if "task-list-item-checkbox" in content:
                    is_checked = 'checked="checked"' in content
                    return True, is_checked

        return False, False

    def _extract_list_items(self, list_node, depth: int = 0, max_depth: int = 10) -> list[dict]:
        """Extract regular list items (no checkbox detection) with depth limit.

        Args:
            list_node: The list node to extract items from
            depth: Current recursion depth (default 0)
            max_depth: Maximum allowed depth to prevent stack overflow (default 10)

        Returns:
            List of item dicts, or empty list if depth exceeded
        """
        # Safety: Prevent stack overflow from deeply nested lists
        if depth >= max_depth:
            return []

        items = []

        for child in list_node.children or []:
            if child.type == "list_item":
                item = {"text": "", "children": [], "blocks": []}

                # Process list item children
                for item_child in child.children or []:
                    if item_child.type == "paragraph":
                        # Regular list item - just extract text (no checkbox detection)
                        text = self._get_text(item_child)
                        item["text"] = text

                    elif item_child.type in ["bullet_list", "ordered_list"]:
                        # Nested list (recursive with depth tracking)
                        item["children"] = self._extract_list_items(
                            item_child,
                            depth=depth + 1,
                            max_depth=max_depth
                        )

                    elif item_child.type in ["fence", "code_block", "blockquote", "table"]:
                        # Block elements within list item
                        item["blocks"].append({
                            "type": item_child.type,
                            "start_line": item_child.map[0] if item_child.map else None,
                            "end_line": item_child.map[1] if item_child.map else None,
                        })

                items.append(item)

        return items

    def _extract_tasklist_items(self, list_node, depth: int = 0, max_depth: int = 10) -> list[dict]:
        """Extract task list items WITH checkbox detection and depth limit.

        Args:
            list_node: The task list node to extract items from
            depth: Current recursion depth (default 0)
            max_depth: Maximum allowed depth to prevent stack overflow (default 10)

        Returns:
            List of task item dicts with checked status, or empty list if depth exceeded
        """
        # Safety: Prevent stack overflow from deeply nested lists
        if depth >= max_depth:
            return []

        items = []

        for child in list_node.children or []:
            if child.type == "list_item":
                item = {"text": "", "checked": None, "children": [], "blocks": []}

                # Process list item children
                for item_child in child.children or []:
                    if item_child.type == "paragraph":
                        # Detect task checkbox (plugin already removed [ ] from text)
                        has_checkbox, is_checked = self._detect_task_checkbox(item_child)
                        text = self._get_text(item_child)

                        if has_checkbox:
                            item["checked"] = is_checked
                            item["text"] = text.strip()
                        else:
                            # Regular list item mixed in task list
                            item["text"] = text

                    elif item_child.type in ["bullet_list", "ordered_list"]:
                        # Check if nested list is also a task list
                        nested_class = ""
                        if hasattr(item_child, 'attrs') and item_child.attrs:
                            nested_class = item_child.attrs.get('class', '')

                        if 'contains-task-list' in nested_class:
                            # Nested task list (recursive with depth tracking)
                            item["children"] = self._extract_tasklist_items(
                                item_child,
                                depth=depth + 1,
                                max_depth=max_depth
                            )
                        else:
                            # Regular nested list inside task list item
                            # Extract as regular list
                            item["children"] = self._extract_list_items(
                                item_child,
                                depth=depth + 1,
                                max_depth=max_depth
                            )

                    elif item_child.type in ["fence", "code_block", "blockquote", "table"]:
                        # Block elements within list item
                        item["blocks"].append({
                            "type": item_child.type,
                            "start_line": item_child.map[0] if item_child.map else None,
                            "end_line": item_child.map[1] if item_child.map else None,
                        })

                items.append(item)

        return items

    def _extract_tables(self) -> list[dict]:
        """Extract all tables with structure preserved."""
        tables = []

        def table_processor(node, ctx, level):
            if node.type == "table":
                start_line = node.map[0] if node.map else None
                end_line = node.map[1] if node.map else None

                # Extract raw table content (preserve original markdown)
                raw_content = ""
                if start_line is not None and end_line is not None:
                    raw_content = "\n".join(self.lines[start_line:end_line])

                table = {
                    "id": f"table_{len(ctx)}",
                    "raw_content": raw_content,  # Original markdown table (unchanged)
                    "headers": [],  # Parsed headers (polished)
                    "rows": [],     # Parsed rows (polished)
                    "align": None,  # Parsed alignment (polished)
                    "start_line": start_line,
                    "end_line": end_line,
                    "section_id": self._find_section_id(start_line if start_line is not None else 0),
                }

                # Extract headers, rows, and alignment (Phase 5: token-based, zero regex)
                for child in node.children or []:
                    if child.type == "thead":
                        for tr in child.children or []:
                            # Extract header text and alignment from th nodes
                            headers = []
                            aligns = []
                            for th in tr.children or []:
                                # Header text from inline children
                                header_text = "".join(
                                    grandchild.content for grandchild in (th.children or [])
                                )
                                headers.append(header_text)

                                # Alignment from th.attrs (markdown-it provides this)
                                align = "left"  # default
                                if hasattr(th, 'attrs') and th.attrs:
                                    style = th.attrs.get('style', '')
                                    if 'text-align:center' in style:
                                        align = "center"
                                    elif 'text-align:right' in style:
                                        align = "right"
                                    elif 'text-align:left' in style:
                                        align = "left"
                                aligns.append(align)

                            table["headers"] = headers
                            table["align"] = aligns
                    elif child.type == "tbody":
                        for tr in child.children or []:
                            row = [
                                "".join(grandchild.content for grandchild in (td.children or []))
                                for td in tr.children or []
                            ]
                            if row:
                                table["rows"].append(row)
                # Normalize align to column count (defensive against escaped pipe miscounts)
                # Safety guard: if header count is zero but there are body rows, use max row width
                header_cols = len(table["headers"])
                body_max_cols = (
                    max((len(r) for r in table["rows"]), default=0) if table["rows"] else 0
                )
                cols = max(header_cols, body_max_cols)

                # Guard against degenerate zero-column tables
                if cols == 0:
                    table["align"] = []
                    table["is_ragged"] = False  # Empty table is not ragged
                    ctx.append(table)
                    return False
                if table["align"]:
                    if len(table["align"]) < cols:
                        # Extend with 'left' for missing columns
                        table["align"] += ["left"] * (cols - len(table["align"]))
                    elif len(table["align"]) > cols:
                        # Truncate if we have too many (likely from escaped pipe miscount)
                        table["align"] = table["align"][:cols]
                else:
                    # Fallback: all left-aligned if alignment detection completely failed
                    table["align"] = ["left"] * cols

                # SECURITY: Detect ragged tables and alignment mismatches
                # Token-based detection first (more accurate)
                is_ragged = False
                align_mismatch = False

                # Check for ragged rows using tokenized data
                # Markdown-it fills missing cells with empty strings, so we check for that
                if table["rows"]:
                    for row in table["rows"]:
                        if len(row) != cols:
                            is_ragged = True
                            break
                        # Check for trailing empty cells which likely indicate missing cells in source
                        # A row like "| 1 |" becomes ["1", ""] for a 2-column table
                        if cols > 1 and row[-1] == "" and any(cell != "" for cell in row):
                            # Has trailing empty and at least one non-empty cell
                            is_ragged = True
                            break

                # Check for alignment mismatch
                if table["align"] and cols > 0:
                    if len(table["align"]) != cols:
                        align_mismatch = True

                table["is_ragged"] = is_ragged
                table["align_mismatch"] = align_mismatch
                table["table_valid_md"] = not is_ragged and not align_mismatch
                table["column_count"] = cols
                table["row_count"] = len(table["rows"])
                # Add heuristic metadata for alignment and ragged detection
                if table["align"]:
                    table["align_meta"] = {"heuristic": True}
                if is_ragged:
                    table["is_ragged_meta"] = {"heuristic": True}

                ctx.append(table)
                return False  # Don't recurse, we handled the table

            return True

        self.process_tree(self.tree, table_processor, tables)
        return tables

    def _extract_code_blocks(self) -> list[dict]:
        """Extract all code blocks (fenced and indented).

        Note: Fences inside table cells won't be parsed as fence nodes by markdown-it.
        They'll appear as text and may be caught by the indented code scanner below.
        This is expected behavior - markdown-it doesn't nest blocks in table cells.
        """
        # Return cached result if available
        if self._cache["code_blocks"] is not None:
            return self._cache["code_blocks"]

        blocks = []

        def code_processor(node, ctx, level):
            # Skip fence/code nodes that are inside table cells (defensive)
            # markdown-it shouldn't create these, but be safe
            parent = getattr(node, "parent", None)
            while parent:
                if getattr(parent, "type", "") in ("td", "th"):
                    return True  # Skip this node, it's in a table cell
                parent = getattr(parent, "parent", None)

            if node.type == "fence":
                block = {
                    "id": f"code_{len(ctx)}",
                    "type": "fenced",
                    "language": node.info if hasattr(node, "info") else "",
                    "content": node.content if hasattr(node, "content") else "",
                    "start_line": node.map[0] if node.map else None,
                    "end_line": node.map[1] if node.map else None,
                    "section_id": self._find_section_id(node.map[0] if node.map else 0),
                }
                ctx.append(block)
                return False
            if node.type == "code_block":
                block = {
                    "id": f"code_{len(ctx)}",
                    "type": "indented",
                    "language": "",
                    "content": node.content if hasattr(node, "content") else "",
                    "start_line": node.map[0] if node.map else None,
                    "end_line": node.map[1] if node.map else None,
                    "section_id": self._find_section_id(node.map[0] if node.map else 0),
                }
                ctx.append(block)
                return False

            return True

        self.process_tree(self.tree, code_processor, blocks)

        # Also extract indented code blocks that markdown-it might miss
        covered = set()
        for b in blocks:
            if b.get("start_line") is not None and b.get("end_line") is not None:
                covered.update(range(b["start_line"], b["end_line"] + 1))

        i, N = 0, len(self.lines)
        while i < N:
            line = self.lines[i]
            if (line.startswith("    ") or line.startswith("\t")) and i not in covered:
                start = i
                i += 1
                while i < N:
                    nxt = self.lines[i]
                    if not nxt.strip() or nxt.startswith("    ") or nxt.startswith("\t"):
                        i += 1
                    else:
                        break
                end = i - 1
                # Extract and process indented content using centralized slicing
                raw_lines = self._slice_lines_inclusive(start, end + 1)
                content = "\n".join(l[4:] if l.startswith("    ") else l[1:] for l in raw_lines)
                blocks.append(
                    {
                        "id": f"code_{len(blocks)}",
                        "type": "indented",
                        "language": "",
                        "content": content,
                        "start_line": start,
                        "end_line": end,
                        "section_id": self._find_section_id(start),
                    }
                )
                covered.update(range(start, end + 1))
            else:
                i += 1

        # Cache the result
        self._cache["code_blocks"] = blocks
        return blocks

    def _extract_headings(self) -> list[dict]:
        """Extract all headings with hierarchy using stable slug-based IDs.

        SECURITY: Only extracts top-level headings (not nested in lists/blockquotes)
        to prevent heading creepage vulnerabilities.
        """
        headings = []
        heading_stack = []
        slug_counts = {}  # Track slug usage for stable IDs

        # First pass: collect heading tokens at document level (level=0)
        # This prevents heading creepage from list continuations
        heading_tokens = []
        for token in self.tokens:
            if token.type == "heading_open" and token.level == 0:
                # This is a document-level heading, not nested
                heading_tokens.append(token)

        def heading_processor(node, ctx, level):
            if node.type == "heading":
                # SECURITY: Check if this heading corresponds to a document-level token
                # by verifying its line mapping matches a level=0 heading token
                is_document_level = False
                if node.map:
                    for h_token in heading_tokens:
                        if h_token.map and h_token.map[0] == node.map[0]:
                            is_document_level = True
                            break

                if not is_document_level:
                    # Skip nested headings (security: prevent creepage)
                    return False

                heading_level = self._heading_level(node)
                heading_text = self._get_text(node)
                base_slug = self._slugify_base(heading_text)

                # Generate stable ID with running count
                if base_slug in slug_counts:
                    slug_counts[base_slug] += 1
                    stable_slug = f"{base_slug}-{slug_counts[base_slug]}"
                else:
                    slug_counts[base_slug] = 1
                    stable_slug = base_slug

                stable_id = f"heading_{stable_slug}"

                # Find parent heading
                parent_id = None
                while heading_stack and heading_stack[-1]["level"] >= heading_level:
                    heading_stack.pop()
                if heading_stack:
                    parent_id = heading_stack[-1]["id"]

                # Add character offsets for RAG chunking
                line_num = node.map[0] if node.map else None
                start_char, end_char = (
                    self._span_from_lines(line_num, line_num)
                    if line_num is not None
                    else (None, None)
                )

                heading = {
                    "id": stable_id,
                    "level": heading_level,
                    "text": heading_text,
                    "line": line_num,
                    "slug": stable_slug,
                    "parent_heading_id": parent_id,
                    "start_char": start_char,
                    "end_char": end_char,
                }

                ctx.append(heading)
                heading_stack.append(heading)

            return True

        self.process_tree(self.tree, heading_processor, headings)
        return headings

    def _extract_links(self) -> list[dict]:
        """Extract links robustly using token parsing."""
        links = []

        # Process all tokens to find links
        for token in self.tokens:
            if token.type == "inline" and token.children:
                # Process inline tokens which contain links
                self._process_inline_tokens(token.children, links, token.map)

        return links

    def _process_inline_tokens(self, tokens, links, line_map):
        """Process inline tokens to extract links with improved line attribution."""
        i = 0
        softbreak_count = 0  # Track softbreaks for line offset

        while i < len(tokens):
            token = tokens[i]

            if token.type == "link_open":
                # Snapshot the break count at link_open for accurate line attribution
                link_line_offset = softbreak_count

                # Extract href from attributes
                href = token.attrGet("href") or ""

                # Validate link scheme for security (Phase 6 Task 6.1)
                scheme, is_allowed = security_validators.validate_link_scheme(href, self._effective_allowed_schemes)

                # Collect text until link_close and watch for embedded images
                text_parts = []
                saw_img = None
                img_title = ""
                i += 1
                while i < len(tokens) and tokens[i].type != "link_close":
                    if tokens[i].type == "text" or tokens[i].type == "code_inline":
                        text_parts.append(tokens[i].content)
                    elif tokens[i].type == "image":
                        # Capture image info for linked images like [![alt](img.jpg)](link.url)
                        img_src = tokens[i].attrGet("src") or ""
                        img_alt = (
                            getattr(tokens[i], "content", "") or tokens[i].attrGet("alt") or ""
                        )
                        img_title = tokens[i].attrGet("title") or ""
                        saw_img = {
                            "src": img_src,
                            "alt": img_alt,
                            "image_id": self._generate_image_id(
                                img_src, (line_map[0] + link_line_offset) if line_map else None
                            ),
                        }
                        text_parts.append(img_alt)  # Use alt text as link text
                    elif tokens[i].type in ("softbreak", "hardbreak"):
                        text_parts.append("\n")
                        softbreak_count += 1  # Still track breaks for subsequent tokens
                    i += 1

                text = "".join(text_parts)
                # Use snapshotted offset for link's line number
                line_num = (line_map[0] + link_line_offset) if line_map else None

                # Determine link type with enhanced scheme detection (Phase 6 Task 6.1)
                link_type = security_validators.classify_link_type(href)

                # Add the main link record with security metadata
                links.append(
                    {
                        "text": text,
                        "url": href,
                        "line": line_num,
                        "type": link_type,
                        "scheme": scheme,  # Security: track scheme
                        "allowed": is_allowed,  # Security: RAG safety flag
                    }
                )

                # If there was an embedded image, add a second record for joinability
                if saw_img:
                    # Get unified image metadata for consistency with first-class images
                    img_metadata = self._determine_image_metadata(saw_img["src"])
                    links.append(
                        {
                            "type": "image",
                            "url": saw_img["src"],
                            "src": saw_img["src"],  # Consistent with first-class images
                            "alt": saw_img["alt"],  # Consistent with first-class images
                            "title": img_title,
                            "text": saw_img["alt"],  # Keep for backward compatibility
                            "line": line_num,
                            "image_id": saw_img["image_id"],
                            "image_kind": img_metadata["image_kind"],  # Unified metadata
                            "format": img_metadata["format"],  # Unified metadata
                        }
                    )

            elif token.type == "image":
                # Snapshot the break count at image token for accurate line attribution
                image_line_offset = softbreak_count

                # Extract image attributes with stable ID
                src = token.attrGet("src") or ""
                alt = getattr(token, "content", "") or token.attrGet("alt") or ""
                title = token.attrGet("title") or ""

                # Use snapshotted offset for image's line number
                line_num = (line_map[0] + image_line_offset) if line_map else None

                # Generate stable ID (same as in _extract_images)
                image_id = self._generate_image_id(src, line_num)

                # Add standardized image reference to links with unified metadata
                img_metadata = self._determine_image_metadata(src)
                links.append(
                    {
                        "image_id": image_id,  # For joining with images table
                        "text": alt,  # Keep for backward compatibility
                        "url": src,  # Keep for backward compatibility
                        "src": src,  # Consistent with first-class images
                        "alt": alt,  # Consistent with first-class images
                        "title": title,
                        "line": line_num,
                        "type": "image",
                        "image_kind": img_metadata["image_kind"],  # Unified metadata
                        "format": img_metadata["format"],  # Unified metadata
                    }
                )

            elif token.type in ("softbreak", "hardbreak"):
                # Track line breaks for better attribution
                softbreak_count += 1

            i += 1

    def _generate_image_id(self, src: str, line: int | None) -> str:
        """Generate stable image ID from source and line number."""

        # Use src + line for stability (same image on different lines gets different ID)
        id_source = f"{src}|{line if line is not None else -1}"
        return hashlib.sha1(id_source.encode()).hexdigest()[:16]

    def _determine_image_metadata(self, src: str) -> dict[str, str]:
        """Determine image_kind and format from src URL for consistent metadata.

        Returns:
            Dictionary with 'image_kind' and 'format' keys.
        """
        # Determine image kind and parse data URIs (Phase 6 Task 6.1)
        if src.startswith("data:"):
            image_kind = "data"
            data_info = security_validators.parse_data_uri(src)
            # Extract format from mediatype (e.g., "image/png" → "png")
            mediatype = data_info.get("mediatype", "")
            format_type = mediatype.split("/")[1] if "/" in mediatype else "unknown"
        elif src.startswith(("http://", "https://")):
            image_kind = "external"
            # Extract format from extension for external URIs
            import os

            _, ext = os.path.splitext(src.lower())
            format_type = ext.lstrip(".") if ext else "unknown"
        else:
            image_kind = "local"
            # Extract format from extension for local paths
            import os

            _, ext = os.path.splitext(src.lower())
            format_type = ext.lstrip(".") if ext else "unknown"

        return {"image_kind": image_kind, "format": format_type}

    # Phase 6 Task 6.1: _classify_link_scheme() moved to security_validators.classify_link_type()

    # Phase 6 Task 6.1: _parse_data_uri() moved to security_validators.parse_data_uri()

    def _extract_images(self) -> list[dict]:
        """Extract all images as first-class elements with enhanced metadata.

        Returns unified image records with stable IDs that can be joined
        with image references in links.
        """
        # Return cached result if available
        if self._cache.get("images") is not None:
            return self._cache["images"]

        images = []
        seen_ids = set()  # Track to avoid duplicates

        # Process all tokens to find images
        for token in self.tokens:
            if token.type == "inline" and token.children:
                self._process_inline_tokens_for_images(token.children, images, token.map, seen_ids)

        # Cache the result
        self._cache["images"] = images
        return images

    def _process_inline_tokens_for_images(self, tokens, images, line_map, seen_ids):
        """Process inline tokens to extract images with enhanced metadata."""
        softbreak_count = 0  # Track softbreaks for line offset

        for i, token in enumerate(tokens):
            if token.type == "image":
                # Snapshot the break count at image token for accurate line attribution
                image_line_offset = softbreak_count

                # Extract image attributes with enhanced metadata
                src = token.attrGet("src") or ""
                alt = getattr(token, "content", "") or token.attrGet("alt") or ""
                title = token.attrGet("title") or ""

                # Use snapshotted offset for image's line number
                line_num = (line_map[0] + image_line_offset) if line_map else None

                # Generate stable ID
                image_id = self._generate_image_id(src, line_num)

                # Skip duplicates (same image on same line)
                if image_id in seen_ids:
                    continue
                seen_ids.add(image_id)

                # Validate image URL scheme for security (Phase 6 Task 6.1)
                scheme, is_allowed = security_validators.validate_link_scheme(src, self._effective_allowed_schemes)

                # Use centralized metadata determination for consistency
                img_metadata = self._determine_image_metadata(src)
                image_kind = img_metadata["image_kind"]
                format_type = img_metadata["format"]

                # Parse data URIs for additional metadata (Phase 6 Task 6.1)
                if image_kind == "data":
                    data_info = security_validators.parse_data_uri(src)
                else:
                    data_info = {}

                # Build unified image record
                image_record = {
                    "image_id": image_id,  # Stable ID for joining
                    "src": src,
                    "alt": alt,
                    "title": title,
                    "line": line_num,
                    "image_kind": image_kind,  # 'external'|'local'|'data'
                    "format": format_type,
                    "has_alt": bool(alt.strip()),
                    "has_title": bool(title.strip()),
                    "scheme": scheme,  # URL scheme for security validation
                    "allowed": is_allowed,  # Whether scheme is allowed
                }

                # Add data URI info if present
                if data_info:
                    # Phase 6 Task 6.1: Map new security_validators field names to old baseline names
                    image_record.update(
                        {
                            "media_type": data_info.get("mediatype"),  # New API uses "mediatype" not "media_type"
                            "encoding": data_info.get("encoding"),
                            "bytes_approx": data_info.get("size_bytes"),  # New API uses "size_bytes" not "bytes_approx"
                        }
                    )

                images.append(image_record)

            elif token.type in ("softbreak", "hardbreak"):
                # Track line breaks for better attribution
                softbreak_count += 1

    def _extract_blockquotes(self) -> list[dict]:
        """Extract all blockquotes from the document.

        Note: For richer nested data extraction, existing extractors can be reused
        with line-range filters on the children_blocks ranges.
        """
        blockquotes = []

        def blockquote_processor(node, ctx, level):
            if node.type == "blockquote":
                # Get blockquote content
                content = self._get_text(node)
                # Get line range
                start_line = node.map[0] if node.map else None
                end_line = node.map[1] if node.map else None

                # Summarize nested structures inside this blockquote
                counts = {"lists": 0, "tables": 0, "code": 0}
                for n in node.walk():
                    if n.type in ("bullet_list", "ordered_list"):
                        counts["lists"] += 1
                    elif n.type == "table":
                        counts["tables"] += 1
                    elif n.type in ("fence", "code_block"):
                        counts["code"] += 1

                ctx.append(
                    {
                        "content": content,
                        "start_line": start_line,
                        "end_line": end_line,
                        "section_id": self._find_section_id(start_line)
                        if start_line is not None
                        else None,
                        "children_summary": counts,
                        "children_blocks": [
                            {
                                "type": n.type,
                                "start_line": (n.map[0] if getattr(n, "map", None) else None),
                                "end_line": (n.map[1] if getattr(n, "map", None) else None),
                            }
                            for n in node.walk()
                            if n.type
                            in ("bullet_list", "ordered_list", "table", "fence", "code_block")
                        ],
                    }
                )

                # Don't recurse into blockquote children to avoid duplication
                return False

            return True  # Continue traversing for other nodes

        self.process_tree(self.tree, blockquote_processor, blockquotes)
        return blockquotes

    def _extract_footnotes(self) -> dict[str, Any]:
        """Extract footnote definitions and back-references with rich metadata.

        Returns:
            Dictionary with 'definitions' and 'references' lists.
            Definitions are deduplicated by label (last-writer-wins).
            Both label and numeric ID are extracted for stability.
        """
        # Use dict for deduplication of definitions
        definitions_dict = {}
        references = []

        def get_footnote_ids(node):
            """Extract both label (stable) and numeric id from footnote node.
            Prefer label for stability, but include both."""
            label = None
            numeric_id = None

            if hasattr(node, "token") and node.token:
                meta = getattr(node.token, "meta", {})
                label = meta.get("label", "")
                numeric_id = meta.get("id", "")

            if not label and hasattr(node, "meta"):
                meta = getattr(node, "meta", {})
                label = meta.get("label", "")
                if not numeric_id:
                    numeric_id = meta.get("id", "")

            # Use label as primary key, fallback to numeric id
            key = label if label else numeric_id
            return key, label, numeric_id

        def footnote_processor(node, ctx, level):
            # Handle footnote references (inline)
            if node.type == "footnote_ref":
                key, label, numeric_id = get_footnote_ids(node)
                line_num = node.map[0] if node.map else None

                ctx["references"].append(
                    {
                        "label": label if label else key,  # Prefer label
                        "id": numeric_id if numeric_id else key,  # Include numeric id
                        "line": line_num,
                        "section_id": self._find_section_id(line_num)
                        if line_num is not None
                        else None,
                    }
                )

            # Handle footnote definitions
            elif node.type == "footnote":
                key, label, numeric_id = get_footnote_ids(node)

                # Skip if no identifier found
                if not key:
                    return True

                start_line = node.map[0] if node.map else None
                end_line = node.map[1] if node.map else None
                # Get text from the footnote content (recursively)
                content = self._get_text(node)

                # Collect nested structures for richer analysis
                nested_structures = []
                for child in node.walk():
                    if child.type in (
                        "bullet_list",
                        "ordered_list",
                        "table",
                        "fence",
                        "code_block",
                    ):
                        if hasattr(child, "map") and child.map:
                            nested_structures.append(
                                {
                                    "type": child.type,
                                    "start_line": child.map[0],
                                    "end_line": child.map[1],
                                }
                            )

                # Use dict for deduplication (last-writer-wins)
                ctx["definitions_dict"][key] = {
                    "label": label if label else key,  # Stable identifier
                    "id": numeric_id if numeric_id else key,  # Numeric identifier
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": content,
                    "byte_length": len(content.encode("utf-8")) if content else 0,
                    "nested_structures": nested_structures,
                    "section_id": self._find_section_id(start_line)
                    if start_line is not None
                    else None,
                }

            return True  # Continue traversing

        context = {"definitions_dict": definitions_dict, "references": references}

        self.process_tree(self.tree, footnote_processor, context)

        # Convert definitions dict to list
        return {
            "definitions": list(context["definitions_dict"].values()),
            "references": context["references"],
        }

    def _extract_html(self) -> dict[str, list[dict]]:
        """Extract both HTML blocks and inline HTML (always, for security scanning).

        RAG Safety: Always extracts HTML but marks with 'allowed' flag based on config.

        Returns:
            Dictionary with 'blocks' and 'inline' lists.
            Inline HTML includes <span>, <em>, <strong>, etc. that appear in paragraphs.
        """
        html_blocks = []
        html_inline_dict = {}  # Use dict for deduplication

        # RAG Safety: Check if HTML is allowed by configuration
        html_allowed = self.config.get("allows_html", False)

        def html_processor(node, ctx, level):
            # Handle HTML blocks
            if node.type == "html_block":
                start_line = node.map[0] if node.map else None
                end_line = node.map[1] if node.map else None
                content = getattr(node, "content", "") or ""

                # Extract raw HTML content from original lines if map available
                raw_content = content
                if start_line is not None and end_line is not None:
                    raw_content = self._slice_lines_raw(start_line, end_line)

                ctx["blocks"].append(
                    {
                        "content": content,
                        "raw_content": raw_content,
                        "start_line": start_line,
                        "end_line": end_line,
                        "inline": False,  # This is a block element
                        "allowed": ctx["html_allowed"],  # RAG Safety: flag if HTML is allowed
                        "section_id": self._find_section_id(start_line)
                        if start_line is not None
                        else None,
                        "tag_hints": self._extract_html_tag_hints(content),
                    }
                )
                return False  # Don't recurse into HTML content

            # Skip inline HTML during tree traversal - we'll get them from tokens
            return True

        context = {
            "blocks": html_blocks,
            "inline_dict": html_inline_dict,
            "html_allowed": html_allowed,  # Pass allowed flag to processor
        }

        self.process_tree(self.tree, html_processor, context)

        # Process inline tokens which contain html_inline with proper line info
        for token in self.tokens:
            if token.type == "inline" and token.children:
                line_num = token.map[0] if token.map else None

                for child in token.children:
                    if child.type == "html_inline":
                        content = getattr(child, "content", "") or ""
                        if content.strip():
                            # Create unique key for deduplication
                            key = (content, line_num)
                            html_inline_dict[key] = {
                                "content": content,
                                "line": line_num,
                                "inline": True,
                                "allowed": html_allowed,  # RAG Safety: flag if HTML is allowed
                                "section_id": self._find_section_id(line_num)
                                if line_num is not None
                                else None,
                                "tag_hints": self._extract_html_tag_hints(content),
                            }

        # Convert dict to list for final output
        html_inline = list(html_inline_dict.values())

        # Return both blocks and inline HTML
        return {"blocks": html_blocks, "inline": html_inline}

    def _extract_html_tag_hints(self, html_content: str) -> list[str]:
        """Extract HTML tag names for downstream sanitizer hints."""
        import re

        # Simple regex to find opening tags
        tags = re.findall(r"<(\w+)", html_content)
        return list(set(tags))  # Deduplicate

    def _build_mappings(self) -> dict[str, Any]:
        """Build line-to-content mappings.

        Phase 6: Pure token-based classification using AST code blocks.
        No ContentContext - classification derived entirely from markdown-it tokens.
        """
        mappings = {
            "line_to_type": {},
            "line_to_section": {},
            "prose_lines": [],
            "code_lines": [],
            "code_blocks": [],  # Expose code blocks with language
        }

        # Initialize all lines as prose (default assumption)
        for i in range(len(self.lines)):
            mappings["prose_lines"].append(i)
            mappings["line_to_type"][str(i)] = "prose"

        # Build section mappings directly to avoid circular dependency
        sections = self._sections or self._get_cached("sections", self._extract_sections)
        for section in sections:
            if section["start_line"] is not None and section["end_line"] is not None:
                for line_num in range(section["start_line"], section["end_line"] + 1):
                    if 0 <= line_num < len(self.lines):  # Bounds check
                        mappings["line_to_section"][str(line_num)] = section["id"]

        # Cache mappings for O(1) lookups in _find_section_id
        self._mappings_cache = mappings

        # Pure token-based code block classification (Phase 6)
        # Extract code blocks from AST and mark those lines as code
        try:
            code_blocks = self._get_cached("code_blocks", self._extract_code_blocks)
            for b in code_blocks:
                s, e = b.get("start_line"), b.get("end_line")
                if s is None or e is None:
                    continue

                # Add to code_blocks list for mappings
                # Note: structure uses exclusive end_line, but mappings uses inclusive for backward compat
                mappings["code_blocks"].append({
                    "start_line": s,
                    "end_line": e - 1,  # Convert exclusive to inclusive
                    "language": b.get("language"),
                })

                # Mark these lines as code (end_line from structure is exclusive)
                for ln in range(s, e):
                    mappings["line_to_type"][str(ln)] = "code"
                    # Remove from prose_lines if present
                    if ln in mappings["prose_lines"]:
                        mappings["prose_lines"].remove(ln)
                    # Add to code_lines if not present
                    if ln not in mappings["code_lines"]:
                        mappings["code_lines"].append(ln)
        except Exception:
            pass

        return mappings

    def _plain_text_in_range(self, start_line: int, end_line: int) -> str:
        """Extract plain text from a line range with proper paragraph boundaries.

        Behavior: Detects blank lines between segments and inserts '\n\n'
        for paragraph boundaries. Consecutive segments are joined with a space.
        This preserves paragraph structure in the plain text output.
        """
        parts: list[str] = []
        last_end = None

        for s, e, txt in getattr(self, "_text_segments", []):
            if e < start_line or s > end_line:
                continue

            # Check for gaps between segments
            if last_end is not None:
                if s > last_end + 1:
                    # There's at least one blank line between segments
                    parts.append("\n\n")  # Paragraph boundary
                elif s == last_end + 1:
                    # Consecutive lines, no blank line
                    parts.append(" ")  # Join with space
                # else: same line, no separator needed

            parts.append(txt)
            last_end = e

        return "".join(parts).strip()

    def _collect_text_segments(self) -> None:
        """Collect text-ish segments with proper line ranges for better paragraph boundary detection."""
        self._text_segments = text_utils.collect_text_segments(self.tokens)

    # Utility methods

    def _heading_level(self, node) -> int:
        """Robust heading level detection (ATX + Setext)."""
        tok = getattr(node, "token", None)
        tag = getattr(tok, "tag", "") if tok else ""
        if tag.startswith("h") and tag[1:].isdigit():
            return int(tag[1:])
        m = getattr(node, "markup", "")
        if set(m) == {"#"} and 1 <= len(m) <= 6:
            return len(m)
        return 1

    def _get_text(self, node) -> str:
        """Get all text content from a node and its children, preserving breaks and alt text."""
        text_parts = []

        def text_collector(n, ctx, level):
            t = getattr(n, "type", "")
            if t == "text" and getattr(n, "content", "") or t == "code_inline" and getattr(n, "content", ""):
                ctx.append(n.content)
            elif t == "softbreak" or t == "hardbreak":
                ctx.append("\n")
            elif t == "image":
                # Prefer token.content (canonical alt text), fall back to attrGet('alt')
                alt = ""
                tok = getattr(n, "token", None)
                if tok:
                    try:
                        # Prefer token.content - this is where markdown-it puts the canonical alt text
                        alt = getattr(tok, "content", "") or tok.attrGet("alt") or ""
                    except Exception:
                        alt = ""
                if alt:
                    ctx.append(alt)
            return True

        self.process_tree(node, text_collector, text_parts)
        return "".join(text_parts)

    def _check_path_traversal(self, url: str) -> bool:
        """
        Comprehensive path traversal detection.

        Args:
            url: URL or path to check

        Returns:
            True if path traversal detected, False otherwise
        """
        if not url:
            return False

        # URL decode first (handle multiple encoding levels)
        decoded = url
        for _ in range(3):  # Handle triple encoding
            try:
                prev = decoded
                decoded = urllib.parse.unquote(decoded)
                if prev == decoded:
                    break
            except:
                return True  # Suspicious if can't decode

        # Convert to lowercase for pattern matching
        decoded_lower = decoded.lower()

        # Check for file:// scheme first (always suspicious in web context)
        if decoded_lower.startswith("file://"):
            return True

        # Check multiple path traversal patterns
        patterns = [
            "../",
            "..\\",  # Direct traversal
            "..%2f",
            "..%5c",  # Mixed encoding
            "%2e%2e/",
            "%2e%2e\\",  # Fully encoded
            "%2e%2e%2f",
            "%2e%2e%5c",  # Fully encoded variations
            "%252e%252e",  # Double encoded
            "..;",
            "..//",  # Variations
            "//",
            "\\\\",  # UNC paths
            "%5c%5c",  # Encoded UNC paths
            "file://",
            "file:\\",  # File protocol
        ]

        # Check for Windows drive letters
        if re.match(r"^[a-z]:[/\\]", decoded_lower):
            return True

        for pattern in patterns:
            if pattern in decoded_lower:
                return True

        # Normalize path and check
        try:
            # Use posixpath for consistent handling
            normalized = posixpath.normpath(decoded)

            # Check if path tries to escape
            if normalized.startswith(".."):
                return True
            if "/../" in normalized or "/.." in normalized:
                return True

            # Check for absolute paths that might be suspicious
            if normalized.startswith("/etc/") or normalized.startswith("/proc/"):
                return True

        except:
            return True  # Suspicious if can't normalize

        return False

    def _check_unicode_spoofing(self, text: str) -> dict[str, bool]:
        """
        Detect Unicode spoofing attempts including BiDi and confusables with size limits.

        Phase 6 Task 6.1: Wrapper around security_validators.detect_unicode_issues()
        with additional BiDi controls check and legacy field names for backward compatibility.

        Args:
            text: Text to check

        Returns:
            Dictionary with spoofing indicators (legacy field names for backward compatibility)
        """
        # Skip very large texts
        if not text or len(text) > 100000:
            return {
                "has_bidi": False,
                "has_confusables": False,
                "has_mixed_scripts": False,
                "has_invisible_chars": False,
                "has_zero_width": False,
            }

        # Use centralized security validator
        unicode_issues = security_validators.detect_unicode_issues(text, max_scan_bytes=10240)

        # Check for BiDi control characters (legacy check, not in centralized validator)
        has_bidi_controls = False
        for char in self._BIDI_CONTROLS:
            if char in text[:10000]:  # Check first 10KB only
                has_bidi_controls = True
                break

        # Map to legacy field names for backward compatibility
        return {
            "has_bidi": unicode_issues["has_bidi_override"] or has_bidi_controls,
            "has_confusables": unicode_issues["has_confusables"],
            "has_mixed_scripts": unicode_issues["has_mixed_scripts"],
            "has_invisible_chars": unicode_issues["has_zero_width"],
            "has_zero_width": unicode_issues["has_zero_width"],
        }

    # Phase 6 Task 6.1: _check_prompt_injection() moved to security_validators.check_prompt_injection()

    # Phase 6 Task 6.1: _validate_link_scheme() moved to security_validators.validate_link_scheme()

    def _check_footnote_injection(self, footnotes: dict) -> bool:
        """
        Check for prompt injection in footnote definitions.

        Args:
            footnotes: Dictionary containing footnote definitions

        Returns:
            True if injection detected in footnotes, False otherwise
        """
        if not footnotes or not isinstance(footnotes, dict):
            return False

        definitions = footnotes.get("definitions", [])
        for footnote in definitions:
            content = footnote.get("content", "")
            if security_validators.check_prompt_injection(content):
                return True

            # Also check for oversized footnotes (potential payload hiding)
            if len(content) > 512:
                # Check more aggressively in long footnotes
                if re.search(
                    r"(system|prompt|instruction|ignore|override)", content, re.IGNORECASE
                ):
                    return True

        return False

    def _slugify_base(self, text: str) -> str:
        """Convert text to base slug format without de-duplication for stable IDs."""
        import re
        import unicodedata

        s = unicodedata.normalize("NFKD", text).lower()
        # First replace slashes and spaces with hyphens
        s = re.sub(r"[\s/]+", "-", s)
        # Then remove other non-word characters (but keep hyphens)
        s = re.sub(r"[^\w-]", "", s).strip()
        # Clean up multiple hyphens
        s = re.sub(r"-+", "-", s)
        # Remove leading/trailing hyphens
        s = s.strip("-")
        return s or "untitled"  # Fallback for empty slugs

    def _find_section_id(self, line_number: int) -> str | None:
        """Find which section a line belongs to.

        Optimized to use line mappings when available (O(1) lookup),
        falls back to section iteration for early/unmapped lookups.
        """
        # Try to use cached line mappings first (O(1) lookup)
        if hasattr(self, "_mappings_cache") and self._mappings_cache:
            section_id = self._mappings_cache.get("line_to_section", {}).get(str(line_number))
            if section_id:
                return section_id

        # Fall back to section iteration (O(n) lookup)
        # Ensure sections are extracted (uses cache if available)
        sections = self._sections or self._get_cached("sections", self._extract_sections)

        for section in sections:
            if section["start_line"] is not None and section["end_line"] is not None:
                if section["start_line"] <= line_number <= section["end_line"]:
                    return section["id"]
        return None

    def _has_child_type(self, node, types) -> bool:
        """Check if node has children of specified type(s)."""
        return text_utils.has_child_type(node, types)

    def _build_line_offsets(self) -> None:
        """Build array of character offsets for each line start."""
        self._line_start_offsets, self._total_chars_with_lf = line_utils.build_line_offsets(self.lines)

    def _span_from_lines(
        self, start_line: int | None, end_line: int | None
    ) -> tuple[int | None, int | None]:
        """Convert line numbers to character offsets.

        Args:
            start_line: Starting line number (0-based)
            end_line: Ending line number (inclusive, 0-based)

        Returns:
            Tuple of (start_char, end_char) positions
        """
        if start_line is None or end_line is None:
            return None, None
        if start_line < 0 or start_line >= len(self._line_start_offsets):
            return None, None

        start_char = self._line_start_offsets[start_line]

        # Handle end_line
        if end_line + 1 < len(self._line_start_offsets):
            end_char = self._line_start_offsets[end_line + 1]
        else:
            end_char = self._total_chars_with_lf

        return start_char, end_char

    def to_ir(self, source_id: str = "") -> DocumentIR:
        """
        Convert parsed document to Document IR for RAG chunking.

        The Document IR is a source-agnostic representation that serves as
        the contract between parsers (Markdown, HTML, PDF) and chunkers.

        Schema Version: md-ir@1.0.0

        Args:
            source_id: Source identifier (file path, URL, or hash)

        Returns:
            DocumentIR object ready for chunking

        Example:
            ```python
            parser = MarkdownParserCore(content)
            result = parser.parse()
            ir = parser.to_ir(source_id="docs/intro.md")

            # Later: pass to chunker
            chunks = chunker.chunk(ir, policy)
            ```
        """
        import hashlib

        # Parse if not already done
        if not hasattr(self, '_parsed') or not self._parsed:
            self.parse()

        # Compute content hash
        normalized_content = self.content.encode('utf-8', errors='replace')
        content_hash = hashlib.sha256(normalized_content).hexdigest()

        # Extract security metadata
        result = self.parse()
        security_meta = result['metadata']['security']

        # Build document tree from sections
        root = DocNode(
            id="root",
            type="section",
            text=None,
            meta={"title": "Document Root"},
            children=self._build_ir_nodes()
        )

        # Build link graph (section_id -> [target_section_ids])
        link_graph = self._build_link_graph()

        return DocumentIR(
            schema_version="md-ir@1.0.0",
            source_id=source_id or content_hash[:16],
            source_type="markdown",
            content_hash=content_hash,
            allows_html=self.allows_html,
            security=security_meta,
            frontmatter=result['metadata'].get('frontmatter', {}),
            root=root,
            link_graph=link_graph,
        )

    def _build_ir_nodes(self) -> list[DocNode]:
        """Build DocNode tree from parsed structures."""
        nodes = []

        # Get parsed structures
        sections = self._get_cached("sections", self._extract_sections)

        for section in sections:
            # Build section node
            section_node = DocNode(
                id=section['id'],
                type="section",
                text=section.get('text_content'),
                meta={
                    "title": section['title'],
                    "level": section['level'],
                    "slug": section['slug'],
                },
                span=None,  # Character spans can be added later if needed
                line_span=(section.get('start_line'), section.get('end_line')),
                children=[],
            )
            nodes.append(section_node)

        return nodes

    def _build_link_graph(self) -> dict[str, list[str]]:
        """Build internal link adjacency list for retrieval expansion."""
        link_graph = {}

        links = self._get_cached("links", self._extract_links)
        sections = self._get_cached("sections", self._extract_sections)

        # Map line numbers to section IDs
        line_to_section = {}
        for section in sections:
            if section.get('start_line') is not None and section.get('end_line') is not None:
                for line in range(section['start_line'], section['end_line'] + 1):
                    line_to_section[line] = section['id']

        # Build adjacency list for internal links
        for link in links:
            line = link.get('line')
            if line is None:
                continue

            source_section = line_to_section.get(line)
            if not source_section:
                continue

            # Check if it's an anchor link (internal reference)
            url = link.get('url', '')
            if url.startswith('#'):
                # Extract target slug from anchor
                target_slug = url.lstrip('#')
                # Find target section by slug
                for section in sections:
                    if section.get('slug') == target_slug:
                        target_id = section['id']
                        if source_section not in link_graph:
                            link_graph[source_section] = []
                        if target_id not in link_graph[source_section]:
                            link_graph[source_section].append(target_id)
                        break

        return link_graph
