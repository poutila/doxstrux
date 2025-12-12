# Web Crawler Pipeline Architecture

A complete pipeline: **URL Discovery → Crawl4AI → Markdown → Doxstrux Parser → Chunker → Vector Embedding**

Built on [Crawl4AI](https://github.com/unclecode/crawl4ai) - an enterprise-grade, LLM-friendly web crawler.

---

## Pipeline Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   URL Seeder    │───▶│    Crawl4AI     │───▶│  Doxstrux       │───▶│    Chunker      │───▶│   Embedder      │
│ Sitemap/Crawl   │    │ Playwright+Stealth│   │    Parser       │    │    Doxstrux     │    │  OpenAI/etc     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │                      │                      │
        ▼                      ▼                      ▼                      ▼                      ▼
   URL List             Raw HTML +              Structured              Chunks               Vectors
   (filtered)           Markdown                JSON output            + metadata            + metadata
```

---

## Why Crawl4AI + Doxstrux?

| Feature | Crawl4AI | Doxstrux | Combined |
|---------|----------|----------|----------|
| **Browser automation** | Playwright with stealth | - | Full JS rendering |
| **Anti-bot evasion** | User agent rotation, stealth mode | - | Access protected sites |
| **Markdown generation** | Built-in html2text | - | Clean markdown |
| **Structure extraction** | Basic | Rich (sections, hierarchy) | Deep structure |
| **Security validation** | - | Prompt injection, XSS detection | Safe embeddings |
| **Chunking** | Basic window/regex | Semantic, boundary-aware | Smart chunks |
| **Rate limiting** | Domain-aware, adaptive | - | Polite crawling |
| **Deep crawling** | BFS/DFS strategies | - | Site-wide ingestion |

**Crawl4AI handles the hard parts**: JavaScript rendering, anti-bot detection, rate limiting, URL discovery.
**Doxstrux handles the RAG parts**: Structure extraction, security validation, semantic chunking.

---

## 1. Stage 0: URL Discovery

### 1.1 URL Sources

```python
from crawl4ai import AsyncUrlSeeder, AsyncWebCrawler
from crawl4ai.async_configs import SeedingConfig

# Option 1: Sitemap discovery
seeder = AsyncUrlSeeder()
urls = await seeder.get_urls(
    domain="docs.example.com",
    include_sitemaps=True,
    max_results=1000,
)

# Option 2: CommonCrawl CDX (historical URLs)
urls = await seeder.get_urls_from_cdx(
    domain="example.com",
    max_results=500,
)

# Option 3: Deep crawl from seed URL (BFS/DFS)
# See Stage 1 deep crawling config
```

### 1.2 URL Filtering

```python
from crawl4ai.deep_crawling import (
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter,
    SEOFilter,
)

# Build filter chain
filters = FilterChain([
    # Only crawl documentation paths
    URLPatternFilter(
        patterns=["*/docs/*", "*/api/*", "*/guide/*"],
        use_glob=True,
    ),

    # Stay within domain
    DomainFilter(scope="internal"),  # Same domain only

    # Skip non-document content
    ContentTypeFilter(
        exclude=["image/*", "video/*", "audio/*", "application/pdf"]
    ),

    # Follow SEO hints (sitemap priority, robots.txt)
    SEOFilter(),
])

# Apply to URLs
filtered_urls = []
for url in urls:
    if await filters.apply(url):
        filtered_urls.append(url)
```

### 1.3 URL Scoring (Priority)

```python
from crawl4ai.deep_crawling import (
    CompositeScorer,
    KeywordRelevanceScorer,
    PathDepthScorer,
    FreshnessScorer,
    DomainAuthorityScorer,
)

# Score URLs for crawl priority
scorer = CompositeScorer([
    KeywordRelevanceScorer(query="api documentation"),  # Relevance to query
    PathDepthScorer(max_depth=5),  # Prefer shallow URLs
    FreshnessScorer(),  # Prefer recent content
    DomainAuthorityScorer(),  # Prefer authoritative domains
])

scored_urls = [(url, scorer.score(url)) for url in filtered_urls]
sorted_urls = sorted(scored_urls, key=lambda x: x[1], reverse=True)
```

---

## 2. Stage 1: Web Crawling (Crawl4AI)

### 2.1 Browser Configuration

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, ProxyConfig

# Full-featured browser config
browser_config = BrowserConfig(
    # Browser type
    browser_type="chromium",  # "chromium", "firefox", "webkit"
    headless=True,

    # Anti-detection
    user_agent_mode="random",  # Rotate user agents
    enable_stealth=True,       # Playwright stealth plugin

    # Performance
    text_mode=False,           # Set True to skip images (faster)
    light_mode=False,          # Disable background services

    # Viewport
    viewport_width=1920,
    viewport_height=1080,

    # Proxy (optional)
    proxy_config=ProxyConfig.from_string("http://user:pass@proxy:8080"),

    # Persistence (optional - for login sessions)
    use_persistent_context=True,
    user_data_dir="./browser_profile",

    # Debugging
    verbose=True,
)
```

### 2.2 Crawler Run Configuration

```python
from crawl4ai.async_configs import CrawlerRunConfig, VirtualScrollConfig
from crawl4ai import CacheMode

crawler_config = CrawlerRunConfig(
    # Content extraction
    word_count_threshold=50,           # Min words to process
    excluded_tags=["script", "style", "nav", "footer", "header"],
    remove_forms=True,

    # Target specific content (optional)
    css_selector="main, article, .content",  # Focus on main content
    target_elements=["main", "article"],

    # Wait strategies
    wait_until="networkidle",          # Wait for network quiet
    wait_for=".content-loaded",        # Wait for specific element
    wait_for_timeout=10000,            # 10s timeout
    wait_for_images=False,             # Don't wait for images

    # JavaScript execution (optional)
    js_code=[
        "document.querySelectorAll('.cookie-banner').forEach(e => e.remove())",
        "document.querySelectorAll('.popup').forEach(e => e.remove())",
    ],

    # Scrolling (for infinite scroll pages)
    scan_full_page=False,              # Set True for infinite scroll
    scroll_delay=0.3,
    max_scroll_steps=20,

    # Virtual scroll (for virtualized lists)
    virtual_scroll_config=VirtualScrollConfig(
        container_selector=".infinite-list",
        scroll_count=10,
        wait_after_scroll=0.5,
    ),

    # Overlays and popups
    remove_overlay_elements=True,      # Remove modals, popups

    # User simulation (optional - for bot detection)
    simulate_user=False,               # Random mouse/keyboard
    override_navigator=True,           # Spoof navigator properties

    # Output
    screenshot=False,                  # Capture screenshot
    pdf=False,                         # Generate PDF

    # Caching
    cache_mode=CacheMode.ENABLED,      # Use cache

    # Timeouts
    page_timeout=60000,                # 60s page load timeout
    delay_before_return_html=0.1,      # Final delay
)
```

### 2.3 Deep Crawling Configuration

```python
from crawl4ai.deep_crawling import (
    BFSDeepCrawlStrategy,
    DFSDeepCrawlStrategy,
    BestFirstCrawlingStrategy,
)

# BFS: Breadth-first (wide coverage)
bfs_strategy = BFSDeepCrawlStrategy(
    max_pages=100,
    max_depth=3,
    filter_chain=filters,  # From Stage 0
    include_external=False,
)

# DFS: Depth-first (follow paths deeply)
dfs_strategy = DFSDeepCrawlStrategy(
    max_pages=100,
    max_depth=5,
    filter_chain=filters,
)

# Best-first: Score-based priority
best_first = BestFirstCrawlingStrategy(
    max_pages=100,
    scorers=scorer,  # From Stage 0
    filter_chain=filters,
)

# Use in config
crawler_config = CrawlerRunConfig(
    deep_crawl_strategy=bfs_strategy,
    # ... other options
)
```

### 2.4 Rate Limiting

```python
from crawl4ai.async_dispatcher import RateLimiter, MemoryAdaptiveDispatcher

# Rate limiter (per-domain)
rate_limiter = RateLimiter(
    base_delay=(1.0, 3.0),      # Random 1-3s between requests
    max_delay=60.0,              # Max backoff delay
    max_retries=3,               # Retry on rate limit
    rate_limit_codes=[429, 503], # HTTP codes to back off on
)

# Memory-adaptive dispatcher
dispatcher = MemoryAdaptiveDispatcher(
    initial_concurrency=5,
    max_concurrency=20,
    memory_threshold=80.0,       # Throttle at 80% RAM
    rate_limiter=rate_limiter,
)
```

### 2.5 Complete Crawling

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def crawl_site(seed_url: str, max_pages: int = 100) -> list:
    """Crawl a site and return results."""

    browser_config = BrowserConfig(
        headless=True,
        user_agent_mode="random",
        enable_stealth=True,
    )

    crawler_config = CrawlerRunConfig(
        word_count_threshold=50,
        excluded_tags=["script", "style", "nav", "footer"],
        wait_until="domcontentloaded",
        cache_mode=CacheMode.ENABLED,
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_pages=max_pages,
            max_depth=3,
        ),
    )

    results = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=seed_url,
            config=crawler_config,
        )

        # Deep crawl returns list of results
        if isinstance(result, list):
            results.extend(result)
        else:
            results.append(result)

    return results


