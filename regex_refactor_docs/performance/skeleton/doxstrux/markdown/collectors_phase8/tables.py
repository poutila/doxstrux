
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

# P0-3: Per-collector hard quota to prevent memory amplification OOM
MAX_TABLES_PER_DOC = 1_000

class TablesCollector:
    def __init__(self):
        self.name = "tables"
        self.interest = Interest(types={
            "table_open","thead_open","tr_open","th_open","td_open",
            "inline","td_close","th_close","tr_close","thead_close","table_close","tbody_open","tbody_close"
        })
        self._tables: List[Dict[str, Any]] = []
        self._cur_table: Dict[str, Any] | None = None
        self._cur_row: List[str] | None = None
        self._in_cell: bool = False
        self._cell_buf: List[str] = []
        self._truncated = False

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        t = getattr(token, "type", "")
        if t == "table_open":
            # P0-3: Enforce cap BEFORE creating table
            if len(self._tables) >= MAX_TABLES_PER_DOC:
                self._truncated = True
                self._cur_table = None  # Skip this table
                return
            self._cur_table = {"rows": [], "start_line": token.map[0] if getattr(token, "map", None) else None}
        elif t == "tr_open":
            self._cur_row = []
        elif t in {"th_open","td_open"}:
            self._in_cell = True
            self._cell_buf.clear()
        elif t == "inline" and self._in_cell:
            c = getattr(token, "content", "") or ""
            if c: self._cell_buf.append(c)
        elif t in {"th_close","td_close"}:
            self._in_cell = False
            if self._cur_row is not None:
                self._cur_row.append("".join(self._cell_buf).strip())
        elif t == "tr_close":
            if self._cur_table is not None and self._cur_row is not None:
                self._cur_table["rows"].append(self._cur_row)
            self._cur_row = None
        elif t == "table_close":
            if self._cur_table is not None:
                self._tables.append(self._cur_table)
            self._cur_table = None

    def finalize(self, wh: TokenWarehouse):
        """Return tables with truncation metadata."""
        return {
            "tables": self._tables,
            "truncated": self._truncated,
            "count": len(self._tables),
            "max_allowed": MAX_TABLES_PER_DOC
        }
