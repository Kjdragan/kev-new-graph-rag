"""
Hybrid Search Implementation for Graph RAG

This script implements hybrid search capabilities for the Graph RAG system,
combining knowledge graph traversal with vector similarity search for more
accurate and contextually relevant results.

Building on the knowledge graph constructed with Llama-Index, this script:
1. Sets up multiple retrieval mechanisms (entity, keyword, vector-based)
2. Combines them into a single query engine pipeline
3. Demonstrates RAG with both structural and semantic understanding
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the parent directory to sys.path to enable imports from project modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import required libraries
from dotenv import load_dotenv
from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.indices.knowledge_graph import KnowledgeGraphIndex
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
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
    Create sample documents for testing hybrid search
    """
    # Using the same sample documents from knowledge graph construction
    # to ensure consistency in testing
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


def setup_components(env_vars: Dict[str, str], debug: bool = False) -> Dict[str, Any]:
    """
    Set up all components needed for hybrid search:
    - LLM
    - Embedding model
    - Graph store
    - Storage context
    - Debug handler (optional)
    """
    print("Setting up components for hybrid search...")
    
    # Get model IDs from config
    config = get_config()
    gemini_model_id = config.get("models", {}).get("gemini_pro", "gemini-2.5-pro")
    embedding_model_id = config.get("models", {}).get("embedding_model", "embedding-001")
    thinking_budget = config.get("models", {}).get("thinking_budget", 1024)
    
    # Set up debug handler if requested
    callback_manager = None
    if debug:
        debug_handler = LlamaDebugHandler(print_trace_on_end=True)
        callback_manager = CallbackManager([debug_handler])
    
    # Configure Google GenAI LLM with thinking
    llm = GoogleGenAI(
        api_key=env_vars["GOOGLE_API_KEY"],
        model=gemini_model_id,
        temperature=0.2,  # Slightly higher for RAG response generation
        additional_kwargs={"candidate_count": 1},
        system_prompt=f"""You are a knowledge graph expert assistant.
        Analyze the provided context carefully, focusing on both direct relationships
        and indirect connections between entities.
        Use the graph structure and semantic information to provide accurate,
        detailed responses based on the retrieved information.
        Think step by step about entities, their attributes, and relationships.
        Thinking budget: {thinking_budget} tokens."""
    )
    
    # Initialize the Google GenAI embedding model
    embed_model = GoogleGenAIEmbedding(
        api_key=env_vars["GOOGLE_API_KEY"],
        model_name=embedding_model_id
    )
    
    # Set up Neo4j graph store with proper configuration
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
    Settings.callback_manager = callback_manager
    
    return {
        "llm": llm,
        "embed_model": embed_model,
        "graph_store": graph_store,
        "storage_context": storage_context,
        "callback_manager": callback_manager
    }


def build_indices(components: Dict[str, Any], documents: List[Document]) -> Dict[str, Any]:
    """
    Build or load both knowledge graph index and vector index
    """
    print("Building knowledge graph and vector indices...")
    
    # Create KnowledgeGraphIndex with documents
    kg_index = KnowledgeGraphIndex.from_documents(
        documents,
        storage_context=components["storage_context"],
        max_triplets_per_chunk=10,
        include_embeddings=True,
        show_progress=True
    )
    
    # Create VectorStoreIndex for semantic search
    vector_index = VectorStoreIndex.from_documents(
        documents,
        storage_context=components["storage_context"],
        show_progress=True
    )
    
    indices = {
        "kg_index": kg_index,
        "vector_index": vector_index
    }
    
    print("Indices built successfully")
    return indices


