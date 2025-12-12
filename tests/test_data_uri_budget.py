"""Tests for data URI budget enforcement - P0 security fix.

These tests verify that the parser correctly enforces size limits on data URIs
to prevent payload hiding attacks.
"""


from doxstrux.markdown.budgets import URIBudget, get_max_data_uri_size
from doxstrux.markdown_parser_core import MarkdownParserCore


class TestURIBudgetBasics:
    """Tests for URIBudget class."""

    def test_budget_respects_profile(self) -> None:
        """Budget limits should vary by security profile."""
        strict_budget = URIBudget("strict")
        moderate_budget = URIBudget("moderate")
        permissive_budget = URIBudget("permissive")

        # Strict should be most restrictive
        assert strict_budget.max_uri_size <= moderate_budget.max_uri_size
        assert moderate_budget.max_uri_size <= permissive_budget.max_uri_size

    def test_budget_tracks_size(self) -> None:
        """Budget should track cumulative size."""
        budget = URIBudget("permissive")
        budget.add_uri(100)
        budget.add_uri(200)
        assert budget.current_size == 300
        assert budget.current_count == 2


class TestDataURISizeEnforcement:
    """Tests for P0-3: Data URI size enforcement in parser."""

    def test_small_data_uri_allowed_in_permissive(self) -> None:
        """Small data URIs should be allowed in permissive mode."""
        # Note: strict mode blocks ALL data URIs (limit=0), so test permissive
        small_data_uri = "data:image/png;base64,iVBORw0KGgo="
        content = f"![Image]({small_data_uri})"

        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser.parse()

        security = result["metadata"]["security"]
        assert security["statistics"]["has_data_uri_images"] is True
        # Should NOT be blocked for small URI in permissive mode
        assert security.get("embedding_blocked") is not True

    def test_strict_mode_blocks_all_data_uris(self) -> None:
        """Strict mode should block ALL data URIs (limit=0)."""
        small_data_uri = "data:image/png;base64,iVBORw0KGgo="
        content = f"![Image]({small_data_uri})"

        parser = MarkdownParserCore(content, security_profile="strict")
        result = parser.parse()

        security = result["metadata"]["security"]
        # Strict mode has limit=0, so ANY data URI is blocked
        assert security.get("embedding_blocked") is True, (
            "Strict mode must block all data URIs"
        )

    def test_large_data_uri_blocked_strict(self) -> None:
        """Large data URIs should be blocked in strict mode."""
        # Get the strict limit
        limit = get_max_data_uri_size("strict")

        # Create a data URI larger than the limit
        large_payload = "A" * (limit + 1000)
        large_data_uri = f"data:image/png;base64,{large_payload}"
        content = f"![Image]({large_data_uri})"

        parser = MarkdownParserCore(content, security_profile="strict")
        result = parser.parse()

        security = result["metadata"]["security"]
        # Should be blocked due to oversized data URI
        assert security.get("embedding_blocked") is True, (
            "Large data URI must trigger embedding_blocked"
        )
        assert "embedding_blocked_reason" in security

        # Should have warning about oversized URI
        warnings = security.get("warnings", [])
        oversized_warnings = [w for w in warnings if w.get("type") == "data_uri_oversized"]
        assert len(oversized_warnings) > 0, "Should have data_uri_oversized warning"

    def test_multiple_data_uris_cumulative(self) -> None:
        """Multiple data URIs should count against total budget."""
        # Get limits - total is 10x single
        limit = get_max_data_uri_size("permissive")

        # Create several medium-sized URIs that together exceed total limit
        single_size = limit // 2  # Half the single limit
        payload = "A" * single_size
        data_uri = f"data:image/png;base64,{payload}"

        # Create enough images to exceed total budget
        num_images = 25  # 25 * (limit/2) = 12.5x limit > 10x total limit
        images = "\n".join([f"![Image{i}]({data_uri})" for i in range(num_images)])
        content = f"# Test\n\n{images}"

        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser.parse()

        security = result["metadata"]["security"]
        # Total budget should be exceeded
        assert security.get("embedding_blocked") is True, (
            "Cumulative data URI size must trigger embedding_blocked"
        )


class TestDataURIWarnings:
    """Tests for data URI warning generation."""

    def test_data_uri_warning_includes_size(self) -> None:
        """Data URI warnings should include size information."""
        data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="
        content = f"![Test]({data_uri})"

        parser = MarkdownParserCore(content, security_profile="strict")
        result = parser.parse()

        warnings = result["metadata"]["security"]["warnings"]
        data_uri_warnings = [w for w in warnings if w.get("type") == "data_uri_image"]

        assert len(data_uri_warnings) > 0
        # Warning should include size
        assert "size" in data_uri_warnings[0]


class TestProfileDifferences:
    """Tests for different security profiles."""

    def test_strict_more_restrictive_than_moderate(self) -> None:
        """Strict profile should block smaller URIs than moderate."""
        strict_limit = get_max_data_uri_size("strict")
        moderate_limit = get_max_data_uri_size("moderate")

        # Create URI between strict and moderate limits
        between_size = strict_limit + ((moderate_limit - strict_limit) // 2)
        payload = "A" * between_size
        data_uri = f"data:image/png;base64,{payload}"
        content = f"![Test]({data_uri})"

        # Strict should block
        strict_parser = MarkdownParserCore(content, security_profile="strict")
        strict_result = strict_parser.parse()
        assert strict_result["metadata"]["security"].get("embedding_blocked") is True

        # Moderate should allow
        moderate_parser = MarkdownParserCore(content, security_profile="moderate")
        moderate_result = moderate_parser.parse()
        assert moderate_result["metadata"]["security"].get("embedding_blocked") is not True
