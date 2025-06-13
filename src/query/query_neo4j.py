import asyncio
import os
import importlib
from typing import Dict, Type, List

from dotenv import load_dotenv
from tabulate import tabulate
from pydantic import BaseModel

from graphiti.client import Graphiti
from graphiti.graph import Neo4jGraph
# from graphiti.llm import LLM # LLM wrapper class might not be needed if passing client directly
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client import LLMConfig
from src.graph_extraction.gemini_embedder import BatchSizeOneGeminiEmbedder # Custom embedder from project
from graphiti_core.embedder.gemini import GeminiEmbedderConfig # Config is still from graphiti-core
from graphiti_core.embedder import EmbedderClient # Required for Graphiti init type hint
from google import genai # For ADC
from graphiti.search import SearchConfig, SearchResults

# Attempt to import a recipe for SearchConfig
SEARCH_CONFIG_RECIPE_NAME = "COMBINED_HYBRID_SEARCH_RRF"
try:
    from graphiti.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF
    search_config_to_use = COMBINED_HYBRID_SEARCH_RRF
    print(f"Using SearchConfig recipe: {SEARCH_CONFIG_RECIPE_NAME}")
except ImportError:
    print(f"Warning: Could not import {SEARCH_CONFIG_RECIPE_NAME} from graphiti.search_config_recipes.")
    print("Attempting to construct a basic SearchConfig. This may need adjustment.")
    # Fallback to a manually constructed SearchConfig if recipes are not available or the specific one isn't.
    # This is a best-guess based on the documentation provided.
    # The actual structure of EdgeSearchConfig, NodeSearchConfig, CommunitySearchConfig might differ.
    try:
        from graphiti.search import EdgeSearchConfig, NodeSearchConfig, CommunitySearchConfig # Assuming these exist
        search_config_to_use = SearchConfig(
            limit=100, # Overall limit for search results
            edges=EdgeSearchConfig(limit=50, enabled=True), # Assuming an 'enabled' flag and sub-limit
            nodes=NodeSearchConfig(limit=50, enabled=True),
            communities=CommunitySearchConfig(limit=10, enabled=True) 
        )
        print("Using a manually constructed basic SearchConfig.")
    except ImportError:
        print("Error: Could not import EdgeSearchConfig, NodeSearchConfig, or CommunitySearchConfig from graphiti.search.")
        print("Please ensure Graphiti is installed correctly and these components are available.")
        print("A SearchConfig is required. Exiting.")
        exit(1)
    except TypeError as e:
        print(f"Error: Could not construct SearchConfig, EdgeSearchConfig, NodeSearchConfig, or CommunitySearchConfig: {e}")
        print("The structure of these config objects might be different in your Graphiti version.")
        print("Please check Graphiti documentation for SearchConfig. Exiting.")
        exit(1)


# Function to load ontology (similar to ingest script)
def load_ontology_from_template(template_name: str) -> Dict[str, Type[BaseModel]]:
    module_path_primary = f"src.ontology_templates.{template_name}_ontology"
    module_path_alternative = f"ontology_templates.{template_name}_ontology" # If src is in PYTHONPATH and script is not in src
    
    module = None
    try:
        module = importlib.import_module(module_path_primary)
        print(f"Successfully imported ontology module: {module_path_primary}")
    except ImportError as e_primary:
        print(f"Could not import ontology from {module_path_primary}: {e_primary}")
        try:
            module = importlib.import_module(module_path_alternative)
            print(f"Successfully imported ontology module with alternative path: {module_path_alternative}")
        except ImportError as e_alternative:
            print(f"Could not import ontology from {module_path_alternative} either: {e_alternative}")
            print("Please ensure the script is run from the project root or PYTHONPATH is set correctly.")
            raise

    entity_types: Dict[str, Type[BaseModel]] = {}
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, BaseModel) and attr is not BaseModel:
            entity_types[attr_name] = attr
            print(f"Found entity type: {attr_name}")
    if not entity_types:
        print(f"No Pydantic models found in the ontology module. Check the ontology file.")
    return entity_types