# Single URL crawl
async def crawl_url(url: str) -> dict:
    """Crawl a single URL."""

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

        return {
            "url": result.url,
            "success": result.success,
            "markdown": str(result.markdown),  # Raw markdown
            "html": result.html,
            "cleaned_html": result.cleaned_html,
            "links": result.links,
            "media": result.media,
            "metadata": result.metadata,
            "status_code": result.status_code,
        }
```

### 2.6 Batch Crawling with Progress

```python
from tqdm.asyncio import tqdm

async def crawl_urls_batch(
    urls: list[str],
    max_concurrent: int = 10,
) -> list[dict]:
    """Crawl multiple URLs with progress tracking."""

    browser_config = BrowserConfig(
        headless=True,
        enable_stealth=True,
    )

    crawler_config = CrawlerRunConfig(
        word_count_threshold=50,
        cache_mode=CacheMode.ENABLED,
    )

    results = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Stream results as they complete
        async for result in tqdm(
            crawler.arun_many(urls, config=crawler_config),
            total=len(urls),
            desc="Crawling",
        ):
            if result.success:
                results.append({
                    "url": result.url,
                    "markdown": str(result.markdown),
                    "metadata": result.metadata,
                })
            else:
                results.append({
                    "url": result.url,
                    "error": result.error_message,
                })

    return results
