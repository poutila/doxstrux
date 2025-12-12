# Embedder & Vector Store Implementation

Complete, production-ready implementations for the final stages of the RAG pipeline.

---

## Overview

```
Chunks (from doxstrux chunker)
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ EMBEDDER                                                         │
│ - OpenAI (text-embedding-3-small/large)                          │
│ - Local (sentence-transformers)                                  │
│ - Hybrid (different models for code vs prose)                    │
│ - Batch processing with retry logic                              │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│ VECTOR STORE                                                     │
│ - Chroma (local development)                                     │
│ - Qdrant (production, self-hosted)                               │
│ - Pinecone (managed cloud)                                       │
│ - pgvector (PostgreSQL integration)                              │
└─────────────────────────────────────────────────────────────────┘
 │
 ▼
Searchable Knowledge Base
```

---

## 1. Chunk Data Model

First, define a universal chunk format that all pipelines produce:

```python
# src/doxstrux/rag/models.py

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import hashlib

@dataclass
class RAGChunk:
    """Universal chunk format for RAG pipelines.

    All pipeline sources (HTML, PDF, web crawler) produce this format.
    """
    # Core content
    chunk_id: str
    text: str                          # Raw text for embedding
    normalized_text: str               # Cleaned text (whitespace normalized)

    # Source tracking
    source_type: str                   # "web", "pdf", "html", "markdown"
    source_path: str                   # File path or URL
    source_title: str                  # Document/page title

    # Structure
    section_path: list[str]            # ["intro", "getting-started", "installation"]
    section_title: str                 # Current section title

    # Position
    char_span: Optional[tuple[int, int]] = None   # (start, end) in source
    line_span: Optional[tuple[int, int]] = None   # (start_line, end_line)
    page_number: Optional[int] = None             # For PDFs

    # Metadata
    token_estimate: int = 0
    word_count: int = 0
    has_code: bool = False
    has_table: bool = False
    languages: list[str] = field(default_factory=list)  # Code languages

    # Security
    risk_flags: list[str] = field(default_factory=list)

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source_modified_at: Optional[str] = None

    # Computed
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                self.normalized_text.encode()
            ).hexdigest()[:16]
        if not self.word_count:
            self.word_count = len(self.text.split())

    def to_metadata_dict(self) -> dict:
        """Convert to flat dict for vector store metadata."""
        return {
            "chunk_id": self.chunk_id,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "source_title": self.source_title,
            "section_path": "/".join(self.section_path),
            "section_title": self.section_title,
            "char_start": self.char_span[0] if self.char_span else None,
            "char_end": self.char_span[1] if self.char_span else None,
            "line_start": self.line_span[0] if self.line_span else None,
            "line_end": self.line_span[1] if self.line_span else None,
            "page_number": self.page_number,
            "token_estimate": self.token_estimate,
            "word_count": self.word_count,
            "has_code": self.has_code,
            "has_table": self.has_table,
            "languages": ",".join(self.languages),
            "risk_flags": ",".join(self.risk_flags),
            "created_at": self.created_at,
            "content_hash": self.content_hash,
        }


@dataclass
class EmbeddedChunk:
    """Chunk with embedding vector."""
    chunk: RAGChunk
    embedding: list[float]
    embedding_model: str
    embedding_dim: int

    @property
    def id(self) -> str:
        return self.chunk.chunk_id

    @property
    def text(self) -> str:
        return self.chunk.normalized_text

    @property
    def metadata(self) -> dict:
        meta = self.chunk.to_metadata_dict()
        meta["embedding_model"] = self.embedding_model
        meta["embedding_dim"] = self.embedding_dim
        return meta
```

---

## 2. Embedder Interface & Implementations

### 2.1 Base Interface

```python
# src/doxstrux/rag/embedders/base.py

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedders."""

    @property
    def model_name(self) -> str:
        """Return model identifier."""
        ...

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        ...

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text."""
        ...


class BaseEmbedder(ABC):
    """Base class for embedders with common functionality."""

    def __init__(self, model_name: str, dimensions: int):
        self._model_name = model_name
        self._dimensions = dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        pass

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text."""
        return self.embed([text])[0]
```

### 2.2 OpenAI Embedder

