from abc import ABC, abstractmethod
from typing import Dict, Any, List


class AICopilotAdapter(ABC):
    """Abstract interface for BorderWise AI Copilot providers."""

    @abstractmethod
    def generate_financial_advice(
        self,
        student_context: Dict[str, Any],
        scenario_notes: str | None = None,
    ) -> Dict[str, Any]:
        """
        Generate structured, actionable cross-border financial insights and advice.
        Must return consistent JSON schema regardless of LLM vs mock backend.
        """
        pass
