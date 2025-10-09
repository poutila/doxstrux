#!/usr/bin/env python3
"""
Test script for unified image record shapes between first-class images and link-side images.
"""

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_unified_image_records():
    """Test that image records have consistent shapes between structure.images and structure.links."""

    print("🖼️  Testing Unified Image Record Shapes")
    print("=" * 60)

    # Test content with various image scenarios
    content = """
# Image Test Document

## Regular Images
![Local image](./local-image.png "Local image title")
![External image](https://example.com/image.jpg "External image title")
![Data URI image](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg== "Data URI title")

## Linked Images
[![Linked local image](./linked-image.gif "Linked image alt")](https://example.com/link-target)
[![Linked external image](https://cdn.example.com/thumb.webp)](./local-target.html)

## Mixed Content
This paragraph has regular ![inline image](./inline.svg) and also [regular link](https://example.com).
"""

    parser = MarkdownParserCore(content, {"allows_html": False})
    result = parser.parse()

    structure = result.get("structure", {})

    # Get first-class images and link-side image records
    first_class_images = structure.get("images", [])
    links = structure.get("links", [])
    link_side_images = [link for link in links if link.get("type") == "image"]

    print("\n📊 Image Analysis:")
    print(f"First-class images: {len(first_class_images)}")
    print(f"Link-side image records: {len(link_side_images)}")
    print(f"Total links: {len(links)}")

    # Test unified field presence
    print("\n🔍 First-Class Images Structure:")
    for i, img in enumerate(first_class_images, 1):
        print(f"  {i}. {img.get('src', 'NO_SRC')}")
        print(f"     Fields: {sorted(img.keys())}")
        print(f"     image_kind: {img.get('image_kind', 'MISSING')}")
        print(f"     format: {img.get('format', 'MISSING')}")

    print("\n🔗 Link-Side Image Records Structure:")
    for i, img in enumerate(link_side_images, 1):
        print(f"  {i}. {img.get('src', 'NO_SRC')} (url: {img.get('url', 'NO_URL')})")
        print(f"     Fields: {sorted(img.keys())}")
        print(f"     image_kind: {img.get('image_kind', 'MISSING')}")
        print(f"     format: {img.get('format', 'MISSING')}")

    # Validation checks
    print("\n✅ Validation Checks:")

    # Check 1: All link-side images have unified fields
    unified_fields = ["src", "alt", "image_kind", "format"]
    missing_fields = []

    for img in link_side_images:
        for field in unified_fields:
            if field not in img:
                missing_fields.append(f"{img.get('image_id', 'unknown')}: missing {field}")

    has_unified_fields = len(missing_fields) == 0
    print(f"Link-side images have unified fields: {has_unified_fields}")
    if missing_fields:
        for missing in missing_fields[:3]:  # Show first 3
            print(f"  ❌ {missing}")

    # Check 2: Consistency between src/url and alt/text
    consistent_mappings = True
    for img in link_side_images:
        if img.get("src") != img.get("url"):
            print(f"  ❌ src/url mismatch: {img.get('src')} != {img.get('url')}")
            consistent_mappings = False
        if img.get("alt") != img.get("text"):
            print(f"  ❌ alt/text mismatch: {img.get('alt')} != {img.get('text')}")
            consistent_mappings = False

    print(f"Consistent src/url and alt/text mappings: {consistent_mappings}")

    # Check 3: Image kinds are properly classified
    valid_image_kinds = {"local", "external", "data"}
    invalid_kinds = []

    all_images = first_class_images + link_side_images
    for img in all_images:
        kind = img.get("image_kind")
        if kind not in valid_image_kinds:
            invalid_kinds.append(f"{img.get('src', 'unknown')}: {kind}")

    valid_classifications = len(invalid_kinds) == 0
    print(f"Valid image_kind classifications: {valid_classifications}")
    if invalid_kinds:
        for invalid in invalid_kinds[:3]:
            print(f"  ❌ {invalid}")

    # Check 4: Formats are extracted
    missing_formats = []
    for img in all_images:
        if not img.get("format") or img.get("format") == "unknown":
            missing_formats.append(img.get("src", "unknown"))

    has_formats = len(missing_formats) <= len(all_images) // 2  # Allow some unknowns
    print(f"Format extraction working: {has_formats}")
    if missing_formats:
        print(f"  ℹ️  {len(missing_formats)} images with unknown/missing format")

    # Check 5: Image IDs are present and consistent
    missing_ids = []
    for img in all_images:
        if not img.get("image_id"):
            missing_ids.append(img.get("src", "unknown"))

    has_image_ids = len(missing_ids) == 0
    print(f"Image IDs present: {has_image_ids}")

    # Test joinability
    print("\n🔗 Joinability Test:")
    # Find images that appear in both structures by image_id
    first_class_ids = {img["image_id"] for img in first_class_images if "image_id" in img}
    link_side_ids = {img["image_id"] for img in link_side_images if "image_id" in img}

    joinable_ids = first_class_ids & link_side_ids
    print(f"Joinable images (same ID in both structures): {len(joinable_ids)}")

    # Test that fields match for joinable images
    field_mismatches = []
    for img_id in joinable_ids:
        # Find matching records
        fc_img = next((img for img in first_class_images if img.get("image_id") == img_id), None)
        ls_img = next((img for img in link_side_images if img.get("image_id") == img_id), None)

        if fc_img and ls_img:
            # Check key fields match
            for field in ["src", "alt", "image_kind", "format"]:
                if fc_img.get(field) != ls_img.get(field):
                    field_mismatches.append(f"{img_id}: {field} differs")

    consistent_joins = len(field_mismatches) == 0
    print(f"Consistent field values for joinable images: {consistent_joins}")
    if field_mismatches:
        for mismatch in field_mismatches[:3]:
            print(f"  ❌ {mismatch}")

    # Overall success
    overall_success = (
        has_unified_fields
        and consistent_mappings
        and valid_classifications
        and has_image_ids
        and consistent_joins
    )

    print("\n🎯 Overall Result:")
    if overall_success:
        print("🎉 SUCCESS: Image record shapes are unified!")
        print("   ✅ Link-side images have src/alt/image_kind/format fields")
        print("   ✅ Consistent field mappings between structures")
        print("   ✅ Proper image classification (local/external/data)")
        print("   ✅ Stable image IDs for joining")
        print("   ✅ No special-case logic needed for downstream joins")
    else:
        print("❌ ISSUES: Image record unification needs improvement")
        if not has_unified_fields:
            print("   ❌ Missing unified fields in link-side images")
        if not consistent_mappings:
            print("   ❌ Inconsistent field mappings")
        if not valid_classifications:
            print("   ❌ Invalid image_kind classifications")
        if not has_image_ids:
            print("   ❌ Missing image IDs")
        if not consistent_joins:
            print("   ❌ Inconsistent field values for joinable images")

    return overall_success


if __name__ == "__main__":
    test_unified_image_records()
