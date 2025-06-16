# src/backend/routers/ingest.py
# FastAPI router for ingestion-related endpoints, now powered by the modular orchestrator.

import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pydantic import BaseModel
from loguru import logger

from src.ingestion.orchestrator import IngestionOrchestrator

router = APIRouter()

# Initialize the orchestrator once. In a production app, you might use a dependency injection system.
# For simplicity, we'll create it here. It will be re-created on each server reload.
# This also ensures it picks up any config changes upon reload.
orchestrator = IngestionOrchestrator()

class GDriveIngestionRequest(BaseModel):
    folder_id: str

@router.post("/ingest/document")
async def ingest_document(file: UploadFile = File(...)):
    """Receives a local document, saves it temporarily, and ingests it via the orchestrator."""
    # Use a temporary file to handle the upload, ensuring it's available for parsing
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        logger.info(f"Received file '{file.filename}', saved to temp path: {tmp_path}")
        
        # Run the local file ingestion pipeline
        result = await orchestrator.run_local_file_ingestion(file_path=tmp_path, file_name=file.filename)
        
        if result.get("errors"):
            raise HTTPException(status_code=500, detail=f"Ingestion failed with errors: {result['errors']}")

        return {
            "message": f"Successfully ingested document: {file.filename}",
            "summary": result
        }

    except Exception as e:
        logger.error(f"Failed to ingest document {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
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
        # The orchestrator now handles the entire GDrive logic
        result = await orchestrator.run_gdrive_ingestion(folder_id=request_data.folder_id)

        if result.get("errors"):
            raise HTTPException(status_code=500, detail=f"Ingestion failed with errors: {result['errors']}")

        return {
            "message": f"Google Drive ingestion complete for folder {request_data.folder_id}.",
            "summary": result
        }

    except Exception as e:
        logger.error(f"Failed to ingest from Google Drive folder {request_data.folder_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to ingest from Google Drive: {str(e)}")

@router.post("/ingest/youtube")
async def ingest_youtube_transcript(youtube_url: str):
    # This is now the next logical step to implement using the new modular pipeline.
    logger.info(f"Placeholder for YouTube transcript ingestion for URL: {youtube_url}")
    # Example of how it would work:
    # 1. Create a new IngestionStep: GetYoutubeTranscript
    # 2. Create a new pipeline in the orchestrator: get_youtube_pipeline()
    # 3. Call it: await orchestrator.run_youtube_ingestion(youtube_url)
    return {"message": f"YouTube transcript ingestion for {youtube_url} is not yet implemented."}
