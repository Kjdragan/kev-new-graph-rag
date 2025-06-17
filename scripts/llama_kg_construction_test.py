"""
Llama-Index Knowledge Graph Construction Test

This script demonstrates the construction of a knowledge graph using Llama-Index,
Neo4jGraphStore, and Gemini. It creates a graph from sample documents and verifies
the structure in Neo4j.

Task 1.4 from the master build plan.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to sys.path to enable imports from project modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import required libraries
from dotenv import load_dotenv
from llama_index.core import Document, Settings
from llama_index.core.indices.knowledge_graph import KnowledgeGraphIndex
from llama_index.core.storage.storage_context import StorageContext
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# Import utils for configuration
from utils.config import get_config


def load_environment_variables() -> Dict[str, str]:
    """
    Load environment variables from .env file
    """
    dotenv_path = os.path.join(project_root, "src", ".env")
    if not os.path.exists(dotenv_path):
        raise FileNotFoundError(f".env file not found at {dotenv_path}")
    
    load_dotenv(dotenv_path)
    
    required_vars = [
        "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "GOOGLE_API_KEY"
    ]
    
    env_vars = {}
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            raise ValueError(f"Required environment variable {var} is missing")
        env_vars[var] = value
    
    return env_vars


def create_sample_documents() -> List[Document]:
    """
    Create sample documents for testing knowledge graph construction
    """
    texts = [
        """
        Kevin Smith is a software engineer at Acme Technologies. 
        He specializes in machine learning and natural language processing.
        Kevin graduated from Stanford University in 2019 with a degree in Computer Science.
        He worked on several projects involving knowledge graphs and semantic search.
        Kevin is currently working on a Graph RAG system that uses Neo4j and Graphiti.
        """,
        
        """
        Acme Technologies is a tech company founded in 2015.
        The company focuses on AI-driven solutions for enterprise clients.
        Acme's headquarters is located in San Francisco, California.
        The company has about 250 employees across offices in San Francisco, New York, and London.
        Their flagship product is AcmeAI, a platform for building intelligent applications.
        """,
        
        """
        Knowledge graphs are structured representations of facts and their semantic relationships.
        They are used in various applications including search engines, recommendation systems, and AI assistants.
        Neo4j is a popular graph database that enables efficient storage and querying of graph data.
        Graphiti is a library that helps build temporal knowledge graphs for AI agents.
        Graph RAG (Retrieval Augmented Generation) systems combine knowledge graphs with large language models.
        """
    ]
    
    return [Document(text=text) for text in texts]


def setup_llama_index_with_neo4j(env_vars: Dict[str, str]) -> Dict[str, Any]:
    """
    Set up Llama-Index with Neo4j and Gemini
    """
    print("Setting up Llama-Index with Neo4j and Gemini...")
    
    # Get model name from config
    config = get_config()
    gemini_model_id = config.get("models", {}).get("gemini_pro", "gemini-2.5-pro")
    
    # Configure Google GenAI LLM
    llm = GoogleGenAI(
        api_key=env_vars["GOOGLE_API_KEY"],
        model=gemini_model_id,
        temperature=0.0
    )
    
    # Initialize the Llama-Index Google GenAI embedding model
    embedding_model_id = config.get("gemini.embeddings.model_id", "embedding-001")
    embed_model = GoogleGenAIEmbedding(
        api_key=env_vars["GOOGLE_API_KEY"],
        model_name=embedding_model_id
    )
    
    # Set up Neo4j graph store
    graph_store = Neo4jGraphStore(
        url=env_vars["NEO4J_URI"],
        username=env_vars["NEO4J_USER"],
        password=env_vars["NEO4J_PASSWORD"],
        database="neo4j",  # Default database name
        node_label_key="entity_type"
    )
    
    # Create storage context
    storage_context = StorageContext.from_defaults(graph_store=graph_store)
    
    # Configure Llama-Index settings
    Settings.llm = llm
    Settings.embed_model = embed_model
    
    return {
        "llm": llm,
        "embed_model": embed_model,
        "graph_store": graph_store,
        "storage_context": storage_context
    }


def build_knowledge_graph(components: Dict[str, Any], documents: List[Document]) -> KnowledgeGraphIndex:
    """
    Build a knowledge graph from documents using Llama-Index
    """
    print("Building Knowledge Graph from documents...")
    
    # Create KnowledgeGraphIndex with documents
    kg_index = KnowledgeGraphIndex.from_documents(
        documents,
        storage_context=components["storage_context"],
        max_triplets_per_chunk=10,
        include_embeddings=True,  # Enable hybrid search capabilities
        show_progress=True
    )
    
    print("Knowledge Graph construction completed")
    return kg_index


def verify_knowledge_graph(components: Dict[str, Any]) -> None:
    """
    Verify the structure of the knowledge graph in Neo4j
    """
    print("Verifying Knowledge Graph structure in Neo4j...")
    
    # Get Neo4j graph store
    graph_store = components["graph_store"]
    
    # Query for nodes
    nodes_query = "MATCH (n) RETURN count(n) as node_count"
    node_count = graph_store.query(nodes_query)[0]["node_count"]
    print(f"Number of nodes in Knowledge Graph: {node_count}")
    
    # Query for relationships
    rels_query = "MATCH ()-[r]->() RETURN count(r) as rel_count"
    rel_count = graph_store.query(rels_query)[0]["rel_count"]
    print(f"Number of relationships in Knowledge Graph: {rel_count}")
    
    # Query for distinct node labels
    labels_query = "MATCH (n) RETURN DISTINCT labels(n) as labels"
    labels_result = graph_store.query(labels_query)
    node_labels = [label for result in labels_result for label in result["labels"]]
    print(f"Node labels in Knowledge Graph: {', '.join(set(node_labels))}")
    
    # Query for distinct relationship types
    rel_types_query = "MATCH ()-[r]->() RETURN DISTINCT type(r) as rel_type"
    rel_types_result = graph_store.query(rel_types_query)
    rel_types = [result["rel_type"] for result in rel_types_result]
    print(f"Relationship types in Knowledge Graph: {', '.join(set(rel_types))}")
    
    # Sample node information
    sample_node_query = "MATCH (n) RETURN n LIMIT 1"
    sample_nodes = graph_store.query(sample_node_query)
    if sample_nodes:
        print("\nSample Node Properties:")
        for key, value in sample_nodes[0]["n"].items():
            print(f"  {key}: {value}")
    
    print("\nKnowledge Graph verification completed")


def main() -> None:
    """
    Main function to test Llama-Index Knowledge Graph construction with Neo4j
    """
    print("Starting Llama-Index Knowledge Graph Construction Test...")
    
    try:
        # Load environment variables
        print("Loading environment variables...")
        env_vars = load_environment_variables()
        
        # Create sample documents
        print("Creating sample documents...")
        documents = create_sample_documents()
        print(f"Created {len(documents)} sample documents")
        
        # Set up Llama-Index with Neo4j and Gemini
        components = setup_llama_index_with_neo4j(env_vars)
        
        # Build knowledge graph
        kg_index = build_knowledge_graph(components, documents)
        
        # Verify knowledge graph structure
        verify_knowledge_graph(components)
        
        print("\nLlama-Index Knowledge Graph Construction Test completed successfully!")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
