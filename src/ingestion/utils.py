# src/ingestion/utils.py
# Utility functions for the ingestion pipeline.

from typing import List
from llama_index.core.schema import Document as LlamaDocument
from utils.chroma_ingester import ChromaDocument

def convert_llama_docs_to_chroma_docs(
    llama_docs: List[LlamaDocument],
    source_document_id: str,
    source_file_name: str
) -> List[ChromaDocument]:
    """Converts a list of LlamaIndex Document objects to ChromaDocument models.

    Args:
        llama_docs: The list of documents from LlamaParse.
        source_document_id: The unique ID of the source document (e.g., GDrive file ID).
        source_file_name: The original filename of the source document.

    Returns:
        A list of ChromaDocument objects ready for ingestion.
    """
    chroma_docs = []
    for doc in llama_docs:
        # Create a unique ID for each chunk by combining source ID and the chunk's ID
        chunk_id = f"{source_document_id}_{doc.id_}"
        
        # Combine metadata
        metadata = {
            "source_document_id": source_document_id,
            "source_file_name": source_file_name,
            **doc.metadata
        }
        
        chroma_docs.append(
            ChromaDocument(
                text=doc.text,
                document_id=chunk_id,
                metadata=metadata
            )
        )
    return chroma_docs
