from fastapi import FastAPI

app = FastAPI(
    title="Hybrid RAG System API",
    description="API for the hybrid RAG system, orchestrating knowledge graph and vector search.",
    version="0.1.0",
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Hybrid RAG System API"}

# Placeholder for future routers (chat, ingest, etc.)
# from .routers import chat_router, ingest_router
# app.include_router(chat_router.router, prefix="/api/v1")
# app.include_router(ingest_router.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    # This is for local development running this file directly.
    # For production, use a command like: uv run uvicorn src.backend.main_api:app --host 0.0.0.0 --port 8000 --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