```python
# src/doxstrux/rag/embedders/openai_embedder.py

import os
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import BaseEmbedder

# Model dimensions
OPENAI_MODELS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,  # Legacy
}

class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embeddings with retry logic and batching."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        batch_size: int = 100,
        max_retries: int = 3,
    ):
        if model not in OPENAI_MODELS:
            raise ValueError(f"Unknown model: {model}. Choose from {list(OPENAI_MODELS.keys())}")

        super().__init__(model, OPENAI_MODELS[model])

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or pass api_key.")

        self.batch_size = batch_size
        self.max_retries = max_retries

        # Lazy client initialization
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a single batch with retry."""
        response = self.client.embeddings.create(
            model=self._model_name,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in batches."""
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            embeddings = self._embed_batch(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        """Embed a search query (same as embed_single for OpenAI)."""
        return self.embed_single(query)


class OpenAIEmbedderAsync(OpenAIEmbedder):
    """Async version of OpenAI embedder."""

    @property
    def async_client(self):
        if not hasattr(self, '_async_client') or self._async_client is None:
            from openai import AsyncOpenAI
            self._async_client = AsyncOpenAI(api_key=self.api_key)
        return self._async_client

    async def embed_async(self, texts: list[str]) -> list[list[float]]:
        """Embed texts asynchronously."""
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            response = await self.async_client.embeddings.create(
                model=self._model_name,
                input=batch,
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)

        return all_embeddings
```

### 2.3 Local Embedder (Sentence Transformers)

```python
# src/doxstrux/rag/embedders/local_embedder.py

from typing import Optional
from .base import BaseEmbedder

# Popular local models
LOCAL_MODELS = {
    "all-MiniLM-L6-v2": 384,
    "all-mpnet-base-v2": 768,
    "paraphrase-MiniLM-L6-v2": 384,
    "multi-qa-MiniLM-L6-cos-v1": 384,
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "BAAI/bge-large-en-v1.5": 1024,
    "nomic-ai/nomic-embed-text-v1.5": 768,
}

class LocalEmbedder(BaseEmbedder):
    """Local embeddings using sentence-transformers."""

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,  # "cpu", "cuda", "mps"
        batch_size: int = 32,
        normalize: bool = True,
    ):
        # Get dimensions (or detect from model)
        dimensions = LOCAL_MODELS.get(model, None)

        super().__init__(model, dimensions or 0)

        self.device = device
        self.batch_size = batch_size
        self.normalize = normalize

        # Lazy model loading
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self._model_name,
                device=self.device,
            )
            # Update dimensions if not known
            if self._dimensions == 0:
                self._dimensions = self._model.get_sentence_embedding_dimension()
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts locally."""
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
        )

        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed a search query.

        Some models have different prefixes for queries vs documents.
        """
        # BGE models use instruction prefix for queries
        if "bge" in self._model_name.lower():
            query = f"Represent this sentence for searching relevant passages: {query}"

        return self.embed_single(query)


class LocalEmbedderGPU(LocalEmbedder):
    """Local embedder optimized for GPU."""

    def __init__(
        self,
        model: str = "BAAI/bge-base-en-v1.5",
        batch_size: int = 64,
        **kwargs
    ):
        import torch
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        super().__init__(model=model, device=device, batch_size=batch_size, **kwargs)
```

### 2.4 Hybrid Embedder (Code vs Prose)

```python
# src/doxstrux/rag/embedders/hybrid_embedder.py

from typing import Optional
from .base import BaseEmbedder
from .openai_embedder import OpenAIEmbedder
from .local_embedder import LocalEmbedder
from ..models import RAGChunk, EmbeddedChunk

class HybridEmbedder:
    """Use different embedding models for code vs prose.

    Technical documentation often has both code and prose.
    Code-optimized embeddings can improve retrieval for code chunks.
    """

    def __init__(
        self,
        prose_embedder: Optional[BaseEmbedder] = None,
        code_embedder: Optional[BaseEmbedder] = None,
    ):
        # Default: OpenAI for prose, local code-optimized for code
        self.prose_embedder = prose_embedder or OpenAIEmbedder(
            model="text-embedding-3-small"
        )
        self.code_embedder = code_embedder or LocalEmbedder(
            model="BAAI/bge-base-en-v1.5"  # Good for code
        )

    def embed_chunks(self, chunks: list[RAGChunk]) -> list[EmbeddedChunk]:
        """Embed chunks using appropriate model based on content."""

        # Separate code and prose chunks
        prose_chunks = []
        code_chunks = []

        for chunk in chunks:
            if chunk.has_code and len(chunk.languages) > 0:
                code_chunks.append(chunk)
            else:
                prose_chunks.append(chunk)

        embedded = []

        # Embed prose chunks
        if prose_chunks:
            prose_texts = [c.normalized_text for c in prose_chunks]
            prose_embeddings = self.prose_embedder.embed(prose_texts)

            for chunk, emb in zip(prose_chunks, prose_embeddings):
                embedded.append(EmbeddedChunk(
                    chunk=chunk,
                    embedding=emb,
                    embedding_model=self.prose_embedder.model_name,
                    embedding_dim=self.prose_embedder.dimensions,
                ))

        # Embed code chunks
        if code_chunks:
            code_texts = [c.normalized_text for c in code_chunks]
            code_embeddings = self.code_embedder.embed(code_texts)

            for chunk, emb in zip(code_chunks, code_embeddings):
                embedded.append(EmbeddedChunk(
                    chunk=chunk,
                    embedding=emb,
                    embedding_model=self.code_embedder.model_name,
                    embedding_dim=self.code_embedder.dimensions,
                ))

        return embedded

    def embed_query(self, query: str, query_type: str = "prose") -> list[float]:
        """Embed a search query.

        Args:
            query: The search query
            query_type: "prose" or "code" to select embedder
        """
        if query_type == "code":
            return self.code_embedder.embed_query(query)
        return self.prose_embedder.embed_query(query)
```

