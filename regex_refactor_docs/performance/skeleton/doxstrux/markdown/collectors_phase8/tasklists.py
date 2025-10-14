
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

class TaskListsCollector:
    def __init__(self):
        self.name = "tasklists"
        # Task marks usually appear in inline text of list items.
        self.interest = Interest(types={"inline"})
        self._tasks: List[Dict[str, Any]] = []

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        # Heuristic: parse "- [ ] ..." or "- [x] ..." patterns in inline text, leaving exact logic for later.
        content = getattr(token, "content", "") or ""
        if "[ ]" in content or "[x]" in content or "[X]" in content:
            line = token.map[0] if getattr(token, "map", None) else None
            self._tasks.append({
                "raw": content,
                "line": line,
                "checked": ("[x]" in content) or ("[X]" in content),
                "section_id": wh.section_of(line) if line is not None else None
            })

    def finalize(self, wh: TokenWarehouse):
        return self._tasks
