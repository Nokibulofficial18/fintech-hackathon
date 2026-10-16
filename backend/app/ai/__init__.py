from app.core.config import settings
from app.ai.adapter import AICopilotAdapter
from app.ai.mock_copilot import DeterministicMockCopilot


def get_ai_copilot() -> AICopilotAdapter:
    """
    Factory returning configured AI copilot adapter.
    Falls back gracefully to DeterministicMockCopilot if API keys are absent.
    """
    if settings.LLM_PROVIDER.lower() in ("gemini", "openai"):
        # If API keys are absent, fallback safely to deterministic copilot
        if settings.LLM_PROVIDER.lower() == "gemini" and not settings.GEMINI_API_KEY:
            return DeterministicMockCopilot()
        if settings.LLM_PROVIDER.lower() == "openai" and not settings.OPENAI_API_KEY:
            return DeterministicMockCopilot()
        # Future LLM adapters plug in here
    return DeterministicMockCopilot()


__all__ = ["AICopilotAdapter", "DeterministicMockCopilot", "get_ai_copilot"]
