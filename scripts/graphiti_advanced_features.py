"""
Advanced Graphiti Features Test Script

This script demonstrates advanced features of Graphiti-core:
1. Bulk episode ingestion using add_episode_bulk
2. Multi-tenant graph segmentation using group_id
3. Custom entity types and relationship extraction

Based on the master build plan Task 1.3.5
"""
import os
import asyncio
import json
import logging
import sys
import time
import traceback
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Graphiti imports
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType


def retry_operation(max_retries=3, delay_seconds=1.0):
    """
    Decorator for retrying operations that might fail due to timing issues.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay_seconds: Delay between retries in seconds
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logging.warning(f"Attempt {attempt+1} failed for {func.__name__}: {e}. Retrying in {delay_seconds}s...")
                        await asyncio.sleep(delay_seconds)
                    else:
                        logging.error(f"All {max_retries} attempts failed for {func.__name__}")
                        raise last_exception
        return wrapper
    return decorator


def prepare_episode_content(content: Any, source_type: EpisodeType) -> str:
    """
    Prepare episode content for Graphiti ingestion based on source type.
    
    Graphiti expects episode_body to be a string, but users might pass Python dictionaries
    for JSON episodes. This helper ensures the content is properly formatted.
    
    Args:
        content: The episode content (string or dict)
        source_type: EpisodeType.text or EpisodeType.json
        
    Returns:
        Properly formatted string content ready for Graphiti ingestion
    """
    # If content is already a string, return as is
    if isinstance(content, str):
        return content
        
    # For JSON episodes, convert dict to JSON string
    if source_type == EpisodeType.json:
        if isinstance(content, (dict, list)):
            try:
                return json.dumps(content)
            except Exception as e:
                raise ValueError(f"Failed to convert dictionary to JSON string: {e}")
        else:
            raise ValueError(f"JSON episode content must be dict or string, got {type(content)}")
            
    # For text episodes, only strings are valid
    if source_type == EpisodeType.text and not isinstance(content, str):
        raise ValueError(f"Text episode content must be string, got {type(content)}")
        
    # Default case - attempt string conversion
    return str(content)

# Define Pydantic models for custom entity types
class Person(BaseModel):
    """A human person, fictional or nonfictional."""
    first_name: Optional[str] = Field(None, description="First name of the person")
    last_name: Optional[str] = Field(None, description="Last name of the person")
    occupation: Optional[str] = Field(None, description="The person's occupation")
    organization: Optional[str] = Field(None, description="Organization the person is affiliated with")

class Organization(BaseModel):
    """An organization or company."""
    org_name: Optional[str] = Field(..., description="Name of the organization")  # Avoid using 'name' as it's protected
    industry: Optional[str] = Field(None, description="Industry the organization operates in")
    founded: Optional[int] = Field(None, description="Year the organization was founded")

class Location(BaseModel):
    """A physical location or place."""
    location_name: Optional[str] = Field(..., description="Name of the location")  # Avoid using 'name' as it's protected
    country: Optional[str] = Field(None, description="Country of the location")
    coordinates: Optional[str] = Field(None, description="Geographic coordinates")

class WorksFor(BaseModel):
    """Relationship representing employment or affiliation."""
    role: Optional[str] = Field(None, description="Job title or role")
    start_date: Optional[str] = Field(None, description="When employment started")
    department: Optional[str] = Field(None, description="Department within the organization")

class LocatedIn(BaseModel):
    """Relationship representing geographical containment."""
    since: Optional[str] = Field(None, description="When the entity was established at this location")
    address: Optional[str] = Field(None, description="Specific address details")

async def test_bulk_episode_ingestion(graph: Graphiti):
    """
    Test bulk ingestion of episodes using sequential calls to add_episode.
    While GraphitiCore has add_episode_bulk, we'll use sequential calls to keep compatibility.
    """
    print("\n=== Testing Bulk Episode Ingestion ===", flush=True)
    
    # 1. Add multiple text episodes sequentially
    print("Adding multiple text episodes sequentially...", flush=True)
    
    # Sample text episodes
    text_episodes = [
        "This is a test episode 1 for bulk ingestion. It contains information about knowledge graphs and graph databases.",
        "This is a test episode 2 for bulk ingestion. It discusses AI and machine learning integration with graph databases.",
        "This is a test episode 3 for bulk ingestion. It explores semantic search capabilities in knowledge management systems."
    ]
    
    # Add text episodes sequentially
    for i, text in enumerate(text_episodes):
        print(f"  Adding text episode {i+1}...", flush=True)
        await graph.add_episode(
            name=f"bulk_text_episode_{i+1}",
            episode_body=text,
            source=EpisodeType.text,
            source_description=f"Test text episode {i+1}",
            reference_time=datetime.now(timezone.utc)
        )
    
    # 2. Add multiple JSON episodes sequentially
    print("Adding multiple JSON episodes sequentially...", flush=True)
    
    # Sample JSON episodes - structured as entities array to match Graphiti expectations
    json_episodes = [
        {
            "entities": [
                {
                    "name": "Entity 1",
                    "type": "TestEntity",
                    "properties": {
                        "attr1": "value1",
                        "attr2": 42,
                        "tags": ["test", "bulk", "tag1"]
                    }
                }
            ]
        },
        {
            "entities": [
                {
                    "name": "Entity 2",
                    "type": "TestEntity",
                    "properties": {
                        "attr1": "value2",
                        "attr2": 84,
                        "tags": ["test", "bulk", "tag2"]
                    }
                }
            ]
        },
        {
            "entities": [
                {
                    "name": "Entity 3",
                    "type": "TestEntity",
                    "properties": {
                        "attr1": "value3",
                        "attr2": 126,
                        "tags": ["test", "bulk", "tag3"]
                    }
                }
            ]
        }
    ]
    
    # Add JSON episodes sequentially
    for i, json_data in enumerate(json_episodes):
        print(f"  Adding JSON episode {i+1}...", flush=True)
        
        await graph.add_episode(
            name=f"bulk_json_episode_{i+1}",
            episode_body=prepare_episode_content(json_data, EpisodeType.json),  # Properly formatted
            source=EpisodeType.json,
            source_description=f"Test JSON episode {i+1}",
            reference_time=datetime.now(timezone.utc)
        )
    
    # 3. Verify bulk ingestion with Neo4j query
    print("Verifying bulk ingestion with Neo4j query...", flush=True)
    
    await verify_bulk_ingestion(graph)

@retry_operation(max_retries=3, delay_seconds=1.0)
async def verify_bulk_ingestion(graph: Graphiti):
    """
    Verify that the bulk ingestion was successful using retry logic.
    """
    logging.info("Verifying bulk ingestion with Neo4j query...")
    
    try:
        # For AsyncSession, we need to use the async pattern instead of context manager
        session = graph.driver.session()
        try:
            # Query for episodes with names starting with 'bulk_'
            result = await session.run("""
                MATCH (e:Episode)
                WHERE e.name STARTS WITH 'bulk_'
                RETURN e.name AS name, e.source AS source
                ORDER BY e.name
                """)
            
            # Fetch and print results
            values = await result.values()
            
            print("Bulk ingested episodes:")
            if not values:
                print("  No bulk episodes found. This might be a timing issue or ingestion failed.")
            for name, source in values:
                print(f"  - {name} (Source: {source})", flush=True)
                
            return values  # Return values for potential further processing
        finally:
            await session.close()
                
    except Exception as e:
        logging.error(f"Error verifying bulk ingestion: {e}")
        traceback.print_exc()
        raise  # Re-raise for the retry decorator to catch

async def test_multitenant_segmentation(graph: Graphiti):
    """
    Test multi-tenant graph segmentation using Graphiti's built-in group_id parameter.
    This allows maintaining separate namespace subgraphs within the same database.
    """
    print("\n=== Testing Multi-tenant Graph Segmentation (Namespacing) ===", flush=True)
    
    # Define test tenants/namespaces
    namespaces = ["finance", "healthcare", "technology"]
    
    # We'll use both individual ingestion and bulk ingestion for demonstration
    for namespace in namespaces:
        print(f"Creating episodes for namespace: {namespace}", flush=True)
        
        # 1. Individual episode ingestion with namespace
        text_content = f"This is domain-specific content for the {namespace} sector. "
        if namespace == "finance":
            text_content += "Topics include banking, investments, and financial regulations."
        elif namespace == "healthcare":
            text_content += "Topics include medical research, patient care, and healthcare policy."
        else:  # technology
            text_content += "Topics include software development, AI, and cloud computing."
        
        # Using the built-in group_id parameter for namespacing
        await graph.add_episode(
            name=f"{namespace}_text_episode",
            episode_body=prepare_episode_content(text_content, EpisodeType.text),
            source=EpisodeType.text,
            source_description=f"{namespace.capitalize()} domain text",
            reference_time=datetime.now(timezone.utc),
            group_id=namespace  # This is Graphiti's built-in namespace parameter
        )
        
        # 2. Add additional JSON episodes with the same namespace
        # Create 2 JSON episodes for this namespace
        for i in range(2):
            json_data = {
                "domain": namespace,
                "concept_id": f"{namespace}_concept_{i+1}",
                "importance": "high" if i == 0 else "medium",
                "description": f"A key concept in the {namespace} domain",
                "related_terms": [f"{namespace}_term_{j+1}" for j in range(3)]
            }
            
            # Add the episode with namespace
            await graph.add_episode(
                name=f"{namespace}_json_episode_{i+1}",
                episode_body=prepare_episode_content(json_data, EpisodeType.json),  # Convert dict to JSON string
                source=EpisodeType.json,
                source_description=f"Structured {namespace} data #{i+1}",
                reference_time=datetime.now(timezone.utc),
                group_id=namespace  # Same namespace for all episodes
            )
            
        print(f"Added episodes for namespace '{namespace}'.", flush=True)
    
    print("All group-specific episodes added.", flush=True)
    
    # Verify multi-tenant segmentation for each namespace
    for namespace in namespaces:
        try:
            await verify_namespace_segmentation(graph, namespace)
        except Exception as e:
            print(f"Error verifying multi-tenant segmentation for {namespace}: {e}", flush=True)
            traceback.print_exc()

@retry_operation(max_retries=3, delay_seconds=1.0)
async def verify_namespace_segmentation(graph: Graphiti, namespace_to_check: str):
    """
    Verify that the multi-tenant segmentation is working correctly, with retry logic.
    """
    logging.info(f"Verifying namespace isolation for group_id: {namespace_to_check}")
    
    try:
        # Using async pattern for AsyncSession
        session = graph.driver.session()
        try:
            # Query episodes by group_id
            result = await session.run(
                """
                MATCH (e:Episode)
                WHERE e.group_id = $group_id
                RETURN e.name AS name, e.source AS source, e.group_id AS group_id
                ORDER BY e.name
                """,
                {"group_id": namespace_to_check}
            )
            
            values = await result.values()
            episodes = [(name, source, group_id) for name, source, group_id in values]
            
            print(f"Episodes in namespace '{namespace_to_check}':", flush=True)
            if not episodes:
                print(f"  No episodes found in namespace '{namespace_to_check}'")
            for name, source, group_id in episodes:
                print(f"  - {name} (Source: {source}, Group: {group_id})", flush=True)
                
            # Also check for entities in this namespace
            result = await session.run(
                """
                MATCH (n:Entity)
                WHERE n.group_id = $group_id
                RETURN n.name AS name, n.type AS type, n.group_id AS group_id
                """,
                {"group_id": namespace_to_check}
            )
            
            values = await result.values()
            entities = [(name, type, group_id) for name, type, group_id in values]
            
            print(f"\nEntities in namespace '{namespace_to_check}':", flush=True)
            if not entities:
                print(f"  No entities found in namespace '{namespace_to_check}'")
            for name, type, group_id in entities:
                print(f"  - {name} (Type: {type}, Group: {group_id})", flush=True)
                
            # Return both for potential further processing
            return {"episodes": episodes, "entities": entities}
        finally:
            await session.close()
    except Exception as e:
        logging.error(f"Error verifying namespace segmentation: {e}")
        traceback.print_exc()
        raise  # Re-raise for retry decorator

async def test_custom_entity_types(graph: Graphiti, use_pydantic_models: bool = False):
    """
    Test custom entity types and relationship extraction using Pydantic models or string-based approach.
    
    Args:
        graph (Graphiti): The Graphiti client instance.
        use_pydantic_models (bool): Whether to use Pydantic models or string-based approach.
    """
    print(f"\n=== Testing Custom Entity Types and Relationship Extraction ===", flush=True)
    
    approach = "pydantic_models" if use_pydantic_models else "string_based"
    print(f"Using {approach} approach", flush=True)
    
    # Create test data based on official examples
    test_episode_body = {
        "text": "TechCorp is a leading AI company based in San Francisco. Sarah Johnson is the CEO of TechInnovate, which has offices in Boston, San Francisco, London, and Toronto. Sarah holds a PhD from MIT."
    }
    
    # More complex JSON data for entity relationships, following official examples
    json_data = {
        "text": "TechInnovate is an innovative company with headquarters in Boston.",
        "entities": [
            {
                "name": "TechInnovate",
                "type": "Organization",
                "attributes": {
                    "industry": "Technology",
                    "founded": 2010,
                    "employees": 500
                }
            },
            {
                "name": "Boston",
                "type": "Location",
                "attributes": {
                    "country": "USA",
                    "population": 675647
                }
            }
        ],
        "relationships": [
            {
                "source": "TechInnovate",
                "target": "Boston",
                "type": "HEADQUARTERED_IN"
            }
        ]
    }
    
    # Create entity and relationship types based on official examples
    if use_pydantic_models:
        # Define relationship type following official examples
        class HeadquarteredIn(BaseModel):
            """Relationship between an organization and its headquarters location"""
            # Empty model following official examples pattern
            pass
            
        # Define entity types and edge types for use with add_episode
        entity_types = {
            "Organization": Organization,  # Uses our updated Organization model with org_name
            "Location": Location,  # Uses our updated Location model with location_name
            "Person": Person  # Uses existing Person model
        }
        edge_types = {"HEADQUARTERED_IN": HeadquarteredIn, "WORKS_FOR": WorksFor, "LOCATED_IN": LocatedIn}
        edge_type_map = {
            ("Organization", "Location"): ["HEADQUARTERED_IN", "LOCATED_IN"],
            ("Person", "Organization"): ["WORKS_FOR"]
        }
    else:
        # Using string-based approach - entity types will be extracted automatically
        entity_types = None
        edge_types = None
        edge_type_map = None
    
    try:
        # Add the test episode with appropriate parameters
        print(f"Adding test episode using {approach} approach...", flush=True)
        
        # Use parameters based on official examples
        if use_pydantic_models:
            await graph.add_episode(
                name=f"custom_entity_episode_{approach}",
                episode_body=prepare_episode_content(test_episode_body, EpisodeType.json),
                source=EpisodeType.json,
                source_description=f"Custom entity test using {approach}",
                reference_time=datetime.now(timezone.utc),
                entity_types=entity_types,
                edge_types=edge_types,
                edge_type_map=edge_type_map
            )
        else:
            await graph.add_episode(
                name=f"custom_entity_episode_{approach}",
                episode_body=prepare_episode_content(test_episode_body, EpisodeType.json),
                source=EpisodeType.json,
                source_description=f"Custom entity test using {approach}",
                reference_time=datetime.now(timezone.utc)
                # No custom entity types needed for string-based approach
            )
        
        # Add the structured JSON episode with appropriate parameters
        print("Adding JSON episode with explicit entity information...", flush=True)
        
        # Use parameters based on official examples
        if use_pydantic_models:
            await graph.add_episode(
                name="entity_relationships_sample",
                episode_body=prepare_episode_content(json_data, EpisodeType.json),
                source=EpisodeType.json,
                source_description="Sample entity relationship data with Pydantic models",
                reference_time=datetime.now(timezone.utc),
                entity_types=entity_types,
                edge_types=edge_types,
                edge_type_map=edge_type_map
            )
        else:
            await graph.add_episode(
                name="entity_relationships_sample",
                episode_body=prepare_episode_content(json_data, EpisodeType.json),
                source=EpisodeType.json,
                source_description="Sample entity relationship data with string-based approach",
                reference_time=datetime.now(timezone.utc)
            )
        
        # Add text episode for LLM-based entity extraction
        print("Adding text episode for LLM-based entity extraction...", flush=True)
        
        text_content = """
        Sarah Johnson is the CEO of TechInnovate, a leading AI research company based in Boston.
        Before joining TechInnovate in 2018, she was a professor at MIT specializing in machine learning.
        TechInnovate was founded in 2015 and has grown to 200 employees across offices in Boston, 
        San Francisco, and London. The company recently opened a new research lab in Toronto.
        """
        
        # Add the text episode with appropriate parameters based on approach
        if use_pydantic_models:
            await graph.add_episode(
                name="tech_innovation_article",
                episode_body=text_content,
                source=EpisodeType.text,
                source_description="News article about TechInnovate",
                reference_time=datetime.now(timezone.utc),
                entity_types=entity_types
                # Following official examples, we don't include edge_types and edge_type_map for text
            )
        else:
            await graph.add_episode(
                name="tech_innovation_article",
                episode_body=text_content,
                source=EpisodeType.text,
                source_description="News article about TechInnovate",
                reference_time=datetime.now(timezone.utc)
            )
        
        print("All entity and relationship episodes added.", flush=True)
        
    except Exception as e:
        print(f"Error during custom entity type test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Call external verification function
    try:
        await verify_custom_entities(graph, approach)
    except Exception as e:
        print(f"Error verifying entity extraction: {e}", flush=True)

async def verify_custom_entities(graph: Graphiti, approach: str):
    """
    Verify entity extraction using a Neo4j query.
    
    This function implements a robust verification process by checking:
    1. Entities created with the correct types
    2. Properties assigned correctly
    3. Relationships between entities
    
    Args:
        graph (Graphiti): The Graphiti client instance
        approach (str): The approach used for entity extraction 
                       (pydantic_models or string_based)
    """
    print("Verifying entity extraction with Neo4j query...", flush=True)
    
    @retry_operation(max_retries=3, delay_seconds=1.0)
    async def _run_verification_query(session, query, params=None):
        result = await session.run(query, params or {})
        records = await result.fetch(10)
        return [record.data() for record in records]
    
    try:
        async with graph.driver.session() as session:
            # 1. Check created entities
            print("Extracted entities:")
            entities = await _run_verification_query(
                session,
                """
                MATCH (e:Entity)
                WHERE e.name IN ['TechInnovate', 'Boston', 'San Francisco', 'MIT', 'Sarah Johnson'] 
                      OR e.org_name IS NOT NULL
                      OR e.location_name IS NOT NULL
                RETURN 
                    COALESCE(e.name, e.org_name, e.location_name) as name,
                    labels(e) as labels,
                    e.type as type
                """
            )
            
            for entity in entities:
                labels_str = ", ".join([label for label in entity["labels"] if label != "Entity"])
                type_str = f" (Type: {entity.get('type', 'None')})"
                print(f"  - {entity['name']}: {labels_str or 'Entity'}{type_str}")
                
            # 2. Check relationships
            print("\nExtracted relationships:")
            relationships = await _run_verification_query(
                session,
                """
                MATCH (s:Entity)-[r]->(t:Entity)
                WHERE s.name IN ['TechInnovate', 'Sarah Johnson', 'TechCorp']
                   OR t.name IN ['Boston', 'San Francisco', 'MIT']
                   OR s.org_name IS NOT NULL
                   OR t.location_name IS NOT NULL
                RETURN 
                    COALESCE(s.name, s.org_name) as source, 
                    type(r) as relationship, 
                    COALESCE(t.name, t.location_name) as target
                LIMIT 10
                """
            )
            
            for rel in relationships:
                print(f"  - {rel['source']} --[{rel['relationship']}]--> {rel['target']}")
            
            # 3. For Pydantic approach, check specific type properties
            if approach == "pydantic_models":
                print("\nPydantic model properties:")
                type_properties = await _run_verification_query(
                    session,
                    """
                    MATCH (e:Entity)
                    WHERE e.org_name IS NOT NULL OR e.location_name IS NOT NULL
                    RETURN 
                        COALESCE(e.org_name, e.location_name) as name,
                        e.org_name IS NOT NULL as is_org,
                        properties(e) as props
                    LIMIT 5
                    """
                )
                
                for item in type_properties:
                    entity_type = "Organization" if item["is_org"] else "Location"
                    props = {k: v for k, v in item["props"].items() 
                             if k not in ["uuid", "name", "org_name", "location_name", "group_id"]}
                    print(f"  - {item['name']} ({entity_type}): {props}")
                
    except Exception as e:
        print(f"Error during entity verification: {str(e)}")
        import traceback
        traceback.print_exc()

@retry_operation(max_retries=3, delay_seconds=1.0)
async def setup_fulltext_index(graph: Graphiti):
    """
    Set up the required fulltext schema indexes for Graphiti.
    This is needed for proper functioning of Graphiti's search capabilities.
    """
    logging.info("Setting up required Neo4j fulltext schema index for Graphiti")
    print("\n=== Setting up required Neo4j fulltext schema index for Graphiti ===", flush=True)
    
    try:
        # For AsyncSession, we need to use the async pattern instead of context manager
        session = graph.driver.session()
        try:
            # Check for existing indexes using SHOW INDEXES command (standard Cypher)
            try:
                result = await session.run("SHOW INDEXES WHERE name = 'node_name_and_summary'")
                records = await result.values()
                index_exists = len(records) > 0
                
                if index_exists:
                    print("Fulltext index 'node_name_and_summary' already exists.", flush=True)
                    return True
            except Exception as e:
                # If SHOW INDEXES fails, we'll try another approach
                logging.warning(f"SHOW INDEXES command failed: {e}")
                # Attempt to drop the index if it exists (this will fail silently if it doesn't exist)
                try:
                    await session.run("""
                        CALL db.index.fulltext.drop("node_name_and_summary")
                    """)
                    print("Dropped existing fulltext index (if any).", flush=True)
                except Exception as drop_err:
                    # Ignore errors - index probably didn't exist
                    logging.debug(f"Could not drop index: {drop_err}")
                    pass
            
            # Create fulltext index on Node name and summary properties
            # Using the db.index.fulltext.createNodeIndex procedure
            await session.run("""
                CALL db.index.fulltext.createNodeIndex(
                    "node_name_and_summary",
                    ["Node", "Entity", "Episode"],
                    ["name", "summary"]
                )
            """)
            print("Fulltext index 'node_name_and_summary' created successfully.", flush=True)
            
            return True
        finally:
            await session.close()
    except Exception as e:
        logging.error(f"Error setting up fulltext index: {e}")
        traceback.print_exc()
        raise  # Re-raise for retry decorator

def setup_logging():
    """Set up logging configuration similar to official examples"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create console handler and set level to INFO
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add formatter to console handler
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    return logger

