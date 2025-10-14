"""Entry point for CLI tools when used as module.

Usage:
    python -m doxstrux.markdown.cli.dump_sections <file>
"""

from .dump_sections import main

if __name__ == "__main__":
    main()
