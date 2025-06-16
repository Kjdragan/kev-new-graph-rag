# src/backend/routers/ingest.py
# FastAPI router for ingestion-related endpoints
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger

from src.graph_extraction.extractor import GraphExtractor
from src.ontology_templates.universal_ontology import NODE_TYPES, RELATIONSHIP_TYPES

router = APIRouter()

@router.post("/ingest/document")
async def ingest_document(file: UploadFile = File(...)):
    """Receives a document, extracts its content, and ingests it into the knowledge graph."""
    try:
        logger.info(f"Received file for ingestion: {file.filename}")
        text_content = (await file.read()).decode('utf-8')
        logger.info(f"Successfully read {len(text_content)} characters from {file.filename}")

        # Initialize the GraphExtractor
        extractor = GraphExtractor(
            neo4j_uri=os.getenv('NEO4J_URI'),
            neo4j_user=os.getenv('NEO4J_USERNAME'),
            neo4j_pass=os.getenv('NEO4J_PASSWORD')
        )

        logger.info("GraphExtractor initialized. Starting extraction...")
        # Perform the extraction
        extracted_data = await extractor.extract(
            text_content=text_content,
            ontology_nodes=NODE_TYPES,
            ontology_edges=RELATIONSHIP_TYPES,
            group_id="ui_upload",
            episode_name_prefix=file.filename
        )
        logger.info(f"Extraction successful for {file.filename}. Ingested {len(extracted_data.get('nodes', []))} nodes and {len(extracted_data.get('edges', []))} edges.")

        return {
            "message": f"Successfully ingested document: {file.filename}",
            "nodes_ingested": len(extracted_data.get('nodes', [])),
            "edges_ingested": len(extracted_data.get('edges', []))
        }

    except Exception as e:
        logger.error(f"Failed to ingest document {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
    finally:
        await file.close()
        if 'extractor' in locals() and extractor:
            await extractor.close()

@router.post("/ingest/gdrive")
async def ingest_gdrive_documents():
    # Placeholder for Google Drive ingestion logic
    return {"message": "Google Drive ingestion started (placeholder)"}

@router.post("/ingest/youtube")
async def ingest_youtube_transcript(youtube_url: str):
    # Placeholder for YouTube transcript ingestion logic
    return {"message": f"YouTube transcript ingestion for {youtube_url} started (placeholder)"}
