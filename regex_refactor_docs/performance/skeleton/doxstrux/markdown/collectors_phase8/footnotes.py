
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class FootnotesCollector:
    def __init__(self):
        self.name = "footnotes"
        # Plugins vary: cover common token type names conservatively
        self.interest = Interest(types={"footnote_ref", "footnote_reference_open", "inline", "footnote_reference_close"})
        self._notes: List[Dict[str, Any]] = []
        self._open: Dict[int, Dict[str, Any]] = {}

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        t = getattr(token, "type", "")
        if t in {"footnote_ref","footnote_reference_open"}:
            line = token.map[0] if getattr(token, "map", None) else None
            self._open[idx] = {"line": line, "text": ""}
        elif t == "inline" and self._open:
            # append to the most recent open footnote
            last_key = sorted(self._open.keys())[-1]
            c = getattr(token, "content", "") or ""
            self._open[last_key]["text"] += c
        elif t == "footnote_reference_close":
            # close the most recent
            if self._open:
                last_key = sorted(self._open.keys())[-1]
                item = self._open.pop(last_key)
                item["section_id"] = wh.section_of(item["line"]) if item.get("line") is not None else None
                self._notes.append(item)

    def finalize(self, wh: TokenWarehouse):
        # Flush any dangling opens
        while self._open:
            _, item = self._open.popitem()
            self._notes.append(item)
        return self._notes
