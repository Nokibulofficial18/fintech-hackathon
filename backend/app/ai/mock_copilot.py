from typing import Dict, Any, List
from app.ai.adapter import AICopilotAdapter


class DeterministicMockCopilot(AICopilotAdapter):
    """
    Deterministic rule-based AI copilot that requires zero external API keys.
    Provides immediate, reliable, structured cross-border advice.
    """

    def generate_financial_advice(
        self,
        student_context: Dict[str, Any],
        scenario_notes: str | None = None,
    ) -> Dict[str, Any]:
        home_curr = student_context.get("home_currency", "BDT")
        dest_curr = student_context.get("destination_currency", "CNY")
        uni = student_context.get("university_name", "Tsinghua University")
        runway_months = float(student_context.get("runway_months", 2.6))

        insights: List[Dict[str, str]] = []

        # Insight 1: FX Timing & Batching
        insights.append({
            "category": "TRANSFER_OPTIMIZATION",
            "title": f"Batch Transfers to Reduce Fixed Wire Penalties ({home_curr} -> {dest_curr})",
            "summary": (
                f"Traditional wire banks charge high upfront wire fees (up to 120 CNY / 1,800 BDT) plus up to 2.6% FX margin. "
                f"Consolidating remittances into planned semester tranches saves substantial network charges "
                f"compared to frequent ad-hoc wires."
            ),
            "priority": "HIGH",
        })

        # Insight 2: Tuition Deadlines & FX Hedging
        insights.append({
            "category": "TUITION_PLANNING",
            "title": f"Upcoming Tuition Payment for {uni}",
            "summary": (
                f"Plan foreign currency conversion 10 business days before the tuition deadline "
                f"to prevent wire processing delays and avoid emergency credit-card surcharges."
            ),
            "priority": "MEDIUM",
        })

        # Insight 3: Emergency Runway Alert
        if runway_months < 3.0:
            insights.append({
                "category": "RUNWAY_WARNING",
                "title": "Low Liquidity Buffer Alert",
                "summary": (
                    f"Current estimated destination runway is {runway_months:.1f} months. "
                    f"International students should maintain at least a 3-month living buffer."
                ),
                "priority": "CRITICAL",
            })
        else:
            insights.append({
                "category": "CASH_FLOW_HEALTH",
                "title": "Stable Living Cost Runway",
                "summary": (
                    f"Estimated destination runway is {runway_months:.1f} months, which exceeds "
                    f"the recommended baseline buffer."
                ),
                "priority": "LOW",
            })

        return {
            "engine": "Deterministic Heuristic Copilot (Offline Safe)",
            "status": "active",
            "recommendations_count": len(insights),
            "insights": insights,
            "disclaimer": (
                "Educational financial planning prototype for international students. "
                "Not financial or tax advice."
            ),
        }
