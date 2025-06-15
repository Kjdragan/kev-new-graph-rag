# src/graph_querying/neo4j_executor.py
import os
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# This placeholder string must match the one expected by the LLM and defined in CypherQueryResult
CURRENT_DATETIME_PLACEHOLDER = "$current_datetime"

class Neo4jConnectionError(Exception):
    """Custom exception for Neo4j connection issues."""
    pass

class Neo4jQueryError(Exception):
    """Custom exception for errors during Neo4j query execution."""
    pass

def get_neo4j_driver():
    """Establishes and verifies a connection to Neo4j, returning a driver instance."""
    load_dotenv() # Ensures .env variables are loaded
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not uri or not username or not password:
        raise Neo4jConnectionError(
            "NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be set in environment variables or .env file."
        )
    try:
        # Using basic_auth for username/password authentication
        driver = GraphDatabase.driver(uri, auth=basic_auth(username, password))
        driver.verify_connectivity() # Check if connection is valid and server is responsive
        print(f"Successfully connected to Neo4j at {uri}")
        return driver
    except Exception as e:
        # Catching a broad exception here as various issues can occur (auth, network, etc.)
        raise Neo4jConnectionError(f"Failed to connect to Neo4j at {uri}: {e}")

def execute_cypher_query(
    query: str,
    parameters: Dict[str, Any],
    database_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Executes a Cypher query against the Neo4j database.

    Args:
        query: The Cypher query string.
        parameters: A dictionary of parameters for the query.
                    If CURRENT_DATETIME_PLACEHOLDER is a key, its value will be replaced
                    with the current ISO 8601 datetime string.
        database_name: The specific Neo4j database to run the query against.
                       If None, uses the database specified by NEO4J_DATABASE env var,
                       or the driver's default database if NEO4J_DATABASE is not set.

    Returns:
        A list of records, where each record is a dictionary representing a row from the result.

    Raises:
        Neo4jConnectionError: If connection to Neo4j fails.
        Neo4jQueryError: If the query execution fails.
    """
    driver = None
    try:
        driver = get_neo4j_driver()
        
        processed_parameters = parameters.copy()
        if CURRENT_DATETIME_PLACEHOLDER in processed_parameters:
            current_dt_iso = datetime.now(timezone.utc).isoformat()
            processed_parameters[CURRENT_DATETIME_PLACEHOLDER] = current_dt_iso
            print(f"Substituted '{CURRENT_DATETIME_PLACEHOLDER}' with '{current_dt_iso}'")

        # Determine the target database for the session
        # Use database_name if provided, else try NEO4J_DATABASE env var, else driver default
        target_database = database_name or os.getenv("NEO4J_DATABASE")
        session_params = {}
        if target_database:
            session_params['database'] = target_database
            print(f"Using Neo4j database: {target_database}")
        else:
            print("Using default Neo4j database for the session.")

        with driver.session(**session_params) as session:
            print(f"Executing Cypher: {query}")
            print(f"With parameters: {processed_parameters}")
            
            # Using session.read_transaction or session.write_transaction can be more robust
            # for handling retries and ensuring atomicity, but session.run is simpler for now.
            result_summary = session.run(query, processed_parameters)
            records = [record.data() for record in result_summary] # Convert records to dictionaries
            
            print(f"Query executed successfully. Returned {len(records)} record(s).")
            return records
            
    except (Neo4jConnectionError, Neo4jQueryError) as e: # Re-raise known errors
        raise e
    except Exception as e:
        # Catch any other unexpected errors during execution
        error_message = f"Error executing Cypher query: {e}\nQuery: {query}\nParams: {processed_parameters if 'processed_parameters' in locals() else parameters}"
        print(f"DEBUG: {error_message}")
        raise Neo4jQueryError(error_message)
    finally:
        if driver:
            driver.close()
            print("Neo4j driver connection closed.")

# Example usage (for testing this module directly)
async def _test_direct_execution():
    print("\n--- Testing Neo4j Executor Directly ---")
    # Ensure your .env file has NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
    # And optionally NEO4J_DATABASE if not using the default 'neo4j'
    
    # Example 1: Create/Merge a test node
    test_query_create = "MERGE (t:TestNode {id: $node_id, name: $name}) SET t.last_tested = $current_datetime RETURN t.name AS name, t.id AS id, t.last_tested as tested_at"
    test_params_create = {"node_id": "executor_test_001", "name": "Neo4jExecutorDirectTestNode", CURRENT_DATETIME_PLACEHOLDER: "will_be_replaced"}
    
    try:
        print("\nExecuting Test Query 1 (Create/Merge Node with datetime)...")
        create_results = execute_cypher_query(test_query_create, test_params_create)
        print(f"Create/Merge Results: {create_results}")

        # Example 2: Match the test node
        if create_results and create_results[0].get('id'):
            node_id_to_match = create_results[0]['id']
            test_query_match = "MATCH (t:TestNode {id: $node_id}) RETURN t.name AS name, t.id as id, t.last_tested as tested_at, $current_datetime AS query_execution_time"
            test_params_match = {"node_id": node_id_to_match, CURRENT_DATETIME_PLACEHOLDER: "will_be_replaced_again"}
            
            print("\nExecuting Test Query 2 (Match Node with datetime)...")
            match_results = execute_cypher_query(test_query_match, test_params_match)
            print(f"Match Results: {match_results}")
        else:
            print("Skipping match query as create/merge did not return expected ID.")

    except (Neo4jConnectionError, Neo4jQueryError) as e:
        print(f"Neo4j direct test execution failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during direct test: {e}")

if __name__ == "__main__":
    import asyncio
    # _test_direct_execution is synchronous but called via asyncio.run for consistency with other main blocks
    asyncio.run(_test_direct_execution())
