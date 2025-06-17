import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

def clear_neo4j_database():
    """
    Clears all data (nodes and relationships) from the Neo4j AuraDB database.
    """
    print("Starting database clearing process...", flush=True)

    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    print(f"Loading .env from: {os.path.abspath(dotenv_path)}", flush=True)

    if not os.path.exists(dotenv_path):
        print(f"Error: .env file not found at {os.path.abspath(dotenv_path)}", flush=True)
        return

    loaded = load_dotenv(dotenv_path=dotenv_path, verbose=True)
    print(f".env file loaded: {loaded}", flush=True)

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        print("Error: NEO4J_URI, NEO4J_USER, or NEO4J_PASSWORD not found in .env file.", flush=True)
        return

    driver = None
    try:
        print(f"Connecting to Neo4j at {uri}...", flush=True)
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("Connected to Neo4j AuraDB.", flush=True)

        with driver.session() as session:
            # First, get count of nodes and relationships before deletion
            count_result = session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->()
                RETURN count(DISTINCT n) AS nodes, count(DISTINCT r) AS relationships
            """)
            count_record = count_result.single()
            
            if count_record:
                nodes_before = count_record['nodes']
                relationships_before = count_record['relationships']
                print(f"Before clearing: {nodes_before} nodes and {relationships_before} relationships found.", flush=True)
            
            if nodes_before > 0 or relationships_before > 0:
                print("Clearing all nodes and relationships from the database...", flush=True)
                # Delete all nodes and relationships
                clear_result = session.run("MATCH (n) DETACH DELETE n")
                clear_result.consume()  # Ensure query completes
                
                # Verify deletion
                verify_result = session.run("""
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]->()
                    RETURN count(DISTINCT n) AS nodes, count(DISTINCT r) AS relationships
                """)
                verify_record = verify_result.single()
                
                if verify_record and verify_record['nodes'] == 0 and verify_record['relationships'] == 0:
                    print("Database cleared successfully. All nodes and relationships deleted.", flush=True)
                else:
                    print(f"Warning: After clearing, database still contains {verify_record['nodes']} nodes and {verify_record['relationships']} relationships.", flush=True)
            else:
                print("Database is already empty. Nothing to clear.", flush=True)

    except exceptions.AuthError as e:
        print(f"Authentication failed: {e}", flush=True)
    except exceptions.ServiceUnavailable as e:
        print(f"Could not connect to Neo4j: {e}", flush=True)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", flush=True)
    finally:
        if driver:
            driver.close()
            print("Neo4j connection closed.", flush=True)
    
    print("Database clearing process completed.", flush=True)

if __name__ == "__main__":
    clear_neo4j_database()
