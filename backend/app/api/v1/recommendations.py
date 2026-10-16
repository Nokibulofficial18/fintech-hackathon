from fastapi import APIRouter
from app.schemas.recommendations import RecommendationsResponse
from app.services.demo_scenario_service import get_seeded_demo_scenario
from app.services.recommendation_service import generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["Actionable Recommendations"])


@router.get("", response_model=RecommendationsResponse)
def get_prioritized_recommendations() -> RecommendationsResponse:
    """
    Generate deterministic, prioritized recommendations derived strictly from quantitative financial modeling.
    Includes reason, supporting numbers, urgency, assumptions, uncertainty, and regulatory disclaimers.
    Zero investment advice or speculative promises.
    """
    scenario = get_seeded_demo_scenario()
    return generate_recommendations(scenario)
