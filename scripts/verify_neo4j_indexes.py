import os
import sys
from typing import List, Dict, Any, Tuple

import dotenv
from neo4j import GraphDatabase, Neo4jDriver
from loguru import logger
from pathlib import Path

# Add project root to path for imports if necessary (though not strictly needed for this script)
# sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logger.remove() # remove default logger
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)

# Define the expected Graphiti indexes
EXPECTED_INDEXES = {
    "episode_content": {
        "entityType": "NODE",
        "labelsOrTypes": ["Episodic"],
        "properties": sorted(["content", "source", "source_description", "group_id"])
    },
    "node_name_and_summary": {
        "entityType": "NODE",
        "labelsOrTypes": ["Entity"],
        "properties": sorted(["name", "summary", "group_id"])
    },
    "community_name": {
        "entityType": "NODE",
        "labelsOrTypes": ["Community"],
        "properties": sorted(["name", "group_id"])
    },
    "edge_name_and_fact": {
        "entityType": "RELATIONSHIP",
        "labelsOrTypes": ["RELATES_TO"],
        "properties": sorted(["name", "fact", "group_id"])
    }
}

def load_env_vars() -> Tuple[str, str, str, str]:
    """Loads Neo4j connection details from .env file."""
    # Construct path to .env in the project root (one level up from 'scripts' directory)
    env_path = Path(__file__).resolve().parent.parent / ".env"
    
    if not env_path.exists():
        logger.error(f".env file not found at expected path: {env_path}")
        # As a fallback, try loading from CWD in case the script is run from project root directly
        logger.info("Attempting to load .env from current working directory as a fallback.")
        load_success_cwd = dotenv.load_dotenv(override=True)
        logger.info(f"dotenv.load_dotenv (CWD fallback) success status: {load_success_cwd}")
    else:
        logger.info(f"Attempting to load .env file from explicit path: {env_path}")
        load_success_explicit = dotenv.load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"dotenv.load_dotenv (explicit path) success status: {load_success_explicit}")

    # Immediately check if variables are loaded
    uri_check = os.getenv("NEO4J_URI")
    user_check = os.getenv("NEO4J_USER")
    password_check = os.getenv("NEO4J_PASSWORD")
    logger.info(f"NEO4J_URI after load attempt: {'SET' if uri_check else 'NOT SET'}")
    logger.info(f"NEO4J_USER after load attempt: {'SET' if user_check else 'NOT SET'}")
    logger.info(f"NEO4J_PASSWORD after load attempt: {'SET' if password_check else 'NOT SET'}")

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    if not all([uri, user, password]):
        logger.error("Missing Neo4j connection details (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) after attempting to load .env file.")
        logger.error("Please ensure the .env file is correctly formatted and located either in the project root or the current working directory.")
        sys.exit(1)
    return uri, user, password, database

def get_existing_indexes(driver: Neo4jDriver, db_name: str) -> List[Dict[str, Any]]:
    """Fetches all full-text indexes from the database."""
    try:
        with driver.session(database=db_name) as session:
            results = session.run("SHOW FULLTEXT INDEXES;")
            indexes = [record.data() for record in results]
            logger.info(f"Found {len(indexes)} full-text indexes in database '{db_name}'.")
            return indexes
    except Exception as e:
        logger.error(f"Error fetching indexes from Neo4j: {e}")
        return []

