
from __future__ import annotations

def test_basic_indices_smoke():
    """Verify warehouse builds all indices correctly."""
    class Tok:
        def __init__(self, t, nesting=0, tag="", map_=None, info=None, href=None, content=""):
            self.type = t; self.nesting = nesting; self.tag = tag
            self.map = map_; self.info = info; self._href = href; self.content = content
        def attrGet(self, name): return self._href if name == "href" else None

    tokens = [
        Tok("heading_open", 1, "h1", (0,1)),
        Tok("inline", 0, "", None, content="Title"),
        Tok("heading_close", -1, "h1", (0,1)),
        Tok("paragraph_open", 1, "", (2,3)),
        Tok("inline", 0, "", None, content="Para"),
        Tok("paragraph_close", -1, "", (2,3)),
        Tok("fence", 0, "", (4,6), info="python"),
    ]

    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    wh = TokenWarehouse(tokens, tree=None)

    # Test by_type index
    assert "heading_open" in wh.by_type
    assert wh.iter_by_type("fence") == [6]

    # Test pairs index
    open_idx = wh.by_type["heading_open"][0]
    close_idx = wh.range_for(open_idx)
    assert isinstance(close_idx, int)

    # Test sections index
    secs = wh.sections_list()
    assert len(secs) == 1 and secs[0][3] == 1

    # Test fences index
    fences = wh.fences_list()
    assert fences and fences[0][2] == "python"

def test_dispatch_links_collector():
    """Verify collector registration and dispatch works correctly."""
    class Tok:
        def __init__(self, t, nesting=0, tag="", map_=None, info=None, href=None, content=""):
            self.type = t
            self.nesting = nesting
            self.tag = tag
            self.map = map_
            self.info = info
            self._href = href
            self.content = content
        def attrGet(self, name):
            return self._href if name == "href" else None

    tokens = [
        Tok("paragraph_open", 1, "", (0,1)),
        Tok("link_open", 1, "", (0,1), href="https://example.com"),
        Tok("inline", 0, "", None, content="x"),
        Tok("link_close", -1, ""),
        Tok("paragraph_close", -1, "", (0,1)),
    ]

    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    from doxstrux.markdown.collectors_phase8.links import LinksCollector

    wh = TokenWarehouse(tokens, tree=None)
    col = LinksCollector()
    wh.register_collector(col)
    wh.dispatch_all()
    data = wh.finalize_all()["links"]
    assert data and data[0]["url"] == "https://example.com" and data[0]["text"] == "x"

def test_lines_property_and_inference():
    """Verify lines property works with/without text parameter."""
    class Tok:
        def __init__(self, t, nesting=0, tag="", map_=None, info=None, content=""):
            self.type = t; self.nesting = nesting; self.tag = tag
            self.map = map_; self.info = info; self.content = content
        def attrGet(self, name): return None

    tokens = [
        Tok("heading_open", 1, "h1", (0,1)),
        Tok("inline", 0, "", None, content="A"),
        Tok("heading_close", -1, "h1", (0,1)),
        Tok("paragraph_open", 1, "", (2,3)),
        Tok("inline", 0, "", None, content="Para"),
        Tok("paragraph_close", -1, "", (2,3)),
    ]

    text = "H1\n\nPara\n"
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse

    # With text parameter
    wh = TokenWarehouse(tokens, tree=None, text=text)
    assert wh.lines is not None and len(wh.lines) == len(text.splitlines(True))
    assert wh.line_count == len(wh.lines)

    # Without text parameter (inference)
    wh2 = TokenWarehouse(tokens, tree=None)
    assert wh2.lines is None
    assert wh2.line_count >= 3

