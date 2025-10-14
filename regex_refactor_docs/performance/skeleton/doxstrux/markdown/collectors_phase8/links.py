
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class LinksCollector:
    def __init__(self, allowed_schemes: Optional[Set[str]] = None):
        self.name = "links"
        self.interest = Interest(types={"link_open", "inline", "link_close"}, ignore_inside={"fence", "code_block"})
        self.allowed_schemes = allowed_schemes or {"http", "https", "mailto"}
        self._links: List[Dict[str, Any]] = []
        self._current: Optional[Dict[str, Any]] = None
        self._depth = 0

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
                    pass
                href = href or ""
                self._current = {
                    "id": f"link_{len(self._links)}",
                    "url": href,
                    "text": "",
                    "line": (token.map[0] if getattr(token, "map", None) else None),
                    "allowed": self._is_allowed(href),
                }
        elif ttype == "inline" and self._current:
            content = getattr(token, "content", "") or ""
            if content:
                self._current["text"] += content
        elif ttype == "link_close":
            self._depth -= 1
            if self._depth == 0 and self._current:
                line = self._current.get("line")
                if line is not None:
                    self._current["section_id"] = wh.section_of(line)
                self._links.append(self._current)
                self._current = None

    def finalize(self, wh: TokenWarehouse):
        return self._links

    def _is_allowed(self, url: str) -> bool:
        if ":" not in url:
            return True
        scheme = url.split(":", 1)[0].lower()
        return scheme in self.allowed_schemes
