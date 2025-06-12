# Kev Graph RAG

A comprehensive Graph-enhanced RAG (Retrieval Augmented Generation) system utilizing Google Drive, ChromaDB vector storage, Neo4j graph database, and Google Gemini models.

## Overview

Kev Graph RAG implements a unified ingestion pipeline that processes documents from Google Drive, parses them using LlamaParse, and stores them in both ChromaDB (vector database) and Neo4j (graph database). The dual-database approach provides enhanced retrieval capabilities by combining vector-based semantic similarity with graph-based contextual relationships. The system leverages Google's Gemini embedding models to generate high-quality semantic embeddings for documents.

## Quick Setup Guide

### Prerequisites

- Python 3.13+
- Docker Desktop
- Google Cloud account with API access and a valid API key
- Neo4j AuraDB instance
- LlamaParse API key
- Google Drive service account credentials

### Installation Steps

1. **Clone the repository**

2. **Set up environment variables**

   Create a `.env` file in the project root with the following variables:

   ```
   # Google API
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_DRIVE_CREDENTIALS_PATH=C:\path\to\service_account_key.json
   GOOGLE_DRIVE_IMPERSONATED_USER_EMAIL=user@example.com
   GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id
   
   # LlamaParse
   LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key
   
   # ChromaDB
   CHROMA_HOST=localhost
   CHROMA_PORT=8000
   CHROMA_COLLECTION_NAME=documents
   CHROMA_AUTH_ENABLED=false
   CHROMA_USERNAME=admin
   CHROMA_PASSWORD=admin123
   
   # Neo4j
   NEO4J_URI=neo4j+s://your-instance-id.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   NEO4J_DATABASE=neo4j
   NEO4J_RETRY_COUNT=3
   NEO4J_RETRY_INTERVAL=1.0
   ```

3. **Install dependencies using uv**

   ```powershell
   uv sync
   ```

4. **Start ChromaDB Docker container**

   ```powershell
   .\scripts\start_chroma_docker.ps1
   ```

   Verify it's running:

   ```powershell
   .\scripts\start_chroma_docker.ps1 status
   ```

## Configuration

### config.yaml

Ensure you have a `config.yaml` file in the project root with the following structure:

```yaml
gemini:
  embeddings:
    model_id: gemini-embedding-001
    output_dimensionality: 1536
```

## Running the Ingestion Pipeline

To ingest documents from your Google Drive folder:

```powershell
uv run scripts\ingest_gdrive_documents.py
```

This orchestration script will:

1. Fetch documents from the configured Google Drive folder
2. Parse them using LlamaParse
3. Generate embeddings using Gemini
4. Store document chunks in ChromaDB
5. Store full documents with metadata in Neo4j

You can monitor the progress in the console and detailed logs in the `logs` directory.

## Key Components

### ChromaDB Vector Storage

- **Purpose**: Stores document chunks with vector embeddings for similarity search
- **Implementation**: Docker-based deployment with persistent storage
- **Management**: Use `.\scripts\start_chroma_docker.ps1` to start/stop/check status
- **Configuration**: Collection settings in `.env` and embedding dimensions in `config.yaml`

### LlamaParse Document Processing

- **Purpose**: Extracts text and metadata from various document formats
- **Capabilities**: Handles PDFs, Word documents, text files, and more
- **Configuration**: API key in `.env` file

### Embedding Generation with Google Gemini

- **Purpose**: Generates semantic embeddings for document chunks
- **Implementation**: `CustomGeminiEmbedding` class in `utils/embedding.py`
- **Configuration**: Model name and dimensions in `config.yaml`, API key in `.env`

### Neo4j Graph Database

- **Purpose**: Stores document metadata and relationships in a graph structure
- **Implementation**: Uses Neo4j vector search capabilities for hybrid retrieval
- **Schema**: Documents stored as nodes with metadata as properties
- **Features**: Supports primitive property types and arrays for efficient indexing and search

### Google Drive Integration

- **Purpose**: Fetches documents from specified Google Drive folders
- **Authentication**: Service account with optional user impersonation
- **Implementation**: `GDriveReader` class in `utils/gdrive_reader.py`

## Project Structure

- `utils/`: Core utility modules
  - `embedding.py`: Custom Gemini embedding implementation
  - `chroma_ingester.py`: ChromaDB integration
  - `neo4j_ingester.py`: Neo4j database operations
  - `gdrive_reader.py`: Google Drive integration
  - `document_parser.py`: LlamaParse integration
  - `config.py` and `config_models.py`: Configuration handling

- `scripts/`: Operation scripts
  - `start_chroma_docker.ps1`: ChromaDB container management
  - `ingest_gdrive_documents.py`: End-to-end ingestion orchestration

- `tests/`: Comprehensive test suite
  - `tests/utils/`: Unit tests for individual components
  - `tests/integration/`: Integration tests between components
  - `tests/test_end_to_end_ingestion.py`: End-to-end workflow tests
  - `tests/README.md`: Detailed test suite documentation

## Testing

The project includes a comprehensive test suite covering unit tests, integration tests, and end-to-end tests. All tests must be run using the `uv` package manager.

### Running Tests

```powershell
# Run all tests
uv run python run_tests.py --all

# Run only unit tests
uv run python run_tests.py --unit

# Run only integration tests
uv run python run_tests.py --integration

# Run specific module tests
uv run python run_tests.py --module tests.utils.test_edge_cases

# Generate coverage report
uv run python run_tests.py --all --coverage
```

For detailed information about the test suite organization, fixtures, and best practices, refer to `tests/README.md`.

- `docs/`: Documentation files
  - `chromadb_docker_usage.md`: ChromaDB setup instructions

- `Project Documentation/`: Project planning and progress tracking
  - `buildprogress.md` and `buildprogress01.md`: Development logs

## Troubleshooting

### ChromaDB Connection Issues

- Verify Docker container is running: `.\scripts\start_chroma_docker.ps1 status`
- Check ChromaDB logs: `.\scripts\start_chroma_docker.ps1 logs`
- Confirm host/port settings in `.env` match Docker configuration

### Google Drive Authentication Problems

- Verify service account has access to the target folder
- Ensure impersonated user has appropriate permissions
- Check path to credentials file in `.env`

### Neo4j Connection Issues

- Verify Neo4j URI, username, and password in `.env`
- Ensure network connectivity to Neo4j instance
- Check for any Neo4j version compatibility issues

## License

This project is for internal use only. All rights reserved.