```

---

## 3. Stage 2: Markdown Enhancement

Crawl4AI provides markdown, but we can enhance it before parsing:

```python
from dataclasses import dataclass
import re

@dataclass
class EnhancedMarkdown:
    markdown: str
    metadata: dict
    source_url: str
    enhancements: list[str]

class CrawlMarkdownEnhancer:
    """Enhance crawl4ai markdown for doxstrux parsing."""

    def enhance(self, crawl_result: dict) -> EnhancedMarkdown:
        """Enhance markdown from crawl result."""
        md = crawl_result.get("markdown", "")
        metadata = crawl_result.get("metadata", {})
        url = crawl_result.get("url", "")

        enhancements = []

        # Add frontmatter from crawl metadata
        md = self._add_frontmatter(md, metadata, url)
        enhancements.append("frontmatter_added")

        # Clean up common artifacts
        md = self._fix_citation_links(md)
        enhancements.append("citations_cleaned")

        md = self._normalize_whitespace(md)
        enhancements.append("whitespace_normalized")

        md = self._fix_tables(md)
        enhancements.append("tables_fixed")

        return EnhancedMarkdown(
            markdown=md,
            metadata=metadata,
            source_url=url,
            enhancements=enhancements,
        )

    def _add_frontmatter(self, md: str, metadata: dict, url: str) -> str:
        """Add YAML frontmatter from metadata."""
        import yaml

        fm = {
            "source_url": url,
            "title": metadata.get("title", ""),
            "description": metadata.get("description", ""),
        }

        # Add Open Graph data if present
        if "og:title" in metadata:
            fm["og_title"] = metadata["og:title"]
        if "og:description" in metadata:
            fm["og_description"] = metadata["og:description"]

        # Filter empty values
        fm = {k: v for k, v in fm.items() if v}

        if not fm:
            return md

        frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
        return f"---\n{frontmatter}---\n\n{md}"

    def _fix_citation_links(self, md: str) -> str:
        """Convert crawl4ai citation format to standard markdown."""
        # crawl4ai uses ⟨1⟩ format - convert to [1]
        md = re.sub(r'⟨(\d+)⟩', r'[\1]', md)
        return md

    def _normalize_whitespace(self, md: str) -> str:
        """Normalize whitespace."""
        # Multiple blank lines to double
        md = re.sub(r'\n{4,}', '\n\n\n', md)
        # Trailing whitespace
        md = '\n'.join(line.rstrip() for line in md.split('\n'))
        return md

    def _fix_tables(self, md: str) -> str:
        """Fix common table issues."""
        lines = md.split('\n')
        fixed = []
        in_table = False

        for line in lines:
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    # Check if next line is separator
            fixed.append(line)

            if in_table and '|' not in line and line.strip():
                in_table = False

        return '\n'.join(fixed)
