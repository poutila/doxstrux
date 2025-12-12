# PDF Scraping Pipeline Architecture

A complete pipeline: **PDF → Markdown → Parser → Chunker → Vector Embedding**

---

## Pipeline Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  PDF Extractor  │───▶│    Converter    │───▶│     Parser      │───▶│     Chunker     │───▶│    Embedder     │
│ PyMuPDF/Marker  │    │  (integrated)   │    │    doxstrux     │    │    doxstrux     │    │  OpenAI/etc     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │                      │                      │
        ▼                      ▼                      ▼                      ▼                      ▼
    Raw PDF              Markdown               Structured              Chunks               Vectors
    + metadata           (clean)                JSON output            + metadata            + metadata
```

---

## PDF Conversion Library Comparison

### Option 1: PyMuPDF4LLM (Recommended for Speed)

| Aspect | Details |
|--------|---------|
| **Speed** | ~0.1s per page (fast, no ML models) |
| **Accuracy** | Good for clean PDFs, struggles with complex layouts |
| **Dependencies** | Lightweight (~50MB) |
| **Tables** | Basic detection, may need post-processing |
| **Equations** | Limited LaTeX support |
| **License** | AGPL-3.0 (free for open source) |
| **Best for** | High-volume processing, simple documents |

### Option 2: Marker (Recommended for Accuracy)

| Aspect | Details |
|--------|---------|
| **Speed** | ~2.8s per page (GPU), slower on CPU |
| **Accuracy** | 95.7% baseline, 97%+ with LLM mode |
| **Dependencies** | Heavy (~2GB models, PyTorch, CUDA) |
| **Tables** | Excellent (0.907 accuracy with LLM) |
| **Equations** | Full LaTeX support, inline math |
| **License** | GPL-3.0 (commercial licensing available) |
| **Best for** | Complex documents, academic papers, accuracy-critical |

### Option 3: MarkItDown (Microsoft)

| Aspect | Details |
|--------|---------|
| **Speed** | Medium |
| **Accuracy** | Good for simple PDFs |
| **Dependencies** | Optional per-format (~200MB full) |
| **Tables** | Basic support |
| **Equations** | Limited |
| **License** | MIT |
| **Best for** | Multi-format pipelines (PDF + DOCX + PPTX) |

### Decision Matrix

| Use Case | Recommended Library |
|----------|---------------------|
| High-volume documentation | PyMuPDF4LLM |
| Academic papers with equations | Marker (with `--use_llm`) |
| Mixed document types | MarkItDown |
| Complex tables | Marker |
| Self-hosted, air-gapped | PyMuPDF4LLM |
| Maximum accuracy | Marker + LLM mode |

---

## 1. Stage 1: PDF Extraction

### 1.1 PyMuPDF4LLM Implementation

```python
from dataclasses import dataclass
from pathlib import Path
import pymupdf4llm
import fitz  # PyMuPDF

@dataclass
class ExtractedPDF:
    source_path: str
    markdown: str
    metadata: dict
    page_count: int
    images: list[dict]  # Extracted image info
    extraction_warnings: list[str]

