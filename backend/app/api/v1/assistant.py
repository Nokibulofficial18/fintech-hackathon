from fastapi import APIRouter
from app.schemas.assistant import ChatRequest, ChatResponse
from app.ai.orchestrator import copilot_orchestrator

router = APIRouter(prefix="/assistant", tags=["AI Copilot Assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(request: ChatRequest) -> ChatResponse:
    """
    Conversational AI Copilot endpoint for international students.
    Interprets student inquiries, retrieves verified financial data via approved deterministic tools,
    validates every parameter using Pydantic, and returns structured explanations with quantitative evidence.
    """
    return copilot_orchestrator.process_chat(request)