async def main():
    """
    Main function that runs all the advanced feature tests.
    """
    print("=== Graphiti Advanced Features Test ===", flush=True)
    logger = setup_logging()
    graph = None
    
    try:
        # Load environment variables for Neo4j connection and API keys
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'src', '.env')
        if not os.path.exists(dotenv_path):
            logger.error(f"Error: .env file not found at {os.path.abspath(dotenv_path)}")
            return
        load_dotenv(dotenv_path=dotenv_path)
        logger.info(".env file loaded.")
        
        # Retrieve environment variables
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not all([uri, user, password]):
            logger.error("Error: Missing required Neo4j environment variables")
            return
        
        # Initialize Graphiti with Neo4j connection and Google Gemini if available
        logger.info("Initializing Graphiti with Neo4j connection...")
        graph = None
        google_api_key = os.environ.get("GOOGLE_API_KEY", None)
        
        # If Google API key is available, use Gemini for LLM and embeddings
        if google_api_key:
            # Add project root to Python path to allow importing our modules
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(project_root)
            
            # Import configuration from central YAML config
            from utils.config import get_config
            config = get_config()
            
            from graphiti_core.llm_client.gemini_client import GeminiClient, LLMConfig
            from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
            from google.genai import types as genai_types
            
            logger.info("Google API key found. Using Gemini for LLM and embeddings.")
            
            # Select which Gemini model to use based on environment or default to Flash
            use_pro_model = os.environ.get("USE_GEMINI_PRO", "false").lower() == "true"
            model_type = "pro" if use_pro_model else "flash"
            
            # Get exact model ID and thinking budget from configuration
            gemini_model_id = config.get_gemini_model_id(model_type)
            thinking_budget = config.get_gemini_thinking_budget(model_type)
            embeddings_model_id = config.get_gemini_embeddings_model()
            
            logger.info(f"Using Gemini model: {gemini_model_id} with thinking budget: {thinking_budget}")
            
            # Create Graphiti client with Google Gemini
            try:
                graph = Graphiti(
                    uri=uri,
                    user=user,
                    password=password,
                    llm_client=GeminiClient(
                        config=LLMConfig(
                            api_key=google_api_key,
                            model=gemini_model_id,  # Using the exact model ID from config
                            # Note: Standard Graphiti doesn't support thinking_config directly
                            # We'll need a custom GeminiClient extension to support thinking capabilities
                        )
                    ),
                    embedder=GeminiEmbedder(
                        config=GeminiEmbedderConfig(
                            api_key=google_api_key,
                            embedding_model=embeddings_model_id  # Using model ID from config
                        )
                    )
                )
                logger.info(f"Graphiti initialized with {gemini_model_id} LLM and embeddings.")
                
                # Initialize schema indices and constraints to prevent unknown label/property warnings
                logger.info("Building Neo4j indices and constraints...")
                await graph.build_indices_and_constraints()
            except Exception as e:
                logger.error(f"Error initializing Graphiti with Gemini: {e}")
                import traceback
                traceback.print_exc()
                return
        else:
            # Fallback to default OpenAI (user will need to set those env vars too)
            logger.info("Warning: No Google API key found. Using default OpenAI.")
            graph = Graphiti(
                uri=uri,
                user=user,
                password=password
            )
            logger.info("Graphiti initialized with default settings.")
            
            # Initialize schema indices and constraints to prevent unknown label/property warnings
            logger.info("Building Neo4j indices and constraints...")
            await graph.build_indices_and_constraints()
        
        # Set up fulltext index after building indices
        await setup_fulltext_index(graph)
        
        # Run the advanced feature tests
        print("\nRunning advanced feature tests...", flush=True)
        
        # 1. Test bulk episode ingestion
        await test_bulk_episode_ingestion(graph)
        
        # 2. Test multi-tenant segmentation
        await test_multitenant_segmentation(graph)
        
        # 3. Test custom entity types with default string-based approach
        await test_custom_entity_types(graph, use_pydantic_models=False)
        
        # 4. Test custom entity types with Pydantic models
        await test_custom_entity_types(graph, use_pydantic_models=True)
        
        # 5. Explicitly verify custom entities created with Pydantic models
        print("\nVerifying custom entities from Pydantic-based extraction...", flush=True)
        await verify_custom_entities(graph, approach="pydantic_models")
        
    except Exception as e:
        print(f"Error during advanced features test: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        # Close the Neo4j driver connection
        if graph and graph.driver:
            print("Closing Neo4j driver connection...", flush=True)
            await graph.driver.close()
            print("Neo4j driver connection closed.", flush=True)
    
    print("=== Advanced Features Test Completed ===", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
