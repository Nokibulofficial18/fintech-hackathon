from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RecommendationPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RecommendationUrgency(str, Enum):
    IMMEDIATE = "IMMEDIATE"            # Next 7 days
    UPCOMING = "UPCOMING"              # Next 8-21 days
    PLANNING = "PLANNING"              # Next 22-90 days
    INFORMATIONAL = "INFORMATIONAL"    # General best practice


class RecommendationCategory(str, Enum):
    TUITION_PRESERVATION = "TUITION_PRESERVATION"
    FUNDING_GAP_ALERT = "FUNDING_GAP_ALERT"
    TRANSFER_OPTIMIZATION = "TRANSFER_OPTIMIZATION"
    EXPENSE_DISCIPLINE = "EXPENSE_DISCIPLINE"
    LIQUIDITY_BUFFER = "LIQUIDITY_BUFFER"


class ActionableRecommendation(BaseModel):
    """Rigorous, deterministic financial recommendation with supporting quantitative evidence."""
    id: str = Field(..., description="Unique deterministic identifier (e.g. REC-TUITION-RESERVE-01)")
    priority: RecommendationPriority
    urgency: RecommendationUrgency
    category: RecommendationCategory
    title: str
    reason: str = Field(..., description="Analytical justification derived strictly from numbers")
    supporting_numbers: Dict[str, Any] = Field(
        ...,
        description="Exact quantitative parameters (amounts, dates, currencies, shortfalls, percentages)",
    )
    assumptions: List[str] = Field(
        ...,
        description="Assumptions underlying this recommendation",
    )
    uncertainty: str = Field(
        ...,
        description="Factors that could alter the recommendation (e.g. FX fluctuations, unexpected delays)",
    )
    suggested_action: str = Field(..., description="Practical non-investment financial action step")


class RecommendationsResponse(BaseModel):
    """Collection of prioritized recommendations generated from deterministic financial analysis."""
    generated_at_utc: datetime
    total_recommendations: int
    critical_count: int
    high_count: int
    recommendations: List[ActionableRecommendation]
    compliance_disclaimer: str = Field(
        default=(
            "Educational decision-support prototype. BorderWise AI provides deterministic "
            "budget and timeline modeling based on student-entered data. It does not provide "
            "investment advice, legal counsel, or guaranteed commercial financial returns."
        ),
    )
