"""
Test script to verify embedding dimensions being generated
"""
import os
import asyncio
from dotenv import load_dotenv
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig

async def test_embedding_dimensions():
    load_dotenv()
    
    # Configure environment for Vertex AI ADC authentication
    os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'
    os.environ['GOOGLE_CLOUD_PROJECT'] = os.getenv('GOOGLE_CLOUD_PROJECT')
    os.environ['GOOGLE_CLOUD_LOCATION'] = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
    
    # Test embedding configuration
    embedder = GeminiEmbedder(
        config=GeminiEmbedderConfig(
            embedding_model="gemini-embedding-001",
            output_dimensionality=1536
        )
    )
    
    # Test query
    test_query = "Who created GPT-4?"
    
    print(f"Testing embedding generation for query: '{test_query}'")
    print(f"Configured model: gemini-embedding-001")
    print(f"Configured dimensionality: 1536")
    
    try:
        embeddings = await embedder.create(input_data=[test_query])
        print(f"Raw embeddings response type: {type(embeddings)}")
        print(f"Raw embeddings response: {embeddings}")
        
        if embeddings:
            if isinstance(embeddings, list):
                print(f"Number of embeddings returned: {len(embeddings)}")
                if len(embeddings) > 0:
                    embedding = embeddings[0]
                    print(f"First embedding type: {type(embedding)}")
                    if isinstance(embedding, list):
                        print(f"Generated embedding dimension: {len(embedding)}")
                        print(f"First 5 values: {embedding[:5]}")
                        print(f"Last 5 values: {embedding[-5:]}")
                    else:
                        print(f"First embedding value: {embedding}")
            else:
                print(f"Embeddings is not a list, it's: {type(embeddings)}")
                if hasattr(embeddings, '__len__'):
                    print(f"Length: {len(embeddings)}")
        else:
            print("No embeddings generated")
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_embedding_dimensions())