### 2.5 Embedder Factory

```python
# src/doxstrux/rag/embedders/__init__.py

from typing import Optional, Literal
from .base import Embedder, BaseEmbedder
from .openai_embedder import OpenAIEmbedder, OpenAIEmbedderAsync
from .local_embedder import LocalEmbedder, LocalEmbedderGPU
from .hybrid_embedder import HybridEmbedder

EmbedderType = Literal["openai", "local", "local-gpu", "hybrid"]

def create_embedder(
    embedder_type: EmbedderType = "openai",
    model: Optional[str] = None,
    **kwargs
) -> BaseEmbedder | HybridEmbedder:
    """Factory function to create embedders.

    Args:
        embedder_type: Type of embedder ("openai", "local", "local-gpu", "hybrid")
        model: Model name (optional, uses defaults)
        **kwargs: Additional arguments for the embedder

    Returns:
        Configured embedder instance

    Examples:
        # OpenAI (default)
        embedder = create_embedder()

        # OpenAI large model
        embedder = create_embedder("openai", model="text-embedding-3-large")

        # Local (CPU)
        embedder = create_embedder("local")

        # Local (GPU)
        embedder = create_embedder("local-gpu", model="BAAI/bge-large-en-v1.5")

        # Hybrid (different for code vs prose)
        embedder = create_embedder("hybrid")
    """
    if embedder_type == "openai":
        return OpenAIEmbedder(
            model=model or "text-embedding-3-small",
            **kwargs
        )

    elif embedder_type == "local":
        return LocalEmbedder(
            model=model or "all-MiniLM-L6-v2",
            **kwargs
        )

    elif embedder_type == "local-gpu":
        return LocalEmbedderGPU(
            model=model or "BAAI/bge-base-en-v1.5",
            **kwargs
        )

    elif embedder_type == "hybrid":
        return HybridEmbedder(**kwargs)

    else:
        raise ValueError(f"Unknown embedder type: {embedder_type}")


__all__ = [
    "Embedder",
    "BaseEmbedder",
    "OpenAIEmbedder",
    "OpenAIEmbedderAsync",
    "LocalEmbedder",
    "LocalEmbedderGPU",
    "HybridEmbedder",
    "create_embedder",
]
```

---

## 3. Vector Store Interface & Implementations

### 3.1 Base Interface

```python
# src/doxstrux/rag/stores/base.py

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from ..models import EmbeddedChunk

@dataclass
class SearchResult:
    """Single search result."""
    chunk_id: str
    text: str
    score: float              # Similarity score (higher = more similar)
    metadata: dict

    # Optional fields populated by some stores
    embedding: Optional[list[float]] = None


@dataclass
class SearchResults:
    """Collection of search results."""
    results: list[SearchResult]
    query: str
    total_found: int

    def __iter__(self):
        return iter(self.results)

    def __len__(self):
        return len(self.results)

    @property
    def texts(self) -> list[str]:
        return [r.text for r in self.results]

    @property
    def ids(self) -> list[str]:
        return [r.chunk_id for r in self.results]


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add(self, chunks: list[EmbeddedChunk]) -> list[str]:
        """Add embedded chunks to the store.

        Returns:
            List of chunk IDs that were added
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filter_dict: Optional[dict] = None,
    ) -> SearchResults:
        """Search for similar chunks.

        Args:
            query_embedding: Query vector
            k: Number of results to return
            filter_dict: Metadata filters

        Returns:
            SearchResults with matching chunks
        """
        pass

    @abstractmethod
    def delete(self, chunk_ids: list[str]) -> int:
        """Delete chunks by ID.

        Returns:
            Number of chunks deleted
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of chunks in store."""
        pass

    def search_by_text(
        self,
        query: str,
        embedder,
        k: int = 10,
        filter_dict: Optional[dict] = None,
    ) -> SearchResults:
        """Search using text query (convenience method)."""
        query_embedding = embedder.embed_query(query)
        results = self.search(query_embedding, k=k, filter_dict=filter_dict)
        results.query = query
        return results
```

### 3.2 Chroma (Local Development)

