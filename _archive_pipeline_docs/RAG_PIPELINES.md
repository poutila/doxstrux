# RAG Pipelines

Unified pipeline architecture: **Source → Markdown → Parser → Chunker → Embedder → Vector Store**

This document covers indexing (ingestion) for all input modalities. For retrieval-time operations (query → answer), see `RETRIEVAL_PIPELINES.md`.

**Package:** `doxstrux-rag` (embedders, stores, pipeline) + `doxstrux-ingest` (scrapers)

**Core dependency:** `doxstrux` (parser, chunker)

---

## 1. Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INPUT ADAPTERS                                  │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  HTML Scraper   │  Web Crawler    │  PDF Extractor  │  Raw Markdown         │
│  (BeautifulSoup)│  (Crawl4AI)     │  (PyMuPDF/      │  (direct)             │
│                 │                 │   Marker)       │                       │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────┬───────────┘
         │                 │                 │                    │
         ▼                 ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MARKDOWN                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PARSER (doxstrux)                                                           │
│  - security_profile="strict" for external content                            │
│  - Extract sections, paragraphs, code blocks                                 │
│  - Security validation (prompt injection, XSS)                               │
│  - Rich metadata (line spans, word counts, hierarchy)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHUNKER (doxstrux)                                                          │
│  - Semantic chunking respecting section boundaries                           │
│  - Token estimation                                                          │
│  - Overlap for context                                                       │
│  - Metadata: section_path, source, char_span                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  EMBEDDER (OpenAI / Local)                                                   │
│  - Batch embedding                                                           │
│  - Optional: different models for code vs prose                              │
│  - Deduplication via content hash                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  VECTOR STORE (Chroma / Qdrant / Pinecone / pgvector)                        │
│  - Store embeddings with rich metadata                                       │
│  - Enable filtered search (by source, section, code)                         │
│  - Support retrieval expansion (link graph)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Input Adapters

### 2.1 Adapter Selection Guide

| Source | Adapter | When to Use |
|--------|---------|-------------|
| Simple HTML pages | HTML Scraper | Static sites, no JavaScript |
| JavaScript SPAs | Web Crawler | React, Vue, dynamic content |
| Protected sites | Web Crawler | Anti-bot protection, login required |
| PDF documents | PDF Extractor | Documents, reports, papers |
| Markdown files | Direct | Already in markdown format |

---

## 3. HTML Scraper (BeautifulSoup)

For simple static HTML pages.

### 3.1 Implementation

```python
from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
import html2text

@dataclass
class ScrapedPage:
    url: str
    title: str
    markdown: str
    metadata: dict

class HTMLScraper:
    def __init__(self, user_agent: str = "DoxstruxBot/1.0", rate_limit: float = 1.0):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self.rate_limit = rate_limit
        self.converter = html2text.HTML2Text()
        self.converter.body_width = 0

    def scrape(self, url: str) -> ScrapedPage:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        metadata = self._extract_metadata(soup, url)
        content = self._extract_content(soup)
        markdown = self.converter.handle(str(content))
        markdown = self._add_frontmatter(markdown, metadata)

        return ScrapedPage(
            url=url,
            title=metadata.get("title", ""),
            markdown=markdown,
            metadata=metadata,
        )

    def _extract_content(self, soup: BeautifulSoup):
        # Remove boilerplate
        for tag in soup.find_all(["nav", "footer", "header", "aside", "script", "style"]):
            tag.decompose()

        return soup.find("main") or soup.find("article") or soup.body or soup

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        meta = {"url": url}
        if soup.title:
            meta["title"] = soup.title.string
        for tag in soup.find_all("meta"):
            name = tag.get("name", tag.get("property", ""))
            if name in ("description", "author") and tag.get("content"):
                meta[name] = tag["content"]
        return meta

    def _add_frontmatter(self, md: str, metadata: dict) -> str:
        import yaml
        fm = {k: v for k, v in metadata.items() if k in ["title", "author", "url"] and v}
        if fm:
            return f"---\n{yaml.dump(fm)}---\n\n{md}"
        return md
```

---

## 4. Web Crawler (Crawl4AI)

For JavaScript-heavy sites, anti-bot protection, and deep crawling.

### 4.1 Why Crawl4AI?

| Feature | BeautifulSoup | Crawl4AI |
|---------|--------------|----------|
| JavaScript rendering | No | Yes (Playwright) |
| Anti-bot evasion | Manual | Built-in |
| Rate limiting | Manual | Built-in |
| Deep crawling | Manual | Built-in |
| Session management | Manual | Built-in |
| Infinite scroll | Complex | Built-in |

### 4.2 Implementation

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(
    browser_type="chromium",
    headless=True,
    user_agent_mode="random",
    enable_stealth=True,
)

crawler_config = CrawlerRunConfig(
    word_count_threshold=50,
    excluded_tags=["script", "style", "nav", "footer"],
    wait_until="networkidle",
)

async def crawl_url(url: str) -> str:
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawler_config)

        if not result.success:
            raise Exception(result.error_message)

        markdown = result.markdown.fit_markdown or result.markdown.raw_markdown
        return enhance_markdown(markdown, result.metadata)