```

---

## 4. Stage 3: Doxstrux Parser

Parse the enhanced markdown with strict security:

```python
from doxstrux import parse_markdown_file
from doxstrux.markdown_parser_core import MarkdownParserCore
import tempfile
import os

def parse_crawled_markdown(
    enhanced: EnhancedMarkdown,
) -> dict:
    """Parse crawled markdown with doxstrux."""

    # Write to temp file for full API
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(enhanced.markdown)
        temp_path = f.name

    try:
        # ALWAYS use strict for web content
        result = parse_markdown_file(temp_path, security_profile="strict")

        # Add crawl metadata
        result["metadata"]["crawl"] = {
            "source_url": enhanced.source_url,
            "title": enhanced.metadata.get("title", ""),
            "description": enhanced.metadata.get("description", ""),
            "enhancements": enhanced.enhancements,
        }

        # Security checks
        if result["metadata"].get("embedding_blocked"):
            raise SecurityError(
                f"Content blocked: {result['metadata'].get('embedding_block_reason')}"
            )

        if result["metadata"].get("quarantined"):
            reasons = result["metadata"].get("quarantine_reasons", [])
            # Log warning but continue
            print(f"Warning: Quarantined content from {enhanced.source_url}: {reasons}")

        # Check for prompt injection
        security = result["metadata"].get("security", {})
        stats = security.get("statistics", {})
        if stats.get("prompt_injection_in_content"):
            raise SecurityError(
                f"Prompt injection detected in {enhanced.source_url}"
            )

        return result

    finally:
        os.unlink(temp_path)
```

---

## 5. Stage 4: Chunking (Doxstrux)

```python
from doxstrux.chunker import chunk_document, ChunkPolicy

def chunk_crawled_document(
    parsed: dict,
    target_tokens: int = 500,
    max_tokens: int = 1000,
) -> list:
    """Chunk parsed document for embedding."""

    policy = ChunkPolicy(
        mode="semantic",
        target_tokens=target_tokens,
        max_chunk_tokens=max_tokens,
        overlap_tokens=50,
        respect_boundaries=True,
        include_code=True,
        include_tables=True,
    )

    result = chunk_document(parsed, policy)

    # Add crawl metadata to chunks
    source_url = parsed["metadata"]["crawl"]["source_url"]
    page_title = parsed["metadata"]["crawl"]["title"]

    for chunk in result.chunks:
        chunk.meta["source_url"] = source_url
        chunk.meta["page_title"] = page_title
        chunk.meta["source_type"] = "web"

    return result.chunks
```

---

## 6. Stage 5: Vector Embedding

```python
from dataclasses import dataclass

@dataclass
class WebEmbeddingChunk:
    """Chunk prepared for embedding from web crawl."""
    chunk_id: str
    text: str
    source_url: str
    page_title: str
    section_path: list[str]
    section_title: str
    char_span: tuple[int, int]
    token_estimate: int
    risk_flags: list[str]
    has_code: bool
    crawled_at: str  # ISO timestamp

