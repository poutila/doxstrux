
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class ParagraphsCollector:
    def __init__(self):
        self.name = "paragraphs"
        self.interest = Interest(types={"paragraph_open", "inline", "paragraph_close"})
        self._buf: List[str] = []
        self._out: List[Dict[str, Any]] = []
        self._line: int | None = None

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        t = getattr(token, "type", "")
        if t == "paragraph_open":
            self._buf.clear()
            self._line = token.map[0] if getattr(token, "map", None) else None
        elif t == "inline":
            c = getattr(token, "content", "") or ""
            if c: self._buf.append(c)
        elif t == "paragraph_close":
            txt = "".join(self._buf)
            sec = wh.section_of(self._line) if self._line is not None else None
            self._out.append({"text": txt, "section_id": sec, "line": self._line})
            self._buf.clear()
            self._line = None

    def finalize(self, wh: TokenWarehouse):
        return self._out
