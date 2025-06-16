"""
Clears all nodes and relationships from the Neo4j database.

WARNING: This script will delete ALL data in the configured Neo4j database.
Ensure you are targeting the correct database and have backups if needed.
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j") # Default to 'neo4j' if not specified

def clear_database():
    """Connects to Neo4j and deletes all nodes and relationships."""
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("Error: NEO4J_URI, NEO4J_USERNAME, or NEO4J_PASSWORD environment variables are not set.")
        print("Please ensure your .env file is correctly configured.")
        return

    driver = None
    try:
        print(f"Connecting to Neo4j at {NEO4J_URI} (Database: {NEO4J_DATABASE})...")
        auth_token = basic_auth(NEO4J_USERNAME, NEO4J_PASSWORD)
        driver = GraphDatabase.driver(NEO4J_URI, auth=auth_token)
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")

        with driver.session(database=NEO4J_DATABASE) as session:
            print("Attempting to delete all nodes and relationships...")
            # Check if the database is empty first to avoid errors on empty DBs with some Aura versions
            result = session.run("MATCH (n) RETURN count(n) AS node_count")
            record = result.single()
            node_count = record["node_count"] if record else 0

            if node_count == 0:
                print("Database is already empty. No action taken.")
            else:
                print(f"Found {node_count} nodes. Proceeding with deletion.")
                # Using apoc.periodic.iterate for potentially large databases if APOC is available
                # Otherwise, a simple MATCH DETACH DELETE n might timeout.
                # For now, using the simpler version, assuming the DB isn't excessively large.
                # If timeouts occur, consider apoc.periodic.iterate or batching.
                query = "MATCH (n) DETACH DELETE n"
                session.run(query)
                print("Successfully deleted all nodes and relationships.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.close()
            print("Neo4j connection closed.")

if __name__ == "__main__":
    print("WARNING: This script will delete ALL data in the configured Neo4j database.")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_database()
    else:
        print("Operation cancelled by user.")
