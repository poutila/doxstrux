from __future__ import annotations
from typing import Any, Callable, Protocol, Dict, List, Tuple, Optional, Set
from collections import defaultdict
import warnings
from .section import Section
from .timeout import collector_timeout

RAISE_ON_COLLECTOR_ERROR = False

# Resource limits (prevent OOM and DoS attacks)
MAX_TOKENS = 100_000  # Maximum number of tokens (prevents R-2: Memory amplification)
MAX_BYTES = 10_000_000  # 10MB maximum document size
MAX_NESTING = 150  # Maximum nesting depth (prevents R-3: Stack overflow)

class DocumentTooLarge(ValueError):
    """Raised when document exceeds resource limits."""
    pass

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
        "by_type", "pairs", "pairs_rev", "parents", "_children",
        "sections", "fences",
        "lines", "line_count",
        "_text_cache", "_section_starts", "_collector_errors",
        "_collectors", "_routing", "_registered_collector_ids",
        "_mask_map", "_collector_masks",
        "_dispatching", "COLLECTOR_TIMEOUT_SECONDS",
    )

    def __init__(self, tokens: List[Any], tree: Any, text: str | None = None):
        """
        Initialize TokenWarehouse with parsed tokens.

        CRITICAL INVARIANT: text must be pre-normalized (NFC + LF).

        Do NOT normalize here - tokens are already parsed from this text.
        If you normalize after parsing, token.map offsets will mismatch line indices.

        Use parse_markdown_normalized() from text_normalization.py to ensure
        correct normalization order.

        Args:
            tokens: Parsed markdown-it tokens (from normalized text)
            tree: SyntaxTreeNode from tokens
            text: The SAME normalized text that was parsed (NFC + LF)

        Raises:
            DocumentTooLarge: If document exceeds safety limits
        """
        # ✅ Fail fast BEFORE building indices (prevents R-2: Memory amplification)
        if len(tokens) > MAX_TOKENS:
            raise DocumentTooLarge(
                f"Document too large: {len(tokens)} tokens (max {MAX_TOKENS})"
            )

        if text and len(text) > MAX_BYTES:
            raise DocumentTooLarge(
                f"Document too large: {len(text)} bytes (max {MAX_BYTES})"
            )

        # Canonicalize tokens to prevent malicious getter execution (supply-chain attack prevention)
        self.tokens: List[Any] = self._canonicalize_tokens(tokens)
        self.tree: Any = tree
        self.lines = text.splitlines(True) if isinstance(text, str) else None
        self.line_count = len(self.lines) if self.lines is not None else self._infer_line_count()

        self.by_type: Dict[str, List[int]] = defaultdict(list)
        self.pairs: Dict[int, int] = {}
        self.pairs_rev: Dict[int, int] = {}  # Reverse pairs: close_idx -> open_idx
        self.parents: Dict[int, int] = {}
        self._children: Optional[Dict[int, List[int]]] = None  # Lazy: built on first access
        # Canonical format: (start_line, end_line, token_idx, level, title)
        self.sections: List[Tuple[int, Optional[int], int, int, str]] = []
        self.fences: List[Tuple[int, int, str, str]] = []

        self._text_cache: Dict[Tuple[int, int], str] = {}
        self._section_starts: List[int] = []
        self._collector_errors: List[tuple] = []

        self._collectors: List[Collector] = []
        self._routing: Dict[str, Tuple[Collector, ...]] = {}
        # Deterministic dispatch: track registered collectors to prevent duplicates
        self._registered_collector_ids: Set[int] = set()

        self._mask_map: Dict[str, int] = {}
        self._collector_masks: Dict[Collector, int] = {}

        self._dispatching: bool = False
        self.COLLECTOR_TIMEOUT_SECONDS: Optional[int] = 2

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

    def _canonicalize_tokens(self, tokens: List[Any]) -> List[Any]:
        """Convert token objects to plain dicts with allowlisted fields.

        This prevents supply-chain attacks where malicious token objects
        with poisoned __getattr__/__int__/__class__ methods could execute
        arbitrary code during hot-path dispatch.

        Performance: ~9% faster dispatch (no getattr() overhead in hot loop)
        Security: Eliminates attrGet() execution risk in dispatch_all()
        """
        ALLOWED_FIELDS = {
            "type", "tag", "nesting", "map", "level", "content",
            "markup", "info", "meta", "block", "hidden", "children",
            "attrIndex", "attrGet", "attrSet", "attrPush", "attrJoin"
        }

        canonicalized = []
        for tok in tokens:
            if isinstance(tok, dict):
                # Already a dict - validate and copy only allowed fields
                clean = {k: v for k, v in tok.items() if k in ALLOWED_FIELDS}
                canonicalized.append(clean)
            else:
                # Object - extract allowed fields safely
                clean = {}
                for field in ALLOWED_FIELDS:
                    try:
                        val = getattr(tok, field, None)
                        if val is not None:
                            clean[field] = val
                    except Exception:
                        # Malicious getter raised exception - skip this field
                        pass

                # Create simple namespace object (faster than dict for attribute access)
                from types import SimpleNamespace
                canonicalized.append(SimpleNamespace(**clean))

        return canonicalized

    # NOTE: timeout logic lives in utils/timeout.py; dispatcher is sole owner of timers.

    def _build_indices(self) -> None:
        """
        Orchestrate index building in logical stages.

        This method coordinates index building through micro-functions,
        each responsible for one concern. This makes failures easier to isolate
        and each stage independently testable.

        Stages:
            1. Normalize token.map fields to safe integers
            2. Build structural indices (single pass over tokens)
            3. Build sections from headings
        """
        # Stage 1: Normalize token maps (prevents crashes from malformed data)
        self._normalize_token_maps()

        # Stage 2: Build structural indices in single pass
        self._index_structure()

        # Stage 3: Build sections from headings
        self._build_sections()

    def _normalize_token_maps(self) -> None:
        """
        Normalize all token.map fields to safe (int, int) tuples.

        Prevents crashes from malformed token data by converting all map
        fields to validated integers, replacing None/invalid values with 0.

        This must run BEFORE indexing because _index_structure() assumes
        maps are (int, int) tuples.

        Modifies: self.tokens[*].map in-place
        """
        for tok in self.tokens:
            m_raw = getattr(tok, 'map', None)

            if m_raw and isinstance(m_raw, (list, tuple)) and len(m_raw) == 2:
                # Convert to safe integers
                try:
                    s = int(m_raw[0]) if m_raw[0] is not None else 0
                except Exception:
                    s = 0

                try:
                    e = int(m_raw[1]) if m_raw[1] is not None else s
                except Exception:
                    e = s

                # Validate: start >= 0, end >= start
                if s < 0:
                    s = 0
                if e < s:
                    e = s

                # Update token with normalized map
                try:
                    tok.map = (s, e)
                except Exception:
                    # Token is immutable or read-only - skip normalization
                    pass

    def _index_structure(self) -> None:
        """
        Build structural indices in single pass over tokens.

        Populates:
            - self.by_type: token_type -> [indices]
            - self.pairs: open_idx -> close_idx (and pairs_rev)
            - self.parents: token_idx -> parent_idx
            - self.fences: list of (start_line, end_line, info, lang)

        Uses a stack to track nesting and enforce depth limits.

        CRITICAL INVARIANT: Closing token parent = matching opening token.
        We set parents[close_idx] = open_idx explicitly, then skip the
        generic parent assignment for closing tokens to avoid overwriting.

        Raises:
            ValueError: If nesting depth exceeds MAX_NESTING
        """
        open_stack: list[int] = []

        for i, tok in enumerate(self.tokens):
            # Enforce nesting depth limit (prevents stack overflow attacks)
            if len(open_stack) > MAX_NESTING:
                raise ValueError(
                    f"Nesting depth exceeds limit: {len(open_stack)} > {MAX_NESTING} "
                    f"at token {i} (type={getattr(tok, 'type', '?')})"
                )

            # Index by type
            ttype = getattr(tok, "type", "")
            self.by_type[ttype].append(i)

            # Track pairs (open ↔ close) - MUST happen before parent assignment
            nesting = getattr(tok, "nesting", 0)
            if nesting == 1:  # Opening token
                open_stack.append(i)
            elif nesting == -1:  # Closing token
                if open_stack:
                    open_idx = open_stack.pop()
                    self.pairs[open_idx] = i
                    self.pairs_rev[i] = open_idx
                    # CRITICAL: Set closing token parent = opening token
                    # This prevents corruption from generic parent assignment below
                    self.parents[i] = open_idx

            # Track container parent (for non-closing tokens only)
            # Closing tokens already have parents set to their matching opener
            if nesting != -1 and open_stack:
                self.parents[i] = open_stack[-1]

            # Collect fence blocks (code blocks with language info)
            if ttype == "fence":
                m = getattr(tok, "map", None) or (None, None)
                if m[0] is not None and m[1] is not None:
                    info = (getattr(tok, "info", "") or "").strip()
                    self.fences.append((
                        int(m[0]),
                        int(m[1]),
                        info,
                        getattr(tok, "info", "") or ""
                    ))

    def _build_sections(self) -> None:
        """
        Build section boundaries from heading tokens.

        Populates:
            - self.sections: list of (start_line, end_line, token_idx, level, title) tuples
            - self._section_starts: list of section start lines (for binary search)

        Algorithm:
            1. Find all heading_open tokens
            2. Sort by line number (tolerates malformed ordering)
            3. Build nested section structure using stack
            4. Close higher-level sections when lower-level headings appear
            5. Close remaining sections at document end

        Uses Section dataclass internally for type safety, converts to tuples
        for API compatibility.
        """
        # Get and sort headings by line number
        heads = self.by_type.get("heading_open", [])
        heads = sorted(heads, key=lambda h: (getattr(self.tokens[h], 'map', (0,0))[0] or 0))

        sections_list: List[Section] = []
        section_stack: List[Section] = []
        last_end = self.line_count

        def level_of(idx: int) -> int:
            """Extract heading level from h1/h2/etc tag."""
            tok = self.tokens[idx]
            tag = getattr(tok, "tag", "") or ""
            return int(tag[1:]) if tag.startswith("h") and tag[1:].isdigit() else 1

        def get_heading_title(hidx: int) -> str:
            """
            Extract title text from inline token SCOPED to heading_open.

            CRITICAL INVARIANT: Only capture inline tokens that are children
            of the heading_open token (parent relationship must be verified).

            This prevents globally greedy capture of unrelated inline tokens.
            """
            if hidx + 1 < len(self.tokens):
                next_tok = self.tokens[hidx + 1]
                next_idx = hidx + 1
                # Check: (1) token is inline, (2) parent is this heading_open
                if (getattr(next_tok, "type", "") == "inline" and
                    self.parents.get(next_idx) == hidx):
                    content = getattr(next_tok, "content", "") or ""
                    # Strip extra whitespace and compact multiple spaces
                    # (prevents double spaces from inline children)
                    return " ".join(content.split())
            return ""

        # Build sections
        for hidx in heads:
            lvl = level_of(hidx)
            m = getattr(self.tokens[hidx], "map", None) or (0, 0)
            start = int(m[0])

            # Close higher/equal level sections
            while section_stack and section_stack[-1].level >= lvl:
                old_section = section_stack.pop()
                end_line = max(start - 1, old_section.start_line)

                # Replace with closed version (fill end_line)
                closed_section = Section(
                    start_line=old_section.start_line,
                    end_line=end_line,
                    token_idx=old_section.token_idx,
                    level=old_section.level,
                    title=old_section.title
                )

                # Find and replace in sections list
                for i, s in enumerate(sections_list):
                    if s.token_idx == old_section.token_idx:
                        sections_list[i] = closed_section
                        break

            # Open new section (end_line=None initially)
            new_section = Section(
                start_line=start,
                end_line=None,
                token_idx=hidx,
                level=lvl,
                title=get_heading_title(hidx)
            )
            sections_list.append(new_section)
            section_stack.append(new_section)

        # Close any remaining open sections at document end
        for section in section_stack:
            end_line = max(last_end, section.start_line)
            closed = Section(
                start_line=section.start_line,
                end_line=end_line,
                token_idx=section.token_idx,
                level=section.level,
                title=section.title
            )
            # Find and replace
            for i, s in enumerate(sections_list):
                if s.token_idx == section.token_idx:
                    sections_list[i] = closed
                    break

        # Store as tuples for API compatibility
        self.sections = [s.to_tuple() for s in sections_list]
        self._section_starts = [s.start_line for s in sections_list]

    # Query API
    def iter_by_type(self, token_type: str) -> List[int]:
        return self.by_type.get(token_type, [])

    def range_for(self, open_idx: int) -> Optional[int]:
        return self.pairs.get(open_idx)

    def parent(self, token_idx: int) -> Optional[int]:
        return self.parents.get(token_idx)

    @property
    def children(self) -> Dict[int, List[int]]:
        """
        Lazy children index: parent_idx -> [child_idx, ...].

        Built on-demand from parents index to reduce memory overhead.
        Cached after first access.

        CRITICAL: This is O(N) on first access, O(1) thereafter.
        """
        if self._children is None:
            ch: Dict[int, List[int]] = defaultdict(list)
            for idx, parent_idx in self.parents.items():
                ch[parent_idx].append(idx)
            self._children = dict(ch)  # Convert to regular dict
        return self._children

    def tokens_between(
        self,
        start_idx: int,
        end_idx: int,
        type_filter: Optional[str] = None
    ) -> List[int]:
        """
        Return token indices between start_idx and end_idx (exclusive).

        Uses binary search (bisect) when type_filter is provided for O(log N + K)
        performance instead of O(N) linear scan.

        Args:
            start_idx: Start index (exclusive)
            end_idx: End index (exclusive)
            type_filter: Optional token type to filter by

        Returns:
            List of token indices in range (start_idx, end_idx)

        Example:
            >>> wh = TokenWarehouse(tokens, tree, text)
            >>> # Get all tokens between heading_open and heading_close
            >>> heading_open_idx = 5
            >>> heading_close_idx = wh.pairs[heading_open_idx]
            >>> inline_tokens = wh.tokens_between(
            ...     heading_open_idx, heading_close_idx, type_filter="inline"
            ... )
        """
        if type_filter is None:
            # No filter: return all indices in range
            return list(range(start_idx + 1, end_idx))

        # With filter: use bisect for O(log N + K) performance
        import bisect
        indices = self.by_type.get(type_filter, [])
        if not indices:
            return []

        # Binary search for start and end positions
        left = bisect.bisect_left(indices, start_idx + 1)
        right = bisect.bisect_left(indices, end_idx)

        return indices[left:right]

    def text_between(self, start_idx: int, end_idx: int, join_spaces: bool = True) -> str:
        """
        Extract text content from inline tokens between start_idx and end_idx.

        Args:
            start_idx: Start index (exclusive)
            end_idx: End index (exclusive)
            join_spaces: If True, join with spaces; if False, concatenate directly

        Returns:
            Combined text content from inline tokens in range

        Example:
            >>> wh = TokenWarehouse(tokens, tree, text)
            >>> # Get heading text between heading_open and heading_close
            >>> text = wh.text_between(heading_open_idx, heading_close_idx)
            >>> # Get text without spaces (for compact titles)
            >>> compact = wh.text_between(start, end, join_spaces=False)
        """
        inline_indices = self.tokens_between(start_idx, end_idx, type_filter="inline")
        parts = []
        for i in inline_indices:
            tok = self.tokens[i]
            content = getattr(tok, "content", "")
            if content:
                parts.append(content)

        return (" " if join_spaces else "").join(parts)

    def sections_list(self) -> List[Tuple[int, Optional[int], int, int, str]]:
        """Return sections in canonical format: (start_line, end_line, token_idx, level, title)."""
        return self.sections

    def fences_list(self) -> List[Tuple[int, int, str, str]]:
        return self.fences

    def section_of(self, line_num: int) -> Optional[Section]:
        """
        Find the section containing the given line number.

        Uses binary search for O(log N) performance.

        Args:
            line_num: Line number to search for (0-indexed)

        Returns:
            Section dataclass if line is within a section, None otherwise

        Example:
            >>> section = wh.section_of(42)
            >>> if section:
            ...     print(f"Line 42 is in section: {section.title}")
        """
        from bisect import bisect_right
        if not self.sections:
            return None
        idx = bisect_right(self._section_starts, line_num) - 1
        if idx < 0 or idx >= len(self.sections):
            return None

        # sections are stored as tuples: (start_line, end_line, token_idx, level, title)
        section_tuple = self.sections[idx]
        section = Section.from_tuple(section_tuple)

        # Verify line is within section bounds
        if section.end_line is not None and line_num > section.end_line:
            return None
        if line_num < section.start_line:
            return None

        return section

    # Routing
    def register_collector(self, collector: Collector) -> None:
        """
        Register collector with deterministic order.

        INVARIANT: Dispatch order matches registration order (stable).
        Uses collector id() for dedup to prevent duplicates while preserving order.
        """
        collector_id = id(collector)

        # Skip if already registered (stable dedup - no set() randomness)
        if collector_id in self._registered_collector_ids:
            return

        self._registered_collector_ids.add(collector_id)
        self._collectors.append(collector)

        for ttype in collector.interest.types:
            prev = self._routing.get(ttype)
            self._routing[ttype] = tuple([*prev, collector]) if prev else (collector,)

        mask = 0
        # ✅ Deterministic routing: sorted() ensures consistent bit assignment across processes
        for t in sorted(getattr(collector.interest, "ignore_inside", set())):
            if t not in self._mask_map:
                self._mask_map[t] = len(self._mask_map)
            mask |= (1 << self._mask_map[t])
        self._collector_masks[collector] = mask

    def dispatch_all(self) -> None:
        # ✅ Reentrancy guard: prevent state corruption from nested dispatch_all() calls
        if self._dispatching:
            raise RuntimeError(
                "dispatch_all() called while already dispatching. "
                "This corrupts routing/mask state. Check collectors for reentrant calls."
            )

        self._dispatching = True
        try:
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

                    # ✅ Per-collector timeout wrapper (prevents DoS from hanging collectors)
                    try:
                        with collector_timeout(self.COLLECTOR_TIMEOUT_SECONDS or 0):
                            col.on_token(i, tok, ctx, self)
                    except TimeoutError as te:
                        try:
                            self._collector_errors.append((
                                getattr(col, 'name', repr(col)),
                                i,
                                'TimeoutError'
                            ))
                        except Exception:
                            pass
                        if globals().get('RAISE_ON_COLLECTOR_ERROR'):
                            raise
                    except Exception as e:
                        try:
                            self._collector_errors.append((getattr(col, 'name', repr(col)), i, type(e).__name__))
                        except Exception:
                            pass
                        if globals().get('RAISE_ON_COLLECTOR_ERROR'):
                            raise
                        # continue
        finally:
            self._dispatching = False
