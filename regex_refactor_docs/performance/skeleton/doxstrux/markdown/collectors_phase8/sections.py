
from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class SectionsCollector:
    """Builds a section list from the warehouse's precomputed sections.
    This collector is mostly a thin presenter so you can preserve a consistent result shape
    as you migrate from Phase 7.
    """
    def __init__(self):
        self.name = "sections"
        # We do not need tokens; we read from warehouse.indices in finalize().
        self.interest = Interest(types=set())
        self._data: List[Dict[str, Any]] = []

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return False  # no-op in dispatch

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        return

    def finalize(self, wh: TokenWarehouse):
        out: List[Dict[str, Any]] = []
        for i, (hidx, start, end, level, text) in enumerate(wh.sections_list()):
            out.append({
                "id": f"section_{i}",
                "heading_token": hidx,
                "level": level,
                "text": text,
                "start_line": start,
                "end_line": end
            })
        return out
