# src/backend/routers/chat.py
# FastAPI router for chat-related endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from src.graph_querying.super_hybrid_orchestrator import SuperHybridOrchestrator

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
async def handle_chat_message(request: ChatRequest):
    """
    Handles a chat message by performing a super-hybrid search across ChromaDB and the graph.
    """
    logger.info(f"Received chat query for super-hybrid search: {request.query}")
    orchestrator = None
    try:
        orchestrator = SuperHybridOrchestrator()
        search_results = await orchestrator.search(request.query)
        return search_results

    except Exception as e:
        logger.error(f"Error during super-hybrid chat processing for query '{request.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing your query: {e}")
    finally:
        if orchestrator:
            await orchestrator.close()
