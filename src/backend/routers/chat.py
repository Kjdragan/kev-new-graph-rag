# src/backend/routers/chat.py
# FastAPI router for chat-related endpoints
from fastapi import APIRouter
from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str

router = APIRouter()

@router.post("/chat")
async def handle_chat_message(request: ChatRequest):
    # Placeholder: In the future, this will orchestrate the hybrid query
    return {"query_received": request.query, "response": f"Backend says: I received '{request.query}'"}
