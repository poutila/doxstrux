
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class ImagesCollector:
    def __init__(self):
        self.name = "images"
        self.interest = Interest(types={"image"}, ignore_inside={"fence","code_block"})
        self._images: List[Dict[str, Any]] = []

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        if getattr(token, "type", "") == "image":
            src = None
            try:
                src = token.attrGet("src")
            except Exception:
                pass
            alt = getattr(token, "content", "") or ""
            line = token.map[0] if getattr(token, "map", None) else None
            self._images.append({
                "src": src or "",
                "alt": alt,
                "line": line,
                "section_id": wh.section_of(line) if line is not None else None
            })

    def finalize(self, wh: TokenWarehouse):
        return self._images