class PyMuPDFExtractor:
    """Fast PDF extraction using PyMuPDF4LLM."""

    def __init__(
        self,
        extract_images: bool = True,
        image_path: str = "./images",
        dpi: int = 150,
        page_chunks: bool = False,
    ):
        self.extract_images = extract_images
        self.image_path = Path(image_path)
        self.dpi = dpi
        self.page_chunks = page_chunks

        if extract_images:
            self.image_path.mkdir(parents=True, exist_ok=True)

    def extract(self, pdf_path: str) -> ExtractedPDF:
        """Extract PDF to markdown."""
        warnings = []
        images = []

        # Open PDF for metadata
        doc = fitz.open(pdf_path)
        metadata = self._extract_metadata(doc)
        page_count = len(doc)
        doc.close()

        # Convert to markdown
        try:
            if self.page_chunks:
                # Get per-page markdown (useful for large docs)
                md_pages = pymupdf4llm.to_markdown(
                    pdf_path,
                    page_chunks=True,
                    write_images=self.extract_images,
                    image_path=str(self.image_path),
                    dpi=self.dpi,
                )
                markdown = "\n\n---\n\n".join(
                    page["text"] for page in md_pages
                )
            else:
                markdown = pymupdf4llm.to_markdown(
                    pdf_path,
                    write_images=self.extract_images,
                    image_path=str(self.image_path),
                    dpi=self.dpi,
                )
        except Exception as e:
            warnings.append(f"Extraction error: {e}")
            markdown = ""

        # Collect extracted images
        if self.extract_images:
            images = self._collect_images()

        # Post-process markdown
        markdown = self._clean_markdown(markdown, warnings)

        return ExtractedPDF(
            source_path=pdf_path,
            markdown=markdown,
            metadata=metadata,
            page_count=page_count,
            images=images,
            extraction_warnings=warnings,
        )

    def _extract_metadata(self, doc: fitz.Document) -> dict:
        """Extract PDF metadata."""
        meta = doc.metadata or {}
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "keywords": meta.get("keywords", ""),
            "creator": meta.get("creator", ""),
            "producer": meta.get("producer", ""),
            "creation_date": meta.get("creationDate", ""),
            "modification_date": meta.get("modDate", ""),
            "page_count": len(doc),
        }

    def _collect_images(self) -> list[dict]:
        """Collect info about extracted images."""
        images = []
        for img_path in self.image_path.glob("*.png"):
            images.append({
                "path": str(img_path),
                "filename": img_path.name,
            })
        return images

    def _clean_markdown(self, md: str, warnings: list[str]) -> str:
        """Clean up extracted markdown."""
        import re

        # Remove excessive blank lines
        md = re.sub(r'\n{4,}', '\n\n\n', md)

        # Fix broken tables (common issue)
        lines = md.split('\n')
        cleaned_lines = []
        in_table = False

        for line in lines:
            # Detect table start
            if '|' in line and not in_table:
                in_table = True
            elif in_table and '|' not in line and line.strip():
                in_table = False

            cleaned_lines.append(line)

        md = '\n'.join(cleaned_lines)

        # Warn about potential issues
        if md.count('```') % 2 != 0:
            warnings.append("Unbalanced code fences")

        table_count = md.count('\n|')
        if table_count > 0 and table_count < 3:
            warnings.append("Possible malformed table detected")

        return md.strip()
```

### 1.2 Marker Implementation (High Accuracy)

```python
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json
import tempfile

@dataclass
class MarkerExtractedPDF:
    source_path: str
    markdown: str
    metadata: dict
    page_count: int
    table_of_contents: list[dict]
    images: list[dict]
    extraction_warnings: list[str]

class MarkerExtractor:
    """High-accuracy PDF extraction using Marker."""

    def __init__(
        self,
        use_llm: bool = False,
        llm_provider: str = "openai",  # openai, anthropic, gemini
        output_format: str = "markdown",  # markdown, json, chunks
        force_ocr: bool = False,
        extract_images: bool = True,
    ):
        self.use_llm = use_llm
        self.llm_provider = llm_provider
        self.output_format = output_format
        self.force_ocr = force_ocr
        self.extract_images = extract_images

    def extract(self, pdf_path: str) -> MarkerExtractedPDF:
        """Extract PDF using Marker CLI."""
        warnings = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Build command
            cmd = [
                "marker_single",
                pdf_path,
                "--output_dir", str(output_dir),
                "--output_format", self.output_format,
            ]

            if self.use_llm:
                cmd.extend(["--use_llm", "--llm_provider", self.llm_provider])

            if self.force_ocr:
                cmd.append("--force_ocr")

            # Run marker
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 min timeout
                )
                if result.returncode != 0:
                    warnings.append(f"Marker error: {result.stderr}")
            except subprocess.TimeoutExpired:
                warnings.append("Marker timeout (>5 min)")
                return self._empty_result(pdf_path, warnings)
            except FileNotFoundError:
                raise RuntimeError("Marker not installed. Run: pip install marker-pdf")

            # Read output
            pdf_name = Path(pdf_path).stem
            md_path = output_dir / pdf_name / f"{pdf_name}.md"
            meta_path = output_dir / pdf_name / "metadata.json"

            markdown = ""
            metadata = {}
            toc = []
            images = []

            if md_path.exists():
                markdown = md_path.read_text()

            if meta_path.exists():
                meta_data = json.loads(meta_path.read_text())
                metadata = meta_data.get("metadata", {})
                toc = meta_data.get("table_of_contents", [])

            # Collect images
            images_dir = output_dir / pdf_name / "images"
            if images_dir.exists():
                for img_path in images_dir.glob("*"):
                    images.append({
                        "path": str(img_path),
                        "filename": img_path.name,
                    })

            return MarkerExtractedPDF(
                source_path=pdf_path,
                markdown=markdown,
                metadata=metadata,
                page_count=metadata.get("page_count", 0),
                table_of_contents=toc,
                images=images,
                extraction_warnings=warnings,
            )

    def _empty_result(self, pdf_path: str, warnings: list[str]) -> MarkerExtractedPDF:
        return MarkerExtractedPDF(
            source_path=pdf_path,
            markdown="",
            metadata={},
            page_count=0,
            table_of_contents=[],
            images=[],
            extraction_warnings=warnings,
        )


