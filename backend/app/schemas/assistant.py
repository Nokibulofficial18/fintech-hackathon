from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.recommendations import ActionableRecommendation


class ChatRequest(BaseModel):
    """User message and optional context sent to the AI Copilot."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The student's financial question or scenario inquiry",
        json_schema_extra={"example": "Can I afford my tuition payment next month?"},
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session or conversation ID",
    )
    simulate_delayed_income_days: Optional[int] = Field(
        default=None,
        ge=0,
        le=180,
        description="Optional simulation scenario: simulate income delayed by N days",
    )


class ToolExecutionResult(BaseModel):
    """Structured record of an approved deterministic tool called by the assistant."""
    tool_name: str
    arguments: Dict[str, Any]
    output: Dict[str, Any]
    timestamp_utc: datetime
    execution_status: str = "SUCCESS"  # SUCCESS or FAILED_VALIDATION


class ChatResponse(BaseModel):
    """Comprehensive, structured AI Copilot response with grounded evidence."""
    message: str = Field(
        ...,
        description="Assistant's conversational, analytical explanation",
    )
    tool_results: List[ToolExecutionResult] = Field(
        default_factory=list,
        description="Verified quantitative evidence retrieved strictly from backend services",
    )
    recommendations: List[ActionableRecommendation] = Field(
        default_factory=list,
        description="Prioritized actionable next steps relevant to the student's question",
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Explicit assumptions made in evaluating the student's scenario",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Disclaimers, data staleness flags, or missing data caveats",
    )
    data_timestamps: Dict[str, str] = Field(
        default_factory=dict,
        description="Timestamps and provenance of the data feeds utilized",
    )
    is_demo_mode: bool = Field(
        default=True,
        description="True if running in offline deterministic mode without external LLM keys",
    )
    requires_confirmation: bool = Field(
        default=False,
        description="True if the simulated action requires student preview/confirmation",
    )
    confirmation_preview: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Preview of simulated consequential plan adjustment",
    )
