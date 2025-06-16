# src/backend/routers/ingest.py
# FastAPI router for ingestion-related endpoints, now powered by the modular orchestrator.

import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pydantic import BaseModel
from loguru import logger

from src.ingestion.orchestrator import IngestionOrchestrator

router = APIRouter()

# The IngestionOrchestrator will be initialized on-demand within each endpoint
# to avoid requiring all environment variables to be set at server startup.

class GDriveIngestionRequest(BaseModel):
    folder_id: str

class YouTubeIngestionRequest(BaseModel):
    url: str

@router.post("/ingest/document")
async def ingest_document(file: UploadFile = File(...)):
    """Receives a local document, saves it temporarily, and ingests it via the orchestrator."""
    try:
        orchestrator = IngestionOrchestrator()
        # Use a temporary file to handle the upload, ensuring it's available for parsing
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        logger.info(f"Received file '{file.filename}', saved to temp path: {tmp_path}")
        
        # Run the local file ingestion pipeline
        result = await orchestrator.run_local_file_ingestion(file_path=tmp_path, file_name=file.filename)
        
        if result.get("errors"):
            logger.error(f"Ingestion failed for {file.filename} with errors: {result['errors']}")
            raise HTTPException(status_code=500, detail={"message": "Ingestion failed", "errors": result['errors']})

        return {
            "message": f"Successfully ingested document: {file.filename}",
            "summary": result
        }

    except Exception as e:
        logger.exception(f"An unexpected error occurred during ingestion for document {file.filename}")
        raise HTTPException(status_code=500, detail={"message": "An unexpected server error occurred", "error": str(e)})
    finally:
        # Clean up the temporary file
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.info(f"Cleaned up temporary file: {tmp_path}")

@router.post("/ingest/gdrive")
async def ingest_gdrive_documents(request_data: GDriveIngestionRequest = Body(...)):
    """Receives a GDrive folder ID and ingests its contents via the orchestrator."""
    logger.info(f"Received request to ingest from Google Drive folder: {request_data.folder_id}")
    try:
        orchestrator = IngestionOrchestrator()
        # The orchestrator now handles the entire GDrive logic
        result = await orchestrator.run_gdrive_ingestion(folder_id=request_data.folder_id)

        if result.get("errors"):
            logger.error(f"Ingestion failed for GDrive folder {request_data.folder_id} with errors: {result['errors']}")
            raise HTTPException(status_code=500, detail={"message": "Ingestion failed", "errors": result['errors']})

        return {
            "message": f"Google Drive ingestion complete for folder {request_data.folder_id}.",
            "summary": result
        }

    except Exception as e:
        logger.exception(f"An unexpected error occurred during GDrive ingestion for folder {request_data.folder_id}")
        raise HTTPException(status_code=500, detail={"message": "An unexpected server error occurred", "error": str(e)})

@router.post("/ingest/youtube")
async def ingest_youtube_transcript(request_data: YouTubeIngestionRequest = Body(...)):
    """Receives a YouTube URL and ingests its transcript via the orchestrator."""
    logger.info(f"Received request to ingest from YouTube URL: {request_data.url}")
    try:
        orchestrator = IngestionOrchestrator()
        result = await orchestrator.run_youtube_ingestion(youtube_url=request_data.url)

        if result.get("errors"):
            logger.error(f"Ingestion failed for YouTube URL {request_data.url} with errors: {result['errors']}")
            raise HTTPException(status_code=500, detail={"message": "Ingestion failed", "errors": result['errors']})

        return {
            "message": f"YouTube transcript ingestion complete for URL {request_data.url}.",
            "summary": result
        }

    except Exception as e:
        logger.exception(f"An unexpected error occurred during YouTube ingestion for URL {request_data.url}")
        raise HTTPException(status_code=500, detail={"message": "An unexpected server error occurred", "error": str(e)})
