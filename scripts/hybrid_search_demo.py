"""
Hybrid Search Demo

This script demonstrates the HybridSearchEngine's capabilities by:
1. Loading sample documents
2. Connecting to Neo4j
3. Setting up the LLM and embedding model
4. Running sample queries against the hybrid search engine
5. Displaying detailed results with timing information
"""
import os
import sys
import time
import json
import importlib
import datetime # For timestamping log files
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path to enable imports from project modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import project modules
from neo4j import GraphDatabase, Driver
from google import genai
from google.genai import types as genai_types # For GenerationConfig
from loguru import logger # Use Loguru for logging

# Import project-specific modules
from utils.hybrid_search_engine import HybridSearchEngine
from utils.config import get_config

# Force reload of embedding module to ensure we get the latest changes
import utils.embedding
importlib.reload(utils.embedding)
from utils.embedding import CustomGeminiEmbedding
from utils.documents import load_sample_documents


# Wrapper for the LLM to maintain compatibility with HybridSearchEngine
class GeminiLLMWrapper:
    def __init__(self, client, model_name, generation_config_dict):
        self.client = client
        self.model_name = model_name
        self.generation_config = genai_types.GenerationConfig(**generation_config_dict)

    def generate_content(self, contents, generation_config=None, tools=None):
        # The HybridSearchEngine expects the response to have a .text attribute.
        # The new SDK's response object from client.models.generate_content should have this.
        
        config_to_use = self.generation_config
        if generation_config:
            if isinstance(generation_config, dict):
                config_to_use = genai_types.GenerationConfig(**generation_config)
            elif isinstance(generation_config, genai_types.GenerationConfig):
                config_to_use = generation_config
            else:
                logger.warning(f"Invalid type for generation_config: {type(generation_config)}. Using default.")

        kwargs_for_sdk = {
            "model": self.model_name,
            "contents": contents,
            "config": config_to_use
        }
        if tools:
            kwargs_for_sdk["tools"] = tools
        
        api_response = self.client.models.generate_content(**kwargs_for_sdk)
        return api_response

def setup_environment():
    """Set up environment variables and configuration."""
    # Load environment variables from .env file in src directory
    src_env_path = os.path.join(project_root, "src", ".env")
    if os.path.exists(src_env_path):
        load_dotenv(src_env_path)
        logger.info(f"Loaded environment from: {src_env_path}")
    else:
        load_dotenv()
        logger.info("Using default .env file location")
    
    # Get configuration
    config = get_config()
    
    # Validate required environment variables
    required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "GOOGLE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Setup Google API
    
    return config

def setup_neo4j():
    """Set up Neo4j connection."""
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    logger.info(f"Connecting to Neo4j at {neo4j_uri}")
    
    # Create Neo4j driver
    driver = GraphDatabase.driver(
        neo4j_uri,
        auth=(neo4j_user, neo4j_password)
    )
    
    # Test connection
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as count").single()
        nodes_count = result["count"] if result else 0
        logger.info(f"Connected to Neo4j. Database contains {nodes_count} nodes.")
    
    return driver

def setup_models():
    """Set up LLM and embedding models."""
    # Set up Gemini Pro model for reasoning
    # Use the model from config
    config = get_config()
    pro_model = config.get('models', {}).get('pro', 'gemini-2.5-pro')
    
    client = genai.Client() # API key will be picked from GOOGLE_API_KEY env var
    
    # pro_model is defined above (line 92 of original file)
    generation_config_dict = {
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 30,
        "max_output_tokens": 2048,
    }
    llm = GeminiLLMWrapper(client, pro_model, generation_config_dict)
    
    # Set up embedding model using config
    embedding_model_name = config.get('gemini', {}).get('embeddings', {}).get('model_id', 'embedding-001') # Corrected path
    
    embedding_model = CustomGeminiEmbedding(
        model_name=embedding_model_name, 
        api_key=os.getenv("GEMINI_API_KEY"),
        title="Knowledge Graph Embeddings"
    )
    
    return llm, embedding_model

