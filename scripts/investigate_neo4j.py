#!/usr/bin/env python3
"""
Script to investigate the current state of Neo4j database.
This will help us understand what schema issues exist before resetting.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def investigate_neo4j():
    """Investigate current Neo4j database state."""
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
            # Check database connectivity
            result = session.run("RETURN 'Connected successfully' as status")
            print(f"Connection status: {result.single()['status']}")
            
            # Get all labels
            print("\n=== Current Labels ===")
            result = session.run("CALL db.labels()")
            labels = [record["label"] for record in result]
            print(f"Found {len(labels)} labels: {labels}")
            
            # Get all relationship types
            print("\n=== Current Relationship Types ===")
            result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in result]
            print(f"Found {len(rel_types)} relationship types: {rel_types}")
            
            # Count nodes and relationships
            print("\n=== Node and Relationship Counts ===")
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]
            print(f"Total nodes: {node_count}")
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]
            print(f"Total relationships: {rel_count}")
            
            # Sample some nodes to see their structure
            if node_count > 0:
                print("\n=== Sample Node Properties ===")
                result = session.run("MATCH (n) RETURN labels(n) as labels, keys(n) as properties LIMIT 5")
                for i, record in enumerate(result):
                    print(f"Node {i+1}: Labels={record['labels']}, Properties={record['properties']}")
            
            # Check for specific properties mentioned in the plan
            print("\n=== Checking for Expected Properties ===")
            expected_props = ["name_embedding", "summary", "name"]
            for prop in expected_props:
                result = session.run(f"MATCH (n) WHERE n.{prop} IS NOT NULL RETURN count(n) as count")
                count = result.single()["count"]
                print(f"Nodes with '{prop}' property: {count}")
            
            # Check for Entity label specifically mentioned in the plan
            print("\n=== Checking for Entity Label ===")
            result = session.run("MATCH (n:Entity) RETURN count(n) as count")
            entity_count = result.single()["count"]
            print(f"Nodes with 'Entity' label: {entity_count}")
            
        driver.close()
        print("\n=== Investigation Complete ===")
        
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return False
    
    return True

if __name__ == "__main__":
    investigate_neo4j()
