# src/backend/routers/chat.py
# FastAPI router for chat-related endpoints
from fastapi import APIRouter

router = APIRouter()

@router.post("/chat")
async def handle_chat_message(query: str):
    # Placeholder: In the future, this will orchestrate the hybrid query
    return {"query_received": query, "response": f"Backend says: I received '{query}'"}