def prepare_web_chunks_for_embedding(
    chunks: list,
    parsed: dict,
) -> list[WebEmbeddingChunk]:
    """Convert chunks to embedding-ready format."""
    from datetime import datetime

    crawl_meta = parsed["metadata"].get("crawl", {})

    embedding_chunks = []
    for chunk in chunks:
        ec = WebEmbeddingChunk(
            chunk_id=chunk.chunk_id,
            text=chunk.normalized_text,
            source_url=crawl_meta.get("source_url", ""),
            page_title=crawl_meta.get("title", ""),
            section_path=chunk.section_path,
            section_title=chunk.meta.get("title", ""),
            char_span=chunk.span,
            token_estimate=chunk.token_estimate,
            risk_flags=chunk.risk_flags,
            has_code=chunk.meta.get("has_code", False),
            crawled_at=datetime.utcnow().isoformat(),
        )
        embedding_chunks.append(ec)

    return embedding_chunks

# Embedding (same as other pipelines)
def embed_web_chunks(chunks: list[WebEmbeddingChunk], embedder) -> list:
    texts = [c.text for c in chunks]
    embeddings = embedder.embed(texts)

    return [
        {"chunk": chunk, "embedding": emb}
        for chunk, emb in zip(chunks, embeddings)
    ]
```

---

## 7. Complete Web Crawler Pipeline

```python
from dataclasses import dataclass
from typing import Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class WebPipelineConfig:
    # Crawling
    max_pages: int = 100
    max_depth: int = 3
    max_concurrent: int = 10
    rate_limit_delay: tuple = (1.0, 3.0)

    # Browser
    headless: bool = True
    enable_stealth: bool = True
    user_agent_mode: str = "random"

    # Content
    word_count_threshold: int = 50
    excluded_tags: list = None
    css_selector: Optional[str] = None

    # Parser
    security_profile: str = "strict"

    # Chunker
    target_tokens: int = 500
    max_tokens: int = 1000

    # Embedder
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 100

    # Storage
    collection_name: str = "web_documents"
    persist_dir: str = "./vector_db"

    def __post_init__(self):
        if self.excluded_tags is None:
            self.excluded_tags = ["script", "style", "nav", "footer", "header"]


