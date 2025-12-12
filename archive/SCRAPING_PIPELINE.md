# Scraping Pipeline Architecture

A complete pipeline: **HTML → Markdown → Parser → Chunker → Vector Embedding**

---

## Pipeline Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Scraper   │───▶│  Converter  │───▶│   Parser    │───▶│   Chunker   │───▶│  Embedder   │
│ BeautifulSoup│    │ html2text   │    │  doxstrux   │    │  doxstrux   │    │ OpenAI/etc  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼                  ▼
   Raw HTML          Markdown           Structured          Chunks           Vectors
   + metadata        (clean)            JSON output        + metadata        + metadata
```

---

## 1. Stage 1: Scraper (BeautifulSoup)

### 1.1 Responsibilities

- Fetch HTML from URLs
- Extract main content (remove nav, footer, ads)
- Preserve semantic HTML structure
- Extract metadata (title, author, date, etc.)
- Handle encoding detection
- Rate limiting and politeness

### 1.2 Implementation

```python
from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import time

@dataclass
class ScrapedPage:
    url: str
    title: str
    html_content: str  # Main content only
    metadata: dict     # title, author, date, description, etc.
    links: list[str]   # For crawling
    scraped_at: str    # ISO timestamp

class Scraper:
    def __init__(
        self,
        user_agent: str = "DoxstruxBot/1.0",
        rate_limit: float = 1.0,  # seconds between requests
        timeout: int = 30,
    ):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self.rate_limit = rate_limit
        self.timeout = timeout
        self._last_request = 0

    def scrape(self, url: str) -> ScrapedPage:
        """Scrape a single URL."""
        # Rate limiting
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        # Fetch
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        self._last_request = time.time()

        # Parse
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract metadata
        metadata = self._extract_metadata(soup, url)

        # Extract main content
        content = self._extract_content(soup)

        # Extract links for crawling
        links = self._extract_links(soup, url)

        return ScrapedPage(
            url=url,
            title=metadata.get("title", ""),
            html_content=str(content),
            metadata=metadata,
            links=links,
            scraped_at=datetime.utcnow().isoformat(),
        )

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        """Extract page metadata."""
        meta = {"url": url}

        # Title
        if soup.title:
            meta["title"] = soup.title.string

        # Meta tags
        for tag in soup.find_all("meta"):
            name = tag.get("name", tag.get("property", ""))
            content = tag.get("content", "")
            if name and content:
                if name in ("description", "author", "keywords"):
                    meta[name] = content
                elif name.startswith("og:"):
                    meta[name] = content
                elif name.startswith("article:"):
                    meta[name] = content

        # Structured data (JSON-LD)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get("@type") == "Article":
                        meta["structured_data"] = data
            except:
                pass

        return meta

    def _extract_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Extract main content, removing boilerplate."""
        # Remove unwanted elements
        for tag in soup.find_all([
            "nav", "footer", "header", "aside",
            "script", "style", "noscript",
            "iframe", "form", "button",
        ]):
            tag.decompose()

        # Remove by class/id patterns
        for pattern in ["nav", "footer", "sidebar", "menu", "ad", "cookie", "popup"]:
            for tag in soup.find_all(class_=lambda x: x and pattern in x.lower()):
                tag.decompose()
            for tag in soup.find_all(id=lambda x: x and pattern in x.lower()):
                tag.decompose()

        # Try to find main content
        main = (
            soup.find("main") or
            soup.find("article") or
            soup.find(role="main") or
            soup.find(class_="content") or
            soup.find(id="content") or
            soup.body or
            soup
        )

        return main

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract links for crawling."""
        from urllib.parse import urljoin

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("#"):
                continue
            full_url = urljoin(base_url, href)
            # Only same domain
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.append(full_url)

        return list(set(links))
```

### 1.3 Content Extraction Strategies

| Strategy | Use Case | Implementation |
|----------|----------|----------------|
| **Main content** | Articles, docs | Find `<main>`, `<article>`, or largest text block |
| **Full page** | Simple pages | Use entire `<body>` |
| **Readability** | News articles | Use `readability-lxml` library |
| **Custom selectors** | Known sites | Configure CSS selectors per domain |

```python
# Custom selectors per domain
DOMAIN_SELECTORS = {
    "docs.python.org": "div.body",
    "developer.mozilla.org": "article.main-page-content",
    "stackoverflow.com": "div.question, div.answer",
}