class MarkerAPIExtractor:
    """Use Marker's Python API directly (no subprocess)."""

    def __init__(
        self,
        use_llm: bool = False,
        llm_service: str = "marker.services.claude.ClaudeService",
    ):
        self.use_llm = use_llm
        self.llm_service = llm_service

    def extract(self, pdf_path: str) -> MarkerExtractedPDF:
        """Extract using Marker's Python API."""
        from marker.converters.pdf import PdfConverter
        from marker.config.parser import ConfigParser
        from marker.output import text_from_rendered

        # Configure
        config = {
            "output_format": "markdown",
            "use_llm": self.use_llm,
        }

        if self.use_llm:
            config["llm_service"] = self.llm_service

        config_parser = ConfigParser(config)
        converter = PdfConverter(config=config_parser.generate_config_dict())

        # Convert
        rendered = converter(pdf_path)
        markdown, images, metadata = text_from_rendered(rendered)

        return MarkerExtractedPDF(
            source_path=pdf_path,
            markdown=markdown,
            metadata=metadata,
            page_count=metadata.get("page_count", 0),
            table_of_contents=metadata.get("table_of_contents", []),
            images=images,
            extraction_warnings=[],
        )
```

### 1.3 MarkItDown Implementation (Multi-format)

```python
from dataclasses import dataclass
from markitdown import MarkItDown

@dataclass
class MarkItDownExtracted:
    source_path: str
    markdown: str
    metadata: dict
    extraction_warnings: list[str]

class MarkItDownExtractor:
    """Multi-format extraction using Microsoft MarkItDown."""

    def __init__(
        self,
        enable_plugins: bool = False,
        use_docintel: bool = False,  # Azure Document Intelligence
        docintel_endpoint: str = None,
    ):
        kwargs = {"enable_plugins": enable_plugins}

        if use_docintel and docintel_endpoint:
            from markitdown import DocumentIntelligenceConverter
            kwargs["document_intelligence_endpoint"] = docintel_endpoint

        self.converter = MarkItDown(**kwargs)

    def extract(self, file_path: str) -> MarkItDownExtracted:
        """Extract any supported format to markdown."""
        warnings = []

        try:
            result = self.converter.convert(file_path)
            markdown = result.text_content
            metadata = {
                "title": getattr(result, "title", ""),
            }
        except Exception as e:
            warnings.append(f"Extraction error: {e}")
            markdown = ""
            metadata = {}

        return MarkItDownExtracted(
            source_path=file_path,
            markdown=markdown,
            metadata=metadata,
            extraction_warnings=warnings,
        )

    def extract_batch(self, file_paths: list[str]) -> list[MarkItDownExtracted]:
        """Extract multiple files."""
        return [self.extract(path) for path in file_paths]
```

---

## 2. Stage 2: Markdown Enhancement

PDF-extracted markdown often needs cleanup before parsing:

```python
import re
from dataclasses import dataclass

@dataclass
class EnhancedMarkdown:
    markdown: str
    metadata: dict
    enhancements_applied: list[str]