def check_document_nodes_in_neo4j(driver: Driver):
    """Checks for :Document nodes and their embeddings in Neo4j."""
    logger.info("Checking for :Document nodes in Neo4j...")
    try:
        with driver.session() as session:
            total_docs_result = session.run("MATCH (d:Document) RETURN count(d) AS count").single()
            total_docs_count = total_docs_result["count"] if total_docs_result else 0
            logger.info(f"Total :Document nodes found: {total_docs_count}")

            docs_with_embeddings_result = session.run(
                "MATCH (d:Document) WHERE d.embedding IS NOT NULL RETURN count(d) AS count"
            ).single()
            docs_with_embeddings_count = docs_with_embeddings_result["count"] if docs_with_embeddings_result else 0
            logger.info(f":Document nodes with 'embedding' property: {docs_with_embeddings_count}")
            
            if total_docs_count > 0 and docs_with_embeddings_count == 0:
                logger.warning("Found :Document nodes, but NONE have an 'embedding' property. Vector search will likely fail or return no results.")
            elif total_docs_count == 0:
                logger.warning("No :Document nodes found in Neo4j. Vector search will not find any documents.")

    except Exception as e:
        logger.error(f"Error checking :Document nodes in Neo4j: {e}")

def run_sample_queries(engine):
    """Run sample queries against the hybrid search engine."""
    sample_queries = [
        "What tools are used in the Kevin-Graph-RAG project?"
    ]
    
    results = []
    
    for query in sample_queries:
        logger.info(f"\n\n{'='*80}")
        logger.info(f"QUERY: {query}")
        logger.info(f"{'='*80}")
        
        start_time = time.time()
        response = engine.query(query)
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        logger.info(f"\nRESPONSE:")
        logger.info(f"{response.answer}")
        
        logger.info(f"\n{'-'*40}")
        logger.info(f"Query time: {elapsed_ms:.2f}ms")
        logger.info(f"Graph results: {len(response.graph_results)}")
        logger.info(f"Vector results: {len(response.vector_results)}")
        
        if response.error:
            logger.error(f"\nERROR: {response.error}")
        
        # Store result
        results.append({
            "query": query,
            "answer": response.answer,
            "graph_results_count": len(response.graph_results),
            "vector_results_count": len(response.vector_results),
            "time_ms": elapsed_ms,
            "error": response.error
        })
    
    return results

def main():
    """Main function to run the hybrid search demo."""
    # Configure Loguru
    log_level = "DEBUG" if "--debug" in sys.argv else "INFO"
    logger.remove()  # Remove default handler to avoid duplicate console logs if any

    # Console sink with formatting
    logger.add(
        sys.stderr, 
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # File sink with timestamped logs and retention
    logs_dir = Path(project_root) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = logs_dir / f"hybrid_search_demo_{timestamp}.log"

    logger.add(
        log_file_path,
        level="DEBUG",  # Log all debug messages and above to file
        rotation="10 MB",  # Rotate log file when it reaches 10 MB
        retention=3,  # Keep the last 3 log files
        compression="zip",  # Compress rotated log files
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    logger.info("Starting Hybrid Search Demo with file logging configured.")
    try:
        # Setup environment
        config = setup_environment()
        
        # Load sample documents
        sample_docs = load_sample_documents()
        
        # Setup Neo4j
        neo4j_driver = setup_neo4j()

        # Check for :Document nodes in Neo4j (critical for vector search)
        check_document_nodes_in_neo4j(neo4j_driver)
        
        # Setup models
        llm, embedding_model = setup_models()
        
        # Create HybridSearchEngine
        logger.info("\nInitializing Hybrid Search Engine")
        engine_config = {
            "thinking_budget": 1024,
            "vector_top_k": 3,
            "similarity_threshold": 0.6,
        }
        engine = HybridSearchEngine(
            neo4j_driver=neo4j_driver, 
            embedding_model=embedding_model,
            llm=llm,
            config=engine_config
        )
        
        # Check for existing knowledge graph
        with neo4j_driver.session() as session:
            entity_count = session.run("MATCH (n:Entity) RETURN count(n) as count").single()["count"]
        
        if entity_count == 0:
            print("\nWARNING: No entities found in the knowledge graph.")
            print("Run the knowledge graph construction script first.")
            print("You can continue but graph search will not return results.")
        
        # Run sample queries
        print("\nRunning sample queries")
        results = run_sample_queries(engine)
        
        # Save results
        results_path = Path(__file__).parent / "hybrid_search_results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {results_path}")
        
        print("\nHybrid Search Demo completed successfully")
        
    except Exception as e:
        print(f"Error in Hybrid Search Demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    print("DEBUG: Starting hybrid_search_demo.py main execution...")
    sys.exit(main())
