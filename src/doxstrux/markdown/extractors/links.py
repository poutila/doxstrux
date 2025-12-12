"""Link extractor - Extract links with security validation and embedded image detection.

This module extracts link structures from markdown tokens, including:
- Regular links with href, text, and line attribution
- Link scheme validation (security: disallowed schemes flagged)
- Link type classification (internal/external/anchor/email/tel/image)
- Embedded images in links (e.g., [![alt](img.jpg)](link.url))
- Standalone images as link references
- Softbreak tracking for accurate line numbers

Functions:
    extract_links: Extract all links from tokens with security metadata
    process_inline_tokens: Process inline tokens to extract links and images
"""

from typing import Any


def extract_links(
    tokens: list[Any],
    process_inline_tokens_func: Any
) -> list[dict]:
    """Extract links robustly using token parsing.

    Args:
        tokens: List of markdown-it Token objects
        process_inline_tokens_func: Function to process inline tokens

    Returns:
        List of link dicts with security metadata
    """
    links = []

    # Process all tokens to find links
    for token in tokens:
        if token.type == "inline" and token.children:
            # Process inline tokens which contain links
            process_inline_tokens_func(token.children, links, token.map)

    return links


def process_inline_tokens(
    tokens: list[Any],
    links: list[dict],
    line_map: Any,
    effective_allowed_schemes: set[str],
    security_validators: Any,
    media_module: Any
) -> None:
    """Process inline tokens to extract links with improved line attribution.

    Args:
        tokens: List of inline tokens to process
        links: Mutable list to collect link dicts
        line_map: Line map from parent token
        effective_allowed_schemes: Set of allowed URL schemes
        security_validators: Security validators module
        media_module: Media extractor module for image metadata
    """
    i = 0
    softbreak_count = 0  # Track softbreaks for line offset

    while i < len(tokens):
        token = tokens[i]

        if token.type == "link_open":
            # Snapshot the break count at link_open for accurate line attribution
            link_line_offset = softbreak_count

            # Extract href from attributes
            href = token.attrGet("href") or ""

            # Validate link scheme for security (Phase 6 Task 6.1)
            scheme, is_allowed = security_validators.validate_link_scheme(href, effective_allowed_schemes)

            # Collect text until link_close and watch for embedded images
            text_parts = []
            saw_img = None
            img_title = ""
            i += 1
            while i < len(tokens) and tokens[i].type != "link_close":
                if tokens[i].type == "text" or tokens[i].type == "code_inline":
                    text_parts.append(tokens[i].content or "")
                elif tokens[i].type == "image":
                    # Capture image info for linked images like [![alt](img.jpg)](link.url)
                    img_src = tokens[i].attrGet("src") or ""
                    img_alt = (
                        getattr(tokens[i], "content", "") or tokens[i].attrGet("alt") or ""
                    )
                    img_title = tokens[i].attrGet("title") or ""
                    saw_img = {
                        "src": img_src,
                        "alt": img_alt,
                        "image_id": media_module._generate_image_id(
                            img_src, (line_map[0] + link_line_offset) if line_map else None
                        ),
                    }
                    text_parts.append(img_alt)  # Use alt text as link text
                elif tokens[i].type in ("softbreak", "hardbreak"):
                    text_parts.append("\n")
                    softbreak_count += 1  # Still track breaks for subsequent tokens
                i += 1

            text = "".join(text_parts)
            # Use snapshotted offset for link's line number
            line_num = (line_map[0] + link_line_offset) if line_map else None

            # Determine link type with enhanced scheme detection (Phase 6 Task 6.1)
            link_type = security_validators.classify_link_type(href)

            # Add the main link record with security metadata
            links.append(
                {
                    "text": text,
                    "url": href,
                    "line": line_num,
                    "type": link_type,
                    "scheme": scheme,  # Security: track scheme
                    "allowed": is_allowed,  # Security: RAG safety flag
                }
            )

            # If there was an embedded image, add a second record for joinability
            if saw_img:
                # Get unified image metadata for consistency with first-class images
                img_metadata = media_module._determine_image_metadata(saw_img["src"])
                links.append(
                    {
                        "type": "image",
                        "url": saw_img["src"],
                        "src": saw_img["src"],  # Consistent with first-class images
                        "alt": saw_img["alt"],  # Consistent with first-class images
                        "title": img_title,
                        "text": saw_img["alt"],  # Keep for backward compatibility
                        "line": line_num,
                        "image_id": saw_img["image_id"],
                        "image_kind": img_metadata["image_kind"],  # Unified metadata
                        "format": img_metadata["format"],  # Unified metadata
                    }
                )

        elif token.type == "image":
            # Snapshot the break count at image token for accurate line attribution
            image_line_offset = softbreak_count

            # Extract image attributes with stable ID
            src = token.attrGet("src") or ""
            alt = getattr(token, "content", "") or token.attrGet("alt") or ""
            title = token.attrGet("title") or ""

            # Use snapshotted offset for image's line number
            line_num = (line_map[0] + image_line_offset) if line_map else None

            # Generate stable ID (same as in _extract_images)
            image_id = media_module._generate_image_id(src, line_num)

            # Add standardized image reference to links with unified metadata
            img_metadata = media_module._determine_image_metadata(src)
            links.append(
                {
                    "image_id": image_id,  # For joining with images table
                    "text": alt,  # Keep for backward compatibility
                    "url": src,  # Keep for backward compatibility
                    "src": src,  # Consistent with first-class images
                    "alt": alt,  # Consistent with first-class images
                    "title": title,
                    "line": line_num,
                    "type": "image",
                    "image_kind": img_metadata["image_kind"],  # Unified metadata
                    "format": img_metadata["format"],  # Unified metadata
                }
            )

        elif token.type in ("softbreak", "hardbreak"):
            # Track line breaks for better attribution
            softbreak_count += 1

        i += 1