class MarkdownEnhancer:
    """Clean and enhance PDF-extracted markdown."""

    def enhance(
        self,
        extracted: ExtractedPDF | MarkerExtractedPDF,
    ) -> EnhancedMarkdown:
        """Apply enhancements to extracted markdown."""
        md = extracted.markdown
        enhancements = []

        # Add frontmatter from PDF metadata
        md = self._add_frontmatter(md, extracted.metadata)
        enhancements.append("frontmatter_added")

        # Fix common PDF extraction artifacts
        md = self._fix_hyphenation(md)
        enhancements.append("hyphenation_fixed")

        md = self._fix_ligatures(md)
        enhancements.append("ligatures_fixed")

        md = self._fix_whitespace(md)
        enhancements.append("whitespace_normalized")

        # Fix table formatting
        md = self._fix_tables(md)
        enhancements.append("tables_fixed")

        # Fix code blocks
        md = self._fix_code_blocks(md)
        enhancements.append("code_blocks_fixed")

        return EnhancedMarkdown(
            markdown=md,
            metadata=extracted.metadata,
            enhancements_applied=enhancements,
        )

    def _add_frontmatter(self, md: str, metadata: dict) -> str:
        """Add YAML frontmatter from PDF metadata."""
        import yaml

        frontmatter_fields = ["title", "author", "subject", "keywords"]
        fm = {k: v for k, v in metadata.items() if k in frontmatter_fields and v}

        if not fm:
            return md

        frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
        return f"---\n{frontmatter}---\n\n{md}"

    def _fix_hyphenation(self, md: str) -> str:
        """Fix words split across lines with hyphens."""
        # Pattern: word- \n continuation
        # This is tricky - we don't want to break intentional hyphens
        # Only fix obvious cases: lowercase-\n lowercase
        pattern = r'([a-z])-\s*\n\s*([a-z])'
        return re.sub(pattern, r'\1\2', md)

    def _fix_ligatures(self, md: str) -> str:
        """Replace PDF ligatures with standard characters."""
        ligatures = {
            'ﬁ': 'fi',
            'ﬂ': 'fl',
            'ﬀ': 'ff',
            'ﬃ': 'ffi',
            'ﬄ': 'ffl',
            '—': '--',  # em dash
            '–': '-',   # en dash
            ''': "'",
            ''': "'",
            '"': '"',
            '"': '"',
            '…': '...',
        }
        for ligature, replacement in ligatures.items():
            md = md.replace(ligature, replacement)
        return md

    def _fix_whitespace(self, md: str) -> str:
        """Normalize whitespace issues."""
        # Multiple spaces to single
        md = re.sub(r' {2,}', ' ', md)

        # Multiple blank lines to double
        md = re.sub(r'\n{4,}', '\n\n\n', md)

        # Remove trailing whitespace
        md = '\n'.join(line.rstrip() for line in md.split('\n'))

        return md

    def _fix_tables(self, md: str) -> str:
        """Fix common table formatting issues."""
        lines = md.split('\n')
        fixed_lines = []
        in_table = False
        table_lines = []

        for line in lines:
            if '|' in line:
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(line)
            else:
                if in_table:
                    # Process collected table
                    fixed_table = self._process_table(table_lines)
                    fixed_lines.extend(fixed_table)
                    in_table = False
                    table_lines = []
                fixed_lines.append(line)

        # Handle table at end of document
        if in_table and table_lines:
            fixed_table = self._process_table(table_lines)
            fixed_lines.extend(fixed_table)

        return '\n'.join(fixed_lines)

    def _process_table(self, table_lines: list[str]) -> list[str]:
        """Fix a single table."""
        if len(table_lines) < 2:
            return table_lines

        # Ensure separator row exists
        has_separator = any(
            re.match(r'\|[\s\-:]+\|', line)
            for line in table_lines[:3]
        )

        if not has_separator and len(table_lines) >= 2:
            # Count columns from first row
            col_count = table_lines[0].count('|') - 1
            separator = '|' + '---|' * col_count
            table_lines.insert(1, separator)

        return table_lines

    def _fix_code_blocks(self, md: str) -> str:
        """Fix code block issues."""
        # Balance code fences
        fence_count = md.count('```')
        if fence_count % 2 != 0:
            # Try to find unclosed fence and close it
            md = md + '\n```'

        return md
```

---

## 3. Stage 3: Parser (Doxstrux)

Same as HTML pipeline - parse with strict security:

```python
from doxstrux import parse_markdown_file
from doxstrux.markdown_parser_core import MarkdownParserCore
import tempfile
import os