```python
# src/doxstrux/rag/stores/chroma_store.py

import os
from typing import Optional
from .base import VectorStore, SearchResult, SearchResults
from ..models import EmbeddedChunk

class ChromaStore(VectorStore):
    """Chroma vector store for local development.

    Features:
    - Persistent storage to disk
    - No external dependencies (embedded)
    - Good for prototyping and small-medium datasets
    """

    def __init__(
        self,
        collection_name: str = "documents",
        persist_dir: str = "./chroma_db",
        distance_metric: str = "cosine",  # "cosine", "l2", "ip"
    ):
        self.collection_name = collection_name
        self.persist_dir = persist_dir

        os.makedirs(persist_dir, exist_ok=True)

        # Lazy initialization
        self._client = None
        self._collection = None
        self._distance_metric = distance_metric

    @property
    def client(self):
        if self._client is None:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self._distance_metric},
            )
        return self._collection

    def add(self, chunks: list[EmbeddedChunk]) -> list[str]:
        """Add embedded chunks to Chroma."""
        if not chunks:
            return []

        ids = [c.id for c in chunks]
        embeddings = [c.embedding for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        # Chroma doesn't like None values in metadata
        clean_metadatas = []
        for meta in metadatas:
            clean = {k: v for k, v in meta.items() if v is not None}
            # Convert bools to strings (Chroma limitation)
            for k, v in clean.items():
                if isinstance(v, bool):
                    clean[k] = str(v)
            clean_metadatas.append(clean)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=clean_metadatas,
        )

        return ids

    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filter_dict: Optional[dict] = None,
    ) -> SearchResults:
        """Search Chroma collection."""

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_dict,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []

        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                # Chroma returns distances, convert to similarity
                distance = results["distances"][0][i]

                # For cosine distance, similarity = 1 - distance
                if self._distance_metric == "cosine":
                    score = 1 - distance
                else:
                    score = -distance  # Lower distance = higher score

                search_results.append(SearchResult(
                    chunk_id=results["ids"][0][i],
                    text=results["documents"][0][i],
                    score=score,
                    metadata=results["metadatas"][0][i],
                ))

        return SearchResults(
            results=search_results,
            query="",
            total_found=len(search_results),
        )

    def delete(self, chunk_ids: list[str]) -> int:
        """Delete chunks by ID."""
        if not chunk_ids:
            return 0

        self.collection.delete(ids=chunk_ids)
        return len(chunk_ids)

    def count(self) -> int:
        """Return total chunks in collection."""
        return self.collection.count()

    def delete_collection(self):
        """Delete entire collection."""
        self.client.delete_collection(self.collection_name)
        self._collection = None

    def get_by_id(self, chunk_id: str) -> Optional[SearchResult]:
        """Get a single chunk by ID."""
        result = self.collection.get(
            ids=[chunk_id],
            include=["documents", "metadatas"],
        )

        if result["ids"]:
            return SearchResult(
                chunk_id=result["ids"][0],
                text=result["documents"][0],
                score=1.0,
                metadata=result["metadatas"][0],
            )
        return None
```

### 3.3 Qdrant (Production Self-Hosted)

```python
# src/doxstrux/rag/stores/qdrant_store.py

from typing import Optional
from .base import VectorStore, SearchResult, SearchResults
from ..models import EmbeddedChunk

class QdrantStore(VectorStore):
    """Qdrant vector store for production workloads.

    Features:
    - High performance
    - Filtering
    - Horizontal scaling
    - Cloud or self-hosted
    """

    def __init__(
        self,
        collection_name: str = "documents",
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
        vector_size: int = 1536,  # OpenAI small default
        distance: str = "Cosine",  # "Cosine", "Euclid", "Dot"
    ):
        self.collection_name = collection_name
        self.url = url
        self.api_key = api_key
        self.vector_size = vector_size
        self.distance = distance

        self._client = None

    @property
    def client(self):
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
            )

            # Ensure collection exists
            self._ensure_collection()

        return self._client

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        from qdrant_client.models import Distance, VectorParams

        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclid": Distance.EUCLID,
                "Dot": Distance.DOT,
            }

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=distance_map[self.distance],
                ),
            )

    def add(self, chunks: list[EmbeddedChunk]) -> list[str]:
        """Add embedded chunks to Qdrant."""
        if not chunks:
            return []

        from qdrant_client.models import PointStruct

        points = []
        for chunk in chunks:
            points.append(PointStruct(
                id=chunk.id,
                vector=chunk.embedding,
                payload={
                    "text": chunk.text,
                    **chunk.metadata,
                },
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return [c.id for c in chunks]

    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filter_dict: Optional[dict] = None,
    ) -> SearchResults:
        """Search Qdrant collection."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # Build filter
        query_filter = None
        if filter_dict:
            conditions = []
            for key, value in filter_dict.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            query_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=k,
            query_filter=query_filter,
        )

        search_results = []
        for hit in results:
            payload = hit.payload or {}
            text = payload.pop("text", "")

            search_results.append(SearchResult(
                chunk_id=hit.id,
                text=text,
                score=hit.score,
                metadata=payload,
            ))

        return SearchResults(
            results=search_results,
            query="",
            total_found=len(search_results),
        )

    def delete(self, chunk_ids: list[str]) -> int:
        """Delete chunks by ID."""
        if not chunk_ids:
            return 0

        from qdrant_client.models import PointIdsList

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=chunk_ids),
        )

        return len(chunk_ids)

    def count(self) -> int:
        """Return total chunks in collection."""
        info = self.client.get_collection(self.collection_name)
        return info.points_count
```

