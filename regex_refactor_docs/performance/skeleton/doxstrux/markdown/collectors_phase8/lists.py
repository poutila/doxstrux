
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class ListsCollector:
    def __init__(self):
        self.name = "lists"
        self.interest = Interest(types={
            "bullet_list_open","bullet_list_close",
            "ordered_list_open","ordered_list_close",
            "list_item_open","list_item_close",
            "inline"
        })
        self._stack: List[Dict[str, Any]] = []   # stack of current list contexts
        self._out: List[Dict[str, Any]] = []
        self._in_item: bool = False
        self._item_buf: List[str] = []

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        t = getattr(token, "type", "")
        if t in {"bullet_list_open","ordered_list_open"}:
            kind = "ordered" if t.startswith("ordered") else "bullet"
            self._stack.append({"kind": kind, "items": [], "start_line": token.map[0] if getattr(token, "map", None) else None})
        elif t == "list_item_open":
            self._in_item = True
            self._item_buf.clear()
        elif t == "inline" and self._in_item:
            c = getattr(token, "content", "") or ""
            if c: self._item_buf.append(c)
        elif t == "list_item_close":
            self._in_item = False
            if self._stack:
                self._stack[-1]["items"].append("".join(self._item_buf).strip())
                self._item_buf.clear()
        elif t in {"bullet_list_close","ordered_list_close"}:
            ctx_obj = self._stack.pop() if self._stack else None
            if ctx_obj:
                self._out.append(ctx_obj)

    def finalize(self, wh: TokenWarehouse):
        return self._out