def parse_pdf_markdown(
    enhanced: EnhancedMarkdown,
    source_path: str,
) -> dict:
    """Parse PDF-extracted markdown with doxstrux."""

    # Write to temp file (full API)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(enhanced.markdown)
        temp_path = f.name

    try:
        # Always use strict for external content
        result = parse_markdown_file(temp_path, security_profile="strict")

        # Add PDF metadata
        result["metadata"]["pdf"] = {
            "source_path": source_path,
            "title": enhanced.metadata.get("title", ""),
            "author": enhanced.metadata.get("author", ""),
            "page_count": enhanced.metadata.get("page_count", 0),
        }

        # Check security
        if result["metadata"].get("embedding_blocked"):
            raise SecurityError(
                f"Content blocked: {result['metadata'].get('embedding_block_reason')}"
            )

        return result

    finally:
        os.unlink(temp_path)
```

---

## 4. Stage 4: Chunker (Doxstrux)

PDF documents often have special chunking needs:

```python
from doxstrux.chunker import chunk_document, ChunkPolicy

def chunk_pdf_document(
    parsed: dict,
    target_tokens: int = 500,
    max_tokens: int = 1000,
    respect_pages: bool = False,  # Chunk within page boundaries
) -> list[dict]:
    """Chunk PDF document for embedding."""

    # PDFs often have denser content - adjust tokens
    policy = ChunkPolicy(
        mode="semantic",
        target_tokens=target_tokens,
        max_chunk_tokens=max_tokens,
        overlap_tokens=75,  # More overlap for PDFs (context loss)
        respect_boundaries=True,
        include_code=True,
        include_tables=True,
    )

    result = chunk_document(parsed, policy)

    chunks = result.chunks

    # Add PDF-specific metadata
    for chunk in chunks:
        chunk.meta["source_type"] = "pdf"
        chunk.meta["pdf_title"] = parsed["metadata"]["pdf"].get("title", "")
        chunk.meta["pdf_author"] = parsed["metadata"]["pdf"].get("author", "")

    return chunks
```

### 4.1 Page-Aware Chunking

For PDFs where page boundaries matter (legal documents, academic papers):

```python
def chunk_pdf_by_page(
    extracted: ExtractedPDF,
    target_tokens: int = 500,
) -> list[dict]:
    """Chunk PDF maintaining page awareness."""

    # Extract with page chunks enabled
    extractor = PyMuPDFExtractor(page_chunks=True)

    # Process each page separately
    all_chunks = []

    md_pages = pymupdf4llm.to_markdown(
        extracted.source_path,
        page_chunks=True,
    )

    for page_num, page_data in enumerate(md_pages, 1):
        page_md = page_data["text"]

        # Parse page
        parser = MarkdownParserCore(page_md, security_profile="strict")
        page_parsed = parser.parse()

        # Chunk page
        policy = ChunkPolicy(
            mode="semantic",
            target_tokens=target_tokens,
            max_chunk_tokens=target_tokens * 2,
        )
        page_chunks = chunk_document(page_parsed, policy).chunks

        # Add page number
        for chunk in page_chunks:
            chunk.meta["page_number"] = page_num
            all_chunks.append(chunk)

    return all_chunks
```

---

## 5. Stage 5: Vector Embedding

Same as HTML pipeline, with PDF-specific metadata:

```python
from dataclasses import dataclass

@dataclass
class PDFEmbeddingChunk:
    """Chunk prepared for embedding from PDF."""
    chunk_id: str
    text: str
    source_path: str           # Original PDF path
    pdf_title: str
    pdf_author: str
    page_number: int | None
    section_path: list[str]
    section_title: str
    char_span: tuple[int, int]
    token_estimate: int
    risk_flags: list[str]
    has_code: bool
    has_table: bool
    has_equation: bool         # PDF-specific