def _extract_content_custom(self, soup: BeautifulSoup, url: str) -> BeautifulSoup:
    """Use custom selectors if available."""
    domain = urlparse(url).netloc

    if domain in DOMAIN_SELECTORS:
        selector = DOMAIN_SELECTORS[domain]
        content = soup.select(selector)
        if content:
            # Wrap in div
            wrapper = soup.new_tag("div")
            for el in content:
                wrapper.append(el.extract())
            return wrapper

    return self._extract_content(soup)
```

---

## 2. Stage 2: HTML to Markdown Converter

### 2.1 Responsibilities

- Convert clean HTML to Markdown
- Preserve structure (headings, lists, tables, code)
- Handle images (extract URLs, alt text)
- Clean up whitespace
- Handle edge cases (nested lists, complex tables)

### 2.2 Library Options

| Library | Pros | Cons |
|---------|------|------|
| **html2text** | Simple, fast, well-maintained | Limited table support |
| **markdownify** | Good structure preservation | Slower |
| **trafilatura** | Built for web extraction | Opinionated output |
| **Custom** | Full control | Maintenance burden |

### 2.3 Implementation with html2text

```python
import html2text

@dataclass
class ConvertedDocument:
    markdown: str
    metadata: dict
    source_url: str
    conversion_warnings: list[str]

class HTMLToMarkdownConverter:
    def __init__(
        self,
        body_width: int = 0,  # No wrapping
        ignore_links: bool = False,
        ignore_images: bool = False,
        ignore_tables: bool = False,
        code_style: str = "fenced",
    ):
        self.converter = html2text.HTML2Text()
        self.converter.body_width = body_width
        self.converter.ignore_links = ignore_links
        self.converter.ignore_images = ignore_images
        self.converter.ignore_tables = ignore_tables

        # Enable features
        self.converter.mark_code = True
        self.converter.wrap_links = False
        self.converter.wrap_list_items = False

    def convert(self, scraped: ScrapedPage) -> ConvertedDocument:
        """Convert scraped HTML to Markdown."""
        warnings = []

        # Convert
        markdown = self.converter.handle(scraped.html_content)

        # Clean up
        markdown = self._clean_markdown(markdown, warnings)

        # Add frontmatter
        markdown = self._add_frontmatter(markdown, scraped.metadata)

        return ConvertedDocument(
            markdown=markdown,
            metadata=scraped.metadata,
            source_url=scraped.url,
            conversion_warnings=warnings,
        )

    def _clean_markdown(self, md: str, warnings: list[str]) -> str:
        """Clean up converted markdown."""
        import re

        # Remove excessive blank lines
        md = re.sub(r'\n{4,}', '\n\n\n', md)

        # Fix broken code blocks
        md = re.sub(r'```\s*\n\s*```', '', md)

        # Remove empty headings
        md = re.sub(r'^#+\s*$', '', md, flags=re.MULTILINE)

        # Warn about potential issues
        if md.count('```') % 2 != 0:
            warnings.append("Unbalanced code fences")
        if '|' in md and '\n|' not in md:
            warnings.append("Potential malformed table")

        return md.strip()

    def _add_frontmatter(self, md: str, metadata: dict) -> str:
        """Add YAML frontmatter from metadata."""
        import yaml

        frontmatter_fields = ["title", "author", "description", "url"]
        fm = {k: v for k, v in metadata.items() if k in frontmatter_fields and v}

        if not fm:
            return md

        frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
        return f"---\n{frontmatter}---\n\n{md}"