### 3.4 Pinecone (Managed Cloud)

```python
# src/doxstrux/rag/stores/pinecone_store.py

import os
from typing import Optional
from .base import VectorStore, SearchResult, SearchResults
from ..models import EmbeddedChunk

class PineconeStore(VectorStore):
    """Pinecone managed vector store.

    Features:
    - Fully managed (no infrastructure)
    - Serverless option
    - High availability
    - Global distribution
    """

    def __init__(
        self,
        index_name: str = "documents",
        api_key: Optional[str] = None,
        environment: str = "us-east-1",  # or specific region
        namespace: str = "",
        dimension: int = 1536,
    ):
        self.index_name = index_name
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment
        self.namespace = namespace
        self.dimension = dimension

        if not self.api_key:
            raise ValueError("Pinecone API key required")

        self._index = None

    @property
    def index(self):
        if self._index is None:
            from pinecone import Pinecone, ServerlessSpec

            pc = Pinecone(api_key=self.api_key)

            # Create index if doesn't exist
            if self.index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=self.environment,
                    ),
                )

            self._index = pc.Index(self.index_name)

        return self._index

    def add(self, chunks: list[EmbeddedChunk]) -> list[str]:
        """Add embedded chunks to Pinecone."""
        if not chunks:
            return []

        vectors = []
        for chunk in chunks:
            # Pinecone metadata has size limits
            metadata = {k: v for k, v in chunk.metadata.items() if v is not None}
            # Truncate text if too long for metadata
            metadata["text"] = chunk.text[:1000]

            vectors.append({
                "id": chunk.id,
                "values": chunk.embedding,
                "metadata": metadata,
            })

        # Batch upsert (Pinecone limit is 100 vectors per request)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(
                vectors=batch,
                namespace=self.namespace,
            )

        return [c.id for c in chunks]

    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filter_dict: Optional[dict] = None,
    ) -> SearchResults:
        """Search Pinecone index."""

        results = self.index.query(
            vector=query_embedding,
            top_k=k,
            filter=filter_dict,
            include_metadata=True,
            namespace=self.namespace,
        )

        search_results = []
        for match in results.matches:
            metadata = match.metadata or {}
            text = metadata.pop("text", "")

            search_results.append(SearchResult(
                chunk_id=match.id,
                text=text,
                score=match.score,
                metadata=metadata,
            ))

        return SearchResults(
            results=search_results,
            query="",
            total_found=len(search_results),
        )

    def delete(self, chunk_ids: list[str]) -> int:
        """Delete chunks by ID."""
        if not chunk_ids:
            return 0

        self.index.delete(
            ids=chunk_ids,
            namespace=self.namespace,
        )

        return len(chunk_ids)

    def count(self) -> int:
        """Return total chunks in index."""
        stats = self.index.describe_index_stats()
        if self.namespace:
            return stats.namespaces.get(self.namespace, {}).get("vector_count", 0)
        return stats.total_vector_count
```

### 3.5 pgvector (PostgreSQL)

