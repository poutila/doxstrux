"""
HTMLCollector for Phase-8 collectors.
Behavior:
 - Default: do NOT collect/render raw HTML. Set allow_html=True to enable.
 - When collecting, the collector stores html blocks with a `needs_sanitization` flag.
 - Optionally sanitizes at finalize() using bleach if enabled.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional

try:
    import bleach
except Exception:
    bleach = None

class HTMLCollector:
    name = "html"

    def __init__(self, allow_html: bool = False, sanitize_on_finalize: bool = False):
        """
        :param allow_html: if False, the collector will ignore html_block tokens (safe default).
        :param sanitize_on_finalize: if True and bleach is available, sanitize collected HTML in finalize().
        """
        self.allow_html = allow_html
        self.sanitize_on_finalize = sanitize_on_finalize and (bleach is not None)
        self._html_blocks: List[Dict[str, Any]] = []

    @property
    def interest(self):
        class I:
            types = {"html_block"}
            tags = set()
            ignore_inside = set()
            predicate = None
        return I()

    def should_process(self, token_view: Dict[str, Any], ctx, wh) -> bool:
        return self.allow_html

    def on_token(self, idx: int, token_view: Dict[str, Any], ctx, wh) -> None:
        if not self.allow_html:
            return
        if token_view.get("type") != "html_block":
            return
        content = token_view.get("content", "") or ""
        self._html_blocks.append({
            "token_index": idx,
            "content": content,
            "needs_sanitization": True,
        })

    def finalize(self, wh) -> List[Dict[str, Any]]:
        if not self._html_blocks:
            return []
        if self.sanitize_on_finalize and bleach is not None:
            cleaned = []
            for b in self._html_blocks:
                safe = bleach.clean(b["content"],
                                     tags=["b","i","u","strong","em","p","ul","ol","li","a","img"],
                                     attributes={"a":["href","title"], "img":["src","alt"]},
                                     protocols=["http","https","mailto"],
                                     strip=True)
                cleaned.append({"token_index": b["token_index"], "content": safe, "was_sanitized": True})
            return cleaned
        return list(self._html_blocks)
