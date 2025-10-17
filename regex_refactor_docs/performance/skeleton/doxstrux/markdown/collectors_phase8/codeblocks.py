
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

# P0-3: Per-collector hard quota to prevent memory amplification OOM
MAX_CODE_BLOCKS_PER_DOC = 2_000

class CodeBlocksCollector:
    def __init__(self):
        self.name = "codeblocks"
        self.interest = Interest(types={"fence","code_block"})
        self._blocks: List[Dict[str, Any]] = []
        self._truncated = False

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        t = getattr(token, "type", "")
        if t in {"fence","code_block"}:
            # P0-3: Enforce cap BEFORE appending
            if len(self._blocks) >= MAX_CODE_BLOCKS_PER_DOC:
                self._truncated = True
                return

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
        """Return code blocks with truncation metadata."""
        return {
            "codeblocks": self._blocks,
            "truncated": self._truncated,
            "count": len(self._blocks),
            "max_allowed": MAX_CODE_BLOCKS_PER_DOC
        }
