"""Tests for budget tracking and enforcement.

Tests NodeBudget, CellBudget, URIBudget classes and budget helper functions.
"""

import pytest
from doxstrux.markdown.budgets import (
    NodeBudget,
    CellBudget,
    URIBudget,
    get_max_data_uri_size,
    get_max_injection_scan_chars,
    MAX_NODES,
    MAX_TABLE_CELLS,
)
from doxstrux.markdown.exceptions import MarkdownSizeError


class TestGetMaxDataUriSize:
    """Tests for get_max_data_uri_size() SSOT helper."""

    def test_strict_profile(self):
        """Strict profile returns 0 (data URIs blocked)."""
        result = get_max_data_uri_size("strict")
        assert result == 0

    def test_moderate_profile(self):
        """Moderate profile returns expected limit."""
        result = get_max_data_uri_size("moderate")
        assert result == 10240  # 10KB

    def test_permissive_profile(self):
        """Permissive profile returns larger limit."""
        result = get_max_data_uri_size("permissive")
        assert result == 102400  # 100KB

    def test_unknown_profile_raises(self):
        """Unknown profile raises ValueError."""
        with pytest.raises(ValueError, match="Unknown profile"):
            get_max_data_uri_size("nonexistent")


class TestGetMaxInjectionScanChars:
    """Tests for get_max_injection_scan_chars() SSOT helper."""

    def test_strict_profile(self):
        """Strict profile scans the most characters."""
        result = get_max_injection_scan_chars("strict")
        assert result == 4096

    def test_moderate_profile(self):
        """Moderate profile scans moderate amount."""
        result = get_max_injection_scan_chars("moderate")
        assert result == 2048

    def test_permissive_profile(self):
        """Permissive profile scans the least."""
        result = get_max_injection_scan_chars("permissive")
        assert result == 1024

    def test_unknown_profile_raises(self):
        """Unknown profile raises ValueError."""
        with pytest.raises(ValueError, match="Unknown profile"):
            get_max_injection_scan_chars("nonexistent")


class TestNodeBudget:
    """Tests for NodeBudget class."""

    def test_init_default_moderate(self):
        """Default profile is moderate."""
        budget = NodeBudget()
        assert budget.max_nodes == MAX_NODES["moderate"]
        assert budget.current_count == 0
        assert budget.profile == "moderate"

    def test_init_strict(self):
        """Strict profile has lower limit."""
        budget = NodeBudget("strict")
        assert budget.max_nodes == MAX_NODES["strict"]

    def test_init_permissive(self):
        """Permissive profile has higher limit."""
        budget = NodeBudget("permissive")
        assert budget.max_nodes == MAX_NODES["permissive"]

    def test_init_unknown_falls_to_moderate(self):
        """Unknown profile falls back to moderate."""
        budget = NodeBudget("unknown")
        assert budget.max_nodes == MAX_NODES["moderate"]

    def test_increment_within_budget(self):
        """Increment within budget succeeds."""
        budget = NodeBudget("strict")
        budget.increment(100)
        assert budget.current_count == 100
        budget.increment(100)
        assert budget.current_count == 200

    def test_increment_exceeds_budget_raises(self):
        """Increment exceeding budget raises MarkdownSizeError."""
        budget = NodeBudget("strict")
        budget.current_count = MAX_NODES["strict"] - 1
        with pytest.raises(MarkdownSizeError, match="Node count.*exceeds budget"):
            budget.increment(2)

    def test_check_within_budget(self):
        """check() returns True when within budget."""
        budget = NodeBudget("strict")
        assert budget.check() is True
        budget.increment(100)
        assert budget.check() is True

    def test_check_over_budget(self):
        """check() returns False when over budget."""
        budget = NodeBudget("strict")
        budget.current_count = MAX_NODES["strict"] + 1
        assert budget.check() is False

    def test_reset(self):
        """reset() clears the count."""
        budget = NodeBudget()
        budget.increment(100)
        assert budget.current_count == 100
        budget.reset()
        assert budget.current_count == 0


