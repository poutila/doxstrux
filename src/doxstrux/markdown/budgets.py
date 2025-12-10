"""Resource budgets and enforcement for markdown parsing.

This module provides budget tracking and enforcement for various resource limits
during markdown parsing to prevent DoS attacks and resource exhaustion.

Classes:
    NodeBudget: Track node counts during parsing
    CellBudget: Track table cell counts
    URIBudget: Track URI counts and sizes

All budget violations raise MarkdownSizeError with embedding_blocked set.
"""

from doxstrux.markdown.exceptions import MarkdownSizeError


# ============================================================================
# Budget Constants
# ============================================================================

# Maximum number of nodes to prevent excessive memory usage
MAX_NODES = {
    "strict": 10000,
    "moderate": 50000,
    "permissive": 200000,
}

# Maximum total table cells to prevent matrix DoS
MAX_TABLE_CELLS = {
    "strict": 1000,
    "moderate": 10000,
    "permissive": 50000,
}

# ============================================================================
# Budget Helper Functions (SSOT Access)
# ============================================================================
# Note: MAX_DATA_URI_SIZE dict removed - use get_max_data_uri_size() instead
# SSOT is SECURITY_PROFILES in config.py per SECURITY_KERNEL_SPEC.md §8

def get_max_data_uri_size(profile: str) -> int:
    """Get max data URI size from SECURITY_PROFILES (SSOT).

    Per SECURITY_KERNEL_SPEC.md §8.2.

    Args:
        profile: Security profile name (strict/moderate/permissive)

    Returns:
        Maximum data URI size in bytes for the profile

    Raises:
        ValueError: If profile is unknown
    """
    from .config import SECURITY_PROFILES

    try:
        return SECURITY_PROFILES[profile]["max_data_uri_size"]
    except KeyError as exc:
        raise ValueError(f"Unknown profile: {profile}") from exc


def get_max_injection_scan_chars(profile: str) -> int:
    """Get max injection scan chars from SECURITY_PROFILES (SSOT).

    Per SECURITY_KERNEL_SPEC.md §8.2.

    Args:
        profile: Security profile name (strict/moderate/permissive)

    Returns:
        Maximum characters to scan for prompt injection

    Raises:
        ValueError: If profile is unknown
    """
    from .config import SECURITY_PROFILES

    try:
        return SECURITY_PROFILES[profile]["max_injection_scan_chars"]
    except KeyError as exc:
        raise ValueError(f"Unknown profile: {profile}") from exc


# ============================================================================
# Budget Tracking Classes
# ============================================================================

class NodeBudget:
    """Track node counts during parsing to prevent excessive memory usage.

    Attributes:
        max_nodes: Maximum allowed nodes for this profile
        current_count: Current node count
        profile: Security profile name
    """

    def __init__(self, security_profile: str = "moderate"):
        """Initialize node budget.

        Args:
            security_profile: Security profile ('strict', 'moderate', 'permissive')
        """
        self.profile = security_profile
        self.max_nodes = MAX_NODES.get(security_profile, MAX_NODES["moderate"])
        self.current_count = 0

    def increment(self, count: int = 1) -> None:
        """Increment node count and check budget.

        Args:
            count: Number of nodes to add

        Raises:
            MarkdownSizeError: If budget exceeded
        """
        self.current_count += count
        if self.current_count > self.max_nodes:
            raise MarkdownSizeError(
                f"Node count {self.current_count} exceeds budget {self.max_nodes}",
                security_profile=self.profile,
                content_info={
                    "count": self.current_count,
                    "limit": self.max_nodes,
                    "embedding_blocked_reason": f"Node budget exceeded: {self.current_count}/{self.max_nodes}"
                }
            )

    def check(self) -> bool:
        """Check if within budget without raising.

        Returns:
            True if within budget, False otherwise
        """
        return self.current_count <= self.max_nodes

    def reset(self) -> None:
        """Reset node count."""
        self.current_count = 0


