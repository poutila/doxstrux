
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class CodeBlocksCollector:
    def __init__(self):
        self.name = "codeblocks"
        self.interest = Interest(types={"fence","code_block"})
        self._blocks: List[Dict[str, Any]] = []

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        t = getattr(token, "type", "")
        if t in {"fence","code_block"}:
            lang = (getattr(token, "info", "") or "").strip()
            code = getattr(token, "content", "") or ""
            m = getattr(token, "map", None) or (None, None)
            self._blocks.append({
                "lang": lang,
                "code": code,
                "start_line": m[0],
                "end_line": m[1],
            })

    def finalize(self, wh: TokenWarehouse):
        return self._blocks