```python
# src/doxstrux/rag/stores/pgvector_store.py

from typing import Optional
from .base import VectorStore, SearchResult, SearchResults
from ..models import EmbeddedChunk

class PgVectorStore(VectorStore):
    """PostgreSQL with pgvector extension.

    Features:
    - Use existing PostgreSQL infrastructure
    - Full SQL capabilities
    - ACID transactions
    - Join with other tables
    """

    def __init__(
        self,
        connection_string: str,
        table_name: str = "document_chunks",
        dimension: int = 1536,
    ):
        self.connection_string = connection_string
        self.table_name = table_name
        self.dimension = dimension

        self._engine = None
        self._ensure_table()

    @property
    def engine(self):
        if self._engine is None:
            from sqlalchemy import create_engine
            self._engine = create_engine(self.connection_string)
        return self._engine

    def _ensure_table(self):
        """Create table if it doesn't exist."""
        from sqlalchemy import text

        with self.engine.connect() as conn:
            # Enable pgvector extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            # Create table
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding vector({self.dimension}) NOT NULL,
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create index for similarity search
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                ON {self.table_name}
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))

            conn.commit()

    def add(self, chunks: list[EmbeddedChunk]) -> list[str]:
        """Add embedded chunks to PostgreSQL."""
        if not chunks:
            return []

        from sqlalchemy import text
        import json

        with self.engine.connect() as conn:
            for chunk in chunks:
                conn.execute(
                    text(f"""
                        INSERT INTO {self.table_name} (id, text, embedding, metadata)
                        VALUES (:id, :text, :embedding, :metadata)
                        ON CONFLICT (id) DO UPDATE SET
                            text = EXCLUDED.text,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                    """),
                    {
                        "id": chunk.id,
                        "text": chunk.text,
                        "embedding": str(chunk.embedding),
                        "metadata": json.dumps(chunk.metadata),
                    }
                )
            conn.commit()

        return [c.id for c in chunks]

    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filter_dict: Optional[dict] = None,
    ) -> SearchResults:
        """Search using pgvector similarity."""
        from sqlalchemy import text

        # Build filter clause
        filter_clause = ""
        params = {"embedding": str(query_embedding), "k": k}

        if filter_dict:
            conditions = []
            for i, (key, value) in enumerate(filter_dict.items()):
                param_name = f"filter_{i}"
                conditions.append(f"metadata->>'{key}' = :{param_name}")
                params[param_name] = str(value)
            filter_clause = "WHERE " + " AND ".join(conditions)

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"""
                    SELECT
                        id,
                        text,
                        metadata,
                        1 - (embedding <=> :embedding) as score
                    FROM {self.table_name}
                    {filter_clause}
                    ORDER BY embedding <=> :embedding
                    LIMIT :k
                """),
                params
            )

            search_results = []
            for row in result:
                search_results.append(SearchResult(
                    chunk_id=row.id,
                    text=row.text,
                    score=float(row.score),
                    metadata=row.metadata,
                ))

        return SearchResults(
            results=search_results,
            query="",
            total_found=len(search_results),
        )

    def delete(self, chunk_ids: list[str]) -> int:
        """Delete chunks by ID."""
        if not chunk_ids:
            return 0

        from sqlalchemy import text

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"DELETE FROM {self.table_name} WHERE id = ANY(:ids)"),
                {"ids": chunk_ids}
            )
            conn.commit()
            return result.rowcount

    def count(self) -> int:
        """Return total chunks in table."""
        from sqlalchemy import text

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {self.table_name}")
            )
            return result.scalar()
```

### 3.6 Vector Store Factory

```python
# src/doxstrux/rag/stores/__init__.py

from typing import Optional, Literal
from .base import VectorStore, SearchResult, SearchResults
from .chroma_store import ChromaStore
from .qdrant_store import QdrantStore
from .pinecone_store import PineconeStore
from .pgvector_store import PgVectorStore

StoreType = Literal["chroma", "qdrant", "pinecone", "pgvector"]

def create_store(
    store_type: StoreType = "chroma",
    collection_name: str = "documents",
    **kwargs
) -> VectorStore:
    """Factory function to create vector stores.

    Args:
        store_type: Type of store ("chroma", "qdrant", "pinecone", "pgvector")
        collection_name: Name of collection/index
        **kwargs: Store-specific arguments

    Returns:
        Configured vector store instance

    Examples:
        # Chroma (local development)
        store = create_store("chroma", persist_dir="./db")

        # Qdrant (production)
        store = create_store("qdrant", url="http://localhost:6333")

        # Pinecone (cloud)
        store = create_store("pinecone", api_key="...")

        # pgvector (PostgreSQL)
        store = create_store("pgvector", connection_string="postgresql://...")
    """
    if store_type == "chroma":
        return ChromaStore(collection_name=collection_name, **kwargs)

    elif store_type == "qdrant":
        return QdrantStore(collection_name=collection_name, **kwargs)

    elif store_type == "pinecone":
        return PineconeStore(index_name=collection_name, **kwargs)

    elif store_type == "pgvector":
        return PgVectorStore(table_name=collection_name, **kwargs)

    else:
        raise ValueError(f"Unknown store type: {store_type}")


__all__ = [
    "VectorStore",
    "SearchResult",
    "SearchResults",
    "ChromaStore",
    "QdrantStore",
    "PineconeStore",
    "PgVectorStore",
    "create_store",
]
```

---

## 4. Unified RAG Pipeline

Tie everything together:

