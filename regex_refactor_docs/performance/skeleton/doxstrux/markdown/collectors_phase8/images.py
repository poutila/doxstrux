
from __future__ import annotations
from typing import Any, Dict, List
from ..utils.token_warehouse import Collector, Interest, DispatchContext, TokenWarehouse
from ..utils.url_utils import normalize_url

# P0-3: Per-collector hard quota to prevent memory amplification OOM
MAX_IMAGES_PER_DOC = 5_000

class ImagesCollector:
    def __init__(self):
        self.name = "images"
        self.interest = Interest(types={"image"}, ignore_inside={"fence","code_block"})
        self._images: List[Dict[str, Any]] = []
        self._truncated = False

    def should_process(self, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> bool:
        return True

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: TokenWarehouse) -> None:
        if getattr(token, "type", "") == "image":
            # P0-3: Enforce cap BEFORE appending
            if len(self._images) >= MAX_IMAGES_PER_DOC:
                self._truncated = True
                return

            src = None
            try:
                src = token.attrGet("src")
            except Exception:
                pass

            # P0-1: Use centralized URL normalization (SSRF/XSS prevention)
            normalized_src = normalize_url(src) if src else None

            # If URL is rejected (None), still collect but mark as invalid
            alt = getattr(token, "content", "") or ""
            line = token.map[0] if getattr(token, "map", None) else None
            self._images.append({
                "src": normalized_src or src or "",  # Use normalized, fallback to original
                "src_valid": normalized_src is not None if src else True,  # Track validity
                "alt": alt,
                "line": line,
                "section_id": wh.section_of(line) if line is not None else None
            })

    def finalize(self, wh: TokenWarehouse):
        """Return images with truncation metadata."""
        return {
            "images": self._images,
            "truncated": self._truncated,
            "count": len(self._images),
            "max_allowed": MAX_IMAGES_PER_DOC
        }
