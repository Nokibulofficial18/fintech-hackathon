from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import SupportedCurrency
from app.schemas.profile import FullStudentScenario


class ForecastRequest(BaseModel):
    """Parameters for running the 90-day cash flow simulation."""
    scenario: Optional[FullStudentScenario] = Field(
        default=None,
        description="Optional custom student scenario. If omitted, uses seeded demo scenario.",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="Forecast simulation start date. Defaults to scenario's baseline date (2026-10-15).",
    )
    forecast_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Horizon in calendar days (typically 90 days).",
    )
    safety_reserve_by_currency: Optional[Dict[str, Decimal]] = Field(
        default=None,
        description="Desired minimum liquidity buffer per currency (e.g. {'USD': 1000.00}).",
    )


class TimelineEvent(BaseModel):
    """Individual transactional event within the forecast horizon."""
    event_id: str
    event_date: date
    event_type: str = Field(..., description="INCOME, LIVING_EXPENSE, TUITION, REMITTANCE_OUT, REMITTANCE_IN")
    description: str
    currency: SupportedCurrency
    amount: Decimal = Field(..., description="Positive for inflows, negative for outflows")
    is_projected: bool = Field(default=True, description="True for all forecast events")


class DailyCurrencyBalance(BaseModel):
    """Running balance position on a specific calendar date."""
    date: date
    currency: SupportedCurrency
    starting_balance: Decimal
    total_inflow: Decimal
    total_outflow: Decimal
    ending_balance: Decimal
    is_projected: bool = True
    is_shortfall: bool = False
    shortfall_amount: Decimal = Decimal("0.00")


class ShortfallEvent(BaseModel):
    """Detected deficit where projected liquid funds fall below zero or the safety threshold."""
    shortfall_id: str
    shortfall_date: date
    currency: SupportedCurrency
    projected_balance: Decimal
    shortfall_amount: Decimal = Field(..., description="Deficit below zero or safety reserve")
    trigger_event: str
    days_from_start: int
    urgency: str = Field(..., description="CRITICAL, HIGH, MEDIUM")


class DataCompletenessReport(BaseModel):
    """Explains which data components were provided vs. defaulted or approximated."""
    completeness_score: float = Field(..., ge=0.0, le=1.0)
    has_verified_actual_balances: bool
    has_scheduled_income: bool
    has_itemized_living_expenses: bool
    has_tuition_deadline: bool
    has_planned_remittances: bool
    missing_elements: List[str]
    notes: str


class CashFlowForecastResponse(BaseModel):
    """Complete 90-day multi-currency cash-flow projection."""
    forecast_start_date: date
    forecast_end_date: date
    horizon_days: int
    actual_balances_as_of: date

    # Initial actual liquid position (distinct from forecast values)
    initial_actual_balances: Dict[str, Decimal]

    # End-of-horizon projected liquid position
    projected_end_balances: Dict[str, Decimal]

    # Net projected inflows and outflows per currency
    total_inflows_by_currency: Dict[str, Decimal]
    total_outflows_by_currency: Dict[str, Decimal]

    # Detailed timeline events
    timeline_events: List[TimelineEvent]

    # Daily state snapshots (by currency)
    daily_summaries: List[DailyCurrencyBalance]

    # Identified deficit risks
    shortfalls: List[ShortfallEvent]

    # Explicit assumptions
    assumptions: List[str]

    # Completeness audit
    data_completeness: DataCompletenessReport