```

### 2.4 Handling Special Cases

```python
class EnhancedConverter(HTMLToMarkdownConverter):
    """Enhanced converter with special case handling."""

    def convert(self, scraped: ScrapedPage) -> ConvertedDocument:
        # Pre-process HTML
        soup = BeautifulSoup(scraped.html_content, "html.parser")

        # Handle syntax-highlighted code blocks
        self._normalize_code_blocks(soup)

        # Handle complex tables
        self._simplify_tables(soup)

        # Convert
        html = str(soup)
        scraped_modified = ScrapedPage(
            url=scraped.url,
            title=scraped.title,
            html_content=html,
            metadata=scraped.metadata,
            links=scraped.links,
            scraped_at=scraped.scraped_at,
        )

        return super().convert(scraped_modified)

    def _normalize_code_blocks(self, soup: BeautifulSoup):
        """Convert various code block formats to standard <pre><code>."""
        # Highlight.js
        for pre in soup.find_all("pre"):
            code = pre.find("code")
            if code:
                # Extract language from class
                classes = code.get("class", [])
                lang = None
                for cls in classes:
                    if cls.startswith("language-"):
                        lang = cls.replace("language-", "")
                        break
                    elif cls.startswith("hljs-"):
                        continue
                    elif cls in ["python", "javascript", "rust", "go", "java"]:
                        lang = cls
                        break

                if lang:
                    code["data-language"] = lang

        # Prism.js
        for pre in soup.find_all("pre", class_=lambda x: x and "language-" in str(x)):
            classes = pre.get("class", [])
            for cls in classes:
                if cls.startswith("language-"):
                    lang = cls.replace("language-", "")
                    code = pre.find("code") or pre
                    code["data-language"] = lang
                    break

    def _simplify_tables(self, soup: BeautifulSoup):
        """Simplify complex tables for better markdown conversion."""
        for table in soup.find_all("table"):
            # Remove colspan/rowspan (markdown doesn't support)
            for cell in table.find_all(["td", "th"]):
                cell.attrs.pop("colspan", None)
                cell.attrs.pop("rowspan", None)

            # Remove nested tables
            for nested in table.find_all("table"):
                nested.unwrap()
```

---

## 3. Stage 3: Parser (Doxstrux)

### 3.1 Integration

```python
from doxstrux import parse_markdown_file
from doxstrux.markdown_parser_core import MarkdownParserCore
import tempfile
import os

def parse_markdown_string(
    markdown: str,
    security_profile: str = "strict",
    source_url: str = "",
) -> dict:
    """Parse markdown string using doxstrux."""
    # Option 1: Write to temp file (uses full API)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(markdown)
        path = f.name

    try:
        result = parse_markdown_file(path, security_profile=security_profile)
        result["metadata"]["source_url"] = source_url
        return result
    finally:
        os.unlink(path)

    # Option 2: Direct parser (lower level)
    # parser = MarkdownParserCore(markdown, security_profile=security_profile)
    # return parser.parse()
```

### 3.2 Security Considerations for Scraped Content

**Always use `security_profile="strict"` for scraped content:**

```python
def parse_scraped_content(converted: ConvertedDocument) -> dict:
    """Parse with strict security for untrusted web content."""
    result = parse_markdown_string(
        converted.markdown,
        security_profile="strict",  # ALWAYS strict for web content
        source_url=converted.source_url,
    )

    # Additional checks for scraped content
    security = result["metadata"]["security"]

    # Check for issues
    if result["metadata"].get("embedding_blocked"):
        raise SecurityError(
            f"Content blocked: {result['metadata'].get('embedding_block_reason')}"
        )

    if result["metadata"].get("quarantined"):
        reasons = result["metadata"].get("quarantine_reasons", [])
        # Log but don't necessarily fail
        logger.warning(f"Quarantined content from {converted.source_url}: {reasons}")

    # Check for suspicious patterns in scraped content
    stats = security.get("statistics", {})
    if stats.get("prompt_injection_in_content"):
        raise SecurityError(f"Prompt injection detected in {converted.source_url}")

    return result
```

### 3.3 Metadata Enrichment

```python
def enrich_parsed_result(result: dict, scraped: ScrapedPage, converted: ConvertedDocument) -> dict:
    """Add scraping metadata to parsed result."""
    result["metadata"]["scraping"] = {
        "source_url": scraped.url,
        "scraped_at": scraped.scraped_at,
        "page_title": scraped.title,
        "conversion_warnings": converted.conversion_warnings,
    }

    # Merge page metadata
    if scraped.metadata:
        result["metadata"]["page"] = scraped.metadata

    return result
