
from __future__ import annotations
from typing import Any, Dict, List
import re
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse

# Common template syntax patterns (SSTI risk detection)
TEMPLATE_PATTERN = re.compile(
    r'\{\{|\{%|<%=|<\?php|\$\{|#\{',
    re.IGNORECASE
)

# P0-3: Per-collector hard quota to prevent memory amplification OOM
MAX_HEADINGS_PER_DOC = 5_000

class HeadingsCollector:
    def __init__(self):
        self.name = "headings"
        self.interest = Interest(types={"heading_open", "inline", "heading_close"})
        self._cur_level: int | None = None
        self._buf: List[str] = []
        self._out: List[Dict[str, Any]] = []
        self._truncated = False

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        t = getattr(token, "type", "")
        if t == "heading_open":
            tag = getattr(token, "tag", "") or ""
            lvl = int(tag[1:]) if tag.startswith("h") and tag[1:].isdigit() else 0
            self._cur_level = lvl
            self._buf.clear()
        elif t == "inline" and self._cur_level is not None:
            c = getattr(token, "content", "") or ""
            if c: self._buf.append(c)
        elif t == "heading_close" and self._cur_level is not None:
            # P0-3: Enforce cap BEFORE appending
            if len(self._out) >= MAX_HEADINGS_PER_DOC:
                self._truncated = True
                self._cur_level = None
                self._buf.clear()
                return

            # use map of opening (idx-2) if available
            line = None
            # find opening line via pairs or map window if needed
            heading_text = "".join(self._buf)

            # ✅ Detect template syntax (SSTI risk)
            contains_template = bool(TEMPLATE_PATTERN.search(heading_text))

            self._out.append({
                "level": self._cur_level,
                "text": heading_text,

                # Security metadata
                "contains_template_syntax": contains_template,
                "needs_escaping": contains_template,
            })
            self._cur_level = None
            self._buf.clear()

    def finalize(self, wh: TokenWarehouse):
        """Return headings with truncation metadata."""
        return {
            "headings": self._out,
            "truncated": self._truncated,
            "count": len(self._out),
            "max_allowed": MAX_HEADINGS_PER_DOC
        }
