import os
import sys # Added for explicit flushing
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

def test_neo4j_connection():
    """
    Tests the connection to Neo4j AuraDB using credentials from .env file.
    """
    print("Script started.", flush=True)

    dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'src', '.env')
    print(f"Looking for .env file at: {os.path.abspath(dotenv_path)}", flush=True)

    if not os.path.exists(dotenv_path):
        print(f"Error: .env file not found at {os.path.abspath(dotenv_path)}", flush=True)
        return

    loaded = load_dotenv(dotenv_path=dotenv_path, verbose=True) # Added verbose
    print(f".env file loaded: {loaded}", flush=True)


    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    print(f"Retrieved NEO4J_URI: {'Set' if uri else 'Not Set'}", flush=True)
    print(f"Retrieved NEO4J_USER: {'Set' if user else 'Not Set'}", flush=True)
    # Not printing password for security, just checking if it's set
    print(f"Retrieved NEO4J_PASSWORD: {'Set' if password else 'Not Set'}", flush=True)


    if not all([uri, user, password]):
        print("Error: NEO4J_URI, NEO4J_USER, or NEO4J_PASSWORD not found in .env file.", flush=True)
        print(f"Please ensure .env is at: {os.path.abspath(dotenv_path)} and variables are set.", flush=True)
        return

    driver = None
    try:
        print(f"Attempting to connect to Neo4j AuraDB at {uri}...", flush=True)
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("Successfully connected to Neo4j AuraDB!", flush=True)

        with driver.session() as session:
            print("Running a simple test query...", flush=True)
            result = session.run("MERGE (t:TestConnectionNode {name: 'CascadeConnectionTest'}) ON CREATE SET t.created = timestamp() RETURN t.name AS name, t.created AS created_at")
            record = result.single()
            if record:
                print(f"Test query successful. Node '{record['name']}' found/created at {record['created_at']}.", flush=True)
            else:
                print("Test query ran, but no record returned (this is unexpected).", flush=True)
            
            session.run("MATCH (t:TestConnectionNode {name: 'CascadeConnectionTest'}) DELETE t")
            print("Test node cleaned up.", flush=True)

    except exceptions.AuthError as e:
        print(f"Authentication failed: {e}", flush=True)
    except exceptions.ServiceUnavailable as e:
        print(f"Could not connect to Neo4j at {uri}: {e}", flush=True)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", flush=True)
    finally:
        if driver:
            driver.close()
            print("Neo4j connection closed.", flush=True)
    
    print("Script finished.", flush=True)

if __name__ == "__main__":
    test_neo4j_connection()
