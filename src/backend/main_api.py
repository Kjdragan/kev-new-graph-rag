from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