def create_hybrid_query_engine(components: Dict[str, Any], indices: Dict[str, Any]) -> Any:
    """
    Create a hybrid query engine that combines:
    1. Knowledge graph query capabilities (entity-based)
    2. Vector similarity search (semantic similarity)
    Using a simple ensemble approach
    """
    print("Creating hybrid query engine...")
    
    # Get indices
    kg_index = indices["kg_index"]
    vector_index = indices["vector_index"]
    
    # 1. Set up knowledge graph query engine
    kg_query_engine = kg_index.as_query_engine(
        response_mode="compact",
        verbose=True
    )
    
    # 2. Set up vector query engine for semantic search
    vector_query_engine = vector_index.as_query_engine(
        similarity_top_k=3,  # Return top 3 semantic matches
        response_mode="compact",
        verbose=True
    )
    
    # 3. Create a simple hybrid query engine class that combines both approaches
    class HybridQueryEngine:
        def __init__(self, kg_engine, vector_engine, llm):
            self.kg_engine = kg_engine
            self.vector_engine = vector_engine
            self.llm = llm
        
        def query(self, query_str):
            print(f"\nProcessing query: '{query_str}'")
            print("1. Querying knowledge graph...")
            kg_response = self.kg_engine.query(query_str)
            
            print("2. Querying vector index...")
            vector_response = self.vector_engine.query(query_str)
            
            print("3. Combining responses...")
            combined_text = f"Knowledge Graph Results:\n{kg_response}\n\nVector Search Results:\n{vector_response}"
            
            # Create a condensed response
            system_prompt = """You are an expert at combining information from multiple sources.
            Given the results from both a knowledge graph search and a vector search,
            synthesize a comprehensive and accurate response that leverages both structural relationships
            and semantic similarities. Favor specific facts from the knowledge graph when available,
            but incorporate broader context from vector search when relevant.
            Always prioritize accuracy over completeness."""
            
            print("4. Generating final response...")
            final_response = self.llm.complete(
                prompt=f"""System: {system_prompt}
                
                Search Results:
                {combined_text}
                
                Original Query: {query_str}
                
                Synthesized Response:"""
            ).text
            
            # Create a response object to match Llama-Index style
            from dataclasses import dataclass
            
            @dataclass
            class HybridResponse:
                response: str
                source_nodes: list = None
                
                def __str__(self):
                    return self.response
            
            return HybridResponse(response=final_response)
    
    # Create and return the hybrid query engine
    hybrid_engine = HybridQueryEngine(
        kg_engine=kg_query_engine,
        vector_engine=vector_query_engine,
        llm=components["llm"]
    )
    
    print("Hybrid query engine created successfully")
    return hybrid_engine


def run_hybrid_search_demo(query_engine: Any) -> None:
    """
    Demonstrate hybrid search capabilities with sample queries
    showing different aspects of the system
    """
    print("\n=== Running Hybrid Search Demo ===\n")
    
    # List of demonstration queries that showcase different aspects
    test_queries = [
        "Who is Kevin Smith and where does he work?",  # Basic entity relationship
        "What technologies is Acme Technologies using?",  # Indirect relationships
        "How is Graphiti related to knowledge graphs?",  # Conceptual relationship
        "What projects has Kevin worked on?",  # Entity attributes
        "What are the applications of knowledge graphs?",  # Domain knowledge
        "How many employees does Acme have across different offices?",  # Numerical information
        "What is the connection between Neo4j and Graph RAG?"  # Complex relationship query
    ]
    
    # Run each query and show results
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i}: '{query}' ---")
        
        # Execute query
        response = query_engine.query(query)
        
        # Display results
        print(f"Answer: {response}")
        print("\nSource Nodes:")
        
        # Show source nodes that were retrieved (if available)
        if hasattr(response, "source_nodes") and response.source_nodes:
            for j, node in enumerate(response.source_nodes, 1):
                print(f"  {j}. Score: {node.score:.4f}")
                print(f"     Text: {node.text[:150]}..." if len(node.text) > 150 else f"     Text: {node.text}")
        else:
            print("  No source nodes available in response")


def main() -> None:
    """
    Main function to demonstrate hybrid search capabilities
    """
    print("Starting Hybrid Search Demo for Graph RAG...")
    
    try:
        # Load environment variables
        print("Loading environment variables...")
        env_vars = load_environment_variables()
        
        # Create sample documents
        print("Creating sample documents...")
        documents = create_sample_documents()
        print(f"Created {len(documents)} sample documents")
        
        # Set up components with debug mode
        components = setup_components(env_vars, debug=True)
        
        # Build knowledge graph and vector indices
        indices = build_indices(components, documents)
        
        # Create hybrid query engine
        query_engine = create_hybrid_query_engine(components, indices)
        
        # Run demonstration queries
        run_hybrid_search_demo(query_engine)
        
        print("\nHybrid Search Demo completed successfully!")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