def verify_indexes(existing_indexes: List[Dict[str, Any]]):
    """Compares existing indexes against expected Graphiti indexes."""
    logger.info("Verifying Neo4j full-text indexes for Graphiti...")
    found_expected_indexes = {name: False for name in EXPECTED_INDEXES}

    for expected_name, expected_config in EXPECTED_INDEXES.items():
        logger.info(f"\nChecking for index: '{expected_name}'")
        found_match = False
        for existing_index in existing_indexes:
            if existing_index.get("name") == expected_name:
                found_match = True
                found_expected_indexes[expected_name] = True
                logger.success(f"  [FOUND] Index '{expected_name}' exists.")
                
                # Verify configuration
                correct_config = True
                if existing_index.get("entityType") != expected_config["entityType"]:
                    logger.error(f"    [MISMATCH] EntityType: Expected '{expected_config['entityType']}', Got '{existing_index.get('entityType')}'")
                    correct_config = False
                
                # labelsOrTypes can be None for older Neo4j versions for relationship indexes, 
                # or a list. Graphiti expects specific labels/types.
                existing_labels = existing_index.get("labelsOrTypes")
                if sorted(existing_labels if existing_labels else []) != sorted(expected_config["labelsOrTypes"]):
                    logger.error(f"    [MISMATCH] Labels/Types: Expected {expected_config['labelsOrTypes']}, Got {existing_labels}")
                    correct_config = False

                existing_props = sorted(existing_index.get("properties", []))
                if existing_props != expected_config["properties"]:
                    logger.error(f"    [MISMATCH] Properties: Expected {expected_config['properties']}, Got {existing_props}")
                    correct_config = False
                
                state = existing_index.get("state")
                if state == "ONLINE":
                    logger.info(f"    [STATE] Index is ONLINE.")
                elif state == "POPULATING":
                    logger.warning(f"    [STATE] Index is POPULATING ({existing_index.get('populationPercent', 0):.2f}%). May not be fully functional yet.")
                else:
                    logger.warning(f"    [STATE] Index state is '{state}'.")

                if correct_config and state == "ONLINE":
                    logger.success(f"    [CONFIG] Index '{expected_name}' appears correctly configured and ONLINE.")
                elif correct_config and state != "ONLINE":
                    logger.warning(f"    [CONFIG] Index '{expected_name}' appears correctly configured but is NOT ONLINE (State: {state}).")
                else:
                    logger.error(f"    [CONFIG] Index '{expected_name}' has configuration mismatches.")
                break # Move to next expected index
        
        if not found_match:
            logger.error(f"  [MISSING] Expected index '{expected_name}' was not found.")

    logger.info("\n--- Summary ---")
    all_good = True
    for name, found in found_expected_indexes.items():
        if not found:
            logger.error(f"Required Graphiti index '{name}' is MISSING.")
            all_good = False
        # Further checks for configuration can be added here if needed, but covered above
    
    if all_good and all(any(idx.get('name') == name and idx.get('state') == 'ONLINE' for idx in existing_indexes) for name in EXPECTED_INDEXES if found_expected_indexes[name]):
        # This check is a bit redundant with above but ensures all found are also online
        is_fully_online = True
        for name in EXPECTED_INDEXES:
            if found_expected_indexes[name]:
                matching_idx = next((idx for idx in existing_indexes if idx.get('name') == name), None)
                if not (matching_idx and matching_idx.get('state') == 'ONLINE'):
                    is_fully_online = False
                    break
        if is_fully_online:
             logger.success("All required Graphiti indexes appear to be present, correctly configured, and ONLINE.")
        else:
            logger.warning("Some required Graphiti indexes are present and configured but NOT YET ONLINE or have issues. Review details above.")
            all_good = False # Ensure overall status reflects this

    elif not all_good:
        logger.error("One or more required Graphiti indexes are missing or misconfigured. Please review details above and recreate them if necessary.")
    else: # All found, but maybe not all online or some config issue detailed above
        logger.warning("All required Graphiti indexes were found, but some may have configuration issues or are not ONLINE. Review details above.")

    if not all_good:
        logger.info("\nTo recreate indexes, you can use Cypher commands like:")
        logger.info("DROP FULLTEXT INDEX <index_name> IF EXISTS;")
        logger.info("CREATE FULLTEXT INDEX episode_content IF NOT EXISTS FOR (e:Episodic) ON EACH [e.content, e.source, e.source_description, e.group_id];")
        logger.info("CREATE FULLTEXT INDEX node_name_and_summary IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.summary, n.group_id];")
        logger.info("CREATE FULLTEXT INDEX community_name IF NOT EXISTS FOR (n:Community) ON EACH [n.name, n.group_id];")
        logger.info("CREATE FULLTEXT INDEX edge_name_and_fact IF NOT EXISTS FOR ()-[e:RELATES_TO]-() ON EACH [e.name, e.fact, e.group_id];")


def main():
    """Main function to verify Neo4j indexes."""
    uri, user, password, db_name = load_env_vars()
    
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        logger.info(f"Successfully connected to Neo4j at {uri} (Database: {db_name}).")
        
        existing_indexes = get_existing_indexes(driver, db_name)
        if existing_indexes is not None:
            verify_indexes(existing_indexes)
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.exception("Details:")
    finally:
        if driver:
            driver.close()
            logger.info("Neo4j connection closed.")

if __name__ == "__main__":
    main()
