"""
Orchestration script for kev-new-graph-rag document ingestion pipeline.

This script manages the end-to-end process of:
1. Fetching documents from Google Drive
2. Parsing them with LlamaParse
3. Ingesting them into both ChromaDB (vector store) and Neo4j (graph database)
"""

import argparse
import nest_asyncio
nest_asyncio.apply()
import os
import sys
import uuid
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Type

import dotenv
from loguru import logger

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.gdrive_reader import GDriveReader, GDriveReaderConfig
from utils.document_parser import DocumentParser, LlamaParseConfig
from utils.embedding import CustomGeminiEmbedding
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
    IngestionOrchestratorConfig,
    GeminiModelInstanceConfig
)
from utils.config_loader import get_config
from src.graph_extraction.extractor import GraphExtractor
from pydantic import BaseModel # For type hinting
import importlib
import asyncio

# Configure logging
logger.remove() # remove default logger
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_filename = f"ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Console logger with INFO level
logger.add(
    sys.stderr, 
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)
# File logger with DEBUG level
logger.add(
    log_dir / log_filename,
    rotation="20 MB",
    retention="7 days",
    level="DEBUG", # Capture everything in the file
    enqueue=True,
    backtrace=True,
    diagnose=True
)


def load_ontology_from_template(template_name: str) -> Tuple[List[Type[BaseModel]], List[Type[BaseModel]]]:
    """Dynamically loads NODES and RELATIONSHIPS from the specified ontology template."""
    try:
        module_name = f"src.ontology_templates.{template_name}_ontology"
        ontology_module = importlib.import_module(module_name)
        
        nodes = getattr(ontology_module, "NODES", [])
        relationships = getattr(ontology_module, "RELATIONSHIPS", [])
        
        if not nodes and not relationships:
            logger.warning(f"Ontology template '{template_name}' loaded, but NODES or RELATIONSHIPS lists are empty or missing. Please review the template file '{template_name}_ontology.py'.")
        else:
            logger.info(f"Successfully loaded ontology module for template: '{template_name}' (module: {module_name})")
            logger.info(f"Found {len(nodes)} node types and {len(relationships)} relationship types.")
            
        return nodes, relationships
    except ImportError:
        logger.error(f"Ontology template file '{template_name}_ontology.py' not found in 'src/ontology_templates/'. Please ensure the file exists and is correctly named.")
        raise
    except AttributeError as e:
        logger.error(f"Error accessing NODES or RELATIONSHIPS in '{template_name}_ontology.py': {e}")
        raise


def setup_config(env_file: Optional[str] = None) -> IngestionOrchestratorConfig:
    """Load configuration using the centralized get_config loader."""
    logger.info("Loading configuration...")
    # The get_config function handles loading .env, config.yaml, and assembling the config object.
    config = get_config(env_file=env_file)
    logger.info("IngestionOrchestratorConfig fully initialized.")
    return config

async def process_documents(config: IngestionOrchestratorConfig, model_config: GeminiModelInstanceConfig, ontology_nodes: List[Type[BaseModel]], ontology_edges: List[Type[BaseModel]], temp_dir: str = "./temp") -> Dict[str, int]:
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
    embedding_model = CustomGeminiEmbedding(
        model_name=config.embedding.embedding_model_name,
        output_dimensionality=config.embedding.dimensions
    )
    chroma_ingester = ChromaIngester(config=config.chromadb, embedding_model=embedding_model)
    await chroma_ingester.async_init()
    graph_extractor = GraphExtractor(
        neo4j_uri=config.neo4j.uri,
        neo4j_user=config.neo4j.user,
        neo4j_pass=config.neo4j.password,
        pro_model_config=model_config, # Use the model specified via CLI
        gemini_api_key=os.environ.get("GOOGLE_API_KEY") # Kept for optional API key usage
    )
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
            
            # Parse document with LlamaParse using async method
            logger.info(f"Parsing {file_name} with LlamaParse using async method...")
            parsed_document = await document_parser.aparse_file(str(temp_file_path))
            
            # ChromaDB Ingestion Path
            logger.info(f"Ingesting {file_name} to ChromaDB...")
            chroma_documents = [
                {
                    "id": str(uuid.uuid4()),
                    "document": page.text,
                    "metadata": {
                        "source": file_name,
                        "page_number": page.metadata.get('page', -1), # Use .get for safety
                        "file_id": file_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
                for page in parsed_document
            ]
            # Batch ingest to ChromaDB
            await chroma_ingester.ingest_documents(chroma_documents)
            
            # GraphExtractor Path for Neo4j
            logger.info(f"Extracting graph data from {file_name} using template for Neo4j...")
            full_text_content = await document_parser.aparse_file_to_concatenated_text(str(temp_file_path))
            
            extraction_results = await graph_extractor.extract(
                text_content=full_text_content,
                ontology_nodes=ontology_nodes,
                ontology_edges=ontology_edges,
                group_id=file_id, 
                episode_name_prefix=file_name[:50]
            )
            # Log only summary counts instead of full extraction results to avoid logging embedding vectors
            nodes_count = len(extraction_results.get('nodes', []))
            edges_count = len(extraction_results.get('edges', []))
            logger.info(f"Graph extraction for {file_name} complete. Summary: {nodes_count} nodes, {edges_count} edges extracted")
            
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
    
    # Ensure GraphExtractor connection is closed
    if 'graph_extractor' in locals() and graph_extractor is not None:
        try:
            logger.info("Closing GraphExtractor connection...")
            await graph_extractor.close()
            logger.info("GraphExtractor connection closed.")
        except Exception as e:
            logger.error(f"Error closing GraphExtractor: {e}")
            
    return stats

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Google Drive Document Ingestion Tool")
    parser.add_argument("--env-file", type=str, help="Path to .env file")
    parser.add_argument("--temp-dir", type=str, default="./temp", help="Path for temporary files")
    parser.add_argument("--template", type=str, default="universal", help="Name of the ontology template to use (e.g., 'universal', 'generic', 'financial_report').")
    parser.add_argument("--llm-model", type=str, default="flash", choices=["pro", "flash"], help="The Gemini model to use for graph extraction ('pro' or 'flash').")
    
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
        
        # Load the specified ontology template
        ontology_nodes, ontology_edges = load_ontology_from_template(args.template)

        # Select the appropriate LLM configuration based on the CLI argument
        if args.llm_model == "pro":
            model_config = config.gemini_suite.pro_model
            logger.info(f"Using Gemini Pro model ('{model_config.model_id}') for graph extraction.")
        else:
            model_config = config.gemini_suite.flash_model
            logger.info(f"Using Gemini Flash model ('{model_config.model_id}') for graph extraction.")
        
        # Process documents
        stats = await process_documents(config, model_config, ontology_nodes, ontology_edges, args.temp_dir)
        
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
    asyncio.run(main())
