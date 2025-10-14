"""Media extractor - Images with metadata and security validation.

This module extracts image elements from markdown tokens, including:
- External images (http/https URLs)
- Local images (relative paths)
- Data URI images (embedded base64)

Functions:
    extract_images: Extract all images with enhanced metadata
"""

import hashlib
import os
from typing import Any
from doxstrux.markdown.security import validators as security_validators


def extract_images(
    tokens: list[Any],
    effective_allowed_schemes: set[str],
    cache: dict[str, Any] | None = None
) -> list[dict]:
    """Extract all images as first-class elements with enhanced metadata.

    Args:
        tokens: List of markdown-it Token objects
        effective_allowed_schemes: Set of allowed URL schemes for validation
        cache: Optional cache dict to store results

    Returns:
        List of image records with stable IDs, metadata, and security info

    Example:
        >>> images = extract_images(tokens, {"http", "https"})
        >>> images[0]['image_id']
        'a1b2c3d4e5f6g7h8'
    """
    # Return cached result if available
    if cache and cache.get("images") is not None:
        return cache["images"]

    images = []
    seen_ids = set()  # Track to avoid duplicates

    # Process all tokens to find images
    for token in tokens:
        if token.type == "inline" and token.children:
            _process_inline_tokens_for_images(
                token.children,
                images,
                token.map,
                seen_ids,
                effective_allowed_schemes
            )

    # Cache the result
    if cache is not None:
        cache["images"] = images

    return images


def _process_inline_tokens_for_images(
    tokens: list[Any],
    images: list[dict],
    line_map: tuple[int, int] | None,
    seen_ids: set[str],
    effective_allowed_schemes: set[str]
) -> None:
    """Process inline tokens to extract images with enhanced metadata.

    Args:
        tokens: List of inline Token objects
        images: List to append image records to (modified in place)
        line_map: Line range tuple (start, end) from parent token
        seen_ids: Set of seen image IDs to avoid duplicates
        effective_allowed_schemes: Set of allowed URL schemes
    """
    softbreak_count = 0  # Track softbreaks for line offset

    for i, token in enumerate(tokens):
        if token.type == "image":
            # Snapshot the break count at image token for accurate line attribution
            image_line_offset = softbreak_count

            # Extract image attributes with enhanced metadata
            src = token.attrGet("src") or ""
            alt = getattr(token, "content", "") or token.attrGet("alt") or ""
            title = token.attrGet("title") or ""

            # Use snapshotted offset for image's line number
            line_num = (line_map[0] + image_line_offset) if line_map else None

            # Generate stable ID
            image_id = _generate_image_id(src, line_num)

            # Skip duplicates (same image on same line)
            if image_id in seen_ids:
                continue
            seen_ids.add(image_id)

            # Validate image URL scheme for security
            scheme, is_allowed = security_validators.validate_link_scheme(
                src, effective_allowed_schemes
            )

            # Use centralized metadata determination for consistency
            img_metadata = _determine_image_metadata(src)
            image_kind = img_metadata["image_kind"]
            format_type = img_metadata["format"]

            # Parse data URIs for additional metadata
            if image_kind == "data":
                data_info = security_validators.parse_data_uri(src)
            else:
                data_info = {}

            # Build unified image record
            image_record = {
                "image_id": image_id,  # Stable ID for joining
                "src": src,
                "alt": alt,
                "title": title,
                "line": line_num,
                "image_kind": image_kind,  # 'external'|'local'|'data'
                "format": format_type,
                "has_alt": bool(alt.strip()),
                "has_title": bool(title.strip()),
                "scheme": scheme,  # URL scheme for security validation
                "allowed": is_allowed,  # Whether scheme is allowed
            }

            # Add data URI info if present
            if data_info:
                # Map security_validators field names to baseline names
                image_record.update(
                    {
                        "media_type": data_info.get("mediatype"),
                        "encoding": data_info.get("encoding"),
                        "bytes_approx": data_info.get("size_bytes"),
                    }
                )

            images.append(image_record)

        elif token.type in ("softbreak", "hardbreak"):
            # Track line breaks for better attribution
            softbreak_count += 1


def _generate_image_id(src: str, line: int | None) -> str:
    """Generate stable image ID from source and line number.

    Args:
        src: Image source URL or path
        line: Line number where image appears

    Returns:
        16-character hex hash for stable identification
    """
    # Use src + line for stability (same image on different lines gets different ID)
    id_source = f"{src}|{line if line is not None else -1}"
    return hashlib.sha1(id_source.encode()).hexdigest()[:16]


def _determine_image_metadata(src: str) -> dict[str, str]:
    """Determine image_kind and format from src URL for consistent metadata.

    Args:
        src: Image source URL or path

    Returns:
        Dictionary with 'image_kind' and 'format' keys
    """
    # Determine image kind and parse data URIs
    if src.startswith("data:"):
        image_kind = "data"
        data_info = security_validators.parse_data_uri(src)
        # Extract format from mediatype (e.g., "image/png" → "png")
        mediatype = data_info.get("mediatype", "")
        format_type = mediatype.split("/")[1] if "/" in mediatype else "unknown"
    elif src.startswith(("http://", "https://")):
        image_kind = "external"
        # Extract format from extension for external URIs
        _, ext = os.path.splitext(src.lower())
        format_type = ext.lstrip(".") if ext else "unknown"
    else:
        image_kind = "local"
        # Extract format from extension for local paths
        _, ext = os.path.splitext(src.lower())
        format_type = ext.lstrip(".") if ext else "unknown"

    return {"image_kind": image_kind, "format": format_type}