```python
# src/doxstrux/rag/pipeline.py

from dataclasses import dataclass
from typing import Optional, Literal
import logging

from .models import RAGChunk, EmbeddedChunk
from .embedders import create_embedder, Embedder
from .stores import create_store, VectorStore, SearchResults

logger = logging.getLogger(__name__)

@dataclass
class RAGPipelineConfig:
    # Embedder
    embedder_type: Literal["openai", "local", "local-gpu", "hybrid"] = "openai"
    embedding_model: Optional[str] = None

    # Store
    store_type: Literal["chroma", "qdrant", "pinecone", "pgvector"] = "chroma"
    collection_name: str = "documents"
    persist_dir: str = "./vector_db"

    # Store-specific
    store_url: Optional[str] = None
    store_api_key: Optional[str] = None

    # Processing
    batch_size: int = 100


class RAGPipeline:
    """Unified pipeline for embedding and storing chunks."""

    def __init__(self, config: RAGPipelineConfig):
        self.config = config

        # Initialize embedder
        self.embedder = create_embedder(
            embedder_type=config.embedder_type,
            model=config.embedding_model,
        )

        # Initialize store
        store_kwargs = {
            "collection_name": config.collection_name,
        }

        if config.store_type == "chroma":
            store_kwargs["persist_dir"] = config.persist_dir
        elif config.store_type == "qdrant":
            store_kwargs["url"] = config.store_url or "http://localhost:6333"
            store_kwargs["vector_size"] = self.embedder.dimensions
        elif config.store_type == "pinecone":
            store_kwargs["api_key"] = config.store_api_key
            store_kwargs["dimension"] = self.embedder.dimensions
        elif config.store_type == "pgvector":
            store_kwargs["connection_string"] = config.store_url
            store_kwargs["dimension"] = self.embedder.dimensions

        self.store = create_store(config.store_type, **store_kwargs)

    def embed_and_store(self, chunks: list[RAGChunk]) -> dict:
        """Embed chunks and store in vector database.

        Returns:
            Stats dict with counts
        """
        stats = {
            "chunks_received": len(chunks),
            "chunks_embedded": 0,
            "chunks_stored": 0,
            "errors": [],
        }

        if not chunks:
            return stats

        try:
            # Embed
            logger.info(f"Embedding {len(chunks)} chunks...")
            texts = [c.normalized_text for c in chunks]
            embeddings = self.embedder.embed(texts)

            # Create embedded chunks
            embedded_chunks = []
            for chunk, embedding in zip(chunks, embeddings):
                embedded_chunks.append(EmbeddedChunk(
                    chunk=chunk,
                    embedding=embedding,
                    embedding_model=self.embedder.model_name,
                    embedding_dim=self.embedder.dimensions,
                ))

            stats["chunks_embedded"] = len(embedded_chunks)

            # Store in batches
            logger.info(f"Storing {len(embedded_chunks)} chunks...")
            stored_ids = self.store.add(embedded_chunks)
            stats["chunks_stored"] = len(stored_ids)

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            stats["errors"].append(str(e))

        return stats

    def search(
        self,
        query: str,
        k: int = 10,
        filter_dict: Optional[dict] = None,
    ) -> SearchResults:
        """Search for similar chunks."""
        return self.store.search_by_text(
            query=query,
            embedder=self.embedder,
            k=k,
            filter_dict=filter_dict,
        )

    def delete_by_source(self, source_path: str) -> int:
        """Delete all chunks from a specific source."""
        # This requires store-specific implementation
        # For now, search and delete
        results = self.store.search_by_text(
            query="",
            embedder=self.embedder,
            k=10000,
            filter_dict={"source_path": source_path},
        )

        if results.ids:
            return self.store.delete(results.ids)
        return 0

    @property
    def count(self) -> int:
        """Return total chunks in store."""
        return self.store.count()


# Convenience function
def create_rag_pipeline(
    embedder_type: str = "openai",
    store_type: str = "chroma",
    collection_name: str = "documents",
    **kwargs
) -> RAGPipeline:
    """Create a RAG pipeline with sensible defaults.

    Examples:
        # Local development
        pipeline = create_rag_pipeline()

        # Production with Qdrant
        pipeline = create_rag_pipeline(
            embedder_type="openai",
            store_type="qdrant",
            store_url="http://qdrant:6333",
        )

        # Local embeddings + pgvector
        pipeline = create_rag_pipeline(
            embedder_type="local-gpu",
            store_type="pgvector",
            store_url="postgresql://user:pass@localhost/db",
        )
    """
    config = RAGPipelineConfig(
        embedder_type=embedder_type,
        store_type=store_type,
        collection_name=collection_name,
        **kwargs
    )
    return RAGPipeline(config)
```

---

## 5. Usage Examples

### 5.1 Basic Usage

