
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse
from ..utils.url_utils import normalize_url

ALLOWED_SCHEMES = {"http", "https", "mailto"}

# P0-3: Per-collector hard quota to prevent memory amplification OOM
# Per CLOSING_IMPLEMENTATION.md: Executive summary B.2
MAX_LINKS_PER_DOC = 10_000

class LinksCollector:
    def __init__(self, allowed_schemes: Optional[Set[str]] = None):
        self.name = "links"
        self.interest = Interest(types={"link_open", "inline", "link_close"}, ignore_inside={"fence", "code_block"})
        self.allowed_schemes = allowed_schemes or ALLOWED_SCHEMES
        self._links: List[Dict[str, Any]] = []
        self._current: Optional[Dict[str, Any]] = None
        self._depth = 0
        self._truncated = False  # P0-3: Track if cap was hit

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        ttype = getattr(token, "type", "")
        if ttype == "link_open":
            self._depth += 1
            if self._depth == 1:
                href = None
                try:
                    href = token.attrGet("href")
                except Exception:
                    href = getattr(token, "href", None) or None
                href = href or ""
                # P0-1: Use centralized URL normalization (SSRF/XSS prevention)
                normalized_href = normalize_url(href)

                # If URL is rejected (None), don't collect this link at all
                if normalized_href is None:
                    self._current = None
                    return

                self._current = {
                    "id": f"link_{len(self._links)}",
                    "url": normalized_href,
                    "text": "",
                    "line": (token.map[0] if getattr(token, "map", None) else None),
                    "allowed": True,
                }
        elif ttype == "inline" and self._current:
            content = getattr(token, "content", "") or ""
            if content:
                self._current["text"] += content
        elif ttype == "link_close":
            self._depth -= 1
            if self._depth == 0 and self._current:
                # P0-3: Enforce cap BEFORE appending
                if len(self._links) >= MAX_LINKS_PER_DOC:
                    self._truncated = True
                    self._current = None  # Discard this link
                    return

                line = self._current.get("line")
                if line is not None:
                    self._current["section_id"] = wh.section_of(line)
                self._links.append(self._current)
                self._current = None

    def finalize(self, wh: TokenWarehouse):
        """Return links with truncation metadata.

        P0-3: Returns dict with truncation metadata to signal capping occurred.
        Per CLOSING_IMPLEMENTATION.md lines 694-704.
        """
        return {
            "links": self._links,
            "truncated": self._truncated,
            "count": len(self._links),
            "max_allowed": MAX_LINKS_PER_DOC
        }
