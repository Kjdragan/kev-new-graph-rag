# Kev Graph RAG

A comprehensive Graph-enhanced RAG (Retrieval Augmented Generation) system utilizing Google Drive, ChromaDB vector storage, Neo4j graph database, and Google Gemini models.

## Overview

This project implements a unified ingestion pipeline for documents from Google Drive into both ChromaDB (vector database) and Neo4j (graph database) for enhanced retrieval and contextual understanding. The system leverages the strengths of both vector and graph-based approaches to improve information retrieval quality.

## Prerequisites

- Python 3.13+
- Docker Desktop
- Google Cloud account with API access
- Neo4j AuraDB instance
- Valid API keys and credentials configured in `.env` file

## Quick Start

### 1. Environment Setup

First, ensure all environment variables are set up in the `.env` file. This includes:
- Google API credentials
- ChromaDB configuration
- Neo4j credentials

### 2. Start ChromaDB Instance (Required)

Use the provided PowerShell script to start ChromaDB:

```powershell
# Start ChromaDB container
.\scripts\start_chroma_docker.ps1
```

Verify ChromaDB is running:

```powershell
.\scripts\start_chroma_docker.ps1 status
```

### 3. Install Dependencies

Install required Python packages using uv:

```powershell
uv sync
```

## Key Components

### ChromaDB Vector Storage

The project uses ChromaDB for vector storage and similarity search:
- Docker-based deployment with persistent storage
- ChromaDB container management via `.\scripts\start_chroma_docker.ps1`
- Complete documentation in `docs\chromadb_docker_usage.md`

### Google Drive Integration

Automated document fetching from Google Drive with:
- Authentication via OAuth 2.0
- Support for various document formats
- Configurable folder synchronization

### Embedding Generation

Custom embedding generation using Google Gemini models:
- Configurable embedding model via `config.yaml`
- Support for different embedding dimensions
- Integration with LlamaIndex embedding interfaces

### Neo4j Graph Database

Graph-enhanced RAG using Neo4j:
- Structured relationship storage
- Graph-based context retrieval
- Entity extraction and relationship mapping

## Usage

### Document Ingestion

To ingest documents from Google Drive:

```powershell
uv run scripts\ingest_gdrive_documents.py
```

### Configuration

Key configuration settings are managed in `config.yaml`:
- Embedding model selection
- Vector dimensions
- Collection settings
- Resource limits

## Documentation

For detailed information on specific components:

- ChromaDB setup and management: `docs\chromadb_docker_usage.md`
- Project build progress: `Project Documentation\buildprogress.md`
- Ingestion build plan: `Project Documentation\ingestionbuildplan.md`

## Project Structure

- `utils/`: Core utility modules
  - `embedding.py`: Custom Gemini embedding implementation
  - `chroma_ingester.py`: ChromaDB integration
  - `neo4j_ingester.py`: Neo4j database operations
  - `gdrive_utils.py`: Google Drive integration
- `scripts/`: Operation scripts
  - `start_chroma_docker.ps1`: ChromaDB container management
  - `ingest_gdrive_documents.py`: End-to-end ingestion orchestration
- `docs/`: Documentation files
- `Project Documentation/`: Project planning and progress tracking

## License

This project is for internal use only. All rights reserved.
