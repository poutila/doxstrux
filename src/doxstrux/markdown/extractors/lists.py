"""List and tasklist extractors - Nested lists with checkbox detection.

This module extracts list structures from the markdown AST, including:
- Regular lists (bullet and ordered) with nested depth tracking
- Task lists (GFM extension) with checkbox state detection
- Recursive item extraction with depth limits (max 10 levels)

Functions:
    extract_lists: Extract regular lists (non-task lists)
    extract_tasklists: Extract GFM task lists with checkboxes
    detect_task_checkbox: Detect checkbox state from plugin HTML
    extract_list_items: Recursively extract regular list items
    extract_tasklist_items: Recursively extract task list items
"""

from typing import Any


def extract_lists(
    tree: Any,
    process_tree_func: Any,
    extract_list_items_func: Any,
    find_section_id_func: Any
) -> list[dict]:
    """Extract regular lists (excludes task lists - those are in extract_tasklists).

    Args:
        tree: The markdown AST tree
        process_tree_func: Function to process tree nodes
        extract_list_items_func: Function to recursively extract list items
        find_section_id_func: Function to find section ID for a line number

    Returns:
        List of regular list dicts with items and metadata
    """
    lists = []

    def list_processor(node, ctx, level):
        if node.type in ["bullet_list", "ordered_list"]:
            # Check if this is a task list (skip if it is)
            class_attr = ""
            if hasattr(node, 'attrs') and node.attrs:
                class_attr = node.attrs.get('class', '')

            if 'contains-task-list' in class_attr:
                # Skip task lists (handled by extract_tasklists)
                return True

            # Extract regular list structure
            items = extract_list_items_func(node)

            list_data = {
                "id": f"list_{len(ctx)}",
                "type": "bullet" if node.type == "bullet_list" else "ordered",
                "start_line": node.map[0] if node.map else None,
                "end_line": node.map[1] if node.map else None,
                "section_id": find_section_id_func(node.map[0] if node.map else 0),
                "items": items,
                "items_count": len(items),
            }

            ctx.append(list_data)
            return False  # Don't recurse, we handled the entire list

        return True

    process_tree_func(tree, list_processor, lists)
    return lists


def extract_tasklists(
    tree: Any,
    process_tree_func: Any,
    extract_tasklist_items_func: Any,
    find_section_id_func: Any
) -> list[dict]:
    """Extract GFM task lists with checkbox detection.

    Task lists are detected via the 'contains-task-list' class added by
    the tasklists plugin.

    Args:
        tree: The markdown AST tree
        process_tree_func: Function to process tree nodes
        extract_tasklist_items_func: Function to recursively extract task items
        find_section_id_func: Function to find section ID for a line number

    Returns:
        List of task list dicts with checkbox states
    """
    tasklists = []

    def tasklist_processor(node, ctx, level):
        if node.type in ["bullet_list", "ordered_list"]:
            # Check if this is a task list
            class_attr = ""
            if hasattr(node, 'attrs') and node.attrs:
                class_attr = node.attrs.get('class', '')

            if 'contains-task-list' not in class_attr:
                # Not a task list, skip
                return True

            # Extract task list structure with checkbox states
            items = extract_tasklist_items_func(node)

            # Calculate metrics
            items_count = len(items)
            checked_count = sum(1 for item in items if item.get("checked") is True)
            unchecked_count = sum(1 for item in items if item.get("checked") is False)
            has_mixed_task_items = any(item.get("checked") is None for item in items)

            tasklist_data = {
                "id": f"tasklist_{len(ctx)}",
                "type": "bullet" if node.type == "bullet_list" else "ordered",
                "start_line": node.map[0] if node.map else None,
                "end_line": node.map[1] if node.map else None,
                "section_id": find_section_id_func(node.map[0] if node.map else 0),
                "items": items,
                "items_count": items_count,
                "checked_count": checked_count,
                "unchecked_count": unchecked_count,
                "has_mixed_task_items": has_mixed_task_items,
            }

            ctx.append(tasklist_data)
            return False  # Don't recurse, we handled the entire list

        return True

    process_tree_func(tree, tasklist_processor, tasklists)
    return tasklists


def detect_task_checkbox(
    paragraph_node: Any,
    walk_tokens_iter_func: Any
) -> tuple[bool, bool]:
    """Detect checkbox state from tasklists plugin HTML injection.

    The tasklists plugin adds HTML inline tokens with checkbox markup:
    - <input class="task-list-item-checkbox" type="checkbox" checked="">
    - <input class="task-list-item-checkbox" type="checkbox">

    Args:
        paragraph_node: The paragraph node to check
        walk_tokens_iter_func: Function to walk token tree iteratively

    Returns:
        Tuple of (has_checkbox: bool, is_checked: bool)
    """
    if not hasattr(paragraph_node, "children"):
        return (False, False)

    # Walk inline tokens looking for checkbox HTML
    # Pass the node in a list to walk_tokens_iter
    for token in walk_tokens_iter_func([paragraph_node]):
        if token.type == "html_inline":
            content = getattr(token, "content", "")
            if "task-list-item-checkbox" in content:
                is_checked = 'checked="checked"' in content
                return (True, is_checked)

    return (False, False)


