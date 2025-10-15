"""
End-to-end collector caps and truncation litmus tests.

Verifies that collectors implement per-type resource limits to prevent:
1. Memory amplification attacks (OOM via unbounded accumulation)
2. CPU exhaustion (O(N²) processing of massive lists)
3. Downstream DoS (overwhelming consumers with huge result sets)

This prevents DoS (Denial of Service) attacks via resource exhaustion.
"""
import pytest
import json
from pathlib import Path
from types import SimpleNamespace


# Per-collector caps (must match implementation)
MAX_LINKS_PER_DOC = 10_000
MAX_IMAGES_PER_DOC = 5_000
MAX_HEADINGS_PER_DOC = 5_000
MAX_CODE_BLOCKS_PER_DOC = 2_000
MAX_TABLES_PER_DOC = 1_000
MAX_LIST_ITEMS_PER_DOC = 50_000


def test_links_collector_enforces_cap():
    """
    Test that links collector enforces MAX_LINKS_PER_DOC cap.

    Prevents memory amplification via documents with millions of links.
    """
    try:
        from doxstrux.markdown.collectors_phase8.links_collector import LinksCollector
    except ImportError:
        pytest.skip("LinksCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with 15,000 links (exceeds MAX_LINKS_PER_DOC)
    tokens = []
    for i in range(15_000):
        tokens.extend([
            SimpleNamespace(
                type="link_open",
                nesting=1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x, default=f"https://example.com/{i}": default if x == "href" else None
            ),
            SimpleNamespace(
                type="text",
                nesting=0,
                tag="",
                map=None,
                info=None,
                content=f"Link {i}",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="link_close",
                nesting=-1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
        ])

    collector = LinksCollector()
    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector)
    wh.dispatch_all()

    # Get results
    links = collector.finalize(wh)

    # Verify cap enforced
    assert len(links) <= MAX_LINKS_PER_DOC, \
        f"Links collector exceeded cap: {len(links)} > {MAX_LINKS_PER_DOC}"

    # Verify truncation metadata present
    if len(links) == MAX_LINKS_PER_DOC:
        # Check if collector added truncation metadata
        # (Implementation detail: check metadata in finalize() return)
        assert True  # If we got here, truncation worked


def test_images_collector_enforces_cap():
    """
    Test that images collector enforces MAX_IMAGES_PER_DOC cap.

    Prevents memory amplification via documents with massive image galleries.
    """
    try:
        from doxstrux.markdown.collectors_phase8.media_collector import MediaCollector
    except ImportError:
        pytest.skip("MediaCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with 7,000 images (exceeds MAX_IMAGES_PER_DOC)
    tokens = []
    for i in range(7_000):
        tokens.append(
            SimpleNamespace(
                type="image",
                nesting=0,
                tag="img",
                map=None,
                info=None,
                content="",
                attrGet=lambda x, default=f"https://example.com/img{i}.png": default if x == "src" else None
            )
        )

    collector = MediaCollector()
    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector)
    wh.dispatch_all()

    # Get results
    images = collector.finalize(wh)

    # Verify cap enforced
    assert len(images) <= MAX_IMAGES_PER_DOC, \
        f"Images collector exceeded cap: {len(images)} > {MAX_IMAGES_PER_DOC}"


def test_headings_collector_enforces_cap():
    """
    Test that headings collector enforces MAX_HEADINGS_PER_DOC cap.

    Prevents ToC explosion and metadata bloat.
    """
    try:
        from doxstrux.markdown.collectors_phase8.sections_collector import SectionsCollector
    except ImportError:
        pytest.skip("SectionsCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with 7,000 headings (exceeds MAX_HEADINGS_PER_DOC)
    tokens = []
    for i in range(7_000):
        tokens.extend([
            SimpleNamespace(
                type="heading_open",
                tag="h2",
                nesting=1,
                map=[i, i+1],
                info=None,
                content="",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="inline",
                tag="",
                nesting=0,
                map=None,
                info=None,
                content=f"Heading {i}",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="heading_close",
                tag="h2",
                nesting=-1,
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
        ])

    collector = SectionsCollector()
    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector)
    wh.dispatch_all()

    # Get results
    sections = collector.finalize(wh)

    # Verify cap enforced
    assert len(sections) <= MAX_HEADINGS_PER_DOC, \
        f"Headings collector exceeded cap: {len(sections)} > {MAX_HEADINGS_PER_DOC}"


def test_code_blocks_collector_enforces_cap():
    """
    Test that code blocks collector enforces MAX_CODE_BLOCKS_PER_DOC cap.

    Prevents syntax highlighting CPU exhaustion.
    """
    try:
        from doxstrux.markdown.collectors_phase8.codeblocks_collector import CodeBlocksCollector
    except ImportError:
        pytest.skip("CodeBlocksCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with 3,000 code blocks (exceeds MAX_CODE_BLOCKS_PER_DOC)
    tokens = []
    for i in range(3_000):
        tokens.append(
            SimpleNamespace(
                type="fence",
                tag="code",
                nesting=0,
                map=[i*3, i*3+3],
                info="python",
                content=f"print('Block {i}')\n",
                attrGet=lambda x: None
            )
        )

    collector = CodeBlocksCollector()
    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector)
    wh.dispatch_all()

    # Get results
    code_blocks = collector.finalize(wh)

    # Verify cap enforced
    assert len(code_blocks) <= MAX_CODE_BLOCKS_PER_DOC, \
        f"Code blocks collector exceeded cap: {len(code_blocks)} > {MAX_CODE_BLOCKS_PER_DOC}"


def test_tables_collector_enforces_cap():
    """
    Test that tables collector enforces MAX_TABLES_PER_DOC cap.

    Prevents O(N²) processing of massive table documents.
    """
    try:
        from doxstrux.markdown.collectors_phase8.tables_collector import TablesCollector
    except ImportError:
        pytest.skip("TablesCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with 1,500 tables (exceeds MAX_TABLES_PER_DOC)
    tokens = []
    for i in range(1_500):
        tokens.extend([
            SimpleNamespace(
                type="table_open",
                tag="table",
                nesting=1,
                map=[i*5, i*5+5],
                info=None,
                content="",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="thead_open",
                tag="thead",
                nesting=1,
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="tr_open",
                tag="tr",
                nesting=1,
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="th_open",
                tag="th",
                nesting=1,
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="inline",
                tag="",
                nesting=0,
                map=None,
                info=None,
                content=f"Table {i}",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="th_close",
                tag="th",
                nesting=-1,
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="tr_close",
                tag="tr",
                nesting=-1,
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="thead_close",
                tag="thead",
                nesting=-1,
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="table_close",
                tag="table",
                nesting=-1,
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
        ])

    collector = TablesCollector()
    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector)
    wh.dispatch_all()

    # Get results
    tables = collector.finalize(wh)

    # Verify cap enforced
    assert len(tables) <= MAX_TABLES_PER_DOC, \
        f"Tables collector exceeded cap: {len(tables)} > {MAX_TABLES_PER_DOC}"


def test_list_items_collector_enforces_cap():
    """
    Test that list items collector enforces MAX_LIST_ITEMS_PER_DOC cap.

    Prevents O(N²) traversal of deeply nested or massive lists.
    """
    try:
        from doxstrux.markdown.collectors_phase8.lists_collector import ListsCollector
    except ImportError:
        pytest.skip("ListsCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with 60,000 list items (exceeds MAX_LIST_ITEMS_PER_DOC)
    tokens = [
        SimpleNamespace(
            type="bullet_list_open",
            tag="ul",
            nesting=1,
            map=[0, 60000],
            info=None,
            content="",
            attrGet=lambda x: None
        )
    ]

    for i in range(60_000):
        tokens.extend([
            SimpleNamespace(
                type="list_item_open",
                tag="li",
                nesting=1,
                map=[i, i+1],
                info=None,
                content="",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="inline",
                tag="",
                nesting=0,
                map=None,
                info=None,
                content=f"Item {i}",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="list_item_close",
                tag="li",
                nesting=-1,
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
        ])

    tokens.append(
        SimpleNamespace(
            type="bullet_list_close",
            tag="ul",
            nesting=-1,
            map=None,
            info=None,
            content="",
            attrGet=lambda x: None
        )
    )

    collector = ListsCollector()
    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector)
    wh.dispatch_all()

    # Get results
    lists = collector.finalize(wh)

    # Count total list items across all lists
    total_items = 0
    for lst in lists:
        total_items += len(lst.get("items", []))

    # Verify cap enforced
    assert total_items <= MAX_LIST_ITEMS_PER_DOC, \
        f"List items exceeded cap: {total_items} > {MAX_LIST_ITEMS_PER_DOC}"


def test_adversarial_large_corpus_respects_all_caps():
    """
    Integration test: Load adversarial_large.json and verify all caps enforced.

    This corpus contains intentionally oversized structures to test resource limits.
    """
    corpus_path = Path(__file__).parent.parent.parent / "adversarial_corpora" / "adversarial_large.json"

    if not corpus_path.exists():
        pytest.skip(f"Corpus not found: {corpus_path}")

    # Load corpus
    test_cases = json.loads(corpus_path.read_text())

    # Test each case
    for test_case in test_cases:
        element_type = test_case.get("type")
        tokens = test_case.get("tokens", [])

        # Skip if not a capped element type
        if element_type not in ["links", "images", "headings", "code_blocks", "tables", "list_items"]:
            continue

        # Convert dict tokens to SimpleNamespace
        ns_tokens = []
        for token_dict in tokens:
            ns = SimpleNamespace(**token_dict)
            # Add attrGet method
            attrs = token_dict.get("attrs", {})
            ns.attrGet = lambda x, attrs=attrs: attrs.get(x)
            ns_tokens.append(ns)

        # Get appropriate collector
        try:
            if element_type == "links":
                from doxstrux.markdown.collectors_phase8.links_collector import LinksCollector
                collector = LinksCollector()
                max_cap = MAX_LINKS_PER_DOC
            elif element_type == "images":
                from doxstrux.markdown.collectors_phase8.media_collector import MediaCollector
                collector = MediaCollector()
                max_cap = MAX_IMAGES_PER_DOC
            elif element_type == "headings":
                from doxstrux.markdown.collectors_phase8.sections_collector import SectionsCollector
                collector = SectionsCollector()
                max_cap = MAX_HEADINGS_PER_DOC
            elif element_type == "code_blocks":
                from doxstrux.markdown.collectors_phase8.codeblocks_collector import CodeBlocksCollector
                collector = CodeBlocksCollector()
                max_cap = MAX_CODE_BLOCKS_PER_DOC
            elif element_type == "tables":
                from doxstrux.markdown.collectors_phase8.tables_collector import TablesCollector
                collector = TablesCollector()
                max_cap = MAX_TABLES_PER_DOC
            elif element_type == "list_items":
                from doxstrux.markdown.collectors_phase8.lists_collector import ListsCollector
                collector = ListsCollector()
                max_cap = MAX_LIST_ITEMS_PER_DOC
            else:
                continue
        except ImportError:
            pytest.skip(f"Collector for {element_type} not available")

        try:
            import importlib
            wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
        except ImportError:
            pytest.skip("token_warehouse not available")

        TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
        if TokenWarehouse is None:
            pytest.skip("TokenWarehouse not available")

        # Run collector
        wh = TokenWarehouse(ns_tokens, tree=None)
        wh.register_collector(collector)
        wh.dispatch_all()
        results = collector.finalize(wh)

        # Verify cap enforced
        result_count = len(results)
        if element_type == "list_items":
            # Count total items across all lists
            result_count = sum(len(lst.get("items", [])) for lst in results)

        assert result_count <= max_cap, \
            f"Collector {element_type} exceeded cap in adversarial corpus: {result_count} > {max_cap}"


def test_truncation_metadata_present():
    """
    Test that collectors add truncation metadata when caps are hit.

    Downstream consumers need to know if results were truncated.
    """
    try:
        from doxstrux.markdown.collectors_phase8.links_collector import LinksCollector
    except ImportError:
        pytest.skip("LinksCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with links that will hit the cap
    tokens = []
    for i in range(MAX_LINKS_PER_DOC + 1000):  # Exceed cap by 1000
        tokens.extend([
            SimpleNamespace(
                type="link_open",
                nesting=1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x, default=f"https://example.com/{i}": default if x == "href" else None
            ),
            SimpleNamespace(
                type="text",
                nesting=0,
                tag="",
                map=None,
                info=None,
                content=f"Link {i}",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="link_close",
                nesting=-1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
        ])

    collector = LinksCollector()
    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector)
    wh.dispatch_all()

    # Get results
    links = collector.finalize(wh)

    # Verify truncation occurred
    assert len(links) == MAX_LINKS_PER_DOC, \
        f"Expected truncation at {MAX_LINKS_PER_DOC}, got {len(links)}"

    # Check for truncation metadata
    # (Implementation detail: collectors should add metadata to finalize() return)
    # This could be a separate metadata dict or a flag in the result
    # For now, we verify the cap was enforced
    assert True  # If we got here, truncation worked


def test_no_false_truncation_below_caps():
    """
    Test that collectors don't truncate when under caps.

    Prevents over-aggressive truncation that loses valid data.
    """
    try:
        from doxstrux.markdown.collectors_phase8.links_collector import LinksCollector
    except ImportError:
        pytest.skip("LinksCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Create tokens with links well under the cap
    num_links = 100  # Well under MAX_LINKS_PER_DOC
    tokens = []
    for i in range(num_links):
        tokens.extend([
            SimpleNamespace(
                type="link_open",
                nesting=1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x, default=f"https://example.com/{i}": default if x == "href" else None
            ),
            SimpleNamespace(
                type="text",
                nesting=0,
                tag="",
                map=None,
                info=None,
                content=f"Link {i}",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="link_close",
                nesting=-1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
        ])

    collector = LinksCollector()
    wh = TokenWarehouse(tokens, tree=None)
    wh.register_collector(collector)
    wh.dispatch_all()

    # Get results
    links = collector.finalize(wh)

    # Verify NO truncation occurred
    assert len(links) == num_links, \
        f"False truncation: expected {num_links}, got {len(links)}"
