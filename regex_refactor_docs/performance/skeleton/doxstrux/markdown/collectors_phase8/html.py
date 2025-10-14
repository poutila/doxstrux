
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class HtmlCollector:
    def __init__(self):
        self.name = "html"
        self.interest = Interest(types={"html_block","html_inline"})
        self._items: List[Dict[str, Any]] = []

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        content = getattr(token, "content", "") or ""
        m = getattr(token, "map", None) or (None, None)
        self._items.append({
            "kind": getattr(token, "type", ""),
            "content": content,
            "start_line": m[0],
            "end_line": m[1],
        })

    def finalize(self, wh: TokenWarehouse):
        return self._items