class WebCrawlerPipeline:
    """Complete web crawler to vector embedding pipeline."""

    def __init__(self, config: WebPipelineConfig):
        self.config = config
        self.enhancer = CrawlMarkdownEnhancer()
        self.embedder = OpenAIEmbedder(config.embedding_model)
        self.store = VectorStore(
            collection_name=config.collection_name,
            persist_dir=config.persist_dir,
        )

    async def crawl_site(self, seed_url: str) -> list[dict]:
        """Crawl entire site from seed URL."""
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
        from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, FilterChain, DomainFilter

        browser_config = BrowserConfig(
            headless=self.config.headless,
            user_agent_mode=self.config.user_agent_mode,
            enable_stealth=self.config.enable_stealth,
        )

        # Filter to stay within domain
        filters = FilterChain([DomainFilter(scope="internal")])

        crawler_config = CrawlerRunConfig(
            word_count_threshold=self.config.word_count_threshold,
            excluded_tags=self.config.excluded_tags,
            css_selector=self.config.css_selector,
            wait_until="domcontentloaded",
            cache_mode=CacheMode.ENABLED,
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_pages=self.config.max_pages,
                max_depth=self.config.max_depth,
                filter_chain=filters,
            ),
        )

        results = []

        async with AsyncWebCrawler(config=browser_config) as crawler:
            crawl_results = await crawler.arun(
                url=seed_url,
                config=crawler_config,
            )

            # Handle both single and multiple results
            if not isinstance(crawl_results, list):
                crawl_results = [crawl_results]

            for result in crawl_results:
                if result.success:
                    results.append({
                        "url": result.url,
                        "markdown": str(result.markdown),
                        "metadata": result.metadata or {},
                        "status_code": result.status_code,
                    })

        return results

    async def process_site(self, seed_url: str) -> dict:
        """Process entire site through pipeline."""
        stats = {
            "seed_url": seed_url,
            "pages_crawled": 0,
            "pages_processed": 0,
            "chunks_created": 0,
            "errors": [],
        }

        try:
            # Stage 1: Crawl
            logger.info(f"Crawling site: {seed_url}")
            crawl_results = await self.crawl_site(seed_url)
            stats["pages_crawled"] = len(crawl_results)

            all_chunks = []

            for crawl_result in crawl_results:
                try:
                    # Stage 2: Enhance
                    enhanced = self.enhancer.enhance(crawl_result)

                    # Stage 3: Parse
                    parsed = parse_crawled_markdown(enhanced)

                    # Check security
                    if parsed["metadata"].get("embedding_blocked"):
                        stats["errors"].append({
                            "url": crawl_result["url"],
                            "error": "embedding_blocked",
                        })
                        continue

                    # Stage 4: Chunk
                    chunks = chunk_crawled_document(
                        parsed,
                        self.config.target_tokens,
                        self.config.max_tokens,
                    )

                    # Prepare for embedding
                    embedding_chunks = prepare_web_chunks_for_embedding(chunks, parsed)
                    all_chunks.extend(embedding_chunks)

                    stats["pages_processed"] += 1

                except Exception as e:
                    stats["errors"].append({
                        "url": crawl_result["url"],
                        "error": str(e),
                    })

            if all_chunks:
                # Stage 5: Embed
                logger.info(f"Embedding {len(all_chunks)} chunks")
                embedded = embed_web_chunks(all_chunks, self.embedder)

                # Stage 6: Store
                logger.info("Storing in vector database")
                self.store.add_web_chunks(embedded)

                stats["chunks_created"] = len(embedded)

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            stats["errors"].append({"error": str(e)})

        return stats

    async def process_urls(self, urls: list[str]) -> dict:
        """Process list of URLs (no deep crawl)."""
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

        stats = {
            "urls_provided": len(urls),
            "pages_processed": 0,
            "chunks_created": 0,
            "errors": [],
        }

        browser_config = BrowserConfig(
            headless=self.config.headless,
            enable_stealth=self.config.enable_stealth,
        )

        crawler_config = CrawlerRunConfig(
            word_count_threshold=self.config.word_count_threshold,
            excluded_tags=self.config.excluded_tags,
            cache_mode=CacheMode.ENABLED,
        )

        all_chunks = []

        async with AsyncWebCrawler(config=browser_config) as crawler:
            async for result in crawler.arun_many(urls, config=crawler_config):
                if not result.success:
                    stats["errors"].append({
                        "url": result.url,
                        "error": result.error_message,
                    })
                    continue

                try:
                    crawl_result = {
                        "url": result.url,
                        "markdown": str(result.markdown),
                        "metadata": result.metadata or {},
                    }

                    enhanced = self.enhancer.enhance(crawl_result)
                    parsed = parse_crawled_markdown(enhanced)

                    if parsed["metadata"].get("embedding_blocked"):
                        continue

                    chunks = chunk_crawled_document(parsed, self.config.target_tokens)
                    embedding_chunks = prepare_web_chunks_for_embedding(chunks, parsed)
                    all_chunks.extend(embedding_chunks)

                    stats["pages_processed"] += 1

                except Exception as e:
                    stats["errors"].append({
                        "url": result.url,
                        "error": str(e),
                    })

        if all_chunks:
            embedded = embed_web_chunks(all_chunks, self.embedder)
            self.store.add_web_chunks(embedded)
            stats["chunks_created"] = len(embedded)

        return stats


# Usage
async def main():
    config = WebPipelineConfig(
        max_pages=50,
        max_depth=2,
        enable_stealth=True,
        target_tokens=500,
        collection_name="documentation",
    )

    pipeline = WebCrawlerPipeline(config)

    # Crawl entire site
    stats = await pipeline.process_site("https://docs.example.com/")
    print(f"Crawled {stats['pages_crawled']} pages")
    print(f"Created {stats['chunks_created']} chunks")

    # Or process specific URLs
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
    ]
    stats = await pipeline.process_urls(urls)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 8. Advanced Patterns

