"""
Doxstrux Markdown Package - Modular Architecture

Phase 7: Modularization of the markdown parser into focused modules.

This package contains the modular components of the markdown parser:
- core: Main parser orchestrator
- extractors: Feature-specific extraction modules
- security: Security validation and policies
- utils: Utility functions for tokens, lines, and text
- ir: Document intermediate representation
- exceptions: Error hierarchy
- config: Security profiles and patterns
- normalize: Text normalization
- serialize: Output serialization

All modules use absolute imports: from doxstrux.markdown.X import Y
"""

__version__ = "0.2.0"
