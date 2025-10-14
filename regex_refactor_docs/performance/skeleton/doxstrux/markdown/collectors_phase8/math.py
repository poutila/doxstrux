
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class MathCollector:
    def __init__(self):
        self.name = "math"
        self.interest = Interest(types={"math_block","math_inline"})
        self._items: List[Dict[str, Any]] = []

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        t = getattr(token, "type", "")
        if t in {"math_block","math_inline"}:
            self._items.append({
                "kind": t,
                "tex": getattr(token, "content", "") or "",
                "line": token.map[0] if getattr(token, "map", None) else None
            })

    def finalize(self, wh: TokenWarehouse):
        return self._items
