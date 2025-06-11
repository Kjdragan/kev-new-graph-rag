"""ChromaDB integration for vector storage in kev-graph-rag."""

import os
from typing import Dict, List, Optional, Any, Union, Sequence

import chromadb
from chromadb.api.models import Collection
from chromadb.api.types import QueryResult
from loguru import logger
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config_models import ChromaDBConfig
from .embedding import CustomGeminiEmbedding


class ChromaIngester:
    """Handles document ingestion into ChromaDB."""

    def __init__(self, config: ChromaDBConfig, embedding_model: CustomGeminiEmbedding):
        """Initialize the ChromaDB ingester.
        
        Args:
            config: Configuration for ChromaDB connection
            embedding_model: The embedding model to use
        """
        self.config = config
        self.embedding_model = embedding_model
        self.client = self._init_client()
        self.collection = self._get_or_create_collection()

    def _init_client(self):
        """Initialize the ChromaDB client with latest API."""
        try:
            # Modern auth approach for ChromaDB
            auth_credentials = None
            if self.config.auth_enabled:
                auth_credentials = {
                    "username": self.config.username,
                    "password": self.config.password
                }
            
            return chromadb.HttpClient(
                host=self.config.host,
                port=self.config.port,
                auth_credentials=auth_credentials if self.config.auth_enabled else None
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise

    def _get_or_create_collection(self) -> Collection:
        """Get or create the collection for document storage."""
        try:
            # Modern collection creation with metadata options
            return self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={
                    "description": "Document collection for kev-graph-rag",
                    "embedding_dimension": self.embedding_model.config.dimensions,
                    "similarity": "cosine"  # Using cosine for Gemini embeddings
                },
                # Create collection with optimized indexing settings
                embedding_function=None,  # We'll handle embeddings manually
                tenant="default",
                database="default"
            )
        except Exception as e:
            logger.error(f"Failed to get/create collection: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((chromadb.errors.ChromaError))
    )
    def ingest_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Ingest documents into ChromaDB.
        
        Args:
            documents: List of document dictionaries with fields:
                - id: Unique document ID
                - text: Document text content
                - metadata: Dictionary of metadata about the document
                
        Returns:
            bool: True if ingestion successful
        """
        try:
            # Batch process documents
            ids = [doc["id"] for doc in documents]
            texts = [doc["text"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            # Generate embeddings using the Gemini model - batched for efficiency
            embeddings = self.batch_embed_documents(texts)
            
            # Using latest upsert semantics and batch processing
            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully ingested {len(documents)} documents into ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest documents into ChromaDB: {e}")
            raise

    def batch_embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch embed multiple texts for efficiency.
        
        Args:
            texts: List of text documents to embed
            
        Returns:
            List of embedding vectors
        """
        # Process in batches of 10 for API efficiency
        batch_size = 10
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = [self.embedding_model._get_text_embedding(text) for text in batch_texts]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
            
    def search(self, 
               query: str, 
               n_results: int = 5, 
               filters: Optional[Dict[str, Any]] = None,
               include_embeddings: bool = False) -> QueryResult:
        """Search documents by vector similarity using modern API.
        
        Args:
            query: The search query
            n_results: Number of results to return
            filters: Optional metadata filters using ChromaDB where syntax
            include_embeddings: Whether to include embeddings in results
            
        Returns:
            QueryResult with matching documents, metadata and distances
        """
        query_embedding = self.embedding_model._get_text_embedding(query)
        
        include = ["documents", "metadatas", "distances"]
        if include_embeddings:
            include.append("embeddings")
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters,
            include=include
        )
        
        return results