### 8.1 Session Management (Login Required Sites)

```python
async def crawl_with_login(seed_url: str, login_url: str):
    """Crawl site that requires login."""
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

    browser_config = BrowserConfig(
        headless=False,  # Show browser for login
        use_persistent_context=True,
        user_data_dir="./login_profile",
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First, navigate to login page
        login_config = CrawlerRunConfig(
            js_code=[
                # Fill login form
                "document.querySelector('#username').value = 'user'",
                "document.querySelector('#password').value = 'pass'",
                "document.querySelector('#login-btn').click()",
            ],
            wait_for=".logged-in-indicator",  # Wait for login
            wait_for_timeout=30000,
        )

        await crawler.arun(url=login_url, config=login_config)

        # Now crawl with session
        crawl_config = CrawlerRunConfig(
            session_id="logged_in",  # Reuse session
            deep_crawl_strategy=BFSDeepCrawlStrategy(max_pages=100),
        )

        results = await crawler.arun(url=seed_url, config=crawl_config)
        return results
```

### 8.2 Handling JavaScript-Heavy Sites

```python
async def crawl_spa(url: str):
    """Crawl Single Page Application."""

    crawler_config = CrawlerRunConfig(
        # Wait for React/Vue to render
        wait_until="networkidle",
        wait_for="[data-loaded='true']",  # Custom attribute
        wait_for_timeout=15000,

        # Scroll to load content
        scan_full_page=True,
        scroll_delay=0.5,
        max_scroll_steps=30,

        # Remove overlays
        remove_overlay_elements=True,

        # Custom JS to wait for app
        js_code=[
            "await new Promise(r => setTimeout(r, 2000))",  # Extra wait
            "window.scrollTo(0, document.body.scrollHeight)",
        ],
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=crawler_config)
        return result
```

### 8.3 Proxy Rotation

```python
from crawl4ai.async_configs import ProxyConfig
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy

# Load proxies
proxies = [
    ProxyConfig.from_string("http://proxy1:8080"),
    ProxyConfig.from_string("http://proxy2:8080"),
    ProxyConfig.from_string("http://user:pass@proxy3:8080"),
]

rotation = RoundRobinProxyStrategy(proxies)

async def crawl_with_rotation(urls: list[str]):
    results = []

    for url in urls:
        proxy = await rotation.get_next_proxy()

        browser_config = BrowserConfig(
            proxy_config=proxy,
            enable_stealth=True,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url)
            results.append(result)

    return results
```

### 8.4 LLM-Based Content Extraction

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.async_configs import LLMConfig

# Use LLM to extract structured data
llm_config = LLMConfig(
    provider="openai/gpt-4o-mini",
    api_token=os.getenv("OPENAI_API_KEY"),
    temperature=0.0,
)

extraction = LLMExtractionStrategy(
    llm_config=llm_config,
    schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "main_content": {"type": "string"},
            "key_points": {"type": "array", "items": {"type": "string"}},
            "code_examples": {"type": "array", "items": {"type": "string"}},
        }
    },
    instruction="Extract the documentation content, focusing on the main text and code examples.",
)

crawler_config = CrawlerRunConfig(
    extraction_strategy=extraction,
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url=url, config=crawler_config)
    extracted = result.extracted_content  # Structured JSON
```

### 8.5 Content Filtering (Query-Focused)

```python
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Filter content by relevance to query
content_filter = BM25ContentFilter(
    user_query="API authentication",
    word_count_threshold=50,
)

markdown_generator = DefaultMarkdownGenerator(
    content_filter=content_filter,
)

crawler_config = CrawlerRunConfig(
    markdown_generator=markdown_generator,
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url=url, config=crawler_config)

    # fit_markdown is filtered by relevance
    relevant_markdown = result.markdown.fit_markdown