def prepare_pdf_chunks_for_embedding(
    chunks: list,
    parsed: dict,
) -> list[PDFEmbeddingChunk]:
    """Convert PDF chunks to embedding-ready format."""
    pdf_meta = parsed["metadata"].get("pdf", {})

    embedding_chunks = []
    for chunk in chunks:
        ec = PDFEmbeddingChunk(
            chunk_id=chunk.chunk_id,
            text=chunk.normalized_text,
            source_path=pdf_meta.get("source_path", ""),
            pdf_title=pdf_meta.get("title", ""),
            pdf_author=pdf_meta.get("author", ""),
            page_number=chunk.meta.get("page_number"),
            section_path=chunk.section_path,
            section_title=chunk.meta.get("title", ""),
            char_span=chunk.span,
            token_estimate=chunk.token_estimate,
            risk_flags=chunk.risk_flags,
            has_code=chunk.meta.get("has_code", False),
            has_table=chunk.meta.get("has_table", False),
            has_equation="$" in chunk.text or "\\(" in chunk.text,
        )
        embedding_chunks.append(ec)

    return embedding_chunks
```

---

## 6. Complete PDF Pipeline

```python
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class PDFPipelineConfig:
    # Extractor
    extractor: str = "pymupdf"  # pymupdf, marker, markitdown
    use_llm: bool = False       # For marker
    extract_images: bool = True
    image_dpi: int = 150

    # Parser
    security_profile: str = "strict"

    # Chunker
    target_tokens: int = 500
    max_tokens: int = 1000
    chunk_mode: str = "semantic"
    page_aware: bool = False

    # Embedder
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 100

    # Storage
    collection_name: str = "pdf_documents"
    persist_dir: str = "./vector_db"


class PDFPipeline:
    """Complete PDF to vector embedding pipeline."""

    def __init__(self, config: PDFPipelineConfig):
        self.config = config

        # Initialize extractor
        if config.extractor == "pymupdf":
            self.extractor = PyMuPDFExtractor(
                extract_images=config.extract_images,
                dpi=config.image_dpi,
            )
        elif config.extractor == "marker":
            self.extractor = MarkerExtractor(
                use_llm=config.use_llm,
                extract_images=config.extract_images,
            )
        elif config.extractor == "markitdown":
            self.extractor = MarkItDownExtractor()
        else:
            raise ValueError(f"Unknown extractor: {config.extractor}")

        self.enhancer = MarkdownEnhancer()
        self.embedder = OpenAIEmbedder(config.embedding_model)
        self.store = VectorStore(
            collection_name=config.collection_name,
            persist_dir=config.persist_dir,
        )

    def process_pdf(self, pdf_path: str) -> dict:
        """Process a single PDF through the pipeline."""
        stats = {
            "path": pdf_path,
            "success": False,
            "chunks_created": 0,
            "page_count": 0,
            "errors": [],
            "warnings": [],
        }

        try:
            # Stage 1: Extract
            logger.info(f"Extracting {pdf_path}")
            extracted = self.extractor.extract(pdf_path)
            stats["page_count"] = extracted.page_count
            stats["warnings"].extend(extracted.extraction_warnings)

            if not extracted.markdown:
                stats["errors"].append("No content extracted")
                return stats

            # Stage 2: Enhance
            logger.info("Enhancing markdown")
            enhanced = self.enhancer.enhance(extracted)

            # Stage 3: Parse
            logger.info("Parsing with doxstrux")
            parsed = parse_pdf_markdown(enhanced, pdf_path)

            # Check security
            if parsed["metadata"].get("embedding_blocked"):
                raise SecurityError(
                    f"Content blocked: {parsed['metadata'].get('embedding_block_reason')}"
                )

            if parsed["metadata"].get("quarantined"):
                stats["warnings"].append(
                    f"Quarantined: {parsed['metadata'].get('quarantine_reasons')}"
                )

            # Stage 4: Chunk
            logger.info("Chunking document")
            if self.config.page_aware:
                chunks = chunk_pdf_by_page(extracted, self.config.target_tokens)
            else:
                chunks = chunk_pdf_document(
                    parsed,
                    self.config.target_tokens,
                    self.config.max_tokens,
                )

            if not chunks:
                stats["warnings"].append("No chunks created")
                return stats

            # Prepare for embedding
            embedding_chunks = prepare_pdf_chunks_for_embedding(chunks, parsed)

            # Stage 5: Embed
            logger.info(f"Embedding {len(embedding_chunks)} chunks")
            embedded = embed_chunks(
                embedding_chunks,
                self.embedder,
                self.config.embedding_model,
                self.config.embedding_batch_size,
            )

            # Stage 6: Store
            logger.info("Storing in vector database")
            self.store.add_pdf_chunks(embedded)

            stats["success"] = True
            stats["chunks_created"] = len(embedded)

        except Exception as e:
            logger.error(f"Pipeline failed for {pdf_path}: {e}")
            stats["errors"].append(str(e))

        return stats

    def process_directory(
        self,
        directory: str,
        pattern: str = "*.pdf",
        recursive: bool = True,
    ) -> list[dict]:
        """Process all PDFs in a directory."""
        from tqdm import tqdm

        path = Path(directory)
        if recursive:
            pdf_files = list(path.rglob(pattern))
        else:
            pdf_files = list(path.glob(pattern))

        logger.info(f"Found {len(pdf_files)} PDF files")

        results = []
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            result = self.process_pdf(str(pdf_path))
            results.append(result)

        return results
