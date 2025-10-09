from src.docpipe import markdown_parser_core
from pathlib import Path

if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    file = base / "README.md"
    content = file.read_text()
    parser = markdown_parser_core.MarkdownParserCore(content)