```

---

## 4. Stage 4: Chunker (Doxstrux)

### 4.1 Integration

```python
from doxstrux.chunker import chunk_document, ChunkPolicy

def chunk_for_embedding(
    parsed: dict,
    target_tokens: int = 500,
    max_tokens: int = 1000,
) -> list[dict]:
    """Chunk parsed document for embedding."""
    policy = ChunkPolicy(
        mode="semantic",
        target_tokens=target_tokens,
        max_chunk_tokens=max_tokens,
        overlap_tokens=50,
        respect_boundaries=True,
        include_code=True,
    )

    result = chunk_document(parsed, policy)

    return result.chunks
```

### 4.2 Chunk Metadata for Retrieval

Each chunk should carry enough metadata for retrieval and citation:

```python
@dataclass
class EmbeddingChunk:
    """Chunk prepared for embedding."""
    chunk_id: str
    text: str                    # For embedding
    source_url: str              # Original URL
    page_title: str              # Page title
    section_path: list[str]      # Section hierarchy
    section_title: str           # Current section title
    char_span: tuple[int, int]   # For highlighting
    line_span: tuple[int, int]   # For context
    token_estimate: int
    risk_flags: list[str]
    has_code: bool
    languages: list[str]         # Code languages if any

def prepare_chunks_for_embedding(
    chunks: list[Chunk],
    parsed: dict,
) -> list[EmbeddingChunk]:
    """Convert chunks to embedding-ready format."""
    source_url = parsed["metadata"].get("scraping", {}).get("source_url", "")
    page_title = parsed["metadata"].get("scraping", {}).get("page_title", "")

    embedding_chunks = []
    for chunk in chunks:
        ec = EmbeddingChunk(
            chunk_id=chunk.chunk_id,
            text=chunk.normalized_text,
            source_url=source_url,
            page_title=page_title,
            section_path=chunk.section_path,
            section_title=chunk.meta.get("title", ""),
            char_span=chunk.span,
            line_span=chunk.line_span,
            token_estimate=chunk.token_estimate,
            risk_flags=chunk.risk_flags,
            has_code=chunk.meta.get("has_code", False),
            languages=chunk.meta.get("languages", []),
        )
        embedding_chunks.append(ec)

    return embedding_chunks
```

---

## 5. Stage 5: Vector Embedding

### 5.1 Embedding Options

| Provider | Model | Dimensions | Use Case |
|----------|-------|------------|----------|
| OpenAI | text-embedding-3-small | 1536 | General purpose |
| OpenAI | text-embedding-3-large | 3072 | Higher quality |
| Cohere | embed-english-v3.0 | 1024 | English text |
| Voyage | voyage-2 | 1024 | Code-aware |
| Local | all-MiniLM-L6-v2 | 384 | Self-hosted |

### 5.2 Implementation

```python
from dataclasses import dataclass
from typing import Protocol
import hashlib

class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        ...

class OpenAIEmbedder:
    def __init__(self, model: str = "text-embedding-3-small"):
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]

class LocalEmbedder:
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

@dataclass
class EmbeddedChunk:
    """Chunk with embedding."""
    chunk: EmbeddingChunk
    embedding: list[float]
    embedding_model: str
    embedding_hash: str  # For deduplication

def embed_chunks(
    chunks: list[EmbeddingChunk],
    embedder: EmbeddingProvider,
    model_name: str,
    batch_size: int = 100,
) -> list[EmbeddedChunk]:
    """Embed chunks in batches."""
    embedded = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.text for c in batch]

        embeddings = embedder.embed(texts)

        for chunk, embedding in zip(batch, embeddings):
            # Compute embedding hash for deduplication
            embedding_bytes = str(embedding[:10]).encode()  # First 10 dims
            text_hash = hashlib.sha256(chunk.text.encode()).hexdigest()[:16]
            embedding_hash = f"{text_hash}_{hashlib.md5(embedding_bytes).hexdigest()[:8]}"

            embedded.append(EmbeddedChunk(
                chunk=chunk,
                embedding=embedding,
                embedding_model=model_name,
                embedding_hash=embedding_hash,
            ))

    return embedded