```

---

## 7. Specialized PDF Handling

### 7.1 Academic Papers

```python
class AcademicPaperPipeline(PDFPipeline):
    """Specialized pipeline for academic papers."""

    def __init__(self, config: PDFPipelineConfig):
        # Force Marker with LLM for best equation handling
        config.extractor = "marker"
        config.use_llm = True
        super().__init__(config)

    def process_pdf(self, pdf_path: str) -> dict:
        result = super().process_pdf(pdf_path)

        # Extract additional academic metadata
        if result["success"]:
            self._extract_references(pdf_path)
            self._extract_abstract(pdf_path)

        return result

    def _extract_abstract(self, pdf_path: str):
        """Extract abstract section separately."""
        # Parse and find abstract section
        pass

    def _extract_references(self, pdf_path: str):
        """Extract references/bibliography."""
        # Parse and find references section
        pass
```

### 7.2 Legal Documents

```python
class LegalDocumentPipeline(PDFPipeline):
    """Specialized pipeline for legal documents."""

    def __init__(self, config: PDFPipelineConfig):
        # Enable page-aware chunking for citations
        config.page_aware = True
        # Smaller chunks for precision
        config.target_tokens = 300
        config.max_tokens = 500
        super().__init__(config)

    def _chunk_with_paragraph_numbers(self, parsed: dict) -> list:
        """Preserve paragraph numbering for legal citations."""
        # Legal docs often have numbered paragraphs
        # Ensure chunk boundaries respect these
        pass
```

### 7.3 Technical Manuals

```python
class TechnicalManualPipeline(PDFPipeline):
    """Specialized pipeline for technical documentation."""

    def __init__(self, config: PDFPipelineConfig):
        # Use PyMuPDF for speed (simpler formatting)
        config.extractor = "pymupdf"
        # Larger chunks for procedures
        config.target_tokens = 600
        super().__init__(config)

    def _enhance_code_blocks(self, markdown: str) -> str:
        """Detect and enhance code/command blocks."""
        # Technical docs have CLI commands, configs, etc.
        pass
```

---

## 8. Error Handling

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientPDFPipeline(PDFPipeline):
    """Pipeline with retry logic."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def _extract_with_retry(self, pdf_path: str):
        return self.extractor.extract(pdf_path)

    def process_pdf(self, pdf_path: str) -> dict:
        try:
            extracted = self._extract_with_retry(pdf_path)
            # ... rest of pipeline
        except Exception as e:
            # Fallback to simpler extractor
            logger.warning(f"Primary extractor failed, trying fallback: {e}")
            fallback = PyMuPDFExtractor()
            extracted = fallback.extract(pdf_path)
            # ... continue
```

---

## 9. Performance Considerations

### 9.1 Batch Processing

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

def process_pdfs_parallel(
    pdf_paths: list[str],
    config: PDFPipelineConfig,
    max_workers: int = 4,
) -> list[dict]:
    """Process PDFs in parallel."""

    def process_single(pdf_path: str) -> dict:
        pipeline = PDFPipeline(config)
        return pipeline.process_pdf(pdf_path)

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single, path): path
            for path in pdf_paths
        }

        for future in tqdm(as_completed(futures), total=len(futures)):
            pdf_path = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "path": pdf_path,
                    "success": False,
                    "errors": [str(e)],
                })

    return results