class CellBudget:
    """Track table cell counts to prevent matrix DoS attacks.

    Large tables with many cells can cause memory exhaustion.

    Attributes:
        max_cells: Maximum allowed total cells
        current_count: Current total cell count across all tables
        profile: Security profile name
    """

    def __init__(self, security_profile: str = "moderate"):
        """Initialize cell budget.

        Args:
            security_profile: Security profile ('strict', 'moderate', 'permissive')
        """
        self.profile = security_profile
        self.max_cells = MAX_TABLE_CELLS.get(security_profile, MAX_TABLE_CELLS["moderate"])
        self.current_count = 0

    def add_table(self, rows: int, cols: int) -> None:
        """Add table cell count and check budget.

        Args:
            rows: Number of rows in table
            cols: Number of columns in table

        Raises:
            MarkdownSizeError: If budget exceeded
        """
        cells = rows * cols
        self.current_count += cells
        if self.current_count > self.max_cells:
            raise MarkdownSizeError(
                f"Table cell count {self.current_count} exceeds budget {self.max_cells}",
                security_profile=self.profile,
                content_info={
                    "count": self.current_count,
                    "limit": self.max_cells,
                    "table_cells": cells,
                    "embedding_blocked_reason": f"Table cell budget exceeded: {self.current_count}/{self.max_cells}"
                }
            )

    def check(self) -> bool:
        """Check if within budget without raising.

        Returns:
            True if within budget, False otherwise
        """
        return self.current_count <= self.max_cells

    def reset(self) -> None:
        """Reset cell count."""
        self.current_count = 0


class URIBudget:
    """Track URI counts and sizes to prevent data URI abuse.

    Data URIs can embed large binary data in links/images. Track both
    count and total size.

    Attributes:
        max_uri_size: Maximum size for single data URI
        max_total_size: Maximum total size for all data URIs
        current_count: Number of data URIs encountered
        current_size: Total size of all data URIs
        profile: Security profile name
    """

    def __init__(self, security_profile: str = "moderate"):
        """Initialize URI budget.

        Args:
            security_profile: Security profile ('strict', 'moderate', 'permissive')
        """
        self.profile = security_profile
        # Use SSOT helper instead of duplicate dict
        self.max_uri_size = get_max_data_uri_size(security_profile)
        # Total size is 10x single URI limit
        self.max_total_size = self.max_uri_size * 10 if self.max_uri_size > 0 else 0
        self.current_count = 0
        self.current_size = 0

    def add_uri(self, size: int) -> None:
        """Add data URI and check budget.

        Args:
            size: Size of data URI in bytes

        Raises:
            MarkdownSizeError: If budget exceeded
        """
        if size > self.max_uri_size:
            raise MarkdownSizeError(
                f"Data URI size {size} exceeds limit {self.max_uri_size}",
                security_profile=self.profile,
                content_info={
                    "uri_size": size,
                    "limit": self.max_uri_size,
                    "embedding_blocked_reason": f"Data URI too large: {size}/{self.max_uri_size} bytes"
                }
            )

        self.current_count += 1
        self.current_size += size

        if self.current_size > self.max_total_size:
            raise MarkdownSizeError(
                f"Total data URI size {self.current_size} exceeds limit {self.max_total_size}",
                security_profile=self.profile,
                content_info={
                    "total_size": self.current_size,
                    "limit": self.max_total_size,
                    "uri_count": self.current_count,
                    "embedding_blocked_reason": f"Total data URI size exceeded: {self.current_size}/{self.max_total_size} bytes"
                }
            )

    def check(self) -> bool:
        """Check if within budget without raising.

        Returns:
            True if within budget, False otherwise
        """
        return self.current_size <= self.max_total_size

    def reset(self) -> None:
        """Reset URI tracking."""
        self.current_count = 0
        self.current_size = 0
