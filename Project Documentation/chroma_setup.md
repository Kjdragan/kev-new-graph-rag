# ChromaDB Setup and Usage Guide

This document outlines how to set up and use ChromaDB with the kev-new-graph-rag project.

## Docker Setup

ChromaDB runs in a Docker container configured with authentication. Use the provided script to manage the container:

```powershell
# Start the ChromaDB container
.\scripts\start_chroma_docker.ps1 start

# Check status
.\scripts\start_chroma_docker.ps1 status

# View logs
.\scripts\start_chroma_docker.ps1 logs

# Stop the container
.\scripts\start_chroma_docker.ps1 stop

# Restart the container
.\scripts\start_chroma_docker.ps1 restart
```

The ChromaDB server will be running at http://localhost:8000 with the following credentials:
- Username: admin
- Password: admin123

## Configuration

ChromaDB connection settings are stored in the `.env` file with these defaults:

```
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=documents
CHROMA_AUTH_ENABLED=true
CHROMA_USERNAME=admin
CHROMA_PASSWORD=admin123
```

Modify these settings as needed for your environment.

## Document Ingestion

The project uses a unified ingestion pipeline that processes documents from Google Drive and stores them in both ChromaDB (vector store) and Neo4j (graph database).

```powershell
# Run the ingestion script with uv
uv run scripts/ingest_gdrive_documents.py
```

The script will:
1. Fetch documents from the Google Drive folder specified in the `.env` file
2. Parse them using LlamaParse
3. Store document chunks and their embeddings in ChromaDB
4. Store whole document nodes with embeddings in Neo4j

## ChromaDB Data Structure

Documents in ChromaDB are stored with:
- Unique ID: `{file_id}_p{page_number}_{uuid}`
- Text: The raw document text
- Embedding: The Gemini-generated embedding vector (1024 dimensions)
- Metadata:
  - `source_file`: Original file name
  - `file_id`: Google Drive file ID
  - `page_number`: Page number within document
  - `mime_type`: File MIME type
  - `ingested_at`: Timestamp

## Search and Retrieval

You can search documents in ChromaDB using the `ChromaIngester.search()` method:

```python
from utils.chroma_ingester import ChromaIngester
from utils.config_models import ChromaDBConfig
from utils.embedding import CustomGeminiEmbedding
from utils.config import Config

# Load configuration
config = Config()
embedding_config = config.get_embedding_config()
chromadb_config = config.get_chromadb_config()

# Initialize components
embedding_model = CustomGeminiEmbedding(embedding_config)
chroma_ingester = ChromaIngester(chromadb_config, embedding_model)

# Search with optional metadata filters
results = chroma_ingester.search(
    query="Your search query here", 
    n_results=5,
    filters={"source_file": "specific_document.pdf"}  # Optional
)

# Process results
for i, doc in enumerate(results['documents'][0]):
    print(f"Result {i+1}: {doc[:100]}...")  # Print first 100 chars of each result
    print(f"Distance: {results['distances'][0][i]}")
    print(f"Metadata: {results['metadatas'][0][i]}")
    print("---")
```

## Testing

To verify your ChromaDB setup is working correctly, first make sure the Docker container is running, then run a simple test:

```powershell
uv run scripts/test_chroma_connection.py
```