def enhance_markdown(md: str, metadata: dict) -> str:
    """Fix common issues and add frontmatter."""
    import re
    # Fix citation format: ⟨1⟩ → [1]
    md = re.sub(r'⟨(\d+)⟩', r'[\1]', md)
    # Add frontmatter
    return add_frontmatter(md, metadata)
```

### 4.3 Deep Crawling

```python
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, FilterChain, URLPatternFilter

strategy = BFSDeepCrawlStrategy(
    max_pages=100,
    max_depth=3,
    filter_chain=FilterChain([
        URLPatternFilter(patterns=["*/docs/*", "*/api/*"]),
    ]),
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    async for result in crawler.arun_many(urls=[start_url], config=crawler_config):
        if result.success:
            yield result.markdown.raw_markdown
```

---

## 5. PDF Extractor

### 5.1 Library Selection

| Library | Speed | Accuracy | Best For |
|---------|-------|----------|----------|
| **PyMuPDF4LLM** | ~0.1s/page | Good | High-volume, simple PDFs |
| **Marker** | ~2.8s/page | Excellent | Complex layouts, equations |
| **MarkItDown** | Medium | Good | Multi-format pipelines |

### 5.2 PyMuPDF4LLM Implementation (Fast)

```python
import pymupdf4llm
import fitz

def extract_pdf(pdf_path: str) -> str:
    """Fast extraction for simple PDFs."""
    doc = fitz.open(pdf_path)
    metadata = {
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "page_count": len(doc),
    }
    doc.close()

    markdown = pymupdf4llm.to_markdown(pdf_path)
    markdown = enhance_pdf_markdown(markdown)
    return add_frontmatter(markdown, metadata)

def enhance_pdf_markdown(md: str) -> str:
    """Fix PDF-specific artifacts."""
    import re
    # Fix hyphenation: word- break → wordbreak
    md = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', md)
    # Fix ligatures
    md = md.replace('ﬁ', 'fi').replace('ﬂ', 'fl').replace('ﬀ', 'ff')
    return md
```

### 5.3 Marker Implementation (Accurate)

```python
import subprocess
import json

def extract_pdf_marker(pdf_path: str, use_llm: bool = False) -> str:
    """High-accuracy extraction for complex PDFs."""
    cmd = ["marker_single", pdf_path, "--output_format", "markdown"]
    if use_llm:
        cmd.append("--use_llm")

    result = subprocess.run(cmd, capture_output=True, text=True)
    # Marker outputs to a directory
    output_dir = pdf_path.replace(".pdf", "")
    md_file = f"{output_dir}/{Path(pdf_path).stem}.md"

    with open(md_file) as f:
        return f.read()
```

---

## 6. Shared Processing Stage

After any adapter produces markdown, processing is identical.

### 6.1 Parse with Security

```python
from doxstrux import parse_markdown_file

def parse_content(markdown: str, source_url: str = "") -> dict:
    """Parse with strict security for external content."""
    import tempfile, os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(markdown)
        path = f.name

    try:
        result = parse_markdown_file(path, security_profile="strict")
        result["metadata"]["source_url"] = source_url
        return result
    finally:
        os.unlink(path)
```

### 6.2 Security Check

```python
def check_safety(parse_result: dict) -> tuple[bool, str]:
    """Check if content is safe for embedding."""
    meta = parse_result["metadata"]

    if meta.get("embedding_blocked"):
        return False, meta.get("embedding_block_reason", "blocked")

    if meta.get("quarantined"):
        reasons = meta.get("quarantine_reasons", [])
        dangerous = ["prompt_injection_content", "prompt_injection_footnotes"]
        if any(r in str(reasons) for r in dangerous):
            return False, f"quarantined: {reasons}"

    return True, "safe"
```

### 6.3 Chunk

```python
from doxstrux.chunker import chunk_document, ChunkPolicy

def chunk_content(parse_result: dict, source_type: str) -> list:
    """Chunk with appropriate policy for source type."""
    policy = {
        "web": ChunkPolicy(mode="semantic", target_tokens=500, overlap_tokens=50),
        "pdf": ChunkPolicy(mode="semantic", target_tokens=500, overlap_tokens=75),
        "markdown": ChunkPolicy(mode="semantic", target_tokens=600, overlap_tokens=60),
    }.get(source_type, ChunkPolicy())

    return chunk_document(parse_result, policy).chunks
```

---

## 7. Embedder

### 7.1 RAGChunk Model

Universal chunk format for all pipelines:

```python
@dataclass
class RAGChunk:
    chunk_id: str
    text: str
    normalized_text: str
    source_type: str              # "web", "pdf", "markdown"
    source_path: str
    source_title: str
    section_path: list[str]
    section_title: str
    char_span: tuple[int, int] | None = None
    line_span: tuple[int, int] | None = None
    page_number: int | None = None
    token_estimate: int = 0
    has_code: bool = False
    risk_flags: list[str] = field(default_factory=list)
    content_hash: str = ""

    def to_metadata_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "section_path": "/".join(self.section_path),
            "has_code": self.has_code,
            "risk_flags": ",".join(self.risk_flags),
            "content_hash": self.content_hash,
        }
