import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment
load_dotenv()
uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USERNAME') 
password = os.getenv('NEO4J_PASSWORD')

# Check Neo4j constraints and indexes
driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    # Check for vector indexes
    result = session.run('SHOW INDEXES')
    indexes = [record for record in result]
    
    print('Neo4j Indexes:')
    for idx in indexes:
        if 'vector' in str(idx).lower():
            print(f'  {idx}')
    
    # Check embedding dimensions on nodes
    result = session.run('MATCH (n) WHERE n.name_embedding IS NOT NULL RETURN n.name_embedding[0..5] as sample_embedding, size(n.name_embedding) as dimension LIMIT 5')
    embeddings = [record for record in result]
    
    print('\nEmbedding Dimensions in Database:')
    for emb in embeddings:
        if emb['dimension']:
            print(f'  Dimension: {emb["dimension"]}')
            print(f'  Sample: {emb["sample_embedding"]}')
        
driver.close()