```

### 5.3 Code-Specific Embeddings

For technical documentation, consider using code-aware embeddings:

```python
class HybridEmbedder:
    """Use different models for code vs prose."""

    def __init__(
        self,
        prose_model: str = "text-embedding-3-small",
        code_model: str = "voyage-code-2",
    ):
        self.prose_embedder = OpenAIEmbedder(prose_model)
        self.code_embedder = VoyageEmbedder(code_model)  # Hypothetical

    def embed_chunks(self, chunks: list[EmbeddingChunk]) -> list[EmbeddedChunk]:
        """Route chunks to appropriate embedder."""
        prose_chunks = [c for c in chunks if not c.has_code]
        code_chunks = [c for c in chunks if c.has_code]

        embedded = []

        if prose_chunks:
            prose_texts = [c.text for c in prose_chunks]
            prose_embeddings = self.prose_embedder.embed(prose_texts)
            for chunk, emb in zip(prose_chunks, prose_embeddings):
                embedded.append(EmbeddedChunk(chunk=chunk, embedding=emb, ...))

        if code_chunks:
            code_texts = [c.text for c in code_chunks]
            code_embeddings = self.code_embedder.embed(code_texts)
            for chunk, emb in zip(code_chunks, code_embeddings):
                embedded.append(EmbeddedChunk(chunk=chunk, embedding=emb, ...))

        return embedded