async def query_database():
    load_dotenv()

    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    # GOOGLE_API_KEY is no longer used; authentication relies on Application Default Credentials (ADC)
    # Ensure you have run 'gcloud auth application-default login'
    if not all([neo4j_uri, neo4j_username, neo4j_password]):
        print("Critical Error: NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD environment variables must be set.")
        return

    try:
        ontology_name = "generic" # Assuming 'generic_ontology.py'
        entity_types = load_ontology_from_template(ontology_name)
        if not entity_types:
            print(f"Ontology '{ontology_name}_ontology.py' could not be loaded or is empty. Exiting.")
            return
    except Exception as e:
        print(f"Failed to load ontology: {e}")
        return

    try:
        # Configure LLM Client (Gemini with ADC)
        # Using default model IDs here for simplicity in query script, consider using utils.config like in GraphExtractor for consistency
        llm_model_id = "gemini-1.5-pro-preview-0514" # Or your preferred model from config
        llm_config_for_graphiti = LLMConfig(
            model=llm_model_id,
            api_key=None,  # Force ADC
            temperature=0.2,
            max_tokens=8192 # Graphiti default, adjust if needed
        )
        graphiti_llm = GeminiClient(config=llm_config_for_graphiti)
        graphiti_llm.client = genai.Client() # Reinforce ADC for LLM
        print(f"Graphiti GeminiClient (LLM) initialized with model: {llm_model_id} using ADC.")

        # Configure Embedder Client (Custom Gemini Embedder with ADC)
        embedding_model_id = "text-embedding-004" # Or your preferred model from config
        embedding_dim = 768 # Dimension for text-embedding-004
        embedder_config = GeminiEmbedderConfig(
            embedding_model=embedding_model_id,
            embedding_dim=embedding_dim,
            api_key=None  # Force ADC
        )
        graphiti_embedder = BatchSizeOneGeminiEmbedder(config=embedder_config) # Use custom BatchSizeOneGeminiEmbedder
        graphiti_embedder.client = genai.Client() # Reinforce ADC for Embedder
        print(f"Graphiti BatchSizeOneGeminiEmbedder initialized with model: {embedding_model_id} using ADC.")

        graph_db_client = Neo4jGraph(uri=neo4j_uri, username=neo4j_username, password=neo4j_password, database="neo4j")
        
        # Note: Graphiti constructor expects llm_client and embedder_client, not a generic LLM object
        graphiti_client = Graphiti(
            project_id="kev-new-graph-rag-query-test",
            llm_client=graphiti_llm, # Pass the configured GeminiClient
            embedder_client=graphiti_embedder, # Pass the configured BatchSizeOneGeminiEmbedder
            graph_client=graph_db_client,
            # entity_types are now loaded and passed directly to Graphiti instance
            # as per Graphiti's newer API (if applicable, based on GraphExtractor's usage)
            # If Graphiti expects entity_types at init, ensure it's passed. The example in GraphExtractor
            # does not show entity_types being passed at Graphiti init, but rather to add_episode.
            # For search, it might be needed at init or when calling search methods.
            # Let's assume for now it's not strictly needed at init for basic search, or handled internally.
        )
        # If entity_types are needed for search context and not passed at init, Graphiti might allow
        # registering them post-init, or they might be implicitly used if already in the graph from ingestion.
        # For now, we rely on the graph already being populated with typed entities.

    except Exception as e:
        print(f"Error initializing Graphiti client: {e}")
        return
    
    print("\nGraphiti client initialized. Attempting to query the database...")

    try:
        # A broad query text for a general overview.
        # Graphiti's search is primarily semantic, so a natural language query is expected.
        query_text = "Retrieve all available information about entities and their relationships."
        
        print(f"Executing search with query: '{query_text}'")
        search_results: SearchResults = await graphiti_client._search(query_text, config=search_config_to_use)
        
        nodes = search_results.nodes
        edges = search_results.edges
        # communities = search_results.communities # Not explicitly requested for table output yet

        print(f"\nSearch complete. Found {len(nodes)} nodes and {len(edges)} edges.")

        if nodes:
            print("\n--- Nodes ---")
            node_data = []
            # Dynamically create headers based on common and specific properties
            # Common properties expected: uuid, type. Others are dynamic.
            # To keep the table manageable, we'll show a few key props and a summary of others.
            headers = ["UUID", "Type", "Name/Label", "Key Properties (sample)"]
            for node in nodes:
                props = {k: v for k, v in node.model_dump().items() if k not in ['uuid', 'type', 'text_'] and not k.startswith('_')}
                # Try to find a 'name' or 'label' like attribute for better identification
                name_label = props.get(f"{node.type.lower()}_name", props.get("name", props.get("label", "N/A")))
                # Sample a few properties for the table
                props_sample = {k: props[k] for k in list(props.keys())[:3]}
                node_data.append([str(node.uuid), node.type, name_label, str(props_sample)])
            print(tabulate(node_data, headers=headers, tablefmt="grid"))
        else:
            print("No nodes found matching the query or criteria.")

        if edges:
            print("\n--- Relationships (Edges) ---")
            edge_data = []
            headers = ["UUID", "Type", "Fact/Properties", "Source Node UUID", "Target Node UUID"]
            for edge in edges:
                props_or_fact = edge.fact if hasattr(edge, 'fact') and edge.fact else edge.model_dump().get('properties', {k: v for k,v in edge.model_dump().items() if k not in ['uuid', 'type', 'source_node_uuid', 'target_node_uuid', 'fact'] and not k.startswith('_')})
                edge_data.append([str(edge.uuid), edge.type, str(props_or_fact), str(edge.source_node_uuid), str(edge.target_node_uuid)])
            print(tabulate(edge_data, headers=headers, tablefmt="grid"))
        else:
            print("No edges found matching the query or criteria.")

        print("\n--- Identifying Recent Ingestions ---")
        print("To identify data from specific ingestions (e.g., your recent GDrive documents):")
        print("1. Check for an 'episode_id' or 'document_id' property on nodes or edges. Graphiti's `add_episode` might associate entities with an episode ID, or you might have added a document ID during ingestion.")
        print("2. Look for timestamp properties (e.g., 'created_at', 'updated_at') if your ontology or Graphiti adds them.")
        print("3. If you know the `episode_id` used during the ingestion of the two GDrive documents, you could potentially filter or search for entities associated with it, though Graphiti's primary search is semantic.")
        print("   Direct Cypher queries might be needed for precise metadata-based filtering if Graphiti's search doesn't directly support it for this use case.")

    except Exception as e:
        print(f"An error occurred during query execution or processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(query_database())
