"""Doxstrux - Markdown parsing for RAG pipelines."""

from doxstrux.api import parse_markdown_file
from doxstrux.markdown.ir import DocumentIR, DocNode, ChunkPolicy, Chunk
from doxstrux.markdown.security.validators import PromptInjectionCheck
from doxstrux.rag_guard import DecisionSeverity, GuardDecision, guard_doxstrux_for_rag

__all__ = [
    "parse_markdown_file",
    "DocumentIR",
    "DocNode",
    "ChunkPolicy",
    "Chunk",
    "PromptInjectionCheck",
    "DecisionSeverity",
    "GuardDecision",
    "guard_doxstrux_for_rag",
]
__version__ = "0.2.1"