def test_section_of_binary_search_boundaries():
    """Verify section_of binary search handles boundaries correctly."""
    class Tok:
        def __init__(self, t, nesting=0, tag="", map_=None, info=None, content=""):
            self.type = t; self.nesting = nesting; self.tag = tag
            self.map = map_; self.info = info; self.content = content
        def attrGet(self, name): return None

    tokens = [
        Tok("heading_open", 1, "h1", (0,1)),
        Tok("inline", 0, "", None, content="A"),
        Tok("heading_close", -1, "h1", (0,1)),
        Tok("paragraph_open", 1, "", (2,3)),
        Tok("inline", 0, "", None, content="x"),
        Tok("paragraph_close", -1, "", (2,3)),
        Tok("heading_open", 1, "h2", (4,5)),
        Tok("inline", 0, "", None, content="B"),
        Tok("heading_close", -1, "h2", (4,5)),
        Tok("paragraph_open", 1, "", (6,7)),
        Tok("inline", 0, "", None, content="y"),
        Tok("paragraph_close", -1, "", (6,7)),
    ]

    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    wh = TokenWarehouse(tokens, tree=None)

    # First section
    assert wh.section_of(0) == "section_0"
    assert wh.section_of(2) == "section_0"
    assert wh.section_of(3) == "section_0"

    # Second section
    assert wh.section_of(4) == "section_1"
    assert wh.section_of(6) == "section_1"
    assert wh.section_of(7) == "section_1"

    # Out of range
    assert wh.section_of(1000) is None

def test_ignore_mask_links_inside_fence_are_ignored():
    """Verify O(1) bitmask ignore-inside works correctly."""
    class Tok:
        def __init__(self, t, nesting=0, tag="", map_=None, info=None, href=None, content=""):
            self.type = t; self.nesting = nesting; self.tag = tag
            self.map = map_; self.info = info; self._href = href; self.content = content
        def attrGet(self, name): return self._href if name == "href" else None

    tokens = [
        Tok("fence", 0, "", (0,3), info="md"),
        Tok("link_open", 1, "", (1,2), href="https://should-ignore"),
        Tok("inline", 0, "", None, content="hidden"),
        Tok("link_close", -1, ""),
    ]

    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    from doxstrux.markdown.collectors_phase8.links import LinksCollector

    wh = TokenWarehouse(tokens, tree=None)
    col = LinksCollector()
    wh.register_collector(col)
    wh.dispatch_all()
    data = wh.finalize_all()["links"]
    # link was inside a fence; LinksCollector.ignore_inside includes 'fence', so it should be ignored
    assert data == []

def test_invariants_pairs_and_sections_sorted():
    """Verify structural invariants (pairs valid, sections sorted)."""
    class Tok:
        def __init__(self, t, nesting=0, tag="", map_=None, info=None, content=""):
            self.type = t; self.nesting = nesting; self.tag = tag
            self.map = map_; self.info = info; self.content = content
        def attrGet(self, name): return None

    tokens = [
        Tok("heading_open", 1, "h1", (0,1)),
        Tok("inline", 0, "", None, content="A"),
        Tok("heading_close", -1, "h1", (0,1)),
        Tok("paragraph_open", 1, "", (2,3)),
        Tok("inline", 0, "", None, content="x"),
        Tok("paragraph_close", -1, "", (2,3)),
        Tok("heading_open", 1, "h2", (4,5)),
        Tok("inline", 0, "", None, content="B"),
        Tok("heading_close", -1, "h2", (4,5)),
        Tok("paragraph_open", 1, "", (6,7)),
        Tok("inline", 0, "", None, content="y"),
        Tok("paragraph_close", -1, "", (6,7)),
    ]

    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    wh = TokenWarehouse(tokens, tree=None)

    # Verify pairs invariant: open < close
    for o, c in wh.pairs.items():
        assert 0 <= o < c < len(tokens)

    # Verify sections invariant: sorted by start, non-overlapping
    secs = wh.sections_list()
    starts = [s for _, s, _, _, _ in secs]
    assert starts == sorted(starts)
    for i in range(1, len(secs)):
        _, prev_s, prev_e, _, _ = secs[i-1]
        _, s, e, _, _ = secs[i]
        assert prev_s <= prev_e < s