class TestCellBudget:
    """Tests for CellBudget class."""

    def test_init_default_moderate(self):
        """Default profile is moderate."""
        budget = CellBudget()
        assert budget.max_cells == MAX_TABLE_CELLS["moderate"]
        assert budget.current_count == 0
        assert budget.profile == "moderate"

    def test_init_strict(self):
        """Strict profile has lower limit."""
        budget = CellBudget("strict")
        assert budget.max_cells == MAX_TABLE_CELLS["strict"]

    def test_init_permissive(self):
        """Permissive profile has higher limit."""
        budget = CellBudget("permissive")
        assert budget.max_cells == MAX_TABLE_CELLS["permissive"]

    def test_add_table_within_budget(self):
        """add_table within budget succeeds."""
        budget = CellBudget("strict")
        budget.add_table(10, 5)  # 50 cells
        assert budget.current_count == 50
        budget.add_table(20, 5)  # 100 more cells
        assert budget.current_count == 150

    def test_add_table_exceeds_budget_raises(self):
        """add_table exceeding budget raises MarkdownSizeError."""
        budget = CellBudget("strict")
        # strict limit is 1000 cells
        with pytest.raises(MarkdownSizeError, match="Table cell count.*exceeds budget"):
            budget.add_table(100, 20)  # 2000 cells > 1000

    def test_check_within_budget(self):
        """check() returns True when within budget."""
        budget = CellBudget("strict")
        budget.add_table(10, 10)  # 100 cells
        assert budget.check() is True

    def test_check_over_budget(self):
        """check() returns False when over budget."""
        budget = CellBudget("strict")
        budget.current_count = MAX_TABLE_CELLS["strict"] + 1
        assert budget.check() is False

    def test_reset(self):
        """reset() clears the count."""
        budget = CellBudget()
        budget.add_table(10, 10)
        assert budget.current_count == 100
        budget.reset()
        assert budget.current_count == 0


class TestURIBudget:
    """Tests for URIBudget class."""

    def test_init_default_moderate(self):
        """Default profile is moderate."""
        budget = URIBudget()
        assert budget.max_uri_size == 10240  # 10KB per SECURITY_PROFILES
        assert budget.max_total_size == 10240 * 10  # 100KB total
        assert budget.current_count == 0
        assert budget.current_size == 0

    def test_init_strict_blocks_data_uris(self):
        """Strict profile blocks data URIs (max_uri_size=0)."""
        budget = URIBudget("strict")
        assert budget.max_uri_size == 0
        assert budget.max_total_size == 0

    def test_init_permissive(self):
        """Permissive profile allows larger URIs."""
        budget = URIBudget("permissive")
        assert budget.max_uri_size == 102400  # 100KB per SECURITY_PROFILES

    def test_add_uri_within_budget(self):
        """add_uri within budget succeeds."""
        budget = URIBudget("moderate")
        budget.add_uri(1000)
        assert budget.current_count == 1
        assert budget.current_size == 1000
        budget.add_uri(2000)
        assert budget.current_count == 2
        assert budget.current_size == 3000

    def test_add_uri_exceeds_single_limit_raises(self):
        """Single URI exceeding limit raises MarkdownSizeError."""
        budget = URIBudget("moderate")
        with pytest.raises(MarkdownSizeError, match="Data URI size.*exceeds limit"):
            budget.add_uri(10241)  # Just over 10KB

    def test_add_uri_exceeds_total_limit_raises(self):
        """Total URI size exceeding limit raises MarkdownSizeError."""
        budget = URIBudget("moderate")
        # max_total_size = 10240 * 10 = 102400 (100KB total)
        # Add URIs that are within single limit but will exceed total
        for _ in range(10):
            budget.add_uri(10000)  # 100KB total, under 102.4KB limit
        # Next one pushes over
        with pytest.raises(MarkdownSizeError, match="Total data URI size.*exceeds limit"):
            budget.add_uri(10000)  # 110KB total > 102.4KB limit

    def test_strict_blocks_any_uri(self):
        """Strict profile blocks any data URI."""
        budget = URIBudget("strict")
        with pytest.raises(MarkdownSizeError, match="Data URI size.*exceeds limit"):
            budget.add_uri(1)  # Even 1 byte exceeds 0 limit

    def test_check_within_budget(self):
        """check() returns True when within budget."""
        budget = URIBudget("moderate")
        budget.add_uri(1000)
        assert budget.check() is True

    def test_check_over_budget(self):
        """check() returns False when over budget."""
        budget = URIBudget("moderate")
        budget.current_size = budget.max_total_size + 1
        assert budget.check() is False

    def test_reset(self):
        """reset() clears count and size."""
        budget = URIBudget("moderate")
        budget.add_uri(1000)
        budget.add_uri(2000)
        assert budget.current_count == 2
        assert budget.current_size == 3000
        budget.reset()
        assert budget.current_count == 0
        assert budget.current_size == 0
