"""Doxstrux - Markdown parsing for RAG pipelines."""

from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.ir import DocumentIR, DocNode, ChunkPolicy, Chunk
from doxstrux.markdown.security.validators import PromptInjectionCheck

__all__ = [
    "MarkdownParserCore",
    "DocumentIR",
    "DocNode",
    "ChunkPolicy",
    "Chunk",
    "PromptInjectionCheck",
]
__version__ = "0.2.1"