```

---

## 9. Error Handling & Resilience

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientWebPipeline(WebCrawlerPipeline):
    """Pipeline with retry logic."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    async def _crawl_with_retry(self, url: str) -> dict:
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            result = await crawler.arun(url=url, config=self.crawler_config)
            if not result.success:
                raise Exception(result.error_message)
            return result

    async def process_with_checkpoint(
        self,
        urls: list[str],
        checkpoint_file: str = "checkpoint.json",
    ) -> dict:
        """Process URLs with checkpointing."""
        import json

        # Load checkpoint
        processed = set()
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file) as f:
                processed = set(json.load(f).get("processed", []))

        remaining = [u for u in urls if u not in processed]

        for url in remaining:
            try:
                await self._process_url(url)
                processed.add(url)

                # Save checkpoint
                with open(checkpoint_file, "w") as f:
                    json.dump({"processed": list(processed)}, f)

            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
```

---

## 10. Summary

### Pipeline Flow

```
Seed URL / URL List
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ URL DISCOVERY (AsyncUrlSeeder)                                   │
│ - Sitemap parsing                                                │
│ - CommonCrawl CDX                                                │
│ - Deep crawl (BFS/DFS/Best-First)                                │
│ - URL filtering (domain, pattern, content type)                  │
│ - URL scoring (relevance, depth, freshness)                      │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ WEB CRAWLING (Crawl4AI)                                          │
│ - Playwright browser automation                                  │
│ - Anti-bot evasion (stealth, user agent rotation)                │
│ - JavaScript execution, infinite scroll                          │
│ - Rate limiting (per-domain, exponential backoff)                │
│ - Session management, proxy support                              │
│ - HTML → Markdown conversion                                     │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ ENHANCEMENT                                                      │
│ - Add YAML frontmatter from metadata                             │
│ - Fix citation format (⟨1⟩ → [1])                                │
│ - Normalize whitespace                                           │
│ - Fix table formatting                                           │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ PARSER (doxstrux)                                                │
│ - security_profile="strict" (always for web content)             │
│ - Extract sections, paragraphs, code blocks                      │
│ - Security validation (prompt injection, XSS)                    │
│ - Rich metadata (line spans, word counts, hierarchy)             │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ CHUNKER (doxstrux)                                               │
│ - Semantic chunking respecting section boundaries                │
│ - Token estimation                                               │
│ - Overlap for context                                            │
│ - Metadata: section_path, source_url, char_span                  │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ EMBEDDER (OpenAI / Local)                                        │
│ - Batch embedding                                                │
│ - Web-specific metadata                                          │
│ - Deduplication via embedding hash                               │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ VECTOR STORE                                                     │
│ - Store with rich metadata                                       │
│ - Filter by source domain, section, date                         │
│ - Link-aware retrieval expansion                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Crawl4AI Features Used

| Feature | Purpose |
|---------|---------|
| **AsyncWebCrawler** | Main crawler interface |
| **BrowserConfig** | Browser settings, stealth mode |
| **CrawlerRunConfig** | Per-crawl settings |
| **BFSDeepCrawlStrategy** | Site-wide crawling |
| **FilterChain** | URL filtering |
| **RateLimiter** | Polite crawling |
| **MemoryAdaptiveDispatcher** | Concurrency control |
| **DefaultMarkdownGenerator** | HTML → Markdown |
| **BM25ContentFilter** | Relevance filtering |

### Comparison with Basic BeautifulSoup

| Feature | BeautifulSoup | Crawl4AI |
|---------|--------------|----------|
| JavaScript rendering | No | Yes (Playwright) |
| Anti-bot evasion | Manual | Built-in |
| Rate limiting | Manual | Built-in |
| Deep crawling | Manual | Built-in |
| Session management | Manual | Built-in |
| Infinite scroll | Complex | Built-in |
| Proxy rotation | Manual | Built-in |
| Caching | Manual | Built-in |

### When to Use This Pipeline

| Use Case | Recommendation |
|----------|----------------|
| Documentation sites | Excellent - deep crawl + semantic chunks |
| SPAs (React, Vue) | Excellent - JS rendering + wait strategies |
| Protected sites | Good - stealth + session management |
| High-volume crawling | Good - rate limiting + memory adaptive |
| Simple static sites | Overkill - use SCRAPING_PIPELINE.md instead |