```python
from doxstrux.rag import create_rag_pipeline, RAGChunk

# Create pipeline (defaults: OpenAI + Chroma)
pipeline = create_rag_pipeline(collection_name="my_docs")

# Create chunks (from your parser/chunker)
chunks = [
    RAGChunk(
        chunk_id="doc1_chunk1",
        text="This is the first chunk of text.",
        normalized_text="this is the first chunk of text",
        source_type="markdown",
        source_path="/docs/intro.md",
        source_title="Introduction",
        section_path=["intro"],
        section_title="Introduction",
        token_estimate=10,
    ),
    # ... more chunks
]

# Embed and store
stats = pipeline.embed_and_store(chunks)
print(f"Stored {stats['chunks_stored']} chunks")

# Search
results = pipeline.search("how to get started", k=5)
for result in results:
    print(f"[{result.score:.3f}] {result.text[:100]}...")
```

### 5.2 Integration with Parser

```python
from doxstrux import parse_markdown_file
from doxstrux.chunker import chunk_document, ChunkPolicy
from doxstrux.rag import create_rag_pipeline, RAGChunk

def process_document(file_path: str, pipeline):
    """Process a markdown file through the full pipeline."""

    # Parse
    parsed = parse_markdown_file(file_path, security_profile="strict")

    # Check security
    if parsed["metadata"].get("embedding_blocked"):
        raise ValueError(f"Document blocked: {parsed['metadata'].get('embedding_block_reason')}")

    # Chunk
    policy = ChunkPolicy(mode="semantic", target_tokens=500)
    chunk_result = chunk_document(parsed, policy)

    # Convert to RAGChunk
    rag_chunks = []
    for chunk in chunk_result.chunks:
        rag_chunks.append(RAGChunk(
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            normalized_text=chunk.normalized_text,
            source_type="markdown",
            source_path=file_path,
            source_title=parsed["metadata"].get("title", ""),
            section_path=chunk.section_path,
            section_title=chunk.meta.get("title", ""),
            char_span=chunk.span,
            line_span=chunk.line_span,
            token_estimate=chunk.token_estimate,
            has_code=chunk.meta.get("has_code", False),
            risk_flags=chunk.risk_flags,
        ))

    # Embed and store
    stats = pipeline.embed_and_store(rag_chunks)
    return stats

# Usage
pipeline = create_rag_pipeline()

for doc in ["doc1.md", "doc2.md", "doc3.md"]:
    stats = process_document(doc, pipeline)
    print(f"{doc}: {stats['chunks_stored']} chunks")

# Search
results = pipeline.search("authentication")
```

### 5.3 Production Setup

```python
from doxstrux.rag import create_rag_pipeline
import os

# Production configuration
pipeline = create_rag_pipeline(
    # OpenAI embeddings (or use "local-gpu" for self-hosted)
    embedder_type="openai",
    embedding_model="text-embedding-3-large",  # Higher quality

    # Qdrant for production
    store_type="qdrant",
    store_url=os.getenv("QDRANT_URL", "http://qdrant:6333"),

    collection_name="production_docs",
)

# Or with Pinecone
pipeline = create_rag_pipeline(
    embedder_type="openai",
    store_type="pinecone",
    store_api_key=os.getenv("PINECONE_API_KEY"),
    collection_name="production_docs",
)
```

---

## 6. Summary

### Components Created

| Component | Purpose | Options |
|-----------|---------|---------|
| **RAGChunk** | Universal chunk format | All metadata fields |
| **EmbeddedChunk** | Chunk + embedding | Includes model info |
| **OpenAIEmbedder** | OpenAI API embeddings | 3-small, 3-large, ada-002 |
| **LocalEmbedder** | sentence-transformers | MiniLM, BGE, mpnet |
| **HybridEmbedder** | Code vs prose routing | Configurable |
| **ChromaStore** | Local development | Persistent, embedded |
| **QdrantStore** | Production self-hosted | High performance |
| **PineconeStore** | Managed cloud | Serverless |
| **PgVectorStore** | PostgreSQL integration | SQL capabilities |
| **RAGPipeline** | Unified interface | Embed + store + search |

### Decision Matrix

| Use Case | Embedder | Store |
|----------|----------|-------|
| **Development** | local | chroma |
| **Production (cost-sensitive)** | local-gpu | qdrant |
| **Production (quality-focused)** | openai | qdrant/pinecone |
| **Existing PostgreSQL** | openai/local | pgvector |
| **Technical docs (code)** | hybrid | any |
| **Serverless** | openai | pinecone |

### Integration Points

All pipelines (HTML, PDF, Web Crawler) produce `RAGChunk` objects:

```
┌─────────────────┐
│  HTML Pipeline  │───┐
└─────────────────┘   │
                      │
┌─────────────────┐   │    ┌─────────────┐    ┌─────────────┐
│   PDF Pipeline  │───┼───▶│  RAGChunk   │───▶│ RAGPipeline │
└─────────────────┘   │    └─────────────┘    └─────────────┘
                      │                              │
┌─────────────────┐   │                              ▼
│ Crawler Pipeline│───┘                       ┌─────────────┐
└─────────────────┘                           │Vector Store │
                                              └─────────────┘
```