```

---

## 6. Stage 6: Vector Storage

### 6.1 Storage Options

| Database | Type | Use Case |
|----------|------|----------|
| Pinecone | Managed | Production, serverless |
| Weaviate | Self-hosted | Full control |
| Qdrant | Self-hosted | High performance |
| Chroma | Local | Development, prototyping |
| pgvector | PostgreSQL | Existing Postgres |

### 6.2 Implementation (Chroma Example)

```python
import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, collection_name: str, persist_dir: str = "./chroma_db"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, embedded_chunks: list[EmbeddedChunk]):
        """Add embedded chunks to store."""
        ids = [ec.chunk.chunk_id for ec in embedded_chunks]
        embeddings = [ec.embedding for ec in embedded_chunks]
        documents = [ec.chunk.text for ec in embedded_chunks]
        metadatas = [
            {
                "source_url": ec.chunk.source_url,
                "page_title": ec.chunk.page_title,
                "section_title": ec.chunk.section_title,
                "section_path": "/".join(ec.chunk.section_path),
                "char_start": ec.chunk.char_span[0] if ec.chunk.char_span else None,
                "char_end": ec.chunk.char_span[1] if ec.chunk.char_span else None,
                "has_code": ec.chunk.has_code,
                "languages": ",".join(ec.chunk.languages),
                "risk_flags": ",".join(ec.chunk.risk_flags),
                "embedding_model": ec.embedding_model,
            }
            for ec in embedded_chunks
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        filter_dict: dict = None,
    ) -> list[dict]:
        """Search for similar chunks."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict,
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for i in range(len(results["ids"][0])):
            hits.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

        return hits
```

---

## 7. Complete Pipeline

### 7.1 Pipeline Class

```python
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    # Scraper
    user_agent: str = "DoxstruxBot/1.0"
    rate_limit: float = 1.0

    # Converter
    ignore_images: bool = False

    # Parser
    security_profile: str = "strict"

    # Chunker
    target_tokens: int = 500
    max_tokens: int = 1000
    chunk_mode: str = "semantic"

    # Embedder
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 100

    # Storage
    collection_name: str = "documents"
    persist_dir: str = "./vector_db"

class ScrapingPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.scraper = Scraper(
            user_agent=config.user_agent,
            rate_limit=config.rate_limit,
        )
        self.converter = HTMLToMarkdownConverter(
            ignore_images=config.ignore_images,
        )
        self.embedder = OpenAIEmbedder(config.embedding_model)
        self.store = VectorStore(
            collection_name=config.collection_name,
            persist_dir=config.persist_dir,
        )

    def process_url(self, url: str) -> dict:
        """Process a single URL through the entire pipeline."""
        stats = {
            "url": url,
            "success": False,
            "chunks_created": 0,
            "errors": [],
        }

        try:
            # Stage 1: Scrape
            logger.info(f"Scraping {url}")
            scraped = self.scraper.scrape(url)

            # Stage 2: Convert to Markdown
            logger.info(f"Converting to markdown")
            converted = self.converter.convert(scraped)
            if converted.conversion_warnings:
                stats["warnings"] = converted.conversion_warnings

            # Stage 3: Parse with doxstrux
            logger.info(f"Parsing markdown")
            parsed = parse_scraped_content(converted)
            parsed = enrich_parsed_result(parsed, scraped, converted)

            # Check security
            if parsed["metadata"].get("embedding_blocked"):
                raise SecurityError(
                    f"Content blocked: {parsed['metadata'].get('embedding_block_reason')}"
                )

            # Stage 4: Chunk
            logger.info(f"Chunking document")
            policy = ChunkPolicy(
                mode=self.config.chunk_mode,
                target_tokens=self.config.target_tokens,
                max_chunk_tokens=self.config.max_tokens,
            )
            chunk_result = chunk_document(parsed, policy)

            if not chunk_result.chunks:
                logger.warning(f"No chunks created for {url}")
                stats["errors"].append("No chunks created")
                return stats

            # Prepare for embedding
            embedding_chunks = prepare_chunks_for_embedding(
                chunk_result.chunks,
                parsed,
            )

            # Stage 5: Embed
            logger.info(f"Embedding {len(embedding_chunks)} chunks")
            embedded = embed_chunks(
                embedding_chunks,
                self.embedder,
                self.config.embedding_model,
                self.config.embedding_batch_size,
            )

            # Stage 6: Store
            logger.info(f"Storing in vector database")
            self.store.add(embedded)

            stats["success"] = True
            stats["chunks_created"] = len(embedded)

        except Exception as e:
            logger.error(f"Pipeline failed for {url}: {e}")
            stats["errors"].append(str(e))

        return stats

    def process_urls(self, urls: list[str]) -> list[dict]:
        """Process multiple URLs."""
        results = []
        for url in urls:
            result = self.process_url(url)
            results.append(result)
        return results

    def crawl_and_process(
        self,
        start_url: str,
        max_pages: int = 100,
        same_domain: bool = True,
    ) -> list[dict]:
        """Crawl from a starting URL and process all pages."""
        from collections import deque

        visited = set()
        queue = deque([start_url])
        results = []

        while queue and len(visited) < max_pages:
            url = queue.popleft()

            if url in visited:
                continue
            visited.add(url)

            # Process
            result = self.process_url(url)
            results.append(result)

            # Add new links to queue
            if result["success"]:
                # Get links from scraped page
                scraped = self.scraper.scrape(url)  # TODO: Cache
                for link in scraped.links:
                    if link not in visited:
                        queue.append(link)

        return results
```

### 7.2 Usage Example

```python
# Configuration
config = PipelineConfig(
    user_agent="MyBot/1.0 (contact@example.com)",
    rate_limit=2.0,  # Be polite
    security_profile="strict",
    target_tokens=500,
    embedding_model="text-embedding-3-small",
    collection_name="docs",
)

# Initialize pipeline
pipeline = ScrapingPipeline(config)

# Process single URL
result = pipeline.process_url("https://docs.example.com/intro")
print(f"Created {result['chunks_created']} chunks")

# Crawl entire site
results = pipeline.crawl_and_process(
    start_url="https://docs.example.com/",
    max_pages=500,
)

# Summary
success = sum(1 for r in results if r["success"])
total_chunks = sum(r["chunks_created"] for r in results)
print(f"Processed {success}/{len(results)} pages, {total_chunks} chunks")
```

---

## 8. Error Handling & Resilience

### 8.1 Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientPipeline(ScrapingPipeline):

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    def _scrape_with_retry(self, url: str) -> ScrapedPage:
        return self.scraper.scrape(url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def _embed_with_retry(
        self,
        chunks: list[EmbeddingChunk],
    ) -> list[EmbeddedChunk]:
        return embed_chunks(
            chunks,
            self.embedder,
            self.config.embedding_model,
            self.config.embedding_batch_size,
        )
```

### 8.2 Progress Tracking

```python
from tqdm import tqdm

def process_urls_with_progress(
    self,
    urls: list[str],
    checkpoint_file: str = "checkpoint.json",
) -> list[dict]:
    """Process URLs with progress tracking and checkpointing."""
    import json

    # Load checkpoint
    processed = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file) as f:
            checkpoint = json.load(f)
            processed = set(checkpoint.get("processed", []))

    results = []
    remaining = [u for u in urls if u not in processed]

    for url in tqdm(remaining, desc="Processing URLs"):
        result = self.process_url(url)
        results.append(result)

        # Update checkpoint
        processed.add(url)
        with open(checkpoint_file, "w") as f:
            json.dump({"processed": list(processed)}, f)

    return results
```

---

## 9. Monitoring & Observability

### 9.1 Metrics

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PipelineMetrics:
    started_at: datetime = field(default_factory=datetime.utcnow)
    urls_processed: int = 0
    urls_failed: int = 0
    chunks_created: int = 0
    tokens_embedded: int = 0
    errors: list[dict] = field(default_factory=list)

    def record_success(self, url: str, chunks: int, tokens: int):
        self.urls_processed += 1
        self.chunks_created += chunks
        self.tokens_embedded += tokens

    def record_failure(self, url: str, error: str):
        self.urls_failed += 1
        self.errors.append({
            "url": url,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def summary(self) -> dict:
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        return {
            "elapsed_seconds": elapsed,
            "urls_per_second": self.urls_processed / elapsed if elapsed > 0 else 0,
            "success_rate": self.urls_processed / (self.urls_processed + self.urls_failed)
                if (self.urls_processed + self.urls_failed) > 0 else 0,
            "total_chunks": self.chunks_created,
            "total_tokens": self.tokens_embedded,
            "errors": len(self.errors),
        }
```

---

## 10. Summary

### Pipeline Flow

```
URL
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ SCRAPER (BeautifulSoup)                                         │
│ - Fetch HTML                                                    │
│ - Extract main content (remove nav, footer, ads)                │
│ - Extract metadata (title, author, structured data)             │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ CONVERTER (html2text)                                           │
│ - HTML → Markdown                                               │
│ - Preserve structure (headings, lists, tables, code)            │
│ - Add YAML frontmatter from metadata                            │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ PARSER (doxstrux)                                               │
│ - security_profile="strict" (always for web content)            │
│ - Extract sections, paragraphs, code blocks                     │
│ - Security validation (prompt injection, blocked schemes)       │
│ - Rich metadata (line spans, word counts, hierarchy)            │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHUNKER (doxstrux)                                              │
│ - Semantic chunking respecting section boundaries               │
│ - Token estimation (no tiktoken needed)                         │
│ - Overlap for context                                           │
│ - Metadata: section_path, char_span, risk_flags                 │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ EMBEDDER (OpenAI / Local)                                       │
│ - Batch embedding                                               │
│ - Optional: different models for code vs prose                  │
│ - Deduplication via embedding hash                              │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ VECTOR STORE (Chroma / Pinecone / etc)                          │
│ - Store embeddings with rich metadata                           │
│ - Enable filtered search (by source, by section, by code)       │
│ - Support for retrieval expansion (link graph)                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Always `strict` profile** for scraped content
2. **Semantic chunking** respects section boundaries (never mid-paragraph)
3. **Rich metadata** propagates through entire pipeline (source URL, section path, char spans)
4. **Security-first** - embedding blocked content never reaches vector store
5. **Code-aware** - optional separate embedding models for code chunks
6. **Resilient** - retry logic, checkpointing, progress tracking
7. **Observable** - metrics, error tracking, logging

### Why This Pipeline Works

1. **BeautifulSoup** extracts clean content (no boilerplate)
2. **html2text** preserves structure as Markdown
3. **Doxstrux parser** provides rich structure extraction with security
4. **Doxstrux chunker** creates semantically meaningful chunks
5. **Vector embeddings** enable semantic search
6. **Metadata** enables filtering, citation, and context expansion

The pipeline leverages doxstrux's strengths:
- Section boundaries → chunk boundaries
- Security signals → filter unsafe content
- Rich metadata → retrieval context
- Code detection → specialized handling