```

### 7.2 OpenAI Embedder

```python
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenAIEmbedder:
    MODELS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }

    def __init__(self, model: str = "text-embedding-3-small", batch_size: int = 100):
        self.model = model
        self.dimensions = self.MODELS[model]
        self.batch_size = batch_size
        self.client = OpenAI()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=60))
    def embed(self, texts: list[str]) -> list[list[float]]:
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            response = self.client.embeddings.create(model=self.model, input=batch)
            all_embeddings.extend([item.embedding for item in response.data])
        return all_embeddings
```

### 7.3 Local Embedder (sentence-transformers)

```python
from sentence_transformers import SentenceTransformer

class LocalEmbedder:
    MODELS = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "BAAI/bge-small-en-v1.5": 384,
    }

    def __init__(self, model: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model
        self.dimensions = self.MODELS.get(model, 384)
        self.model = SentenceTransformer(model, device=device)

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
```

---

## 8. Vector Stores

### 8.1 Store Selection

| Store | Use Case | Pros |
|-------|----------|------|
| **Chroma** | Development | Embedded, zero config |
| **Qdrant** | Production (self-hosted) | High performance |
| **Pinecone** | Production (managed) | Serverless |
| **pgvector** | PostgreSQL stack | SQL integration |

### 8.2 Chroma Implementation

```python
import chromadb
from chromadb.config import Settings

class ChromaStore:
    def __init__(self, collection_name: str, persist_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: list[RAGChunk], embeddings: list[list[float]]) -> list[str]:
        self.collection.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.normalized_text for c in chunks],
            metadatas=[c.to_metadata_dict() for c in chunks],
        )
        return [c.chunk_id for c in chunks]

    def search(self, query_embedding: list[float], k: int = 10, filter_dict: dict = None):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_dict,
            include=["documents", "metadatas", "distances"],
        )
        return results
```

---

## 9. Complete Pipeline

### 9.1 Unified Pipeline Class

```python
@dataclass
class PipelineConfig:
    embedder_type: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    store_type: str = "chroma"
    collection_name: str = "documents"
    security_profile: str = "strict"
    target_tokens: int = 500

class RAGPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.embedder = self._create_embedder()
        self.store = self._create_store()

    def process_markdown(self, markdown: str, source_type: str, source_path: str) -> dict:
        """Process markdown through full pipeline."""
        # Parse
        parse_result = parse_content(markdown, source_path)

        # Safety check
        safe, reason = check_safety(parse_result)
        if not safe:
            raise ValueError(f"Content blocked: {reason}")

        # Chunk
        chunks = chunk_content(parse_result, source_type)

        # Convert to RAGChunk
        rag_chunks = [self._to_rag_chunk(c, source_type, source_path) for c in chunks]

        # Embed
        embeddings = self.embedder.embed([c.normalized_text for c in rag_chunks])

        # Store
        self.store.add(rag_chunks, embeddings)

        return {"chunks_created": len(rag_chunks), "success": True}

    def search(self, query: str, k: int = 10, filter_dict: dict = None):
        query_embedding = self.embedder.embed([query])[0]
        return self.store.search(query_embedding, k, filter_dict)
```

### 9.2 Usage Examples

```python
# Initialize
pipeline = RAGPipeline(PipelineConfig(collection_name="my_docs"))

# Process HTML
scraper = HTMLScraper()
page = scraper.scrape("https://docs.example.com/intro")
pipeline.process_markdown(page.markdown, "web", page.url)

# Process PDF
markdown = extract_pdf("report.pdf")
pipeline.process_markdown(markdown, "pdf", "report.pdf")

# Process raw markdown
with open("README.md") as f:
    pipeline.process_markdown(f.read(), "markdown", "README.md")

# Search
results = pipeline.search("how to authenticate", k=5)
```

---

## 10. Error Handling & Resilience

### 10.1 Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=60))
def process_with_retry(pipeline, url):
    scraper = HTMLScraper()
    page = scraper.scrape(url)
    return pipeline.process_markdown(page.markdown, "web", url)
```

### 10.2 Checkpointing

```python
def process_urls_with_checkpoint(urls: list[str], checkpoint_file: str = "checkpoint.json"):
    import json

    processed = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file) as f:
            processed = set(json.load(f).get("processed", []))

    for url in urls:
        if url in processed:
            continue

        try:
            process_with_retry(pipeline, url)
            processed.add(url)

            with open(checkpoint_file, "w") as f:
                json.dump({"processed": list(processed)}, f)
        except Exception as e:
            logger.error(f"Failed {url}: {e}")
```

---

## 11. Configuration Matrix

| Use Case | Input | Embedder | Store | Notes |
|----------|-------|----------|-------|-------|
| Development | Any | local | chroma | Fast iteration |
| Production (cost) | Any | local-gpu | qdrant | Self-hosted |
| Production (quality) | Any | openai-large | qdrant | Best results |
| Existing PostgreSQL | Any | openai | pgvector | SQL integration |
| Serverless | Any | openai | pinecone | No infrastructure |
| Technical docs | Code-heavy | hybrid | any | Separate code embeddings |
