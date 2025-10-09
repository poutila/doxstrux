"""
Content Context Mapping for Markdown Parser

This module provides context awareness for markdown parsing,
ensuring that markdown elements inside code blocks are not
processed as actual markdown.
"""

import re


class ContentContext:
    """Maps document lines to their context (prose, code, etc.)"""

    def __init__(self, content: str):
        """Initialize with markdown content.

        Args:
            content: The markdown content to analyze
        """
        self.lines = content.split("\n")
        self.context_map = self._build_context_map()

    def _build_context_map(self) -> dict[int, str]:
        """Build line number -> context mapping.

        Returns:
            Dictionary mapping line numbers to context types:
            - 'prose': Regular markdown content
            - 'fenced_code': Inside ``` or ~~~ blocks
            - 'indented_code': Lines with 4+ spaces/tab indent
            - 'fence_marker': The ``` or ~~~ lines themselves
            - 'blank': Empty lines
        """
        context_map = {}
        in_fenced = False
        in_indented = False
        fence_lang = None
        fence_char = None
        fence_len = 0

        for i, line in enumerate(self.lines):
            # Detect fenced code blocks (robust: track fence char and length)
            m = re.match(r"^\s*([`~])\1{2,}(\s*\S.*)?\s*$", line)
            if m:
                ch = m.group(1)
                # count the opening fence run length after leading spaces
                run = re.match(r"^\s*([`~])\1{2,}", line).group(0).lstrip()
                run_len = len(run)
                if not in_fenced:
                    # opening fence
                    in_fenced = True
                    fence_char, fence_len = ch, run_len
                    fence_lang = (m.group(2) or "").strip() or None
                    context_map[i] = "fence_marker"
                    continue
                # closing fence: must match char and be >= opener length
                if ch == fence_char and run_len >= fence_len:
                    in_fenced = False
                    fence_char, fence_len = None, 0
                    fence_lang = None
                    context_map[i] = "fence_marker"
                    continue

            if in_fenced:
                context_map[i] = "fenced_code"
                continue

            # Handle blank lines (but tab/space-only lines in code blocks are part of the block)
            if line.strip() == "":
                # Check if it's a whitespace-only line in an indented block
                if in_indented and (line.startswith("    ") or line.startswith("\t")):
                    context_map[i] = "indented_code"
                    continue
                context_map[i] = "blank"
                # Blank line may end indented code block
                if in_indented:
                    # Check if next non-blank line is also indented
                    next_indented = False
                    for j in range(i + 1, len(self.lines)):
                        if self.lines[j].strip() != "":
                            if self.lines[j].startswith("    ") or self.lines[j].startswith("\t"):
                                next_indented = True
                            break
                    if not next_indented:
                        in_indented = False
                continue

            # Detect indented code blocks (4 spaces or tab)
            # Conservative rule: Must be preceded by a blank line or be at start of document
            # This avoids false positives from list continuations and nested content
            if (line.startswith("    ") or line.startswith("\t")) and not in_fenced:
                if not in_indented:
                    # Check if this starts an indented code block
                    # Require preceding blank line to avoid list-continuation false positives
                    if i == 0 or self.lines[i - 1].strip() == "":
                        in_indented = True

                if in_indented:
                    context_map[i] = "indented_code"
                else:
                    # Indented but not a code block (e.g., list continuation)
                    context_map[i] = "prose"
            else:
                # Non-indented, non-blank line
                if in_indented:
                    in_indented = False
                context_map[i] = "prose"

        return context_map

    def is_prose_line(self, line_number: int) -> bool:
        """Check if line is prose (not in code block).

        Args:
            line_number: Zero-based line number

        Returns:
            True if line is prose content, False otherwise
        """
        return self.context_map.get(line_number, "prose") == "prose"

    def is_code_line(self, line_number: int) -> bool:
        """Check if line is inside a code block.

        Args:
            line_number: Zero-based line number

        Returns:
            True if line is in fenced or indented code block
        """
        context = self.context_map.get(line_number, "prose")
        return context in ("fenced_code", "indented_code")

    def get_prose_lines(self) -> list[tuple[int, str]]:
        """Get all prose lines with their numbers.

        Returns:
            List of (line_number, line_content) tuples for prose lines
        """
        return [(i, line) for i, line in enumerate(self.lines) if self.is_prose_line(i)]

    def get_code_blocks(self) -> list[dict[str, any]]:
        """Get all code blocks with their content and type.

        Returns:
            List of dictionaries with code block information
        """
        blocks = []
        current_block = None

        for i, line in enumerate(self.lines):
            context = self.context_map.get(i, "prose")

            if context == "fence_marker" and not current_block:
                # Start of fenced block
                # Compute regex match once and reuse (micro-optimization for hot path)
                fence_match = re.match(r"^\s*([`~])\1{2,}(\s*\S.*)?\s*$", line)
                language = ""
                if fence_match and fence_match.group(2):
                    language = fence_match.group(2).strip()

                current_block = {
                    "type": "fenced",
                    "start_line": i,
                    "language": language,
                    "lines": [],
                }
            elif context == "fence_marker" and current_block and current_block["type"] == "fenced":
                # End of fenced block
                current_block["end_line"] = i
                current_block["content"] = "\n".join(current_block["lines"])
                blocks.append(current_block)
                current_block = None
            elif context == "fenced_code" and current_block:
                current_block["lines"].append(line)
            elif context == "indented_code":
                if not current_block or current_block["type"] != "indented":
                    # Start new indented block
                    if current_block:
                        # Save previous block
                        current_block["end_line"] = i - 1
                        current_block["content"] = "\n".join(current_block["lines"])
                        blocks.append(current_block)
                    current_block = {"type": "indented", "start_line": i, "lines": []}
                # Remove indentation from line
                if line.startswith("    "):
                    current_block["lines"].append(line[4:])
                elif line.startswith("\t"):
                    current_block["lines"].append(line[1:])
            elif current_block and current_block["type"] == "indented":
                # End indented block
                current_block["end_line"] = i - 1
                current_block["content"] = "\n".join(current_block["lines"])
                blocks.append(current_block)
                current_block = None

        # Handle block at end of file
        if current_block:
            current_block["end_line"] = len(self.lines) - 1
            current_block["content"] = "\n".join(current_block["lines"])
            blocks.append(current_block)

        return blocks

    def get_prose_content(self) -> str:
        """Get only the prose content as a single string.

        Returns:
            String containing only prose lines joined with newlines
        """
        prose_lines = [line for i, line in enumerate(self.lines) if self.is_prose_line(i)]
        return "\n".join(prose_lines)
