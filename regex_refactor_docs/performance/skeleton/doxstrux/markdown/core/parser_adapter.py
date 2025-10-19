
from __future__ import annotations
import os
from typing import Any, Dict, List, Tuple

# Adapter for integrating the Warehouse under a feature flag without
# disturbing your Phase 7 extractors.

USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"

def extract_links_with_adapter(tokens, tree, normalized_text, original_extract_links):
    """
    Switchable implementation for _extract_links().

    CRITICAL INVARIANT: tokens must be from normalized text (NFC + LF).
    Use parse_markdown_normalized() to ensure correct normalization order.

    Args:
        tokens: markdown-it token list (from NORMALIZED text)
        tree: SyntaxTreeNode
        normalized_text: The SAME text that tokens were parsed from (NFC + LF)
        original_extract_links: call-through to Phase 7 extractor

    Example:
        >>> from ..utils.text_normalization import parse_markdown_normalized
        >>> tokens, tree, normalized = parse_markdown_normalized(content)
        >>> links = extract_links_with_adapter(tokens, tree, normalized, original_extract)
    """
    if not USE_WAREHOUSE:
        return original_extract_links(tokens)

    # Warehouse path
    from ..utils.token_warehouse import TokenWarehouse
    from ..collectors_phase8.links import LinksCollector

    wh = TokenWarehouse(tokens, tree, normalized_text)
    links = LinksCollector()
    wh.register_collector(links)
    wh.dispatch_all()
    out = wh.finalize_all().get("links", [])
    return out
