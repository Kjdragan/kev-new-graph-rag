"""
Document Utilities

This module provides functions for loading and processing documents
for the Graph RAG system.
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

def load_sample_documents(data_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load sample documents from the data directory.
    
    Args:
        data_dir: Path to the data directory. If None, uses default path.
        
    Returns:
        List of document dictionaries with text content and metadata
    """
    # Default to project's data directory if none provided
    if data_dir is None:
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "data" / "samples"
    else:
        data_dir = Path(data_dir)
    
    # Ensure data directory exists
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample documents if directory is empty
        _create_sample_documents(data_dir)
    
    documents = []
    
    # Load all text files from data directory
    for file_path in data_dir.glob("*.txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Create document dictionary
            document = {
                "id": file_path.stem,
                "text": content,
                "metadata": {
                    "source": str(file_path.name),
                    "type": "text",
                    "created": file_path.stat().st_ctime
                }
            }
            
            documents.append(document)
        except Exception as e:
            print(f"Error loading document {file_path}: {e}")
    
    print(f"Loaded {len(documents)} documents from {data_dir}")
    return documents

def _create_sample_documents(data_dir: Path) -> None:
    """
    Create sample documents for testing.
    
    Args:
        data_dir: Directory to create sample documents in
    """
    samples = [
        {
            "filename": "graph_rag.txt",
            "content": """
            Graph-based RAG (Retrieval Augmented Generation) combines knowledge graphs with traditional 
            vector search for more comprehensive information retrieval. Unlike standard RAG systems that 
            rely solely on embedding similarity, graph-based RAG leverages the structured relationships 
            between entities to provide more accurate and contextual information retrieval.
            
            Key benefits of graph-based RAG include:
            1. Relationship awareness: Understanding connections between entities
            2. Structured reasoning: Following logical paths through the knowledge graph
            3. Better factual grounding: Explicit relationship representation reduces hallucination
            4. Enhanced context: Leveraging both graph structure and semantic content
            
            The Kevin-Graph-RAG project implements a hybrid search approach that combines Neo4j knowledge 
            graphs with vector embeddings from Google's generative AI models. This combination provides 
            both structured relationship traversal and semantic similarity search for comprehensive 
            question answering.
            """
        },
        {
            "filename": "kevin_smith.txt",
            "content": """
            Kevin Smith is a software engineer specializing in knowledge graphs and natural language 
            processing. He currently works at Acme Technologies where he leads the Graph Database 
            Solutions team. Kevin has published several papers on the integration of knowledge graphs 
            with large language models and has contributed to open-source projects in the RAG space.
            
            Kevin's current project, Kevin-Graph-RAG, focuses on implementing hybrid search capabilities 
            that combine knowledge graph traversal with vector similarity search. The project uses 
            Graphiti for temporal knowledge graphs, Neo4j AuraDB as the persistent graph store, 
            Llama-Index for knowledge graph construction and querying, and Google Gemini Pro for reasoning.
            
            Prior to joining Acme Technologies, Kevin worked at DataGraph Inc. where he helped develop 
            graph-based solutions for financial services clients.
            """
        },
        {
            "filename": "hybrid_search.txt",
            "content": """
            Hybrid search in the context of RAG systems refers to combining multiple retrieval methods to 
            enhance the quality and relevance of retrieved information. The primary hybrid approach in 
            the Kevin-Graph-RAG project combines knowledge graph traversal with vector similarity search.
            
            The hybrid search process works as follows:
            1. Query Analysis: The input query is analyzed to extract entities, relationships, and semantic meaning
            2. Graph Traversal: The knowledge graph is queried using the extracted entities and relationships
            3. Vector Search: In parallel, vector embeddings are used to find semantically similar content
            4. Result Combination: Results from both approaches are combined based on relevance
            5. Response Generation: An LLM synthesizes a final response using the combined information
            
            This hybrid approach overcomes limitations of either method alone:
            - Graph traversal provides precise relationship information but may miss content without explicit connections
            - Vector search provides semantic similarity but lacks structured relationship understanding
            - Combined, they offer both precision and recall for comprehensive information retrieval
            
            The implementation uses Neo4j for graph operations and Google's Generative AI models for embeddings and reasoning.
            """
        }
    ]
    
    for sample in samples:
        file_path = data_dir / sample["filename"]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sample["content"])
    
    print(f"Created {len(samples)} sample documents in {data_dir}")
