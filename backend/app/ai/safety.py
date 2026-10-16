import re
from typing import Tuple

# Patterns identifying injection attempts or unauthorized actions
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s+prompt",
    r"(reveal|print|show|leak)\s+(the\s+)?(api[_\s]?key|secret|password|env)",
    r"(drop|delete|update|insert\s+into)\s+(table|users|profiles|database)",
    r"\b(bash|powershell|cmd|sh|curl|wget|exec|eval)\b",
    r"(bypass|override)\s+(auth|security|controls|permissions)",
    r"rm\s+-rf",
]

# Patterns attempting autonomous live financial movement
AUTONOMOUS_TRANSFER_PATTERNS = [
    r"\b(transfer|wire|send|pay|debit)\s+(\$|usd|inr|\d+)",
    r"\b(execute|initiate|authorize)\s+(the\s+)?(real\s+|live\s+)?(payment|transfer|transaction|wire)\b",
    r"\bmove\s+money\b",
]


def evaluate_prompt_safety(user_message: str) -> Tuple[bool, str | None, bool]:
    """
    Evaluate user prompt against strict security guardrails.
    Returns: (is_safe, refusal_reason, is_autonomous_transfer_request)
    """
    lower = user_message.strip().lower()

    # 1. Check prompt injection and unauthorized execution
    for pat in INJECTION_PATTERNS:
        if re.search(pat, lower):
            return (
                False,
                "Request refused: Prompt contains disallowed instruction override, credential access, or unauthorized system execution syntax.",
                False,
            )

    # 2. Check autonomous transaction requests
    for pat in AUTONOMOUS_TRANSFER_PATTERNS:
        if re.search(pat, lower):
            # Check if it's purely an advisory question vs a command to move money
            if any(q_word in lower for q_word in ["which", "compare", "how much", "can i", "what if", "options", "cheapest", "best"]):
                # Advisory question, allowed
                pass
            else:
                return (
                    False,
                    "Advisory Guardrail: BorderWise AI is an educational decision-support copilot. It does not initiate or execute live wire transfers or connect to live payment rails. You can simulate transfer costs using the transfer comparison tool.",
                    True,
                )

    return True, None, False
