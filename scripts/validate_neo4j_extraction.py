"""
Neo4j Validation Script for Knowledge Graph Extraction

This script connects to Neo4j and runs validation queries to assess the quality
of the knowledge graph extraction process.
"""

import os
import sys
from pathlib import Path
import dotenv
from neo4j import GraphDatabase
from loguru import logger

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO")
logger.add(
    "logs/neo4j_validation.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)

def load_env():
    """Load environment variables from .env file"""
    dotenv.load_dotenv()
    
    # Check if Neo4j credentials are available
    required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please ensure these are set in your .env file")
        sys.exit(1)
    
    return {
        "uri": os.getenv("NEO4J_URI"),
        "user": os.getenv("NEO4J_USER"),
        "password": os.getenv("NEO4J_PASSWORD"),
        "database": os.getenv("NEO4J_DATABASE", "neo4j")
    }

def run_validation_query(session, query, description):
    """Run a validation query and log the results"""
    logger.info(f"Running query: {description}")
    try:
        result = session.run(query)
        records = list(result)
        logger.info(f"Query results ({len(records)} records):")
        
        # Format and display results
        if records:
            # Get column names from first record
            columns = records[0].keys()
            
            # Print header
            header = " | ".join(columns)
            separator = "-" * len(header)
            logger.info(separator)
            logger.info(header)
            logger.info(separator)
            
            # Print rows
            for record in records:
                row_values = []
                for col in columns:
                    value = record[col]
                    # Format value based on type
                    if isinstance(value, (list, tuple)):
                        formatted_value = str(value)
                    else:
                        formatted_value = str(value)
                    row_values.append(formatted_value)
                logger.info(" | ".join(row_values))
            
            logger.info(separator)
        else:
            logger.info("No results returned")
        
        return records
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return []

def validate_neo4j_extraction():
    """Run validation queries to assess extraction quality"""
    # Load environment variables
    neo4j_config = load_env()
    
    # Connect to Neo4j
    logger.info(f"Connecting to Neo4j at {neo4j_config['uri']}...")
    try:
        driver = GraphDatabase.driver(
            neo4j_config["uri"],
            auth=(neo4j_config["user"], neo4j_config["password"])
        )
        
        # Test connection
        with driver.session(database=neo4j_config["database"]) as session:
            logger.info("Connection successful!")
            
            # Run validation queries
            logger.info("\n=== BASIC VALIDATION QUERIES ===\n")
            
            # 1. Count entities by type
            query1 = """
            MATCH (n) 
            RETURN labels(n) as EntityType, count(*) as Count
            ORDER BY Count DESC
            """
            run_validation_query(session, query1, "Count entities by type")
            
            # 2. Check relationship distribution
            query2 = """
            MATCH ()-[r]->() 
            RETURN type(r) as RelationshipType, count(*) as Count
            ORDER BY Count DESC
            """
            run_validation_query(session, query2, "Check relationship distribution")
            
            # 3. Find isolated nodes (potential extraction errors)
            query3 = """
            MATCH (n)
            WHERE NOT (n)--()
            RETURN labels(n) as EntityType, n.entity_name as EntityName, count(*) as Count
            ORDER BY Count DESC
            """
            run_validation_query(session, query3, "Find isolated nodes (potential extraction errors)")
            
            # 4. Check property completeness
            query4 = """
            MATCH (n)
            RETURN labels(n) as EntityType, 
                   count(*) as TotalCount,
                   sum(CASE WHEN n.description IS NOT NULL THEN 1 ELSE 0 END) as HasDescription,
                   sum(CASE WHEN n.properties IS NOT NULL THEN 1 ELSE 0 END) as HasProperties
            """
            run_validation_query(session, query4, "Check property completeness")
            
            # 5. Sample of each entity type
            query5 = """
            MATCH (n)
            WITH labels(n) as EntityType, collect(n) as Nodes
            UNWIND Nodes[0..3] as SampleNode
            RETURN EntityType, SampleNode.entity_name as Name, SampleNode.description as Description
            """
            run_validation_query(session, query5, "Sample of each entity type")
            
            # 6. Sample of each relationship type
            query6 = """
            MATCH (a)-[r]->(b)
            WITH type(r) as RelType, collect(r) as Rels
            UNWIND Rels[0..3] as SampleRel
            MATCH (src)-[SampleRel]->(dst)
            RETURN RelType, 
                   labels(src)[0] as SourceType, src.entity_name as SourceName,
                   labels(dst)[0] as TargetType, dst.entity_name as TargetName
            """
            run_validation_query(session, query6, "Sample of each relationship type")
            
            # 7. Check for entity coherence (similar entities with different types)
            query7 = """
            MATCH (n)
            WITH n.entity_name as Name, collect(distinct labels(n)) as Types
            WHERE size(Types) > 1
            RETURN Name, Types, count(*) as Count
            ORDER BY Count DESC
            LIMIT 10
            """
            run_validation_query(session, query7, "Check for entity coherence")
            
            logger.info("\n=== VALIDATION COMPLETE ===\n")
            
    except Exception as e:
        logger.error(f"Error connecting to Neo4j: {e}")
        sys.exit(1)
    finally:
        if 'driver' in locals():
            driver.close()
            logger.info("Neo4j connection closed")

if __name__ == "__main__":
    validate_neo4j_extraction()