def extract_list_items(
    list_node: Any,
    get_text_func: Any,
    depth: int = 0,
    max_depth: int = 10
) -> list[dict]:
    """Recursively extract regular list items (no checkbox detection) with depth limit.

    Args:
        list_node: The list node to extract items from
        get_text_func: Function to extract text from node
        depth: Current recursion depth (default 0)
        max_depth: Maximum recursion depth to prevent stack overflow (default 10)

    Returns:
        List of item dicts with text, children, and blocks
    """
    # Safety: Prevent stack overflow from deeply nested lists
    if depth >= max_depth:
        return []

    items = []
    children = getattr(list_node, "children", [])

    for child in children:
        if child.type == "list_item":
            item = {"text": "", "children": [], "blocks": []}

            # Process list item children
            for item_child in getattr(child, "children", []):
                if item_child.type == "paragraph":
                    # Regular list item - just extract text (no checkbox detection)
                    text = get_text_func(item_child)
                    item["text"] = text

                elif item_child.type in ["bullet_list", "ordered_list"]:
                    # Nested list (recursive with depth tracking)
                    item["children"] = extract_list_items(
                        list_node=item_child,
                        get_text_func=get_text_func,
                        depth=depth + 1,
                        max_depth=max_depth
                    )

                elif item_child.type in ["fence", "code_block", "blockquote", "table"]:
                    # Block elements within list item
                    item["blocks"].append({
                        "type": item_child.type,
                        "start_line": item_child.map[0] if item_child.map else None,
                        "end_line": item_child.map[1] if item_child.map else None,
                    })

            items.append(item)

    return items


def extract_tasklist_items(
    list_node: Any,
    get_text_func: Any,
    detect_task_checkbox_func: Any,
    extract_list_items_func: Any,
    depth: int = 0,
    max_depth: int = 10
) -> list[dict]:
    """Extract task list items WITH checkbox detection and depth limit.

    Args:
        list_node: The task list node to extract items from
        get_text_func: Function to extract text from node
        detect_task_checkbox_func: Function to detect checkbox state
        extract_list_items_func: Function to extract regular list items
        depth: Current recursion depth (default 0)
        max_depth: Maximum recursion depth to prevent stack overflow (default 10)

    Returns:
        List of task item dicts with checked status, or empty list if depth exceeded
    """
    # Safety: Prevent stack overflow from deeply nested lists
    if depth >= max_depth:
        return []

    items = []
    children = getattr(list_node, "children", [])

    for child in children:
        if child.type == "list_item":
            item = {"text": "", "checked": None, "children": [], "blocks": []}

            # Process list item children
            for item_child in getattr(child, "children", []):
                if item_child.type == "paragraph":
                    # Detect task checkbox (plugin already removed [ ] from text)
                    has_checkbox, is_checked = detect_task_checkbox_func(item_child)
                    text = get_text_func(item_child)

                    if has_checkbox:
                        item["checked"] = is_checked
                        item["text"] = text.strip()
                    else:
                        # Regular list item mixed in task list
                        item["text"] = text

                elif item_child.type in ["bullet_list", "ordered_list"]:
                    # Check if nested list is also a task list
                    nested_class = ""
                    if hasattr(item_child, 'attrs') and item_child.attrs:
                        nested_class = item_child.attrs.get('class', '')

                    if 'contains-task-list' in nested_class:
                        # Nested task list (recursive with depth tracking)
                        item["children"] = extract_tasklist_items(
                            list_node=item_child,
                            get_text_func=get_text_func,
                            detect_task_checkbox_func=detect_task_checkbox_func,
                            extract_list_items_func=extract_list_items_func,
                            depth=depth + 1,
                            max_depth=max_depth
                        )
                    else:
                        # Regular nested list inside task list item
                        # Extract as regular list
                        item["children"] = extract_list_items_func(
                            item_child,
                            depth=depth + 1,
                            max_depth=max_depth
                        )

                elif item_child.type in ["fence", "code_block", "blockquote", "table"]:
                    # Block elements within list item
                    item["blocks"].append({
                        "type": item_child.type,
                        "start_line": item_child.map[0] if item_child.map else None,
                        "end_line": item_child.map[1] if item_child.map else None,
                    })

            items.append(item)

    return items
