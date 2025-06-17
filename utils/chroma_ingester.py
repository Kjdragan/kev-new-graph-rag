"""ChromaDB integration for vector storage in kev-graph-rag."""

import os
import asyncio
from typing import Dict, List, Optional, Any, Union, Sequence

import chromadb
from chromadb.api.models import Collection
from chromadb.api.types import QueryResult
from loguru import logger
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config_models import ChromaDBConfig
from .embedding import CustomGeminiEmbedding

# Import truncate_embedding function
try:
    from src.graph_extraction.gemini_embedder import truncate_embedding
except ImportError:
    # Define fallback truncate_embedding function if import fails
    def truncate_embedding(embedding, max_length=100):
        """Truncate embedding vector representation for readability in logs."""
        embedding_str = str(embedding)
        if len(embedding_str) <= max_length:
            return embedding_str
        return embedding_str[:max_length] + '...'


class ChromaIngester:
    """Handles document ingestion into ChromaDB using an async client."""

    def __init__(self, config: ChromaDBConfig, embedding_model: CustomGeminiEmbedding):
        """Initialize the ChromaDB ingester.
        
        Note: This only sets up configuration. Call `async_init()` to establish
        a connection.
        
        Args:
            config: Configuration for ChromaDB connection
            embedding_model: The embedding model to use
        """
        self.config = config
        self.embedding_model = embedding_model
        self.client: Optional[chromadb.AsyncClientAPI] = None
        self.collection: Optional[Collection] = None

    async def async_init(self):
        """
        Asynchronously initializes the ChromaDB client and gets/creates the collection.
        This method is idempotent and can be called multiple times.
        """
        if self.collection:
            return

        logger.info("Initializing ChromaDB async client and collection...")
        try:
            # 1. Initialize Client
            if self.config.auth_enabled:
                settings = chromadb.Settings(
                    chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                    chroma_client_auth_credentials=f"{self.config.username}:{self.config.password}"
                )
                self.client = await chromadb.AsyncHttpClient(
                    host=self.config.host, port=self.config.port, settings=settings
                )
            else:
                self.client = await chromadb.AsyncHttpClient(host=self.config.host, port=self.config.port)
            
            logger.info(f"ChromaDB async client created for host {self.config.host}:{self.config.port}")

            # 2. Get or Create Collection
            self.collection = await self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={
                    "description": "Document collection for kev-graph-rag",
                    "embedding_dimension": str(self.embedding_model._gemini_config.get("output_dimensionality", 1024)),
                    "similarity": "cosine"
                },
                embedding_function=None
            )
            logger.success(f"Successfully got or created ChromaDB collection: '{self.config.collection_name}'")

        except Exception as e:
            logger.error(f"Failed during ChromaDB async initialization: {e}", exc_info=True)
            # Reset state on failure
            self.client = None
            self.collection = None
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((chromadb.errors.ChromaError))
    )
    async def ingest_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Asynchronously ingest documents into ChromaDB."""
        if not self.collection:
            raise RuntimeError("ChromaIngester not initialized. Call async_init() before using.")

        try:
            texts = [doc['document'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]
            ids = [doc['id'] for doc in documents]

            embeddings = await self.batch_embed_documents(texts)
            
            await self.collection.upsert(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully ingested {len(documents)} documents into ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Failed to ingest documents into ChromaDB: {e}")
            raise

    async def batch_embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Asynchronously batch embed multiple texts for efficiency."""
        batch_size = 10
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            # Use the async embedding method
            embedding_tasks = [self.embedding_model._aget_text_embedding(text) for text in batch_texts]
            batch_embeddings = await asyncio.gather(*embedding_tasks)
            all_embeddings.extend(batch_embeddings)
            
            if batch_embeddings:
                sample_embedding = batch_embeddings[0]
                logger.debug(f"Batch embedding sample (truncated): {truncate_embedding(sample_embedding)}")
        
        return all_embeddings

    async def add_documents(self, documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> bool:
        """Asynchronously add documents to the collection."""
        if not self.collection:
            raise RuntimeError("ChromaIngester not initialized. Call async_init() before using.")
        try:
            embeddings = await self.batch_embed_documents(documents)
            
            await self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"Successfully added {len(documents)} documents to ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise

    async def count_documents(self) -> int:
        """Asynchronously get the number of documents in the collection."""
        if not self.collection:
            raise RuntimeError("ChromaIngester not initialized. Call async_init() before using.")
        try:
            return await self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0

    async def search(self, query: str, n_results: int = 5, filters: Optional[Dict[str, Any]] = None, include_embeddings: bool = False) -> QueryResult:
        """Asynchronously search documents by vector similarity."""
        if not self.collection:
            raise RuntimeError("ChromaIngester not initialized. Call async_init() before using.")
            
        query_embedding = await self.embedding_model._aget_text_embedding(query)
        logger.debug(f"Search query embedding (truncated): {truncate_embedding(query_embedding)}")
        
        include = ["documents", "metadatas", "distances"]
        if include_embeddings:
            include.append("embeddings")
        
        results = await self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters,
            include=include
        )
        
        return results
