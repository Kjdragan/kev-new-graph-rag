"""
Orchestration script for kev-new-graph-rag document ingestion pipeline.

This script manages the end-to-end process of:
1. Fetching documents from Google Drive
2. Parsing them with LlamaParse
3. Ingesting them into both ChromaDB (vector store) and Neo4j (graph database)
"""

import argparse
import os
import sys
import uuid
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import dotenv
from loguru import logger

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.gdrive_reader import GDriveReader, GDriveReaderConfig
from utils.document_parser import DocumentParser, LlamaParseConfig
from utils.chroma_ingester import ChromaIngester 
from utils.neo4j_ingester import Neo4jIngester, DocumentIngestionData
from neo4j import GraphDatabase
from utils.embedding import CustomGeminiEmbedding
from utils.config_models import (
    GDriveReaderConfig, 
    LlamaParseConfig, 
    ChromaDBConfig, 
    Neo4jConfig, 
    EmbeddingConfig,
    IngestionOrchestratorConfig
)
from utils.config import Config

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_filename = f"ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logger.add(
    log_dir / log_filename,
    rotation="20 MB",
    retention="7 days",
    level="INFO"
)

def setup_config(env_file: Optional[str] = None) -> IngestionOrchestratorConfig:
    """Load configuration from environment variables and/or config files."""
    # Load environment variables
    if env_file:
        dotenv.load_dotenv(env_file)
    else:
        dotenv.load_dotenv()
    
    # Load config from YAML via Config singleton
    config = Config()
    
    # Create configuration objects
    gdrive_config = GDriveReaderConfig(
        credentials_path=os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH", ""),
        folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""),
        impersonated_user_email=os.getenv("GOOGLE_DRIVE_IMPERSONATED_USER_EMAIL", None)
    )
    
    llamaparse_config = LlamaParseConfig(
        api_key=os.getenv("LLAMA_CLOUD_API_KEY", "")
    )
    
    neo4j_config = Neo4jConfig(
        uri=os.getenv("NEO4J_URI", ""),
        user=os.getenv("NEO4J_USER", ""),
        password=os.getenv("NEO4J_PASSWORD", ""),
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
        retry_count=int(os.getenv("NEO4J_RETRY_COUNT", "3")),
        retry_interval=float(os.getenv("NEO4J_RETRY_INTERVAL", "1.0"))
    )
    
    chroma_config = ChromaDBConfig(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
        collection_name=os.getenv("CHROMA_COLLECTION_NAME", "documents"),
        auth_enabled=os.getenv("CHROMA_AUTH_ENABLED", "false").lower() == "true",
        username=os.getenv("CHROMA_USERNAME", "admin"),
        password=os.getenv("CHROMA_PASSWORD", "admin123")
    )
    
    # Get embedding configuration from Config singleton
    # The config.yaml structure uses gemini.embeddings.model_id and gemini.embeddings.output_dimensionality
    embedding_model_name = config.get("gemini.embeddings.model_id", "gemini-embedding-001")
    embedding_dimensions = config.get("gemini.embeddings.output_dimensionality", 1536)
    
    logger.info(f"Using embedding model: {embedding_model_name} with {embedding_dimensions} dimensions")
    
    embedding_config = EmbeddingConfig(
        model_name=embedding_model_name,
        dimensions=embedding_dimensions,
        google_api_key=os.getenv("GOOGLE_API_KEY", "")
    )
    
    # Create orchestrator config
    orchestrator_config = IngestionOrchestratorConfig(
        gdrive=gdrive_config,
        llamaparse=llamaparse_config,
        neo4j=neo4j_config,
        chromadb=chroma_config,
        embedding=embedding_config
    )
    
    return orchestrator_config

