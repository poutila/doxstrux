
from __future__ import annotations
import os
from typing import Any, Dict, List, Tuple

# Adapter for integrating the Warehouse under a feature flag without
# disturbing your Phase 7 extractors.

USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"

def extract_links_with_adapter(tokens, tree, original_extract_links):
    """Switchable implementation for _extract_links().
    - tokens: markdown-it token list
    - tree:   SyntaxTreeNode
    - original_extract_links: call-through to Phase 7 extractor
    """
    if not USE_WAREHOUSE:
        return original_extract_links(tokens)

    # Warehouse path
    from ..utils.token_warehouse import TokenWarehouse
    from ..collectors_phase8.links import LinksCollector

    wh = TokenWarehouse(tokens, tree)
    links = LinksCollector()
    wh.register_collector(links)
    wh.dispatch_all()
    out = wh.finalize_all().get("links", [])
    return out
