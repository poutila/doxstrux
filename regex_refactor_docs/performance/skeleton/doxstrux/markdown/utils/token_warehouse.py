
RAISE_ON_COLLECTOR_ERROR = False

from __future__ import annotations
from typing import Any, Callable, Protocol, Dict, List, Tuple, Optional, Set
from collections import defaultdict

class DispatchContext:
    __slots__ = ("stack", "line")
    def __init__(self):
        self.stack: List[str] = []
        self.line: int = 0

class Interest:
    __slots__ = ("types", "tags", "ignore_inside", "predicate")
    def __init__(self, types: Optional[Set[str]] = None, tags: Optional[Set[str]] = None,
                 ignore_inside: Optional[Set[str]] = None,
                 predicate: Optional[Callable[[Any, DispatchContext, "TokenWarehouse"], bool]] = None):
        self.types: Set[str] = types or set()
        self.tags: Set[str] = tags or set()
        self.ignore_inside: Set[str] = ignore_inside or set()
        self.predicate = predicate

class Collector(Protocol):
    name: str
    interest: Interest
    def should_process(self, token: Any, ctx: DispatchContext, wh: "TokenWarehouse") -> bool: ...
    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: "TokenWarehouse") -> None: ...
    def finalize(self, wh: "TokenWarehouse") -> Any: ...