def process_documents(config: IngestionOrchestratorConfig, temp_dir: str = "./temp") -> Dict[str, int]:
    """Process documents from Google Drive to ChromaDB and Neo4j.
    
    Returns:
        Dict with counts of processed, failed, and skipped documents.
    """
    # Create temp directory if needed
    temp_path = Path(temp_dir)
    temp_path.mkdir(exist_ok=True)
    
    # Initialize components
    logger.info("Initializing pipeline components...")
    gdrive_reader = GDriveReader(config.gdrive)
    document_parser = DocumentParser(config.llamaparse)
    
    # Initialize embedding model with error handling
    try:
        # Get Google API key directly from environment variables, not from EmbeddingConfig
        google_api_key = os.getenv("GOOGLE_API_KEY", "")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
            
        embedding_model = CustomGeminiEmbedding(
            model_name=config.embedding.model_name,
            output_dimensionality=config.embedding.dimensions,
            google_api_key=google_api_key
        )
        # Verify embedding model works by testing a simple embedding
        test_embedding = embedding_model.embed_query("Test embedding capability")
        if not test_embedding or len(test_embedding) != config.embedding.dimensions:
            raise ValueError(f"Embedding model returned invalid embedding dimensions: {len(test_embedding) if test_embedding else 0}, expected {config.embedding.dimensions}")
        logger.info(f"Embedding model initialized successfully with {config.embedding.dimensions} dimensions")
    except Exception as e:
        logger.error(f"Failed to initialize embedding model: {e}")
        raise
    
    # Initialize both ingestion paths with proper error handling
    try:
        logger.info("Initializing ChromaDB ingester...")
        chroma_ingester = ChromaIngester(config.chromadb, embedding_model)
        # Verify ChromaDB connection by getting collection count
        collection = chroma_ingester.get_or_create_collection()
        doc_count = chroma_ingester.count_documents()
        logger.info(f"ChromaDB ingester initialized successfully. Collection '{config.chromadb.collection_name}' has {doc_count} documents.")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB ingester: {e}")
        raise
        
    try:
        logger.info("Initializing Neo4j ingester...")
        # Create a Neo4j Driver instance from the config
        neo4j_driver = GraphDatabase.driver(
            config.neo4j.uri,
            auth=(config.neo4j.user, config.neo4j.password)
        )
        # Pass the driver instance to Neo4jIngester
        neo4j_ingester = Neo4jIngester(neo4j_driver)
        logger.info("Neo4j ingester initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j ingester: {e}")
        raise
    
    # Ensure Neo4j constraints and indices
    logger.info("Setting up Neo4j constraints and indices...")
    neo4j_ingester.ensure_constraints_and_indices()
    
    # List files in Google Drive with error handling
    try:
        logger.info(f"Listing files from Google Drive folder {config.gdrive.folder_id}...")
        drive_files = gdrive_reader.list_files()
        logger.info(f"Found {len(drive_files)} files in Google Drive folder")
    except Exception as e:
        logger.error(f"Failed to list files from Google Drive: {e}")
        raise
    
    # Statistics counters
    stats = {
        "total": len(drive_files),
        "processed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # Process each file
    for file_info in drive_files:
        file_id = file_info.get('id')
        file_name = file_info.get('name')
        mime_type = file_info.get('mimeType')
        
        logger.info(f"Processing file: {file_name} ({file_id}) of type {mime_type}")
        
        try:
            # Download file to temp directory if needed
            temp_file_path = temp_path / f"{file_id}_{file_name}"
            gdrive_reader.download_file_to_path(file_id, str(temp_file_path))
            
            # Parse document with LlamaParse
            logger.info(f"Parsing {file_name} with LlamaParse...")
            parsed_document = document_parser.parse_file(str(temp_file_path))
            
            # ChromaDB Ingestion Path
            logger.info(f"Ingesting {file_name} to ChromaDB...")
            chroma_documents = []
            
            # Process each page/chunk from the parsed document
            for idx, page in enumerate(parsed_document):
                page_doc = {
                    "id": f"{file_id}_p{idx}_{uuid.uuid4()}",
                    "text": page['text'],
                    "metadata": {
                        "source_file": file_name,
                        "file_id": file_id,
                        "page_number": idx + 1,
                        "mime_type": mime_type,
                        "ingested_at": datetime.now().isoformat()
                    }
                }
                chroma_documents.append(page_doc)
            
            # Batch ingest to ChromaDB
            chroma_ingester.ingest_documents(chroma_documents)
            
            # Neo4j Ingestion Path
            logger.info(f"Ingesting {file_name} to Neo4j...")
            # For Neo4j, we concatenate all text for a single document embedding
            concatenated_text = document_parser.parse_file_to_concatenated_text(str(temp_file_path))
            
            # Generate embedding for Neo4j
            logger.info(f"Generating embedding for Neo4j document {file_name}...")
            document_embedding = embedding_model.embed_query(concatenated_text)
            
            # Create DocumentIngestionData for Neo4j
            doc_data = DocumentIngestionData(
                doc_id=file_id,
                filename=file_name,
                content=concatenated_text,
                embedding=document_embedding,
                source_type="google_drive",
                mime_type=mime_type,
                gdrive_id=file_id,
                gdrive_webview_link=file_info.get('webViewLink', ''),
                metadata={
                    "title": file_name,
                    "ingestion_date": datetime.now().isoformat(),
                    "source_folder_id": config.gdrive.folder_id
                }
            )
            
            # Ingest to Neo4j
            neo4j_ingester.ingest_document(doc_data)
            
            # Clean up temp file if needed
            if temp_file_path.exists():
                temp_file_path.unlink()
                
            logger.info(f"Successfully processed {file_name} (ID: {file_id})")
            stats["processed"] += 1
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {str(e)}")
            logger.exception("Exception details:")
            stats["failed"] += 1
            continue
    
    logger.info(f"Document ingestion complete! Summary: {stats['processed']} processed, {stats['failed']} failed, {stats['skipped']} skipped")
    return stats

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Google Drive Document Ingestion Tool")
    parser.add_argument("--env-file", type=str, help="Path to .env file")
    parser.add_argument("--temp-dir", type=str, default="./temp", help="Path for temporary files")
    
    args = parser.parse_args()
    
    try:
        # Setup configuration
        config = setup_config(args.env_file)
        
        # Validate required configuration
        if not config.gdrive.credentials_path or not config.gdrive.folder_id:
            logger.error("Missing Google Drive configuration. Check your .env file.")
            sys.exit(1)
        
        if not config.llamaparse.api_key:
            logger.error("Missing LlamaParse API key. Check your .env file.")
            sys.exit(1)
        
        # Process documents
        stats = process_documents(config, args.temp_dir)
        
        # Print final summary
        print(f"\nIngestion Summary:")
        print(f"  Total files found:   {stats['total']}")
        print(f"  Successfully processed: {stats['processed']}")
        print(f"  Failed:               {stats['failed']}")
        print(f"  Skipped:              {stats['skipped']}")
        
        if stats['failed'] > 0:
            print(f"\nWARNING: {stats['failed']} files failed processing. Check the logs for details.")
        
    except Exception as e:
        logger.error(f"Error during ingestion process: {str(e)}")
        logger.exception("Exception details:")
        sys.exit(1)

if __name__ == "__main__":
    main()
