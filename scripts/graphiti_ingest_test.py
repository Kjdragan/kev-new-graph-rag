print("--- GRAPHITI_INGEST_TEST.PY TOP LEVEL EXECUTION MARKER ---", flush=True)
import os
import asyncio
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Graphiti imports
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

# Import the google-genai SDK for diagnostic purposes only
# (we're not using it directly in the ingestion test anymore)
from google import genai

async def test_graphiti_ingestion():
    """
    Tests basic data ingestion into Neo4j using Graphiti-core.
    """
    print("--- test_graphiti_ingestion function started ---", flush=True)
    print("Graphiti ingestion test script started.", flush=True)
    graph = None

    # Load environment variables for Neo4j connection
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'src', '.env')
    if not os.path.exists(dotenv_path):
        print(f"Error: .env file not found at {os.path.abspath(dotenv_path)}", flush=True)
        return
    load_dotenv(dotenv_path=dotenv_path, verbose=True)
    print(".env file loaded.", flush=True)
    
    # Retrieve environment variables
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    # Check if environment variables are set
    if not uri or not user or not password:
        print("Error: Neo4j environment variables not set correctly.", flush=True)
        return
    if not google_api_key:
        print("Error: Google API key not set.", flush=True)
        return
    
    print("Environment variables loaded successfully.", flush=True)
    print(f"Neo4j URI: {uri}", flush=True)
    print(f"Neo4j User: {user}", flush=True)
    print("Neo4j Password: [REDACTED]", flush=True)
    print("Google API Key: [REDACTED]", flush=True)
    
    try:
        # Initialize Graphiti with Neo4j connection only - don't use LLM or embedder
        print("Initializing Graphiti with Neo4j connection...", flush=True)
        graph = Graphiti(
            uri=uri,
            user=user,
            password=password
        )
        print("Graphiti initialized successfully.", flush=True)
        
        # Create test data for ingestion
        print("Creating test data for ingestion...", flush=True)
        
        # Create document chunks for ingestion as text episodes
        text_episodes = [
            ("Document chunk about machine learning", 
             "Machine learning is a field of artificial intelligence that uses statistical techniques to give "
             "computer systems the ability to learn from data, without being explicitly programmed."),
            ("Document chunk about knowledge graphs", 
             "Knowledge graphs represent a collection of interlinked descriptions of entities – real-world objects "
             "and events, or abstract concepts. They power intelligent applications and enable AI reasoning.")
        ]
        
        # Create structured data for JSON episodes
        json_episodes = [
            {
                "name": "Machine Learning",
                "type": "Concept",
                "description": "Field of study that gives computers the ability to learn without being explicitly programmed.",
                "related_fields": ["Deep Learning", "Neural Networks", "Data Science"],
                "year_coined": 1959
            },
            {
                "name": "Neo4j",
                "type": "Technology",
                "description": "A graph database management system.",
                "features": ["ACID compliance", "Native graph storage", "Cypher query language"],
                "release_year": 2007
            }
        ]
        
        print(f"Created {len(text_episodes)} text episodes and {len(json_episodes)} JSON episodes for ingestion.", flush=True)
        
        # Ingest text episodes
        for i, (name, content) in enumerate(text_episodes):
            episode_name = f"text_episode_{i+1}"
            print(f"Adding episode '{episode_name}'...", flush=True)
            
            await graph.add_episode(
                name=episode_name,
                episode_body=content,
                source=EpisodeType.text,
                source_description=name,
                reference_time=datetime.now(timezone.utc)
            )
            print(f"Successfully added text episode '{episode_name}'.", flush=True)
        
        # Ingest JSON episodes
        for i, data in enumerate(json_episodes):
            episode_name = f"json_episode_{i+1}"
            print(f"Adding JSON episode '{episode_name}'...", flush=True)
            
            await graph.add_episode(
                name=episode_name,
                episode_body=data,  # Pass the Python dict directly
                source=EpisodeType.json,
                source_description=f"Structured data about {data['name']}",
                reference_time=datetime.now(timezone.utc)
            )
            print(f"Successfully added JSON episode '{episode_name}'.", flush=True)
        
        print("All episodes successfully ingested.", flush=True)
        
        # Verify data ingestion by querying Neo4j directly
        print("Verifying data ingestion by querying Neo4j...", flush=True)
        driver = graph.driver
        
        with driver.session() as session:
            # Query for episodes
            result = session.run(
                "MATCH (e:Episode) RETURN e.name AS name, e.source_type AS source_type LIMIT 10"
            )
            episodes = [record for record in result]
            
            if episodes:
                print(f"Found {len(episodes)} episodes in Neo4j:", flush=True)
                for episode in episodes:
                    print(f"  - {episode['name']} (Type: {episode['source_type']})", flush=True)
            else:
                print("No episodes found in Neo4j.", flush=True)
            
            # Query for concepts extracted by Graphiti
            result = session.run(
                "MATCH (c) WHERE NOT c:Episode RETURN labels(c) AS labels, c.name AS name LIMIT 10"
            )
            entities = [record for record in result]
            
            if entities:
                print(f"Found {len(entities)} entities in Neo4j:", flush=True)
                for entity in entities:
                    print(f"  - {entity['name']} (Type: {entity['labels']})", flush=True)
            else:
                print("No entities found in Neo4j (other than Episodes).", flush=True)
                
    except Exception as e:
        print(f"Error during ingestion or verification: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        # Close the Neo4j driver connection
        if graph and graph.driver:
            try:
                print("Closing Neo4j driver connection...", flush=True)
                await graph.driver.close()
                print("Neo4j driver connection closed.", flush=True)
            except Exception as e:
                print(f"Error closing Neo4j connection: {e}", flush=True)
        
    print("Graphiti ingestion test completed.", flush=True)

async def main():
    print("--- Script execution started (__main__) ---", flush=True)
    await test_graphiti_ingestion()
    # print("--- MINIMAL MAIN FUNCTION EXECUTED ---", flush=True) # No longer minimal
    # await asyncio.sleep(0.01) # No longer needed just for testing main
    print("--- Script execution finished (__main__) ---", flush=True)

if __name__ == "__main__":
    print("--- BEFORE ASYNCIO.RUN(MAIN) ---", flush=True)
    asyncio.run(main())
    print("--- AFTER ASYNCIO.RUN(MAIN) ---", flush=True)