class TokenWarehouse:
    __slots__ = (
        "tokens", "tree",
        "by_type", "pairs", "parents",
        "sections", "fences",
        "lines", "line_count",
        "_text_cache", "_section_starts", "_collector_errors",
        "_collectors", "_routing",
        "_mask_map", "_collector_masks",
    )

    def __init__(self, tokens: List[Any], tree: Any, text: str | None = None):
        self.tokens: List[Any] = tokens
        self.tree: Any = tree
        self.lines = text.splitlines(True) if isinstance(text, str) else None
        self.line_count = len(self.lines) if self.lines is not None else self._infer_line_count()

        self.by_type: Dict[str, List[int]] = defaultdict(list)
        self.pairs: Dict[int, int] = {}
        self.parents: Dict[int, int] = {}
        self.sections: List[Tuple[int, int, int, int, str]] = []
        self.fences: List[Tuple[int, int, str, str]] = []

        self._text_cache: Dict[Tuple[int, int], str] = {}
        self._section_starts: List[int] = []
        self._collector_errors: List[tuple] = []

        self._collectors: List[Collector] = []
        self._routing: Dict[str, Tuple[Collector, ...]] = {}

        self._mask_map: Dict[str, int] = {}
        self._collector_masks: Dict[Collector, int] = {}

        self._build_indices()

    def _infer_line_count(self) -> int:
        max_line = 0
        for tok in self.tokens:
            m = getattr(tok, "map", None)
            if m and isinstance(m, (list, tuple)) and len(m) == 2 and m[1] is not None:
                try:
                    if int(m[1]) > max_line:
                        max_line = int(m[1])
                except Exception:
                    pass
        return max_line or 0

    def _build_indices(self) -> None:
        open_stack: list[int] = []
        tokens = self.tokens
        by_type = self.by_type
        parents = self.parents
        pairs = self.pairs
        fences = self.fences

        for i, tok in enumerate(tokens):
            # normalize map tuples to safe ints
            m_raw = getattr(tok, 'map', None)
            if m_raw and isinstance(m_raw, (list, tuple)) and len(m_raw) == 2:
                try:
                    s = int(m_raw[0]) if m_raw[0] is not None else 0
                except Exception:
                    s = 0
                try:
                    e = int(m_raw[1]) if m_raw[1] is not None else s
                except Exception:
                    e = s
                if s < 0: s = 0
                if e < s: e = s
                try:
                    tok.map = (s, e)
                except Exception:
                    pass
            else:
                m_raw = None

            ttype = getattr(tok, "type", "")
            by_type[ttype].append(i)

            # assign parent before mutating the stack to ensure correctness
            if open_stack:
                parents[i] = open_stack[-1]

            nesting = getattr(tok, "nesting", 0)
            if nesting == 1:
                open_stack.append(i)
            elif nesting == -1:
                if open_stack:
                    pairs[open_stack.pop()] = i

            if ttype == "fence":
                m = getattr(tok, "map", None) or (None, None)
                if m[0] is not None and m[1] is not None:
                    info = (getattr(tok, "info", "") or "").strip()
                    fences.append((int(m[0]), int(m[1]), info, getattr(tok, "info", "") or ""))

        # build sections (sort headings by normalized start to tolerate malformed order)
        heads = self.by_type.get("heading_open", [])
        heads = sorted(heads, key=lambda h: (getattr(self.tokens[h], 'map', (0,0))[0] or 0))

        stack: List[Tuple[int, int, int, str]] = []
        last_end = self.line_count

        def level_of(idx: int) -> int:
            tok = self.tokens[idx]
            tag = getattr(tok, "tag", "") or ""
            return int(tag[1:]) if tag.startswith("h") and tag[1:].isdigit() else 1

        for hidx in heads:
            lvl = level_of(hidx)
            m = getattr(self.tokens[hidx], "map", None) or (0, 0)
            start = int(m[0])

            while stack and stack[-1][1] >= lvl:
                ohidx, olvl, ostart, otext = stack.pop()
                self.sections.append((ohidx, ostart, max(start - 1, ostart), olvl, otext))

            text = ""
            if hidx + 1 < len(self.tokens) and getattr(self.tokens[hidx + 1], "type", "") == "inline":
                text = getattr(self.tokens[hidx + 1], "content", "") or ""

            stack.append((hidx, lvl, start, text))

        for ohidx, olvl, ostart, otext in stack:
            self.sections.append((ohidx, ostart, max(last_end, ostart), olvl, otext))

        self._section_starts = [s for _, s, _, _, _ in self.sections]

    # Query API
    def iter_by_type(self, token_type: str) -> List[int]:
        return self.by_type.get(token_type, [])

    def range_for(self, open_idx: int) -> Optional[int]:
        return self.pairs.get(open_idx)

    def parent(self, token_idx: int) -> Optional[int]:
        return self.parents.get(token_idx)

    def sections_list(self) -> List[Tuple[int, int, int, int, str]]:
        return self.sections

    def fences_list(self) -> List[Tuple[int, int, str, str]]:
        return self.fences

    def section_of(self, line_num: int) -> Optional[str]:
        from bisect import bisect_right
        if not self.sections:
            return None
        idx = bisect_right(self._section_starts, line_num) - 1
        if idx < 0 or idx >= len(self.sections):
            return None
        _, start, end, _, _ = self.sections[idx]
        if start <= line_num <= end:
            return f"section_{idx}"
        return None

    # Routing
    def register_collector(self, collector: Collector) -> None:
        self._collectors.append(collector)
        for ttype in collector.interest.types:
            prev = self._routing.get(ttype)
            self._routing[ttype] = tuple([*prev, collector]) if prev else (collector,)
        mask = 0
        for t in getattr(collector.interest, "ignore_inside", set()):
            if t not in self._mask_map:
                self._mask_map[t] = len(self._mask_map)
            mask |= (1 << self._mask_map[t])
        self._collector_masks[collector] = mask

    def dispatch_all(self) -> None:
        ctx = DispatchContext()
        tokens = self.tokens; routing = self._routing
        open_types = ctx.stack; append = open_types.append; pop = open_types.pop
        type_mask_bit = self._mask_map; col_masks = self._collector_masks
        open_mask = 0

        for i, tok in enumerate(tokens):
            ttype = getattr(tok, "type", ""); nesting = getattr(tok, "nesting", 0)

            if nesting == 1:
                append(ttype)
                bit = type_mask_bit.get(ttype)
                if bit is not None: open_mask |= (1 << bit)
            elif nesting == -1 and open_types:
                last = open_types[-1]; pop()
                bit = type_mask_bit.get(last)
                if bit is not None: open_mask &= ~(1 << bit)

            cols = routing.get(ttype, ())
            if not cols:
                continue

            for col in cols:
                cm = col_masks.get(col, 0)
                if cm and (open_mask & cm):
                    continue
                pred = getattr(col.interest, "predicate", None)
                if pred and not pred(tok, ctx, self):
                    continue
                sp = getattr(col, "should_process", None)
                if sp is not None and not sp(tok, ctx, self):
                    continue
                try:
                    col.on_token(i, tok, ctx, self)
                except Exception as e:
                    try:
                        self._collector_errors.append((getattr(col, 'name', repr(col)), i, type(e).__name__))
                    except Exception:
                        pass
                    if globals().get('RAISE_ON_COLLECTOR_ERROR'):
                        raise
                    # continue