```

### 9.2 Memory Management

```python
def process_large_pdf(
    pdf_path: str,
    config: PDFPipelineConfig,
    max_pages_per_batch: int = 50,
) -> dict:
    """Process large PDFs in batches to manage memory."""
    import fitz

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    if total_pages <= max_pages_per_batch:
        pipeline = PDFPipeline(config)
        return pipeline.process_pdf(pdf_path)

    # Process in page batches
    all_chunks = []
    for start_page in range(0, total_pages, max_pages_per_batch):
        end_page = min(start_page + max_pages_per_batch, total_pages)

        # Extract page range
        md = pymupdf4llm.to_markdown(
            pdf_path,
            pages=list(range(start_page, end_page)),
        )

        # Process batch
        # ... parse, chunk, embed

        # Clear memory
        import gc
        gc.collect()

    return {"chunks_created": len(all_chunks), "success": True}
```

---

## 10. Summary

### Pipeline Flow

```
PDF File
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ EXTRACTOR (PyMuPDF4LLM / Marker / MarkItDown)                   │
│ - OCR if needed                                                 │
│ - Extract text, tables, images                                  │
│ - Convert to Markdown                                           │
│ - Extract PDF metadata (title, author, pages)                   │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ ENHANCER                                                        │
│ - Fix hyphenation (word- breaks)                                │
│ - Replace ligatures (ﬁ → fi)                                    │
│ - Fix table formatting                                          │
│ - Add YAML frontmatter from metadata                            │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ PARSER (doxstrux)                                               │
│ - security_profile="strict" (always for PDFs)                   │
│ - Extract sections, paragraphs, code blocks                     │
│ - Security validation                                           │
│ - Rich metadata (line spans, word counts, hierarchy)            │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHUNKER (doxstrux)                                              │
│ - Semantic chunking respecting section boundaries               │
│ - Optional: page-aware chunking for legal/academic              │
│ - Higher overlap (75 tokens) for PDF context loss               │
│ - Metadata: section_path, page_number, char_span                │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ EMBEDDER (OpenAI / Local)                                       │
│ - Batch embedding                                               │
│ - PDF-specific metadata (title, author, page)                   │
│ - Deduplication via embedding hash                              │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ VECTOR STORE                                                    │
│ - Store with rich metadata                                      │
│ - Enable filtering by PDF, page, section                        │
│ - Support citation retrieval (page numbers)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Differences from HTML Pipeline

| Aspect | HTML Pipeline | PDF Pipeline |
|--------|---------------|--------------|
| **Extraction** | BeautifulSoup (simple) | PyMuPDF/Marker (complex) |
| **Artifacts** | Nav, footer, ads | Hyphenation, ligatures, OCR errors |
| **Tables** | Clean HTML | Often malformed |
| **Equations** | Rare | Common (LaTeX) |
| **Page numbers** | N/A | Critical for citation |
| **Images** | URLs | Embedded, need extraction |
| **Chunk overlap** | 50 tokens | 75 tokens (more context loss) |

### Extractor Selection Guide

```
┌──────────────────────────────────────────────────────────────┐
│                    PDF Extractor Selection                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  High Volume?  ───Yes──▶  PyMuPDF4LLM (fast, lightweight)   │
│       │                                                      │
│      No                                                      │
│       │                                                      │
│       ▼                                                      │
│  Complex Layout? ─Yes─▶  Marker (accurate, GPU recommended) │
│       │                                                      │
│      No                                                      │
│       │                                                      │
│       ▼                                                      │
│  Multi-format?  ──Yes──▶  MarkItDown (PDF + DOCX + PPTX)   │
│       │                                                      │
│      No                                                      │
│       │                                                      │
│       ▼                                                      │
│  Equations?  ────Yes───▶  Marker + LLM mode                 │
│       │                                                      │
│      No                                                      │
│       │                                                      │
│       ▼                                                      │
│  Default: PyMuPDF4LLM                                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Sources

- [PyMuPDF4LLM Documentation](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
- [Marker GitHub](https://github.com/datalab-to/marker)
- [Microsoft MarkItDown](https://github.com/microsoft/markitdown)
- [Real Python - MarkItDown Guide](https://realpython.com/python-markitdown/)
