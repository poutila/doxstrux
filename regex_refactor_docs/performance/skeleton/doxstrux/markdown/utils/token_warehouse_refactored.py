# This file contains the refactored _build_indices() implementation
# It will be integrated into token_warehouse.py after verification

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
        4. Store sections in canonical format
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

    This must run BEFORE indexing because index_structure() assumes
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
        - self.pairs: open_idx -> close_idx
        - self.parents: token_idx -> parent_idx
        - self.fences: list of (start_line, end_line, info, lang)

    Uses a stack to track nesting and enforce depth limits.

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

        # Track parent (must happen before mutating stack)
        if open_stack:
            self.parents[i] = open_stack[-1]

        # Track pairs (open ↔ close)
        nesting = getattr(tok, "nesting", 0)
        if nesting == 1:  # Opening token
            open_stack.append(i)
        elif nesting == -1:  # Closing token
            if open_stack:
                self.pairs[open_stack.pop()] = i

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
    from .section import Section

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
        """Extract title text from inline token following heading_open."""
        if hidx + 1 < len(self.tokens):
            next_tok = self.tokens[hidx + 1]
            if getattr(next_tok, "type", "") == "inline":
                return getattr(next_tok, "content", "") or ""
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
