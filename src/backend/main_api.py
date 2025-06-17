import sys
from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# --- Logging Configuration ---
# Remove default handler to avoid duplicate logs
logger.remove()
# Add a new handler that logs to stderr
# Set level to INFO to capture all important operational events
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)
# Also add a file sink to ensure logs are captured persistently
log_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "backend.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logger.add(log_file_path, rotation="10 MB", level="INFO", format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}")

logger.info("Logging configured successfully to console and file.")
# --- End Logging Configuration ---

app = FastAPI(
    title="Hybrid RAG System API",
    description="API for the hybrid RAG system, orchestrating knowledge graph and vector search.",
    version="0.1.0",
)

# CORS configuration
# This allows the Streamlit frontend (running on a different port) to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Hybrid RAG System API"}

# Include routers
from .routers import chat, ingest, graph

app.include_router(chat.router, prefix="/api/v2", tags=["Chat"])
app.include_router(ingest.router, prefix="/api/v2", tags=["Ingestion"])
app.include_router(graph.router, prefix="/api/v2", tags=["Graph"])

if __name__ == "__main__":
    import uvicorn
    # This is for local development running this file directly.
    # For production, use a command like: uv run uvicorn src.backend.main_api:app --host 0.0.0.0 --port 8001 --reload --reload-dir src
    uvicorn.run(app, host="0.0.0.0", port=8001)
