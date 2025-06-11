"""
Database management utility functions for Neo4j operations.
Provides functionality for Neo4j database administration tasks.
"""
import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

# Set up logging
logger = logging.getLogger(__name__)

def load_neo4j_credentials():
    """
    Load Neo4j credentials from the .env file.
    
    Returns:
        tuple: (uri, user, password) if successful, (None, None, None) otherwise
    """
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'src', '.env')
    logger.info(f"Loading .env from: {os.path.abspath(dotenv_path)}")
    
    if not os.path.exists(dotenv_path):
        logger.error(f"Error: .env file not found at {os.path.abspath(dotenv_path)}")
        return None, None, None
    
    load_dotenv(dotenv_path=dotenv_path)
    
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, user, password]):
        logger.error("Error: NEO4J_URI, NEO4J_USER, or NEO4J_PASSWORD not found in .env file.")
        return None, None, None
    
    return uri, user, password

def clear_database():
    """
    Clears all data (nodes and relationships) from the Neo4j AuraDB database.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("Starting database clearing process...")
    
    uri, user, password = load_neo4j_credentials()
    if not all([uri, user, password]):
        return False
    
    driver = None
    try:
        print(f"Connecting to Neo4j at {uri}...")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("Connected to Neo4j AuraDB.")
        
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
                print(f"Before clearing: {nodes_before} nodes and {relationships_before} relationships found.")
            
            if nodes_before > 0 or relationships_before > 0:
                print("Clearing all nodes and relationships from the database...")
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
                    print("Database cleared successfully. All nodes and relationships deleted.")
                    return True
                else:
                    print(f"Warning: After clearing, database still contains {verify_record['nodes']} nodes and {verify_record['relationships']} relationships.")
                    return False
            else:
                print("Database is already empty. Nothing to clear.")
                return True
                
    except exceptions.AuthError as e:
        print(f"Authentication failed: {e}")
        return False
    except exceptions.ServiceUnavailable as e:
        print(f"Could not connect to Neo4j: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    finally:
        if driver:
            driver.close()
            print("Neo4j connection closed.")
    
    print("Database clearing process completed.")
    return True

def get_database_stats():
    """
    Gets statistics about the current Neo4j database.
    
    Returns:
        dict: Statistics including node and relationship counts, or None if unsuccessful
    """
    uri, user, password = load_neo4j_credentials()
    if not all([uri, user, password]):
        return None
    
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        
        stats = {}
        with driver.session() as session:
            # Get node statistics
            node_result = session.run("""
                MATCH (n)
                RETURN labels(n) AS label, count(*) AS count
            """)
            
            node_stats = {}
            for record in node_result:
                label = ":".join(record["label"]) if record["label"] else "unlabeled"
                node_stats[label] = record["count"]
            
            stats["nodes"] = node_stats
            
            # Get relationship statistics
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(*) AS count
            """)
            
            rel_stats = {}
            for record in rel_result:
                rel_stats[record["type"]] = record["count"]
            
            stats["relationships"] = rel_stats
            
            # Get total counts
            count_result = session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->()
                RETURN count(DISTINCT n) AS nodes, count(DISTINCT r) AS relationships
            """)
            count_record = count_result.single()
            if count_record:
                stats["total_nodes"] = count_record["nodes"]
                stats["total_relationships"] = count_record["relationships"]
        
        return stats
        
    except Exception as e:
        print(f"Error getting database statistics: {e}")
        return None
    finally:
        if driver:
            driver.close()
