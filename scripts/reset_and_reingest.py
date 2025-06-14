#!/usr/bin/env python3
"""
Script to reset Neo4j database and re-ingest data using the extraction pipeline.
This will clear all existing data and re-run the ingestion with the generic ontology.
"""

import os
import sys
import asyncio
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

def reset_neo4j_database():
    """Clear all nodes and relationships from Neo4j database."""
    load_dotenv()
    
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    print(f"Connecting to Neo4j at: {uri}")
    print(f"Database: {database}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # Get current counts before reset
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]
            
            print(f"Before reset: {node_count} nodes, {rel_count} relationships")
            
            # Clear all relationships first
            print("Clearing all relationships...")
            session.run("MATCH ()-[r]->() DELETE r")
            
            # Clear all nodes
            print("Clearing all nodes...")
            session.run("MATCH (n) DELETE n")
            
            # Verify database is empty
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]
            
            print(f"After reset: {node_count} nodes, {rel_count} relationships")
            
            if node_count == 0 and rel_count == 0:
                print("✅ Database reset successful!")
                return True
            else:
                print("❌ Database reset failed - some data remains")
                return False
                
        driver.close()
        
    except Exception as e:
        print(f"Error resetting Neo4j database: {e}")
        return False

async def run_ingestion():
    """Run the ingestion pipeline with generic ontology."""
    print("\n=== Starting Data Ingestion ===")
    
    # Import the ingestion script - fix the import path
    try:
        # Add the scripts directory to sys.path temporarily
        scripts_dir = Path(__file__).parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        
        # Import the main function from the ingestion script
        import ingest_gdrive_documents
        
        # Run the ingestion with generic ontology
        print("Running ingestion with generic_ontology...")
        await ingest_gdrive_documents.main()
        print("✅ Ingestion completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_ingestion():
    """Verify that data was successfully ingested."""
    load_dotenv()
    
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    print("\n=== Verifying Ingestion Results ===")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # Get all labels
            result = session.run("CALL db.labels()")
            labels = [record["label"] for record in result]
            print(f"Labels found: {labels}")
            
            # Get all relationship types
            result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in result]
            print(f"Relationship types found: {rel_types}")
            
            # Count nodes and relationships
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]
            
            print(f"Total nodes: {node_count}")
            print(f"Total relationships: {rel_count}")
            
            # Sample some nodes by label
            for label in labels:
                if label != "Episodic":  # Skip Graphiti internal nodes
                    result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    count = result.single()["count"]
                    print(f"Nodes with '{label}' label: {count}")
                    
                    if count > 0:
                        # Show sample properties
                        result = session.run(f"MATCH (n:{label}) RETURN keys(n) as properties LIMIT 1")
                        properties = result.single()["properties"]
                        print(f"  Sample properties: {properties}")
            
            if node_count > 1 and rel_count > 0:  # More than just Episodic nodes
                print("✅ Ingestion verification successful!")
                return True
            else:
                print("❌ Ingestion verification failed - insufficient data")
                return False
                
        driver.close()
        
    except Exception as e:
        print(f"Error verifying ingestion: {e}")
        return False

async def main():
    """Main function to reset and re-ingest data."""
    print("🔄 Starting Neo4j Reset and Re-ingestion Process")
    print("=" * 50)
    
    # Step 1: Reset the database
    print("Step 1: Resetting Neo4j database...")
    if not reset_neo4j_database():
        print("❌ Database reset failed. Exiting.")
        return False
    
    # Step 2: Run ingestion
    print("\nStep 2: Running data ingestion...")
    if not await run_ingestion():
        print("❌ Data ingestion failed. Exiting.")
        return False
    
    # Step 3: Verify results
    print("\nStep 3: Verifying ingestion results...")
    if not verify_ingestion():
        print("❌ Ingestion verification failed.")
        return False
    
    print("\n🎉 Reset and re-ingestion process completed successfully!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    asyncio.run(main())
